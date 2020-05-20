from tc.common import BaseVisitor
from tc.globals import global_env
from tc.parser import Variable

global_functions = global_env().functions.keys()


class Node:
    """Node of data dependency graph where edges correspond to Use-Define relations."""
    def __init__(self, node):
        self.ast_node = node  # corresponding AST node
        self.deps = set()  # defs needed for given use (Use-Define relationship)
        self.kills = set()  # set of (name, redefinition node that kills previous definition of name)


class RedundancyOptimizer(BaseVisitor):
    """Statically builds a use-def graph and removes redundant subtrees of input AST."""

    BUILD = 0
    PRUNE = 1

    def __init__(self):
        self.mode = RedundancyOptimizer.BUILD
        self.effective_nodes = set()
        self.scopes = [{
            'variable': {},
            'function': {f: Node(None) for f in global_functions}
        }]

    def reset(self):
        self.mode = self.BUILD
        self.effective_nodes = set()
        self.scopes = [{
            'variable': {},
            'function': {f: Node(None) for f in global_functions}
        }]

    def push_scope(self):
        self.scopes.append({'variable': {}, 'function': {}})

    def define(self, name, node, what):
        self.scopes[-1][what][name] = node

    def resolve(self, name, what):
        for i in range(len(self.scopes)):
            if name in self.scopes[-(i + 1)][what]:
                return self.scopes[-(i + 1)][what][name]
        raise Exception(f'Failed to resolve {what} {name}')

    def pop_scope(self):
        self.scopes.pop()

    def kill(self, kills):
        for name, node in kills:
            self.scopes[-1]['variable'][name] = node

    def run(self, statements):
        if self.mode == self.BUILD:
            # Build the dependency graph and find effective nodes
            for stmt in statements:
                self.visit(stmt)

            self.effective_nodes = self.extend_effective()

            # Prune redundant subtrees.
            self.mode = self.PRUNE
            effective_statements = [s for s in statements if s in self.effective_nodes]
            for stmt in effective_statements:
                self.visit(stmt)

            return effective_statements

    def extend_effective(self):
        def extend_inner(node):
            effective_ast_nodes.add(node.ast_node)
            for d in node.deps:
                if d.ast_node not in effective_ast_nodes:  # not a DAG - e.g. while loops
                    extend_inner(d)

        effective_ast_nodes = set()
        for node in self.effective_nodes:
            extend_inner(node)
        return effective_ast_nodes

    def visit_block(self, node):
        if self.mode == self.PRUNE:
            remaining_statements = []
            for stmt in node.statements:
                if stmt in self.effective_nodes:
                    remaining_statements.append(stmt)
                    self.visit(stmt)
            node.statements = remaining_statements
            return

        b_node = Node(node)

        self.push_scope()
        try:
            for stmt in node.statements:
                n = self.visit(stmt)
                n.deps.add(b_node)
                b_node.kills.update(n.kills)
        except RedundancyOptimizer.Return as r:
            b_node.deps.add(r.node)
        self.pop_scope()

        return b_node

    def visit_function_def(self, node):
        if self.mode == self.PRUNE:
            self.visit(node.body)
            return

        f_node = Node(node)

        self.push_scope()
        for p in node.parameters:
            n = Node(node)
            self.define(p.name, n, 'variable')

        b_node = self.visit(node.body)
        self.pop_scope()

        f_node.deps = b_node.deps
        f_node.kills = b_node.kills
        self.define(node.name, f_node, 'function')

        return f_node

    def visit_print_stmt(self, node):
        if self.mode == self.PRUNE:
            return

        p_node = Node(node)
        self.effective_nodes.add(p_node)
        n = self.visit(node.expr)

        p_node.deps.add(n)
        self.kill(n.kills)
        return p_node

    def visit_variable_declaration(self, node):
        if self.mode == self.PRUNE:
            return

        v_node = Node(node)

        if node.value:
            n = self.visit(node.value)
            v_node.deps.add(n)
            v_node.kills.update(n.kills)
            v_node.kills.add((node.name, v_node))
            self.kill(n.kills)

        self.define(node.name, v_node, 'variable')
        return v_node

    def visit_assignment(self, node):
        if self.mode == self.PRUNE:
            return

        a_node = Node(node)
        n = self.visit(node.value)

        a_node.deps.add(n)
        a_node.kills.add((node.name, a_node))
        self.define(node.name, a_node, 'variable')

        return a_node

    def visit_if_stmt(self, node):
        if self.mode == self.PRUNE:
            self.visit(node.body)
            return

        i_node = Node(node)
        c_node = self.visit(node.condition)
        i_node.deps.add(c_node)

        b_node = self.visit(node.body)
        b_node.deps.add(i_node)
        i_node.kills.update(b_node.kills)

        return i_node

    def visit_while_stmt(self, node):
        if self.mode == self.PRUNE:
            self.visit(node.body)
            return

        w_node = Node(node)
        c_node = self.visit(node.condition)
        w_node.deps.add(c_node)

        b_node = self.visit(node.body)
        b_node.deps.add(w_node)

        w_node.kills.update(b_node.kills)

        # Variables in loop condition depend on redefinitions in loop body!
        # TODO: separation of data dependencies from AST structure would do better?
        cond_deps = set()
        for n in c_node.deps:
            if isinstance(n.ast_node, Variable):
                cond_deps.add(n.ast_node.name)
        print(cond_deps)
        print(b_node.kills)
        for name, node in b_node.kills:
            if name in cond_deps:
                c_node.deps.add(node)

        return w_node

    def visit_for_stmt(self, node):
        if self.mode == self.PRUNE:
            self.visit(node.body)
            return

        f_node = Node(node)
        self.push_scope()

        b_node = self.visit(node.body)
        b_node.deps.add(f_node)
        f_node.deps.update({
            self.visit(node.initializer),
            self.visit(node.condition),
            self.visit(node.increment),
        })

        self.pop_scope()
        return f_node

    def visit_binary_expr(self, node):
        if self.mode == self.PRUNE:
            return

        b_node = Node(node)
        l_node = self.visit(node.left)
        r_node = self.visit(node.right)

        b_node.deps.update({l_node, r_node})
        b_node.kills.update(l_node.kills | r_node.kills)
        return b_node

    def visit_unary_expr(self, node):
        if self.mode == self.PRUNE:
            return

        u_node = Node(node)
        e_node = self.visit(node.expr)

        u_node.deps.add(e_node)
        u_node.kills.update(e_node.kills)
        return u_node

    class Return(Exception):
        def __init__(self, return_node):
            super()
            self.node = return_node

    def visit_return_stmt(self, node):
        if self.mode == self.PRUNE:
            return

        r_node = Node(node)
        e_node = self.visit(node.expr)
        r_node.deps.add(e_node)
        r_node.kills.update(e_node.kills)
        raise RedundancyOptimizer.Return(r_node)

    def visit_call(self, node):
        if self.mode == self.PRUNE:
            return

        c_node = Node(node)

        for a in node.args:
            n = self.visit(a)
            c_node.deps.add(n)
            self.kill(n.kills)

        f_node = self.resolve(node.name, 'function')
        c_node.deps.add(f_node)
        self.kill(f_node.kills)

        return c_node

    def visit_variable(self, node):
        if self.mode == self.PRUNE:
            return

        v_node = Node(node)
        value_node = self.resolve(node.name, 'variable')
        v_node.deps.add(value_node)
        return v_node

    def visit_literal(self, node):
        if self.mode == self.PRUNE:
            return

        return Node(node)

    def visit_unknown(self, m_name):
        pass
