"""
Tests for GUI backend executor.

Run with: pytest tests/test_gui_executor.py
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Import the executor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'gui' / 'backend'))
from executor import PipelineExecutor


class TestPipelineExecutor:
    """Test the testable pipeline executor logic."""

    def test_determine_paths_with_absolute_pipeline(self, tmp_path):
        """Test path resolution when pipeline path is absolute."""
        # Create actual directories
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        pipeline_file = tmp_path / "pipeline.yaml"
        pipeline_file.touch()

        executor = PipelineExecutor(
            pipeline_path=str(pipeline_file),
            project_path=str(project_dir),
            variables={},
            execution_id="test-123"
        )

        cwd, pipeline_arg = executor._determine_paths()

        assert cwd == str(project_dir)
        # Absolute path outside project should stay absolute
        assert pipeline_arg == str(pipeline_file)

    def test_determine_paths_with_relative_pipeline(self, tmp_path):
        """Test path resolution when pipeline path is relative to project."""
        # Create actual directories
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        executor = PipelineExecutor(
            pipeline_path="pipelines/test.yaml",
            project_path=str(project_dir),
            variables={},
            execution_id="test-123"
        )

        cwd, pipeline_arg = executor._determine_paths()

        assert cwd == str(project_dir)
        assert pipeline_arg == "pipelines/test.yaml"

    def test_build_command_with_variables(self):
        """Test command building with variables."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"foo": "bar", "baz": "qux"},
            execution_id="test-123"
        )

        cmd = executor._build_command("test.yaml", "test.log")

        assert cmd[0:4] == ['sp', 'run', '--pipeline', 'test.yaml']
        assert '--log' in cmd
        assert 'test.log' in cmd
        assert '--var' in cmd
        assert 'foo=bar' in cmd
        assert 'baz=qux' in cmd

    def test_generate_log_filename(self):
        """Test unique log filename generation."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-exec-12345678"
        )

        log_filename = executor._generate_log_filename()

        # Should include timestamp and first 8 chars of execution ID
        assert 'llmflow-' in log_filename
        assert '-test-exe' in log_filename  # Truncated to 8 chars: 'test-exe'
        assert log_filename.endswith('.log')

    def test_parse_log_file_extracts_created_files(self, tmp_path):
        """Test parsing log file for created files."""
        # Create fake log file
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2026-03-27 10:00:00 - INFO - Starting pipeline\n"
            "2026-03-27 10:00:01 - INFO - Wrote file: /path/to/output1.json\n"
            "2026-03-27 10:00:02 - INFO - Processing...\n"
            "2026-03-27 10:00:03 - INFO - Wrote file: /path/to/output2.md\n"
            "2026-03-27 10:00:04 - INFO - Done\n"
        )

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        created_files, telemetry = executor._parse_log_file(log_file)

        assert len(created_files) == 2
        assert "/path/to/output1.json" in created_files
        assert "/path/to/output2.md" in created_files

    def test_parse_log_file_extracts_telemetry(self, tmp_path):
        """Test parsing log file for telemetry report."""
        # Create fake log file with telemetry
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2026-03-27 10:00:00 - INFO - Starting pipeline\n"
            "2026-03-27 10:00:05 - INFO - 📊 Pipeline Telemetry Summary\n"
            "2026-03-27 10:00:05 - INFO - ============================================================\n"
            "2026-03-27 10:00:05 - INFO - Total Duration: 5.2s\n"
            "2026-03-27 10:00:05 - INFO - Total Cost: $0.0032\n"
            "2026-03-27 10:00:05 - INFO - ============================================================\n"
            "2026-03-27 10:00:05 - INFO - Pipeline complete\n"
        )

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        created_files, telemetry = executor._parse_log_file(log_file)

        assert telemetry is not None
        assert "Total Duration: 5.2s" in telemetry
        assert "Total Cost: $0.0032" in telemetry

    def test_emit_callback_is_called(self):
        """Test that emit callback is called during execution."""
        emit_mock = Mock()

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123",
            emit_callback=emit_mock
        )

        # Call _emit directly
        executor._emit('status', {'message': 'test'})

        emit_mock.assert_called_once_with('status', {'message': 'test'})

    def test_clean_log_line_removes_timestamp_and_level(self):
        """Test that log line cleaning removes timestamps and log levels."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        # Test standard log format
        dirty_line = "2026-03-27 18:37:35,689 - INFO - Pipeline Summary"
        clean_line = executor._clean_log_line(dirty_line)
        assert clean_line == "Pipeline Summary"

        # Test with different log level
        dirty_line = "2026-03-27 10:15:42,123 - WARNING - Some warning"
        clean_line = executor._clean_log_line(dirty_line)
        assert clean_line == "Some warning"

        # Test line without log prefix (should return as-is)
        plain_line = "Just a plain message"
        clean_line = executor._clean_log_line(plain_line)
        assert clean_line == "Just a plain message"

    def test_multiple_executors_generate_different_log_files(self):
        """Test that different execution IDs result in different log filenames."""
        executor1 = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="exec-aaa"
        )

        executor2 = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="exec-bbb"
        )

        log1 = executor1._generate_log_filename()
        log2 = executor2._generate_log_filename()

        # Should be different
        assert log1 != log2
        # Should contain respective execution ID prefixes
        assert 'exec-aaa' in log1
        assert 'exec-bbb' in log2

    def test_parse_log_file_handles_missing_file(self):
        """Test that parsing handles missing log file gracefully."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        fake_path = Path("/nonexistent/path/to/file.log")
        created_files, telemetry = executor._parse_log_file(fake_path)

        assert created_files == []
        assert telemetry is None

    def test_parse_log_file_handles_duplicate_file_entries(self, tmp_path):
        """Test that duplicate file entries are deduplicated."""
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "INFO - Wrote file: /path/to/output.json\n"
            "INFO - Processing...\n"
            "INFO - Wrote file: /path/to/output.json\n"  # Duplicate
            "INFO - Done\n"
        )

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        created_files, telemetry = executor._parse_log_file(log_file)

        # Should only have one entry
        assert len(created_files) == 1
        assert created_files[0] == "/path/to/output.json"

    def test_parse_log_file_cleans_telemetry_lines(self, tmp_path):
        """Test that telemetry lines have log formatting stripped."""
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2026-03-27 10:00:00,123 - INFO - 📊 Pipeline Telemetry Summary\n"
            "2026-03-27 10:00:00,124 - INFO - ============================================================\n"
            "2026-03-27 10:00:00,125 - INFO - Pipeline: test.yaml\n"
            "2026-03-27 10:00:00,126 - INFO - Total Duration: 5.2s\n"
            "2026-03-27 10:00:00,127 - INFO - ============================================================\n"
        )

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        created_files, telemetry = executor._parse_log_file(log_file)

        assert telemetry is not None
        # Should not contain log prefixes
        assert "INFO -" not in telemetry
        assert "2026-03-27" not in telemetry
        # Should contain actual content
        assert "Pipeline: test.yaml" in telemetry
        assert "Total Duration: 5.2s" in telemetry

    def test_build_command_without_variables(self):
        """Test command building with no variables."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        cmd = executor._build_command("test.yaml", "test.log")

        assert 'sp' in cmd
        assert 'run' in cmd
        assert '--pipeline' in cmd
        assert 'test.yaml' in cmd
        assert '--log' in cmd
        # Should not have --var
        assert cmd.count('--var') == 0

    def test_build_command_rejects_invalid_variable_keys(self):
        """Test that variable keys with shell-special chars are rejected."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"bad key": "value"},
            execution_id="test-123"
        )

        with pytest.raises(ValueError, match="Invalid variable name"):
            executor._build_command("test.yaml", "test.log")

    def test_build_command_rejects_dash_in_variable_key(self):
        """Dashes are not valid Python identifiers and must be rejected."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"my-var": "value"},
            execution_id="test-123"
        )

        with pytest.raises(ValueError, match="Invalid variable name"):
            executor._build_command("test.yaml", "test.log")

    def test_build_command_rejects_injection_in_variable_key(self):
        """Variable keys with shell metacharacters must be rejected."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"key=injected --flag": "value"},
            execution_id="test-123"
        )

        with pytest.raises(ValueError, match="Invalid variable name"):
            executor._build_command("test.yaml", "test.log")

    def test_build_command_accepts_valid_variable_keys(self):
        """Valid Python-identifier keys must pass through."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={"valid_key": "v1", "KEY2": "v2", "_private": "v3"},
            execution_id="test-123"
        )

        cmd = executor._build_command("test.yaml", "test.log")

        assert 'valid_key=v1' in cmd
        assert 'KEY2=v2' in cmd
        assert '_private=v3' in cmd

    def test_determine_paths_without_project_path(self):
        """Test path resolution when no project path is provided."""
        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=None,
            variables={},
            execution_id="test-123"
        )

        cwd, pipeline_arg = executor._determine_paths()

        assert cwd is None
        assert pipeline_arg == "test.yaml"

    @patch('subprocess.Popen')
    @patch('select.select')
    def test_execute_integration(self, mock_select, mock_popen, tmp_path):
        """Test full execution flow with mocked subprocess."""
        # Create real log file that will be parsed
        log_file = tmp_path / "llmflow-test.log"
        log_file.write_text(
            "INFO - Wrote file: /output/result.json\n"
            "INFO - 📊 Pipeline Telemetry Summary\n"
            "INFO - Total Cost: $0.01\n"
            "INFO - ===================================\n"
        )

        # Mock process with proper stdout simulation
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = [
            "Line 1\n",
            "Line 2\n",
            ""  # EOF
        ]
        mock_process.poll.side_effect = [None, None, 0]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Mock select.select to always indicate stdout is ready
        mock_select.return_value = ([mock_process.stdout], [], [])

        emit_mock = Mock()

        executor = PipelineExecutor(
            pipeline_path="test.yaml",
            project_path=str(tmp_path),
            variables={"var1": "value1"},
            execution_id="test-123",
            emit_callback=emit_mock
        )

        # Mock _generate_log_filename to return our test log
        with patch.object(executor, '_generate_log_filename', return_value=str(log_file)):
            result = executor.execute()

        # Verify result
        assert result['success'] is True
        assert result['exit_code'] == 0
        assert '/output/result.json' in result['created_files']
        assert result['telemetry'] is not None

        # Verify emit was called
        assert emit_mock.call_count > 0
        # Check that status was emitted
        status_calls = [call for call in emit_mock.call_args_list if call[0][0] == 'status']
        assert len(status_calls) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
