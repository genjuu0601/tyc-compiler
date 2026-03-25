"""
Lexer test cases for TyC compiler
TODO: Implement 100 test cases for lexer
"""

import pytest
from tests.utils import Tokenizer


# ========== Simple Test Cases (10 types) ==========
def test_keyword_auto():
    """1. Keyword"""
    tokenizer = Tokenizer("auto")
    assert tokenizer.get_tokens_as_string() == "auto,<EOF>"


def test_operator_assign():
    """2. Operator"""
    tokenizer = Tokenizer("=")
    assert tokenizer.get_tokens_as_string() == "=,<EOF>"


def test_separator_semi():
    """3. Separator"""
    tokenizer = Tokenizer(";")
    assert tokenizer.get_tokens_as_string() == ";,<EOF>"


def test_integer_single_digit():
    """4. Integer literal"""
    tokenizer = Tokenizer("5")
    assert tokenizer.get_tokens_as_string() == "5,<EOF>"


def test_float_decimal():
    """5. Float literal"""
    tokenizer = Tokenizer("3.14")
    assert tokenizer.get_tokens_as_string() == "3.14,<EOF>"


def test_string_simple():
    """6. String literal"""
    tokenizer = Tokenizer('"hello"')
    assert tokenizer.get_tokens_as_string() == "hello,<EOF>"


def test_identifier_simple():
    """7. Identifier"""
    tokenizer = Tokenizer("x")
    assert tokenizer.get_tokens_as_string() == "x,<EOF>"


def test_line_comment():
    """8. Line comment"""
    tokenizer = Tokenizer("// This is a comment")
    assert tokenizer.get_tokens_as_string() == "<EOF>"


def test_integer_in_expression():
    """9. Mixed: integers and operator"""
    tokenizer = Tokenizer("5+10")
    assert tokenizer.get_tokens_as_string() == "5,+,10,<EOF>"


def test_complex_expression():
    """10. Complex: variable declaration"""
    tokenizer = Tokenizer("auto x = 5 + 3 * 2;")
    assert tokenizer.get_tokens_as_string() == "auto,x,=,5,+,3,*,2,;,<EOF>"


# ========== Additional Test Cases (100+ total) ==========

lexer_cases = []

# Keywords
for kw in [
    "auto",
    "break",
    "case",
    "continue",
    "default",
    "else",
    "float",
    "for",
    "if",
    "int",
    "return",
    "string",
    "struct",
    "switch",
    "void",
    "while",
]:
    lexer_cases.append((kw, f"{kw},<EOF>"))

# Operators
for op in [
    "++",
    "--",
    "==",
    "<=",
    ">=",
    "||",
    "&&",
    "+",
    "-",
    "*",
    "/",
    "%",
    "<",
    "!",
    "=",
]:
    lexer_cases.append((op, f"{op},<EOF>"))

# Separators
for sep in ["(", ")", "{", "}", ";", ",", ":"]:
    lexer_cases.append((sep, f"{sep},<EOF>"))

# Identifiers
for ident in [
    "x",
    "_x",
    "x1",
    "x_1",
    "Abc",
    "a_b_c",
    "longIdentifier123",
]:
    lexer_cases.append((ident, f"{ident},<EOF>"))

# Integers
for num in ["0", "7", "10", "100", "255", "2500", "99999", "1234567890"]:
    lexer_cases.append((num, f"{num},<EOF>"))

# Floats
for fl in [
    "0.0",
    "3.14",
    "1.",
    ".5",
    "1e4",
    "2E-3",
    "5.67E-2",
    "12e8",
]:
    lexer_cases.append((fl, f"{fl},<EOF>"))

# Strings (valid)
lexer_cases += [
    ('"hello"', "hello,<EOF>"),
    ('"Hello, World!"', "Hello, World!,<EOF>"),
    ('"tab\\t"', "tab\\t,<EOF>"),
    ('"line\\n"', "line\\n,<EOF>"),
    ('"quote\\\""', "quote\\\",<EOF>"),
    ('"backslash\\\\ "', "backslash\\\\ ,<EOF>"),
    ('"mix \\t \\n \\\\ "', "mix \\t \\n \\\\ ,<EOF>"),
    ('"A_B_C_123"', "A_B_C_123,<EOF>"),
]

# Mixed tokens
lexer_cases += [
    ("int x=1;", "int,x,=,1,;,<EOF>"),
    ("float y=3.14;", "float,y,=,3.14,;,<EOF>"),
    ("string s=\"hi\";", "string,s,=,hi,;,<EOF>"),
    ("a&&b", "a,&&,b,<EOF>"),
    ("!a", "!,a,<EOF>"),
    ("++i", "++,i,<EOF>"),
    ("i--", "i,--,<EOF>"),
    ("printInt(123);", "printInt,(,123,),;,<EOF>"),
    ("Point p={1,2};", "Point,p,=,{,1,,,2,},;,<EOF>"),
    ("p.x = 10;", "p,.,x,=,10,;,<EOF>"),
    ("x==y", "x,==,y,<EOF>"),
    ("for(i=0;i<10;i=i+1){}", "for,(,i,=,0,;,i,<,10,;,i,=,i,+,1,),{,},<EOF>"),
    ("if(a){b=1;}else{b=2;}", "if,(,a,),{,b,=,1,;,},else,{,b,=,2,;,},<EOF>"),
]

# Comments and whitespace
lexer_cases += [
    ("// comment only", "<EOF>"),
    ("/* block comment */", "<EOF>"),
    ("// line\nint y;", "int,y,;,<EOF>"),
]

# Extra cases (add 100 more total)
extra_lexer_cases = []

for i in range(1, 21):
    extra_lexer_cases.append((f"int v{i};", f"int,v{i},;,<EOF>"))

for i in range(1, 11):
    extra_lexer_cases.append((f"auto a{i} = {i};", f"auto,a{i},=,{i},;,<EOF>"))

for i in range(1, 11):
    extra_lexer_cases.append((f"float f{i} = {i}.0;", f"float,f{i},=,{i}.0,;,<EOF>"))

for i in range(1, 11):
    extra_lexer_cases.append((f"string s{i} = \"t{i}\";", f"string,s{i},=,t{i},;,<EOF>"))

for i in range(1, 11):
    extra_lexer_cases.append(
        (f"x{i}=x{i}+{i};", f"x{i},=,x{i},+,{i},;,<EOF>")
    )

for i in range(1, 6):
    extra_lexer_cases.append((f"if({i}){{}}", f"if,(,{i},),{{,}},<EOF>"))

for i in range(1, 6):
    extra_lexer_cases.append((f"while({i}){{}}", f"while,(,{i},),{{,}},<EOF>"))

for i in range(1, 6):
    extra_lexer_cases.append(
        (
            f"for(i=0;i<{i};i=i+1){{}}",
            f"for,(,i,=,0,;,i,<,{i},;,i,=,i,+,1,),{{,}},<EOF>",
        )
    )

extra_lexer_cases += [
    ("a+b-c", "a,+,b,-,c,<EOF>"),
    ("x*y/z", "x,*,y,/,z,<EOF>"),
    ("x%y", "x,%,y,<EOF>"),
    ("p.y", "p,.,y,<EOF>"),
    ("f(1,2,3)", "f,(,1,,,2,,,3,),<EOF>"),
    ("f({1,2})", "f,(,{,1,,,2,},),<EOF>"),
    ("\"\\b\"", "\\b,<EOF>"),
    ("\"\\f\"", "\\f,<EOF>"),
    ("\"\\r\"", "\\r,<EOF>"),
    ("\"\\\\\"", "\\\\,<EOF>"),
    ("\"a\\\"b\"", "a\\\"b,<EOF>"),
    ("/*c*/int x;", "int,x,;,<EOF>"),
    ("//c\nint x;", "int,x,;,<EOF>"),
    ("struct S{int a;};", "struct,S,{,int,a,;,},;,<EOF>"),
    ("a.b.c", "a,.,b,.,c,<EOF>"),
]

lexer_cases.extend(extra_lexer_cases)

# Error cases
lexer_error_cases = [
    ("@", "Error Token @"),
    ("\"abc", "Unclosed String: abc"),
    ("\"abc\\q\"", "Illegal Escape In String: abc\\q"),
    ("auto s = \"ab\\q\";", "auto,s,=,Illegal Escape In String: ab\\q"),
    ("auto s = \"ab", "auto,s,=,Unclosed String: ab"),
]

extra_lexer_error_cases = [
    ("#", "Error Token #"),
    ("`", "Error Token `"),
    ("~", "Error Token ~"),
    ("\"ab\\x\"", "Illegal Escape In String: ab\\x"),
    ("\"\\z\"", "Illegal Escape In String: \\z"),
    ("\"ab\\", "Unclosed String: ab\\"),
    ("\"ab\n", "Unclosed String: ab"),
    ("auto s = \"a\\x\";", "auto,s,=,Illegal Escape In String: a\\x"),
    ("auto t = \"a\\z\";", "auto,t,=,Illegal Escape In String: a\\z"),
    ("auto u = \"unter", "auto,u,=,Unclosed String: unter"),
]

lexer_error_cases.extend(extra_lexer_error_cases)


@pytest.mark.parametrize("source, expected", lexer_cases)
def test_additional_lexer_cases(source, expected):
    tokenizer = Tokenizer(source)
    assert tokenizer.get_tokens_as_string() == expected


@pytest.mark.parametrize("source, expected", lexer_error_cases)
def test_lexer_error_cases(source, expected):
    tokenizer = Tokenizer(source)
    assert tokenizer.get_tokens_as_string() == expected
