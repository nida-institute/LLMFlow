"""Test local plugin/module imports from pipeline working directory."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from llmflow.runner import run_pipeline


class TestLocalPluginImports:
    """Test that pipelines can import plugins from their working directory"""

    @pytest.fixture
    def pipeline_with_local_plugin(self, tmp_path):
        """Create a test pipeline that uses a local plugin"""
        # Create a local plugin directory
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        # Create __init__.py
        (plugins_dir / "__init__.py").write_text("")

        # Create a simple local plugin
        plugin_code = '''"""Local test plugin."""

def run(**kwargs):
    """Test plugin that concatenates inputs."""
    a = kwargs.get("a", "")
    b = kwargs.get("b", "")
    return f"{a}_{b}"
'''
        (plugins_dir / "local_test_plugin.py").write_text(plugin_code)

        # Create pipeline that uses the local plugin
        pipeline_content = {
            "name": "local-plugin-test",
            "variables": {"input_a": "hello", "input_b": "world"},
            "llm_config": {"model": "gpt-4o"},
            "steps": [
                {
                    "name": "use_local_plugin",
                    "type": "function",
                    "function": "plugins.local_test_plugin.run",
                    "inputs": {
                        "a": "${input_a}",
                        "b": "${input_b}"
                    },
                    "outputs": "result"
                }
            ]
        }

        pipeline_path = tmp_path / "pipeline.yaml"
        with open(pipeline_path, "w") as f:
            yaml.dump(pipeline_content, f)

        return str(pipeline_path), tmp_path

    @pytest.fixture
    def pipeline_with_nested_plugin(self, tmp_path):
        """Create a pipeline with a nested local plugin module"""
        # Create nested plugin directory structure
        plugins_dir = tmp_path / "custom_plugins"
        plugins_dir.mkdir()
        (plugins_dir / "__init__.py").write_text("")

        renderers_dir = plugins_dir / "renderers"
        renderers_dir.mkdir()
        (renderers_dir / "__init__.py").write_text("")

        # Create nested plugin
        plugin_code = '''"""Nested renderer plugin."""

def render(**kwargs):
    """Render function that formats data."""
    data = kwargs.get("data", "")
    return f"[RENDERED: {data}]"
'''
        (renderers_dir / "markdown.py").write_text(plugin_code)

        # Create pipeline
        pipeline_content = {
            "name": "nested-plugin-test",
            "variables": {"content": "test content"},
            "llm_config": {"model": "gpt-4o"},
            "steps": [
                {
                    "name": "render_content",
                    "type": "function",
                    "function": "custom_plugins.renderers.markdown.render",
                    "inputs": {"data": "${content}"},
                    "outputs": "rendered"
                }
            ]
        }

        pipeline_path = tmp_path / "pipeline.yaml"
        with open(pipeline_path, "w") as f:
            yaml.dump(pipeline_content, f)

        return str(pipeline_path), tmp_path

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_import_local_plugin_from_cwd(
        self, mock_lint, mock_validate, pipeline_with_local_plugin
    ):
        """Test that pipeline can import plugins from its working directory"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        pipeline_path, working_dir = pipeline_with_local_plugin

        # Change to pipeline directory to simulate running from there
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(working_dir)

            # Run pipeline - should be able to import plugins.local_test_plugin
            result = run_pipeline(pipeline_path, skip_lint=True)

            # Verify the local plugin was successfully imported and executed
            assert "result" in result
            assert result["result"] == "hello_world"

        finally:
            os.chdir(original_cwd)
            # Clean up sys.path
            if str(working_dir) in sys.path:
                sys.path.remove(str(working_dir))

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_import_nested_local_plugin(
        self, mock_lint, mock_validate, pipeline_with_nested_plugin
    ):
        """Test that pipeline can import nested local plugin modules"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        pipeline_path, working_dir = pipeline_with_nested_plugin

        # Change to pipeline directory
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(working_dir)

            # Run pipeline with nested plugin
            result = run_pipeline(pipeline_path, skip_lint=True)

            # Verify
            assert "rendered" in result
            assert result["rendered"] == "[RENDERED: test content]"

        finally:
            os.chdir(original_cwd)
            # Clean up sys.path
            if str(working_dir) in sys.path:
                sys.path.remove(str(working_dir))

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_local_plugin_does_not_pollute_sys_path(
        self, mock_lint, mock_validate, pipeline_with_local_plugin
    ):
        """Test that adding cwd to sys.path doesn't cause issues with multiple runs"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        pipeline_path, working_dir = pipeline_with_local_plugin

        original_cwd = Path.cwd()
        initial_sys_path_len = len(sys.path)

        try:
            import os
            os.chdir(working_dir)

            # Run pipeline twice
            run_pipeline(pipeline_path, skip_lint=True)
            run_pipeline(pipeline_path, skip_lint=True)

            # sys.path should not have duplicate entries for working_dir
            working_dir_count = sys.path.count(str(working_dir))
            assert working_dir_count <= 1, f"sys.path has {working_dir_count} entries for {working_dir}"

        finally:
            os.chdir(original_cwd)
            # Clean up
            while str(working_dir) in sys.path:
                sys.path.remove(str(working_dir))
