from tc import Parser, PrettyPrinter
from tc.optimizers import ExpressionDAGOptimizer


example = """
    var a : int = 3;
    var b : int = 1;
    var c : int = 10;
    var l : int = b c -;
    var d : int = 100;
    var x : int = b c - a * b c - d * + a +;
    return x
"""

parser = Parser()
ast_root = parser.run(example)

optimizer = ExpressionDAGOptimizer()
optimizer.run(ast_root)

pprint = PrettyPrinter()
pprint.run(ast_root, 'out/fib', view=True)
