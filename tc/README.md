# TC
The Throwaway Calculator is an interpreter for a simple language that resembles gnome-calculator 

### Examples
```python
from tc import Interpreter

function_call_program = """
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
"""


def test_call():
    interpreter = Interpreter()
    interpreter.run(function_call_program)
```

Can also run a REPL with `python examples/repl.py`

### HOWTO
`make install` to install into local env

`make test` to run test for all cases required during the labs
