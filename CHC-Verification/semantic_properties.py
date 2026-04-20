"""
Semantic property helper transpiler.

Goal:
Users write helper-style property strings, for example:
  - is_nonnegative(v)
  - position_in_box(-10, 50, -10, 30)
  - relation_guarded(x >= 0, pen_is_up(), pen_is_down())

This module rewrites such strings into raw expressions accepted by
CHC_Verification, without touching safety_properties.py.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence


def _arity(name: str, args: Sequence[str], expected: int) -> None:
    if len(args) != expected:
        raise ValueError(f"{name} expects {expected} args, got {len(args)}.")


def _arity_at_least(name: str, args: Sequence[str], minimum: int) -> None:
    if len(args) < minimum:
        raise ValueError(f"{name} expects at least {minimum} args, got {len(args)}.")


def _and(parts: Sequence[str]) -> str:
    if len(parts) == 0:
        return "True"
    if len(parts) == 1:
        return parts[0]
    return f"And({', '.join(parts)})"


def _or(parts: Sequence[str]) -> str:
    if len(parts) == 0:
        return "False"
    if len(parts) == 1:
        return parts[0]
    return f"Or({', '.join(parts)})"


def _not(part: str) -> str:
    return f"Not({part})"


def _implies(p: str, q: str) -> str:
    return f"Or(Not({p}), {q})"


def _fmt_is_zero(args: Sequence[str]) -> str:
    _arity("is_zero", args, 1)
    return f"{args[0]} == 0"


def _fmt_is_nonzero(args: Sequence[str]) -> str:
    _arity("is_nonzero", args, 1)
    return f"{args[0]} != 0"


def _fmt_is_positive(args: Sequence[str]) -> str:
    _arity("is_positive", args, 1)
    return f"{args[0]} > 0"


def _fmt_is_nonnegative(args: Sequence[str]) -> str:
    _arity("is_nonnegative", args, 1)
    return f"{args[0]} >= 0"


def _fmt_is_negative(args: Sequence[str]) -> str:
    _arity("is_negative", args, 1)
    return f"{args[0]} < 0"


def _fmt_is_nonpositive(args: Sequence[str]) -> str:
    _arity("is_nonpositive", args, 1)
    return f"{args[0]} <= 0"


def _fmt_is_greater(args: Sequence[str]) -> str:
    _arity("is_greater", args, 2)
    return f"{args[0]} > {args[1]}"


def _fmt_is_greater_equal(args: Sequence[str]) -> str:
    _arity("is_greater_equal", args, 2)
    return f"{args[0]} >= {args[1]}"


def _fmt_is_less(args: Sequence[str]) -> str:
    _arity("is_less", args, 2)
    return f"{args[0]} < {args[1]}"


def _fmt_is_less_equal(args: Sequence[str]) -> str:
    _arity("is_less_equal", args, 2)
    return f"{args[0]} <= {args[1]}"


def _fmt_is_equal(args: Sequence[str]) -> str:
    _arity("is_equal", args, 2)
    return f"{args[0]} == {args[1]}"


def _fmt_is_not_equal(args: Sequence[str]) -> str:
    _arity("is_not_equal", args, 2)
    return f"{args[0]} != {args[1]}"


def _fmt_is_between(args: Sequence[str]) -> str:
    _arity("is_between", args, 3)
    v, lo, hi = args
    return _and([f"{v} >= {lo}", f"{v} <= {hi}"])


def _fmt_is_strictly_between(args: Sequence[str]) -> str:
    _arity("is_strictly_between", args, 3)
    v, lo, hi = args
    return _and([f"{v} > {lo}", f"{v} < {hi}"])


def _fmt_is_one_of(args: Sequence[str]) -> str:
    _arity_at_least("is_one_of", args, 2)
    v = args[0]
    values = args[1:]
    return _or([f"{v} == {x}" for x in values])


def _fmt_is_multiple_of(args: Sequence[str]) -> str:
    _arity("is_multiple_of", args, 2)
    return f"{args[0]} % {args[1]} == 0"


def _fmt_sum_is(args: Sequence[str]) -> str:
    _arity("sum_is", args, 3)
    return f"{args[0]} + {args[1]} == {args[2]}"


def _fmt_diff_is(args: Sequence[str]) -> str:
    _arity("diff_is", args, 3)
    return f"{args[0]} - {args[1]} == {args[2]}"


def _fmt_linear_eq(args: Sequence[str]) -> str:
    _arity("linear_eq", args, 2)
    return f"{args[0]} == {args[1]}"


def _fmt_all_of(args: Sequence[str]) -> str:
    return _and(args)


def _fmt_any_of(args: Sequence[str]) -> str:
    return _or(args)


def _fmt_not_prop(args: Sequence[str]) -> str:
    _arity("not_prop", args, 1)
    return _not(args[0])


def _fmt_implies(args: Sequence[str]) -> str:
    _arity("implies", args, 2)
    return _implies(args[0], args[1])


def _fmt_pen_is_down(args: Sequence[str]) -> str:
    _arity("pen_is_down", args, 0)
    return "pendown"


def _fmt_pen_is_up(args: Sequence[str]) -> str:
    _arity("pen_is_up", args, 0)
    return "Not(pendown)"


def _fmt_x_in_range(args: Sequence[str]) -> str:
    _arity("x_in_range", args, 2)
    return _and([f"xcor >= {args[0]}", f"xcor <= {args[1]}"])


def _fmt_y_in_range(args: Sequence[str]) -> str:
    _arity("y_in_range", args, 2)
    return _and([f"ycor >= {args[0]}", f"ycor <= {args[1]}"])


def _fmt_position_in_box(args: Sequence[str]) -> str:
    _arity("position_in_box", args, 4)
    xmin, xmax, ymin, ymax = args
    return _and(
        [
            f"xcor >= {xmin}",
            f"xcor <= {xmax}",
            f"ycor >= {ymin}",
            f"ycor <= {ymax}",
        ]
    )


def _fmt_at_position(args: Sequence[str]) -> str:
    _arity("at_position", args, 2)
    return _and([f"xcor == {args[0]}", f"ycor == {args[1]}"])


def _fmt_x_equals(args: Sequence[str]) -> str:
    _arity("x_equals", args, 1)
    return f"xcor == {args[0]}"


def _fmt_y_equals(args: Sequence[str]) -> str:
    _arity("y_equals", args, 1)
    return f"ycor == {args[0]}"


def _fmt_position_relation(args: Sequence[str]) -> str:
    _arity("position_relation", args, 1)
    return args[0]


def _fmt_on_diagonal(args: Sequence[str]) -> str:
    _arity("on_diagonal", args, 0)
    return "xcor == ycor"


def _fmt_heading_in_range(args: Sequence[str]) -> str:
    _arity("heading_in_range", args, 0)
    return "And(heading >= 0, heading < 360)"


def _fmt_heading_is(args: Sequence[str]) -> str:
    _arity("heading_is", args, 1)
    return f"heading == {args[0]}"


def _fmt_heading_in(args: Sequence[str]) -> str:
    _arity_at_least("heading_in", args, 1)
    return _or([f"heading == {v}" for v in args])


def _fmt_heading_on_15_grid(args: Sequence[str]) -> str:
    _arity("heading_on_15_grid", args, 0)
    return "heading % 15 == 0"


def _fmt_heading_multiple_of(args: Sequence[str]) -> str:
    _arity("heading_multiple_of", args, 1)
    return f"heading % {args[0]} == 0"


def _fmt_heading_cardinal(args: Sequence[str]) -> str:
    _arity("heading_cardinal", args, 0)
    return "Or(heading == 0, heading == 90, heading == 180, heading == 270)"


def _fmt_var_nonnegative(args: Sequence[str]) -> str:
    _arity("var_nonnegative", args, 1)
    return f"{args[0]} >= 0"


def _fmt_var_bounded(args: Sequence[str]) -> str:
    _arity("var_bounded", args, 3)
    return _and([f"{args[0]} >= {args[1]}", f"{args[0]} <= {args[2]}"])


def _fmt_vars_all_nonnegative(args: Sequence[str]) -> str:
    _arity_at_least("vars_all_nonnegative", args, 1)
    return _and([f"{v} >= 0" for v in args])


def _fmt_relation_guarded(args: Sequence[str]) -> str:
    _arity("relation_guarded", args, 3)
    cond, p_then, p_else = args
    return _or([_and([cond, p_then]), _and([_not(cond), p_else])])


HELPER_FORMATTERS: dict[str, Callable[[Sequence[str]], str]] = {
    "is_zero": _fmt_is_zero,
    "is_nonzero": _fmt_is_nonzero,
    "is_positive": _fmt_is_positive,
    "is_nonnegative": _fmt_is_nonnegative,
    "is_negative": _fmt_is_negative,
    "is_nonpositive": _fmt_is_nonpositive,
    "is_greater": _fmt_is_greater,
    "is_greater_equal": _fmt_is_greater_equal,
    "is_less": _fmt_is_less,
    "is_less_equal": _fmt_is_less_equal,
    "is_equal": _fmt_is_equal,
    "is_not_equal": _fmt_is_not_equal,
    "is_between": _fmt_is_between,
    "is_strictly_between": _fmt_is_strictly_between,
    "is_one_of": _fmt_is_one_of,
    "is_multiple_of": _fmt_is_multiple_of,
    "sum_is": _fmt_sum_is,
    "diff_is": _fmt_diff_is,
    "linear_eq": _fmt_linear_eq,
    "all_of": _fmt_all_of,
    "any_of": _fmt_any_of,
    "not_prop": _fmt_not_prop,
    "implies": _fmt_implies,
    "pen_is_down": _fmt_pen_is_down,
    "pen_is_up": _fmt_pen_is_up,
    "x_in_range": _fmt_x_in_range,
    "y_in_range": _fmt_y_in_range,
    "position_in_box": _fmt_position_in_box,
    "at_position": _fmt_at_position,
    "x_equals": _fmt_x_equals,
    "y_equals": _fmt_y_equals,
    "position_relation": _fmt_position_relation,
    "on_diagonal": _fmt_on_diagonal,
    "heading_in_range": _fmt_heading_in_range,
    "heading_is": _fmt_heading_is,
    "heading_in": _fmt_heading_in,
    "heading_on_15_grid": _fmt_heading_on_15_grid,
    "heading_multiple_of": _fmt_heading_multiple_of,
    "heading_cardinal": _fmt_heading_cardinal,
    "var_nonnegative": _fmt_var_nonnegative,
    "var_bounded": _fmt_var_bounded,
    "vars_all_nonnegative": _fmt_vars_all_nonnegative,
    "relation_guarded": _fmt_relation_guarded,
}


def _op_symbol(op: ast.AST) -> str:
    mapping = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.Mod: "%",
        ast.Eq: "==",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.LtE: "<=",
        ast.Gt: ">",
        ast.GtE: ">=",
    }
    for k, v in mapping.items():
        if isinstance(op, k):
            return v
    raise ValueError(f"Unsupported operator: {type(op).__name__}")


class _ExprToString(ast.NodeVisitor):
    def visit_Expression(self, node: ast.Expression) -> str:  
        return self.visit(node.body)

    def visit_Name(self, node: ast.Name) -> str: 
        return node.id

    def visit_Constant(self, node: ast.Constant) -> str: 
        if isinstance(node.value, bool):
            return "True" if node.value else "False"
        if isinstance(node.value, str):
            return node.value
        return str(node.value)

    def visit_BinOp(self, node: ast.BinOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = _op_symbol(node.op)
        return f"({left} {op} {right})"

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str: 
        if isinstance(node.op, ast.Not):
            return f"Not({self.visit(node.operand)})"
        if isinstance(node.op, ast.USub):
            return f"(-{self.visit(node.operand)})"
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    def visit_BoolOp(self, node: ast.BoolOp) -> str:  
        parts = [self.visit(v) for v in node.values]
        if isinstance(node.op, ast.And):
            return _and(parts)
        if isinstance(node.op, ast.Or):
            return _or(parts)
        raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")

    def visit_Compare(self, node: ast.Compare) -> str:  
        left = self.visit(node.left)
        parts: list[str] = []
        for op, comp in zip(node.ops, node.comparators):
            right = self.visit(comp)
            parts.append(f"({left} {_op_symbol(op)} {right})")
            left = right
        return _and(parts)

    def visit_Call(self, node: ast.Call) -> str: 
        if node.keywords:
            raise ValueError("Keyword args are not supported in semantic property strings.")
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function-call names are supported.")

        fname = node.func.id
        arg_strs = [self.visit(a) for a in node.args]

        if fname == "And":
            return _and(arg_strs)
        if fname == "Or":
            return _or(arg_strs)
        if fname == "Not":
            _arity("Not", arg_strs, 1)
            return _not(arg_strs[0])
        if fname == "Implies":
            _arity("Implies", arg_strs, 2)
            return _implies(arg_strs[0], arg_strs[1])

        if fname in HELPER_FORMATTERS:
            return HELPER_FORMATTERS[fname](arg_strs)

        # Unknown call: preserve it.
        return f"{fname}({', '.join(arg_strs)})"

    def generic_visit(self, node: ast.AST) -> str:
        raise ValueError(f"Unsupported syntax in semantic property string: {type(node).__name__}")


def transpile_property_expr(expr: str) -> str:
    """
    Convert a helper-style property string to a raw solver property string.
    """
    if not isinstance(expr, str):
        raise TypeError(f"expr must be str, got {type(expr)}")
    tree = ast.parse(expr, mode="eval")
    return _ExprToString().visit(tree)


@dataclass
class Property:
    name: str
    expr: str


def transpile_user_properties(user_properties: Iterable[Any]) -> list[Property]:
    """
    Accepts either:
      - objects with .name (str) and .expr (str)
      - tuples of (name, expr)
    Returns Property objects with transpiled .expr.
    """
    out: list[Property] = []
    for p in user_properties:
        if isinstance(p, tuple) and len(p) == 2:
            name, expr = p
        else:
            name = getattr(p, "name", None)
            expr = getattr(p, "expr", None)
        if not isinstance(name, str) or not isinstance(expr, str):
            raise TypeError(
                "Each property must be (name:str, expr:str) or object with .name/.expr strings."
            )
        out.append(Property(name=name, expr=transpile_property_expr(expr)))
    return out


def CHC_Verification_semantic(file_name, mode, user_properties, **kwargs):
    """
    Wrapper over core CHC_Verification.
    It transpiles helper-style property strings first, then calls core verifier.
    """
    from safety_properties import CHC_Verification

    return CHC_Verification(
        file_name=file_name,
        mode=mode,
        user_properties=transpile_user_properties(user_properties),
        **kwargs,
    )

