from tc.common import BaseVisitor


class ExpressionDAGOptimizer(BaseVisitor):
    """Converts AST to DAG by reusing common subexpression nodes."""

    def __init__(self, in_sets):
        self.in_sets = in_sets
        self.subexpr = {}

    def define_sub(self, key, node):
        self.subexpr[key] = node

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)
        return statements

    def visit_block(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_function_def(self, node):
        self.visit(node.body)

    def visit_print_stmt(self, node):
        self.visit(node.expr, node, 'expr')

    def visit_variable_declaration(self, node):
        if node.value:
            self.visit(node.value, node, 'value')

    def visit_assignment(self, node):
        self.visit(node.value, node, 'value')

    def visit_if_stmt(self, node):
        self.visit(node.condition, node, 'condition')
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.condition, node, 'condition')
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.condition, node, 'condition')
        self.visit(node.increment)
        self.visit(node.body)

    def visit_binary_expr(self, node, parent, parent_attr):
        l_key = self.visit(node.left, node, 'left')
        r_key = self.visit(node.right, node, 'right')
        if not (l_key and r_key):
            return None

        cur_key = (l_key, r_key, node.op)

        if cur_key in self.subexpr:
            setattr(parent, parent_attr, self.subexpr[cur_key])
            node.caching = True
            node.cache = None
        else:
            self.subexpr[cur_key] = node
        return cur_key

    def visit_unary_expr(self, node, parent, parent_attr):
        key = self.visit(node.expr, node, 'expr')
        if not key:
            return None

        cur_key = (key, node.op)
        if cur_key in self.subexpr:
            setattr(parent, parent_attr, self.subexpr[cur_key])
            node.caching = True
            node.cache = None
        else:
            self.subexpr[cur_key] = node
        return cur_key

    def visit_assert_stmt(self, node):
        self.visit(node.expr, node, 'expr')

    def visit_return_stmt(self, node):
        self.visit(node.expr, node, 'expr')

    def visit_call(self, *args):
        # Unknown side-effects - prevent optimization
        return None

    def visit_variable(self, node, *args):
        in_set = self.in_sets[node]
        if len(in_set) == 1:
            reach_def = next(iter(in_set))
            import logging
            logging.warning('IN')
            return id(reach_def)  # dumb hashing
        else:
            # More reaching definitions - can't reliably share variables in expressions
            # e.g. loops etc.
            return None

    @staticmethod
    def visit_literal(node, parent, parent_attr):
        return node.value

    def visit_unknown(self, m_name):
        pass
