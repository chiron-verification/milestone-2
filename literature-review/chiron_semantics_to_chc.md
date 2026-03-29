---
noteId: "d2549ff0155911f1bab76da85a4d811c"
tags: []

---

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
2. Conditional (If): `if condition [...]`
3. Conditional (If-Else): `if condition [...] else [...]`
4. Forward: `forward expression`
5. Backward: `backward expression`
6. Left: `left expression`
7. Right: `right expression`
8. Pen Down: `pendown`
9. Pen Up: `penup`
10. Goto: `goto (x_expr, y_expr)`
11. No-Op: `NOP`
12. Pause: `pause`
13. Repeat: `repeat N [body]` (desugared into loop with counter)

## Arithmetic and Boolean Expressions
### Arithmetic Expressions
- Addition: `expr + expr`
- Subtraction: `expr - expr`
- Multiplication: `expr * expr`
- Division: `expr / expr`
- Unary Minus: `-expr`

### Boolean Expressions
- And: `expr && expr`
- Or: `expr || expr`
- Not: `!expr`
- Less Than: `expr < expr`
- Greater Than: `expr > expr`
- Less Than or Equal: `expr <= expr`
- Greater Than or Equal: `expr >= expr`
- Equal: `expr == expr`
- Not Equal: `expr != expr`
- Pen Status Check: `pendown?`
- True: `true`
- False: `false`
- Numeric Value: `Num`
- Variable Reference: `Var`vs code
