"""
AST Generation module for TyC programming language.
This module contains the ASTGeneration class that converts parse trees
into Abstract Syntax Trees using the visitor pattern.
"""

from build.TyCVisitor import TyCVisitor
from src.utils.nodes import *


class ASTGeneration(TyCVisitor):
    """AST Generation visitor for TyC language."""

    def visitProgram(self, ctx):
        decls = []
        struct_decls = ctx.structDecl()
        func_decls = ctx.funcDecl()
        struct_type = type(struct_decls[0]) if struct_decls else None
        func_type = type(func_decls[0]) if func_decls else None

        for child in ctx.children:
            if struct_type is not None and isinstance(child, struct_type):
                decls.append(self.visit(child))
            elif func_type is not None and isinstance(child, func_type):
                decls.append(self.visit(child))
        return Program(decls)

    def visitStructDecl(self, ctx):
        name = ctx.ID().getText()
        members = [self.visit(member) for member in ctx.structMember()]
        return StructDecl(name, members)

    def visitStructMember(self, ctx):
        member_type = self.visit(ctx.typeSpecNoVoid())
        name = ctx.ID().getText()
        return MemberDecl(member_type, name)

    def visitFuncDecl(self, ctx):
        return_type = self.visit(ctx.returnType()) if ctx.returnType() else None
        name = ctx.ID().getText()
        params = self.visit(ctx.paramList()) if ctx.paramList() else []
        body = self.visit(ctx.block())
        return FuncDecl(return_type, name, params, body)

    def visitReturnType(self, ctx):
        return self.visit(ctx.typeSpec())

    def visitTypeSpec(self, ctx):
        if ctx.primitiveType():
            return self.visit(ctx.primitiveType())
        return StructType(ctx.ID().getText())

    def visitPrimitiveType(self, ctx):
        if ctx.INT():
            return IntType()
        if ctx.FLOAT():
            return FloatType()
        if ctx.STRING():
            return StringType()
        return VoidType()

    def visitTypeSpecNoVoid(self, ctx):
        if ctx.primitiveNoVoid():
            return self.visit(ctx.primitiveNoVoid())
        return StructType(ctx.ID().getText())

    def visitPrimitiveNoVoid(self, ctx):
        if ctx.INT():
            return IntType()
        if ctx.FLOAT():
            return FloatType()
        return StringType()

    def visitParamList(self, ctx):
        return [self.visit(param) for param in ctx.param()]

    def visitParam(self, ctx):
        param_type = self.visit(ctx.typeSpecNoVoid())
        name = ctx.ID().getText()
        return Param(param_type, name)

    def visitBlock(self, ctx):
        statements = self.visit(ctx.statementList()) if ctx.statementList() else []
        return BlockStmt(statements)

    def visitStatementList(self, ctx):
        return [self.visit(statement) for statement in ctx.statement()]

    def visitStatement(self, ctx):
        if ctx.varDeclStmt():
            return self.visit(ctx.varDeclStmt())
        if ctx.block():
            return self.visit(ctx.block())
        if ctx.ifStmt():
            return self.visit(ctx.ifStmt())
        if ctx.whileStmt():
            return self.visit(ctx.whileStmt())
        if ctx.forStmt():
            return self.visit(ctx.forStmt())
        if ctx.switchStmt():
            return self.visit(ctx.switchStmt())
        if ctx.breakStmt():
            return self.visit(ctx.breakStmt())
        if ctx.continueStmt():
            return self.visit(ctx.continueStmt())
        if ctx.returnStmt():
            return self.visit(ctx.returnStmt())
        return self.visit(ctx.exprStmt())

    def visitVarDeclStmt(self, ctx):
        return self.visit(ctx.varDecl())

    def visitVarDecl(self, ctx):
        var_type = None if ctx.AUTO() else self.visit(ctx.typeSpecNoVoid())
        name = ctx.ID().getText()
        init_value = self.visit(ctx.expr()) if ctx.expr() else None
        return VarDecl(var_type, name, init_value)

    def visitIfStmt(self, ctx):
        condition = self.visit(ctx.expr())
        statements = ctx.statement()
        then_stmt = self.visit(statements[0])
        else_stmt = self.visit(statements[1]) if len(statements) > 1 else None
        return IfStmt(condition, then_stmt, else_stmt)

    def visitWhileStmt(self, ctx):
        condition = self.visit(ctx.expr())
        body = self.visit(ctx.statement())
        return WhileStmt(condition, body)

    def visitForStmt(self, ctx):
        init = None
        if ctx.forInit():
            init_node = self.visit(ctx.forInit())
            init = init_node if isinstance(init_node, VarDecl) else ExprStmt(init_node)

        condition = self.visit(ctx.forCond()) if ctx.forCond() else None
        update = self.visit(ctx.forUpdate()) if ctx.forUpdate() else None
        body = self.visit(ctx.statement())
        return ForStmt(init, condition, update, body)

    def visitForInit(self, ctx):
        if ctx.varDecl():
            return self.visit(ctx.varDecl())
        return self.visit(ctx.forAssign())

    def visitForCond(self, ctx):
        return self.visit(ctx.expr())

    def visitForUpdate(self, ctx):
        if ctx.forIncDec():
            return self.visit(ctx.forIncDec())
        return self.visit(ctx.forAssign())

    def visitForAssign(self, ctx):
        lhs = self.visit(ctx.lvalue())
        rhs = self.visit(ctx.assignmentExpr())
        return AssignExpr(lhs, rhs)

    def visitForIncDec(self, ctx):
        if ctx.prefixIncDec():
            return self.visit(ctx.prefixIncDec())

        node = self.visit(ctx.postfixBase())
        for child in ctx.children[1:]:
            text = child.getText()
            if text in ("++", "--"):
                node = PostfixOp(text, node)
        return node

    def visitSwitchStmt(self, ctx):
        expr = self.visit(ctx.expr())
        cases = []
        for section in ctx.switchSection():
            cases.extend(self.visit(section))
        default_case = self.visit(ctx.defaultSection()) if ctx.defaultSection() else None
        return SwitchStmt(expr, cases, default_case)

    def visitSwitchSection(self, ctx):
        labels = [self.visit(label) for label in ctx.caseLabel()]
        statements = self.visit(ctx.statementList()) if ctx.statementList() else []
        cases = []
        for index, label in enumerate(labels):
            case_statements = statements if index == len(labels) - 1 else []
            cases.append(CaseStmt(label, case_statements))
        return cases

    def visitCaseLabel(self, ctx):
        return self.visit(ctx.expr())

    def visitDefaultSection(self, ctx):
        statements = self.visit(ctx.statementList()) if ctx.statementList() else []
        return DefaultStmt(statements)

    def visitBreakStmt(self, ctx):
        return BreakStmt()

    def visitContinueStmt(self, ctx):
        return ContinueStmt()

    def visitReturnStmt(self, ctx):
        expr = self.visit(ctx.expr()) if ctx.expr() else None
        return ReturnStmt(expr)

    def visitExprStmt(self, ctx):
        return ExprStmt(self.visit(ctx.expr()))

    def visitExpr(self, ctx):
        return self.visit(ctx.assignmentExpr())

    def visitAssignmentExpr(self, ctx):
        if ctx.ASSIGN():
            lhs = self.visit(ctx.lvalue())
            rhs = self.visit(ctx.assignmentExpr())
            return AssignExpr(lhs, rhs)
        return self.visit(ctx.logicalOrExpr())

    def visitLogicalOrExpr(self, ctx):
        terms = [self.visit(term) for term in ctx.logicalAndExpr()]
        if len(terms) == 1:
            return terms[0]
        operators = [token.getText() for token in ctx.OR()]
        node = terms[0]
        for operator, right in zip(operators, terms[1:]):
            node = BinaryOp(node, operator, right)
        return node

    def visitLogicalAndExpr(self, ctx):
        terms = [self.visit(term) for term in ctx.equalityExpr()]
        if len(terms) == 1:
            return terms[0]
        operators = [token.getText() for token in ctx.AND()]
        node = terms[0]
        for operator, right in zip(operators, terms[1:]):
            node = BinaryOp(node, operator, right)
        return node

    def visitEqualityExpr(self, ctx):
        terms = [self.visit(term) for term in ctx.relationalExpr()]
        if len(terms) == 1:
            return terms[0]
        operators = [
            child.getText() for child in ctx.children if child.getText() in ("==", "!=")
        ]
        node = terms[0]
        for operator, right in zip(operators, terms[1:]):
            node = BinaryOp(node, operator, right)
        return node

    def visitRelationalExpr(self, ctx):
        terms = [self.visit(term) for term in ctx.additiveExpr()]
        if len(terms) == 1:
            return terms[0]
        operators = [
            child.getText()
            for child in ctx.children
            if child.getText() in ("<", "<=", ">", ">=")
        ]
        node = terms[0]
        for operator, right in zip(operators, terms[1:]):
            node = BinaryOp(node, operator, right)
        return node

    def visitAdditiveExpr(self, ctx):
        terms = [self.visit(term) for term in ctx.multiplicativeExpr()]
        if len(terms) == 1:
            return terms[0]
        operators = [child.getText() for child in ctx.children if child.getText() in ("+", "-")]
        node = terms[0]
        for operator, right in zip(operators, terms[1:]):
            node = BinaryOp(node, operator, right)
        return node

    def visitMultiplicativeExpr(self, ctx):
        terms = [self.visit(term) for term in ctx.unaryExpr()]
        if len(terms) == 1:
            return terms[0]
        operators = [child.getText() for child in ctx.children if child.getText() in ("*", "/", "%")]
        node = terms[0]
        for operator, right in zip(operators, terms[1:]):
            node = BinaryOp(node, operator, right)
        return node

    def visitUnaryExpr(self, ctx):
        if ctx.prefixIncDec():
            return self.visit(ctx.prefixIncDec())
        if ctx.postfixExpr():
            return self.visit(ctx.postfixExpr())
        operator = ctx.getChild(0).getText()
        operand = self.visit(ctx.unaryExpr())
        return PrefixOp(operator, operand)

    def visitPrefixIncDec(self, ctx):
        operator = ctx.getChild(0).getText()
        operand_ctx = ctx.prefixIncDec() if ctx.prefixIncDec() else ctx.postfixExpr()
        operand = self.visit(operand_ctx)
        return PrefixOp(operator, operand)

    def visitPostfixExpr(self, ctx):
        node = self.visit(ctx.postfixBase())
        for child in ctx.children[1:]:
            text = child.getText()
            if text in ("++", "--"):
                node = PostfixOp(text, node)
        return node

    def visitPostfixBase(self, ctx):
        if ctx.callSuffix():
            tokens = ctx.ID()
            node = FuncCall(tokens[0].getText(), self.visit(ctx.callSuffix()))
            for token in tokens[1:]:
                node = MemberAccess(node, token.getText())
            return node

        if ctx.primaryExprNoId():
            node = self.visit(ctx.primaryExprNoId())
            for token in ctx.ID():
                node = MemberAccess(node, token.getText())
            return node

        tokens = ctx.ID()
        node = Identifier(tokens[0].getText())
        for token in tokens[1:]:
            node = MemberAccess(node, token.getText())
        return node

    def visitLvalue(self, ctx):
        if ctx.callSuffix():
            tokens = ctx.ID()
            node = FuncCall(tokens[0].getText(), self.visit(ctx.callSuffix()))
            for token in tokens[1:]:
                node = MemberAccess(node, token.getText())
            return node

        if ctx.primaryExprNoId():
            node = self.visit(ctx.primaryExprNoId())
            for token in ctx.ID():
                node = MemberAccess(node, token.getText())
            return node

        tokens = ctx.ID()
        node = Identifier(tokens[0].getText())
        for token in tokens[1:]:
            node = MemberAccess(node, token.getText())
        return node

    def visitPrimaryExprNoId(self, ctx):
        if ctx.literal():
            return self.visit(ctx.literal())
        if ctx.structLiteral():
            return self.visit(ctx.structLiteral())
        return self.visit(ctx.expr())

    def visitCallSuffix(self, ctx):
        return self.visit(ctx.argList()) if ctx.argList() else []

    def visitArgList(self, ctx):
        return [self.visit(expr) for expr in ctx.expr()]

    def visitStructLiteral(self, ctx):
        values = self.visit(ctx.exprList()) if ctx.exprList() else []
        return StructLiteral(values)

    def visitExprList(self, ctx):
        return [self.visit(expr) for expr in ctx.expr()]

    def visitLiteral(self, ctx):
        if ctx.INT_LIT():
            return IntLiteral(int(ctx.INT_LIT().getText()))
        if ctx.FLOAT_LIT():
            return FloatLiteral(float(ctx.FLOAT_LIT().getText()))
        return StringLiteral(ctx.STRING_LIT().getText())
