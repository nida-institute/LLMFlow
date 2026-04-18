# Regex Audit: Replace with Proper Parsers

**Status:** Open — tracked in #138  
**Principle:** Use parsers that understand the language being parsed. Regex on structured
languages fails on inputs the author didn't anticipate; a parser fails loudly and predictably.

---

## Category A — Replace (high confidence)

### A1: `str.isidentifier()` instead of regex — `gui/executor.py:17`

```python
_VALID_VAR_KEY = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
```

Validates Python identifiers. Python has a built-in for this:

```python
key.isidentifier()
```

Simple one-line fix. No regex needed.

---

### A2: Root variable extraction still uses regex split — `linter.py:592`, `linter.py:1141-1142`

Two places in the linter still use the old regex split to extract the root variable name
from `${...}` expressions:

```python
# linter.py:592
root_var = re.split(r'[.\[]', var)[0]

# linter.py:1141-1142
for m in re.findall(r'\$\{([^}]+)\}', obj):
    root = re.split(r'[.\[]', m.strip())[0]
```

`_identifiers_in_expr()` (linter.py:18) already does this correctly with `ast.parse`.
These two spots were missed when the top-level `extract_variable_references()` was fixed.
Both should call `_identifiers_in_expr()` instead.

---

### A3: `get_from_context()` parses Python accessor syntax with regex — `runner.py:164, 170, 193`

```python
parts = re.split(r"\.(?![^\[]*\])", expr)       # split on dots not inside brackets
m = re.match(r"^([a-zA-Z0-9_]+)(.*)$", part)    # extract identifier + bracket tail
bracket_matches = re.findall(r"\[([^\]]+)\]", bracket_section)
```

This is a hand-rolled parser for Python attribute/index access expressions (`foo.bar[0].baz`).
The ` is None` tail-stripping bug that caused the `${x is None}` condition failure was a
direct consequence of this regex matching the leading identifier and silently ignoring
the operator tail.

**Replacement:** Parse with `ast.parse(expr, mode='eval')` and walk the AST to resolve
`ast.Attribute`, `ast.Subscript`, and `ast.Name` nodes against the context dict. This is
what `_eval_node()` in `guards.py` already does — `get_from_context()` should delegate to it
rather than reimplementing attribute/subscript access with regex.

---

### A4: YAML frontmatter extraction with regex — `runner.py:437-442`, `linter.py:137, 149, 205`

```python
# YAML block
re.search(r"^---[ \t]*\n.*?\n---[ \t]*\n?", text, re.DOTALL | re.MULTILINE)
# HTML comment block  
re.search(r"<!--(.*?)-->", text, re.DOTALL)
```

Used to extract the frontmatter header from `.gpt` prompt files. The extracted content is
then parsed with `yaml.safe_load()` — so the regex is only doing the boundary detection.
`python-frontmatter` (or a small manual split on `---`) would be more robust and
deduplicated. Currently identical patterns appear in three separate places.

**Replacement:** Extract a single `parse_prompt_frontmatter(text)` helper that splits on
`---` boundaries using `str.split('---', 2)` and passes the middle section to
`yaml.safe_load()`. For the HTML comment variant, use a simple `text.index('<!--')` /
`text.index('-->')` pair. No regex needed.

---

### A5: Markdown code fence extraction — `llm_response_clean.py:11`, `plugins/insert_references.py:49, 54, 59`

```python
# llm_response_clean.py
fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"

# insert_references.py — three cascading fallbacks
re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
re.search(r'\{.*\}', text, re.DOTALL)
```

Extracts JSON from LLM responses that may be wrapped in markdown code fences. The
`r'\{.*\}'` greedy fallback is particularly risky — it will match from the first `{`
to the last `}` in the entire response, grabbing everything in between.

**Replacement:** 
1. Split on ` ``` ` as a literal string delimiter (no regex needed for fence detection).
2. For each candidate block, attempt `json.loads()` — if it parses, use it.
3. If no fence found, scan for `{` and attempt progressive `json.loads()` from each
   candidate start position (brace-counting), which is what `json_parser.py` partially
   does already.

Consolidate all three variants into a single `extract_json_from_llm_response(text)`
function in `modules/json_parser.py`.

---

## Category B — Worth replacing (moderate confidence)

### B1: `resolve()` template substitution — `runner.py:340, 353, 371-372`

```python
re.match(r"^\$\{([^\}]+)\}$", value)   # exact ${...} match
re.match(r"^\{([^\}]+)\}$", value)     # exact {...} match
re.sub(r"\$\{([^\}]+)\}", replace_var, value)   # inline substitution
re.sub(r"\{([^\}]+)\}", replace_var, value)
```

These patterns are repeated verbatim at `runner.py:1534` and across `linter.py` and
`io.py`. The `${...}` boundary detection is mechanically simple but scattered.

**Replacement:** Centralize into a `TemplateString` helper module with:
- `is_sole_reference(s)` — True if the whole string is a single `${...}` or `{...}`
- `extract_expression(s)` — returns the inner expression
- `substitute(s, resolver)` — applies `resolver` to every `${...}` occurrence

This reduces duplication and makes the boundary logic testable in one place.

---

### B2: `io.py` template variable extraction — `io.py:82, 109, 139, 146`

```python
re.sub(r"\{\{\s*([^\}]+?)\s*\}\}", replacer, template_content)
re.findall(r"\$\{([^}]+)\}", template_content)
re.finditer(curly_pattern, template_content)
re.finditer(dollar_pattern, template_content)
```

`{{var}}` substitution in `.gpt` prompt files. The `{{...}}` syntax is Jinja2-adjacent
but this project deliberately avoids Jinja2. The patterns are simple enough that regex
is defensible, but centralizing into `TemplateString` (B1 above) would eliminate
duplication between `io.py`, `linter.py`, and `runner.py`.

---

### B3: Log line timestamp stripping — `gui/executor.py:151`

```python
pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - \w+ - '
cleaned = re.sub(pattern, '', line)
```

Strips the timestamp/level prefix from a log line before displaying in the GUI.

**Replacement:** Use Python's `logging` module's `LogRecord` parsing or switch to
structured logging (JSON log lines) so the GUI can parse fields without knowing the
format string. At minimum, extract the format string from the logger configuration
rather than duplicating it here.

---

## Category C — Regex is appropriate

These are fine as-is:

| Location | Pattern | Reason |
|---|---|---|
| `io.py:32` | `re.sub(r"[^\w]+", "_", ...)` | Filename sanitization — simple char class |
| `context.py:54` | `re.sub(r"^#+\s*", "", line)` | Strip `#` heading markers — trivial |
| `cli_utils.py:551` | `re.escape(begin) + r".*?" + re.escape(end)` | Dynamic delimiters require `re.escape` |
| `linter.py:1202` | `re.search(r"\$\{item\b", group_by)` | Sanity check for user intent |
| `json_parser.py:33` | `re.sub(r'\\(?!["\\/bfnrtu])', '', ...)` | JSON escape repair — negative lookahead |
| `xml_entry_to_base_json.py:96` | `re.split(r'([,;.])', text)` | Punctuation split with capture |

---

## Recommended order of attack

1. **A1** — `str.isidentifier()` for identifier validation (5 minutes)
2. **A2** — Fix the two missed regex-split spots in `linter.py` to use `_identifiers_in_expr()` (15 minutes)
3. **A4** — Centralize frontmatter extraction into one helper, delete three copies (30 minutes)
4. **A5** — Consolidate JSON-from-LLM extraction into `json_parser.py` (1 hour)
5. **B1/B2** — `TemplateString` helper to centralize `${...}` / `{{...}}` handling (2 hours)
6. **A3** — Rewrite `get_from_context()` to use AST (biggest, most careful — needs its own branch)
