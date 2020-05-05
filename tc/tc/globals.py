from tc.common import Callable, CallableSignature, Environment, PolyCallableSignature, Type


def global_env():
    env = Environment(None)

    # Define some builtin functions
    env.define_fun('toint', ToInt())
    env.define_fun('tofloat', ToFloat())
    env.define_fun('tostring', ToString())
    return env

   
# Builtin functions 
# TODO: boolean conversions?
class ToInt(Callable):
    def __init__(self):
        self.signature = PolyCallableSignature([
            CallableSignature([Type.INT], Type.INT),
            CallableSignature([Type.FLOAT], Type.INT),
            CallableSignature([Type.STRING], Type.INT),
        ])

    def call(self, evaluator, args):
        assert len(args) == 1
        return int(evaluator.visit(args[0]))


class ToFloat(Callable):
    def __init__(self):
        self.signature = PolyCallableSignature([
            CallableSignature([Type.INT], Type.FLOAT),
            CallableSignature([Type.FLOAT], Type.FLOAT),
            CallableSignature([Type.STRING], Type.FLOAT),
        ])

    def call(self, evaluator, args):
        assert len(args) == 1
        return float(evaluator.visit(args[0]))


class ToString(Callable):
    def __init__(self):
        self.signature = PolyCallableSignature([
            CallableSignature([Type.INT], Type.STRING),
            CallableSignature([Type.FLOAT], Type.STRING),
            CallableSignature([Type.STRING], Type.STRING),
        ])

    def call(self, evaluator, args):
        assert len(args) == 1
        return str(evaluator.visit(args[0]))

