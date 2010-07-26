from collections import namedtuple

inf     = float("inf")
nan     = float("nan")
eps     = 1.0 + 1.111e-16
max     = 1.7976931348623155e+308
min     = 2.2250738585072014e-308 

Float   = namedtuple("Float",   "x")
Integer = namedtuple("Integer", "n")
String  = namedtuple("String",  "s prefix")

Array   = namedtuple("Array",   "a")
Hash    = namedtuple("Hash",    "d")

Maybe = object() # #?
Bool    = namedtuple("Bool",    "b")

nil     = None

Symbol  = namedtuple("Symbol",  "s")

class ForpObject(object):
    def __init__(self, obj, **meta):
        self.obj = obj
        self.meta = meta

    def __repr__(self):
        return repr(self.obj)

class Form(ForpObject):
    def __init__(self, args=[], kwargs={}):
        self.l = args
        self.d = kwargs
        self.meta = self.d
        self.obj = self.l

    def __getitem__(self, key):
        if isinstance(key, int) and 0 <= key < len(self.l):
            return self.l[key]
        else:
            return self.d[key]
    
    def __setitem__(self, key, value):
        if isinstance(key, int) and 0 < key < len(self.l):
            self.l[key] = value
        else:
            self.d[key] = value

    def __str__(self):
        l = []
        
        for val in self.l:
            l.append(str(val))

        for key, val in self.d.items():
            l.append(str(key) + "~" + str(val))

        return " ".join(l)

    def __len__(self):
        return len(self.l)


