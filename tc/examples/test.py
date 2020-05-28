from tc import Interpreter, Parser, PrettyPrinter


# Correct use examples.
interpreter = Interpreter()

example_if = """
var a : int = 3;
if (a < 4) {
    print (a - 7)
}
"""
example_while = """
    var i : int = 1;
    while (i < 10) {
        var tmp : int = i * -1;
        i = i + 2;
        print tmp
    }
"""
example_for = """
    for (var x : int = 2; x > 0; x = x - 1) {
        print x
    }
"""
example_overloading = """
    var x : string = 'a';
    print x + 'lamakota';
    var y : int = 0;
    print y + 12
"""
example_int_to_float = """
    var x : int = -1;
    var y : float = tofloat(x);
    print y 
"""
example_function = """
    def sayHello(name : string) {
        print 'Hello, ' + name
    }
    
    sayHello('good man.')
"""
example_nested_call = """
    def TheAnswer(): int {
        return 42
    }
    def relieve(name : string) {
        var Answer : string = tostring(TheAnswer());
        print 'Hello, ' + name;
        print 'The answer you need so desperately is ' + Answer
    }

    relieve('good man.')
"""
example_fib = """
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
    
    print fib(n)
"""

examples = [
    example_if,
    example_while,
    example_for,
    example_overloading,
    example_int_to_float,
    example_function,
    example_nested_call,
    example_fib
]

for example in examples:
    print('Example: {}'.format(example))
    print('Result: ')
    interpreter.run(example)


# Tests for incorrect examples.
bad_types = """
    var x : string = 1
"""
bad_op_types = """
    var x : string = 'a';
    x + 1
"""
bad_fun_types = """
    def fun(s : string) : int {
        return 0
    };
    fun(1)
"""
bad_condition = """
    if (1 + 1) {
        print 2
    }
"""
bad_lvalue = """
    var x : string = '';
    '' = x + 'b'
"""

bad_examples = [
    bad_types,
    bad_op_types,
    bad_fun_types,
    bad_condition,
    bad_lvalue
]

for example in bad_examples:
    try:
        print('Bad example: {}'.format(example))
        interpreter.run(example)
    except:
        print('Raises.')  # should raise
    else:
        raise Exception('No exception occurred!')


# Visualize Fibonacci sequence program.
parser = Parser()
ast_root = parser.run(example_fib)
pprint = PrettyPrinter()
pprint.run(ast_root, 'out/fib', view=True)
