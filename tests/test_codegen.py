"""
Test cases for TyC code generation.
"""

import pytest

from src.utils.nodes import *
from tests.utils import CodeGenerator


def test_001():
    """Test 1: Hello World - print string"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                ExprStmt(FuncCall("printString", [StringLiteral("Hello World")]))
            ])
        )
    ])
    expected = "Hello World"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_002():
    """Test 2: Print integer"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                ExprStmt(FuncCall("printInt", [IntLiteral(42)]))
            ])
        )
    ])
    expected = "42"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_003():
    """Test 3: Print float"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                ExprStmt(FuncCall("printFloat", [FloatLiteral(3.14)]))
            ])
        )
    ])
    expected = "3.14"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_004():
    """Test 4: Variable declaration and assignment"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                VarDecl(IntType(), "x", IntLiteral(10)),
                ExprStmt(FuncCall("printInt", [Identifier("x")]))
            ])
        )
    ])
    expected = "10"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_005():
    """Test 5: Binary operation - addition"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                ExprStmt(FuncCall("printInt", [
                    BinaryOp(IntLiteral(5), "+", IntLiteral(3))
                ]))
            ])
        )
    ])
    expected = "8"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_006():
    """Test 6: Binary operation - multiplication"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                ExprStmt(FuncCall("printInt", [
                    BinaryOp(IntLiteral(6), "*", IntLiteral(7))
                ]))
            ])
        )
    ])
    expected = "42"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_007():
    """Test 7: If statement"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                IfStmt(
                    BinaryOp(IntLiteral(1), "<", IntLiteral(2)),
                    ExprStmt(FuncCall("printString", [StringLiteral("yes")])),
                    ExprStmt(FuncCall("printString", [StringLiteral("no")]))
                )
            ])
        )
    ])
    expected = "yes"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_008():
    """Test 8: While loop"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                VarDecl(IntType(), "i", IntLiteral(0)),
                WhileStmt(
                    BinaryOp(Identifier("i"), "<", IntLiteral(3)),
                    BlockStmt([
                        ExprStmt(FuncCall("printInt", [Identifier("i")])),
                        ExprStmt(AssignExpr(
                            Identifier("i"),
                            BinaryOp(Identifier("i"), "+", IntLiteral(1))
                        ))
                    ])
                )
            ])
        )
    ])
    expected = "012"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_009():
    """Test 9: Function call with return value"""
    ast = Program([
        FuncDecl(
            IntType(),
            "add",
            [Param(IntType(), "a"), Param(IntType(), "b")],
            BlockStmt([
                ReturnStmt(BinaryOp(Identifier("a"), "+", Identifier("b")))
            ])
        ),
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                ExprStmt(FuncCall("printInt", [
                    FuncCall("add", [IntLiteral(20), IntLiteral(22)])
                ]))
            ])
        )
    ])
    expected = "42"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_010():
    """Test 10: Multiple statements - arithmetic operations"""
    ast = Program([
        FuncDecl(
            VoidType(),
            "main",
            [],
            BlockStmt([
                VarDecl(IntType(), "x", IntLiteral(10)),
                VarDecl(IntType(), "y", IntLiteral(20)),
                ExprStmt(FuncCall("printInt", [
                    BinaryOp(Identifier("x"), "+", Identifier("y"))
                ]))
            ])
        )
    ])
    expected = "30"
    result = CodeGenerator().generate_and_run(ast)
    assert result == expected, f"Expected '{expected}', got '{result}'"


def _main(stmts, extra_decls=None):
    return Program((extra_decls or []) + [FuncDecl(VoidType(), "main", [], BlockStmt(stmts))])


def _pi(expr):
    return ExprStmt(FuncCall("printInt", [expr]))


def _pf(expr):
    return ExprStmt(FuncCall("printFloat", [expr]))


def _ps(expr):
    return ExprStmt(FuncCall("printString", [expr]))


def _assign(name, expr):
    return ExprStmt(AssignExpr(Identifier(name), expr))


def _set_member(obj, member, expr):
    return ExprStmt(AssignExpr(MemberAccess(obj, member), expr))


EXTRA_CODEGEN_CASES = [
    (
        "011_subtraction",
        lambda: _main([_pi(BinaryOp(IntLiteral(9), "-", IntLiteral(4)))]),
        "5",
        "",
    ),
    (
        "012_integer_division",
        lambda: _main([_pi(BinaryOp(IntLiteral(9), "/", IntLiteral(2)))]),
        "4",
        "",
    ),
    (
        "013_modulo",
        lambda: _main([_pi(BinaryOp(IntLiteral(17), "%", IntLiteral(5)))]),
        "2",
        "",
    ),
    (
        "014_left_associative_arithmetic",
        lambda: _main([_pi(BinaryOp(BinaryOp(IntLiteral(10), "-", IntLiteral(3)), "-", IntLiteral(2)))]),
        "5",
        "",
    ),
    (
        "015_precedence_ast",
        lambda: _main([_pi(BinaryOp(IntLiteral(2), "+", BinaryOp(IntLiteral(3), "*", IntLiteral(4))))]),
        "14",
        "",
    ),
    (
        "016_unary_minus_int",
        lambda: _main([_pi(PrefixOp("-", IntLiteral(8)))]),
        "-8",
        "",
    ),
    (
        "017_unary_plus_int",
        lambda: _main([_pi(PrefixOp("+", IntLiteral(8)))]),
        "8",
        "",
    ),
    (
        "018_large_bipush_sipush_constants",
        lambda: _main([_pi(BinaryOp(IntLiteral(200), "+", IntLiteral(40000)))]),
        "40200",
        "",
    ),
    (
        "019_float_add",
        lambda: _main([_pf(BinaryOp(FloatLiteral(1.25), "+", FloatLiteral(2.5)))]),
        "3.75",
        "",
    ),
    (
        "020_mixed_int_float_add",
        lambda: _main([_pf(BinaryOp(IntLiteral(2), "+", FloatLiteral(3.5)))]),
        "5.5",
        "",
    ),
    (
        "021_mixed_float_int_sub",
        lambda: _main([_pf(BinaryOp(FloatLiteral(7.5), "-", IntLiteral(2)))]),
        "5.5",
        "",
    ),
    (
        "022_float_multiply",
        lambda: _main([_pf(BinaryOp(FloatLiteral(2.0), "*", FloatLiteral(4.5)))]),
        "9.0",
        "",
    ),
    (
        "023_float_divide",
        lambda: _main([_pf(BinaryOp(FloatLiteral(9.0), "/", FloatLiteral(2.0)))]),
        "4.5",
        "",
    ),
    (
        "024_rel_less_false",
        lambda: _main([_pi(BinaryOp(IntLiteral(5), "<", IntLiteral(3)))]),
        "0",
        "",
    ),
    (
        "025_rel_less_equal_true",
        lambda: _main([_pi(BinaryOp(IntLiteral(5), "<=", IntLiteral(5)))]),
        "1",
        "",
    ),
    (
        "026_rel_greater_true",
        lambda: _main([_pi(BinaryOp(IntLiteral(9), ">", IntLiteral(4)))]),
        "1",
        "",
    ),
    (
        "027_rel_greater_equal_false",
        lambda: _main([_pi(BinaryOp(IntLiteral(3), ">=", IntLiteral(4)))]),
        "0",
        "",
    ),
    (
        "028_rel_equal_true",
        lambda: _main([_pi(BinaryOp(IntLiteral(6), "==", IntLiteral(6)))]),
        "1",
        "",
    ),
    (
        "029_rel_not_equal_true",
        lambda: _main([_pi(BinaryOp(IntLiteral(6), "!=", IntLiteral(7)))]),
        "1",
        "",
    ),
    (
        "030_float_relation",
        lambda: _main([_pi(BinaryOp(FloatLiteral(1.5), "<", FloatLiteral(2.0)))]),
        "1",
        "",
    ),
    (
        "031_logical_and_true",
        lambda: _main([_pi(BinaryOp(IntLiteral(1), "&&", IntLiteral(2)))]),
        "1",
        "",
    ),
    (
        "032_logical_and_false",
        lambda: _main([_pi(BinaryOp(IntLiteral(1), "&&", IntLiteral(0)))]),
        "0",
        "",
    ),
    (
        "033_logical_or_true",
        lambda: _main([_pi(BinaryOp(IntLiteral(0), "||", IntLiteral(5)))]),
        "1",
        "",
    ),
    (
        "034_logical_or_false",
        lambda: _main([_pi(BinaryOp(IntLiteral(0), "||", IntLiteral(0)))]),
        "0",
        "",
    ),
    (
        "035_logical_not",
        lambda: _main([_pi(PrefixOp("!", IntLiteral(0))), _pi(PrefixOp("!", IntLiteral(9)))]),
        "10",
        "",
    ),
    (
        "036_and_short_circuit",
        lambda: _main([
            VarDecl(IntType(), "x", IntLiteral(1)),
            ExprStmt(BinaryOp(IntLiteral(0), "&&", AssignExpr(Identifier("x"), IntLiteral(9)))),
            _pi(Identifier("x")),
        ]),
        "1",
        "",
    ),
    (
        "037_or_short_circuit",
        lambda: _main([
            VarDecl(IntType(), "x", IntLiteral(1)),
            ExprStmt(BinaryOp(IntLiteral(5), "||", AssignExpr(Identifier("x"), IntLiteral(9)))),
            _pi(Identifier("x")),
        ]),
        "1",
        "",
    ),
    (
        "038_assignment_expression_value",
        lambda: _main([
            VarDecl(IntType(), "x", IntLiteral(0)),
            _pi(BinaryOp(AssignExpr(Identifier("x"), IntLiteral(5)), "+", IntLiteral(2))),
            _pi(Identifier("x")),
        ]),
        "75",
        "",
    ),
    (
        "039_chained_assignment",
        lambda: _main([
            VarDecl(IntType(), "x"),
            VarDecl(IntType(), "y"),
            ExprStmt(AssignExpr(Identifier("x"), AssignExpr(Identifier("y"), IntLiteral(4)))),
            _pi(Identifier("x")),
            _pi(Identifier("y")),
        ]),
        "44",
        "",
    ),
    (
        "040_prefix_increment_identifier",
        lambda: _main([VarDecl(IntType(), "x", IntLiteral(3)), _pi(PrefixOp("++", Identifier("x"))), _pi(Identifier("x"))]),
        "44",
        "",
    ),
    (
        "041_postfix_increment_identifier",
        lambda: _main([VarDecl(IntType(), "x", IntLiteral(3)), _pi(PostfixOp("++", Identifier("x"))), _pi(Identifier("x"))]),
        "34",
        "",
    ),
    (
        "042_prefix_decrement_identifier",
        lambda: _main([VarDecl(IntType(), "x", IntLiteral(3)), _pi(PrefixOp("--", Identifier("x"))), _pi(Identifier("x"))]),
        "22",
        "",
    ),
    (
        "043_postfix_decrement_identifier",
        lambda: _main([VarDecl(IntType(), "x", IntLiteral(3)), _pi(PostfixOp("--", Identifier("x"))), _pi(Identifier("x"))]),
        "32",
        "",
    ),
    (
        "044_default_int_local",
        lambda: _main([VarDecl(IntType(), "x"), _pi(Identifier("x"))]),
        "0",
        "",
    ),
    (
        "045_default_float_local",
        lambda: _main([VarDecl(FloatType(), "x"), _pf(Identifier("x"))]),
        "0.0",
        "",
    ),
    (
        "046_default_string_local",
        lambda: _main([VarDecl(StringType(), "s"), _ps(Identifier("s"))]),
        "",
        "",
    ),
    (
        "047_block_shadowing",
        lambda: _main([
            VarDecl(IntType(), "x", IntLiteral(1)),
            BlockStmt([VarDecl(IntType(), "x", IntLiteral(2)), _pi(Identifier("x"))]),
            _pi(Identifier("x")),
        ]),
        "21",
        "",
    ),
    (
        "048_if_without_else_true",
        lambda: _main([IfStmt(IntLiteral(1), _ps(StringLiteral("T")))]),
        "T",
        "",
    ),
    (
        "049_if_else_false",
        lambda: _main([IfStmt(IntLiteral(0), _ps(StringLiteral("T")), _ps(StringLiteral("F")))]),
        "F",
        "",
    ),
    (
        "050_negative_condition_true",
        lambda: _main([IfStmt(IntLiteral(-1), _ps(StringLiteral("T")), _ps(StringLiteral("F")))]),
        "T",
        "",
    ),
    (
        "051_nested_if",
        lambda: _main([IfStmt(IntLiteral(1), IfStmt(IntLiteral(0), _ps(StringLiteral("A")), _ps(StringLiteral("B"))), _ps(StringLiteral("C")))]),
        "B",
        "",
    ),
    (
        "052_while_sum",
        lambda: _main([
            VarDecl(IntType(), "i", IntLiteral(1)),
            VarDecl(IntType(), "s", IntLiteral(0)),
            WhileStmt(BinaryOp(Identifier("i"), "<=", IntLiteral(4)), BlockStmt([
                ExprStmt(AssignExpr(Identifier("s"), BinaryOp(Identifier("s"), "+", Identifier("i")))),
                ExprStmt(PostfixOp("++", Identifier("i"))),
            ])),
            _pi(Identifier("s")),
        ]),
        "10",
        "",
    ),
    (
        "053_while_break",
        lambda: _main([
            VarDecl(IntType(), "i", IntLiteral(0)),
            WhileStmt(IntLiteral(1), BlockStmt([
                IfStmt(BinaryOp(Identifier("i"), "==", IntLiteral(3)), BreakStmt()),
                ExprStmt(PostfixOp("++", Identifier("i"))),
            ])),
            _pi(Identifier("i")),
        ]),
        "3",
        "",
    ),
    (
        "054_while_continue",
        lambda: _main([
            VarDecl(IntType(), "i", IntLiteral(0)),
            WhileStmt(BinaryOp(Identifier("i"), "<", IntLiteral(4)), BlockStmt([
                ExprStmt(PostfixOp("++", Identifier("i"))),
                IfStmt(BinaryOp(Identifier("i"), "==", IntLiteral(2)), ContinueStmt()),
                _pi(Identifier("i")),
            ])),
        ]),
        "134",
        "",
    ),
    (
        "055_for_basic",
        lambda: _main([ForStmt(VarDecl(IntType(), "i", IntLiteral(0)), BinaryOp(Identifier("i"), "<", IntLiteral(3)), PostfixOp("++", Identifier("i")), _pi(Identifier("i")))]),
        "012",
        "",
    ),
    (
        "056_for_no_init",
        lambda: _main([
            VarDecl(IntType(), "i", IntLiteral(0)),
            ForStmt(None, BinaryOp(Identifier("i"), "<", IntLiteral(3)), PostfixOp("++", Identifier("i")), _pi(Identifier("i"))),
        ]),
        "012",
        "",
    ),
    (
        "057_for_no_update",
        lambda: _main([
            VarDecl(IntType(), "i", IntLiteral(0)),
            ForStmt(None, BinaryOp(Identifier("i"), "<", IntLiteral(3)), None, BlockStmt([_pi(Identifier("i")), ExprStmt(PostfixOp("++", Identifier("i")))])),
        ]),
        "012",
        "",
    ),
    (
        "058_for_no_condition_break",
        lambda: _main([
            ForStmt(VarDecl(IntType(), "i", IntLiteral(0)), None, PostfixOp("++", Identifier("i")), BlockStmt([
                IfStmt(BinaryOp(Identifier("i"), "==", IntLiteral(3)), BreakStmt()),
                _pi(Identifier("i")),
            ])),
        ]),
        "012",
        "",
    ),
    (
        "059_for_continue",
        lambda: _main([
            ForStmt(VarDecl(IntType(), "i", IntLiteral(0)), BinaryOp(Identifier("i"), "<", IntLiteral(4)), PostfixOp("++", Identifier("i")), BlockStmt([
                IfStmt(BinaryOp(Identifier("i"), "==", IntLiteral(2)), ContinueStmt()),
                _pi(Identifier("i")),
            ])),
        ]),
        "013",
        "",
    ),
    (
        "060_nested_loops",
        lambda: _main([
            ForStmt(VarDecl(IntType(), "i", IntLiteral(1)), BinaryOp(Identifier("i"), "<=", IntLiteral(2)), PostfixOp("++", Identifier("i")), BlockStmt([
                ForStmt(VarDecl(IntType(), "j", IntLiteral(1)), BinaryOp(Identifier("j"), "<=", IntLiteral(2)), PostfixOp("++", Identifier("j")), _pi(BinaryOp(BinaryOp(Identifier("i"), "*", IntLiteral(10)), "+", Identifier("j")))),
            ])),
        ]),
        "11122122",
        "",
    ),
    (
        "060a_for_init_scope_after_loop",
        lambda: _main([
            ForStmt(VarDecl(IntType(), "i", IntLiteral(0)), BinaryOp(Identifier("i"), "<=", IntLiteral(10)), PostfixOp("++", Identifier("i")), BlockStmt([
                _pi(Identifier("i")),
            ])),
            _pi(Identifier("i")),
        ]),
        "01234567891011",
        "",
    ),
    (
        "061_switch_match_first",
        lambda: _main([SwitchStmt(IntLiteral(1), [CaseStmt(IntLiteral(1), [_ps(StringLiteral("A")), BreakStmt()]), CaseStmt(IntLiteral(2), [_ps(StringLiteral("B"))])])]),
        "A",
        "",
    ),
    (
        "062_switch_default",
        lambda: _main([SwitchStmt(IntLiteral(3), [CaseStmt(IntLiteral(1), [_ps(StringLiteral("A"))])], DefaultStmt([_ps(StringLiteral("D"))]))]),
        "D",
        "",
    ),
    (
        "063_switch_fallthrough",
        lambda: _main([SwitchStmt(IntLiteral(2), [CaseStmt(IntLiteral(1), [_ps(StringLiteral("A"))]), CaseStmt(IntLiteral(2), [_ps(StringLiteral("B"))]), CaseStmt(IntLiteral(3), [_ps(StringLiteral("C"))])])]),
        "BC",
        "",
    ),
    (
        "064_switch_grouped_labels",
        lambda: _main([SwitchStmt(IntLiteral(2), [CaseStmt(IntLiteral(1), []), CaseStmt(IntLiteral(2), [_ps(StringLiteral("G")), BreakStmt()]), CaseStmt(IntLiteral(3), [_ps(StringLiteral("N"))])])]),
        "G",
        "",
    ),
    (
        "065_switch_empty",
        lambda: _main([SwitchStmt(IntLiteral(9), [])]),
        "",
        "",
    ),
    (
        "066_switch_case_expression",
        lambda: _main([SwitchStmt(IntLiteral(3), [CaseStmt(BinaryOp(IntLiteral(1), "+", IntLiteral(2)), [_ps(StringLiteral("E"))])])]),
        "E",
        "",
    ),
    (
        "067_function_multi_param",
        lambda: _main([_pi(FuncCall("sum3", [IntLiteral(1), IntLiteral(2), IntLiteral(3)]))], [FuncDecl(IntType(), "sum3", [Param(IntType(), "a"), Param(IntType(), "b"), Param(IntType(), "c")], BlockStmt([ReturnStmt(BinaryOp(BinaryOp(Identifier("a"), "+", Identifier("b")), "+", Identifier("c")))]))]),
        "6",
        "",
    ),
    (
        "068_function_float_return",
        lambda: _main([_pf(FuncCall("half", [IntLiteral(9)]))], [FuncDecl(FloatType(), "half", [Param(IntType(), "x")], BlockStmt([ReturnStmt(BinaryOp(Identifier("x"), "/", FloatLiteral(2.0)))]))]),
        "4.5",
        "",
    ),
    (
        "069_function_string_return",
        lambda: _main([_ps(FuncCall("msg", []))], [FuncDecl(StringType(), "msg", [], BlockStmt([ReturnStmt(StringLiteral("ok"))]))]),
        "ok",
        "",
    ),
    (
        "070_void_function_side_effect",
        lambda: _main([ExprStmt(FuncCall("say", []))], [FuncDecl(VoidType(), "say", [], BlockStmt([_ps(StringLiteral("hi"))]))]),
        "hi",
        "",
    ),
    (
        "071_inferred_int_return",
        lambda: _main([_pi(FuncCall("inc", [IntLiteral(4)]))], [FuncDecl(None, "inc", [Param(IntType(), "x")], BlockStmt([ReturnStmt(BinaryOp(Identifier("x"), "+", IntLiteral(1)))]))]),
        "5",
        "",
    ),
    (
        "072_inferred_void_return",
        lambda: _main([ExprStmt(FuncCall("noop", [])), _ps(StringLiteral("x"))], [FuncDecl(None, "noop", [], BlockStmt([]))]),
        "x",
        "",
    ),
    (
        "073_recursive_factorial",
        lambda: _main([_pi(FuncCall("fact", [IntLiteral(5)]))], [FuncDecl(IntType(), "fact", [Param(IntType(), "n")], BlockStmt([
            IfStmt(BinaryOp(Identifier("n"), "<=", IntLiteral(1)), ReturnStmt(IntLiteral(1))),
            ReturnStmt(BinaryOp(Identifier("n"), "*", FuncCall("fact", [BinaryOp(Identifier("n"), "-", IntLiteral(1))]))),
        ]))]),
        "120",
        "",
    ),
    (
        "074_function_local_shadow",
        lambda: _main([_pi(FuncCall("f", [IntLiteral(1)]))], [FuncDecl(IntType(), "f", [Param(IntType(), "x")], BlockStmt([BlockStmt([VarDecl(IntType(), "x", IntLiteral(9)), _pi(Identifier("x"))]), ReturnStmt(Identifier("x"))]))]),
        "91",
        "",
    ),
    (
        "075_read_int",
        lambda: _main([VarDecl(IntType(), "x", FuncCall("readInt", [])), _pi(BinaryOp(Identifier("x"), "+", IntLiteral(2)))]),
        "9",
        "7",
    ),
    (
        "076_read_float",
        lambda: _main([VarDecl(FloatType(), "x", FuncCall("readFloat", [])), _pf(BinaryOp(Identifier("x"), "+", FloatLiteral(1.5)))]),
        "4.0",
        "2.5",
    ),
    (
        "077_read_string",
        lambda: _main([VarDecl(StringType(), "s", FuncCall("readString", [])), _ps(Identifier("s"))]),
        "abc",
        "abc",
    ),
    (
        "078_auto_var_from_initializer",
        lambda: _main([VarDecl(None, "x", IntLiteral(6)), _pi(Identifier("x"))]),
        "6",
        "",
    ),
    (
        "079_auto_var_from_later_assignment",
        lambda: _main([VarDecl(None, "x"), _assign("x", IntLiteral(8)), _pi(Identifier("x"))]),
        "8",
        "",
    ),
    (
        "080_auto_var_from_function_arg",
        lambda: _main([VarDecl(None, "x"), ExprStmt(FuncCall("printInt", [Identifier("x")]))]),
        "0",
        "",
    ),
    (
        "081_struct_literal_members",
        lambda: _main([
            VarDecl(StructType("Point"), "p", StructLiteral([IntLiteral(3), IntLiteral(4)])),
            _pi(MemberAccess(Identifier("p"), "x")),
            _pi(MemberAccess(Identifier("p"), "y")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x"), MemberDecl(IntType(), "y")])]),
        "34",
        "",
    ),
    (
        "082_struct_member_assignment",
        lambda: _main([
            VarDecl(StructType("Point"), "p", StructLiteral([IntLiteral(1), IntLiteral(2)])),
            _set_member(Identifier("p"), "x", IntLiteral(9)),
            _pi(MemberAccess(Identifier("p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x"), MemberDecl(IntType(), "y")])]),
        "9",
        "",
    ),
    (
        "083_struct_string_float_members",
        lambda: _main([
            VarDecl(StructType("Person"), "p", StructLiteral([StringLiteral("Ann"), FloatLiteral(1.5)])),
            _ps(MemberAccess(Identifier("p"), "name")),
            _pf(MemberAccess(Identifier("p"), "height")),
        ], [StructDecl("Person", [MemberDecl(StringType(), "name"), MemberDecl(FloatType(), "height")])]),
        "Ann1.5",
        "",
    ),
    (
        "084_nested_struct_member_read",
        lambda: _main([
            VarDecl(StructType("Box"), "b", StructLiteral([StructLiteral([IntLiteral(7)])])),
            _pi(MemberAccess(MemberAccess(Identifier("b"), "p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")]), StructDecl("Box", [MemberDecl(StructType("Point"), "p")])]),
        "7",
        "",
    ),
    (
        "085_nested_struct_member_assignment",
        lambda: _main([
            VarDecl(StructType("Box"), "b", StructLiteral([StructLiteral([IntLiteral(1)])])),
            ExprStmt(AssignExpr(MemberAccess(MemberAccess(Identifier("b"), "p"), "x"), IntLiteral(8))),
            _pi(MemberAccess(MemberAccess(Identifier("b"), "p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")]), StructDecl("Box", [MemberDecl(StructType("Point"), "p")])]),
        "8",
        "",
    ),
    (
        "086_struct_assignment_copies",
        lambda: _main([
            VarDecl(StructType("Point"), "p", StructLiteral([IntLiteral(1)])),
            VarDecl(StructType("Point"), "q", Identifier("p")),
            _set_member(Identifier("q"), "x", IntLiteral(9)),
            _pi(MemberAccess(Identifier("p"), "x")),
            _pi(MemberAccess(Identifier("q"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")])]),
        "19",
        "",
    ),
    (
        "087_nested_struct_assignment_copies",
        lambda: _main([
            VarDecl(StructType("Box"), "a", StructLiteral([StructLiteral([IntLiteral(4)])])),
            VarDecl(StructType("Box"), "b", Identifier("a")),
            ExprStmt(AssignExpr(MemberAccess(MemberAccess(Identifier("b"), "p"), "x"), IntLiteral(9))),
            _pi(MemberAccess(MemberAccess(Identifier("a"), "p"), "x")),
            _pi(MemberAccess(MemberAccess(Identifier("b"), "p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")]), StructDecl("Box", [MemberDecl(StructType("Point"), "p")])]),
        "49",
        "",
    ),
    (
        "088_struct_function_param_copy",
        lambda: _main([
            VarDecl(StructType("Point"), "p", StructLiteral([IntLiteral(3)])),
            ExprStmt(FuncCall("mut", [Identifier("p")])),
            _pi(MemberAccess(Identifier("p"), "x")),
        ], [
            StructDecl("Point", [MemberDecl(IntType(), "x")]),
            FuncDecl(VoidType(), "mut", [Param(StructType("Point"), "p")], BlockStmt([_set_member(Identifier("p"), "x", IntLiteral(6))])),
        ]),
        "3",
        "",
    ),
    (
        "089_struct_function_return",
        lambda: _main([
            VarDecl(StructType("Point"), "p", FuncCall("mk", [IntLiteral(5)])),
            _pi(MemberAccess(Identifier("p"), "x")),
        ], [
            StructDecl("Point", [MemberDecl(IntType(), "x")]),
            FuncDecl(StructType("Point"), "mk", [Param(IntType(), "x")], BlockStmt([ReturnStmt(StructLiteral([Identifier("x")]))])),
        ]),
        "5",
        "",
    ),
    (
        "090_member_access_from_func_call",
        lambda: _main([
            _pi(MemberAccess(FuncCall("mk", []), "x")),
        ], [
            StructDecl("Point", [MemberDecl(IntType(), "x")]),
            FuncDecl(StructType("Point"), "mk", [], BlockStmt([ReturnStmt(StructLiteral([IntLiteral(7)]))])),
        ]),
        "7",
        "",
    ),
    (
        "091_struct_literal_argument",
        lambda: _main([
            _pi(FuncCall("get", [StructLiteral([IntLiteral(6)])])),
        ], [
            StructDecl("Point", [MemberDecl(IntType(), "x")]),
            FuncDecl(IntType(), "get", [Param(StructType("Point"), "p")], BlockStmt([ReturnStmt(MemberAccess(Identifier("p"), "x"))])),
        ]),
        "6",
        "",
    ),
    (
        "092_prefix_increment_member",
        lambda: _main([
            VarDecl(StructType("Point"), "p", StructLiteral([IntLiteral(2)])),
            _pi(PrefixOp("++", MemberAccess(Identifier("p"), "x"))),
            _pi(MemberAccess(Identifier("p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")])]),
        "33",
        "",
    ),
    (
        "093_postfix_increment_member",
        lambda: _main([
            VarDecl(StructType("Point"), "p", StructLiteral([IntLiteral(2)])),
            _pi(PostfixOp("++", MemberAccess(Identifier("p"), "x"))),
            _pi(MemberAccess(Identifier("p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")])]),
        "23",
        "",
    ),
    (
        "094_default_struct_local",
        lambda: _main([
            VarDecl(StructType("Point"), "p"),
            _pi(MemberAccess(Identifier("p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")])]),
        "0",
        "",
    ),
    (
        "095_assign_struct_member_struct",
        lambda: _main([
            VarDecl(StructType("Box"), "b", StructLiteral([StructLiteral([IntLiteral(1)])])),
            ExprStmt(AssignExpr(MemberAccess(Identifier("b"), "p"), StructLiteral([IntLiteral(8)]))),
            _pi(MemberAccess(MemberAccess(Identifier("b"), "p"), "x")),
        ], [StructDecl("Point", [MemberDecl(IntType(), "x")]), StructDecl("Box", [MemberDecl(StructType("Point"), "p")])]),
        "8",
        "",
    ),
    (
        "096_string_variable_assignment",
        lambda: _main([
            VarDecl(StringType(), "s", StringLiteral("a")),
            _assign("s", StringLiteral("b")),
            _ps(Identifier("s")),
        ]),
        "b",
        "",
    ),
    (
        "097_float_variable_assignment",
        lambda: _main([
            VarDecl(FloatType(), "x", FloatLiteral(1.0)),
            ExprStmt(AssignExpr(Identifier("x"), BinaryOp(Identifier("x"), "+", FloatLiteral(2.25)))),
            _pf(Identifier("x")),
        ]),
        "3.25",
        "",
    ),
    (
        "098_return_inside_while",
        lambda: _main([_pi(FuncCall("f", []))], [FuncDecl(IntType(), "f", [], BlockStmt([WhileStmt(IntLiteral(1), ReturnStmt(IntLiteral(8))), ReturnStmt(IntLiteral(0))]))]),
        "8",
        "",
    ),
    (
        "099_return_inside_for",
        lambda: _main([_pi(FuncCall("f", []))], [FuncDecl(IntType(), "f", [], BlockStmt([ForStmt(VarDecl(IntType(), "i", IntLiteral(0)), BinaryOp(Identifier("i"), "<", IntLiteral(3)), PostfixOp("++", Identifier("i")), IfStmt(BinaryOp(Identifier("i"), "==", IntLiteral(2)), ReturnStmt(Identifier("i")))), ReturnStmt(IntLiteral(9))]))]),
        "2",
        "",
    ),
    (
        "100_switch_break_in_loop",
        lambda: _main([
            VarDecl(IntType(), "i", IntLiteral(0)),
            WhileStmt(BinaryOp(Identifier("i"), "<", IntLiteral(3)), BlockStmt([
                SwitchStmt(Identifier("i"), [CaseStmt(IntLiteral(1), [BreakStmt()])], DefaultStmt([_pi(Identifier("i"))])),
                ExprStmt(PostfixOp("++", Identifier("i"))),
            ])),
        ]),
        "02",
        "",
    ),
]


@pytest.mark.parametrize(
    ("case_name", "ast_factory", "expected", "input_data"),
    EXTRA_CODEGEN_CASES,
    ids=[case[0] for case in EXTRA_CODEGEN_CASES],
)
def test_assignment4_extra_codegen_cases(case_name, ast_factory, expected, input_data):
    result = CodeGenerator().generate_and_run(ast_factory(), input_data)
    assert result == expected, f"{case_name}: expected {expected!r}, got {result!r}"
