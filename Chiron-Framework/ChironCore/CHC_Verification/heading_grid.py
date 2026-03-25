from z3 import Or, RealVal

def heading_on_grid(h):
    return Or([h == RealVal(deg) for deg in range(0, 360, 15)])