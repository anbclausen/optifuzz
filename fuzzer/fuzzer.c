#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include <bsd/stdlib.h>

// #include <linux/preempt.h> // TODO:

#define MIN(x, y) (((x) < (y)) ? (x) : (y))

// #define USE_GCC_RDTSC

#ifdef USE_GCC_RDTSC
#include <x86intrin.h>
#define rdtsc_cycles() ((uint64_t)__rdtsc());
#else
/*
 * https://en.wikipedia.org/wiki/Time_Stamp_Counter
 */
static inline uint64_t rdtsc_cycles(void)
{
    uint32_t lo, hi;
    __asm__ __volatile__(
        //"xorl %%eax, %%eax\n" // i don't think there is any need for this
        "cpuid\n" // fuck, it also fucks up "%rbx", "%rcx", "%rax", "%rcx"
        "rdtsc\n"
        : "=a"(lo), "=d"(hi)
        :
        : "%rbx", "%rcx");
    return (uint64_t)hi << 32 | lo;
}
#endif

extern int seed;
extern int program(int64_t, int64_t);

typedef struct measurement
{
    uint64_t clocks_spent; // Amount of clocks spent on executing
    int64_t fuzz_input_a;  // The input used
    int64_t fuzz_input_b;  // The input used
} measurement_st;

static inline uint64_t get_time(int a, int b)
{
    
    uint64_t clock_cycles = rdtsc_cycles();
    program(a, b);
    uint64_t diff = rdtsc_cycles() - clock_cycles;
    return diff;

    // NOTE: The best way according to INTEL
    // NOTE: page 16: https://www.intel.de/content/dam/www/public/us/en/documents/white-papers/ia-32-ia-64-benchmark-code-execution-paper.pdf
    /*
    unsigned cycles_low, cycles_high, cycles_low1, cycles_high1;
    uint64_t start, end;
    
    asm volatile("CPUID\n\t"
                 "RDTSC\n\t"
                 "mov %%edx, %0\n\t"
                 "mov %%eax, %1\n\t"
                 : "=r"(cycles_high), "=r"(cycles_low)::"%rax", "%rbx", "%rcx", "%rdx");
    /***********************************/
    /*call the function to measure here*/
    program(a,b);
    /***********************************/
    asm volatile("RDTSCP\n\t"
                 "mov %%edx, %0\n\t"
                 "mov %%eax, %1\n\t"
                 "CPUID\n\t"
                 : "=r"(cycles_high1), "=r"(cycles_low1)::"%rax", "%rbx", "%rcx", "%rdx");
    
    start = (((uint64_t)cycles_high << 32) | cycles_low);
    end = (((uint64_t)cycles_high1 << 32) | cycles_low1);

    return end - start;
    */
}

static inline int64_t get_rand(void)
{
    // return (int64_t) arc4random();
    int64_t r;
    arc4random_buf(&r, sizeof(int64_t));
    return r;
}

typedef struct
{
    int64_t a;
    int64_t b;
} input_st;

static void measure(measurement_st *measurements, size_t count, size_t iterations)
{
    uint64_t get_clocks, diff;

    // Single initial run through
    size_t initial_min = 0;
    for (size_t i = 0; i < count; i++)
    {
        int time = get_time(0, 0); // just a baseline
        int64_t a = get_rand();
        int64_t b = get_rand();
        measurements[i] = (measurement_st){time, a, b};
        initial_min = MIN(initial_min, time);
    }

    // Complete run through
    for (size_t j = 0; j < iterations; j++)
    {
        for (size_t i = 0; i < count; i++)
        {
            if (measurements[i].clocks_spent <= initial_min + initial_min / 8)
                continue;

            int a = measurements[i].fuzz_input_a;
            int b = measurements[i].fuzz_input_b;

            uint64_t min = get_time(a, b);

            // NOTE: min is unsigned. we cannot detect if the counter overflows by checking negative. should be fine

            min = MIN(measurements[i].clocks_spent, min);
            measurements[i].clocks_spent = min;
        }
        fprintf(stdout, "\rIteration %ld/%ld..", j + 1, iterations);
        fflush(stdout);
    }

    fprintf(stdout, "\n");
}

static void write_data(const char *filename, const measurement_st *measurements, size_t count, const char *flags)
{
    FILE *fs = fopen(filename, "w");
    if (fs == NULL)
    {
        printf("ERROR: File\n");
        exit(EXIT_FAILURE);
    }

    fprintf(fs, "# prog seed: [%d] compile flags: [%s]\n", seed, flags);
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
        fprintf(stderr, "supply input amount and compile flags");
        return 1;
    }
    // Amount of random inputs to the program
    size_t fuzz_count = atoi(argv[1]);
    const char *opt_flags = argv[2];

    // Allocate space for measurements and start fuzzing
    measurement_st *measurements = malloc(sizeof(*measurements) * fuzz_count);

    // TODO: preempt_disable(); /*we disable preemption on our CPU*/
    // TODO: raw_local_irq_save(flags); /*we disable hard interrupts on our CPU*/
    // TODO: raw_local_irq_restore(flags);
    // TODO: preempt_enable();

    measure(measurements, fuzz_count, 100);

    write_data("./result.csv", measurements, fuzz_count, opt_flags);

    free(measurements);

    return 0;
}
