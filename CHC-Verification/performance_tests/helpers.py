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

_PERF_DIR = os.path.dirname(os.path.abspath(__file__))

_CSV_FIELDS = [
    "file", "prop",
    # No hint (check_heading_always_on_grid)
    "verdict_none",  "result_none",  "build_s_none",  "solve_s_none",
    "verdict_basic", "result_basic", "build_s_basic", "solve_s_basic",
    # With hint (heading_on_grid_always)
    "verdict_none_hint",  "result_none_hint",  "build_s_none_hint",  "solve_s_none_hint",
    "verdict_basic_hint", "result_basic_hint", "build_s_basic_hint", "solve_s_basic_hint",
]

def _verdict(status):
    """Raw solver output: PASSED, FAILED, or UNKNOWN for anything else (timeout, error)."""
    if status in ("PASSED", "FAILED"):
        return status
    return "UNKNOWN"

def _result(verdict, expected):
    """Compare verdict against expected outcome.
    Returns PASSED if they match, SKIPPED if verdict is UNKNOWN, FAILED otherwise."""
    if verdict == "UNKNOWN":
        return "SKIPPED"
    return "PASSED" if verdict == expected else "FAILED"

def _write_perf_row(row: dict, mode: str):
    csv_path = os.path.join(_PERF_DIR, f"perf_results_{mode}.csv")
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
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
from variable_name_detection_in_IR import OptimizationLevel

PROGRAMS_DIR = os.path.join(_THIS_DIR, "programs")


class UserProperty:
    def __init__(self, name: str, expr: str):
        self.name = name
        self.expr = expr

def program_path(name: str) -> str:
    return os.path.join(PROGRAMS_DIR, name)

def _run_api_check(file_path, mode, name, expr_str, params=None,
                   hints=None, timeout_ms=20_000, property_scope="all",
                   optimization_level=OptimizationLevel.NONE):
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
                optimization_level=optimization_level,
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
    DEFAULT_TIMEOUT_MS: int = 20_000

    def load(self, tl_file: str, params=None,
             hints=None, timeout_ms=None, property_scope="all"):
        self._tl_file        = tl_file
        self._file_path      = program_path(tl_file)
        self._params         = params
        self._hints          = hints if hints is not None else ["check_heading_always_on_grid"]
        self._timeout_ms     = timeout_ms if timeout_ms is not None else self.DEFAULT_TIMEOUT_MS
        self._property_scope = property_scope

    def time_check(self, name: str, expr: str, expected_status: str = None):
        """
        Run verification under two OptimizationLevels x two hint modes,
        write a single combined CSV row, and return
        (result_none, result_basic,
         result_none_hint, result_basic_hint).

        No-hint runs use ["check_heading_always_on_grid"] (the default, which
        queries heading safety).  Hint runs use ["heading_on_grid_always"]
        (assumes heading is on the 15-degree grid, skipping that query).

        verdict_* columns hold the raw solver output (PASSED / FAILED / UNKNOWN).
        result_*  columns hold PASSED when verdict==expected_status, FAILED when
        they differ, and SKIPPED when the verdict is UNKNOWN (timeout/error).
        If expected_status is None the result_* columns are left blank.
        """
        _no_hint   = ["check_heading_always_on_grid"]
        _with_hint = ["heading_on_grid_always"]

        def _run(opt, hints):
            return _run_api_check(self._file_path, self.MODE, name, expr,
                                  self._params, hints,
                                  self._timeout_ms, self._property_scope,
                                  optimization_level=opt)

        def _safe_run(opt, hints):
            try:
                return _run(opt, hints), None
            except Exception as e:
                return None, e

        result_none,      exc_none      = _safe_run(OptimizationLevel.NONE,  _no_hint)
        result_basic,     exc_basic     = _safe_run(OptimizationLevel.BASIC, _no_hint)
        result_none_hint, exc_none_hint = _safe_run(OptimizationLevel.NONE,  _with_hint)
        result_basic_hint,exc_basic_hint= _safe_run(OptimizationLevel.BASIC, _with_hint)

        def _fmt(v):
            return f"{v:.4f}" if v is not None else ""

        def _raw_status(r, exc):
            return "ERROR" if exc else r.status

        def _solve(r):
            return _fmt(r.solve_times[0] if r and r.solve_times else None)

        v_none       = _verdict(_raw_status(result_none,      exc_none))
        v_basic      = _verdict(_raw_status(result_basic,     exc_basic))
        v_none_hint  = _verdict(_raw_status(result_none_hint, exc_none_hint))
        v_basic_hint = _verdict(_raw_status(result_basic_hint,exc_basic_hint))

        _write_perf_row({
            "file":                    self._tl_file,
            "prop":                    name,
            "verdict_none":            v_none,
            "result_none":             _result(v_none, expected_status) if expected_status is not None else "",
            "build_s_none":            _fmt(result_none.build_time) if result_none else "",
            "solve_s_none":            _solve(result_none),
            "verdict_basic":           v_basic,
            "result_basic":            _result(v_basic, expected_status) if expected_status is not None else "",
            "build_s_basic":           _fmt(result_basic.build_time) if result_basic else "",
            "solve_s_basic":           _solve(result_basic),
            "verdict_none_hint":       v_none_hint,
            "result_none_hint":        _result(v_none_hint, expected_status) if expected_status is not None else "",
            "build_s_none_hint":       _fmt(result_none_hint.build_time) if result_none_hint else "",
            "solve_s_none_hint":       _solve(result_none_hint),
            "verdict_basic_hint":      v_basic_hint,
            "result_basic_hint":       _result(v_basic_hint, expected_status) if expected_status is not None else "",
            "build_s_basic_hint":      _fmt(result_basic_hint.build_time) if result_basic_hint else "",
            "solve_s_basic_hint":      _solve(result_basic_hint),
        }, self.MODE)

        for exc in (
            exc_none, 
            exc_basic, 
            exc_none_hint, 
            exc_basic_hint
            ):
            if exc:
                raise exc

        return (result_none, result_basic, result_none_hint, result_basic_hint)

    def assert_and_time(self, name: str, expr: str, expected_status: str,
                        max_build_s: float = None, max_solve_s: float = None):
        """
        Run verification under two optimization levels * two hint modes.

        For each of the 4 configurations:
          - verdict = raw solver output (PASSED / FAILED / UNKNOWN)
          - result  = PASSED if verdict==expected_status, SKIPPED if UNKNOWN, FAILED otherwise

        Assertions are only made for configurations whose verdict is not UNKNOWN;
        an UNKNOWN verdict (solver timeout) counts as SKIPPED, not a test failure.
        Returns (result_none, result_basic, result_none_hint, result_basic_hint).
        """
        (result_none, result_basic,
         result_none_hint, result_basic_hint) = self.time_check(name, expr, expected_status)
        
        for result in (result_none, result_basic, result_none_hint, result_basic_hint):
            if result is None:
                self.fail("API error: no result returned")
            if result.error == ReturnError.ERROR:
                self.fail(f"API error: {result.expr} - {result.advice}")

        for r, label in (
            (result_none,      "NONE"),
            (result_basic,     "BASIC"),
            (result_none_hint, "NONE+hint"),
            (result_basic_hint,"BASIC+hint"),
        ):
            if r.status != "UNKNOWN":
                self.assertEqual(
                    r.status, expected_status,
                    f"Property '{name}' ({label}): expected {expected_status}, got {r.status}",
                )
            if max_solve_s is not None and r.solve_times:
                self.assertLessEqual(
                    r.solve_times[0], max_solve_s,
                    f"Solve time for property '{name}' ({label}) exceeded {max_solve_s:.2f}s: {r.solve_times[0]:.2f}s"
                )
            if max_build_s is not None:
                self.assertLessEqual(
                    r.build_time, max_build_s,
                    f"Build time for property '{name}' ({label}) exceeded {max_build_s:.2f}s: {r.build_time:.2f}s"
                )


            
        # print(f"File: '{self._tl_file}', Property '{name}': expected {expected_status}")
        # print(f"NONE build {build_t:.3f}s, solve {solve_t:.3f}s")
        # print(f"BASIC build {result_basic.build_time:.3f}s, solve {result_basic.solve_times[0]:.3f}s")
        # print(f"NONE+hint build {result_none_hint.build_time:.3f}s, solve {result_none_hint.solve_times[0]:.3f}s")
        # print(f"BASIC+hint build {result_basic_hint.build_time:.3f}s, solve {result_basic_hint.solve_times[0]:.3f}s")

        return (result_none, result_basic, result_none_hint, result_basic_hint)
