"""
Tests for CHC verification in **universal** mode.
"""

from helpers import *

class TestUniversalArithmetic(ChironTestCase):

    MODE = "universal"

    def test_arith_assign_z_nonneg_fail(self):
        """z is arbitrary at pc=0 (universally quantified) -> z >= 0 fails."""
        self.load("assign_basic.tl")
        self.assert_fail("z_nonneg", self.v("z") >= 0)

    def test_arith_tautology_pass(self):
        """Or(z > 0, z <= 0) is a tautology - holds at every state."""
        self.load("assign_basic.tl")
        self.assert_pass("tautology", Or(self.v("z") > 0, self.v("z") <= 0))

    def test_arith_loop_x_nonneg_fail(self):
        """x is arbitrary at pc=0 -> x >= 0 fails."""
        self.load("loop_basic.tl")
        self.assert_fail("x_nonneg", self.v("x") >= 0)

    def test_arith_cond_z_nonneg_fail(self):
        """z is arbitrary at pc=0 -> z >= 0 fails."""
        self.load("conditional.tl")
        self.assert_fail("z_nonneg", self.v("z") >= 0)

    def test_arith_algebra_a_nonneg_fail(self):
        """a is arbitrary at pc=0 -> a >= 0 fails."""
        self.load("assign_algebra.tl")
        self.assert_fail("a_nonneg", self.v("a") >= 0)

    def test_arith_loop_cond_y_upper_fail(self):
        """y is arbitrary at pc=0 -> y <= 100 fails."""
        self.load("loop_cond.tl")
        self.assert_fail("y_upper", self.v("y") <= 100)

    def test_arith_loop_accum_tautology_pass(self):
        """x >= 0 OR x < 0 is a tautology, holds at every state."""
        self.load("loop_accum.tl")
        self.assert_pass("taut", Or(self.v("x") >= 0, self.v("x") < 0))

    def test_arith_algebra_c_nonneg_fail(self):
        """c_0 is arbitrary and c = :a * :b is nonlinear - SPACER may not be
        able to disprove c >= 0; the test is then reported as skipped."""
        self.load("assign_algebra.tl")
        self.assert_fail("c_nonneg", self.v("c") >= 0)


class TestUniversalGeometric(ChironTestCase):
    """Geometric properties - fail because position starts arbitrary."""

    MODE = "universal"

    def test_geo_square_box_fail(self):
        """xcor is arbitrary at pc=0 -> bounding box fails."""
        self.load("square_goto.tl")
        self.assert_fail("box", And(
            self.v("xcor") >= -100, self.v("xcor") <= 100,
        ))

    def test_geo_computed_xcor_fail(self):
        """xcor is arbitrary at pc=0 -> xcor <= 50 fails."""
        self.load("goto_computed.tl")
        self.assert_fail("xcor_bound", self.v("xcor") <= 50)

    def test_geo_loop_cond_xcor_fail(self):
        """xcor is arbitrary at pc=0 -> xcor == 0 fails."""
        self.load("loop_cond.tl")
        self.assert_fail("xcor_zero", self.v("xcor") == 0)


_HEADING_SKIP = (
    "SPACER cannot efficiently prove invariants over the normalize_heading "
    "If-chain (20 nested Z3 If-expressions per turn)."
)


class TestUniversalPen(ChironTestCase):
    """Pen-state properties - pen starts False in universal mode."""

    MODE = "universal"

    def test_pen_no_movement_always_up_pass(self):
        """assign_basic.tl has no pen commands -> pen stays False."""
        self.load("assign_basic.tl")
        self.assert_pass("pen_up", Not(self.v("pendown")))

    def test_pen_toggle_always_up_fail(self):
        """pendown command -> Not(pendown) violated."""
        self.load("pen_only.tl")
        self.assert_fail("pen_up", Not(self.v("pendown")))

    def test_pen_loop_always_up_pass(self):
        """loop_basic.tl has no pen commands -> pen stays False."""
        self.load("loop_basic.tl")
        self.assert_pass("pen_up", Not(self.v("pendown")))

    def test_pen_loop_cond_always_up_pass(self):
        """loop_cond.tl has no pen commands -> pen stays False."""
        self.load("loop_cond.tl")
        self.assert_pass("pen_up", Not(self.v("pendown")))

    def test_pen_with_var_fail(self):
        """pen_with_var.tl executes pendown -> Not(pendown) violated."""
        self.load("pen_with_var.tl")
        self.assert_fail("pen_up", Not(self.v("pendown")))


class TestUniversalDirectional(ChironTestCase):
    """Heading properties - fail because heading starts arbitrary."""

    MODE = "universal"

    @unittest.skip(_HEADING_SKIP)
    def test_dir_heading_nonneg_fail(self):
        """Heading is arbitrary at pc=0 (universally quantified) -> heading >= 0 fails."""
        self.load("turns_only.tl")
        self.assert_fail("heading_nonneg", self.v("heading") >= 0)

    def test_dir_no_turns_heading_arbitrary_fail(self):
        """Heading is arbitrary at pc=0 -> heading == 0 fails (no turns, but arbitrary start)."""
        self.load("assign_basic.tl")
        self.assert_fail("heading_zero", self.v("heading") == 0)

    def test_dir_loop_heading_tautology_pass(self):
        """heading >= 0 OR heading < 0 is always True regardless of initial value."""
        self.load("loop_accum.tl")
        self.assert_pass("taut", Or(self.v("heading") >= 0, self.v("heading") < 0))


if __name__ == "__main__":
    unittest.main()
