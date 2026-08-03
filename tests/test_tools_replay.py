"""Tests for `llmflow.tools.replay` — the deterministic core of `sp tools replay`.

Ported from the scriptorium project's tests/test_replay_prompt.py. The LLM call
itself is not unit-tested (hits the API, nondeterministic); these cover the pure
parts: template inversion, substitution, schema-ref parsing, field summarizing,
response pairing, and table formatting.
"""

import pytest

from llmflow.tools.replay import (
    recover_var_map,
    render,
    schema_ref,
    summarize_segment,
    pairing_stem,
    parse_saved_response,
    format_table,
)


# ---------------------------------------------------------------------------
# recover_var_map: original .gpt + rendered request -> {var: value}
# ---------------------------------------------------------------------------

class TestRecoverVarMap:
    def test_whole_line_block_var(self):
        prompt = "intro\n{{scene}}\noutro"
        request = "intro\n{'id': 'MRK 1:1'}\noutro"
        assert recover_var_map(prompt, request) == {"scene": "{'id': 'MRK 1:1'}"}

    def test_inline_var_prefix_suffix(self):
        prompt = "You are working in the book of {{book}}."
        request = "You are working in the book of Mark."
        assert recover_var_map(prompt, request)["book"] == "Mark"

    def test_same_var_twice_consistent(self):
        prompt = "book of {{book}}.\nanalysis of {{book}}:"
        request = "book of Mark.\nanalysis of Mark:"
        assert recover_var_map(prompt, request) == {"book": "Mark"}

    def test_multiple_distinct_vars(self):
        prompt = "book {{book}}\n{{source_text}}\nend"
        request = "book Mark\n⌊1:1⌋ text\nend"
        m = recover_var_map(prompt, request)
        assert m["book"] == "Mark"
        assert m["source_text"] == "⌊1:1⌋ text"

    def test_identical_lines_yield_no_vars(self):
        prompt = "line a\nline b\n"
        request = "line a\nline b\n"
        assert recover_var_map(prompt, request) == {}

    def test_unicode_greek_value(self):
        prompt = "## Source text\n{{source_text}}\nend"
        greek = "⌊1:1⌋ Ἀρχὴ τοῦ εὐαγγελίου Ἰησοῦ χριστοῦ"
        request = f"## Source text\n{greek}\nend"
        assert recover_var_map(prompt, request)["source_text"] == greek

    def test_line_count_mismatch_raises(self):
        with pytest.raises(ValueError):
            recover_var_map("a\nb\nc", "a\nb")


# ---------------------------------------------------------------------------
# render: substitute var_map (+ overrides) into edited prompt
# ---------------------------------------------------------------------------

class TestRender:
    def test_basic_substitution(self):
        assert render("book of {{book}}.", {"book": "Mark"}) == "book of Mark."

    def test_override_beats_recovered(self):
        out = render("p {{primary_participants}}",
                     {"primary_participants": "['Implied Audience']"},
                     overrides={"primary_participants": "[]"})
        assert out == "p []"

    def test_override_supplies_var_absent_from_map(self):
        out = render("names: {{primary_participants}}",
                     {},
                     overrides={"primary_participants": "['Jesus']"})
        assert out == "names: ['Jesus']"

    def test_unresolved_var_raises(self):
        with pytest.raises(Exception):
            render("dangling {{mystery}}", {"book": "Mark"})

    def test_new_prompt_may_drop_a_var(self):
        out = render("only {{book}} here", {"book": "Mark", "scene": "{...}"})
        assert out == "only Mark here"


# ---------------------------------------------------------------------------
# schema_ref: read schema path from frontmatter
# ---------------------------------------------------------------------------

class TestSchemaRef:
    def test_reads_schema_path(self):
        prompt = (
            "---\n"
            "prompt:\n"
            "  format: JSON\n"
            "  schema: schemas/scene-bodies.schema.json\n"
            "---\n\nbody\n"
        )
        assert schema_ref(prompt) == "schemas/scene-bodies.schema.json"

    def test_no_schema_returns_none(self):
        prompt = "---\nprompt:\n  format: JSON\n---\nbody\n"
        assert schema_ref(prompt) is None


# ---------------------------------------------------------------------------
# summarize_segment: extract the semantic fields we compare on
# ---------------------------------------------------------------------------

class TestSummarizeSegment:
    def test_bodies_fields(self):
        seg = {
            "canonical_reference": "Mark 1:1",
            "has_content": False,
            "sensory_inventory": [],
            "background": [{"id": "BG-1"}],
        }
        s = summarize_segment(seg, ["has_content", "sensory"])
        assert s["has_content"] is False
        assert s["sensory"] == 0

    def test_hearts_fields_character_names(self):
        seg = {
            "canonical_reference": "Mark 1:4-5",
            "has_content": True,
            "characters": [{"character": "John"}, {"character": "The crowds"}],
        }
        s = summarize_segment(seg, ["has_content", "characters"])
        assert s["has_content"] is True
        assert s["characters"] == ["John", "The crowds"]

    def test_arbitrary_field_read_verbatim(self):
        seg = {"canonical_reference": "Mark 2:1", "custom_flag": "yes"}
        assert summarize_segment(seg, ["custom_flag"])["custom_flag"] == "yes"


# ---------------------------------------------------------------------------
# pairing_stem: pair a request file with its saved response (timestamps differ)
# ---------------------------------------------------------------------------

class TestPairingStem:
    def test_request_and_response_share_stem(self):
        req = "2026-07-07-124717_scene_bodies_lvl1_pericope_section-_id_MRK_16_14_20_canonical_reference_M_request.txt"
        resp = "2026-07-07-124748_scene_bodies_lvl1_pericope_section-_id_MRK_16_14_20_canonical_reference_M_response.txt"
        assert pairing_stem(req) == pairing_stem(resp)

    def test_stem_strips_timestamp_and_suffix(self):
        req = "2026-07-07-124717_scene_bodies_lvl1_MRK_1_1_request.txt"
        assert pairing_stem(req) == "scene_bodies_lvl1_MRK_1_1"

    def test_different_pericopes_differ(self):
        a = "2026-07-07-124717_scene_bodies_MRK_16_14_20_request.txt"
        b = "2026-07-07-124600_scene_bodies_MRK_16_9_11_request.txt"
        assert pairing_stem(a) != pairing_stem(b)


# ---------------------------------------------------------------------------
# parse_saved_response: saved debug responses are Python-dict reprs, not JSON
# ---------------------------------------------------------------------------

class TestParseSavedResponse:
    def test_parses_python_repr_with_true_and_none(self):
        text = "{'segments': [{'canonical_reference': 'Mark 1:1', 'has_content': True, 'sensory_inventory': [], 'background': [], 'acai_id': None}]}"
        obj = parse_saved_response(text)
        assert obj["segments"][0]["has_content"] is True
        assert obj["segments"][0]["sensory_inventory"] == []

    def test_parses_json_too(self):
        text = '{"segments": [{"canonical_reference": "Mark 1:1", "has_content": false}]}'
        obj = parse_saved_response(text)
        assert obj["segments"][0]["has_content"] is False


# ---------------------------------------------------------------------------
# format_table: aligned columns for the batch summary
# ---------------------------------------------------------------------------

class TestFormatTable:
    def test_aligns_columns(self):
        out = format_table(
            ["ref", "has_content"],
            [["Mark 1:1", "true -> false"], ["Mark 1:4-5", "true -> true"]],
        )
        lines = out.splitlines()
        assert "ref" in lines[0] and "has_content" in lines[0]
        assert any("Mark 1:1" in ln for ln in lines)
        assert any("Mark 1:4-5" in ln for ln in lines)
