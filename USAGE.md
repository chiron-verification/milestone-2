# CHC Verification Usage Guide

This document is the canonical place for setup, API usage, examples, hints,
optimization settings, and test-running instructions.

## Setup

Use Python 3.11+ and install dependencies in a virtual environment.

```bash
cd Chiron-Framework/ChironCore
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install antlr4-python3-runtime==4.13.2 networkx numpy z3-solver
```

## Working Directory for API Runs

Activate environment from `Chiron-Framework/ChironCore`, then run verifier code
from `CHC-Verification`:

```bash
cd Chiron-Framework/ChironCore
source .venv/bin/activate
cd ../../CHC-Verification
```

## Python API Reference

Primary entrypoint: `CHC-Verification/safety_properties.py`
(`OptimizationLevel` is defined in
`CHC-Verification/variable_name_detection_in_IR.py`)

```python
CHC_Verification(
    file_name,
    mode,
    user_properties,
    params=None,
    input_ranges=None,
    property_scope="all",
    pc_target=None,
    hints=["check_heading_always_on_grid", "check_termination"],
    timeout_ms=60_000,
    optimization_level=OptimizationLevel.NONE,
)
```

### Parameters

- `file_name`: path to `.tl` program
- `mode`: `default`, `specific`, or `universal`
- `user_properties`: list of objects with fields:
  - `name`: property label
  - `expr`: property expression as string
- `params`: required in `specific` mode, passed as a dictionary string
  (example: `"{':start': 10, ':step': 5}"`)
- `input_ranges`: optional in `universal` mode only; dictionary mapping a variable to:
  - an integer (fixed value),
  - `(lo, hi)` integer bounds, or
  - `None` (unconstrained)
- `property_scope`:
  - `"all"`: evaluate over all reachable states
  - `"terminating"`: evaluate only at terminating states (`pc == terminal_pc`)
  - `"at_pc"`: evaluate only at a specific program counter (`pc == pc_target`)
  - `"upto_pc"`: evaluate only over the prefix region (`0 <= pc <= pc_target`)
- `pc_target`: required for `at_pc` / `upto_pc`; must be a valid integer program counter
- `hints`:
  - `"check_heading_always_on_grid"`: verify heading stays on 15-degree lattice before property checks
  - `"heading_on_grid_always"`: assume heading grid restriction directly
  - `"check_termination"`: accepted compatibility hint (currently no extra behavior)
  - `"always_terminates"`: assume terminating states are reachable (skip reachability check)
- `timeout_ms`: solver timeout in milliseconds
- `optimization_level`:
  - `OptimizationLevel.NONE`: baseline encoding
  - `OptimizationLevel.BASIC`: lightweight static simplifications

### Return Value

`CHC_Verification(...)` returns a `ReturnValue` object with fields:

- `status`: overall `PASSED` / `FAILED` / `UNKNOWN`
- `error`: `ReturnError.SUCCESS` / `ERROR` / `UNKNOWN`
- `expr`: short status message
- `advice`: guidance text
- `heading_grid_safe`: `PASSED` / `FAILED` / `UNKNOWN`
- `build_time`: fixedpoint construction time (seconds)
- `solve_times`: list of per-property solve times (seconds)
- `passing_properties`: list of `[name, invariant]`
- `failing_properties`: list of `[name, counterexample]`
- `unknown_properties`: list of property names with unknown verdict

## Python API Examples

```python
from safety_properties import CHC_Verification
from variable_name_detection_in_IR import OptimizationLevel

class UserProperty:
  def __init__(self, name, expr):
    self.name = name
    self.expr = expr

# Default mode
result = CHC_Verification(
  file_name="correctness_tests/programs/loop_accum.tl",
  mode="default",
  user_properties=[UserProperty("x_nonneg", "x >= 0")],
  optimization_level=OptimizationLevel.BASIC,
)
print(result.status, result.expr)

# Specific mode
result = CHC_Verification(
  file_name="correctness_tests/programs/param_loop.tl",
  mode="specific",
  user_properties=[UserProperty("acc_nonneg", "acc >= 0")],
  params="{':start': 0, ':step': 1}",
  property_scope="all",
)
print(result.status)

# Universal + terminating scope
result = CHC_Verification(
  file_name="correctness_tests/programs/u_clamp_to_zero.tl",
  mode="universal",
  user_properties=[UserProperty("z_nonneg_at_end", "z >= 0")],
  property_scope="terminating",
)
print(result.status)
```

## CLI Reference

This section documents the exact CHC CLI interface implemented in
`Chiron-Framework/ChironCore/chiron.py` (argument definitions + dispatch logic).

### Invocation Shape

From `Chiron-Framework/ChironCore`:

```bash
python3 chiron.py -chc [CHC_FLAGS...] <program.tl>
```

- CHC verification runs only when `-chc` / `--chcVerify` is present.
- `<program.tl>` is positional (`progfl`) and required.

### API-to-CLI Mapping

| Python API field | CLI flag(s) | Type / format in `chiron.py` | Default / behavior |
|---|---|---|---|
| `file_name` | positional `progfl` | path to `.tl` program | required |
| CHC enable | `-chc`, `--chcVerify` | boolean flag | off unless set |
| `mode` | `-chc_mode`, `--chcMode` | one of `default`, `specific`, `universal` | `default` |
| `user_properties` | `-chc_props`, `--chcProperties` | string: semicolon-separated `name:expr` entries | empty string => no properties |
| `params` | `-d`, `--params` | Python dict literal (`ast.literal_eval`) | `{}`; forwarded only in `specific` mode |
| `input_ranges` | no CHC CLI counterpart | not exposed by `chiron.py` | unavailable from CLI |
| `property_scope` | `-chc_scope`, `--chcScope` | one of `all`, `terminating`, `at_pc`, `upto_pc` | `all` |
| `pc_target` | `-chc_pc`, `--chcPc` | integer | `None` |
| `hints` | `-chc_hints`, `--chcHints` | comma-separated string, split into list by `,` | `check_heading_always_on_grid,check_termination` |
| `timeout_ms` | `-chc_timeout`, `--chcTimeout` | integer milliseconds | `60000` |
| `optimization_level` | `-chc_opt`, `--chcOpt` | `NONE` or `BASIC` | `NONE` |

### How to Provide CLI Inputs

- Properties:
  - Format: `-chc_props "name1:expr1;name2:expr2"`
  - Example: `-chc_props "x_nonneg:x >= 0;heading_ok:heading % 15 == 0"`
  - Use unprefixed variable names in expressions (`x`, `y`, `xcor`, `heading`, ...), not `:x`.

- Params (for `specific` mode):
  - Format: `-d "{':var1': value1, ':var2': value2}"`
  - Example: `-d "{':start': 0, ':step': 1}"`
  - Use `-d` together with `-chc_mode specific`.

- Scope and PC target:
  - Set scope with `-chc_scope all|terminating|at_pc|upto_pc`
  - For `at_pc` and `upto_pc`, also provide `-chc_pc <int>`

- Hints:
  - Format: `-chc_hints "hint1,hint2"`
  - Example: `-chc_hints "heading_on_grid_always,always_terminates"`

- Optimization:
  - Format: `-chc_opt NONE|BASIC`

- Timeout:
  - Format: `-chc_timeout <milliseconds>`
  - Example: `-chc_timeout 120000`

- Complete template:
  - `python3 chiron.py -chc -chc_mode <mode> -chc_scope <scope> -chc_props "<name:expr;...>" -chc_hints "<hint1,hint2>" -chc_opt <NONE|BASIC> -chc_timeout <ms> <program.tl>`

### CLI Limits vs Python API

- `input_ranges` is currently Python-only; `chiron.py` does not expose a CHC flag for it.
- `CHC_Verification_semantic(...)` is also Python-only from current CLI path; CLI invokes `CHC_Verification(...)` directly.

### Output Produced by CHC CLI Path

`chiron.py` prints:

- overall `Status`
- `Heading-grid`
- `Build time` (if available)
- passing property names
- failing property names
- unknown property names
- message (`expr`) and advice (`advice`) when present

### Ready-to-Run CHC CLI Recipes

#### 1) Minimal default-mode run (no explicit properties)

```bash
cd Chiron-Framework/ChironCore
python3 chiron.py -chc ../../CHC-Verification/correctness_tests/programs/assign_basic.tl
```

#### 2) Default mode with two properties

```bash
python3 chiron.py -chc \
  -chc_mode default \
  -chc_props "x_nonneg:x >= 0;heading_range:And(heading >= 0, heading < 360)" \
  ../../CHC-Verification/correctness_tests/programs/loop_accum.tl
```

#### 3) Specific mode (CLI `-d` is the params source)

```bash
python3 chiron.py -chc \
  -chc_mode specific \
  -d "{':start': 0, ':step': 1}" \
  -chc_props "acc_nonneg:acc >= 0" \
  ../../CHC-Verification/correctness_tests/programs/param_loop.tl
```

#### 4) Universal mode + terminating scope

```bash
python3 chiron.py -chc \
  -chc_mode universal \
  -chc_scope terminating \
  -chc_props "z_nonneg_end:z >= 0" \
  ../../CHC-Verification/correctness_tests/programs/u_clamp_to_zero.tl
```

#### 5) PC-scoped query (`at_pc`)

```bash
python3 chiron.py -chc \
  -chc_mode universal \
  -chc_scope at_pc \
  -chc_pc 3 \
  -chc_opt NONE \
  -chc_props "branch_point:And(d >= 0, x - y == d)" \
  ../../CHC-Verification/correctness_tests/programs/u_branch_merge_affine.tl
```

#### 6) Faster run with assumptions + BASIC encoding

```bash
python3 chiron.py -chc \
  -chc_mode default \
  -chc_hints "heading_on_grid_always,always_terminates" \
  -chc_opt BASIC \
  -chc_props "heading_ok:heading % 15 == 0" \
  ../../CHC-Verification/correctness_tests/programs/turns_15.tl
```

## Property Expression Language

Property strings can reference:

- turtle state: `xcor`, `ycor`, `heading`, `pendown`
- user variables discovered from program
- loop counters discovered from `repeat`
- boolean combinators: `And(...)`, `Or(...)`, `Not(...)`
- arithmetic/comparison operators supported by Z3 expressions

Examples:

- `"And(xcor >= 0, xcor <= 50)"`
- `"Not(pendown)"`
- `"Or(heading == 0, heading == 90, heading == 180, heading == 270)"`
- `"acc >= 0"`

## Hints

Hints are passed as a list of strings.
Default: `["check_heading_always_on_grid", "check_termination"]`.

### Heading-grid hints

Chiron's exact semantics requires `heading` to remain a multiple of 15 degrees.
If a reachable off-grid heading exists, the verifier reports `UNKNOWN` and skips
property checks under strict exact semantics.

| Hint | Behaviour |
|---|---|
| `check_heading_always_on_grid` | Runs a pre-check for reachable off-grid heading states before property verification. |
| `heading_on_grid_always` | Skips that pre-check and assumes heading is always on the 15-degree grid. |

### Termination hints

Relevant only when `property_scope="terminating"`.

| Hint | Behaviour |
|---|---|
| `check_termination` | Accepted compatibility hint. Current behavior for terminating scope already includes a reachability check unless `always_terminates` is provided. |
| `always_terminates` | Skips terminating-state reachability check and assumes termination is reachable. |

### Combining hints

You can combine one heading-related and one termination-related hint:

```python
hints=["heading_on_grid_always", "always_terminates"]
```

## Optimization Level

Passed as an `OptimizationLevel` enum value.

| Level | Behaviour |
|---|---|
| `OptimizationLevel.NONE` | Baseline encoding; compatible with all scopes, including `at_pc` and `upto_pc`. |
| `OptimizationLevel.BASIC` | Adds static simplifications (including turn-safety and loop summarization) for faster solving on many programs. Not compatible with `property_scope="at_pc"` or `"upto_pc"`. |
