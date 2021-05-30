
def scope():

    # ----------------------------------------
    # int SYS_Lup(unsigned int addr)
    #   Notes: This is not a real SYS call. Just the LUP instruction.
    def code0():
        nohop()
        label('SYS_Lup')
        LDW(R8);LUP(0);RET()

    module(name='sys_lup.s',
           code=[('EXPORT', 'SYS_Lup'),
                 ('CODE', 'SYS_Lup', code0) ])

    # ----------------------------------------
    # unsigned int SYS_Random(void);
    def code0():
        nohop()
        label('SYS_Random')
        _LDI('SYS_Random_34');STW('sysFn')
        SYS(34);RET()

    module(name='sys_random.s',
           code=[('EXPORT', 'SYS_Random'),
                 ('CODE', 'SYS_Random', code0) ])

    # ----------------------------------------
    # void SYS_VDrawBits(int fgbg, char bits, char *addr);
    def code0():
        nohop()
        label('SYS_VDrawBits')
        _LDI('SYS_VDrawBits_134');STW('sysFn')
        LDW(R8);STW('sysArgs0')
        LD(R9);ST('sysArgs2')
        LDW(R10);STW('sysArgs4')
        SYS(134);RET()

    module(name='sys_vdrawbits.s',
           code=[('EXPORT', 'SYS_VDrawBits'),
                 ('CODE', 'SYS_VDrawBits', code0) ])
    
    # ----------------------------------------
    # void SYS_ExpanderControl(unsigned int ctrl);
    def code0():
        nohop()
        label('SYS_ExpanderControl')
        _LDI('SYS_ExpanderControl_v4_40');STW('sysFn')
        LDW(R8);SYS(40);RET()

    module(name='sys_expandercontrol.s',
           code=[('EXPORT', 'SYS_ExpanderControl'),
                 ('CODE', 'SYS_ExpanderControl', code0) ])

    # ----------------------------------------
    # void SYS_SpiExchangeBytes(void *dst, void *src, void *srcend);
    #    Notes: This exists in v4 but depends on 0x81 containing ctrlBits.
    #    Notes: only the high 8 bits of `dst` are used.
    #    Notes: only the low 8 bits of `srcend` are used.
    def code0():
        nohop()
        label('SYS_SpiExchangeBytes')
        _LDI('SYS_SpiExchangeBytes_v4_134');STW('sysFn')
        # sysArgs[0]      Page index start, for both send/receive (in, changed)
        # sysArgs[1]      Memory page for send data (in)
        # sysArgs[2]      Page index stop (in)
        # sysArgs[3]      Memory page for receive data (in)
        LDW(R9);STW('sysArgs0')
        LD(R10);ST('sysArgs2')
        LD(R8+1);ST('sysArgs3')
        SYS(134)
        RET()
    
    module(name='sys_spiexchangebytes.s',
           code=[('EXPORT', 'SYS_SpiExchangeBytes'),
                 ('CODE', 'SYS_SpiExchangeBytes', code0) ])


# execute    
scope()

# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
