from tc.common import BaseVisitor
from tc.globals import global_env

global_functions = global_env().functions.keys()


class Resolver(BaseVisitor):
    """For each name usage (variable/function) determines which scope it references."""

    def __init__(self):
        self.scopes = [{'variable': set(), 'function': set(global_functions)}]

    def reset(self):
        self.scopes = [{'variable': set(), 'function': set(global_functions)}]

    def push_scope(self):
        self.scopes.append({'variable': set(), 'function': set()})

    def define(self, name, what):
        self.scopes[-1][what].add(name)

    def resolve(self, name, what):
        for i in range(len(self.scopes)):
            if name in self.scopes[-(i + 1)][what]:
                return i
        raise Exception(f'Failed to resolve {what} {name}')

    def pop_scope(self):
        self.scopes.pop()

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

    def visit_block(self, node):
        self.push_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.pop_scope()

    def visit_function_def(self, node):
        self.define(node.name, 'function')

        self.push_scope()
        for p in node.parameters:
            self.define(p.name, 'variable')

        self.visit(node.body)
        self.pop_scope()

    def visit_print_stmt(self, node):
        self.visit(node.expr)

    def visit_variable_declaration(self, node):
        if node.value:
            self.visit(node.value)
        # TODO: handle repeating definitions here!
        self.define(node.name, 'variable')

    def visit_assignment(self, node):
        depth = self.resolve(node.name, 'variable')
        node.scope_depth = depth  # place scope info in the tree
        self.visit(node.value)

    def visit_if_stmt(self, node):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.push_scope()

        self.visit(node.initializer)
        self.visit(node.condition)
        self.visit(node.body)
        self.visit(node.increment)

        self.pop_scope()

    def visit_binary_expr(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_unary_expr(self, node):
        self.visit(node.expr)

    def visit_assert_stmt(self, node):
        self.visit(node.expr)

    def visit_return_stmt(self, node):
        self.visit(node.expr)

    def visit_call(self, node):
        depth = self.resolve(node.name, 'function')
        node.scope_depth = depth  # place scope info in the tree

        for a in node.args:
            self.visit(a)

    def visit_variable(self, node):
        depth = self.resolve(node.name, 'variable')
        node.scope_depth = depth  # place scope info in the tree

    @staticmethod
    def visit_literal(node):
        pass

    def visit_unknown(self, m_name):
        pass
