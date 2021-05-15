#include <stdlib.h>


/* Gigatron encoding:
   - 0x00-0x7f: ASCII
   - 0x80-0x83: Arrows U+2190 to U+2193
   Also supported here:
   - 0x84-0xff: Latin 1
*/


static wchar_t ctow(char c)
{
	if ((c & 0xfc) == 0x80)
		return 0x2190u + (c & 3);
	return c;
}

static int wtoc(wchar_t w)
{
	if (w >> 8) {
		if ((w & 0xfffcU) == 0x2190)
			return 0x80 | (w & 0x03);
		return -1;
	} else {
		if ((w & 0xfc) == 0x80)
			return -1;
		return w;
	}
}

int mblen(const char *s, size_t n)
{
	if (s == 0 || *s == 0)
		return 0;
	if (n <= 0)
		return -1;
	return 1;
}

int mbtowc(wchar_t *pwc, const char *s, size_t n)
{
	if (n <= 0)
		return -1;
	if (s == 0 || *s == 0)
		return 0;
	if (pwc)
		*pwc = ctow(*s);
	return 1;
}

int wctomb(char *s, wchar_t wc)
{
	int c = wtoc(wc);
	if (s == 0)
		return 0;
	if (c < 0)
		return -1;
	*s = (char)c;
	return 1;
}


size_t mbstowcs(wchar_t *d, const char *s, size_t n)
{
	size_t r = 0;
	if (s != 0) {
		while (*s && r < n) {
			if (d) { *d++ = ctow(*s); }
			r += 1, s += 1;
		}
	}
	return r;
}

size_t wcstombs(char *d, const wchar_t *s, size_t n)
{
	size_t r = 0;
	if (s != 0) {
		while (*s && r < n) {
			int c = wtoc(*s);
			if (c < 0) { return (size_t)-1; }
			if (d) { *d++ = c; }
			r += 1, s += 1;
		}
	}
	return r;
}

