"""
Performance tests for CHC verification in **specific** mode.

Run with:  pytest test_specific.py
           pytest test_specific.py -v
"""

import unittest
from helpers import *

class TestSpecificLoopCountScaling(PerformanceTestCase):
    """
    :x = :init; x += 1  repeated 50 and 100 times.
    With init=0  this mirrors TestDefaultLoopCountScaling for direct comparison.
    With init=50 the bound shifts by +50, stressing a larger absolute value range.

    perf_s_repeat_50.tl  (init=0): x goes 0 → 50.
    perf_s_repeat_100.tl (init=0): x goes 0 → 100.
    """

    MODE = "specific"

    def test_loop50_x_nonneg_pass(self):
        """init=0: x starts 0, increments 50 times => x >= 0 always."""
        self.load("perf_s_repeat_50.tl", params={"init": 0})
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_loop100_x_nonneg_pass(self):
        """init=0: x starts 0, increments 100 times => x >= 0 always."""
        self.load("perf_s_repeat_100.tl", params={"init": 0})
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_loop50_x_tight_pass(self):
        """init=0: x ends at 50. x <= 50 is the exact tight bound."""
        self.load("perf_s_repeat_50.tl", params={"init": 0})
        self.assert_and_time("x_tight", "x <= 50", "PASSED")

    def test_loop100_x_tight_pass(self):
        """init=0: x ends at 100. x <= 100 is the exact tight bound."""
        self.load("perf_s_repeat_100.tl", params={"init": 0})
        self.assert_and_time("x_tight", "x <= 100", "PASSED")

    def test_loop50_x_violated_fail(self):
        """init=0: x reaches 50 => x <= 25 violated."""
        self.load("perf_s_repeat_50.tl", params={"init": 0})
        self.assert_and_time("x_violated", "x <= 25", "FAILED")

    def test_loop100_x_violated_fail(self):
        """init=0: x reaches 100 => x <= 50 violated."""
        self.load("perf_s_repeat_100.tl", params={"init": 0})
        self.assert_and_time("x_violated", "x <= 50", "FAILED")

    def test_loop50_offset_tight_pass(self):
        """init=50: :x=:init sets x=50; after 50 iters x=100. x <= 100 holds."""
        self.load("perf_s_repeat_50.tl", params={"init": 50})
        self.assert_and_time("x_tight_offset", "x <= 100", "PASSED")

    def test_loop100_offset_tight_pass(self):
        """init=50: x reaches 150. x <= 150 holds (tight)."""
        self.load("perf_s_repeat_100.tl", params={"init": 50})
        self.assert_and_time("x_tight_offset", "x <= 150", "PASSED")

    def test_loop50_offset_violated_fail(self):
        """init=50: x reaches 100 => x <= 50 violated."""
        self.load("perf_s_repeat_50.tl", params={"init": 50})
        self.assert_and_time("x_violated_offset", "x <= 50", "FAILED")

    def test_loop100_offset_violated_fail(self):
        """init=50: x reaches 150 => x <= 100 violated."""
        self.load("perf_s_repeat_100.tl", params={"init": 50})
        self.assert_and_time("x_violated_offset", "x <= 100", "FAILED")


class TestSpecificNestingDepth(PerformanceTestCase):
    """
    Nested repeat loops: 3-deep (repeat 4 * 4 * 4) vs 4-deep (repeat 3 * 3 * 3 * 3).

    perf_s_nest_3.tl (start=0):  a=5,  b=25,  c=125.
    perf_s_nest_3.tl (start=10): a=15, b=35,  c=135.
    perf_s_nest_4.tl (start=0):  a=4,  b=16,  c=64,  d=256.
    """

    MODE = "specific"

    # 3-level nesting

    def test_nest3_all_nonneg_pass(self):
        """start=0: all counters start 0 and only increment => all >= 0."""
        self.load("perf_s_nest_3.tl", params={"start": 0})
        self.assert_and_time("all_nonneg", "And(a >= 0, b >= 0, c >= 0)", "PASSED")

    def test_nest3_c_tight_pass(self):
        """start=0: c ends at 125."""
        self.load("perf_s_nest_3.tl", params={"start": 0})
        self.assert_and_time("c_tight", "c <= 125", "PASSED")

    def test_nest3_c_violated_fail(self):
        """start=0: c reaches 125 => c <= 100 violated."""
        self.load("perf_s_nest_3.tl", params={"start": 0})
        self.assert_and_time("c_violated", "c <= 100", "FAILED")

    def test_nest3_offset_c_tight_pass(self):
        """start=10: c ends at 135. c <= 135 holds (tight)."""
        self.load("perf_s_nest_3.tl", params={"start": 10})
        self.assert_and_time("c_tight_offset", "c <= 135", "PASSED")

    def test_nest3_offset_c_violated_fail(self):
        """start=10: c reaches 135 => c <= 125 violated (SAT)."""
        self.load("perf_s_nest_3.tl", params={"start": 10})
        self.assert_and_time("c_violated_offset", "c <= 125", "FAILED")

    # 4-level nesting

    def test_nest4_all_nonneg_pass(self):
        """start=0: all 4 counters only increment => all >= 0"""
        self.load("perf_s_nest_4.tl", params={"start": 0})
        self.assert_and_time("all_nonneg", "And(a >= 0, b >= 0, c >= 0, d >= 0)", "PASSED")

    def test_nest4_d_tight_pass(self):
        """start=0: d ends at 256 — hardest UNSAT"""
        self.load("perf_s_nest_4.tl", params={"start": 0})
        self.assert_and_time("d_tight", "d <= 256", "PASSED")

    def test_nest4_d_violated_fail(self):
        """start=0: d reaches 256 => d <= 200 violated."""
        self.load("perf_s_nest_4.tl", params={"start": 0})
        self.assert_and_time("d_violated", "d <= 200", "FAILED")

    def test_nest4_offset_d_tight_pass(self):
        """start=10: d ends at 266 — tight bound shifts up by :start."""
        self.load("perf_s_nest_4.tl", params={"start": 10})
        self.assert_and_time("d_tight_offset", "d <= 266", "PASSED")

    def test_nest4_offset_d_violated_fail(self):
        """start=10: d reaches 266 => d <= 256 violated. Old tight bound no longer holds."""
        self.load("perf_s_nest_4.tl", params={"start": 10})
        self.assert_and_time("d_violated_offset", "d <= 256", "FAILED")


class TestSpecificWideState(PerformanceTestCase):
    """
    8-variable chained state (b += a, c += b, …, h += g) — 5 iterations.
    perf_s_wide.tl has NO literal initial assignments; every initial value
    comes from the params dict.
    """

    MODE = "specific"

    # positive initial state

    def test_wide_all_positive_pos_params_pass(self):
        """Params {a:1,…,h:8}: initial state already has all > 0 => all > 0 invariant holds.
        This PASSES in specific mode but would FAIL in default mode."""
        self.load("perf_s_wide.tl",
                  params={"a": 1, "b": 2, "c": 3, "d": 4,
                          "e": 5, "f": 6, "g": 7, "h": 8})
        self.assert_and_time(
            "all_positive",
            "And(a > 0, b > 0, c > 0, d > 0, e > 0, f > 0, g > 0, h > 0)",
            "PASSED",
        )

    def test_wide_a_tight_pass(self):
        """Params {a:1,…,h:8}: a = 1+#iters => a <= 6 is the exact tight bound."""
        self.load("perf_s_wide.tl",
                  params={"a": 1, "b": 2, "c": 3, "d": 4,
                          "e": 5, "f": 6, "g": 7, "h": 8})
        self.assert_and_time("a_tight", "a <= 6", "PASSED")

    def test_wide_a_violated_fail(self):
        """a reaches 6 => a <= 4 violated."""
        self.load("perf_s_wide.tl",
                  params={"a": 1, "b": 2, "c": 3, "d": 4,
                          "e": 5, "f": 6, "g": 7, "h": 8})
        self.assert_and_time("a_violated", "a <= 4", "FAILED")

    def test_wide_h_nonneg_pass(self):
        """h >= 0 holds throughout (h only grows)."""
        self.load("perf_s_wide.tl",
                  params={"a": 1, "b": 2, "c": 3, "d": 4,
                          "e": 5, "f": 6, "g": 7, "h": 8})
        self.assert_and_time("h_nonneg", "h >= 0", "PASSED")

    def test_wide_h_tight_pass(self):
        """h <= 2211 is the exact tight bound"""
        self.load("perf_s_wide.tl",
                  params={"a": 1, "b": 2, "c": 3, "d": 4,
                          "e": 5, "f": 6, "g": 7, "h": 8})
        self.assert_and_time("h_tight", "h <= 2211", "PASSED")

    def test_wide_h_violated_fail(self):
        """h reaches 2211 => h <= 2000 violated."""
        self.load("perf_s_wide.tl",
                  params={"a": 1, "b": 2, "c": 3, "d": 4,
                          "e": 5, "f": 6, "g": 7, "h": 8})
        self.assert_and_time("h_violated", "h <= 2000", "FAILED")

    def test_wide_all_positive_zero_params_fail(self):
        """Params all-zero: a=0 at initial state violates a > 0."""
        self.load("perf_s_wide.tl",
                  params={"a": 0, "b": 0, "c": 0, "d": 0,
                          "e": 0, "f": 0, "g": 0, "h": 0})
        self.assert_and_time(
            "all_positive",
            "And(a > 0, b > 0, c > 0, d > 0, e > 0, f > 0, g > 0, h > 0)",
            "FAILED",
        )

    def test_wide_zero_h_tight_pass(self):
        """Params all-zero: h ends at 495. h <= 495 holds (tight). Lower bound than pos-params."""
        self.load("perf_s_wide.tl",
                  params={"a": 0, "b": 0, "c": 0, "d": 0,
                          "e": 0, "f": 0, "g": 0, "h": 0})
        self.assert_and_time("h_tight_zero", "h <= 495", "PASSED")

    def test_wide_zero_h_violated_fail(self):
        """Params all-zero: h reaches 495 => h <= 400 violated (SAT)."""
        self.load("perf_s_wide.tl",
                  params={"a": 0, "b": 0, "c": 0, "d": 0,
                          "e": 0, "f": 0, "g": 0, "h": 0})
        self.assert_and_time("h_violated_zero", "h <= 400", "FAILED")

class TestSpecificBranchingDensity(PerformanceTestCase):
    """
    An 8-iteration loop whose body contains 4 sequential if/else blocks.
    All four thresholds are derived from a single param :thresh:
      t1=thresh, t2=thresh+1, t3=thresh+2, t4=thresh+3.
    """

    MODE = "specific"

    # thresh = 2

    def test_branches_thresh2_x_nonneg_pass(self):
        """thresh=2: x starts 0 and only increments => x >= 0 holds."""
        self.load("perf_s_branches.tl", params={"thresh": 2})
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_branches_thresh2_x_tight_pass(self):
        """thresh=2: x ends at 8. x <= 8 is the exact tight bound."""
        self.load("perf_s_branches.tl", params={"thresh": 2})
        self.assert_and_time("x_tight", "x <= 8", "PASSED")

    def test_branches_thresh2_acc_nonneg_pass(self):
        """thresh=2: all branch increments are +1 => acc >= 0 holds throughout."""
        self.load("perf_s_branches.tl", params={"thresh": 2})
        self.assert_and_time("acc_nonneg", "acc >= 0", "PASSED")

    def test_branches_thresh2_acc_tight_pass(self):
        """thresh=2: acc ends at 18. acc <= 18 is the tight bound."""
        self.load("perf_s_branches.tl", params={"thresh": 2})
        self.assert_and_time("acc_tight", "acc <= 18", "PASSED")

    def test_branches_thresh2_acc_violated_fail(self):
        """thresh=2: acc reaches 18 => acc <= 10 violated (SAT)."""
        self.load("perf_s_branches.tl", params={"thresh": 2})
        self.assert_and_time("acc_violated", "acc <= 10", "FAILED")

    # thresh = 4

    def test_branches_thresh4_acc_nonneg_pass(self):
        """thresh=4: higher threshold delays branch firing — acc >= 0 still holds."""
        self.load("perf_s_branches.tl", params={"thresh": 4})
        self.assert_and_time("acc_nonneg", "acc >= 0", "PASSED")

    def test_branches_thresh4_acc_tight_pass(self):
        """thresh=4: acc ends at 10. acc <= 10 tight bound."""
        self.load("perf_s_branches.tl", params={"thresh": 4})
        self.assert_and_time("acc_tight", "acc <= 10", "PASSED")

    def test_branches_thresh4_acc_violated_fail(self):
        """thresh=4: acc reaches 10 => acc <= 5 violated (SAT)."""
        self.load("perf_s_branches.tl", params={"thresh": 4})
        self.assert_and_time("acc_violated", "acc <= 5", "FAILED")

    def test_branches_thresh4_x_violated_fail(self):
        """thresh=4: x reaches 8 => x <= 4 violated (fast SAT)."""
        self.load("perf_s_branches.tl", params={"thresh": 4})
        self.assert_and_time("x_violated", "x <= 4", "FAILED")

class TestSpecificTrigScaling(PerformanceTestCase):
    """
    'forward :step; right 90' repeated 10 / 20 times.
    :step is a concrete param; heading cycles through {0, 90, 180, 270}.
    """

    MODE = "specific"

    # 10-iteration trig

    def test_trig10_pen_up_pass(self):
        """No pen commands => pendown stays False (step=10)."""
        self.load("perf_s_trig_10.tl", params={"step": 10},
                  hints=["heading_on_grid_always"])
        self.assert_and_time("pen_up", "Not(pendown)", "PASSED")

    def test_trig10_heading_quarters_pass(self):
        """Heading stays in {0, 90, 180, 270} for 10 iterations (step=10)."""
        self.load("perf_s_trig_10.tl", params={"step": 10},
                  hints=["heading_on_grid_always"])
        self.assert_and_time(
            "heading_quarters",
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
            "PASSED",
        )

    def test_trig10_ycor_violated_fail(self):
        """ycor goes negative at step 2 => ycor >= 0 violated (step=10)."""
        self.load("perf_s_trig_10.tl", params={"step": 10},
                  hints=["heading_on_grid_always"])
        self.assert_and_time("ycor_nonneg", "ycor >= 0", "FAILED")

    def test_trig10_large_step_heading_pass(self):
        """step=50: heading cycling is identical — {0,90,180,270} invariant still holds."""
        self.load("perf_s_trig_10.tl", params={"step": 50},
                  hints=["heading_on_grid_always"])
        self.assert_and_time(
            "heading_quarters",
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
            "PASSED",
        )

    def test_trig10_large_step_ycor_violated_fail(self):
        """step=50: ycor goes to -50 at step 2 => ycor >= 0 violated (larger magnitude)."""
        self.load("perf_s_trig_10.tl", params={"step": 50},
                  hints=["heading_on_grid_always"])
        self.assert_and_time("ycor_nonneg", "ycor >= 0", "FAILED")

    # 20-iteration trig loop

    def test_trig20_pen_up_pass(self):
        """No pen commands => pendown stays False (step=10, repeat 20)."""
        self.load("perf_s_trig_20.tl", params={"step": 10},
                  hints=["heading_on_grid_always"])
        self.assert_and_time("pen_up", "Not(pendown)", "PASSED")

    def test_trig20_heading_quarters_pass(self):
        """Heading stays in {0, 90, 180, 270} for 20 iterations (step=10)."""
        self.load("perf_s_trig_20.tl", params={"step": 10},
                  hints=["heading_on_grid_always"])
        self.assert_and_time(
            "heading_quarters",
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
            "PASSED",
        )

    def test_trig20_ycor_violated_fail(self):
        """ycor goes negative — SAT query on the 20-iteration version (step=10)."""
        self.load("perf_s_trig_20.tl", params={"step": 10},
                  hints=["heading_on_grid_always"])
        self.assert_and_time("ycor_nonneg", "ycor >= 0", "FAILED")

class TestSpecificPropertyComplexity(PerformanceTestCase):
    """
    Fixed program (perf_s_repeat_100.tl, x: 0→100 with init=0) and
    perf_s_wide.tl with positive params, but increasingly complex property
    expressions. 
    """

    MODE = "specific"

    def test_prop_single_atom_pass(self):
        """Single atom: x >= 0."""
        self.load("perf_s_repeat_100.tl", params={"init": 0})
        self.assert_and_time("single_atom", "x >= 0", "PASSED")

    def test_prop_two_atom_conj_pass(self):
        """Two-atom conjunction: And(x >= 0, x <= 100)."""
        self.load("perf_s_repeat_100.tl", params={"init": 0})
        self.assert_and_time("two_atom_conj", "And(x >= 0, x <= 100)", "PASSED")

    def test_prop_exact_disjunction_pass(self):
        """101-way disjunction: Or(x==0, x==1, ..., x==100). Hard UNSAT — explicit enumeration."""
        self.load("perf_s_repeat_100.tl", params={"init": 0})
        expr = "Or(" + ", ".join(f"x == {i}" for i in range(101)) + ")"
        self.assert_and_time("exact_disj_101", expr, "PASSED")

    def test_prop_wide_chain_conj_pass(self):
        """8-atom conjunction across all chained vars — hardest multi-var UNSAT in specific mode."""
        self.load("perf_s_wide.tl",
                  params={"a": 1, "b": 2, "c": 3, "d": 4,
                          "e": 5, "f": 6, "g": 7, "h": 8})
        self.assert_and_time(
            "chain_all_pos",
            "And(a > 0, b > 0, c > 0, d > 0, e > 0, f > 0, g > 0, h > 0)",
            "PASSED",
        )

    def test_prop_shifted_loop_two_atom_pass(self):
        """init=50: x stays in [0, 150]. Two-atom conjunction And(x >= 0, x <= 150) holds."""
        self.load("perf_s_repeat_100.tl", params={"init": 50})
        self.assert_and_time("two_atom_shifted", "And(x >= 0, x <= 150)", "PASSED")

    def test_prop_shifted_loop_tight_fail(self):
        """init=50: x reaches 150 => x <= 100 violated. Shows that param shifts the bound."""
        self.load("perf_s_repeat_100.tl", params={"init": 50})
        self.assert_and_time("tight_shifted", "x <= 100", "FAILED")


if __name__ == "__main__":
    unittest.main()
