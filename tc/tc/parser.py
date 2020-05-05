import ply.lex as lex
import ply.yacc as yacc
from tc.typecheck import Type


# All possible nodes of the abstract syntax tree.
class Assignment:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class BinaryExpr:
    def __init__(self, left, operator, right):
        self.left = left
        self.op = operator
        self.right = right


class Block:
    def __init__(self, statements):
        self.statements = statements


class Call:
    def __init__(self, name, arguments):
        self.name = name
        self.args = arguments


class ForStmt:
    def __init__(self, initializer, condition, increment, body):
        self.initializer = initializer
        self.condition = condition
        self.increment = increment
        self.body = body


class Function:
    def __init__(self, name, parameters, return_type, body):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.body = body


class IfStmt:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class Literal:
    def __init__(self, value, type):
        self.value = value
        self.type = type


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


class Variable:
    def __init__(self, name):
        self.name = name


class VariableDeclaration:
    def __init__(self, name, type, value):
        self.name = name
        self.type = type
        self.value = value


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

    # Lexing rules.
    tokens = [
        'INT', 'FLOAT', 'BOOL', 'STRING',
        'EQ', 'NEQ', 'LE', 'LEQ', 'GE', 'GEQ', 'ITOF',
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
    }
    tokens += list(reserved.values())

    literals = ['=', '+', '-', '*', '/', '^', '(', ')', ':', ',', ';', '{', '}']

    t_EQ = r'=='
    t_NEQ = r'!='
    t_LE = r'<'
    t_LEQ = r'<='
    t_GE = r'>'
    t_GEQ = r'>='

    @staticmethod
    def t_ITOF(t):
        r"""inttofloat"""
        t.value = 'itof'
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

    t_ignore = ' \t\n'

    @staticmethod
    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Parsing.
    # A program is a list of statements.
    @staticmethod
    def p_statements(p):
        """statements : statements ';' statement
                      | statement
        """
        if len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        else:
            p[0] = [p[1]]

    @staticmethod
    def p_statements_err(p):
        """statements : error"""
        print('Error!')
        raise Exception

    @staticmethod
    def p_stmt_block(p):
        """statement : block"""
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
        """statement : FUNCTION IDENT '(' ')' ':' IDENT block
                     | FUNCTION IDENT '(' ')' block
        """
        if len(p) == 5:
            return_type = Type.UNIT
        else:
            return_type = Type(p[6])
        p[0] = Function(name=p[2], parameters=[], return_type=return_type, body=p[7])

    @staticmethod
    def p_function_declaration(p):
        """statement : FUNCTION IDENT '(' params ')' ':' IDENT block
                     | FUNCTION IDENT '(' params ')' block
        """
        if len(p) == 7:
            return_type = Type.UNIT
            body = p[6]
        else:
            return_type = Type(p[7])
            body = p[8]
        p[0] = Function(name=p[2], parameters=p[4], return_type=return_type, body=body)

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
        """statement : IF '(' expr ')' block"""
        p[0] = IfStmt(condition=p[3], body=p[5])

    @staticmethod
    def p_while_stmt(p):
        """statement : WHILE '(' expr ')' block"""
        p[0] = WhileStmt(condition=p[3], body=p[5])

    @staticmethod
    def p_for_stmt(p):
        """statement : FOR '(' statement ';' expr ';' statement ')' block"""
        p[0] = ForStmt(initializer=p[3], condition=p[5], increment=p[7], body=p[9])

    @staticmethod
    def p_return_stmt(p):
        """statement : RETURN expr"""
        p[0] = ReturnStmt(expr=p[2])

    # Expressions
    @staticmethod
    def p_expression_statement(p):
        """statement : expr"""
        p[0] = p[1]

    @staticmethod
    def p_expr_function_call_noarg(p):
        """expr : IDENT '(' ')'"""
        p[0] = Call(name=p[1], arguments=[])

    @staticmethod
    def p_expr_function_call(p):
        """expr : IDENT '(' arguments ')'"""
        p[0] = Call(name=p[1], arguments=p[3])

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
    def p_expr_binary(p):
        """expr : expr expr '+'
                | expr expr '-'
                | expr expr '*'
                | expr expr '/'
                | expr expr '^'
                | expr expr EQ
                | expr expr NEQ
                | expr expr LE
                | expr expr LEQ
                | expr expr GE
                | expr expr GEQ
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExpr(left=p[1], right=p[2], operator=p[3])

    @staticmethod
    def p_expr_uminus(p):
        """expr : expr '-'"""
        p[0] = UnaryExpr(operator='-', expr=p[1])

    @staticmethod
    def p_expr_inttofloat(p):
        """expr : expr ITOF"""
        p[0] = UnaryExpr(operator='itof', expr=p[1])

    @staticmethod
    def p_expr_var_value(p):
        """expr : IDENT"""
        p[0] = Variable(name=p[1])

    @staticmethod
    def p_expr_bool(p):
        """expr : BOOL"""
        p[0] = Literal(value=p[1], type=Type.BOOL)

    @staticmethod
    def p_expr_int(p):
        """expr : INT"""
        p[0] = Literal(value=p[1], type=Type.INT)

    @staticmethod
    def p_expr_float(p):
        """expr : FLOAT"""
        p[0] = Literal(value=p[1], type=Type.FLOAT)

    @staticmethod
    def p_expr_string(p):
        """expr : STRING"""
        p[0] = Literal(value=p[1], type=Type.STRING)
