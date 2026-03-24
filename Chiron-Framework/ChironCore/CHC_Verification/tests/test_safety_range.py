"""
Tests for CHC verification in **safety-range** mode.
"""

from helpers import *

class TestSafetyRangeArithmetic(ChironTestCase):
    """Arithmetic properties - user vars start at arbitrary ghost values."""

    MODE = "safety-range"

    def test_arith_loop_accum_x_nonneg_fail(self):
        """x = x_start at pc=0 (arbitrary) -> x >= 0 fails."""
        self.load("loop_accum.tl")
        self.assert_fail("x_nonneg", "x >= 0")

    def test_arith_assign_z_upper_fail(self):
        """z = z_start at pc=0 (arbitrary) -> z <= 20 fails."""
        self.load("assign_basic.tl")
        self.assert_fail("z_upper", "z <= 20")

    def test_arith_tautology_pass(self):
        """x >= 0 OR x < 0 is a tautology regardless of x_start."""
        self.load("assign_basic.tl")
        self.assert_pass("taut", "Or(x >= 0, x < 0)")

    def test_arith_algebra_a_upper_fail(self):
        """a_start is arbitrary -> a <= 10 fails when a_start > 10."""
        self.load("assign_algebra.tl")
        self.assert_fail("a_upper", "a <= 10")

    def test_arith_loop_cond_y_upper_fail(self):
        """y_start is arbitrary -> y <= 100 fails."""
        self.load("loop_cond.tl")
        self.assert_fail("y_upper", "y <= 100")

    def test_arith_param_loop_acc_nonneg_fail(self):
        """start is arbitrary -> acc >= 0 fails when start < -30."""
        self.load("param_loop.tl")
        self.assert_fail("acc_nonneg", "acc >= 0")

class TestSafetyRangeGeometric(ChironTestCase):
    """Geometric properties - positions are driven by user variables."""

    MODE = "safety-range"

    def test_geo_computed_box_pass(self):
        """goto_computed: xcor goes 0->10->40, always <= 50. safety_range is set."""
        self.load("goto_computed.tl")
        result = self.assert_pass("box", "xcor <= 50")
        self.assertIsNotNone(result.passing_properties[0][2])

    def test_geo_computed_tight_fail(self):
        """goto_computed: xcor reaches 10 -> xcor <= 5 violated."""
        self.load("goto_computed.tl")
        self.assert_fail("tight_x", "xcor <= 5")

    def test_geo_computed_ycor_pass(self):
        """goto_computed: ycor goes 0->20 and stays 20. ycor <= 25 always holds."""
        self.load("goto_computed.tl")
        self.assert_pass("ycor_bound", "ycor <= 25")

    def test_geo_param_goto_xcor_fail(self):
        """startx_start is arbitrary -> xcor <= 50 fails."""
        self.load("param_goto.tl")
        self.assert_fail("xcor_bound", "xcor <= 50")


class TestSafetyRangePen(ChironTestCase):
    """Pen-state properties - pen starts False regardless of ghost params."""

    MODE = "safety-range"

    def test_pen_noop_always_up_pass(self):
        """assign_basic.tl has no pen commands -> pen stays False."""
        self.load("assign_basic.tl")
        self.assert_pass("pen_up", "Not(pendown)")

    def test_pen_toggle_always_up_fail(self):
        """pen_with_var.tl has :x and pendown -> Not(pendown) violated."""
        self.load("pen_with_var.tl")
        self.assert_fail("pen_up", "Not(pendown)")

    def test_pen_loop_cond_always_up_pass(self):
        """loop_cond.tl has no pen commands -> pen stays False."""
        self.load("loop_cond.tl")
        self.assert_pass("pen_up", "Not(pendown)")

    def test_pen_param_pen_always_up_fail(self):
        """param_pen.tl executes pendown -> Not(pendown) violated."""
        self.load("param_pen.tl")
        self.assert_fail("pen_up", "Not(pendown)")


class TestSafetyRangeDirectional(ChironTestCase):
    """Heading properties - heading starts at 0."""

    MODE = "safety-range"

    def test_dir_heading_nonneg_pass(self):
        """Heading starts 0, right 90 -> 270, 180, 90, 0 - all >= 0."""
        self.load("turns_only.tl")
        self.assert_pass("heading_nonneg", "heading >= 0")

    def test_dir_heading_small_fail(self):
        """Heading reaches 270 -> heading <= 90 violated."""
        self.load("turns_only.tl")
        self.assert_fail("heading_small", "heading <= 90")


class TestSafetyRangeDirectionalNoTurn(ChironTestCase):
    """Heading properties on programs without turn commands (heading stays 0)."""

    MODE = "safety-range"

    def test_dir_no_turns_heading_zero_pass(self):
        """assign_basic.tl has no turns -> heading always stays 0."""
        self.load("assign_basic.tl")
        self.assert_pass("heading_zero", "heading == 0")

    def test_dir_loop_no_turns_heading_zero_pass(self):
        """loop_accum.tl has no turns -> heading always stays 0."""
        self.load("loop_accum.tl")
        self.assert_pass("heading_zero", "heading == 0")

    def test_dir_loop_no_turns_heading_pos_fail(self):
        """loop_accum.tl: heading is always 0 -> heading > 0 violated."""
        self.load("loop_accum.tl")
        self.assert_fail("heading_pos", "heading > 0")

    def test_dir_algebra_heading_nonzero_fail(self):
        """assign_algebra.tl has no turns -> heading > 0 violated."""
        self.load("assign_algebra.tl")
        self.assert_fail("heading_pos", "heading > 0")


if __name__ == "__main__":
    unittest.main()
