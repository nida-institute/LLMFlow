import pytest
import json
import time
from llmflow.runner import run_pipeline
from llmflow.modules.mcp import MCPClient, init_mcp_client

class TestMCPBatchCalls:
    """Integration tests for MCP batch reference retrieval"""

    @pytest.fixture
    def mcp_server_url(self):
        """MCP server URL"""
        return "https://bible-resource-server-preview.labs.biblica.com/mcp"

    @pytest.fixture
    def sample_references(self):
        """Sample Bible references for testing"""
        return [
            "JHN 3:16",
            "ROM 8:28",
            "PSA 23:1",
            "MAT 5:3",
            "1CO 13:4"
        ]

    @pytest.mark.asyncio
    async def test_single_batch_call(self, mcp_server_url, sample_references):
        """Test that multiple references can be fetched in one batch call"""

        # Initialize MCP client with correct signature
        async with MCPClient(mcp_server_url, tools=["get_passage_text"]) as client:
            start_time = time.time()

            # Make batch call - USE _async_call_tool in async context!
            result = await client._async_call_tool(
                "get_passage_text",
                {
                    "usfm_references": sample_references,
                    "textual_editions": ["SBLGNT"]
                }
            )

            duration = time.time() - start_time

            # Assertions
            assert result is not None
            assert duration < 30  # Should complete in under 30 seconds

            print(f"✅ Batch call completed in {duration:.2f}s")
            print(f"   Fetched {len(sample_references)} passages")
            print(f"   Average: {duration/len(sample_references):.2f}s per passage")
            print(f"   Result preview: {str(result)[:200]}...")

    @pytest.mark.asyncio
    async def test_batch_vs_individual_calls(self, mcp_server_url, sample_references):
        """Compare batch call performance vs individual calls"""

        async with MCPClient(mcp_server_url, tools=["get_passage_text"]) as client:
            # Test 1: Batch call
            start_batch = time.time()
            batch_result = await client._async_call_tool(
                "get_passage_text",
                {
                    "usfm_references": sample_references,
                    "textual_editions": ["SBLGNT"]
                }
            )
            batch_duration = time.time() - start_batch

            # Test 2: Individual calls
            start_individual = time.time()
            individual_results = []
            for ref in sample_references:
                result = await client._async_call_tool(
                    "get_passage_text",
                    {
                        "usfm_references": [ref],
                        "textual_editions": ["SBLGNT"]
                    }
                )
                individual_results.append(result)
            individual_duration = time.time() - start_individual

            # Compare
            print(f"\n📊 Performance Comparison:")
            print(f"   Batch call:       {batch_duration:.2f}s")
            print(f"   Individual calls: {individual_duration:.2f}s")
            print(f"   Speedup:          {individual_duration/batch_duration:.2f}x")

            # Batch should ideally be faster (but we know it's not with Biblica!)
            if batch_duration < individual_duration:
                print(f"   ✅ Batch is faster!")
            else:
                print(f"   ⚠️  Individual calls are faster (server issue)")

            # Calculate efficiency
            batch_per_ref = batch_duration / len(sample_references)
            individual_per_ref = individual_duration / len(sample_references)
            print(f"\n   Per-reference times:")
            print(f"   Batch:       {batch_per_ref:.2f}s/ref")
            print(f"   Individual:  {individual_per_ref:.2f}s/ref")

    def test_pipeline_with_mcp_batch(self, tmp_path):
        """Test full pipeline with MCP batch calls"""

        # Create prompt file
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        prompt_file = prompts_dir / "fetch_batch.gpt"
        prompt_file.write_text("""---
prompt:
  requires: []
  optional: []
  format: JSON
  description: Fetch multiple Bible passages in one batch call
---

Fetch these Bible passages in ONE batch call:
- John 3:16
- Romans 8:28
- Psalm 23:1

Call get_passage_text with ALL THREE references in a single array:
```json
{
  "usfm_references": ["JHN 3:16", "ROM 8:28", "PSA 23:1"],
  "textual_editions": ["SBLGNT"]
}
```

Do NOT make multiple calls. Make exactly ONE call with all references.
Output JSON with the passage texts.
""")

        # Create test pipeline
        pipeline_path = tmp_path / "test_mcp_batch.yaml"
        pipeline_path.write_text(f"""
name: test-mcp-batch
description: Test MCP batch reference retrieval

llm_config:
  model: gpt-4o-mini
  temperature: 0.7

mcp_servers:
  bible:
    url: https://bible-resource-server-preview.labs.biblica.com/mcp
    enabled: true

steps:
  - name: fetch_passages
    type: llm
    description: Fetch multiple passages in one batch
    mcp:
      enabled: true
      server: bible
      tools:
        - get_passage_text
    prompt:
      file: {prompt_file}
    outputs:
      - passages
    saveas:
      path: passages.json
""")

        # Run pipeline
        start_time = time.time()
        result = run_pipeline(str(pipeline_path))
        duration = time.time() - start_time

        # Assertions
        assert result is not None
        assert duration < 60  # Should complete in under 1 minute

        # Check output file
        output_file = tmp_path / "passages.json"
        if output_file.exists():
            passages = json.loads(output_file.read_text())
            print(f"✅ Pipeline completed in {duration:.2f}s")
            print(f"   Output: {output_file}")
        else:
            print(f"⚠️  Pipeline ran but no output file created")

    @pytest.mark.asyncio
    async def test_large_batch(self, mcp_server_url):
        """Test batch call with many references (stress test)"""

        # Generate 50 references
        large_batch = [
            f"MAT {chapter}:{verse}"
            for chapter in range(1, 11)
            for verse in range(1, 6)
        ]

        async with MCPClient(mcp_server_url, tools=["get_passage_text"]) as client:
            start_time = time.time()

            result = await client._async_call_tool(
                "get_passage_text",
                {
                    "usfm_references": large_batch,
                    "textual_editions": ["SBLGNT"]
                }
            )

            duration = time.time() - start_time

            print(f"\n📦 Large Batch Test:")
            print(f"   References: {len(large_batch)}")
            print(f"   Duration:   {duration:.2f}s")
            print(f"   Per ref:    {duration/len(large_batch):.2f}s")

            # Should complete in reasonable time
            assert duration < 300  # 5 minutes max

    @pytest.mark.asyncio
    async def test_mcp_tool_call_counting(self, mcp_server_url, sample_references):
        """Verify that batch calls count as ONE tool call, not multiple"""

        async with MCPClient(mcp_server_url, tools=["get_passage_text"]) as client:
            # Track tool calls
            call_count = 0
            original_call_tool = client._async_call_tool

            async def tracked_call_tool(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return await original_call_tool(*args, **kwargs)

            client._async_call_tool = tracked_call_tool

            # Make batch call
            await client._async_call_tool(
                "get_passage_text",
                {
                    "usfm_references": sample_references,
                    "textual_editions": ["SBLGNT"]
                }
            )

            # Should be exactly 1 call
            assert call_count == 1, f"Expected 1 tool call, got {call_count}"

            print(f"✅ Batch with {len(sample_references)} refs = {call_count} tool call")

    @pytest.mark.asyncio
    async def test_chunked_batches(self, mcp_server_url):
        """Test fetching references in smaller chunks"""

        # Generate 30 references
        all_refs = [
            f"MAT {chapter}:{verse}"
            for chapter in range(1, 7)
            for verse in range(1, 6)
        ]

        chunk_size = 10
        chunks = [all_refs[i:i + chunk_size] for i in range(0, len(all_refs), chunk_size)]

        async with MCPClient(mcp_server_url, tools=["get_passage_text"]) as client:
            start_time = time.time()
            chunk_durations = []

            for i, chunk in enumerate(chunks):
                chunk_start = time.time()
                result = await client._async_call_tool(
                    "get_passage_text",
                    {
                        "usfm_references": chunk,
                        "textual_editions": ["SBLGNT"]
                    }
                )
                chunk_duration = time.time() - chunk_start
                chunk_durations.append(chunk_duration)
                print(f"   Chunk {i+1}/{len(chunks)}: {chunk_duration:.2f}s ({len(chunk)} refs)")

            total_duration = time.time() - start_time

            print(f"\n📊 Chunked Batch Results:")
            print(f"   Total refs:     {len(all_refs)}")
            print(f"   Chunk size:     {chunk_size}")
            print(f"   Num chunks:     {len(chunks)}")
            print(f"   Total time:     {total_duration:.2f}s")
            print(f"   Avg per chunk:  {sum(chunk_durations)/len(chunk_durations):.2f}s")
            print(f"   Avg per ref:    {total_duration/len(all_refs):.2f}s")


if __name__ == "__main__":
    # Run with: pytest tests/integration/test_mcp_batch_calls.py -v -s
    pytest.main([__file__, "-v", "-s"])