import logging
from tc.interpreter import Interpreter

logging.basicConfig(level=logging.INFO)


nested_call_program = """
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
"""


def test_nested_call():
    interpreter = Interpreter()
    interpreter.run(nested_call_program)
