from z3 import *
from ChironAST import ChironAST
from math import cos, sin, pi
from fractions import Fraction
from z3 import z3util

_MULT15_VALUES = {
    deg: (Fraction(cos(deg * pi / 180)).limit_denominator(10**9),
          Fraction(sin(deg * pi / 180)).limit_denominator(10**9))
    for deg in range(0, 360, 15)
}

def linearized_trig_move(x, y, h, delta, forward=True):
    delta_real = ToReal(delta) if delta.sort() == IntSort() else delta
    x_expr = x
    y_expr = y
    for deg in range(345, -1, -15):
        cos_f, sin_f = _MULT15_VALUES[deg]
        cos_v = RealVal(f"{cos_f.numerator}/{cos_f.denominator}")
        sin_v = RealVal(f"{sin_f.numerator}/{sin_f.denominator}")
        dx = delta_real * cos_v
        dy = delta_real * sin_v
        if not forward:
            dx = -dx
            dy = -dy
        x_expr = If(h == RealVal(deg), x + dx, x_expr)
        y_expr = If(h == RealVal(deg), y + dy, y_expr)
    return x_expr, y_expr, BoolVal(True)


def _is_int_literal(val):
    return isinstance(val, int) or (isinstance(val, float) and val.is_integer())

def is_multiple_of_15(expr, env):
    if isinstance(expr, ChironAST.Value):
        if isinstance(expr, ChironAST.Num):
            if _is_int_literal(expr.val):
                if int(expr.val) % 15 == 0:
                    return True
                elif int(expr.val) % 15 != 0:
                    return False
            else:
                return None
        elif isinstance(expr, ChironAST.Var):
            return env.get(expr.varname[1:], None)
    elif isinstance(expr, ChironAST.ArithExpr):
        if isinstance(expr, ChironAST.BinArithOp):
            lexpr = expr.lexpr
            rexpr = expr.rexpr
            l_ret = is_multiple_of_15(lexpr, env)
            r_ret = is_multiple_of_15(rexpr, env)
            if isinstance(expr, ChironAST.Sum) or isinstance(expr, ChironAST.Diff) :
                if (l_ret is not None) and (r_ret is not None):
                    if (l_ret is True) or (r_ret is True):
                        return (l_ret and r_ret)
                    else:
                        return None
                else:
                    return None
            elif isinstance(expr, ChironAST.Mult):
                if (l_ret is True) and (r_ret is True):
                    return True
                else:
                    return None
            else:
                return None
        elif isinstance(expr, ChironAST.UMinus):
            return is_multiple_of_15(expr.expr, env)
    else:
        return None

def build_successors(ir):
    n = len(ir)
    succs = [[] for _ in range(n)]
    for i, (instr, jump_target) in enumerate(ir):
        if isinstance(instr, ChironAST.ConditionCommand):
            # true branch
            if i + 1 < n:
                succs[i].append(i + 1)
            # false branch
            j = i + jump_target
            if 0 <= j < n:
                succs[i].append(j)
        else:
            if i + 1 < n:
                succs[i].append(i + 1)
    return succs

def build_predecessors(succs):
    preds = [[] for _ in range(len(succs))]
    for i, successors in enumerate(succs):
        for j in successors:
            preds[j].append(i)
    return preds

def join_envs(env_list):
    common_keys = set(env_list[0].keys())
    for env in env_list[1:]:
        common_keys.intersection_update(env.keys())
    env_out = {}
    for key in common_keys:
        if all(env[key] is True for env in env_list):
            env_out[key] = True
    return env_out

def transfer_env(instr, env_in):
    if isinstance(instr, ChironAST.AssignmentCommand):
        env_out = env_in.copy()
        lvar = instr.lvar
        rexpr = instr.rexpr
        if (is_multiple_of_15(rexpr, env_in) is True):
            env_out[lvar.varname[1:]] = True
        else:
            env_out.pop(lvar.varname[1:], None)
        return env_out
    else:
        return env_in.copy()
    
def compute_env_in(ir):
    succs = build_successors(ir)
    preds = build_predecessors(succs)
    n = len(ir)
    env_in = [None] * n
    env_in[0] = {}
    env_out = [None] * n
    worklist = [0]

    while worklist:
        i = worklist.pop()
        instr, _ = ir[i]
        env_out[i] = transfer_env(instr, env_in[i])
        for s in succs[i]:
            incoming = [env_out[p] for p in preds[s] if env_out[p] is not None]
            joined = join_envs(incoming) if incoming else {}
            if env_in[s] != joined:
                env_in[s] = joined
                worklist.append(s)

    return env_in

def turn_safe(ir):
    env_in = compute_env_in(ir)
    turn_safe_map = [False] * len(ir)
    for i, (instr, _) in enumerate(ir):
        if isinstance(instr, ChironAST.MoveCommand):
            direction = instr.direction
            if direction in ["left", "right"]:
                env = env_in[i] or {}
                if (is_multiple_of_15(instr.expr, env) is True):
                    turn_safe_map[i] = True
    return turn_safe_map

def is_all_turn_safe(turn_safe_map, ir):
    for i, (instr, _) in enumerate(ir):
        if isinstance(instr, ChironAST.MoveCommand):
            direction = instr.direction
            if direction in ["left", "right"]:
                if turn_safe_map[i] is not True:
                    return False
    return True