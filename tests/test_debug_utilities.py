"""Tests for debug utility functions in llmflow.runner"""

from llmflow.runner import save_content_to_file


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
