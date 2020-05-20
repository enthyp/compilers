from tc.common import BaseVisitor


class ExpressionDAGOptimizer(BaseVisitor):
    """Converts AST to DAG by reusing common subexpression nodes."""
    # TODO: save value of expression in node (interpreter)

    def __init__(self):
        self.subexpr = {}
        self.var_scopes = [{}]

    def reset(self):
        self.subexpr = {}
        self.var_scopes = [{}]

    def push_scope(self):
        self.var_scopes.append({})

    def pop_scope(self):
        self.var_scopes.pop()

    def resolve_var(self, name):
        for i in range(len(self.var_scopes)):
            if name in self.var_scopes[-(i + 1)]:
                return i
        raise Exception(f'Failed to resolve variable {name}')

    def var_name(self, name):
        depth = self.resolve_var(name)
        cnt = self.var_scopes[-(depth + 1)][name]
        return f'{name}_{cnt}'

    def define_var(self, name):
        try:
            depth = self.resolve_var(name)
            cnt = self.var_scopes[-(depth + 1)][name]
            self.var_scopes[-1][name] = cnt + 1
        except:
            self.var_scopes[-1][name] = 0

    def bump_var(self, name):
        depth = self.resolve_var(name)
        self.var_scopes[-(depth + 1)][name] += 1

    def define_sub(self, key, node):
        self.subexpr[key] = node

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

    def visit_block(self, node):
        self.push_scope()

        for stmt in node.statements:
            self.visit(stmt)

        self.pop_scope()

    def visit_function_def(self, node):
        self.push_scope()
        for p in node.parameters:
            self.define_var(p.name)

        self.visit(node.body)
        self.pop_scope()

    def visit_print_stmt(self, node):
        self.visit(node.expr, node, 'expr')

    def visit_variable_declaration(self, node):
        if node.value:
            self.visit(node.value, node, 'value')
        self.define_var(node.name)

    def visit_assignment(self, node):
        self.visit(node.value, node, 'value')
        self.bump_var(node.name)

    def visit_if_stmt(self, node):
        self.visit(node.condition, node, 'condition')
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.body)

    def visit_binary_expr(self, node, parent, parent_attr):
        l_key = self.visit(node.left, node, 'left')
        r_key = self.visit(node.right, node, 'right')
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
        cur_key = (key, node.op)
        if cur_key in self.subexpr:
            setattr(parent, parent_attr, self.subexpr[cur_key])
            node.caching = True
            node.cache = None
        else:
            self.subexpr[cur_key] = node
        return cur_key

    def visit_return_stmt(self, node):
        self.visit(node.expr, node, 'expr')

    def visit_call(self, node, *args):
        # Unknown side-effects - invalidate all variables.
        for scope in self.var_scopes:
            for v in scope:
                scope[v] += 1

    def visit_variable(self, node, parent, parent_attr):
        return self.var_name(node.name)

    @staticmethod
    def visit_literal(node, parent, parent_attr):
        return node.value

    def visit_unknown(self, m_name):
        pass
