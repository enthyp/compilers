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
        self.visit(node.expr)

    def visit_variable_declaration(self, node):
        if node.value:
            self.visit(node.value)

    def visit_assignment(self, node):
        self.visit(node.value)

    def visit_if_stmt(self, node):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.condition)
        self.visit(node.increment)
        self.visit(node.body)

    def visit_binary_expr(self, node):
        l_key = self.visit(node.left)
        r_key = self.visit(node.right)
        if l_key is None or r_key is None:
            return None

        cur_key = (l_key, r_key, node.op)

        if cur_key in self.subexpr:
            common_node = self.subexpr[cur_key]
            node.common_node = common_node
            node.left = node.right = None  # prune
        else:
            self.subexpr[cur_key] = node
            # Mark node that shall compute the cache value - for evaluation
            node.cache = None
        return cur_key

    def visit_unary_expr(self, node):
        key = self.visit(node.expr)
        if key is None:
            return None

        cur_key = (key, node.op)
        if cur_key in self.subexpr:
            common_node = self.subexpr[cur_key]
            node.common_node = common_node
            node.expr = None  # prune
        else:
            self.subexpr[cur_key] = node
            # Mark node that shall compute the cache value - for evaluation
            node.cache = None
        return cur_key

    def visit_assert_stmt(self, node):
        self.visit(node.expr)

    def visit_return_stmt(self, node):
        self.visit(node.expr)

    def visit_call(self):
        # Unknown side-effects - prevent optimization
        return None

    def visit_variable(self, node):
        in_set = self.in_sets[node]
        reach_defs = {reach_def for reach_def in in_set if reach_def.name == node.name}

        if len(reach_defs) == 1:
            reach_def = next(iter(reach_defs))
            return id(reach_def)  # dumb hashing
        else:
            # More reaching definitions - can't reliably share variables in expressions
            # e.g. loops etc.
            return None

    @staticmethod
    def visit_literal(node):
        return node.value

    def visit_unknown(self, m_name):
        pass
