"""Text goes to a model, and onto disk, as Unicode — never as `\\uXXXX` escapes or a Python repr.

Measured before this was written: a mapping substituted into a prompt arrived as `str(value)` —
a Python repr, single-quoted, with `None` and `True`, though the prompts call it JSON — and two
writers stored escapes on disk. An escaped Greek letter is six characters where one would do,
and several tokens where one would do. Plan: `project/plans/plan-starter-cost.md` D3.
"""
import json
from types import SimpleNamespace

from llmflow.steps.llm import render_prompt
from llmflow.utils.content_transition import _update_metadata
from llmflow.utils.debug import DebugRecorder

GREEK = {"lemma": "λόγος", "gloss": "word", "rare": None, "verb": True}

HEADER = """---
requires:
  - data
format: Markdown
description: Probe for how a value reaches the model.
---
user: |
  {{data}}
"""


def test_a_mapping_reaches_the_model_as_json(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "probe.gpt").write_text(HEADER, encoding="utf-8")
    rendered = render_prompt("probe.gpt", {"prompts_dir": str(prompts), "data": GREEK})
    body = rendered[rendered.index("{"): rendered.rindex("}") + 1]
    assert json.loads(body) == GREEK, "valid JSON, not a Python repr"
    assert "λόγος" in rendered and "\\u" not in rendered


def test_a_list_reaches_the_model_as_json(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "probe.gpt").write_text(HEADER, encoding="utf-8")
    rendered = render_prompt("probe.gpt", {"prompts_dir": str(prompts), "data": [GREEK]})
    assert json.loads(rendered[rendered.index("["): rendered.rindex("]") + 1]) == [GREEK]


def test_a_string_reaches_the_model_unchanged(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "probe.gpt").write_text(HEADER, encoding="utf-8")
    rendered = render_prompt("probe.gpt", {"prompts_dir": str(prompts), "data": "ἐν ἀρχῇ"})
    assert "ἐν ἀρχῇ" in rendered and '"ἐν ἀρχῇ"' not in rendered


def test_a_debug_response_is_stored_as_unicode(tmp_path):
    recorder = DebugRecorder(tmp_path, enabled=True)
    call = recorder.begin("step")
    written = recorder.save_response(call, GREEK)
    text = (tmp_path / written).read_text(encoding="utf-8") if written else ""
    assert "λόγος" in text and "\\u" not in text


def test_transition_metadata_is_stored_as_unicode(tmp_path):
    config = SimpleNamespace(copy_metadata=False, metadata_fields_to_set={"title": "Λόγος"})
    _update_metadata(tmp_path, "a.md", "draft", tmp_path, config)
    text = (tmp_path / ".metadata.json").read_text(encoding="utf-8")
    assert "Λόγος" in text and "\\u" not in text
