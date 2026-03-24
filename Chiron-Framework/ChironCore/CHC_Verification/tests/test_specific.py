"""
Tests for CHC verification in **specific** mode.
"""

from helpers import *


class TestSpecificArithmetic(ChironTestCase):
    """Arithmetic properties where params control initial variable values."""

    MODE = "specific"

    def test_arith_rbw_z_nonneg_pass(self):
        """With step=50: y=100, z=150. z >= 0 at all states."""
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_pass("z_nonneg", "z >= 0")

    def test_arith_rbw_z_upper_fail(self):
        """With step=50: z reaches 150 -> z <= 100 violated."""
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_fail("z_upper", "z <= 100")

    def test_arith_rbw_step_nonneg_pass(self):
        """step is never modified -> step=50 >= 0 always holds."""
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_pass("step_pos", "step >= 0")

    def test_arith_rbw_step_small_fail(self):
        """step=50 -> step <= 30 violated."""
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_fail("step_small", "step <= 30")

    def test_arith_scale_pos_pass(self):
        """With scale=10: result reaches 50. result >= 0 holds throughout."""
        self.load("param_scale.tl", params={"scale": 10})
        self.assert_pass("result_nonneg", "result >= 0")

    def test_arith_scale_tight_fail(self):
        """With scale=10: result reaches 50. result <= 30 violated."""
        self.load("param_scale.tl", params={"scale": 10})
        self.assert_fail("result_tight", "result <= 30")

    def test_arith_scale_neg_fail(self):
        """With scale=-5: result = -25. result >= 0 violated."""
        self.load("param_scale.tl", params={"scale": -5})
        self.assert_fail("result_nonneg", "result >= 0")

    def test_arith_param_loop_acc_nonneg_pass(self):
        """With start=0: acc goes 0->10->20->30. acc >= 0 always."""
        self.load("param_loop.tl", params={"start": 0})
        self.assert_pass("acc_nonneg", "acc >= 0")

    def test_arith_param_loop_acc_tight_fail(self):
        """With start=0: acc reaches 30. acc <= 20 violated."""
        self.load("param_loop.tl", params={"start": 0})
        self.assert_fail("acc_tight", "acc <= 20")

    def test_arith_param_cond_truebranch_pass(self):
        """With init=80 (>50): val goes 80->70. val >= 0 holds."""
        self.load("param_cond.tl", params={"init": 80})
        self.assert_pass("val_nonneg", "val >= 0")

    def test_arith_param_cond_tight_fail(self):
        """With init=80: val reaches 80. val <= 60 violated."""
        self.load("param_cond.tl", params={"init": 80})
        self.assert_fail("val_tight", "val <= 60")

class TestSpecificGeometric(ChironTestCase):
    """Geometric properties - goto coordinates driven by user-provided params."""

    MODE = "specific"

    def test_geo_goto_box_pass(self):
        """With startx=10, starty=20: xcor=10, ycor=20. Both within bounds."""
        self.load("param_goto.tl", params={"startx": 10, "starty": 20})
        self.assert_pass("box", "And(xcor <= 50, ycor <= 50)")

    def test_geo_goto_tight_fail(self):
        """With startx=100, starty=200: xcor=100. xcor <= 50 violated."""
        self.load("param_goto.tl", params={"startx": 100, "starty": 200})
        self.assert_fail("tight_x", "xcor <= 50")

    def test_geo_goto_neg_startx_fail(self):
        """With startx=-50: xcor=-50 -> xcor >= 0 violated."""
        self.load("param_goto.tl", params={"startx": -50, "starty": 0})
        self.assert_fail("xcor_nonneg", "xcor >= 0")

    def test_geo_goto_ycor_pass(self):
        """With startx=5, starty=10: ycor=10 <= 50 holds."""
        self.load("param_goto.tl", params={"startx": 5, "starty": 10})
        self.assert_pass("ycor_bound", "ycor <= 50")


class TestSpecificPen(ChironTestCase):
    """Pen properties - param_pen.tl reads :base before any write."""

    MODE = "specific"

    def test_pen_mark_nonneg_pass(self):
        """With base=5: mark = base+1 = 6. mark >= 0 holds."""
        self.load("param_pen.tl", params={"base": 5})
        self.assert_pass("mark_nonneg", "mark >= 0")

    def test_pen_always_up_fail(self):
        """param_pen.tl executes pendown -> Not(pendown) violated."""
        self.load("param_pen.tl", params={"base": 5})
        self.assert_fail("pen_always_up", "Not(pendown)")

    def test_pen_base_neg_mark_fail(self):
        """With base=-5: mark = base+1 = -4. mark >= 0 violated."""
        self.load("param_pen.tl", params={"base": -5})
        self.assert_fail("mark_nonneg", "mark >= 0")

    def test_pen_base_large_mark_pass(self):
        """With base=3: mark = 4. mark <= 10 holds."""
        self.load("param_pen.tl", params={"base": 3})
        self.assert_pass("mark_upper", "mark <= 10")


class TestSpecificDirectional(ChironTestCase):
    """Directional - heading stays 0 when there are no turns (concrete start)."""

    MODE = "specific"

    def test_dir_param_scale_heading_zero_pass(self):
        """param_scale.tl has no turns -> heading stays 0."""
        self.load("param_scale.tl", params={"scale": 10})
        self.assert_pass("heading_zero", "heading == 0")

    def test_dir_param_loop_heading_zero_pass(self):
        """param_loop.tl has no turns -> heading stays 0."""
        self.load("param_loop.tl", params={"start": 5})
        self.assert_pass("heading_zero", "heading == 0")

    def test_dir_param_cond_heading_nonzero_fail(self):
        """param_cond.tl has no turns -> heading is always 0, heading > 0 fails."""
        self.load("param_cond.tl", params={"init": 80})
        self.assert_fail("heading_pos", "heading > 0")


if __name__ == "__main__":
    unittest.main()
