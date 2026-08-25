import logging
from pathlib import Path

import pytest

from llmflow.cli import main
from llmflow.cli_utils import (
    HELLO_PIPELINE,
    HELLO_PROMPT,
    HELLO_REPLY_PROMPT,
    AI_INDEX_DOC,
    AI_OVERVIEW_DOC,
    AI_RULES_DOC,
    ASSISTANT_RULES_POINTER,
    LANGUAGE_QUICKREF_DOC,
    PROJECT_AUDITS_README,
    PROJECT_TODO,
    TUTORIAL_DOC,
    VSCODE_DOC,
    init_project as init_environment,
)


def test_cli_init_creates_hello_prompt(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.chdir(tmp_path)

    main(["init"])

    prompt_path = tmp_path / "prompts" / "hello.gpt"
    assert prompt_path.exists()
    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT

    # second run should be idempotent
    main(["init"])
    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT


def test_init_environment_creates_files(tmp_path, caplog):
    caplog.set_level(logging.INFO)

    init_environment(tmp_path)

    prompt_path = tmp_path / "prompts" / "hello.gpt"
    reply_prompt_path = tmp_path / "prompts" / "reply.gpt"
    pipeline_path = tmp_path / "pipelines" / "hello-llmflow.yaml"
    output_dir = tmp_path / "outputs"
    docs_dir = tmp_path / "docs"
    ai_context_dir = docs_dir / "ai-context"

    tutorial_doc_path = docs_dir / "tutorial.md"
    language_quickref_path = docs_dir / "llmflow-language-quickref.md"
    ai_overview_path = ai_context_dir / "project" / "overview.md"
    ai_rules_path = ai_context_dir / "sp" / "rules.md"
    ai_project_index_path = ai_context_dir / "project" / "index.md"

    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT
    assert reply_prompt_path.read_text(encoding="utf-8") == HELLO_REPLY_PROMPT
    assert pipeline_path.read_text(encoding="utf-8") == HELLO_PIPELINE
    assert output_dir.is_dir()

    assert tutorial_doc_path.read_text(encoding="utf-8") == TUTORIAL_DOC
    assert language_quickref_path.read_text(encoding="utf-8") == LANGUAGE_QUICKREF_DOC
    assert ai_overview_path.read_text(encoding="utf-8") == AI_OVERVIEW_DOC
    assert ai_rules_path.read_text(encoding="utf-8") == AI_RULES_DOC
    assert ai_project_index_path.read_text(encoding="utf-8") == AI_INDEX_DOC

    vscode_doc_path = docs_dir / "vscode.md"
    project_todo_path = tmp_path / "project" / "TODO.md"
    project_audits_readme_path = tmp_path / "project" / "audits" / "README.md"

    assert vscode_doc_path.read_text(encoding="utf-8") == VSCODE_DOC
    assert project_todo_path.read_text(encoding="utf-8") == PROJECT_TODO
    assert project_audits_readme_path.read_text(encoding="utf-8") == PROJECT_AUDITS_README

    # idempotency: second run should not change existing files
    init_environment(tmp_path)
    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT
    assert reply_prompt_path.read_text(encoding="utf-8") == HELLO_REPLY_PROMPT
    assert pipeline_path.read_text(encoding="utf-8") == HELLO_PIPELINE
    assert tutorial_doc_path.read_text(encoding="utf-8") == TUTORIAL_DOC
    assert language_quickref_path.read_text(encoding="utf-8") == LANGUAGE_QUICKREF_DOC
    assert ai_overview_path.read_text(encoding="utf-8") == AI_OVERVIEW_DOC
    assert ai_rules_path.read_text(encoding="utf-8") == AI_RULES_DOC
    assert ai_project_index_path.read_text(encoding="utf-8") == AI_INDEX_DOC
    # project/TODO.md must never be overwritten — it's hand-edited from first run
    project_todo_path.write_text("# my hand-edited TODO\n", encoding="utf-8")
    init_environment(tmp_path)
    assert project_todo_path.read_text(encoding="utf-8") == "# my hand-edited TODO\n"


def test_init_update_overwrites_what_sp_owns_and_leaves_the_rest(tmp_path):
    """`--update` decides by catalog `policy`, not by the generated marker.

    Changed 2026-08-25 (#214). This test previously asserted the marker contract — *"overwrites
    files carrying the generated marker, leaves hand-edited files alone"* — which protected
    nothing: `sp doctor` keys on `policy` and overwrote the same hand edit on its next run, so
    the two commands gave opposite answers about the same file.

    The Captain, on which way they should agree: *"hand edits to ~/.sp files should not be
    protected. it's the wrong place to put them."* A project's own content belongs under
    `docs/ai-context/project/`, which is `create-once` and which sp never touches.

    Measured on the same day: only 5 of 12 `generated` documents begin with the marker, and 5 of
    9 `create-once` documents do — so the marker could not carry ownership in either direction.
    """
    init_environment(tmp_path)

    # policy: generated, and no marker in its shipped content — the case the marker missed.
    pipeline_path = tmp_path / "pipelines" / "hello-llmflow.yaml"
    pipeline_path.write_text("# hand-edited pipeline\n", encoding="utf-8")

    # policy: generated, stale content.
    quickref_path = tmp_path / "docs" / "llmflow-language-quickref.md"
    quickref_path.write_text("# OLD CONTENT\n", encoding="utf-8")

    # policy: create-once — the project's, and never overwritten however it is marked.
    project_rules = tmp_path / "docs" / "ai-context" / "project" / "rules.md"
    project_rules.write_text("<!-- Generated by sp init -->\n# mine\n", encoding="utf-8")

    init_environment(tmp_path, update=True)

    assert quickref_path.read_text(encoding="utf-8") == LANGUAGE_QUICKREF_DOC
    assert pipeline_path.read_text(encoding="utf-8") == HELLO_PIPELINE, (
        "A `generated` file must be refreshed by --update whether or not it carries the marker."
    )
    assert project_rules.read_text(encoding="utf-8") == "<!-- Generated by sp init -->\n# mine\n", (
        "A `create-once` file is the project's. The marker must not make sp claim it."
    )


def test_init_update_flag_via_cli(tmp_path, monkeypatch):
    """llmflow init --update works via the CLI entrypoint."""
    monkeypatch.chdir(tmp_path)
    main(["init"])

    quickref_path = tmp_path / "docs" / "llmflow-language-quickref.md"
    quickref_path.write_text("<!-- Generated by sp init -->\n# OLD\n", encoding="utf-8")

    main(["init", "--update"])

    assert quickref_path.read_text(encoding="utf-8") == LANGUAGE_QUICKREF_DOC


class TestHelloGptContract:
    """hello.gpt and reply.gpt must declare variable contracts parseable by the linter."""

    def test_hello_prompt_has_requires_header(self, tmp_path):
        """HELLO_PROMPT must have a ---...--- frontmatter with requires: listing language_count."""
        from llmflow.utils.linter import parse_prompt_header

        p = tmp_path / "hello.gpt"
        p.write_text(HELLO_PROMPT, encoding="utf-8")
        header = parse_prompt_header(str(p))
        assert header is not None, "HELLO_PROMPT has no parseable header"
        requires = header.get("requires", [])
        assert "language_count" in requires, (
            f"HELLO_PROMPT header must declare 'language_count' in requires, got: {requires}"
        )

    def test_reply_prompt_has_requires_header(self, tmp_path):
        """HELLO_REPLY_PROMPT must have a ---...--- frontmatter with requires: listing greeting_markdown."""
        from llmflow.utils.linter import parse_prompt_header

        p = tmp_path / "reply.gpt"
        p.write_text(HELLO_REPLY_PROMPT, encoding="utf-8")
        header = parse_prompt_header(str(p))
        assert header is not None, "HELLO_REPLY_PROMPT has no parseable header"
        requires = header.get("requires", [])
        assert "greeting_markdown" in requires, (
            f"HELLO_REPLY_PROMPT header must declare 'greeting_markdown' in requires, got: {requires}"
        )


def test_init_with_sync_flag_creates_ai_context_dir(tmp_path, monkeypatch, caplog):
    """llmflow init --sync creates .github/ai-context/ directory structure."""
    caplog.set_level(logging.INFO)
    monkeypatch.chdir(tmp_path)

    # Run init with --sync flag
    # Note: sync_ai_context_files may warn if not in an installed package,
    # but it should still create the directory structure
    main(["init", "--sync"])

    ai_context_dir = tmp_path / ".github" / "ai-context"
    assert ai_context_dir.exists(), ".github/ai-context/ should be created"
    assert ai_context_dir.is_dir(), ".github/ai-context/ should be a directory"


class TestSpCliName:
    """All generated template content must reference 'sp' as the CLI command, not 'llmflow'."""

    def test_hello_pipeline_uses_sp_not_llmflow(self):
        """HELLO_PIPELINE description must say 'sp run', not 'llmflow run'."""
        assert "sp run" in HELLO_PIPELINE, (
            "HELLO_PIPELINE must reference 'sp run' — the CLI was renamed from 'llmflow' to 'sp'"
        )
        assert "llmflow run" not in HELLO_PIPELINE, (
            "HELLO_PIPELINE must not reference 'llmflow run' — the CLI was renamed to 'sp'"
        )

    def test_tutorial_doc_uses_sp_not_llmflow(self):
        """TUTORIAL_DOC must say 'sp run ...', not 'llmflow run ...'."""
        assert "sp run" in TUTORIAL_DOC, (
            "TUTORIAL_DOC must reference 'sp run' — the CLI was renamed from 'llmflow' to 'sp'"
        )
        assert "llmflow run" not in TUTORIAL_DOC, (
            "TUTORIAL_DOC must not reference 'llmflow run' — the CLI was renamed to 'sp'"
        )

    def test_language_quickref_uses_sp_not_llmflow(self):
        """LANGUAGE_QUICKREF_DOC must say 'sp run ...', not 'llmflow run ...'."""
        assert "sp run" in LANGUAGE_QUICKREF_DOC, (
            "LANGUAGE_QUICKREF_DOC must reference 'sp run'"
        )
        assert "llmflow run" not in LANGUAGE_QUICKREF_DOC, (
            "LANGUAGE_QUICKREF_DOC must not reference 'llmflow run'"
        )

    def test_copilot_instructions_uses_sp_not_llmflow(self):
        """ASSISTANT_RULES_POINTER must say 'sp lint/run ...', not 'llmflow lint/run ...'."""
        assert "llmflow run" not in ASSISTANT_RULES_POINTER, (
            "ASSISTANT_RULES_POINTER must not reference 'llmflow run'"
        )
        assert "llmflow lint" not in ASSISTANT_RULES_POINTER, (
            "ASSISTANT_RULES_POINTER must not reference 'llmflow lint'"
        )

    def test_generated_marker_uses_sp(self):
        """GENERATED_MARKER must reference 'sp init', not 'llmflow init'."""
        from llmflow.cli_utils import GENERATED_MARKER
        assert "sp init" in GENERATED_MARKER, (
            f"GENERATED_MARKER must say 'Generated by sp init', got: {GENERATED_MARKER!r}"
        )

    def test_project_todo_uses_sp(self):
        """PROJECT_TODO must not reference 'llmflow' as a CLI command."""
        assert "llmflow run" not in PROJECT_TODO, (
            "PROJECT_TODO must not reference 'llmflow run'"
        )

    def test_sp_entrypoint_in_pyproject(self):
        """pyproject.toml must define 'sp' as a console script entry point."""
        import tomllib
        from pathlib import Path
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        scripts = data.get("project", {}).get("scripts", {})
        assert "sp" in scripts, (
            f"pyproject.toml [project.scripts] must have 'sp' entry, got: {list(scripts.keys())}"
        )
        assert "llmflow" not in scripts, (
            "pyproject.toml [project.scripts] must not have old 'llmflow' entry"
        )


class TestAiContextDocsCoverGptFormat:
    """AI context docs must teach an LLM how to write .gpt variable contract headers."""

    def test_language_quickref_includes_requires_syntax(self):
        """LANGUAGE_QUICKREF_DOC must show 'requires:' so an AI knows to declare it."""
        assert "requires:" in LANGUAGE_QUICKREF_DOC, (
            "LANGUAGE_QUICKREF_DOC must include 'requires:' to teach .gpt contract syntax"
        )

    def test_ai_rules_doc_mentions_prompt_contract(self):
        """AI_RULES_DOC must reference 'requires' so the AI knows to declare prompt contracts."""
        assert "requires" in AI_RULES_DOC, (
            "AI_RULES_DOC must reference 'requires' so the AI knows to declare prompt contracts"
        )


class TestProjectTodoTutorial:
    """PROJECT_TODO must pre-populate with tutorial backlog items guiding new users
    through AI-assisted pipeline exploration and GitHub issue workflow."""

    def test_todo_has_run_command(self):
        """Backlog must show users how to run the hello pipeline."""
        assert "sp run" in PROJECT_TODO, (
            "PROJECT_TODO must include 'sp run' so users know how to run a pipeline"
        )

    def test_todo_has_copilot_explain(self):
        """Backlog must direct users to use Copilot /explain on the pipeline."""
        assert "/explain" in PROJECT_TODO, (
            "PROJECT_TODO must include '/explain' to guide AI-assisted exploration"
        )

    def test_todo_has_github_issues(self):
        """Backlog must reference GitHub issues as a workflow step."""
        assert "issue" in PROJECT_TODO.lower(), (
            "PROJECT_TODO must mention GitHub issues so users connect AI + issue workflow"
        )

    def test_todo_has_extend_step(self):
        """Backlog must prompt user to extend the pipeline with AI help."""
        assert "extend" in PROJECT_TODO.lower() or "implement" in PROJECT_TODO.lower(), (
            "PROJECT_TODO must include a step to extend or implement a new pipeline idea"
        )

    def test_todo_has_debug_step(self):
        """Backlog must include a debugging step with AI."""
        assert "debug" in PROJECT_TODO.lower() or "diagnose" in PROJECT_TODO.lower(), (
            "PROJECT_TODO must include a step for AI-assisted debugging"
        )


class TestHelloYaml:
    """hello.yaml must be created by llmflow init and pass full lint."""

    def test_init_creates_hello_yaml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        main(["init"])
        assert (tmp_path / "pipelines" / "hello.yaml").exists()

    def test_hello_yaml_content_has_variables_block(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        main(["init"])
        import yaml

        content = yaml.safe_load(
            (tmp_path / "pipelines" / "hello.yaml").read_text(encoding="utf-8")
        )
        assert "variables" in content, "hello.yaml must have a variables: block"

    def test_hello_yaml_passes_lint(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        main(["init"])
        from llmflow.utils.linter import lint_pipeline_full

        result = lint_pipeline_full(str(tmp_path / "pipelines" / "hello.yaml"))
        assert result.valid, f"hello.yaml failed lint: {result.errors}"


class TestAiContextConsistency:
    """AI context files must be consistent and up-to-date."""

    def test_sp_index_references_the_documents_sp_ships(self):
        """The inventory claim belongs to sp-index.md, not the project's own starter map.

        Moved 2026-08-24 with the two-index split (Q1): AI_INDEX_DOC is now a short starter
        the project owns, and the list of what sp ships is rendered from the file catalog.
        """
        from llmflow.file_catalog import render_sp_index

        rendered = render_sp_index()
        assert "docs/tutorial.md" in rendered, "sp-index must list the tutorial"
        assert "docs/llmflow-language-quickref.md" in rendered, "sp-index must list the quickref"
        assert "sp/index.md" in AI_INDEX_DOC, (
            "the project's starter map must point at sp's inventory"
        )

    def test_copilot_instructions_has_read_index_first(self):
        """ASSISTANT_RULES_POINTER must emphasize reading index first"""
        assert "Read Index First" in ASSISTANT_RULES_POINTER or "index.md" in ASSISTANT_RULES_POINTER, (
            "ASSISTANT_RULES_POINTER must tell AI to read index.md first"
        )

    def test_variable_syntax_consistency(self):
        """${var} in YAML, {{var}} in templates — documented where syntax belongs.

        This used to require AI_INDEX_DOC to carry it. After the two-index split the project's
        starter map carries no reference material, so the claim moved to the quickref, which is
        the document the catalog describes as the pipeline YAML reference.
        """
        from llmflow.cli_utils import LANGUAGE_QUICKREF_DOC

        assert "${" in LANGUAGE_QUICKREF_DOC, "the quickref must document ${var}"
        assert "{{" in LANGUAGE_QUICKREF_DOC, "the quickref must document {{var}}"

    def test_logger_pattern_documented(self):
        """Logger singleton pattern must be documented for AI."""
        # Check that one of the docs mentions the Logger pattern
        mentions_logger = (
            "Logger()" in ASSISTANT_RULES_POINTER or
            "Logger()" in AI_RULES_DOC or
            "Logger()" in AI_INDEX_DOC or
            "logger" in AI_OVERVIEW_DOC.lower()
        )
        assert mentions_logger, (
            "AI context should document Logger singleton pattern"
        )

    def test_cli_command_name_consistency(self):
        """All generated docs must reference 'sp' not 'llmflow' for CLI."""
        # This is already tested in TestSpCliName, but let's verify AI context too
        assert "sp run" in AI_INDEX_DOC or "sp run" in TUTORIAL_DOC, (
            "AI context must use 'sp' as CLI command name, not 'llmflow'"
        )
        assert "llmflow run" not in TUTORIAL_DOC and "llmflow run" not in AI_INDEX_DOC, (
            "AI context must not reference old 'llmflow' command name"
        )

    def test_ai_index_has_global_context_section(self):
        """AI_INDEX_DOC must reference global ~/.sp/ context."""
        has_global = "~/.sp/" in AI_INDEX_DOC or "Global Context" in AI_INDEX_DOC
        assert has_global, (
            "AI_INDEX_DOC should include section on global ~/.sp/ context files"
        )

    def test_ai_rules_has_design_authority(self):
        """AI_RULES_DOC must include design authority guardrails."""
        assert "design document" in AI_RULES_DOC.lower(), (
            "AI_RULES_DOC must state that design documents are the authoritative specification"
        )
        assert "going rogue" in AI_RULES_DOC.lower(), (
            "AI_RULES_DOC must warn against implementing without known requirements"
        )


def test_init_registers_project_in_registry(tmp_path, monkeypatch):
    """sp init must register the project in ~/.sp/projects/ and index ai-context files."""
    sp_dir = tmp_path / ".sp"
    monkeypatch.setenv("SP_HOME", str(sp_dir))

    project_dir = tmp_path / "my-project"
    project_dir.mkdir()

    from llmflow.cli_utils import init_project
    init_project(project_dir)

    # Project should be registered
    from llmflow.registry import Registry
    registry = Registry(sp_dir)
    project = registry.projects.get("my-project")
    assert project is not None, "Project should be registered in ~/.sp/projects/"
    assert project["name"] == "my-project"
    assert project["path"] == str(project_dir.resolve())

    # ai-context files should be indexed
    ai_contexts = registry.ai_context.list()
    indexed_files = {ctx["file"] for ctx in ai_contexts}
    assert "project-overview.md" in indexed_files, "project/overview.md should be indexed in ~/.sp/ai-context/"
    assert "sp-rules.md" in indexed_files, "sp/rules.md should be indexed in ~/.sp/ai-context/"
    assert "project-index.md" in indexed_files, "project/index.md should be indexed in ~/.sp/ai-context/"
    assert "sp-index.md" in indexed_files, "sp/index.md should be indexed in ~/.sp/ai-context/"
    for ctx in ai_contexts:
        assert ctx["project"] == "my-project"
        assert "ai-context" in ctx["topics"]


def test_init_register_is_idempotent(tmp_path, monkeypatch):
    """Running sp init twice must not raise errors for already-registered entries."""
    monkeypatch.setenv("SP_HOME", str(tmp_path / ".sp"))
    project_dir = tmp_path / "my-project"
    project_dir.mkdir()

    from llmflow.cli_utils import init_project
    init_project(project_dir)
    # Second run must not raise
    init_project(project_dir)


def test_generate_ai_context_includes_user_context(tmp_path):
    """generate_ai_context() must prepend ~/.sp/user-context/*.md files."""
    from llmflow.registry import Registry

    sp_dir = tmp_path / ".sp"
    user_ctx_dir = sp_dir / "user-context"
    user_ctx_dir.mkdir(parents=True)
    (user_ctx_dir / "machine.md").write_text("Machine-level instructions here.", encoding="utf-8")
    (user_ctx_dir / "workflow.md").write_text("Workflow preferences here.", encoding="utf-8")

    registry = Registry(sp_dir)
    context = registry.generate_ai_context()

    assert "Machine-level instructions here." in context
    assert "Workflow preferences here." in context


def test_generate_ai_context_without_user_context_dir(tmp_path):
    """generate_ai_context() must work normally when ~/.sp/user-context/ does not exist."""
    from llmflow.registry import Registry

    sp_dir = tmp_path / ".sp"
    sp_dir.mkdir()

    registry = Registry(sp_dir)
    context = registry.generate_ai_context()

    assert "Scripture Pipeline Registry" in context


def test_generate_ai_context_ignores_missing_user_context_files(tmp_path):
    """generate_ai_context() must not raise if user-context dir exists but is empty."""
    from llmflow.registry import Registry

    sp_dir = tmp_path / ".sp"
    user_ctx_dir = sp_dir / "user-context"
    user_ctx_dir.mkdir(parents=True)
    # No .md files in the directory

    registry = Registry(sp_dir)
    context = registry.generate_ai_context()

    assert "Scripture Pipeline Registry" in context


def test_ai_index_doc_mentions_user_context():
    """AI_INDEX_DOC must document ~/.sp/user-context/ so AI tools know to read it."""
    from llmflow.cli_utils import AI_INDEX_DOC
    assert "user-context" in AI_INDEX_DOC, (
        "AI_INDEX_DOC must mention ~/.sp/user-context/ so AI tools read machine-level instructions"
    )


def test_copilot_instructions_point_at_the_authoritative_rules():
    """Under plan D4/A2 the assistant files carry no rules of their own.

    This test used to require ASSISTANT_RULES_POINTER to restate the `~/.sp/user-context/`
    step. It no longer restates anything: that instruction lives in `AI_INDEX_DOC` (pinned
    by `test_ai_index_mentions_user_context` directly above), and the pointer sends every
    reader there. Three partial copies of one rule set is what A2 removed — the Cursor
    copy had already lost the `sp run` prohibition entirely.
    """
    from llmflow.cli_utils import AI_INDEX_DOC, ASSISTANT_RULES_POINTER

    assert "docs/ai-context/project/index.md" in ASSISTANT_RULES_POINTER
    assert "docs/ai-context/sp/rules.md" in ASSISTANT_RULES_POINTER
    assert "user-context" in AI_INDEX_DOC, (
        "the pointer is only safe while the authoritative doc still carries the instruction"
    )


class TestNoExamples:
    """sp init --no-examples skips example files but still creates directories and structural files."""

    EXAMPLE_FILES = [
        "prompts/hello.gpt",
        "prompts/reply.gpt",
        "pipelines/hello-llmflow.yaml",
        "pipelines/hello.yaml",
        "docs/tutorial.md",
    ]
    STRUCTURAL_FILES = [
        "docs/llmflow-language-quickref.md",
        "docs/ai-context/project/overview.md",
        "docs/ai-context/sp/rules.md",
        "docs/ai-context/project/index.md",
        "project/TODO.md",
    ]
    STRUCTURAL_DIRS = [
        "prompts",
        "pipelines",
        "outputs",
        "docs",
    ]

    def test_no_examples_skips_example_files(self, tmp_path):
        init_environment(tmp_path, no_examples=True)

        for rel in self.EXAMPLE_FILES:
            assert not (tmp_path / rel).exists(), f"{rel} should not be created with no_examples=True"

        for rel in self.STRUCTURAL_FILES:
            assert (tmp_path / rel).exists(), f"{rel} should still be created with no_examples=True"

        for rel in self.STRUCTURAL_DIRS:
            assert (tmp_path / rel).is_dir(), f"{rel}/ directory should still be created with no_examples=True"

    def test_no_examples_via_cli(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        main(["init", "--no-examples"])

        for rel in self.EXAMPLE_FILES:
            assert not (tmp_path / rel).exists(), f"{rel} should not be created with --no-examples"


# --- docs/ai-context/project.md: the consumer-owned lane ---

def test_init_does_not_create_a_project_specific_document(tmp_path, monkeypatch):
    """sp creates the three standard context documents and nothing a project invented (#210).

    `project.md` and the `docs/audits/` checklists were catalogued and shipped to every project.
    They are one project's documents, and a project reaches its own files by naming them in
    `docs/ai-context/project/index.md` — the map sp creates once and never touches.
    """
    monkeypatch.chdir(tmp_path)
    main(["init"])

    ai_context = tmp_path / "docs" / "ai-context"
    assert sorted(p.name for p in (ai_context / "project").iterdir()) == [
        "index.md", "overview.md", "rules.md"
    ]
    for gone in ["docs/audits/INDEX.md", "docs/audits/audit-passage.md",
                 "docs/audits/audit-leadersguide.md"]:
        assert not (tmp_path / gone).exists(), f"sp should no longer create {gone}"


def test_the_starter_map_does_not_name_a_document_sp_stopped_shipping():
    assert "project.md" not in AI_INDEX_DOC
    assert "docs/audits" not in AI_INDEX_DOC


def test_index_references_python_api():
    """Project AIs must be able to discover the public Python API from their AI context.

    The pointers moved from AI_INDEX_DOC to the rendered sp index with the two-index split
    (Q1, 2026-08-24): they describe what the *engine* offers, so they belong in sp's
    inventory rather than in the map a project writes for itself.
    """
    from llmflow.file_catalog import render_sp_index

    rendered = render_sp_index()
    assert "python-api" in rendered
    assert "load_pipeline" in rendered
    assert "api_catalog" in rendered


def test_init_uses_outputs_not_singular_output_decoy(tmp_path, monkeypatch):
    # sp init must scaffold the plural `outputs/` (matching sp's runtime default) and never
    # plant a singular `output/` decoy next to it.
    monkeypatch.chdir(tmp_path)
    main(["init"])
    assert (tmp_path / "outputs").is_dir()
    assert not (tmp_path / "output").exists(), "sp init must not plant a singular output/ decoy"