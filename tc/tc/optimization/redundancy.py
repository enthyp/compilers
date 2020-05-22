from collections import defaultdict
from contextlib import contextmanager
from tc.common import BaseVisitor
from tc.globals import global_env
from tc.parser import Variable

global_functions = global_env().functions.keys()


class EffectiveNodeSearch(BaseVisitor):
    """Finds top level statements with side effects.

    These include:
        - top level 'print' statements
        - top level calls of functions with side effects
        - TODO: return statements of functions called in effective nodes
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

    def visit_unknown(self, m_name):
        pass


TOP = 'PROGRAM'


class VarDefLocator(BaseVisitor):
    """Finds all variable declarations/assignments in the program."""

    def __init__(self):
        self.defs = set()

    def reset(self):
        self.defs = set()

    def run(self, statements):
        for stmt in statements:
            self.visit(stmt)
        return self.defs

    def visit_block(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_function_def(self, node):
        for p in node.parameters:
            self.visit(p)
        self.visit(node.body)

    def visit_variable_declaration(self, node):
        self.defs.add(node)

    def visit_assignment(self, node):
        self.defs.add(node)

    def visit_if_stmt(self, node):
        self.visit(node.body)

    def visit_while_stmt(self, node):
        self.visit(node.body)

    def visit_for_stmt(self, node):
        self.visit(node.initializer)
        self.visit(node.increment)
        self.visit(node.body)

    def visit_unknown(self, m_name):
        pass


class GenKillBuilder(BaseVisitor):
    """Statically determines GEN and KILL sets of variable definition nodes for each node of the AST.

    Importantly, we use very crude approximation of GEN and KILL sets for scoped blocks. For GEN sets, we
    simply take GEN of the inner block statements (so we disregard fact that GENs like inner variable
    declarations can't be visible outside), which is a blown-up upper bound. For KILL, we take an empty
    set as a lower bound, so we disregard fact that assignments to outer scope variables are legitimate
    KILLs.

    TODO: use stack of scopes to approximate them better
    TODO: 'return' statement should only appear at the end of a block?

    Attributes:
        var_defs (dict): map (name -> set of Assignment/VariableDeclaration nodes) - all variable
            definitions in the whole program
        scopes (list): stack of scopes, in each we store GEN and KILL sets that shall be assigned to
            Call nodes for functions present in scope
        gen (dict): map (AST node -> set of Assignment/VariableDeclaration nodes) - all definitions of
            variables (assignments or declarations) WITHIN given node that reach the endpoint of this
            node
        kill (dict): map (AST node -> set of Assignment/VariableDeclaration nodes) - all definitions
            of variables within/outside given node that do not reach the endpoint of this node due to
            reassignment or redeclaration
    """

    def __init__(self):
        self.var_defs = defaultdict(set)
        self.scopes = [{}]
        self.gen = {}
        self.kill = {}

    def reset(self):
        self.var_defs = defaultdict(set)
        self.scopes = [{}]
        self.gen = {}
        self.kill = {}

    @contextmanager
    def in_scope(self):
        try:
            self.scopes.append({})
            yield
        finally:
            self.scopes.pop()

    def resolve(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f'Failed to resolve function {name}')

    def run(self, statements):
        self.gather_defs(statements)
        self.gen[TOP], self.kill[TOP] = self.visit_statements(statements)
        return self.gen, self.kill

    def gather_defs(self, statements):
        locator = VarDefLocator()
        def_nodes = locator.run(statements)
        for node in def_nodes:
            self.var_defs[node.name].add(node)

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


class RedundancyOptimizer(BaseVisitor):
    """Removes redundant subtrees of input AST."""

    def __init__(self):
        self.effective_search = EffectiveNodeSearch()
        self.use_def = GenKillBuilder()

    def reset(self):
        self.effective_search.reset()
        self.use_def.reset()

    def run(self, statements):
        # TODO:
        #  - find effective nodes
        #  - build use-def table
        #  - traverse AST from effective nodes via use-def table to find all required nodes
        #  - prune all nodes that were not found required

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
