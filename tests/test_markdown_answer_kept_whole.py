"""A text answer reaches the pipeline whole: only a fence around all of it is taken off.

Every model answer went through the cleaner written for JSON, which returns the first fenced
block, or failing that the first balanced `[...]` or `{...}`. For a markdown answer that threw
the answer away: in a run of hebrew-poetry-features on Psalm 23, six of seven reviews were saved
as `[x]` (the first ticked checkbox), a revision as `[X.X]` (a score placeholder), and two drafts
as the contents of their first fenced block. JSON is still dug out of prose, by the JSON parser.
"""

from unittest.mock import Mock

from llmflow.modules.json_parser import parse_llm_json_response
from llmflow.utils.llm_runner import _call_model

REVIEW = """# Step 1 Review: Context and Setting

## Checklist

- [x] The historical setting is named.
- [ ] The canonical setting is named.

| Criterion | Score |
|---|---|
| **OVERALL** | [X.X] |
"""

DRAFT = """# Step 7: Synthesis

The psalm moves in three acts:

```
ACT I (vv1-3): SHEPHERDING CARE
ACT II (v4): CONFIDENCE IN DANGER
```

## Translation brief

Keep the shepherd image.
"""


def _answer(text: str) -> str:
    model = Mock()
    model.prompt.return_value.text.return_value = text
    return _call_model(model, "prompt", {})["content"]


def test_a_checklist_answer_is_kept_whole():
    assert _answer(REVIEW) == REVIEW.strip()


def test_a_fenced_block_inside_an_answer_does_not_replace_it():
    assert _answer(DRAFT) == DRAFT.strip()


def test_a_fence_around_the_whole_answer_is_taken_off():
    assert _answer("```markdown\n" + REVIEW + "```") == REVIEW.strip()


def test_a_markdown_fence_around_a_document_with_a_diagram_is_taken_off():
    # The Psalm 23 synthesis came back like this once the answer was no longer cut down.
    assert _answer("```markdown\n" + DRAFT + "```") == DRAFT.strip()


def test_two_separate_blocks_at_either_end_are_left_alone():
    two = "```\nfirst block\n```\n\nProse between.\n\n```\nsecond block\n```"
    assert _answer(two) == two


def test_json_in_prose_is_still_found_by_the_json_parser():
    assert parse_llm_json_response(_answer('Here it is:\n```json\n{"text": "x"}\n```\nDone.')) == {"text": "x"}
