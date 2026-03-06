from variable_name_detection_in_IR import *
import sys
from z3 import *

def z3_fixed_point_invariant_generation(ir, mode):
    symbol_table, counter_table = parse_variables_from_ir(ir)
    print("Obtained user variables and loop counters from the IR.")

    print("\n========== Step 2 ==========")
    if (mode == "default") or (mode == "universal") or (mode == "specific") :
        Inv = Function('Inv',
            IntSort(), # pc
            RealSort(), # xcor
            RealSort(), # ycor
            RealSort(), # heading
            BoolSort(), # pendown
            *[RealSort() for _ in symbol_table], # user_variable
            *[RealSort() for _ in counter_table], # loop_counter
            BoolSort()
        )

        pc = Int('pc')
        pc_prime = Int('pc_prime')
        xcor = Real('xcor')
        xcor_prime = Real('xcor_prime')
        ycor = Real('ycor')
        ycor_prime = Real('ycor_prime')
        heading = Real('heading')
        heading_prime = Real('heading_prime')
        pendown = Bool('pendown')
        pendown_prime = Bool('pendown_prime')
        user_variables = [entry['z3_var'] for entry in symbol_table.values()]
        user_variables_prime = [Real(f"{entry['var_name']}_prime") for entry in symbol_table.values()]
        loop_counters = [entry['z3_var'] for entry in counter_table.values()]
        loop_counters_prime = [Real(f"{entry['counter_name']}_prime") for entry in counter_table.values()]

        state = (pc, xcor, ycor, heading, pendown, *user_variables, *loop_counters)
        next_state = (pc_prime, xcor_prime, ycor_prime, heading_prime, pendown_prime, *user_variables_prime, *loop_counters_prime)

        print("Created Z3 variables for program state components, user variables, and loop counters.")

        return Inv, state, next_state, symbol_table, counter_table

    elif (mode == "safety-range") :
        # Augment Inv using ghost parameters to mark the start value
        Inv = Function('Inv',
            IntSort(), # pc
            RealSort(), # xcor
            RealSort(), # ycor
            RealSort(), # heading
            BoolSort(), # pendown
            *[RealSort() for _ in symbol_table], # user_variable
            *[RealSort() for _ in counter_table], # loop_counter
            *[RealSort() for _ in symbol_table], # user_variable_start_value (ghost parameter)
            BoolSort()
        )

        pc = Int('pc')
        pc_prime = Int('pc_prime')
        xcor = Real('xcor')
        xcor_prime = Real('xcor_prime')
        ycor = Real('ycor')
        ycor_prime = Real('ycor_prime')
        heading = Real('heading')
        heading_prime = Real('heading_prime')
        pendown = Bool('pendown')
        pendown_prime = Bool('pendown_prime')
        user_variables = [entry['z3_var'] for entry in symbol_table.values()]
        user_variables_prime = [Real(f"{entry['var_name']}_prime") for entry in symbol_table.values()]
        loop_counters = [entry['z3_var'] for entry in counter_table.values()]
        loop_counters_prime = [Real(f"{entry['counter_name']}_prime") for entry in counter_table.values()]
        user_variable_start_values = [Real(f"{entry['var_name']}_start") for entry in symbol_table.values()]

        state = (pc, xcor, ycor, heading, pendown, *user_variables, *loop_counters, *user_variable_start_values)
        next_state = (pc_prime, xcor_prime, ycor_prime, heading_prime, pendown_prime, *user_variables_prime, *loop_counters_prime, *user_variable_start_values)

        print("Created Z3 variables for program state components, user variables, loop counters, and ghost parameters for user variable start values.")

        return Inv, state, next_state, symbol_table, counter_table
    
    else :
        print(f"Error: Invalid mode '{mode}' specified. Supported modes are 'default', 'universal', 'safety-range' and 'specific'.")
        sys.exit(1)