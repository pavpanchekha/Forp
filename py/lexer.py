# WARNING: this module contains ugly and boring code. The tests here should
# cover most of it. Do not modify if one does not have to.

import common # Need these for data types

# How to call SyntaxError::
#
#     SyntaxError(msg, (file, line, offset, text))

def parse_int(stream, (file, char, row, col)):
    r"""
    Parses a Forp-compliant integer. Syntax:

    <integer> : <base-10-digit>*
              | a@<integer> 'r' [<base-a-digit>]*

    >>> parse_int("10", (0,0,0,0))[0]
    Integer(n=10)
    >>> parse_int("2r101", (0,0,0,0))[0]
    Integer(n=5)
    >>> parse_int("2r101r43", (0,0,0,0))[0]
    Integer(n=23)
    """

    valid_digits = "0123456789abcdefghijklmnopq"
    def parse_int_base(stream, (file, char, row, col), base):
        valid_digits_base = valid_digits[:base]
        if stream[char].lower() not in valid_digits_base:
            raise SyntaxError("Invalid radix-%d digit: `%s`" % (base, stream[char]), (file, row, col, stream[char]))

        digits = []
        while len(stream) > char and stream[char].lower() in valid_digits_base:
            digits.append(stream[char])
            char += 1
            col  += 1
        return int("".join(digits), base), (file, char, row, col)
    
    to_negate = False
    
    if len(stream) > char and stream[char] == "-":
        to_negate = True
        char += 1; col += 1
    elif len(stream) > char and stream[char] == "+":
        char += 1; col += 1
    elif len(stream) <= char or not stream[char].isdigit():
        raise SyntaxError("Invalid radix-10 digit: `%s`" % stream[char], (file, row, col, stream[char]))

    val, (file, char, row, col) = parse_int_base(stream,
            (file, char, row, col), 10)
    
    while len(stream) > char and stream[char] == "r":
        val, (file, char, row, col) = parse_int_base(stream,
                (file, char+1, row, col+1), val)

    if to_negate:
        val = -val

    return common.Integer(val), (file, char, row, col)

def parse_float(stream, (file, char, row, col)):
    r"""
    Parses a Forp-compliant floating-point. Syntax:

    <float> : [-+] <10digits> '.' <10digits> 'e' [-+] <10digits>

    Where components may be missing, and where <10digits> represents a string
    of radix-10 digits.

    >>> parse_float("1.", (0,0,0,0))[0]
    Float(x=1.0)
    >>> parse_float("1.2", (0,0,0,0))[0]
    Float(x=1.2)
    >>> parse_float("2.2e3", (0,0,0,0))[0]
    Float(x=2200.0)
    >>> parse_float("-2.3e-3", (0,0,0,0))[0]
    Float(x=-0.0023)
    """
    
    def parse_base_10(stream, (file, char, row, col)):
        init_char = char
        while len(stream) > char and stream[char].isdigit():
            char += 1
            col  += 1
        if init_char == char:
            return 0, (file, char, row, col)
        else:
            return int(stream[init_char:char]), (file, char, row, col)

    to_negate = False
    to_negate_mantissa = False

    if len(stream) > char and stream[char] == "-":
        to_negate = True
        char += 1; col += 1
    elif len(stream) > char and stream[char] == "+":
        char += 1; col += 1

    float_parts = [0, 0, 0] # before dot, after dot, mantissa
    if len(stream) > char and stream[char].isdigit():
        float_parts[0], (file, char, row, col) = parse_base_10(stream, (file, char, row, col))
    elif len(stream) <= char or stream[char] not in ".e":
        raise SyntaxError("Invalid start of floating-point number: `%s`" % stream[char], (file, row, col, stream[char]))
    
    if len(stream) > char and stream[char] == ".":
        char += 1; col += 1
        float_parts[1], (file, char, row, col) = parse_base_10(stream, (file, char, row, col))
    
    if len(stream) > char and stream[char] == "e":
        char += 1; col += 1

        if len(stream) > char and stream[char] == "-":
            to_negate_mantissa = True
            char += 1; col += 1
        elif len(stream) > char and stream[char] == "+":
            char += 1; col += 1

        float_parts[2], (file, char, row, col) = parse_base_10(stream, (file, char, row, col))
    
    return common.Float(float("%s%d.%de%s%d" % ("-" if to_negate else "+", float_parts[0], float_parts[1], "-" if to_negate_mantissa else "+", float_parts[2]))), (file, char, row, col)

def parse_string(stream, (file, char, row, col)):
    r"""
    Parses a Forp-compliant string. Syntax:

    <string> : <lower-case>? '"' [^\n] '"'

    >>> parse_string('"adsf"', (0,0,0,0))[0]
    String(s='adsf', prefix='')
    >>> parse_string('r"asdf"', (0,0,0,0))[0]
    String(s='asdf', prefix='r')
    >>> parse_string(r'p"asdf\"/asdf"', (0,0,0,0))[0]
    String(s='asdf\\"/asdf', prefix='p')
    >>> parse_string(r'x"^r\"\["', (0,0,0,0))[0]
    String(s='^r\\"\\[', prefix='x')
    """
    
    prefix = ""
    
    if len(stream) > char and stream[char].islower():
        prefix = stream[char]
        char += 1; col += 1;
    
    if len(stream) <= char or stream[char] != "\"":
        raise SyntaxError("Illegal start of string: `%s`" % stream[char], (file, row, col, stream[char]))
        
    char += 1; col += 1
    init_char = char

    while len(stream) > char and stream[char] != "\"":
        char += 1; col += 1
        if stream[char-1] == "\\":
            char += 1; col += 1
        if stream[char-1] == "\n":
            raise SyntaxError("Illegal newline in string", (file, row, col, stream[char]))
    
    char += 1; col += 1
    return common.String(stream[init_char:char-1], prefix), (file, char, row, col)

def parse_special(stream, (file, char, row, col)):
    if   stream[char:char+5] == "-#inf":
        return common.Float(-common.inf), (file, char+5, row, col+5)
    elif stream[char:char+4] == "#inf":
        return common.Float(common.inf),  (file, char+4, row, col+4)
    elif stream[char:char+5] == "-#max":
        return common.Float(-common.max), (file, char+5, row, col+5)
    elif stream[char:char+4] == "#max":
        return common.Float(common.max),  (file, char+4, row, col+4)
    elif stream[char:char+5] == "-#min":
        return common.Float(-common.min), (file, char+5, row, col+5)
    elif stream[char:char+4] == "#min":
        return common.Float(common.min),  (file, char+4, row, col+4)
    elif stream[char:char+5] == "-#eps":
        return common.Float(-common.eps), (file, char+5, row, col+5)
    elif stream[char:char+4] == "#eps":
        return common.Float(common.eps),  (file, char+4, row, col+4)
    elif stream[char:char+2] == "#t":
        return common.Bool(True),         (file, char+2, row, col+2)
    elif stream[char:char+2] == "#f":
        return common.Bool(False),        (file, char+2, row, col+2)
    elif stream[char:char+2] == "#?":
        return common.Bool(common.Maybe), (file, char+2, row, col+2)
    elif stream[char:char+2] == "#0":
        return common.nil,                (file, char+2, row, col+2)
    else:
        raise SyntaxError("Invalid special symbol", (file, row, col, stream[char]))

def parse_symbol(stream, (file, char, row, col)):
    r"""
    Parses a Forp identifier. Syntax:

    <string> : <lower-case>? '"' [^\n] '"'

    >>> parse_symbol('name', (0,0,0,0))[0]
    Symbol(s=('name',))
    >>> parse_symbol('type/*', (0,0,0,0))[0]
    Symbol(s=('type/*',))
    >>> parse_symbol('www:open', (0,0,0,0))[0]
    Symbol(s=('www', 'open'))
    >>> parse_symbol('*:_-$:/\\', (0,0,0,0))[0]
    Symbol(s=('*', '_-$', '/\\'))
    """

    valid_punct = "!@$%^*_-?=+/\\<>"

    if len(stream) <= char or not (stream[char].islower() or stream[char] in valid_punct):
        raise SyntaxError("Invalid start of symbol: `%s`" % stream[char], (file, row, col, stream[char]))

    symbol = []
    brk = False

    while not brk:
        init_char = char
        while len(stream) > char and (stream[char].isalnum() or stream[char] in valid_punct):
            char += 1
            col += 1
        symbol.append(stream[init_char:char])
        if len(stream) > char and stream[char] == ":":
            char += 1
            col += 1
        else:
            brk = True
    
    return common.Symbol(tuple(symbol)), (file, char, row, col)

def parse_number(stream, (file, char, row, col)):
    r"""
    Parses a Forp-compliant number; a float or integer. Syntax:

    >>> parse_number('1.2e3', (0,0,0,0))[0]
    Float(x=1200.0)
    >>> parse_number('1', (0,0,0,0))[0]
    Integer(n=1)
    """

    if len(stream) <= char or not (stream[char].isdigit() or stream[char] in "-+.e#"):
        raise SyntaxError("Invalid start of number: `%s`" % stream[char], (file, row, col, stream[char]))

    char2 = char
    if len(stream) > char2 and stream[char2] in "-+":
        char2 += 1
    
    while len(stream) > char2 and stream[char2].isdigit():
        char2 += 1
    
    if len(stream) <= char2 or (stream[char2].isspace() or stream[char2] == "r"):
        return parse_int(stream, (file, char, row, col))
    elif len(stream) > char2 and stream[char2] in ".e":
        return parse_float(stream, (file, char, row, col))
    elif len(stream) > char2 and stream[char2] == "#":
        return parse_special(stream, (file, char, row, col))
    else:
        return parse_int(stream, (file, char, row, col))

def parse_num_sym(stream, (file, char, row, col)):
    char2 = char

    if len(stream) > char2 and stream[char2] == "\"" or len(stream) > char2 + 1 and stream[char2].islower() and stream[char2+1] == "\"":
        return parse_string(stream, (file, char, row, col))
    
    if len(stream) > char2 and stream[char2] == "-":
        char2 += 1
    
    if len(stream) > char2 and stream[char2] in "0123456789.#":
        return parse_number(stream, (file, char, row, col))
    else:
        return parse_symbol(stream, (file, char, row, col))

def parse_whitespace(stream, (file, char, row, col)):
    r"""
    Recognizes and consumes whitespace and comments.

    >>> parse_whitespace('   a', (0, 0, 0, 0))[1][1]
    3
    >>> parse_whitespace(' a   b', (0, 0, 0, 0))[1][1]
    1
    """

    while len(stream) > char and stream[char] == " ":
        char += 1; col += 1
    
    if len(stream) > char and stream[char] == "\t":
        raise SyntaxError("Tabs not allowed in Forp code", (file, row, col, "\t"))
    elif len(stream) > char and stream[char] == ";":
        while len(stream) > char and stream[char] == " ":
            char += 1; col += 1

    # TODO: #;, #| ... |#, and #> ... <#

    return None, (file, char, row, col)

def tokenize(stream, file):
    r"""
    Tokenizes Forp source code

    >>> [tok.obj for tok in tokenize('print "asdf" 1 -> + 4 3', 0)]
    [Symbol(s=('print',)), String(s='asdf', prefix=''), Integer(n=1), '->', Symbol(s=('+',)), Integer(n=4), Integer(n=3), 'EOF']
    >>> [tok.obj for tok in tokenize("if (= a b) ->\n    just a\n    print\n        'a\n        'b", 0)]
    [Symbol(s=('if',)), '(', Symbol(s=('=',)), Symbol(s=('a',)), Symbol(s=('b',)), ')', '->', '\n', 'INDENT', Symbol(s=('just',)), Symbol(s=('a',)), '\n', Symbol(s=('print',)), '\n', 'INDENT', "'", Symbol(s=('a',)), '\n', "'", Symbol(s=('b',)), 'DEDENT', 'DEDENT', 'EOF']
    """
    
    indent_stack = [0]
    _, (file, char, row, col) = parse_whitespace(stream, (file, 0, 0, 0))
    
    tokens = []
    while len(stream) > char:
        if stream[char] in "([{)]}~|`'.,&":
            tokens.append(common.ForpObject(stream[char], row=row, col=col))
            char += 1; col += 1
        elif stream[char:char+2] == "->":
            tokens.append(common.ForpObject("->", row=row, col=col))
            char += 2; col += 2
        elif stream[char:char+2] == "<-":
            tokens.append(common.ForpObject("<-", row=row, col=col))
            char += 2; col += 2
        elif stream[char] == "\n":
            tokens.append(common.ForpObject("\n", row=row, col=col))
            
            while len(stream) > char and stream[char] == "\n":
                row += 1; char += 1; col = 1
                _, (_, char2, _, _) = parse_whitespace(stream, (file, char, row, col))
                if len(stream) > char2 and stream[char2] != "\n":
                    break
                else:
                    char = char2
                   
            indent = char2 - char
            if indent > indent_stack[-1]:
                tokens.append(common.ForpObject("INDENT", row=row, col=col))
                indent_stack.append(indent)
            else:
                while indent < indent_stack[-1]:
                    tokens.append(common.ForpObject("DEDENT", row=row, col=col))
                    indent_stack.pop()
                 
                if indent != indent_stack[-1]: # Indent not in stack
                    raise SyntaxError("Invalid indentation", (file, row, col, stream[char]))
        else:
            val, (file, char2, row2, col2) = parse_num_sym(stream, (file, char, row, col))
            tokens.append(common.ForpObject(val, row=row, col=col))
            char = char2; row = row2; col = col2
        _, (file, char, row, col) = parse_whitespace(stream, (file, char, row, col))
    
    finalrow = stream.count("\n")+1
    finalcol = len(stream) - stream.rfind("\n")
    return tokens + [common.ForpObject("DEDENT", row=finalrow, col=finalcol)] * (len(indent_stack) - 1) + [common.ForpObject("EOF", row=finalrow, col=finalcol)]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
