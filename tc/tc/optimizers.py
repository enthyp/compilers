from tc.common import BaseVisitor
from tc.parser import Block


class Node:
    pass


class DAG:
    pass


class RedundancyOptimizer(BaseVisitor):
    """Builds (statically) a data dependency DAG and removes redundant subtrees of input AST.

    Attributes:
        effective_nodes (set): nodes that have side effects, e.g. 'return', 'print' and the like.
            In the end only the result of their execution matters, any data processing that does
            not contribute to an effective node is redundant
        scopes (list): stack of mappings (scopes) from variable name to AST node that defined the
            variable value
            # TODO: to remove redundant functions - you need to store their definition nodes too...
        control_deps (list): stack of sets of nodes that MAY be dependencies for nodes lower in
            the tree - like variables in the 'if' clause or 'for' condition etc
        dependencies (dict): map from node to list of nodes that key node depends on
    """

    def __init__(self):
        self.effective_nodes = set()
        self.scopes = [{}]
        self.control_deps = [set()]
        self.dependencies = {}

    def reset(self):
        self.effective_nodes = set()
        self.scopes = [{}]
        self.control_deps = [set()]
        self.dependencies = {}

    def push_scope(self):
        self.scopes.append({})

    def push_deps(self):
        self.control_deps.append(set())

    def define_var(self, name, node):
        self.scopes[-1][name] = node

    def resolve_var(self, name):
        for i in range(len(self.scopes)):
            if name in self.scopes[-(i + 1)]:
                return self.scopes[-(i + 1)][name]
        raise Exception(f'Failed to resolve variable {name}')

    def pop_scope(self):
        self.scopes.pop()

    def pop_deps(self):
        self.control_deps.pop()

    def run(self, statements):
        # Build the dependency graph and find effective nodes
        for stmt in statements:
            self.visit(stmt)

        # Prune ineffective nodes
        self.extend_effective()

        effective_statements = [s for s in statements if s in self.effective_nodes]
        for stmt in effective_statements:
            self.prune(stmt)

        return effective_statements

    def extend_effective(self):
        def extend_inner(node):
            if node not in self.dependencies:
                return
            for nd in self.dependencies[node]:
                self.effective_nodes.add(nd)
                extend_inner(nd)

        for node in self.effective_nodes.copy():
            extend_inner(node)

    def prune(self, node):
        if node not in self.effective_nodes:
            # Top level redundant node
            return

        if not isinstance(node, Block):
            return

        remaining_statements = []
        for stmt in node.statements:
            if stmt in self.effective_nodes:
                remaining_statements.append(stmt)
        node.statements = remaining_statements

    def visit_block(self, node):
        self.push_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.pop_scope()

    def visit_function_def(self, node):
        return  # TODO

        self.push_scope()
        for p in node.parameters:
            self.define(p.name, 'variable')

        self.visit(node.body)
        self.pop_scope()

    def visit_print_stmt(self, node):
        self.effective_nodes.add(node)
        self.visit(node.expr)
        self.dependencies[node] = [node.expr]

    def visit_variable_declaration(self, node):
        # TODO: add control_deps to dependencies EVERYWHERE!
        self.define_var(node.name, node)
        if node.value:
            self.visit(node.value)
            self.dependencies[node] = [node.value]

    def visit_assignment(self, node):
        self.define_var(node.name, node)  # overwrite previous node
        self.visit(node.value)
        self.dependencies[node] = [node.value]

    def visit_if_stmt(self, node):
        return  # TODO
        self.visit(node.condition)
        self.visit(node.body)

    def visit_while_stmt(self, node):
        return  # TODO

        self.visit(node.condition)
        self.visit(node.body)

    def visit_for_stmt(self, node):
        return  # TODO

        self.push_scope()

        self.visit(node.initializer)
        self.visit(node.condition)
        self.visit(node.body)
        self.visit(node.increment)

        self.pop_scope()

    def visit_binary_expr(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.dependencies[node] = [node.left, node.right]

    def visit_unary_expr(self, node):
        self.visit(node.expr)
        self.dependencies[node] = [node.expr]

    def visit_return_stmt(self, node):
        self.effective_nodes.add(node)
        self.visit(node.expr)
        self.dependencies[node] = [node.expr]

    def visit_call(self, node):
        self.dependencies[node] = []
        for a in node.args:
            self.visit(a)
            self.dependencies[node].add(a)

    def visit_variable(self, node):
        def_node = self.resolve_var(node.name)
        self.dependencies[node] = [def_node]

    @staticmethod
    def visit_literal(node):
        pass

    def visit_unknown(self, m_name):
        pass


# HOW TO:
#  - for each expression (go simple) node build a map from e.g. (KEY_1, OP, KEY_2) tuples
#    to nodes where computed value of this subexpression is stored
#  - when encountering other subexpressions - first check the map (caching)
#
#  Of interest: BinaryExpr, UnaryExpr, Call, Literal, Variable
#  Important: Call won't be optimized (order of execution matters - side effects!)
class ExpressionDAGOptimizer(BaseVisitor):
    """Converts expression parse trees to DAGs to decrease redundancy."""

    def __init__(self):
        self.in_expr = False
        self.subexpr = {}

    def reset(self):
        self.in_expr = False
        self.subexpr = {}

    def define(self, key, node):
        self.subexpr[key] = node

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

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
        self.visit(node.body)
        self.visit(node.increment)

    def visit_binary_expr(self, node, parent, parent_attr):
        print('in: ', node)
        outermost = not self.in_expr

        self.in_expr = True
        try:
            l_key = self.visit(node.left, node, 'left')
            r_key = self.visit(node.right, node, 'right')
            cur_key = (l_key, r_key, node.op)

            if cur_key in self.subexpr:
                setattr(parent, parent_attr, self.subexpr[cur_key])
            else:
                self.subexpr[cur_key] = node
            return cur_key
        except ExpressionDAGOptimizer.Call:
            if not outermost:
                raise
        finally:
            if outermost:
                self.reset()

    def visit_unary_expr(self, node, parent, parent_attr):
        outermost = not self.in_expr

        self.in_expr = True
        try:
            key = self.visit(node.expr, node, 'expr')
            cur_key = (key, node.op)
            if cur_key in self.subexpr:
                setattr(parent, parent_attr, self.subexpr[cur_key])
            else:
                self.subexpr[cur_key] = node
            return cur_key
        except ExpressionDAGOptimizer.Call:
            if not outermost:
                raise
        finally:
            if outermost:
                self.reset()

    def visit_return_stmt(self, node):
        self.visit(node.expr, node, 'expr')

    class Call(Exception):
        """We can't track side effects yet - retreat!"""
        pass

    def visit_call(self, node, parent, parent_attr):
        raise ExpressionDAGOptimizer.Call()

    def visit_variable(self, node, parent, parent_attr):
        return node.name

    @staticmethod
    def visit_literal(node, parent, parent_attr):
        return node.value

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
