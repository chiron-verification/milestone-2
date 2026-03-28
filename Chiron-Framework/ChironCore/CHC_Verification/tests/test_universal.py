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

    def test_all_scope_init_tautology_pass(self):
        self.load("u_init_core.tl", property_scope="all")
        self.assert_property_pass("x_minus_x_zero", "x - x == 0")

    def test_all_scope_branch_merge_tautology_pass(self):
        self.load("u_branch_merge_affine.tl", property_scope="all")
        self.assert_property_pass("d_trichotomy", "Or(d >= 0, d < 0)")

    def test_all_scope_euclid_commute_pass(self):
        self.load("u_euclid_avg.tl", property_scope="all")
        self.assert_property_pass("a_plus_b_commute", "a + b == b + a")

    def test_all_scope_swap_wo_tmp_tautology_pass(self):
        self.load("u_swap_without_tmp.tl", property_scope="all")
        self.assert_property_pass("s_minus_s_zero", "s - s == 0")

class TestUniversalGeometric(ChironTestCase):
    """Geometric properties - fail because position starts arbitrary."""

    MODE = "universal"

    def test_geo_fixed_target_xcor_pass(self):
        self.load("u_fixed_target.tl", property_scope="terminating")
        self.assert_property_pass("xcor_10", "xcor == 10")

    def test_geo_fixed_target_ycor_pass(self):
        self.load("u_fixed_target.tl", property_scope="terminating")
        self.assert_property_pass("ycor_20", "ycor == 20")

    def test_geo_fixed_target_both_pass(self):
        self.load("u_fixed_target.tl", property_scope="terminating")
        self.assert_property_pass("at_target", "And(xcor == 10, ycor == 20)")

    def test_geo_fixed_target_xcor_zero_fail(self):
        self.load("u_fixed_target.tl", property_scope="terminating")
        self.assert_property_fail("xcor_zero", "xcor == 0")

    def test_geo_fixed_target_ycor_zero_fail(self):
        self.load("u_fixed_target.tl", property_scope="terminating")
        self.assert_property_fail("ycor_zero", "ycor == 0")

    def test_geo_fixed_target_user_relation_pass(self):
        self.load("u_fixed_target_user.tl", property_scope="terminating")
        self.assert_property_pass("delta_7", "ycor - xcor == 7")

    def test_geo_fixed_target_user_x_eq_a_pass(self):
        self.load("u_fixed_target_user.tl", property_scope="terminating")
        self.assert_property_pass("x_eq_a", "xcor == a")

    def test_geo_fixed_target_user_y_eq_a_plus_7_pass(self):
        self.load("u_fixed_target_user.tl", property_scope="terminating")
        self.assert_property_pass("y_eq_a_plus_7", "ycor == a + 7")

    def test_geo_fixed_target_user_diag_fail(self):
        self.load("u_fixed_target_user.tl", property_scope="terminating")
        self.assert_property_fail("diag", "ycor == xcor")

    def test_geo_fixed_target_user_xcor_zero_fail(self):
        self.load("u_fixed_target_user.tl", property_scope="terminating")
        self.assert_property_fail("xcor_zero", "xcor == 0")

    def test_geo_normalize_x_xcor_pass(self):
        self.load("u_normalize_x.tl", property_scope="terminating")
        self.assert_property_pass("xcor_5", "xcor == 5")

    def test_geo_normalize_x_ycor_pass(self):
        self.load("u_normalize_x.tl", property_scope="terminating")
        self.assert_property_pass("ycor_5", "ycor == 5")

    def test_geo_normalize_x_diag_pass(self):
        self.load("u_normalize_x.tl", property_scope="terminating")
        self.assert_property_pass("diag", "xcor == ycor")

    def test_geo_normalize_x_i_pass(self):
        self.load("u_normalize_x.tl", property_scope="terminating")
        self.assert_property_pass("i_eq_5", "i == 5")

    def test_geo_normalize_x_xcor_zero_fail(self):
        self.load("u_normalize_x.tl", property_scope="terminating")
        self.assert_property_fail("xcor_zero", "xcor == 0")

    def test_geo_xcor_fixed_xcor_pass(self):
        self.load("u_xcor_fixed.tl", property_scope="terminating")
        self.assert_property_pass("xcor_8", "xcor == 8")

    def test_geo_xcor_fixed_ycor_choices_pass(self):
        self.load("u_xcor_fixed.tl", property_scope="terminating")
        self.assert_property_pass("ycor_choices", "Or(ycor == 3, ycor == -3)")

    def test_geo_xcor_fixed_branch_relation_pass(self):
        self.load("u_xcor_fixed.tl", property_scope="terminating")
        self.assert_property_pass(
            "branch_relation",
            "Or(And(p >= 0, ycor == 3), And(p < 0, ycor == -3))",
        )

    def test_geo_xcor_fixed_ycor_zero_fail(self):
        self.load("u_xcor_fixed.tl", property_scope="terminating")
        self.assert_property_fail("ycor_zero", "ycor == 0")

    def test_geo_loop_diagonal_heading_grid_safe(self):
        self.load("u_loop_diagonal.tl", property_scope="all")
        self.assert_heading_grid_safe("heading_grid", "xcor == xcor")

    def test_geo_loop_diagonal_heading_range_pass(self):
        self.load("u_loop_diagonal.tl", property_scope="all")
        self.assert_property_pass("heading_range", "And(heading >= 0, heading < 360)")

class TestUniversalPen(ChironTestCase):
    """Pen-state properties - pen starts False in universal mode."""

    MODE = "universal"

    def test_pen_no_touch_pendown_pass(self):
        self.load("u_pen_no_touch.tl", property_scope="all")
        self.assert_property_pass("pendown_true", "pendown")

    def test_pen_no_touch_not_pendown_fail(self):
        self.load("u_pen_no_touch.tl", property_scope="all")
        self.assert_property_fail("pendown_false", "Not(pendown)")

    def test_pen_up_all_scope_pendown_fail(self):
        self.load("u_pen_up.tl", property_scope="all")
        self.assert_property_fail("pendown_true", "pendown")

    def test_pen_up_term_scope_not_pendown_pass(self):
        self.load("u_pen_up.tl", property_scope="terminating")
        self.assert_property_pass("pendown_false", "Not(pendown)")

    def test_pen_up_term_scope_pendown_fail(self):
        self.load("u_pen_up.tl", property_scope="terminating")
        self.assert_property_fail("pendown_true", "pendown")

    def test_branch_pen_term_relation_pass(self):
        self.load("u_branch_pen.tl", property_scope="terminating")
        self.assert_property_pass(
            "branch_relation",
            "Or(And(x >= 0, Not(pendown)), And(x < 0, pendown))",
        )

    def test_branch_pen_term_pendown_fail(self):
        self.load("u_branch_pen.tl", property_scope="terminating")
        self.assert_property_fail("pendown_true", "pendown")

    def test_branch_pen_adv_term_relation_pass(self):
        self.load("u_branch_pen_adv.tl", property_scope="terminating")
        self.assert_property_pass(
            "branch_relation",
            "Or(And(a + b >= b, Not(pendown)), And(a + b < b, pendown))",
        )

    def test_branch_pen_adv_term_pendown_fail(self):
        self.load("u_branch_pen_adv.tl", property_scope="terminating")
        self.assert_property_fail("pendown_true", "pendown")

    def test_branch_pen_adv_term_sign_relation_pass(self):
        self.load("u_branch_pen_adv.tl", property_scope="terminating")
        self.assert_property_pass(
            "sign_relation",
            "Or(And(a < 0, pendown), And(a >= 0, Not(pendown)))",
        )

    def test_loop_pen_term_pendown_pass(self):
        self.load("u_loop_pen.tl", property_scope="terminating")
        self.assert_property_pass("pendown_true", "pendown")

    def test_loop_pen_term_not_pendown_fail(self):
        self.load("u_loop_pen.tl", property_scope="terminating")
        self.assert_property_fail("pendown_false", "Not(pendown)")

class TestUniversalDirectional(ChironTestCase):
    """Heading properties - fail because heading starts arbitrary."""

    MODE = "universal"

    def test_heading_non_grid_unsafe(self):
        self.load("u_heading_non_grid.tl", property_scope="all")
        self.assert_heading_grid_unsafe("heading_grid", "xcor == xcor")

    def test_heading_net_zero_grid_safe(self):
        self.load("u_net_zero_turn.tl", property_scope="all")
        self.assert_heading_grid_safe("heading_grid", "xcor == xcor")

    def test_heading_net_zero_range_pass(self):
        self.load("u_net_zero_turn.tl", property_scope="all")
        self.assert_property_pass("heading_range", "And(heading >= 0, heading < 360)")

    def test_heading_on_spot_grid_safe(self):
        self.load("u_on_spot_turn.tl", property_scope="all", hints=["heading_on_grid_always"])
        self.assert_heading_grid_safe("heading_grid", "xcor == xcor")

    def test_heading_on_spot_range_pass(self):
        self.load("u_on_spot_turn.tl", property_scope="all", hints=["heading_on_grid_always"])
        self.assert_property_pass("heading_range", "And(heading >= 0, heading < 360)")

    def test_heading_fixed_left_grid_safe(self):
        self.load("u_fixed_left.tl", property_scope="all")
        self.assert_heading_grid_safe("heading_grid", "xcor == xcor")

    def test_heading_fixed_left_range_pass(self):
        self.load("u_fixed_left.tl", property_scope="all")
        self.assert_property_pass("heading_range", "And(heading >= 0, heading < 360)")

if __name__ == "__main__":
    unittest.main()
