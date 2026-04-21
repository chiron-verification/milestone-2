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

Current submission commit (milestone-3):
`<TBD>`

## Features

- **API-first verification pipeline**
  - Main entrypoint `CHC_Verification(...)` builds CHCs from Chiron IR and checks properties with Z3 Fixedpoint (SPACER).
  - Verifies multiple properties in one call and reports per-property outcomes.

- **Rich state modeling in invariant relation**
  - Tracks `pc`, `xcor`, `ycor`, `heading`, `pendown`, discovered user variables, and internal repeat counters.
  - Uses exact transition rules over this state to model program execution.

- **Three execution modes with distinct initial-state semantics**
  - `default`: concrete initial state (`pc=0`, `(xcor,ycor)=(0,0)`, `heading=0`, `pendown=False`, vars/counters zero).
  - `specific`: concrete initial state from provided parameter map (missing params default to `0`).
  - `universal`: quantified initial state with unconstrained position/vars, heading constrained to 15-degree grid, `pendown=True`, loop counters initialized to `0`, and optional `input_ranges` bounds for selected variables.

- **Property scoping beyond full-program invariants**
  - `all`: check over all reachable states.
  - `terminating`: check only when `pc == terminal_pc`, with reachability guard checks.
  - `at_pc`: check exactly at a chosen `pc_target` (with reachability validation).
  - `upto_pc`: check on the prefix region `0 <= pc <= pc_target`.

- **Heading-grid soundness gate**
  - Builds a dedicated `BadHeading` relation to detect states where heading leaves the 15-degree lattice.
  - If heading-grid safety fails (or is unknown), property checks are skipped and status is reported as `UNKNOWN` under strict semantics.
  - Supports hints to either check or assume grid-safety (`check_heading_always_on_grid`, `heading_on_grid_always`).

- **Instruction coverage in CHC translation**
  - Handles assignment, branching (`ConditionCommand`), assertions, movement (`forward/backward/left/right`), pen commands, `goto`, `pause`, and `noop`.
  - Models heading updates modulo `360`.
  - Uses exact precomputed trig constants for movement under grid-aligned headings.

- **Optimization support (`OptimizationLevel`)**
  - `NONE`: baseline precise encoding.
  - `BASIC`: static turn-safety analysis (skip redundant heading-bad checks when provably safe) and repeat-loop summarization.
  - Loop summarization supports nested loops and structured if/else in loop bodies, with safeguards (iteration cap and shape checks).

- **Semantic helper properties**
  - `CHC_Verification_semantic(...)` transpiles helper-style properties into raw solver expressions.
  - Includes helpers for arithmetic, ranges, pen state, heading predicates, and guarded relational properties (e.g., `is_nonnegative`, `position_in_box`, `heading_cardinal`, `relation_guarded`).

- **Robust API ergonomics**
  - Strict validation for modes, scopes, hints, `pc_target`, optimization compatibility, `input_ranges`, and property parsing.
  - Structured return object includes:
    - overall status/error/advice,
    - heading-grid status,
    - fixedpoint build time,
    - per-property solve times,
    - passing invariants and failing counterexamples.

- **Regression and performance infrastructure**
  - Correctness suites cover `default`, `specific`, `universal`, and semantic-helper pathways.
  - Performance harness benchmarks `NONE/BASIC` and hint/no-hint variants, and records timings/results to CSV.

## Repository Structure and File Responsibilities

### Top-Level Files and Directories

- `USAGE.md`: canonical setup + API usage instructions.
- `CHC-Verification/`: verifier implementation, correctness tests, performance tests, and benchmark outputs.
- `Chiron-Framework/`: upstream Chiron parser/IR framework consumed by this verifier.
- `milestone-1-report/`, `milestone-2-report/`, `milestone-3-report/`: report sources and generated milestone PDFs.
- `literature-review/`: background notes and references for related work.
- `presentation_suite/`: demo/presentation scripts.
- `project_poster/`: poster sources and assets.

### `CHC-Verification/` Core Verifier Files

- `safety_properties.py`: primary API (`CHC_Verification`), input validation, solver orchestration, property querying, and structured return construction.
- `semantic_properties.py`: helper-property transpiler and semantic wrapper API (`CHC_Verification_semantic`).
- `step_rules.py`: IR instruction-to-CHC transition encoding, `BadHeading` rule generation, and optimization-aware rule emission.
- `optimization_helpers.py`: static analyses and helpers for turn safety and repeat-loop summarization logic.
- `init_fixed_point.py`: fixedpoint object initialization and mode-specific initial-state rule construction.
- `z3_fixed_point.py`: invariant signature/state tuple generation and symbol/counter table integration.
- `variable_name_detection_in_IR.py`: discovers user variables + repeat counters from IR and defines `OptimizationLevel`.
- `heading_grid.py`: heading lattice predicate helper (`heading_on_grid`).

### `CHC-Verification/correctness_tests/`

- Detailed correctness test-file responsibilities and fixture grouping are documented in `CHC-Verification/correctness_tests/README.md`.

### `CHC-Verification/performance_tests/`

- Detailed performance test-file responsibilities, benchmark fixtures, and result artifacts are documented in `CHC-Verification/performance_tests/README.md`.

### Chiron Framework Files Directly Consumed by Verifier

- `Chiron-Framework/ChironCore/irhandler.py`: parser frontend used to produce parse trees from `.tl` programs.
- `Chiron-Framework/ChironCore/ChironAST/builder.py`: AST/IR generation pass consumed before CHC encoding.
- `Chiron-Framework/ChironCore/ChironAST/ChironAST.py`: AST node definitions referenced by the encoder and analyses.

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

## Usage

All setup, API usage, examples, hints/optimization behavior, property-expression
syntax, and test-running instructions are documented in [USAGE.md](USAGE.md).
