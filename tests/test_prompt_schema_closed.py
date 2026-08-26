"""The `prompt` object declares exactly the keys the renderer reads (LLMFlow#197).

`prompt` was `oneOf: [string, object]` with `additionalProperties: true`, so any key was
accepted by the schema and then ignored by `render_prompt()`, which reads only `file` and
`inputs`. A pipeline could validate and then die on `ValueError: Prompt 'file' must be a
string, got <class 'NoneType'>`.

`pipelines/json-schema-example.yaml` hit exactly this: all three steps wrote the prompt
inline as `prompt.template`. That spelling looks plausible because `template` *is* real —
at *step* level, naming a file that formats the model's **output**. Two concepts, one word.

Survey before closing the schema: across every pipeline in every sibling repo, `prompt:`
used only `file` (185 occurrences) and `inputs` (188). The three `template` uses were all
in the broken example. Closing it costs nothing real.
"""
import pytest

from llmflow.pipeline_schema import PIPELINE_SCHEMA


def _validate(step):
    """Validate a one-step pipeline, returning the list of error messages."""
    import jsonschema
    v = jsonschema.Draft7Validator(PIPELINE_SCHEMA)
    return [e.message for e in v.iter_errors({"name": "p", "steps": [step]})]


def _llm_step(**prompt_keys):
    return {"name": "s", "type": "llm", "prompt": dict(**prompt_keys)}


class TestSupportedFormsStillValidate:
    def test_file_and_inputs(self):
        assert _validate(_llm_step(file="p.gpt", inputs={"book": "${book}"})) == []

    def test_file_alone(self):
        assert _validate(_llm_step(file="p.gpt")) == []

    def test_bare_string_path(self):
        assert _validate({"name": "s", "type": "llm", "prompt": "prompts/p.gpt"}) == []


class TestUnsupportedKeysAreRejected:
    def test_inline_template_is_rejected(self):
        """The exact mistake in json-schema-example.yaml."""
        errors = _validate(_llm_step(template="Summarise {{book}}.", inputs={}))
        assert errors, "prompt.template validated, but render_prompt() cannot use it"

    @pytest.mark.parametrize("key", ["text", "content", "body", "prompt", "system"])
    def test_other_plausible_inline_spellings_rejected(self, key):
        assert _validate(_llm_step(**{key: "some text"})), f"prompt.{key} was accepted"

    def test_error_names_the_offending_key(self):
        """A schema error must beat a NoneType at runtime — it has to say what is wrong."""
        errors = _validate(_llm_step(template="x"))
        assert any("template" in e for e in errors), errors


class TestKeysMatchTheRenderer:
    def test_schema_declares_exactly_what_render_prompt_reads(self):
        """Guard against the two drifting apart again.

        `render_prompt()` (steps/llm.py) reads `file` and `inputs` from the dict form and
        nothing else. If a key is added there, add it here deliberately.
        """
        found = _find_prompt_object(PIPELINE_SCHEMA)
        assert found is not None, "could not locate the prompt object schema"
        assert set(found.get("properties", {})) == {"file", "inputs"}
        assert found.get("additionalProperties") is False


def _find_prompt_object(node):
    """Depth-first search for the object branch of the `prompt` property."""
    if isinstance(node, dict):
        if "prompt" in node and isinstance(node["prompt"], dict):
            p = node["prompt"]
            for candidate in p.get("oneOf", []) + p.get("anyOf", []) + [p]:
                if isinstance(candidate, dict) and candidate.get("type") == "object":
                    return candidate
        for v in node.values():
            found = _find_prompt_object(v)
            if found is not None:
                return found
    elif isinstance(node, list):
        for v in node:
            found = _find_prompt_object(v)
            if found is not None:
                return found
    return None
