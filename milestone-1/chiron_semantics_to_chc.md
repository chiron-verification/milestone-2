# Chiron Commands to CHC Translation

## State Representation
```
State = (PC, Vars, TurtleState)
  - PC: Int (program counter)
  - Vars: variable environment (user variables without : prefix)
  - TurtleState: (x_pos: Real, y_pos: Real, heading: Real, pen_down: Bool)
```

## Chiron Commands

1. Assignment: `:var = expression`
2. Conditional: `if condition [...]`
3. Forward: `forward expression`
4. Backward: `backward expression`
5. Left: `left expression`
6. Right: `right expression`
7. Pen Down: `pendown`
8. Pen Up: `penup`
9. Goto: `goto (x_expr, y_expr)`
10. No-Op: `NOP`
11. Pause: `pause`
12. Repeat: `repeat N [body]` (desugared into loop with counter)

### Loop Implementation

The `repeat N [body]` construct is **desugared** into:
1. Counter initialization: `:__rep_counter_K = N`
2. Loop condition: `if (:__rep_counter_K > 0) [...]`
3. Loop body instructions
4. Counter decrement: `:__rep_counter_K = :__rep_counter_K - 1`
5. Backedge: `(ConditionCommand(False), -len(body) - 2)` - unconditional jump back

Example:
```
repeat 3 [forward 50]
```

Desugars to IR (K=1):
```
[L0] :__rep_counter_1 = 3                    [1]
[L1] if (:__rep_counter_1 > 0) [...]         [3]  // skip to L4 if false
[L2] forward 50                              [1]
[L3] :__rep_counter_1 = :__rep_counter_1 - 1 [1]
[L4] if (False) [...]                        [-3] // unconditional jump to L1
```