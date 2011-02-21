import parser
import compiler
import vm

try:
    import readline
except ImportError:
    print "Readline support not loaded"

def read():
    return raw_input("forp> ")

def eval(str, compiler, _vm, frames):
    insts = compiler.compile(parser.from_str(str))
    n = len(compiler.symbol_table[0])

    newlen = n - len(frames.car.context)

    frames.car.context.extend([None] * newlen)
    newframes = vm.Cons(vm.Frame(None, frames.car.fn, len(_vm.code), frames.car.context, frames.car.pcontext), frames.cdr)
    _vm.code.extend(insts)

    return vm.run(_vm, newframes) # frames

def output(frames):
    if frames.car.stack:
        print frames.car.stack.car
    return frames

def loop():
    comp = compiler.Compiler(file="#?")
    _vm = vm.VM([])
    frames = _vm.mk_state(0)

    while True:
        try:
            s = read()
        except (EOFError, KeyboardInterrupt):
            return
        frames = output(eval(s, comp, _vm, frames))

if __name__ == "__main__":
    loop()
