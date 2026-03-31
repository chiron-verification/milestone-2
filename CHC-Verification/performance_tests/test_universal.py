import unittest
from helpers import *


class TestUniversalLoopCountScaling(PerformanceTestCase):
    # Universal mode: scope='all' fails lower-bound props (unconstrained pc=0);
    # scope='terminating' passes (x ends at N).
    MODE = "universal"

    def test_loop10_all_x_nonneg_fail(self):
        self.load("perf_repeat_10.tl", property_scope="all")
        self.assert_and_time("x_nonneg-all", "x >= 0", "FAILED")

    def test_loop50_all_x_nonneg_fail(self):
        self.load("perf_repeat_50.tl", property_scope="all")
        self.assert_and_time("x_nonneg-all", "x >= 0", "FAILED")

    def test_loop100_all_x_nonneg_fail(self):
        self.load("perf_repeat_100.tl", property_scope="all")
        self.assert_and_time("x_nonneg-all", "x >= 0", "FAILED")

    def test_loop10_term_x_nonneg_pass(self):
        self.load("perf_repeat_10.tl", property_scope="terminating")
        self.assert_and_time("x_nonneg-terminating", "x >= 0", "PASSED")

    def test_loop50_term_x_nonneg_pass(self):
        self.load("perf_repeat_50.tl", property_scope="terminating")
        self.assert_and_time("x_nonneg", "x >= 0", "PASSED")

    def test_loop100_term_x_nonneg_pass(self):
        self.load("perf_repeat_100.tl", property_scope="terminating")
        self.assert_and_time("x_nonneg-terminating", "x >= 0", "PASSED")

    def test_loop10_term_x_tight_pass(self):
        self.load("perf_repeat_10.tl", property_scope="terminating")
        self.assert_and_time("x_tight", "x <= 10", "PASSED")

    def test_loop50_term_x_tight_pass(self):
        self.load("perf_repeat_50.tl", property_scope="terminating")
        self.assert_and_time("x_tight", "x <= 50", "PASSED")

    def test_loop100_term_x_tight_pass(self):
        self.load("perf_repeat_100.tl", property_scope="terminating")
        self.assert_and_time("x_tight", "x <= 100", "PASSED")

    def test_loop10_term_x_violated_fail(self):
        self.load("perf_repeat_10.tl", property_scope="terminating")
        self.assert_and_time("x_violated", "x <= 5", "FAILED")

    def test_loop50_term_x_violated_fail(self):
        self.load("perf_repeat_50.tl", property_scope="terminating")
        self.assert_and_time("x_violated", "x <= 25", "FAILED")

    def test_loop100_term_x_violated_fail(self):
        self.load("perf_repeat_100.tl", property_scope="terminating")
        self.assert_and_time("x_violated", "x <= 50", "FAILED")


class TestUniversalNestingDepth(PerformanceTestCase):
    # scope='terminating': a=4,b=16,c=64 (3-level); a=3,b=9,c=27,d=81 (4-level).
    MODE = "universal"

    def test_nest3_all_c_nonneg_fail(self):
        self.load("perf_deep_nest_3.tl", property_scope="all")
        self.assert_and_time("c_nonneg", "c >= 0", "FAILED")

    def test_nest4_all_d_nonneg_fail(self):
        self.load("perf_deep_nest_4.tl", property_scope="all")
        self.assert_and_time("d_nonneg", "d >= 0", "FAILED")

    def test_nest3_term_all_nonneg_pass(self):
        self.load("perf_deep_nest_3.tl", property_scope="terminating")
        self.assert_and_time("all_nonneg", "And(a >= 0, b >= 0, c >= 0)", "PASSED")

    def test_nest3_term_c_tight_pass(self):
        self.load("perf_deep_nest_3.tl", property_scope="terminating")
        self.assert_and_time("c_tight", "c <= 64", "PASSED")

    def test_nest3_term_c_violated_fail(self):
        self.load("perf_deep_nest_3.tl", property_scope="terminating")
        self.assert_and_time("c_violated", "c <= 60", "FAILED")

    def test_nest4_term_all_nonneg_pass(self):
        self.load("perf_deep_nest_4.tl", property_scope="terminating")
        self.assert_and_time("all_nonneg", "And(a >= 0, b >= 0, c >= 0, d >= 0)", "PASSED")

    def test_nest4_term_d_tight_pass(self):
        self.load("perf_deep_nest_4.tl", property_scope="terminating")
        self.assert_and_time("d_tight", "d <= 81", "PASSED")

    def test_nest4_term_d_violated_fail(self):
        self.load("perf_deep_nest_4.tl", property_scope="terminating")
        self.assert_and_time("d_violated", "d <= 70", "FAILED")


class TestUniversalWideState(PerformanceTestCase):
    # scope='terminating': a=6,b=22,c=63,d=154,e=336,f=672,g=1254,h=2211.
    MODE = "universal"

    def test_wide_all_all_positive_fail(self):
        self.load("perf_wide_vars.tl", property_scope="all")
        self.assert_and_time(
            "all_positive",
            "And(a > 0, b > 0, c > 0, d > 0, e > 0, f > 0, g > 0, h > 0)",
            "FAILED",
        )

    def test_wide_term_all_positive_pass(self):
        self.load("perf_wide_vars.tl", property_scope="terminating")
        self.assert_and_time(
            "all_positive",
            "And(a > 0, b > 0, c > 0, d > 0, e > 0, f > 0, g > 0, h > 0)",
            "PASSED",
        )

    def test_wide_term_a_tight_pass(self):
        self.load("perf_wide_vars.tl", property_scope="terminating")
        self.assert_and_time("a_tight", "a <= 6", "PASSED")

    def test_wide_term_a_violated_fail(self):
        self.load("perf_wide_vars.tl", property_scope="terminating")
        self.assert_and_time("a_violated", "a <= 4", "FAILED")

    def test_wide_term_h_nonneg_pass(self):
        self.load("perf_wide_vars.tl", property_scope="terminating")
        self.assert_and_time("h_nonneg", "h >= 0", "PASSED")

    def test_wide_term_h_tight_pass(self):
        self.load("perf_wide_vars.tl", property_scope="terminating")
        self.assert_and_time("h_tight", "h <= 2211", "PASSED")

    def test_wide_term_h_violated_fail(self):
        self.load("perf_wide_vars.tl", property_scope="terminating")
        self.assert_and_time("h_violated", "h <= 2000", "FAILED")


class TestUniversalBranchingDensity(PerformanceTestCase):
    # Final values: x=6, acc=14.
    MODE = "universal"

    def test_branches_all_x_nonneg_fail(self):
        self.load("perf_many_branches.tl", property_scope="all")
        self.assert_and_time("x_nonneg", "x >= 0", "FAILED")

    def test_branches_all_acc_nonneg_fail(self):
        self.load("perf_many_branches.tl", property_scope="all")
        self.assert_and_time("acc_nonneg", "acc >= 0", "FAILED")

    def test_branches_term_x_tight_pass(self):
        self.load("perf_many_branches.tl", property_scope="terminating")
        self.assert_and_time("x_tight", "x <= 6", "PASSED")

    def test_branches_term_x_violated_fail(self):
        self.load("perf_many_branches.tl", property_scope="terminating")
        self.assert_and_time("x_violated", "x <= 3", "FAILED")

    def test_branches_term_acc_nonneg_pass(self):
        self.load("perf_many_branches.tl", property_scope="terminating")
        self.assert_and_time("acc_nonneg", "acc >= 0", "PASSED")

    def test_branches_term_acc_violated_fail(self):
        self.load("perf_many_branches.tl", property_scope="terminating")
        self.assert_and_time("acc_violated", "acc <= 5", "FAILED")


class TestUniversalTrigScaling(PerformanceTestCase):
    # Universal init: pendown=True, heading on 15-degree grid, xcor/ycor unconstrained.
    MODE = "universal"

    def test_trig10_pen_down_pass(self):
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"], property_scope="all")
        self.assert_and_time("pen_down", "pendown", "PASSED")

    def test_trig10_not_pendown_fail(self):
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"], property_scope="all")
        self.assert_and_time("not_pendown", "Not(pendown)", "FAILED")

    def test_trig10_heading_range_pass(self):
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"], property_scope="all")
        self.assert_and_time("heading_range", "And(heading >= 0, heading < 360)", "PASSED")

    def test_trig10_heading_quarters_fail(self):
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"], property_scope="all")
        self.assert_and_time(
            "heading_quarters",
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
            "FAILED",
        )

    def test_trig10_ycor_nonneg_fail(self):
        self.load("perf_trig_10.tl", hints=["heading_on_grid_always"], property_scope="all")
        self.assert_and_time("ycor_nonneg", "ycor >= 0", "FAILED")

if __name__ == "__main__":
    unittest.main()