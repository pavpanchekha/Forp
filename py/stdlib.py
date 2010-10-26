import operator
import sys

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

def opprint(*args):
    sys.stdout.write(" ".join(str(i) for i in args) + "\n")
    return args[0]

stdlib = OrderedDict([
    ("+", operator.add),
    ("-", operator.sub),
    ("*", operator.mul),
    ("/", operator.div),
    ("=", operator.eq),
    ("print", opprint),
    ("true?", bool)])
          
