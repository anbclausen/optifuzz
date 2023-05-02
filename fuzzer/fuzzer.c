#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include <bsd/stdlib.h>
// #include <x86intrin.h>

//#define USE_GCC_RDTSC
#ifdef USE_GCC_RDTSC
/* rdtsc */
extern __inline unsigned long long
    __attribute__((__gnu_inline__, __always_inline__, __artificial__))
    __rdtsc(void)
{
    return __builtin_ia32_rdtsc();
}
#endif

#define MIN(i, j) (((i) < (j)) ? (i) : (j))

extern int seed;
extern volatile int program(int64_t, int64_t);

typedef struct measurement
{
    uint64_t clocks_spent; // Amount of clocks spent on executing
    int64_t fuzz_input_a;  // The input used
    int64_t fuzz_input_b;  // The input used
} measurement_st;

// Mby use clocks from time.h instead
static inline uint64_t rdtsc(void)
{
#ifdef USE_GCC_RDTSC
    return (uint64_t) __rdtsc();
#else
    /*
    unsigned int lo, hi;
    __asm__ __volatile__("rdtsc"
                         : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
    */
    uint32_t lo, hi;
    __asm__ __volatile__(
        "xorl %%eax, %%eax\n"
        "cpuid\n"
        "rdtsc\n"
        : "=a"(lo), "=d"(hi)
        :
        : "%ebx", "%ecx");
    return (uint64_t)hi << 32 | lo;
#endif
}

static uint64_t get_time(int a, int b)
{
    uint64_t get_clocks = rdtsc();
    program(a, b);
    uint64_t diff = rdtsc() - get_clocks;
    return diff;
}

static inline int64_t get_rand(void)
{
    // return rand();
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

/*
static inline void generate_input(input_st *input, size_t amount) {
    for (size_t i = 0; i < amount; i++)
        input[i] = (input_st) {get_rand(), get_rand()};
}
*/

static void measure(measurement_st *measurements, size_t count, size_t retries)
{
    uint64_t get_clocks, diff;

    // input_st input[count];
    // generate_input(input, count);

    size_t initial_min = 0;
    for (size_t i = 0; i < count; i++)
    {
        int time = get_time(0, 0); // just a baseline
        int64_t a = get_rand();
        int64_t b = get_rand();
        measurements[i] = (measurement_st){time, a, b};
        initial_min = MIN(initial_min, time);
    }

    for (size_t j = 0; j < retries; j++)
    {
        for (size_t i = 0; i < count; i++)
        {
            if (measurements[i].clocks_spent <= initial_min + initial_min / 8)
                continue;

            int a = measurements[i].fuzz_input_a;
            int b = measurements[i].fuzz_input_b;

            uint64_t min = get_time(a, b);

            if (min < 0)
            {
                // TODO if rdtsc resets
                i--;
                continue;
                // This is a little naughty, but it might just do the trick..
            }
            min = MIN(measurements[i].clocks_spent, min);
            measurements[i].clocks_spent = min;
        }
        fprintf(stdout, "\rRetry %ld/%ld..", j + 1, retries);
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
    // Seed from time (used for fuzzing)
    // unsigned int fuzz_seed = time(NULL);
    // srand(fuzz_seed);

    // Amount of random inputs to the program
    size_t fuzz_count = atoi(argv[1]);
    const char *opt_flags = argv[2];

    // Allocate space for measurements and start fuzzing
    measurement_st *measurements = malloc(sizeof(*measurements) * fuzz_count);
    measure(measurements, fuzz_count, 100);

    write_data("./result.csv", measurements, fuzz_count, opt_flags);

    free(measurements);

    return 0;
}
