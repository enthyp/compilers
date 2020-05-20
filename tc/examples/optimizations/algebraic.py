from tc import Parser, PrettyPrinter
from tc.optimization import AlgebraicOptimizer


example1 = """
    var x : int = 1;
    x = x 1 *;
    x = x 0 +;
    x = x 1 ^;
    x = 1 0 -
"""


def run(example, name):
    parser = Parser()
    ast_root = parser.run(example)

    optimizer = AlgebraicOptimizer()
    ast_root = optimizer.run(ast_root)

    pprint = PrettyPrinter()
    pprint.run(ast_root, f'out/{name}', view=True)


run(example1, 'a_opt')
