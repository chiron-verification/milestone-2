#!/usr/bin/env python3
"""
Live Demo: CHC Verification
Runs 4 programs across 2 optimization modes × 2 hint settings.

Programs:
  1. perf_repeat_10.tl   — simple repeat loop
  2. perf_deep_nest_3.tl — 3-level nested loops
  3. perf_trig_10.tl     — turtle trig (forward/right × 10)
  4. perf_turns_20.tl    — heading turns (right/left × 20)

Modes:    NONE (baseline) vs BASIC (optimized)
Hints:    no-hint  = check_heading_always_on_grid (verifier checks heading grid)
          with-hint = heading_on_grid_always       (solver trusts heading is on grid)
"""

import multiprocessing as mp
import os
import sys
import time
from contextlib import redirect_stdout
from io import StringIO

# ── path setup ─────────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_MS2_DIR    = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_CHC_DIR    = os.path.join(_MS2_DIR, "CHC-Verification")
_PROGRAMS   = os.path.join(_CHC_DIR, "performance_tests", "programs")

for _p in (_CHC_DIR, _MS2_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from safety_properties import CHC_Verification, ReturnError, ReturnValue
from variable_name_detection_in_IR import OptimizationLevel

# ── terminal colours ───────────────────────────────────────────────────────────
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
MAGENTA= "\033[95m"
RESET  = "\033[0m"

# ── demo configuration ─────────────────────────────────────────────────────────
TIMEOUT_MS = 60_000

DEMOS = [
    {
        "label":    "Sum Accumulator     (repeat 100, universal)",
        "file":     "opt_universal_100.tl",
        "mode":     "universal",
        "scope":    "terminating",
        "prop":     ("b_sum_tight", "b == 100*a - 4950"),
        "expected": "PASSED",
    },
    {
        "label":    "Deep Nested Loops   (3 levels, 4×4×4)",
        "file":     "perf_deep_nest_3.tl",
        "mode":     "universal",
        "scope":    "terminating",
        "prop":     ("all_nonneg", "And(a >= 0, b >= 0, c >= 0)"),
        "expected": "PASSED",
    },
    {
        "label":    "Turtle Trig         (forward+right × 10)",
        "file":     "perf_trig_10.tl",
        "mode":     "default",
        "scope":    "all",
        "prop":     ("heading_quarters",
                     "Or(heading == 0, heading == 90, heading == 180, heading == 270)"),
        "expected": "PASSED",
    },
    # {
    #     "label":    "Heading Turns       (right 15, left 15 × 20)",
    #     "file":     "perf_turns_20.tl",
    #     "mode":     "default",
    #     "scope":    "all",
    #     "prop":     ("heading_mul15", "heading % 15 == 0"),
    #     "expected": "PASSED",
    # },
]

CONFIGS = [
    ("NONE  | no hint ", OptimizationLevel.NONE,  ["check_heading_always_on_grid"]),
    ("NONE  | hint    ", OptimizationLevel.NONE,  ["heading_on_grid_always"]),
    ("BASIC | no hint ", OptimizationLevel.BASIC, ["check_heading_always_on_grid"]),
    ("BASIC | hint    ", OptimizationLevel.BASIC, ["heading_on_grid_always"]),
]

# ── helpers ────────────────────────────────────────────────────────────────────

class _Prop:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr


def _run(file, name, expr, opt, hints, mode="default", scope="all"):
    fp = os.path.join(_PROGRAMS, file)
    try:
        with redirect_stdout(StringIO()):
            return CHC_Verification(
                fp, mode, [_Prop(name, expr)],
                hints=hints,
                timeout_ms=TIMEOUT_MS,
                optimization_level=opt,
                property_scope=scope,
            ), None
    except Exception:
        rv = ReturnValue()
        rv.status = "UNKNOWN"
        rv.error  = ReturnError.SUCCESS
        rv.build_time  = 0.0
        rv.solve_times = []
        return rv, None


# ── process-isolated runner (prevents z3 context corruption between calls) ──────

_mp_ctx = mp.get_context("fork")   # fork inherits sys.path + loaded modules


def _run_worker(q, file, name, expr, opt, hints, mode, scope):
    rv, _ = _run(file, name, expr, opt, hints, mode, scope)
    q.put({
        "status":     rv.status,
        "build_time": rv.build_time,
        "solve_times": list(rv.solve_times),
        "error":      rv.error,
    } if rv is not None else None)


def _run_isolated(file, name, expr, opt, hints, mode="default", scope="all"):
    q    = _mp_ctx.Queue()
    proc = _mp_ctx.Process(target=_run_worker,
                           args=(q, file, name, expr, opt, hints, mode, scope))
    proc.start()
    proc.join(timeout=(TIMEOUT_MS / 1000) + 30)
    if proc.is_alive():
        proc.terminate()
        proc.join()

    rv            = ReturnValue()
    rv.error      = ReturnError.SUCCESS
    rv.build_time = 0.0
    rv.solve_times = []
    rv.status     = "UNKNOWN"
    if not q.empty():
        data = q.get_nowait()
        if data:
            rv.status      = data["status"]
            rv.build_time  = data["build_time"]
            rv.solve_times = data["solve_times"]
            rv.error       = data["error"]
    return rv, None


def _fmt_ms(t):
    if t is None:
        return f"{DIM}{'---':>7}{RESET}"
    ms = t * 1000
    if ms < 100:
        colour = GREEN
    elif ms < 500:
        colour = YELLOW
    else:
        colour = RED
    return f"{colour}{ms:7.1f}{RESET}"


def _coloured_status(s, expected):
    if s == "UNKNOWN":
        return f"{YELLOW}TIMEOUT{RESET}"
    if s == expected:
        return f"{GREEN}{s}{RESET}"
    return f"{RED}{s}{RESET}"


def _speedup(t_base, t_fast):
    if t_base and t_fast and t_fast > 0:
        ratio = t_base / t_fast
        if ratio >= 1.5:
            return f"  {CYAN}↑{ratio:.1f}×{RESET}"
    return ""


# ── main demo ──────────────────────────────────────────────────────────────────

def run_demo(demo):
    W = 72
    name, expr = demo["prop"]
    expected   = demo["expected"]
    mode       = demo.get("mode", "default")
    scope      = demo.get("scope", "all")

    print(f"\n{BOLD}{CYAN}{'━' * W}{RESET}")
    print(f"{BOLD}  {demo['label']}{RESET}")
    print(f"  {DIM}file:{RESET} {demo['file']}   "
          f"{DIM}mode:{RESET} {mode}/{scope}   "
          f"{DIM}property:{RESET} {name} = {expr}")
    print(f"{CYAN}{'─' * W}{RESET}")
    print(f"  {'Config':<20}  {'Result':<8}  "
          f"{'Build (ms)':>10}  {'Solve (ms)':>10}")
    print(f"  {'─'*20}  {'─'*8}  {'─'*10}  {'─'*10}")

    results = {}
    for cfg_label, opt, hints in CONFIGS:
        rv, exc = _run_isolated(demo["file"], name, expr, opt, hints, mode=mode, scope=scope)
        results[cfg_label] = (rv, exc)

        if exc or rv is None:
            status_str = f"{RED}ERROR{RESET}"
            build_str  = f"{DIM}{'---':>7}{RESET}"
            solve_str  = f"{DIM}{'---':>7}{RESET}"
        else:
            status_str = _coloured_status(rv.status, expected)
            build_str  = _fmt_ms(rv.build_time)
            solve_str  = _fmt_ms(rv.solve_times[0] if rv.solve_times else None)

        print(f"  {BOLD}{cfg_label}{RESET}  {status_str:<8}  "
              f"{build_str}   {solve_str}")

    # speedup summary
    def _solve_t(label):
        rv, exc = results.get(label, (None, None))
        if rv and rv.solve_times:
            return rv.solve_times[0]
        return None

    sp_opt  = _speedup(_solve_t("NONE  | no hint "), _solve_t("BASIC | no hint "))
    sp_hint = _speedup(_solve_t("NONE  | no hint "), _solve_t("NONE  | hint    "))
    sp_both = _speedup(_solve_t("NONE  | no hint "), _solve_t("BASIC | hint    "))

    if sp_opt or sp_hint or sp_both:
        print(f"\n  {DIM}speedup vs baseline (NONE | no hint):{RESET}")
        if sp_opt:
            print(f"    BASIC opt alone  :{sp_opt}")
        if sp_hint:
            print(f"    Hint alone       :{sp_hint}")
        if sp_both:
            print(f"    BASIC + hint     :{sp_both}")


def main():
    W = 72
    print(f"\n{BOLD}{'═' * W}")
    print(f"  CHC Verification — Live Demo")
    print(f"  Optimization Mode × Hint Mode Comparison")
    print(f"{'═' * W}{RESET}")
    print(f"  {DIM}NONE  = baseline (no variable optimisation)")
    print(f"  BASIC = optimised (symbolic variable detection)")
    print(f"  no hint  = verifier checks heading stays on 15° grid")
    print(f"  hint     = solver trusts heading is always on 15° grid")
    print(f"  mode/scope shown per demo (default/all or universal/terminating){RESET}")

    for i, demo in enumerate(DEMOS, 1):
        print(f"\n{BOLD}[{i}/{len(DEMOS)}] Running: {demo['label']} ...{RESET}", flush=True)
        run_demo(demo)

    print(f"\n{BOLD}{CYAN}{'━' * W}{RESET}")
    print(f"{BOLD}  Demo complete.{RESET}\n")


if __name__ == "__main__":
    main()
