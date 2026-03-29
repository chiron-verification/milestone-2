"""
Performance tests for CHC verification in **default** mode.

Run with:  pytest test_default.py.         (see timing output)
           pytest test_default.py -v     (verbose + timing)
"""

import unittest
from helpers import *


class TestDefaultLoopCountScaling(PerformanceTestCase):
    """
    Same body (x += 1) with repeat counts 10, 50, and 100.
    Shows how loop count affects build_time and solve_time.
    """

    MODE = "default"

    def test_loop10_x_nonneg_pass(self):
        """x starts 0 and only increments => x >= 0 (repeat 10)."""
        self.load("perf_repeat_10.tl")
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_loop50_x_nonneg_pass(self):
        """x starts 0 and only increments => x >= 0 (repeat 50)."""
        self.load("perf_repeat_50.tl")
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_loop100_x_nonneg_pass(self):
        """x starts 0 and only increments => x >= 0 (repeat 100)."""
        self.load("perf_repeat_100.tl")
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_loop10_x_tight_pass(self):
        """x <= 10 is the exact tight bound (repeat 10)."""
        self.load("perf_repeat_10.tl")
        self.assert_and_time("x_tight", "x <= 10", "PASSED")

    def test_loop50_x_tight_pass(self):
        """x <= 50 tight bound (repeat 50)"""
        self.load("perf_repeat_50.tl")
        self.assert_and_time("x_tight", "x <= 50", "PASSED")

    def test_loop100_x_tight_pass(self):
        """x <= 100 tight bound (repeat 100)."""
        self.load("perf_repeat_100.tl")
        self.assert_and_time("x_tight", "x <= 100", "PASSED")

    def test_loop10_x_violated_fail(self):
        """x reaches 10 => x <= 5 violated. Expect fast SAT (repeat 10)."""
        self.load("perf_repeat_10.tl")
        self.assert_and_time("x_violated", "x <= 5", "FAILED")

    def test_loop50_x_violated_fail(self):
        """x reaches 50 => x <= 5 violated (repeat 50). Compare SAT time."""
        self.load("perf_repeat_50.tl")
        self.assert_and_time("x_violated", "x <= 5", "FAILED")

    def test_loop100_x_violated_fail(self):
        """x reaches 100 => x <= 5 violated (repeat 100). Compare SAT time."""
        self.load("perf_repeat_100.tl")
        self.assert_and_time("x_violated", "x <= 5", "FAILED")

class TestDefaultNestingDepth(PerformanceTestCase):
    """
    Nested repeat loops: 3-deep (repeat 4 * 4 * 4) vs 4-deep (repeat 3 * 3 * 3 * 3).

    perf_deep_nest_3.tl: a ends at 4, b at 16, c at 64.
    perf_deep_nest_4.tl: a ends at 3, b at  9, c at 27, d at 81.
    """

    MODE = "default"

    # 3-level nesting
    def test_nest3_all_nonneg_pass(self):
        """All counters start at 0 and only increment => all >= 0 (easy UNSAT)."""
        self.load("perf_deep_nest_3.tl")
        self.assert_and_time("all_nonneg", "And(a >= 0, b >= 0, c >= 0)", "PASSED")

    def test_nest3_c_tight_pass(self):
        """c <= 64 is the exact tight bound — hard UNSAT (requires full nested invariant)."""
        self.load("perf_deep_nest_3.tl")
        self.assert_and_time("c_tight", "c <= 64", "PASSED")

    def test_nest3_c_violated_fail(self):
        """c reaches 64 => c <= 60 violated. SAT (counterexample at last inner iterations)."""
        self.load("perf_deep_nest_3.tl")
        self.assert_and_time("c_violated", "c <= 60", "FAILED")

    # 4-level nesting
    def test_nest4_all_nonneg_pass(self):
        """All 4 counters >= 0 (easy UNSAT). Note build_time vs 3-level."""
        self.load("perf_deep_nest_4.tl")
        self.assert_and_time("all_nonneg", "And(a >= 0, b >= 0, c >= 0, d >= 0)", "PASSED")

    def test_nest4_d_tight_pass(self):
        """d <= 81 tight bound (4-level, hard UNSAT — deeper invariant required)."""
        self.load("perf_deep_nest_4.tl")
        self.assert_and_time("d_tight", "d <= 81", "PASSED")

    def test_nest4_d_violated_fail(self):
        """d reaches 81 => d <= 70 violated (SAT)."""
        self.load("perf_deep_nest_4.tl")
        self.assert_and_time("d_violated", "d <= 70", "FAILED")


class TestDefaultWideState(PerformanceTestCase):
    """
    8 chained variables updated every iteration of a 5-step loop.
    Each variable depends on the previous one (b += a, c += b, …), so the
    CHC predicate must track an 8-dimensional arithmetic state.

    Final values after 5 iterations: a=6, b=22, c=63, d=154, e=336,
    f=672, g=1254, h=2211.  All variables start positive and grow.
    """

    MODE = "default"

    def test_wide_all_positive_pass(self):
        """All 8 vars start positive and only grow => all > 0 always (easy UNSAT)."""
        self.load("perf_wide_vars.tl")
        self.assert_and_time(
            "all_positive",
            "And(a > 0, b > 0, c > 0, d > 0, e > 0, f > 0, g > 0, h > 0)",
            "PASSED",
        )

    def test_wide_a_tight_pass(self):
        """a = 1 + #iters => a <= 6 is the exact tight bound after 5 iterations."""
        self.load("perf_wide_vars.tl")
        self.assert_and_time("a_tight", "a <= 6", "PASSED")

    def test_wide_a_violated_fail(self):
        """a reaches 5 in iteration 4 => a <= 4 violated (SAT)."""
        self.load("perf_wide_vars.tl")
        self.assert_and_time("a_violated", "a <= 4", "FAILED")

    def test_wide_h_nonneg_pass(self):
        """h >= 0 holds (h only grows). Requires Spacer to track the full 8-var chain."""
        self.load("perf_wide_vars.tl")
        self.assert_and_time("h_nonneg", "h >= 0", "PASSED")

    def test_wide_h_tight_pass(self):
        """h <= 2211 is the tight exact bound — hardest UNSAT in this class."""
        self.load("perf_wide_vars.tl")
        self.assert_and_time("h_tight", "h <= 2211", "PASSED")


class TestDefaultBranchingDensity(PerformanceTestCase):
    """
    A 6-iteration loop whose body contains 4 sequential if/else blocks,
    each guarded by a different threshold on x (>1, >2, >3, >4).
    This creates 4x as many CHC rules per iteration as a branch-free loop.
    """

    MODE = "default"

    def test_branches_x_nonneg_pass(self):
        """x starts 0 and only increments => x >= 0."""
        self.load("perf_many_branches.tl")
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_branches_x_tight_pass(self):
        """x <= 6 is the exact upper bound (6 loop iterations)."""
        self.load("perf_many_branches.tl")
        self.assert_and_time("x_tight", "x <= 6", "PASSED")

    def test_branches_acc_nonneg_pass(self):
        """acc only accumulates non-negative increments => acc >= 0."""
        self.load("perf_many_branches.tl")
        self.assert_and_time("acc_nonneg", "acc >= 0", "PASSED")

    def test_branches_x_violated_fail(self):
        """x reaches 6 => x <= 3 violated (SAT). Tests early-exit on SAT."""
        self.load("perf_many_branches.tl")
        self.assert_and_time("x_violated", "x <= 3", "FAILED")

    def test_branches_acc_violated_fail(self):
        """acc reaches 6 by iteration 4 => acc <= 5 violated."""
        self.load("perf_many_branches.tl")
        self.assert_and_time("acc_violated", "acc <= 5", "FAILED")


class TestDefaultTrigScaling(PerformanceTestCase):
    """
    'forward 10; right 90' repeated N times (N=10, N=20).
    """

    MODE = "default"

    # 10-iteration trig loop

    def test_trig10_ycor_violated_fail(self):
        """ycor goes to -10 at step 2 => ycor >= 0 violated."""
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"])
        self.assert_and_time("ycor_nonneg", "ycor >= 0", "FAILED")

    def test_trig10_pen_up_pass(self):
        """No pen commands => pendown stays False."""
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"])
        self.assert_and_time("pen_up", "Not(pendown)", "PASSED")

    def test_trig10_heading_quarters_pass(self):
        """Heading stays in {0,90,180,270}"""
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"])
        self.assert_and_time(
            "heading_quarters",
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
            "PASSED",
        )

    # 20-iteration trig loop (same structure, more IR nodes)

    def test_trig20_ycor_violated_fail(self):
        """SAT query on 20-iteration version"""
        self.load("perf_trig_20.tl", hints=["heading_on_grid_always"])
        self.assert_and_time("ycor_nonneg", "ycor >= 0", "FAILED")

    def test_trig20_pen_up_pass(self):
        """No pen commands => pendown stays False (repeat 20)"""
        self.load("perf_trig_20.tl", hints=["heading_on_grid_always"])
        self.assert_and_time("pen_up", "Not(pendown)", "PASSED")

    def test_trig20_heading_quarters_pass(self):
        """Heading stays in {0,90,180,270}"""
        self.load("perf_trig_20.tl", hints=["heading_on_grid_always"])
        self.assert_and_time(
            "heading_quarters",
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
            "PASSED",
        )


# 6. Heading-grid check cost

class TestDefaultHeadingGridCost(PerformanceTestCase):
    """
    Cost of the heading-grid query (check_heading_always_on_grid hint) as
    the number of turns in a loop grows from 20 to 50.   """

    MODE = "default"

    def test_turns20_heading_binary_pass(self):
        """Heading visits only {0, 345} => Or(heading==0, heading==345) is invariant."""
        self.load("perf_turns_20.tl", hints=["check_heading_always_on_grid"])
        result, _, _ = self.assert_and_time(
            "heading_binary", "Or(heading == 0, heading == 345)", "PASSED"
        )
        self.assertEqual(result.heading_grid_safe, "PASSED",
            f"Expected heading_grid_safe=PASSED, got {result.heading_grid_safe}")

    def test_turns50_heading_binary_pass(self):
        """Invariant on repeat 50"""
        self.load("perf_turns_50.tl", hints=["check_heading_always_on_grid"])
        result, _, _ = self.assert_and_time(
            "heading_binary", "Or(heading == 0, heading == 345)", "PASSED"
        )
        self.assertEqual(result.heading_grid_safe, "PASSED",
            f"Expected heading_grid_safe=PASSED, got {result.heading_grid_safe}")

    def test_turns20_heading_nonneg_pass(self):
        """heading >= 0. Isolates heading-grid check cost."""
        self.load("perf_turns_20.tl", hints=["check_heading_always_on_grid"])
        result, _, _ = self.assert_and_time("heading_nonneg", "heading >= 0", "PASSED")
        self.assertEqual(result.heading_grid_safe, "PASSED",
            f"Expected heading_grid_safe=PASSED, got {result.heading_grid_safe}")

    def test_turns50_heading_nonneg_pass(self):
        """Same loose property on repeat 50. Grid check should dominate solve time."""
        self.load("perf_turns_50.tl", hints=["check_heading_always_on_grid"])
        result, _, _ = self.assert_and_time("heading_nonneg", "heading >= 0", "PASSED")
        self.assertEqual(result.heading_grid_safe, "PASSED",
            f"Expected heading_grid_safe=PASSED, got {result.heading_grid_safe}")


# 7. Property-expression complexity 

class TestDefaultPropertyComplexity(PerformanceTestCase):
    """
    Fixed program (perf_repeat_10.tl, x goes 0=>10), but increasingly complex property
    """

    MODE = "default"

    def test_prop_single_atom_pass(self):
        """Single atom: x >= 0."""
        self.load("perf_repeat_10.tl")
        self.assert_and_time("single_atom", "x >= 0", "PASSED")

    def test_prop_two_atom_conj_pass(self):
        """Two-atom conjunction: And(x >= 0, x <= 10)."""
        self.load("perf_repeat_10.tl")
        self.assert_and_time("two_atom_conj", "And(x >= 0, x <= 10)", "PASSED")

    def test_prop_exact_disjunction_pass(self):
        """11-way disjunction: Or(x==0, x==1, ..., x==10)"""
        self.load("perf_repeat_10.tl")
        expr = "Or(" + ", ".join(f"x == {i}" for i in range(11)) + ")"
        self.assert_and_time("exact_disj_11", expr, "PASSED")

    def test_prop_heading_grid_24_pass(self):
        """24-way disjunction: Or(heading==0, heading==15, ..., heading==345).
        Uses perf_turns_20.tl; heading visits {0,345} which are both in the set."""
        self.load("perf_turns_20.tl", hints=["heading_on_grid_always"])
        expr = "Or(" + ", ".join(f"heading == {deg}" for deg in range(0, 360, 15)) + ")"
        self.assert_and_time("heading_grid_24", expr, "PASSED")


# class TestDefaultComboStress(PerformanceTestCase):
#     """
#     perf_combo.tl: 5-iteration loop with a conditional that selects between
#     a movement branch (forward :step; right 90) and a pure-turn branch (left 90).
#     Exercises trig rules, branching, and multi-variable state simultaneously.

#     Execution trace (default: xcor=0, ycor=0, heading=0, step=0, acc=0):
#       iter 1: step=1, step>2 false => left 90 (h=90),  acc=1
#       iter 2: step=2, step>2 false => left 90 (h=180), acc=2
#       iter 3: step=3, step>2 true  => fwd 3 at h=180 (xcor=-3), right 90 (h=90), acc=5
#       iter 4: step=4, step>2 true  => fwd 4 at h=90  (ycor=4),  right 90 (h=0),  acc=9
#       iter 5: step=5, step>2 true  => fwd 5 at h=0   (xcor=2),  right 90 (h=270),acc=14
#     Final: xcor=2, ycor=4, heading=270, step=5, acc=14.
#     """

#     MODE = "default"

#     def test_combo_step_nonneg_pass(self):
#         """step counter is always >= 0 (easy UNSAT)."""
#         self.load("perf_combo.tl", hints=["heading_on_grid_always"])
#         self.assert_and_time("step_nonneg", "step >= 0", "PASSED")

#     def test_combo_acc_nonneg_pass(self):
#         """acc only increases => acc >= 0 always."""
#         self.load("perf_combo.tl", hints=["heading_on_grid_always"])
#         self.assert_and_time("acc_nonneg", "acc >= 0", "PASSED")

#     def test_combo_step_tight_pass(self):
#         """step <= 5 is the exact tight bound (hard UNSAT — needs step invariant)."""
#         self.load("perf_combo.tl", hints=["heading_on_grid_always"])
#         self.assert_and_time("step_tight", "step <= 5", "PASSED")

#     def test_combo_step_violated_fail(self):
#         """step reaches 5 => step <= 3 violated (SAT). Tests SAT on mixed program."""
#         self.load("perf_combo.tl", hints=["heading_on_grid_always"])
#         self.assert_and_time("step_violated", "step <= 3", "FAILED")

#     def test_combo_acc_tight_pass(self):
#         """acc <= 14 is the exact tight bound — hardest UNSAT (trig + branch + arithmetic)."""
#         self.load("perf_combo.tl", hints=["heading_on_grid_always"])
#         self.assert_and_time("acc_tight", "acc <= 14", "PASSED")


if __name__ == "__main__":
    unittest.main()
