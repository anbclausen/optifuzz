#include <stdint.h>
#include <time.h>


int mssleep(long nano)
{
   struct timespec rem;
   struct timespec req= {
       0,     /* secs (Must be Non-Negative) */ 
       nano /* nano (Must be in range of 0 to 999999999) */ 
   };

   return nanosleep(&req , &rem);
}

int seed = 602436049;
int program(int64_t x, int64_t y) { 
    if (x > 0) {
        printf("\n");
    } else {
        
    }
};
