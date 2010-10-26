
# MASTER SYNTAX DEFINITION:
# <expr> : '\'' <expr>
#        | '`'  <expr>
#        | '.'  <expr>
#        | ','  <expr>
#        | <expr> '|' <arg>
#        | <array> | <hash> | <int> | <float> | <ident> | <string> | <special>
#        | '(' <expr ')'
#        | '(' '\n' INDENT <expr> '\n' DEDENT ')'
#
# <layout> : INDENT <command>* DEDENT
#
# <arg> : <expr>
#       | <ident> '~' <expr>
#
# <command> : <arg>* ('\n' INDENT <command>* DEDENT)? '\n'
#           | <command> '&' <ident>
#           | <command> '<-' <command> '\n'
#           | <command> '<-' '\n' <layout>
#
# <array> : '[' <expr>* ']'
#         | '[' '\n' <layout> ']'
#
# <hash> : '{' (<expr> <expr>)* '}'
#        | '{' '\n' <layout> '}'
# <TOP> : <command> *

# All right, let's go a-implementing!

DEBUG = False

def loud(f):
    if not DEBUG: return f

    def inner(*args, **kwargs):
        print "ENTERING::", "%s(%s, %s)" % (f, ", ".join(map(repr, args)), ["%s=%s" % (key, repr(val)) for key, val in kwargs.items()])
        res = f(*args, **kwargs)
        print "%s(%s, %s) = %s" % (f, ", ".join(map(repr, args)), ["%s=%s" % (key, repr(val)) for key, val in kwargs.items()], res)
        return res
    return inner

import common
import lexer
import warnings

@loud
def parse_expr(tokens, (ptr, file)):
    prefix_map = dict(zip("'`.,", ["quote", "quote/quasi", "unquote", "unquote/list"]))
    grouper_map = dict(zip("([{", zip(")]}", [parse_command, parse_array, parse_hash])))

    if not isinstance(tokens[ptr].obj, str):
        return tokens[ptr], ptr+1
    if tokens[ptr].obj in prefix_map:
        res, ptr2 = parse_expr(tokens, (ptr+1, file))
        return common.Form([common.ForpObject(common.Symbol(s=("", prefix_map[tokens[ptr].obj]))), res]), ptr2
    elif tokens[ptr].obj in grouper_map:
        end, fn = grouper_map[tokens[ptr].obj]
        res, ptr2 = fn(tokens, (ptr+1, file))
        
        if tokens[ptr2].obj == end:
            return res, ptr2+1
        else:
            raise SyntaxError("Expecting `%s`, not `%s`" % (end, tokens[ptr2].obj), (file, tokens[ptr2].meta["row"], tokens[ptr2].meta["col"], tokens[ptr2].obj))
    elif tokens[ptr].obj == "|":
        if ptr == 0:
            raise SyntaxError("Invalid `|` at start of file", (file, 1, 1, "|"))
         
        arg, ptr2 = parse_arg(tokens, (ptr+1, file))
        if isinstance(arg, tuple):
            return common.Form([common.Symbol(s=("", "tag")), tokens[ptr-1].obj, arg[0], arg[1]]), ptr
        else:
            return common.Form([common.Symbol(s=("", "tag")), tokens[ptr-1].obj, arg]), ptr
    else:
        raise SyntaxError("Unexpected `%s`" % tokens[ptr].obj, (file, tokens[ptr].meta["row"], tokens[ptr].meta["col"], tokens[ptr].obj))

@loud
def parse_array(tokens, (ptr, file)):
    if tokens[ptr].obj == "\n":
        res, ptr2 = parse_layout(tokens, (ptr+1, file))
        return common.ForpObject(common.Array(res)), ptr2
    else:
        values = []
        while tokens[ptr].obj != "]":
            res, ptr = parse_expr(tokens, (ptr, file))
            values.append(res)
        return common.ForpObject(common.Array(values)), ptr

@loud
def parse_hash(tokens, (ptr, file)):
    if tokens[ptr].obj == "\n":
        res, ptr2 = parse_layout(tokens, (ptr+1, file))

        for cmd in res:
            print repr(cmd)
            if len(cmd) != 2:
                raise SyntaxError("Hash element `%s` is not two elements long" % cmd, (file, cmd[0].meta["row"], cmd[0].meta["col"], str(cmd)))
            if cmd.d:
                raise SyntaxError("Hash element `%s` has keyword arguments" % cmd, (file, cmd[0].meta["row"], cmd[0].meta["col"], str(cmd)))

        return common.ForpObject(common.Hash(dict((elem[0], elem[1]) for elem in res))), ptr2
    else:
        values = {}
        while tokens[ptr].obj != "}":
            key, ptr = parse_expr(tokens, (ptr, file))
            val, ptr = parse_expr(tokens, (ptr, file))
            values[key] = val
        return common.ForpObject(common.Hash(values)), ptr

@loud
def parse_layout(tokens, (ptr, file)):
    if tokens[ptr].obj == "INDENT":
        ptr += 1

        commands = []
        while tokens[ptr].obj != "DEDENT":
            cmd, ptr = parse_command(tokens, (ptr, file))
            commands.append(cmd)
        return commands, ptr+1
    else:
        raise SyntaxError("Layout must begin with an indentation", (file, tokens[ptr].meta["row"], tokens[ptr].meta["col"], ""))

@loud
def parse_arg(tokens, (ptr, file)):
    if isinstance(tokens[ptr].obj, common.Symbol) and tokens[ptr+1].obj == "~":
        key = tokens[ptr].obj
        res, ptr = parse_expr(tokens, (ptr+2, file))
        return (key, res), ptr
    else:
        return parse_expr(tokens, (ptr, file))

@loud
def parse_command(tokens, (ptr, file)):
    l = []
    d = {}
    while True: # Will break out due to returns
        if tokens[ptr].obj == "\n":
            if tokens[ptr+1].obj == "INDENT":
                cmds, ptr = parse_layout(tokens, (ptr+1, file))

                for cmd in cmds:
                    l.extend(cmd.l)
                    d.update(cmd.d)

                return common.Form(l, d), ptr
            else:
                return common.Form(l, d), ptr+1
        elif tokens[ptr].obj == "<-":
            if tokens[ptr+1].obj == "\n":
                if tokens[ptr+2].obj == "INDENT":
                    cmds, ptr = parse_layout(tokens, (ptr+2, file))
                    l.extend(cmds)
                    return common.Form(l, d), ptr
                else:
                    warnings.warn_explicit("Using empty layout --- did you forget to indent?", SyntaxWarning, file, tokens[ptr+1].meta["row"])
            else:
                cmd, ptr = parse_command(tokens, (ptr+1, file))
                l.append(cmd)
                return common.Form(l, d), ptr
        elif tokens[ptr].obj in ("EOF", ")"):
            return common.Form(l, d), ptr
        elif tokens[ptr].obj == "&":
            tail, ptr = parse_expr(tokens, (ptr+1, file))
            form = common.Form(l, d)
            form.tail = tail
            return form, ptr
        else:
            arg, ptr = parse_arg(tokens, (ptr, file))
            if type(arg) == type(()):
                d[arg[0]] = arg[1]
            else:
                l.append(arg)

@loud
def parse(tokens, file):
    ptr = 0

    commands = []
    while tokens[ptr].obj != "EOF":
        cmd, ptr = parse_command(tokens, (ptr, file))
        commands.append(cmd)

    return commands

def from_str(str, file="#?"):
    tokens = lexer.tokenize(str, file)
    return parse(tokens, file)

def from_file(file):
    return from_str(open(file).read(), file)
