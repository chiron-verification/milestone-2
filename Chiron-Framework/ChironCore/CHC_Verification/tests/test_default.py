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
        self.assert_property_pass("z_nonneg", "z >= 0")

    def test_arith_assign_z_upper_fail(self):
        """z reaches 30, so z <= 20 is violated."""
        self.load("assign_basic.tl")
        self.assert_property_fail("z_upper", "z <= 20")
    
    def test_arith_x_pos_pass(self):
        """x starts at 0 and is assinged to 10"""
        self.load("assign_basic.tl")
        self.assert_property_pass("x_bounded", "And(x >= 0, x <= 10)")
    
    def test_arith_x_greater_10_fail(self):
        """x starts at 0 and is assinged to 10"""
        self.load("assign_basic.tl")
        self.assert_property_fail("x_greater_10", "x > 10")

    def test_arith_loop_accum_nonneg_pass(self):
        """x starts 0 and only increases -> x >= 0."""
        self.load("loop_accum.tl")
        self.assert_property_pass("x_nonneg", "x >= 0")

    def test_arith_loop_accum_upper_fail(self):
        """x reaches 50, so x <= 30 is violated."""
        self.load("loop_accum.tl")
        self.assert_property_fail("x_upper", "x <= 30")

    def test_arith_cond_z_nonneg_pass(self):
        """z is 0 (before assign) then 25 -> always >= 0."""
        self.load("conditional.tl")
        self.assert_property_pass("z_nonneg", "z >= 0")

    def test_arith_loop_basic_x_nonneg_pass(self):
        """x accumulates in loop_basic.tl -> x always >= 0 in default mode."""
        self.load("loop_basic.tl")
        self.assert_property_pass("x_nonneg", "x >= 0")

    def test_arith_algebra_b_upper_fail(self):
        """b reaches 35. b <= 10 violated."""
        self.load("assign_algebra.tl")
        self.assert_property_fail("b_upper", "b <= 10")

    def test_arith_loop_cond_y_upper_pass(self):
        """y starts 100 and only decreases -> y <= 100 holds."""
        self.load("loop_cond.tl")
        self.assert_property_pass("y_upper", "y <= 100")

    def test_arith_assign_z_tight_fail(self):
        """z=30 in assign_basic.tl (default mode) -> z >= 100 violated."""
        self.load("assign_basic.tl")
        self.assert_property_fail("z_tight", "z >= 100")

    def test_arith_adv_x_bound_pass(self):
        """x starts at 0 grows as x=0->5->15->30->50->75 -> x <= 75 holds."""
        self.load("loop_adv.tl")
        self.assert_property_pass("x_bound", "x <= 75")

    def test_arith_adv_x_bound_fail(self):
        """x starts at 0 grows as x=0->5->15->30->50->75 -> x <= 70 fails."""
        self.load("loop_adv.tl")
        self.assert_property_fail("x_bound", "x <= 70")

class TestDefaultGeometric(ChironTestCase):
    """Geometric (bounded box / safety region) properties using goto programs."""

    MODE = "default"

    def test_geo_square_box_pass(self):
        """All positions within a generous bounding box."""
        self.load("square_goto.tl")
        self.assert_property_pass("box", "And(xcor >= -10, xcor <= 110, ycor >= -10, ycor <= 110)")

    def test_geo_square_tight_fail(self):
        """xcor reaches 50, so xcor <= 30 is violated."""
        self.load("square_goto.tl")
        self.assert_property_fail("tight_x", "xcor <= 30")

    def test_geo_computed_box_pass(self):
        """Positions stay within [-10,50]x[-10,30]."""
        self.load("goto_computed.tl")
        self.assert_property_pass("box", "And(xcor >= -10, xcor <= 50, ycor >= -10, ycor <= 30)")

    def test_geo_computed_ycor_fail(self):
        """ycor reaches 20 -> ycor <= 10 violated."""
        self.load("goto_computed.tl")
        self.assert_property_fail("tight_y", "ycor <= 10")

    def test_geo_no_movement_xcor_zero_pass(self):
        """loop_cond.tl has no movement commands -> xcor stays 0."""
        self.load("loop_cond.tl")
        self.assert_property_pass("xcor_zero", "xcor == 0")

    def test_geo_square_y_window_pass(self):
        """square_goto.tl keeps ycor in [0, 50]."""
        self.load("square_goto.tl")
        self.assert_property_pass("y_window", "And(ycor >= 0, ycor <= 50)")

    def test_geo_square_non_origin_fail(self):
        """square_goto.tl revisits origin, so xcor > 0 is violated."""
        self.load("square_goto.tl")
        self.assert_property_fail("strict_x_positive", "xcor > 0")

    def test_geo_computed_y_discrete_pass(self):
        """goto_computed.tl only has ycor values 0 and 20."""
        self.load("goto_computed.tl")
        self.assert_property_pass("y_discrete", "Or(ycor == 0, ycor == 20)")

    def test_geo_computed_x_tight_fail(self):
        """goto_computed.tl reaches xcor=40, so xcor <= 30 is violated."""
        self.load("goto_computed.tl")
        self.assert_property_fail("x_tight", "xcor <= 30")


class TestDefaultPen(ChironTestCase):
    """Pen-state properties."""

    MODE = "default"

    def test_pen_always_up_pass(self):
        """assign_basic.tl has no pen commands -> pen stays False."""
        self.load("assign_basic.tl")
        self.assert_property_pass("pen_up", "Not(pendown)")

    def test_pen_toggle_down_tautology_pass(self):
        """pen_only.tl: pendown OR NOT pendown is always True."""
        self.load("pen_only.tl")
        self.assert_property_pass("taut", "Or(pendown, Not(pendown))")

    def test_pen_toggle_always_up_fail(self):
        """pen_only.tl executes pendown -> Not(pendown) is violated."""
        self.load("pen_only.tl")
        self.assert_property_fail("pen_up", "Not(pendown)")

    def test_pen_loop_always_up_pass(self):
        """loop_basic.tl has no pen commands -> pen stays False."""
        self.load("loop_basic.tl")
        self.assert_property_pass("pen_up", "Not(pendown)")

    def test_pen_loop_cond_always_up_pass(self):
        """loop_cond.tl has no pen commands -> pen stays False."""
        self.load("loop_cond.tl")
        self.assert_property_pass("pen_up", "Not(pendown)")

    def test_pen_with_var_always_down_fail(self):
        """pen_with_var.tl executes pendown -> Not(pendown) violated."""
        self.load("pen_with_var.tl")
        self.assert_property_fail("pen_up", "Not(pendown)")


class TestDefaultDirectional(ChironTestCase):
    """Heading / directional properties."""

    MODE = "default"

    def test_dir_heading_nonneg_pass(self):
        """Heading is normalized to [0,360). Starting at 0, right 90 -> 270, etc."""
        self.load("turns_only.tl")
        self.assert_property_pass("heading_nonneg", "heading >= 0")

    def test_dir_heading_small_fail(self):
        """Heading reaches 270 -> heading <= 90 is violated."""
        self.load("turns_only.tl")
        self.assert_property_fail("heading_small", "heading <= 90")

    def test_dir_no_turns_heading_zero_pass(self):
        """assign_basic.tl has no turn commands -> heading stays 0."""
        self.load("assign_basic.tl")
        self.assert_property_pass("heading_zero", "heading == 0")

    def test_dir_loop_no_turns_heading_zero_pass(self):
        """loop_accum.tl has no turn commands -> heading stays 0."""
        self.load("loop_accum.tl")
        self.assert_property_pass("heading_zero", "heading == 0")

    def test_dir_no_turns_heading_nonzero_fail(self):
        """assign_basic.tl: heading is always 0 -> heading > 0 violated."""
        self.load("assign_basic.tl")
        self.assert_property_fail("heading_pos", "heading > 0")

    def test_dir_cond_no_turns_heading_zero_pass(self):
        """conditional.tl has no turn commands -> heading stays 0."""
        self.load("conditional.tl")
        self.assert_property_pass("heading_zero", "heading == 0")

class TestDefaultHeadingGrid(ChironTestCase):
    """15-degree heading grid checks in default mode."""

    MODE = "default"

    def test_heading_grid_turns_15_pass(self):
        """turns_15.tl keeps heading on 15-degree grid."""
        self.load("turns_15.tl", hints=["heading_on_grid_always"])
        grid_expr = "Or(" + ", ".join(f"heading == {deg}" for deg in range(-360, 721, 15)) + ")"
        self.assert_property_pass("heading_on_grid", grid_expr)

    def test_heading_grid_turns_15_heading_range_pass(self):
        """Concrete property checked only after grid restriction passes."""
        self.load("turns_15.tl", hints=["heading_on_grid_always"])
        self.assert_property_pass(
            "heading_in_range",
            "And(heading >= 0, heading < 360)",
        )

    @unittest.skip("Timed out")
    def test_heading_grid_turns_15_narrow_fail(self):
        """turns_15.tl reaches more than one heading value, so a narrow set fails."""
        self.load("turns_15.tl", hints=["heading_on_grid_always"])
        self.assert_property_fail(
            "heading_narrow",
            "Or(heading == 0, heading == 15)",
        )

class TestDefaultTrig(ChironTestCase):
    """
    * TRIG-DEPENDENT tests - forward/backward involve cos/sin interval bounds.
    These may be slower or require generous bounds due to trig approximation.
    """

    MODE = "default"

    @unittest.skip("Timed out")
    def test_trig_forward_square_box_pass(self):
        """forward_square.tl draws ~square at heading multiples of 90.
        Generous box [-100,100]x[-100,100] should hold."""
        self.load("forward_square.tl", hints=["heading_on_grid_always"])
        self.assert_property_pass("box", "And(xcor >= -100, xcor <= 100, ycor >= -100, ycor <= 100)")

    def test_trig_forward_square_positive_fail(self):
        """ycor goes negative (~ -50) -> ycor >= 0 is violated."""
        self.load("forward_square.tl", hints=["heading_on_grid_always"])
        self.assert_property_fail("positive_y", "ycor >= 0")

    def test_trig_forward_square_heading_set_pass(self):
        """Only quarter-turn headings are reachable in forward_square.tl."""
        self.load("forward_square.tl", hints=["heading_on_grid_always"])
        self.assert_property_pass(
            "heading_quarters",
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
        )

    def test_trig_forward_square_heading_small_fail(self):
        """Heading reaches 270, so heading < 180 is violated."""
        self.load("forward_square.tl", hints=["heading_on_grid_always"])
        self.assert_property_fail("heading_small", "heading < 180")

    def test_trig_forward_square_pen_up_pass(self):
        """No pen commands in forward_square.tl, so pendown stays False."""
        self.load("forward_square.tl", hints=["heading_on_grid_always"])
        self.assert_property_pass("pen_up", "Not(pendown)")

class TestDefaultAdvanced(ChironTestCase):
    """Complex default-mode turtle programs with nested loops and pen toggles."""

    MODE = "default"

    @unittest.skip("Timed out")
    def test_adv_flower_nested_fail(self):
        """flower_nested_pen.tl reaches count=6, so count<=4 is violated."""
        self.load("flower_nested_pen.tl", hints=["heading_on_grid_always"])
        self.assert_property_fail("flower_count_tight", "count <= 4")

    def test_adv_flower_nested_pass(self):
        """flower_nested_pen.tl: nested motif keeps counters bounded."""
        self.load("flower_nested_pen.tl", hints=["heading_on_grid_always"])
        self.assert_property_pass(
            "flower_bounds",
            "And(count >= 0, heading >= 0, heading < 360)",
        )

    @unittest.skip("Timed out")
    def test_adv_triangle_nested_fail(self):
        """triangle_nested_pen.tl reaches step=6, so step<=5 is violated."""
        self.load("triangle_nested_pen.tl", hints=["heading_on_grid_always"])
        self.assert_property_fail("triangle_step_tight", "step <= 5")
    
    def test_adv_triangle_nested_pass(self):
        """triangle_nested_pen.tl: nested loops produce bounded counters and heading."""
        self.load("triangle_nested_pen.tl", hints=["heading_on_grid_always"])
        self.assert_property_pass(
            "triangle_bounds",
            "And(step >= 0, side >= 0, heading >= 0, heading < 360)",
        )


if __name__ == "__main__":
    unittest.main()
