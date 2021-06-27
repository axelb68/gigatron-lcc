#ifndef _STDIO_INTERNAL
#define _STDIO_INTERNAL

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <gigatron/libc.h>

#define _WITH_MALLOC 0
#define _IOB_NUM 5
extern struct _more_iobuf *_more_iob;
struct _more_iobuf {
	struct _iobuf _iob[_IOB_NUM];
	struct _more_iobuf *next;
};

extern int _schkwrite(FILE*);
extern int _schkread(FILE*);
extern int _serror(FILE*, int);
extern int _fcheck(FILE*);
extern int _fclose(FILE*);
extern void _fflush(FILE*);
extern size_t _fwrite(FILE*, const char*, size_t);
extern size_t _fread(FILE*, char*, size_t);
extern FILE *_sfindiob(void);
extern void _sfreeiob(FILE *fp);
extern void _swalk(int(*f)(FILE*));

#define CONS_BUFSIZE 80
extern struct _svec _cons_svec;



#endif
