"""
Tests for CHC verification in **universal** mode.
"""

from helpers import *

class TestUniversalAPI(ChironTestCase):
    """Tests for the CHC verification API in universal mode."""

    MODE = "universal"

    def _call_api(self, *args, **kwargs):
        with redirect_stdout(StringIO()):
            return CHC_Verification(*args, **kwargs)

    def test_invalid_mode_error(self):
        result = self._call_api(
            program_path("assign_basic.tl"),
            "bogus",
            [UserProperty("x_nonneg", "x >= 0")],
        )
        self.assertEqual(result.error, ReturnError.ERROR)
        self.assertEqual(result.expr, "Invalid mode.")

    def test_hints_not_list_error(self):
        result = self._call_api(
            program_path("assign_basic.tl"),
            "universal",
            [UserProperty("x_nonneg", "x >= 0")],
            hints="check_heading_always_on_grid",
        )
        self.assertEqual(result.error, ReturnError.ERROR)
        self.assertEqual(result.expr, "Error: 'hints' must be a list of strings.")

    def test_hints_non_string_element_error(self):
        result = self._call_api(
            program_path("assign_basic.tl"),
            "universal",
            [UserProperty("x_nonneg", "x >= 0")],
            hints=["check_heading_always_on_grid", 5],
        )
        self.assertEqual(result.error, ReturnError.ERROR)
        self.assertEqual(result.expr, "Error: 'hints' must be a list of strings.")

    def test_invalid_hint_value_error(self):
        result = self._call_api(
            program_path("assign_basic.tl"),
            "universal",
            [UserProperty("x_nonneg", "x >= 0")],
            hints=["not_a_hint"],
        )
        self.assertEqual(result.error, ReturnError.ERROR)
        self.assertTrue(result.expr.startswith("Error: Invalid hint value:"))

    def test_property_parse_error(self):
        result = self._call_api(
            program_path("assign_basic.tl"),
            "universal",
            [UserProperty("bad_prop", "no_such_var >= 0")],
            hints=[],
        )
        self.assertEqual(result.error, ReturnError.ERROR)
        self.assertTrue(result.expr.startswith("Error parsing property"))

    def test_property_syntax_error(self):
        result = self._call_api(
            program_path("assign_basic.tl"),
            "universal",
            [UserProperty("bad_syntax", "x >")],
            hints=[],
        )
        self.assertEqual(result.error, ReturnError.ERROR)
        self.assertTrue(result.expr.startswith("Error parsing property"))

    def test_empty_property_list_passes(self):
        result = self._call_api(
            program_path("assign_basic.tl"),
            "universal",
            [],
            hints=[],
        )
        self.assertEqual(result.error, ReturnError.SUCCESS)
        self.assertEqual(result.status, "PASSED")
        self.assertEqual(result.passing_properties, [])
        self.assertEqual(result.failing_properties, [])
        self.assertEqual(result.unknown_properties, [])

class TestUniversalInitialState(ChironTestCase):
    """Initial-state semantics in universal mode."""

    MODE = "universal"

    def test_init_pendown_pass(self):
        """Universal init sets pendown=True."""
        self.load("u_init_core.tl")
        self.assert_property_pass("pendown_true", "pendown")

    def test_init_not_pendown_fail(self):
        """Universal init sets pendown=True, so Not(pendown) fails."""
        self.load("u_init_core.tl")
        self.assert_property_fail("pendown_false", "Not(pendown)")

    def test_init_heading_grid_range_pass(self):
        """Universal init constrains heading to [0,360) on 15-degree grid."""
        self.load("u_init_core.tl")
        self.assert_property_pass("heading_range", "And(heading >= 0, heading < 360)")

    def test_init_heading_zero_fail(self):
        """Heading is arbitrary on the 15-degree grid; heading == 0 not invariant."""
        self.load("u_init_core.tl")
        self.assert_property_fail("heading_zero", "heading == 0")

    def test_init_xcor_zero_fail(self):
        """xcor is arbitrary in universal init."""
        self.load("u_init_core.tl")
        self.assert_property_fail("xcor_zero", "xcor == 0")

    def test_init_ycor_zero_fail(self):
        """ycor is arbitrary in universal init."""
        self.load("u_init_core.tl")
        self.assert_property_fail("ycor_zero", "ycor == 0")

    def test_init_user_var_nonneg_fail(self):
        """User vars are unconstrained at pc=0 in universal init."""
        self.load("u_init_core.tl")
        self.assert_property_fail("x_nonneg", "x >= 0")

    def test_init_user_var_zero_fail(self):
        """User vars are unconstrained at pc=0 in universal init."""
        self.load("u_init_core.tl")
        self.assert_property_fail("x_zero", "x == 0")


class TestUniversalArithmetic(ChironTestCase):

    MODE = "universal"

    def test_term_clamp_nonneg_pass(self):
        self.load("u_clamp_to_zero.tl", property_scope="terminating")
        self.assert_property_pass("z_nonneg", "z >= 0")

    def test_term_clamp_disjunction_pass(self):
        self.load("u_clamp_to_zero.tl", property_scope="terminating")
        self.assert_property_pass("z_is_x_or_zero", "Or(z == 0, z == x)")

    def test_term_clamp_z_eq_x_fail(self):
        self.load("u_clamp_to_zero.tl", property_scope="terminating")
        self.assert_property_fail("z_eq_x", "z == x")

    def test_term_clamp_z_negative_fail(self):
        self.load("u_clamp_to_zero.tl", property_scope="terminating")
        self.assert_property_fail("z_negative", "z < 0")

    def test_term_product_zero_pass(self):
        self.load("u_product_zero.tl", property_scope="terminating")
        self.assert_property_pass("z_zero", "z == 0")

    def test_term_product_nonneg_pass(self):
        self.load("u_product_zero.tl", property_scope="terminating")
        self.assert_property_pass("z_nonneg", "z >= 0")

    def test_term_product_not_zero_fail(self):
        self.load("u_product_zero.tl", property_scope="terminating")
        self.assert_property_fail("z_not_zero", "z != 0")

    def test_term_product_z_eq_xy_fail(self):
        self.load("u_product_zero.tl", property_scope="terminating")
        self.assert_property_fail("z_eq_xy", "z == x * y")

    def test_term_same_post_z_zero_pass(self):
        self.load("u_same_postcondition.tl", property_scope="terminating")
        self.assert_property_pass("z_zero", "z == 0")

    def test_term_same_post_z_eq_x_minus_x_pass(self):
        self.load("u_same_postcondition.tl", property_scope="terminating")
        self.assert_property_pass("z_eq_x_minus_x", "z == x - x")

    def test_term_same_post_z_not_zero_fail(self):
        self.load("u_same_postcondition.tl", property_scope="terminating")
        self.assert_property_fail("z_not_zero", "z != 0")

    def test_term_swap_y_eq_tmp_pass(self):
        self.load("u_swap_with_temp.tl", property_scope="terminating")
        self.assert_property_pass("y_eq_tmp", "y == tmp")

    def test_term_swap_x_eq_tmp_fail(self):
        self.load("u_swap_with_temp.tl", property_scope="terminating")
        self.assert_property_fail("x_eq_tmp", "x == tmp")

    def test_term_swap_x_eq_y_fail(self):
        self.load("u_swap_with_temp.tl", property_scope="terminating")
        self.assert_property_fail("x_eq_y", "x == y")

    def test_term_affine_y_eq_minus3_fail(self):
        self.load("u_two_step_affine.tl", property_scope="terminating")
        self.assert_property_fail("y_eq_minus3", "y == -3")

    def test_term_affine_linear_relation_fail(self):
        self.load("u_two_step_affine.tl", property_scope="terminating")
        self.assert_property_fail("x_minus_2y_eq_6", "x - 2*y == 6")

    def test_term_absdiff_y_eq_minus3_fail(self):
        self.load("u_abs_diff_branching.tl", property_scope="terminating")
        self.assert_property_fail("y_eq_minus3", "y == -3")

    def test_term_absdiff_linear_relation_fail(self):
        self.load("u_abs_diff_branching.tl", property_scope="terminating")
        self.assert_property_fail("x_minus_2y_eq_6", "x - 2*y == 6")

    def test_term_branch_merge_d_nonneg_pass(self):
        self.load("u_branch_merge_affine.tl", property_scope="terminating")
        self.assert_property_pass("d_nonneg", "d >= 0")

    def test_term_branch_merge_s_eq_x_pass(self):
        self.load("u_branch_merge_affine.tl", property_scope="terminating")
        self.assert_property_pass("s_eq_x", "s == x")

    def test_term_branch_merge_abs_diff_pass(self):
        self.load("u_branch_merge_affine.tl", property_scope="terminating")
        self.assert_property_pass("abs_diff", "Or(d == x - y, d == y - x)")

    def test_term_branch_merge_d_eq_x_minus_y_fail(self):
        self.load("u_branch_merge_affine.tl", property_scope="terminating")
        self.assert_property_fail("d_eq_x_minus_y", "d == x - y")

    def test_term_euclid_avg_a_def_pass(self):
        self.load("u_euclid_avg.tl", property_scope="terminating")
        self.assert_property_pass("a_def", "a == m + n")

    def test_term_euclid_avg_b_def_pass(self):
        self.load("u_euclid_avg.tl", property_scope="terminating")
        self.assert_property_pass("b_def", "b == m - n")

    def test_term_euclid_avg_c_eq_2m_pass(self):
        self.load("u_euclid_avg.tl", property_scope="terminating")
        self.assert_property_pass("c_eq_2m", "c == 2*m")

    def test_term_euclid_avg_c_eq_2n_fail(self):
        self.load("u_euclid_avg.tl", property_scope="terminating")
        self.assert_property_fail("c_eq_2n", "c == 2*n")

    def test_term_swap_wo_tmp_sum_pass(self):
        self.load("u_swap_without_tmp.tl", property_scope="terminating")
        self.assert_property_pass("s_eq_x_plus_y", "s == x + y")

    def test_term_swap_wo_tmp_x_eq_y_fail(self):
        self.load("u_swap_without_tmp.tl", property_scope="terminating")
        self.assert_property_fail("x_eq_y", "x == y")

class TestUniversalGeometric(ChironTestCase):
    """Geometric properties - fail because position starts arbitrary."""

    MODE = "universal"


class TestUniversalPen(ChironTestCase):
    """Pen-state properties - pen starts False in universal mode."""

    MODE = "universal"

    # def test_pen_no_movement_always_up_pass(self):
    #     """assign_basic.tl has no pen commands -> pen stays False."""
    #     self.load("assign_basic.tl")
    #     self.assert_pass("pen_up", "Not(pendown)")

    # def test_pen_toggle_always_up_fail(self):
    #     """pendown command -> Not(pendown) violated."""
    #     self.load("pen_only.tl")
    #     self.assert_fail("pen_up", "Not(pendown)")

    # def test_pen_loop_always_up_pass(self):
    #     """loop_basic.tl has no pen commands -> pen stays False."""
    #     self.load("loop_basic.tl")
    #     self.assert_pass("pen_up", "Not(pendown)")

    # def test_pen_loop_cond_always_up_pass(self):
    #     """loop_cond.tl has no pen commands -> pen stays False."""
    #     self.load("loop_cond.tl")
    #     self.assert_pass("pen_up", "Not(pendown)")

    # def test_pen_with_var_fail(self):
    #     """pen_with_var.tl executes pendown -> Not(pendown) violated."""
    #     self.load("pen_with_var.tl")
    #     self.assert_fail("pen_up", "Not(pendown)")


class TestUniversalDirectional(ChironTestCase):
    """Heading properties - fail because heading starts arbitrary."""

    MODE = "universal"

    # def test_dir_heading_nonneg_fail(self):
    #     """Heading is arbitrary at pc=0 (universally quantified) -> heading >= 0 fails."""
    #     self.load("turns_only.tl")
    #     self.assert_fail("heading_nonneg", "heading >= 0")

    # def test_dir_no_turns_heading_arbitrary_fail(self):
    #     """Heading is arbitrary at pc=0 -> heading == 0 fails (no turns, but arbitrary start)."""
    #     self.load("assign_basic.tl")
    #     self.assert_fail("heading_zero", "heading == 0")

    # def test_dir_loop_heading_tautology_pass(self):
    #     """heading >= 0 OR heading < 0 is always True regardless of initial value."""
    #     self.load("loop_accum.tl")
    #     self.assert_pass("taut", "Or(heading >= 0, heading < 0)")


if __name__ == "__main__":
    unittest.main()
