# CHC Verification Correctness Tests

This directory contains the correctness regression suite for CHC verification.
The suite checks that verification outcomes (`PASSED`, `FAILED`, `UNKNOWN`) match
expected semantics across verifier modes, scopes, and property styles.

## What This Suite Validates

- Soundness of invariant checking across `default`, `specific`, and `universal` modes.
- Correct handling of `property_scope` variants (`all`, `terminating`, `at_pc`, `upto_pc`).
- Heading-grid behavior and hint-sensitive flows.
- API-level validation errors (bad modes, bad hints, bad scopes, bad property syntax).
- Semantic helper-property transpilation (`CHC_Verification_semantic`) correctness.

## Layout

```text
correctness_tests/
  README.md
  helpers.py
  test_default.py
  test_specific.py
  test_universal.py
  test_semantics.py
  programs/
```

## File Responsibilities

- `helpers.py`: shared harness (`ChironTestCase`), API adapters, and reusable assertions.
- `test_default.py`: correctness regressions for `default` mode.
- `test_specific.py`: correctness regressions for `specific` mode (parameterized initialization).
- `test_universal.py`: correctness regressions for `universal` mode, including API validation and scope checks.
- `test_semantics.py`: semantic helper transpilation tests plus semantic API integration tests.

## Current Test Inventory

- Total correctness tests: `358`
- `test_default.py`: `46`
- `test_specific.py`: `70`
- `test_universal.py`: `112`
- `test_semantics.py`: `130`

## Assertion Semantics Used by the Harness

`helpers.py` wraps API calls and converts expectations into clear test assertions:

- `assert_property_pass(...)`: expects verifier status `PASSED` and heading-grid `PASSED`.
- `assert_property_fail(...)`: expects verifier status `FAILED` and heading-grid `PASSED`.
- `assert_property_unknown(...)`: expects verifier status `UNKNOWN` and heading-grid `PASSED`.
- `assert_semantic_property_*`: same expectations via semantic-wrapper API.
- `assert_heading_grid_safe/unsafe/unknown`: heading-grid-only checks.

By default, raw solver stdout is suppressed in helper calls to keep test output clean.

## Fixture Programs (`programs/`)

Current fixture count: `64` `.tl` programs.

Grouped by role:

- Baseline/default-mode arithmetic, control-flow, geometric, and loop fixtures:
  - `assign_algebra.tl`, `assign_basic.tl`, `branchy_non_grid.tl`, `conditional.tl`, `flower_nested_pen.tl`, `forward_square.tl`, `goto_accum.tl`, `goto_computed.tl`, `loop_accum.tl`, `loop_adv.tl`, `loop_basic.tl`, `loop_cond.tl`, `loop_nested.tl`, `loop_xy_dep.tl`, `maze_counter.tl`
- Specific-mode parameterized behavior fixtures:
  - `param_accumulate.tl`, `param_chain.tl`, `param_cond.tl`, `param_countdown.tl`, `param_goto.tl`, `param_loop.tl`, `param_loop_move.tl`, `param_nested_cond.tl`, `param_pen.tl`, `param_pen_cond.tl`, `param_scale.tl`, `read_before_write.tl`, `two_params.tl`
- Pen-state, heading, and geometry-focused fixtures:
  - `pen_only.tl`, `pen_toggle.tl`, `pen_with_var.tl`, `spiral_grid_goto.tl`, `square_goto.tl`, `triangle_nested_pen.tl`, `turns_15.tl`, `turns_only.tl`
- Universal-mode and scope-sensitive invariance fixtures:
  - `u_abs_diff_branching.tl`, `u_branch_always_mul_15.tl`, `u_branch_always_mul_15_adv.tl`, `u_branch_merge_affine.tl`, `u_branch_pen.tl`, `u_branch_pen_adv.tl`, `u_clamp_to_zero.tl`, `u_euclid_avg.tl`, `u_fixed_left.tl`, `u_fixed_target.tl`, `u_fixed_target_user.tl`, `u_heading_non_grid.tl`, `u_init_core.tl`, `u_loop_diagonal.tl`, `u_loop_pen.tl`, `u_mul_15_heading_on_grid.tl`, `u_net_heading_preserved.tl`, `u_net_zero_turn.tl`, `u_normalize_x.tl`, `u_on_spot_turn.tl`, `u_pen_no_touch.tl`, `u_pen_up.tl`, `u_product_zero.tl`, `u_same_postcondition.tl`, `u_swap_with_temp.tl`, `u_swap_without_tmp.tl`, `u_two_step_affine.tl`, `u_xcor_fixed.tl`

## Running the Suite

Prerequisite environment:

```bash
cd Chiron-Framework/ChironCore
source .venv/bin/activate
```

Run all correctness tests from repository root:

```bash
pytest CHC-Verification/correctness_tests -q
```

Run from this directory:

```bash
cd CHC-Verification/correctness_tests
pytest -q
```

Useful variants:

```bash
pytest -v
pytest --collect-only -q
pytest test_default.py -q
pytest test_specific.py::TestSpecificArithmetic -q
pytest test_universal.py::TestUniversalAPI::test_invalid_mode_error -q
pytest -k heading -q
```

Exit behavior:

- `0`: all tests passed (or skipped).
- non-zero: one or more failures/errors.

## Typical Workflow for Adding New Correctness Tests

- Add or reuse a `.tl` fixture in `programs/`.
- Add test cases in the mode-appropriate file (`test_default.py`, `test_specific.py`, `test_universal.py`, or `test_semantics.py`).
- Prefer harness helpers from `helpers.py` for consistent expectations and reporting.
- Run a narrow selection first (`pytest <file_or_test> -q`), then run full suite.