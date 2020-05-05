from enum import Enum
from tc.util import BaseVisitor, Environment


class Type(Enum):
    BOOL = 'bool'
    INT = 'int'
    FLOAT = 'float'
    STRING = 'string'
    UNIT = 'unit'


op_types = {
    '+': [Type.INT, Type.FLOAT, Type.STRING],
    '-': [Type.INT, Type.FLOAT],
    '*': [Type.INT, Type.FLOAT],
    '/': [Type.INT, Type.FLOAT],
    '^': [Type.INT, Type.FLOAT],
}
unary_op_types = {
    '-': [Type.INT, Type.FLOAT],
    'itof': [Type.INT]
}
logical_op_types = {
    '==': [Type.INT, Type.FLOAT, Type.STRING, Type.BOOL],
    '!=': [Type.INT, Type.FLOAT, Type.STRING, Type.BOOL],
    '>': [Type.INT, Type.FLOAT],
    '>=': [Type.INT, Type.FLOAT],
    '<=': [Type.INT, Type.FLOAT],
    '<': [Type.INT, Type.FLOAT],
}


class CallableSignature:
    def __init__(self, param_types, return_type):
        self.param_types = param_types
        self.return_type = return_type


class TypeCheck(BaseVisitor):
    def __init__(self):
        self.env = Environment(enclosing=None)

    def reset(self):
        self.env = Environment(enclosing=None)

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

    def visit_block(self, node):
        self.env = Environment(enclosing=self.env)
        for stmt in node.statements:
            self.visit(stmt)
        self.env = self.env.enclosing

    def visit_function_def(self, node):
        self.env = Environment(enclosing=self.env)
        for p in node.parameters:
            self.env.declare_var(p.name, p.type)

        try:
            self.visit(node.body)
        except TypeCheck.ReturnType as r:
            self.env = self.env.enclosing
            return_type = r.type
        except:
            raise Exception("Types don't match.")  # TODO: improve
        else:
            self.env = self.env.enclosing
            return_type = Type.UNIT

        param_types = [p.type for p in node.parameters]
        self.env.define_fun(node.name, CallableSignature(param_types, return_type))

    def visit_variable_declaration(self, node):
        if node.value:
            r_type = self.visit(node.value)
            assert node.type == r_type
        self.env.declare_var(node.name, node.type)

    def visit_assignment(self, node):
        l_type = self.env.resolve_var(node.name)
        r_type = self.visit(node.value)
        assert l_type == r_type

    def visit_if_stmt(self, node):
        assert self.visit(node.condition) == Type.BOOL
        self.visit(node.body)

    def visit_while_stmt(self, node):
        assert self.visit(node.condition) == Type.BOOL
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.env = Environment(enclosing=self.env)

        self.visit(node.initializer)
        assert self.visit(node.condition) == Type.BOOL
        self.visit(node.body)

        self.env = self.env.enclosing

    def visit_binary_expr(self, node):
        l_type = self.visit(node.left)
        r_type = self.visit(node.right)
        return self.check_binary(l_type, r_type, node.op)

    def visit_unary_expr(self, node):
        e_type = self.visit(node.expr)
        return self.check_unary(e_type, node.op)

    class ReturnType(Exception):
        def __init__(self, type):
            super()
            self.type = type

    def visit_return_stmt(self, node):
        type = self.visit(node.expr)
        raise TypeCheck.ReturnType(type)

    def visit_call(self, node):
        signature = self.env.resolve_fun(node.name)
        arg_types = [self.visit(a) for a in node.args]

        assert all([
            a_type == p_type for a_type, p_type in zip(arg_types, signature.param_types)
        ])
        return signature.return_type

    def visit_variable(self, node):
        return self.env.resolve_var(node.name)

    @staticmethod
    def visit_literal(node):
        return node.type

    def visit_unknown(self, m_name):
        pass

    @staticmethod
    def check_binary(l_type, r_type, op):
        if op in op_types:
            assert l_type in op_types[op] and r_type in op_types[op]
            return l_type
        else:
            assert l_type in logical_op_types[op] and r_type in logical_op_types[op]
            return Type.BOOL

    @staticmethod
    def check_unary(e_type, op):
        assert e_type in unary_op_types[op]
        if op == 'itof':  # TODO: improve
            return Type.FLOAT
        else:
            return e_type

