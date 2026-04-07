from init_fixed_point import *
import sys
from z3 import *
from z3 import z3util
from ChironAST import ChironAST
from optimization_helpers import *
from optimization_helpers import _MULT15_VALUES

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
    k = ToInt(h / RealVal(360))
    return h - RealVal(360) * ToReal(k)

def _env_from_state(state, symbol_table, counter_table):
    env = {}
    names = list(symbol_table.keys())
    for idx, name in enumerate(names):
        env[name] = state[5 + idx]
    ctr_names = list(counter_table.keys())
    base = 5 + len(names)
    for idx, name in enumerate(ctr_names):
        env[name] = state[base + idx]
    return env

def chiron_expr_to_z3_env(expr, env):
    if isinstance(expr, ChironAST.Num):
        return RealVal(expr.val)
    if isinstance(expr, ChironAST.Var):
        return env[expr.varname[1:]]
    if isinstance(expr, ChironAST.Sum):
        return chiron_expr_to_z3_env(expr.lexpr, env) + chiron_expr_to_z3_env(expr.rexpr, env)
    if isinstance(expr, ChironAST.Diff):
        return chiron_expr_to_z3_env(expr.lexpr, env) - chiron_expr_to_z3_env(expr.rexpr, env)
    if isinstance(expr, ChironAST.Mult):
        return chiron_expr_to_z3_env(expr.lexpr, env) * chiron_expr_to_z3_env(expr.rexpr, env)
    if isinstance(expr, ChironAST.Div):
        return chiron_expr_to_z3_env(expr.lexpr, env) / chiron_expr_to_z3_env(expr.rexpr, env)
    if isinstance(expr, ChironAST.UMinus):
        return -chiron_expr_to_z3_env(expr.expr, env)
    raise Exception("Unsupported expr in summarizer")

def apply_instr_state_only(instr, fp, Inv, state, next_state, symbol_table, counter_table, i):
    next_state_xcor = state[1]
    next_state_ycor = state[2]
    next_state_heading = state[3]
    next_state_pendown = state[4]
    next_state_user_vars = [state[j] for j in range(5, len(state))]

    bad_heading_cond = None

    if isinstance(instr, ChironAST.AssignmentCommand):
        lvar = instr.lvar
        rexpr = instr.rexpr
        env = _env_from_state(state, symbol_table, counter_table)
        expr_z3 = chiron_expr_to_z3_env(rexpr, env)
        if isinstance(lvar, ChironAST.Var):
            var_name = lvar.varname[1:]
            if var_name in symbol_table:
                var_index = list(symbol_table.keys()).index(var_name)
                next_state_user_vars[var_index] = expr_z3
            elif var_name in counter_table:
                counter_index = list(counter_table.keys()).index(var_name)
                next_state_user_vars[len(symbol_table) + counter_index] = expr_z3
            else:
                print("Error: Variable " + var_name + " not found in symbol table.")
                sys.exit(1)
        else:
            print("Error: Left-hand side of assignment is not a variable.")
            sys.exit(1)

    elif isinstance(instr, ChironAST.MoveCommand):
        direction = instr.direction
        expr = instr.expr
        env = _env_from_state(state, symbol_table, counter_table)
        expr_z3 = chiron_expr_to_z3_env(expr, env)

        if direction == "forward":
            cos_h, sin_h, _ = cos_sin_exact_z3(state[3], i)
            next_state_xcor = state[1] + expr_z3 * cos_h
            next_state_ycor = state[2] + expr_z3 * sin_h
        elif direction == "backward":
            cos_h, sin_h, _ = cos_sin_exact_z3(state[3], i)
            next_state_xcor = state[1] - expr_z3 * cos_h
            next_state_ycor = state[2] - expr_z3 * sin_h
        elif direction == "left":
            next_state_heading = normalize_heading(state[3] + expr_z3)
            bad_heading_cond = Not(heading_on_grid(next_state_heading))
        elif direction == "right":
            next_state_heading = normalize_heading(state[3] - expr_z3)
            bad_heading_cond = Not(heading_on_grid(next_state_heading))
        else:
            print("Error: Invalid direction in MoveCommand.")
            sys.exit(1)

    elif isinstance(instr, ChironAST.PenCommand):
        status = instr.status
        if status == "pendown":
            next_state_pendown = BoolVal(True)
        elif status == "penup":
            next_state_pendown = BoolVal(False)
        else:
            print("Error: Invalid pen status in PenCommand.")
            sys.exit(1)

    elif isinstance(instr, ChironAST.GotoCommand):
        env = _env_from_state(state, symbol_table, counter_table)
        xcor_expr = chiron_expr_to_z3_env(instr.xcor, env)
        ycor_expr = chiron_expr_to_z3_env(instr.ycor, env)
        next_state_xcor = ToReal(xcor_expr) if xcor_expr.sort() == IntSort() else xcor_expr
        next_state_ycor = ToReal(ycor_expr) if ycor_expr.sort() == IntSort() else ycor_expr

    elif isinstance(instr, ChironAST.NoOpCommand):
        pass

    elif isinstance(instr, ChironAST.PauseCommand):
        pass

    elif isinstance(instr, ChironAST.ConditionCommand) or isinstance(instr, ChironAST.AssertCommand):
        print("Error: apply_instr_state_only called on conditional/assert.")
        sys.exit(1)

    else:
        print("Error: Unrecognized instruction type.")
        sys.exit(1)

    next_state_tuple = (next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
    return next_state_tuple, bad_heading_cond

def summarize_loop_effect(ir, loop_desc, fp, Inv, state, next_state, symbol_table, counter_table, turn_safe_map):
    (init_idx, cond_idx, body_start, body_end, dec_idx, back_idx, exit_idx, counter_name, loop_count) = loop_desc

    if loop_count > MAX_SUMMARIZE_ITERATIONS:
        return None, []

    bad_rules = []
    current_state = state

    init_instr, init_jump_target = ir[init_idx]
    current_state_no_pc, bad_rule = apply_instr_state_only(init_instr, fp, Inv, current_state, next_state, symbol_table, counter_table, init_idx)
    if (bad_rule is not None) and (turn_safe_map is None or not turn_safe_map[init_idx]):
        bad_rules.append((bad_rule, current_state_no_pc, init_idx + 1))
    current_state = (state[0], *current_state_no_pc)

    instr_in_loop_body = [(j, ir[j][0]) for j in range(body_start, body_end + 1)]
    dec_instr = ir[dec_idx][0]

    for _ in range(loop_count):
        for j, instr in instr_in_loop_body:
            current_state_no_pc, bad_rule = apply_instr_state_only(instr, fp, Inv, current_state, next_state, symbol_table, counter_table, j)
            if (bad_rule is not None) and (turn_safe_map is None or not turn_safe_map[j]):
                bad_rules.append((bad_rule, current_state_no_pc, j + 1))
            current_state = (state[0], *current_state_no_pc)
        
        current_state_no_pc, bad_rule = apply_instr_state_only(dec_instr, fp, Inv, current_state, next_state, symbol_table, counter_table, dec_idx)
        if (bad_rule is not None) and (turn_safe_map is None or not turn_safe_map[dec_idx]):
            bad_rules.append((bad_rule, current_state_no_pc, dec_idx + 1))
        current_state = (state[0], *current_state_no_pc)
    
    return current_state_no_pc, bad_rules

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

def chiron_command_to_z3_rule(i, instr, jump_target, fp, Inv, BadHeading, state, next_state, symbol_table, counter_table, optimization_level, turn_safe_map):

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
                return rule, None, None
            elif var_name in counter_table:
                counter_index = list(counter_table.keys()).index(var_name)
                next_state_user_vars[len(symbol_table) + counter_index] = expr_z3
                next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
                rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
                return rule, None, None
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
            return rule_true, rule_false, None

        else:
            rule_false = Implies(And(Inv(*current_state), Not(cond)), BoolVal(False))
            return rule_true, rule_false, None
        
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

        bad_rule = None
        if direction in ["left", "right"] :
            if (optimization_level == OptimizationLevel.BASIC) and turn_safe_map and (turn_safe_map[i] is True):
                pass
            else:
                bad_rule = Implies(And(Inv(*current_state), trig_constraints, Not(heading_on_grid(next_state_heading))), BadHeading(*next_state_tuple))
        return rule, None, bad_rule

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
        return rule, None, None

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
        return rule, None, None

    elif isinstance(instr, ChironAST.NoOpCommand):
        next_pc = IntVal(i+1)
        next_state_xcor = state[1]
        next_state_ycor = state[2]
        next_state_heading = state[3]
        next_state_pendown = state[4]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
        rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
        return rule, None, None

    elif isinstance(instr, ChironAST.PauseCommand):
        next_pc = IntVal(i+1)
        next_state_xcor = state[1]
        next_state_ycor = state[2]
        next_state_heading = state[3]
        next_state_pendown = state[4]
        next_state_user_vars = [state[j] for j in range(5, len(state))]

        next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
        rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
        return rule, None, None
    
    else:
        print("Error: Unrecognized instruction type.")
        sys.exit(1)

def add_step_rules_to_fixed_point(ir, mode, param=None, optimization_level=OptimizationLevel.NONE):
    fp, BadHeading, Inv, state, next_state, symbol_table, counter_table = z3_fixed_point_object_with_start_state_set(ir, mode, params=param, optimization_level=optimization_level)

    print("\n========== Step 4 ==========")

    if optimization_level == OptimizationLevel.BASIC:
        turn_safe_map = turn_safe(ir) 
        loops = find_repeat_loops(ir)
        summarizable = [l for l in loops if is_summarizable_loop(ir, l)]
        summarizable_by_init = {l[0]: l for l in summarizable}
        skip_indices = set()
        for l in summarizable:
            # Skip all the instruction in the body of the loop as well as the condition, decrement and jump instructions
            skip_indices.update(range(l[0], l[6]))
    else:
        summarizable_by_init = {}
        skip_indices = set()
        turn_safe_map = None

    for i, stmt in enumerate(ir):
        if i in summarizable_by_init:
            loop_desc = summarizable_by_init[i]
            (init_idx, cond_idx, body_start, body_end, dec_idx, back_idx, exit_idx, counter_name, loop_count) = loop_desc
            current_state_no_pc, bad_rules = summarize_loop_effect(ir, loop_desc, fp, Inv, state, next_state, symbol_table, counter_table, turn_safe_map)
            if current_state_no_pc is None:
                # Summarization skipped (too many iterations). Fall back to normal rules.
                instr = stmt[0]
                jump_target = stmt[1]
                rule_true, rule_false, bad_rule = chiron_command_to_z3_rule(i, instr, jump_target, fp, Inv, BadHeading, state, next_state, symbol_table, counter_table, optimization_level, turn_safe_map)
                rule_true_vars = z3util.get_vars(rule_true)
                fp.rule(ForAll(rule_true_vars, rule_true))
                print(f"Added rule for instruction at line {i}: {rule_true}")
                if rule_false is not None:
                    rule_false_vars = z3util.get_vars(rule_false)
                    fp.rule(ForAll(rule_false_vars, rule_false))
                    print(f"Added rule for instruction at line {i} (false branch): {rule_false}")
                if bad_rule is not None:
                    bad_rule_vars = z3util.get_vars(bad_rule)
                    fp.rule(ForAll(bad_rule_vars, bad_rule))
                    print(f"Added BadHeading rule for instruction at line {i}: {bad_rule}")
            else:
                current_state = (IntVal(i), *state[1:])
                next_state_tuple = (IntVal(exit_idx), *current_state_no_pc)
                rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
                rule_vars = z3util.get_vars(rule)
                fp.rule(ForAll(rule_vars, rule))
                print(f"Added summarized rule for loop starting at line {i}: {rule}")
                for bad_cond, bad_state_no_pc, bad_pc in bad_rules:
                    bad_rule_full = Implies(
                        And(Inv(*current_state), bad_cond),
                        BadHeading(IntVal(bad_pc), *bad_state_no_pc)
                    )
                    bad_rule_vars = z3util.get_vars(bad_rule_full)
                    fp.rule(ForAll(bad_rule_vars, bad_rule_full))
                    print(f"Added summarized BadHeading rule for loop starting at line {i}: {bad_rule_full}")

        elif i in skip_indices:
            continue
        else:
            instr = stmt[0]
            jump_target = stmt[1]
            rule_true, rule_false, bad_rule = chiron_command_to_z3_rule(i, instr, jump_target, fp, Inv, BadHeading, state, next_state, symbol_table, counter_table, optimization_level, turn_safe_map)
            rule_true_vars = z3util.get_vars(rule_true)
            fp.rule(ForAll(rule_true_vars, rule_true))
            print(f"Added rule for instruction at line {i}: {rule_true}")
            if rule_false is not None:
                rule_false_vars = z3util.get_vars(rule_false)
                fp.rule(ForAll(rule_false_vars, rule_false))
                print(f"Added rule for instruction at line {i} (false branch): {rule_false}")
            if bad_rule is not None:
                bad_rule_vars = z3util.get_vars(bad_rule)
                fp.rule(ForAll(bad_rule_vars, bad_rule))
                print(f"Added BadHeading rule for instruction at line {i}: {bad_rule}")
        
    print("Step rules added to fixedpoint object.")

    return fp, Inv, BadHeading, state, next_state, symbol_table, counter_table, turn_safe_map
