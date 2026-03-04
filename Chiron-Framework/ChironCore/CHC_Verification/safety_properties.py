from step_rules import *
import sys
from z3 import *
from z3 import z3util
from irhandler import getParseTree
from ChironAST.builder import astGenPass
from ChironAST import ChironAST
from math import cos, sin, pi
from fractions import Fraction

class Property:
    def __init__(self, name, property_expr):
        self.name = name
        if is_bool(property_expr):
            self.property_expr = property_expr
        else:
            print(f"Error: Property expression must be a boolean expression. Got: {property_expr}")
            sys.exit(1)
        self.status = 'UNKNOWN'
        self.invariant = None
        self.counterexample = None

def check_property(fp, Inv, state, next_state, symbol_table, counter_table, property):
    property_name = property.name
    property_expr = property.property_expr
    query_vars = z3util.get_vars(And(Inv(*state), Not(property_expr)))
    result = fp.query(Exists(query_vars, And(Inv(*state), Not(property_expr))))
    if result == sat:
        print(f"Property '{property_name}' is NOT an invariant. Counterexample found.")
        property.status = 'FAILED'
        property.counterexample = fp.get_answer()
    elif result == unsat:
        print(f"Property '{property_name}' is an invariant. No counterexample exists.")
        property.status = 'PASSED'
        property.invariant = property_expr
    else:
        print(f"Property '{property_name}' status is UNKNOWN. Solver returned: {result}")
        property.status = 'UNKNOWN'
    
if __name__ == "__main__":
    file_name = sys.argv[1]
    ir = astGenPass().visit(getParseTree(file_name))
    fp, Inv, state, next_state, symbol_table, counter_table = add_step_rules_to_fixed_point(ir, sanity_check=False)

    # print the variables and counters for the user to reference when writing properties
    print("For turtle's x-coordinate, use 'xcor'")
    print("For turtle's y-coordinate, use 'ycor'")
    print("For turtle's heading, use 'heading'")
    print("For turtle's pen state, use 'pendown'")
    print("State variables available for properties:")
    for i, var in enumerate(symbol_table):
        print(f"{i}. {var}")
    print("\nCounters available for properties:")
    for i, counter in enumerate(counter_table):
        print(f"{i}. {counter}")

    eval_context = {
        'xcor': state[1], 'ycor': state[2], 'heading': state[3], 'pendown': state[4],
        'And': And, 'Or': Or, 'Not': Not,
    }
    for var_name, entry in symbol_table.items():
        eval_context[var_name] = entry['z3_var']
    for ctr_name, entry in counter_table.items():
        eval_context[ctr_name] = entry['z3_var']

    num_properties = int(sys.argv[2])
    properties = []
    for i in range(num_properties):
        property_name = input(f"\nEnter name for property {i+1}: ")
        property_expr_str = input(f"Enter the boolean expression for property '{property_name}': ")
        try:
            prop_expr = eval(property_expr_str, {"__builtins__": {}}, eval_context)
            properties.append(Property(property_name, prop_expr))
        except Exception as e:
            print(f"Error parsing property '{property_name}': {e}")
            sys.exit(1)    

    print("\n========== Step 5 ==========")
    safe = True
    for property in properties:
        check_property(fp, Inv, state, next_state, symbol_table, counter_table, property)
        if property.status == 'FAILED':
            print(f"Stopping further checks since property '{property.name}' failed.")
            print(f"Counterexample for property '{property.name}': {property.counterexample}")
            safe = False
            break
        elif property.status == 'UNKNOWN':
            print(f"Stopping further checks since property '{property.name}' status is UNKNOWN.")
            safe = False
            break
        else:
            print(f"Property '{property.name}' PASSED.")
            print(f"Invariant for property '{property.name}': {property.invariant}")

    if safe:
        print("All properties satisfied, the program is safe to run.")
    else:
        print("Some properties failed. The program is not safe to run.")
    print("\n========== Step 5 Completed ==========")