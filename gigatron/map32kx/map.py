

def map_describe():
    print('''  Memory map '32kx' steals screen memory on a 32KB Gigatron.
             
  This map uses a special version of the console that adds spacing
  between character lines in a manner that saves screen memory
  and makes memory range 0x800-0x2eff available.
  
  Program and data are first scattered in the video memory holes starting in
  0x2fa0-0x2fff and progressing towards 0x7fa0-0x7fff. Remaining code and 
  data items larger than 96 bytes can then be located in pages 2, 3, 4, 5, 
  6, and 8 to 0x2a. The stack grows from 0x2efe.
  ''')


# ------------size----addr----step----end---- flags (1=nocode, 2=nodata)
segments = [ (0x0060, 0x2fa0, 0x0100, 0x80a0, 0),
	     (0x00fa, 0x0200, 0x0100, 0x0500, 0),
	     (0x0200, 0x0500, None,   None,   0),
             (0x2300, 0x0800, None,   None,   0),
]

initsp = 0x2efe
minram = 0x80

def map_segments():
    '''
    Enumerate all segments as tuples (saddr, eaddr, dataonly)
    '''
    global segments
    for tp in segments:
        estep = tp[2] or 1
        eaddr = tp[3] or (tp[1] + estep)
        for addr in range(tp[1], eaddr, estep):
            yield (addr, addr+tp[0], tp[4])

def map_extra_libs(romtype):
    '''
    Returns a list of extra libraries to scan before the standard ones
    '''
    return [ 'conx' ]

def map_extra_modules(romtype):
    '''
    Generate an extra modules for this map. At the minimum this should
    define a function '_gt1exec' that sets the stack pointer,
    checks the rom and ram size, then calls v(args.e). This is ofen
    pinned at address 0x200.
    '''
    def code0():
        org(0x200)
        label(args.gt1exec)
        # Set stack
        _LDI(initsp);STW(SP);
        # Check rom and ram
        if romtype:
            LD('romType');ANDI(0xfc);SUBI(romtype);BLT('.err')
        if minram == 0x100:
            LD('memSize');BNE('.err')
        else:
            LD('memSize');SUBI(1);ANDI(0xff);SUBI(minram-1);BLT('.err')
        # Call _start
        _LDI(v(args.e));CALL(vAC)
        # Run Marcel's smallest program when machine check fails
        label('.err')
        LDW('frameCount');DOKE(vPC+1);BRA('.err')

    module(name='_gt1exec.s',
           code=[ ('EXPORT', '_gt1exec'),
                  ('CODE', '_gt1exec', code0) ] )

    debug(f"synthetizing module '_gt1exec.s' at address 0x200")



# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
