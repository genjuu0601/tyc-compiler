"""
Submission-safe static checker for TyC.

This version avoids helper dataclasses or module-level custom types outside the
`StaticChecker` class so students can more easily copy the implementation part
into a submission box that only keeps the class body.
"""

from typing import Any

from ..utils.nodes import (
    ASTNode,
    AssignExpr,
    BinaryOp,
    BlockStmt,
    BreakStmt,
    CaseStmt,
    ContinueStmt,
    DefaultStmt,
    Expr,
    ExprStmt,
    FloatType,
    ForStmt,
    FuncCall,
    FuncDecl,
    Identifier,
    IfStmt,
    IntType,
    MemberAccess,
    MemberDecl,
    Param,
    PostfixOp,
    PrefixOp,
    Program,
    ReturnStmt,
    StringType,
    StructDecl,
    StructLiteral,
    StructType,
    SwitchStmt,
    VarDecl,
    VoidType,
    WhileStmt,
)
from ..utils.visitor import ASTVisitor
from .static_error import (
    MustInLoop,
    Redeclared,
    TypeCannotBeInferred,
    TypeMismatchInExpression,
    TypeMismatchInStatement,
    UndeclaredFunction,
    UndeclaredIdentifier,
    UndeclaredStruct,
)


class StaticChecker(ASTVisitor):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    VOID = "void"

    UNKNOWN_VAR = "unknown_var"
    UNKNOWN_FUNC = "unknown_func"
    PENDING_STRUCT_LITERAL = "pending_struct_literal"
    STRUCT = "struct"

    def __init__(self):
        self.structs = {}
        self.functions = {}
        self.scopes = []
        self.current_function = None
        self.loop_depth = 0
        self.switch_depth = 0

    def check_program(self, program):
        self._reset()
        self.visit(program)

    # ------------------------------------------------------------------
    # Program / declarations
    # ------------------------------------------------------------------

    def visit_program(self, node: "Program", o: Any = None):
        for decl in node.decls:
            self.visit(decl)

    def visit_struct_decl(self, node: "StructDecl", o: Any = None):
        self._ensure_global_name_available(node.name, "Struct")

        members = []
        member_map = {}
        for member in node.members:
            name, member_type = self.visit(member)
            if name in member_map:
                raise Redeclared("Variable", name)
            members.append((name, member_type))
            member_map[name] = member_type

        self.structs[node.name] = {
            "name": node.name,
            "members": members,
            "member_map": member_map,
        }

    def visit_member_decl(self, node: "MemberDecl", o: Any = None):
        return (node.name, self.visit(node.member_type))

    def visit_func_decl(self, node: "FuncDecl", o: Any = None):
        self._ensure_global_name_available(node.name, "Function")

        return_type = self.visit(node.return_type) if node.return_type else None
        params = []
        param_scope = {}

        for param in node.params:
            info = self.visit(param)
            if info["name"] in param_scope:
                raise Redeclared("Parameter", info["name"])
            params.append(info)
            param_scope[info["name"]] = info

        func_info = {
            "name": node.name,
            "params": params,
            "return_type": return_type,
            "decl": node,
            "explicit_return": node.return_type is not None,
            "builtin": False,
        }
        self.functions[node.name] = func_info

        prev_function = self.current_function
        prev_scopes = self.scopes
        prev_loop_depth = self.loop_depth
        prev_switch_depth = self.switch_depth

        self.current_function = func_info
        self.scopes = [param_scope]
        self.loop_depth = 0
        self.switch_depth = 0

        try:
            for stmt in node.body.statements:
                self.visit(stmt)
        finally:
            if (not func_info["explicit_return"]) and func_info["return_type"] is None:
                func_info["return_type"] = self.VOID

            self.current_function = prev_function
            self.scopes = prev_scopes
            self.loop_depth = prev_loop_depth
            self.switch_depth = prev_switch_depth

    def visit_param(self, node: "Param", o: Any = None):
        return {"name": node.name, "typ": self.visit(node.param_type), "node": node}

    # ------------------------------------------------------------------
    # Type nodes
    # ------------------------------------------------------------------

    def visit_int_type(self, node: "IntType", o: Any = None):
        return self.INT

    def visit_float_type(self, node: "FloatType", o: Any = None):
        return self.FLOAT

    def visit_string_type(self, node: "StringType", o: Any = None):
        return self.STRING

    def visit_void_type(self, node: "VoidType", o: Any = None):
        return self.VOID

    def visit_struct_type(self, node: "StructType", o: Any = None):
        if node.struct_name not in self.structs:
            raise UndeclaredStruct(node.struct_name)
        return (self.STRUCT, node.struct_name)

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def visit_block_stmt(self, node: "BlockStmt", o: Any = None):
        self._push_scope()
        try:
            for stmt in node.statements:
                self.visit(stmt)
        finally:
            self._pop_scope()

    def visit_var_decl(self, node: "VarDecl", o: Any = None):
        declared_type = self.visit(node.var_type) if node.var_type else None

        self._ensure_local_name_available(node.name, "Variable")
        symbol = {"name": node.name, "typ": declared_type, "node": node}
        self.scopes[-1][node.name] = symbol

        if node.init_value is None:
            return

        if declared_type is None:
            init_type = self._actual_type(self.visit(node.init_value))
            if self._is_pending_struct_literal(init_type):
                raise TypeCannotBeInferred(node.init_value)
            if self._is_unknown(init_type):
                raise TypeCannotBeInferred(node.init_value)
            if init_type == self.VOID:
                raise TypeMismatchInStatement(node)
            symbol["typ"] = init_type
            return

        init_type = self._actual_type(
            self.visit(node.init_value, self._expr_context(declared_type))
        )

        if self._is_pending_struct_literal(init_type):
            init_type = self._actual_type(
                self.visit(node.init_value, self._expr_context(declared_type))
            )

        if self._is_unknown(init_type):
            self._bind_unknown(init_type, declared_type)
            init_type = declared_type

        if init_type == self.VOID or not self._same_type(init_type, declared_type):
            raise TypeMismatchInStatement(node)

    def visit_if_stmt(self, node: "IfStmt", o: Any = None):
        self._ensure_statement_type(node.condition, self.INT, node)
        self.visit(node.then_stmt)
        if node.else_stmt:
            self.visit(node.else_stmt)

    def visit_while_stmt(self, node: "WhileStmt", o: Any = None):
        self._ensure_statement_type(node.condition, self.INT, node)
        self.loop_depth += 1
        try:
            self.visit(node.body)
        finally:
            self.loop_depth -= 1

    def visit_for_stmt(self, node: "ForStmt", o: Any = None):
        self._push_scope()
        try:
            if node.init:
                self.visit(node.init)

            if node.condition:
                self._ensure_statement_type(node.condition, self.INT, node)

            if node.update:
                if isinstance(node.update, AssignExpr):
                    self.visit(node.update, self._expr_context(assign_mode="stmt"))
                else:
                    self.visit(node.update)

            self.loop_depth += 1
            try:
                self.visit(node.body)
            finally:
                self.loop_depth -= 1
        finally:
            self._pop_scope()

    def visit_switch_stmt(self, node: "SwitchStmt", o: Any = None):
        self._ensure_statement_type(node.expr, self.INT, node)
        self.switch_depth += 1
        try:
            for case in node.cases:
                self.visit(case)
            if node.default_case:
                self.visit(node.default_case)
        finally:
            self.switch_depth -= 1

    def visit_case_stmt(self, node: "CaseStmt", o: Any = None):
        case_type = self._actual_type(self.visit(node.expr, self._expr_context(self.INT)))
        if self._is_pending_struct_literal(case_type) or case_type != self.INT:
            raise TypeMismatchInStatement(node)
        for stmt in node.statements:
            self.visit(stmt)

    def visit_default_stmt(self, node: "DefaultStmt", o: Any = None):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_break_stmt(self, node: "BreakStmt", o: Any = None):
        if self.loop_depth == 0 and self.switch_depth == 0:
            raise MustInLoop(node)

    def visit_continue_stmt(self, node: "ContinueStmt", o: Any = None):
        if self.loop_depth == 0:
            raise MustInLoop(node)

    def visit_return_stmt(self, node: "ReturnStmt", o: Any = None):
        func = self.current_function

        if node.expr is None:
            if func is None:
                return
            if func["explicit_return"]:
                if func["return_type"] != self.VOID:
                    raise TypeMismatchInStatement(node)
                return
            if func["return_type"] is not None and func["return_type"] != self.VOID:
                raise TypeMismatchInStatement(node)
            return

        if func is not None and func["explicit_return"] and func["return_type"] == self.VOID:
            self.visit(node.expr)
            raise TypeMismatchInStatement(node)

        expected = None if func is None else func["return_type"]
        expr_type = self._actual_type(self.visit(node.expr, self._expr_context(expected)))

        if self._is_pending_struct_literal(expr_type):
            if func is None or func["return_type"] is None:
                raise TypeCannotBeInferred(node.expr)
            expr_type = self._actual_type(
                self.visit(node.expr, self._expr_context(func["return_type"]))
            )

        if expr_type == self.VOID:
            raise TypeMismatchInStatement(node)

        if func is None:
            return

        if func["explicit_return"]:
            if not self._same_type(expr_type, func["return_type"]):
                raise TypeMismatchInStatement(node)
            return

        if func["return_type"] is None:
            if self._is_unknown(expr_type):
                raise TypeCannotBeInferred(node.expr)
            func["return_type"] = expr_type
            return

        if self._is_unknown(expr_type):
            self._bind_unknown(expr_type, func["return_type"])
            return

        if not self._same_type(expr_type, func["return_type"]):
            raise TypeMismatchInStatement(node)

    def visit_expr_stmt(self, node: "ExprStmt", o: Any = None):
        if isinstance(node.expr, AssignExpr):
            self.visit(node.expr, self._expr_context(assign_mode="stmt"))
            return
        self.visit(node.expr)

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def visit_binary_op(self, node: "BinaryOp", o: Any = None):
        ctx = self._normalize_expr_context(o)
        op = node.operator

        if op in {"&&", "||"}:
            left_type = self.visit(node.left, self._expr_context(self.INT))
            right_type = self.visit(node.right, self._expr_context(self.INT))
            return self._finalize_binary_int(node, left_type, right_type)

        if op == "%":
            left_type = self.visit(node.left, self._expr_context(self.INT))
            right_type = self.visit(node.right, self._expr_context(self.INT))
            return self._finalize_binary_int(node, left_type, right_type)

        if op in {"+", "-", "*", "/"} and ctx["expected"] == self.INT:
            left_type = self.visit(node.left, self._expr_context(self.INT))
            right_type = self.visit(node.right, self._expr_context(self.INT))
            return self._finalize_arithmetic(
                node, left_type, right_type, ctx["expected"]
            )

        left_type, left_error = self._attempt_expr_visit(node.left)
        right_type, right_error = self._attempt_expr_visit(node.right)

        if op in {"+", "-", "*", "/"}:
            if left_error and self._is_numeric_like(right_type):
                expectation = self._derive_arithmetic_expectation(
                    self._actual_type(right_type), ctx["expected"]
                )
                if expectation is not None:
                    left_type = self.visit(node.left, self._expr_context(expectation))
                    left_error = None

            if right_error and self._is_numeric_like(left_type):
                expectation = self._derive_arithmetic_expectation(
                    self._actual_type(left_type), ctx["expected"]
                )
                if expectation is not None:
                    right_type = self.visit(node.right, self._expr_context(expectation))
                    right_error = None

            if left_error:
                raise left_error
            if right_error:
                raise right_error

            return self._finalize_arithmetic(
                node, left_type, right_type, ctx["expected"]
            )

        if op in {"==", "!=", "<", "<=", ">", ">="}:
            if left_error and self._is_numeric_like(right_type):
                expectation = self._actual_type(right_type)
                left_type = self.visit(node.left, self._expr_context(expectation))
                left_error = None

            if right_error and self._is_numeric_like(left_type):
                expectation = self._actual_type(left_type)
                right_type = self.visit(node.right, self._expr_context(expectation))
                right_error = None

            if left_error:
                raise left_error
            if right_error:
                raise right_error

            return self._finalize_relational(node, left_type, right_type)

        raise TypeMismatchInExpression(node)

    def visit_prefix_op(self, node: "PrefixOp", o: Any = None):
        ctx = self._normalize_expr_context(o)

        if node.operator in {"++", "--"}:
            if not self._is_lvalue_expr(node.operand):
                raise TypeMismatchInExpression(node)
            operand_type = self._actual_type(
                self.visit(node.operand, self._expr_context(self.INT))
            )
            if operand_type != self.INT:
                raise TypeMismatchInExpression(node)
            return self.INT

        if node.operator == "!":
            operand_type = self._actual_type(
                self.visit(node.operand, self._expr_context(self.INT))
            )
            if operand_type != self.INT:
                raise TypeMismatchInExpression(node)
            return self.INT

        if node.operator in {"+", "-"}:
            expectation = (
                ctx["expected"] if ctx["expected"] in {self.INT, self.FLOAT} else None
            )
            operand_type = self._actual_type(
                self.visit(node.operand, self._expr_context(expectation))
            )

            if self._is_unknown(operand_type):
                raise TypeCannotBeInferred(node)
            if not self._is_numeric(operand_type):
                raise TypeMismatchInExpression(node)
            if expectation is not None and operand_type != expectation:
                raise TypeMismatchInExpression(node)
            return operand_type

        raise TypeMismatchInExpression(node)

    def visit_postfix_op(self, node: "PostfixOp", o: Any = None):
        if node.operator not in {"++", "--"}:
            raise TypeMismatchInExpression(node)
        if not self._is_lvalue_expr(node.operand):
            raise TypeMismatchInExpression(node)

        operand_type = self._actual_type(
            self.visit(node.operand, self._expr_context(self.INT))
        )
        if operand_type != self.INT:
            raise TypeMismatchInExpression(node)
        return self.INT

    def visit_assign_expr(self, node: "AssignExpr", o: Any = None):
        ctx = self._normalize_expr_context(o)

        if not self._is_lvalue_expr(node.lhs):
            raise TypeMismatchInExpression(node)

        lhs_type = self._actual_type(self.visit(node.lhs))
        rhs_context = self._expr_context(
            lhs_type if self._is_concrete_type(lhs_type) else None, "expr"
        )
        rhs_type = self._actual_type(self.visit(node.rhs, rhs_context))

        if self._is_pending_struct_literal(rhs_type):
            if not self._is_concrete_type(lhs_type):
                raise TypeCannotBeInferred(node)
            rhs_type = self._actual_type(
                self.visit(node.rhs, self._expr_context(lhs_type))
            )

        if self._is_pending_struct_literal(lhs_type):
            self._raise_assignment_mismatch(node, ctx)

        if self._is_unknown(lhs_type):
            if self._is_unknown(rhs_type):
                raise TypeCannotBeInferred(node)
            if rhs_type == self.VOID:
                self._raise_assignment_mismatch(node, ctx)
            self._bind_unknown(lhs_type, rhs_type)
            return rhs_type

        if self._is_unknown(rhs_type):
            if lhs_type == self.VOID:
                self._raise_assignment_mismatch(node, ctx)
            self._bind_unknown(rhs_type, lhs_type)
            return lhs_type

        if rhs_type == self.VOID or not self._same_type(lhs_type, rhs_type):
            self._raise_assignment_mismatch(node, ctx)

        return lhs_type

    def visit_member_access(self, node: "MemberAccess", o: Any = None):
        obj_type = self._actual_type(self.visit(node.obj))

        if self._is_unknown(obj_type):
            raise TypeCannotBeInferred(node)
        if self._is_pending_struct_literal(obj_type):
            raise TypeMismatchInExpression(node)
        if not self._is_struct(obj_type):
            raise TypeMismatchInExpression(node)

        struct_info = self.structs[obj_type[1]]
        if node.member not in struct_info["member_map"]:
            raise TypeMismatchInExpression(node)
        return struct_info["member_map"][node.member]

    def visit_func_call(self, node: "FuncCall", o: Any = None):
        ctx = self._normalize_expr_context(o)
        func = self.functions.get(node.name)
        if func is None:
            raise UndeclaredFunction(node.name)

        param_types = [param["typ"] for param in func["params"]]

        for index, arg in enumerate(node.args):
            expected = param_types[index] if index < len(param_types) else None
            arg_type = self._actual_type(self.visit(arg, self._expr_context(expected)))

            if expected is None:
                continue

            if self._is_pending_struct_literal(arg_type):
                arg_type = self._actual_type(
                    self.visit(arg, self._expr_context(expected))
                )

            if self._is_unknown(arg_type):
                self._bind_unknown(arg_type, expected)
                arg_type = expected

            if arg_type == self.VOID or not self._same_type(arg_type, expected):
                raise TypeMismatchInExpression(node)

        if len(node.args) != len(param_types):
            raise TypeMismatchInExpression(node)

        if func["return_type"] is None:
            if ctx["expected"] is not None and ctx["expected"] != self.VOID:
                func["return_type"] = ctx["expected"]
                return ctx["expected"]
            return (self.UNKNOWN_FUNC, func)

        return func["return_type"]

    def visit_identifier(self, node: "Identifier", o: Any = None):
        symbol = self._lookup_var(node.name)
        if symbol is None:
            raise UndeclaredIdentifier(node.name)

        if symbol["typ"] is not None:
            return symbol["typ"]

        expected = self._normalize_expr_context(o)["expected"]
        if expected is not None and expected != self.VOID:
            symbol["typ"] = expected
            return expected
        return (self.UNKNOWN_VAR, symbol)

    def visit_struct_literal(self, node: "StructLiteral", o: Any = None):
        expected = self._normalize_expr_context(o)["expected"]

        if not self._is_struct(expected):
            for value in node.values:
                self.visit(value)
            return (self.PENDING_STRUCT_LITERAL, node)

        struct_info = self.structs[expected[1]]
        if len(node.values) != len(struct_info["members"]):
            raise TypeMismatchInExpression(node)

        for value, (_, member_type) in zip(node.values, struct_info["members"]):
            value_type = self._actual_type(
                self.visit(value, self._expr_context(member_type))
            )

            if self._is_pending_struct_literal(value_type):
                value_type = self._actual_type(
                    self.visit(value, self._expr_context(member_type))
                )

            if self._is_unknown(value_type):
                self._bind_unknown(value_type, member_type)
                value_type = member_type

            if value_type == self.VOID or not self._same_type(value_type, member_type):
                raise TypeMismatchInExpression(node)

        return expected

    # ------------------------------------------------------------------
    # Literals
    # ------------------------------------------------------------------

    def visit_int_literal(self, node, o: Any = None):
        return self.INT

    def visit_float_literal(self, node, o: Any = None):
        return self.FLOAT

    def visit_string_literal(self, node, o: Any = None):
        return self.STRING

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset(self):
        self.structs = {}
        self.functions = {}
        self.scopes = []
        self.current_function = None
        self.loop_depth = 0
        self.switch_depth = 0
        self._install_builtins()

    def _install_builtins(self):
        self.functions = {
            "readInt": {
                "name": "readInt",
                "params": [],
                "return_type": self.INT,
                "decl": None,
                "explicit_return": True,
                "builtin": True,
            },
            "readFloat": {
                "name": "readFloat",
                "params": [],
                "return_type": self.FLOAT,
                "decl": None,
                "explicit_return": True,
                "builtin": True,
            },
            "readString": {
                "name": "readString",
                "params": [],
                "return_type": self.STRING,
                "decl": None,
                "explicit_return": True,
                "builtin": True,
            },
            "printInt": {
                "name": "printInt",
                "params": [{"name": "value", "typ": self.INT, "node": "value"}],
                "return_type": self.VOID,
                "decl": None,
                "explicit_return": True,
                "builtin": True,
            },
            "printFloat": {
                "name": "printFloat",
                "params": [{"name": "value", "typ": self.FLOAT, "node": "value"}],
                "return_type": self.VOID,
                "decl": None,
                "explicit_return": True,
                "builtin": True,
            },
            "printString": {
                "name": "printString",
                "params": [{"name": "value", "typ": self.STRING, "node": "value"}],
                "return_type": self.VOID,
                "decl": None,
                "explicit_return": True,
                "builtin": True,
            },
        }

    def _push_scope(self):
        self.scopes.append({})

    def _pop_scope(self):
        self.scopes.pop()

    def _lookup_var(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def _ensure_global_name_available(self, name, kind):
        if name in self.structs or name in self.functions:
            raise Redeclared(kind, name)

    def _ensure_local_name_available(self, name, kind):
        if name in self.scopes[-1]:
            raise Redeclared(kind, name)

    def _expr_context(self, expected=None, assign_mode="expr"):
        return {"expected": expected, "assign_mode": assign_mode}

    def _normalize_expr_context(self, o):
        if isinstance(o, dict) and "expected" in o and "assign_mode" in o:
            return o
        return self._expr_context()

    def _is_unknown(self, typ):
        return isinstance(typ, tuple) and len(typ) == 2 and typ[0] in {
            self.UNKNOWN_VAR,
            self.UNKNOWN_FUNC,
        }

    def _is_pending_struct_literal(self, typ):
        return (
            isinstance(typ, tuple)
            and len(typ) == 2
            and typ[0] == self.PENDING_STRUCT_LITERAL
        )

    def _is_struct(self, typ):
        return isinstance(typ, tuple) and len(typ) == 2 and typ[0] == self.STRUCT

    def _owner_type(self, owner):
        if self._is_unknown(owner):
            owner = owner[1]
        if isinstance(owner, dict) and "typ" in owner:
            return owner["typ"]
        return owner["return_type"]

    def _bind_unknown(self, ref, concrete):
        owner = ref[1]
        if "typ" in owner:
            owner["typ"] = concrete
        else:
            owner["return_type"] = concrete

    def _actual_type(self, typ):
        if self._is_unknown(typ):
            concrete = self._owner_type(typ)
            if concrete is not None:
                return concrete
        return typ

    def _same_type(self, left, right):
        left = self._actual_type(left)
        right = self._actual_type(right)
        if not self._is_concrete_type(left) or not self._is_concrete_type(right):
            return False
        return left == right

    def _is_concrete_type(self, typ):
        return not self._is_unknown(typ) and not self._is_pending_struct_literal(typ)

    def _is_numeric(self, typ):
        return typ in {self.INT, self.FLOAT}

    def _is_numeric_like(self, typ):
        if typ is None:
            return False
        typ = self._actual_type(typ)
        return self._is_unknown(typ) or self._is_numeric(typ)

    def _numeric_result_type(self, left, right):
        if left == self.FLOAT or right == self.FLOAT:
            return self.FLOAT
        return self.INT

    def _inference_target(self, ref):
        owner = ref[1]
        if "typ" in owner:
            return owner["node"]
        return owner["name"]

    def _assign_inference_target(self, lhs_type, node):
        if self._is_unknown(lhs_type):
            return self._inference_target(lhs_type)
        if isinstance(node.lhs, Identifier):
            symbol = self._lookup_var(node.lhs.name)
            if symbol is not None:
                return symbol["node"]
        return node

    def _is_lvalue_expr(self, expr):
        return isinstance(expr, (Identifier, MemberAccess))

    def _attempt_expr_visit(self, expr, expected=None):
        try:
            return self.visit(expr, self._expr_context(expected)), None
        except TypeCannotBeInferred as err:
            return None, err

    def _derive_arithmetic_expectation(self, known_type, expected_result):
        known_type = self._actual_type(known_type)
        if not self._is_numeric(known_type):
            return None
        if expected_result == self.INT:
            return self.INT
        if expected_result == self.FLOAT:
            return self.FLOAT
        return known_type

    def _finalize_binary_int(self, node, left_type, right_type):
        left_type = self._actual_type(left_type)
        right_type = self._actual_type(right_type)

        if self._is_pending_struct_literal(left_type) or self._is_pending_struct_literal(
            right_type
        ):
            raise TypeMismatchInExpression(node)
        if self._is_unknown(left_type):
            self._bind_unknown(left_type, self.INT)
            left_type = self.INT
        if self._is_unknown(right_type):
            self._bind_unknown(right_type, self.INT)
            right_type = self.INT
        if left_type != self.INT or right_type != self.INT:
            raise TypeMismatchInExpression(node)
        return self.INT

    def _finalize_arithmetic(self, node, left_type, right_type, expected_result):
        left_type = self._actual_type(left_type)
        right_type = self._actual_type(right_type)

        if self._is_pending_struct_literal(left_type) or self._is_pending_struct_literal(
            right_type
        ):
            raise TypeMismatchInExpression(node)

        if self._is_unknown(left_type) and self._is_unknown(right_type):
            if expected_result == self.INT:
                self._bind_unknown(left_type, self.INT)
                self._bind_unknown(right_type, self.INT)
                return self.INT
            raise TypeCannotBeInferred(node)

        if self._is_unknown(left_type):
            if not self._is_numeric(right_type):
                raise TypeMismatchInExpression(node)
            inferred = self._derive_arithmetic_expectation(right_type, expected_result)
            if inferred is None:
                raise TypeCannotBeInferred(node)
            self._bind_unknown(left_type, inferred)
            left_type = inferred

        if self._is_unknown(right_type):
            if not self._is_numeric(left_type):
                raise TypeMismatchInExpression(node)
            inferred = self._derive_arithmetic_expectation(left_type, expected_result)
            if inferred is None:
                raise TypeCannotBeInferred(node)
            self._bind_unknown(right_type, inferred)
            right_type = inferred

        if not self._is_numeric(left_type) or not self._is_numeric(right_type):
            raise TypeMismatchInExpression(node)

        result_type = self._numeric_result_type(left_type, right_type)
        if expected_result is not None and result_type != expected_result:
            raise TypeMismatchInExpression(node)
        return result_type

    def _finalize_relational(self, node, left_type, right_type):
        left_type = self._actual_type(left_type)
        right_type = self._actual_type(right_type)

        if self._is_pending_struct_literal(left_type) or self._is_pending_struct_literal(
            right_type
        ):
            raise TypeMismatchInExpression(node)

        if self._is_unknown(left_type) and self._is_unknown(right_type):
            raise TypeCannotBeInferred(node)

        if self._is_unknown(left_type):
            if not self._is_numeric(right_type):
                raise TypeMismatchInExpression(node)
            self._bind_unknown(left_type, right_type)
            left_type = right_type

        if self._is_unknown(right_type):
            if not self._is_numeric(left_type):
                raise TypeMismatchInExpression(node)
            self._bind_unknown(right_type, left_type)
            right_type = left_type

        if not self._is_numeric(left_type) or not self._is_numeric(right_type):
            raise TypeMismatchInExpression(node)
        return self.INT

    def _ensure_statement_type(self, expr, expected_type, stmt_node):
        expr_type = self._actual_type(self.visit(expr, self._expr_context(expected_type)))

        if self._is_pending_struct_literal(expr_type):
            raise TypeMismatchInStatement(stmt_node)
        if self._is_unknown(expr_type):
            self._bind_unknown(expr_type, expected_type)
            expr_type = expected_type
        if expr_type != expected_type:
            raise TypeMismatchInStatement(stmt_node)

    def _raise_assignment_mismatch(self, node, ctx):
        if ctx["assign_mode"] == "stmt":
            raise TypeMismatchInStatement(node)
        raise TypeMismatchInExpression(node)
