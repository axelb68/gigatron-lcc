
def code0():
    nohop()
    label('labs')
    LDW(L8+2)
    BLT('.neg')
    STW(LAC+2)
    LDW(L8)
    STW(LAC)
    RET()
    label('.neg')
    _LDI(0xffff);XORW(L8+2);STW(LAC+2)
    _LDI(0xffff);XORW(L8);ADDI(1);STW(LAC)
    BNE('.ret')
    LDI(1);ADDW(LAC+2);STW(LAC+2)
    label('.ret')
    RET()
    
code=[
    ('EXPORT', 'labs'),
    ('CODE', 'labs', code0) ]

module(code=code, name='abs.s');

# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
	
