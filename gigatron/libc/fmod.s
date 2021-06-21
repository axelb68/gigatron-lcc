
def scope():
    
    def code0():
        nohop()
        label('fmod')
        PUSH()
        _FMOV(F8, FAC)
        LDI(F11);_CALLI('_@_fmod')
        POP();RET()

    module(name='fmod.s',
           code=[ ('EXPORT', 'fmod'),
                  ('IMPORT', '_@_fmod'),
                  ('CODE', 'fmod', code0) ] )

    def code1():
        label('_fmodquo')
        PUSH()
        _FMOV(F8, FAC)
        LDI(F11);_CALLI('_@_fmod')
        LDW(T2);DOKE(R14) # low bits of quotient
        POP();RET()
        
    module(name='fmodquo.s',
           code=[ ('EXPORT', 'fmodquo'),
                  ('IMPORT', '_@_fmod'),
                  ('CODE', '_fmodquo', code0) ] )

    
scope()

# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
