from tc.globals import global_env
from tc.common import BaseVisitor, Callable, CallableSignature, Environment, Type


binary_signatures = {
    (Type.INT, Type.INT): {
        '+': Type.INT, 
        '-': Type.INT, 
        '*': Type.INT,
        '%': Type.INT,
        '^': Type.INT,
        '==': Type.BOOL, 
        '!=': Type.BOOL, 
        '<': Type.BOOL, 
        '<=': Type.BOOL, 
        '>': Type.BOOL, 
        '>=': Type.BOOL
    },
    (Type.FLOAT, Type.FLOAT): {
        '+': Type.FLOAT, 
        '-': Type.FLOAT, 
        '*': Type.FLOAT,
        '/': Type.FLOAT,
        '^': Type.FLOAT,
        '==': Type.BOOL, 
        '!=': Type.BOOL, 
        '<': Type.BOOL, 
        '<=': Type.BOOL, 
        '>': Type.BOOL, 
        '>=': Type.BOOL
    }, 
    (Type.BOOL, Type.BOOL): {
        '==': Type.BOOL,
        '!=': Type.BOOL
    }, 
    (Type.STRING, Type.STRING): {
        '+': Type.STRING,
        '==': Type.BOOL,
        '!=': Type.BOOL
    }
}

unary_signatures = {
    Type.INT: {
        '-': Type.INT,
        'itof': Type.FLOAT
    },
    Type.FLOAT: {
        '-': Type.FLOAT
    } 
}


class TypeCheck(BaseVisitor):
    def __init__(self):
        self.env = global_env()

    def reset(self):
        self.env = global_env()

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

    def visit_block(self, node):
        try:
            self.env = Environment(enclosing=self.env)
            for stmt in node.statements:
                self.visit(stmt)
        finally:
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
        else:
            self.env = self.env.enclosing
            return_type = Type.UNIT

        param_types = [p.type for p in node.parameters]

        fun = Callable()  # dummy for uniformity 
        fun.signature = CallableSignature(param_types, return_type)
        self.env.define_fun(node.name, fun)

    def visit_print_stmt(self, node):
        self.visit(node.expr)

    def visit_variable_declaration(self, node):
        if node.value:
            r_type = self.visit(node.value)
            if node.type != r_type:
                raise TypeError(f'Incorrect value for variable {node.name} of type: {node.type}')
        self.env.declare_var(node.name, node.type)

    def visit_assignment(self, node):
        l_type = self.env.resolve_var(node.name, level=node.scope_depth)
        r_type = self.visit(node.value)
        if l_type != r_type:
            raise TypeError(f'Incorrect value for variable {node.name} of type: {l_type}')

    def visit_if_stmt(self, node):
        if self.visit(node.condition) != Type.BOOL:
            raise TypeError(f'Non-boolean condition in "if" statement.')
        self.visit(node.body)

    def visit_while_stmt(self, node):
        if self.visit(node.condition) != Type.BOOL:
            raise TypeError(f'Non-boolean condition in "while" statement.')

        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.env = Environment(enclosing=self.env)

        self.visit(node.initializer)
        if self.visit(node.condition) != Type.BOOL:
            raise TypeError(f'Non-boolean condition in "for" statement.')

        self.visit(node.body)

        self.env = self.env.enclosing

    def visit_binary_expr(self, node):
        l_type = self.visit(node.left)
        r_type = self.visit(node.right)
        return self.check_binary(l_type, r_type, node.op)

    def visit_unary_expr(self, node):
        e_type = self.visit(node.expr)
        return self.check_unary(e_type, node.op)

    def visit_assert_stmt(self, node):
        type = self.visit(node.expr)
        assert type == Type.BOOL

    class ReturnType(Exception):
        def __init__(self, type):
            super()
            self.type = type

    def visit_return_stmt(self, node):
        type = self.visit(node.expr)
        raise TypeCheck.ReturnType(type)

    def visit_call(self, node):
        signature = self.env.resolve_fun(node.name, level=node.scope_depth).signature
        arg_types = [self.visit(a) for a in node.args]

        return signature.verify(arg_types)

    def visit_variable(self, node):
        return self.env.resolve_var(node.name, level=node.scope_depth)

    @staticmethod
    def visit_literal(node):
        return node.type

    def visit_unknown(self, m_name):
        pass

    @staticmethod
    def check_binary(l_type, r_type, op):
        try:
            assert (l_type, r_type) in binary_signatures
            assert op in binary_signatures[(l_type, r_type)]
            return binary_signatures[(l_type, r_type)][op]
        except AssertionError:
            raise TypeError(f'Incorrect types for operator: {l_type} {r_type} {op}')

    @staticmethod
    def check_unary(e_type, op):
        try:
            assert e_type in unary_signatures
            assert op in unary_signatures[e_type]
            return unary_signatures[e_type][op]
        except AssertionError:
            raise TypeError(f'Incorrect type for operator: {e_type} {op}')

