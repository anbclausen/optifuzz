#ifndef FUZZER_CORE_H
#define FUZZER_CORE_H

#include <stdint.h>
#include <stddef.h>
#define print_error(...) (fprintf(stderr, __VA_ARGS__))

#define ITERATIONS 50 /** The amount of times to cycle through all  \
                        *  fuzz inputs to lower noise from other CPU \
                        *  tasks. */

#define MIN(x, y) ((x < y) ? (x) : (y))

typedef enum
{
    SUCCESS = 0,
    FAILURE
} status_et;

/**
 * @struct      distribution_et
 * @brief       Distributions for setting the two input variables.
 */
typedef enum
{
    UNIFORMLY, // Uniformly random values
    EQUAL,     // Uniformly random but equal values
    MAX64,     // One is INT64_MAX, other is uniform random
    XZERO,     // x is 0, y is uniform random
    YZERO,     // y is 0, x is uniform random
    XLTY,      // Uniformly random but x < y
    YLTX,      // Uniformly random but y < x
    SMALL,     // Uniformly random but small values
    FIXED,     // x = y = 0x12345678

    INVALID // Indicates invalid distribution, no a real distribution
} distribution_et;

// This needs to match the amount of elements in distribution_et
#define DIST_COUNT 9

/**
 * @struct      input_st
 * @brief       A tuple (a, b, dist) defining an input to the program
 */
typedef struct
{
    int64_t a;            /** The first input.                */
    int64_t b;            /** The second input.               */
    distribution_et dist; /** The distribution of the inputs. */
} input_st;

/**
 * @struct      analysis_st
 * @brief       Contains all values that are needed to make measurements
 */
typedef struct
{
    input_st *inputs;
    uint64_t *(*measurements)[ITERATIONS];
    size_t count;
} analysis_st;

/**
 * @fn          dist_to_string
 * @brief       Converts an element of distribution_et type to its string representation.
 * @param       dist                The name of the file to write to.
 * @return      Returns distribution string or NULL on failure.
 */
const char *dist_to_string(distribution_et dist);

/**
 * @fn          initialize_analysis
 * @brief       Allocates memory and initializes an analysis_st struct.
 * @param       analysis            The analysis to be initialized.
 * @param       count               The amount of measurements to get.
 * @return      Returns SUCCESS or FAILURE.
 */
status_et initialize_analysis(analysis_st *analysis, size_t count);

/**
 * @fn          destroy_analysis
 * @brief       Frees all memory used by analysis_st struct element.
 * @details     This function should only be used on already initialized
 *              analysis_st struct elements.
 * @param       analysis            The anaylis to be initialized.
 * @param       count               The amount of measurements to get.
 */
void destroy_analysis(analysis_st *analysis);

/**
 * @fn          construct_filename
 * @brief       Creates a filename for the given distribution string.
 * @details     Aditional calls to this function will overwrite the last
 *              returned string.
 * @param       dist_str            String represenation of the distribution.
 * @return      Pointer to buffered string.
 */
const char *construct_filename(const char *dist_str);

/**
 * @fn          run
 * @brief       Run measurements according to analysis parameter and save results.
 * @param       analysis            The specifications for the measurement.
 * @param       dists               The distributions to use.
 * @param       dists_size          The amount of distributions.
 * @return      Returns SUCCESS or FAILURE.
 */
status_et run(analysis_st *analysis, distribution_et *dists, size_t dists_size);

/**
 * @fn          parse_classes
 * @brief       Parses a string of space seperated distribution names.
 * @param       str                 A zero terminated string with space seperated distributions.
 * @param       size                Set to the amount if classes parsed classes.
 * @return      Returns an array of all the classes.
 */
distribution_et *parse_classes(const char *str, size_t *size);

#endif