from contextlib import contextmanager
from tc.common import BaseVisitor
from tc.optimization.common import GenKillBuilder, InOutBuilder


class EffectiveStatementSearch(BaseVisitor):
    """Finds top-level statements necessary to trigger all side effects."""

    def __init__(self):
        self.eff_statements = set()
        self.call_fun_info = {}
        self.scopes = [{}]
        self.fun_def_scopes = []

    def reset(self):
        self.eff_statements = set()
        self.call_fun_info = {}
        self.scopes = [{}]
        self.fun_def_scopes = []

    @contextmanager
    def in_scope(self):
        try:
            self.scopes.append({})
            yield
        finally:
            self.scopes.pop()

    @contextmanager
    def in_fun_def(self, node):
        try:
            self.scopes[-1][node.name] = {
                'follow_nodes': {node},
                'is_effective': False,
            }
            self.fun_def_scopes.append(node.name)
            yield
        finally:
            self.fun_def_scopes.pop()

    def resolve_fun(self, name):
        for i in range(len(self.scopes)):
            if name in self.scopes[-(i + 1)]:
                return i
        raise Exception(f'Failed to resolve function {name}')

    def get_fun_info(self, name):
        depth = self.resolve_fun(name)
        return self.scopes[-(depth + 1)][name]

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

        return self.eff_statements, self.call_fun_info

    def visit_block(self, node):
        with self.in_scope():
            for stmt in node.statements:
                self.visit(stmt)

    def visit_function_def(self, node):
        with self.in_fun_def(node):
            self.visit(node.body)

    def visit_print_stmt(self, node):
        self.visit(node.expr)

        if self.fun_def_scopes:
            cur_function = self.fun_def_scopes[-1]
            info = self.get_fun_info(cur_function)
            info['is_effective'] = True
            info['follow_nodes'].add(node)
        else:
            # Top level print - an effective statement
            self.eff_statements.add(node)

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
        self.visit(node.body)
        self.visit(node.increment)

    def visit_binary_expr(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_unary_expr(self, node):
        self.visit(node.expr)

    def visit_return_stmt(self, node):
        if self.fun_def_scopes:
            self.visit(node.expr)
            cur_function = self.fun_def_scopes[-1]
            info = self.get_fun_info(cur_function)
            info['follow_nodes'].add(node)
        else:
            raise Exception('Return statement outside of function!')

    def visit_call(self, node):
        for a in node.args:
            self.visit(a)

        info = self.get_fun_info(node.name)
        self.call_fun_info[node] = info
        effective_body = info['is_effective']
        effective_args = any(a in self.eff_statements for a in node.args)

        if effective_body or effective_args:
            if self.fun_def_scopes:
                cur_function = self.fun_def_scopes[-1]
                info = self.get_fun_info(cur_function)
                info['is_effective'] = True
                info['follow_nodes'].add(node)
            else:
                self.eff_statements.add(node)

    def visit_unknown(self, m_name):
        pass


class UseDefFollower(BaseVisitor):
    """Find variable assignments and declarations necessary for top-level effective statements."""
    def __init__(self, in_sets, effective_nodes, call_fun_info):
        self.in_sets = in_sets
        self.effective_nodes = effective_nodes
        self.call_fun_info = call_fun_info

        self.follow_cnt = 0  # follow a Use-Definition chain
        self.followed = set()

    @contextmanager
    def following(self):
        try:
            self.follow_cnt += 1
            yield
        finally:
            self.follow_cnt -= 1

    @property
    def follows(self):
        return self.follow_cnt != 0

    def reset(self):
        self.followed = set()

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

        return self.effective_nodes

    def visit_block(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_function_def(self, node):
        if self.follows:
            self.effective_nodes.add(node)

    def visit_print_stmt(self, node):
        if node in self.effective_nodes or self.follows:
            with self.following():
                self.visit(node.expr)

    def visit_variable_declaration(self, node):
        if node.value:
            self.visit(node.value)

        if self.follows:
            self.effective_nodes.add(node)

    def visit_assignment(self, node):
        self.visit(node.value)

        if self.follows:
            self.effective_nodes.add(node)

    def visit_if_stmt(self, node):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.condition)
        self.visit(node.body)
        self.visit(node.increment)

    def visit_binary_expr(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_unary_expr(self, node):
        self.visit(node.expr)

    def visit_return_stmt(self, node):
        if self.follows:
            self.effective_nodes.add(node)
        self.visit(node.expr)

    def visit_call(self, node):
        if self.follows or node in self.effective_nodes:
            for a in node.args:
                self.visit(a)

            # Enter function body in effective node points
            info = self.call_fun_info[node]

            with self.following():
                for node in info['follow_nodes']:
                    self.visit(node)

    def visit_variable(self, node):
        if self.follows:
            if node in self.followed:
                return
            else:
                self.followed.add(node)

            with self.following():
                in_set = self.in_sets[node]
                for n in in_set:
                    if n.name == node.name:
                        self.visit(n)

    def visit_unknown(self, m_name):
        pass


class RedundancyOptimizer(BaseVisitor):
    """Removes all subtrees of input AST that do not contain effective nodes."""

    def __init__(self):
        self.effective_nodes = None

    def reset(self):
        self.effective_nodes = None

    def run(self, statements):
        # Build IN and OUT sets
        gen, kill = GenKillBuilder().run(statements)
        in_sets, out_sets = InOutBuilder(gen, kill).run(statements)

        # Find all effective nodes of the AST
        effective_top_level, call_fun_info = EffectiveStatementSearch().run(statements)
        follower = UseDefFollower(in_sets, effective_top_level, call_fun_info)
        self.effective_nodes = follower.run(statements)

        # Prune redundant nodes
        return self.visit_statements(statements)

    def visit_statements(self, statements):
        new_statements = []
        for stmt in statements:
            if self.visit(stmt):
                new_statements.append(stmt)

        return new_statements

    def visit_block(self, node):
        statements = self.visit_statements(node.statements)
        if statements:
            node.statements = statements
            return True
        else:
            return False

    def visit_function_def(self, node):
        return self.visit(node.body)

    def visit_variable_declaration(self, node):
        if node in self.effective_nodes:
            return True
        elif node.value:
            return self.visit(node.value)
        else:
            return False

    def visit_assignment(self, node):
        if node in self.effective_nodes:
            return True
        else:
            return self.visit(node.value)

    def visit_print_stmt(self, node):
        return node in self.effective_nodes

    def visit_if_stmt(self, node):
        cond_effective = self.visit(node.condition)
        body_effective = self.visit(node.body)
        return cond_effective or body_effective

    def visit_while_stmt(self, node):
        cond_effective = self.visit(node.condition)
        body_effective = self.visit(node.body)
        return cond_effective or body_effective

    def visit_for_stmt(self, node):
        init_effective = self.visit(node.initializer)
        cond_effective = self.visit(node.condition)
        inc_effective = self.visit(node.increment)
        body_effective = self.visit(node.body)

        return init_effective or cond_effective or body_effective or inc_effective

    def visit_binary_expr(self, node):
        return self.visit(node.left) or self.visit(node.right)

    def visit_unary_expr(self, node):
        return self.visit(node.expr)

    def visit_return_stmt(self, node):
        return node in self.effective_nodes

    def visit_call(self, node):
        return node in self.effective_nodes or any(a in self.effective_nodes for a in node.args)

    def visit_unknown(self, m_name):
        return True
