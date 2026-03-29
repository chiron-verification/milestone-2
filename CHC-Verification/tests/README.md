---
noteId: "101ea8f01adf11f1a84401e3aa707330"
tags: []

---

# CHC Verification Test Suite

This directory contains the automated test suite for the Chiron CHC (Constrained Horn Clause)
verification pipeline. The suite verifies that safety properties over Chiron turtle-language
programs are correctly classified as PASSED or FAILED by the Z3 SPACER engine or reported to be UNKNOWN
---

## Directory Layout

```
tests/
  README.md           -- this file
  helpers.py          -- shared base class and utility functions
  run_all.py          -- top-level test runner
  test_default.py     -- tests for "default" mode
  test_specific.py    -- tests for "specific" mode
  test_universal.py   -- tests for "universal" mode
  programs/           -- .tl Chiron source programs used as fixtures
```

---
## Infrastructure
<!-- 

### helpers.py

`helpers.py` provides everything a test module needs; all test files import it with a single
`from helpers import *`.

**`build_fp(name, mode, params=None)`**

Parses the named `.tl` file from the `programs/` directory, runs the AST generation pass,
and calls `add_step_rules_to_fixed_point` to produce the complete CHC system. A Z3 timeout
hint of 15 000 ms is applied to the resulting fixedpoint object. Returns the tuple
`(fp, Inv, state, next_state, symbol_table, counter_table)`.

**`make_context(state, st, ct)`**

Builds a plain Python dict mapping human-readable names to Z3 variables. The dict always
contains `xcor`, `ycor`, `heading`, `pendown`, and the Z3 logical connectives `And`, `Or`,
`Not`, `Implies`. It is then extended with every user variable from the symbol table and
every loop counter from the counter table, so that test code can write `self.v("x")` instead
of indexing into raw tuples.

**`ChironTestCase`**

A `unittest.TestCase` subclass that all test classes inherit from. It provides:

- `load(tl_file, params=None)` -- calls `build_fp` and `make_context`, storing the results
  as instance attributes. stdout is suppressed during loading so that pipeline log messages
  do not clutter test output.
- `v(name)` -- short accessor that looks up a Z3 variable by name from the context dict.
- `assert_pass(name, expr)` -- wraps `expr` in a `Property`, runs `check_property`, and
  calls `self.assertEqual(..., "PASSED")`. If the solver returns UNKNOWN the test is
  automatically skipped rather than failed.
- `assert_fail(name, expr)` -- same as above but asserts `"FAILED"`.

Every test class sets the class attribute `MODE` to control which initialisation rule is
added to the fixedpoint (see [Initialisation Modes](#initialisation-modes)). -->

### run_all.py

A minimal script that uses `unittest.TestLoader.discover` to find all `test_*.py` files in
this directory and runs them.

---

## Program Library

The `programs/` directory contains the `.tl` source files used as test fixtures. They are
small, self-contained Chiron programs that exercise specific language features:

| File | Features exercised |
|---|---|
| `assign_basic.tl` | Sequential variable assignments |
| `assign_algebra.tl` | Multi-variable arithmetic, multiplication |
| `conditional.tl` | If/else branching |
| `loop_basic.tl` | Counted loop, single accumulator |
| `loop_accum.tl` | Loop with accumulating variable |
| `loop_cond.tl` | Loop with conditional body |
| `goto_computed.tl` | `goto` movement with computed coordinates |
| `square_goto.tl` | `goto`-based square traversal |
| `forward_square.tl` | `forward`/`right` square (trig-dependent) |
| `turns_only.tl` | Heading changes via `right`/`left` |
| `pen_only.tl` | Pen commands only |
| `pen_with_var.tl` | Pen command inside a variable-dependent branch |
| `pen_toggle.tl` | Alternating pendown/penup |
| `param_goto.tl` | `goto` with parameterised coordinates |
| `param_loop.tl` | Loop with parameterised start value |
| `param_cond.tl` | Conditional with parameterised initial value |
| `param_scale.tl` | Assignment scaled by a parameter |
| `param_pen.tl` | Pen command gated by a parameter |
| `read_before_write.tl` | Variable read before first write |

---

## Property Categories

Across all four modes the suite tests three broad categories of safety property:

**Arithmetic properties** -- linear inequalities and equalities over user-defined variables
(e.g., `x >= 0`, `z <= 100`). These exercise the arithmetic reasoning capabilities of
SPACER and cover assignments, loops, and conditionals.

**Geometric properties** -- constraints over the turtle's position (`xcor`, `ycor`) after
movement commands. These exercise the translation of `goto` and `forward` instructions into
CHC rules and the ability of SPACER to infer spatial invariants.

**Pen/directional properties** -- constraints over the boolean `pendown` flag and the
`heading` real variable. Pen properties are straightforward; heading properties involving the
`normalize_heading` approximation (a chain of nested Z3 `If`-expressions) are currently
skipped due to a known SPACER scalability issue.

Properties are further classified by expected verdict:

- **assert_pass** -- the property is a true invariant; SPACER must return `unsat` when
  asked whether a counterexample exists.
- **assert_fail** -- the property can be violated; SPACER must return `sat` and produce a
  counterexample.

---

## Running the Tests

Run everything from this directory:

```bash
python run_all.py
```

Verbose output (one line per test):

```bash
python run_all.py -v
```

Run a single module:

```bash
python -m unittest test_default
```

Run a single test class:

```bash
python -m unittest test_default.TestDefaultArithmetic
```

Run a single test method:

```bash
python -m unittest test_default.TestDefaultArithmetic.test_arith_assign_z_nonneg_pass
```

The runner exits with code 0 if all tests pass (or are skipped) and code 1 if any test
fails or errors.

---
<!-- 
## Known Limitations

**SPACER and normalize_heading** -- The heading normalisation function is encoded as a
chain of 20 nested Z3 `If`-expressions (10 for wrapping above 360, 10 for wrapping below
0). SPACER cannot efficiently synthesise an invariant over this structure, so all tests that
depend on heading after a `right` or `left` command are decorated with
`@unittest.skip(...)`. This is a solver scalability issue, not a correctness defect in the
CHC encoding.

**SPACER timeout** -- A timeout hint of 15 000 ms is passed to the fixedpoint object. Z3
does not always respect this hint exactly. If SPACER returns UNKNOWN for a property the test
is skipped (not failed), with a descriptive message indicating which property was
indeterminate.

**Nonlinear arithmetic** -- Properties involving products of two unconstrained variables
(e.g., `c = a * b` where both `a` and `b` are ghost parameters) may return UNKNOWN because
SPACER's default strategy does not handle nonlinear arithmetic well. Affected tests are
written with `assert_fail` and will be automatically skipped if UNKNOWN is returned. -->