import logging
import pytest
from tc.common import PrettyPrinter
from tc.interpreter import Evaluator, Interpreter
from tc.parser import Parser

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
    pp.run(ast, 'out/test', view=True)
