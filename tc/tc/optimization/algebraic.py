from tc.common import BaseVisitor
from tc.parser import Literal


class AlgebraicOptimizer(BaseVisitor):
    """Simplifies some expressions containing neutral elements, e.g. y = x * 1; => y = x;"""

    neutral_elements = {
        '+': 0,
        '-': 0,
        '*': 1,
        '/': 1,
        '^': 1,
    }

    def run(self, statements):
        for i, stmt in enumerate(statements):
            statements[i] = self.visit(stmt)
        return statements

    def visit_block(self, node):
        for i, stmt in enumerate(node.statements):
            node.statements[i] = self.visit(stmt)
        return node

    def visit_function_def(self, node):
        node.body = self.visit(node.body)
        return node

    def visit_print_stmt(self, node):
        node.expr = self.visit(node.expr)
        return node

    def visit_variable_declaration(self, node):
        if node.value:
            node.value = self.visit(node.value)
        return node

    def visit_assignment(self, node):
        node.value = self.visit(node.value)
        return node

    def visit_if_stmt(self, node):
        node.condition = self.visit(node.condition)
        node.body = self.visit(node.body)
        return node

    def visit_while_stmt(self, node):
        node.condition = self.visit(node.condition)
        node.body = self.visit(node.body)
        return node

    def visit_for_stmt(self, node):
        node.initializer = self.visit(node.initializer)
        node.condition = self.visit(node.condition)
        node.increment = self.visit(node.increment)
        node.body = self.visit(node.body)
        return node

    def visit_binary_expr(self, node):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)

        ne = self.neutral_elements.get(node.op, None)
        if ne is not None:
            if isinstance(node.left, Literal) and node.left.value == ne:
                return node.right
            elif isinstance(node.right, Literal) and node.right.value == ne:
                return node.left

        return node

    def visit_unary_expr(self, node):
        node.expr = self.visit(node.expr)

        ne = self.neutral_elements.get(node.op, None)
        if ne and isinstance(node.expr, Literal) and node.expr.value == ne:
            return node.expr

        return node

    def visit_return_stmt(self, node):
        node.expr = self.visit(node.expr)
        return node

    def visit_call(self, node):
        for i, a in enumerate(node.args):
            node.args[i] = self.visit(a)
        return node

    @staticmethod
    def visit_variable(node):
        return node

    @staticmethod
    def visit_literal(node):
        return node

    def visit_unknown(self, m_name):
        pass
