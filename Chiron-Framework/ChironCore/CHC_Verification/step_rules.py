from init_fixed_point import *
import sys
from z3 import *
from ChironAST import ChironAST
from math import cos, sin, pi
from fractions import Fraction

_MULT15_VALUES = {
    deg: (Fraction(cos(deg * pi / 180)).limit_denominator(10**9),
          Fraction(sin(deg * pi / 180)).limit_denominator(10**9))
    for deg in range(0, 360, 15)
}

def cos_sin_exact_z3(h, i):
    cos_expr = RealVal(0)
    sin_expr = RealVal(0)
    for deg in range(345, -1, -15):
        cos_f, sin_f = _MULT15_VALUES[deg]
        cos_expr = If(h == RealVal(deg),
                      RealVal(f"{cos_f.numerator}/{cos_f.denominator}"),
                      cos_expr)
        sin_expr = If(h == RealVal(deg),
                      RealVal(f"{sin_f.numerator}/{sin_f.denominator}"),
                      sin_expr)
    return cos_expr, sin_expr, BoolVal(True)

def normalize_heading(h):
    result = If(h >= RealVal(360), h - RealVal(360), h)
    result = If(result < RealVal(0), result + RealVal(360), result)
    return result

def chiron_expr_to_z3(expr, fp, Inv, state, next_state, symbol_table, counter_table):
    if isinstance(expr, ChironAST.ArithExpr):
        if isinstance(expr, ChironAST.BinArithOp):
            lexpr = expr.lexpr
            rexpr = expr.rexpr
            if isinstance(expr, ChironAST.Sum):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) + chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.Diff):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) - chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.Mult):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) * chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.Div):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) / chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            else:
                print(f"Error: Unrecognized BinArithOp type: {type(expr)}")
                sys.exit(1)
        elif isinstance(expr, ChironAST.UnaryArithOp):
            if isinstance(expr, ChironAST.UMinus):
                lexpr = expr.expr
                return -chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            else:
                print(f"Error: Unrecognized UnaryArithOp type: {type(expr)}")
                sys.exit(1)
        else:
            print(f"Error: Unrecognized ArithExpr type: {type(expr)}")
            sys.exit(1)
    elif isinstance(expr, ChironAST.BoolExpr):
        if isinstance(expr, ChironAST.BinCondOp):
            lexpr = expr.lexpr
            rexpr = expr.rexpr
            if isinstance(expr, ChironAST.AND):
                return And(chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table), chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table))
            elif isinstance(expr, ChironAST.OR):
                return Or(chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table), chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table))
            elif isinstance(expr, ChironAST.LT):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) < chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.GT):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) > chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.LTE):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) <= chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.GTE):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) >= chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.EQ):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) == chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            elif isinstance(expr, ChironAST.NEQ):
                return chiron_expr_to_z3(lexpr, fp, Inv, state, next_state, symbol_table, counter_table) != chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
            else:
                print(f"Error: Unrecognized BinCondOp type: {type(expr)}")
                sys.exit(1)
        elif isinstance(expr, ChironAST.NOT):
            expr = expr.expr
            return Not(chiron_expr_to_z3(expr, fp, Inv, state, next_state, symbol_table, counter_table))
        elif isinstance(expr, ChironAST.PenStatus):
            return state[4]
        elif isinstance(expr, ChironAST.BoolTrue):
            return BoolVal(True)
        elif isinstance(expr, ChironAST.BoolFalse):
            return BoolVal(False)
        else:
            print(f"Error: Unrecognized BoolExpr type: {type(expr)}")
            sys.exit(1)
    elif isinstance(expr, ChironAST.Value):
        if isinstance(expr, ChironAST.Num):
            return RealVal(expr.val)
        elif isinstance(expr, ChironAST.Var):
            var_name = expr.varname
            var_name = var_name[1:]
            if var_name in symbol_table:
                return symbol_table[var_name]['z3_var']
            elif var_name in counter_table:
                return counter_table[var_name]['z3_var']
            else:
                print("Error: Variable " + var_name + " not found in symbol table.")
                sys.exit(1)
        else:
            print(f"Error: Unrecognized Value type: {type(expr)}")
            sys.exit(1)
    else:
        print(f"Error: Unrecognized expression type: {type(expr)}")
        sys.exit(1)

def chiron_command_to_z3_rule(i, instr, jump_target, fp, Inv, state, next_state, symbol_table, counter_table):

    current_state = (IntVal(i), *state[1:])

    if isinstance(instr, ChironAST.AssignmentCommand):
        next_pc = IntVal(i+1)
        next_state_xcor = state[1]
        next_state_ycor = state[2]
        next_state_heading = state[3]
        next_state_pendown = state[4]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        lvar = instr.lvar
        rexpr = instr.rexpr
        expr_z3 = chiron_expr_to_z3(rexpr, fp, Inv, state, next_state, symbol_table, counter_table)
        if isinstance(lvar, ChironAST.Var):
            var_name = lvar.varname
            var_name = var_name[1:] # Strip the colon
            if var_name in symbol_table:
                var_index = list(symbol_table.keys()).index(var_name)
                next_state_user_vars[var_index] = expr_z3
                next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
                rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
                return rule, None
            elif var_name in counter_table:
                counter_index = list(counter_table.keys()).index(var_name)
                next_state_user_vars[len(symbol_table) + counter_index] = expr_z3
                next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
                rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
                return rule, None
            else:
                print("Error: Variable " + var_name + " not found in symbol table.")
                sys.exit(1)
        else:
            print("Error: Left-hand side of assignment is not a variable.")
            sys.exit(1)

    elif isinstance(instr, ChironAST.ConditionCommand) or isinstance(instr, ChironAST.AssertCommand):
        cond = instr.cond
        cond = chiron_expr_to_z3(cond, fp, Inv, state, next_state, symbol_table, counter_table)

        next_pc_true = IntVal(i+1)
        next_state_xcor_true = state[1]
        next_state_ycor_true = state[2]
        next_state_heading_true = state[3]
        next_state_pendown_true = state[4]
        next_state_user_vars_true = [state[j] for j in range(5, len(state))]
        next_state_tuple_true = (next_pc_true, next_state_xcor_true, next_state_ycor_true, next_state_heading_true, next_state_pendown_true, *next_state_user_vars_true)
        rule_true = Implies(And(Inv(*current_state), cond), Inv(*next_state_tuple_true))

        if isinstance(instr, ChironAST.ConditionCommand):
            next_pc_false = IntVal(i + jump_target)
            next_state_xcor_false = state[1]
            next_state_ycor_false = state[2]
            next_state_heading_false = state[3]
            next_state_pendown_false = state[4]
            next_state_user_vars_false = [state[j] for j in range(5, len(state))]
            next_state_tuple_false = (next_pc_false, next_state_xcor_false, next_state_ycor_false, next_state_heading_false, next_state_pendown_false, *next_state_user_vars_false)
            rule_false = Implies(And(Inv(*current_state), Not(cond)), Inv(*next_state_tuple_false))
            return rule_true, rule_false

        else:
            rule_false = Implies(And(Inv(*current_state), Not(cond)), BoolVal(False))
            return rule_true, rule_false
        
    elif isinstance(instr, ChironAST.MoveCommand):
        next_pc = IntVal(i+1)
        next_state_pendown = state[4]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        direction = instr.direction
        expr = instr.expr
        expr_z3 = chiron_expr_to_z3(expr, fp, Inv, state, next_state, symbol_table, counter_table)

        if direction == "forward":
            cos_h, sin_h, trig_constraints = cos_sin_exact_z3(state[3], i)
            next_state_xcor = state[1] + expr_z3 * cos_h
            next_state_ycor = state[2] + expr_z3 * sin_h
            next_state_heading = state[3]
        elif direction == "backward":
            cos_h, sin_h, trig_constraints = cos_sin_exact_z3(state[3], i)
            next_state_xcor = state[1] - expr_z3 * cos_h
            next_state_ycor = state[2] - expr_z3 * sin_h
            next_state_heading = state[3]
        elif direction == "left":
            trig_constraints = BoolVal(True)
            next_state_xcor = state[1]
            next_state_ycor = state[2]
            next_state_heading = normalize_heading(state[3] + expr_z3)
        elif direction == "right":
            trig_constraints = BoolVal(True)
            next_state_xcor = state[1]
            next_state_ycor = state[2]
            next_state_heading = normalize_heading(state[3] - expr_z3)
        else:
            print("Error: Invalid direction in MoveCommand.")
            sys.exit(1)

        next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
        rule = Implies(And(Inv(*current_state), trig_constraints), Inv(*next_state_tuple))
        return rule, None

    elif isinstance(instr, ChironAST.PenCommand):
        next_pc = IntVal(i+1)
        next_state_xcor = state[1]
        next_state_ycor = state[2]
        next_state_heading = state[3]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        status = instr.status
        if status == "pendown":
            next_state_pendown = BoolVal(True)
        elif status == "penup":
            next_state_pendown = BoolVal(False)
        else:
            print("Error: Invalid pen status in PenCommand.")
            sys.exit(1)

        next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
        rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
        return rule, None

    elif isinstance(instr, ChironAST.GotoCommand):
        next_pc = IntVal(i+1)
        next_state_heading = state[3]
        next_state_pendown = state[4]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        xcor_expr = chiron_expr_to_z3(instr.xcor, fp, Inv, state, next_state, symbol_table, counter_table)
        ycor_expr = chiron_expr_to_z3(instr.ycor, fp, Inv, state, next_state, symbol_table, counter_table)

        next_state_xcor = ToReal(xcor_expr) if xcor_expr.sort() == IntSort() else xcor_expr
        next_state_ycor = ToReal(ycor_expr) if ycor_expr.sort() == IntSort() else ycor_expr

        next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
        rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
        return rule, None

    elif isinstance(instr, ChironAST.NoOpCommand):
        next_pc = IntVal(i+1)
        next_state_xcor = state[1]
        next_state_ycor = state[2]
        next_state_heading = state[3]
        next_state_pendown = state[4]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
        rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
        return rule, None

    elif isinstance(instr, ChironAST.PauseCommand):
        next_pc = IntVal(i+1)
        next_state_xcor = state[1]
        next_state_ycor = state[2]
        next_state_heading = state[3]
        next_state_pendown = state[4]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
        rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
        return rule, None
    
    else:
        print("Error: Unrecognized instruction type.")
        sys.exit(1)
        


def add_step_rules_to_fixed_point(ir, mode, param=None):
    fp, Inv, state, next_state, symbol_table, counter_table = z3_fixed_point_object_with_start_state_set(ir, mode, params=param)

    print("\n========== Step 4 ==========")

    for i, stmt in enumerate(ir):
        instr = stmt[0]
        jump_target = stmt[1]
        rule_true, rule_false = chiron_command_to_z3_rule(i, instr, jump_target, fp, Inv, state, next_state, symbol_table, counter_table)
        rule_true_vars = z3util.get_vars(rule_true)
        fp.rule(ForAll(rule_true_vars, rule_true))
        print(f"Added rule for instruction at line {i}: {rule_true}")
        if rule_false is not None:
            rule_false_vars = z3util.get_vars(rule_false)
            fp.rule(ForAll(rule_false_vars, rule_false))
            print(f"Added rule for instruction at line {i} (false branch): {rule_false}")

        
    print("Step rules added to fixedpoint object.")

    return fp, Inv, state, next_state, symbol_table, counter_table
