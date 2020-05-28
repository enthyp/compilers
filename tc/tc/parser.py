import logging
import ply.lex as lex
import ply.yacc as yacc
import typing
from dataclasses import dataclass
from tc.common import Type


# All possible nodes of the abstract syntax tree.
@dataclass(unsafe_hash=True)
class AssertStmt:
    expr: typing.Any


@dataclass(unsafe_hash=True)
class Assignment:
    name: str
    value: typing.Any


@dataclass(unsafe_hash=True)
class BinaryExpr:
    left: typing.Any
    op: str
    right: typing.Any

    def __eq__(self, other):
        if isinstance(other, BinaryExpr):
            return self.left == other.left and self.op == other.op and self.right == other.right
        return False


class Block:
    def __init__(self, statements):
        self.statements = statements


@dataclass
class Call:
    name: str
    args: typing.List
    scope_depth: int = None

    def __hash__(self):
        return hash((hash(self.name), hash(self.scope_depth)))


class ForStmt:
    def __init__(self, initializer, condition, increment, body):
        self.initializer = initializer
        self.condition = condition
        self.increment = increment
        self.body = body


class FunctionDef:
    def __init__(self, name, parameters, return_type, body):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.body = body


class IfStmt:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


@dataclass(frozen=True)
class Literal:
    value: typing.Union[str, int, float, bool]
    type: typing.Any = None

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f'Literal(value={self.value}, type={self.type})'


class Parameter:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class PrintStmt:
    def __init__(self, expr):
        self.expr = expr


class ReturnStmt:
    def __init__(self, expr):
        self.expr = expr


class UnaryExpr:
    def __init__(self, operator, expr):
        self.op = operator
        self.expr = expr


@dataclass
class Variable:
    name: str
    scope_depth: int = None

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f'Variable(name={self.name})'


@dataclass
class VariableDeclaration:
    name: str
    type: typing.Any
    value: typing.Any

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f'VariableDeclaration(name={self.name}, value={self.value})'


class WhileStmt:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


###


class Parser:
    def __init__(self, debug=False):
        self.debug = debug

        # Build the lexer and parser
        self.lexer = lex.lex(module=self, debug=self.debug)
        self.yacc_parser = yacc.yacc(module=self, debug=self.debug)

    def run(self, input):
        return self.yacc_parser.parse(input, debug=self.debug)

    ###
    # LEXING
    ###

    tokens = [
        'INT', 'FLOAT', 'BOOL', 'STRING',
        'POW', 'EQ', 'NEQ', 'LE', 'LEQ', 'GE', 'GEQ',
        'IDENT',
    ]

    reserved = {
        'if': 'IF',
        'while': 'WHILE',
        'for': 'FOR',
        'var': 'VAR',
        'print': 'PRINT',
        'return': 'RETURN',
        'def': 'FUNCTION',
        'assert': 'ASSERT'
    }
    tokens += list(reserved.values())

    literals = ['=', '+', '-', '*', '/', '%', '(', ')', '[', ']', ':', ',', ';', '{', '}']

    t_EQ = r'=='
    t_NEQ = r'!='
    t_LE = r'<'
    t_LEQ = r'<='
    t_GE = r'>'
    t_GEQ = r'>='

    @staticmethod
    def t_POW(t):
        r"""\*\*"""
        t.value = '^'
        return t

    @staticmethod
    def t_FLOAT(t):
        r"""-?(\d+)\.\d*|-?\.(\d)+"""
        t.value = float(t.value)
        return t

    @staticmethod
    def t_INT(t):
        r"""-?\d+"""
        t.value = int(t.value)
        return t

    @staticmethod
    def t_BOOL(t):
        r"""true|false"""
        t.value = (t.value == 'true')
        return t

    @staticmethod
    def t_STRING(t):
        r"""(\'.*?\')|(\".*?\")"""
        t.value = t.value.strip('\'\"')
        return t

    def t_IDENT(self, t):
        r"""[a-zA-Z_][a-zA-Z_0-9]*"""
        t.type = self.reserved.get(t.value, 'IDENT')
        return t

    @staticmethod
    def t_COMMENT(t):
        r"""\#.*\n"""

    t_ignore = ' \t\n'

    @staticmethod
    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    ###
    # PARSING
    ###

    precedence = (
        ('nonassoc', 'EQ', 'NEQ', 'LEQ', 'LE', 'GEQ', 'GE'),
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
        ('right', 'POW'),
        ('right', 'UMINUS')
    )

    # A program is a list of statements.
    @staticmethod
    def p_statements(p):
        """statements : inner_statements statement
                      | inner_statements ns_statement 
                      | statement
                      | ns_statement
        """
        if len(p) == 3:
            if p[2]:
                p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = [p[1]] if p[1] else []

    @staticmethod
    def p_inner_stmt(p):
        """inner_statements : inner_statements statement ';'
                            | statement ';'
        """
        if len(p) == 4:
            if p[2]:
                p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = [p[1]] if p[1] else []

    @staticmethod
    # A statement (like block or function declaration) without delimiting semicolon.
    def p_inner_block(p):
        """inner_statements : inner_statements ns_statement
                            | ns_statement
        """
        if len(p) == 3:
            if p[2]:
                p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = [p[1]] if p[1] else []

    @staticmethod
    def p_statements_err(p):
        """statements : statements error statement """
        logging.error('Skipped syntactically incorrect statement.')
        p[0] = p[1] + [p[3]]

    @staticmethod
    def p_stmt_empty(p):
        """statement : """

    @staticmethod
    def p_stmt_block(p):
        """ns_statement : block"""
        p[0] = p[1]

    @staticmethod
    def p_block(p):
        """block : '{' statements '}'"""
        p[0] = Block(p[2])

    @staticmethod
    def p_print_stmt(p):
        """statement : PRINT expr"""
        p[0] = PrintStmt(p[2])

    @staticmethod
    def p_function_declaration_noarg(p):
        """ns_statement : FUNCTION IDENT '(' ')' ':' IDENT block
                        | FUNCTION IDENT '(' ')' block
        """
        if len(p) == 6:
            return_type = Type.UNIT
            body = p[5]
        else:
            return_type = Type(p[6])
            body = p[7]
        p[0] = FunctionDef(name=p[2], parameters=[], return_type=return_type, body=body)

    @staticmethod
    def p_function_declaration(p):
        """ns_statement : FUNCTION IDENT '(' params ')' ':' IDENT block
                        | FUNCTION IDENT '(' params ')' block
        """
        if len(p) == 7:
            return_type = Type.UNIT
            body = p[6]
        else:
            return_type = Type(p[7])
            body = p[8]
        p[0] = FunctionDef(name=p[2], parameters=p[4], return_type=return_type, body=body)

    @staticmethod
    def p_params(p):
        """params : params ',' param
                  | param
        """
        if len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        else:
            p[0] = [p[1]]

    @staticmethod
    def p_param(p):
        """param : IDENT ':' IDENT"""
        p[0] = Parameter(name=p[1], type=Type(p[3]))

    @staticmethod
    def p_var_declaration_noval(p):
        """statement : VAR IDENT ':' IDENT"""
        p[0] = VariableDeclaration(name=p[2], type=Type(p[4]), value=None)

    @staticmethod
    def p_var_declaration_value(p):
        """statement : VAR IDENT ':' IDENT '=' rvalue"""
        p[0] = VariableDeclaration(name=p[2], type=Type(p[4]), value=p[6])

    @staticmethod
    def p_var_assignment(p):
        """statement : IDENT '=' rvalue"""
        p[0] = Assignment(name=p[1], value=p[3])

    # Lvalues are handled implicitly as variable declarations or definitions.
    @staticmethod
    def p_rvalue(p):
        """rvalue : expr"""
        p[0] = p[1]

    @staticmethod
    def p_if_stmt(p):
        """ns_statement : IF '(' expr ')' block"""
        p[0] = IfStmt(condition=p[3], body=p[5])

    @staticmethod
    def p_while_stmt(p):
        """ns_statement : WHILE '(' expr ')' block"""
        p[0] = WhileStmt(condition=p[3], body=p[5])

    @staticmethod
    def p_for_stmt(p):
        """ns_statement : FOR '(' statement ';' expr ';' statement ')' block"""
        p[0] = ForStmt(initializer=p[3], condition=p[5], increment=p[7], body=p[9])

    @staticmethod
    def p_return_stmt(p):
        """statement : RETURN expr"""
        p[0] = ReturnStmt(expr=p[2])

    @staticmethod
    def p_assert_stmt(p):
        """statement : ASSERT expr"""
        p[0] = AssertStmt(expr=p[2])

    # Expressions
    @staticmethod
    def p_expression_statement(p):
        """statement : expr"""
        p[0] = p[1]

    @staticmethod
    def p_expr_function_call_noarg(p):
        """expr : IDENT '(' ')'"""
        p[0] = Call(name=p[1], args=[])

    @staticmethod
    def p_expr_function_call(p):
        """expr : IDENT '(' arguments ')'"""
        p[0] = Call(name=p[1], args=p[3])

    @staticmethod
    def p_expr_function_call_no_par(p):
        """expr : call_no_par """
        p[0] = p[1]

    @staticmethod
    def p_call_no_par(p):
        """call_no_par : IDENT call_no_par
                       | IDENT variable
                       | IDENT primitive
        """
        p[0] = Call(name=p[1], args=[p[2]])

    @staticmethod
    def p_arguments(p):
        """arguments : arguments ',' expr
                     | expr
        """
        if len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        else:
            p[0] = [p[1]]

    @staticmethod
    def p_expr_par(p):
        """expr : '(' expr ')'
                | '[' onp_expr ']'
        """
        p[0] = p[2]

    @staticmethod
    def p_expr_binary(p):
        """expr : expr '+' expr
                | expr '-' expr
                | expr '*' expr
                | expr '/' expr
                | expr '%' expr
                | expr POW expr
                | expr EQ expr
                | expr NEQ expr
                | expr LE expr
                | expr LEQ expr
                | expr GE expr
                | expr GEQ expr
        """
        p[0] = BinaryExpr(left=p[1], right=p[3], op=p[2])

    @staticmethod
    def p_onp_expr_binary(p):
        """onp_expr : onp_expr onp_expr '+'
                    | onp_expr onp_expr '-'
                    | onp_expr onp_expr '*'
                    | onp_expr onp_expr '/'
                    | onp_expr onp_expr '%'
                    | onp_expr onp_expr POW
                    | onp_expr onp_expr EQ
                    | onp_expr onp_expr NEQ
                    | onp_expr onp_expr LE
                    | onp_expr onp_expr LEQ
                    | onp_expr onp_expr GE
                    | onp_expr onp_expr GEQ
        """
        p[0] = BinaryExpr(left=p[1], right=p[2], op=p[3])

    @staticmethod
    def p_expr_uminus(p):
        """expr : '-' expr %prec UMINUS"""
        p[0] = UnaryExpr(operator='-', expr=p[2])

    @staticmethod
    def p_expr_mult_implicit(p):
        """expr : expr expr """
        p[0] = BinaryExpr(op='*', left=p[1], right=p[2])

    @staticmethod
    def p_expr_var(p):
        """expr : variable"""
        p[0] = p[1]

    @staticmethod
    def p_onp_expr_var(p):
        """onp_expr : variable"""
        p[0] = p[1]

    @staticmethod
    def p_expr_var_value(p):
        """variable : IDENT"""
        p[0] = Variable(name=p[1])

    @staticmethod
    def p_expr_primitive(p):
        """expr : primitive"""
        p[0] = p[1]

    @staticmethod
    def p_onp_expr_primitive(p):
        """onp_expr : primitive"""
        p[0] = p[1]

    @staticmethod
    def p_expr_bool(p):
        """primitive : BOOL"""
        p[0] = Literal(value=p[1], type=Type.BOOL)

    @staticmethod
    def p_expr_int(p):
        """primitive : INT"""
        p[0] = Literal(value=p[1], type=Type.INT)

    @staticmethod
    def p_expr_float(p):
        """primitive : FLOAT"""
        p[0] = Literal(value=p[1], type=Type.FLOAT)

    @staticmethod
    def p_expr_string(p):
        """primitive : STRING"""
        p[0] = Literal(value=p[1], type=Type.STRING)
