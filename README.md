# Chiron IR Verification Using Constrained Horn Clauses
This repository contains the implementation of a verifier for Chiron IR using Constrained Horn Clauses (CHCs). The verifier is designed to check the safety properties of programs represented in Chiron IR by translating them into CHCs and using the Z3 SMT solver to verify their correctness.

## Team Members
| Name | Roll Number | GitHub Username |
|------|-------------|-----------------|
| Aditi Khandelia | 220061 | [AditiKhandelia](https://github.com/AditiKhandelia) |
| Arush Upadhyaya | 220213 | [A-Rush-R](https://github.com/A-Rush-R)
| Kushagra Srivastava | 220573 | [whizdor](https://github.com/whizdor)

## Project Overview
The project implements a safety verifier for Chiron Turtle programs by translating Chiron IR into Constrained Horn Clauses (CHCs) and solving them with Z3 SPACER.

### What this verifier can do
- Check whether user-provided properties are invariants over all reachable program states.
- Report `PASSED`, `FAILED`, or `UNKNOWN` for each property.
- Produce a counterexample model when a property fails.
- Work with turtle state (`xcor`, `ycor`, `heading`, `pendown`), user variables, and loop counters from `repeat`.
- Support four initialization modes:

| Mode | What it verifies |
|---|---|
| `default` | Safety from a fixed concrete start state (all numeric values initialized to `0`, `pendown=False`) |
| `universal` | Safety for all initial values of turtle coordinates/heading and user variables |
| `specific` | Safety for a user-provided concrete initial variable assignment |

### How verification is done
1. Parse `.tl` source into linear Chiron IR (instruction + jump-offset form).
2. Extract symbols: user variables and loop counters.
3. Build mode-dependent invariant relation `Inv(...)` and state tuples in Z3.
4. Add initial facts/rules based on selected mode.
5. Translate each IR command into CHC transition rules (`Inv(s) -> Inv(s')`).
6. For each property `P`, query reachability of violating states: `Exists(vars, Inv(state) and Not(P))`.
7. Interpret solver result:
   - `sat` => property fails (counterexample exists)
   - `unsat` => property is proved invariant
   - otherwise => unknown


## Project Structure 
- `ChironFramework/`: Contains the implementation of the Chiron IR and the translation to CHCs.
    - `ChironCore/CHC_Verification/`: Contains the code for the CHC verification process, including variable name detection, Z3 fixed point generation, rule translation, and safety property checking.
- `README.md`: This file, providing an overview of the project and its structure.

## Pipeline and Code Structure 
1. **Variable Name Detection in Chiron IR**: 
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/variable_name_detection_in_IR.py`
        - Input : A Chiron IR Object.
        - Output : Pretty prints the symbol table and the counter table for the variables in the Chiron IR. Returns the symbol table and counter table.
        - ``getParseTree`` function is used to parse the input Turtle file and generate the parse tree.
        - ``astGenPass`` function converts ANTLR parse tree into a flat list of (command, offset) used as linear IR.
        - ``parse_variables_from_ir`` function extracts variable names from the linear IR and populates the symbol table and counter table.
2. **Z3 Fixed Point Function Signature**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/z3_fixed_point.py`
        - Input : A Chiron IR Object.
        - Output : A Z3 Fixed Point object with the appropriate function signatures for the CHC verification. Tuples for state and next_state.
        - ``parse_variables_from_ir`` function is reused to get the symbol table and counter table for the variables in the Chiron IR.
        - ``z3_fixed_point_invariant_generation`` function creates mode-aware function signatures for `default`, `universal`, `specific`.
3. **Create Fixed Point Object and set Initial Conditions**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/init_fixed_point.py`
        - Input : A Chiron IR Object.
        - Output : A Z3 Fixed Point object with the initial conditions set for the CHC verification.
        - ``z3_fixed_point_invariant_generation`` function is used to set the signature for the state and next_state prediactes, as well as the ``Inv`` predicate.
        - ``z3_fixed_point_object_with_start_state_set`` function initializes the Z3 Fixed Point object, registers the invariant relation, and adds mode-specific initial rules for `default`, `universal`, `specific`.
4. **Translate Chiron IR to CHC Rules**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/step_rules.py`
        - Input : A Chiron IR Object, Z3 Fixed Point object, invariant relation, state and next_state tuples, symbol table and counter table.
        - Output : CHC rules corresponding to the semantics of each instruction in the Chiron IR added to the Z3 Fixed Point object.
        - ``cos_sin_bounds_z3`` function defines the constraints for the cosine and sine of the heading variable in the Z3 solver.
        - ``normalize_heading`` function ensures that the heading variable is always within the range of \[0, 360\) degrees.
        - ``chiron_expr_to_z3`` function recursively translates a Chiron expression into a Z3 expression, handling various types of expressions such as binary arithmetic operations, comparisons, and variable references.
        - ``chiron_command_to_z3_rule`` function translates a Chiron command into one or more Z3 rules (for conditional commands) based on the semantics of the command and the structure of the Chiron IR.
        - ``add_chiron_ir_to_fixed_point`` function iterates through the linear IR of the Chiron program, translates each instruction into Z3 rules using the previous functions, and adds those rules to the Z3 Fixed Point object. It also includes print statements to show the rules being added for debugging and verification purposes.
5. **Check Safety Properties**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/safety_properties.py`
        - Input (CLI) : `python safety_properties.py <chiron_program_file> <number_of_properties> <mode> [params_dict_for_specific]`
            - `<mode>` must be one of `default`, `universal`, `specific`.
            - for `specific`, an additional params dictionary is required (example: `'{\":x\": 10, \"y\": 20}'`).
        - Input (interactive) : for each property, user enters
            - property name (string label),
            - property boolean expression over available variables (`xcor`, `ycor`, `heading`, `pendown`, user vars, counters) using `And/Or/Not` and comparisons.
        - Output : For each property, prints `PASSED` / `FAILED` / `UNKNOWN`; on failure prints a counterexample
        - ``check_property`` queries reachability of violating states (`Inv(state) AND NOT(property)`), then classifies result as invariant proved (`unsat`) or violated (`sat`).

## Usage

### Running the Verifier

Run commands from `Chiron-Framework/ChironCore`:

```bash
cd Chiron-Framework/ChironCore
python CHC_Verification/safety_properties.py <path-to-turtle-file> <num-properties> <mode> [params]
```

| Argument | Description |
|---|---|
| `<path-to-turtle-file>` | Path to a Chiron Turtle (`.tl`) source file |
| `<num-properties>` | Number of safety properties to check interactively |
| `<mode>` | One of `default`, `universal`, `specific` |
| `[params]` | Required only for `specific`; dictionary of initial user-variable values |

For `specific` mode, pass a dictionary string as the 4th argument, for example:
```bash
python CHC_Verification/safety_properties.py CHC_Verification/test_files/variable_arithmetic/assignment.tl 1 specific '{"a": 0, ":b": 10}'
```

After startup, the verifier prompts for each property:
1. Property name
2. Property boolean expression

### Available State Variables in Property Expressions

| Variable | Description |
|---|---|
| `xcor` | Turtle's current x-coordinate |
| `ycor` | Turtle's current y-coordinate |
| `heading` | Turtle's current heading in degrees |
| `pendown` | Boolean - whether the pen is down |
| `varname` | Any user variable declared in the program (`:varname` in source appears as `varname`) |
| `__rep_counter_*` | Loop counters introduced for `repeat` constructs |

Supported Z3 operators: `And(...)`, `Or(...)`, `Not(...)`, `>=`, `<=`, `==`, `!=`, `>`, `<`, `+`, `-`, `*`, `/`.

---

### Examples

#### Example 1 - Default mode
```bash
python CHC_Verification/safety_properties.py ../../test_files/forward.tl 2 default
```

#### Example 2 - Universal mode
```bash
python CHC_Verification/safety_properties.py ../../test_files/nested_loops.tl 1 universal
```
#### Example 3 - Specific mode
```bash
python CHC_Verification/safety_properties.py CHC_Verification/test_files/variable_arithmetic/assignment.tl 1 specific '{"a": 0}'
```

```
Enter name for property 1: ycor is zero
Enter the boolean expression for property 'ycor is zero': ycor == 0
```

Expected output: property **FAILED** - the turtle moves forward, so `ycor` is not always 0. A counterexample state is printed.

## Tests

- Usage:
```bash
cd Chiron-Framework/ChironCore/CHC_Verfication/tests
python run_all.py
```

- See the tests [`README.md`](./Chiron-Framework/ChironCore/CHC_Verification/tests/README.md) for the test cases and description
