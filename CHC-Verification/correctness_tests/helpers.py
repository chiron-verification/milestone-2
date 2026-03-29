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

from safety_properties import CHC_Verification, ReturnError

PROGRAMS_DIR = os.path.join(_THIS_DIR, "programs")

class UserProperty:
    """Property with a string expression for passing to CHC_Verification."""
    def __init__(self, name: str, expr: str):
        self.name = name
        self.expr = expr

def program_path(name: str) -> str:
    return os.path.join(PROGRAMS_DIR, name)

def _run_api_check(file_path, mode, name, expr_str, params=None, hints=["check_heading_always_on_grid"], timeout_ms=60_000, property_scope="all"):
    """Call CHC_Verification with a single property, stdout suppressed.
    params is a plain dict; converts to colon-keyed string for CHC_Verification."""
    params_str = None
    if params is not None:
        params_str = str({':' + k: v for k, v in params.items()})
    with redirect_stdout(StringIO()):
        return CHC_Verification(
            file_path,
            mode,
            [UserProperty(name, expr_str)],
            params_str,
            property_scope=property_scope,
            hints=hints,
            timeout_ms=timeout_ms,
        )

class ChironTestCase(unittest.TestCase):

    MODE: str = None

    def load(self, tl_file: str, params=None, hints=["check_heading_always_on_grid"], timeout_ms=60_000, property_scope="all"):
        """Store file info for CHC_Verification runs."""
        self._tl_file = tl_file
        self._file_path = program_path(tl_file)
        self._params = params
        self._hints = hints
        self._timeout_ms = timeout_ms
        self._property_scope = property_scope
    
    def return_from_api_check(self, name: str, expr: str):
        """Run CHC_Verification and return the full result object for inspection."""
        return _run_api_check(self._file_path, self.MODE, name, expr, self._params, self._hints, self._timeout_ms, self._property_scope)

    def _assert_property_status(self, name: str, expr: str, expected: str, heading_grid_expected: str = None):
        """Run CHC_Verification and assert property status (and heading grid if provided)."""
        result = _run_api_check(self._file_path, self.MODE, name, expr, self._params, self._hints, self._timeout_ms, self._property_scope)
        if result.error == ReturnError.ERROR:
            self.fail(f"{result.expr} {result.advice}")
        self.assertEqual(
            result.status, expected,
            f"Property '{name}': expected {expected}, got {result.status}",
        )
        if heading_grid_expected is not None:
            self.assertEqual(
                result.heading_grid_safe, heading_grid_expected,
                f"Property '{name}': expected heading grid to be {heading_grid_expected}, got {result.heading_grid_safe}",
            )
        return result

    def _assert_heading_grid_status(self, name: str, expr: str, expected: str):
        """Run CHC_Verification and assert heading grid status."""
        result = _run_api_check(self._file_path, self.MODE, name, expr, self._params, self._hints, self._timeout_ms, self._property_scope)
        if result.error == ReturnError.ERROR:
            self.fail(f"{result.expr} {result.advice}")
        self.assertEqual(
            result.heading_grid_safe, expected,
            f"Expected heading grid to be {expected}, got {result.heading_grid_safe}",
        )
        return result

    def assert_property_pass(self, name: str, expr: str):
        """Assert the property is an invariant (PASSED).
        If the solver returns UNKNOWN the test fails."""
        return self._assert_property_status(name, expr, "PASSED", heading_grid_expected="PASSED")

    def assert_property_fail(self, name: str, expr: str):
        """Assert the property is NOT an invariant (FAILED).
        If the solver returns UNKNOWN the test fails."""
        return self._assert_property_status(name, expr, "FAILED", heading_grid_expected="PASSED")

    def assert_property_unknown(self, name: str, expr: str):
        """Assert the property status is UNKNOWN.
        This is for cases where we expect the solver to be inconclusive."""
        return self._assert_property_status(name, expr, "UNKNOWN", heading_grid_expected="PASSED")
    
    def assert_heading_grid_safe(self, name: str, expr: str):
        """Assert that the heading stays on the 15-degree grid.
        This is a helper for tests that only want to check this aspect."""
        return self._assert_heading_grid_status(name, expr, "PASSED")
    
    def assert_heading_grid_unsafe(self, name: str, expr: str):
        """Assert that the heading can reach non-15-degree values.
        This is a helper for tests that only want to check this aspect."""
        return self._assert_heading_grid_status(name, expr, "FAILED")
    
    def assert_heading_grid_unknown(self, name: str, expr: str):
        """Assert that we cannot determine if the heading stays on the 15-degree grid.
        This is a helper for tests that only want to check this aspect."""
        return self._assert_heading_grid_status(name, expr, "UNKNOWN")
