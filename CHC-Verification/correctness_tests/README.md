# CHC Verification Correctness Tests

This directory contains the correctness regression suite for the CHC verification API.
Tests validate that safety properties are classified as `PASSED`, `FAILED`, or `UNKNOWN`
as expected across the three verification modes.

## Framework and Layout

The suite is written with `unittest.TestCase` classes and executed with `pytest`.

```text
correctness_tests/
  README.md
  helpers.py            # common harness + API wrapper helpers
  test_default.py       # default-mode tests
  test_specific.py      # specific-mode tests
  test_universal.py     # universal-mode tests
  programs/             # .tl fixtures
```

## Mode Coverage and Test Categories

Current collected test counts:

- `default`: 46 tests
- `specific`: 70 tests
- `universal`: 90 tests

Category coverage by mode:

- `default` (`test_default.py`): arithmetic, geometric, pen-state, directional,
  heading-grid, trig-sensitive, and advanced nested-loop scenarios.
- `specific` (`test_specific.py`): parameterized initialization semantics,
  arithmetic/geometric/pen/directional checks, and multi-parameter/compound workflows.
- `universal` (`test_universal.py`): API validation, unconstrained-initial-state
  reasoning, arithmetic/geometric/pen/directional properties, heading-grid behavior,
  and terminating-scope checks.

Property expectation styles used throughout:

- `assert_property_pass(...)`: expected solver result is `unsat` for counterexample query.
- `assert_property_fail(...)`: expected solver result is `sat` for counterexample query.

## Running Instructions (pytest)

Prerequisite: use the project virtual environment (or any environment with
`pytest`, `z3-solver`, and project dependencies installed).

```bash
cd Chiron-Framework/ChironCore
source .venv/bin/activate
```

Run from repository root:

```bash
pytest CHC-Verification/correctness_tests -q
```

Or run from this directory:

```bash
pytest -q
```

Useful variants:

```bash
# Verbose
pytest -v

# Collect-only (sanity check discovery)
pytest --collect-only -q

# Run one mode file
pytest test_default.py -q

# Run one class
pytest test_specific.py::TestSpecificArithmetic -q

# Run one test
pytest test_universal.py::TestUniversalAPI::test_invalid_mode_error -q

# Keyword filter
pytest -k heading -q
```

Exit behavior:

- `0`: all tests passed (or were skipped)
- non-zero: one or more failures/errors