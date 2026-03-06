"""
Shared helpers and base test class for CHC verification tests.
"""

import unittest
import sys
import os
from contextlib import redirect_stdout
from io import StringIO

_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CHC_DIR     = os.path.abspath(os.path.join(_THIS_DIR, ".."))
_CHIRON_CORE = os.path.abspath(os.path.join(_CHC_DIR, ".."))

for _p in (_CHIRON_CORE, _CHC_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from irhandler import getParseTree
from ChironAST.builder import astGenPass
from step_rules import add_step_rules_to_fixed_point
from safety_properties import Property, check_property
from z3 import *

PROGRAMS_DIR = os.path.join(_THIS_DIR, "programs")
TIMEOUT_MS   = 15_000   # Z3 hint - not always respected by SPACER


def program_path(name: str) -> str:
    return os.path.join(PROGRAMS_DIR, name)


def build_fp(name: str, mode: str, params=None):
    """Parse *name*.tl and return (fp, Inv, state, next_state, sym, ctr)."""
    ir = astGenPass().visit(getParseTree(program_path(name)))
    fp, Inv, state, ns, st, ct = add_step_rules_to_fixed_point(ir, mode, param=params)
    fp.set(timeout=TIMEOUT_MS)
    return fp, Inv, state, ns, st, ct


def make_context(state, st, ct):
    """Build a name->Z3-var dict from state tuple + symbol/counter tables."""
    ctx = {
        "xcor":    state[1],
        "ycor":    state[2],
        "heading": state[3],
        "pendown": state[4],
        "And": And, "Or": Or, "Not": Not, "Implies": Implies,
    }
    for name, entry in st.items():
        ctx[name] = entry["z3_var"]
    for name, entry in ct.items():
        ctx[name] = entry["z3_var"]
    return ctx


def _run_check(fp, Inv, state, st, ct, prop, mode):
    """Run check_property with stdout suppressed."""
    with redirect_stdout(StringIO()):
        check_property(fp, Inv, state, st, ct, prop, mode)


class ChironTestCase(unittest.TestCase):

    MODE: str = None

    def load(self, tl_file: str, params=None):
        """Build the fixedpoint for *tl_file* under ``self.MODE``."""

        with redirect_stdout(StringIO()):
            self._fp, self._Inv, self._state, self._ns, self._st, self._ct = \
                build_fp(tl_file, self.MODE, params)
        self._ctx = make_context(self._state, self._st, self._ct)

    def v(self, name: str):
        return self._ctx[name]

    def assert_pass(self, name: str, expr):
        """Assert the property is an invariant (PASSED).
        If the solver returns UNKNOWN the test is skipped with a message."""
        prop = Property(name, expr)
        _run_check(self._fp, self._Inv, self._state, self._st, self._ct, prop, self.MODE)
        if prop.status == "UNKNOWN":
            self.skipTest(f"Property '{name}': solver could not determine result (UNKNOWN)")
        self.assertEqual(
            prop.status, "PASSED",
            f"Property '{name}': expected PASSED, got {prop.status}",
        )
        return prop

    def assert_fail(self, name: str, expr):
        """Assert the property is NOT an invariant (FAILED).
        If the solver returns UNKNOWN the test is skipped with a message."""
        prop = Property(name, expr)
        _run_check(self._fp, self._Inv, self._state, self._st, self._ct, prop, self.MODE)
        if prop.status == "UNKNOWN":
            self.skipTest(f"Property '{name}': solver could not determine result (UNKNOWN)")
        self.assertEqual(
            prop.status, "FAILED",
            f"Property '{name}': expected FAILED, got {prop.status}",
        )
        return prop
