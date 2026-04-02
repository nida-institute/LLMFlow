## VERIFICATION REQUIRED: Does `llm` Package Support response_format?

**Issue:** The discourse-flow project correctly identified that LLMFlow's structured outputs documentation assumes Simon Willison's `llm` package passes the `response_format` parameter through to OpenAI's API. This needs verification.

### Two Code Paths in LLMFlow

1. **Default path (non-MCP):** Uses Simon Willison's `llm` package
   - Code: `model.prompt(prompt, **options)` in `_call_model()` ([llm_runner.py:326](../src/llmflow/utils/llm_runner.py#L326))
   - Filters params through `get_valid_parameters()` which INCLUDES `response_format`
   - **UNKNOWN:** Does `llm` package pass `response_format` to OpenAI API?

2. **MCP tool-calling path:** Uses OpenAI client directly
   - Code: `client.chat.completions.create(**api_params)` in `_run_with_chat_completions()` ([llm_runner.py:767](../src/llmflow/utils/llm_runner.py#L767))
   - Explicitly adds `response_format` at line 743-744
   - **VERIFIED:** This path definitely works

### What We Know

✅ **Parameter is included in filtered options:**
```python
# llm_runner.py:118
FAMILY_PARAMETERS = {
    "gpt-4": {
        # ...
        "response_format",  # ← explicitly listed
    }
}

# llm_runner.py:319-323
valid_llm_params = get_valid_parameters(model_name)
options = {
    k: v for k, v in config.items() if k != "model" and k in valid_llm_params
}
# response_format will be in options if present in config
```

❓ **Unknown: Does `llm` package pass it through?**
- The `llm` package by Simon Willison wraps multiple providers
- It may filter parameters it doesn't recognize
- It may not support `response_format` at all (as of version 0.29+)

### Verification Steps

**Option 1: Test with actual OpenAI call**
```bash
cd /Users/jonathan/github/nida-institute/LLMFlow
hatch shell

python3 << 'EOF'
import llm

# Get OpenAI model
model = llm.get_model("gpt-4o-2024-08-06")

# Try passing response_format
response = model.prompt(
    "Return JSON with a 'message' field saying 'Hello'",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "test",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
                "additionalProperties": False
            }
        }
    }
)

print(response.text())
EOF
```

**Expected results:**
- ✅ If it works: Returns valid JSON `{"message": "Hello"}`
- ❌ If it fails: Either error about unknown parameter, or returns text instead of JSON

**Option 2: Check `llm` package source**
```bash
# Find where llm is installed
python3 -c "import llm; print(llm.__file__)"

# Check if response_format is supported
grep -r "response_format" $(python3 -c "import llm, os; print(os.path.dirname(llm.__file__))")
```

**Option 3: Use MCP path (known to work)**

If `llm` package doesn't support it, pipelines can use the MCP path by adding a dummy MCP server:

```yaml
steps:
  - name: json_step
    type: llm
    model: gpt-4o-2024-08-06
    output_type: json
    response_format:
      type: json_schema
      json_schema:
        # ... schema
    mcp:
      enabled: true  # Forces MCP path which uses OpenAI client directly
      server: none   # No actual MCP server needed
      tools: []      # Empty tools list
```

### Recommended Actions

**For discourse-flow (URGENT):**

1. **Test immediately:**
   ```bash
   # In discourse-flow repo
   python3 -c "import llm; m = llm.get_model('gpt-4o-2024-08-06'); print(m.prompt('Return JSON: {\"test\": 1}', response_format={'type': 'json_object'}).text())"
   ```

2. **If test fails:** Use MCP path workaround above OR request LLMFlow add direct OpenAI fallback

3. **If test succeeds:** Document the `llm` version requirement in your pipeline

**For LLMFlow (this repo):**

1. **Add integration test:** Create `tests/test_response_format_integration.py` that actually calls OpenAI with response_format (skipped unless `OPENAI_API_KEY` set)

2. **Add fallback path:** If `llm` package doesn't support it, add direct OpenAI client option:
   ```python
   if "response_format" in config and not mcp_enabled:
       # Use direct OpenAI client for structured outputs
       return _call_with_openai_client(model_name, prompt, config)
   ```

3. **Update documentation:** Add note about `llm` package version requirements or MCP workaround

### Status

- **Blocker confirmed:** Cannot guarantee structured outputs work through default path
- **Workaround exists:** MCP path definitely works (uses OpenAI client directly)
- **Action needed:** Verify `llm` package support OR document MCP path requirement
