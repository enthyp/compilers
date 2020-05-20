from tc.common import BaseVisitor
from tc.globals import global_env
from tc.parser import Block

global_functions = global_env().functions.keys()


class Node:
    """Node of data dependency DAG."""
    def __init__(self, node):
        self.ast_node = node  # corresponding AST node
        self.deps = set()  # defs needed for given use (Use-Def relationship)
        self.kills = set()  # set of (name, redefinition node that kills previous definition of name)


# HOW TO:
#  - e.g. for function (def) we have:
#    - map: name -> assignment node (all redefinitions to be accounted for upon call)
#    - a dependency on the return node
#  - for a 'while' loop block:
#    - map: name -> assignment node (all redefinitions to be accounted for when executing)
class RedundancyOptimizer(BaseVisitor):
    """Builds (statically) a data dependency DAG and removes redundant subtrees of input AST.

    Attributes:
        effective_nodes (set): nodes that have side effects, e.g. 'return', 'print' and the like.
            In the end only the result of their execution matters, any data processing that does
            not contribute to an effective node is redundant
        scopes (list): stack of mappings (scopes) from function/variable name to the defining AST
            node AND all redefinitions to be accounted for
    """

    def __init__(self):
        self.effective_nodes = set()
        self.scopes = [{
            'variable': {},
            'function': {f: Node(None) for f in global_functions}
        }]

    def reset(self):
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
        # Build the dependency graph and find effective nodes
        for stmt in statements:
            self.visit(stmt)

        # Prune ineffective nodes
        effective = self.extend_effective()

        effective_statements = [s for s in statements if s in effective]
        for stmt in effective_statements:
            self.prune(stmt, effective)

        return effective_statements

    def extend_effective(self):
        def extend_inner(node):
            effective_ast_nodes.add(node.ast_node)
            for d in node.deps:
                extend_inner(d)

        effective_ast_nodes = set()
        for node in self.effective_nodes:
            extend_inner(node)
        return effective_ast_nodes

    @staticmethod
    def prune(node, effective):
        if not isinstance(node, Block):
            return

        remaining_statements = []
        for stmt in node.statements:
            if stmt in effective:
                remaining_statements.append(stmt)
        node.statements = remaining_statements

    def visit_block(self, node):
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
        p_node = Node(node)
        self.effective_nodes.add(p_node)
        n = self.visit(node.expr)

        p_node.deps.add(n)
        self.kill(n.kills)
        return p_node

    def visit_variable_declaration(self, node):
        v_node = Node(node)

        if node.value:
            n = self.visit(node.value)
            v_node.deps.add(n)
            self.kill(n.kills)

        self.define(node.name, v_node, 'variable')
        return v_node

    def visit_assignment(self, node):
        a_node = Node(node)
        n = self.visit(node.value)

        a_node.deps.add(n)
        self.define(node.name, a_node, 'variable')

        return a_node

    def visit_if_stmt(self, node):
        i_node = Node(node)
        c_node = self.visit(node.condition)
        i_node.deps.add(c_node)

        b_node = self.visit(node.body)
        b_node.deps.add(i_node)
        i_node.kills.update(b_node.kills)

        return i_node

    def visit_while_stmt(self, node):
        w_node = Node(node)
        c_node = self.visit(node.condition)
        w_node.deps.add(c_node)

        b_node = self.visit(node.body)
        b_node.deps.add(w_node)
        w_node.kills.update(b_node.kills)

        return w_node

    def visit_for_stmt(self, node):
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
        b_node = Node(node)
        l_node = self.visit(node.left)
        r_node = self.visit(node.right)

        b_node.deps.update({l_node, r_node})
        b_node.kills.update(l_node.kills | r_node.kills)
        return b_node

    def visit_unary_expr(self, node):
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
        r_node = Node(node)
        e_node = self.visit(node.expr)
        r_node.deps.add(e_node)
        r_node.kills.update(e_node.kills)
        raise RedundancyOptimizer.Return(r_node)

    def visit_call(self, node):
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
        v_node = Node(node)
        value_node = self.resolve(node.name, 'variable')
        v_node.deps.add(value_node)
        return v_node

    @staticmethod
    def visit_literal(node):
        return Node(node)

    def visit_unknown(self, m_name):
        pass


# HOW TO:
#  - find REACHING DEFINITIONS for expressions/statements within the loop
#  - if these are outside the loop - expression/statement can be moved outside the loop body
class LoopOptimizer(BaseVisitor):
    """Moves loop-invariant expressions outside of the loops (conditions, bodies etc)."""

    def __init__(self):
        self.scopes = [{'variable': set(), 'function': set()}]

    def reset(self):
        self.scopes = [{'variable': set(), 'function': set()}]

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

    def visit_return_stmt(self, node):
        self.visit(node.expr)

    def visit_call(self, node):
        depth = self.resolve(node.name, 'function')
        node.scope_depth = depth  # place scope info in the tree

        self.push_scope()
        for a in node.args:
            self.visit(a)
        self.pop_scope()

    def visit_variable(self, node):
        depth = self.resolve(node.name, 'variable')
        node.scope_depth = depth  # place scope info in the tree

    @staticmethod
    def visit_literal(node):
        pass

    def visit_unknown(self, m_name):
        pass
