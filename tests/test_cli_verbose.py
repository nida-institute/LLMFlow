def test_verbose_flag_dry_run():
    runner = CliRunner()
    test_pipeline = {
        "name": "test_verbose",
        "vars": {"test": "value"},
        "steps": [{"name": "step1", "type": "function", "function": "print", "inputs": {"args": ["test"]}}]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name
    try:
        result = runner.invoke(cli, ['run', '--pipeline', pipeline_file, '--var', 'test=123', '--dry-run'], standalone_mode=False)
        assert result.exit_code == 0
        assert "Skipping execution" in result.output
    finally:
        os.remove(pipeline_file)

def test_verbose_short_flag():
    runner = CliRunner()
    test_pipeline = {
        "name": "test_verbose",
        "vars": {"test": "value"},
        "steps": []
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_pipeline, f)
        pipeline_file = f.name
    try:
        result = runner.invoke(cli, ['run', '--pipeline', pipeline_file, '-v', '--dry-run'], standalone_mode=False)
        assert result.exit_code == 0
        assert "Skipping execution" in result.output
    finally:
        os.remove(pipeline_file)