import ast, json, sys, pathlib
from typing import Optional, Union


def format_param(arg: ast.arg, defaults_map):
    """Format a single parameter with optional type and default."""
    name = arg.arg
    annotation = ast.unparse(arg.annotation) if arg.annotation and hasattr(ast, "unparse") else None
    default = defaults_map.get(name)

    # Build simple string: "name: type = default" or just "name"
    parts = [name]
    if annotation:
        parts.append(f": {annotation}")
    if default:
        parts.append(f" = {default}")
    return "".join(parts)


def simple_signature(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
    """Generate a simple function signature string."""
    try:
        pos_args = node.args.args
        kwonly = node.args.kwonlyargs
        defaults = node.args.defaults or []
        kw_defaults = node.args.kw_defaults or []

        # Map defaults to parameter names
        pos_defaults_map = {}
        if defaults:
            for name, d in zip([a.arg for a in pos_args][-len(defaults):], defaults):
                pos_defaults_map[name] = ast.unparse(d) if hasattr(ast, "unparse") else None

        kw_defaults_map = {}
        for a, d in zip(kwonly, kw_defaults):
            kw_defaults_map[a.arg] = ast.unparse(d) if d and hasattr(ast, "unparse") else None

        # Build parameter list
        params = [format_param(a, pos_defaults_map) for a in pos_args]

        if node.args.vararg:
            params.append(f"*{node.args.vararg.arg}")

        params.extend(format_param(a, kw_defaults_map) for a in kwonly)

        if node.args.kwarg:
            params.append(f"**{node.args.kwarg.arg}")

        # Build return type
        returns = ""
        if getattr(node, "returns", None):
            ret_str = ast.unparse(node.returns) if hasattr(ast, "unparse") else None
            if ret_str:
                returns = f" -> {ret_str}"

        return f"{node.name}({', '.join(params)}){returns}"

    except Exception:
        return f"{node.name}(...)"


def collect_imports(tree: ast.Module) -> list[str]:
    """Extract just the module names being imported (no details)."""
    imports = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return sorted(imports)


def module_name_from_path(path: str, root: Optional[str]) -> str:
    """Convert file path to Python module name."""
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


def index_file(path: str, root: Optional[str] = None) -> Optional[dict]:
    """Extract minimal module information."""
    try:
        src = pathlib.Path(path).read_text(encoding="utf-8")
        tree = ast.parse(src, filename=path)
    except Exception:
        return None

    module = module_name_from_path(path, root)
    imports = collect_imports(tree)
    functions = []

    # Collect all functions (including methods)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or ""
            # Take only first line of docstring
            doc_first_line = doc.split("\n")[0] if doc else ""

            functions.append({
                "name": node.name,
                "signature": simple_signature(node),
                "doc": doc_first_line
            })

    return {
        "module": module,
        "imports": imports,
        "functions": functions
    }


def main(root: str):
    """Index all Python files in root directory."""
    rootp = pathlib.Path(root)
    files = [
        str(p) for p in rootp.rglob("*.py")
        if "venv" not in p.parts and "/." not in str(p)
    ]

    modules = []
    for f in files:
        idx = index_file(f, root=str(rootp))
        if idx:
            modules.append(idx)

    output = {
        "modules": modules,
        "summary": {
            "total_modules": len(modules),
            "total_functions": sum(len(m["functions"]) for m in modules)
        }
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    main(root)