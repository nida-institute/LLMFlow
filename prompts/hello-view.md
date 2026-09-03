# hello.gpt

```yaml
---
requires:
  - language_count
format: Markdown
description: Generate a multilingual greeting list for {language_count} languages.
---
system: |
  You are a friendly assistant who showcases multilingual greetings.
user: |
  Pick {{language_count}} languages randomly.
  For each one, identify the language in English, share a native-script greeting,
  and add a short cultural note.
  Respond as a markdown bullet list.
```
