"""Output templates tolerate whitespace inside {{ }}, like prompt templates do.

`render_markdown_template()` built its placeholder by string formatting —
`f"{{{{{key}}}}}"`, i.e. exactly `{{content}}` — and replaced it literally. So
`{{ content }}` with spaces never matched. It did not warn: the literal text landed in
the rendered deliverable, which is worse than an error, because the run reports success
and the wrong file is written.

The other renderer, `render_template()`, uses `\\{\\{\\s*([^\\}]+?)\\s*\\}\\}` and has always
accepted spaces — so the same spelling behaved differently depending on which template
it was in.

Unknown placeholders are still left untouched, as before: a template may legitimately
contain literal braces, and silently blanking them would be a different kind of wrong.
"""
import pytest

from llmflow.utils.io import render_markdown_template


@pytest.fixture
def render(tmp_path):
    def _render(body, variables, context=None):
        p = tmp_path / "t.md"
        p.write_text(body, encoding="utf-8")
        return render_markdown_template(str(p), variables, context)
    return _render


class TestWhitespaceTolerance:
    @pytest.mark.parametrize("placeholder", [
        "{{content}}",
        "{{ content }}",
        "{{  content  }}",
        "{{\tcontent\t}}",
    ])
    def test_spacing_variants_all_substitute(self, render, placeholder):
        out = render(f"Body: {placeholder}", {"content": "RESULT"})
        assert out == "Body: RESULT", f"{placeholder!r} did not substitute"

    def test_matches_the_prompt_renderer(self, render):
        """The two renderers must agree on the same spelling."""
        from llmflow.utils.io import render_template
        body = "{{ book }} / {{book}}"
        variables = {"book": "Mark"}
        assert render(body, variables) == render_template(body, variables) == "Mark / Mark"


class TestUnchangedBehaviour:
    def test_unknown_placeholder_is_left_alone(self, render):
        out = render("keep {{not_a_variable}} intact", {"content": "x"})
        assert "{{not_a_variable}}" in out

    def test_dollar_syntax_still_resolves_with_context(self, render):
        out = render("ref ${scene.Citation}", {"content": "x"},
                     {"scene": {"Citation": "Mark 1:1"}})
        assert out == "ref Mark 1:1"

    def test_content_and_context_together(self, render):
        out = render("# {{ book }}\n\n{{content}}", {"book": "Mark", "content": "Body."})
        assert out == "# Mark\n\nBody."

    def test_value_containing_braces_is_not_re_expanded(self, render):
        """A substituted value must not itself be scanned for placeholders."""
        out = render("{{content}}", {"content": "{{book}}", "book": "Mark"})
        assert out == "{{book}}"
