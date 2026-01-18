"""Tests for debug utility functions in llmflow.runner"""

import pytest
import os
from pathlib import Path

from llmflow.runner import build_debug_filename, save_content_to_file


class TestDebugFilename:
    """Test debug filename generation for request/response logging"""

    def test_build_filename_with_passage(self):
        """Filename should include passage reference when available"""
        step = {
            "name": "test_step",
            "prompt": {"file": "prompts/test-prompt.gpt"}
        }
        context = {"passage": "Mark 1:1-12"}

        filename_request = build_debug_filename(step, context, "request")
        filename_response = build_debug_filename(step, context, "response")

        assert "Mark" in filename_request
        assert "test_prompt" in filename_request or "test-prompt" in filename_request
        assert "request" in filename_request
        assert "response" in filename_response

    def test_build_filename_without_passage(self):
        """Filename should use timestamp when passage not available"""
        step = {
            "name": "test_step",
            "prompt": {"file": "prompts/test-prompt.gpt"}
        }
        context = {}

        filename = build_debug_filename(step, context, "request")

        assert "request" in filename
        # Should have some timestamp-like pattern (digits)
        assert any(c.isdigit() for c in filename)

    def test_build_filename_request_vs_response(self):
        """Request and response filenames should differ only in type indicator"""
        step = {
            "name": "test_step",
            "prompt": {"file": "prompts/test-prompt.gpt"}
        }
        context = {"passage": "Luke 7:36-50"}

        filename_request = build_debug_filename(step, context, "request")
        filename_response = build_debug_filename(step, context, "response")

        # Should both contain passage
        assert "Luke" in filename_request
        assert "Luke" in filename_response
        # Should differ in type
        assert "request" in filename_request
        assert "response" in filename_response
        assert filename_request != filename_response


class TestSaveContentToFile:
    """Test content saving utility"""

    def test_save_text_content(self, tmp_path):
        """Text content should be saved correctly"""
        content = "This is test content"
        filepath = tmp_path / "test.txt"

        result = save_content_to_file(content, str(filepath), format="text")

        assert filepath.exists()
        assert filepath.read_text() == content
        assert result == str(filepath)

    def test_save_json_content(self, tmp_path):
        """JSON content should be saved with proper formatting"""
        content = {"key": "value", "number": 42}
        filepath = tmp_path / "test.json"

        result = save_content_to_file(content, str(filepath), format="json")

        assert filepath.exists()
        import json
        saved_data = json.loads(filepath.read_text())
        assert saved_data == content

    def test_save_creates_parent_directories(self, tmp_path):
        """Parent directories should be created if they don't exist"""
        content = "Test content"
        filepath = tmp_path / "subdir" / "nested" / "test.txt"

        save_content_to_file(content, str(filepath), format="text")

        assert filepath.exists()
        assert filepath.read_text() == content

    def test_save_returns_path(self, tmp_path):
        """Function should return the path where content was saved"""
        content = "Test"
        filepath = tmp_path / "test.txt"

        result = save_content_to_file(content, str(filepath), format="text")

        assert result == str(filepath)
