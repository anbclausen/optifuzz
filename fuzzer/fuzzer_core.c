#include "fuzzer_core.h"

#define FORMAT_BUF_SIZE 50

#ifdef KERNEL_MODE
#include <linux/random.h>
#include <linux/slab.h>
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

#define RANDXLTY(x, y)    \
    RAND64(x);            \
    RAND64(y);            \
    if (*x > *y)          \
    {                     \
        int64_t tmp = *x; \
        *x = *y;          \
        *y = tmp;         \
    }

// Array of all dists
static const distribution_et dists[DIST_COUNT] = {UNIFORMLY, EQUAL, MAX64, UMAX64, ZERO, XLTY, YLTX, SMALL};

/**
 * @fn          get_dist
 * @brief       Gets the distribution type from its index.
 * @param       index               The index.
 */
distribution_et get_dist(size_t index)
{
    return dists[index];
}

/**
 * @fn          set_values
 * @brief       Set values for input according to distribution.
 * @param       dist                The name of the file to write to.
 * @param       x                   The input value a.
 * @param       y                   The input value b.
 */
static void set_values(distribution_et dist, int64_t *x, int64_t *y)
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
        error_exit("Distribution not yet supported!\n"); // TODO - kernel mode...
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
    {
        program(a, b);
    }

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
char *dist_to_string(distribution_et dist)
{
    switch (dist)
    {
    case UNIFORMLY:
        return "uniform";
    case EQUAL:
        return "equal";
    case MAX64:
        return "max64";
    case UMAX64:
        return "umax64";
    case ZERO:
        return "zero";
    case XLTY:
        return "xlty";
    case YLTX:
        return "yltx";
    case SMALL:
        return "small";
    default:
        return NULL;
    }
}

/**
 * @fn          run
 * @brief       Run measurements according to analysis parameter and save results.
 * @param       analysis            The specifications for the measurement.
 */
void run(analysis_st *analysis)
{
    generate_inputs(analysis->dist, analysis->inputs, analysis->count);
    initialize_measurements(*(analysis->measurements), analysis->count);
    measure(*(analysis->measurements), analysis->inputs, analysis->count);
}

/**
 * @fn          initialize_analysis
 * @brief       Alocates memory and initializes an analysis_st struct.
 * @param       analysis            The anaylis to be initialized.
 * @param       count               The amount of measurements to get.
 */
void initialize_analysis(analysis_st *analysis, size_t count)
{
    // Allocate memory for input and measurements
    input_st *inputs = calloc(count, sizeof(input_st));
    uint64_t *(*measurements)[ITERATIONS] = calloc(ITERATIONS, sizeof(uint64_t *));
    for (size_t i = 0; i < ITERATIONS; i++)
        (*measurements)[i] = calloc(count, sizeof(uint64_t));

    // Default dist to UNIFORMLY
    analysis->dist = UNIFORMLY;
    analysis->inputs = inputs;
    analysis->measurements = (uint64_t * (*)[ITERATIONS]) measurements;
    analysis->count = count;
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
