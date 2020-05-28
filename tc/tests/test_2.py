import logging
import pytest
from tc.interpreter import Evaluator, Interpreter
from tc.parser import Parser

logging.basicConfig(level=logging.INFO)

operations = [
    'assert 2 ** 3 == 8',
    'assert sin(0) == 0.',
    'assert cos(0) == 1.',
    'assert 1 < 2',
    'assert 2 >= 1',
    'assert 1 != 2',
    'assert -1 == 1 * (-1)'
]


@pytest.mark.parametrize('test_input', operations)
def test_operations_impl(test_input):
    interpreter = Interpreter()
    interpreter.run(test_input)


semicolon_separated = [
    'assert 1 == 1; assert 2 == 2'
]


@pytest.mark.parametrize('test_input', semicolon_separated)
def test_semicolon_separated(test_input):
    interpreter = Interpreter()
    interpreter.run(test_input)


error_continuation = [
    'var x:: ; print "skipped erroneous statement!"'
]


@pytest.mark.parametrize('test_input', error_continuation)
def test_error_continuation(test_input):
    parser = Parser()
    ast = parser.run(test_input)
    evaluator = Evaluator()
    evaluator.run(ast)


rpn = [
    'assert [2 3 -] == -1'
]


@pytest.mark.parametrize('test_input', rpn)
def test_rpn(test_input):
    interpreter = Interpreter()
    interpreter.run(test_input)


conditions_loops = [
    """
    if (1 < 2) {
        print 'If condition met!'
    } 
    """,
    """
    var i: float = 1.;
    while (i < 5.) {
        print 'While: ' + tostring(i);
        i = i + 1.
    }
    """
    """
    for (var i: int = 1; i < 10; i = i + 1) {
        print 'For: ' + tostring(i)
    } 
    """,
]


@pytest.mark.parametrize('test_input', conditions_loops)
def test_conditions_loops(test_input):
    interpreter = Interpreter()
    interpreter.run(test_input)
