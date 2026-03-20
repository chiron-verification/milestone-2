from step_rules import *
import sys
from z3 import *
from irhandler import getParseTree
from ChironAST.builder import astGenPass
import ast as _ast

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
        self.safety_range = None

HEADING_GRID_SAFE = "SAFE"
HEADING_GRID_VIOLATED = "VIOLATED"
HEADING_GRID_UNKNOWN = "UNKNOWN"

def check_heading_on_grid(fp, Inv, state):
    heading = state[3]
    on_grid = Or([heading == RealVal(deg) for deg in range(0, 360, 15)])
    query_vars = z3util.get_vars(And(Inv(*state), Not(on_grid)))
    result = fp.query(Exists(query_vars, And(Inv(*state), Not(on_grid))))
    if result == sat:
        print("Heading can reach a value that is not a multiple of 15 degrees.")
        print("Verification status is UNKNOWN under strict 15-degree exact semantics.")
        return HEADING_GRID_VIOLATED
    elif result == unsat:
        print("Heading is always a multiple of 15 degrees. Proceeding with exact verification.")
        return HEADING_GRID_SAFE
    else:
        print("Could not determine if heading stays on the 15-degree grid.")
        print("Verification status is UNKNOWN.")
        return HEADING_GRID_UNKNOWN

def check_property(fp, Inv, state, symbol_table, counter_table, property, mode):
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
        property.invariant = fp.get_answer()
        if mode == 'safety-range':
            inv = property.invariant
            n_user_vars = len(symbol_table)
            n_counters = len(counter_table)
            ghost_params = list(state[5 + n_user_vars + n_counters:])
            user_vars = list(state[5 : 5 + n_user_vars])
            subs = [(state[0], IntVal(0)), (state[1], RealVal(0)), (state[2], RealVal(0)),
                    (state[3], RealVal(0)), (state[4], BoolVal(False))]
            subs += [(uv, gp) for uv, gp in zip(user_vars, ghost_params)]
            subs += [(state[5 + n_user_vars + i], RealVal(0)) for i in range(n_counters)]
            precondition = substitute(inv, *subs)
            property.safety_range = simplify(precondition)

    else:
        print(f"Property '{property_name}' status is UNKNOWN. Solver returned: {result}")
        property.status = 'UNKNOWN'
    
if __name__ == "__main__":
    # Command line arguments: 1) Chiron program file, 2) number of properties, 
    # 3) mode (universal/safety-range/specific/default), 4) params dict (only for specific mode)

    if len(sys.argv) < 4:
        print("Usage: python safety_properties.py <chiron_program_file> <number_of_properties> <mode>")
        sys.exit(1)
    file_name = sys.argv[1]
    mode = sys.argv[3]

    if mode not in ['universal', 'safety-range', 'specific', 'default']:
        print("Invalid mode. Please choose 'universal', 'safety-range', 'specific', or 'default'.")
        sys.exit(1)
        
    params = None
    if mode == 'specific':
        if len(sys.argv) < 5:
            print("Error: 'specific' mode requires a params dict as 4th argument.")
            print("Example: python safety_properties.py prog.tl 1 specific '{\":x\": 10}'")
            sys.exit(1)
        try:
            raw_params = _ast.literal_eval(sys.argv[4])
            params = {k.lstrip(':'): float(v) for k, v in raw_params.items()}

            if params is None :
                raise ValueError("Params dict cannot be None for specific mode.")
            
        except Exception as e:
            print(f"Error parsing params dict: {e}")
            sys.exit(1)

    ir = astGenPass().visit(getParseTree(file_name))
    fp, Inv, state, next_state, symbol_table, counter_table = add_step_rules_to_fixed_point(ir, mode, param=params)
    print("Obtained fixed point object and invariant predicate. Ready to check properties.")

    # Check that the heading stays on a 15-degree grid
    heading_grid_status = check_heading_on_grid(fp, Inv, state)
    if heading_grid_status != HEADING_GRID_SAFE:
        print("Skipping property checks.")
        print("Final verification result: UNKNOWN.")
        sys.exit(0)

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
        check_property(fp, Inv, state, symbol_table, counter_table, property, mode)
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
            if mode == 'safety-range':
                print(f"Safety range for property '{property.name}': {property.safety_range}")

    if safe:
        print("All properties satisfied, the program is safe to run.")
    else:
        print("Some properties failed. The program is not safe to run.")
    print("\n========== Step 5 Completed ==========")
