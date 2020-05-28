import logging
import pytest
from tc.common import PrettyPrinter
from tc.interpreter import Evaluator, Interpreter
from tc.parser import Literal, Parser, VariableDeclaration
from tc.typecheck import Type

logging.basicConfig(level=logging.INFO)

function_def_program = """
    def gcd(a: int, b: int): int {
        if (a < b) {
            var tmp: int = a;
            a = b;
            b = a;
        }
        if (b == 1) {
            return a;
        }
        
        return gcd(b, b % a)
    }
    
    assert gcd(14, 21) == 3
"""

function_def_program = """
    def factorial(x: int): int {
        if (x == 0) {
            return 1;
        }
        return x * factorial(x - 1)
    }
    
    assert factorial(4) == 24
"""


def test_function_def():
    interpreter = Interpreter()
    interpreter.run(function_def_program)
