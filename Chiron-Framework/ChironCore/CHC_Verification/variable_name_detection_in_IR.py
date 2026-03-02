# input the ir file
import sys
from z3 import *

directory_to_add = os.path.abspath("/Users/aditikhandelia/Desktop/IITK ACADS/sem 8/CS335/project/code/Chiron-Framework/ChironCore")
sys.path.append(directory_to_add)

from irhandler import getParseTree
from ChironAST.builder import astGenPass
from ChironAST import ChironAST

def pretty_print_symbol_table(symbol_table):
    print("\n---------- Symbol Table (User Variables) ---------\n")
    for var_name, entry in symbol_table.items():
        print(f"Variable Name: {entry['var_name']}, Z3 Variable: {entry['z3_var']}")

def pretty_print_counter_table(counter_table):
    print("\n---------- Counter Table (Loop Counters) ---------\n")
    for counter_name, entry in counter_table.items():
        print(f"Counter Name: {entry['counter_name']}, Z3 Variable: {entry['z3_var']}")

def add_to_symbol_table_or_counter_table(var_name, symbol_table, symbol_table_entry, counter_table, counter_table_entry):
    var_name = var_name[1:]
    # Handle loop counters separately to avoid name clashes with user-defined variables
    if var_name.startswith("__rep_counter"):
        counter_table_entry['counter_name'] = var_name
        counter_table_entry['z3_var'] = Int(var_name)
        counter_table[var_name] = counter_table_entry.copy()
    elif var_name not in symbol_table:
        symbol_table_entry['var_name'] = var_name
        symbol_table_entry['z3_var'] = Int(var_name)
        symbol_table[var_name] = symbol_table_entry.copy()

def parse_variables_from_ir_expr(expr, symbol_table, symbol_table_entry, counter_table, counter_table_entry):
    if isinstance(expr, ChironAST.Var):
        add_to_symbol_table_or_counter_table(expr.varname, symbol_table, symbol_table_entry, counter_table, counter_table_entry)
    elif isinstance(expr, ChironAST.Num):
        pass    
    elif isinstance(expr, ChironAST.BinArithOp):
        for operand in [expr.lexpr, expr.rexpr]:
            parse_variables_from_ir_expr(operand, symbol_table, symbol_table_entry, counter_table, counter_table_entry)
    elif isinstance(expr, ChironAST.UnaryArithOp):
        parse_variables_from_ir_expr(expr.expr, symbol_table, symbol_table_entry, counter_table, counter_table_entry)

def parse_variables_from_ir_cond(cond, symbol_table, symbol_table_entry, counter_table, counter_table_entry):
    if isinstance(cond, ChironAST.AND) or isinstance(cond, ChironAST.OR):
        for operand in [cond.lexpr, cond.rexpr]:
            parse_variables_from_ir_cond(operand, symbol_table, symbol_table_entry, counter_table, counter_table_entry)
    elif isinstance(cond, ChironAST.BinCondOp):
        for operand in [cond.lexpr, cond.rexpr]:
            parse_variables_from_ir_expr(operand, symbol_table, symbol_table_entry, counter_table, counter_table_entry)
    elif isinstance(cond, ChironAST.NOT):
        parse_variables_from_ir_cond(cond.expr, symbol_table, symbol_table_entry, counter_table, counter_table_entry)
    elif isinstance(cond, ChironAST.PenStatus) or isinstance(cond, ChironAST.BoolTrue) or isinstance(cond, ChironAST.BoolFalse):
        pass

def parse_variables_from_ir(ir):
    print("\n========== Step 1 ==========")
    symbol_table = {}
    symbol_table_entry = {
        'var_name': None,
        'z3_var': None,
    }
    num_loop_counters = 0
    counter_table = {}
    counter_table_entry = {
        'counter_name': None,
        'z3_var': None,
    }

    for stmt in ir:
        instr = stmt[0]
        
        if isinstance(instr, ChironAST.AssignmentCommand):
            operand = instr.lvar 
            if isinstance(operand, ChironAST.Var):
                add_to_symbol_table_or_counter_table(operand.varname, symbol_table, symbol_table_entry, counter_table, counter_table_entry)
            operand = instr.rexpr
            parse_variables_from_ir_expr(operand, symbol_table, symbol_table_entry, counter_table, counter_table_entry)

        elif isinstance(instr, ChironAST.ConditionCommand) or isinstance(instr, ChironAST.AssertCommand):
            cond = instr.cond
            parse_variables_from_ir_cond(cond, symbol_table, symbol_table_entry, counter_table, counter_table_entry)

        elif isinstance(instr, ChironAST.MoveCommand):
            operand = instr.expr
            parse_variables_from_ir_expr(operand, symbol_table, symbol_table_entry, counter_table, counter_table_entry)

        elif isinstance(instr, ChironAST.PenCommand):
            pass  

        elif isinstance(instr, ChironAST.GotoCommand):
            for operand in [instr.xcor, instr.ycor]:
                parse_variables_from_ir_expr(operand, symbol_table, symbol_table_entry, counter_table, counter_table_entry)

        elif isinstance(instr, ChironAST.PauseCommand) or isinstance(instr, ChironAST.NoOpCommand):
            pass    

    pretty_print_symbol_table(symbol_table)
    pretty_print_counter_table(counter_table)

    return symbol_table, counter_table
