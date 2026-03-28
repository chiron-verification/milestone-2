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
        self.assert_property_pass("z_nonneg", "z >= 0")

    def test_arith_rbw_z_upper_fail(self):
        """With step=50: z reaches 150 -> z <= 100 violated."""
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_property_fail("z_upper", "z <= 100")

    def test_arith_rbw_step_const(self):
        """step is never modified -> step=50 always holds."""
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_property_pass("step_pos", "step == 50")

    def test_arith_rbw_step_small_fail(self):
        """step=50 -> step <= 30 violated."""
        self.load("read_before_write.tl", params={"step": 50})
        self.assert_property_fail("step_small", "step <= 30")

    def test_arith_scale_pos_pass(self):
        """With scale=10: result reaches 50. result >= 0 holds throughout."""
        self.load("param_scale.tl", params={"scale": 10})
        self.assert_property_pass("result_nonneg", "result >= 0")

    def test_arith_scale_tight_fail(self):
        """With scale=10: result reaches 50. result <= 30 violated."""
        self.load("param_scale.tl", params={"scale": 10})
        self.assert_property_fail("result_tight", "result <= 30")

    def test_arith_scale_neg_fail(self):
        """With scale=-5: result = -25. result >= 0 violated."""
        self.load("param_scale.tl", params={"scale": -5})
        self.assert_property_fail("result_nonneg", "result >= 0")

    def test_arith_param_loop_acc_nonneg_pass(self):
        """With start=0: acc goes 0->10->20->30. acc >= 0 always."""
        self.load("param_loop.tl", params={"start": 0})
        self.assert_property_pass("acc_nonneg", "acc >= 0")

    def test_arith_param_loop_acc_tight_fail(self):
        """With start=0: acc reaches 30. acc <= 20 violated."""
        self.load("param_loop.tl", params={"start": 0})
        self.assert_property_fail("acc_tight", "acc <= 20")

    def test_arith_param_loop_acc_tight_fail_100(self):
        """With start=100: acc reaches 130. acc <= 120 violated."""
        self.load("param_loop.tl", params={"start": 100})
        self.assert_property_fail("acc_tight", "acc <= 120")

    def test_arith_param_cond_truebranch_pass(self):
        """With init=80 (>50): val goes 80->70. val >= 0 holds."""
        self.load("param_cond.tl", params={"init": 80})
        self.assert_property_pass("val_nonneg", "val >= 0")

    def test_arith_param_cond_tight_fail(self):
        """With init=80: val reaches 80. val <= 60 violated."""
        self.load("param_cond.tl", params={"init": 80})
        self.assert_property_fail("val_tight", "val <= 60")

class TestSpecificGeometric(ChironTestCase):
    """Geometric properties - goto coordinates driven by user-provided params."""

    MODE = "specific"

    def test_geo_goto_box_pass(self):
        """With startx=10, starty=20: xcor=10, ycor=20. Both within bounds."""
        self.load("param_goto.tl", params={"startx": 10, "starty": 20})
        self.assert_property_pass("box", "And(xcor <= 10, ycor <= 20)")

    def test_geo_goto_tight_fail(self):
        """With startx=100, starty=200: xcor=100. xcor <= 50 violated."""
        self.load("param_goto.tl", params={"startx": 100, "starty": 200})
        self.assert_property_fail("tight_x", "Or(xcor <= 50, ycor <= 150)")

    def test_geo_goto_neg_startx_fail(self):
        """With startx=-50: xcor=-50 -> xcor >= 0 violated."""
        self.load("param_goto.tl", params={"startx": -50, "starty": 0})
        self.assert_property_fail("xcor_nonneg", "xcor >= 0")

    def test_geo_goto_ycor_pass(self):
        """With startx=5, starty=10: ycor=10 <= 50 holds."""
        self.load("param_goto.tl", params={"startx": 5, "starty": 10})
        self.assert_property_pass("ycor_bound", "ycor <= 50")


class TestSpecificPen(ChironTestCase):
    """Pen properties - param_pen.tl reads :base before any write."""

    MODE = "specific"

    def test_pen_mark_nonneg_pass(self):
        """With base=5: mark = base+1 = 6. mark >= 0 holds."""
        self.load("param_pen.tl", params={"base": 5})
        self.assert_property_pass("mark_nonneg", "mark >= 0")

    def test_pen_always_up_fail(self):
        """param_pen.tl executes pendown -> Not(pendown) violated."""
        self.load("param_pen.tl", params={"base": 5})
        self.assert_property_fail("pen_always_up", "Not(pendown)")

    def test_pen_base_neg_mark_fail(self):
        """With base=-5: mark = base+1 = -4. mark >= 0 violated."""
        self.load("param_pen.tl", params={"base": -5})
        self.assert_property_fail("mark_nonneg", "mark >= 0")

    def test_pen_base_large_mark_pass(self):
        """With base=3: mark = 4. mark <= 10 holds."""
        self.load("param_pen.tl", params={"base": 3})
        self.assert_property_pass("mark_upper", "mark <= 10")


class TestSpecificDirectional(ChironTestCase):
    """Directional - heading stays 0 when there are no turns (concrete start)."""

    MODE = "specific"

    def test_dir_param_scale_heading_zero_pass(self):
        """param_scale.tl has no turns -> heading stays 0."""
        self.load("param_scale.tl", params={"scale": 10})
        self.assert_property_pass("heading_zero", "heading == 0")

    def test_dir_param_loop_heading_zero_pass(self):
        """param_loop.tl has no turns -> heading stays 0."""
        self.load("param_loop.tl", params={"start": 5})
        self.assert_property_pass("heading_zero", "heading == 0")

    def test_dir_param_cond_heading_nonzero_fail(self):
        """param_cond.tl has no turns -> heading is always 0, heading > 0 fails."""
        self.load("param_cond.tl", params={"init": 80})
        self.assert_property_fail("heading_pos", "heading > 0")


class TestSpecificTwoParams(ChironTestCase):
    """two_params.tl: diff = hi - lo, sum = hi + lo.
    The relationship between params (not just their individual values) determines outcomes."""

    MODE = "specific"

    def test_hi_gt_lo_diff_nonneg_pass(self):
        """hi=20 > lo=10: diff=10 >= 0 holds."""
        self.load("two_params.tl", params={"hi": 20, "lo": 10})
        self.assert_property_pass("diff_nonneg", "diff >= 0")

    def test_hi_lt_lo_diff_nonneg_fail(self):
        """hi=5 < lo=10: diff=-5 < 0 violated."""
        self.load("two_params.tl", params={"hi": 5, "lo": 10})
        self.assert_property_fail("diff_nonneg", "diff >= 0")

    def test_hi_eq_lo_diff_zero_pass(self):
        """hi=lo=10: diff=0 >= 0 holds (boundary between pass and fail)."""
        self.load("two_params.tl", params={"hi": 10, "lo": 10})
        self.assert_property_pass("diff_nonneg", "diff >= 0")

    def test_both_pos_sum_nonneg_pass(self):
        """hi=20, lo=10: sum=30 >= 0 holds."""
        self.load("two_params.tl", params={"hi": 20, "lo": 10})
        self.assert_property_pass("sum_nonneg", "sum >= 0")

    def test_both_neg_sum_nonneg_fail(self):
        """hi=-5, lo=-10: sum=-15 < 0 violated."""
        self.load("two_params.tl", params={"hi": -5, "lo": -10})
        self.assert_property_fail("sum_nonneg", "sum >= 0")

    def test_cancelling_sum_zero_pass(self):
        """hi=5, lo=-5: sum=0 >= 0 holds (exactly zero)."""
        self.load("two_params.tl", params={"hi": 5, "lo": -5})
        self.assert_property_pass("sum_nonneg", "sum >= 0")


class TestSpecificCountdown(ChironTestCase):
    """param_countdown.tl: counter counts down from :n over 5 steps.
    counter >= 0 holds iff n >= 5 — clean boundary driven purely by the param."""

    MODE = "specific"

    def test_n_at_boundary_pass(self):
        """n=5: counter goes 5->4->3->2->1->0. counter >= 0 holds (hits 0 exactly)."""
        self.load("param_countdown.tl", params={"n": 5})
        self.assert_property_pass("counter_nonneg", "counter >= 0")

    def test_n_one_below_boundary_fail(self):
        """n=4: counter reaches -1 on the last step. counter >= 0 violated."""
        self.load("param_countdown.tl", params={"n": 4})
        self.assert_property_fail("counter_nonneg", "counter >= 0")

    def test_n_large_pass(self):
        """n=10: counter goes 10->9->...->5. counter >= 0 holds."""
        self.load("param_countdown.tl", params={"n": 10})
        self.assert_property_pass("counter_nonneg", "counter >= 0")

    def test_n_negative_fail(self):
        """n=-1: counter starts at -1. counter >= 0 violated immediately."""
        self.load("param_countdown.tl", params={"n": -1})
        self.assert_property_fail("counter_nonneg", "counter >= 0")

    def test_upper_bound_pass(self):
        """n=10: counter starts at 10. counter <= 10 holds at all states."""
        self.load("param_countdown.tl", params={"n": 10})
        self.assert_property_pass("counter_upper", "counter <= 10")

    def test_upper_bound_fail(self):
        """n=11: counter starts at 11 which exceeds 10. counter <= 10 violated."""
        self.load("param_countdown.tl", params={"n": 11})
        self.assert_property_fail("counter_upper", "counter <= 10")


class TestSpecificAccumulate(ChironTestCase):
    """param_accumulate.tl: total = base, base+inc, base+2*inc, base+3*inc.
    Outcome depends on the *combination* of two params — neither alone is sufficient."""

    MODE = "specific"

    def test_pos_inc_nonneg_pass(self):
        """base=0, inc=5: total grows 0->5->10->15. total >= 0 holds."""
        self.load("param_accumulate.tl", params={"base": 0, "inc": 5})
        self.assert_property_pass("total_nonneg", "total >= 0")

    def test_neg_inc_nonneg_fail(self):
        """base=0, inc=-1: total goes 0->-1->... total >= 0 violated."""
        self.load("param_accumulate.tl", params={"base": 0, "inc": -1})
        self.assert_property_fail("total_nonneg", "total >= 0")

    def test_base_offsets_neg_inc_pass(self):
        """base=3, inc=-1: total=3->2->1->0. Hits 0 exactly — boundary case. PASS."""
        self.load("param_accumulate.tl", params={"base": 3, "inc": -1})
        self.assert_property_pass("total_nonneg", "total >= 0")

    def test_base_one_short_fail(self):
        """base=2, inc=-1: total=2->1->0->-1. One step too few. FAIL."""
        self.load("param_accumulate.tl", params={"base": 2, "inc": -1})
        self.assert_property_fail("total_nonneg", "total >= 0")

    def test_upper_bound_pass(self):
        """base=0, inc=5: total reaches 15. total <= 15 holds."""
        self.load("param_accumulate.tl", params={"base": 0, "inc": 5})
        self.assert_property_pass("total_upper", "total <= 15")

    def test_upper_bound_fail(self):
        """base=0, inc=6: total reaches 18. total <= 15 violated."""
        self.load("param_accumulate.tl", params={"base": 0, "inc": 6})
        self.assert_property_fail("total_upper", "total <= 15")


class TestSpecificNestedCond(ChironTestCase):
    """param_nested_cond.tl: clamps :a at 100 if > 100, doubles if in (0,100], zeroes if <= 0.
    Two distinct boundary points (at 80 and 100) produce four different outcome regions."""

    MODE = "specific"

    def test_double_at_upper_boundary_pass(self):
        """a=80: takes double branch, val=160. val <= 160 holds."""
        self.load("param_nested_cond.tl", params={"a": 80})
        self.assert_property_pass("val_bound", "val <= 160")

    def test_double_one_over_boundary_fail(self):
        """a=81: takes double branch, val=162 > 160. val <= 160 violated."""
        self.load("param_nested_cond.tl", params={"a": 81})
        self.assert_property_fail("val_bound", "val <= 160")

    def test_clamp_restores_pass(self):
        """a=101: takes clamp branch (>100), val=100 <= 160. val <= 160 holds."""
        self.load("param_nested_cond.tl", params={"a": 101})
        self.assert_property_pass("val_bound", "val <= 160")

    def test_double_at_clamp_boundary_fail(self):
        """a=100: 100>100 is False, takes double branch, val=200 > 160. FAIL."""
        self.load("param_nested_cond.tl", params={"a": 100})
        self.assert_property_fail("val_bound", "val <= 160")

    def test_neg_param_lower_bound_pass(self):
        """a=-10: val reaches -10 then recovers to 0. val >= -10 holds at all states."""
        self.load("param_nested_cond.tl", params={"a": -10})
        self.assert_property_pass("val_lower", "val >= -10")

    def test_neg_param_intermediate_fail(self):
        """a=-10: val reaches -10 at state after :val=:a. val >= 0 violated there."""
        self.load("param_nested_cond.tl", params={"a": -10})
        self.assert_property_fail("val_nonneg", "val >= 0")

    def test_zero_param_zeroed_pass(self):
        """a=0: 0>0 is False, takes else branch, val=0. val >= 0 holds."""
        self.load("param_nested_cond.tl", params={"a": 0})
        self.assert_property_pass("val_nonneg", "val >= 0")


class TestSpecificLoopMove(ChironTestCase):
    """param_loop_move.tl: x = start, then x += step and goto(x, 0) for 3 iters.
    Combines loop arithmetic with geometric state — xcor tracks x exactly."""

    MODE = "specific"

    def test_xcor_final_pass(self):
        """start=0, step=10: xcor goes 0->10->20->30. xcor <= 30 holds."""
        self.load("param_loop_move.tl", params={"start": 0, "step": 10})
        self.assert_property_pass("xcor_final", "xcor <= 30")

    def test_xcor_tight_fail(self):
        """start=0, step=10: xcor reaches 30. xcor <= 20 violated."""
        self.load("param_loop_move.tl", params={"start": 0, "step": 10})
        self.assert_property_fail("xcor_tight", "xcor <= 20")

    def test_nonzero_start_shifts_bound_fail(self):
        """start=5, step=10: xcor reaches 35. xcor <= 30 violated."""
        self.load("param_loop_move.tl", params={"start": 5, "step": 10})
        self.assert_property_fail("xcor_shifted", "xcor <= 30")

    def test_bounding_box_fail(self):
        """start=0, step=8: xcor reaches 24. xcor <= 30 holds."""
        self.load("param_loop_move.tl", params={"start": 0, "step": 8})
        self.assert_property_fail("xcor_bounded", "And(xcor >= 0, xcor <= 16)")

    def test_smaller_step_fits_pass(self):
        """start=0, step=8: xcor reaches 24. xcor <= 30 holds."""
        self.load("param_loop_move.tl", params={"start": 0, "step": 8})
        self.assert_property_pass("xcor_small_step", "xcor <= 30")

    def test_x_and_xcor_agree_pass(self):
        """xcor mirrors x throughout — both bounded by start + 3*step."""
        self.load("param_loop_move.tl", params={"start": 0, "step": 10})
        self.assert_property_pass("both_bounded", "And(x <= 30, xcor <= 30)")

    def test_neg_step_xcor_nonpos_pass(self):
        """start=0, step=-5: x goes 0->-5->-10->-15. xcor <= 0 holds after first goto."""
        self.load("param_loop_move.tl", params={"start": 0, "step": -5})
        self.assert_property_pass("xcor_nonpos", "xcor <= 0")

    def test_heading_unaffected_pass(self):
        """goto does not change heading. heading == 0 holds throughout."""
        self.load("param_loop_move.tl", params={"start": 0, "step": 10})
        self.assert_property_pass("heading_zero", "heading == 0")

    def test_ycor_affected_fail(self):
        """goto(x, 0) should not change ycor. ycor == 0 violated after first goto."""
        self.load("param_loop_move.tl", params={"start": 0, "step": 10})
        self.assert_property_fail("ycor_pos", "ycor > 0")


class TestSpecificPenCond(ChironTestCase):
    """param_pen_cond.tl: pen goes down only if :value > :threshold.
    Tests param-driven pen behaviour — pen state is a function of two params."""

    MODE = "specific"

    def test_above_threshold_pen_fires_fail(self):
        """value=10 > threshold=5: pendown executes. Not(pendown) violated."""
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 10})
        self.assert_property_fail("pen_always_up", "Not(pendown)")

    def test_below_threshold_pen_stays_up_pass(self):
        """value=3 <= threshold=5: pendown never executes. Not(pendown) holds."""
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 3})
        self.assert_property_pass("pen_always_up", "Not(pendown)")

    def test_at_threshold_pen_stays_up_pass(self):
        """value=5, threshold=5: 5 > 5 is False. pendown never executes. Not(pendown) holds."""
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 5})
        self.assert_property_pass("pen_always_up", "Not(pendown)")

    def test_one_above_threshold_pen_fires_fail(self):
        """value=6, threshold=5: 6 > 5 is True. pendown executes. Not(pendown) violated."""
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 6})
        self.assert_property_fail("pen_always_up", "Not(pendown)")

    def test_above_threshold_current_reduced_pass(self):
        """value=10, threshold=5: true branch runs, current = 10-5 = 5. current >= 0 holds."""
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 10})
        self.assert_property_pass("current_nonneg", "current >= 0")

    def test_below_threshold_current_raised_pass(self):
        """value=3, threshold=5: else branch runs, current = 3+5 = 8. current >= 0 holds."""
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": 3})
        self.assert_property_pass("current_nonneg", "current >= 0")

    def test_neg_value_below_threshold_current_fail(self):
        """value=-3, threshold=5: -3>5 False, current=-3+5=2. But at intermediate state
        current=-3 violates current >= 0."""
        self.load("param_pen_cond.tl", params={"threshold": 5, "value": -3})
        self.assert_property_fail("current_nonneg", "current >= 0")


class TestSpecificChain(ChironTestCase):
    """param_chain.tl: a=seed, b=a+1, c=a+b, d=b+c.
    d = 3*seed + 2 — a closed-form result derived through a chain of dependent assignments.
    The solver must track the chain to verify d <= 20, with boundary at seed=6."""

    MODE = "specific"

    def test_seed_at_boundary_pass(self):
        """seed=6: d = 3*6+2 = 20. d <= 20 holds exactly."""
        self.load("param_chain.tl", params={"seed": 6})
        self.assert_property_pass("d_bound", "d <= 20")

    def test_seed_one_over_boundary_fail(self):
        """seed=7: d = 3*7+2 = 23 > 20. d <= 20 violated."""
        self.load("param_chain.tl", params={"seed": 7})
        self.assert_property_fail("d_bound", "d <= 20")

    def test_seed_zero_pass(self):
        """seed=0: a=0, b=1, c=1, d=2. d <= 20 holds."""
        self.load("param_chain.tl", params={"seed": 0})
        self.assert_property_pass("d_bound", "d <= 20")

    def test_neg_seed_d_nonneg_fail(self):
        """seed=-5: a=-5, b=-4, c=-9, d=-13. d >= 0 violated."""
        self.load("param_chain.tl", params={"seed": -5})
        self.assert_property_fail("d_nonneg", "d >= 0")

    def test_pos_seed_all_nonneg_pass(self):
        """seed=3: a=3, b=4, c=7, d=11. All intermediate values >= 0."""
        self.load("param_chain.tl", params={"seed": 3})
        self.assert_property_pass("all_nonneg", "And(a >= 0, b >= 0, c >= 0, d >= 0)")

    def test_neg_seed_intermediate_chain_fail(self):
        """seed=-1: a=-1, b=0, c=-1, d=-1. a >= 0 violated."""
        self.load("param_chain.tl", params={"seed": -1})
        self.assert_property_fail("all_nonneg", "And(a >= 0, b >= 0, c >= 0, d >= 0)")


if __name__ == "__main__":
    unittest.main()
