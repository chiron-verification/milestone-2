"""
Shared helpers for CHC performance tests.
"""

import csv
import fcntl
import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO

PERF_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perf_results.csv")

def _write_perf_row(row: dict):
    write_header = not os.path.exists(PERF_CSV)
    with open(PERF_CSV, "a", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            writer = csv.DictWriter(f, fieldnames=["file", "prop", "status", "build_s", "solve_s"])
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CHC_DIR     = os.path.abspath(os.path.join(_THIS_DIR, ".."))
_CHIRON_CORE = os.path.abspath(os.path.join(_CHC_DIR, ".."))

for _p in (_CHIRON_CORE, _CHC_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from safety_properties import CHC_Verification, ReturnError, ReturnValue

PROGRAMS_DIR = os.path.join(_THIS_DIR, "programs")


class UserProperty:
    def __init__(self, name: str, expr: str):
        self.name = name
        self.expr = expr

def program_path(name: str) -> str:
    return os.path.join(PROGRAMS_DIR, name)

def _run_api_check(file_path, mode, name, expr_str, params=None,
                   hints=None, timeout_ms=120_000, property_scope="all"):
    if hints is None:
        hints = ["check_heading_always_on_grid"]
    params_str = None
    if params is not None:
        params_str = str({':' + k: v for k, v in params.items()})
    try:
        with redirect_stdout(StringIO()):
            return CHC_Verification(
                file_path, mode,
                [UserProperty(name, expr_str)],
                params_str,
                property_scope=property_scope,
                hints=hints,
                timeout_ms=timeout_ms,
            )
    except Exception as e:
        if 'canceled' in str(e):
            rv = ReturnValue()
            rv.status = 'UNKNOWN'
            rv.error = ReturnError.SUCCESS
            rv.expr = f"Solver timed out on property '{name}'."
            rv.advice = "Increase timeout_ms."
            rv.build_time = 0.0
            return rv
        raise


class PerformanceTestCase(unittest.TestCase):
    """
    Base class for performance tests.

    Each test should call load(), then assert_and_time() or time_check().
    Timing results are always printed to stdout so pytest -s shows them.
    """

    MODE: str = None
    DEFAULT_TIMEOUT_MS: int = 120_000

    def load(self, tl_file: str, params=None,
             hints=None, timeout_ms=None, property_scope="all"):
        self._tl_file        = tl_file
        self._file_path      = program_path(tl_file)
        self._params         = params
        self._hints          = hints if hints is not None else ["check_heading_always_on_grid"]
        self._timeout_ms     = timeout_ms if timeout_ms is not None else self.DEFAULT_TIMEOUT_MS
        self._property_scope = property_scope

    def time_check(self, name: str, expr: str):
        """
        Run verification and return (result, build_time, solve_time).
        Always prints a timing summary line.
        solve_time is None when no property query was issued (e.g. heading
        grid check failed early).
        """
        result   = _run_api_check(self._file_path, self.MODE, name, expr,
                                  self._params, self._hints,
                                  self._timeout_ms, self._property_scope)
        build_t  = result.build_time
        solve_t  = result.solve_times[0] if result.solve_times else None

        _write_perf_row({
            "file":    self._tl_file,
            "prop":    name,
            "status":  result.status,
            "build_s": f"{build_t:.4f}" if build_t is not None else "",
            "solve_s": f"{solve_t:.4f}" if solve_t is not None else "",
        })
        return result, build_t, solve_t

    def assert_and_time(self, name: str, expr: str, expected_status: str,
                        max_build_s: float = None, max_solve_s: float = None):
        """
        Run verification, assert expected_status, print timings, and
        optionally assert generous upper-bound time limits.
        Returns (result, build_time, solve_time).
        """
        result, build_t, solve_t = self.time_check(name, expr)

        if result.error == ReturnError.ERROR:
            self.fail(f"API error: {result.expr} — {result.advice}")

        self.assertEqual(
            result.status, expected_status,
            f"Property '{name}': expected {expected_status}, got {result.status}",
        )
        if max_build_s is not None:
            self.assertLess(build_t, max_build_s,
                f"Build time {build_t:.3f}s exceeded limit {max_build_s}s")
        if max_solve_s is not None and solve_t is not None:
            self.assertLess(solve_t, max_solve_s,
                f"Solve time {solve_t:.3f}s exceeded limit {max_solve_s}s")

        return result, build_t, solve_t
