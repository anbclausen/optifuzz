#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>

extern int seed;
extern int program(int, int);



static uint64_t rdtsc(void) {
    unsigned int lo,hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((uint64_t)hi << 32) | lo;
}

static void measure(uint64_t *measurements, size_t count) {
    int x, y;
    uint64_t get_clocks, diff;
   
    for (size_t i = 0; i < count; i++) {
        x = rand();
        y = rand();
        get_clocks = rdtsc();
        program(x, y);
        diff = get_clocks - rdtsc();
        
        if (diff < 0) {
            // TODO - Karl
        }

        measurements[i] = diff;
    }
    
}


int main(int argc, char const *argv[]) {
    // Seed from time. It is not crypto, it is okay.
    unsigned int fuzz_seed = time(NULL);
    srand(fuzz_seed);

    uint64_t *measurements = (uint64_t *) malloc(sizeof(*measurements)*1000);
    
    int result = program(42, 1337);
    printf("%d\n", result);

    return 0;
}
