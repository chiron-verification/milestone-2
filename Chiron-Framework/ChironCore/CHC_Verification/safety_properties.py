from step_rules import *
import sys
from z3 import *
from irhandler import getParseTree
from ChironAST.builder import astGenPass
import ast as _ast
from enum import Enum

class ReturnError(Enum):
    SUCCESS = 0
    ERROR = 1
    UNKNOWN = 2

class ReturnValue:
    def __init__(self, return_expr=None):
        self.expr = return_expr
        self.advice = None   
        self.error = ReturnError.UNKNOWN
        self.status = 'UNKNOWN'
        self.passing_properties = []
        self.failing_properties = []
        self.unknown_properties = []

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

HEADING_GRID_SAFE = "SAFE"
HEADING_GRID_VIOLATED = "VIOLATED"
HEADING_GRID_UNKNOWN = "UNKNOWN"

def check_heading_on_grid(fp, Inv, state):
    heading = state[3]
    on_grid = Or([heading == RealVal(deg) for deg in range(-360, 721, 15)])
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
    else:
        print(f"Property '{property_name}' status is UNKNOWN. Solver returned: {result}")
        property.status = 'UNKNOWN'

def CHC_Verification(file_name, mode, user_properties, params=None):

    return_safety = ReturnValue()

    if mode not in ['universal', 'specific', 'default']:
        return_safety.expr = "Invalid mode."
        return_safety.advice = "Please choose 'universal', 'specific', or 'default'."
        return_safety.error = ReturnError.ERROR
        return return_safety
        
    if mode == 'specific':
        if params is None:
            return_safety.expr = "Error: 'specific' mode requires a params string representing a dictionary of parameter values."
            return_safety.advice = "Example: CHC_Verfication('prog.tl', 1, 'specific', {':x': 10})"
            return_safety.error = ReturnError.ERROR
            return return_safety
        try:
            raw_params = _ast.literal_eval(params)
            params = {k.lstrip(':'): float(v) for k, v in raw_params.items()}

            if params is None :
                raise ValueError("Params dict cannot be None for specific mode.")
        except Exception as e:
            return_safety.expr = f"Error parsing params dict: {e}"
            return_safety.advice = "Example: CHC_Verfication('prog.tl', 1, 'specific', {':x': 10})"
            return_safety.error = ReturnError.ERROR
            return return_safety

    ir = astGenPass().visit(getParseTree(file_name))
    fp, Inv, state, next_state, symbol_table, counter_table = add_step_rules_to_fixed_point(ir, mode, param=params)
    print("Obtained fixed point object and invariant predicate. Ready to check properties.")

    # Check that the heading stays on a 15-degree grid
    heading_grid_status = check_heading_on_grid(fp, Inv, state)
    if heading_grid_status != HEADING_GRID_SAFE:
        return_safety.expr = "Skipping property checks."
        return_safety.advice = "Heading can reach non-15-degree values. Verification status is UNKNOWN under strict 15-degree exact semantics."
        return_safety.error = ReturnError.SUCCESS
        return_safety.status = 'UNKNOWN'
        return return_safety

    eval_context = {
        'xcor': state[1], 'ycor': state[2], 'heading': state[3], 'pendown': state[4],
        'And': And, 'Or': Or, 'Not': Not,
    }
    for var_name, entry in symbol_table.items():
        eval_context[var_name] = entry['z3_var']
    for ctr_name, entry in counter_table.items():
        eval_context[ctr_name] = entry['z3_var']

    properties = []
    for i in range(len(user_properties)):
        property_name = user_properties[i].name
        property_expr_str = user_properties[i].expr
        try:
            prop_expr = eval(property_expr_str, {"__builtins__": {}}, eval_context)
            properties.append(Property(property_name, prop_expr))
        except Exception as e: 
            return_safety.expr = f"Error parsing property '{property_name}': {e}"
            return_safety.advice = "Please ensure the property expression is a valid boolean expression using the available state variables and logical operators."
            return_safety.error = ReturnError.ERROR
            return return_safety

    print("\n========== Step 5 ==========")
    safe = True
    for property in properties:
        check_property(fp, Inv, state, symbol_table, counter_table, property, mode)
        if property.status == 'FAILED':
            print(f"Stopping further checks since property '{property.name}' failed.")
            print(f"Counterexample for property '{property.name}': {property.counterexample}")
            safe = False
            return_safety.failing_properties.append([property.name, property.counterexample])
            break
        elif property.status == 'UNKNOWN':
            print(f"Stopping further checks since property '{property.name}' status is UNKNOWN.")
            safe = False
            return_safety.unknown_properties.append(property.name)
            break
        else:
            print(f"Property '{property.name}' PASSED.")
            print(f"Invariant for property '{property.name}': {property.invariant}")
            return_safety.passing_properties.append([property.name, property.invariant])

    if safe:
        return_safety.expr = "All properties satisfied."
        return_safety.advice = "The program is safe to run with respect to the specified properties."
        return_safety.error = ReturnError.SUCCESS
        return_safety.status = 'PASSED'
        print("All properties satisfied, the program is safe to run.")
    else:
        return_safety.expr = "Some properties failed or are UNKNOWN."
        return_safety.advice = "The program is not safe to run with respect to the specified properties. Please review the failing properties and their counterexamples or unknown status."
        return_safety.error = ReturnError.SUCCESS
        return_safety.status = 'FAILED' if return_safety.failing_properties else 'UNKNOWN'
        print("Some properties failed. The program is not safe to run.")

    print("\n========== Step 5 Completed ==========")
    return return_safety
