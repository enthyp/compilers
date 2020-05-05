import re
from graphviz import Digraph
from uuid import uuid4


class BaseVisitor:

    cc_pattern = re.compile(r'([A-Z]+)')

    def visit(self, node):
        # Find appropriate implementation.
        k_name = node.__class__.__name__
        k_name = self.cc_pattern.sub(r'_\1', k_name).lower()  # to snake case
        m_name = 'visit' + k_name

        method = getattr(self, m_name, None)

        if not method:
            self.visit_unknown(m_name)
        else:
            return method(node)

    def visit_unknown(self, m_name):
        raise Exception('No such method: {}!'.format(m_name))


class Callable:
    def __init__(self, params, body):
        self.params = params
        self.body = body


class Environment:
    # Inspired by https://craftinginterpreters.com/contents.html

    def __init__(self, enclosing):
        self.functions = {}
        self.variables = {}
        self.enclosing = enclosing

    def define_fun(self, name, obj):
        self.functions[name] = obj

    def resolve_fun(self, name, locally=False):
        env = self
        while env:
            if name in env.functions:
                return env.functions[name]
            if locally:
                break
            env = env.enclosing
        raise Exception(f'Failed to resolve function {name}')

    def declare_var(self, name, obj):
        self.variables[name] = obj

    def resolve_var(self, name, locally=False):
        env = self
        while env:
            if name in env.variables:
                return env.variables[name]
            if locally:
                break
            env = env.enclosing
        raise Exception(f'Failed to resolve variable {name}')

    def define_var(self, name, obj):
        env = self
        while env:
            if name in env.variables:
                env.variables[name] = obj
            env = env.enclosing


class PrettyPrinter(BaseVisitor):
    def __init__(self):
        self.graph = Digraph('.', node_attr={'style': 'filled'}, format='png')
        self.root_id = self.node_id()
        self.graph.node(self.root_id, 'top')

    def run(self, statements, filepath, view=True):
        for stmt in statements:
            self.graph.edge(self.root_id, self.visit(stmt), '')
        self.graph.render(filepath, view=view)

    def visit_block(self, node):
        return self.add_viz_node(node, 'block', ['statements'])

    def visit_function(self, node):
        return self.add_viz_node(node, f'definition of {node.name}', ['body', 'parameters'])

    def visit_parameter(self, node):
        return self.add_viz_node(node, f'param {node.name} : {node.type}', [])

    def visit_print_stmt(self, node):
        return self.add_viz_node(node, 'print', ['expr'])

    def visit_variable_declaration(self, node):
        return self.add_viz_node(node, f'declaration of {node.name} : {node.type}', ['value'])

    def visit_assignment(self, node):
        return self.add_viz_node(node, f'assignment to {node.name}', ['value'])

    def visit_if_stmt(self, node):
        return self.add_viz_node(node, 'if', ['condition', 'body'])

    def visit_while_stmt(self, node):
        return self.add_viz_node(node, 'while', ['condition', 'body'])

    def visit_for_stmt(self, node):
        return self.add_viz_node(node, 'for', ['initializer', 'condition', 'increment', 'body'])

    def visit_binary_expr(self, node):
        return self.add_viz_node(node, node.op, ['left', 'right'])

    def visit_unary_expr(self, node):
        return self.add_viz_node(node, node.op, ['expr'])

    def visit_return_stmt(self, node):
        return self.add_viz_node(node, 'return', ['expr'])

    def visit_call(self, node):
        return self.add_viz_node(node, f'call {node.name}', ['args'])

    def visit_variable(self, node):
        return self.add_viz_node(node, f'value of {node.name}', [])

    def visit_literal(self, node):
        return self.add_viz_node(node, f'literal {node.value}', [])

    @staticmethod
    def node_id():
        return str(uuid4())

    def add_viz_node(self, node, label, child_attributes):
        n_id = self.node_id()
        self.graph.node(n_id, label=label)

        for c in child_attributes:
            field = getattr(node, c)
            if isinstance(field, list):
                for child in field:
                    self.graph.edge(n_id, self.visit(child), label='')
            else:
                self.graph.edge(n_id, self.visit(field), label='')
        return n_id
