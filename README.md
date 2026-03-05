# Chiron IR Verification Using Constrained Horn Clauses
This repository contains the implementation of a verifier for Chiron IR using Constrained Horn Clauses (CHCs). The verifier is designed to check the safety properties of programs represented in Chiron IR by translating them into CHCs and using the Z3 SMT solver to verify their correctness.

## Team Members
| Name | Roll Number | GitHub Username |
|------|-------------|-----------------|
| Aditi Khandelia | 220061 | [AditiKhandelia](https://github.com/AditiKhandelia) |
| Arush Upadhyaya | 220213 | [A-Rush-R](https://github.com/A-Rush-R)
| Kushagra Srivastava | 220573 | [hizdor](https://github.com/whizdor)

## Project Structure 
- `ChironFramework/`: Contains the implementation of the Chiron IR and the translation to CHCs.
- `test_files/`: Contains sample Turtle files used for testing the verifier.
- `README.md`: This file, providing an overview of the project and its structure.

## Steps 
- [x] **Variable Name Detection in Chiron IR**: 
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/variable_name_detection_in_IR.py`
        - Input : A Chiron IR Object.
        - Output : Pretty prints the symbol table and the counter table for the variables in the Chiron IR. Returns the symbol table and counter table.
        - ``getParseTree`` function is used to parse the input Turtle file and generate the parse tree.
        - ``astGenPass`` function converts ANTLR parse tree into a flat list of (command, offset) used as linear IR.
        - ``parse_variables_from_ir`` function extracts variable names from the linear IR and populates the symbol table and counter table.
    - Test file : `test_files/check_symbol_table_and_counter_table`
- [x] **Z3 Fixed Point Function Signature**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/z3_fixed_point.py`
        - Input : A Chiron IR Object.
        - Output : A Z3 Fixed Point object with the appropriate function signatures for the CHC verification. Tuples for state and next_state.
        - ``parse_variables_from_ir`` function is reused to get the symbol table and counter table for the variables in the Chiron IR.
        - ``z3_fixed_point_invariant_generation`` function creates a Z3 Fixed Point object and defines the function signatures for the state and next_state predicates based on the variables in the symbol table and counter table.
- [x] **Create Fixed Point Object and set Initial Conditions**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/init_fixed_point.py`
        - Input : A Chiron IR Object.
        - Output : A Z3 Fixed Point object with the initial conditions set for the CHC verification.
        - ``z3_fixed_point_invariant_generation`` function is used to set the signature for the state and next_state prediactes, as well as the ``Inv`` predicate.
        - ``z3_fixed_point_object_with_start_state_set`` function initializes the Z3 Fixed Point object, registers the invariant relation, and adds the initial state fact to the fixed point object. It also includes sanity checks to verify that the initial state satisfies the invariant relation and that a non-start state does not satisfy the invariant relation.
- [x] **Translate Chiron IR to CHC Rules**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/step_rules.py`
        - Input : A Chiron IR Object, Z3 Fixed Point object, invariant relation, state and next_state tuples, symbol table and counter table.
        - Output : CHC rules corresponding to the semantics of each instruction in the Chiron IR added to the Z3 Fixed Point object.
        - ``cos_sin_bounds_z3`` function defines the constraints for the cosine and sine of the heading variable in the Z3 solver.
        - ``normalize_heading`` function ensures that the heading variable is always within the range of \[0, 360\) degrees.
        - ``chiron_expr_to_z3`` function recursively translates a Chiron expression into a Z3 expression, handling various types of expressions such as binary arithmetic operations, comparisons, and variable references.
        - ``chiron_command_to_z3_rule`` function translates a Chiron command into one or more Z3 rules (for conditional commands) based on the semantics of the command and the structure of the Chiron IR.
        - ``add_chiron_ir_to_fixed_point`` function iterates through the linear IR of the Chiron program, translates each instruction into Z3 rules using the previous functions, and adds those rules to the Z3 Fixed Point object. It also includes print statements to show the rules being added for debugging and verification purposes.
- [x] **Check Safety Properties**:
    - Code File : `Chiron-Framework/ChironCore/CHC_Verification/safety_properties.py`
        - Input : A Chiron Turtle (.tl) file, the properties from the input console.
        - Output : Checks the specified safety properties against the CHC rules in the Z3 Fixed Point object and prints whether each property is satisfied or not, along with any counterexamples if a property fails.
        - ``check_property`` function takes a Z3 Fixed Point object, the invariant relation, state and next_state tuples, symbol table, counter table, and a property to check. It queries the fixed point object to determine if there exists a state that satisfies the invariant but violates the property. If such a state exists, it marks the property as failed and stores the counterexample.

## Usage

### Running the Verifier

All commands must be run from the `CHC_Verification/` directory:

```bash
cd Chiron-Framework/ChironCore/CHC_Verification
python safety_properties.py <path-to-turtle-file> <num-properties>
```

| Argument | Description |
|---|---|
| `<path-to-turtle-file>` | Path to a Chiron Turtle (`.tl`) source file |
| `<num-properties>` | Number of safety properties to check interactively |

The verifier will then prompt you interactively for each property:
1. A **name** for the property (free text label)
2. A **Z3 boolean expression** using the program's state variables

### Available State Variables in Property Expressions

| Variable | Description |
|---|---|
| `xcor` | Turtle's current x-coordinate |
| `ycor` | Turtle's current y-coordinate |
| `heading` | Turtle's current heading in degrees |
| `pendown` | Boolean — whether the pen is down |
| `:varname` → `varname` | Any user variable declared in the program (colon stripped) |

Supported Z3 operators: `And(...)`, `Or(...)`, `Not(...)`, `>=`, `<=`, `==`, `!=`, `>`, `<`, `+`, `-`, `*`, `/`.

---

### Examples

#### Example 1 — Simple forward movement (`forward.tl`)

Program (`test_files/forward.tl`):
```
pendown
forward 50
forward 100
:d = 30
forward :d
:d = :d + 20
forward :d
```

Run:
```bash
python safety_properties.py ../../../test_files/forward.tl 2
```

Interactive session:
```
Enter name for property 1: ycor is non-negative
Enter the boolean expression for property 'ycor is non-negative': ycor >= 0

Enter name for property 2: d is positive
Enter the boolean expression for property 'd is positive': d >= 0
```

Expected output: both properties **PASSED** — `ycor` only increases via `forward` and `:d` starts at 30.

---

#### Example 2 — Nested loops (`nested_loops.tl`)

Program (`test_files/nested_loops.tl`):
```
:i = 3
:j = 2
repeat 3 [
    repeat 2 [
        forward :i
        right :j
    ]
    :i = :i + 1
]
```

Run:
```bash
python safety_properties.py ../../../test_files/nested_loops.tl 1
```

Interactive session:
```
Enter name for property 1: i stays positive
Enter the boolean expression for property 'i stays positive': i >= 3
```

Expected output: property **PASSED** — `:i` starts at 3 and only increases.

---

#### Example 3 — Conditional branching (`conditional_if_else.tl`)

Program (`test_files/conditional_if_else.tl`):
```
:x = 10
:y = 20
if (:x < :y) [
    forward 50
] else [
    backward 50
]
:z = :x + :y
if (:z > 25) [
    forward :z
] else [
    forward 10
]
```

Run:
```bash
python safety_properties.py ../../../test_files/conditional_if_else.tl 2
```

Interactive session:
```
Enter name for property 1: x equals 10
Enter the boolean expression for property 'x equals 10': x == 10

Enter name for property 2: z is sum of x and y
Enter the boolean expression for property 'z is sum of x and y': z == x + y
```

Expected output: both properties **PASSED**.

---

#### Example 4 — A failing property

Using `forward.tl`, check a property that does not hold:

```bash
python safety_properties.py ../../../test_files/forward.tl 1
```

```
Enter name for property 1: ycor is zero
Enter the boolean expression for property 'ycor is zero': ycor == 0
```

Expected output: property **FAILED** — the turtle moves forward, so `ycor` is not always 0. A counterexample state is printed.

## Tests
- Usage:
```bash
Run:  pytest test_runner.py -v
```

- See `Chiron-Framework/ChironCore/CHC_Verification/test_runner.py` for the test cases and description
