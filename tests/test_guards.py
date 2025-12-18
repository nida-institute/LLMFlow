"""Tests for guard functionality in LLMFlow"""
import pytest
from llmflow.utils.guards import build_step_eval_ctx, enforce_require, _safe_eval


class TestSafeEval:
    """Test the _safe_eval function"""

    def test_simple_expression(self):
        """Test evaluating a simple boolean expression"""
        ctx = {"x": 5}
        assert _safe_eval("x > 3", ctx) is True
        assert _safe_eval("x < 3", ctx) is False

    def test_string_operations(self):
        """Test string operations in guard expressions"""
        ctx = {"name": "hello"}
        assert _safe_eval("len(name) == 5", ctx) is True
        assert _safe_eval("'ell' in name", ctx) is True

    def test_boolean_coercion(self):
        """Test bool() coercion in guard expressions"""
        ctx = {"content": "some text"}
        assert _safe_eval("bool(content)", ctx) is True

        ctx = {"content": ""}
        assert _safe_eval("bool(content)", ctx) is False

    def test_empty_content_with_or_fallback(self):
        """Test the pattern: not bool(str(var or '').strip())"""
        # Content exists
        ctx = {"bodies_content": "### Heading\n\nContent here"}
        assert _safe_eval("not bool(str(bodies_content or '').strip())", ctx) is False

        # Content is empty string
        ctx = {"bodies_content": ""}
        assert _safe_eval("not bool(str(bodies_content or '').strip())", ctx) is True

        # Content is None
        ctx = {"bodies_content": None}
        assert _safe_eval("not bool(str(bodies_content or '').strip())", ctx) is True

        # Content is whitespace only
        ctx = {"bodies_content": "   \n\n  "}
        assert _safe_eval("not bool(str(bodies_content or '').strip())", ctx) is True

    def test_undefined_variable_raises_error(self):
        """Test that referencing undefined variable raises NameError"""
        ctx = {}
        with pytest.raises(NameError):
            _safe_eval("undefined_var > 0", ctx)

    def test_safe_builtins_available(self):
        """Test that safe builtins are available"""
        ctx = {"nums": [1, 2, 3]}
        assert _safe_eval("len(nums) == 3", ctx) is True
        assert _safe_eval("sum(nums) == 6", ctx) is True
        assert _safe_eval("max(nums) == 3", ctx) is True


class TestBuildStepEvalCtx:
    """Test building evaluation context from step and context"""

    def test_single_string_output(self):
        """Test step with single string output"""
        step = {"outputs": "result"}
        context = {"result": "some value"}

        eval_ctx = build_step_eval_ctx(step, context)

        assert "result" in eval_ctx
        assert eval_ctx["result"] == "some value"

    def test_list_outputs(self):
        """Test step with list of outputs"""
        step = {"outputs": ["result1", "result2"]}
        context = {"result1": "value1", "result2": "value2"}

        eval_ctx = build_step_eval_ctx(step, context)

        assert eval_ctx["result1"] == "value1"
        assert eval_ctx["result2"] == "value2"

    def test_dict_outputs(self):
        """Test step with dict outputs"""
        step = {"outputs": {"result": "string"}}
        context = {"result": "some value"}

        eval_ctx = build_step_eval_ctx(step, context)

        assert eval_ctx["result"] == "some value"

    def test_context_merged_into_eval_ctx(self):
        """Test that entire context is merged into eval_ctx"""
        step = {"outputs": "result"}
        context = {
            "result": "primary value",
            "exegetical_culture": "background info",
            "scene": {"Citation": "Matthew 2:13-15"}
        }

        eval_ctx = build_step_eval_ctx(step, context)

        # All context values should be in eval_ctx
        assert eval_ctx["result"] == "primary value"
        assert eval_ctx["exegetical_culture"] == "background info"
        assert eval_ctx["scene"] == {"Citation": "Matthew 2:13-15"}

    def test_variable_resolution(self):
        """Test that ${var} style inputs are resolved"""
        step = {
            "outputs": "result",
            "inputs": {
                "variables": {
                    "passage": "${passage_ref}",
                    "literal": "literal value"
                }
            }
        }
        context = {"passage_ref": "Matthew 2:13-23", "result": "output"}

        eval_ctx = build_step_eval_ctx(step, context)

        assert eval_ctx["passage"] == "Matthew 2:13-23"
        assert eval_ctx["literal"] == "literal value"


class TestEnforceRequire:
    """Test the enforce_require function"""

    def test_passing_guard(self):
        """Test that passing guard doesn't raise error"""
        eval_ctx = {"content": "some text"}
        rules = [{"if": "len(content) > 0", "message": "Content is empty"}]

        # Should not raise
        enforce_require(eval_ctx, rules)

    def test_failing_guard_raises_error(self):
        """Test that failing guard raises ValueError"""
        eval_ctx = {"content": ""}
        rules = [{"if": "len(content) > 0", "message": "Content is empty"}]

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules)

        assert "Content is empty" in str(exc_info.value)

    def test_multiple_rules(self):
        """Test multiple guard rules"""
        eval_ctx = {"bodies_content": "### Heading\n\nContent"}
        rules = [
            {"if": "bool(str(bodies_content or '').strip())", "message": "Bodies content is empty"},
            {"if": "'### Heading' in bodies_content", "message": "Missing required heading"}
        ]

        # Both should pass
        enforce_require(eval_ctx, rules)

    def test_first_failing_rule_stops_execution(self):
        """Test that first failing rule raises immediately"""
        eval_ctx = {"content": ""}
        rules = [
            {"if": "len(content) > 0", "message": "First rule failed"},
            {"if": "True", "message": "Second rule failed"}  # This would fail if checked
        ]

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules)

        assert "First rule failed" in str(exc_info.value)
        assert "Second rule failed" not in str(exc_info.value)

    def test_error_message_includes_step_name(self):
        """Test that error message includes step name when provided"""
        eval_ctx = {"content": ""}
        rules = [{"if": "len(content) > 0", "message": "Content is empty"}]

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules, step_name="bodies")

        assert "Step: bodies" in str(exc_info.value)

    def test_error_message_includes_context_info(self):
        """Test that error message includes context info when provided"""
        eval_ctx = {"content": ""}
        rules = [{"if": "len(content) > 0", "message": "Content is empty"}]
        context_info = {"scene_citation": "Matthew 2:13-15"}

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules, step_name="bodies", context_info=context_info)

        error_msg = str(exc_info.value)
        assert "Step: bodies" in error_msg
        assert "scene_citation='Matthew 2:13-15'" in error_msg

    def test_error_message_shows_variable_values(self):
        """Test that error message shows actual variable values"""
        eval_ctx = {"bodies_content": ""}
        rules = [{"if": "len(bodies_content) > 0", "message": "Empty content"}]

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules)

        error_msg = str(exc_info.value)
        assert "bodies_content" in error_msg
        assert "length=0" in error_msg

    def test_bodies_guard_scenario(self):
        """Test the actual Bodies guard scenario from the pipeline"""
        # Simulate successful Bodies step
        eval_ctx = {
            "bodies_content": "### Enter the Scene with Your Body (Matthew 2:13-15)\n\n1. Imagine the quiet...",
            "scene": {"Citation": "Matthew 2:13-15", "SBLGNT": "Greek text here"}
        }
        rules = [
            {"if": "bool(str(bodies_content or '').strip())",
             "message": "Bodies step produced empty content for a scene."},
            {"if": "'Enter the Scene with Your Body' in str(bodies_content or '')",
             "message": "Bodies content missing required heading."}
        ]

        # Should pass
        enforce_require(eval_ctx, rules, step_name="bodies",
                       context_info={"scene_citation": "Matthew 2:13-15"})

    def test_bodies_guard_empty_content(self):
        """Test Bodies guard with empty content"""
        eval_ctx = {"bodies_content": ""}
        rules = [
            {"if": "bool(str(bodies_content or '').strip())",
             "message": "Bodies step produced empty content for a scene."}
        ]

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules, step_name="bodies",
                           context_info={"scene_citation": "Matthew 2:13-15"})

        error_msg = str(exc_info.value)
        assert "Bodies step produced empty content" in error_msg
        assert "Matthew 2:13-15" in error_msg

    def test_bodies_guard_missing_heading(self):
        """Test Bodies guard with missing heading"""
        eval_ctx = {"bodies_content": "Some content without the required heading"}
        rules = [
            {"if": "bool(str(bodies_content or '').strip())",
             "message": "Bodies step produced empty content for a scene."},
            {"if": "'Enter the Scene with Your Body' in str(bodies_content or '')",
             "message": "Bodies content missing required heading."}
        ]

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules, step_name="bodies")

        # 3. eval_ctx is built from step + context
        # 4. Guards are checked

        step = {
            "name": "bodies",
            "outputs": "bodies_content",
            "require": [
                {"if": "bool(str(bodies_content or '').strip())",
                 "message": "Bodies content is empty"}
            ]
        }

        # Simulate context after handle_step_outputs stored the result
        context = {
            "bodies_content": "### Enter the Scene with Your Body\n\nContent here",
            "scene": {"Citation": "Matthew 2:13-15"}
        }

        # Build eval context (this is what runner.py does)
        eval_ctx = build_step_eval_ctx(step, context)

        # Verify bodies_content is in eval_ctx
        assert "bodies_content" in eval_ctx
        assert eval_ctx["bodies_content"] == context["bodies_content"]

        # Guards should pass
        enforce_require(eval_ctx, step["require"], step_name="bodies")

    def test_guard_in_for_each_iteration(self):
        """Test guards work correctly in for-each iteration context"""
        # In for-each, iteration_context is a deepcopy of parent context
        # Each iteration stores its outputs in iteration_context
        # Guards should see those outputs

        step = {
            "name": "bodies",
            "outputs": "bodies_content",
            "require": [
                {"if": "bool(str(bodies_content or '').strip())",
                 "message": "Bodies content is empty"}
            ]
        }

        # Simulate iteration context after output storage
        iteration_context = {
            "scene": {"Citation": "Matthew 2:13-15", "SBLGNT": "Greek text"},
            "passage": "Matthew 2:13-23",
            "exegetical_culture": "Background info",
            "bodies_content": "### Enter the Scene with Your Body\n\n1. Imagine..."
        }

        # Build eval context
        eval_ctx = build_step_eval_ctx(step, iteration_context)

        # Verify bodies_content is in eval_ctx
        assert "bodies_content" in eval_ctx
        assert len(eval_ctx["bodies_content"]) > 0

        # Guards should pass
        enforce_require(eval_ctx, step["require"], step_name="bodies",
                       context_info={"scene_citation": iteration_context["scene"]["Citation"]})
