"""
Parser test cases for TyC compiler
TODO: Implement 100 test cases for parser
"""

import pytest
from tests.utils import Parser


# ========== Simple Test Cases (10 types) ==========
def test_empty_program():
    """1. Empty program"""
    assert Parser("").parse() == "success"


def test_program_with_only_main():
    """2. Program with only main function"""
    assert Parser("void main() {}").parse() == "success"


def test_struct_simple():
    """3. Struct declaration"""
    source = "struct Point { int x; int y; };"
    assert Parser(source).parse() == "success"


def test_function_no_params():
    """4. Function with no parameters"""
    source = "void greet() { printString(\"Hello\"); }"
    assert Parser(source).parse() == "success"


def test_var_decl_auto_with_init():
    """5. Variable declaration"""
    source = "void main() { auto x = 5; }"
    assert Parser(source).parse() == "success"


def test_if_simple():
    """6. If statement"""
    source = "void main() { if (1) printInt(1); }"
    assert Parser(source).parse() == "success"


def test_while_simple():
    """7. While statement"""
    source = "void main() { while (1) printInt(1); }"
    assert Parser(source).parse() == "success"


def test_for_simple():
    """8. For statement"""
    source = "void main() { for (auto i = 0; i < 10; ++i) printInt(i); }"
    assert Parser(source).parse() == "success"


def test_switch_simple():
    """9. Switch statement"""
    source = "void main() { switch (1) { case 1: printInt(1); break; } }"
    assert Parser(source).parse() == "success"


def test_assignment_simple():
    """10. Assignment statement"""
    source = "void main() { int x; x = 5; }"
    assert Parser(source).parse() == "success"


# ========== Additional Test Cases (100+ total) ==========

valid_programs = [
    "",
    "void main() {}",
    "struct Empty {};",
    "struct Point { int x; int y; };",
    "struct Person { string name; int age; float height; };",
    "int add(int x, int y) { return x + y; }",
    "float mul(float a, float b) { return a * b; }",
    "add(int x, int y) { return x + y; }",
    "greet(string name) { printString(name); }",
    "void main() { auto x = 1; }",
    "void main() { auto x; x = 1; }",
    "void main() { int x; x = 1; }",
    "void main() { float y; y = 1.0; }",
    "void main() { string s; s = \"hi\"; }",
    "void main() { if (1) { } else { } }",
    "void main() { while (1) { break; } }",
    "void main() { for (auto i = 0; i < 10; ++i) { continue; } }",
    "void main() { for (;;){ } }",
    "void main() { for (auto i = 0; i < 3;) { i = i + 1; } }",
    "void main() { switch (1) { case 1: break; default: break; } }",
    "void main() { switch (1) { } }",
    "void main() { switch (1) { case 1: case 2: break; } }",
    "void main() { int x; x = (1 + 2) * 3; }",
    "void main() { int x; x = 1 + 2 * 3; }",
    "void main() { int x; x = (1 < 2) && (3 < 4); }",
    "void main() { int x; x = 1 == 2; }",
    "void main() { int x; x = 1 != 2; }",
    "void main() { int x; x = 1 <= 2; }",
    "void main() { int x; x = 1 >= 2; }",
    "void main() { int x; x = !1; }",
    "void main() { int x; x = -1; }",
    "void main() { int x; x = +1; }",
    "void main() { int x; x = ++x; }",
    "void main() { int x; x = x++; }",
    "void main() { int x; x = x-- ; }",
    "void main() { int x; x = (x = 5) + 7; }",
    "void main() { int x; x = 1; int y; y = x; }",
    "void main() { auto x = readInt(); printInt(x); }",
    "void main() { auto f = readFloat(); printFloat(f); }",
    "void main() { auto s = readString(); printString(s); }",
    "void main() { Point p; p = {1, 2}; }",
    "struct Point2D { int x; int y; }; struct Point3D { Point2D p; int z; }; void main() { Point3D t = {{1,2},3}; }",
    "void main() { Point p; p.x = 10; p.y = 20; }",
    "void main() { Point p; auto a = p.x; }",
    "void main() { auto p = {1, 2}; }",
    "void main() { auto p = { {1,2}, 3 }; }",
    "void main() { int x; { int y; { int z; } } }",
    "void main() { if (1) if (2) printInt(1); else printInt(0); }",
    "void main() { while (1) { if (0) break; else continue; } }",
    "void main() { int x; x = 1; x = x + 1; x = x - 1; x = x * 2; x = x / 2; x = x % 2; }",
]

for i in range(1, 7):
    valid_programs.append(f"void main() {{ int x{i}; x{i} = {i}; }}")

for i in range(1, 5):
    valid_programs.append(f"void main() {{ auto a{i} = {i}.0; }}")

for i in range(1, 4):
    valid_programs.append(
        f"void main() {{ auto i{i} = 0; while (i{i} < {i+1}) {{ ++i{i}; }} }}"
    )

for i in range(1, 4):
    valid_programs.append(
        f"void main() {{ for (auto i{i} = 0; i{i} < {i+2}; i{i} = i{i} + 1) {{ }} }}"
    )

for i in range(1, 3):
    valid_programs.append(
        f"void main() {{ if ({i} < {i+1}) printInt({i}); else printInt({i+1}); }}"
    )

for i in range(1, 3):
    valid_programs.append(
        f"void main() {{ switch ({i}) {{ case {i}: printInt({i}); break; default: break; }} }}"
    )

# More valid programs (add 100 more total in this file)
more_valid_programs = []

for i in range(1, 11):
    more_valid_programs.append(
        f"add{i}(int x, int y) {{ return x + y + {i}; }}"
    )

for i in range(1, 11):
    more_valid_programs.append(
        f"void main() {{ int a{i}; float b{i}; string c{i}; }}"
    )

for i in range(1, 11):
    more_valid_programs.append(
        f"void main() {{ {{ int x{i}; {{ float y{i}; }} }} }}"
    )

for i in range(1, 11):
    more_valid_programs.append(
        f"void main() {{ switch ({i}) {{ case {i}: case {i+1}: break; default: break; }} }}"
    )

for i in range(1, 11):
    more_valid_programs.append(
        f"void main() {{ for (auto i{i} = 0; i{i} < {i+1}; i{i} = i{i} + 1) {{ }} }}"
    )

for i in range(1, 11):
    more_valid_programs.append(
        f"struct S{i} {{ int a; int b; }}; void main() {{ S{i} s; s.a = {i}; s.b = {i+1}; }}"
    )

valid_programs.extend(more_valid_programs)


@pytest.mark.parametrize("source", valid_programs)
def test_additional_parser_cases(source):
    assert Parser(source).parse() == "success"


# ========== Syntax Error Test Cases ==========

invalid_programs = [
    ("void main( { }", "{"),
    ("void main() { int x }", "}"),
    ("struct Point { int x; int y; } void main() {}", "void"),
    ("void main() { for (auto i = 0; i < 10; ++i printInt(i); }", "printInt"),
    ("void main() { switch (1) { case 1 printInt(1); } }", "printInt"),
    ("void main() { return 1 2; }", "2"),
    ("void main() { if (1) else { } }", "else"),
    ("void main() { while (1) { break } }", "}"),
    # Missing semicolon
    ("void main() { x = 1 }", "}"),
    ("void main() { return 1 }", "}"),
    # Missing right parenthesis
    ("void main() { if (1 { } }", "{"),
    ("void main() { for (auto i = 0; i < 10; ++i { } }", "{"),
    # Missing right brace
    ("void main() { if (1) { }", "<EOF>"),
    ("struct A { int x; ", "<EOF>"),
    # Wrong case/default placement
    ("void main() { case 1: break; }", "case"),
    ("void main() { default: break; }", "default"),
    ("void main() { switch (1) { default break; } }", "break"),
    ("void main() { switch (1) { case 1 break; } }", "break"),
    # Expression syntax errors
    ("void main() { int x; x = 1 +; }", ";"),
    ("void main() { printInt(1,); }", ")"),
]

more_invalid_programs = [
    # Missing semicolon variants
    ("void main() { int x = 1 }", "}"),
    ("void main() { return 1 }", "}"),
    ("void main() { break }", "}"),
    ("void main() { continue }", "}"),
    ("void main() { if (1) { } else }", "}"),
    # Missing right parenthesis
    ("void main() { while (1 { } }", "{"),
    ("void main() { printInt(1; }", ";"),
    ("void main() { int x; x = (1 + 2; }", ";"),
    # Missing right brace
    ("void main() { while (1) { }", "<EOF>"),
    ("void main() { for (;;){ }", "<EOF>"),
    # Expression errors
    ("void main() { int x; x = ; }", ";"),
    ("void main() { int x; x = * 2; }", "*"),
    ("void main() { int x; x = 1 + * 2; }", "*"),
    ("void main() { int x; x = ( ); }", ")"),
    ("void main() { int x; x = (1 2); }", "2"),
    ("void main() { int x; x = 1, 2; }", ","),
    ("void main() { int x; x = 1 && ; }", ";"),
    ("void main() { ++; }", ";"),
    # Call/struct literal errors
    ("void main() { printInt(,1); }", ","),
    ("void main() { f(1,,2); }", ","),
    ("void main() { auto p = {,1}; }", ","),
    ("void main() { auto p = {1,2,}; }", "}"),
    # Switch/for errors
    ("void main() { case 1: break; }", "case"),
    ("void main() { default: break; }", "default"),
    ("void main() { switch (1) { case : break; } }", ":"),
    ("void main() { switch (1) { case 1 break; } }", "break"),
    ("void main() { switch (1) { default break; } }", "break"),
    ("void main() { switch (1) case 1: break; }", "case"),
    ("void main() { switch (1) { default: break; case 2 break; } }", "break"),
    ("void main() { switch (1) { case 1: break default: break; } }", "default"),
    ("void main() { for (i=0 i<10; i=i+1) {} }", "i"),
    ("void main() { for (i=0; i<10 i=i+1) {} }", "i"),
    # Misc
    ("void main() { struct S { int x; }; }", "struct"),
    ("void main() { int x; x = p.; }", ";"),
    ("void main() { int x; x = 1 == ; }", ";"),
    ("void main() { int x; x = (1 + 2)) ; }", ")"),
    ("void main() { for (auto i = 0; i < 10; ++i) break }", "}"),
    ("void main() { switch (1) { case 1: break; case 2 break; } }", "break"),
    ("void main() { return (1 + ); }", ")"),
    ("void main() { int x; x = 1 / ; }", ";"),
]

invalid_programs.extend(more_invalid_programs)


@pytest.mark.parametrize("source, offending", invalid_programs)
def test_parser_syntax_errors(source, offending):
    msg = Parser(source).parse()
    assert "Error on line" in msg
    assert f": {offending}" in msg
