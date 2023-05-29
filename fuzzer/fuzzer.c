#include <stdlib.h>
#include <stdio.h>
#include <limits.h>

#include "fuzzer_core.h"

/**
 * @fn          write_data
 * @brief       Write the measurements to a file.
 * @param       analysis            The analysis struct containing the measurements.
 * @param       dists               The distributions used to generate the inputs.
 * @param       dists_size          The amount of distributions.
 * @param       flag                The flag used to compile the program.
 */
static void write_data(const analysis_st *analysis, distribution_et *dists, size_t dists_size, const char *flag)
{
    uint64_t **measurements = *(analysis->measurements);
    const input_st *inputs = analysis->inputs;
    size_t count = analysis->count;

    for (int i = 0; i < dists_size; i++)
    {
        const char *dist_str, *filename;
        dist_str = dist_to_string(dists[i]);
        filename = construct_filename(dist_str);

        FILE *fs = fopen(filename, "w");
        if (fs == NULL)
        {
            print_error("Error when opening file\n");
            exit(EXIT_FAILURE);
        }

        fprintf(fs, "# compile flags: [%s], fuzz class: [%s]\n", flag, dist_str);
        fprintf(fs, "input_a,input_b,min_clock_measured");
        fprintf(fs, "\n");

        for (size_t j = 0; j < count; j++)
        {
            if (inputs[j].dist != dists[i])
                continue;

            fprintf(fs, "%ld,%ld", inputs[j].a, inputs[j].b);

            // Find min for given set of inputs
            uint64_t min = UINT64_MAX;
            for (int k = 0; k < ITERATIONS; k++)
                min = MIN(min, measurements[k][j]);
            fprintf(fs, ",%lu", min);
            fprintf(fs, "\n");
        }

        fclose(fs);
    }
}

int main(int argc, char const *argv[])
{
    analysis_st analysis;
    const char *flag, *classes_string;
    size_t count;

    if (argc != 4)
    {
        print_error(stderr, "usage: %s #data-points flag \"class1 class2 ...\"", argv[0]);
        exit(EXIT_FAILURE);
    }

    count = atoi(argv[1]);
    flag = argv[2];
    classes_string = argv[3];

    if (initialize_analysis(&analysis, count))
    {
        print_error("Could not initialize analysis struct!\n");
        exit(EXIT_FAILURE);
    }

    size_t number_of_dists;
    distribution_et *dists = parse_classes(classes_string, &number_of_dists);

    if (run_single(&analysis, dists, number_of_dists))
    {
        print_error("Fuzz run failed!\n");
        exit(EXIT_FAILURE);
    }

    write_data(&analysis, dists, number_of_dists, flag);

    destroy_analysis(&analysis);

    return 0;
}
