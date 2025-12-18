from typing import Dict, List

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


def _safe_eval(expr: str, ctx: Dict[str, object]) -> bool:
    if not isinstance(expr, str) or not expr.strip():
        raise ValueError("Guard expression must be a non-empty string")
    return bool(eval(expr, {"__builtins__": SAFE_BUILTINS}, ctx))

def build_step_eval_ctx(step: dict, context: Dict[str, object]) -> Dict[str, object]:
    eval_ctx: Dict[str, object] = {}

    outs = step.get("outputs")
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

def enforce_require(eval_ctx: Dict[str, object], rules: List[Dict[str, object]], step_name: str = None, context_info: Dict[str, object] = None):
    for rule in rules or []:
        expr = rule.get("if")
        msg = rule.get("message", "Require condition failed")
        try:
            ok = _safe_eval(expr, eval_ctx)
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
                if var_name in expr and not var_name.startswith('_'):
                    val = eval_ctx[var_name]
                    if isinstance(val, str):
                        error_parts.append(f"  {var_name} = {repr(val[:200])}... (length={len(val)})")
                    else:
                        error_parts.append(f"  {var_name} = {repr(val)[:200]}")

            raise ValueError("\n".join(error_parts))

def collect_warnings(eval_ctx: Dict[str, object], rules: List[Dict[str, object]]) -> List[str]:
    messages: List[str] = []
    for rule in rules or []:
        expr = rule.get("if")
        msg = rule.get("message", "Warning condition matched")
        try:
            ok = _safe_eval(expr, eval_ctx)
        except Exception as e:
            messages.append(f"Warn eval error for '{expr}': {e}")
            continue
        if ok:
            messages.append(msg)
    return messages