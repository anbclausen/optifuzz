#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include <bsd/stdlib.h>

#define MIN(x, y) (((x) < (y)) ? (x) : (y))

#define REPEATS 100

extern int program(int64_t, int64_t);

typedef struct measurement
{
    uint64_t clocks_spent; // Amount of clocks spent on executing
    int64_t fuzz_input_a;  // The input used
    int64_t fuzz_input_b;  // The input used
} measurement_st;

static inline uint64_t get_time(int64_t a, int64_t b)
{
    /*
     * NOTE: The best way to measure time according to INTEL (well, should be in kernel space)
     * NOTE: section 3.2.1: https://www.intel.de/content/dam/www/public/us/en/documents/white-papers/ia-32-ia-64-benchmark-code-execution-paper.pdf
     */

    unsigned cycles_low, cycles_high, cycles_low1, cycles_high1;
    uint64_t start, end;

    asm volatile("CPUID\n\t"                                                             // Force prev instructions to complete before RDTSC bellow is executed (Serializing instruction execution)
                 "RDTSC\n\t"                                                             // Get clock
                 "mov %%edx, %0\n\t"                                                     // %0 is cycles_high
                 "mov %%eax, %1\n\t"                                                     // %1 is cycles_low
                 : "=r"(cycles_high), "=r"(cycles_low)::"%rax", "%rbx", "%rcx", "%rdx"); // Restore clobbered registers

    // NOTE: This is done to combat too fast execution of the program
    for (size_t i = 0; i < REPEATS; i++)
    {
        program(a, b);
    }
    // program(a,b);

    asm volatile("RDTSCP\n\t"                                                              // Force to wait for all prev instructions before reading counter. (subsequent instructions may begin execution before the read)
                 "mov %%edx, %0\n\t"                                                       // Depends on values from RDTSCP, so executed after
                 "mov %%eax, %1\n\t"                                                       // Executed after RDTSCP
                 "CPUID\n\t"                                                               // Ensure that the RDTSCP read before any other execution takes place
                 : "=r"(cycles_high1), "=r"(cycles_low1)::"%rax", "%rbx", "%rcx", "%rdx"); // Restore clobbered registers

    start = (((uint64_t)cycles_high << 32) | cycles_low);
    end = (((uint64_t)cycles_high1 << 32) | cycles_low1);

    return end - start;
}

static inline int64_t get_rand(void)
{
    int64_t r;
    arc4random_buf(&r, sizeof(int64_t));
    return r;
}

static void measure(measurement_st *measurements, size_t count, size_t iterations)
{
    int64_t a, b;
    uint64_t time, min, old_min, initial_min = 0;

    // Single initial run through
    for (size_t i = 0; i < count; i++)
    {
        time = get_time(0, 0); // just a baseline
        a = get_rand();
        b = get_rand();
        measurements[i] = (measurement_st){time, a, b};
        initial_min = MIN(initial_min, time);
    }

    // Complete run through
    for (size_t j = 1; j < iterations; j++)
    {
        for (size_t i = 0; i < count; i++)
        {
            // If the measured speed is no more than 10% above initial minimum, then we roll with it to save time.
            // TODO: this does not seem to have any effect.
            if (measurements[i].clocks_spent <= initial_min + initial_min / 10)
                continue;

            a = measurements[i].fuzz_input_a;
            b = measurements[i].fuzz_input_b;
            min = get_time(a, b);

            // NOTE: min is unsigned. we cannot detect if the counter overflows by checking negative. should be fine

            old_min = measurements[i].clocks_spent;
            measurements[i].clocks_spent = MIN(old_min, min);
        }
        fprintf(stdout, "\rIteration %ld/%ld..", j + 1, iterations);
        fflush(stdout);
    }

    fprintf(stdout, " Done!\n");
}

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

    // Amount of random inputs to the program
    size_t fuzz_count = atoi(argv[1]);
    const char *opt_flags = argv[2];

    // Allocate space for measurements and start fuzzing
    measurement_st *measurements = malloc(sizeof(*measurements) * fuzz_count);

    measure(measurements, fuzz_count, 10);

    write_data("./result.csv", measurements, fuzz_count, opt_flags);

    free(measurements);

    return 0;
}
