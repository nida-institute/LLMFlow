"""Extended tests for src/llmflow/utils/io.py — uncovered functions.

test_template_comprehensive.py already covers eval_template_expr and
render_template, so this file focuses on the functions that remain uncovered:
render_markdown_template, validate_template, validate_all_templates,
save_markdown_as, save_xml, save_text, extract_pipeline_variables,
extract_interleave_fields, and validate_template_structure.
"""

import pytest
from pathlib import Path

from llmflow.utils.io import (
    render_markdown_template,
    validate_template,
    validate_all_templates,
    save_markdown_as,
    save_xml,
    save_text,
    extract_pipeline_variables,
    extract_pipeline_variables_at_step,
    extract_interleave_fields,
    validate_template_structure,
    extract_template_variables,
)


# ---------------------------------------------------------------------------
# render_markdown_template
# ---------------------------------------------------------------------------

class TestRenderMarkdownTemplate:

    def test_simple_curly_substitution(self, tmp_path):
        tmpl = tmp_path / "test.md"
        tmpl.write_text("Hello {{name}}!", encoding="utf-8")

        result = render_markdown_template(str(tmpl), {"name": "World"})

        assert result == "Hello World!"

    def test_multiple_variables(self, tmp_path):
        tmpl = tmp_path / "test.md"
        tmpl.write_text("{{greeting}}, {{name}}!", encoding="utf-8")

        result = render_markdown_template(str(tmpl), {"greeting": "Hi", "name": "Alice"})

        assert result == "Hi, Alice!"

    def test_missing_variable_leaves_placeholder(self, tmp_path):
        tmpl = tmp_path / "test.md"
        tmpl.write_text("Hello {{missing}}!", encoding="utf-8")

        result = render_markdown_template(str(tmpl), {})

        assert "{{missing}}" in result

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            render_markdown_template("/nonexistent/path/template.md", {})

    def test_no_placeholders_returns_content_unchanged(self, tmp_path):
        tmpl = tmp_path / "test.md"
        tmpl.write_text("Just plain text.", encoding="utf-8")

        result = render_markdown_template(str(tmpl), {})

        assert result == "Just plain text."


# ---------------------------------------------------------------------------
# extract_template_variables
# ---------------------------------------------------------------------------

class TestExtractTemplateVariables:

    def test_curly_variable(self):
        vars_ = extract_template_variables("Hello {{name}}!")
        assert "name" in vars_

    def test_dollar_variable(self):
        vars_ = extract_template_variables("Value: ${key}")
        assert "key" in vars_

    def test_mixed_syntax(self):
        vars_ = extract_template_variables("{{a}} and ${b}")
        assert "a" in vars_
        assert "b" in vars_

    def test_no_variables(self):
        vars_ = extract_template_variables("No placeholders here.")
        assert vars_ == set()


# ---------------------------------------------------------------------------
# validate_template
# ---------------------------------------------------------------------------

class TestValidateTemplate:

    def test_existing_template_is_valid(self, tmp_path):
        tmpl = tmp_path / "t.md"
        tmpl.write_text("{{passage}}", encoding="utf-8")

        is_valid, missing, extra = validate_template(str(tmpl))

        assert is_valid is True

    def test_missing_file_returns_invalid(self):
        is_valid, missing, extra = validate_template("/nonexistent/t.md")
        assert is_valid is False

    def test_missing_required_variable_detected(self, tmp_path):
        tmpl = tmp_path / "t.md"
        tmpl.write_text("{{passage}}", encoding="utf-8")

        is_valid, missing, extra = validate_template(str(tmpl), required_variables=["passage", "source"])

        assert is_valid is False
        assert "source" in missing

    def test_extra_variables_reported(self, tmp_path):
        tmpl = tmp_path / "t.md"
        tmpl.write_text("{{passage}} {{extra_field}}", encoding="utf-8")

        is_valid, missing, extra = validate_template(str(tmpl), required_variables=["passage"])

        assert is_valid is True
        assert "extra_field" in extra

    def test_all_required_present_is_valid(self, tmp_path):
        tmpl = tmp_path / "t.md"
        tmpl.write_text("{{a}} {{b}}", encoding="utf-8")

        is_valid, missing, extra = validate_template(str(tmpl), required_variables=["a", "b"])

        assert is_valid is True
        assert missing == []


# ---------------------------------------------------------------------------
# validate_all_templates
# ---------------------------------------------------------------------------

class TestValidateAllTemplates:

    def test_pipeline_with_no_templates_passes(self):
        pipeline = {
            "steps": [
                {"name": "step1", "type": "llm"}
            ]
        }
        # Should not raise
        validate_all_templates(pipeline)

    def test_pipeline_with_valid_template_passes(self, tmp_path):
        tmpl = tmp_path / "t.md"
        tmpl.write_text("{{passage}}", encoding="utf-8")

        pipeline = {
            "steps": [
                {
                    "name": "render_step",
                    "type": "function",
                    "inputs": {"template_path": str(tmpl)},
                }
            ]
        }
        validate_all_templates(pipeline)  # Should not raise

    def test_pipeline_with_missing_template_raises(self):
        pipeline = {
            "steps": [
                {
                    "name": "bad_step",
                    "type": "function",
                    "inputs": {"template_path": "/nonexistent/template.md"},
                }
            ]
        }
        with pytest.raises(ValueError, match="Template validation failed"):
            validate_all_templates(pipeline)

    def test_foreach_steps_are_checked_recursively(self, tmp_path):
        bad_tmpl = tmp_path / "missing.md"
        # Don't create the file

        pipeline = {
            "steps": [
                {
                    "name": "loop",
                    "type": "for-each",
                    "steps": [
                        {
                            "name": "inner",
                            "type": "function",
                            "inputs": {"template_path": str(bad_tmpl)},
                        }
                    ],
                }
            ]
        }
        with pytest.raises(ValueError, match="Template validation failed"):
            validate_all_templates(pipeline)


# ---------------------------------------------------------------------------
# save_markdown_as / save_xml / save_text
# ---------------------------------------------------------------------------

class TestSaveFunctions:

    def test_save_markdown_as_md(self, tmp_path):
        path = save_markdown_as("# Hello", "passage_one", format="md", output_dir=str(tmp_path))
        assert Path(path).exists()
        assert path.endswith(".md")

    def test_save_markdown_as_html(self, tmp_path):
        path = save_markdown_as("# Hello", "passage_one", format="html", output_dir=str(tmp_path))
        assert Path(path).exists()
        assert path.endswith(".html")
        content = Path(path).read_text()
        assert "<h1>" in content

    def test_save_markdown_as_invalid_format_raises(self, tmp_path):
        with pytest.raises(ValueError):
            save_markdown_as("text", "p", format="pdf", output_dir=str(tmp_path))

    def test_save_xml(self, tmp_path):
        path = save_xml("<root/>", "entry_one", output_dir=str(tmp_path))
        assert Path(path).exists()
        assert path.endswith(".xml")
        assert "<root/>" in Path(path).read_text()

    def test_save_text(self, tmp_path):
        out = tmp_path / "out.txt"
        path = save_text("content here", str(out))
        assert Path(path).exists()
        assert Path(path).read_text() == "content here"


# ---------------------------------------------------------------------------
# extract_pipeline_variables / extract_pipeline_variables_at_step
# ---------------------------------------------------------------------------

class TestExtractPipelineVariables:

    PIPELINE = {
        "variables": {"passage": "John 3:16", "lang": "en"},
        "steps": [
            {"name": "step1", "type": "llm", "outputs": ["result1"]},
            {"name": "step2", "type": "llm", "outputs": ["result2"]},
        ],
    }

    def test_includes_global_variables(self):
        avail = extract_pipeline_variables(self.PIPELINE)
        assert "passage" in avail
        assert "lang" in avail

    def test_includes_step_outputs(self):
        avail = extract_pipeline_variables(self.PIPELINE)
        assert "result1" in avail
        assert "result2" in avail

    def test_at_step_excludes_later_outputs(self):
        avail = extract_pipeline_variables_at_step(self.PIPELINE, "step2")
        assert "result1" in avail
        assert "result2" not in avail  # step2's own output not yet available

    def test_at_step_includes_globals(self):
        avail = extract_pipeline_variables_at_step(self.PIPELINE, "step1")
        assert "passage" in avail


# ---------------------------------------------------------------------------
# extract_interleave_fields
# ---------------------------------------------------------------------------

class TestExtractInterleaveFields:

    def test_no_interleave_returns_empty(self):
        pipeline = {"steps": [{"name": "s", "inputs": {"variables": {"x": "static"}}}]}
        result = extract_interleave_fields(pipeline)
        assert result == {}

    def test_interleave_fields_extracted(self):
        pipeline = {
            "steps": [
                {
                    "name": "s",
                    "inputs": {
                        "variables": {
                            "rows": {
                                "interleave": {
                                    "col_a": "${a}",
                                    "col_b": "${b}",
                                }
                            }
                        }
                    },
                }
            ]
        }
        result = extract_interleave_fields(pipeline)
        assert "rows" in result
        assert "col_a" in result["rows"]
        assert "col_b" in result["rows"]


# ---------------------------------------------------------------------------
# validate_template_structure
# ---------------------------------------------------------------------------

class TestValidateTemplateStructure:

    def test_template_vars_match_step_inputs(self, tmp_path):
        tmpl = tmp_path / "t.md"
        tmpl.write_text("{{passage}} {{lang}}", encoding="utf-8")

        pipeline = {
            "variables": {},
            "steps": [
                {
                    "name": "render",
                    "type": "function",
                    "inputs": {"variables": {"passage": "John 1:1", "lang": "en"}},
                }
            ],
        }

        result = validate_template_structure(str(tmpl), pipeline, "render")
        assert result["valid"] is True
        assert len(result["missing_vars"]) == 0

    def test_missing_template_vars_detected(self, tmp_path):
        tmpl = tmp_path / "t.md"
        tmpl.write_text("{{passage}} {{source}}", encoding="utf-8")

        pipeline = {
            "variables": {},
            "steps": [
                {
                    "name": "render",
                    "type": "function",
                    "inputs": {"variables": {"passage": "John 1:1"}},  # source missing
                }
            ],
        }

        result = validate_template_structure(str(tmpl), pipeline, "render")
        assert result["valid"] is False
        assert "source" in result["missing_vars"]
