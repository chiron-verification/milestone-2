# input the ir file
import sys
from z3 import *
from irhandler import getParseTree
from ChironAST.builder import astGenPass
from ChironAST import ChironAST

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

def add_to_symbol_table_or_counter_table(var_name):
    var_name = var_name[1:]
    # Handle loop counters separately to avoid name clashes with user-defined variables
    if var_name.startswith("__rep_counter"):
        counter_table_entry['counter_name'] = var_name
        counter_table_entry['z3_var'] = Int(var_name)
        counter_table[var_name] = counter_table_entry.copy()
    elif var_name not in symbol_table:
        z3_var = Int(var_name)
        symbol_table_entry['var_name'] = var_name
        symbol_table_entry['z3_var'] = z3_var
        symbol_table[var_name] = symbol_table_entry.copy()

def parse_variables_from_ir_expr(expr):
    if isinstance(expr, ChironAST.Var):
        add_to_symbol_table_or_counter_table(expr.varname)
    elif isinstance(expr, ChironAST.Num):
        pass    
    elif isinstance(expr, ChironAST.BinArithOp):
        for operand in [expr.lexpr, expr.rexpr]:
            parse_variables_from_ir_expr(operand)
    elif isinstance(expr, ChironAST.UnaryArithOp):
        parse_variables_from_ir_expr(expr.expr)

def parse_variables_from_ir_cond(cond):
    if isinstance(cond, ChironAST.AND) or isinstance(cond, ChironAST.OR):
        for operand in [cond.lexpr, cond.rexpr]:
            parse_variables_from_ir_cond(operand)
    elif isinstance(cond, ChironAST.BinCondOp):
        for operand in [cond.lexpr, cond.rexpr]:
            parse_variables_from_ir_expr(operand)
    elif isinstance(cond, ChironAST.NOT):
        parse_variables_from_ir_cond(cond.expr)
    elif isinstance(cond, ChironAST.PenStatus) or isinstance(cond, ChironAST.BoolTrue) or isinstance(cond, ChironAST.BoolFalse):
        pass

def parse_variables_from_ir(ir):
    for stmt in ir:
        instr = stmt[0]
        
        if isinstance(instr, ChironAST.AssignmentCommand):
            operand = instr.lvar 
            if isinstance(operand, ChironAST.Var):
                add_to_symbol_table_or_counter_table(operand.varname)
            operand = instr.rexpr
            parse_variables_from_ir_expr(operand)

        elif isinstance(instr, ChironAST.ConditionCommand) or isinstance(instr, ChironAST.AssertCommand):
            cond = instr.cond
            parse_variables_from_ir_cond(cond)

        elif isinstance(instr, ChironAST.MoveCommand):
            operand = instr.expr
            parse_variables_from_ir_expr(operand)

        elif isinstance(instr, ChironAST.PenCommand):
            pass  

        elif isinstance(instr, ChironAST.GotoCommand):
            for operand in [instr.xcor, instr.ycor]:
                parse_variables_from_ir_expr(operand)

        elif isinstance(instr, ChironAST.PauseCommand) or isinstance(instr, ChironAST.NoOpCommand):
            pass    

def pretty_print_symbol_table():
    print("\n========== Symbol Table ==========\n")
    for var_name, entry in symbol_table.items():
        print(f"Variable Name: {entry['var_name']}, Z3 Variable: {entry['z3_var']}")

def pretty_print_counter_table():
    print("\n========== Loop Counter Table ==========\n")
    for counter_name, entry in counter_table.items():
        print(f"Counter Name: {entry['counter_name']}, Z3 Variable: {entry['z3_var']}")

if __name__ == "__main__":
    file_path = sys.argv[1]

    ir = astGenPass().visit(getParseTree(file_path))
    parse_variables_from_ir(ir)
    pretty_print_symbol_table()
    pretty_print_counter_table()
    