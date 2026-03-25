"""
Custom AST generation tests aligned with the current nodes.py output.
"""

import pytest

from src.utils.nodes import (
    AssignExpr,
    BinaryOp,
    BlockStmt,
    CaseStmt,
    DefaultStmt,
    ExprStmt,
    FloatLiteral,
    ForStmt,
    FuncCall,
    FuncDecl,
    Identifier,
    IfStmt,
    IntLiteral,
    MemberAccess,
    PostfixOp,
    PrefixOp,
    StringLiteral,
    StructDecl,
    StructLiteral,
    SwitchStmt,
    WhileStmt,
)
from tests.utils import ASTGenerator


def assert_ast(source, expected):
    assert str(ASTGenerator(source).generate()) == expected


AST_SNAPSHOTS = [
    pytest.param("", "Program([])", id="empty-program"),
    pytest.param(
        "struct Point { int x; int y; };",
        "Program([StructDecl(Point, [MemberDecl(IntType(), x), MemberDecl(IntType(), y)])])",
        id="struct-basic",
    ),
    pytest.param(
        "void main() {}",
        "Program([FuncDecl(VoidType(), main, [], [])])",
        id="func-void-empty",
    ),
    pytest.param(
        "sum(int a, int b) { return a + b; }",
        "Program([FuncDecl(auto, sum, [Param(IntType(), a), Param(IntType(), b)], [ReturnStmt(return BinaryOp(Identifier(a), +, Identifier(b)))])])",
        id="func-inferred-return",
    ),
    pytest.param(
        "struct A {}; void main() {} struct B { string s; };",
        "Program([StructDecl(A, []), FuncDecl(VoidType(), main, [], []), StructDecl(B, [MemberDecl(StringType(), s)])])",
        id="mixed-top-level",
    ),
    pytest.param(
        "void main() { int x; auto y = 2; }",
        "Program([FuncDecl(VoidType(), main, [], [VarDecl(IntType(), x), VarDecl(auto, y = IntLiteral(2))])])",
        id="vars-basic",
    ),
    pytest.param(
        "void main() { { auto x = 1; } }",
        "Program([FuncDecl(VoidType(), main, [], [BlockStmt([VarDecl(auto, x = IntLiteral(1))])])])",
        id="nested-block",
    ),
    pytest.param(
        "void main() { if (x) { y = 1; } else { y = 2; } }",
        "Program([FuncDecl(VoidType(), main, [], [IfStmt(if Identifier(x) then BlockStmt([ExprStmt(AssignExpr(Identifier(y) = IntLiteral(1)))]), else BlockStmt([ExprStmt(AssignExpr(Identifier(y) = IntLiteral(2)))]))])])",
        id="if-else-blocks",
    ),
    pytest.param(
        "void main() { while (x) { break; continue; } }",
        "Program([FuncDecl(VoidType(), main, [], [WhileStmt(while Identifier(x) do BlockStmt([BreakStmt(), ContinueStmt()]))])])",
        id="while-break-continue",
    ),
    pytest.param(
        "void main() { for (auto i = 0; i < 10; i++) {} }",
        "Program([FuncDecl(VoidType(), main, [], [ForStmt(for VarDecl(auto, i = IntLiteral(0)); BinaryOp(Identifier(i), <, IntLiteral(10)); PostfixOp(Identifier(i)++) do BlockStmt([]))])])",
        id="for-basic",
    ),
    pytest.param(
        "void main() { for (p.x = 0; p.x < 5; ++p.x) {} }",
        "Program([FuncDecl(VoidType(), main, [], [ForStmt(for ExprStmt(AssignExpr(MemberAccess(Identifier(p).x) = IntLiteral(0))); BinaryOp(MemberAccess(Identifier(p).x), <, IntLiteral(5)); PrefixOp(++MemberAccess(Identifier(p).x)) do BlockStmt([]))])])",
        id="for-member-update",
    ),
    pytest.param(
        "void main() { switch (x) { case 1: case 2: x = 1; break; default: return; } }",
        "Program([FuncDecl(VoidType(), main, [], [SwitchStmt(switch Identifier(x) cases [CaseStmt(case IntLiteral(1): []), CaseStmt(case IntLiteral(2): [ExprStmt(AssignExpr(Identifier(x) = IntLiteral(1))), BreakStmt()])], default DefaultStmt(default: [ReturnStmt(return)]))])])",
        id="switch-fallthrough",
    ),
    pytest.param(
        "int main() { return add(1, 2); }",
        "Program([FuncDecl(IntType(), main, [], [ReturnStmt(return FuncCall(add, [IntLiteral(1), IntLiteral(2)]))])])",
        id="return-call",
    ),
    pytest.param(
        "void main() { auto x = 1 + 2 * 3 - 4; }",
        "Program([FuncDecl(VoidType(), main, [], [VarDecl(auto, x = BinaryOp(BinaryOp(IntLiteral(1), +, BinaryOp(IntLiteral(2), *, IntLiteral(3))), -, IntLiteral(4)))])])",
        id="precedence",
    ),
    pytest.param(
        "void main() { auto x = (1 < 2) && (3 < 4) || !0; }",
        "Program([FuncDecl(VoidType(), main, [], [VarDecl(auto, x = BinaryOp(BinaryOp(BinaryOp(IntLiteral(1), <, IntLiteral(2)), &&, BinaryOp(IntLiteral(3), <, IntLiteral(4))), ||, PrefixOp(!IntLiteral(0))))])])",
        id="logical-chain",
    ),
    pytest.param(
        "void main() { a = b = c = 1; }",
        "Program([FuncDecl(VoidType(), main, [], [ExprStmt(AssignExpr(Identifier(a) = AssignExpr(Identifier(b) = AssignExpr(Identifier(c) = IntLiteral(1)))))])])",
        id="assign-assoc",
    ),
    pytest.param(
        "void main() { ++--x; }",
        "Program([FuncDecl(VoidType(), main, [], [ExprStmt(PrefixOp(++PrefixOp(--Identifier(x))))])])",
        id="prefix-chain",
    ),
    pytest.param(
        "void main() { foo(1).x.y++; }",
        "Program([FuncDecl(VoidType(), main, [], [ExprStmt(PostfixOp(MemberAccess(MemberAccess(FuncCall(foo, [IntLiteral(1)]).x).y)++))])])",
        id="postfix-member",
    ),
    pytest.param(
        "void main() { auto v = getLine().start.x; }",
        "Program([FuncDecl(VoidType(), main, [], [VarDecl(auto, v = MemberAccess(MemberAccess(FuncCall(getLine, []).start).x))])])",
        id="member-call-chain",
    ),
    pytest.param(
        "void main() { auto p = {{1, 2}, 3}; }",
        "Program([FuncDecl(VoidType(), main, [], [VarDecl(auto, p = StructLiteral({StructLiteral({IntLiteral(1), IntLiteral(2)}), IntLiteral(3)}))])])",
        id="struct-literal-nested",
    ),
    pytest.param(
        r'void main() { auto s = "a\nb"; }',
        r"Program([FuncDecl(VoidType(), main, [], [VarDecl(auto, s = StringLiteral('a\\nb'))])])",
        id="string-escape",
    ),
    pytest.param(
        "void main() { printInt(add(1, 2) * 3); }",
        "Program([FuncDecl(VoidType(), main, [], [ExprStmt(FuncCall(printInt, [BinaryOp(FuncCall(add, [IntLiteral(1), IntLiteral(2)]), *, IntLiteral(3))]))])])",
        id="call-expr-args",
    ),
    pytest.param(
        "void main() { auto x = (a = 1); }",
        "Program([FuncDecl(VoidType(), main, [], [VarDecl(auto, x = AssignExpr(Identifier(a) = IntLiteral(1)))])])",
        id="paren-assignment",
    ),
    pytest.param(
        "void main() { switch (x) { default: break; } }",
        "Program([FuncDecl(VoidType(), main, [], [SwitchStmt(switch Identifier(x) cases [], default DefaultStmt(default: [BreakStmt()]))])])",
        id="switch-default-only",
    ),
    pytest.param(
        "void main() { getPoint().x = 5; }",
        "Program([FuncDecl(VoidType(), main, [], [ExprStmt(AssignExpr(MemberAccess(FuncCall(getPoint, []).x) = IntLiteral(5)))])])",
        id="member-assign",
    ),
    pytest.param(
        "void main() { for (;;) break; }",
        "Program([FuncDecl(VoidType(), main, [], [ForStmt(for None; None; None do BreakStmt())])])",
        id="empty-for",
    ),
    pytest.param(
        "struct P { int x; int y; }; void main() { P p = {1, 2}; }",
        "Program([StructDecl(P, [MemberDecl(IntType(), x), MemberDecl(IntType(), y)]), FuncDecl(VoidType(), main, [], [VarDecl(StructType(P), p = StructLiteral({IntLiteral(1), IntLiteral(2)}))])])",
        id="struct-var-init",
    ),
    pytest.param(
        "void main() { foo({1, 2}, 3); }",
        "Program([FuncDecl(VoidType(), main, [], [ExprStmt(FuncCall(foo, [StructLiteral({IntLiteral(1), IntLiteral(2)}), IntLiteral(3)]))])])",
        id="call-struct-arg",
    ),
]


@pytest.mark.parametrize(("source", "expected"), AST_SNAPSHOTS)
def test_ast_generation_snapshots(source, expected):
    assert_ast(source, expected)


def test_func_body_is_blockstmt_object():
    ast = ASTGenerator("void main() {}").generate()
    func = ast.decls[0]
    assert func.body.__class__.__name__ == "BlockStmt"
    assert func.body.statements == []


def test_switch_fallthrough_keeps_only_last_case_statements():
    ast = ASTGenerator(
        "void main() { switch (x) { case 1: case 2: x = 1; break; } }"
    ).generate()
    switch_stmt = ast.decls[0].body.statements[0]
    assert len(switch_stmt.cases) == 2
    assert switch_stmt.cases[0].statements == []
    assert len(switch_stmt.cases[1].statements) == 2


def generate_ast(source):
    ast = ASTGenerator(source).generate()
    assert not isinstance(ast, str), ast
    return ast


def first_func(source):
    ast = generate_ast(source)
    for decl in ast.decls:
        if isinstance(decl, FuncDecl):
            return decl
    raise AssertionError("No function declaration found")


def body_stmt(source, index=0):
    return first_func(source).body.statements[index]


def auto_init_expr(expr_source):
    return body_stmt(f"void main() {{ auto x = {expr_source}; }}").init_value


def expr_stmt_expr(expr_source):
    return body_stmt(f"void main() {{ {expr_source}; }}").expr


INT_LITERAL_VALUES = [0, 1, 2, 7, 10, 42, 99, 123, 256, 999, 12345, 999999]


@pytest.mark.parametrize("value", INT_LITERAL_VALUES)
def test_int_literal_values(value):
    expr = auto_init_expr(str(value))
    assert isinstance(expr, IntLiteral)
    assert expr.value == value


FLOAT_LITERAL_CASES = [
    ("0.0", 0.0),
    ("1.", 1.0),
    (".5", 0.5),
    ("3.14", 3.14),
    ("1e2", 100.0),
    ("2E-1", 0.2),
    ("5.67E-2", 0.0567),
    ("1.23e+4", 12300.0),
]


@pytest.mark.parametrize(("source_expr", "expected"), FLOAT_LITERAL_CASES)
def test_float_literal_values(source_expr, expected):
    expr = auto_init_expr(source_expr)
    assert isinstance(expr, FloatLiteral)
    assert expr.value == pytest.approx(expected)


STRING_LITERAL_CASES = [
    ('"alpha"', "alpha"),
    ('""', ""),
    (r'"a\nb"', r"a\nb"),
    (r'"x\ty"', r"x\ty"),
    (r'"slash\\end"', r"slash\\end"),
    (r'"mix_123"', "mix_123"),
]


@pytest.mark.parametrize(("source_expr", "expected"), STRING_LITERAL_CASES)
def test_string_literal_values(source_expr, expected):
    expr = auto_init_expr(source_expr)
    assert isinstance(expr, StringLiteral)
    assert expr.value == expected


ADDITIVE_CASES = [
    ("1 + 2", "BinaryOp(IntLiteral(1), +, IntLiteral(2))"),
    ("9 - 4", "BinaryOp(IntLiteral(9), -, IntLiteral(4))"),
    (
        "1 + 2 + 3",
        "BinaryOp(BinaryOp(IntLiteral(1), +, IntLiteral(2)), +, IntLiteral(3))",
    ),
    (
        "10 - 3 - 2",
        "BinaryOp(BinaryOp(IntLiteral(10), -, IntLiteral(3)), -, IntLiteral(2))",
    ),
    (
        "1 + 2 - 3",
        "BinaryOp(BinaryOp(IntLiteral(1), +, IntLiteral(2)), -, IntLiteral(3))",
    ),
    (
        "1 - 2 + 3",
        "BinaryOp(BinaryOp(IntLiteral(1), -, IntLiteral(2)), +, IntLiteral(3))",
    ),
    (
        "1 + 2 * 3",
        "BinaryOp(IntLiteral(1), +, BinaryOp(IntLiteral(2), *, IntLiteral(3)))",
    ),
    (
        "(1 + 2) - 3",
        "BinaryOp(BinaryOp(IntLiteral(1), +, IntLiteral(2)), -, IntLiteral(3))",
    ),
    ("a + b", "BinaryOp(Identifier(a), +, Identifier(b))"),
    (
        "foo(1) + p.x",
        "BinaryOp(FuncCall(foo, [IntLiteral(1)]), +, MemberAccess(Identifier(p).x))",
    ),
]


@pytest.mark.parametrize(("expr_source", "expected"), ADDITIVE_CASES)
def test_additive_expression_shapes(expr_source, expected):
    assert str(auto_init_expr(expr_source)) == expected


MULTIPLICATIVE_CASES = [
    ("2 * 3", "BinaryOp(IntLiteral(2), *, IntLiteral(3))"),
    ("8 / 2", "BinaryOp(IntLiteral(8), /, IntLiteral(2))"),
    ("10 % 3", "BinaryOp(IntLiteral(10), %, IntLiteral(3))"),
    (
        "2 * 3 * 4",
        "BinaryOp(BinaryOp(IntLiteral(2), *, IntLiteral(3)), *, IntLiteral(4))",
    ),
    (
        "20 / 5 / 2",
        "BinaryOp(BinaryOp(IntLiteral(20), /, IntLiteral(5)), /, IntLiteral(2))",
    ),
    (
        "20 % 7 % 3",
        "BinaryOp(BinaryOp(IntLiteral(20), %, IntLiteral(7)), %, IntLiteral(3))",
    ),
    (
        "2 * 3 / 4",
        "BinaryOp(BinaryOp(IntLiteral(2), *, IntLiteral(3)), /, IntLiteral(4))",
    ),
    (
        "8 / 2 * 3",
        "BinaryOp(BinaryOp(IntLiteral(8), /, IntLiteral(2)), *, IntLiteral(3))",
    ),
    (
        "8 % 3 * 2",
        "BinaryOp(BinaryOp(IntLiteral(8), %, IntLiteral(3)), *, IntLiteral(2))",
    ),
    (
        "foo(1) * bar(2)",
        "BinaryOp(FuncCall(foo, [IntLiteral(1)]), *, FuncCall(bar, [IntLiteral(2)]))",
    ),
]


@pytest.mark.parametrize(("expr_source", "expected"), MULTIPLICATIVE_CASES)
def test_multiplicative_expression_shapes(expr_source, expected):
    assert str(auto_init_expr(expr_source)) == expected


RELATIONAL_CASES = [
    ("1 < 2", "BinaryOp(IntLiteral(1), <, IntLiteral(2))"),
    ("1 <= 2", "BinaryOp(IntLiteral(1), <=, IntLiteral(2))"),
    ("2 > 1", "BinaryOp(IntLiteral(2), >, IntLiteral(1))"),
    ("2 >= 1", "BinaryOp(IntLiteral(2), >=, IntLiteral(1))"),
    ("1 == 1", "BinaryOp(IntLiteral(1), ==, IntLiteral(1))"),
    ("1 != 2", "BinaryOp(IntLiteral(1), !=, IntLiteral(2))"),
    (
        "1 < 2 < 3",
        "BinaryOp(BinaryOp(IntLiteral(1), <, IntLiteral(2)), <, IntLiteral(3))",
    ),
    (
        "1 == 2 != 3",
        "BinaryOp(BinaryOp(IntLiteral(1), ==, IntLiteral(2)), !=, IntLiteral(3))",
    ),
    (
        "a + 1 >= b * 2",
        "BinaryOp(BinaryOp(Identifier(a), +, IntLiteral(1)), >=, BinaryOp(Identifier(b), *, IntLiteral(2)))",
    ),
    (
        "foo() == p.x",
        "BinaryOp(FuncCall(foo, []), ==, MemberAccess(Identifier(p).x))",
    ),
]


@pytest.mark.parametrize(("expr_source", "expected"), RELATIONAL_CASES)
def test_relational_expression_shapes(expr_source, expected):
    assert str(auto_init_expr(expr_source)) == expected


LOGICAL_CASES = [
    ("1 && 2", "BinaryOp(IntLiteral(1), &&, IntLiteral(2))"),
    ("1 || 2", "BinaryOp(IntLiteral(1), ||, IntLiteral(2))"),
    (
        "1 && 2 && 3",
        "BinaryOp(BinaryOp(IntLiteral(1), &&, IntLiteral(2)), &&, IntLiteral(3))",
    ),
    (
        "1 || 2 || 3",
        "BinaryOp(BinaryOp(IntLiteral(1), ||, IntLiteral(2)), ||, IntLiteral(3))",
    ),
    (
        "1 || 2 && 3",
        "BinaryOp(IntLiteral(1), ||, BinaryOp(IntLiteral(2), &&, IntLiteral(3)))",
    ),
    (
        "1 < 2 && 3 < 4",
        "BinaryOp(BinaryOp(IntLiteral(1), <, IntLiteral(2)), &&, BinaryOp(IntLiteral(3), <, IntLiteral(4)))",
    ),
    (
        "1 == 2 || 3 == 4",
        "BinaryOp(BinaryOp(IntLiteral(1), ==, IntLiteral(2)), ||, BinaryOp(IntLiteral(3), ==, IntLiteral(4)))",
    ),
    (
        "!(1 < 2) || x",
        "BinaryOp(PrefixOp(!BinaryOp(IntLiteral(1), <, IntLiteral(2))), ||, Identifier(x))",
    ),
]


@pytest.mark.parametrize(("expr_source", "expected"), LOGICAL_CASES)
def test_logical_expression_shapes(expr_source, expected):
    assert str(auto_init_expr(expr_source)) == expected


PREFIX_CASES = [
    ("+x", "PrefixOp(+Identifier(x))"),
    ("-x", "PrefixOp(-Identifier(x))"),
    ("!x", "PrefixOp(!Identifier(x))"),
    ("++x", "PrefixOp(++Identifier(x))"),
    ("--x", "PrefixOp(--Identifier(x))"),
    ("++--x", "PrefixOp(++PrefixOp(--Identifier(x)))"),
    ("+(a + b)", "PrefixOp(+BinaryOp(Identifier(a), +, Identifier(b)))"),
    ("-(a * b)", "PrefixOp(-BinaryOp(Identifier(a), *, Identifier(b)))"),
    ("!foo(1)", "PrefixOp(!FuncCall(foo, [IntLiteral(1)]))"),
    ("++p.x", "PrefixOp(++MemberAccess(Identifier(p).x))"),
]


@pytest.mark.parametrize(("expr_source", "expected"), PREFIX_CASES)
def test_prefix_expression_shapes(expr_source, expected):
    expr = expr_stmt_expr(expr_source)
    assert isinstance(expr, PrefixOp)
    assert str(expr) == expected


POSTFIX_CASES = [
    ("x++", "PostfixOp(Identifier(x)++)"),
    ("x--", "PostfixOp(Identifier(x)--)"),
    ("p.x++", "PostfixOp(MemberAccess(Identifier(p).x)++)"),
    ("foo(1).x--", "PostfixOp(MemberAccess(FuncCall(foo, [IntLiteral(1)]).x)--)"),
    ("x++++", "PostfixOp(PostfixOp(Identifier(x)++)++)"),
    ("x----", "PostfixOp(PostfixOp(Identifier(x)--)--)"),
    ("p.x.y++", "PostfixOp(MemberAccess(MemberAccess(Identifier(p).x).y)++)"),
    ("foo().x.y--", "PostfixOp(MemberAccess(MemberAccess(FuncCall(foo, []).x).y)--)"),
]


@pytest.mark.parametrize(("expr_source", "expected"), POSTFIX_CASES)
def test_postfix_expression_shapes(expr_source, expected):
    expr = expr_stmt_expr(expr_source)
    assert isinstance(expr, PostfixOp)
    assert str(expr) == expected


MEMBER_CASES = [
    ("p.x", "MemberAccess(Identifier(p).x)"),
    ("p.x.y", "MemberAccess(MemberAccess(Identifier(p).x).y)"),
    ("p.x.y.z", "MemberAccess(MemberAccess(MemberAccess(Identifier(p).x).y).z)"),
    ("getPoint().x", "MemberAccess(FuncCall(getPoint, []).x)"),
    ("getLine().start.x", "MemberAccess(MemberAccess(FuncCall(getLine, []).start).x)"),
    ("(p).x", "MemberAccess(Identifier(p).x)"),
    ("{1, 2}.x", "MemberAccess(StructLiteral({IntLiteral(1), IntLiteral(2)}).x)"),
    (
        "foo(1).x.y.z",
        "MemberAccess(MemberAccess(MemberAccess(FuncCall(foo, [IntLiteral(1)]).x).y).z)",
    ),
    ("(foo(1)).x", "MemberAccess(FuncCall(foo, [IntLiteral(1)]).x)"),
    ("((p.x)).y", "MemberAccess(MemberAccess(Identifier(p).x).y)"),
]


@pytest.mark.parametrize(("expr_source", "expected"), MEMBER_CASES)
def test_member_access_shapes(expr_source, expected):
    assert str(auto_init_expr(expr_source)) == expected


CALL_CASES = [
    ("foo()", "FuncCall(foo, [])"),
    ("foo(1)", "FuncCall(foo, [IntLiteral(1)])"),
    ("foo(1, 2)", "FuncCall(foo, [IntLiteral(1), IntLiteral(2)])"),
    ("foo(a, b, c)", "FuncCall(foo, [Identifier(a), Identifier(b), Identifier(c)])"),
    ("foo(1 + 2)", "FuncCall(foo, [BinaryOp(IntLiteral(1), +, IntLiteral(2))])"),
    ("foo(bar(1), 2)", "FuncCall(foo, [FuncCall(bar, [IntLiteral(1)]), IntLiteral(2)])"),
    ("foo({1, 2})", "FuncCall(foo, [StructLiteral({IntLiteral(1), IntLiteral(2)})])"),
    (
        "foo(p.x, getY())",
        "FuncCall(foo, [MemberAccess(Identifier(p).x), FuncCall(getY, [])])",
    ),
    ("foo((a = 1))", "FuncCall(foo, [AssignExpr(Identifier(a) = IntLiteral(1))])"),
    (
        "foo(1, 2, 3, 4)",
        "FuncCall(foo, [IntLiteral(1), IntLiteral(2), IntLiteral(3), IntLiteral(4)])",
    ),
]


@pytest.mark.parametrize(("expr_source", "expected"), CALL_CASES)
def test_function_call_shapes(expr_source, expected):
    assert str(expr_stmt_expr(expr_source)) == expected


ASSIGNMENT_CASES = [
    ("a = 1", "AssignExpr(Identifier(a) = IntLiteral(1))"),
    ("a = b = 1", "AssignExpr(Identifier(a) = AssignExpr(Identifier(b) = IntLiteral(1)))"),
    ("p.x = 3", "AssignExpr(MemberAccess(Identifier(p).x) = IntLiteral(3))"),
    (
        "p.x.y = q.z",
        "AssignExpr(MemberAccess(MemberAccess(Identifier(p).x).y) = MemberAccess(Identifier(q).z))",
    ),
    ("getPoint().x = 5", "AssignExpr(MemberAccess(FuncCall(getPoint, []).x) = IntLiteral(5))"),
    ("(p).x = 1", "AssignExpr(MemberAccess(Identifier(p).x) = IntLiteral(1))"),
    ("a = foo(1)", "AssignExpr(Identifier(a) = FuncCall(foo, [IntLiteral(1)]))"),
    (
        "p.x = q.y = 7",
        "AssignExpr(MemberAccess(Identifier(p).x) = AssignExpr(MemberAccess(Identifier(q).y) = IntLiteral(7)))",
    ),
]


@pytest.mark.parametrize(("expr_source", "expected"), ASSIGNMENT_CASES)
def test_assignment_shapes(expr_source, expected):
    expr = expr_stmt_expr(expr_source)
    assert isinstance(expr, AssignExpr)
    assert str(expr) == expected


BLOCK_CASES = [
    ("void main() { {} }", 1, 0, None),
    ("void main() { { int x; float y; } }", 1, 2, None),
    ("void main() { { { return; } } }", 1, 1, BlockStmt),
    ("void main() { { auto x = 1; } auto y = 2; }", 2, 1, None),
    ("void main() { { if (x) break; } }", 1, 1, IfStmt),
    ("void main() { { while (x) {} } }", 1, 1, WhileStmt),
]


@pytest.mark.parametrize(("source", "body_len", "nested_len", "nested_type"), BLOCK_CASES)
def test_block_shapes(source, body_len, nested_len, nested_type):
    func = first_func(source)
    assert len(func.body.statements) == body_len
    block = func.body.statements[0]
    assert isinstance(block, BlockStmt)
    assert len(block.statements) == nested_len
    if nested_type is not None:
        assert isinstance(block.statements[0], nested_type)


CONTROL_CASES = [
    ("void main() { if (x) y = 1; }", IfStmt, 0, None),
    ("void main() { if (x) y = 1; else y = 2; }", IfStmt, 0, ExprStmt),
    ("void main() { while (x) y = y + 1; }", WhileStmt, None, ExprStmt),
    ("void main() { for (;;) {} }", ForStmt, None, BlockStmt),
    ("void main() { for (i = 0; i < 3; ++i) i = i + 1; }", ForStmt, None, ExprStmt),
    ("void main() { switch (x) {} }", SwitchStmt, 0, None),
    ("void main() { switch (x) { default: break; } }", SwitchStmt, 0, DefaultStmt),
    ("void main() { switch (x) { case 1: break; case 2: return; } }", SwitchStmt, 2, None),
]


@pytest.mark.parametrize(("source", "stmt_type", "extra", "tail_type"), CONTROL_CASES)
def test_control_flow_shapes(source, stmt_type, extra, tail_type):
    stmt = body_stmt(source)
    assert isinstance(stmt, stmt_type)
    if isinstance(stmt, IfStmt):
        if tail_type is None:
            assert stmt.else_stmt is None
        else:
            assert isinstance(stmt.else_stmt, tail_type)
    elif isinstance(stmt, WhileStmt):
        assert isinstance(stmt.body, tail_type)
    elif isinstance(stmt, ForStmt):
        assert isinstance(stmt.body, tail_type)
    elif isinstance(stmt, SwitchStmt):
        assert len(stmt.cases) == extra
        if tail_type is None:
            assert (stmt.default_case is None) or isinstance(stmt.default_case, DefaultStmt)
        else:
            assert isinstance(stmt.default_case, tail_type)


TOP_LEVEL_CASES = [
    ("void main() {}", ["FuncDecl"], ["main"]),
    ("struct A {};", ["StructDecl"], ["A"]),
    ("struct A {}; struct B {};", ["StructDecl", "StructDecl"], ["A", "B"]),
    ("void f() {} void g() {}", ["FuncDecl", "FuncDecl"], ["f", "g"]),
    ("struct A {}; void main() {}", ["StructDecl", "FuncDecl"], ["A", "main"]),
    ("void main() {} struct B { int x; };", ["FuncDecl", "StructDecl"], ["main", "B"]),
    (
        "struct A {}; void f() {} struct B {}; void g() {}",
        ["StructDecl", "FuncDecl", "StructDecl", "FuncDecl"],
        ["A", "f", "B", "g"],
    ),
    (
        "sum(int a, int b) { return a + b; } void main() {}",
        ["FuncDecl", "FuncDecl"],
        ["sum", "main"],
    ),
    (
        "struct P { int x; }; P build() { return {}; }",
        ["StructDecl", "FuncDecl"],
        ["P", "build"],
    ),
    (
        "struct A {}; struct B { A x; }; void main() {}",
        ["StructDecl", "StructDecl", "FuncDecl"],
        ["A", "B", "main"],
    ),
]


@pytest.mark.parametrize(("source", "expected_types", "expected_names"), TOP_LEVEL_CASES)
def test_top_level_declaration_order(source, expected_types, expected_names):
    ast = generate_ast(source)
    assert [decl.__class__.__name__ for decl in ast.decls] == expected_types
    names = [decl.name for decl in ast.decls]
    assert names == expected_names
