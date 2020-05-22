from collections import defaultdict
from contextlib import contextmanager
from tc.common import BaseVisitor
from tc.globals import global_env

global_functions = global_env().functions.keys()

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
        if not statements:
            return gen, kill

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


class InOutBuilder(BaseVisitor):
    """Statically determines IN and OUT sets for each node of the AST.

    We are specifically interested in IN sets at each node, because they contain all reachable variable
    definitions for nodes and allow us to follow the Use-Definition chains.

    """

    def __init__(self, gen, kill):
        self.in_sets = {}
        self.out_sets = {}
        self.gen = gen
        self.kill = kill

    def reset(self):
        self.in_sets = {}
        self.out_sets = {}

    def run(self, statements):
        self.in_sets[TOP] = set()
        self.out_sets[TOP] = self.visit_statements(statements, self.in_sets[TOP])
        return self.in_sets, self.out_sets

    def visit_statements(self, statements, in_set):
        if not statements:
            return in_set

        self.in_sets[statements[0]] = in_set

        for i, stmt in enumerate(statements[:-1]):
            self.visit(stmt)
            self.in_sets[statements[i + 1]] = self.out_sets[stmt]

        self.visit(statements[-1])

        return self.out_sets[statements[-1]]

    def transfer(self, node):
        # Classic
        self.out_sets[node] = self.gen[node] | (self.in_sets[node] - self.kill[node])

    def visit_block(self, node):
        self.visit_statements(node.statements, self.in_sets[node])
        self.transfer(node)

    def visit_function_def(self, node):
        self.in_sets[node.body] = self.in_sets[node]
        self.visit(node.body)
        self.transfer(node)

    def visit_variable_declaration(self, node):
        if node.value:
            self.in_sets[node.value] = self.in_sets[node]
            self.visit(node.value)
        self.transfer(node)

    def visit_assignment(self, node):
        self.in_sets[node.value] = self.in_sets[node]
        self.visit(node.value)
        self.transfer(node)

    def visit_print_stmt(self, node):
        self.in_sets[node.expr] = self.in_sets[node]
        self.visit(node.expr)
        self.transfer(node)

    def visit_if_stmt(self, node):
        self.in_sets[node.condition] = self.in_sets[node]
        self.visit(node.condition)

        self.in_sets[node.body] = self.out_sets[node.condition]
        self.visit(node.body)
        self.out_sets[node] = self.out_sets[node.condition] | self.out_sets[node.body]

    def visit_while_stmt(self, node):
        self.in_sets[node.condition] = self.in_sets[node] | self.gen[node.body]
        self.visit(node.condition)

        self.in_sets[node.body] = self.out_sets[node.condition]
        self.visit(node.body)
        self.out_sets[node] = self.out_sets[node.condition] | self.out_sets[node.body]

    def visit_for_stmt(self, node):
        self.in_sets[node.initializer] = self.in_sets[node]
        self.visit(node.initializer)

        self.in_sets[node.condition] = self.out_sets[node.initializer] | self.gen[node.increment]
        self.visit(node.condition)

        self.in_sets[node.body] = self.out_sets[node.condition]
        self.visit(node.body)

        self.in_sets[node.increment] = self.out_sets[node.body]
        self.visit(node.increment)
        self.out_sets[node] = (
            self.out_sets[node.condition] | self.out_sets[node.body]
        )

    def visit_binary_expr(self, node):
        stmt_list = [node.left, node.right]
        self.out_sets[node] = self.visit_statements(stmt_list, self.in_sets[node])

    def visit_unary_expr(self, node):
        self.in_sets[node.expr] = self.in_sets[node]
        self.visit(node.expr)
        self.transfer(node)

    def visit_return_stmt(self, node):
        self.in_sets[node.expr] = self.in_sets[node]
        self.visit(node.expr)
        self.transfer(node)

    def visit_call(self, node):
        self.visit_statements(node.args, self.in_sets[node])
        self.transfer(node)

    def visit_variable(self, node):
        self.transfer(node)

    def visit_literal(self, node):
        self.transfer(node)  # not really necessary

    def visit_unknown(self, m_name):
        pass
