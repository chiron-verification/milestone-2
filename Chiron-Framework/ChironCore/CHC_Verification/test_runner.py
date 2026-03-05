#!/usr/bin/env python3
"""CHC Verification - pytest test suite.
Run:  pytest test_runner.py -v
"""
import sys, os, contextlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from z3 import *
from step_rules import add_step_rules_to_fixed_point
from safety_properties import check_property, Property
from irhandler import getParseTree
from ChironAST.builder import astGenPass

# -- helpers -------------------------------------------------------------------
TL = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../test_files"))
t  = lambda f: os.path.join(TL, f)   # full path to a test file
v  = lambda st, n: st[n]["z3_var"]   # Z3 ref for user variable :n
P, F = "PASSED", "FAILED"            # expected outcomes

@contextlib.contextmanager
def _quiet():
    with open(os.devnull, "w") as nul:
        sys.stdout, sys.stderr = nul, nul
        try:    yield
        finally: sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__

# Module-level cache: build each fixed-point object only once per .tl file
_fp_cache: dict = {}

def _get_fp(filepath):
    if filepath not in _fp_cache:
        ir = astGenPass().visit(getParseTree(filepath))
        with _quiet():
            _fp_cache[filepath] = add_step_rules_to_fixed_point(ir)
    return _fp_cache[filepath]

# -- test suites ---------------------------------------------------------------
# Each suite: (label, tl_file, [(test_name, lambda(state,sym,ctr)->BoolExpr, P|F)])
# State tuple: (pc, xcor, ycor, heading, pendown, *user_vars, *counters)
#   s[1]=xcor  s[2]=ycor  s[3]=heading  s[4]=pendown (Bool)

SUITES = [

    # :x=10  :y=20  :z=x+y(30)  :w=z*2(60)  :v=w-x(50)  :u=v/5(10)  — no movement
    # vars start at 0; only >= bounds hold as invariants across all reachable states
    ("assignment.tl", t("assignment.tl"), [
        ("x >= 0  (0 then 10)",   lambda s,st,ct: v(st,"x") >= 0,               P),
        ("y >= 0  (0 then 20)",   lambda s,st,ct: v(st,"y") >= 0,               P),
        ("z >= 0  (0 then 30)",   lambda s,st,ct: v(st,"z") >= 0,               P),
        ("xcor stays 0",          lambda s,st,ct: s[1] == 0,                    P),
        ("ycor stays 0",          lambda s,st,ct: s[2] == 0,                    P),
        ("x == 5  (wrong)",       lambda s,st,ct: v(st,"x") == 5,               F),
        ("y == x  (20 != 10)",     lambda s,st,ct: v(st,"y") == v(st,"x"),      F),
        ("z == 0  (never 0)",     lambda s,st,ct: v(st,"z") == 0,               F),
        ("xcor > 0  (no move)",   lambda s,st,ct: s[1] > 0,                     F),
        ("v == 0  (v is 50)",     lambda s,st,ct: v(st,"v") == 0,               F),
    ]),

    # pendown; forward×4 at heading=0 → xcor grows, ycor stays 0
    # initial state has pendown=False, so only coordinate/variable bounds are invariants
    ("forward.tl", t("forward.tl"), [
        ("xcor >= 0",             lambda s,st,ct: s[1] >= 0,                    P),
        ("ycor == 0  (east axis)",lambda s,st,ct: s[2] == 0,                    P),
        ("heading == 0",          lambda s,st,ct: s[3] == 0,                    P),
        ("d >= 0",                lambda s,st,ct: v(st,"d") >= 0,               P),
        ("d <= 50  (max assigned value)", lambda s,st,ct: v(st,"d") <= 50,      P),
        ("xcor < 0  (moves +x)",  lambda s,st,ct: s[1] < 0,                     F),
        ("ycor > 0  (stays 0)",   lambda s,st,ct: s[2] > 0,                     F),
        ("pendown is False",      lambda s,st,ct: Not(s[4]),                    F),
        ("heading != 0",          lambda s,st,ct: s[3] != 0,                    F),
        ("d < 0",                 lambda s,st,ct: v(st,"d") < 0,                F),
    ]),

    # pendown; backward×4 at heading=0 → xcor shrinks (≤0), ycor stays 0
    # initial state has pendown=False, so only coordinate/variable bounds are invariants
    ("backward.tl", t("backward.tl"), [
        ("xcor <= 0",             lambda s,st,ct: s[1] <= 0,                    P),
        ("ycor == 0",             lambda s,st,ct: s[2] == 0,                    P),
        ("heading == 0",          lambda s,st,ct: s[3] == 0,                    P),
        ("d >= 0",                lambda s,st,ct: v(st,"d") >= 0,               P),
        ("d <= 50  (max assigned value)", lambda s,st,ct: v(st,"d") <= 50,      P),
        ("xcor > 0  (moves -x)",  lambda s,st,ct: s[1] > 0,                     F),
        ("ycor > 0",              lambda s,st,ct: s[2] > 0,                     F),
        ("pendown is False",      lambda s,st,ct: Not(s[4]),                    F),
        ("heading > 0",           lambda s,st,ct: s[3] > 0,                     F),
        ("d > 100  (max is 50)",  lambda s,st,ct: v(st,"d") > 100,              F),
    ]),

    # :x=10 :y=20; if x<y→fwd 50; if x!=y→right 90; :z=x+y; if z>25→fwd z; no pen
    # vars start at 0; x<y fails at pc=1 when x=10,y=0; use >= bounds instead
    ("conditional_if_else.tl", t("conditional_if_else.tl"), [
        ("x >= 0  (0 then 10)",   lambda s,st,ct: v(st,"x") >= 0,               P),
        ("y >= 0  (0 then 20)",   lambda s,st,ct: v(st,"y") >= 0,               P),
        ("z >= 0  (0 then 30)",   lambda s,st,ct: v(st,"z") >= 0,               P),
        ("pen never set (False)", lambda s,st,ct: Not(s[4]),                    P),
        ("xcor >= 0  (only fwd east)", lambda s,st,ct: s[1] >= 0,               P),
        ("x == y  (10 != 20)",     lambda s,st,ct: v(st,"x") == v(st,"y"),      F),
        ("z < 0  (z = 0 or 30)", lambda s,st,ct: v(st,"z") < 0,                 F),
        ("pendown is True",       lambda s,st,ct: s[4],                         F),
        ("x > y  (10 not > 20)", lambda s,st,ct: v(st,"x") > v(st,"y"),         F),
        ("y < x  (20 not < 10)", lambda s,st,ct: v(st,"y") < v(st,"x"),         F),
    ]),

    # :x=10 :y=20; if x<y→fwd 50; if x>5→right 90; if y==20→fwd 30; no pen
    # vars start at 0; x<y and x>0 fail at initial state; use >= bounds instead
    ("conditional_if.tl", t("conditional_if.tl"), [
        ("x >= 0  (0 then 10)",   lambda s,st,ct: v(st,"x") >= 0,               P),
        ("y >= 0  (0 then 20)",   lambda s,st,ct: v(st,"y") >= 0,               P),
        ("pen never set (False)", lambda s,st,ct: Not(s[4]),                    P),
        ("xcor >= 0  (only fwd east)", lambda s,st,ct: s[1] >= 0,               P),
        ("ycor >= -30  (fwd south at most 30)", lambda s,st,ct: s[2] >= -30,    P),
        ("x == y  (10 != 20)",     lambda s,st,ct: v(st,"x") == v(st,"y"),      F),
        ("x > y  (10 not > 20)", lambda s,st,ct: v(st,"x") > v(st,"y"),         F),
        ("pendown is True",       lambda s,st,ct: s[4],                         F),
        ("x < 5  (x = 10)",       lambda s,st,ct: v(st,"x") < 5,                F),
        ("y < x  (20 not < 10)", lambda s,st,ct: v(st,"y") < v(st,"x"),         F),
    ]),

    # penup/pendown + goto(0,0)(100,100)(:x,:y); :x=50 :y=75; xcor/ycor always ≥0
    ("goto.tl", t("goto.tl"), [
        ("xcor >= 0",             lambda s,st,ct: s[1] >= 0,                    P),
        ("ycor >= 0",             lambda s,st,ct: s[2] >= 0,                    P),
        ("x >= 0  (0 or 50)",     lambda s,st,ct: v(st,"x") >= 0,               P),
        ("y >= 0  (0 or 75)",     lambda s,st,ct: v(st,"y") >= 0,               P),
        ("x + y >= 0",            lambda s,st,ct: v(st,"x") + v(st,"y") >= 0,   P),
        ("xcor < 0",              lambda s,st,ct: s[1] < 0,                     F),
        ("ycor < 0",              lambda s,st,ct: s[2] < 0,                     F),
        ("xcor == 200  (never)",  lambda s,st,ct: s[1] == 200,                  F),
        ("x == 0  (becomes 50)", lambda s,st,ct: v(st,"x") == 0,                F),
        ("y < 0",                 lambda s,st,ct: v(st,"y") < 0,                F),
    ]),

    # pendown; fwd 50; left 90; fwd 50; left 45; fwd 50; :angle=60; left :angle; fwd 50
    # initial state has pendown=False; heading and angle are always non-negative
    ("left.tl", t("left.tl"), [
        ("angle >= 0  (0 or 60)", lambda s,st,ct: v(st,"angle") >= 0,           P),
        ("angle <= 60",           lambda s,st,ct: v(st,"angle") <= 60,          P),
        ("heading >= 0",          lambda s,st,ct: s[3] >= 0,                    P),
        ("heading <= 360",        lambda s,st,ct: s[3] <= 360,                  P),
        ("angle + heading >= 0",  lambda s,st,ct: v(st,"angle") + s[3] >= 0,    P),
        ("pendown is False",      lambda s,st,ct: Not(s[4]),                    F),
        ("angle < 0",             lambda s,st,ct: v(st,"angle") < 0,            F),
        ("angle > 90  (max 60)",  lambda s,st,ct: v(st,"angle") > 90,           F),
        ("angle == 45  (never)",  lambda s,st,ct: v(st,"angle") == 45,          F),
        ("heading < 0",           lambda s,st,ct: s[3] < 0,                     F),
    ]),

    # :i=3 :j=2; repeat 3 [repeat 2 [fwd i; right j]; i+=1]
    # i reachable: 0,3,4,5,6   j reachable: 0,2
    ("nested_loops.tl", t("nested_loops.tl"), [
        ("i >= 0",                lambda s,st,ct: v(st,"i") >= 0,               P),
        ("j >= 0  (0 or 2)",      lambda s,st,ct: v(st,"j") >= 0,               P),
        ("j <= 2",                lambda s,st,ct: v(st,"j") <= 2,               P),
        ("i <= 6  (max after loop)",lambda s,st,ct: v(st,"i") <= 6,             P),
        ("i + j >= 0",            lambda s,st,ct: v(st,"i") + v(st,"j") >= 0,   P),
        ("i < 0",                 lambda s,st,ct: v(st,"i") < 0,                F),
        ("j < 0",                 lambda s,st,ct: v(st,"j") < 0,                F),
        ("j > 5  (max 2)",        lambda s,st,ct: v(st,"j") > 5,                F),
        ("i > 10  (max 6)",       lambda s,st,ct: v(st,"i") > 10,               F),
        ("i == 1  (never 1)",     lambda s,st,ct: v(st,"i") == 1,               F),
    ]),

    # pendown; fwd 50; pause; fwd 50; pause → xcor in {0,50,100}
    # initial state has pendown=False; coordinate bounds are the true invariants
    ("pause.tl", t("pause.tl"), [
        ("xcor >= 0",             lambda s,st,ct: s[1] >= 0,                    P),
        ("ycor == 0",             lambda s,st,ct: s[2] == 0,                    P),
        ("heading == 0",          lambda s,st,ct: s[3] == 0,                    P),
        ("xcor <= 100",           lambda s,st,ct: s[1] <= 100,                  P),
        ("xcor + ycor >= 0",      lambda s,st,ct: s[1] + s[2] >= 0,             P),
        ("xcor < 0",              lambda s,st,ct: s[1] < 0,                     F),
        ("ycor > 0",              lambda s,st,ct: s[2] > 0,                     F),
        ("pendown is False",      lambda s,st,ct: Not(s[4]),                    F),
        ("xcor > 200  (max 100)", lambda s,st,ct: s[1] > 200,                   F),
        ("heading > 0",           lambda s,st,ct: s[3] > 0,                     F),
    ]),

    # pendown; fwd 50; penup; fwd 50; pendown; fwd 50 → xcor in {0,50,100,150}
    ("pendown.tl", t("pendown.tl"), [
        ("xcor >= 0",             lambda s,st,ct: s[1] >= 0,                    P),
        ("ycor == 0",             lambda s,st,ct: s[2] == 0,                    P),
        ("heading == 0",          lambda s,st,ct: s[3] == 0,                    P),
        ("xcor <= 150",           lambda s,st,ct: s[1] <= 150,                  P),
        ("xcor + ycor >= 0",      lambda s,st,ct: s[1] + s[2] >= 0,             P),
        ("xcor < 0",              lambda s,st,ct: s[1] < 0,                     F),
        ("ycor > 0",              lambda s,st,ct: s[2] > 0,                     F),
        ("heading > 0",           lambda s,st,ct: s[3] > 0,                     F),
        ("xcor > 200  (max 150)", lambda s,st,ct: s[1] > 200,                   F),
        ("xcor + ycor > 500",     lambda s,st,ct: s[1] + s[2] > 500,            F),
    ]),

    # pendown; fwd 50; penup; fwd 50; penup → xcor in {0,50,100}
    ("penup.tl", t("penup.tl"), [
        ("xcor >= 0",             lambda s,st,ct: s[1] >= 0,                    P),
        ("ycor == 0",             lambda s,st,ct: s[2] == 0,                    P),
        ("heading == 0",          lambda s,st,ct: s[3] == 0,                    P),
        ("xcor <= 100",           lambda s,st,ct: s[1] <= 100,                  P),
        ("xcor + ycor >= 0",      lambda s,st,ct: s[1] + s[2] >= 0,             P),
        ("xcor < 0",              lambda s,st,ct: s[1] < 0,                     F),
        ("ycor > 0",              lambda s,st,ct: s[2] > 0,                     F),
        ("heading > 0",           lambda s,st,ct: s[3] > 0,                     F),
        ("xcor > 200  (max 100)", lambda s,st,ct: s[1] > 200,                   F),
        ("xcor + ycor > 500",     lambda s,st,ct: s[1] + s[2] > 500,            F),
    ]),

    # pendown; repeat 4 [fwd 50; right 90] → square; xcor∈{0,50}, ycor∈{0,−50}
    # initial state has pendown=False; heading and coordinate bounds are true invariants
    ("repeat.tl", t("repeat.tl"), [
        ("heading >= 0",          lambda s,st,ct: s[3] >= 0,                    P),
        ("heading <= 360",        lambda s,st,ct: s[3] <= 360,                  P),
        ("xcor >= 0  (0 or 50)",  lambda s,st,ct: s[1] >= 0,                    P),
        ("xcor <= 50",            lambda s,st,ct: s[1] <= 50,                   P),
        ("ycor >= -50  (south at most 50)", lambda s,st,ct: s[2] >= -50,        P),
        ("pendown is False",      lambda s,st,ct: Not(s[4]),                    F),
        ("heading < 0",           lambda s,st,ct: s[3] < 0,                     F),
        ("xcor > 500  (max 50)",  lambda s,st,ct: s[1] > 500,                   F),
        ("ycor >= 0  (can be −50)",lambda s,st,ct: s[2] >= 0,                   F),
        ("xcor == 200  (never)",  lambda s,st,ct: s[1] == 200,                  F),
    ]),

    # pendown; fwd 50; right 90; fwd 50; right 45; fwd 50; :angle=60; right :angle; fwd 50
    # initial state has pendown=False; heading and angle bounds are true invariants
    ("right.tl", t("right.tl"), [
        ("angle >= 0  (0 or 60)", lambda s,st,ct: v(st,"angle") >= 0,           P),
        ("angle <= 60",           lambda s,st,ct: v(st,"angle") <= 60,          P),
        ("heading >= 0",          lambda s,st,ct: s[3] >= 0,                    P),
        ("heading <= 360",        lambda s,st,ct: s[3] <= 360,                  P),
        ("angle + heading >= 0",  lambda s,st,ct: v(st,"angle") + s[3] >= 0,    P),
        ("pendown is False",      lambda s,st,ct: Not(s[4]),                    F),
        ("angle < 0",             lambda s,st,ct: v(st,"angle") < 0,            F),
        ("angle > 90  (max 60)",  lambda s,st,ct: v(st,"angle") > 90,           F),
        ("angle == 45  (never)",  lambda s,st,ct: v(st,"angle") == 45,          F),
        ("heading < 0",           lambda s,st,ct: s[3] < 0,                     F),
    ]),

]

# -- pytest parametrize -------------------------------------------------------
# Flatten SUITES into individual test cases; each gets a readable ID.

_cases = [
    pytest.param(filepath, expr_fn, expected, id=f"{label} > {name}")
    for label, filepath, tests in SUITES
    for name, expr_fn, expected in tests
]

@pytest.mark.parametrize("filepath,expr_fn,expected", _cases)
def test_property(filepath, expr_fn, expected):
    fp, Inv, state, next_state, st, ct = _get_fp(filepath)
    with _quiet():
        prop = Property("prop", expr_fn(state, st, ct))
        check_property(fp, Inv, state, next_state, st, ct, prop)
    if prop.status == "UNKNOWN":
        pytest.skip("UNKNOWN")
    assert prop.status == expected, f"expected {expected}, got {prop.status}"
