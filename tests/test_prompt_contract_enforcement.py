"""Test that render_prompt() enforces prompt contracts at runtime."""

import pytest
from pathlib import Path
from llmflow.runner import render_prompt


class TestPromptContractEnforcement:
    """Tests for runtime prompt contract enforcement."""

    def test_undeclared_variable_raises_error(self, tmp_path):
        """Using {{variable}} not in header should raise ValueError."""
        prompt_file = tmp_path / "prompts" / "test.gpt"
        prompt_file.parent.mkdir()

        # Prompt uses {{name}} but only declares {{passage}} in header
        prompt_file.write_text("""---
prompt:
  requires:
    - passage
  optional: []
---

Analyze {{passage}} for {{name}}.
""")

        context = {
            "prompts_dir": str(tmp_path / "prompts"),
            "passage": "John 3:16",
            "name": "John"  # Variable present in context but not declared
        }

        with pytest.raises(ValueError) as exc_info:
            render_prompt({"file": "test.gpt"}, context)

        assert "Prompt contract violation" in str(exc_info.value)
        assert "name" in str(exc_info.value)
        assert "not declared in header" in str(exc_info.value)

    def test_missing_required_variable_raises_error(self, tmp_path):
        """Required variable missing from context should raise ValueError."""
        prompt_file = tmp_path / "prompts" / "test.gpt"
        prompt_file.parent.mkdir()

        prompt_file.write_text("""---
prompt:
  requires:
    - passage
    - source
---

Analyze {{passage}} from {{source}}.
""")

        context = {
            "prompts_dir": str(tmp_path / "prompts"),
            "passage": "John 3:16"
            # source is missing!
        }

        with pytest.raises(ValueError) as exc_info:
            render_prompt({"file": "test.gpt"}, context)

        assert "Prompt contract violation" in str(exc_info.value)
        assert "source" in str(exc_info.value)
        assert "Required variables missing" in str(exc_info.value)

    def test_declared_variables_work_correctly(self, tmp_path):
        """Variables declared in header should be substituted correctly."""
        prompt_file = tmp_path / "prompts" / "test.gpt"
        prompt_file.parent.mkdir()

        prompt_file.write_text("""---
prompt:
  requires:
    - passage
  optional:
    - source
---

Analyze {{passage}} from {{source}}.
""")

        context = {
            "prompts_dir": str(tmp_path / "prompts"),
            "passage": "John 3:16",
            "source": "ESV"
        }

        result = render_prompt({"file": "test.gpt"}, context)

        assert "John 3:16" in result
        assert "ESV" in result
        assert "{{passage}}" not in result
        assert "{{source}}" not in result

    def test_optional_variable_can_be_missing(self, tmp_path):
        """Optional variables should not raise error if missing."""
        prompt_file = tmp_path / "prompts" / "test.gpt"
        prompt_file.parent.mkdir()

        prompt_file.write_text("""---
prompt:
  requires:
    - passage
  optional:
    - source
---

Analyze {{passage}}.
""")

        context = {
            "prompts_dir": str(tmp_path / "prompts"),
            "passage": "John 3:16"
            # source is optional and missing - should not error
        }

        result = render_prompt({"file": "test.gpt"}, context)

        assert "John 3:16" in result
        assert "{{passage}}" not in result

    def test_html_comment_header_format(self, tmp_path):
        """HTML comment header format should also be validated."""
        prompt_file = tmp_path / "prompts" / "test.gpt"
        prompt_file.parent.mkdir()

        prompt_file.write_text("""<!--
prompt:
  requires:
    - passage
-->

Analyze {{passage}} for {{name}}.
""")

        context = {
            "prompts_dir": str(tmp_path / "prompts"),
            "passage": "John 3:16",
            "name": "John"
        }

        with pytest.raises(ValueError) as exc_info:
            render_prompt({"file": "test.gpt"}, context)

        assert "name" in str(exc_info.value)
        assert "not declared in header" in str(exc_info.value)

    def test_prompt_without_header_has_backward_compatibility(self, tmp_path):
        """Prompts without headers should still work (backward compatibility)."""
        prompt_file = tmp_path / "prompts" / "test.gpt"
        prompt_file.parent.mkdir()

        # No header - should fall back to old behavior
        prompt_file.write_text("Analyze {{passage}} for {{name}}.")

        context = {
            "prompts_dir": str(tmp_path / "prompts"),
            "passage": "John 3:16",
            "name": "John"
        }

        # Should not raise - backward compatibility
        result = render_prompt({"file": "test.gpt"}, context)

        assert "John 3:16" in result
        assert "John" in result

    def test_multiple_undeclared_variables_listed(self, tmp_path):
        """All undeclared variables should be listed in error message."""
        prompt_file = tmp_path / "prompts" / "test.gpt"
        prompt_file.parent.mkdir()

        prompt_file.write_text("""---
prompt:
  requires:
    - passage
---

Analyze {{passage}} from {{source}} by {{author}}.
""")

        context = {
            "prompts_dir": str(tmp_path / "prompts"),
            "passage": "John 3:16",
            "source": "ESV",
            "author": "John"
        }

        with pytest.raises(ValueError) as exc_info:
            render_prompt({"file": "test.gpt"}, context)

        error_msg = str(exc_info.value)
        assert "author" in error_msg
        assert "source" in error_msg
