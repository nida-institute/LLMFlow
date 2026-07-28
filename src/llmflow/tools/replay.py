"""`sp tools replay` — test a prompt change against captured debug requests, cheaply.

Ported from the scriptorium project's `scripts/replay_prompt.py`, shipped as-is
(GitHub #177 tracks generalization: schema-driven `--show`, engine call-path reuse,
a stable capture contract, nested `--set`, concurrency).

Mechanism: a captured `*_request.txt` is the original `.gpt` with each `{{var}}`
replaced by its value. Aligning the original `.gpt` against the request line-for-line
recovers the var→value map; substituting that map into the *edited* `.gpt` produces a
faithful test prompt with the same data. One call per variant instead of a full run.

Current assumptions carried from the source tool (see #177):
  - Response is a list of `segments`, each with a `canonical_reference`.
  - `--show` special-cases `sensory`/`characters`; any other field is read verbatim.
  - Direct OpenAI SDK call (faithful for gpt-4.x + response_format).
  - Reads the current debug-file naming convention.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

# A template variable: {{ name }}
_VAR = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

# Debug filename: "<YYYY-MM-DD-HHMMSS>_<stem>_(request|response).txt"
_TS_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}_")
_REQRESP_SUFFIX = re.compile(r"_(request|response)\.txt$")


# ===========================================================================
# Deterministic core (unit-tested in tests/test_tools_replay.py)
# ===========================================================================

def recover_var_map(prompt: str, request: str) -> dict[str, str]:
    """Recover {var: value} by aligning the original `.gpt` against the rendered
    request. The request is the prompt with each `{{var}}` substituted, so the two
    are line-for-line identical except at variable sites.

    Raises ValueError if the two don't align (usually: `prompt` is not the version
    that generated `request`).
    """
    p_lines = prompt.split("\n")
    r_lines = request.split("\n")
    if len(p_lines) != len(r_lines):
        raise ValueError(
            f"prompt and request have different line counts "
            f"({len(p_lines)} vs {len(r_lines)}); is --prompt the version that "
            f"generated --request?"
        )

    result: dict[str, str] = {}
    for p, r in zip(p_lines, r_lines):
        if p == r:
            continue
        names = _VAR.findall(p)
        if not names:
            raise ValueError(
                f"lines differ but the template line has no {{{{var}}}}:\n"
                f"  template: {p!r}\n  request:  {r!r}"
            )
        # Build a regex from the template line: literals escaped, each {{var}} a
        # named capture group. Matching it against the request line extracts values.
        pattern = ""
        last = 0
        for m in _VAR.finditer(p):
            pattern += re.escape(p[last:m.start()])
            pattern += f"(?P<{m.group(1)}>.*)"
            last = m.end()
        pattern += re.escape(p[last:])
        match = re.fullmatch(pattern, r, re.DOTALL)
        if not match:
            raise ValueError(f"could not extract value(s) from line:\n  {p!r}\n  {r!r}")
        for name, val in match.groupdict().items():
            if name in result and result[name] != val:
                raise ValueError(
                    f"variable {name!r} recovered two different values: "
                    f"{result[name]!r} vs {val!r}"
                )
            result[name] = val
    return result


def render(prompt_new: str, var_map: dict[str, str],
           overrides: dict[str, str] | None = None) -> str:
    """Substitute values into the edited prompt's `{{var}}` sites.

    `overrides` (--set) take precedence over recovered values and supply variables
    absent from `var_map`. Raises KeyError if any `{{var}}` has no value — we never
    send a prompt containing a literal `{{var}}`.
    """
    values = dict(var_map)
    if overrides:
        values.update(overrides)

    def _repl(m: re.Match) -> str:
        name = m.group(1)
        if name not in values:
            raise KeyError(
                f"no value for {{{{{name}}}}} — recover it from the request or "
                f"supply it with --set {name}=..."
            )
        return values[name]

    return _VAR.sub(_repl, prompt_new)


def schema_ref(prompt: str) -> str | None:
    """Return the `schema:` path declared in the `.gpt` frontmatter, or None."""
    m = re.search(r"^\s*schema:\s*(\S+)\s*$", prompt, re.MULTILINE)
    return m.group(1) if m else None


def summarize_segment(seg: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Extract the semantic fields we compare on from one output segment. Special
    fields: `sensory` = len(sensory_inventory); `characters` = list of character
    names. Anything else is read verbatim.
    """
    out: dict[str, Any] = {}
    for f in fields:
        if f == "sensory":
            out[f] = len(seg.get("sensory_inventory") or [])
        elif f == "characters":
            out[f] = [c.get("character") for c in (seg.get("characters") or [])]
        else:
            out[f] = seg.get(f)
    return out


def pairing_stem(filename: str) -> str:
    """The stable middle of a debug filename — used to pair a request with its
    saved response, whose timestamps differ (sent vs. received).

    "2026-07-07-124717_scene_bodies_..._M_request.txt"  ->  "scene_bodies_..._M"
    """
    base = filename.rsplit("/", 1)[-1]
    base = _TS_PREFIX.sub("", base)
    base = _REQRESP_SUFFIX.sub("", base)
    return base


def parse_saved_response(text: str) -> dict[str, Any]:
    """Parse a response body. Saved debug responses are Python-dict reprs
    (single quotes, `True`/`None`); fresh API responses are JSON. Accept both.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return ast.literal_eval(text)


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render an aligned monospace table. Column widths use character counts,
    which is correct for the Greek/Hebrew content that runs through this tool
    (one code point per glyph)."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    def fmt(cells: list[str]) -> str:
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells)).rstrip()
    return "\n".join([fmt(headers)] + [fmt(r) for r in rows])


# ===========================================================================
# I/O + LLM call layer (not unit-tested — hits the filesystem and the API).
# Direct OpenAI SDK. The engine sends the frontmatter, so we send the rendered
# prompt VERBATIM (frontmatter included) for faithful replay.
# ===========================================================================

import glob as _glob
from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def find_response_file(request_path: str) -> str | None:
    """Locate the saved response paired with a request file: same directory, same
    pairing_stem, `_response.txt` suffix. Request/response timestamps differ; if
    several responses share the stem, take the earliest at or after the request's.
    """
    p = Path(request_path)
    stem = pairing_stem(p.name)
    candidates = sorted(
        c for c in p.parent.iterdir()
        if c.name.endswith("_response.txt") and pairing_stem(c.name) == stem
    )
    if not candidates:
        return None
    later = [c for c in candidates if c.name >= p.name.replace("_request.txt", "_response.txt")]
    return str((later or candidates)[0])


def load_schema(schema_path: str, repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / schema_path).read_text(encoding="utf-8"))


def call_model(prompt_text: str, schema: dict[str, Any], schema_name: str,
               model: str, temperature: float) -> dict[str, Any]:
    """One LLM call, verbatim prompt, json_schema-constrained. Returns parsed dict."""
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt_text}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    )
    return json.loads(resp.choices[0].message.content)


def _segments_by_ref(obj: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {s.get("canonical_reference", f"#{i}"): s
            for i, s in enumerate(obj.get("segments", []))}


def _parse_set(pairs: list[str] | None) -> dict[str, str]:
    """Parse repeated --set VAR=VALUE (or VAR=@file) into an overrides dict."""
    out: dict[str, str] = {}
    for item in (pairs or []):
        if "=" not in item:
            raise SystemExit(f"--set expects VAR=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        if v.startswith("@"):
            v = _read(v[1:])
        out[k] = v
    return out


# ===========================================================================
# CLI: `sp tools replay ...`
# ===========================================================================

def add_arguments(parser) -> None:
    """Register `replay` flags on the given argparse subparser."""
    parser.add_argument("--request", nargs="+", required=True,
                        help="captured *_request.txt file(s) or glob(s)")
    parser.add_argument("--prompt", required=True,
                        help="original .gpt that generated the request")
    parser.add_argument("--prompt-new", required=True, help="edited .gpt under test")
    parser.add_argument("--set", action="append", dest="set_", metavar="VAR=VALUE",
                        help="supply/override a variable (VAR=VALUE or VAR=@file); repeatable")
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--n", type=int, default=5, help="draws per segment")
    parser.add_argument("--show", default="has_content",
                        help="comma-separated fields to compare (special: sensory, characters)")
    parser.add_argument("--full", action="store_true",
                        help="print full responses, not just the table")


def run(args) -> int:
    """Handler for `sp tools replay`. Schema paths in the prompt frontmatter are
    resolved relative to the current working directory (the project root)."""
    repo_root = Path.cwd()
    fields = [f.strip() for f in args.show.split(",") if f.strip()]
    overrides = _parse_set(args.set_)

    prompt_old = _read(args.prompt)
    prompt_new = _read(args.prompt_new)
    sref = schema_ref(prompt_new) or schema_ref(prompt_old)
    if not sref:
        raise SystemExit("no schema declared in the prompt frontmatter")
    schema = load_schema(sref, repo_root)
    schema_name = Path(sref).stem.replace(".schema", "").replace("-", "_")

    request_files: list[str] = []
    for pat in args.request:
        request_files.extend(sorted(_glob.glob(pat)))
    if not request_files:
        raise SystemExit("no request files matched")

    headers = ["ref"] + [f"{f} (old->new k/n)" for f in fields]
    rows: list[list[str]] = []

    for req in request_files:
        req_text = _read(req)
        var_map = recover_var_map(prompt_old, req_text)
        rendered = render(prompt_new, var_map, overrides)

        resp_file = find_response_file(req)
        old_by_ref = _segments_by_ref(parse_saved_response(_read(resp_file))) if resp_file else {}

        draws = [call_model(rendered, schema, schema_name, args.model, args.temperature)
                 for _ in range(args.n)]
        if args.full:
            print(f"\n===== {req} =====")
            for i, d in enumerate(draws):
                print(f"--- draw {i+1} ---\n{json.dumps(d, ensure_ascii=False, indent=2)}")

        new_by_ref: dict[str, list[dict]] = {}
        for d in draws:
            for ref, seg in _segments_by_ref(d).items():
                new_by_ref.setdefault(ref, []).append(summarize_segment(seg, fields))

        for ref in new_by_ref:
            old = summarize_segment(old_by_ref[ref], fields) if ref in old_by_ref else {}
            cells = [ref]
            for f in fields:
                news = [s.get(f) for s in new_by_ref[ref]]
                top = max(set(map(str, news)), key=lambda v: list(map(str, news)).count(v))
                k = list(map(str, news)).count(top)
                cells.append(f"{old.get(f)}->{top} {k}/{len(news)}")
            rows.append(cells)

    print(format_table(headers, rows))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Standalone entry point (`python -m llmflow.tools.replay ...`)."""
    import argparse
    ap = argparse.ArgumentParser(
        prog="sp tools replay",
        description="Replay a prompt change against captured debug requests.")
    add_arguments(ap)
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
