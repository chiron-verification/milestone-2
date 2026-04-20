"""
Tests for semantic helper-string support in semantic_properties.py.
"""

import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CHC_DIR = os.path.abspath(os.path.join(_THIS_DIR, ".."))

if _CHC_DIR not in sys.path:
    sys.path.insert(0, _CHC_DIR)

from semantic_properties import (
    transpile_property_expr,
    transpile_user_properties,
)
from helpers import ChironTestCase


class TestSemanticTranspile(unittest.TestCase):
    def test_transpile_simple_helper(self):
        self.assertEqual(transpile_property_expr("is_nonnegative(v)"), "v >= 0")

    def test_transpile_boolean_and_helpers(self):
        expr = "is_nonnegative(x) and is_less_equal(x, 10)"
        self.assertEqual(transpile_property_expr(expr), "And(x >= 0, x <= 10)")

    def test_transpile_relation_guarded(self):
        expr = "relation_guarded(x >= 0, pen_is_up(), pen_is_down())"
        got = transpile_property_expr(expr)
        want = "Or(And((x >= 0), Not(pendown)), And(Not((x >= 0)), pendown))"
        self.assertEqual(got, want)

    def test_transpile_implies(self):
        expr = "Implies(is_nonnegative(x), is_nonnegative(y))"
        self.assertEqual(transpile_property_expr(expr), "Or(Not(x >= 0), y >= 0)")

    def test_transpile_chain_comparison(self):
        self.assertEqual(transpile_property_expr("a < b < c"), "And((a < b), (b < c))")

    def test_transpile_unknown_call_preserved(self):
        self.assertEqual(transpile_property_expr("custom_pred(x, 1)"), "custom_pred(x, 1)")

    def test_transpile_rejects_keyword_args(self):
        with self.assertRaisesRegex(ValueError, "Keyword args are not supported"):
            transpile_property_expr("is_between(v=v, lo=0, hi=10)")

    def test_transpile_rejects_unsupported_syntax(self):
        with self.assertRaisesRegex(ValueError, "Unsupported syntax"):
            transpile_property_expr("[x for x in xs]")

    def test_transpile_builtin_and_call(self):
        expr = "And(is_nonnegative(x), is_less_equal(x, 10))"
        self.assertEqual(transpile_property_expr(expr), "And(x >= 0, x <= 10)")

    def test_transpile_builtin_or_call(self):
        expr = "Or(is_equal(x, 0), is_equal(x, 1))"
        self.assertEqual(transpile_property_expr(expr), "Or(x == 0, x == 1)")

    def test_transpile_builtin_not_call(self):
        expr = "Not(is_equal(x, 0))"
        self.assertEqual(transpile_property_expr(expr), "Not(x == 0)")

    def test_transpile_builtin_implies_call(self):
        expr = "Implies(is_nonnegative(x), is_nonnegative(y))"
        self.assertEqual(transpile_property_expr(expr), "Or(Not(x >= 0), y >= 0)")

    def test_transpile_lowercase_implies_helper(self):
        expr = "implies(is_nonnegative(x), is_nonnegative(y))"
        self.assertEqual(transpile_property_expr(expr), "Or(Not(x >= 0), y >= 0)")

    def test_transpile_python_not(self):
        expr = "not is_nonnegative(x)"
        self.assertEqual(transpile_property_expr(expr), "Not(x >= 0)")

    def test_transpile_unary_minus_constant(self):
        expr = "is_equal(v, -3)"
        self.assertEqual(transpile_property_expr(expr), "v == (-3)")

    def test_transpile_binop_arguments(self):
        expr = "is_equal(x + y, z - 1)"
        self.assertEqual(transpile_property_expr(expr), "(x + y) == (z - 1)")

    def test_transpile_mod_expression(self):
        expr = "is_equal(x % 15, 0)"
        self.assertEqual(transpile_property_expr(expr), "(x % 15) == 0")

    def test_transpile_direct_compare_with_binop(self):
        expr = "(x + y) >= 0"
        self.assertEqual(transpile_property_expr(expr), "((x + y) >= 0)")

    def test_transpile_bool_constants(self):
        expr = "True and False"
        self.assertEqual(transpile_property_expr(expr), "And(True, False)")

    def test_transpile_helper_is_zero(self):
        self.assertEqual(transpile_property_expr("is_zero(a)"), "a == 0")

    def test_transpile_helper_is_nonzero(self):
        self.assertEqual(transpile_property_expr("is_nonzero(a)"), "a != 0")

    def test_transpile_helper_is_positive(self):
        self.assertEqual(transpile_property_expr("is_positive(a)"), "a > 0")

    def test_transpile_helper_is_negative(self):
        self.assertEqual(transpile_property_expr("is_negative(a)"), "a < 0")

    def test_transpile_helper_is_nonpositive(self):
        self.assertEqual(transpile_property_expr("is_nonpositive(a)"), "a <= 0")

    def test_transpile_helper_is_greater(self):
        self.assertEqual(transpile_property_expr("is_greater(a, b)"), "a > b")

    def test_transpile_helper_is_greater_equal(self):
        self.assertEqual(transpile_property_expr("is_greater_equal(a, b)"), "a >= b")

    def test_transpile_helper_is_less(self):
        self.assertEqual(transpile_property_expr("is_less(a, b)"), "a < b")

    def test_transpile_helper_is_not_equal(self):
        self.assertEqual(transpile_property_expr("is_not_equal(a, b)"), "a != b")

    def test_transpile_helper_between(self):
        expr = "is_between(v, 0, 10)"
        self.assertEqual(transpile_property_expr(expr), "And(v >= 0, v <= 10)")

    def test_transpile_helper_strict_between(self):
        expr = "is_strictly_between(v, 0, 10)"
        self.assertEqual(transpile_property_expr(expr), "And(v > 0, v < 10)")

    def test_transpile_helper_is_one_of(self):
        expr = "is_one_of(v, 1, 2, 3)"
        self.assertEqual(transpile_property_expr(expr), "Or(v == 1, v == 2, v == 3)")

    def test_transpile_helper_is_multiple_of(self):
        expr = "is_multiple_of(v, 15)"
        self.assertEqual(transpile_property_expr(expr), "v % 15 == 0")

    def test_transpile_helper_sum_is(self):
        expr = "sum_is(a, b, c)"
        self.assertEqual(transpile_property_expr(expr), "a + b == c")

    def test_transpile_helper_diff_is(self):
        expr = "diff_is(a, b, c)"
        self.assertEqual(transpile_property_expr(expr), "a - b == c")

    def test_transpile_helper_linear_eq(self):
        expr = "linear_eq(a + b, c)"
        self.assertEqual(transpile_property_expr(expr), "(a + b) == c")

    def test_transpile_helper_not_prop(self):
        expr = "not_prop(is_equal(x, 0))"
        self.assertEqual(transpile_property_expr(expr), "Not(x == 0)")

    def test_transpile_helper_all_of_empty(self):
        self.assertEqual(transpile_property_expr("all_of()"), "True")

    def test_transpile_helper_any_of_empty(self):
        self.assertEqual(transpile_property_expr("any_of()"), "False")

    def test_transpile_builtin_and_empty(self):
        self.assertEqual(transpile_property_expr("And()"), "True")

    def test_transpile_builtin_or_empty(self):
        self.assertEqual(transpile_property_expr("Or()"), "False")

    def test_transpile_pen_helpers(self):
        self.assertEqual(transpile_property_expr("pen_is_up()"), "Not(pendown)")
        self.assertEqual(transpile_property_expr("pen_is_down()"), "pendown")

    def test_transpile_position_helpers(self):
        self.assertEqual(
            transpile_property_expr("position_in_box(-10, 50, -10, 30)"),
            "And(xcor >= (-10), xcor <= 50, ycor >= (-10), ycor <= 30)",
        )
        self.assertEqual(
            transpile_property_expr("at_position(10, 20)"),
            "And(xcor == 10, ycor == 20)",
        )
        self.assertEqual(transpile_property_expr("x_equals(5)"), "xcor == 5")
        self.assertEqual(transpile_property_expr("y_equals(7)"), "ycor == 7")
        self.assertEqual(transpile_property_expr("on_diagonal()"), "xcor == ycor")

    def test_transpile_heading_helpers(self):
        self.assertEqual(transpile_property_expr("heading_in_range()"), "And(heading >= 0, heading < 360)")
        self.assertEqual(transpile_property_expr("heading_is(90)"), "heading == 90")
        self.assertEqual(transpile_property_expr("heading_in(0, 90)"), "Or(heading == 0, heading == 90)")
        self.assertEqual(transpile_property_expr("heading_on_15_grid()"), "heading % 15 == 0")
        self.assertEqual(transpile_property_expr("heading_multiple_of(30)"), "heading % 30 == 0")
        self.assertEqual(
            transpile_property_expr("heading_cardinal()"),
            "Or(heading == 0, heading == 90, heading == 180, heading == 270)",
        )

    def test_transpile_var_helpers(self):
        self.assertEqual(transpile_property_expr("var_nonnegative(v)"), "v >= 0")
        self.assertEqual(transpile_property_expr("var_bounded(v, 0, 10)"), "And(v >= 0, v <= 10)")
        self.assertEqual(
            transpile_property_expr("vars_all_nonnegative(a, b, c)"),
            "And(a >= 0, b >= 0, c >= 0)",
        )

    def test_transpile_unknown_nested_call_preserved(self):
        expr = "foo(is_nonnegative(x), bar(y))"
        self.assertEqual(transpile_property_expr(expr), "foo(x >= 0, bar(y))")

    def test_transpile_relation_guarded_with_exprs(self):
        expr = "relation_guarded(x + y >= 0, is_equal(z, 0), is_equal(z, 1))"
        want = "Or(And(((x + y) >= 0), z == 0), And(Not(((x + y) >= 0)), z == 1))"
        self.assertEqual(transpile_property_expr(expr), want)

    def test_transpile_rejects_helper_arity_too_few(self):
        with self.assertRaisesRegex(ValueError, "is_nonnegative expects 1 args"):
            transpile_property_expr("is_nonnegative()")

    def test_transpile_rejects_helper_arity_too_many(self):
        with self.assertRaisesRegex(ValueError, "heading_is expects 1 args"):
            transpile_property_expr("heading_is(0, 90)")

    def test_transpile_rejects_helper_min_arity(self):
        with self.assertRaisesRegex(ValueError, "heading_in expects at least 1 args"):
            transpile_property_expr("heading_in()")

    def test_transpile_rejects_builtin_not_arity(self):
        with self.assertRaisesRegex(ValueError, "Not expects 1 args"):
            transpile_property_expr("Not(x, y)")

    def test_transpile_rejects_builtin_implies_arity(self):
        with self.assertRaisesRegex(ValueError, "Implies expects 2 args"):
            transpile_property_expr("Implies(x)")

    def test_transpile_rejects_non_simple_call_name(self):
        with self.assertRaisesRegex(ValueError, "Only simple function-call names are supported"):
            transpile_property_expr("obj.f(x)")


class TestSemanticPropertyList(unittest.TestCase):
    class _P:
        def __init__(self, name: str, expr: str):
            self.name = name
            self.expr = expr

    def test_transpile_user_properties_from_objects(self):
        props = [self._P("p1", "is_nonnegative(v)")]
        out = transpile_user_properties(props)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].name, "p1")
        self.assertEqual(out[0].expr, "v >= 0")

    def test_transpile_user_properties_from_tuples(self):
        props = [("p1", "is_nonnegative(v)"), ("p2", "is_positive(v)")]
        out = transpile_user_properties(props)
        self.assertEqual([p.name for p in out], ["p1", "p2"])
        self.assertEqual([p.expr for p in out], ["v >= 0", "v > 0"])

    def test_transpile_user_properties_rejects_invalid_item(self):
        with self.assertRaisesRegex(TypeError, "Each property must be"):
            transpile_user_properties([{"name": "p", "expr": "is_nonnegative(v)"}])


class TestSemanticArithmeticDefault(ChironTestCase):
    """Default-mode arithmetic checks using helper-style semantic properties."""

    MODE = "default"

    def test_assign_nonnegative_pass(self):
        self.load("assign_basic.tl")
        self.assert_semantic_property_pass("z_nonneg_sem", "is_nonnegative(z)")

    def test_assign_upper_fail(self):
        self.load("assign_basic.tl")
        self.assert_semantic_property_fail("z_upper_sem", "is_less_equal(z, 20)")

    def test_assign_bounded_pass(self):
        self.load("assign_basic.tl")
        self.assert_semantic_property_pass(
            "x_bounded_sem",
            "all_of(is_nonnegative(x), is_less_equal(x, 10))",
        )


class TestSemanticArithmeticSpecific(ChironTestCase):
    """Specific-mode arithmetic checks using helper-style semantic properties."""

    MODE = "specific"

    def test_rbw_nonnegative_pass(self):
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_semantic_property_pass("z_nonneg_sem", "is_nonnegative(z)")

    def test_rbw_upper_fail(self):
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_semantic_property_fail("z_upper_sem", "is_less_equal(z, 100)")

    def test_rbw_step_const_pass(self):
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_semantic_property_pass("step_const_sem", "is_equal(step, 50)")


class TestSemanticArithmeticUniversal(ChironTestCase):
    """Universal-mode arithmetic checks using helper-style semantic properties."""

    MODE = "universal"

    def test_clamp_nonnegative_terminating_pass(self):
        self.load("u_clamp_to_zero.tl", property_scope="terminating")
        self.assert_semantic_property_pass("z_nonneg_term_sem", "is_nonnegative(z)")

    def test_clamp_disjunction_terminating_pass(self):
        self.load("u_clamp_to_zero.tl", property_scope="terminating")
        self.assert_semantic_property_pass(
            "z_is_x_or_zero_sem",
            "any_of(is_equal(z, 0), is_equal(z, x))",
        )

    def test_clamp_eq_x_terminating_fail(self):
        self.load("u_clamp_to_zero.tl", property_scope="terminating")
        self.assert_semantic_property_fail("z_eq_x_sem", "is_equal(z, x)")

    def test_product_zero_multiplicative_relation_fail(self):
        self.load("u_product_zero.tl", property_scope="terminating")
        self.assert_semantic_property_fail("z_eq_xy_sem", "is_equal(z, x * y)")

    def test_same_post_x_minus_x_identity_pass(self):
        self.load("u_same_postcondition.tl", property_scope="terminating")
        self.assert_semantic_property_pass("z_eq_x_minus_x_sem", "is_equal(z, x - x)")

    def test_branch_merge_abs_diff_pass(self):
        self.load("u_branch_merge_affine.tl", property_scope="terminating")
        self.assert_semantic_property_pass(
            "abs_diff_sem",
            "any_of(is_equal(d, x - y), is_equal(d, y - x))",
        )

    def test_affine_linear_relation_fail(self):
        self.load("u_two_step_affine.tl", property_scope="terminating")
        self.assert_semantic_property_fail("affine_rel_sem", "is_equal(x - 2 * y, 6)")

    def test_euclid_avg_c_eq_2m_pass(self):
        self.load("u_euclid_avg.tl", property_scope="terminating")
        self.assert_semantic_property_pass("c_eq_2m_sem", "is_equal(c, 2 * m)")

    def test_euclid_avg_c_eq_2n_fail(self):
        self.load("u_euclid_avg.tl", property_scope="terminating")
        self.assert_semantic_property_fail("c_eq_2n_sem", "is_equal(c, 2 * n)")

    def test_swap_without_tmp_sum_pass(self):
        self.load("u_swap_without_tmp.tl", property_scope="terminating")
        self.assert_semantic_property_pass("sum_rel_sem", "is_equal(s, x + y)")

    def test_swap_without_tmp_equal_fail(self):
        self.load("u_swap_without_tmp.tl", property_scope="terminating")
        self.assert_semantic_property_fail("x_eq_y_sem", "is_equal(x, y)")


class TestSemanticGeometricDefault(ChironTestCase):
    """Default-mode geometric checks using helper-style semantic properties."""

    MODE = "default"

    def test_square_box_pass(self):
        self.load("square_goto.tl")
        self.assert_semantic_property_pass(
            "square_box_sem",
            "position_in_box(-10, 110, -10, 110)",
        )

    def test_square_tight_x_fail(self):
        self.load("square_goto.tl")
        self.assert_semantic_property_fail("square_tight_x_sem", "is_less_equal(xcor, 30)")

    def test_computed_y_discrete_pass(self):
        self.load("goto_computed.tl")
        self.assert_semantic_property_pass(
            "computed_y_discrete_sem",
            "any_of(y_equals(0), y_equals(20))",
        )

    def test_no_movement_x_zero_pass(self):
        self.load("loop_cond.tl")
        self.assert_semantic_property_pass("loop_cond_x_zero_sem", "x_equals(0)")

    def test_square_strictly_positive_x_fail(self):
        self.load("square_goto.tl")
        self.assert_semantic_property_fail("square_x_positive_sem", "is_positive(xcor)")


class TestSemanticGeometricSpecific(ChironTestCase):
    """Specific-mode geometric checks using helper-style semantic properties."""

    MODE = "specific"

    def test_param_goto_box_pass(self):
        self.load("param_goto.tl", params={"startx": 10, "starty": 20})
        self.assert_semantic_property_pass(
            "param_goto_box_sem",
            "all_of(is_less_equal(xcor, 10), is_less_equal(ycor, 20))",
        )

    def test_param_goto_tight_fail(self):
        self.load("param_goto.tl", params={"startx": 100, "starty": 200})
        self.assert_semantic_property_fail(
            "param_goto_tight_sem",
            "any_of(is_less_equal(xcor, 50), is_less_equal(ycor, 150))",
        )

    def test_param_goto_nonnegative_fail(self):
        self.load("param_goto.tl", params={"startx": -50, "starty": 0})
        self.assert_semantic_property_fail("param_goto_nonneg_sem", "is_nonnegative(xcor)")

    def test_param_goto_y_bound_pass(self):
        self.load("param_goto.tl", params={"startx": 5, "starty": 10})
        self.assert_semantic_property_pass("param_goto_y_bound_sem", "is_less_equal(ycor, 50)")


class TestSemanticGeometricUniversal(ChironTestCase):
    """Universal-mode geometric checks using helper-style semantic properties."""

    MODE = "universal"

    def test_fixed_target_point_pass(self):
        self.load("u_fixed_target.tl", property_scope="terminating")
        self.assert_semantic_property_pass("u_fixed_target_point_sem", "at_position(10, 20)")

    def test_fixed_target_x_zero_fail(self):
        self.load("u_fixed_target.tl", property_scope="terminating")
        self.assert_semantic_property_fail("u_fixed_target_x_zero_sem", "x_equals(0)")

    def test_fixed_target_user_delta_pass(self):
        self.load("u_fixed_target_user.tl", property_scope="terminating")
        self.assert_semantic_property_pass("u_fixed_target_delta_sem", "is_equal(ycor - xcor, 7)")

    def test_xcor_fixed_y_choices_pass(self):
        self.load("u_xcor_fixed.tl", property_scope="terminating")
        self.assert_semantic_property_pass(
            "u_xcor_fixed_y_choices_sem",
            "any_of(y_equals(3), y_equals(-3))",
        )

    def test_xcor_fixed_y_zero_fail(self):
        self.load("u_xcor_fixed.tl", property_scope="terminating")
        self.assert_semantic_property_fail("u_xcor_fixed_y_zero_sem", "y_equals(0)")

    def test_normalize_x_diagonal_pass(self):
        self.load("u_normalize_x.tl", property_scope="terminating")
        self.assert_semantic_property_pass("u_normalize_x_diag_sem", "on_diagonal()")

    def test_xcor_fixed_at_pc_then_point_pass(self):
        self.load("u_xcor_fixed.tl", property_scope="at_pc", pc_target=2)
        self.assert_semantic_property_pass(
            "u_xcor_fixed_then_point_sem",
            "all_of(at_position(8, 3), is_nonnegative(p))",
        )

    def test_xcor_fixed_at_pc_merge_y_three_fail(self):
        self.load("u_xcor_fixed.tl", property_scope="at_pc", pc_target=4)
        self.assert_semantic_property_fail("u_xcor_fixed_merge_y_three_sem", "y_equals(3)")


class TestSemanticPenDefault(ChironTestCase):
    """Default-mode pen-state checks using helper-style semantic properties."""

    MODE = "default"

    def test_assign_pen_up_pass(self):
        self.load("assign_basic.tl")
        self.assert_semantic_property_pass("default_assign_pen_up_sem", "pen_is_up()")

    def test_pen_only_tautology_pass(self):
        self.load("pen_only.tl")
        self.assert_semantic_property_pass(
            "default_pen_taut_sem",
            "any_of(pen_is_down(), pen_is_up())",
        )

    def test_pen_only_pen_up_fail(self):
        self.load("pen_only.tl")
        self.assert_semantic_property_fail("default_pen_only_up_sem", "pen_is_up()")

    def test_loop_basic_pen_up_pass(self):
        self.load("loop_basic.tl")
        self.assert_semantic_property_pass("default_loop_pen_up_sem", "pen_is_up()")

    def test_pen_with_var_pen_up_fail(self):
        self.load("pen_with_var.tl")
        self.assert_semantic_property_fail("default_pen_with_var_up_sem", "pen_is_up()")


class TestSemanticPenSpecific(ChironTestCase):
    """Specific-mode pen-state checks using helper-style semantic properties."""

    MODE = "specific"

    def test_param_pen_pen_up_fail(self):
        self.load("param_pen.tl", params={"base": 5})
        self.assert_semantic_property_fail("specific_param_pen_up_sem", "pen_is_up()")

    def test_param_pen_cond_above_threshold_fail(self):
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 10})
        self.assert_semantic_property_fail("specific_pen_cond_up_fail_sem", "pen_is_up()")

    def test_param_pen_cond_below_threshold_pass(self):
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 3})
        self.assert_semantic_property_pass("specific_pen_cond_up_pass_sem", "pen_is_up()")

    def test_param_pen_cond_at_threshold_pass(self):
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 5})
        self.assert_semantic_property_pass("specific_pen_cond_up_eq_sem", "pen_is_up()")

    def test_param_pen_cond_one_above_threshold_fail(self):
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 6})
        self.assert_semantic_property_fail("specific_pen_cond_up_plus1_sem", "pen_is_up()")


class TestSemanticPenUniversal(ChironTestCase):
    """Universal-mode pen-state checks using helper-style semantic properties."""

    MODE = "universal"

    def test_pen_no_touch_down_pass(self):
        self.load("u_pen_no_touch.tl", property_scope="all")
        self.assert_semantic_property_pass("u_pen_no_touch_down_sem", "pen_is_down()")

    def test_pen_no_touch_up_fail(self):
        self.load("u_pen_no_touch.tl", property_scope="all")
        self.assert_semantic_property_fail("u_pen_no_touch_up_sem", "pen_is_up()")

    def test_pen_up_all_scope_down_fail(self):
        self.load("u_pen_up.tl", property_scope="all")
        self.assert_semantic_property_fail("u_pen_up_all_down_sem", "pen_is_down()")

    def test_pen_up_terminating_up_pass(self):
        self.load("u_pen_up.tl", property_scope="terminating")
        self.assert_semantic_property_pass("u_pen_up_term_up_sem", "pen_is_up()")

    def test_pen_up_terminating_down_fail(self):
        self.load("u_pen_up.tl", property_scope="terminating")
        self.assert_semantic_property_fail("u_pen_up_term_down_sem", "pen_is_down()")

    def test_branch_pen_terminating_guarded_relation_pass(self):
        self.load("u_branch_pen.tl", property_scope="terminating")
        self.assert_semantic_property_pass(
            "u_branch_pen_guarded_sem",
            "relation_guarded(x >= 0, pen_is_up(), pen_is_down())",
        )

    def test_branch_pen_terminating_down_fail(self):
        self.load("u_branch_pen.tl", property_scope="terminating")
        self.assert_semantic_property_fail("u_branch_pen_down_sem", "pen_is_down()")

    def test_branch_pen_at_pc_then_guard_pass(self):
        self.load("u_branch_pen.tl", property_scope="at_pc", pc_target=2)
        self.assert_semantic_property_pass(
            "u_branch_pen_atpc_then_sem",
            "all_of(is_nonnegative(x), pen_is_up())",
        )

    def test_branch_pen_at_pc_merge_then_only_fail(self):
        self.load("u_branch_pen.tl", property_scope="at_pc", pc_target=4)
        self.assert_semantic_property_fail(
            "u_branch_pen_atpc_merge_sem",
            "all_of(is_nonnegative(x), pen_is_up())",
        )

    def test_branch_pen_upto_pc_prefix_guarded_pass(self):
        self.load("u_branch_pen.tl", property_scope="upto_pc", pc_target=4)
        self.assert_semantic_property_pass(
            "u_branch_pen_upto_guarded_sem",
            "any_of(all_of(is_nonnegative(x), pen_is_up()), pen_is_down())",
        )

    def test_branch_pen_upto_pc_opposite_guard_fail(self):
        self.load("u_branch_pen.tl", property_scope="upto_pc", pc_target=4)
        self.assert_semantic_property_fail(
            "u_branch_pen_upto_opposite_sem",
            "any_of(all_of(is_negative(x), pen_is_down()), pen_is_up())",
        )

    def test_branch_pen_adv_sign_relation_pass(self):
        self.load("u_branch_pen_adv.tl", property_scope="terminating")
        self.assert_semantic_property_pass(
            "u_branch_pen_adv_sign_sem",
            "relation_guarded(a >= 0, pen_is_up(), pen_is_down())",
        )

    def test_loop_pen_terminating_down_pass(self):
        self.load("u_loop_pen.tl", property_scope="terminating")
        self.assert_semantic_property_pass("u_loop_pen_term_down_sem", "pen_is_down()")

    def test_loop_pen_terminating_up_fail(self):
        self.load("u_loop_pen.tl", property_scope="terminating")
        self.assert_semantic_property_fail("u_loop_pen_term_up_sem", "pen_is_up()")


class TestSemanticHeadingDefault(ChironTestCase):
    """Default-mode heading checks using helper-style semantic properties."""

    MODE = "default"

    def test_turns_only_heading_nonnegative_pass(self):
        self.load("turns_only.tl")
        self.assert_semantic_property_pass("default_heading_nonneg_sem", "is_nonnegative(heading)")

    def test_turns_only_heading_small_fail(self):
        self.load("turns_only.tl")
        self.assert_semantic_property_fail("default_heading_small_sem", "is_less_equal(heading, 90)")

    def test_assign_basic_heading_zero_pass(self):
        self.load("assign_basic.tl")
        self.assert_semantic_property_pass("default_heading_zero_sem", "heading_is(0)")

    def test_assign_basic_heading_positive_fail(self):
        self.load("assign_basic.tl")
        self.assert_semantic_property_fail("default_heading_pos_sem", "is_positive(heading)")

    def test_turns_15_heading_range_pass(self):
        self.load("turns_15.tl", hints=["heading_on_grid_always"])
        self.assert_semantic_property_pass("default_heading_range_sem", "heading_in_range()")


class TestSemanticHeadingSpecific(ChironTestCase):
    """Specific-mode heading checks using helper-style semantic properties."""

    MODE = "specific"

    def test_param_scale_heading_zero_pass(self):
        self.load("param_scale.tl", params={"scale": 10})
        self.assert_semantic_property_pass("specific_heading_zero_scale_sem", "heading_is(0)")

    def test_param_loop_heading_zero_pass(self):
        self.load("param_loop.tl", params={"start": 5})
        self.assert_semantic_property_pass("specific_heading_zero_loop_sem", "heading_is(0)")

    def test_param_cond_heading_positive_fail(self):
        self.load("param_cond.tl", params={"init": 80})
        self.assert_semantic_property_fail("specific_heading_pos_sem", "is_positive(heading)")

    def test_param_loop_heading_range_pass(self):
        self.load("param_loop.tl", params={"start": 5})
        self.assert_semantic_property_pass("specific_heading_range_sem", "heading_in_range()")


class TestSemanticHeadingUniversal(ChironTestCase):
    """Universal-mode heading checks using helper-style semantic properties."""

    MODE = "universal"

    def test_init_heading_range_pass(self):
        self.load("u_init_core.tl", property_scope="all")
        self.assert_semantic_property_pass("u_init_heading_range_sem", "heading_in_range()")

    def test_init_heading_zero_fail(self):
        self.load("u_init_core.tl", property_scope="all")
        self.assert_semantic_property_fail("u_init_heading_zero_sem", "heading_is(0)")

    def test_init_heading_cardinal_fail(self):
        self.load("u_init_core.tl", property_scope="all")
        self.assert_semantic_property_fail("u_init_heading_cardinal_sem", "heading_cardinal()")

    def test_net_zero_at_pc_on_15_grid_pass(self):
        self.load("u_net_zero_turn.tl", property_scope="at_pc", pc_target=1)
        self.assert_semantic_property_pass("u_net_zero_atpc_grid_sem", "heading_on_15_grid()")

    def test_net_zero_at_pc_multiple_of_30_fail(self):
        self.load("u_net_zero_turn.tl", property_scope="at_pc", pc_target=1)
        self.assert_semantic_property_fail("u_net_zero_atpc_30_sem", "heading_multiple_of(30)")

    def test_net_zero_upto_pc_on_15_grid_pass(self):
        self.load("u_net_zero_turn.tl", property_scope="upto_pc", pc_target=1)
        self.assert_semantic_property_pass("u_net_zero_upto_grid_sem", "heading_on_15_grid()")

    def test_net_zero_upto_pc_heading_zero_fail(self):
        self.load("u_net_zero_turn.tl", property_scope="upto_pc", pc_target=1)
        self.assert_semantic_property_fail("u_net_zero_upto_zero_sem", "heading_is(0)")

    def test_net_heading_preserved_range_pass(self):
        self.load(
            "u_net_heading_preserved.tl",
            property_scope="all",
            hints=["heading_on_grid_always"],
        )
        self.assert_semantic_property_pass("u_net_heading_preserved_range_sem", "heading_in_range()")

if __name__ == "__main__":
    unittest.main()
