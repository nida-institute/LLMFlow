"""Tests for run_save_step function"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from llmflow.runner import run_save_step


class TestRunSaveStep:
    """Test suite for run_save_step function"""

    def test_basic_save(self, tmp_path):
        """Test basic save operation with explicit content"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt"),
            "content": "Hello, World!"
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Hello, World!"

    def test_save_with_variable_resolution(self, tmp_path):
        """Test save with variables in path and content"""
        step = {
            "name": "test-save",
            "path": "${output_dir}/result.txt",
            "content": "Result: ${value}"
        }
        context = {
            "output_dir": str(tmp_path),
            "value": "42"
        }

        run_save_step(step, context, None)

        output_file = tmp_path / "result.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Result: 42"

    def test_save_uses_context_content_fallback(self, tmp_path):
        """Test save uses context['content'] when content not specified"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt")
        }
        context = {
            "content": "Fallback content"
        }

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Fallback content"

    def test_save_with_default_path(self, tmp_path):
        """Test save uses default path when not specified"""
        with patch('llmflow.runner.save_content_to_file') as mock_save:
            mock_save.return_value = str(tmp_path / "output.txt")

            step = {
                "name": "test-save",
                "content": "Test content"
            }
            context = {}

            run_save_step(step, context, None)

            # Verify default path is used
            call_args = mock_save.call_args
            assert call_args[0][0] == "Test content"
            assert call_args[0][1] == "output.txt"

    def test_save_creates_parent_directories(self, tmp_path):
        """Test save creates parent directories if they don't exist"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "nested" / "dir" / "output.txt"),
            "content": "Nested content"
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "nested" / "dir" / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Nested content"

    def test_save_with_dict_content(self, tmp_path):
        """Test save converts dict to string"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt"),
            "content": {"key": "value", "number": 42}
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        content = output_file.read_text()
        assert "key" in content
        assert "value" in content

    def test_save_with_list_content(self, tmp_path):
        """Test save converts list to string"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt"),
            "content": ["item1", "item2", "item3"]
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        content = output_file.read_text()
        assert "item1" in content

    def test_save_with_empty_content(self, tmp_path):
        """Test save with empty string content"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt"),
            "content": ""
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == ""

    def test_save_with_context_variable_content(self, tmp_path):
        """Test save with content from context variable"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt"),
            "content": "${my_data}"
        }
        context = {
            "my_data": "Data from context"
        }

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Data from context"

    def test_save_records_written_file(self, tmp_path):
        """Test save records the written file path"""
        with patch('llmflow.runner._record_written_file') as mock_record:
            step = {
                "name": "test-save",
                "path": str(tmp_path / "output.txt"),
                "content": "Test"
            }
            context = {}

            run_save_step(step, context, None)

            mock_record.assert_called_once()
            # Verify absolute path is recorded
            recorded_path = mock_record.call_args[0][0]
            assert Path(recorded_path).is_absolute()

    def test_save_logs_info_messages(self, tmp_path):
        """Test save logs appropriate info messages"""
        with patch('llmflow.runner.logger') as mock_logger:
            step = {
                "name": "test-save-step",
                "path": str(tmp_path / "output.txt"),
                "content": "Test"
            }
            context = {}

            run_save_step(step, context, None)

            # Check starting message
            mock_logger.info.assert_any_call("💾 Starting save step: test-save-step")
            # Check completion message
            mock_logger.info.assert_any_call("✅ Completed save step: test-save-step")

    def test_save_with_no_context_content_fallback(self, tmp_path):
        """Test save with no content and empty context defaults to empty string"""
        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt")
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == ""

    def test_save_with_multiline_content(self, tmp_path):
        """Test save preserves multiline content"""
        multiline_content = """Line 1
Line 2
Line 3"""

        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt"),
            "content": multiline_content
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == multiline_content

    def test_save_with_unicode_content(self, tmp_path):
        """Test save handles Unicode content correctly"""
        unicode_content = "Hello 世界 🌍"

        step = {
            "name": "test-save",
            "path": str(tmp_path / "output.txt"),
            "content": unicode_content
        }
        context = {}

        run_save_step(step, context, None)

        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text(encoding='utf-8') == unicode_content

    def test_save_overwrites_existing_file(self, tmp_path):
        """Test save overwrites existing file"""
        output_file = tmp_path / "output.txt"
        output_file.write_text("Old content")

        step = {
            "name": "test-save",
            "path": str(output_file),
            "content": "New content"
        }
        context = {}

        run_save_step(step, context, None)

        assert output_file.read_text() == "New content"

    def test_save_with_nested_variable_resolution(self, tmp_path):
        """Test save with nested variable resolution"""
        step = {
            "name": "test-save",
            "path": "${base_path}/${filename}",
            "content": "${data.message}"
        }
        context = {
            "base_path": str(tmp_path),
            "filename": "result.txt",
            "data": {"message": "Nested value"}
        }

        run_save_step(step, context, None)

        output_file = tmp_path / "result.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Nested value"