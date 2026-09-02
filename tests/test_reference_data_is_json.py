"""Guardrail: YAML this project loads must not hold scalars PyYAML silently retypes.

PyYAML resolves a bare `1:1` as a base-60 integer — `61` — and a bare `NO` as `False`. Both
happen with no error, and `61` is a plausible verse number, so a corrupted reference survives
review. Rule `reference-data-is-json` is the response: reference data is JSON, and YAML that
must carry such a scalar quotes it and says why the quotes are load-bearing.

The check asks PyYAML itself rather than matching the file text. Composing a document yields
nodes carrying both the original scalar text and the tag the resolver chose, so a coercion is
visible as a disagreement between the two:

    1:1   -> tag int,  raw '1:1'    coerced
    "1:1" -> tag str,  raw '1:1'    quoted, safe
    61    -> tag int,  raw '61'     a genuine number
    NO    -> tag bool, raw 'NO'     coerced
    false -> tag bool, raw 'false'  written as a boolean

**Scope is the YAML this codebase loads.** `.github/workflows/*.yml` are parsed by GitHub, not
by us, and their `on:` key resolves to `True` under PyYAML — a coercion that is correct there
and would be noise here.

Convention: rule `reference-data-is-json`.
"""
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Directories holding YAML that this codebase reads with PyYAML.
LOADED_YAML_DIRS = (
    REPO_ROOT / "data",
    REPO_ROOT / "pipelines",
    REPO_ROOT / "src" / "llmflow" / "templates",
)

INT_TAG = "tag:yaml.org,2002:int"
FLOAT_TAG = "tag:yaml.org,2002:float"
BOOL_TAG = "tag:yaml.org,2002:bool"

#: Both numeric tags, because the base-60 reading is not confined to integers: `1:1` becomes
#: the integer 61 and `1:30.5` becomes the float 90.5. Measured against PyYAML.
NUMERIC_TAGS = (INT_TAG, FLOAT_TAG)

#: The only spellings that mean a boolean and nothing else. Everything else PyYAML calls a
#: bool — `NO`, `yes`, `on`, `off`, `y`, `n` — is a word that happened to resolve.
EXPLICIT_BOOLEANS = {"true", "false"}

YAML_FILES = sorted(
    path
    for directory in LOADED_YAML_DIRS
    if directory.is_dir()
    for path in list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))
    if path.is_file()
)


def _coercions(path: Path) -> list[str]:
    """Scalars whose resolved tag disagrees with how they are written."""
    text = path.read_text(encoding="utf-8")
    try:
        documents = list(yaml.compose_all(text))
    except yaml.YAMLError as error:
        pytest.fail(f"{path.relative_to(REPO_ROOT)} is not loadable YAML: {error}")

    found: list[str] = []

    def walk(node) -> None:
        if isinstance(node, yaml.ScalarNode):
            raw = node.value
            if node.tag in NUMERIC_TAGS and ":" in raw:
                found.append(
                    f"line {node.start_mark.line + 1}: `{raw}` reads as the number "
                    f"{yaml.safe_load(raw)!r}, not as a reference"
                )
            elif node.tag == BOOL_TAG and raw.lower() not in EXPLICIT_BOOLEANS:
                found.append(
                    f"line {node.start_mark.line + 1}: `{raw}` reads as the boolean "
                    f"{yaml.safe_load(raw)!r}, not as the word it looks like"
                )
        elif isinstance(node, yaml.SequenceNode):
            for child in node.value:
                walk(child)
        elif isinstance(node, yaml.MappingNode):
            for key, value in node.value:
                walk(key)
                walk(value)

    for document in documents:
        if document is not None:
            walk(document)
    return found


def test_the_check_recognises_a_coercion():
    """Without this, an empty scan would look like a clean one."""
    probe = (
        "opening: 1:1\n"          # int 61
        "midverse: 1:30.5\n"      # float 90.5 — the same trap, not confined to integers
        "flag: NO\n"              # False
        "safe_ref: \"1:1\"\n"     # quoted, a string
        "safe_bool: false\n"      # written as a boolean
        "count: 61\n"             # a genuine number
        "temperature: 0.7\n"      # a genuine float
    )
    nodes = list(yaml.compose_all(probe))
    assert nodes, "the probe composed nothing"

    coerced = []
    for key, value in nodes[0].value:
        if value.tag in NUMERIC_TAGS and ":" in value.value:
            coerced.append(key.value)
        elif value.tag == BOOL_TAG and value.value.lower() not in EXPLICIT_BOOLEANS:
            coerced.append(key.value)
    assert coerced == ["opening", "midverse", "flag"], coerced


def test_yaml_files_exist():
    assert YAML_FILES, f"no YAML found under {[str(d) for d in LOADED_YAML_DIRS]}"


@pytest.mark.parametrize("path", YAML_FILES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_loaded_yaml_holds_a_retyped_scalar(path):
    coercions = _coercions(path)
    assert not coercions, (
        f"{path.relative_to(REPO_ROOT)} holds scalars PyYAML retypes, against rule "
        f"`reference-data-is-json`:\n"
        + "\n".join(f"   {c}" for c in coercions)
        + "\n   Quote the scalar and say in a comment why the quotes are load-bearing, or move "
        "the data to JSON. The coercion is silent, and an integer like 61 is a plausible verse "
        "number."
    )
