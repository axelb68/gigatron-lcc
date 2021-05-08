
def code0():
   nohop()
   if args.cpu < 6:
      for i in range(0,8):
         label("_@_saveR%dto7" % i);
         STW(T3);LDW(R0+i+i);DOKE(T3);LDI(2);ADDW(T3)
      RET()
   else:
      for i in range(0,8):
         label("_@_saveR%dto7" % i);
         DOKEA(R0+i+i);ADDI(2)
      RET()

def code1():
   nohop()
   if args.cpu < 6:
      for i in range(0,8):
         label("_@_restoreR%dto7" % i);
         STW(T3);DEEK();STW(R0+i+i);LDI(2);ADDW(T3)
      RET()
   else:
      for i in range(0,8):
         label("_@_restoreR%dto7" % i);
         DEEKA(R0+i+i);ADDI(2)
      RET()

      
code= [ ('EXPORT', '_@_saveR%dto7' % i) for i in range(0,8) ] + \
      [ ('CODE', '_@_saveR0to7', code0) ] + \
      [ ('EXPORT', '_@_restoreR%dto7' % i) for i in range(0,8) ] + \
      [ ('CODE', '_@_restoreR0to7', code1) ] 

module(code=code, name='_rt_save.s');

# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
