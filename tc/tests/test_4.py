import logging
import pytest
from tc.interpreter import Interpreter

logging.basicConfig(level=logging.INFO)


function_def_program = """
    def nothing() { print 'nothing' }
    def something(): string { return 'something' }
    def really_something(x: string): string {
        nothing();
        return something() + x;
    }
    def two_things(thing1 : string, thing2 : string) : string {
        return thing1 + ' ' + thing2 + ' things'
    }

    print really_something(' out of nothing');
    print two_things('two', 'more')
"""


def test_function_def():
    interpreter = Interpreter()
    interpreter.run(function_def_program)


blocks_program = """
    var x: int = 1;
    {
        assert x + 1 == 2;
        var y: int = 2;
        { 
            assert x + y == 3;
        }
    }
    assert x == 1
"""


def test_blocks():
    interpreter = Interpreter()
    interpreter.run(blocks_program)


global_local_var_program = """
    var x: int = 1;
    {
        var y: int = 1;
        assert x + y == 2;
        { 
            var x: int = 2;
            assert x + y == 3;
            y = 100;
        }
        var x: int = 3;
        assert x + y == 103;
    }
    assert x == 1;
"""


def test_global_local_var():
    interpreter = Interpreter()
    interpreter.run(global_local_var_program)


function_call_programs = [
    """
        def gcd(a: int, b: int): int {
            if (a < b) {
                var tmp: int = a;
                a = b;
                b = tmp;
            }
            if (b == 0) {
                return a;
            }
    
            return gcd(b, a % b)
        }
    
        assert gcd(14, 21) == 7
    """,
    """
        var name: string = 'User';
    
        def fun(name: string) {
            print 'Hello from global scope, ' + name
        }
    
        {
            def fun(name: string) {
                print 'Hello from inner scope, ' + name
            }
    
            fun(name);  # inner
        }
    
        fun(name)       # global
    """
]


@pytest.mark.parametrize('test_input', function_call_programs)
def test_call(test_input):
    interpreter = Interpreter()
    interpreter.run(test_input)
