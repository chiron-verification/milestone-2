"""
Tests for CHC verification in **default** mode.

Default mode: pc=0, xcor=0, ycor=0, heading=0, pendown=False, all vars=0.
"""

from helpers import *

class TestDefaultArithmetic(ChironTestCase):
    """Linear-arithmetic properties on assignment / loop / conditional programs."""

    MODE = "default"

    def test_arith_assign_z_nonneg_pass(self):
        """z is always >= 0 (z goes 0->0->0->30)."""
        self.load("assign_basic.tl")
        self.assert_pass("z_nonneg", "z >= 0")

    def test_arith_assign_z_upper_fail(self):
        """z reaches 30, so z <= 20 is violated."""
        self.load("assign_basic.tl")
        self.assert_fail("z_upper", "z <= 20")

    def test_arith_loop_accum_nonneg_pass(self):
        """x starts 0 and only increases -> x >= 0."""
        self.load("loop_accum.tl")
        self.assert_pass("x_nonneg", "x >= 0")

    def test_arith_loop_accum_upper_fail(self):
        """x reaches 50, so x <= 30 is violated."""
        self.load("loop_accum.tl")
        self.assert_fail("x_upper", "x <= 30")

    def test_arith_cond_z_nonneg_pass(self):
        """z is 0 (before assign) then 25 -> always >= 0."""
        self.load("conditional.tl")
        self.assert_pass("z_nonneg", "z >= 0")

    def test_arith_loop_basic_x_nonneg_pass(self):
        """x accumulates in loop_basic.tl -> x always >= 0 in default mode."""
        self.load("loop_basic.tl")
        self.assert_pass("x_nonneg", "x >= 0")

    def test_arith_algebra_b_upper_fail(self):
        """b reaches 35. b <= 10 violated."""
        self.load("assign_algebra.tl")
        self.assert_fail("b_upper", "b <= 10")

    def test_arith_loop_cond_y_upper_pass(self):
        """y starts 100 and only decreases -> y <= 100 holds."""
        self.load("loop_cond.tl")
        self.assert_pass("y_upper", "y <= 100")

    def test_arith_assign_z_tight_fail(self):
        """z=30 in assign_basic.tl (default mode) -> z >= 100 violated."""
        self.load("assign_basic.tl")
        self.assert_fail("z_tight", "z >= 100")

class TestDefaultGeometric(ChironTestCase):
    """Geometric (bounded box / safety region) properties using goto programs."""

    MODE = "default"

    def test_geo_square_box_pass(self):
        """All positions within a generous bounding box."""
        self.load("square_goto.tl")
        self.assert_pass("box", "And(xcor >= -10, xcor <= 110, ycor >= -10, ycor <= 110)")

    def test_geo_square_tight_fail(self):
        """xcor reaches 50, so xcor <= 30 is violated."""
        self.load("square_goto.tl")
        self.assert_fail("tight_x", "xcor <= 30")

    def test_geo_computed_box_pass(self):
        """Positions stay within [-10,50]x[-10,30]."""
        self.load("goto_computed.tl")
        self.assert_pass("box", "And(xcor >= -10, xcor <= 50, ycor >= -10, ycor <= 30)")

    def test_geo_computed_ycor_fail(self):
        """ycor reaches 20 -> ycor <= 10 violated."""
        self.load("goto_computed.tl")
        self.assert_fail("tight_y", "ycor <= 10")

    def test_geo_no_movement_xcor_zero_pass(self):
        """loop_cond.tl has no movement commands -> xcor stays 0."""
        self.load("loop_cond.tl")
        self.assert_pass("xcor_zero", "xcor == 0")


class TestDefaultPen(ChironTestCase):
    """Pen-state properties."""

    MODE = "default"

    def test_pen_always_up_pass(self):
        """assign_basic.tl has no pen commands -> pen stays False."""
        self.load("assign_basic.tl")
        self.assert_pass("pen_up", "Not(pendown)")

    def test_pen_toggle_down_tautology_pass(self):
        """pen_only.tl: pendown OR NOT pendown is always True."""
        self.load("pen_only.tl")
        self.assert_pass("taut", "Or(pendown, Not(pendown))")

    def test_pen_toggle_always_up_fail(self):
        """pen_only.tl executes pendown -> Not(pendown) is violated."""
        self.load("pen_only.tl")
        self.assert_fail("pen_up", "Not(pendown)")

    def test_pen_loop_always_up_pass(self):
        """loop_basic.tl has no pen commands -> pen stays False."""
        self.load("loop_basic.tl")
        self.assert_pass("pen_up", "Not(pendown)")

    def test_pen_loop_cond_always_up_pass(self):
        """loop_cond.tl has no pen commands -> pen stays False."""
        self.load("loop_cond.tl")
        self.assert_pass("pen_up", "Not(pendown)")

    def test_pen_with_var_always_down_fail(self):
        """pen_with_var.tl executes pendown -> Not(pendown) violated."""
        self.load("pen_with_var.tl")
        self.assert_fail("pen_up", "Not(pendown)")


class TestDefaultDirectional(ChironTestCase):
    """Heading / directional properties."""

    MODE = "default"

    def test_dir_heading_nonneg_pass(self):
        """Heading is normalized to [0,360). Starting at 0, right 90 -> 270, etc."""
        self.load("turns_only.tl")
        self.assert_pass("heading_nonneg", "heading >= 0")

    def test_dir_heading_small_fail(self):
        """Heading reaches 270 -> heading <= 90 is violated."""
        self.load("turns_only.tl")
        self.assert_fail("heading_small", "heading <= 90")

    def test_dir_no_turns_heading_zero_pass(self):
        """assign_basic.tl has no turn commands -> heading stays 0."""
        self.load("assign_basic.tl")
        self.assert_pass("heading_zero", "heading == 0")

    def test_dir_loop_no_turns_heading_zero_pass(self):
        """loop_accum.tl has no turn commands -> heading stays 0."""
        self.load("loop_accum.tl")
        self.assert_pass("heading_zero", "heading == 0")

    def test_dir_no_turns_heading_nonzero_fail(self):
        """assign_basic.tl: heading is always 0 -> heading > 0 violated."""
        self.load("assign_basic.tl")
        self.assert_fail("heading_pos", "heading > 0")

    def test_dir_cond_no_turns_heading_zero_pass(self):
        """conditional.tl has no turn commands -> heading stays 0."""
        self.load("conditional.tl")
        self.assert_pass("heading_zero", "heading == 0")

class TestDefaultHeadingGrid(ChironTestCase):
    """15-degree heading grid checks in default mode."""

    MODE = "default"

    def test_heading_grid_turns_15_pass(self):
        """turns_15.tl keeps heading on 15-degree grid."""
        self.load("turns_15.tl")
        grid_expr = "Or(" + ", ".join(f"heading == {deg}" for deg in range(-360, 721, 15)) + ")"
        self.assert_pass("heading_on_grid", grid_expr)

    def test_heading_grid_turns_non_15_violated(self):
        """turns_non_15.tl can reach heading not on grid — heading grid pre-check is VIOLATED."""
        self.load("turns_non_15.tl")
        self.assert_heading_grid_violated()

    def test_heading_grid_turns_15_safe(self):
        """turns_15.tl keeps heading on the 15-degree grid (pre-check)."""
        self.load("turns_15.tl")
        self.assert_heading_grid_safe()

    def test_heading_grid_turns_non_15_unknown(self):
        """turns_non_15.tl can leave grid -> verification treated as UNKNOWN."""
        self.load("turns_non_15.tl")
        self.assert_heading_grid_unknown()

    def test_heading_grid_turns_15_heading_range_pass(self):
        """Concrete property checked only after grid restriction passes."""
        self.load("turns_15.tl")
        self.assert_pass_after_heading_grid(
            "heading_in_range",
            "And(heading >= 0, heading < 360)",
        )

    def test_heading_grid_turns_non_15_heading_range_skipped(self):
        """Concrete property is UNKNOWN when grid restriction is not safe."""
        self.load("turns_non_15.tl")
        self.assert_unknown_after_heading_grid(
            "heading_in_range",
            "And(heading >= 0, heading < 360)",
        )

class TestDefaultTrig(ChironTestCase):
    """
    * TRIG-DEPENDENT tests - forward/backward involve cos/sin interval bounds.
    These may be slower or require generous bounds due to trig approximation.
    """

    MODE = "default"

    @unittest.skip("SPACER cannot prove trig-based position invariants with the exact If-chain encoding.")
    def test_trig_forward_square_box_pass(self):
        """forward_square.tl draws ~square at heading multiples of 90.
        Generous box [-100,100]x[-100,100] should hold."""
        self.load("forward_square.tl")
        self.assert_pass("box", "And(xcor >= -100, xcor <= 100, ycor >= -100, ycor <= 100)")

    def test_trig_forward_square_positive_fail(self):
        """ycor goes negative (~ -50) -> ycor >= 0 is violated."""
        self.load("forward_square.tl")
        self.assert_fail("positive_y", "ycor >= 0")


if __name__ == "__main__":
    unittest.main()
