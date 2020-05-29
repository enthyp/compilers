import logging
import pytest
from tc.common import PrettyPrinter
from tc.interpreter import Interpreter
from tc.parser import Parser
from tc.optimization import AlgebraicOptimizer, ExpressionDAGOptimizer, RedundancyOptimizer
from tc.resolver import Resolver


logging.basicConfig(level=logging.INFO)


nested_call_programs = [
    """
    def fun(i: int) {
        var x: int = 3;
        
        # Multiplies by 3
        def fun(y: int) {
            print 'Called inner fun with y = ' + tostring(y);
            return x * y
        }

        return fun(i)
    }

    assert fun(2) == 6
    """,
    """
        var a : string = "global";
        {
          def showA() {
            print a;
          }
    
          showA();
          var a : string = "block";
          showA();
        }
    """
]


@pytest.mark.parametrize('test_input', nested_call_programs)
def test_nested_calls(test_input):
    interpreter = Interpreter()
    interpreter.run(test_input)


redundancy_test_programs = [
    (
        """
            var x: int = 1;
            var y: int = 2;
            print x
        """,
        'unused_variable_declaration'
    ),
    (
        """
            var y: int = 2;
            print y;
            y = 3
        """,
        'unused_variable_assignment'
    ),
    (
        """
            var b : int = 1;
            def useless() : int {
                return 1
            }
            var d : int = 100;
            print b + d
        """,
        'unused_function'
    ),
    (
        """
            var b : int = 1;
            def useful() : int {
                def useless() {
                    print 'I am completely useless!'
                }
                return 1
            }
            print b + useful()
        """,
        'unused_inner_function'
    ),
    (
        """
            var i : int = 1;
            var p : int = 1;
            var x : int = 2;
            
            while (i < 10) {
                print p;
                p = p * 2;
                x = x + 100;
                i = i + 1
            }
        """,
        'unused_loop_variable'
    ),
]


@pytest.mark.parametrize('test_input, name', redundancy_test_programs)
def test_redundancy_optimizations(test_input, name):
    parser = Parser()
    resolver = Resolver()
    optimizer = RedundancyOptimizer()

    ast = parser.run(test_input)
    resolver.run(ast)
    ast = optimizer.run(ast)

    pp = PrettyPrinter()
    pp.run(ast, f'out/redundancy_opt_{name}', view=False)


common_subexpression_test_programs = [
    (
        """
            var a : int = 3;
            var b : int = 1;
            var c : int = 10;
            var l : int = b - c;
            var d : int = 100;
            var x : int = (b - c) * a + (b - c) * d + a;
        """,
        'b-c'
    ),
    (
        """
            var b : int = 2;
            var c : int = 4;
            var a : int = b + c;
            var d : int = 8;
            b = a - d;
            c = b + c;
            d = a - d;
        """,
        'a-d_overwrite'
    ),
    (
        """
            var i : int = 1;
            var x : bool = i < 10;
            
            while (i < 10) {
                x = i < 10;
                var tmp : int = i * -1;
                i = i + 2;
                print tmp
            }
        """,
        'i_loop'
    )
]


@pytest.mark.parametrize('test_input, name', common_subexpression_test_programs)
def test_cs_optimizations(test_input, name):
    parser = Parser()
    resolver = Resolver()
    optimizer = ExpressionDAGOptimizer()  # TODO: i_loop

    ast = parser.run(test_input)
    resolver.run(ast)
    ast = optimizer.run(ast)

    pp = PrettyPrinter()
    pp.run(ast, f'out/common_subexpr_opt_{name}', view=False)


algebraic_test_programs = [
    (
        """
            var x: int = 1 + 0;
            x = x * 1;
            x = 0 + x;
            x = x ** 1;
            x = 1 - 0
        """,
        'simple'
    )
]


@pytest.mark.parametrize('test_input, name', algebraic_test_programs)
def test_algebraic_optimizations(test_input, name):
    parser = Parser()
    resolver = Resolver()
    optimizer = AlgebraicOptimizer()

    ast = parser.run(test_input)
    resolver.run(ast)
    ast = optimizer.run(ast)

    pp = PrettyPrinter()
    pp.run(ast, f'out/algebraic_opt_{name}', view=True)
