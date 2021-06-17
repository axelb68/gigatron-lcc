#include "_stdio.h"


/* This initialization function is called before main whenever _iob[]
   is referenced in the program. The default version hooks stdin,
   stdout, and stderr to the console. */

void _iob_setup(void)
{
	/* stdin */
	_iob[0]._flag = _IOFBF|_IOREAD;
	_iob[0]._base = &_cons_linebuf;
	_iob[0]._v = &_cons_svec;
	_iob[0]._file = 0;
	/* stdout */
	_iob[1]._flag = _IONBF|_IOWRIT;
	_iob[1]._v = &_cons_svec;
	_iob[1]._file = 1;
	/* stderr */
	_iob[2]._flag = _IONBF|_IOWRIT;
	_iob[2]._v = &_cons_svec;
	_iob[2]._file = 2;
}



