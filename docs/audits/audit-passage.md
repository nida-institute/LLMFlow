# Audit: Passage Output

**STOP if:**
- File is not markdown
- Content is empty or just boilerplate
- Passage reference is missing or malformed

## Checklist

- [ ] Passage reference matches the expected book/chapter/verses
- [ ] Output format is valid markdown (headings, paragraphs, lists)
- [ ] No untranslated source-language text appears (unless intentional)
- [ ] Tone matches project style guide (formal/informal/devotional)
- [ ] Length is appropriate for passage scope (not truncated, not padded)
- [ ] Cross-references or footnotes (if expected) are present and correctly formatted
- [ ] No placeholder text like "TODO" or "[insert content]"
- [ ] File naming convention: `<BOOK>-<CHAPTER>-<VERSES>.md` (e.g. `LUK-1-1-10.md`)

## Shell Commands

```bash
# Count passages processed today
find output/ -name "*.md" -mtime -1 | wc -l

# Check for placeholder text
grep -r "TODO\|insert content\|FIXME" output/

# Validate markdown structure
markdownlint output/*.md
```

## Pass/Fail Criteria

**Pass:** All checkboxes marked, no STOP conditions triggered.
**Fail:** Any STOP condition OR 2+ checkboxes unchecked.
