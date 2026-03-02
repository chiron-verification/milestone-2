from variable_name_detection_in_IR import *
import sys
from z3 import *
from irhandler import getParseTree
from ChironAST.builder import astGenPass
from ChironAST import ChironAST

def z3_fixed_point_invariant_generation(ir):
    symbol_table, counter_table = parse_variables_from_ir(ir)

    print("\n========== Step 2 ==========")

    print("Obtained user variables and loop counters from the IR.")
    
    Inv = Function('Inv',
                IntSort(), # pc
                RealSort(), # xcor
                RealSort(), # ycor
                RealSort(), # heading
                BoolSort(), # pendown
                *[IntSort() for _ in symbol_table], # user_variable
                *[IntSort() for _ in counter_table], # loop_counter
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
    user_variables_prime = [Int(f"{entry['var_name']}_prime") for entry in symbol_table.values()]
    loop_counters = [entry['z3_var'] for entry in counter_table.values()]
    loop_counters_prime = [Int(f"{entry['counter_name']}_prime") for entry in counter_table.values()]

    state = (pc, xcor, ycor, heading, pendown, *user_variables, *loop_counters)
    next_state = (pc_prime, xcor_prime, ycor_prime, heading_prime, pendown_prime, *user_variables_prime, *loop_counters_prime)

    print("Created Z3 variables for program state components, user variables, and loop counters.")

    return Inv, state, next_state, symbol_table, counter_table

