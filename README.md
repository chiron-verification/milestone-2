# Chiron IR Verification Using Constrained Horn Clauses
This repository contains the implementation of a verifier for Chiron IR using Constrained Horn Clauses (CHCs). The verifier is designed to check the safety properties of programs represented in Chiron IR by translating them into CHCs and using the Z3 SMT solver to verify their correctness.

## Team Members
| Name | Roll Number | GitHub Username |
|------|-------------|-----------------|
| Aditi Khandelia | 220061 | [AditiKhandelia](https://github.com/AditiKhandelia) |
| Arush Upadhyaya | 220213 | [A-Rush-R](https://github.com/A-Rush-R)
| Kushagra Srivastava | 220573| [whizdor](https://github.com/whizdor)

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
    



