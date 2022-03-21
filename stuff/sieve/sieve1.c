#include <stdio.h>
#include <gigatron/console.h>
#include <gigatron/sys.h>
#define TIMER 1

/** This is a minor modification of the genuine C program of the sieve benchmark.
    It uses cprintf instead of printf. Loop conditions and certain expressions 
    have been rewritten. **/

#define true 1
#define false 0
#define size 8190
#define sizepl 8191
char flags[sizepl];
main() {
    int i, prime, k, count, iter, ticks; 
    cprintf("10 iterations\n");
    ticks = 0;
#if TIMER
    frameCount = 0;
#endif
    for (iter = 1; iter <= 10; iter ++) {
        count=0 ; 
	for (i = 0; i != sizepl; i++)
	    flags[i] = true; 
        for (i = 0; i != sizepl; i++) { 
	    if (flags[i]) {
                prime = i + i + 3; 
                k = prime + i; 
                while (size - k >= 0) { 
                    flags[k] = false; 
                    k += prime; 
                }
                count = count + 1;
            }
        }
#if TIMER
	ticks += frameCount;
	frameCount = 0;
#endif
    }
    cprintf("\n%d primes", count);
#if TIMER
    cprintf("\n%d %d/60 seconds", ticks/60, ticks % 60, count);
#endif
}

/* Local Variables: */
/* mode: c */
/* c-basic-offset: 4 */
/* indent-tabs-mode: () */
/* End: */
