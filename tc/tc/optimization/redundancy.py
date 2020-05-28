from contextlib import contextmanager
from tc.common import BaseVisitor
from tc.optimization.common import GenKillBuilder, InOutBuilder
from tc.globals import global_env

global_functions = global_env().functions.keys()


class FindEffectiveStatements(BaseVisitor):
    """Finds top-level statements necessary to trigger all side effects."""

    def __init__(self):
        self.eff_statements = set()
        self.call_fun_info = {}
        self.scopes = [{f: {'follow_nodes': set(), 'is_effective': False} for f in global_functions}]
        self.fun_def_scopes = []

    def reset(self):
        self.eff_statements = set()
        self.call_fun_info = {}
        self.scopes = [{f: {'follow_nodes': set(), 'is_effective': False} for f in global_functions}]
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
            info = {
                'follow_nodes': {node},
                'is_effective': False,
            }
            self.scopes[-1][node.name] = info
            self.fun_def_scopes.append(info)
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
            info = self.fun_def_scopes[-1]
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

    def visit_assert_stmt(self, node):
        self.visit(node.expr)

    def visit_return_stmt(self, node):
        if self.fun_def_scopes:
            self.visit(node.expr)
            info = self.fun_def_scopes[-1]
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
                info = self.fun_def_scopes[-1]
                info['is_effective'] = True
            else:
                self.eff_statements.add(node)

    def visit_unknown(self, m_name):
        pass


class FollowUseDef(BaseVisitor):
    """Find variable and function definitions necessary for top-level effective statements."""
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
            self.effective_nodes.add(node)
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

    def visit_assert_stmt(self, node):
        if self.follows:
            self.effective_nodes.add(node)
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


class ExtendEffective(BaseVisitor):
    """Mark as effective by following AST structure from top-level effective statements.

    This is purely syntax based, does not consider semantic issues like: variables from loop
    condition may not be referenced by effective statements but still must be declared for
    loop to work etc. For such cases we need additional processing (below).

    """

    def __init__(self, effective_nodes):
        self.effective_nodes = effective_nodes

    def run(self, statements):
        self.visit_statements(statements)

    def visit_statements(self, statements):
        are_effective = False
        for stmt in statements:
            if self.visit(stmt):
                self.effective_nodes.add(stmt)
                are_effective = True
        return are_effective

    def visit_block(self, node):
        if self.visit_statements(node.statements):
            self.effective_nodes.add(node)
            return True
        return False

    def visit_function_def(self, node):
        if node in self.effective_nodes:
            for p in node.parameters:
                self.effective_nodes.add(p)
            self.effective_nodes.add(node.body)
            self.visit(node.body)
            return True
        return False

    def visit_variable_declaration(self, node):
        if node in self.effective_nodes:
            if node.value:
                self.effective_nodes.add(node.value)
                self.visit(node.value)
            return True
        return False

    def visit_assignment(self, node):
        if node in self.effective_nodes:
            self.effective_nodes.add(node.value)
            self.visit(node.value)
            return True
        return False

    def visit_print_stmt(self, node):
        if node in self.effective_nodes:
            self.effective_nodes.add(node.expr)
            self.visit(node.expr)
            return True
        return False

    def visit_if_stmt(self, node):
        cond_effective = self.visit(node.condition)
        body_effective = self.visit(node.body)
        if cond_effective or body_effective:
            self.effective_nodes.add(node)
            return True
        return False

    def visit_while_stmt(self, node):
        cond_effective = self.visit(node.condition)
        body_effective = self.visit(node.body)
        if cond_effective or body_effective:
            self.effective_nodes.add(node)
            return True
        return False

    def visit_for_stmt(self, node):
        init_effective = self.visit(node.initializer)
        cond_effective = self.visit(node.condition)
        body_effective = self.visit(node.body)
        inc_effective = self.visit(node.increment)
        if init_effective or cond_effective or body_effective or inc_effective:
            self.effective_nodes.add(node)
            return True
        return False

    def visit_binary_expr(self, node):
        l_effective = self.visit(node.left)
        r_effective = self.visit(node.right)
        if l_effective or r_effective:
            self.effective_nodes.add(node)
            return True
        return False

    def visit_unary_expr(self, node):
        if self.visit(node.expr):
            self.effective_nodes.add(node)
            return True
        return False

    def visit_assert_stmt(self, node):
        if node in self.effective_nodes:
            self.effective_nodes.add(node.expr)
            self.visit(node.expr)
            return True
        return False

    def visit_return_stmt(self, node):
        if node in self.effective_nodes:
            self.effective_nodes.add(node.expr)
            self.visit(node.expr)
            return True
        return False

    def visit_call(self, node):
        if node in self.effective_nodes:
            for a in node.args:
                self.effective_nodes.add(a)
                self.visit(a)
            return True
        return False

    def visit_unknown(self, m_name):
        return True


class FollowConditions(BaseVisitor):
    """For effective conditional blocks marks all definitions of condition variables as effective."""

    def __init__(self, in_sets, effective_nodes):
        self.in_sets = in_sets
        self.effective_nodes = effective_nodes

    def run(self, statements):
        self.visit_statements(statements)

    def visit_statements(self, statements):
        for stmt in statements:
            self.visit(stmt)

    def visit_block(self, node):
        self.visit_statements(node.statements)

    def visit_function_def(self, node):
        self.visit(node.body)

    def visit_if_stmt(self, node):
        if node in self.effective_nodes:
            definitions = self.visit(node.condition)
            for d in definitions:
                self.effective_nodes.add(d)

    def visit_while_stmt(self, node):
        if node in self.effective_nodes:
            definitions = self.visit(node.condition)
            for d in definitions:
                self.effective_nodes.add(d)

    def visit_for_stmt(self, node):
        if node in self.effective_nodes:
            definitions = self.visit(node.condition)
            for d in definitions:
                self.effective_nodes.add(d)

    def visit_binary_expr(self, node):
        return self.visit(node.left) | self.visit(node.right)

    def visit_unary_expr(self, node):
        return self.visit(node.expr)

    def visit_call(self, node):
        arg_defs = [self.visit(a) for a in node.args]
        return set().union(*arg_defs)

    def visit_variable(self, node):
        defs = self.in_sets[node]
        return {d for d in defs if d.name == node.name}

    def visit_unknown(self, m_name):
        return set()


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
        effective_top_level, call_fun_info = FindEffectiveStatements().run(statements)
        self.effective_nodes = FollowUseDef(in_sets, effective_top_level, call_fun_info).run(statements)

        ExtendEffective(self.effective_nodes).run(statements)
        FollowConditions(in_sets, self.effective_nodes).run(statements)

        # Prune redundant nodes
        return self.visit_statements(statements)

    def visit_statements(self, statements):
        new_statements = []
        for stmt in statements:
            if stmt in self.effective_nodes:
                new_statements.append(stmt)
                self.visit(stmt)

        return new_statements

    def visit_block(self, node):
        node.statements = self.visit_statements(node.statements)

    def visit_function_def(self, node):
        self.visit(node.body)

    def visit_if_stmt(self, node):
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.body)
        self.visit(node.increment)

    def visit_unknown(self, m_name):
        pass
