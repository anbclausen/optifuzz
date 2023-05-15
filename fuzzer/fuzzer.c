#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include <bsd/stdlib.h>

#define MIN(x, y) ((x < y) ? (x) : (y))
#define RAND64(x) arc4random_buf(x, sizeof(int64_t))
#define RAND8(x) arc4random_buf(x, sizeof(int8_t))

#define RANDOM (arc4random() > UINT32_MAX / 2)

#define REPEATS 100   /** The amount of times the program \
                       *  is run to get a more accurate measurement. */
#define ITERATIONS 10 /** The amount of times to cycle through all  \
                       *  fuzz inputs to lower noise from other CPU \
                       *  tasks. */

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
    ALTB,      // Uniformly random but a < b
    BLTA,      // Uniformly random but b < a
    SMALL,     // Uniformly random but small values
} distribution_et;

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
    case ALTB:
        RAND64(a);
        RAND64(b);
        if (*a > *b)
        {
            int64_t tmp = *a;
            *a = *b;
            *b = tmp;
        }
        break;
    case BLTA:
        RAND64(a);
        RAND64(b);
        if (*a < *b)
        {
            int64_t tmp = *a;
            *a = *b;
            *b = tmp;
        }
        break;
    case SMALL:
        RAND8(a);
        RAND8(b);
        break;
    default:
        fprintf(stderr, "Distribution not yet supported!");
        exit(1);
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
 * @fn          write_data
 * @brief       Write the measurements to a file.
 * @param       filename            The name of the file to write to.
 * @param       measurements        The measurements to write.
 * @param       inputs              The inputs to write.
 * @param       count               The amount of measurements to write.
 * @param       flags               The flags used to compile the program.
 * @param       fuzz_class          The class of fuzzing input.
 */
static void write_data(const char *filename, const char *flags, const char *fuzz_class, const analysis_st *analysis)
{
    uint64_t **measurements = *(analysis->measurements);
    const input_st *inputs = analysis->inputs;
    size_t count = analysis->count;

    FILE *fs = fopen(filename, "w");
    if (fs == NULL)
    {
        fprintf(stderr, "Error when opening file\n");
        exit(EXIT_FAILURE);
    }

    fprintf(fs, "# compile flags: [%s], fuzz class: [%s]\n", flags, fuzz_class);
    fprintf(fs, "input_a,input_b,min_clock_measured");
    for (int i = 1; i <= ITERATIONS; i++)
        fprintf(fs, ",it%d", i);
    fprintf(fs, "\n");

    for (size_t i = 0; i < count; i++)
    {
        fprintf(fs, "%ld,%ld", inputs[i].a, inputs[i].b);

        // Find min for given set of inputs
        uint64_t min = UINT64_MAX;
        for (int j = 0; j < ITERATIONS; j++)
            min = MIN(min, measurements[j][i]);
        fprintf(fs, ",%lu", min);

        for (int j = 0; j < ITERATIONS; j++)
            fprintf(fs, ",%lu", measurements[j][i]);
        fprintf(fs, "\n");
    }

    fclose(fs);
}

/**
 * @fn          run
 * @brief       Run measurements according to analysis parameter and save results.
 * @param       analysis            The specifications for the measurement.
 * @param       out_file            The filename to save the results.
 * @param       flags               The flags used to compile the program.
 * @param       fuzz_class          The class of fuzzing input.
 */
static void run(analysis_st *analysis, const char *out_file, const char *flags, const char *fuzz_class)
{
    generate_inputs(analysis->dist, analysis->inputs, analysis->count);
    initialize_measurements(*(analysis->measurements), analysis->count);
    measure(*(analysis->measurements), analysis->inputs, analysis->count);
    write_data(out_file, flags, fuzz_class, analysis);
}

int main(int argc, char const *argv[])
{
    if (argc != 3)
    {
        fprintf(stderr, "usage: %s #data-points flag", argv[0]);
        return 1;
    }

    size_t fuzz_count = atoi(argv[1]);
    const char *opt_flags = argv[2];

    // Allocate memory for input and measurements
    input_st *inputs = malloc(sizeof(*inputs) * fuzz_count);
    uint64_t *measurements[ITERATIONS];
    for (size_t i = 0; i < ITERATIONS; i++)
        measurements[i] = malloc(sizeof(uint64_t) * fuzz_count);

    analysis_st analysis;
    
    analysis = (analysis_st) {UNIFORMLY, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-uniform.csv", opt_flags, "uniform");

    analysis = (analysis_st) {EQUAL, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-equal.csv", opt_flags, "equal");

    analysis = (analysis_st) {ZERO, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-zero.csv", opt_flags, "zero");

    analysis = (analysis_st) {MAX64, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-max64.csv", opt_flags, "max64");

    analysis = (analysis_st) {UMAX64, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-umax64.csv", opt_flags, "umax64");

    analysis = (analysis_st) {ALTB, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-xlty.csv", opt_flags, "xlty");

    analysis = (analysis_st) {BLTA, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-yltx.csv", opt_flags, "yltx");

    analysis = (analysis_st) {SMALL, inputs, &measurements, fuzz_count};
    run(&analysis, "./result-small.csv", opt_flags, "small");

    // Free input for memory and measurements
    free(inputs);
    for (size_t i = 0; i < ITERATIONS; i++)
        free(measurements[i]);

    return 0;
}
