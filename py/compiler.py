import parser
import common, stdlib
import sys

class Compiler(object):
    special_forms = {
        "set!": "set", "declare": "declare", "fn": "fn", "if": "if",
    }

    def __init__(self, file):
        self.symbol_table = [[], stdlib.stdlib.keys()]
        self.file = file

    def lookup(self, ast):
        for i, symbols in enumerate(self.symbol_table):
            if ast.obj.s[0] in symbols:
                return symbols.index(ast.obj.s[0]), i
        raise SyntaxError("Unknown variable `%s`" % ":".join(ast.obj.s), (file, ast.meta["row"], ast.meta["col"], ":".join(ast.obj.s)))

    def is_native(self, ast):
        if len(ast.obj.s) == 1:
            name = ast.obj.s[0]
        elif len(ast.obj.s) == 2 and ast.obj.s[0] in ("", "@"):
            name = ast.obj.s[1]
        else:
            return False

        try:
            self.lookup(common.ForpObject(common.Symbol(s=(name,)), col=ast.meta["col"], row=ast.meta["row"]))
        except SyntaxError:
            return name
        else:
            return False

    def compile_expr(self, ast):
        if isinstance(ast, common.Form):
            return self.compile_command(ast)
        elif isinstance(ast.obj, common.Integer):
            return [("PUSH", ast.obj.n)]
        elif isinstance(ast.obj, common.Float):
            return [("PUSH", ast.obj.x)]
        elif isinstance(ast.obj, common.String):
            return [("PUSH", '"%s"' % ast.obj.s)]
        elif isinstance(ast.obj, common.Bool):
            return [("PUSH", ast.obj.b)]
        elif ast.obj is None:
            return [("PUSH", "#0")]
        elif isinstance(ast.obj, common.Symbol):
            n, l = self.lookup(ast)
            return [("GET", n, l)]
        else:
            raise Exception(ast)

    def compile_set(self, ast):
        if len(ast.l) != 3:
            raise SyntaxError("`set!` takes three arguments", (file, ast.meta["row"], ast.meta["col"], "set!"))
        if not isinstance(ast.l[1].obj, common.Symbol):
            raise NotImplementedError("`set!` currently only supports symbols", (file, ast.l[1].meta["row"], ast.l[1].meta["col"], ""))

        n, l = self.lookup(ast.l[1])
        return self.compile_expr(ast.l[2]) + [("SET", n, l)]

    def compile_declare(self, ast):
        if any(not isinstance(arg.obj, common.Symbol) for arg in ast.l[1:]):
            raise SyntaxError("Can only `@declare` symbols", (file, ast.l[1].meta["row"], ast.l[1].meta["col"]))

        for symbol in ast.l[1:]:
            self.symbol_table[0].append(symbol.obj.s[0])
        
        return []

    def compile_fn(self, ast):
        self.symbol_table.insert(0, [])

        if any(not isinstance(arg.obj, common.Symbol) for arg in ast.l[1].l):
            raise NotImplementedError("Destructuring parameter lists not yet supported", (file, ast.l[1].meta["row"], ast.l[1].meta["col"], ""))

        for symbol in ast.l[1].l:
            self.symbol_table[0].append(symbol.obj.s[0])

        body = sum(map(self.compile_expr, ast.l[2:]), []) + [("HALT",)]
        body = [("CLSR", 2, len(self.symbol_table[0])), ("GOTO", len(body) + 1)] + body
        del self.symbol_table[0]
        return body

    def compile_if(self, ast):
        if len(ast.l) < 3 or len(ast.l) > 5:
            raise SyntaxError("`if` statement requires at least three arguments and at most five", (file, ast.meta["row"], ast.meta["col"], "if"))
        body = self.compile_expr(ast.l[1])
        

        trueclause  = self.compile_expr(ast.l[2]) if len(ast.l) >= 3 else []
        falseclause = self.compile_expr(ast.l[3]) if len(ast.l) >= 4 else []
        maybeclause = self.compile_expr(ast.l[4]) if len(ast.l) >= 5 else []

        if maybeclause: falseclause.append(("GOTO", len(maybeclause) + 1))
        if falseclause: trueclause.append(("GOTO", len(falseclause) + len(maybeclause) + 1))

        body += [("DUP", 1)] * (len(ast.l) - 3)

        if len(ast.l) >= 3: body += [("IFT", len(ast.l)-1)]
        if len(ast.l) >= 4: body += [("IFF", len(ast.l)-2 + len(trueclause))]
        if len(ast.l) >= 5: body += [("IFQ", len(ast.l)-3 + len(trueclause) + len(falseclause))]

        body.append(("GOTO", len(trueclause) + len(falseclause) + len(maybeclause) + 1))
        body += trueclause + falseclause + maybeclause

        return body

    def compile_command(self, ast):
        if not isinstance(ast, common.Form):
            raise SyntaxError("Top-level command not really a command!", (file, ast.meta["row"], ast.meta["col"], ""))

        name = self.is_native(ast.l[0])
        if name and name in self.special_forms:
            func = "compile_" + self.special_forms[name]
            return getattr(self, func)(ast)
        else:
            insts = sum(map(self.compile_expr, ast.l[:0:-1]), [])
            insts += self.compile_expr(ast.l[0])
            insts.append(("CALL", len(ast.l) - 1))
            return insts

    def compile(self, ast):
        """
        Compile AST to bytecode
        """

        cmds = sum(map(self.compile_command, ast), [])
        cmds.append(("HALT",))
        return cmds

if __name__ == "__main__":
    c = Compiler(sys.argv[1])
    insts = c.compile(parser.from_file(sys.argv[1]))

    print len(c.symbol_table[0])
    for inst in insts:
        print inst[0].ljust(8), " ".join(map(str, inst[1:]))

