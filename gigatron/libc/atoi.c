#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <errno.h>

int  atoi(register const char *s)
{
	register int x = 0;
	register int n = 0;
	register int c = *s;
	while (isspace(c))
		c = *++s;
	if (c == '-')
		n = c = *++s;
	else if (c == '+')
		c = *++s;
	while (isdigit(c)) {
		c = c - '0';
		x = x * 10 + c;
		c = *++s;
	}
	if (n)
		x = -x;
	return x;
}
