
def scope():
    
    code = [ ('EXPORT', 'memchr'),
             ('EXPORT', '_memchr2') ]

    if 'has_SYS_ScanMemory' in rominfo:
        info = rominfo['has_SYS_ScanMemory']
        addr = int(str(info['addr']),0)
        cycs = int(str(info['cycs']),0)
        def m_prepScanMemory():
            LDWI(addr);STW('sysFn')
        def m_ScanMemory():
            # copy without page crossings
            # takes destination ptr in sysArgs0/1
            # takes source ptr in sysArgs2/3
            # takes length in vACL (0 means 256)
            SYS(cycs)
    else:
        def m_prepScanMemory():
            pass
        def m_ScanMemory():
            STW('sysArgs4');_CALLJ('_memscan0')
        def code0():
            # scan memory without page crossings
            # takes data ptr in sysArgs0/1
            # takes two byte targets in sysArgs2/3
            # takes length in sysArgs4 (not vACL)
            # returns pointer to target or 0
            nohop()
            label('_memscan0')
            if args.cpu <= 5:
                LDI(0);SUBW('sysArgs4');STW('sysArgs4')
                label('.scanloop')
                LDW('sysArgs0');PEEK()
                ST(vACH);XORW('sysArgs2');STW(T3)
                LD(T3);BEQ('.scanok')
                LD(T3+1);BEQ('.scanok')
                INC('sysArgs0');INC('sysArgs4')
                LD('sysArgs4');BNE('.scanloop')
            else:
                label('.scanloop')
                PEEKp('sysArgs0')
                ST(vACH);XORW('sysArgs2');STW(T3)
                LD(T3);BEQ('.scanok')
                LD(T3+1);BEQ('.scanok')
                DBNE('sysArgs4','_memscan0')
            LDI(0);RET()
            label('.scanok')
            LDW('sysArgs0');RET()

        code.append(('CODE', '_memscan0', code0))


    # void *memchr(const void *s, int c0, size_t n)
    # void *_memchr2(const void *s, char c0, char c1, size_t n)
    # - scans at most n bytes from s until finding one equal to c0 or c1
    # - return pointer to the byte if found, 0 if not found.

    def code1():
        label('memchr');
        tryhop(16);
        LDW(R10);STW(R11);LDW(R9);STW(R10)
        label('_memchr2');                          # R8=d, R9=c0 R10=c1, R11=l
        tryhop(4);LDW(vLR);STW(R22)
        LDW(R8);STW('sysArgs0')
        LD(R9);ST('sysArgs2');LD(R10);ST('sysArgs3')
        m_prepScanMemory()
        label('.loop')
        LD(R8);ST(R20);LDI(255);ST(R20+1)           # R20 is minus count to end of block
        LDW(R11);_BGE('.memscan2')
        ADDW(R20);_BRA('.memscan4')                 # b) len is larger than 0x8000
        label('.memscan2')
        _BEQ('.done')                               # a) len is zero
        ADDW(R20);_BLE('.memscan5')                 # c) len is smaller than -R20
        label('.memscan4')
        STW(R11)                                    # d) len is larger than -R20
        LDI(0);SUBW(R20);STW(R20)
        m_ScanMemory();_BNE('.done')
        LDW(R8);ADDW(R20);STW(R8);STW('sysArgs0')
        _BRA('.loop')
        label('.memscan5')
        LDW(R11);m_ScanMemory()
        label('.done')
        STW(R21);LDW(R22);tryhop(5);STW(vLR);LDW(R21);RET();

    code.append(('CODE', 'memchr', code1))

    
    return code;

module(code=scope(), name='memchr.s');

# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
