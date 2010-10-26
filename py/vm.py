DEBUG = False

from collections import namedtuple
from datastructs import Cons
T, F, Q = "#t", "#f", "#q"

class HALT(Exception): pass
Frame = namedtuple("Frame", ["stack", "fn", "pc", "context", "pcontext"])

def print_frame(frame):
    return "%s{%s, %s}" % (frame.fn, frame.stack, frame.context)
Frame.__str__ = Frame.__repr__ = print_frame

import stdlib
class VM(object):
    def __init__(self, bytecode):
        self.code = bytecode

    def mk_state(self, n):
        stdlibframe = Frame([], None, 0, stdlib.stdlib.values(), None)
        return Cons(Frame(None, None, 0, [None]*n, stdlibframe), Cons(stdlibframe, None))
    
    def step(self, frames):
        frame = frames.car
        inst = self.code[frame.pc][0]
        if DEBUG: print "  " * (len(frames) - 1), ":".join(self.code[frame.pc]), frame.context, frame.stack

        if hasattr(self, "h" + inst):
            return getattr(self, "h" + inst)(frame, frames, *self.code[frame.pc][1:])
        else:
            raise Exception("Unknown bytecode %s" % inst)

    def hNOOP(self, frame, frames):
        return Cons(Frame(frame.stack, frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hPOP(self, frame, frames):
        return Cons(Frame(frame.stack.cdr, frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hPUSH(self, frame, frames, obj):
        # TODO Properly parse `obj`
        obj = int(obj)
        return Cons(Frame(Cons(obj, frame.stack), frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hROT(self, frame, frames):
        fst = frame.stack.car
        snd = frame.stack.cdr.car
        return Cons(Frame(Cons(snd, Cons(fst, frame.stack.cdr.cdr)), frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hDUP(self, frame, frames, n):
        n = int(n)
        assert n == 1, "n > 1 not supported"
        return Cons(Frame(Cons(frame.stack.car, frame.stack), frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hGET(self, frame, frames, n, d):
        n, d = int(n), int(d)
        cframe = frame
        for i in range(d):
            cframe = cframe.pcontext
        return Cons(Frame(Cons(cframe.context[n], frame.stack), frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hSET(self, frame, frames, n, d):
        n, d = int(n), int(d)
        cframe = frame
        for i in range(d):
            cframe = cframe.pcontext
        cframe.context[n] = frame.stack.car
        return Cons(Frame(frame.stack.cdr, frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hCALL(self, frame, frames, n):
        n = int(n)
        fn = frame.stack.car
        stack = frame.stack.cdr
        args = []
        for i in range(n):
            args.append(stack.car)
            stack = stack.cdr

        if callable(fn):
            return Cons(Frame(Cons(fn(*args), stack), frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)
        elif isinstance(fn, Frame):
            return Cons(Frame(fn.stack, fn.fn, fn.pc, args + fn.context[len(args):], fn.pcontext), Cons(Frame(stack, frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr))
        else:
            print fn

    def hGOTO(self, frame, frames, delta):
        delta = int(delta)
        return Cons(Frame(frame.stack, frame.fn, frame.pc+delta, frame.context, frame.pcontext), frames.cdr)

    def hIFT(self, frame, frames, delta):
        delta = int(delta)
        top = frame.stack.car
        stack = frame.stack.cdr

        if top and top != Q:
            return Cons(Frame(stack, frame.fn, frame.pc+delta, frame.context, frame.pcontext), frames.cdr)
        else:
            return Cons(Frame(stack, frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)
        
    def hIFF(self, frame, frames, delta):
        delta = int(delta)
        top = frame.stack.car
        stack = frame.stack.cdr

        if not top and top != Q:
            return Cons(Frame(stack, frame.fn, frame.pc+delta, frame.context, frame.pcontext), frames.cdr)
        else:
            return Cons(Frame(stack, frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hIFQ(self, frame, frames, delta):
        delta = int(delta)
        top = frame.stack.car
        stack = frame.stack.cdr

        if top == Q:
            return Cons(Frame(stack, frame.fn, frame.pc+delta, frame.context, frame.pcontext), frames.cdr)
        else:
            return Cons(Frame(stack, frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hCLSR(self, frame, frames, delta, n):
        n = int(n)
        delta = int(delta)

        nctx = [None] * n
        newframe = Frame(None, "", frame.pc + delta, nctx, frame)
        # Error, replace fn with the frame we're making. Can't figure out how.
        return Cons(Frame(Cons(newframe, frame.stack), frame.fn, frame.pc+1, frame.context, frame.pcontext), frames.cdr)

    def hHALT(self, frame, frames):
        if frames.car.fn is not None:
            top = frame.stack.car
            f = frames.cdr.car
            return Cons(Frame(Cons(top, f.stack), f.fn, f.pc, f.context, f.pcontext), frames.cdr.cdr)
        else:
            raise HALT, frame.stack.car

def read(stream): # TODO: Properly parse PUSH instructions
    n = int(stream.readline().strip())
    bytecodes = [line.strip().split() for line in stream]
    return n, bytecodes

def run(vm, state):
    while True:
        try:
            state = vm.step(state)
        except HALT as e:
            return e.args[0]

if __name__ == "__main__":
    import sys
    n, bytecodes = read(sys.stdin)
    vm = VM(bytecodes)
    run(vm, vm.mk_state(n))
