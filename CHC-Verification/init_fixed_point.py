from z3_fixed_point import *
import sys
from z3 import *
from heading_grid import heading_on_grid

def _normalize_input_ranges(input_ranges, symbol_table):
    if input_ranges is None:
        return {}
    if not isinstance(input_ranges, dict):
        raise ValueError("input_ranges must be a dict mapping var names to ranges.")

    normalized = {}
    for var_name, spec in input_ranges.items():
        if var_name not in symbol_table:
            raise ValueError(f"Unknown input variable in input_ranges: {var_name}")
        if spec is None:
            continue # unconstrained variable
        if isinstance(spec, int):
            normalized[var_name] = (spec, spec) # treat single int as fixed value
            continue
        elif isinstance(spec, (list, tuple)) and len(spec) == 2:
            lo, hi = spec
            if not isinstance(lo, int) or not isinstance(hi, int):
                raise ValueError(f"Invalid range for {var_name}: bounds must be integers.")
            if lo > hi:
                raise ValueError(f"Invalid range for {var_name}: lower bound > upper bound.")
            normalized[var_name] = (lo, hi)
            continue
        raise ValueError(
            f"Invalid range for {var_name}: use an int, (lo, hi), or None."
        )

    return normalized

def z3_fixed_point_object_with_start_state_set(ir, mode, params=None, input_ranges=None, optimization_level=OptimizationLevel.NONE):
    Inv, BadHeading, state, next_state, symbol_table, counter_table = z3_fixed_point_invariant_generation(ir, mode, optimization_level=optimization_level)
    print("Obtained the invariant relation, state variables, and symbol/counter tables from the IR.")

    print("\n========== Step 3 ==========")
    fp = Fixedpoint()
    fp.set(engine='spacer')
    fp.register_relation(Inv)
    print("Initialized the Z3 fixedpoint object and registered the invariant relation.")
    fp.register_relation(BadHeading)
    print("Registered the BadHeading relation for checking heading grid violations.")

    if (mode == "default"):
        if input_ranges is not None:
            raise ValueError("input_ranges is only supported in universal mode.")
        start_state = (
            IntVal(0), # pc
            RealVal(0), # xcor
            RealVal(0), # ycor
            IntVal(0), # heading
            BoolVal(False), # pendown
            *[IntVal(0) for _ in symbol_table], # user variables initialized to 0
            *[IntVal(0) for _ in counter_table]  # loop counters initialized to 0
        )

        fp.fact(Inv(*start_state))
        print("Added default initial rule: pc=0, xcor=0, ycor=0, heading=0, pendown=False, all user variables and counters initialized to 0.")
    
    elif (mode == "universal"):
        xcor, ycor, heading = state[1], state[2], state[3]
        user_vars = list(state[5 : 5 + len(symbol_table)])
        counter_zeros = [IntVal(0) for _ in counter_table]
        quantified = [xcor, ycor, heading] + user_vars
        init_fact = Inv(IntVal(0), 
                        xcor, 
                        ycor, 
                        heading,
                        BoolVal(True), 
                        *user_vars, 
                        *counter_zeros)

        normalized_ranges = _normalize_input_ranges(input_ranges, symbol_table)
        range_constraints = []
        for var_name, (lo, hi) in normalized_ranges.items():
            z3_var = symbol_table[var_name]["z3_var"]
            if lo == hi:
                range_constraints.append(z3_var == IntVal(lo))
            else:
                range_constraints.append(And(z3_var >= IntVal(lo), z3_var <= IntVal(hi)))

        init_guard = heading_on_grid(heading)
        if range_constraints:
            init_guard = And(init_guard, *range_constraints)
        fp.rule(ForAll(quantified, Implies(init_guard, init_fact)))
        print("Added universal initial rule: xcor, ycor, and user variables are unconstrained; user variables are integers; heading is constrained to be a multiple of 15 degrees, and pc=0, pendown=True, counters=0.")

    elif (mode == "specific"):
        if input_ranges is not None:
            raise ValueError("input_ranges is only supported in universal mode.")
        for var_name in symbol_table:
            if var_name not in params:
                params[var_name] = 0.0
        
        start_state = (
            IntVal(0),
            RealVal(0),
            RealVal(0),
            IntVal(0),
            BoolVal(False),
            *[IntVal(int(params[var_name])) for var_name in symbol_table],
            *[IntVal(0) for _ in counter_table]
        )

        fp.fact(Inv(*start_state))
        print("Added specific initial rule based on provided parameters, with defaults for any missing variables.")
    
    else :
        print(f"Error: Invalid mode '{mode}' specified. Supported modes are 'default', 'universal' and 'specific'.")
        sys.exit(1)

    return fp, BadHeading, Inv, state, next_state, symbol_table, counter_table
