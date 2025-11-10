"""Test MCP integration in pipeline execution."""

import pytest
from pathlib import Path
import yaml

def test_pipeline_mcp_configuration():
    """Test that pipeline has valid MCP configuration."""
    pipeline_file = Path("pipelines/semlex-multipass.yaml")

    if not pipeline_file.exists():
        pytest.skip("Pipeline file not found")

    # Load pipeline YAML
    with open(pipeline_file) as f:
        config = yaml.safe_load(f)

    # Check MCP servers defined at root level
    assert "mcp_servers" in config, "mcp_servers not defined in pipeline"
    assert "bible" in config["mcp_servers"], "bible server not defined"

    bible_server = config["mcp_servers"]["bible"]
    assert "url" in bible_server, "bible server missing URL"
    assert "biblica.com/mcp" in bible_server["url"], "unexpected bible server URL"

    print(f"✅ MCP server configured: {bible_server['url']}")

    # Find the process-entries step
    pipeline = config.get("pipeline", config)
    steps = pipeline.get("steps", [])

    process_entries_step = None
    for step in steps:
        if step.get("name") == "process-entries":
            process_entries_step = step
            break

    assert process_entries_step is not None, "process-entries step not found"
    assert process_entries_step.get("type") == "for-each", "process-entries should be for-each"

    # Check nested verify-citations step
    nested_steps = process_entries_step.get("steps", [])
    verify_step = None
    for step in nested_steps:
        if step.get("name") == "verify-citations":
            verify_step = step
            break

    assert verify_step is not None, "verify-citations step not found"
    assert verify_step.get("type") == "llm", "verify-citations should be llm step"

    # Check MCP configuration
    mcp_config = verify_step.get("mcp", {})
    assert mcp_config.get("enabled") == True, "MCP not enabled for verify-citations"
    assert mcp_config.get("server") == "bible", "MCP server should be 'bible'"

    print(f"✅ MCP enabled for verify-citations step")
    print(f"   Server: {mcp_config.get('server')}")
    print(f"   Tools: {mcp_config.get('tools', 'all')}")


def test_runner_has_mcp_support():
    """Test that runner module has MCP integration."""
    from llmflow.runner import run_llm_step
    from llmflow.modules.mcp import init_mcp_client
    from llmflow.utils.llm_runner import run_llm_with_mcp_tools

    # Check imports exist
    assert run_llm_step is not None
    assert init_mcp_client is not None
    assert run_llm_with_mcp_tools is not None

    print("✅ Runner has MCP support")


def test_mcp_module_structure():
    """Test MCP module has required components."""
    from llmflow.modules.mcp import MCPClient, init_mcp_client

    # Check classes/functions exist
    assert MCPClient is not None
    assert init_mcp_client is not None

    # Check MCPClient has required methods
    assert hasattr(MCPClient, '__aenter__')
    assert hasattr(MCPClient, '__aexit__')
    assert hasattr(MCPClient, '_async_get_tool_definitions')
    assert hasattr(MCPClient, '_async_call_tool')

    print("✅ MCP module structure is correct")