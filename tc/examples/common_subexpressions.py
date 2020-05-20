from tc import Parser, PrettyPrinter
from tc.optimization import ExpressionDAGOptimizer


example1 = """
    var a : int = 3;
    var b : int = 1;
    var c : int = 10;
    var l : int = b c -;
    var d : int = 100;
    var x : int = b c - a * b c - d * + a +;
    return x
"""

example2 = """
    var b : int = 2;
    var c : int = 4;
    var a : int = b c +;
    var d : int = 8;
    b = a d -;
    c = b c +;
    d = a d -;
"""

example3 = """
    var i : int = 1;
    var x : bool = i 10 <;
    
    while (i 10 <) {
        var tmp : int = i -1 *;
        i = i 2 +;
        print tmp
    }
"""


def run(example, name):
    parser = Parser()
    ast_root = parser.run(example)

    optimizer = ExpressionDAGOptimizer()
    optimizer.run(ast_root)

    pprint = PrettyPrinter()
    pprint.run(ast_root, f'out/{name}', view=True)


run(example1, 'csopt1')
run(example2, 'csopt2')
run(example3, 'while')
