import ast
import operator
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional, cast

SAFE_BUILTINS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "any": any,
    "all": all,
    "min": min,
    "max": max,
    "sum": sum,
}

_COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

_UNARY_OPS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Not: operator.not_,
}


def _eval_node(node, ctx: Mapping[str, Any]):
    """Recursively evaluate an AST node against ctx without using eval()."""

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        name = node.id
        if name.startswith("_"):
            raise NameError(f"Name '{name}' is not defined")
        if name in ctx:
            return ctx[name]
        if name in SAFE_BUILTINS:
            return SAFE_BUILTINS[name]
        raise NameError(f"Name '{name}' is not defined")

    if isinstance(node, ast.Attribute):
        attr = node.attr
        if attr.startswith("_"):
            raise ValueError(f"Access to attribute '{attr}' is not allowed")
        obj = _eval_node(node.value, ctx)
        if isinstance(obj, dict) and attr in obj:
            return obj[attr]
        return getattr(obj, attr)

    if isinstance(node, ast.Subscript):
        obj = _eval_node(node.value, ctx)
        slice_node = node.slice
        # Python 3.8 compat: ast.Index was removed in 3.9
        if hasattr(ast, "Index") and isinstance(slice_node, ast.Index):
            slice_node = slice_node.value  # type: ignore[attr-defined]
        key = _eval_node(slice_node, ctx)
        return cast(Any, obj)[key]

    if isinstance(node, ast.UnaryOp):
        op_fn = _UNARY_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_fn(_eval_node(node.operand, ctx))

    if isinstance(node, ast.BinOp):
        op_fn = _BIN_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        return op_fn(_eval_node(node.left, ctx), _eval_node(node.right, ctx))

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: object = True
            for val in node.values:
                result = _eval_node(val, ctx)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for val in node.values:
                result = _eval_node(val, ctx)
                if result:
                    return result
            return result

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, ctx)
        for op, comparator in zip(node.ops, node.comparators):
            op_fn = _COMPARE_OPS.get(type(op))
            if op_fn is None:
                raise ValueError(f"Unsupported comparison operator: {type(op).__name__}")
            right = _eval_node(comparator, ctx)
            if not op_fn(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            # Method call: obj.method(args) — allow non-underscore methods only
            attr = node.func.attr
            if attr.startswith("_"):
                raise ValueError(f"Calling method '{attr}' is not allowed")
            obj = _eval_node(node.func.value, ctx)
            method = getattr(obj, attr, None)
            if method is None:
                raise ValueError(f"Object has no method '{attr}'")
            args = [_eval_node(arg, ctx) for arg in node.args]
            kwargs: dict[str, Any] = {kw.arg: _eval_node(kw.value, ctx) for kw in node.keywords if kw.arg is not None}
            return method(*args, **kwargs)
        else:
            # Free function call — only SAFE_BUILTINS allowed
            func = _eval_node(node.func, ctx)
            if func not in SAFE_BUILTINS.values():
                name = getattr(node.func, "id", "?")
                raise ValueError(f"Calling '{name}' is not allowed")
            args = [_eval_node(arg, ctx) for arg in node.args]
            kwargs = {kw.arg: _eval_node(kw.value, ctx) for kw in node.keywords if kw.arg is not None}
            return func(*args, **kwargs)

    if isinstance(node, ast.IfExp):
        test = _eval_node(node.test, ctx)
        return _eval_node(node.body if test else node.orelse, ctx)

    if isinstance(node, ast.List):
        return [_eval_node(e, ctx) for e in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e, ctx) for e in node.elts)

    raise ValueError(f"Expression type '{type(node).__name__}' is not allowed in pipeline conditions")


def build_eval_locals(context: Dict[str, Any]) -> dict:
    """Build a locals dict for _safe_eval from a pipeline context.

    Adds all identifier-safe context keys as locals plus a ``ctx`` lookup
    function for dot-notation access via get_from_context.
    """
    from llmflow.utils.context import get_from_context, _MISSING

    def ctx_lookup(expr):
        result = get_from_context(expr, context)
        return None if result is _MISSING else result

    eval_locals: dict = {"context": context, "ctx": ctx_lookup}
    for key, value in context.items():
        if isinstance(key, str) and key.isidentifier():
            eval_locals[key] = value
    return eval_locals


def _safe_eval(expr: str, ctx: Mapping[str, Any]) -> bool:
    if not isinstance(expr, str):
        raise ValueError("Guard expression must be a string")
    expr_stripped = expr.strip()
    if not expr_stripped:
        raise ValueError("Guard expression must be a non-empty string")
    try:
        tree = ast.parse(expr_stripped, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression syntax: {exc}") from exc
    return bool(_eval_node(tree.body, ctx))


def build_step_eval_ctx(step: dict, context: Mapping[str, Any]) -> Dict[str, object]:
    eval_ctx: Dict[str, object] = {}

    # Handle None context gracefully
    if context is None:
        context = {}

    outs = step.get("output")
    if isinstance(outs, dict):
        for k in outs.keys():
            eval_ctx[k] = context.get(k)
    elif isinstance(outs, list):
        for k in outs:
            eval_ctx[k] = context.get(k)
    elif isinstance(outs, str):
        eval_ctx[outs] = context.get(outs)

    inputs_vars = step.get("inputs", {}).get("variables", {})
    if isinstance(inputs_vars, dict):
        for k, v in inputs_vars.items():
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                eval_ctx[k] = context.get(v[2:-1])
            else:
                eval_ctx[k] = v

    eval_ctx.update(context or {})
    return eval_ctx

def enforce_require(eval_ctx: Mapping[str, Any], rules: Sequence[Mapping[str, Any]], step_name: Optional[str] = None, context_info: Optional[Mapping[str, Any]] = None):
    for rule in rules or []:
        expr = rule.get("if")
        msg = rule.get("message", "Require condition failed")
        try:
            if expr is None:
                raise ValueError("Require rule missing 'if' expression")
            ok = _safe_eval(str(expr), eval_ctx)
        except Exception as e:
            raise ValueError(f"Require eval error for '{expr}': {e}")
        if not ok:
            # Build detailed error message
            error_parts = []
            if step_name:
                error_parts.append(f"Step: {step_name}")
            if context_info:
                info_str = ", ".join(f"{k}={repr(v)[:100]}" for k, v in context_info.items())
                error_parts.append(f"Context: {info_str}")
            error_parts.append(f"Condition: {expr}")
            error_parts.append(f"Message: {msg}")

            # Show actual variable values being checked
            for var_name in eval_ctx:
                if expr is not None and var_name in str(expr) and not var_name.startswith('_'):
                    val = eval_ctx[var_name]
                    if isinstance(val, str):
                        error_parts.append(f"  {var_name} = {repr(val[:200])}... (length={len(val)})")
                    else:
                        error_parts.append(f"  {var_name} = {repr(val)[:200]}")

            raise ValueError("\n".join(error_parts))

def collect_warnings(eval_ctx: Mapping[str, Any], rules: Sequence[Mapping[str, Any]]) -> List[str]:
    messages: List[str] = []
    for rule in rules or []:
        expr = rule.get("if")
        msg = rule.get("message", "Warning condition matched")
        try:
            if expr is None:
                messages.append("Warn eval error: rule missing 'if' expression")
                continue
            ok = _safe_eval(str(expr), eval_ctx)
        except Exception as e:
            messages.append(f"Warn eval error for '{expr}': {e}")
            continue
        if ok:
            messages.append(str(msg))
    return messages
