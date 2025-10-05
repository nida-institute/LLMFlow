import pytest


class TestCriticalResolution:
    def test_resolution_chain_through_pipeline(self):
        """Test that variables resolve correctly through pipeline steps"""
        from llmflow.runner import resolve

        # Simulate pipeline progression
        context = {}

        # Step 1: Create initial data
        context["scenes"] = ["Scene A", "Scene B", "Scene C"]

        # Step 2: Test list indexing
        last_scene = resolve("${scenes[-1]}", context)
        assert last_scene == "Scene C"

        # Step 3: resolve() DOES do recursive resolution
        context["current_scene"] = "${scenes[-1]}"
        resolved = resolve("${current_scene}", context)
        # Updated behavior: resolve() DOES recursively resolve
        assert resolved == "Scene C"  # This is the correct behavior

        # To get recursive resolution, need to resolve twice
        # if isinstance(resolved, str) and resolved.startswith("${"):
        #     resolved = resolve(resolved, context)
        # assert resolved == "Scene C"  # Remove this - no longer needed

        # Step 4: Test in template context
        context["template_vars"] = {
            "final_scene": "${scenes[-1]}",
            "scene_count": len(context["scenes"]),
        }

        # Critical: template variables should resolve
        final = resolve("${template_vars.final_scene}", context)
        assert final == "Scene C"