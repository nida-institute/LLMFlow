import subprocess
import tempfile
import yaml
import os

def test_execution_shows_progress_messages():
    test_pipeline = {
        "name": "test_progress",
        "steps": [{
            "name": "test_step",
            "type": "function",
            "function": "tests.test_output_integration.simple_test_func",
            "outputs": ["result"]
        }]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name

    try:
        result = subprocess.run(
            ["llmflow", "run", "--pipeline", pipeline_file],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}
        )

        assert "🔧 Starting function step: test_step" in result.stderr
    finally:
        os.remove(pipeline_file)

def test_verbose_flag_shows_debug_output():
    test_pipeline = {
        "name": "test_verbose",
        "vars": {"test": "value"},
        "steps": [{
            "name": "step1",
            "type": "function",
            "function": "builtins.print",
            "inputs": {"args": ["{{test}}"]}
        }]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name

    try:
        result = subprocess.run(
            ["llmflow", "run", "--pipeline", pipeline_file, "--verbose"],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}
        )

        assert "DEBUG" in result.stderr or "Variables:" in result.stderr
    finally:
        os.remove(pipeline_file)

def test_dry_run_shows_would_run_messages():
    test_pipeline = {
        "name": "test_dry",
        "steps": [
            {"name": "step1", "type": "function", "function": "builtins.print", "inputs": {"args": ["test1"]}},
            {"name": "step2", "type": "function", "function": "builtins.print", "inputs": {"args": ["test2"]}}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name

    try:
        result = subprocess.run(
            ["llmflow", "run", "--pipeline", pipeline_file, "--dry-run"],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}
        )

        assert "Would run: step1" in result.stderr
    finally:
        os.remove(pipeline_file)

def test_no_duplicate_messages():
    test_pipeline = {
        "name": "test_dup",
        "steps": [{
            "name": "unique",
            "type": "function",
            "function": "builtins.print",
            "inputs": {"args": ["test"]}
        }]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name

    try:
        result = subprocess.run(
            ["llmflow", "run", "--pipeline", pipeline_file],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}
        )

        assert result.stderr.count("🔧 Starting function step: unique") == 1
    finally:
        os.remove(pipeline_file)