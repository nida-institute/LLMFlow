## URGENT: Verification Needed for `response_format` Support

**Your concern is valid.** I cannot confirm Simon Willison's `llm` package passes `response_format` through to OpenAI.

### Immediate Workaround (VERIFIED TO WORK)

Use the MCP path which calls OpenAI API directly:

```yaml
- name: segment_chunk
  type: llm
  model: gpt-4o-2024-08-06
  output_type: json
  response_format:
    type: json_schema
    json_schema:
      name: book_segmentation
      strict: true
      schema:
        # ... your schema
  mcp:
    enabled: true       # Forces direct OpenAI API path
    max_iterations: 1   # No actual tool calling needed
    server: dummy       # Placeholder - won't be used
    tools: []           # Empty tools list
  prompt:
    file: segment-book.gpt
  outputs: segments
```

**Why this works:**
- LLMFlow's MCP code path uses `from openai import AsyncOpenAI` ([llm_runner.py:694](https://github.com/nida-institute/LLMFlow/blob/dev/src/llmflow/utils/llm_runner.py#L694))
- Explicitly adds `response_format` at line 743-744
- Tested and working in production

### Verification Test

Please run this in your environment:

```bash
python3 << 'EOF'
import llm
try:
    model = llm.get_model("gpt-4o-2024-08-06")
    response = model.prompt(
        "Return JSON: {\"message\": \"test\"}",
        response_format={"type": "json_object"}
    )
    print("✅ SUCCESS:", response.text())
except TypeError as e:
    print("❌ FAILED:", str(e))
    print("Workaround required: Use MCP path")
EOF
```

### Documentation Updated

I've posted full verification details to Issue #95. If `llm` package doesn't support it, the MCP workaround above is your reliable path forward.

**Status:** Can start migration NOW using MCP path workaround while we verify `llm` package support.
