#include "_stdio.h"
#include <errno.h>


void setbuf(FILE *fp, char *buf)
{
	setvbuf(fp, buf, buf ? _IOFBF : _IONBF, BUFSIZ);
}

int setvbuf(FILE *fp, char *buf, int mode, size_t sz)
{
	register int flag;
	if (! (flag = fp->_flag))
		goto einval;
	
	_fflush(fp);
	fp->_cnt = 0;
	fp->_ptr = 0;
	flag = (flag & ~_IOLBF) | _IONBF;
	if (mode == _IONBF)
		goto fini;
	if (mode != _IOFBF && mode != _IOLBF)
		goto einval;
	if ((flag & _IORW) == _IORW)
		goto enotsup;
	if ((flag & _IOMYBUF) && fp->_base)
		__glink_weak_free(fp->_base);
	flag = (flag & ~(_IOLBF|_IOMYBUF)) | mode;
	fp->_base = 0;
	if (buf && sz >= sizeof(struct _sbuf)) {
		register struct _sbuf *sb = (struct _sbuf*) buf;
		sb->size = sz - sizeof(struct _sbuf) + 2;
		fp->_base = sb;
	}
 fini:
	fp->_flag = flag;
	return _fcheck(fp);
 enotsup:
	errno = ENOTSUP;
	return EOF;
 einval:
	errno = EINVAL;
	return EOF;
}
