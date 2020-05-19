from tc import Interpreter

interpreter = Interpreter()
var_blocks = """
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

ci_block = """
    var a : string = "global";
    {
      def showA() {
        print a;
      }
    
      showA();
      var a : string = "block";
      showA();
    }
"""

fun_blocks = """
    var name: string = 'User';

    def fun(name: string) {
        print 'Hello from global scope, ' name +
    }

    {
        def fun(name: string) {
            print 'Hello from inner scope, ' name +
        }
        
        fun(name);  # inner
    }

    fun(name)       # global
"""

nested_fun = """
    def fun(i: int) {
        var x: int = 3;
        
        # Multiplies by 3
        def fun(y: int) {
            print 'Called inner fun with y = ' tostring(y) +;
            return x y *
        }

        return fun(i)
    }

    print fun(2)
"""

programs = [
    var_blocks,
    ci_block,
    fun_blocks,
    nested_fun
]

for program in programs:
    interpreter.run(program)
    print()

