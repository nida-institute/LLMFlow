from llmflow.runner import resolve


class TestResolveFunction:
    """Test the resolve function with various variable patterns"""

    def test_simple_variable(self):
        """Test basic variable resolution"""
        context = {"name": "John", "age": 30}
        assert resolve("${name}", context) == "John"
        assert resolve("${age}", context) == 30

    def test_list_indexing(self):
        """Test list indexing with positive and negative indices"""
        context = {
            "items": ["first", "second", "third", "fourth"],
            "numbers": [10, 20, 30, 40],
        }

        # Positive indices
        assert resolve("${items[0]}", context) == "first"
        assert resolve("${items[2]}", context) == "third"
        assert resolve("${numbers[1]}", context) == 20

        # Negative indices
        assert resolve("${items[-1]}", context) == "fourth"
        assert resolve("${items[-2]}", context) == "third"
        assert resolve("${numbers[-1]}", context) == 40

    def test_nested_resolution(self):
        """Test nested object resolution"""
        context = {"user": {"name": "Alice", "scores": [85, 90, 95]}}

        assert resolve("${user.name}", context) == "Alice"
        assert resolve("${user.scores[0]}", context) == 85
        assert resolve("${user.scores[-1]}", context) == 95

    def test_template_variables(self):
        """Test the exact pattern used in templates"""
        context = {
            "bodies_list": ["body1", "body2", "body3"],
            "hearts_list": ["heart1", "heart2", "heart3"],
            "scene": {"title": "Scene 1", "number": 1},
        }

        # These are the exact patterns failing in your templates
        assert resolve("${bodies_list[-1]}", context) == "body3"
        assert resolve("${hearts_list[-1]}", context) == "heart3"
        assert resolve("${scene.title}", context) == "Scene 1"

    def test_empty_list_handling(self):
        """Test behavior with empty lists"""
        context = {"empty_list": []}

        # Should handle gracefully
        result = resolve("${empty_list[-1]}", context)
        assert result is None or result == "${empty_list[-1]}"

    def test_missing_variable(self):
        """Test behavior with missing variables"""
        context = {"existing": "value"}

        # Should return the original string if not found
        assert resolve("${missing}", context) == "${missing}"
        assert resolve("${missing[-1]}", context) == "${missing[-1]}"
