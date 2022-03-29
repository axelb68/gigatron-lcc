#include "stdlib.h"
#include "string.h"
#include "gigatron/console.h"
#include "gigatron/sys.h"

int main()
{
  int i;
  
  // Display a red line at the top of the screen
  SYS_ExpanderControl(0xe8f0u);
  memset((void*)0x8800u, 0x3, 160);
  SYS_ExpanderControl(0xc8f0u);
  memset((void*)0x8800u, 0xc, 160);
  SYS_ExpanderControl(0x00f0u);
  
  // Print something
  cprintf("\n\nHello World\n\n");

  for (i = 1; i < 100; i++)
    cprintf("* %d\n", i);
  
  return 0;
}
