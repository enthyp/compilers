from pprint import pprint
from tc import Parser
from tc.optimization.redundancy import GenKillBuilder

example1 = """
    var x : int = 1;
    var y : int = 2;
    x = 10;
"""

example2 = """
    var i : int = 1;
    var j : int = 10;
    var a : int = 100;
    
    while (i j - 10 <) {
        i = i 1 +;
        j = j 1 -;
        if (i j - 5 <) {
            a = 1000;
        }
        if (i j - 5 >=) {
            i = 10;
        }
    }
"""

example3 = """
    var a : int = 1;
    
    def fun(p : int) {
        a = 10;
        return p
    }

    fun(10)
"""


def run(example):
    parser = Parser()
    ast = parser.run(example)

    builder = GenKillBuilder()
    gen, kill = builder.run(ast)

    pprint(gen)
    pprint(kill)


run(example3)
