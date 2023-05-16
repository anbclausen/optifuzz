#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/hardirq.h>
#include <linux/preempt.h>
#include <linux/sched.h>
#include <linux/proc_fs.h>
#include <asm/uaccess.h>
#include <linux/mm.h>
#include <linux/string.h>
#include <linux/random.h>
#include <linux/moduleparam.h>

// Definitions from libc not available in kernel
#define INT64_MAX 9223372036854775807LL
#define UINT64_MAX 0xffffffffffffffffULL
#define UINT32_MAX 0xffffffffU

MODULE_LICENSE("Dual BSD/GPL");

#define MIN(x, y) ((x < y) ? (x) : (y))

// Kernel functions to get random values replacing BSD lib functions
#define RAND64(x) get_random_bytes(x, sizeof(int64_t))
#define RANDOM (get_random_u32() > UINT32_MAX / 2)

#define REPEATS 100   /** The amount of times the program \
                       *  is run to get a more accurate measurement. */
#define ITERATIONS 10 /** The amount of times to cycle through all  \
                       *  fuzz inputs to lower noise from other CPU \
                       *  tasks. */

// Kernel parameters
static size_t fuzz_count = 10000;
static char opt_flags[50];

// Registering kernel parameters
module_param_named(count, fuzz_count, long, 0644);
module_param_string(flag, opt_flags, 50, 0644);

// Externel program to be timed
extern int program(int64_t, int64_t);

/**
 * @struct      distribution_et
 * @brief       Distributions for setting the two input variables.
 */
typedef enum
{
    UNIFORMLY, // Uniformly random values
    EQUAL,     // Uniformly random but equal values
    MAX64,     // One is INT64_MAX, other is uniform random
    UMAX64,    // One is UINT64_MAX, other is uniform random. UINT64_MAX is -1 in signed (int64_t)
    ZERO,      // One is 0, other is uniform random
} distribution_et;

#define TOTAL_DISTRIBUTIONS 5

/**
 * @struct      status_et
 * @brief       Status of the program.
 */
typedef enum
{
    RUNNING,
    DONE
} status_et;

// The program status
static status_et status;

// Defines the filenames entries in /proc for reading the program status and the output
#define PROC_STATUS_FILENAME "optifuzz_status"
#define PROC_OUTPUT_FILENAME "optifuzz_output"

// Specifies the entries in /proc for interaction with the module
static struct proc_dir_entry *proc_status;
static struct proc_dir_entry *proc_output;

// Function signatures for read handlers implemented later in this file
static ssize_t proc_status_read(struct file *file, char __user *buf, size_t count, loff_t *pos);
static ssize_t proc_output_read(struct file *file, char __user *buf, size_t count, loff_t *pos);

// Specifies the the read handlers for the proc entries
static const struct proc_ops proc_status_ops = {.proc_read = proc_status_read};
static const struct proc_ops proc_output_ops = {.proc_read = proc_output_read};

// Size of char array in link
#define LINK_SIZE 1000

// Single linked list with char buffer
typedef struct link
{
    struct link *next;
    size_t index;
    char buffer[LINK_SIZE];
} link_buf_st;

// Global list for buffering the result until requested
static link_buf_st *link_buf;

/**
 * @fn          new_link
 * @brief       Allocate space for new link and initialize its values.
 * @return      Returns new initialized link.
 */
link_buf_st *new_link(void)
{
    link_buf_st *link = kmalloc(sizeof(link_buf_st), GFP_KERNEL);
    if (link == NULL)
        printk(KERN_ERR "Could not allocate memory for list link\n");
    link->next = NULL;
    link->index = 0;
    memset(link->buffer, '\0', LINK_SIZE);
    return link;
}
/**
 * @fn          free_links
 * @brief       Free the memory of all links in list.
 */
static void free_links(void)
{
    link_buf_st *prev;
    while (link_buf != NULL)
    {
        prev = link_buf;
        link_buf = link_buf->next;
        kfree(prev);
    }
}

/**
 * @fn          set_values
 * @brief       Set values for input according to distribution.
 * @param       dist                The name of the file to write to.
 * @param       a                   The input value a.
 * @param       b                   The input value b.
 */
static void set_values(distribution_et dist, int64_t *a, int64_t *b)
{
    switch (dist)
    {
    case UNIFORMLY:
        RAND64(a);
        RAND64(b);
        break;
    case EQUAL:
        RAND64(a);
        *b = *a;
        break;
    case MAX64:
        *a = *b = INT64_MAX;
        if (RANDOM)
            RAND64(a);
        else
            RAND64(b);
        break;
    case UMAX64:
        *a = *b = -1;
        if (RANDOM)
            RAND64(a);
        else
            RAND64(b);
        break;
    case ZERO:
        *a = *b = 0;
        if (RANDOM)
            RAND64(a);
        else
            RAND64(b);
        break;
    default:
        printk(KERN_ERR "Distribution not yet supported!");
        break;
    }
}

/**
 * @struct      input_st
 * @brief       A tuple (a,b) defining an input to the program
 */
typedef struct
{
    int64_t a; /** The first input.                         */
    int64_t b; /** The second input.                        */
} input_st;

/**
 * @fn          get_time
 * @brief       Get the time it takes to execute the program with the given inputs.
 * @details     This function is a wrapper around the RDTSC instruction.
 *              It uses CPUID (and DRTSCP) to serialize instructions to avoid out
 *              of order execution for encreased precision.
 *
 *              The code is run multiple times to for a more accurate measurement.
 *              The amount of repeats is determined by REPEATS.
 *
 *              Note: On older machines this returns the actual amount of clock
 *              cycles spent. On newer machines this register is increased at a
 *              fixed rate. Even on newer machines the behavior might differ
 *              between intels version INTEL's IA-64 and AMD's AMD64 version of the
 *              x86-64 architecture.
 *
 *              Note: This is best way to measure time according to INTEL (except
 *              for not running it in kernel space with exclusive permissions) as
 *              described in section 3.2.1 of their white paper fro, sep. 2010:
 *              https://www.intel.de/content/dam/www/public/us/en/documents/white-papers/ia-32-ia-64-benchmark-code-execution-paper.pdf
 *
 * @param       a                   The first input.
 * @param       b                   The second input.
 * @return      The amount of clocks spent on executing.
 */
static inline uint64_t get_time(int64_t a, int64_t b)
{
    unsigned cycles_low_before, cycles_high_before,
        cycles_low_after, cycles_high_after;
    uint64_t start, end;
    unsigned long flags;

    local_irq_save(flags);
    preempt_disable();
    asm volatile( // Force prev instructions to complete before RDTSC bellow
                  // is executed (Serializing instruction execution)
        "CPUID\n\t"
        // Get clock
        "RDTSC\n\t"
        // %0 is cycles_high
        "mov %%edx, %0\n\t"
        // %1 is cycles_low
        "mov %%eax, %1\n\t"
        // Restore clobbered registers
        : "=r"(cycles_high_before), "=r"(cycles_low_before)::"%rax", "%rbx", "%rcx", "%rdx");

    for (size_t i = 0; i < REPEATS; i++)
        program(a, b);

    asm volatile( // Force to wait for all prev instructions before reading
                  // counter. (subsequent instructions may begin execution
                  // before the read)
        "RDTSCP\n\t"
        // Depends on values from RDTSCP, so executed after
        "mov %%edx, %0\n\t"
        // Executed after RDTSCP
        "mov %%eax, %1\n\t"
        // Ensure that the RDTSCP read before any other execution takes place
        "CPUID\n\t"
        // Restore clobbered registers
        : "=r"(cycles_high_after), "=r"(cycles_low_after)::"%rax", "%rbx", "%rcx", "%rdx");
    preempt_enable();
    raw_local_irq_restore(flags);

    start = (((uint64_t)cycles_high_before << 32) | cycles_low_before);
    end = (((uint64_t)cycles_high_after << 32) | cycles_low_after);

    return (end - start);
}

/**
 * @fn          measure
 * @brief       Measure the execution time of the program with random inputs.
 * @details     This function measures the execution time of the program with
 *              random inputs. The measurements are repeated multiple times
 *              to get a more accurate measurement.
 * @param       measurements        The array to store the measurements in.
 * @param       inputs              The inputs to the program.
 * @param       count               The amount of measurements to take.
 */
static void measure(uint64_t *measurements[ITERATIONS], input_st *inputs, size_t count)
{
    uint64_t min, old_min;

    for (size_t j = 0; j < ITERATIONS; j++)
    {
        for (size_t i = 0; i < count; i++)
        {
            min = get_time(inputs[i].a, inputs[i].b);

            old_min = measurements[j][i];
            measurements[j][i] = MIN(old_min, min);
        }
    }
}

/**
 * @fn          generate_inputs
 * @brief       Generate and set all input values.
 * @param       dist                The distribution to draw the inputs from.
 * @param       inputs              the list to write them to.
 * @param       count               The amount of measurements to write.
 */
static void generate_inputs(distribution_et dist, input_st *inputs, size_t count)
{
    for (size_t i = 0; i < count; i++)
        set_values(dist, &inputs[i].a, &inputs[i].b);
}

/**
 * @fn          initialize_measurements
 * @brief       Set initial value of measurements to MAX.
 * @param       measurements        The measurements to set.
 * @param       count               The amount of measurements to write.
 */
static void initialize_measurements(uint64_t *measurements[ITERATIONS], size_t count)
{
    for (size_t j = 0; j < ITERATIONS; j++)
        for (size_t i = 0; i < count; i++)
            measurements[j][i] = UINT64_MAX;
}

/**
 * @struct      analysis_st
 * @brief       Contains all values that are needed to make measurements
 */
typedef struct
{
    distribution_et dist;
    input_st *inputs;
    uint64_t *(*measurements)[ITERATIONS];
    size_t count;
} analysis_st;

/**
 * @fn          write_chars
 * @brief       Write chars to output list.
 * @param       arr            The array of chars.
 * @param       amount         The amount of chars to process.
 */
static void write_chars(const char *arr, size_t amount)
{
    link_buf_st *link;

    if (link_buf == NULL)
        link_buf = new_link();

    link = link_buf;
    while (link->next != NULL)
        link = link->next;

    // This could be done smarter, but the compiler will probably optimize it
    for (size_t i = 0; i < amount; i++)
    {
        if (link->index == LINK_SIZE)
        {
            link->next = new_link();
            link = link->next;
        }
        (link->buffer)[link->index] = arr[i];
        (link->index)++;
    }
}

/**
 * @fn          write_string
 * @brief       Wrapper for write_chars taking zero terminated string and writing to output list.
 * @param       str            The zero terminated string.
 */
static void write_string(const char *str)
{
    write_chars(str, strlen(str));
}

/**
 * @fn          write_data
 * @brief       Process and write the measurements to the output list.
 * @param       filename            The name of the file to write to.
 * @param       measurements        The measurements to write.
 * @param       inputs              The inputs to write.
 * @param       count               The amount of measurements to write.
 * @param       flags               The flags used to compile the program.
 */
static void write_data(const char *filename, const char *flags, const char *fuzz_class, const analysis_st *analysis)
{
    uint64_t min, **measurements = *(analysis->measurements);
    const input_st *inputs = analysis->inputs;
    size_t count = analysis->count;

    char conversion_buffer[100];

    write_string("# FILE: [");
    write_string(filename);
    write_string("]\n");
    write_string("# compile flags: [");
    write_string(flags);
    write_string("], fuzz class: [");
    write_string(fuzz_class);
    write_string("]\n");
    write_string("input_a,input_b,min_clock_measured");
    for (int i = 1; i <= ITERATIONS; i++)
    {
        write_string(",it");
        snprintf(conversion_buffer, sizeof(conversion_buffer), "%d", i);
        write_string(conversion_buffer);
    }
    write_string("\n");

    for (size_t i = 0; i < count; i++)
    {
        snprintf(conversion_buffer, sizeof(conversion_buffer), "%lld,%lld", inputs[i].a, inputs[i].b);
        write_string(conversion_buffer);

        // Find min for given set of inputs
        min = UINT64_MAX;
        for (int j = 0; j < ITERATIONS; j++)
            min = MIN(min, measurements[j][i]);
        snprintf(conversion_buffer, sizeof(conversion_buffer), ",%llu", min);
        write_string(conversion_buffer);

        for (int j = 0; j < ITERATIONS; j++)
        {
            snprintf(conversion_buffer, sizeof(conversion_buffer), ",%llu", measurements[j][i]);
            write_string(conversion_buffer);
        }
        write_string("\n");
    }
}

/**
 * @fn          run
 * @brief       Run measurements according to analysis parameter and save results.
 * @param       analysis            The specifications for the measurement.
 * @param       out_file            The filename to save the results.
 * @param       flags               The flags used to compile the program.
 */
static void run(analysis_st *analysis, const char *out_file, const char *flags, const char *fuzz_class)
{
    generate_inputs(analysis->dist, analysis->inputs, analysis->count);
    initialize_measurements(*(analysis->measurements), analysis->count);
    measure(*(analysis->measurements), analysis->inputs, analysis->count);
    write_data(out_file, flags, fuzz_class, analysis);
}

/**
 * @fn          start
 * @brief       Run all measurements.
 * @param       opt_flags            Optimization flags used to compile the external program.
 */
int start(const char *opt_flags)
{
    analysis_st analysis;

    // Allocate memory for input and measurements
    input_st *inputs = kmalloc(sizeof(*inputs) * fuzz_count, GFP_KERNEL);
    uint64_t *measurements[ITERATIONS];
    for (size_t i = 0; i < ITERATIONS; i++)
        measurements[i] = kmalloc(sizeof(uint64_t) * fuzz_count, GFP_KERNEL);

    analysis = (analysis_st){UNIFORMLY, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-uniform.csv", opt_flags, "uniform");

    analysis = (analysis_st){EQUAL, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-equal.csv", opt_flags, "equal");

    analysis = (analysis_st){ZERO, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-zero.csv", opt_flags, "zero");

    analysis = (analysis_st){MAX64, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-max64.csv", opt_flags, "max64");

    analysis = (analysis_st){UMAX64, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-umax64.csv", opt_flags, "umax64");

    // Free input for memory and measurements
    kfree(inputs);
    for (size_t i = 0; i < ITERATIONS; i++)
        kfree(measurements[i]);

    return 0;
}

/**
 * @fn          proc_status_read
 * @brief       This function handles reads from /proc/optifuzz_status and is called by the kernel.
 */
static ssize_t proc_status_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
    const char *actual_msg;
    char *msg;
    size_t len;
    ssize_t ret = 0;
    actual_msg = (status == RUNNING) ? "running\n" : "done\n";
    len = strlen(actual_msg);

    if (*pos >= len)
        return 0;

    if (count > len - *pos)
        count = len - *pos;

    msg = kmalloc(count, GFP_KERNEL);
    if (!msg)
        return -ENOMEM;

    memcpy(msg, actual_msg + *pos, count);

    if (copy_to_user(buf, msg, count))
        ret = -EFAULT;
    else
        *pos += count;

    kfree(msg);
    return ret ?: count;
}

/**
 * @fn          proc_output_read
 * @brief       This function handles reads from /proc/optifuzz_output and is called by the kernel.
 */
static ssize_t proc_output_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
    link_buf_st *link;
    size_t jumps, start_index, to_read;
    ssize_t ret = 0;
    if (status == RUNNING)
        return 0;

    link = link_buf;

    jumps = *pos / LINK_SIZE;

    for (size_t i = 0; i < jumps; i++)
    {
        if (link == NULL)
            return 0;
        link = link->next;
    }

    if (link == NULL)
        return 0;

    start_index = *pos % LINK_SIZE;
    if (link->index < start_index)
        return 0;

    to_read = MIN(link->index - start_index, count);

    if (copy_to_user(buf, link->buffer + start_index, to_read))
        ret = -EFAULT;
    else
        *pos += to_read;

    return ret ?: to_read;
}

/**
 * @fn          entry
 * @brief       This function is the module entry called when it is mounted in the kernel.
 */
static int __init entry(void)
{
    printk(KERN_INFO "Optifuzz Loaded [%s]\n", opt_flags);
    status = RUNNING;

    proc_status = proc_create(PROC_STATUS_FILENAME, 0, NULL, &proc_status_ops);
    if (!proc_status)
    {
        pr_err("Failed to create proc entry\n");
        return -ENOMEM;
    }

    proc_output = proc_create(PROC_OUTPUT_FILENAME, 0, NULL, &proc_output_ops);
    if (!proc_output)
    {
        pr_err("Failed to create proc entry\n");
        return -ENOMEM;
    }

    start(opt_flags);

    printk(KERN_INFO "Optifuzz Done[%s]\n", opt_flags);
    status = DONE;
    return 0;
}

/**
 * @fn          end
 * @brief       This function is the module exit called when it is removed from the kernel.
 */
static void __exit end(void)
{
    proc_remove(proc_status);
    proc_remove(proc_output);
    free_links();
    printk(KERN_INFO "Optifuzz Unloaded[%s]\n", opt_flags);
}

// Specifying module init and exit functions
module_init(entry);
module_exit(end);
