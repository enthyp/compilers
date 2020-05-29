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

### HOW TO
 * `make install` to install into local env
 * `make test` to run all required test cases
 * once installed command `tisi` enters REPL, `tisi filename` executes code from given file

### Features
* strong typing
* variable and function definitions
* proper name scoping
* lexical closures
* some optimizations: 
  * redundant code removal and reusing common
  subexpressions based on reaching definitions 
  * trivial algebraic optimizations
  
### Problems
* error handling sucks
* optimizations based on reaching definitions work most of the time but some corner cases have gone unhandled probably
