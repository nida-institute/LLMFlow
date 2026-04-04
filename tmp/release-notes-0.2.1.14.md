# LLMFlow v0.2.1.14

## Highlights

This release focuses on **type safety**, **content lifecycle management**, and **stability improvements**.

- ✅ **1888 tests passing** with zero Pyright type errors
- ✅ **CI type checking** - prevents type regressions in PRs
- ✅ **Content lifecycle system** - manage content through stages (draft → editing → published)
- ✅ **GUI architecture documentation** - prevent drift between dev/production servers

## Type Safety & CI

- **Added Pyright to CI pipeline** - Type checking now runs on every PR
- **Zero type errors** in `src/llmflow/` - Fixed all 191 original errors
- **Type coverage** - Added type stubs for PyYAML, Flask, jsonschema, Markdown
- **Standard mode** - Using Pyright's "standard" type checking level
- **Test infrastructure** - `tests/test_types.py` enforces zero-tolerance policy

## Content Lifecycle System

Complete system for managing content through lifecycle stages:

- **Stage transitions** - Copy/move/symlink files between stages
- **Permission management** - Sentinel-based file permissions (`.sp-permissions`)
- **Git integration** - Auto-commit, tag creation, metadata tracking
- **Validation** - Schema validation, requirement checks, approval workflows
- **Metadata** - Track transitions, editors, timestamps
- **Full test coverage** - 100+ tests covering all lifecycle features

Files: `content_stages_schema.py`, `content_transition.py`, `content_list.py`, `content_status.py`, `content_diff.py`

## GUI Improvements

- **Fixed file selection bug** (Issue #110) - Draft file clicks now work correctly
- **Architecture docs** - Documented dual-server setup to prevent drift
- **Test coverage** - Added `test_gui_api_contract.py`, `test_gui_button_states.py`
- **Type safety** - Fixed null pointer issues in GUI server routes

## Documentation

- **AI context improvements** - Added "READ THIS FIRST" warnings in `docs/ai-context/index.md`
- **GUI architecture guide** - `docs/ai-context/gui-architecture.md` with workflow docs
- **Updated instructions** - `.github/copilot-instructions.md` and `CLAUDE.md`
- **Prevent duplication** - Index warns about existing functionality (bible parsing, YAML steps)

## Bug Fixes

- Fixed Pydantic Field() syntax in content_stages_schema.py
- Added field aliases for YAML compatibility (`from`/`to` → `from_stage`/`to_stage`)
- Fixed covariance issues in guards.py (Dict→Mapping, List→Sequence)
- Added null checks for Flask app.static_folder

## Testing

- **1888 tests passing**, 12 skipped
- **Runtime**: ~75 seconds full test suite
- **Coverage**: Content lifecycle, GUI API, type checking, model metadata
- **CI integration**: Pyright runs on every build

## Closed Issues

- #102 - Pyright type checking in CI
- #110 - Draft file "File not Found" error (GUI)

## Contributors

- Jonathan Robie (@jonathanrobie)
