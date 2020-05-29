from tc import Parser, PrettyPrinter
from tc.optimization.redundancy import GenKillBuilder, InOutBuilder, RedundancyOptimizer


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

example4 = """
    var i : int = 1;
    while (i 10 <) {
        var tmp : int = i -1 *;
        i = i 2 +;
        print tmp
    }
"""

example5 = """
    var n : int = 10;
    
    def fib(n : int) : int {
        var a : int = 1;
        var b : int = 1;
        var i : int = 1;
        while (i n <) {
            print b;
            var tmp : int = a;
            a = b;
            b = tmp b +;
            i = i 1 +
        }
        return b
    }
    
    print fib(n)
"""

example6 = """
    var x: int = 1;
    {
        var y: int = 1;
        print x y +;            # 2
        { 
            var x: int = 2;
            print x y +;        # 3
            y = 100;
        }
        var x: int = 3;
        print x y +;            # 103
    }
    print x;                    # 1
"""

example7 = """
    var name: string = 'User';

    def fun(name: string) {
        print 'Hello from global scope, ' name +
    }

    {
        def fun2(name: string) {
            print 'Hello from inner scope, ' name +
        }

        fun(name);  # inner
    }

    fun(name)       # global
"""

example8 = """
    def useful() : int {
        print "totally useless";
        return 1
    }
    var x : int = 1;
    
    # certainly should remain here
    useful();  
    
    # guess it should stay - may be called for side effects, forgot to use return value
    var y : int = useful();  
    print x;
    y = y 2 +
"""

example9 = """
    def fun(i: int) {
        var x: int = 3;
        
        # Multiplies by 3
        def fun(y: int) {
            print 'Called inner fun with y = ' tostring(y) +;
            return x y *
        }

        return fun(i);
    }

    print fun(2)
"""


def run(example, name):
    parser = Parser()
    ast_root = parser.run(example)

    # pprint = PrettyPrinter()
    # pprint.run(ast_root, f'out/{name}1', view=True)

    # optimizer = RedundancyOptimizer()
    # ast_root = optimizer.run(ast_root)

    builder = GenKillBuilder()
    gen, kill = builder.run(ast_root)

    # pprint(gen)
    # pprint(kill)

    io_builder = InOutBuilder(gen, kill)
    in_sets, out_sets = io_builder.run(ast_root)

    import pprint as pp
    # pp.pprint(in_sets)
    # pp.pprint(out_sets)

    optimizer = RedundancyOptimizer()
    ast_root = optimizer.run(ast_root)
    pprint = PrettyPrinter()
    pprint.run(ast_root, f'out/{name}', view=True)


# run(example1, 'redundancy_1')
# run(example2, 'redundancy_2')
# run(example3, 'redundancy3')
# run(example4, 'redundancy_while')
# run(example5, 'redundancy_fib')
# run(example6, 'redundancy_blocks')
# run(example7, 'redundancy_fun')
# run(example8, 'redundancy_fun2')
run(example9, 'redundancy_nested_fun')
