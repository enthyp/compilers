from tc.common import BaseVisitor
from tc.globals import global_env
from tc.parser import Variable

global_functions = global_env().functions.keys()


class EffectiveNodeSearch(BaseVisitor):
    """Finds top level statements with side effects.

    These include:
        - top level 'print' statements
        - top level calls of functions with side effects
    """

    def __init__(self):
        self.effective_nodes = set()
        self.scopes = [{}]
        self.fun_def_scopes = []

    def reset(self):
        self.effective_nodes = set()
        self.scopes = [{}]
        self.fun_def_scopes = []

    def push_scope(self):
        self.scopes.append({})

    def push_fun_scope(self, name):
        self.fun_def_scopes.append(name)

    def pop_scope(self):
        self.scopes.pop()

    def pop_fun_scope(self):
        self.fun_def_scopes.pop()

    def define_fun(self, name):
        self.scopes[-1][name] = False

    def resolve_fun(self, name):
        for i in range(len(self.scopes)):
            if name in self.scopes[-(i + 1)]:
                return i
        raise Exception(f'Failed to resolve function {name}')

    def is_effective(self, name):
        depth = self.resolve_fun(name)
        return self.scopes[-(depth + 1)][name]

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)

    def visit_block(self, node):
        self.push_scope()

        for stmt in node.statements:
            self.visit(stmt)

        self.pop_scope()

    def visit_function_def(self, node):
        self.define_fun(node.name)
        self.push_fun_scope(node.name)
        try:
            self.visit(node.body)
        except EffectiveNodeSearch.Print:
            depth = self.resolve_fun(node.name)
            self.scopes[-(depth + 1)][node.name] = True
        finally:
            self.pop_fun_scope()

    class Print(Exception):
        pass

    def visit_print_stmt(self, node):
        if self.fun_def_scopes:
            # Notify - currently defined function is effective
            raise EffectiveNodeSearch.Print()
        else:
            # Top level print - an effective statement
            self.effective_nodes.add(node)

    def visit_variable_declaration(self, node):
        if node.value:
            self.visit(node.value)

    def visit_assignment(self, node):
        self.visit(node.value)

    def visit_if_stmt(self, node):
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.body)
        self.visit(node.increment)

    def visit_binary_expr(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_unary_expr(self, node):
        self.visit(node.expr)

    def visit_return_stmt(self, node):
        self.visit(node.expr)

    def visit_call(self, node):
        if self.is_effective(node.name):
            self.effective_nodes.add(node)

    def visit_variable(self, node):
        pass

    def visit_literal(self, node):
        pass

    def visit_unknown(self, m_name):
        pass


class Node:
    """Node of data dependency graph where edges correspond to Use-Define relations."""
    def __init__(self, node):
        self.ast_node = node  # corresponding AST node
        self.deps = set()  # defs needed for given use (Use-Define relationship)
        self.kills = set()  # set of (name, redefinition node that kills previous definition of name)


class DefinitionReach(BaseVisitor):
    """Statically builds a use-def graph."""

    def __init__(self):
        self.scopes = [{
            'variable': {},
            'function': {f: Node(None) for f in global_functions}
        }]

    def reset(self):
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
                return i
        raise Exception(f'Failed to resolve {what} {name}')

    def pop_scope(self):
        self.scopes.pop()

    def kill(self, kills):
        for name, node in kills:
            self.scopes[-1]['variable'][name] = node

    def run(self, statements):
        # Build the dependency graph
        ext_statements = []
        for stmt in statements:
            ext_statements.append(self.visit(stmt))

    def visit_block(self, node):
        b_node = Node(node)

        self.push_scope()
        try:
            for stmt in node.statements:
                n = self.visit(stmt)
                n.deps.add(b_node)
                b_node.kills.update(n.kills)
        except RedundancyOptimizer.Return as r:
            b_node.kills.update(r.node.kills)
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
        n = self.visit(node.expr)

        p_node.deps.add(n)
        self.kill(n.kills)

        self.effective_nodes.add(p_node)
        return p_node

    def visit_variable_declaration(self, node):
        v_node = Node(node)

        if node.value:
            n = self.visit(node.value)
            v_node.deps.add(n)
            v_node.kills.update(n.kills)

        self.define(node.name, v_node, 'variable')
        return v_node

    def visit_assignment(self, node):
        a_node = Node(node)
        n = self.visit(node.value)

        a_node.deps.add(n)
        a_node.kills.add((node.name, a_node))

        depth = self.resolve(node.name, 'variable')
        self.scopes[-(depth + 1)]['variable'][node.name] = a_node

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

        from copy import deepcopy
        scopy = [deepcopy(s) for s in self.scopes]

        b_node = self.visit(node.body)
        w_node.kills.update(b_node.kills)
        b_node.deps.add(w_node)
        import pprint as pp
        pp.pprint(b_node.kills)

        # Variables in loop condition depend on redefinitions in loop body!
        # TODO: separation of data dependencies from AST structure would do better?
        cond_deps = set()
        for n in c_node.deps:
            if isinstance(n.ast_node, Variable):
                cond_deps.add(n.ast_node.name)

        for name, node in w_node.kills:
            if name in cond_deps:
                c_node.deps.add(node)

            # TODO:???
            for sc in reversed(scopy):
                if name in sc['variable']:
                    sc['variable'][name].deps.add(node)

        return w_node

    def visit_for_stmt(self, node):
        f_node = Node(node)
        self.push_scope()

        init_node = self.visit(node.initializer)
        c_node = self.visit(node.condition)
        inc_node = self.visit(node.increment)

        b_node = self.visit(node.body)
        b_node.deps.add(f_node)
        f_node.deps.update({
            init_node, c_node, inc_node
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

        f_depth = self.resolve(node.name, 'function')
        f_node = self.scopes[-(f_depth + 1)]['function'][node.name]
        c_node.deps.add(f_node)
        self.kill(f_node.kills)

        return c_node

    def visit_variable(self, node):
        v_node = Node(node)
        v_depth = self.resolve(node.name, 'variable')
        value_node = self.scopes[-(v_depth + 1)]['variable'][node.name]
        v_node.deps.add(value_node)
        return v_node

    def visit_literal(self, node):
        return Node(node)

    def visit_unknown(self, m_name):
        pass


class RedundancyOptimizer(BaseVisitor):
    """Removes redundant subtrees of input AST."""

    def __init__(self):
        self.effective_search = EffectiveNodeSearch()
        self.def_reach = DefinitionReach()

    def reset(self):
        self.effective_search.reset()
        self.def_reach.reset()

    def run(self, statements):
        # Build the dependency graph
        ext_statements = []
        for stmt in statements:
            ext_statements.append(self.visit(stmt))

        # Find all effective nodes
        search = EffectiveNodeSearch()
        for stmt in statements:
            search.run(stmt)
        self.effective_nodes = self.extend(search.effective_nodes)

        # Prune redundant subtrees
        self.mode = self.PRUNE
        effective_statements = [s for s in statements if s in self.effective_nodes]
        for stmt in effective_statements:
            self.visit(stmt)

        return effective_statements

    # TODO: effective_nodes are from AST, not dep graph
    def extend(self, effective_nodes):
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
        remaining_statements = []
        for stmt in node.statements:
            if stmt in self.effective_nodes:
                remaining_statements.append(stmt)
                self.visit(stmt)
        node.statements = remaining_statements

    def visit_function_def(self, node):
        self.visit(node.body)

    def visit_if_stmt(self, node):
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.body)

    def visit_unknown(self, m_name):
        return
