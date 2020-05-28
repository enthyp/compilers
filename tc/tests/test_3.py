import logging
import pytest
from tc.common import PrettyPrinter
from tc.interpreter import Evaluator, Interpreter
from tc.parser import Literal, Parser, VariableDeclaration
from tc.typecheck import Type

logging.basicConfig(level=logging.INFO)

tree_program = """
    var n : int = 10;
    
    def fib(n : int) : int {
        var a : int = 1;
        var b : int = 1;
        var i : int = 1;
        while (i < n) {
            print b;
            var tmp : int = a;
            a = b;
            b = tmp + b;
            i = i + 1
        }
        return b
    }
    
    print fib(n)
"""


def test_ast_viz():
    parser = Parser()
    ast = parser.run(tree_program)
    pp = PrettyPrinter()
    pp.run(ast, 'out/test', view=False)


types_program = """
    var w: string = 'string';
    var x: int = 1;
    var y: float;
    var z: bool = true;
"""
types_ast = [
    VariableDeclaration('w', Type.STRING, Literal('string', Type.STRING)),
    VariableDeclaration('x', Type.INT, Literal(1, Type.INT)),
    VariableDeclaration('y', Type.FLOAT, None),
    VariableDeclaration('z', Type.BOOL, Literal(True, Type.BOOL))
]


def test_type_declarations():
    parser = Parser()
    ast = parser.run(types_program)
    assert ast == types_ast


typecheck_programs = [
    'var w: string; w = 1',
    'var a: int = 1; var b: float = 2; a + b',
    'var a: string = "a"; a + 1',
    'if (2 + 2) { print 4 }'
]


@pytest.mark.parametrize('test_input', typecheck_programs)
def test_typecheck_raised(test_input):
    interpreter = Interpreter()
    with pytest.raises(TypeError):
        interpreter.run(test_input)


assignment_program = """
    var x: int = 1;
    x = x + 2;
    assert x == 3
"""


def test_assignment():
    interpreter = Interpreter()
    interpreter.run(assignment_program)


operator_overload_program = """
    var x: int = 1;
    assert x + 1 == 2;

    var y: string = "ala ma ";
    assert y + "kota" == "ala ma kota"'
"""


def test_operator_overload():
    interpreter = Interpreter()
    interpreter.run(operator_overload_program)


declaration_checks = [
    ('var x: int = 1; print y', 'Failed to resolve variable'),
    ('var x: int; 1 + 1; var x: int = 2;', 'declared twice'),
    ('var x: int = 2; 1 + 1; var x: int = 2;', 'declared twice')
]


@pytest.mark.parametrize('test_input, error_msg', declaration_checks)
def test_declarations_raised(test_input, error_msg):
    interpreter = Interpreter()
    with pytest.raises(Exception) as exc_info:
        interpreter.run(test_input)
    assert error_msg in str(exc_info)


lvalue_checks = [
    'var x: int = 1; 2 = x; print x',
]


@pytest.mark.parametrize('test_input', lvalue_checks)
def test_lvalues_raised(test_input):
    interpreter = Interpreter()
    interpreter.run(test_input)


type_conversions_program = """
    var x: int = 1;
    assert tofloat(x) == 1.0;
    assert tostring(x) == '1';
    assert x == toint(1.0)
"""


def test_type_conversions():
    interpreter = Interpreter()
    interpreter.run(type_conversions_program)
