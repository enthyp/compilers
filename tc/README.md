# TC
The Throwaway Calculator is an interpreter for a simple language that resembles gnome-calculator 

### Examples
```python
from tc import Interpreter

euclid = """
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

fibonacci = """
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
    
    assert fib(n) == 89
"""

def test_call():
    interpreter = Interpreter()
    interpreter.run(euclid)
    interpreter.run(fibonacci)
```

Once `tc` is installed one can enter REPL with `tc-repl` command

### HOWTO
`make install` to install into local env

`make test` to run all required test cases
