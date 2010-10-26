import sys
sys.path.append("../..")

import compile.parser as parser
import compile.common as common

def convert(ast):
    """
    Convert Forp AST to a Common Lisp s-expression
    """

    return map(convert_expr, ast)

def convert_expr(ast):
    if type(ast) == common.Form:
        l = map(convert_expr, ast.l)
        for key, value in ast.d.items():
            key_name = ":" + key.s[-1] # Last part of the name, with colon before it
            l += [key_name, convert_expr(value)]
        if ast.tail:
            l.append("&rest")
            l.append(convert_expr(ast.tail))
        return l
    else:
        ast = ast.obj

    if type(ast) == common.Array:
        return ["make-array", ":initial-contents", ["list"] + map(convert_expr, ast)]
    elif type(ast) == common.Hash:
        return ["progn", ["let", [["a", ["make-hash-table"]]]] + [["setf", ["gethash", convert_expr(key), "a"], convert_expr(val)] for key, val in ast.d.items()]] + ["a"]
    elif type(ast) == common.Bool:
        if ast.b == True:
            return "t"
        elif ast.b == False:
            return "nil"
        elif ast.b == common.Maybe:
            return "?"
    elif type(ast) == common.Symbol:
        if len(ast.s) == 2 and ast.s[0] == "" and ast.s[1] in ("quote", "quote/quasi", "unquote", "unquote/list"):
            return {"quote/quasi": "quasiquote", "unquote/list": "unquote-splicing"}.get(ast.s[1], ast.s[1])
        return ":".join(ast.s)
    elif type(ast) == common.String:
        if ast.prefix != "":
            raise ValueError("Prefixes on strings not yet supported. Sorry!")
        else:
            return '"%s"' % ast.s
    elif type(ast) == common.Float:
        return repr(ast.x)
    elif type(ast) == common.Integer:
        return repr(ast.n)
    else:
        raise TypeError("Unexpected type: `%s`" % type(ast))

def sexp_to_str(sexp):
    if isinstance(sexp, str):
        return sexp
    elif len(sexp) == 2 and sexp[0] in ("quote", "quasiquote", "unquote", "unquote-splicing"):
        return {"quote": "'", "quasiquote": "`", "unquote": ",", "unquote-splicing": ",@"}[sexp[0]] + sexp_to_str(sexp[1])
    else:
        return "(" + " ".join(map(sexp_to_str, sexp)) + ")"

def sexps_to_str(sexps):
    return "\n".join(map(sexp_to_str, filter(lambda x: x, sexps)))

if __name__ == "__main__":
    print sexps_to_str(convert(parser.from_file(sys.argv[1])))

