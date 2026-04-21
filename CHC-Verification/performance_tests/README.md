# CHC Verification Performance Tests

This directory contains benchmark-oriented tests for CHC verification.
The suite measures build/solve behavior across modes, hint settings, and
optimization levels while still checking expected verdict outcomes.

## What This Suite Measures

- Build-time and solve-time trends under increasing program complexity.
- Behavior differences between `OptimizationLevel.NONE` and `OptimizationLevel.BASIC`.
- Effect of heading-grid pre-check vs explicit heading-grid assumption.
- Expected outcome stability (`PASSED`/`FAILED`) for benchmark properties.
- Universal/specific/default mode differences under identical benchmark patterns.

## Layout

```text
performance_tests/
  README.md
  helpers.py
  test_default.py
  test_specific.py
  test_universal.py
  pytest.ini
  programs/
  perf_results_*.csv
```

## File Responsibilities

- `helpers.py`: shared timing harness, 4-configuration runner, verdict normalization, and CSV writing.
- `test_default.py`: default-mode benchmark scenarios.
- `test_specific.py`: specific-mode benchmark scenarios.
- `test_universal.py`: universal-mode benchmark scenarios.
- `pytest.ini`: pytest configuration for this directory (includes parallel options).

## Current Test Inventory

- Total performance tests: `128`
- `test_default.py`: `38`
- `test_specific.py`: `52`
- `test_universal.py`: `38`

## Benchmark Programs (`programs/`)

Current benchmark fixture count: `24` `.tl` programs.

Grouped by role:

- Optimization-focused benchmark cases:
  - `opt_found.tl`, `opt_universal_100.tl`
- Default/universal scaling benchmarks:
  - `perf_combo.tl`, `perf_deep_nest_3.tl`, `perf_deep_nest_4.tl`, `perf_many_branches.tl`, `perf_repeat_10.tl`, `perf_repeat_50.tl`, `perf_repeat_100.tl`, `perf_repeat_5000.tl`, `perf_trig_10.tl`, `perf_trig_20.tl`, `perf_turns_20.tl`, `perf_turns_50.tl`, `perf_wide_vars.tl`, `turn_mul_sum.tl`
- Specific-mode parameterized scaling benchmarks:
  - `perf_s_branches.tl`, `perf_s_nest_3.tl`, `perf_s_nest_4.tl`, `perf_s_repeat_50.tl`, `perf_s_repeat_100.tl`, `perf_s_trig_10.tl`, `perf_s_trig_20.tl`, `perf_s_wide.tl`

## How Performance Assertions Work

`helpers.py` runs each property under 4 configurations:

- `NONE` + default hint (`check_heading_always_on_grid`)
- `BASIC` + default hint
- `NONE` + assumed heading hint (`heading_on_grid_always`)
- `BASIC` + assumed heading hint

For each configuration, the harness records:

- raw verdict (`PASSED`, `FAILED`, `UNKNOWN`)
- result status against expected outcome (`PASSED`, `FAILED`, `SKIPPED`)
- build time and solve time

Important behavior:

- `UNKNOWN` verdict is treated as `SKIPPED` for result comparison.
- API errors fail tests.
- Timeouts are converted to `UNKNOWN` and can be skipped rather than hard-failed (depending on assertion path).

## CSV Result Artifacts

Primary result files written by the harness:

- `perf_results_default.csv`
- `perf_results_specific.csv`
- `perf_results_universal.csv`


The CSV columns include file/property ids plus per-configuration verdict/result and timing fields (`build_s_*`, `solve_s_*`).

## Running the Suite

Prerequisite environment:

```bash
cd Chiron-Framework/ChironCore
source .venv/bin/activate
```

Run all performance tests from repository root:

```bash
pytest CHC-Verification/performance_tests -q
```

Run from this directory:

```bash
cd CHC-Verification/performance_tests
pytest -q
```

Useful variants:

```bash
pytest -v
pytest --collect-only -q
pytest test_default.py -q
pytest test_specific.py::TestSpecificLoopCountScaling -q
pytest test_universal.py::TestUniversalLoopCountScaling::test_loop10_all_x_nonneg_fail -q
```

Parallelism note:

- `pytest.ini` uses `-n auto`; install `pytest-xdist` if needed.

## Typical Workflow for New Benchmarks

- Add new `.tl` benchmark in `programs/`.
- Add property checks in the relevant mode test file.
- Use `assert_and_time(...)` to enforce expected outcome and capture timing (runs all 4 configurations).
