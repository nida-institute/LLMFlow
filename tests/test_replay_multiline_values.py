"""`recover_var_map` aligns on variable sites, not on line counts (#255).

Reported by `nida-institute/discourse-flow`. A captured request is the `.gpt` with each `{{var}}`
replaced by its value, and the recovery aligned the two **line for line** — so it began by
requiring equal line counts. A variable whose value is multi-line JSON makes the request longer
than the template, and the whole recovery was refused before anything was examined.

**It is not one awkward prompt.** Measured on their side: `segment-book.gpt` is 890 template
lines against 964 rendered, `segments.gpt` 666 against 742, and every prompt in that pipeline
embeds a JSON payload. So no prompt there could be replayed at all. Four rulings in their
segmentation audit said "test with sp replay" and could not be carried out; a 37-rule prompt
change landed untested. The alternative is a book run per edit, which they cost at roughly $22
for Mark — which is the cost replay exists to remove.

**The fix is to align on the variable sites.** One pattern over the whole prompt: literals
escaped, each `{{var}}` a capture group, matched with `DOTALL` against the whole request. A
multi-line value is then no different from a single-line one.

**The non-regression is the point of half these tests.** The old check refused a `--prompt` that
did not generate the capture, and that refusal has to survive — it is what stops a silently wrong
var map being substituted into an edited prompt and sent to a model. It now refuses for a better
reason than a line count.
"""

from __future__ import annotations

import json

import pytest

from llmflow.tools.replay import recover_var_map, render


class TestAMultilineValueIsRecovered:
    def test_a_json_payload_spanning_many_lines(self):
        """The reported case: the request is longer than the template and must still align."""
        prompt = "# Segments\n\n{{segments}}\n\nEnd."
        payload = json.dumps([{"id": n, "text": f"unit {n}"} for n in range(5)], indent=2)
        request = f"# Segments\n\n{payload}\n\nEnd."

        assert request.count("\n") > prompt.count("\n"), "the fixture must exercise the bug"
        assert recover_var_map(prompt, request)["segments"] == payload

    def test_two_multiline_values_in_one_prompt(self):
        prompt = "A:\n{{first}}\nB:\n{{second}}\nend"
        first = "one\ntwo\nthree"
        second = "{\n  \"k\": 1\n}"
        recovered = recover_var_map(prompt, f"A:\n{first}\nB:\n{second}\nend")

        assert recovered["first"] == first
        assert recovered["second"] == second

    def test_a_value_containing_regex_metacharacters(self):
        """Literals are escaped; a value full of metacharacters must not be read as pattern."""
        prompt = "text: {{body}}\nend"
        body = "a.b*c+d?e[f]g(h)i|j\\k^l$m"
        assert recover_var_map(prompt, f"text: {body}\nend")["body"] == body

    def test_a_value_that_is_empty(self):
        """An empty value is a value. `say-which-kind-of-nothing` in miniature."""
        assert recover_var_map("x:{{v}}:y", "x::y")["v"] == ""

    def test_a_variable_at_the_very_end(self):
        """Nothing follows it to anchor against, so the match must run to the end."""
        assert recover_var_map("tail: {{v}}", "tail: one\ntwo")["v"] == "one\ntwo"


class TestTheOldBehaviourSurvives:
    """Single-line recovery worked and must go on working."""

    def test_single_line_values(self):
        prompt = "book {{book}}\n{{source_text}}\nend"
        recovered = recover_var_map(prompt, "book Mark\n⌊1:1⌋ text\nend")
        assert recovered == {"book": "Mark", "source_text": "⌊1:1⌋ text"}

    def test_identical_text_yields_no_vars(self):
        assert recover_var_map("line a\nline b\n", "line a\nline b\n") == {}

    def test_unicode_is_unharmed(self):
        greek = "⌊1:1⌋ Ἀρχὴ τοῦ εὐαγγελίου Ἰησοῦ χριστοῦ"
        assert recover_var_map("## Source\n{{t}}\nend", f"## Source\n{greek}\nend")["t"] == greek


class TestAWrongPromptIsStillRefused:
    """The check must not be turned off, only moved off the line count.

    This is what stops a wrong var map reaching a model. A recovery that accepts anything is
    worse than one that refuses too much, because the failure then arrives as a plausible
    response rather than an error.
    """

    def test_a_prompt_that_did_not_generate_the_request(self):
        with pytest.raises(ValueError) as caught:
            recover_var_map("wholly different text\n{{v}}", "nothing like it at all")
        assert "--prompt" in str(caught.value), "the message must say what is likely wrong"

    def test_a_template_with_no_variables_that_does_not_match(self):
        """No variables to absorb the difference, so the two must simply be equal."""
        with pytest.raises(ValueError):
            recover_var_map("a\nb\nc", "a\nb")

    def test_a_repeated_variable_recovering_two_different_values(self):
        """`{{v}}` twice cannot hold two values; that is a mismatched prompt, not a var map."""
        with pytest.raises(ValueError):
            recover_var_map("{{v}} and {{v}}", "one and two")


class TestCasesTheLineVersionNeverMet:
    def test_the_same_variable_twice_with_one_value(self):
        assert recover_var_map("{{v}} and {{v}}", "same and same")["v"] == "same"

    def test_two_adjacent_variables_are_refused_rather_than_guessed(self):
        """Nothing separates them, so any split is arbitrary. Say so."""
        with pytest.raises(ValueError) as caught:
            recover_var_map("{{a}}{{b}}", "impossible")
        message = str(caught.value).lower()
        assert "adjacent" in message or "separat" in message


class TestRoundTrip:
    def test_a_recovered_multiline_value_renders_back(self):
        """The whole point: recover from a capture, substitute into an edited prompt."""
        prompt = "# Old heading\n{{data}}\nend"
        payload = json.dumps({"a": [1, 2, 3]}, indent=2)
        recovered = recover_var_map(prompt, f"# Old heading\n{payload}\nend")

        assert render("# New heading\n{{data}}\nend", recovered) == (
            f"# New heading\n{payload}\nend"
        )
