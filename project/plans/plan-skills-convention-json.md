# Plan: Issues #163, #164, and new `type: json` step — Rolling file convention + skill distribution fix + JSON construction step

**Status:** Implemented — historical record. Describes why the code looks as it does; do not rebuild from it. Verify against the code before relying on any detail.

`type: json` shipped as `steps/json_step.py` (`tests/test_json_step.py`). The skills and
rolling-file conventions in the later sections were part of the same plan — check each
against the code rather than assuming it followed.

## Context

Three items:

- **#163**: The project convention of one rolling file per pipeline (`project/audits/audit-{pipeline}.md`, `project/plans/{pipeline}-plan.md`) is not documented or distributed.
- **#164**: `install_global_skills()` hardcodes `audit-prompts` — only that one skill ships. Six other skills exist in `~/.sp/skills/` but are absent from the templates. A broken `scope-check` symlink and an orphaned `stand-down` symlink (pointing to `human-at-the-helm`) make the state confusing. `authorize` is missing from `~/.claude/skills/`.
- **New (`type: json` step)**: No declarative step type exists for constructing a JSON object/array from in-scope variables mid-pipeline. The `variables:` section handles static construction, but can't assemble values from step outputs. A new `type: json` step fills this gap.

---

## Issue #163 — Rolling file convention

### What to add

New file: `src/llmflow/templates/sp-conventions/llmflow-project-tracking.md`

Content covers:
- `project/audits/audit-{pipeline-name}.md` — one rolling findings file per pipeline, updated in place; items removed when fully resolved; git history is the audit trail
- `project/plans/{pipeline-name}-plan.md` — implementation tasks, checked off and removed when done
- Dates on individual items, not in filenames
- Distinction from `project/audits/audit-<PASSAGE>.md` (per-artifact records, which still follow the existing pattern in `audits-pattern.md`)

### Files touched

| File | Change |
|------|--------|
| `src/llmflow/templates/sp-conventions/llmflow-project-tracking.md` | **New** convention template |
| `docs/ai-context/audits-pattern.md` | Add a paragraph clarifying per-pipeline rolling files vs per-artifact records |
| `docs/ai-context/index.md` | Add entry pointing to the new convention |

### Code change needed?

**None.** `install_global_conventions()` already uses `glob("*.md")` — it will pick up the new file automatically.

### Pytest needed?

**No.** The new template file is structurally identical to existing ones; the existing `test_install_global_conventions_creates_files` covers the install path.

---

## Issue #164 — Skill distribution fix

### Root causes

1. `install_global_skills()` hardcodes `audit-prompts` instead of iterating the templates directory (contrast with `install_global_conventions()` which uses `glob` correctly).
2. Six skills in `~/.sp/skills/` were hand-placed, never added to `src/llmflow/templates/sp-skills/`.
3. `stand-down` is a symlink to a different repo (`human-at-the-helm`), not in the distribution.
4. `scope-check` is a broken symlink — target never existed; no content to recover.
5. `authorize` has no symlink in `~/.claude/skills/` (a pre-existing gap in `_install_claude_skills()` that will be fixed by step 1 once `authorize` is in the templates and re-installed).

### Step 1 — Add missing skills to templates

Copy these files into `src/llmflow/templates/sp-skills/`:

| Skill | Source |
|-------|--------|
| `audit-code/SKILL.md` | `~/.sp/skills/audit-code/SKILL.md` |
| `audit-output/SKILL.md` | `~/.sp/skills/audit-output/SKILL.md` |
| `audit-pipeline/SKILL.md` | `~/.sp/skills/audit-pipeline/SKILL.md` |
| `authorize/SKILL.md` | `~/.sp/skills/authorize/SKILL.md` |
| `commit-ready/SKILL.md` | `~/.sp/skills/commit-ready/SKILL.md` |
| `load-context/SKILL.md` | `~/.sp/skills/load-context/SKILL.md` |
| `stand-down/SKILL.md` | LLMFlow-specific fork (see below) |

### Step 2 — stand-down installation

**Approach: fetch from source, bundled fallback**

During `install_global_skills()`, for `stand-down` specifically:
1. Attempt to fetch from `https://raw.githubusercontent.com/nida-institute/human-at-the-helm/main/skills/stand-down/SKILL.md`
2. On success, write fetched content to `~/.sp/skills/stand-down/SKILL.md`
3. On failure (network error, timeout), fall back to the bundled version in `src/llmflow/templates/sp-skills/stand-down/SKILL.md`

The bundled fallback is still needed for offline installs. Its content: the `../../drift-patterns.md` reference replaced with the relevant drift patterns inline, and `docs/ai-context/rules.md` referenced as the LLMFlow rules source.

### Step 3 — Fix `install_global_skills()`

**File:** `src/llmflow/cli_utils.py`, lines 1586–1614

Rewrite to mirror `install_global_conventions()`:

```python
def install_global_skills(sp_home=None, force=False):
    if sp_home is None:
        sp_home = Path.home() / ".sp"

    import llmflow
    pkg_root = Path(llmflow.__file__).parent
    templates_dir = pkg_root / "templates" / "sp-skills"

    for skill_dir in sorted(templates_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        target_dir = sp_home / "skills" / skill_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "SKILL.md"
        if target.exists() and not force:
            logger.info(f"{skill_dir.name} already exists in ~/.sp/skills/; skipping")
            continue
        target.write_text(skill_file.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info(f"✓ Installed {skill_dir.name} skill to ~/.sp/skills/")
```

### Step 4 — Update tests

**File:** `tests/test_global_conventions.py`

Changes:
1. `test_skill_template_exists()` → replace single `audit-prompts` check with a parametrized test that asserts every expected skill has a `SKILL.md` in the templates. Expected set: `audit-code`, `audit-output`, `audit-pipeline`, `audit-prompts`, `authorize`, `commit-ready`, `load-context`, `release`, `stand-down`.
2. `test_install_global_skills_creates_files()` → assert that ALL templates skills are installed, not just `audit-prompts`.
3. `test_sp_init_installs_global_resources()` → add checks for a sample of the new skills (e.g., `load-context`, `authorize`).
4. New test: `test_installed_skills_match_templates()` — reads the templates directory and asserts the installed set equals the templates set exactly. This is the regression guard against future drift.

### Step 5 — Local cleanup (not distribution)

Remove the broken `scope-check` symlink from `~/.claude/skills/`:
```bash
rm ~/.claude/skills/scope-check
```

### Step 6 — Re-run install to sync local machine

```bash
sp init --update
```

This will push all new skills to `~/.sp/skills/` and then (with user consent) to `~/.claude/skills/`, including `authorize` which was previously missing.

---

## New step type: `type: json`

### Problem

No declarative mid-pipeline step exists for constructing a JSON object or array from variables already in context. The top-level `variables:` section handles static construction, but values there enter context un-resolved and can't reference step outputs. A `function` plugin works but requires a Python file.

### Spec

```yaml
- name: build_scene
  type: json
  output: scene_object
  value:
    scene_id: "${scene.scene_id}"
    canonical_reference: "${scene.canonical_reference}"
    sensory_items: "${scene.sensory_items}"
    spatial_relationships: "${scene.spatial_relationships}"
    social_background: "${scene.social_background}"
    characters: "${scene.characters}"
```

- `output` — name of the context variable the result is bound to (required)
- `value` — any YAML value (object, array, scalar); `${var}` references resolved via `resolve()` at step execution time
- `value` may be nested arbitrarily; `resolve()` already walks dicts and lists recursively

Arrays are also valid:

```yaml
- name: collect_ids
  type: json
  output: id_list
  value:
    - "${scene.scene_id}"
    - "${passage.id}"
```

### Files touched

| File | Change |
|------|--------|
| `src/llmflow/runner.py` | Add `"json"` branch in step dispatch (~10 lines); call `run_json_step()` |
| `src/llmflow/runner.py` | Add `run_json_step()` function: resolve `value`, store to `output` in context |
| `src/llmflow/utils/linter.py` | Register `json` as valid step type; validate `output` and `value` keys present |
| `docs/llmflow-language.md` | Add `type: json` section with example |
| `docs/llmflow-language-quickref.md` | Add one-line entry |
| `pipelines/json-step-example.yaml` | New demo pipeline showing `type: json` usage |
| `tests/test_json_step.py` | New test file: object construction, array construction, nested, dot-notation vars, missing output key error |

### Pytest

Yes — new `tests/test_json_step.py`. Key cases:
- Basic object construction from flat vars
- Nested object
- Array value
- Dot-notation variable references (`${scene.scene_id}`)
- `output` key missing → linter error
- `value` key missing → linter error
- Unknown variable reference → passes through un-resolved (consistent with `resolve()` behavior)

---

## Files touched summary

| File | Change |
|------|--------|
| `src/llmflow/templates/sp-conventions/llmflow-project-tracking.md` | New |
| `src/llmflow/templates/sp-skills/audit-code/SKILL.md` | New (copied from installed) |
| `src/llmflow/templates/sp-skills/audit-output/SKILL.md` | New (copied from installed) |
| `src/llmflow/templates/sp-skills/audit-pipeline/SKILL.md` | New (copied from installed) |
| `src/llmflow/templates/sp-skills/authorize/SKILL.md` | New (copied from installed) |
| `src/llmflow/templates/sp-skills/commit-ready/SKILL.md` | New (copied from installed) |
| `src/llmflow/templates/sp-skills/load-context/SKILL.md` | New (copied from installed) |
| `src/llmflow/templates/sp-skills/stand-down/SKILL.md` | New (LLMFlow fork) |
| `src/llmflow/cli_utils.py` | Fix `install_global_skills()` — dynamic iteration |
| `src/llmflow/runner.py` | Add `type: json` step dispatch + `run_json_step()` |
| `src/llmflow/utils/linter.py` | Register `json` as valid step type |
| `docs/llmflow-language.md` | Add `type: json` section |
| `docs/llmflow-language-quickref.md` | Add `type: json` entry |
| `docs/ai-context/audits-pattern.md` | Add per-pipeline rolling file section |
| `docs/ai-context/index.md` | Add convention index entry |
| `pipelines/json-step-example.yaml` | New demo pipeline |
| `tests/test_global_conventions.py` | Update + add regression test |
| `tests/test_json_step.py` | New |

## Verification

1. `hatch run pytest tests/test_global_conventions.py tests/test_json_step.py -v` — all tests green
2. `hatch run pytest` — full suite clean
3. `sp lint --pipeline pipelines/json-step-example.yaml` — passes
4. `sp run --pipeline pipelines/json-step-example.yaml --dry-run` — no LLM calls, output shows resolved object
5. `sp init --update` on this machine — observe all skills installed including `authorize` and `stand-down`
6. Confirm `~/.claude/skills/` matches `~/.sp/skills/` (no orphaned entries)
