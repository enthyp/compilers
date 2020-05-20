from tc import Parser, PrettyPrinter
from tc.optimization import RedundancyOptimizer


example1 = """
    var b : int = 1;
    var c : int = 10;
    var d : int = 100;
    print b d +
"""

example2 = """
    var b : int = 1;
    def useless() : int {
        return 1
    }
    var d : int = 100;
    print b d +
"""

example3 = """
    var b : int = 1;
    def fun() : int {
        var x : int = b;
        return 1
    }
    var d : int = 100;
    print b d + fun() *
"""


def run(example, name):
    parser = Parser()
    ast_root = parser.run(example)

    optimizer = RedundancyOptimizer()
    ast_root = optimizer.run(ast_root)

    pprint = PrettyPrinter()
    pprint.run(ast_root, f'out/{name}', view=True)


run(example3, 'redundancy3')
