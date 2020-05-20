from tc import Parser, PrettyPrinter
from tc.optimization import RedundancyOptimizer


example1 = """
    var b : int = 1;
    var c : int = 10;
    var d : int = 100;
    return b d +
"""

parser = Parser()
ast_root = parser.run(example1)

optimizer = RedundancyOptimizer()
ast_root = optimizer.run(ast_root)

pprint = PrettyPrinter()
pprint.run(ast_root, 'out/redundancy1', view=True)
