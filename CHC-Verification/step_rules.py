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
        cos_expr = If(h == IntVal(deg),
                      RealVal(f"{cos_f.numerator}/{cos_f.denominator}"),
                      cos_expr)
        sin_expr = If(h == IntVal(deg),
                      RealVal(f"{sin_f.numerator}/{sin_f.denominator}"),
                      sin_expr)
    return cos_expr, sin_expr, BoolVal(True)

def normalize_heading(h):
    return h % IntVal(360)

def _to_int_expr(expr):
    return expr if expr.sort() == IntSort() else ToInt(expr)

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
        return IntVal(expr.val)
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

def chiron_bool_to_z3_env(expr, env, pendown_expr):
    if isinstance(expr, ChironAST.BinCondOp):
        lexpr = expr.lexpr
        rexpr = expr.rexpr
        if isinstance(expr, ChironAST.AND):
            return And(
                chiron_bool_to_z3_env(lexpr, env, pendown_expr),
                chiron_bool_to_z3_env(rexpr, env, pendown_expr),
            )
        if isinstance(expr, ChironAST.OR):
            return Or(
                chiron_bool_to_z3_env(lexpr, env, pendown_expr),
                chiron_bool_to_z3_env(rexpr, env, pendown_expr),
            )
        if isinstance(expr, ChironAST.LT):
            return chiron_expr_to_z3_env(lexpr, env) < chiron_expr_to_z3_env(rexpr, env)
        if isinstance(expr, ChironAST.GT):
            return chiron_expr_to_z3_env(lexpr, env) > chiron_expr_to_z3_env(rexpr, env)
        if isinstance(expr, ChironAST.LTE):
            return chiron_expr_to_z3_env(lexpr, env) <= chiron_expr_to_z3_env(rexpr, env)
        if isinstance(expr, ChironAST.GTE):
            return chiron_expr_to_z3_env(lexpr, env) >= chiron_expr_to_z3_env(rexpr, env)
        if isinstance(expr, ChironAST.EQ):
            return chiron_expr_to_z3_env(lexpr, env) == chiron_expr_to_z3_env(rexpr, env)
        if isinstance(expr, ChironAST.NEQ):
            return chiron_expr_to_z3_env(lexpr, env) != chiron_expr_to_z3_env(rexpr, env)
        raise Exception("Unsupported boolean binop in summarizer")
    if isinstance(expr, ChironAST.NOT):
        return Not(chiron_bool_to_z3_env(expr.expr, env, pendown_expr))
    if isinstance(expr, ChironAST.PenStatus):
        return pendown_expr
    if isinstance(expr, ChironAST.BoolTrue):
        return BoolVal(True)
    if isinstance(expr, ChironAST.BoolFalse):
        return BoolVal(False)
    raise Exception("Unsupported boolean expression in summarizer")

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
                next_state_user_vars[var_index] = _to_int_expr(expr_z3)
            elif var_name in counter_table:
                counter_index = list(counter_table.keys()).index(var_name)
                next_state_user_vars[len(symbol_table) + counter_index] = _to_int_expr(expr_z3)
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
            turn_int = _to_int_expr(expr_z3)
            next_state_heading = normalize_heading(state[3] + turn_int)
            bad_heading_cond = Not(heading_on_grid(next_state_heading))
        elif direction == "right":
            turn_int = _to_int_expr(expr_z3)
            next_state_heading = normalize_heading(state[3] - turn_int)
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

def _sub_state(expr, state_vars, new_vals):
    """Substitute state_vars[i] -> new_vals[i] in a Z3 expression."""
    return substitute(expr, *zip(state_vars, new_vals))

def _merge_branch_value(cond_expr, then_expr, else_expr):
    """
    Merge then/else expressions with a guard while factoring common arithmetic
    prefixes to avoid expression blow-up in branch-heavy loops.
    """
    if then_expr.eq(else_expr):
        return then_expr

    # Factor common additive prefix:
    #   If(c, base + a, base + b) -> base + If(c, a, b)
    if (
        is_app(then_expr)
        and is_app(else_expr)
        and then_expr.decl().kind() == Z3_OP_ADD
        and else_expr.decl().kind() == Z3_OP_ADD
        and then_expr.num_args() == 2
        and else_expr.num_args() == 2
    ):
        t0, t1 = then_expr.arg(0), then_expr.arg(1)
        e0, e1 = else_expr.arg(0), else_expr.arg(1)
        if t0.eq(e0):
            return t0 + If(cond_expr, t1, e1)
        if t1.eq(e1):
            return If(cond_expr, t0, e0) + t1

    return If(cond_expr, then_expr, else_expr)

def _execute_segment_with_branch_merge(
    ir,
    start_idx,
    end_idx,
    current_state,
    path_guard,
    fp,
    Inv,
    state,
    next_state,
    symbol_table,
    counter_table,
    turn_safe_map,
    inner_summaries,
    state_vars,
):
    """
    Symbolically execute a straight-line IR segment with structured if/else
    support, returning:
      (end_state, bad_rules)

    bad_rules entries are triples:
      (path_guarded_bad_cond, bad_state_no_pc, bad_pc)
    """
    if start_idx > end_idx:
        return current_state, []

    bad_rules = []
    idx = start_idx
    while idx <= end_idx:
        if idx in inner_summaries:
            inner_exit_idx, inner_snpc, inner_bad = inner_summaries[idx]
            cur_no_pc = list(current_state[1:])
            
            # Compose: substitute free state vars with the current state
            # expressions in the pre-computed inner summary.
            new_no_pc = tuple(_sub_state(e, state_vars, cur_no_pc) for e in inner_snpc)
            
            # Remap the inner loop's bad-heading conditions the same way.
            for (ib_cond, ib_snpc, ib_pc) in inner_bad:
                guarded = And(path_guard, _sub_state(ib_cond, state_vars, cur_no_pc))
                if is_false(guarded):
                    continue
                bad_rules.append((
                    guarded,
                    tuple(_sub_state(e, state_vars, cur_no_pc) for e in ib_snpc),
                    ib_pc,
                ))
            current_state = (state[0], *new_no_pc)
            idx = inner_exit_idx
            continue

        instr, jump = ir[idx]

        if isinstance(instr, ChironAST.AssertCommand):
            raise ValueError(f"Unsupported assert in summarized segment at index {idx}")

        if isinstance(instr, ChironAST.ConditionCommand):
            # Parser-emitted forward goto used to skip else blocks.
            if isinstance(instr.cond, ChironAST.BoolFalse):
                target = idx + jump
                if target <= idx or target < start_idx or target > end_idx + 1:
                    raise ValueError(f"Unsupported forward goto shape at index {idx}")
                idx = target
                continue

            false_start = idx + jump
            goto_idx = false_start - 1
            if false_start <= idx or false_start > end_idx + 1:
                raise ValueError(f"Unsupported conditional jump target at index {idx}")
            if goto_idx < start_idx or goto_idx > end_idx:
                raise ValueError(f"Malformed if/else (missing true-branch terminator) at index {idx}")

            goto_instr, goto_jump = ir[goto_idx]
            if not isinstance(goto_instr, ChironAST.ConditionCommand) or not isinstance(goto_instr.cond, ChironAST.BoolFalse):
                raise ValueError(f"Malformed if/else join marker at index {idx}")

            join_idx = goto_idx + goto_jump
            if goto_jump <= 0 or join_idx <= false_start or join_idx > end_idx + 1:
                raise ValueError(f"Malformed if/else join target at index {idx}")

            env = _env_from_state(current_state, symbol_table, counter_table)
            cond_expr = chiron_bool_to_z3_env(instr.cond, env, current_state[4])

            # Statically known branch condition: avoid introducing unnecessary ITEs.
            if is_true(cond_expr):
                current_state, then_bad = _execute_segment_with_branch_merge(
                    ir,
                    idx + 1,
                    goto_idx - 1,
                    current_state,
                    path_guard,
                    fp,
                    Inv,
                    state,
                    next_state,
                    symbol_table,
                    counter_table,
                    turn_safe_map,
                    inner_summaries,
                    state_vars,
                )
                bad_rules.extend(then_bad)
                idx = join_idx
                continue

            if is_false(cond_expr):
                current_state, else_bad = _execute_segment_with_branch_merge(
                    ir,
                    false_start,
                    join_idx - 1,
                    current_state,
                    path_guard,
                    fp,
                    Inv,
                    state,
                    next_state,
                    symbol_table,
                    counter_table,
                    turn_safe_map,
                    inner_summaries,
                    state_vars,
                )
                bad_rules.extend(else_bad)
                idx = join_idx
                continue

            then_state, then_bad = _execute_segment_with_branch_merge(
                ir,
                idx + 1,
                goto_idx - 1,
                current_state,
                And(path_guard, cond_expr),
                fp,
                Inv,
                state,
                next_state,
                symbol_table,
                counter_table,
                turn_safe_map,
                inner_summaries,
                state_vars,
            )
            else_state, else_bad = _execute_segment_with_branch_merge(
                ir,
                false_start,
                join_idx - 1,
                current_state,
                And(path_guard, Not(cond_expr)),
                fp,
                Inv,
                state,
                next_state,
                symbol_table,
                counter_table,
                turn_safe_map,
                inner_summaries,
                state_vars,
            )

            merged_no_pc = []
            for j in range(1, len(current_state)):
                then_j = then_state[j]
                else_j = else_state[j]
                merged_no_pc.append(_merge_branch_value(cond_expr, then_j, else_j))
            merged_no_pc = tuple(merged_no_pc)
            current_state = (state[0], *merged_no_pc)
            bad_rules.extend(then_bad)
            bad_rules.extend(else_bad)
            idx = join_idx
            continue

        if jump != 1:
            raise ValueError(f"Unsupported non-unit jump at index {idx}")

        current_state_no_pc, bad_rule = apply_instr_state_only(
            instr, fp, Inv, current_state, next_state, symbol_table, counter_table, idx
        )
        if (bad_rule is not None) and (turn_safe_map is None or not turn_safe_map[idx]):
            guarded = And(path_guard, bad_rule)
            if not is_false(guarded):
                bad_rules.append((guarded, current_state_no_pc, idx + 1))
        current_state = (state[0], *current_state_no_pc)
        idx += 1

    return current_state, bad_rules

def summarize_loop_effect_nested(ir, loop_desc, fp, Inv, state, next_state, symbol_table, counter_table, turn_safe_map, inner_summaries):
    """
    Like summarize_loop_effect but handles nested summarized inner loops and conditional branches in the loop body.

    inner_summaries: dict mapping inner loop init_idx ->
                     (exit_idx, state_no_pc_tuple, bad_rules_list)
      where state_no_pc_tuple is a tuple of Z3 exprs in terms of state[1:],
      and bad_rules_list is a list of (bad_cond, bad_state_no_pc, bad_pc)
      also in terms of state[1:].

    When an inner loop's init is encountered during body traversal the
    pre-computed symbolic transformation is applied via Z3 substitution
    instead of stepping through the inner loop's instructions one by one.
    """
    (init_idx, cond_idx, body_start, body_end, dec_idx, back_idx, exit_idx, counter_name, loop_count) = loop_desc

    if loop_count > MAX_SUMMARIZE_ITERATIONS:
        return None, []

    state_vars = list(state[1:])
    bad_rules = []
    current_state = state

    # Apply init instruction (counter assignment).
    init_instr, _ = ir[init_idx]
    current_state_no_pc, bad_rule = apply_instr_state_only(init_instr, fp, Inv, current_state, next_state, symbol_table, counter_table, init_idx)
    if (bad_rule is not None) and (turn_safe_map is None or not turn_safe_map[init_idx]):
        bad_rules.append((bad_rule, current_state_no_pc, init_idx + 1))
    current_state = (state[0], *current_state_no_pc)

    dec_instr = ir[dec_idx][0]

    for _ in range(loop_count):
        try:
            current_state, iter_bad_rules = _execute_segment_with_branch_merge(
                ir,
                body_start,
                body_end,
                current_state,
                BoolVal(True),
                fp,
                Inv,
                state,
                next_state,
                symbol_table,
                counter_table,
                turn_safe_map,
                inner_summaries,
                state_vars,
            )
        except ValueError:
            # Unsupported control-flow shape in this loop body.
            return None, []
        bad_rules.extend(iter_bad_rules)

        # Apply decrement at end of each iteration.
        current_state_no_pc, bad_rule = apply_instr_state_only(dec_instr, fp, Inv, current_state, next_state, symbol_table, counter_table, dec_idx)
        if (bad_rule is not None) and (turn_safe_map is None or not turn_safe_map[dec_idx]):
            bad_rules.append((bad_rule, current_state_no_pc, dec_idx + 1))
        current_state = (state[0], *current_state_no_pc)

    return tuple(current_state[1:]), bad_rules

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
            return IntVal(expr.val)
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
                next_state_user_vars[var_index] = _to_int_expr(expr_z3)
                next_state_tuple = (next_pc, next_state_xcor, next_state_ycor, next_state_heading, next_state_pendown, *next_state_user_vars)
                rule = Implies(Inv(*current_state), Inv(*next_state_tuple))
                return rule, None, None
            elif var_name in counter_table:
                counter_index = list(counter_table.keys()).index(var_name)
                next_state_user_vars[len(symbol_table) + counter_index] = _to_int_expr(expr_z3)
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
            turn_int = _to_int_expr(expr_z3)
            next_state_heading = normalize_heading(state[3] + turn_int)
        elif direction == "right":
            trig_constraints = BoolVal(True)
            next_state_xcor = state[1]
            next_state_ycor = state[2]
            turn_int = _to_int_expr(expr_z3)
            next_state_heading = normalize_heading(state[3] - turn_int)
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

def add_step_rules_to_fixed_point(ir, mode, param=None, input_ranges=None, optimization_level=OptimizationLevel.NONE):
    fp, BadHeading, Inv, state, next_state, symbol_table, counter_table = z3_fixed_point_object_with_start_state_set(
        ir,
        mode,
        params=param,
        input_ranges=input_ranges,
        optimization_level=optimization_level,
    )

    print("\n========== Step 4 ==========")

    if optimization_level == OptimizationLevel.BASIC:
        turn_safe_map = turn_safe(ir)
        loops = find_repeat_loops(ir)

        # Sort by span (smallest = innermost) so inner loops are processed first.
        loops_sorted = sorted(loops, key=lambda l: l[6] - l[0])

        # Build summaries from innermost outward.  A loop is summarizable if
        # its body (after treating already-summarized inner loops as atomic
        # blocks) contains no ConditionCommands or non-unit jumps.
        loop_summaries = {}       # init_idx -> (exit_idx, state_no_pc_tuple, bad_rules_list)
        summarizable_by_init = {} # init_idx -> loop_desc

        for loop_desc in loops_sorted:
            _init, _cond, _bstart, _bend, _dec, _back, _exit, _cname, _cnt = loop_desc
            # Collect summaries of inner loops whose init falls within this body.
            inner_sums = {k: v for k, v in loop_summaries.items() if _bstart <= k <= _bend}
            if is_summarizable_loop_nested(ir, loop_desc, {k: v[0] for k, v in inner_sums.items()}):
                snpc, br = summarize_loop_effect_nested(
                    ir, loop_desc, fp, Inv, state, next_state,
                    symbol_table, counter_table, turn_safe_map, inner_sums
                )
                if snpc is not None:
                    loop_summaries[_init] = (_exit, snpc, br)
                    summarizable_by_init[_init] = loop_desc

        skip_indices = set()
        for _init, ld in summarizable_by_init.items():
            # Skip every instruction from init through back (i.e. up to but not
            # including exit_idx) — the single summarized rule replaces them all.
            skip_indices.update(range(ld[0], ld[6]))
    else:
        summarizable_by_init = {}
        loop_summaries = {}
        skip_indices = set()
        turn_safe_map = None

    for i, stmt in enumerate(ir):
        if i in summarizable_by_init:
            loop_desc = summarizable_by_init[i]
            (init_idx, cond_idx, body_start, body_end, dec_idx, back_idx, exit_idx, counter_name, loop_count) = loop_desc
            _, snpc, bad_rules = loop_summaries[i]
            current_state = (IntVal(i), *state[1:])
            next_state_tuple = (IntVal(exit_idx), *snpc)
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
