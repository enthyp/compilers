import logging
import pytest
from tc.parser import Parser

logging.basicConfig(level=logging.INFO)

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
