"""
Code generator for TyC.

The generator targets Jasmin/JVM bytecode.  It assumes the input AST has
already passed semantic checking, but still resolves enough type information to
generate bytecode for `auto` declarations and inferred function return types.
"""

from typing import Any, Optional

from ..utils.nodes import (
    AssignExpr,
    BinaryOp,
    BlockStmt,
    BreakStmt,
    CaseStmt,
    ContinueStmt,
    DefaultStmt,
    Expr,
    ExprStmt,
    FloatLiteral,
    FloatType,
    ForStmt,
    FuncCall,
    FuncDecl,
    Identifier,
    IfStmt,
    IntLiteral,
    IntType,
    MemberAccess,
    MemberDecl,
    Param,
    PostfixOp,
    PrefixOp,
    Program,
    ReturnStmt,
    StringLiteral,
    StringType,
    StructDecl,
    StructLiteral,
    StructType,
    SwitchStmt,
    Type,
    VarDecl,
    VoidType,
    WhileStmt,
)
from ..utils.visitor import BaseVisitor
from .emitter import Emitter
from .frame import Frame
from .io import IO_SYMBOL_LIST
from .utils import Access, CName, FunctionType, Index, SubBody, Symbol


class StringArrayType:
    """Marker type for JVM main(String[] args)."""

    pass


class CodeGenerator(BaseVisitor):
    """AST -> Jasmin code generator for TyC."""

    def __init__(self):
        self.emit: Optional[Emitter] = None
        self.functions: dict[str, Symbol] = {}
        self.function_decls: dict[str, FuncDecl] = {}
        self.structs: dict[str, StructDecl] = {}
        self.struct_members: dict[str, list[MemberDecl]] = {}
        self.var_decl_types: dict[int, Type] = {}
        self.current_return_type: Type = VoidType()
        self.class_name = "TyC"
        self.break_labels: list[int] = []
        self.continue_labels: list[int] = []

    # ------------------------------------------------------------------
    # Program preparation
    # ------------------------------------------------------------------

    def _reset(self):
        self.emit = None
        self.functions = {}
        self.function_decls = {}
        self.structs = {}
        self.struct_members = {}
        self.var_decl_types = {}
        self.current_return_type = VoidType()
        self.break_labels = []
        self.continue_labels = []

    def visit_program(self, node: Program, o: Any = None):
        self._reset()

        for decl in node.decls:
            if isinstance(decl, StructDecl):
                self.structs[decl.name] = decl
                self.struct_members[decl.name] = decl.members

        for io_sym in IO_SYMBOL_LIST:
            self.functions[io_sym.name] = io_sym

        for decl in node.decls:
            if isinstance(decl, FuncDecl):
                self.function_decls[decl.name] = decl
                self.functions[decl.name] = Symbol(
                    decl.name,
                    FunctionType([p.param_type for p in decl.params], decl.return_type),
                    CName(self.class_name),
                )

        self._resolve_inferred_types(node)
        self._emit_struct_classes()

        self.emit = Emitter(f"{self.class_name}.j")
        self.emit.print_out(self.emit.emit_prolog(self.class_name))

        for decl in node.decls:
            if isinstance(decl, FuncDecl):
                self.visit(decl, None)

        self.emit.emit_epilog()

    def _resolve_inferred_types(self, program: Program):
        funcs = [decl for decl in program.decls if isinstance(decl, FuncDecl)]

        for _ in range(len(funcs) + 3):
            changed = False
            self.var_decl_types = {}
            for func in funcs:
                inferred = self._infer_function_return(func)
                fn_type = self.functions[func.name].type
                if fn_type.return_type is None and inferred is not None:
                    fn_type.return_type = inferred
                    changed = True
            if not changed:
                break

        for func in funcs:
            fn_type = self.functions[func.name].type
            if fn_type.return_type is None:
                fn_type.return_type = VoidType()

        self.var_decl_types = {}
        for func in funcs:
            self._infer_function_return(func)

    def _infer_function_return(self, node: FuncDecl) -> Optional[Type]:
        fn_type = self.functions[node.name].type
        expected_return = node.return_type if node.return_type else fn_type.return_type
        scopes: list[dict[str, dict[str, Any]]] = [{}]
        for param in node.params:
            scopes[-1][param.name] = {"type": param.param_type, "node": param}

        returns: list[Optional[Type]] = []
        for stmt in node.body.statements:
            returns.extend(self._infer_stmt(stmt, scopes, expected_return))

        if node.return_type is not None:
            return node.return_type
        if fn_type.return_type is not None:
            return fn_type.return_type
        for typ in returns:
            if typ is not None:
                return typ
        if returns:
            return VoidType()
        return VoidType()

    def _infer_stmt(
        self,
        stmt,
        scopes: list[dict[str, dict[str, Any]]],
        expected_return: Optional[Type],
    ) -> list[Optional[Type]]:
        if isinstance(stmt, VarDecl):
            typ = stmt.var_type
            if typ is None and stmt.init_value is not None:
                typ = self._infer_expr_type(stmt.init_value, scopes)
            self.var_decl_types[id(stmt)] = typ
            scopes[-1][stmt.name] = {"type": typ, "node": stmt}
            return []

        if isinstance(stmt, BlockStmt):
            scopes.append({})
            returns: list[Optional[Type]] = []
            for child in stmt.statements:
                returns.extend(self._infer_stmt(child, scopes, expected_return))
            scopes.pop()
            return returns

        if isinstance(stmt, IfStmt):
            self._infer_expr_type(stmt.condition, scopes, IntType())
            returns = self._infer_nested_stmt(stmt.then_stmt, scopes, expected_return)
            if stmt.else_stmt:
                returns.extend(self._infer_nested_stmt(stmt.else_stmt, scopes, expected_return))
            return returns

        if isinstance(stmt, WhileStmt):
            self._infer_expr_type(stmt.condition, scopes, IntType())
            return self._infer_nested_stmt(stmt.body, scopes, expected_return)

        if isinstance(stmt, ForStmt):
            returns: list[Optional[Type]] = []
            if stmt.init:
                init_stmt = stmt.init if isinstance(stmt.init, VarDecl) else stmt.init.expr
                if isinstance(init_stmt, VarDecl):
                    self._infer_stmt(init_stmt, scopes, expected_return)
                else:
                    self._infer_expr_type(init_stmt, scopes, IntType())
            if stmt.condition:
                self._infer_expr_type(stmt.condition, scopes, IntType())
            if stmt.update:
                self._infer_expr_type(stmt.update, scopes, IntType())
            returns.extend(self._infer_nested_stmt(stmt.body, scopes, expected_return))
            return returns

        if isinstance(stmt, SwitchStmt):
            self._infer_expr_type(stmt.expr, scopes, IntType())
            scopes.append({})
            returns: list[Optional[Type]] = []
            for case in stmt.cases:
                self._infer_expr_type(case.expr, scopes, IntType())
                for child in case.statements:
                    returns.extend(self._infer_stmt(child, scopes, expected_return))
            if stmt.default_case:
                for child in stmt.default_case.statements:
                    returns.extend(self._infer_stmt(child, scopes, expected_return))
            scopes.pop()
            return returns

        if isinstance(stmt, ReturnStmt):
            if stmt.expr is None:
                return [VoidType()]
            return [self._infer_expr_type(stmt.expr, scopes, expected_return)]

        if isinstance(stmt, ExprStmt):
            self._infer_expr_type(stmt.expr, scopes)
            return []

        return []

    def _infer_nested_stmt(
        self,
        stmt,
        scopes: list[dict[str, dict[str, Any]]],
        expected_return: Optional[Type],
    ) -> list[Optional[Type]]:
        if isinstance(stmt, BlockStmt):
            return self._infer_stmt(stmt, scopes, expected_return)
        scopes.append({})
        try:
            return self._infer_stmt(stmt, scopes, expected_return)
        finally:
            scopes.pop()

    def _infer_expr_type(
        self,
        expr: Expr,
        scopes: list[dict[str, dict[str, Any]]],
        expected: Optional[Type] = None,
    ) -> Optional[Type]:
        if isinstance(expr, IntLiteral):
            return IntType()
        if isinstance(expr, FloatLiteral):
            return FloatType()
        if isinstance(expr, StringLiteral):
            return StringType()
        if isinstance(expr, Identifier):
            sym = self._lookup_infer_symbol(expr.name, scopes)
            if sym is None:
                return expected
            if sym["type"] is None and expected is not None:
                sym["type"] = expected
                if isinstance(sym["node"], VarDecl):
                    self.var_decl_types[id(sym["node"])] = expected
            return sym["type"]
        if isinstance(expr, FuncCall):
            fn_type = self.functions[expr.name].type
            for arg, param_type in zip(expr.args, fn_type.param_types):
                self._infer_expr_type(arg, scopes, param_type)
            return fn_type.return_type
        if isinstance(expr, StructLiteral):
            if self._is_struct_type(expected):
                for value, member in zip(expr.values, self.struct_members[expected.struct_name]):
                    self._infer_expr_type(value, scopes, member.member_type)
                return expected
            return expected
        if isinstance(expr, MemberAccess):
            obj_type = self._infer_expr_type(expr.obj, scopes)
            member = self._find_member(obj_type, expr.member)
            return member.member_type if member else expected
        if isinstance(expr, AssignExpr):
            lhs_type = self._infer_lvalue_type(expr.lhs, scopes)
            rhs_type = self._infer_expr_type(expr.rhs, scopes, lhs_type)
            if lhs_type is None and rhs_type is not None:
                self._bind_lvalue_type(expr.lhs, scopes, rhs_type)
                lhs_type = rhs_type
            return lhs_type or rhs_type
        if isinstance(expr, BinaryOp):
            if expr.operator in ("&&", "||", "%"):
                self._infer_expr_type(expr.left, scopes, IntType())
                self._infer_expr_type(expr.right, scopes, IntType())
                return IntType()
            if expr.operator in ("+", "-", "*", "/"):
                left_type = self._infer_expr_type(expr.left, scopes)
                right_type = self._infer_expr_type(expr.right, scopes)
                if left_type is None and right_type is not None:
                    left_type = self._infer_expr_type(expr.left, scopes, right_type)
                if right_type is None and left_type is not None:
                    right_type = self._infer_expr_type(expr.right, scopes, left_type)
                if self._is_float_type(left_type) or self._is_float_type(right_type):
                    return FloatType()
                return IntType()
            if expr.operator in ("<", "<=", ">", ">=", "==", "!="):
                left_type = self._infer_expr_type(expr.left, scopes)
                right_type = self._infer_expr_type(expr.right, scopes)
                if left_type is None and right_type is not None:
                    self._infer_expr_type(expr.left, scopes, right_type)
                if right_type is None and left_type is not None:
                    self._infer_expr_type(expr.right, scopes, left_type)
                return IntType()
        if isinstance(expr, PrefixOp):
            if expr.operator in ("++", "--", "!"):
                self._infer_expr_type(expr.operand, scopes, IntType())
                return IntType()
            return self._infer_expr_type(expr.operand, scopes, expected)
        if isinstance(expr, PostfixOp):
            self._infer_expr_type(expr.operand, scopes, IntType())
            return IntType()
        return expected

    def _lookup_infer_symbol(self, name: str, scopes):
        for scope in reversed(scopes):
            if name in scope:
                return scope[name]
        return None

    def _infer_lvalue_type(self, expr: Expr, scopes) -> Optional[Type]:
        if isinstance(expr, Identifier):
            sym = self._lookup_infer_symbol(expr.name, scopes)
            return sym["type"] if sym else None
        if isinstance(expr, MemberAccess):
            obj_type = self._infer_expr_type(expr.obj, scopes)
            member = self._find_member(obj_type, expr.member)
            return member.member_type if member else None
        return None

    def _bind_lvalue_type(self, expr: Expr, scopes, typ: Type):
        if isinstance(expr, Identifier):
            sym = self._lookup_infer_symbol(expr.name, scopes)
            if sym is not None:
                sym["type"] = typ
                if isinstance(sym["node"], VarDecl):
                    self.var_decl_types[id(sym["node"])] = typ

    # ------------------------------------------------------------------
    # Struct class emission
    # ------------------------------------------------------------------

    def _emit_struct_classes(self):
        for name, decl in self.structs.items():
            emitter = Emitter(f"{name}.j")
            emitter.print_out(f".source {name}.java\n")
            emitter.print_out(f".class public {name}\n")
            emitter.print_out(".super java/lang/Object\n")
            for member in decl.members:
                emitter.print_out(
                    f".field public {member.name} {emitter.get_jvm_type(member.member_type)}\n"
                )
            emitter.print_out("\n.method public <init>()V\n")
            emitter.print_out(".limit stack 100\n")
            emitter.print_out(".limit locals 1\n")
            emitter.print_out("\taload_0\n")
            emitter.print_out(emitter.jvm.emitINVOKESPECIAL())
            for member in decl.members:
                emitter.print_out("\taload_0\n")
                emitter.print_out(self._emit_default_value_raw(member.member_type, emitter))
                emitter.print_out(
                    emitter.jvm.emitPUTFIELD(
                        f"{name}/{member.name}", emitter.get_jvm_type(member.member_type)
                    )
                )
            emitter.print_out("\treturn\n")
            emitter.print_out(".end method\n")
            emitter.emit_epilog()

    def _emit_default_value_raw(self, typ: Type, emitter: Emitter) -> str:
        if self._is_int_type(typ):
            return "\ticonst_0\n"
        if self._is_float_type(typ):
            return "\tfconst_0\n"
        if self._is_string_type(typ):
            return '\tldc ""\n'
        if self._is_struct_type(typ):
            return (
                f"\tnew {typ.struct_name}\n"
                "\tdup\n"
                f"\tinvokespecial {typ.struct_name}/<init>()V\n"
            )
        return "\treturn\n"

    # ------------------------------------------------------------------
    # Function / statement generation
    # ------------------------------------------------------------------

    def visit_func_decl(self, node: FuncDecl, o: Any = None):
        fn_type = self.functions[node.name].type
        self.current_return_type = fn_type.return_type or VoidType()
        frame = Frame(node.name, self.current_return_type)
        frame.enter_scope(True)

        emitted_type = (
            FunctionType([StringArrayType()], VoidType())
            if node.name == "main"
            else FunctionType([p.param_type for p in node.params], self.current_return_type)
        )
        self.emit.print_out(self.emit.emit_method(node.name, emitted_type, True))

        start_label = frame.get_start_label()
        end_label = frame.get_end_label()
        self.emit.print_out(self.emit.emit_label(start_label, frame))

        local_syms: list[Symbol] = []
        if node.name == "main":
            args_idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(args_idx, "args", StringArrayType(), start_label, end_label)
            )

        for param in node.params:
            idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(idx, param.name, param.param_type, start_label, end_label)
            )
            local_syms.append(Symbol(param.name, param.param_type, Index(idx)))

        sub_body = SubBody(frame, local_syms)
        for stmt in node.body.statements:
            self.visit(stmt, sub_body)

        if self._is_void_type(self.current_return_type):
            self.emit.print_out(self.emit.emit_return(VoidType(), frame))
        else:
            self.emit.print_out(self._emit_default_value(self.current_return_type, frame))
            self.emit.print_out(self.emit.emit_return(self.current_return_type, frame))

        self.emit.print_out(self.emit.emit_label(end_label, frame))
        frame.exit_scope()
        self.emit.print_out(self.emit.emit_end_method(frame))

    def visit_block_stmt(self, node: BlockStmt, o: SubBody = None):
        frame = o.frame
        saved_len = len(o.sym)
        frame.enter_scope(False)
        start_label = frame.get_start_label()
        end_label = frame.get_end_label()
        self.emit.print_out(self.emit.emit_label(start_label, frame))
        try:
            for stmt in node.statements:
                self.visit(stmt, o)
        finally:
            self.emit.print_out(self.emit.emit_label(end_label, frame))
            frame.exit_scope()
            del o.sym[saved_len:]
        return o

    def _visit_scoped_stmt(self, stmt, o: SubBody):
        if isinstance(stmt, BlockStmt):
            return self.visit(stmt, o)
        return self.visit(BlockStmt([stmt]), o)

    def visit_var_decl(self, node: VarDecl, o: SubBody = None):
        frame = o.frame
        idx = frame.get_new_index()
        var_type = self._resolved_var_type(node)
        self.emit.print_out(
            self.emit.emit_var(
                idx,
                node.name,
                var_type,
                frame.get_start_label(),
                frame.get_end_label(),
            )
        )

        if node.init_value is not None:
            rhs_code, rhs_type = self._visit_expr_expected(
                node.init_value, Access(frame, o.sym), var_type
            )
            rhs_code = self._coerce(rhs_code, rhs_type, var_type, frame)
            if self._is_struct_type(var_type) and not isinstance(node.init_value, StructLiteral):
                rhs_code += self._emit_copy_struct_from_stack(var_type, frame)
            self.emit.print_out(rhs_code)
        else:
            self.emit.print_out(self._emit_default_value(var_type, frame))

        self.emit.print_out(self.emit.emit_write_var(node.name, var_type, idx, frame))
        o.sym.append(Symbol(node.name, var_type, Index(idx)))
        return o

    def visit_expr_stmt(self, node: ExprStmt, o: SubBody = None):
        code, expr_type = self.visit(node.expr, Access(o.frame, o.sym))
        self.emit.print_out(code)
        if not self._is_void_type(expr_type):
            self.emit.print_out(self.emit.emit_pop(o.frame))
        return o

    def visit_if_stmt(self, node: IfStmt, o: SubBody = None):
        frame = o.frame
        cond_code, _ = self._visit_expr_expected(node.condition, Access(frame, o.sym), IntType())
        else_label = frame.get_new_label()
        end_label = frame.get_new_label()
        self.emit.print_out(cond_code)
        self.emit.print_out(self.emit.emit_if_false(else_label, frame))
        self._visit_scoped_stmt(node.then_stmt, o)
        self.emit.print_out(self.emit.emit_goto(end_label, frame))
        self.emit.print_out(self.emit.emit_label(else_label, frame))
        if node.else_stmt:
            self._visit_scoped_stmt(node.else_stmt, o)
        self.emit.print_out(self.emit.emit_label(end_label, frame))
        return o

    def visit_while_stmt(self, node: WhileStmt, o: SubBody = None):
        frame = o.frame
        cond_label = frame.get_new_label()
        end_label = frame.get_new_label()
        self.break_labels.append(end_label)
        self.continue_labels.append(cond_label)
        try:
            self.emit.print_out(self.emit.emit_label(cond_label, frame))
            cond_code, _ = self._visit_expr_expected(node.condition, Access(frame, o.sym), IntType())
            self.emit.print_out(cond_code)
            self.emit.print_out(self.emit.emit_if_false(end_label, frame))
            self._visit_scoped_stmt(node.body, o)
            self.emit.print_out(self.emit.emit_goto(cond_label, frame))
            self.emit.print_out(self.emit.emit_label(end_label, frame))
        finally:
            self.continue_labels.pop()
            self.break_labels.pop()
        return o

    def visit_for_stmt(self, node: ForStmt, o: SubBody = None):
        frame = o.frame
        cond_label = frame.get_new_label()
        update_label = frame.get_new_label()
        end_label = frame.get_new_label()

        self.break_labels.append(end_label)
        self.continue_labels.append(update_label)
        try:
            if node.init:
                self.visit(node.init, o)
            self.emit.print_out(self.emit.emit_label(cond_label, frame))
            if node.condition:
                cond_code, _ = self._visit_expr_expected(
                    node.condition, Access(frame, o.sym), IntType()
                )
                self.emit.print_out(cond_code)
                self.emit.print_out(self.emit.emit_if_false(end_label, frame))
            self._visit_scoped_stmt(node.body, o)
            self.emit.print_out(self.emit.emit_label(update_label, frame))
            if node.update:
                update_code, update_type = self.visit(node.update, Access(frame, o.sym))
                self.emit.print_out(update_code)
                if not self._is_void_type(update_type):
                    self.emit.print_out(self.emit.emit_pop(frame))
            self.emit.print_out(self.emit.emit_goto(cond_label, frame))
            self.emit.print_out(self.emit.emit_label(end_label, frame))
        finally:
            self.continue_labels.pop()
            self.break_labels.pop()
        return o

    def visit_switch_stmt(self, node: SwitchStmt, o: SubBody = None):
        frame = o.frame
        saved_len = len(o.sym)
        frame.enter_scope(False)
        start_scope = frame.get_start_label()
        end_scope = frame.get_end_label()
        self.emit.print_out(self.emit.emit_label(start_scope, frame))

        end_label = frame.get_new_label()
        default_label = frame.get_new_label() if node.default_case else end_label
        case_labels = [frame.get_new_label() for _ in node.cases]
        temp_idx = frame.get_new_index()

        self.break_labels.append(end_label)
        try:
            expr_code, _ = self._visit_expr_expected(node.expr, Access(frame, o.sym), IntType())
            self.emit.print_out(expr_code)
            self.emit.print_out(self.emit.emit_write_var("__switch", IntType(), temp_idx, frame))

            for case, label in zip(node.cases, case_labels):
                self.emit.print_out(self.emit.emit_read_var("__switch", IntType(), temp_idx, frame))
                case_code, _ = self._visit_expr_expected(case.expr, Access(frame, o.sym), IntType())
                self.emit.print_out(case_code)
                frame.pop()
                frame.pop()
                self.emit.print_out(self.emit.jvm.emitIFICMPEQ(label))
            self.emit.print_out(self.emit.emit_goto(default_label, frame))

            for case, label in zip(node.cases, case_labels):
                self.emit.print_out(self.emit.emit_label(label, frame))
                for stmt in case.statements:
                    self.visit(stmt, o)

            if node.default_case:
                self.emit.print_out(self.emit.emit_label(default_label, frame))
                for stmt in node.default_case.statements:
                    self.visit(stmt, o)

            self.emit.print_out(self.emit.emit_label(end_label, frame))
        finally:
            self.break_labels.pop()
            self.emit.print_out(self.emit.emit_label(end_scope, frame))
            frame.exit_scope()
            del o.sym[saved_len:]
        return o

    def visit_case_stmt(self, node: CaseStmt, o: Any = None):
        return None

    def visit_default_stmt(self, node: DefaultStmt, o: Any = None):
        return None

    def visit_break_stmt(self, node: BreakStmt, o: SubBody = None):
        self.emit.print_out(self.emit.emit_goto(self.break_labels[-1], o.frame))
        return o

    def visit_continue_stmt(self, node: ContinueStmt, o: SubBody = None):
        self.emit.print_out(self.emit.emit_goto(self.continue_labels[-1], o.frame))
        return o

    def visit_return_stmt(self, node: ReturnStmt, o: SubBody = None):
        if node.expr is None:
            self.emit.print_out(self.emit.emit_return(VoidType(), o.frame))
            return o
        code, ret_type = self._visit_expr_expected(
            node.expr, Access(o.frame, o.sym), self.current_return_type
        )
        code = self._coerce(code, ret_type, self.current_return_type, o.frame)
        if self._is_struct_type(self.current_return_type) and not isinstance(node.expr, StructLiteral):
            code += self._emit_copy_struct_from_stack(self.current_return_type, o.frame)
        self.emit.print_out(code)
        self.emit.print_out(self.emit.emit_return(self.current_return_type, o.frame))
        return o

    # ------------------------------------------------------------------
    # Expression generation
    # ------------------------------------------------------------------

    def visit_binary_op(self, node: BinaryOp, o: Access = None):
        frame = o.frame
        if node.operator in ("&&", "||"):
            return self._emit_logical_binary(node, o), IntType()

        left_code, left_type = self.visit(node.left, o)
        right_code, right_type = self.visit(node.right, o)

        if node.operator in ("+", "-", "*", "/"):
            result_type = (
                FloatType()
                if self._is_float_type(left_type) or self._is_float_type(right_type)
                else IntType()
            )
            left_code = self._coerce(left_code, left_type, result_type, frame)
            right_code = self._coerce(right_code, right_type, result_type, frame)
            op_code = (
                self.emit.emit_add_op(node.operator, result_type, frame)
                if node.operator in ("+", "-")
                else self.emit.emit_mul_op(node.operator, result_type, frame)
            )
            return left_code + right_code + op_code, result_type

        if node.operator == "%":
            return left_code + right_code + self.emit.emit_mod(frame), IntType()

        if node.operator in ("<", "<=", ">", ">=", "==", "!="):
            op_type = (
                FloatType()
                if self._is_float_type(left_type) or self._is_float_type(right_type)
                else IntType()
            )
            left_code = self._coerce(left_code, left_type, op_type, frame)
            right_code = self._coerce(right_code, right_type, op_type, frame)
            return left_code + right_code + self.emit.emit_re_op(node.operator, op_type, frame), IntType()

        raise RuntimeError(f"Unsupported operator: {node.operator}")

    def _emit_logical_binary(self, node: BinaryOp, o: Access) -> str:
        frame = o.frame
        result_label = frame.get_new_label()
        end_label = frame.get_new_label()
        left_code, _ = self._visit_expr_expected(node.left, o, IntType())
        code = left_code
        if node.operator == "&&":
            code += self.emit.emit_if_false(result_label, frame)
            right_code, _ = self._visit_expr_expected(node.right, o, IntType())
            code += right_code
            code += self.emit.emit_if_false(result_label, frame)
            code += self.emit.emit_push_iconst(1, frame)
            code += self.emit.emit_goto(end_label, frame)
            code += self.emit.emit_label(result_label, frame)
            code += self.emit.emit_push_iconst(0, frame)
        else:
            code += self.emit.emit_if_true(result_label, frame)
            right_code, _ = self._visit_expr_expected(node.right, o, IntType())
            code += right_code
            code += self.emit.emit_if_true(result_label, frame)
            code += self.emit.emit_push_iconst(0, frame)
            code += self.emit.emit_goto(end_label, frame)
            code += self.emit.emit_label(result_label, frame)
            code += self.emit.emit_push_iconst(1, frame)
        code += self.emit.emit_label(end_label, frame)
        return code

    def visit_prefix_op(self, node: PrefixOp, o: Access = None):
        if node.operator == "+":
            return self.visit(node.operand, o)
        if node.operator == "-":
            code, typ = self.visit(node.operand, o)
            return code + self.emit.emit_neg_op(typ, o.frame), typ
        if node.operator == "!":
            code, _ = self._visit_expr_expected(node.operand, o, IntType())
            true_label = o.frame.get_new_label()
            end_label = o.frame.get_new_label()
            code += self.emit.emit_if_false(true_label, o.frame)
            code += self.emit.emit_push_iconst(0, o.frame)
            code += self.emit.emit_goto(end_label, o.frame)
            code += self.emit.emit_label(true_label, o.frame)
            code += self.emit.emit_push_iconst(1, o.frame)
            code += self.emit.emit_label(end_label, o.frame)
            return code, IntType()
        if node.operator in ("++", "--"):
            return self._emit_inc_dec(node.operand, node.operator, o, prefix=True), IntType()
        raise RuntimeError(f"Unsupported prefix operator: {node.operator}")

    def visit_postfix_op(self, node: PostfixOp, o: Access = None):
        if node.operator in ("++", "--"):
            return self._emit_inc_dec(node.operand, node.operator, o, prefix=False), IntType()
        raise RuntimeError(f"Unsupported postfix operator: {node.operator}")

    def _emit_inc_dec(self, operand: Expr, operator: str, o: Access, prefix: bool) -> str:
        if isinstance(operand, Identifier):
            sym = self._lookup_symbol(operand.name, o.sym)
            read = self.emit.emit_read_var(operand.name, sym.type, sym.value.value, o.frame)
            if prefix:
                code = read
                code += self.emit.emit_push_iconst(1, o.frame)
                code += self.emit.emit_add_op("+" if operator == "++" else "-", IntType(), o.frame)
                code += self.emit.emit_dup(o.frame)
                code += self.emit.emit_write_var(operand.name, sym.type, sym.value.value, o.frame)
                return code
            code = read
            code += self.emit.emit_dup(o.frame)
            code += self.emit.emit_push_iconst(1, o.frame)
            code += self.emit.emit_add_op("+" if operator == "++" else "-", IntType(), o.frame)
            code += self.emit.emit_write_var(operand.name, sym.type, sym.value.value, o.frame)
            return code

        if isinstance(operand, MemberAccess):
            obj_code, owner_name, member_type = self._emit_member_owner(operand, o)
            field = f"{owner_name}/{operand.member}"
            if prefix:
                code = obj_code
                code += self.emit.emit_dup(o.frame)
                code += self.emit.emit_get_field(field, member_type, o.frame)
                code += self.emit.emit_push_iconst(1, o.frame)
                code += self.emit.emit_add_op("+" if operator == "++" else "-", IntType(), o.frame)
                code += self.emit.emit_dup_x1(o.frame)
                code += self.emit.emit_put_field(field, member_type, o.frame)
                return code
            code = obj_code
            code += self.emit.emit_dup(o.frame)
            code += self.emit.emit_get_field(field, member_type, o.frame)
            code += self.emit.emit_dup_x1(o.frame)
            code += self.emit.emit_push_iconst(1, o.frame)
            code += self.emit.emit_add_op("+" if operator == "++" else "-", IntType(), o.frame)
            code += self.emit.emit_put_field(field, member_type, o.frame)
            return code

        raise RuntimeError("Increment/decrement requires an lvalue")

    def visit_assign_expr(self, node: AssignExpr, o: Access = None):
        if isinstance(node.lhs, Identifier):
            lhs_sym = self._lookup_symbol(node.lhs.name, o.sym)
            rhs_code, rhs_type = self._visit_expr_expected(node.rhs, o, lhs_sym.type)
            rhs_code = self._coerce(rhs_code, rhs_type, lhs_sym.type, o.frame)
            if self._is_struct_type(lhs_sym.type) and not isinstance(node.rhs, StructLiteral):
                rhs_code += self._emit_copy_struct_from_stack(lhs_sym.type, o.frame)
            code = rhs_code + self.emit.emit_dup(o.frame)
            code += self.emit.emit_write_var(node.lhs.name, lhs_sym.type, lhs_sym.value.value, o.frame)
            return code, lhs_sym.type

        if isinstance(node.lhs, MemberAccess):
            obj_code, owner_name, member_type = self._emit_member_owner(node.lhs, o)
            rhs_code, rhs_type = self._visit_expr_expected(node.rhs, o, member_type)
            rhs_code = self._coerce(rhs_code, rhs_type, member_type, o.frame)
            if self._is_struct_type(member_type) and not isinstance(node.rhs, StructLiteral):
                rhs_code += self._emit_copy_struct_from_stack(member_type, o.frame)
            code = obj_code + rhs_code + self.emit.emit_dup_x1(o.frame)
            code += self.emit.emit_put_field(f"{owner_name}/{node.lhs.member}", member_type, o.frame)
            return code, member_type

        raise RuntimeError("Assignment requires an lvalue")

    def visit_member_access(self, node: MemberAccess, o: Access = None):
        obj_code, owner_name, member_type = self._emit_member_owner(node, o)
        return obj_code + self.emit.emit_get_field(f"{owner_name}/{node.member}", member_type, o.frame), member_type

    def _emit_member_owner(self, node: MemberAccess, o: Access):
        obj_code, obj_type = self.visit(node.obj, o)
        if not self._is_struct_type(obj_type):
            raise RuntimeError("Member access requires a struct value")
        member = self._find_member(obj_type, node.member)
        if member is None:
            raise RuntimeError(f"Unknown member {node.member} of {obj_type.struct_name}")
        return obj_code, obj_type.struct_name, member.member_type

    def visit_func_call(self, node: FuncCall, o: Access = None):
        frame = o.frame
        fn_sym = self.functions[node.name]
        fn_type = fn_sym.type
        code = ""
        for index, arg in enumerate(node.args):
            param_type = fn_type.param_types[index]
            arg_code, arg_type = self._visit_expr_expected(arg, o, param_type)
            arg_code = self._coerce(arg_code, arg_type, param_type, frame)
            if self._is_struct_type(param_type) and not isinstance(arg, StructLiteral):
                arg_code += self._emit_copy_struct_from_stack(param_type, frame)
            code += arg_code
        code += self.emit.emit_invoke_static(f"{fn_sym.value.value}/{node.name}", fn_type, frame)
        return code, fn_type.return_type

    def visit_identifier(self, node: Identifier, o: Access = None):
        sym = self._lookup_symbol(node.name, o.sym)
        return self.emit.emit_read_var(node.name, sym.type, sym.value.value, o.frame), sym.type

    def visit_struct_literal(self, node: StructLiteral, o: Access = None):
        expected = getattr(o, "expected_type", None)
        if not self._is_struct_type(expected):
            raise RuntimeError("Struct literal requires an expected struct type")
        code = self.emit.emit_new_instance(expected.struct_name, o.frame)
        for value, member in zip(node.values, self.struct_members[expected.struct_name]):
            code += self.emit.emit_dup(o.frame)
            value_code, value_type = self._visit_expr_expected(value, o, member.member_type)
            value_code = self._coerce(value_code, value_type, member.member_type, o.frame)
            if self._is_struct_type(member.member_type) and not isinstance(value, StructLiteral):
                value_code += self._emit_copy_struct_from_stack(member.member_type, o.frame)
            code += value_code
            code += self.emit.emit_put_field(
                f"{expected.struct_name}/{member.name}", member.member_type, o.frame
            )
        return code, expected

    def visit_int_literal(self, node: IntLiteral, o: Access = None):
        return self.emit.emit_push_iconst(node.value, o.frame), IntType()

    def visit_float_literal(self, node: FloatLiteral, o: Access = None):
        return self.emit.emit_push_fconst(str(node.value), o.frame), FloatType()

    def visit_string_literal(self, node: StringLiteral, o: Access = None):
        return self.emit.emit_push_const(node.value, StringType(), o.frame), StringType()

    # ------------------------------------------------------------------
    # Type/default/copy helpers
    # ------------------------------------------------------------------

    def _visit_expr_expected(self, expr: Expr, o: Access, expected: Optional[Type]):
        access = Access(o.frame, o.sym, o.is_left, o.is_first)
        access.expected_type = expected
        return self.visit(expr, access)

    def _resolved_var_type(self, node: VarDecl) -> Type:
        typ = node.var_type or self.var_decl_types.get(id(node))
        if typ is None and node.init_value is not None:
            typ = self._infer_type_runtime(node.init_value, [])
        return typ or IntType()

    def _infer_type_runtime(self, node: Expr, sym_list: list[Symbol]) -> Type:
        if isinstance(node, IntLiteral):
            return IntType()
        if isinstance(node, FloatLiteral):
            return FloatType()
        if isinstance(node, StringLiteral):
            return StringType()
        if isinstance(node, Identifier):
            return self._lookup_symbol(node.name, sym_list).type
        if isinstance(node, FuncCall):
            return self.functions[node.name].type.return_type
        if isinstance(node, AssignExpr):
            return self._infer_type_runtime(node.lhs, sym_list)
        if isinstance(node, MemberAccess):
            obj_type = self._infer_type_runtime(node.obj, sym_list)
            member = self._find_member(obj_type, node.member)
            return member.member_type
        if isinstance(node, BinaryOp):
            if node.operator in ("&&", "||", "%", "<", "<=", ">", ">=", "==", "!="):
                return IntType()
            left = self._infer_type_runtime(node.left, sym_list)
            right = self._infer_type_runtime(node.right, sym_list)
            return FloatType() if self._is_float_type(left) or self._is_float_type(right) else IntType()
        if isinstance(node, (PrefixOp, PostfixOp)):
            if node.operator in ("++", "--", "!"):
                return IntType()
            return self._infer_type_runtime(node.operand, sym_list)
        return IntType()

    def _emit_default_value(self, typ: Type, frame: Frame) -> str:
        if self._is_int_type(typ):
            return self.emit.emit_push_iconst(0, frame)
        if self._is_float_type(typ):
            return self.emit.emit_push_fconst("0.0", frame)
        if self._is_string_type(typ):
            return self.emit.emit_push_const("", StringType(), frame)
        if self._is_struct_type(typ):
            return self.emit.emit_new_instance(typ.struct_name, frame)
        return ""

    def _emit_copy_struct_from_stack(self, typ: Type, frame: Frame) -> str:
        if not self._is_struct_type(typ):
            return ""
        temp_idx = frame.get_new_index()
        code = self.emit.emit_write_var("__copy", typ, temp_idx, frame)
        code += self.emit.emit_new_instance(typ.struct_name, frame)
        for member in self.struct_members[typ.struct_name]:
            code += self.emit.emit_dup(frame)
            code += self.emit.emit_read_var("__copy", typ, temp_idx, frame)
            code += self.emit.emit_get_field(f"{typ.struct_name}/{member.name}", member.member_type, frame)
            if self._is_struct_type(member.member_type):
                code += self._emit_copy_struct_from_stack(member.member_type, frame)
            code += self.emit.emit_put_field(
                f"{typ.struct_name}/{member.name}", member.member_type, frame
            )
        return code

    def _coerce(self, code: str, from_type: Type, to_type: Optional[Type], frame: Frame) -> str:
        if to_type is not None and self._is_float_type(to_type) and self._is_int_type(from_type):
            return code + self.emit.emit_i2f(frame)
        return code

    def _lookup_symbol(self, name: str, sym_list: list[Symbol]) -> Symbol:
        for sym in reversed(sym_list):
            if sym.name == name:
                return sym
        raise RuntimeError(f"Undeclared symbol: {name}")

    def _find_member(self, struct_type: Optional[Type], member_name: str) -> Optional[MemberDecl]:
        if not self._is_struct_type(struct_type):
            return None
        for member in self.struct_members.get(struct_type.struct_name, []):
            if member.name == member_name:
                return member
        return None

    def _is_int_type(self, typ) -> bool:
        return isinstance(typ, IntType)

    def _is_float_type(self, typ) -> bool:
        return isinstance(typ, FloatType)

    def _is_string_type(self, typ) -> bool:
        return isinstance(typ, StringType)

    def _is_void_type(self, typ) -> bool:
        return isinstance(typ, VoidType)

    def _is_struct_type(self, typ) -> bool:
        return isinstance(typ, StructType)

    # ------------------------------------------------------------------
    # Trivial visitor implementations
    # ------------------------------------------------------------------

    def visit_struct_decl(self, node: StructDecl, o: Any = None):
        return None

    def visit_member_decl(self, node: MemberDecl, o: Any = None):
        return None

    def visit_param(self, node: Param, o: Any = None):
        return None

    def visit_int_type(self, node: IntType, o: Any = None):
        return node

    def visit_float_type(self, node: FloatType, o: Any = None):
        return node

    def visit_string_type(self, node: StringType, o: Any = None):
        return node

    def visit_void_type(self, node: VoidType, o: Any = None):
        return node

    def visit_struct_type(self, node: StructType, o: Any = None):
        return node
