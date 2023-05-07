#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include <bsd/stdlib.h>

#define MIN(x, y) ((x < y) ? (x) : (y))
#define RAND64(x) arc4random_buf(x, sizeof(int64_t))

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
    MAX64A,    // a is INT64_MAX, b uniform random
    MAX64B,    // b is INT64_MAX, a uniform random
    ZEROA,     // a is 0, b is uniform random
    ZEROB,     // b is 0, a is uniform random
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
    case MAX64A:
        *a = INT64_MAX;
        RAND64(b);
        break;
    case MAX64B:
        RAND64(a);
        *b = INT64_MAX;
        break;
    case ZEROA:
        *a = 0;
        RAND64(b);
        break;
    case ZEROB:
        *b = 0;
        RAND64(a);
        break;

    default:
        fprintf(stderr, "Distribution not yet supported!");
        exit(1);
        break;
    }
}

/**
 * @struct      measurement_st
 * @brief       A measurement of the execution time of the program.
 */
typedef struct measurement
{
    uint64_t clocks_spent; /** The amount of clocks spent on executing. */
    int64_t fuzz_input_a;  /** The first input.                         */
    int64_t fuzz_input_b;  /** The second input.                        */
} measurement_st;

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
 * @param       count               The amount of measurements to take.
 */
static void measure(measurement_st *measurements, size_t count)
{
    int64_t a, b;
    uint64_t min, old_min;

    for (size_t j = 0; j < ITERATIONS; j++)
    {
        for (size_t i = 0; i < count; i++)
        {
            a = measurements[i].fuzz_input_a;
            b = measurements[i].fuzz_input_b;
            min = get_time(a, b);

            old_min = measurements[i].clocks_spent;
            measurements[i].clocks_spent = MIN(old_min, min);
        }
    }
}

/**
 * @fn          instantiate_measurements
 * @brief       Generate and set all initial values for measurements struct.
 * @param       dist                The name of the file to write to.
 * @param       measurements        The measurements to write.
 * @param       count               The amount of measurements to write.
 */
static void instantiate_measurements(distribution_et dist, measurement_st *measurements, size_t count)
{
    // Optimizer, plz do your thing here :)
    int64_t a, b;
    for (size_t i = 0; i < count; i++)
    {
        set_values(UNIFORMLY, &a, &b);
        measurements[i] = (measurement_st){INT64_MAX, a, b};
    }
}

/**
 * @fn          write_data
 * @brief       Write the measurements to a file.
 * @param       filename            The name of the file to write to.
 * @param       measurements        The measurements to write.
 * @param       count               The amount of measurements to write.
 * @param       flags               The flags used to compile the program.
 */
static void write_data(const char *filename, const measurement_st *measurements, size_t count, const char *flags)
{
    FILE *fs = fopen(filename, "w");
    if (fs == NULL)
    {
        fprintf(stderr, "Error when opening file\n");
        exit(EXIT_FAILURE);
    }

    fprintf(fs, "# compile flags: [%s]\n", flags);
    fprintf(fs, "input_a,input_b,clock_cycles\n");
    for (size_t i = 0; i < count; i++)
    {
        fprintf(fs, "%ld,%ld,%lu\n",
                measurements[i].fuzz_input_a,
                measurements[i].fuzz_input_b,
                measurements[i].clocks_spent);
    }

    fclose(fs);
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

    measurement_st *measurements = malloc(sizeof(*measurements) * fuzz_count);

    instantiate_measurements(UNIFORMLY, measurements, fuzz_count);
    measure(measurements, fuzz_count);
    write_data("./result.csv", measurements, fuzz_count, opt_flags);

    /*
    instantiate_measurements(EQUAL, measurements, fuzz_count);
    measure(measurements, fuzz_count);
    write_data("./result-equal.csv", measurements, fuzz_count, opt_flags);
    */

    free(measurements);

    return 0;
}
