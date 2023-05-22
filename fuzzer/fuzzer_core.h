#ifndef FUZZER_CORE_H
#define FUZZER_CORE_H

#ifdef KERNEL_MODE
#include <linux/types.h>
// Definitions from libc that are not available in kernel module
#define INT64_MAX 9223372036854775807LL
#define UINT64_MAX 0xffffffffffffffffULL
#define UINT32_MAX 0xffffffffU
#define error_exit(...) (printk(KERN_ERR __VA_ARGS__))

#else
#include <stdint.h>
#include <stddef.h>
#define error_exit(...) (fprintf(stderr, __VA_ARGS__), exit(EXIT_FAILURE))
#endif

#define REPEATS 100   /** The amount of times the program \
                       *  is run to get a more accurate measurement. */
#define ITERATIONS 10 /** The amount of times to cycle through all  \
                       *  fuzz inputs to lower noise from other CPU \
                       *  tasks. */

extern int program(int64_t, int64_t);

#define MIN(x, y) ((x < y) ? (x) : (y))

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
    XLTY,      // Uniformly random but x < y
    YLTX,      // Uniformly random but y < x
    SMALL,     // Uniformly random but small values
} distribution_et;

// This needs to match the amount of elements in distribution_et
#define DIST_COUNT 8

/**
 * @fn          get_dist
 * @brief       Gets the distribution type from its index.
 * @param       index               The index.
 */
distribution_et get_dist(size_t index);

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
 * @fn          run
 * @brief       Run measurements according to analysis parameter and save results.
 * @param       analysis            The specifications for the measurement.
 */
void run(analysis_st *analysis);

/**
 * @fn          dist_to_string
 * @brief       Converts an element of distribution_et type to its string representation.
 * @param       dist                The name of the file to write to.
 */
char *dist_to_string(distribution_et dist);

/**
 * @fn          initialize_analysis
 * @brief       Alocates memory and initializes an analysis_st struct.
 * @param       analysis            The anaylis to be initialized.
 * @param       count               The amount of measurements to get.
 */
void initialize_analysis(analysis_st *analysis, size_t count);

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
 */
const char *construct_filename(const char *dist_str);

#endif