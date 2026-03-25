from z3_fixed_point import *
import sys
from z3 import *

def z3_fixed_point_object_with_start_state_set(ir, mode, params=None):
    Inv, state, next_state, symbol_table, counter_table = z3_fixed_point_invariant_generation(ir, mode)
    print("Obtained the invariant relation, state variables, and symbol/counter tables from the IR.")

    print("\n========== Step 3 ==========")
    fp = Fixedpoint()
    fp.set(engine='spacer')
    fp.register_relation(Inv)
    print("Initialized the Z3 fixedpoint object and registered the invariant relation.")

    if (mode == "default"):
        start_state = (
            IntVal(0), # pc
            RealVal(0), # xcor
            RealVal(0), # ycor
            RealVal(0), # heading
            BoolVal(False), # pendown
            *[RealVal(0) for _ in symbol_table], # user variables initialized to 0
            *[RealVal(0) for _ in counter_table]  # loop counters initialized to 0
        )

        fp.fact(Inv(*start_state))
        print("Added default initial rule: pc=0, xcor=0, ycor=0, heading=0, pendown=False, all user variables and counters initialized to 0.")
    
    elif (mode == "universal"):
        xcor, ycor, heading = state[1], state[2], state[3]
        user_vars = list(state[5 : 5 + len(symbol_table)])
        counter_zeros = [RealVal(0) for _ in counter_table]
        quantified = [xcor, ycor, heading] + user_vars
        init_fact = Inv(IntVal(0), 
                        xcor, 
                        ycor, 
                        heading,
                        BoolVal(False), 
                        *user_vars, 
                        *counter_zeros)

        heading_on_grid = Or([heading == RealVal(deg) for deg in range(-360, 721, 15)])
        fp.rule(ForAll(quantified, Implies(heading_on_grid, init_fact)))
        print("Added universal initial rule: xcor, ycor, and user variables are unconstrained; heading is a multiple of 15 in [-360, 720].")

    elif (mode == "specific"):
        for var_name in symbol_table:
            if var_name not in params:
                params[var_name] = 0.0
        
        start_state = (
            IntVal(0),
            RealVal(0),
            RealVal(0),
            RealVal(0),
            BoolVal(False),
            *[RealVal(params[var_name]) for var_name in symbol_table],
            *[RealVal(0) for _ in counter_table]
        )

        fp.fact(Inv(*start_state))
        print("Added specific initial rule based on provided parameters, with defaults for any missing variables.")
    
    else :
        print(f"Error: Invalid mode '{mode}' specified. Supported modes are 'default', 'universal' and 'specific'.")
        sys.exit(1)

    return fp, Inv, state, next_state, symbol_table, counter_table
