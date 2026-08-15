"""Check a structured-output JSON Schema before the run, not after the bill (LLMFlow#196).

Under ``strict: true`` OpenAI accepts only a restricted subset of JSON Schema and rejects
anything outside it with **HTTP 400 at request time**. Without this check a pipeline passes
every validation we have, runs, fetches its passage, completes several steps, and then dies
on a provider error naming a JSON path rather than a line in the YAML — with the earlier
steps already paid for.

The engine already refuses to spend tokens on a prompt whose contract cannot be satisfied.
This is the same promise for the other half of the same request.

Design notes, all deliberate:

* **Pure.** No network, no provider client, no API key. It cannot itself cost anything, and
  it is cheap to test.
* **Hard rules are errors; keyword and size limits are warnings.** OpenAI has widened the
  accepted subset several times. An error on a keyword the provider has since accepted
  would block work that is fine, so the moving parts warn and the stable parts fail.
* **The rule table is data, and it is dated.** When the provider moves, one table changes.
  Spreading these rules across a dozen ``if`` statements is how a checker goes quietly wrong.

See project/plans/design-structured-output-preflight.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# --------------------------------------------------------------------------------------
# The rule table. One place to edit when the provider moves.
# --------------------------------------------------------------------------------------

RULES_LAST_VERIFIED = "2026-08-15"
RULES_DOC_URL = "https://platform.openai.com/docs/guides/structured-outputs"

#: Keywords the strict subset has historically rejected. Warnings, not errors — several of
#: these have been added to the supported set over time, and a stale entry must not block
#: work the provider would accept.
UNSUPPORTED_KEYWORDS = {
    "allOf": "not supported under strict mode; inline the combined shape",
    "not": "not supported under strict mode",
    "if": "conditional subschemas are not supported under strict mode",
    "then": "conditional subschemas are not supported under strict mode",
    "else": "conditional subschemas are not supported under strict mode",
    "dependentRequired": "not supported under strict mode",
    "dependentSchemas": "not supported under strict mode",
    "patternProperties": "not supported under strict mode",
    "propertyNames": "not supported under strict mode",
    "unevaluatedProperties": "not supported under strict mode",
    "unevaluatedItems": "not supported under strict mode",
    "contains": "not supported under strict mode",
    "default": "ignored under strict mode — every property is required anyway",
}

#: Keywords accepted but with a better spelling under strict mode.
DISCOURAGED_KEYWORDS = {
    "oneOf": ("use anyOf — strict mode supports anyOf, and oneOf's "
              "exactly-one semantics are not enforced"),
}

#: Structural limits. Deliberately the *permissive* published figures: warning on something
#: the provider accepts is noise, and this table will drift.
MAX_NESTING_DEPTH = 10
MAX_TOTAL_PROPERTIES = 5000


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    """One problem with a schema, located and explained."""

    severity: Severity
    path: str
    message: str
    fix: str = ""

    def __str__(self) -> str:
        where = self.path or "(root)"
        out = f"{where}: {self.message}"
        if self.fix:
            out += f"\n    Fix: {self.fix}"
        return out


@dataclass
class _Walk:
    """Mutable state for one traversal."""

    root: Any
    findings: list[Finding] = field(default_factory=list)
    seen: set[int] = field(default_factory=set)
    property_count: int = 0
    max_depth: int = 0


def check_strict_schema(schema: Any, *, path: str = "") -> list[Finding]:
    """Check *schema* against OpenAI's strict structured-output subset.

    Returns findings in document order. An empty list means nothing was detected — not that
    the provider is guaranteed to accept it, since the published subset moves.
    """
    walk = _Walk(root=schema)

    if not isinstance(schema, dict):
        return [Finding(Severity.ERROR, path,
                        "schema must be a JSON object",
                        "give the root a 'type: object' schema")]

    if schema.get("type") != "object":
        walk.findings.append(Finding(
            Severity.ERROR, path,
            "the schema root must be an object under strict mode "
            f"(found {schema.get('type') or _describe_root(schema)})",
            "wrap the payload in an object, e.g. {type: object, properties: {result: ...}}",
        ))

    _walk(schema, path, walk, depth=0)

    if walk.property_count > MAX_TOTAL_PROPERTIES:
        walk.findings.append(Finding(
            Severity.WARNING, path,
            f"{walk.property_count} properties in total; the documented limit is "
            f"{MAX_TOTAL_PROPERTIES}",
            "split the response across steps",
        ))
    if walk.max_depth > MAX_NESTING_DEPTH:
        walk.findings.append(Finding(
            Severity.WARNING, path,
            f"nested {walk.max_depth} levels deep; the documented limit is "
            f"{MAX_NESTING_DEPTH}",
            "flatten the shape or split it across steps",
        ))

    return walk.findings


def _describe_root(schema: dict) -> str:
    for combiner in ("anyOf", "oneOf", "allOf"):
        if combiner in schema:
            return combiner
    return "no type"


def _walk(node: Any, path: str, walk: _Walk, depth: int) -> None:
    """Recurse through a schema, collecting findings.

    Cycles are possible and legal — recursive schemas via ``$ref: "#"`` are a documented
    feature — so nodes are visited once by identity.
    """
    if not isinstance(node, dict):
        return

    marker = id(node)
    if marker in walk.seen:
        return
    walk.seen.add(marker)
    walk.max_depth = max(walk.max_depth, depth)

    if "$ref" in node:
        _check_ref(node, path, walk, depth)
        return

    for keyword, why in UNSUPPORTED_KEYWORDS.items():
        if keyword in node:
            walk.findings.append(Finding(
                Severity.WARNING, _join(path, keyword), f"'{keyword}' {why}",
                f"remove '{keyword}' (rule table last verified {RULES_LAST_VERIFIED})",
            ))
    for keyword, why in DISCOURAGED_KEYWORDS.items():
        if keyword in node:
            walk.findings.append(Finding(
                Severity.WARNING, _join(path, keyword), f"'{keyword}': {why}",
                "rename 'oneOf' to 'anyOf'",
            ))

    if node.get("type") == "object" or "properties" in node:
        _check_object(node, path, walk)

    properties = node.get("properties")
    if isinstance(properties, dict):
        walk.property_count += len(properties)
        for name, sub in properties.items():
            _walk(sub, _join(path, f"properties.{name}"), walk, depth + 1)

    items = node.get("items")
    if isinstance(items, dict):
        _walk(items, _join(path, "items"), walk, depth + 1)
    elif isinstance(items, list):
        for i, sub in enumerate(items):
            _walk(sub, _join(path, f"items[{i}]"), walk, depth + 1)

    for combiner in ("anyOf", "oneOf", "allOf"):
        branches = node.get(combiner)
        if isinstance(branches, list):
            for i, sub in enumerate(branches):
                _walk(sub, _join(path, f"{combiner}[{i}]"), walk, depth + 1)

    for defs_key in ("$defs", "definitions"):
        defs = node.get(defs_key)
        if isinstance(defs, dict):
            for name, sub in defs.items():
                _walk(sub, _join(path, f"{defs_key}.{name}"), walk, depth + 1)


def _check_object(node: dict, path: str, walk: _Walk) -> None:
    """The two rules that account for essentially every real strict-mode rejection."""
    properties = node.get("properties")
    if not isinstance(properties, dict):
        return

    if node.get("additionalProperties") is not False:
        walk.findings.append(Finding(
            Severity.ERROR, path,
            "every object must set 'additionalProperties: false' under strict mode",
            "add 'additionalProperties: false' to this object",
        ))

    required = node.get("required")
    required_set = set(required) if isinstance(required, list) else set()
    missing = [name for name in properties if name not in required_set]
    if missing:
        walk.findings.append(Finding(
            Severity.ERROR, path,
            "every property must be listed in 'required' under strict mode. "
            f"Missing: {', '.join(missing)}",
            "add them to 'required'; if a field is genuinely optional, give it a nullable "
            'type — {"type": ["string", "null"]} — and list it in \'required\' anyway',
        ))


def _check_ref(node: dict, path: str, walk: _Walk, depth: int) -> None:
    """Resolve a local ``$ref`` and continue, or report it as dangling."""
    ref = node["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#"):
        walk.findings.append(Finding(
            Severity.ERROR, path,
            f"'$ref' must point inside this document under strict mode (got {ref!r})",
            "inline the schema, or move it into '$defs' in the same document",
        ))
        return

    target: Any = walk.root
    for part in [p for p in ref.lstrip("#").split("/") if p]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(target, dict) and part in target:
            target = target[part]
        else:
            walk.findings.append(Finding(
                Severity.ERROR, path,
                f"'$ref' does not resolve: {ref}",
                "check the path, or add the missing entry to '$defs'",
            ))
            return

    _walk(target, path, walk, depth + 1)


def _join(path: str, part: str) -> str:
    return f"{path}.{part}" if path else part
