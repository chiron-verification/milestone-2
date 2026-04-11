from z3 import Or, IntVal

def heading_on_grid(h):
    return Or([h == IntVal(deg) for deg in range(0, 360, 15)])