import ast, json, sys, pathlib
from typing import Optional, Union


def format_arg(arg: ast.arg, defaults_map):
    name = arg.arg
    annotation = None
    if arg.annotation:
        annotation = ast.unparse(arg.annotation) if hasattr(ast, "unparse") else None
    default = defaults_map.get(name)
    return {"name": name, "type": annotation, "default": default}


def function_signature(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
    pos_args = node.args.args
    kwonly = node.args.kwonlyargs
    defaults = node.args.defaults or []
    kw_defaults = node.args.kw_defaults or []

    pos_defaults_map = {}
    if defaults:
        for name, d in zip([a.arg for a in pos_args][-len(defaults):], defaults):
            pos_defaults_map[name] = ast.unparse(d) if hasattr(ast, "unparse") else None
    kw_defaults_map = {}
    for a, d in zip(kwonly, kw_defaults):
        kw_defaults_map[a.arg] = ast.unparse(d) if d and hasattr(ast, "unparse") else None

    params = [format_arg(a, pos_defaults_map) for a in pos_args]
    if node.args.vararg:
        params.append({"name": "*" + node.args.vararg.arg, "type": None, "default": None})
    params.extend(format_arg(a, kw_defaults_map) for a in kwonly)
    if node.args.kwarg:
        params.append({"name": "**" + node.args.kwarg.arg, "type": None, "default": None})

    returns = ast.unparse(node.returns) if getattr(node, "returns", None) and hasattr(ast, "unparse") else None
    return {"params": params, "returns": returns}


def safe_function_signature(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
    try:
        sig = function_signature(node)
        # Guarantee params key
        if "params" not in sig or sig["params"] is None:
            sig["params"] = []
        return sig
    except Exception:
        return {"params": [], "returns": None}


def _module_name_from_path(path: str, root: Optional[str]) -> str:
    p = pathlib.Path(path)
    try:
        rel = p.relative_to(root) if root else p
    except Exception:
        rel = p
    parts = list(rel.parts)
    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts and parts[0] in {"src", "lib"}:
        parts = parts[1:]
    return ".".join(parts)


def _collect_imports(tree: ast.Module):
    imports = []
    alias_map = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append({"type": "import", "module": n.name, "as": n.asname, "lineno": node.lineno})
                if n.asname:
                    alias_map[n.asname] = n.name
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            for n in node.names:
                imports.append({
                    "type": "from",
                    "module": base,
                    "name": n.name,
                    "as": n.asname,
                    "level": node.level,
                    "lineno": node.lineno,
                })
                if n.asname:
                    alias_map[n.asname] = f"{base}.{n.name}" if base else n.name
    return imports, alias_map


def _class_bases(node: ast.ClassDef):
    bases = []
    for b in node.bases:
        try:
            bases.append(ast.unparse(b) if hasattr(ast, "unparse") else None)
        except Exception:
            bases.append(None)
    return bases


def _class_attributes(node: ast.ClassDef):
    attrs = []
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name):
                    val = None
                    try:
                        val = ast.unparse(stmt.value) if hasattr(ast, "unparse") else None
                    except Exception:
                        pass
                    attrs.append({"name": tgt.id, "value": val, "lineno": stmt.lineno, "public": not tgt.id.startswith("_")})
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            annotation = None
            value = None
            try:
                annotation = ast.unparse(stmt.annotation) if hasattr(ast, "unparse") and stmt.annotation else None
            except Exception:
                pass
            try:
                value = ast.unparse(stmt.value) if hasattr(ast, "unparse") and stmt.value else None
            except Exception:
                pass
            attrs.append({"name": name, "type": annotation, "value": value, "lineno": stmt.lineno, "public": not name.startswith("_")})
    return attrs


def _decorators(node):
    decos = []
    for d in getattr(node, "decorator_list", []):
        try:
            decos.append(ast.unparse(d) if hasattr(ast, "unparse") else None)
        except Exception:
            decos.append(None)
    return decos


def _raises(node):
    raised = []
    for n in ast.walk(node):
        if isinstance(n, ast.Raise) and n.exc:
            try:
                raised.append(ast.unparse(n.exc) if hasattr(ast, "unparse") else None)
            except Exception:
                raised.append(None)
    return raised


def _module_variables(tree: ast.Module):
    vars_ = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id != "__all__":
                    name = tgt.id
                    public = not name.startswith("_")
                    val = None
                    try:
                        val = ast.unparse(node.value) if hasattr(ast, "unparse") else None
                    except Exception:
                        pass
                    vars_.append({"name": name, "value": val, "lineno": node.lineno, "public": public})
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            public = not name.startswith("_")
            annotation = None
            value = None
            try:
                annotation = ast.unparse(node.annotation) if hasattr(ast, "unparse") and node.annotation else None
            except Exception:
                pass
            try:
                value = ast.unparse(node.value) if hasattr(ast, "unparse") and node.value else None
            except Exception:
                pass
            vars_.append({"name": name, "type": annotation, "value": value, "lineno": node.lineno, "public": public})
    return vars_


def index_file(path, root=None):
    try:
        src = pathlib.Path(path).read_text(encoding="utf-8")
        tree = ast.parse(src, filename=path)
    except Exception:
        return None

    module_doc = ast.get_docstring(tree) or ""
    module = _module_name_from_path(path, root)
    imports, alias_map = _collect_imports(tree)

    items = []
    exports = []
    constants = []
    calls = []

    # Top-level assignments (constants by ALL_CAPS)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    val = None
                    try:
                        val = ast.unparse(node.value) if hasattr(ast, "unparse") else None
                    except Exception:
                        pass
                    constants.append({"name": tgt.id, "value": val, "lineno": node.lineno, "public": True})
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            try:
                exports = [elt.s for elt in node.value.elts if isinstance(elt, ast.Str)]
            except Exception:
                exports = []

    module_vars = _module_variables(tree)

    # Build parent pointers
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    def current_parent(n: ast.AST):
        while n:
            parent = parents.get(id(n))
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                return parent
            n = parent
        return None

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or ""
            parent = parents.get(id(node))
            ctx = {"in_class": isinstance(parent, ast.ClassDef), "class_name": parent.name if isinstance(parent, ast.ClassDef) else None}
            items.append({
                "kind": "function",
                "name": node.name,
                "public": not node.name.startswith("_"),
                "signature": safe_function_signature(node),
                "doc": doc,
                "lineno": node.lineno,
                "context": ctx,
                "decorators": _decorators(node),
                "raises": _raises(node),
            })
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node) or ""
            methods = []
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        "name": m.name,
                        "public": not m.name.startswith("_"),
                        "signature": safe_function_signature(m),
                        "lineno": m.lineno,
                        "doc": ast.get_docstring(m) or "",
                        "decorators": _decorators(m),
                        "raises": _raises(m),
                    })
            items.append({
                "kind": "class",
                "name": node.name,
                "public": not node.name.startswith("_"),
                "doc": doc,
                "lineno": node.lineno,
                "bases": _class_bases(node),
                "attributes": _class_attributes(node),
                "methods": methods,
                "decorators": _decorators(node),
            })
        elif isinstance(node, ast.Call):
            caller_parent = current_parent(node)
            caller_ctx = {
                "module": module,
                "class": caller_parent.name if isinstance(caller_parent, ast.ClassDef) else None,
                "function": caller_parent.name if isinstance(caller_parent, (ast.FunctionDef, ast.AsyncFunctionDef)) else None,
            }
            try:
                if isinstance(node.func, ast.Name):
                    fname = node.func.id
                    calls.append({"callee": fname, "lineno": node.lineno, "caller": caller_ctx})
                elif isinstance(node.func, ast.Attribute):
                    fname = node.func.attr
                    calls.append({"callee": fname, "lineno": node.lineno, "caller": caller_ctx})
            except Exception:
                pass

    calls = _compress_calls(calls)

    module_summary = {
        "functions": sum(1 for i in items if i["kind"] == "function"),
        "classes": sum(1 for i in items if i["kind"] == "class"),
        "constants": len(constants),
        "variables": len(module_vars),
        "imports": len(imports),
    }

    return {
        "file": str(path),
        "module": module,
        "module_doc": module_doc,
        "imports": imports,
        "import_aliases": alias_map,
        "exports": exports,
        "constants": constants,
        "variables": module_vars,
        "calls": calls,
        "summary": module_summary,
        "items": items,
    }


def _compress_calls(calls, max_unique=50):
    # Deduplicate by (callee, caller.function, caller.class, lineno bucket)
    seen = set()
    out = []
    for c in calls:
        key = (
            c.get("callee"),
            (c.get("caller") or {}).get("function"),
            (c.get("caller") or {}).get("class"),
            int(c.get("lineno", 0) // 10),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= max_unique:
            break
    return out


def _top_package_of(module: str) -> str:
    return module.split(".", 1)[0] if module else ""


def main(root, shard_dir=None, auto_shard=False, mod_threshold=150, size_threshold_mb=10):
    rootp = pathlib.Path(root)
    files = [str(p) for p in rootp.rglob("*.py") if "venv" not in p.parts and "/." not in str(p)]
    out = []
    for f in files:
        idx = index_file(f, root=str(rootp))
        if idx:
            out.append(idx)
    summary = {
        "root": str(rootp),
        "counts": {
            "modules": len(out),
            "functions": sum(1 for m in out for i in m["items"] if i["kind"] == "function"),
            "classes": sum(1 for m in out for i in m["items"] if i["kind"] == "class"),
            "constants": sum(len(m["constants"]) for m in out),
            "variables": sum(len(m["variables"]) for m in out),
            "imports": sum(len(m["imports"]) for m in out),
        },
        "files": out,
    }

    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    should_shard = bool(shard_dir) or (auto_shard and (
        summary["counts"]["modules"] > mod_threshold or len(payload.encode("utf-8")) > size_threshold_mb * 1024 * 1024
    ))
    if should_shard:
        shard_root = pathlib.Path(shard_dir or "docs/signatures")
        shard_root.mkdir(parents=True, exist_ok=True)
        buckets = {}
        for m in out:
            pkg = _top_package_of(m["module"])
            buckets.setdefault(pkg, []).append(m)
        for pkg, files_idx in buckets.items():
            shard_path = shard_root / f"{pkg or 'root'}.json"
            shard_payload = {
                "package": pkg or "root",
                "counts": {
                    "modules": len(files_idx),
                    "functions": sum(1 for m in files_idx for i in m["items"] if i["kind"] == "function"),
                    "classes": sum(1 for m in files_idx for i in m["items"] if i["kind"] == "class"),
                },
                "files": files_idx,
            }
            shard_path.write_text(json.dumps(shard_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        # Also write a lightweight root summary
        (shard_root / "_summary.json").write_text(
            json.dumps(summary["counts"], ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(payload)


if __name__ == "__main__":
    # Usage: python tools/index_signatures.py src [--shard docs/signatures] [--auto-shard]
    args = sys.argv[1:]
    root = args[0] if args and not args[0].startswith("--") else "."
    shard = None
    auto = "--auto-shard" in args
    if "--shard" in args:
        i = args.index("--shard")
        shard = args[i + 1] if i + 1 < len(args) else None
    main(root, shard_dir=shard, auto_shard=auto)