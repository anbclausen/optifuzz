#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>

#include "fuzzer_core.h"

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
        error_exit("Error when opening file\n");

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

int main(int argc, char const *argv[])
{
    analysis_st analysis;
    const char *dist_str, *opt_flags;
    const size_t buf_size = 50;
    char format_buf[buf_size];
    size_t count;
    distribution_et dist;

    if (argc != 3)
    {
        fprintf(stderr, "usage: %s #data-points flag", argv[0]);
        return 1;
    }

    count = atoi(argv[1]);
    opt_flags = argv[2];

    initialize_analysis(&analysis, count);

    for (size_t i = 0; i < DIST_COUNT; i++)
    {
        dist = get_dist(i);
        analysis.dist = dist;
        run(&analysis);

        dist_str = dist_to_string(dist);
        if (dist_str == NULL)
            error_exit("Could not convert distribution with index \"%ld\" to string!\n", i);

        memset(format_buf, '\0', sizeof(format_buf));
        snprintf(format_buf, buf_size, "./result-%s.csv", dist_str);
        write_data(format_buf, opt_flags, dist_str, &analysis);
    }

    destroy_analysis(&analysis);

    return 0;
}
