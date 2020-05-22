from contextlib import contextmanager
from tc.common import BaseVisitor
from tc.optimization.common import GenKillBuilder, InOutBuilder


# HOW TO:
#  - find functions with side effects:
#    - ones that contain 'print' statements
#    - ones that call functions with side effects
#  - for these functions find return nodes and effective statements (link to functions)
#    - at the same time you can find top-level effective statements
#  - for all top-level effective statements follow Use-Define chains to gather all effective nodes
class EffectiveNodeSearch(BaseVisitor):
    """Finds nodes necessary to trigger all side effects."""

    def __init__(self, in_sets, out_sets):
        self.in_sets = in_sets
        self.out_sets = out_sets

        # TODO: could be split into two visitors (yeah, dozens of visitors)
        self.follow = False  # follow Use-Definition chains
        self.effective_nodes = set()
        self.effective_fun_def_nodes = {}
        self.scopes = [{}]
        self.fun_def_scopes = []

    def reset(self):
        self.follow = False
        self.effective_nodes = set()
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
    def in_fun_def(self, name):
        try:
            self.scopes[-1][name] = {'is_effective': False, 'effective_nodes': set()}
            self.fun_def_scopes.append(name)
            yield
        finally:
            self.fun_def_scopes.pop()

    def define_fun(self, name):
        self.scopes[-1][name] = False

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

        self.follow = True
        for stmt in statements:
            if stmt in self.effective_nodes:
                self.visit(stmt)

        return self.effective_nodes

    def visit_block(self, node):
        with self.in_scope():
            for stmt in node.statements:
                self.visit(stmt)
                if stmt in self.effective_nodes:
                    self.effective_nodes.add(node)

    def visit_function_def(self, node):
        with self.in_fun_def(node.name):
            self.visit(node.body)

    def visit_print_stmt(self, node):
        self.visit(node.expr)

        if self.follow:
            return

        if self.fun_def_scopes:
            cur_function = self.fun_def_scopes[-1]
            info = self.get_fun_info(cur_function)
            info['is_effective'] = True
            info['effective_nodes'].add(node)
        else:
            # Top level print - an effective statement
            self.effective_nodes.add(node)

    def visit_variable_declaration(self, node):
        if self.follow:
            self.effective_nodes.add(node)
            self.visit(node.value)
            return

        if node.value:
            self.visit(node.value)

            if self.fun_def_scopes:
                return

            if node.value in self.effective_nodes:
                self.effective_nodes.add(node)

    def visit_assignment(self, node):
        if self.follow:
            self.effective_nodes.add(node)
            self.visit(node.value)
            return

        self.visit(node.value)

        if self.fun_def_scopes:
            return

        if node.value in self.effective_nodes:
            self.effective_nodes.add(node)

    def visit_if_stmt(self, node):
        if self.follow:
            self.visit(node.condition)
            self.visit(node.body)
            return

        self.visit(node.condition)
        self.visit(node.body)

        if self.fun_def_scopes:
            return

        if node.condition in self.effective_nodes or node.body in self.effective_nodes:
            self.effective_nodes.add(node)

    def visit_while_stmt(self, node):
        if self.follow:
            self.visit(node.condition)
            self.visit(node.body)
            return

        self.visit(node.condition)
        self.visit(node.body)

        if self.fun_def_scopes:
            return

        if node.condition in self.effective_nodes or node.body in self.effective_nodes:
            self.effective_nodes.add(node)

    def visit_for_stmt(self, node):
        if self.follow:
            self.visit(node.initializer)
            self.visit(node.condition)
            self.visit(node.body)
            self.visit(node.increment)
            return

        self.visit(node.initializer)
        self.visit(node.condition)
        self.visit(node.body)
        self.visit(node.increment)

        if self.fun_def_scopes:
            return

        if (
            node.initializer in self.effective_nodes or
            node.body in self.effective_nodes or
            node.condition in self.effective_nodes or
            node.increment in self.effective_nodes
        ):
            self.effective_nodes.add(node)

    def visit_binary_expr(self, node):
        if self.follow:
            self.effective_nodes.add(node)
            self.visit(node.left)
            self.visit(node.right)
            return

        self.visit(node.left)
        self.visit(node.right)

        if self.fun_def_scopes:
            return

        if node.left in self.effective_nodes or node.right in self.effective_nodes:
            self.effective_nodes.add(node)

    def visit_unary_expr(self, node):
        if self.follow:
            self.effective_nodes.add(node)
            self.visit(node.expr)
            return

        self.visit(node.expr)

        if self.fun_def_scopes:
            return

        if node.expr in self.effective_nodes:
            self.effective_nodes.add(node)

    def visit_return_stmt(self, node):
        if self.follow:
            self.effective_nodes.add(node)
            self.visit(node.expr)
            return

        if self.fun_def_scopes:
            self.visit(node.expr)
            cur_function = self.fun_def_scopes[-1]
            info = self.get_fun_info(cur_function)
            info['effective_nodes'].add(node)
        else:
            raise Exception('Return statement outside of funtion!')

    def visit_call(self, node):
        if self.follow:
            self.effective_nodes.add(node)

            for a in node.args:
                self.visit(a)

            # Enter function body in effective node points.
            effective_nodes = self.effective_fun_def_nodes[node]
            for node in effective_nodes:
                self.visit(node)

            return

        for a in node.args:
            self.visit(a)

        info = self.get_fun_info(node.name)
        self.effective_fun_def_nodes[node] = info['effective_nodes']

        if info['is_effective']:
            if self.fun_def_scopes:
                cur_function = self.fun_def_scopes[-1]
                info = self.get_fun_info(cur_function)
                info['is_effective'] = True
                info['effective_nodes'].add(node)
            else:
                self.effective_nodes.add(node)
                # TODO: add function def node to effective

    def visit_variable(self, node):
        if self.follow:
            if node in self.effective_nodes:
                return

            self.effective_nodes.add(node)

            in_set = self.in_sets[node]
            for n in in_set:
                if n.name == node.name:
                    self.visit(n)

    def visit_unknown(self, m_name):
        pass


class RedundancyOptimizer(BaseVisitor):
    """Removes all subtrees of input AST that do not contain effective nodes."""

    def run(self, statements):
        # Build IN and OUT sets
        gen, kill = GenKillBuilder().run(statements)
        in_sets, out_sets = InOutBuilder(gen, kill).run(statements)

        # Find all effective nodes of the AST
        effective_nodes = EffectiveNodeSearch(in_sets, out_sets).run(statements)

        # Prune redundant nodes
        for node in effective_nodes:
            self.visit_statements(node)

        return statements

    def visit_statements(self, statements):
        gen, kill = set(), set()

        self.visit(statements[0])
        gen |= self.gen[statements[0]]
        kill |= self.kill[statements[0]]

        for i, stmt in enumerate(statements[1:]):
            self.visit(stmt)
            gen -= self.kill[stmt]
            gen |= self.gen[stmt]

            kill -= self.gen[stmt]  # NOTE: is it even used?
            kill |= self.kill[stmt]

        return gen, kill

    def visit_block(self, node):
        with self.in_scope():
            gen, _ = self.visit_statements(node.statements)
            self.gen[node] = gen
            self.kill[node] = set()

    def visit_function_def(self, node):
        self.visit(node.body)
        self.gen[node] = set()
        self.kill[node] = set()

        p_names = {param.name for param in node.parameters}
        gen = {node for node in self.gen[node.body] if node.name not in p_names}
        kill = {node for node in self.kill[node.body] if node.name not in p_names}

        self.scopes[-1][node.name] = (gen, kill)  # GEN and KILL for function calls

    def visit_variable_declaration(self, node):
        if node.value:
            self.visit_assignment(node)
        else:
            self.gen[node] = {node}
            self.kill[node] = self.var_defs[node.name] - {node}

    def visit_assignment(self, node):
        self.visit(node.value)
        self.gen[node] = {node} | (self.gen[node.value] - self.var_defs[node.name])
        self.kill[node] = (self.var_defs[node.name] | self.kill[node.value]) - {node}

    def carry(self, node, source_node):
        self.visit(source_node)
        self.gen[node] = self.gen[source_node]
        self.kill[node] = self.kill[source_node]

    def visit_print_stmt(self, node):
        self.carry(node, node.expr)

    def visit_if_stmt(self, node):
        stmt_list = [node.condition, node.body]
        gen, kill = self.visit_statements(stmt_list)

        self.gen[node] = gen
        self.kill[node] = kill

    def visit_while_stmt(self, node):
        self.visit(node.condition)
        self.visit(node.body)

        self.gen[node] = self.gen[node.condition] | self.gen[node.body]
        self.kill[node] = self.kill[node.condition] & self.kill[node.body]

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.condition)
        self.visit(node.increment)
        self.visit(node.body)

        gen = self.gen[node.initializer] - self.kill[node.condition]
        gen |= self.gen[node.body] | self.gen[node.increment]

        kill = self.kill[node.initializer] - (
            self.gen[node.condition] | self.gen[node.body] | self.gen[node.increment]
        )

        self.gen[node] = gen
        self.kill[node] = kill

    def visit_binary_expr(self, node):
        stmt_list = [node.left, node.right]
        gen, kill = self.visit_statements(stmt_list)

        self.gen[node] = gen
        self.kill[node] = kill

    def visit_unary_expr(self, node):
        self.carry(node, node.expr)

    def visit_return_stmt(self, node):
        self.carry(node, node.expr)

    def visit_call(self, node):
        gen, kill = self.visit_statements(node.args)
        f_gen, f_kill = self.resolve(node.name)
        self.gen[node] = f_gen | (gen - f_kill)
        self.kill[node] = f_kill | (kill - f_gen)

    def visit_variable(self, node):
        self.gen[node] = set()
        self.kill[node] = set()

    def visit_literal(self, node):
        self.gen[node] = set()
        self.kill[node] = set()

    def visit_unknown(self, m_name):
        pass
