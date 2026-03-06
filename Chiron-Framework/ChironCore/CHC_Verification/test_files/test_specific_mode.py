"""
Pytest tests for specific mode in the CHC verification pipeline.
Run from ChironCore/ directory:
    source .venv/bin/activate
    pytest CHC_Verification/test_specific_mode.py -v
"""
import sys
import os
import pytest

# ensure both CHC_Verification/ and ChironCore/ are on the path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from z3 import *
from step_rules import add_step_rules_to_fixed_point
from safety_properties import Property, check_property
from irhandler import getParseTree
from ChironAST.builder import astGenPass

ASSIGNMENT_TL = os.path.join(os.path.dirname(__file__), "test_files/variable_arithmetic/assignment.tl")

def build_fp(file_path, mode, params=None):
    ir = astGenPass().visitStart(getParseTree(file_path))
    return add_step_rules_to_fixed_point(ir, mode, param=params)


# ── specific mode ────────────────────────────────────────────────────────────

def test_specific_k_final_value_passes():
    """At pc=9 (end of program), k must equal 78 regardless of initial a value."""
    fp, Inv, state, next_state, symbol_table, counter_table = build_fp(
        ASSIGNMENT_TL, "specific", params={"a": 0.0}
    )
    pc = state[0]
    k_var = symbol_table["k"]["z3_var"]
    prop = Property("k_final", Implies(pc == 9, k_var == RealVal(78)))
    check_property(fp, Inv, state, symbol_table, counter_table, prop, "specific")
    print(f"\n[k_final] status={prop.status} | invariant={prop.invariant}")
    assert prop.status == "PASSED", f"Expected PASSED, got {prop.status}"


def test_specific_k_not_global_invariant_fails():
    """k == 78 is NOT a global invariant: at pc=0 k=0, so SPACER should find a counterexample."""
    fp, Inv, state, next_state, symbol_table, counter_table = build_fp(
        ASSIGNMENT_TL, "specific", params={"a": 0.0}
    )
    k_var = symbol_table["k"]["z3_var"]
    prop = Property("k_global", k_var == RealVal(78))
    check_property(fp, Inv, state, symbol_table, counter_table, prop, "specific")
    print(f"\n[k_global] status={prop.status} | counterexample={prop.counterexample}")
    assert prop.status == "FAILED", f"Expected FAILED, got {prop.status}"


def test_specific_a_final_value_passes():
    """At pc=9, a must equal 12 (set on first instruction, never changed)."""
    fp, Inv, state, next_state, symbol_table, counter_table = build_fp(
        ASSIGNMENT_TL, "specific", params={"a": 99.0}  # initial value overridden by :a=12
    )
    pc = state[0]
    a_var = symbol_table["a"]["z3_var"]
    prop = Property("a_final", Implies(pc == 9, a_var == RealVal(12)))
    check_property(fp, Inv, state, symbol_table, counter_table, prop, "specific")
    print(f"\n[a_final] status={prop.status} | invariant={prop.invariant}")
    assert prop.status == "PASSED", f"Expected PASSED, got {prop.status}"


def test_specific_wrong_value_fails():
    """At pc=9, k != 99 — SPACER should find a counterexample."""
    fp, Inv, state, next_state, symbol_table, counter_table = build_fp(
        ASSIGNMENT_TL, "specific", params={"a": 0.0}
    )
    pc = state[0]
    k_var = symbol_table["k"]["z3_var"]
    prop = Property("k_wrong", Implies(pc == 9, k_var == RealVal(99)))
    check_property(fp, Inv, state, symbol_table, counter_table, prop, "specific")
    print(f"\n[k_wrong] status={prop.status} | counterexample={prop.counterexample}")
    assert prop.status == "FAILED", f"Expected FAILED, got {prop.status}"
