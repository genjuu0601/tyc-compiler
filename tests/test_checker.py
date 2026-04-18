"""
Test cases for TyC Static Semantic Checker.

This module contains 100 semantic test cases covering valid programs and all
required static error categories for Assignment 3.
"""

import pytest

from tests.utils import Checker
from src.utils.nodes import (
    AssignExpr,
    BinaryOp,
    BlockStmt,
    BreakStmt,
    CaseStmt,
    ContinueStmt,
    DefaultStmt,
    FloatLiteral,
    ForStmt,
    FuncCall,
    Identifier,
    IfStmt,
    IntLiteral,
    IntType,
    MemberAccess,
    PostfixOp,
    PrefixOp,
    ReturnStmt,
    StringLiteral,
    StructLiteral,
    SwitchStmt,
    VarDecl,
    WhileStmt,
)


def run_checker(source: str) -> str:
    return Checker(source).check_from_source()


def stmt_error(stmt) -> str:
    return f"TypeMismatchInStatement({stmt})"


def expr_error(expr) -> str:
    return f"TypeMismatchInExpression({expr})"


def loop_error(stmt) -> str:
    return f"MustInLoop({stmt})"


def ids_from_range(start: int, count: int) -> list[str]:
    return [f"test_{index:03d}" for index in range(start, start + count)]


VALID_CASES = [
    ("void main() { int x = 5; int y = x + 1; }", "Static checking passed"),
    (
        "void main() { auto x = 10; auto y = 3.14; auto z = x + y; }",
        "Static checking passed",
    ),
    (
        "int add(int x, int y) { return x + y; } void main() { int sum = add(5, 3); }",
        "Static checking passed",
    ),
    (
        "struct Point { int x; int y; }; void main() { Point p; p.x = 10; p.y = 20; }",
        "Static checking passed",
    ),
    (
        "void main() { int x = 10; { int y = 20; int z = x + y; } }",
        "Static checking passed",
    ),
    (
        "add(int x, int y) { return x + y; } void main() { auto sum = add(1, 2); }",
        "Static checking passed",
    ),
    (
        "void main() { int x = 0; while (x < 5) { if (x == 3) { break; } x = x + 1; continue; } }",
        "Static checking passed",
    ),
    (
        "void main() { for (auto i = 0; i < 3; i = i + 1) { printInt(i); } }",
        "Static checking passed",
    ),
    (
        "void main() { int x = 2; switch (x) { case 1: break; case 2: printInt(x); break; default: break; } }",
        "Static checking passed",
    ),
    (
        "struct Point { int x; int y; }; void take(Point p) { printInt(p.x); } void main() { take({1, 2}); }",
        "Static checking passed",
    ),
]


REDECLARED_CASES = [
    ("void main() { int x = 1; int x = 2; }", "Redeclared(Variable, x)"),
    ("int add(int x, int x) { return x; } void main() {}", "Redeclared(Parameter, x)"),
    (
        "int add(int x, int y) { return x + y; } int add(int a, int b) { return a - b; } void main() {}",
        "Redeclared(Function, add)",
    ),
    (
        "struct Point { int x; int y; }; struct Point { int z; }; void main() {}",
        "Redeclared(Struct, Point)",
    ),
    (
        "void main() { int x = 1; { int y = 2; int y = 3; } }",
        "Redeclared(Variable, y)",
    ),
    ("void f(int x) { int x = 1; } void main() {}", "Redeclared(Variable, x)"),
    (
        "int foo(int x) { return x; } float foo(float x) { return x; } void main() {}",
        "Redeclared(Function, foo)",
    ),
    (
        "int foo(int x) { return x; } foo(float x) { return x; } void main() {}",
        "Redeclared(Function, foo)",
    ),
    ("struct Data { int x; }; void Data() {} void main() {}", "Redeclared(Function, Data)"),
    ("void Point() {} struct Point { int x; }; void main() {}", "Redeclared(Struct, Point)"),
]


UNDECLARED_IDENTIFIER_CASES = [
    ("void main() { int x = y + 1; }", "UndeclaredIdentifier(y)"),
    ("void main() { y = 1; }", "UndeclaredIdentifier(y)"),
    ("int foo() { return y; } void main() {}", "UndeclaredIdentifier(y)"),
    ("void main() { if (y) {} }", "UndeclaredIdentifier(y)"),
    ("void main() { while (y) {} }", "UndeclaredIdentifier(y)"),
    ("void main() { printInt(y); }", "UndeclaredIdentifier(y)"),
    ("void main() { y.x = 1; }", "UndeclaredIdentifier(y)"),
    ("void main() { { int y = 1; } printInt(y); }", "UndeclaredIdentifier(y)"),
    ("void main() { switch (y) { default: break; } }", "UndeclaredIdentifier(y)"),
    ("void main() { auto x = 1; auto z = x + y; }", "UndeclaredIdentifier(y)"),
]


UNDECLARED_FUNCTION_CASES = [
    ("void main() { foo(); }", "UndeclaredFunction(foo)"),
    ("void main() { int x = foo(); }", "UndeclaredFunction(foo)"),
    ("void main() { printInt(foo()); }", "UndeclaredFunction(foo)"),
    ("void main() { int x = 1; x = foo(); }", "UndeclaredFunction(foo)"),
    ("int bar() { return foo(); } void main() {}", "UndeclaredFunction(foo)"),
    ("void main() { if (foo()) {} }", "UndeclaredFunction(foo)"),
    ("void main() { switch (foo()) { default: break; } }", "UndeclaredFunction(foo)"),
    (
        "void main() { add(1, 2); } int add(int x, int y) { return x + y; }",
        "UndeclaredFunction(add)",
    ),
    (
        "int bar(int x) { return x; } void main() { printInt(bar(foo())); }",
        "UndeclaredFunction(foo)",
    ),
    ("void main() { foo().x = 1; }", "UndeclaredFunction(foo)"),
]


UNDECLARED_STRUCT_CASES = [
    ("void main() { Point p; }", "UndeclaredStruct(Point)"),
    ("void f(Point p) {} void main() {}", "UndeclaredStruct(Point)"),
    ("Point make() { return {1, 2}; } void main() {}", "UndeclaredStruct(Point)"),
    ("struct Line { Point p; }; void main() {}", "UndeclaredStruct(Point)"),
    (
        "void main() { Point p = {1, 2}; } struct Point { int x; int y; };",
        "UndeclaredStruct(Point)",
    ),
    (
        "void f(Point p) {} struct Point { int x; int y; }; void main() {}",
        "UndeclaredStruct(Point)",
    ),
    (
        "Point make() { return {1, 2}; } struct Point { int x; int y; }; void main() {}",
        "UndeclaredStruct(Point)",
    ),
    (
        "struct Segment { Point a; Point b; }; struct Point { int x; int y; }; void main() {}",
        "UndeclaredStruct(Point)",
    ),
    ("struct Point { int x; int y; }; void main() { Line l; }", "UndeclaredStruct(Line)"),
    ("void main() { Unknown value = {1}; }", "UndeclaredStruct(Unknown)"),
]


TYPE_CANNOT_BE_INFERRED_CASES = [
    ("void main() { auto x; auto y; x = y; }", "TypeCannotBeInferred(x)"),
    ("void main() { auto x; auto y; y = x; }", "TypeCannotBeInferred(y)"),
    ("void main() { auto x; auto y; auto z = x + y; }", "TypeCannotBeInferred(x)"),
    ("void main() { auto x; auto y; auto z = x == y; }", "TypeCannotBeInferred(x)"),
    ("void main() { auto x; auto y; auto z = x * y; }", "TypeCannotBeInferred(x)"),
    ("void main() { auto p = {1, 2}; }", "TypeCannotBeInferred(p)"),
    ("void main() { auto x; auto y; if (x = y) {} }", "TypeCannotBeInferred(x)"),
    ("void main() { auto x; auto y; printInt(x = y); }", "TypeCannotBeInferred(x)"),
    ("foo() { auto x; return x; } void main() { foo(); }", "TypeCannotBeInferred(x)"),
    ("void main() { auto x; auto y; auto z = (x = y) + 1; }", "TypeCannotBeInferred(x)"),
]


TYPE_MISMATCH_STATEMENT_CASES = [
    (
        "void main() { float x = 1.0; if (x) {} }",
        stmt_error(IfStmt(Identifier("x"), BlockStmt([]))),
    ),
    (
        "void main() { string s = \"hi\"; while (s) {} }",
        stmt_error(WhileStmt(Identifier("s"), BlockStmt([]))),
    ),
    (
        "void main() { float x = 1.0; for (; x; ) {} }",
        stmt_error(ForStmt(None, Identifier("x"), None, BlockStmt([]))),
    ),
    (
        "void main() { float x = 1.0; switch (x) { default: break; } }",
        stmt_error(SwitchStmt(Identifier("x"), [], DefaultStmt([BreakStmt()]))),
    ),
    (
        "void main() { int x = 1; x = \"hi\"; }",
        stmt_error(AssignExpr(Identifier("x"), StringLiteral("hi"))),
    ),
    (
        "void main() { float f = 1.0; f = 1; }",
        stmt_error(AssignExpr(Identifier("f"), IntLiteral(1))),
    ),
    (
        "struct Point { int x; int y; }; struct Person { string name; int age; }; void main() { Point p; Person q; p = q; }",
        stmt_error(AssignExpr(Identifier("p"), Identifier("q"))),
    ),
    (
        "int foo() { return \"hi\"; } void main() {}",
        stmt_error(ReturnStmt(StringLiteral("hi"))),
    ),
    (
        "void main() { return 1; }",
        stmt_error(ReturnStmt(IntLiteral(1))),
    ),
    (
        "int foo() { return; } void main() {}",
        stmt_error(ReturnStmt()),
    ),
    (
        "void main() { int x = readFloat(); }",
        stmt_error(VarDecl(IntType(), "x", FuncCall("readFloat", []))),
    ),
    (
        "void main() { if (readFloat()) {} }",
        stmt_error(IfStmt(FuncCall("readFloat", []), BlockStmt([]))),
    ),
    (
        "void main() { for (int i = 0; i < 3; i = 1.5) {} }",
        stmt_error(AssignExpr(Identifier("i"), FloatLiteral(1.5))),
    ),
    (
        "void main() { switch (1) { case 1.5: break; } }",
        stmt_error(CaseStmt(FloatLiteral(1.5), [BreakStmt()])),
    ),
    (
        "foo() { if (1) return 1; return 1.5; } void main() { foo(); }",
        stmt_error(ReturnStmt(FloatLiteral(1.5))),
    ),
]


TYPE_MISMATCH_EXPRESSION_CASES = [
    (
        "void main() { int x = 1; string s = \"hi\"; int y = x + s; }",
        expr_error(BinaryOp(Identifier("x"), "+", Identifier("s"))),
    ),
    (
        "void main() { float f = 1.0; int x = 1; int y = f % x; }",
        expr_error(BinaryOp(Identifier("f"), "%", Identifier("x"))),
    ),
    (
        "void main() { int x = 1; string s = \"hi\"; int y = x < s; }",
        expr_error(BinaryOp(Identifier("x"), "<", Identifier("s"))),
    ),
    (
        "void main() { float f = 1.0; int x = 1; int y = f && x; }",
        expr_error(BinaryOp(Identifier("f"), "&&", Identifier("x"))),
    ),
    (
        "void main() { float f = 1.0; int x = !f; }",
        expr_error(PrefixOp("!", Identifier("f"))),
    ),
    (
        "void main() { float f = 1.0; ++f; }",
        expr_error(PrefixOp("++", Identifier("f"))),
    ),
    (
        "void main() { int x = 1; (x + 1)++; }",
        expr_error(PostfixOp("++", BinaryOp(Identifier("x"), "+", IntLiteral(1)))),
    ),
    (
        "void main() { int x = 1; int y = x.z; }",
        expr_error(MemberAccess(Identifier("x"), "z")),
    ),
    (
        "struct Point { int x; int y; }; void main() { Point p = {1, 2}; int z = p.z; }",
        expr_error(MemberAccess(Identifier("p"), "z")),
    ),
    (
        "void main() { printInt(\"hi\"); }",
        expr_error(FuncCall("printInt", [StringLiteral("hi")])),
    ),
    (
        "int add(int x, int y) { return x + y; } void main() { add(1); }",
        expr_error(FuncCall("add", [IntLiteral(1)])),
    ),
    (
        "void main() { int x = 1; int y = (x = \"hi\") + 1; }",
        expr_error(AssignExpr(Identifier("x"), StringLiteral("hi"))),
    ),
    (
        "void main() { int y = printInt(1) + 2; }",
        expr_error(BinaryOp(FuncCall("printInt", [IntLiteral(1)]), "+", IntLiteral(2))),
    ),
    (
        "struct Point { int x; int y; }; void take(Point p) {} void main() { take({1, \"a\"}); }",
        expr_error(StructLiteral([IntLiteral(1), StringLiteral("a")])),
    ),
    (
        "struct Point { int x; int y; }; void take(Point p) {} void main() { take({1}); }",
        expr_error(StructLiteral([IntLiteral(1)])),
    ),
]


MUST_IN_LOOP_CASES = [
    ("void main() { break; }", loop_error(BreakStmt())),
    ("void main() { continue; }", loop_error(ContinueStmt())),
    ("void main() { if (1) { break; } }", loop_error(BreakStmt())),
    ("void main() { if (1) { continue; } }", loop_error(ContinueStmt())),
    ("void main() { { break; } }", loop_error(BreakStmt())),
    ("void main() { { continue; } }", loop_error(ContinueStmt())),
    (
        "void main() { switch (1) { case 1: continue; } }",
        loop_error(ContinueStmt()),
    ),
    (
        "void main() { switch (1) { default: continue; } }",
        loop_error(ContinueStmt()),
    ),
    (
        "void helper() { break; } void main() { while (1) { helper(); } }",
        loop_error(BreakStmt()),
    ),
    (
        "void helper() { continue; } void main() { while (1) { helper(); } }",
        loop_error(ContinueStmt()),
    ),
]


@pytest.mark.parametrize(("source", "expected"), VALID_CASES, ids=ids_from_range(1, 10))
def test_valid_programs(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), REDECLARED_CASES, ids=ids_from_range(11, 10)
)
def test_redeclared_errors(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), UNDECLARED_IDENTIFIER_CASES, ids=ids_from_range(21, 10)
)
def test_undeclared_identifier_errors(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), UNDECLARED_FUNCTION_CASES, ids=ids_from_range(31, 10)
)
def test_undeclared_function_errors(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), UNDECLARED_STRUCT_CASES, ids=ids_from_range(41, 10)
)
def test_undeclared_struct_errors(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), TYPE_CANNOT_BE_INFERRED_CASES, ids=ids_from_range(51, 10)
)
def test_type_cannot_be_inferred_errors(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), TYPE_MISMATCH_STATEMENT_CASES, ids=ids_from_range(61, 15)
)
def test_type_mismatch_in_statement_errors(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), TYPE_MISMATCH_EXPRESSION_CASES, ids=ids_from_range(76, 15)
)
def test_type_mismatch_in_expression_errors(source: str, expected: str):
    assert run_checker(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), MUST_IN_LOOP_CASES, ids=ids_from_range(91, 10)
)
def test_must_in_loop_errors(source: str, expected: str):
    assert run_checker(source) == expected
