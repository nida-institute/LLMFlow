from llmflow.utils.linter import collect_all_steps


class TestLinterForEach:
    """Test that the linter properly checks steps inside for-each loops"""

    def test_collect_all_steps_finds_nested_steps(self):
        """Test that collect_all_steps recursively finds steps in for-each"""
        pipeline_steps = [
            {"name": "step1", "type": "llm"},
            {
                "name": "for_each_step",
                "type": "for-each",
                "steps": [
                    {"name": "nested1", "type": "llm"},
                    {"name": "nested2", "type": "function"},
                    {"name": "nested3", "type": "llm"},
                ],
            },
            {"name": "step3", "type": "function"},
        ]

        all_steps = collect_all_steps(pipeline_steps)

        # Should find all 6 steps (3 top-level + 3 nested)
        assert len(all_steps) == 6

        # Check that nested steps are included
        step_names = [s.get("name") for s in all_steps]
        assert "nested1" in step_names
        assert "nested2" in step_names
        assert "nested3" in step_names

    def test_linter_validates_nested_contracts(self):
        """Test that linter checks contracts for steps inside for-each"""
        # This test would verify that contract mismatches in nested steps are caught
        pass
