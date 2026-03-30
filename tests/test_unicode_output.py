"""Tests that all output formats preserve Unicode instead of ASCII-escaping it.

The sentinel string for every test is שָׁלוֹם (shalom with full niqquud).
If any serialization path emits \\u05e9 instead of שׁ the test will catch it.
"""

import json

from llmflow.runner import save_content_to_file


HEBREW       = "שָׁלוֹם"                        # shalom with niqquud
CANTILLATION = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים"  # Genesis 1:1 — niqquud + cantillation (U+0591–U+05AF)
GREEK        = "Χαίρετε"                        # Greek — multi-byte UTF-8
MIXED        = f"{HEBREW} / {CANTILLATION} / {GREEK}"


# ---------------------------------------------------------------------------
# save_content_to_file — JSON format
# ---------------------------------------------------------------------------

def test_json_dict_no_ascii_escaping(tmp_path):
    """save_content_to_file(dict, json) must write literal Hebrew, not \\uXXXX."""
    out = tmp_path / "out.json"
    save_content_to_file({"word": HEBREW, "greeting": GREEK}, str(out), "json")
    raw = out.read_text(encoding="utf-8")
    assert HEBREW in raw, f"Expected שָׁלוֹם in file, got: {raw[:200]}"
    assert "\\u" not in raw, f"Unexpected ASCII-escaped Unicode in JSON output: {raw[:200]}"


def test_json_string_no_ascii_escaping(tmp_path):
    """save_content_to_file(JSON string, json) must re-serialize without ASCII escaping."""
    out = tmp_path / "out.json"
    input_str = json.dumps({"word": HEBREW}, ensure_ascii=False)
    save_content_to_file(input_str, str(out), "json")
    raw = out.read_text(encoding="utf-8")
    assert HEBREW in raw, f"Expected שָׁלוֹם in file, got: {raw[:200]}"
    assert "\\u" not in raw, f"ASCII-escaped Unicode in re-serialized JSON: {raw[:200]}"


def test_json_autodetect_from_extension(tmp_path):
    """A .json path with no explicit format must still avoid ASCII escaping."""
    out = tmp_path / "out.json"
    save_content_to_file({"text": MIXED}, str(out))   # format inferred from extension
    raw = out.read_text(encoding="utf-8")
    assert HEBREW in raw
    assert GREEK in raw
    assert "\\u" not in raw


def test_json_nested_unicode(tmp_path):
    """Nested structures with Unicode at multiple depths must all be preserved."""
    out = tmp_path / "out.json"
    payload = {
        "passage": HEBREW,
        "translations": [GREEK, MIXED],
        "meta": {"source": HEBREW},
    }
    save_content_to_file(payload, str(out), "json")
    raw = out.read_text(encoding="utf-8")
    assert HEBREW in raw
    assert GREEK in raw
    assert "\\u" not in raw


def test_json_cantillation_marks_preserved(tmp_path):
    """Cantillation marks (טעמים, U+0591–U+05AF) must survive JSON serialization intact.

    Cantillation marks sit above/below consonants and are even more obscure than
    niqquud — a naïve ASCII-escape pass turns בְּרֵאשִׁ֖ית into a wall of \\uXXXX.
    """
    out = tmp_path / "out.json"
    save_content_to_file({"verse": CANTILLATION}, str(out), "json")
    raw = out.read_text(encoding="utf-8")
    assert CANTILLATION in raw, f"Cantillation text missing from output: {raw[:300]}"
    assert "\\u" not in raw, f"ASCII-escaped cantillation marks in JSON: {raw[:300]}"


# ---------------------------------------------------------------------------
# save_content_to_file — text format
# ---------------------------------------------------------------------------

def test_text_format_preserves_unicode(tmp_path):
    """Text format must write Unicode as-is, not as escape sequences."""
    out = tmp_path / "out.txt"
    save_content_to_file(MIXED, str(out), "text")
    raw = out.read_text(encoding="utf-8")
    assert HEBREW in raw
    assert GREEK in raw


def test_text_autodetect_preserves_unicode(tmp_path):
    """Non-.json extension with no format arg must preserve Unicode."""
    out = tmp_path / "out.txt"
    save_content_to_file(MIXED, str(out))
    raw = out.read_text(encoding="utf-8")
    assert HEBREW in raw


# ---------------------------------------------------------------------------
# Registry YAML — must not emit \\uXXXX escape sequences
# ---------------------------------------------------------------------------

def test_registry_project_yaml_allow_unicode(tmp_path):
    """ProjectRegistry.register() must write Unicode descriptions without \\uXXXX escaping."""
    from llmflow.registry import ProjectRegistry

    reg = ProjectRegistry(tmp_path)
    reg.register("test-proj", path=str(tmp_path), description=MIXED)

    yaml_file = tmp_path / "projects" / "test-proj.yaml"
    raw = yaml_file.read_text(encoding="utf-8")
    assert HEBREW in raw, f"Hebrew missing from registry YAML: {raw}"
    assert CANTILLATION in raw, f"Cantillation missing from registry YAML: {raw}"
    assert "\\u" not in raw, f"ASCII-escaped Unicode in registry YAML: {raw}"
