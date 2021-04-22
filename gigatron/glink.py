# -------------- glink proper

import argparse, json, string
import os, sys, traceback, functools

args = None
rominfo = None
lccdir = '/usr/local/lib/gigatron-lcc'
current_module = None
current_proc = None
symdefs = {}
safe_dict = {}
module_list = []
emit_counter = 0
lbranch_counter = 0

# --------------- utils

def debug(s, level=1):
    if args.v and args.v >= level:
        print("(glink debug) " + s, file=sys.stderr)
        
def where(tb=None):
    '''Locate error in a .s/.o/.a file'''
    stb = traceback.extract_tb(tb, limit=8) if tb else \
          traceback.extract_stack(limit=8)
    for s in stb:
        if (s[2].startswith('code')):
            return "{0}:{1}".format(s[0],s[1])
    return None

class Module:
    '''Class for assembly modules read from .s/.o/.a files.'''
    def __init__(self, name=None, cpu=None, code=None):
        global args, current_module
        self.code = code
        self.name = name
        self.cpu = cpu if cpu != None else args.cpu
        self.exports = {}
        self.externs = {}
        self.genlabelcounter = 0
    def __repr__(self):
        return f"Module('{self.name}',...)"
    def genlabel():
        self.genlabelcounter += 1
        return f".LL{self.genlabelcounter}"
    def run(self,proc):
        '''Execute the module code with the specified delegate''' 
        global current_proc, current_module
        current_proc = proc
        current_module = self
        self.genlabelcounter = 0
        self.code()
        current_proc = None
        current_module = None

class __metaUnk(type):
    wrapped = ''' 
      __abs__ __add__ __and__ __eq__ __floordiv__ __ge__ __gt__ __invert__
      __le__ __le__ __lshift__ __lt__ __mod__ __mul__ __neg__ __or__ 
      __pos__ __pow__ __radd__ __rand__ __rfloordiv__ __rlshift__ __rmod__
      __rmul__ __ror__ __rpow__ __rrshift__ __rshift__ __rsub__ 
      __rtruediv__ __rxor__ __sub__ __truediv__  __xor__
    '''
    def __new__(cls, name, bases, namespace, **kwargs):
        def wrap(f):
            @functools.wraps(f)
            def wrapper(self, *args):
                return Unk(f(int(self), *map(int, args)))
            return wrapper if f else None
        for m in cls.wrapped.split():
            namespace[m] = wrap(getattr(int, m))
        return type(name, bases, namespace)
    
class Unk(int, metaclass=__metaUnk):
    '''Class to flag unknow integers'''
    __slots__= ()
    def __new__(cls,val):
        return int.__new__(cls,val)
    def __repr__(self):
        return f"Unk({hex(int(self))})"

def is_zero(x):
    if isinstance(x,int) and not isinstance(x,Unk):
        return int(x) == 0
    return False

def is_zeropage(x, l = 0):
    if isinstance(x,int) and not isinstance(x,Unk):
        if int(x) & 0xff00 == 0:
            return l < 1 or int(x + l) & 0xff00 == 0
    return False

def is_not_zeropage(x):
    if isinstance(x,int) and not isinstance(x,Unk):
        return int(x) & 0xff00 == 0
    return False

def is_pcpage(x):
    if isinstance(x,int) and not isinstance(x,Unk):
        return int(x) & 0xff00 == pc() & 0xff00
    return False

def is_not_pcpage(x):
    if isinstance(x,int) and not isinstance(x,Unk):
        return int(x) & 0xff00 == pc() & 0xff00
    return False

def check_zp(x):
    x = v(x)
    if is_not_zeropage(x):
        warning(f"zero page argument overflow")
    return x

def check_br(x):
    x = v(x)
    if is_not_pcpage(x):
        warning(f"short branch overflow")
    return (int(x)-2) & 0xff

def check_cpu(op, v):
    if args.cpu < v:
        warning(f"opcode not implemented for cpu={arg.cpu}")

def emit(*args):
    global emit_counter
    emit_counter += len(args)
    current_proc.emit(*args)

def emitjmp(d, saveAC=False):
    if is_pcpage(d): # 2 bytes
        BRA(d)
        return
    global lbranch_counter
    if args.cpu >= 5: # 3 bytes
        lbranch_counter += 3
        CALLI(d)
    elif not saveAC:  # 5 bytes
        lbranch_counter += 5
        emit(0x11, lo(int(d)-2), hi(int(d))) # LDWI (nohop)
        STW(vPC)
    else:             # 10 bytes (sigh!)
        lbranch_counter += 10
        STLW(-2)
        emit(0x11, lo(int(d)), hi(int(d)))   # LDWI (nohop)
        STW(vLR)
        LDLW(-2)
        RET()
    
def emitjcc(BCC, BNCC, d, saveAC=False):
    lbl = current_module.genlabel()
    if is_pcpage(d):
        BCC(d)
    else:
        BNCC(lbl);
        emitjmp(int(d), saveAC=saveAC)
        label(lbl)
    
        
# ------------- usable vocabulary for .s/.o/.a files

def register_names():
    d = { "vPC":  0x0016, "vAC":  0x0018, "vACL": 0x0018, "vACH": 0x0019,
          "vLR":  0x001a, "vSP":  0x001c, 
          "AC":   0x0018, "LAC":  0x0084, "FAC":  0x0081,
          "FACS": 0x0081, "FACE": 0x0082, "FACX": 0x0083, "FACM": 0x0084 }
    for i in range(0,4): d[f'T{i}'] = 0x88+i+i
    for i in range(8,32): d[f'R{i}'] = 0x80+i+i
    for i in range(8,29): d[f'L{i}'] = d[f'R{i}']
    for i in range(8,28): d[f'F{i}'] = d[f'R{i}']
    d['SP'] = d['R31']
    d['LR'] = d['R30']
    return d

for (k,v) in register_names().items():
    safe_dict[k] = v
    globals()[k] = v

def vasm(func):
    '''Decorator to mark functions usable in .s/.o/.a files'''
    safe_dict[func.__name__] = func
    return func

@vasm
def error(s):
    w = where()
    current_proc.error(f"glink: {w}: error: {s}")
@vasm
def warning(s):
    w = where()
    current_proc.warning(f"glink: {w}: warning: {s}")
@vasm
def fatal(s):
    w = where()
    w = "" if w == None else w + ": "
    print(f"glink: {w}fatal error: {s}", file=sys.stderr)
    sys.exit(1)

@vasm
def module(code=None,name=None,cpu=None):
    global module_list
    if current_module or current_proc:
        warning("module() should not be called from the code fragment")
    else:
        module_list.append(Module(name,cpu,code))

@vasm
def pc():
    return current_proc.pc()
@vasm
def v(x):
    return current_proc.v(x) if isinstance(x,str) else x
@vasm
def lo(x):
    return v(x) & 0xff
@vasm
def hi(x):
    return (v(x) >> 8) & 0xff

@vasm
def ST(d):
    emit(0x5e, check_zp(d))
@vasm
def STW(d):
    emit(0x2b, check_zp(d))
@vasm
def STLW(d):
    emit(0xec, check_zp(d))
@vasm
def LD(d):
    tryhop(); emit(0x1a, check_zp(d))
@vasm
def LDI(d, hop=True):
    tryhop(); emit(0x59, check_zp(d))
@vasm
def LDWI(d):
    tryhop(); d=int(v(d)); emit(0x11, lo(d), hi(d))
@vasm
def LDW(d):
    tryhop(); emit(0x21, check_zp(d))
@vasm
def LDLW(d):
    emit(0xee, check_zp(d))
@vasm
def ADDW(d):
    emit(0x99, check_zp(d))
@vasm
def SUBW(d):
    emit(0xb8, check_zp(d))
@vasm
def ADDI(d):
    emit(0xe3, check_zp(d))
@vasm
def SUBI(d):
    emit(0x36, check_zp(d))
@vasm
def LSLW():
    emit(0xe9)
@vasm
def INC(d):
    emit(0x93, check_zp(d))
@vasm
def ANDI(d):
    emit(0x82, check_zp(d))
@vasm
def ANDW(d):
    emit(0xf8, check_zp(d))
@vasm
def ORI(d):
    emit(0x88, check_zp(d))
@vasm
def ORW(d):
    emit(0xfa, check_zp(d))
@vasm
def XORI(d):
    emit(0x8c, check_zp(d))
@vasm
def XORW(d):
    emit(0xfc, check_zp(d))
@vasm
def PEEK():
    emit(0xad)
@vasm
def DEEK():
    emit(0xf6)
@vasm
def POKE(d):
    emit(0xf0, check_zp(d))
@vasm
def DOKE(d):
    emit(0xf3, check_zp(d))
@vasm
def LUP(d):
    emit(0x7f, check_zp(d))
@vasm
def BRA(d):
    emit(0x90, check_br(d)); tryhop(jump=False);
@vasm
def BEQ(d):
    emit(0x35, 0x3f, check_br(d))
@vasm
def BNE(d):
    emit(0x35, 0x72, check_br(d))
@vasm
def BLT(d):
    emit(0x35, 0x50, check_br(d))
@vasm
def BGT(d):
    emit(0x35, 0x4d, check_br(d))
@vasm
def BLE(d):
    emit(0x35, 0x56, check_br(d))
@vasm
def BGE(d):
    emit(0x35, 0x53, check_br(d))
@vasm
def CALL(d):
    emit(0xcf, check_zp(d))
@vasm
def RET():
    emit(0xff); tryhop(jump=False)
@vasm
def PUSH():
    emit(0x75)
@vasm
def POP():
    emit(0x63)
@vasm
def ALLOC(d):
    emit(0xdf, check_zp(d))
@vasm
def SYS(op):
    t = 270-op//2 if op>28 else 0
    if not isinstance(t,Unk):
        if t <= 128 or t > 255:
            error(f"argument overflow in SYS opcode");
    emit(0xb4, t)
@vasm
def HALT():
    emit(0xb4, 0x80); tryhop(jump=False)
@vasm
def DEF(d):
    emit(0xcd, check_br(d))
@vasm
def CALLI(d):
    check_cpu(5); d=int(v(d)); emit(0x85, lo(d-2), hi(d))
@vasm
def CMPHS(d):
    check_cpu(5); emit(0x1f, check_zp(d))
@vasm
def CMPHU(d):
    check_cpu(5); emit(0x97, check_zp(d))

@vasm
def _SP(n):
    n = v(n)
    if is_zero(n):
        LDW(SP);
    elif is_zeropage(n):
        LDW(SP); ADDI(n)
    elif is_zeropage(-n):
        LDW(SP); SUBI(n)
    else:
        LDWI(n); ADDW(SP)
@vasm
def _LDI(d):
    '''Emit LDI or LDWI depending on the size of d. No hops.'''
    d = v(d)
    if is_zeropage(d):
        emit(0x59, d)
    else:
        emit(0x11, lo(d), hi(d))
@vasm
def _LDW(d):
    '''Emit LDW or LDWI+DEEK depending on the size of d. No hops.'''
    d = v(d)
    if is_zeropage(d):
        emit(0x21, d)
    else:
        _LDI(d); DEEK()
@vasm
def _LD(d):
    '''Emit LD or LDWI+PEEK depending on the size of d. No hops.'''
    d = v(d)
    if is_zeropage(d):
        emit(0x21, d)
    else:
        _LDI(d); PEEK()
@vasm
def _SHL(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_shl16')
    _CALLI('_@_shl')            # T3<<T2 -> AC
@vasm
def _SHRS(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_shrs16')
    _CALLI('_@_shrs16')         # T3>>T2 --> AC
@vasm
def _SHRU(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_shru16')
    _CALLI('_@_shru16')         # T3>>T2 --> AC
@vasm
def _MUL(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_mul16')
    _CALLI('_@_mul16')          # T3*T2 --> AC
@vasm
def _DIVS(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_divs16')
    _CALLI('_@_divs16')         # T3/T2 --> AC
@vasm
def _DIVU(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_divu16')
    _CALLI('_@_divu16')         # T3/T2 --> AC
@vasm
def _MODS(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_mods16')
    _CALLI('_@_mods16')         # T3%T2 --> AC
@vasm
def _MODU(d):
    STW(T3); LDW(d); STW(T2)
    extern('_@_modu16')
    _CALLI('_@_modu16')         # T3%T2 --> AC
@vasm
def _MOV(s,d):
    '''Move word from reg/addr s to d.
       Also accepts [AC] for s or d.'''
    s = v(s)
    d = v(d)
    if s != d:
        if args.cpu > 5 and s == [AC] and is_zeropage(d):
            DEEKA(d)
        elif args.cpu > 5 and is_zeropage(s) and d == [AC]:
            DOKEA(s)
        elif d == [AC]:
            STW(T3)
            if s != AC:
                _LDW(s)
            DOKE(T3)
        elif is_zeropage(d):
            if s == [AC]:
                DEEK()
            elif s != AC:
                _LDW(s)
            if d != AC:
                STW(d)
        elif s == AC or s == [AC]:
            if s == [AC]:
                DEEK()
            STW(T3); _LDI(d)
            if args.cpu > 5:
                DOKEA(T3)
            else:
                STW(T2); LDW(T3); DOKE(T2)
        else:
            _LDI(d); STW(T2); _LDW(s); DOKE(T2)
@vasm
def _BRA(d, saveAC=False):
    emitjmp(v(d), saveAC=saveAC)
@vasm
def _BEQ(d, saveAC=False):
    emitjcc(BEQ, BNE, v(d), saveAC=saveAC)
@vasm
def _BNE(d, saveAC=False):
    emitjcc(BNE, BEQ, v(d), saveAC=saveAC)
@vasm
def _BLT(d, saveAC=False):
    emitjcc(BLT,_BGE, v(d), saveAC=saveAC)
@vasm
def _BGT(d, saveAC=False):
    emitjcc(BGT,_BLE, v(d), saveAC=saveAC)
@vasm
def _BLE(d, saveAC=False):
    emitjcc(BLE, BGT, v(d), saveAC=saveAC)
@vasm
def _BGE(d, saveAC=False):
    emitjcc(BGE, BLT, v(d), saveAC=saveAC)
@vasm
def _CMPIS(d):
    if args.cpu >= 5:
        CMPHS(0); SUBI(d)
    else:
        lbl = current_module.genlabel()
        BLT(lbl)
        SUBI(d)
        label(lbl)
@vasm
def _CMPIU(d):
    if args.cpu >= 5:
        CMPHU(0); SUBI(d)
    else:
        lbl = current_module.genlabel()
        BGE(lbl)
        LDWI(0x100)
        label(lbl)
        SUBI(d)
@vasm
def _CMPWS(d):
    if args.cpu >= 5:
        CMPHS(d+1); SUBW(d)
    else:
        lbl1 = current_module.genlabel()
        lbl2 = current_module.genlabel()
        STW(T3); XORW(d)
        BGE(lbl1)
        LDW(T3); ORI(1)
        BRA(lbl2)
        label(lbl1)
        LDW(T3); SUBW(d)
        label(lbl2)
@vasm
def _CMPWU(d):
    if args.cpu >= 5:
        CMPHU(d+1); SUBW(d)
    else:
        lbl1 = current_module.genlabel()
        lbl2 = current_module.genlabel()
        STW(T3); XORW(d)
        BGE(lbl1)
        LDW(d); ORI(1)
        BRA(lbl2)
        label(lbl1)
        LDW(T3); SUBW(d)
        label(lbl2)
@vasm
def _BMOV(s,d,n):
    '''Move memory block of size n from addr s to d.
       Also accepts [AC] as s and [AC] or [T2] as d.'''
    dr = v(dr)
    sr = v(sr)
    n = v(n)
    if s != d:
        if d == [AC]:
            STW(T2)
        if s == [AC]:
            STW(T3)
        if d != [AC] and d != [T2]:
            _LDI(d); STW(T2)
        if s != [AC] and s != [T3]:
            _LDI(s); STW(T3)
        _LDI(n);
        extern('_@_memcpy')
        _CALLI('_@_memcpy', storeAC=T1)         # [T2..T2+AC) --> [T3..T3+AC)
@vasm
def _LMOV(s,d):
    '''Move long from reg/addr s to d.
       Also accepts [AC] as s, and [AC] or [T2] as d.'''
    s = v(s)
    d = v(d)
    if s != d:
        if is_zeropage(d, 3):
            if is_zeropage(s, 3):
                _LDW(s); STW(d); _LDW(s+2); STW(d+2)      # 8 bytes
            elif args.cpu > 5:
                if s != [AC]:
                    _LDI(s)
                DEEKA(d); ADDI(2); DEEKA(d+2)             # 6-9 bytes
            elif s != [AC]:
                _LDW(s); STW(d); _LDW(s+2); STW(d+2)      # 12 bytes
            else:
                STW(T3); DEEK(); STW(d)
                _LDW(T3); ADDI(2); DEEK(); STW(d+2);      # 12 bytes
        elif is_zeropage(s, 3) and args.cpu > 5:
            if d == [T2]:
                _LDW(T2)
            elif s != [AC]:
                _LDI(s)
            DOKEA(s); ADDI(2); DOKEA(s+2)                 # 6-9 bytes
        else:
            if d == [AC]:
                STW(T2)
            if s == [AC]:
                STW(T3)
            if d != [AC] and d != [T2]:
                _LDI(d); STW(T2)
            if s != [AC] and s != [T3]:               # call sequence
                _LDI(s); STW(T3)                      # 5-13 bytes
            extern('_@_lcopy')
            _CALLI('_@_lcopy')  #   [T3..T3+4) --> [T2..T2+4)
@vasm
def _LADD():
    extern('_@_ladd')              # [AC/T3] means [AC] for cpu>=5, [T3] for cpu<5
    _CALLI('_@_ladd', storeAC=T3)  # LAC+[AC/T3] --> LAC
@vasm
def _LSUB():
    extern('_@_lsub') 
    _CALLI('_@_lsub', storeAC=T3)  # LAC-[AC/T3] --> LAC
@vasm
def _LMUL():
    extern('_@_lmul')
    _CALLI('_@_lmul', storeAC=T3)  # LAC*[AC/T3] --> LAC
@vasm
def _LDIVS():
    extern('_@_ldivs')
    _CALLI('_@_ldivs', storeAC=T3)  # LAC/[AC/T3] --> LAC
@vasm
def _LDIVU():
    extern('_@_ldivu')
    _CALLI('_@_ldivu', storeAC=T3)  # LAC/[AC/T3] --> LAC
@vasm
def _LMODS():
    extern('_@_lmods')
    _CALLI('_@_lmods', storeAC=T3)  # LAC%[AC/T3] --> LAC
@vasm
def _LMODU():
    extern('_@_lmodu')
    _CALLI('_@_lmodu', storeAC=T3)  # LAC%[AC/T3] --> LAC
@vasm
def _LSHL(d):
    extern('_@_lshl')
    _CALLI('_@_lshl', storeAC=T3)  # LAC<<[AC/T3] --> LAC
@vasm
def _LSHRS(d):
    extern('_@_lshrs')
    _CALLI('_@_lshrs', storeAC=T3)  # LAC>>[AC/T3] --> LAC
@vasm
def _LSHRU(d):
    extern('_@_lshru')
    _CALLI('_@_lshru', storeAC=T3)  # LAC>>[AC/T3] --> LAC
@vasm
def _LNEG():
    extern('_@_lneg')
    _CALLI('_@_lneg')               # -LAC --> LAC
@vasm
def _LCOM():
    extern('_@_lcom')
    _CALLI('_@_lcom')               # ~LAC --> LAC
@vasm
def _LAND():
    extern('_@_land')
    _CALLI('_@_land', storeAC=T3)   # LAC&[AC/T3] --> LAC
@vasm
def _LOR():
    extern('_@_lor')
    _CALLI('_@_lor', storeAC=T3)    # LAC|[AC/T3] --> LAC
@vasm
def _LXOR():
    extern('_@_lxor')
    _CALLI('_@_lxor', storeAC=T3)   # LAC^[AC/T3] --> LAC
@vasm
def _LCMPS():
    extern('_@_lcmps')
    _CALLI('_@_lcmps', storeAC=T3)  # SGN(LAC-[AC/T3]) --> AC
@vasm
def _LCMPU():
    extern('_@_lcmpu')
    _CALLI('_@_lcmpu', storeAC=T3)  # SGN(LAC-[AC/T3]) --> AC
@vasm
def _LCMPX():
    extern('_@_lcmpx')
    _CALLI('_@_lcmpx', storeAC=T3)  # TST(LAC-[AC/T3]) --> AC
@vasm
def _FMOV(s,d):
    '''Move float from reg s to d with special cases when s or d is FAC.
       Also accepts [AC] or [T3] for s and [AC] or [T2] for d.'''
    s = v(s)
    d = v(d)
    if s != d:
        if d == FAC:
            if s == [AC]:
                STW(T3)
            elif s != [T3]:
                _LDI(s); STW(T3)
            extern('_@_fstorefac') 
            _CALLI('_@_fstorefac')   # [T3..T3+5) --> FAC
        elif s == FAC:
            if d == [AC]:
                STW(T2)
            elif d != [T2]:
                _LDI(d); STW(T2)
            extern('_@_floadfac') 
            _CALLI('_@_floadfac')   # FAC --> [T2..T2+5)
        elif is_zeropage(d, 4) and is_zeropage(s, 4):
            _LDW(s); STW(d); _LDW(s+2); STW(d+2); _LD(s+4); ST(d+4)
        else:
            if d == [AC]:
                STW(T2)
            if s == [AC]:
                STW(T3)
            if d != [AC] and d != [T2]:
                _LDI(d); STW(T2)
            if s != [AC] and s != [T3]:
                _LDI(s); STW(T3)
            extern('_@_fcopy')       # [T3..T3+5) --> [T2..T2+5)
            _CALLI('_@_fcopy')
@vasm
def _FADD():
    extern('_@_fadd')
    _CALLI('_@_fadd', storeAC=T3)   # FAC+[AC/T3] --> FAC
@vasm
def _FSUB():
    extern('_@_fsub')
    _CALLI('_@_fsub', storeAC=T3)   # FAC-[AC/T3] --> FAC
@vasm
def _FMUL():
    extern('_@_fmul')
    _CALLI('_@_fmul', storeAC=T3)   # FAC*[AC/T3] --> FAC
@vasm
def _FDIV():
    extern('_@_fdiv')
    _CALLI('_@_fdiv', storeAC=T3)   # FAC/[AC/T3] --> FAC
@vasm
def _FNEG():
    extern('_@_fneg')
    _CALLI('_@_fneg')               # -FAC --> FAC
@vasm
def _FCMP():
    extern('_@_fcmp')
    _CALLI('_@_fcmp', storeAC=T3)   # SGN(FAC-[AC/T3]) --> AC
@vasm
def _CALLI(d, saveAC=False, storeAC=None):
    '''Call subroutine at far location d.
       When cpu<5, option saveAC=True ensures AC is preserved, 
       and option storeAC=reg stores AC into a register before jumping.
       When cpu>=5, this just calls CALLI. '''
    if args.cpu >= 5:
        CALLI(d)
    elif saveAC:
        STSW(-2)
        LDWI(d)
        STW('sysFn')
        LDSW(-2)
        CALL('sysFn')
    elif storeAC:
        STW(storeAC)
        LDWI(d)
        STW('sysFn')
        CALL('sysFn')
    else:
        LDWI(d)
        STW('sysFn')
        CALL('sysFn')

# export(sym):
# extern(sym)
# common(sym,size,align)
# segment(seg)
# function(sym)
# globvar(sym)
# label(sym,[def])
# sethop(n)
# tryhop(jump=True)
# align(d)
# bytes(*args)
# words(*args)
# space(d)


# ------------- reading .s/.o/.a files


    
        
# ------------- reading .s/.o/.a files
        
              
def new_globals():
    '''Return a pristine global symbol table to read .s/.o/.a files.'''
    global safe_dict
    g = safe_dict.copy()
    g['args'] = { k:vars(args)[k] for k in ('cpu','rom','map') }
    g['__builtins__'] = None
    return g

def read_file(f):
    '''Safely read a .s/.o/.a file.'''
    global code, current_module, current_proc
    debug(f"reading '{f}'")
    with open(f, 'r') as fd: 
        c = compile(fd.read(), f, 'exec')
    n = len(module_list)
    current_module = None
    current_proc = None
    exec(c, new_globals())
    if len(module_list) <= n:
        fatal(f"no module found")

def read_lib(l):
    '''Search a library file along the library path and read it.'''
    for d in (args.L or []) + [lccdir]:
        f = os.path.join(d, f"lib{l}.a")
        if os.access(f, os.R_OK):
            return read_file(f)
    fatal(f"library -l{l} not found!")

def read_map(m):
    dn = os.path.dirname(__file__)
    fn = os.path.join(dn, f"map{m}", "map.py")
    if not os.access(fn, os.R_OK):
        fatal(f"Cannot find linker map '{m}'")
        with open(fn, 'r') as fd: 
            exec(compile(fd.read(), fn, 'exec'))

def read_interface():
    global symdefs
    with open(os.path.join(lccdir,'interface.json')) as file:
        for (name, value) in json.load(file).items():
            symdefs[name] = value if isinstance(value, int) else int(value, base=0)

def read_rominfo(rom):
    global rominfo
    with open(os.path.join(lccdir,'roms.json')) as file:
        d = json.load(file)
        if rom in d:
            rominfo = d[args.rom]
    if not rominfo:
        print(f"glink: warning: rom '{args.rom}' is not recognized", file=sys.stderr)
    
    
# ------------- main function


def main(argv):
    '''Main entry point'''
    global lccdir, args, rominfo, symdefs
    try:
        ## Obtain LCCDIR
        lccdir = os.getenv("LCCDIR", default=lccdir)

        ## Parse arguments
        parser = argparse.ArgumentParser(
            conflict_handler='resolve',allow_abbrev=False,
            usage='glink [options] {<files.o>} -l<lib> -o <outfile.gt1>',
            description='Collects gigatron .{s,o,a} files into a .gt1 file.',
            epilog=''' 
            	This program accepts the modules generated by
                gigatron-lcc/rcc (suffix .s or .o). These files are
                text files with a python syntax. They contain a single
                function that defines all the VCPU instructions,
                labels and data for this module.  Glink also accepts
                concatenation of such files forming a library (suffix
                .a).  The -cpu, -rom, and -map options provide values
                than handcrafted code inside a module can test to
                select different implementations. The -cpu option
                enables instructions that were added in successive
                implementations of the Gigatron VCPU.  The -rom option
                informs the libraries about the availability of
                natively implemented SYS functions. The -map option
                tells at which addresses the program, the data, and
                the stack should be located. It also tells which
                runtime libraries should be loaded by default. The
                final output file includes the module that exports the
                entry point symbol, then the modules that exports all
                the symbols that it imports, then recursively all the
                modules that are needed to resolve imported
                symbols.''')
        parser.add_argument('-o', type=str, default='a.gt1', metavar='file.gt1',
                            help='select the output filename (default: a.gt1)')
        parser.add_argument('-cpu', type=int, action='store',
                            help='select the target cpu version')
        parser.add_argument('-rom', type=str, action='store',
                            help='select the target rom version')
        parser.add_argument('-map', type=str, action='store',
                            help='select a linker map')
        parser.add_argument('-v', action='count',
                            help='enable verbose output')
        parser.add_argument('-e', type=str, action='store', default='_start',
                            help='select the entry point symbol (default _start)')
        parser.add_argument('files', type=str, nargs='+',
                            help='input files')
        parser.add_argument('-l', type=str, action='append',
                            help='library files. -lxxx searches for libxxx.a')
        parser.add_argument('-L', type=str, action='append',
                            help='additional library directories')
        args = parser.parse_args(argv)

        # defaults
        if args.map == None:
            args.map = '64k'
        if args.rom == None:
            args.rom = 'v5a'
        read_rominfo(args.rom)
        if rominfo and args.cpu and args.cpu > rominfo['cpu']:
            print(f"glink: warning: rom '{args.rom}' does not implement cpu{args.cpu}", file=sys.stderr)
        if rominfo and not args.cpu:
            args.cpu = rominfo['cpu']
        if not args.cpu:
            args.cpu = 5
        read_interface()
        read_map(args.map)
        
        ### Load all .s/.o/.a files and libraries
        for f in args.files or []:
            read_file(f)
        for f in args.l or []:
            read_lib(f)

        return 0
    
    except FileNotFoundError as err:
        fatal(str(err))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
