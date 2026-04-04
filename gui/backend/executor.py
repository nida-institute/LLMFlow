"""
Testable pipeline execution logic for GUI backend.

This module contains the core execution logic extracted from the WebSocket handlers,
making it testable without Flask/SocketIO dependencies.
"""

import os
import re
import select
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

_VALID_VAR_KEY = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


class PipelineExecutor:
    """Execute pipelines and parse results - testable without WebSocket."""

    def __init__(
        self,
        pipeline_path: str,
        project_path: Optional[str],
        variables: Dict[str, str],
        execution_id: str,
        emit_callback: Optional[Callable[[str, Dict], None]] = None
    ):
        """
        Initialize executor.

        Args:
            pipeline_path: Path to pipeline YAML file
            project_path: Working directory for execution
            variables: Pipeline variables
            execution_id: Unique ID for this execution
            emit_callback: Optional callback for status updates (event_type, data)
        """
        self.pipeline_path = pipeline_path
        self.project_path = project_path
        self.variables = variables
        self.execution_id = execution_id
        self.emit_callback = emit_callback or (lambda *args: None)

        # Output buffer for testing
        self.output_lines: List[str] = []

    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event via callback and store for testing."""
        self.emit_callback(event_type, data)

    def _determine_paths(self) -> Tuple[Optional[str], str]:
        """Determine working directory and pipeline argument."""
        if self.project_path and Path(self.project_path).exists():
            cwd = self.project_path
            pipeline_file = Path(self.pipeline_path)

            if pipeline_file.is_absolute():
                try:
                    pipeline_rel = pipeline_file.relative_to(self.project_path)
                    pipeline_arg = str(pipeline_rel)
                except ValueError:
                    pipeline_arg = str(self.pipeline_path)
            else:
                pipeline_arg = str(self.pipeline_path)
        else:
            cwd = None
            pipeline_arg = str(self.pipeline_path)

        return cwd, pipeline_arg

    def _build_command(self, pipeline_arg: str, log_filename: str) -> List[str]:
        """Build sp run command with arguments."""
        cmd = ['sp', 'run', '--pipeline', pipeline_arg, '--log', log_filename]
        for key, value in self.variables.items():
            if not _VALID_VAR_KEY.match(str(key)):
                raise ValueError(f"Invalid variable name '{key}': must be a valid identifier")
            cmd.extend(['--var', f'{key}={value}'])
        return cmd

    def _generate_log_filename(self) -> str:
        """Generate unique log filename for this execution."""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        return f'llmflow-{timestamp}-{self.execution_id[:8]}.log'

    def _stream_output(self, process: subprocess.Popen) -> int:
        """
        Stream output from subprocess with throttling and heartbeat.

        Returns:
            Exit code
        """
        buffer = []
        last_emit = time.time()
        last_heartbeat = time.time()
        EMIT_INTERVAL = 0.5
        HEARTBEAT_INTERVAL = 2.0
        CHECK_INTERVAL = 0.2

        while True:
            now = time.time()

            # Non-blocking read
            ready = select.select([process.stdout], [], [], CHECK_INTERVAL)[0]
            if ready and process.stdout:
                line = process.stdout.readline()
                if line:
                    stripped = line.rstrip()
                    buffer.append(stripped)
                    self.output_lines.append(stripped)
                    last_heartbeat = now

            # Check if finished
            if process.poll() is not None:
                break

            # Emit batch
            if buffer and ((now - last_emit >= EMIT_INTERVAL) or len(buffer) >= 30):
                self._emit('output_batch', {'lines': buffer})
                buffer = []
                last_emit = now
                last_heartbeat = now

            # Heartbeat
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                self._emit('heartbeat', {'message': '⏳ Pipeline is running...'})
                last_heartbeat = now

        # Emit remaining
        if buffer:
            self._emit('output_batch', {'lines': buffer})
            self.output_lines.extend(buffer)

        return process.wait()

    def _clean_log_line(self, line: str) -> str:
        """
        Clean log formatting from a line.

        Removes timestamps and log level prefixes like:
        '2026-03-27 18:37:35,689 - INFO - Pipeline: ...'
        -> 'Pipeline: ...'
        """
        import re

        # Pattern: timestamp - LEVEL - message
        # Example: 2026-03-27 18:37:35,689 - INFO - Pipeline Summary
        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - \w+ - '
        cleaned = re.sub(pattern, '', line)

        return cleaned.rstrip()

    def _parse_log_file(self, log_path: Path) -> Tuple[List[str], Optional[str]]:
        """
        Parse log file for created files and telemetry report.

        Returns:
            (created_files, telemetry_report)
        """
        created_files = []
        telemetry_report = None

        if not log_path.exists():
            return created_files, telemetry_report

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Extract created files
            for line in lines:
                if 'Wrote file:' in line:
                    parts = line.split('Wrote file:', 1)
                    if len(parts) == 2:
                        file_path = parts[1].strip()
                        if file_path and file_path not in created_files:
                            created_files.append(file_path)

            # Extract telemetry
            in_telemetry = False
            telemetry_lines = []
            for line in lines:
                if '📊 Pipeline Telemetry Summary' in line:
                    in_telemetry = True
                    # Add the header without log prefix
                    cleaned = self._clean_log_line(line)
                    telemetry_lines.append(cleaned)
                    continue
                elif in_telemetry:
                    if line.strip().startswith('==='):
                        break
                    # Clean log formatting from telemetry lines
                    cleaned = self._clean_log_line(line)
                    if cleaned:  # Only add non-empty lines
                        telemetry_lines.append(cleaned)

            if telemetry_lines:
                telemetry_report = '\n'.join(telemetry_lines)

        except Exception:
            pass

        return created_files, telemetry_report

    def execute(self) -> Dict[str, Any]:
        """
        Execute pipeline and return results.

        Returns:
            {
                'success': bool,
                'exit_code': int,
                'created_files': List[str],
                'telemetry': Optional[str],
                'output_dir': Optional[str],
                'output_lines': List[str]  # For testing
            }
        """
        self._emit('status', {'message': 'Starting pipeline...', 'stage': 'init'})

        cwd, pipeline_arg = self._determine_paths()
        log_filename = self._generate_log_filename()
        cmd = self._build_command(pipeline_arg, log_filename)

        # Execute
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            cwd=cwd,
            env=env
        )

        exit_code = self._stream_output(process)

        # Parse log
        created_files, telemetry_report = ([], None)
        if cwd:
            log_path = Path(cwd) / log_filename
            created_files, telemetry_report = self._parse_log_file(log_path)

        return {
            'success': exit_code == 0,
            'exit_code': exit_code,
            'created_files': created_files,
            'telemetry': telemetry_report,
            'output_dir': cwd,
            'output_lines': self.output_lines  # For testing
        }
