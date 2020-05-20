import operator
from tc.common import BaseVisitor, Environment, Function
from tc.globals import global_env
from tc.optimization import ExpressionDAGOptimizer
from tc.parser import Parser
from tc.resolver import Resolver
from tc.typecheck import TypeCheck


# TODO:
#  - skip redundant instructions (e.g. ones that do not influence function return value etc.)
#  - don't recompute common subexpressions
#  - implement algebraic optimizations of choice
#  - implement loop code shift (???) optimization
#  - fix closures (static resolution of variable scope required! ci_block example)
#    - also, one should not be able to assign closure variable (nor variable from enclosing scope)!

# AST evaluation
class Evaluator(BaseVisitor):
    """Visitor of abstract syntax tree nodes."""

    operators = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '^': operator.pow,
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '>=': operator.ge,
        '<=': operator.le,
        '<': operator.lt,
    }
    unary_operators = {
        '-': operator.neg,
    }

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
        try:
            self.env.resolve_fun(node.name, level=0)
        except:
            self.env.define_fun(node.name, Function(node.parameters, node.body, self.env))
        else:
            raise Exception(f'Function {node.name} defined twice!')

    def visit_print_stmt(self, node):
        print(self.visit(node.expr))

    def visit_variable_declaration(self, node):
        try:
            self.env.resolve_var(node.name, level=0)
        except:
            value = self.visit(node.value)
            self.env.declare_var(node.name, value)
        else:
            raise Exception(f'Variable {node.name} declared twice!')

    def visit_assignment(self, node):
        self.env.resolve_var(node.name, level=node.scope_depth)
        value = self.visit(node.value)
        self.env.define_var(node.name, value)
 
    def visit_if_stmt(self, node):
        if self.visit(node.condition):
            self.visit(node.body)

    def visit_while_stmt(self, node):
        while self.visit(node.condition):
            self.visit(node.body)
    
    def visit_for_stmt(self, node):
        self.env = Environment(enclosing=self.env)

        self.visit(node.initializer)
        while self.visit(node.condition):
            self.visit(node.body)
            self.visit(node.increment)

        self.env = self.env.enclosing

    def visit_binary_expr(self, node):
        op = self.operators[node.op]
        lval = self.visit(node.left)
        rval = self.visit(node.right)
        return op(lval, rval)

    def visit_unary_expr(self, node):
        op = self.unary_operators[node.op]
        return op(self.visit(node.expr))

    class ReturnValue(Exception):
        def __init__(self, val):
            super()
            self.val = val

    def visit_return_stmt(self, node):
        value = self.visit(node.expr)
        raise Evaluator.ReturnValue(value)

    def visit_call(self, node):
        function = self.env.resolve_fun(node.name, level=node.scope_depth)
        return function.call(self, node.args)

    def visit_variable(self, node):
        return self.env.resolve_var(node.name, level=node.scope_depth)

    @staticmethod
    def visit_literal(node):
        return node.value


class Interpreter:
    def __init__(self):
        self.dag_optimizer = ExpressionDAGOptimizer()
        self.parser = Parser()
        self.resolver = Resolver()
        self.eval = Evaluator()
        self.typecheck = TypeCheck()

    def reset(self):
        self.dag_optimizer.reset()
        self.eval.reset()
        self.typecheck.reset()
        self.resolver.reset()

    def run(self, program):
        ast = self.parser.run(program)
        self.resolver.run(ast)
        self.typecheck.run(ast)
        self.dag_optimizer.run(ast)
        self.eval.run(ast)
        self.reset()

