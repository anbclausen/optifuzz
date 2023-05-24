#include "fuzzer_core.h"

#define FORMAT_BUF_SIZE 50

#ifdef KERNEL_MODE
#include <linux/random.h>
#include <linux/slab.h>
#include <linux/irqflags.h>
#include <linux/preempt.h>
#define RANDOM_BUF get_random_bytes
#define RANDOM_U32 get_random_u32
#define malloc(size) kmalloc(size, GFP_KERNEL)
#define calloc(nmamb, size) kcalloc(nmamb, size, GFP_KERNEL)
#define free(ptr) kfree(ptr)
#else
#include <bsd/stdlib.h>
#include <string.h>
#define RANDOM_BUF arc4random_buf
#define RANDOM_U32 arc4random
#endif

#define RAND64(x) RANDOM_BUF(x, sizeof(int64_t))
#define RAND8(x) RANDOM_BUF(x, sizeof(int8_t))
#define RANDOM (RANDOM_U32() > UINT32_MAX / 2)
#define SWAP(x, y, type) \
    {                    \
        type tmp = *x;   \
        *x = *y;         \
        *y = tmp;        \
    }
#define RANDXLTY(x, y)           \
    {                            \
        RAND64(x);               \
        RAND64(y);               \
        if (*x > *y)             \
            SWAP(x, y, int64_t); \
    }

// Array of all diststibutions and their string names
static const distribution_et dists[DIST_COUNT] = {UNIFORMLY, EQUAL, MAX64, UMAX64, ZERO, XLTY, YLTX, SMALL};
#define MAX_DIST_STR_LEN 10
static const char dists_strings[DIST_COUNT][MAX_DIST_STR_LEN] = {"uniform", "equal", "max64", "umax64", "zero", "xlty", "yltx", "small"};

// FILO queue (stack) for distributions to fuzz
#define MAX_DIST_QUEUE_SIZE 20
static distribution_et dist_queue[MAX_DIST_QUEUE_SIZE];
static distribution_et *dist_queue_head = dist_queue;

/**
 * @fn          set_values
 * @brief       Set values for input according to distribution.
 * @param       dist                The name of the file to write to.
 * @param       x                   The input value a.
 * @param       y                   The input value b.
 * @return      Returns 0 on success.
 */
static int set_values(distribution_et dist, int64_t *x, int64_t *y)
{
    switch (dist)
    {
    case UNIFORMLY:
        RAND64(x);
        RAND64(y);
        break;
    case EQUAL:
        RAND64(x);
        *y = *x;
        break;
    case MAX64:
        *x = *y = INT64_MAX;
        if (RANDOM)
            RAND64(x);
        else
            RAND64(y);
        break;
    case UMAX64:
        *x = *y = -1;
        if (RANDOM)
            RAND64(x);
        else
            RAND64(y);
        break;
    case ZERO:
        *x = *y = 0;
        if (RANDOM)
            RAND64(x);
        else
            RAND64(y);
        break;
    case XLTY:
        RANDXLTY(x, y);
        break;
    case YLTX:
        RANDXLTY(y, x);
        break;
    case SMALL:
        RAND8(x);
        RAND8(y);
        // Clear all but lower byte
        *x &= 255;
        *y &= 255;
        break;
    default:
        print_error("Distribution not yet supported!\n");
        return 1;
    }
    return 0;
}

/**
 * @fn          generate_inputs
 * @brief       Generate and set all input values.
 * @param       dist                The distribution to draw the inputs from.
 * @param       inputs              the list to write them to.
 * @param       count               The amount of measurements to write.
 * @return      Returns 0 on success.
 */
static int generate_inputs(distribution_et dist, input_st *inputs, size_t count)
{
    int ret = 0;
    for (size_t i = 0; i < count; i++)
        ret |= set_values(dist, &inputs[i].a, &inputs[i].b);
    return ret;
}

/**
 * @fn          initialize_measurements
 * @brief       Set initial value of measurements to UINT64_MAX.
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
 * @fn          get_time
 * @brief       Get the time it takes to execute the program with the given inputs.
 * @details     This function is a wrapper around the RDTSC instruction.
 *              It uses CPUID (and RDTSCP) to serialize instructions to avoid out
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

#ifdef KERNEL_MODE
    unsigned long flags;
    // Disables hard interrupts on the local CPU
    local_irq_save(flags);
    // Disables preemption (essentially context switches)
    preempt_disable();
#endif

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

#ifdef KERNEL_MODE
    // Reenables preemption
    preempt_enable();
    // Reenables interupts
    raw_local_irq_restore(flags);
#endif

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
 * @fn          dist_to_string
 * @brief       Converts an element of distribution_et type to its string representation.
 * @param       dist                The name of the file to write to.
 * @return      The string representation or NULL if bad distribution.
 */
const char *dist_to_string(distribution_et dist)
{
    for (size_t i = 0; i < DIST_COUNT; i++)
        if (dist == dists[i])
            return dists_strings[i];
    return NULL;
}

/**
 * @fn          string_to_dist
 * @brief       Converts a string to its distribution_et type.
 * @param       str                 A zero terminated string.
 * @return      A distribution or INVALID when no match found.
 */
static distribution_et string_to_dist(const char *str)
{
    for (size_t i = 0; i < DIST_COUNT; i++)
        if (strncmp(str, dists_strings[i], MAX_DIST_STR_LEN) == 0)
            return dists[i];
    return INVALID;
}

/**
 * @fn          dist_queue_full
 * @brief       Check if the queue is full.
 * @return      1 if full and 0 otherwize.
 */
static int dist_queue_full(void)
{
    return dist_queue_head == dist_queue + MAX_DIST_QUEUE_SIZE;
}

/**
 * @fn          dist_queue_empty
 * @brief       Check if the queue is empty.
 * @return      1 if empty and 0 otherwize.
 */
int dist_queue_empty(void)
{
    return dist_queue_head == dist_queue;
}

static int dist_enqueue(distribution_et dist)
{
    // Check if full
    if (dist_queue_full())
        return 1;

    *dist_queue_head = dist;
    dist_queue_head++;
    return 0;
}

/**
 * @fn          dist_dequeue
 * @brief       Dequeues (pop) next element from queue.
 * @return      Next distribution in queue or INVALID when queue is empty.
 */
static distribution_et dist_dequeue(void)
{
    if (dist_queue_empty())
        return INVALID;

    dist_queue_head--;
    return *dist_queue_head;
}

/**
 * @fn          parse_and_enqueue_classes
 * @brief       Parses a string of space seperated distribution names and enqueues them for fuzzing.
 * @param       str                 A zero terminated string with space seperated distributions.
 * @return      Returns 0 on success.
 */
int parse_and_enqueue_classes(const char *str)
{
    char class[MAX_DIST_STR_LEN];
    char *class_ptr;
    const char *str_ptr;
    distribution_et dist;

    str_ptr = str;
    class_ptr = class;

    // Empty string
    if (*str == '\0')
        return 1;

    do
    {
        // Fast forward to first non-space char
        while (*str_ptr == ' ')
            str_ptr++;

        // Copy next word
        while (*str_ptr != ' ' && *str_ptr != '\0')
        {
            *class_ptr = *str_ptr;
            class_ptr++;
            str_ptr++;
        }

        // If anything was copied
        if (class_ptr != class)
        {
            *class_ptr = '\0';

            // Convert to distribution
            dist = string_to_dist(class);
            if (dist == INVALID)
                return 1;
            // Enqueue distribution
            if (dist_enqueue(dist))
                return 1;

            class_ptr = class;
        }
    } while (*str_ptr != '\0');

    return 0;
}

/**
 * @fn          run_single
 * @brief       Run measurements according to analysis parameter and save results.
 * @param       analysis            The specifications for the measurement.
 * @return      Returns 0 on success.
 */
static int run_single(analysis_st *analysis)
{
    if (generate_inputs(analysis->dist, analysis->inputs, analysis->count))
        return 1;
    initialize_measurements(*(analysis->measurements), analysis->count);
    measure(*(analysis->measurements), analysis->inputs, analysis->count);
    return 0;
}

/**
 * @fn          run_next
 * @brief       Run measurements using the next distribution in queue.
 * @param       analysis            The specifications for the measurement. Contains the results.
 * @return      Returns 0 on success.
 */
int run_next(analysis_st *analysis)
{
    if (dist_queue_empty())
        return 1;

    analysis->dist = dist_dequeue();
    if (analysis->dist == INVALID)
        return 1;

    if (run_single(analysis))
        return 1;

    return 0;
}

/**
 * @fn          initialize_analysis
 * @brief       Alocates memory and initializes an analysis_st struct.
 * @param       analysis            The anaylis to be initialized.
 * @param       count               The amount of measurements to get.
 * @return      Returns 0 on success.
 */
int initialize_analysis(analysis_st *analysis, size_t count)
{
    // Allocate memory for input and measurements
    input_st *inputs = calloc(count, sizeof(input_st));
    if (inputs == NULL)
        return 1;
    uint64_t *(*measurements)[ITERATIONS] = calloc(ITERATIONS, sizeof(uint64_t *));
    if (measurements == NULL)
        return 1;
    for (size_t i = 0; i < ITERATIONS; i++)
    {
        (*measurements)[i] = calloc(count, sizeof(uint64_t));
        if ((*measurements)[i] == NULL)
            return 1;
    }

    // Default dist to UNIFORMLY
    analysis->dist = UNIFORMLY;
    analysis->inputs = inputs;
    analysis->measurements = (uint64_t * (*)[ITERATIONS]) measurements;
    analysis->count = count;
    return 0;
}

/**
 * @fn          destroy_analysis
 * @brief       Frees all memory used by analysis_st struct element.
 * @details     This function should only be used on already initialized
 *              analysis_st struct elements.
 * @param       analysis            The anaylis to be initialized.
 * @param       count               The amount of measurements to get.
 */
void destroy_analysis(analysis_st *analysis)
{
    // Free input for memory and measurements
    free(analysis->inputs);
    for (size_t i = 0; i < ITERATIONS; i++)
        free((*(analysis->measurements))[i]);
    free(*(analysis->measurements));
}

/**
 * @fn          construct_filename
 * @brief       Creates a filename for the given distribution string.
 * @details     Aditional calls to this function will overwrite the last
 *              returned string.
 * @param       dist_str            String represenation of the distribution.
 */
const char *construct_filename(const char *dist_str)
{
    static char format_buf[FORMAT_BUF_SIZE];

    memset(format_buf, '\0', FORMAT_BUF_SIZE);
    snprintf(format_buf, FORMAT_BUF_SIZE, "./result-%s.csv", dist_str);
    return format_buf;
}
