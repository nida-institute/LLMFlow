# Audits

Store pipeline QA reports, output review notes, and lint snapshots here.

## Suggested naming

```
YYYY-MM-DD_<passage-or-scope>_<pipeline-or-step>.md
```

Examples:
- `2026-03-17_Ruth-1_storyflow-psalms.md`
- `2026-03-18_full-run_semlex-multipass.md`

## What belongs here

- Manual review of LLM outputs (correctness, tone, coverage)
- Notes on specific failures and how they were resolved
- Before/after comparisons when a prompt or pipeline changes
- Coverage validator reports

## What does not belong here

- Pipeline YAML files → `pipelines/`
- Generated artifacts → `output/`
- Active tasks → `project/TODO.md`
