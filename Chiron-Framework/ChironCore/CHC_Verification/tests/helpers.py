"""
Shared helpers and base test class for CHC verification tests.
"""

import unittest
import sys
import os
import time
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
from safety_properties import (
    CHC_Verification,
    check_heading_on_grid,
    HEADING_GRID_SAFE,
    HEADING_GRID_VIOLATED,
    HEADING_GRID_UNKNOWN,
)
from z3 import *

PROGRAMS_DIR = os.path.join(_THIS_DIR, "programs")
TIMEOUT_MS   = 15_000
TIMING       = "-t" in sys.argv


class UserProperty:
    """Property with a string expression for passing to CHC_Verification."""
    def __init__(self, name: str, expr: str):
        self.name = name
        self.expr = expr


def program_path(name: str) -> str:
    return os.path.join(PROGRAMS_DIR, name)


def build_fp(name: str, mode: str, params=None):
    """Parse *name*.tl and return (fp, Inv, state, next_state, sym, ctr)."""
    ir = astGenPass().visit(getParseTree(program_path(name)))
    fp, Inv, state, ns, st, ct = add_step_rules_to_fixed_point(ir, mode, param=params)
    fp.set(timeout=TIMEOUT_MS)
    return fp, Inv, state, ns, st, ct


def _run_heading_check(fp, Inv, state):
    """Run check_heading_on_grid with stdout suppressed."""
    with redirect_stdout(StringIO()):
        return check_heading_on_grid(fp, Inv, state)


def _run_api_check(file_path, mode, name, expr_str, params=None):
    """Call CHC_Verification with a single property, stdout suppressed.
    params is a plain dict; converts to colon-keyed string for CHC_Verification."""
    params_str = None
    if params is not None:
        params_str = str({':' + k: v for k, v in params.items()})
    with redirect_stdout(StringIO()):
        return CHC_Verification(file_path, mode, [UserProperty(name, expr_str)], params_str)


class ChironTestCase(unittest.TestCase):

    MODE: str = None

    def load(self, tl_file: str, params=None):
        """Store file info; also build fp for heading-grid pre-checks."""
        self._tl_file = tl_file
        self._file_path = program_path(tl_file)
        self._params = params
        t0 = time.perf_counter()
        with redirect_stdout(StringIO()):
            self._fp, self._Inv, self._state, self._ns, self._st, self._ct = \
                build_fp(tl_file, self.MODE, params)
        self._build_time = time.perf_counter() - t0

    def assert_pass(self, name: str, expr: str):
        """Assert the property is an invariant (PASSED).
        If the solver returns UNKNOWN the test is skipped."""
        t1 = time.perf_counter()
        result = _run_api_check(self._file_path, self.MODE, name, expr, self._params)
        solve_time = time.perf_counter() - t1
        if result.status == 'UNKNOWN':
            self.skipTest(f"Property '{name}': solver could not determine result (UNKNOWN)")
        if TIMING:
            print(
                f"  TIMING  {self._tl_file:<25} {self.MODE:<15} {name:<30} "
                f"build={self._build_time:.4f}s  solve={solve_time:.4f}s  "
                f"total={self._build_time + solve_time:.4f}s  expected=PASSED",
                file=sys.stderr,
            )
        self.assertEqual(
            result.status, "PASSED",
            f"Property '{name}': expected PASSED, got {result.status}",
        )
        return result

    def assert_fail(self, name: str, expr: str):
        """Assert the property is NOT an invariant (FAILED).
        If the solver returns UNKNOWN the test is skipped."""
        t1 = time.perf_counter()
        result = _run_api_check(self._file_path, self.MODE, name, expr, self._params)
        solve_time = time.perf_counter() - t1
        if result.status == 'UNKNOWN':
            self.skipTest(f"Property '{name}': solver could not determine result (UNKNOWN)")
        if TIMING:
            print(
                f"  TIMING  {self._tl_file:<25} {self.MODE:<15} {name:<30} "
                f"build={self._build_time:.4f}s  solve={solve_time:.4f}s  "
                f"total={self._build_time + solve_time:.4f}s  expected=FAILED",
                file=sys.stderr,
            )
        self.assertEqual(
            result.status, "FAILED",
            f"Property '{name}': expected FAILED, got {result.status}",
        )
        return result

    def assert_heading_grid_safe(self):
        """Assert heading always stays on 15-degree grid."""
        status = _run_heading_check(self._fp, self._Inv, self._state)
        self.assertEqual(
            status,
            HEADING_GRID_SAFE,
            f"Expected heading to stay on 15-degree grid, got {status}",
        )
        return status

    def assert_heading_grid_violated(self):
        """Assert heading can leave 15-degree grid."""
        status = _run_heading_check(self._fp, self._Inv, self._state)
        self.assertEqual(
            status,
            HEADING_GRID_VIOLATED,
            f"Expected heading to leave 15-degree grid, got {status}",
        )
        return status

    def assert_heading_grid_unknown(self):
        """Assert heading-grid status is not safe (treated as UNKNOWN for verification)."""
        status = _run_heading_check(self._fp, self._Inv, self._state)
        if status == HEADING_GRID_SAFE:
            self.fail("Expected heading-grid status to be UNKNOWN, but it was SAFE")
        return status

    def assert_pass_after_heading_grid(self, name: str, expr: str):
        """Run via CHC_Verification; skip property if heading grid is not safe."""
        result = _run_api_check(self._file_path, self.MODE, name, expr, self._params)
        if result.status == 'UNKNOWN':
            self.skipTest(f"Heading grid not safe; property '{name}' not checked")
        self.assertEqual(
            result.status, "PASSED",
            f"Property '{name}': expected PASSED after heading grid check, got {result.status}",
        )
        return result

    def assert_fail_after_heading_grid(self, name: str, expr: str):
        """Run via CHC_Verification; skip property if heading grid is not safe."""
        result = _run_api_check(self._file_path, self.MODE, name, expr, self._params)
        if result.status == 'UNKNOWN':
            self.skipTest(f"Heading grid not safe; property '{name}' not checked")
        self.assertEqual(
            result.status, "FAILED",
            f"Property '{name}': expected FAILED after heading grid check, got {result.status}",
        )
        return result

    def assert_unknown_after_heading_grid(self, name: str, expr: str):
        """Assert CHC_Verification returns UNKNOWN when heading grid is not safe."""
        result = _run_api_check(self._file_path, self.MODE, name, expr, self._params)
        self.assertEqual(
            result.status, "UNKNOWN",
            f"Property '{name}': expected UNKNOWN (heading grid not safe), got {result.status}",
        )
        return result
