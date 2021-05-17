#ifndef __SIGNAL
#define __SIGNAL

typedef int sig_atomic_t;

typedef void (*sig_handler_t)(int);

#define SIG_DFL ((sig_handler_t)0)
#define SIG_ERR ((sig_handler_t)(unsigned int)-1)
#define SIG_IGN ((sig_handler_t)1)

/* Non recoverable signals        */
#define SIGABRT	0  /* see abort() */
#define SIGILL	1  /* (not impl.) */
#define SIGSEGV	2  /* (not impl.) */
#define SIGQUIT	3  /* (not impl.) */
/* Recoverable signals            */
#define SIGFPE  4  /* see runtime */
#define SIGINT	5  /* (not impl.) */
#define SIGTERM	6  /* (not impl.) */
#define SIGVBL  7  /* (not yet.)  */

#define FPE_INTDIV      1       /* integer divide by zero */
#define FPE_FLTOVF      2       /* floating point overflow */
#define FPE_FLTDIV      3       /* floating point divide by zero */
#define FPE_INTOVF      4       /* (not impl.) integer overflow */
#define FPE_FLTUND      5       /* (not impl.) floating point underflow */
#define FPE_FLTRES      6       /* (not impl.) floating point inexact result */
#define FPE_FLTINV      7       /* (not impl.) floating point invalid operation */

sig_handler_t signal(int, sig_handler_t);

int raise(int);

int _raise(int, int);

#endif /* __SIGNAL */
