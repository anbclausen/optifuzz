#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/sched.h>
#include <linux/proc_fs.h>
#include <linux/string.h>
#include <linux/moduleparam.h>

// Compile fuzzer_core in kernel compatability mode
#ifndef KERNEL_MODE
#define KERNEL_MODE
#endif
#include "../fuzzer_core.h"

MODULE_LICENSE("Dual BSD/GPL");
MODULE_DESCRIPTION("OptiFuzz running in kernel space");

// Kernel parameters
static size_t count = 10000;
static char flag[10];
static char classes[200];

// Registering kernel parameters
module_param_named(count, count, long, 0644);
module_param_string(flag, flag, 10, 0644);
module_param_string(classes, classes, 200, 0644);

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
 * @fn          start
 * @brief       Run all measurements.
 * @return      Returns 0 on success.
 */
int start(void)
{
    analysis_st analysis;
    const char *dist_str, *filename;

    if (parse_and_enqueue_classes(classes))
    {
        printk(KERN_INFO "Could not parse fuzz classes!\n");
        return -ENOMEM;
    }

    // Allocate memory for input and measurements
    initialize_analysis(&analysis, count);

    // Fuzz all classes in queue
    while (!dist_queue_empty())
    {
        if (run_next(&analysis))
        {
            printk(KERN_INFO "Fuzz run failed!\n");
            return -ENOMEM;
        }
        dist_str = dist_to_string(analysis.dist);
        filename = construct_filename(dist_str);
        write_data(filename, flag, dist_str, &analysis);
    }

    destroy_analysis(&analysis);

    return 0;
}

/**
 * @fn          entry
 * @brief       This function is the module entry called when it is mounted in the kernel.
 */
static int __init entry(void)
{
    int ret = 0;
    printk(KERN_INFO "OptiFuzz Loaded [%s]\n", flag);
    status = RUNNING;

    proc_status = proc_create(PROC_STATUS_FILENAME, 0, NULL, &proc_status_ops);
    if (!proc_status)
    {
        pr_err("Failed to create proc entry\n");
        return -ENOMEM;
    }

    ret = start();

    proc_output = proc_create(PROC_OUTPUT_FILENAME, 0, NULL, &proc_output_ops);
    if (!proc_output)
    {
        pr_err("Failed to create proc entry\n");
        return -ENOMEM;
    }

    printk(KERN_INFO "OptiFuzz Done[%s]\n", flag);
    status = DONE;
    return ret;
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
    printk(KERN_INFO "OptiFuzz Unloaded[%s]\n", flag);
}

// Specifying module init and exit functions
module_init(entry);
module_exit(end);
