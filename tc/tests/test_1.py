import logging
import pytest
from tc.interpreter import Evaluator
from tc.parser import Parser, BinaryExpr, Call, Literal, Variable
from tc.typecheck import Type


numbers = [
    ('1', 1),
    ('-1', -1),
    ('.1', 0.1),
    ('-.1', -0.1),
    ('1.', 1.0),
    ('-1.', -1.0),
    ('1.1', 1.1),
    ('-1.1', -1.1),
]


@pytest.mark.parametrize('test_input, test_value', numbers)
def test_numbers_lexing(test_input, test_value):
    parser = Parser()
    tokens = parser.run(test_input)
    assert type(tokens[0].value) == type(test_value)
    assert tokens[0].value == test_value


functions = [
    ('sin 23', [Call('sin', [Literal(23, Type.INT)])]),
    ('sin sin 12', [Call('sin', [Call('sin', [Literal(12, Type.INT)])])]),
    ('sin 23 sin 23', [BinaryExpr(Call('sin', [Literal(23, Type.INT)]), '*', Call('sin', [Literal(23, Type.INT)]))]),
    ('sin x', [Call('sin', [Variable('x')])]),
    ('sin(x)', [Call('sin', [Variable('x')])])
]


@pytest.mark.parametrize('test_input, test_tokens', functions)
def test_function_lexing(test_input, test_tokens):
    parser = Parser()
    tokens = parser.run(test_input)
    assert tokens == test_tokens


power_op = [
    'assert 2 ** 3 == 8',
    'assert 2 ** 3 * 4 == 32',
    'assert 2 ** -1 == 0.5',
    'assert -2 ** 2 == 4'
]


@pytest.mark.parametrize('test_input', power_op)
def test_power_op(test_input):
    parser = Parser()
    ast = parser.run(test_input)
    evaluator = Evaluator()
    evaluator.run(ast)
