# Chiron IR Verification Using Constrained Horn Clauses

This repository contains a CHC-based safety verifier for Chiron turtle-language programs.
The verifier translates Chiron IR into Horn clauses and uses Z3 Fixedpoint (SPACER)
to prove or refute safety properties.

## Team Members

| Name | Roll Number | GitHub Username |
|---|---|---|
| Aditi Khandelia | 220061 | [AditiKhandelia](https://github.com/AditiKhandelia) |
| Arush Upadhyaya | 220213 | [A-Rush-R](https://github.com/A-Rush-R) |
| Kushagra Srivastava | 220573 | [whizdor](https://github.com/whizdor) |

## Milestone-2 Snapshot

Compared to the milestone-1 submission (`0f99ade6d4aa2516f9e47e013ad06d29e8b8a2f7`),
the verifier is now API-first and supports richer configuration:

- Programmatic API via `CHC_Verification(...)`
- Structured return object with status, advice, build/solve times, and per-property outcomes
- Modes: `default`, `specific`, `universal`
- Property scopes: `all` reachable states or `terminating` states only
- Heading-grid checks/hints for enforcing or assuming 15-degree turn alignment
- Explicit timeout control per verification call

Current submission commit (milestone-2):
`c88682f82df5d5f287c4460d8bb6d30d7d2c8a82`

## Repository Structure

- `CHC-Verification/`
  - `variable_name_detection_in_IR.py`: extracts user variables and loop counters from linear IR
  - `z3_fixed_point.py`: builds mode-dependent invariant signature/state vectors
  - `init_fixed_point.py`: initializes fixedpoint engine and mode-specific base rules
  - `step_rules.py`: translates Chiron IR instructions to CHC transition rules
  - `heading_grid.py`: heading lattice helper logic
  - `safety_properties.py`: main API (`CHC_Verification`) and property checking
- `Chiron-Framework/ChironCore/`
  - Chiron parser/IR infrastructure consumed by the verifier (`irhandler`, AST builder, etc.)

## Verification Model

The state tracked by the invariant relation includes:

- program counter (`pc`)
- turtle coordinates (`xcor`, `ycor`)
- turtle heading (`heading`)
- pen state (`pendown`)
- user variables
- internal repeat counters

A property `P` is checked by querying reachability of violating states:
`Exists(vars, Inv(state) and Not(P))`.

- `sat` => property fails (`FAILED`)
- `unsat` => property proved invariant (`PASSED`)
- otherwise => solver could not conclude (`UNKNOWN`)

## API Reference

Primary entrypoint: `CHC-Verification/safety_properties.py`
(`OptimizationLevel` is defined in `CHC-Verification/variable_name_detection_in_IR.py`)

```python
CHC_Verification(
    file_name,
    mode,
    user_properties,
    params=None,
    property_scope="all",
    hints=["check_heading_always_on_grid"],
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
  (example: `"{'start': 10, 'step': 5}"`)
- `property_scope`:
  - `"all"`: evaluate over all reachable states
  - `"terminating"`: evaluate only at terminating states (`pc == terminal_pc`)
- `hints`:
  - `"check_heading_always_on_grid"`: verify heading stays on 15-degree lattice before property checks
  - `"heading_on_grid_always"`: assume heading grid restriction directly
- `timeout_ms`: solver timeout in milliseconds
- `optimization_level`: optimization mode for CHC generation.
  - `OptimizationLevel.NONE`: baseline encoding
  - `OptimizationLevel.BASIC`: enable lightweight static simplifications

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

## Setup

Use Python 3.11+ and install dependencies in a virtual environment.

```bash
cd Chiron-Framework/ChironCore
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install antlr4-python3-runtime==4.13.2 networkx numpy z3-solver
```

Environment activation should be done from `Chiron-Framework/ChironCore`

## Running Instructions (API Usage)

1. Activate environment from `Chiron-Framework/ChironCore`.
2. Switch to `CHC-Verification` to run verification commands.

```bash
cd Chiron-Framework/ChironCore
source .venv/bin/activate
cd ../../CHC-Verification
```

### Example

```python
from safety_properties import CHC_Verification
from variable_name_detection_in_IR import OptimizationLevel

class UserProperty:
  def __init__(self, name, expr):
    self.name = name
    self.expr = expr

result = CHC_Verification(
  file_name="correctness_tests/programs/loop_accum.tl",
  mode="default",
  user_properties=[UserProperty("x_nonneg", "x >= 0")],
  optimization_level=OptimizationLevel.BASIC,
)
print(result.status, result.expr)
```

### Short Specific Example

```python
result = CHC_Verification(
  file_name="correctness_tests/programs/param_loop.tl",
  mode="specific",
  user_properties=[UserProperty("acc_nonneg", "acc >= 0")],
  params="{':start': 0, ':step': 1}",
  property_scope="all",
)
print(result.status)
```

### Short Universal + Terminating Example

```python
result = CHC_Verification(
  file_name="correctness_tests/programs/u_clamp_to_zero.tl",
  mode="universal",
  user_properties=[UserProperty("z_nonneg_at_end", "z >= 0")],
  property_scope="terminating",
)
print(result.status)
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

## Notes and Current Limitations

- A program that might violate the condition `heading % 15 == 0` at any point during execution may throw `UNKNOWN`
- Some complex cases can return `UNKNOWN` under time limits, or may simply timeout
- If heading-grid safety fails under strict semantics, the API returns `UNKNOWN` and skips subsequent property checks

## Test Information

Test suite details are documented separately in:
`CHC-Verification/correctness_tests/README.md`

Quick commands:

```bash
# Correctness suite
cd CHC-Verification/correctness_tests
python -m pytest -q

# Performance suite
cd CHC-Verification/performance_tests
python -m pytest -q
```

Note: `CHC-Verification/performance_tests/pytest.ini` uses `-n auto`, so install
`pytest-xdist` if parallel execution is unavailable by default.