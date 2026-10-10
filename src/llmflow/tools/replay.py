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
    """Recover {var: value} by aligning the original `.gpt` against the rendered request.

    The request is the prompt with each `{{var}}` substituted, so the two are identical
    except at the variable sites. Alignment is on **those sites**, not on lines: one pattern
    over the whole prompt, literals escaped and each variable a capture group, matched with
    `DOTALL`. A value spanning many lines is then no different from one that does not.

    This aligned line-for-line and began by requiring equal line counts, so a variable holding
    multi-line JSON made the request longer than the template and the recovery was refused
    before anything was examined. Reported by a consumer for whom *every* prompt embeds a JSON
    payload, so none of them could be replayed at all (#255) — which left a check their own
    rulings called for unavailable, and a book run per edit as the alternative.

    Raises ValueError if the two do not align, which usually means `prompt` is not the version
    that generated `request`. That refusal is the point and is not relaxed here: a var map
    recovered from the wrong prompt is substituted into an edited prompt and sent to a model,
    where the failure arrives as a plausible answer rather than an error.
    """
    pattern = ""
    seen: set[str] = set()
    last = 0
    previous_end: int | None = None

    for m in _VAR.finditer(prompt):
        literal = prompt[last:m.start()]
        # Two variables with nothing between them: any split of the text is arbitrary, so
        # there is no answer to give rather than a wrong one to guess at.
        if previous_end is not None and not literal:
            raise ValueError(
                f"variables {{{{{m.group(1)}}}}} and the one before it are adjacent, with no "
                f"text separating them. Nothing can say where one value ends and the next "
                f"begins; separate them in the prompt, or supply one with --set."
            )
        pattern += re.escape(literal)
        name = m.group(1)
        if name in seen:
            # The same variable twice holds one value. A backreference says so, and makes a
            # capture that disagrees with the first simply fail to match.
            pattern += f"(?P={name})"
        else:
            seen.add(name)
            # Non-greedy, anchored by the literal that follows and by `fullmatch` at the end.
            pattern += f"(?P<{name}>.*?)"
        last = m.end()
        previous_end = m.end()

    pattern += re.escape(prompt[last:])
    match = re.fullmatch(pattern, request, re.DOTALL)
    if not match:
        raise ValueError(
            "the prompt does not align with the request; is --prompt the version that "
            f"generated --request? ({len(prompt.splitlines())} template lines, "
            f"{len(request.splitlines())} rendered, {len(seen)} variable(s))"
        )
    return {name: value for name, value in match.groupdict().items() if value is not None}


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
    """Locate the saved response paired with a request file.

    Prefers the run manifest, where the pairing is a recorded field (LLMFlow#198). Falls
    back to matching filenames for directories captured before the manifest existed — that
    path strips the timestamp and suffix, globs, sorts, and takes the earliest response at
    or after the request, which is a guess that two steps sharing a prompt file, or a
    retried step, could get wrong.
    """
    p = Path(request_path)

    from llmflow.utils.debug import read_manifest

    for record in read_manifest(p.parent):
        if record.get("request_file") == p.name:
            response = record.get("response_file")
            if not response:
                return None  # recorded, and there genuinely was no response
            resolved = p.parent / response
            return str(resolved) if resolved.exists() else None

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

    from llmflow.utils.llm_runner import resolve_provider_key

    client = OpenAI(api_key=resolve_provider_key("openai"))
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt_text}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    )
    content = resp.choices[0].message.content
    if content is None:
        raise RuntimeError("model returned empty content")
    return json.loads(content)


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
                        help="captured request file(s) or glob(s) — '*-request.txt' from "
                             "0.2.1.24 on, '*_request.txt' for older captures")
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
        # Say what was looked at and what was not. Replay is given a prompt and a capture and
        # never sees the pipeline, so a step's `response_format` is not consulted — and a
        # reader meeting a bare "no schema declared" concludes that is the whole problem, when
        # it may be hiding the real one behind it (#255).
        raise SystemExit(
            "no `schema:` in the frontmatter of either --prompt or --prompt-new.\n"
            "  replay reads the prompt's frontmatter only. A `response_format` on the "
            "pipeline step is NOT consulted:\n"
            "  replay is given a prompt and a capture, and never sees the pipeline.\n"
            "  Add `schema: path/to.schema.json` to the prompt header — harmless, since the "
            "step's response_format still governs a real run.\n"
            "  Reading the step's schema instead would mean replay knowing the pipeline, not "
            "just the prompt: deferred to #243 Part 3."
        )
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
