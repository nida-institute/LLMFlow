from llmflow.runner import resolve


class TestTemplateResolution:
    """Test the specific issue with [-1] resolution in templates"""

    def test_resolve_function_supports_negative_indices(self):
        """Test that the resolve function properly handles list[-1] syntax"""
        context = {
            "bodies_list": ["intro", "middle", "conclusion"],
            "hearts_list": [],  # Empty list case
        }

        # Should resolve to last item
        assert resolve("${bodies_list[-1]}", context) == "conclusion"

        # Should handle empty list gracefully
        result = resolve("${hearts_list[-1]}", context)
        assert result in [None, "", "${hearts_list[-1]}"]

    def test_template_variables_resolution_order(self):
        """Test that variables are resolved BEFORE being passed to template"""
        # This is the core issue - variables with [-1] are being passed
        # literally to the template instead of being resolved first

        # Mock the function call chain to verify resolution happens
        pass

    def test_complex_variable_patterns(self):
        """Test various variable patterns we use"""
        context = {
            "scene": {"Citation": "Psalm 23:1-3", "SceneTitle": "The Good Shepherd"},
            "list": ["a", "b", "c"],
        }

        assert resolve("${scene.Citation}", context) == "Psalm 23:1-3"
        assert resolve("${list[0]}", context) == "a"
        assert resolve("${list[-1]}", context) == "c"
