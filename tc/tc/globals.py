import math
from tc.common import Callable, CallableSignature, Environment, PolyCallableSignature, Type


def global_env():
    env = Environment(None)

    # Define some builtin functions
    env.define_fun('sin', Sin)
    env.define_fun('cos', Cos)
    env.define_fun('toint', ToInt())
    env.define_fun('tofloat', ToFloat())
    env.define_fun('tostring', ToString())
    return env

   
# Builtin functions 
# TODO: boolean conversions?
class MathFunction(Callable):
    def __init__(self, fun):
        self.fun = fun
        self.signature = PolyCallableSignature([
            CallableSignature([Type.INT], Type.FLOAT),
            CallableSignature([Type.FLOAT], Type.FLOAT),
        ])

    def call(self, evaluator, args):
        assert len(args) == 1
        arg = evaluator.visit(args[0])
        evaluator.env = Environment(enclosing=evaluator.env)
        try:
            return self.fun(arg)
        finally:
            evaluator.env = evaluator.env.enclosing


Sin = MathFunction(math.sin)
Cos = MathFunction(math.cos)


class ToInt(Callable):
    def __init__(self):
        self.signature = PolyCallableSignature([
            CallableSignature([Type.INT], Type.INT),
            CallableSignature([Type.FLOAT], Type.INT),
            CallableSignature([Type.STRING], Type.INT),
        ])

    def call(self, evaluator, args):
        assert len(args) == 1
        arg = evaluator.visit(args[0])
        evaluator.env = Environment(enclosing=evaluator.env)
        try:
            return int(arg)
        finally:
            evaluator.env = evaluator.env.enclosing


class ToFloat(Callable):
    def __init__(self):
        self.signature = PolyCallableSignature([
            CallableSignature([Type.INT], Type.FLOAT),
            CallableSignature([Type.FLOAT], Type.FLOAT),
            CallableSignature([Type.STRING], Type.FLOAT),
        ])

    def call(self, evaluator, args):
        assert len(args) == 1
        arg = evaluator.visit(args[0])
        evaluator.env = Environment(enclosing=evaluator.env)
        try:
            return float(arg)
        finally:
            evaluator.env = evaluator.env.enclosing


class ToString(Callable):
    def __init__(self):
        self.signature = PolyCallableSignature([
            CallableSignature([Type.INT], Type.STRING),
            CallableSignature([Type.FLOAT], Type.STRING),
            CallableSignature([Type.STRING], Type.STRING),
        ])

    def call(self, evaluator, args):
        assert len(args) == 1
        arg = evaluator.visit(args[0])
        evaluator.env = Environment(enclosing=evaluator.env)
        try:
            return str(arg)
        finally:
            evaluator.env = evaluator.env.enclosing
