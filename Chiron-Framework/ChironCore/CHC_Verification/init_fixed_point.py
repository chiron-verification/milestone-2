from z3_fixed_point import *
import sys
from z3 import *
from irhandler import getParseTree
from ChironAST.builder import astGenPass
from ChironAST import ChironAST

def z3_fixed_point_object_with_start_state_set(ir, sanity_check=False):
    Inv, state, next_state, symbol_table, counter_table = z3_fixed_point_invariant_generation(ir)

    print("\n========== Step 3 ==========")
    fp = Fixedpoint()
    fp.register_relation(Inv)
    print("Initialized the Z3 fixedpoint object and registered the invariant relation.")

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
    print("Added the initial state fact to the fixedpoint object.")

    if sanity_check:
        print("\n---------- Sanity Checks for Step 3 ----------\n")
        result = fp.query(Inv(*start_state))
        assert result == sat, "The initial state should satisfy the invariant relation."
        print("Verified that the initial state satisfies the invariant relation.")

        non_start_state = (
            IntVal(1), # pc
            RealVal(1), # xcor
            RealVal(1), # ycor
            RealVal(90), # heading
            BoolVal(True), # pendown
            *[RealVal(0) for _ in symbol_table],
            *[RealVal(0) for _ in counter_table]
        )
        result = fp.query(Inv(*non_start_state))
        assert result == unsat, "A non-start state should not satisfy the invariant relation."
        print("Verified that a non-start state does not satisfy the invariant relation.")
        print("\n---------- End of Sanity Checks for Step 3 ----------")

    return fp, Inv, state, next_state, symbol_table, counter_table
