"""
Tests for the installable GUI executor (src/llmflow/gui/executor.py).

Mirrors test_gui_executor.py but imports from the package so that coverage
is recorded against src/llmflow/gui/executor.py, not gui/backend/executor.py.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from llmflow.gui.executor import PipelineExecutor


class TestPkgPipelineExecutor:

    def test_determine_paths_with_absolute_pipeline(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        pipeline_file = tmp_path / "pipeline.yaml"
        pipeline_file.touch()

        executor = PipelineExecutor(
            pipeline_path=str(pipeline_file),
            project_path=str(project_dir),
            variables={},
            execution_id="test-123",
        )

        cwd, pipeline_arg = executor._determine_paths()

        assert cwd == str(project_dir)
        assert pipeline_arg == str(pipeline_file)

    def test_determine_paths_with_relative_pipeline(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        executor = PipelineExecutor(
            pipeline_path="pipelines/test.yaml",
            project_path=str(project_dir),
            variables={},
            execution_id="test-123",
        )

        cwd, pipeline_arg = executor._determine_paths()

        assert cwd == str(project_dir)
        assert pipeline_arg == "pipelines/test.yaml"

    def test_determine_paths_without_project(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123",
        )

        cwd, pipeline_arg = executor._determine_paths()

        assert cwd is None
        assert pipeline_arg == "test.yaml"

    def test_build_command_with_variables(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"foo": "bar", "baz": "qux"},
            execution_id="test-123",
        )

        cmd = executor._build_command("test.yaml", "test.log")

        assert cmd[:4] == ["sp", "run", "--pipeline", "test.yaml"]
        assert "--log" in cmd
        assert "foo=bar" in cmd
        assert "baz=qux" in cmd

    def test_build_command_rejects_invalid_variable_keys(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"bad key": "value"},
            execution_id="test-123",
        )

        with pytest.raises(ValueError, match="Invalid variable name"):
            executor._build_command("test.yaml", "test.log")

    def test_build_command_rejects_dash_in_key(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"my-var": "value"},
            execution_id="test-123",
        )

        with pytest.raises(ValueError, match="Invalid variable name"):
            executor._build_command("test.yaml", "test.log")

    def test_build_command_accepts_valid_keys(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"valid_key": "v", "KEY2": "v2", "_p": "v3"},
            execution_id="test-123",
        )

        cmd = executor._build_command("test.yaml", "test.log")

        assert "valid_key=v" in cmd
        assert "KEY2=v2" in cmd
        assert "_p=v3" in cmd

    def test_generate_log_filename(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-exec-12345678",
        )

        name = executor._generate_log_filename()

        assert name.startswith("llmflow-")
        assert name.endswith(".log")
        assert "test-exe" in name

    def test_parse_log_file_extracts_created_files(self, tmp_path):
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "INFO - Wrote file: /out/a.json\n"
            "INFO - Wrote file: /out/b.md\n"
        )

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123",
        )

        created, _ = executor._parse_log_file(log_file)

        assert "/out/a.json" in created
        assert "/out/b.md" in created

    def test_parse_log_file_deduplicates(self, tmp_path):
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "INFO - Wrote file: /out/a.json\n"
            "INFO - Wrote file: /out/a.json\n"
        )

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123",
        )

        created, _ = executor._parse_log_file(log_file)

        assert len(created) == 1

    def test_parse_log_file_handles_missing_file(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123",
        )

        created, telemetry = executor._parse_log_file(Path("/nonexistent/file.log"))

        assert created == []
        assert telemetry is None

    def test_clean_log_line(self):
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123",
        )

        dirty = "2026-03-27 18:37:35,689 - INFO - Pipeline Summary"
        assert executor._clean_log_line(dirty) == "Pipeline Summary"

    def test_emit_callback_called(self):
        cb = Mock()
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123",
            emit_callback=cb,
        )

        executor._emit("status", {"message": "hi"})

        cb.assert_called_once_with("status", {"message": "hi"})

    @patch("llmflow.gui.executor.subprocess.Popen")
    @patch("llmflow.gui.executor.select.select")
    def test_execute_integration(self, mock_select, mock_popen, tmp_path):
        log_file = tmp_path / "llmflow-test.log"
        log_file.write_text(
            "INFO - Wrote file: /output/result.json\n"
            "INFO - 📊 Pipeline Telemetry Summary\n"
            "INFO - Total Cost: $0.01\n"
            "INFO - ===================================\n"
        )

        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["Line 1\n", "Line 2\n", ""]
        mock_process.poll.side_effect = [None, None, 0]
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        mock_select.return_value = ([mock_process.stdout], [], [])

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=str(tmp_path),
            variables={},
            execution_id="test-123",
            emit_callback=Mock(),
        )

        with patch.object(executor, "_generate_log_filename", return_value=str(log_file)):
            result = executor.execute()

        assert result["success"] is True
        assert "/output/result.json" in result["created_files"]
