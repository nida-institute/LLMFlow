"""Tests for guard functionality in LLMFlow"""
import pytest
from llmflow.utils.guards import build_step_eval_ctx, enforce_require, collect_warnings, _safe_eval


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


class TestCollectWarnings:
    """Test the collect_warnings function"""

    def test_no_warnings_when_all_pass(self):
        """Test that no warnings are collected when all conditions are false"""
        eval_ctx = {"content": "some text"}
        rules = [
            {"if": "len(content) == 0", "message": "Content is empty"},
            {"if": "len(content) > 100", "message": "Content is too long"}
        ]

        warnings = collect_warnings(eval_ctx, rules)
        assert warnings == []

    def test_warning_collected_when_condition_true(self):
        """Test that warning is collected when condition is true"""
        eval_ctx = {"content": ""}
        rules = [{"if": "len(content) == 0", "message": "Content is empty"}]

        warnings = collect_warnings(eval_ctx, rules)
        assert len(warnings) == 1
        assert warnings[0] == "Content is empty"

    def test_multiple_warnings_collected(self):
        """Test that multiple warnings are collected"""
        eval_ctx = {"content": "", "title": ""}
        rules = [
            {"if": "len(content) == 0", "message": "Content is empty"},
            {"if": "len(title) == 0", "message": "Title is empty"}
        ]

        warnings = collect_warnings(eval_ctx, rules)
        assert len(warnings) == 2
        assert "Content is empty" in warnings
        assert "Title is empty" in warnings

    def test_warning_on_eval_error(self):
        """Test that eval errors are captured as warnings"""
        eval_ctx = {"content": "text"}
        rules = [{"if": "undefined_var > 0", "message": "Should not reach"}]

        warnings = collect_warnings(eval_ctx, rules)
        assert len(warnings) == 1
        assert "Warn eval error" in warnings[0]
        assert "undefined_var" in warnings[0]

    def test_partial_warnings(self):
        """Test that only matching conditions generate warnings"""
        eval_ctx = {"x": 5, "y": 10}
        rules = [
            {"if": "x > 10", "message": "X too large"},  # False, no warning
            {"if": "y > 5", "message": "Y is large"},     # True, warning
            {"if": "x < 0", "message": "X negative"}      # False, no warning
        ]

        warnings = collect_warnings(eval_ctx, rules)
        assert len(warnings) == 1
        assert warnings[0] == "Y is large"

    def test_empty_rules(self):
        """Test with no rules provided"""
        eval_ctx = {"content": "text"}
        warnings = collect_warnings(eval_ctx, [])
        assert warnings == []

    def test_none_rules(self):
        """Test with None rules"""
        eval_ctx = {"content": "text"}
        warnings = collect_warnings(eval_ctx, None)
        assert warnings == []


class TestGuardEdgeCases:
    """Test edge cases and error scenarios"""

    def test_empty_expression_raises_error(self):
        """Test that empty expression raises ValueError"""
        with pytest.raises(ValueError, match="non-empty string"):
            _safe_eval("", {"x": 1})

    def test_whitespace_only_expression_raises_error(self):
        """Test that whitespace-only expression raises ValueError"""
        with pytest.raises(ValueError, match="non-empty string"):
            _safe_eval("   ", {"x": 1})

    def test_non_string_expression_raises_error(self):
        """Test that non-string expression raises ValueError"""
        with pytest.raises(ValueError, match="non-empty string"):
            _safe_eval(123, {"x": 1})

    def test_none_expression_raises_error(self):
        """Test that None expression raises ValueError"""
        with pytest.raises(ValueError, match="non-empty string"):
            _safe_eval(None, {"x": 1})

    def test_dangerous_builtins_blocked(self):
        """Test that dangerous builtins are not available"""
        ctx = {}
        with pytest.raises(NameError):
            _safe_eval("open('/etc/passwd')", ctx)

        with pytest.raises(NameError):
            _safe_eval("eval('1+1')", ctx)

        with pytest.raises(NameError):
            _safe_eval("__import__('os')", ctx)

    def test_safe_builtins_all_available(self):
        """Test that all safe builtins work"""
        ctx = {"nums": [1, 2, 3], "text": "hello"}

        assert _safe_eval("len(nums) == 3", ctx)
        assert _safe_eval("str(5) == '5'", ctx)
        assert _safe_eval("int('42') == 42", ctx)
        assert _safe_eval("float('3.14') > 3.0", ctx)
        assert _safe_eval("bool(text)", ctx)
        assert _safe_eval("any([False, True, False])", ctx)
        assert _safe_eval("all([True, True, True])", ctx)
        assert _safe_eval("min(nums) == 1", ctx)
        assert _safe_eval("max(nums) == 3", ctx)
        assert _safe_eval("sum(nums) == 6", ctx)

    def test_complex_boolean_expression(self):
        """Test complex boolean expressions with multiple operators"""
        ctx = {
            "bodies_content": "### Heading\n\nContent here",
            "scene": {"Citation": "Matthew 2:13-15"}
        }

        # Complex expression combining multiple checks
        expr = (
            "bool(str(bodies_content or '').strip()) and "
            "'Heading' in bodies_content and "
            "len(bodies_content) > 10"
        )
        assert _safe_eval(expr, ctx)

    def test_nested_data_access(self):
        """Test accessing nested dictionary/list data"""
        ctx = {
            "scene": {
                "Citation": "Matthew 2:13-15",
                "SBLGNT": "Greek text"
            },
            "items": [1, 2, 3]
        }

        assert _safe_eval("scene['Citation'] == 'Matthew 2:13-15'", ctx)
        assert _safe_eval("'Greek' in scene['SBLGNT']", ctx)
        assert _safe_eval("items[0] == 1", ctx)

    def test_none_context(self):
        """Test that None context is handled gracefully"""
        step = {"outputs": "result"}
        eval_ctx = build_step_eval_ctx(step, None)
        # Should not crash, context updates with None should be safe
        assert isinstance(eval_ctx, dict)

    def test_outputs_none(self):
        """Test step with no outputs"""
        step = {"name": "test_step"}
        context = {"some_var": "value"}
        eval_ctx = build_step_eval_ctx(step, context)
        # Context should still be merged
        assert eval_ctx["some_var"] == "value"

    def test_enforce_with_eval_error_in_rule(self):
        """Test that eval errors in enforce_require are properly reported"""
        eval_ctx = {"content": "text"}
        rules = [{"if": "undefined_var > 0", "message": "This should not appear"}]

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules)

        error_msg = str(exc_info.value)
        assert "Require eval error" in error_msg
        assert "undefined_var" in error_msg

    def test_default_message_when_missing(self):
        """Test that default message is used when not provided"""
        eval_ctx = {"x": 0}
        rules = [{"if": "x > 0"}]  # No message provided

        with pytest.raises(ValueError) as exc_info:
            enforce_require(eval_ctx, rules)

        assert "Require condition failed" in str(exc_info.value)

    def test_warning_default_message(self):
        """Test that warning uses default message when not provided"""
        eval_ctx = {"x": 5}
        rules = [{"if": "x > 0"}]  # No message provided

        warnings = collect_warnings(eval_ctx, rules)
        assert len(warnings) == 1
        assert "Warning condition matched" in warnings[0]


class TestGuardRealWorldScenarios:
    """Test real-world guard scenarios from pipelines"""

    def test_bodies_content_validation_full_flow(self):
        """Test the full Bodies content validation flow"""
        # Successful case
        eval_ctx = {
            "bodies_content": "### Enter the Scene with Your Body (Matthew 2:13-15)\n\n1. Picture Jesus...",
            "scene": {"Citation": "Matthew 2:13-15"}
        }
        rules = [
            {"if": "bool(str(bodies_content or '').strip())",
             "message": "Bodies step produced empty content for a scene."},
            {"if": "'Enter the Scene with Your Body' in str(bodies_content or '')",
             "message": "Bodies content missing required heading."}
        ]

        # Should not raise
        enforce_require(eval_ctx, rules, step_name="bodies",
                       context_info={"scene_citation": "Matthew 2:13-15"})

    def test_hearts_content_validation(self):
        """Test Hearts content validation"""
        eval_ctx = {
            "hearts_content": "### Enter the Scene with Your Whole Heart (Matthew 2:13-15)\n\n1. Notice...",
        }
        rules = [
            {"if": "bool(str(hearts_content or '').strip())",
             "message": "Hearts step produced empty content for a scene."},
            {"if": "'Enter the Scene with Your Whole Heart' in str(hearts_content or '')",
             "message": "Hearts content missing required heading."}
        ]

        enforce_require(eval_ctx, rules, step_name="hearts")

    def test_list_append_validation(self):
        """Test validation when appending to lists"""
        # Simulating append_to functionality
        eval_ctx = {
            "bodies_content": "### Heading\n\nContent",
            "bodies_list": ["Previous item 1", "Previous item 2"]
        }
        rules = [
            {"if": "bool(str(bodies_content or '').strip())",
             "message": "Cannot append empty content to bodies_list"}
        ]

        enforce_require(eval_ctx, rules)

    def test_multiple_scene_iteration_guards(self):
        """Test guards across multiple scene iterations"""
        scenes = [
            {"Citation": "Matthew 2:13-15"},
            {"Citation": "Matthew 2:16-18"},
            {"Citation": "Matthew 2:19-23"}
        ]

        for scene in scenes:
            eval_ctx = {
                "scene": scene,
                "bodies_content": f"### Content for {scene['Citation']}"
            }
            rules = [
                {"if": "bool(str(bodies_content or '').strip())",
                 "message": f"Empty content for {scene['Citation']}"}
            ]

            # All should pass
            enforce_require(eval_ctx, rules, step_name="bodies",
                           context_info={"scene_citation": scene['Citation']})

    def test_conditional_guard_with_string_matching(self):
        """Test guards that check for specific string patterns"""
        eval_ctx = {
            "passage_text": "In the beginning was the Word...",
            "language": "english"
        }
        rules = [
            {"if": "'Word' in passage_text", "message": "Missing key term 'Word'"},
            {"if": "language in ['english', 'greek']", "message": "Unsupported language"}
        ]

        enforce_require(eval_ctx, rules)

    def test_numeric_threshold_guards(self):
        """Test guards that check numeric thresholds"""
        eval_ctx = {
            "token_count": 1500,
            "max_tokens": 2000,
            "question_count": 5
        }
        rules = [
            {"if": "token_count < max_tokens", "message": "Content exceeds token limit"},
            {"if": "question_count >= 3", "message": "Insufficient questions"}
        ]

        enforce_require(eval_ctx, rules)

    def test_warning_for_long_content(self):
        """Test warning system for content length"""
        eval_ctx = {
            "bodies_content": "x" * 3000,  # Very long content
            "expected_length": 2000
        }
        rules = [
            {"if": "len(bodies_content) > expected_length",
             "message": "Bodies content is unusually long"}
        ]

        warnings = collect_warnings(eval_ctx, rules)
        assert len(warnings) == 1
        assert "unusually long" in warnings[0]

    def test_guard_with_or_fallback_pattern(self):
        """Test the common (var or default) pattern in guards"""
        # With value
        eval_ctx = {"content": "text"}
        assert _safe_eval("len(str(content or 'default')) > 0", eval_ctx)

        # With None
        eval_ctx = {"content": None}
        assert _safe_eval("str(content or 'default') == 'default'", eval_ctx)

        # With empty string
        eval_ctx = {"content": ""}
        assert _safe_eval("len(str(content or 'default')) > 0", eval_ctx)
