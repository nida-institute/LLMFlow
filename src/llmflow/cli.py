import sys
import signal
from pathlib import Path

from llmflow.modules.logger import Logger

# Following the Logger Pattern guideline: use the shared Logger()
# singleton so CLI messages go to both console and llmflow.log.
logger = Logger()


def _cli_sigint_handler(signum, frame):
    """Handle Ctrl+C at the CLI process level."""
    msg1 = "\n⚠️  Execution interrupted by user (Ctrl+C)"
    msg2 = "   Pipeline stopped."
    logger.info(msg1)
    logger.info(msg2)
    sys.exit(130)


signal.signal(signal.SIGINT, _cli_sigint_handler)


import argparse
import json
import os
from pathlib import Path


#: Distribution names to look the version up under, current first. The project was renamed
#: `llmflow` -> `scripture-pipelines` (f5e4d8f) but the console script is `sp` in both, so an
#: older install still provides a working `sp` registered under the old name — and if it sits
#: earlier on PATH it shadows the released binary. Asking only for the current name reported
#: `unknown` on those machines.
_DISTRIBUTION_NAMES = ("scripture-pipelines", "llmflow")


def _resolve_version() -> str:
    """Return the installed version, or an `unknown` string that says why."""
    import importlib.metadata

    for name in _DISTRIBUTION_NAMES:
        try:
            resolved = importlib.metadata.version(name)
        except Exception:
            continue
        if resolved:
            return resolved
    # No distribution metadata at all — typically running from a source checkout that was
    # never installed. Say so, rather than leaving a bare "unknown" to puzzle over.
    return "unknown (no package metadata — running from source? try: pip install -e .)"


__version__ = _resolve_version()

from llmflow.cli_utils import init_project, list_pipelines

def list_pipelines(directory: str) -> list[str]:
    """List all YAML pipeline files in a directory."""
    base = Path(directory)
    if not base.exists():
        return []
    pipelines: list[str] = []
    for pattern in ("*.yaml", "*.yml"):
        for path in base.rglob(pattern):
            if path.is_file():
                pipelines.append(str(path.relative_to(base)))
    return sorted(dict.fromkeys(pipelines))


def build_parser():
    parser = argparse.ArgumentParser(prog="sp", description="Scripture Pipelines CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_p = subparsers.add_parser("run", help="Run a pipeline")
    run_p.add_argument("--pipeline", required=True, help="Path to pipeline YAML")
    run_p.add_argument("--var", action="append", default=[], help="Pipeline variables key=value")
    run_p.add_argument("--dry-run", action="store_true", help="Dry run (no LLM calls)")
    run_p.add_argument("--skip-lint", action="store_true", help="Skip linting")
    run_p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    run_p.add_argument("--log", default="llmflow.log", help="Path to log file (default: llmflow.log in cwd)")
    run_p.add_argument("--rewind-to", help="Replay checkpoints up to and including this step name")
    run_p.add_argument("--stop-after", help="Stop pipeline after this step name runs")
    run_p.add_argument("--resume", action="store_true", help="Skip steps whose saveas files already exist (resume interrupted run)")

    # list command
    list_p = subparsers.add_parser("list", help="List available pipelines")
    list_p.add_argument("--dir", default="pipelines", help="Directory to scan")
    list_p.add_argument("--json", action="store_true", help="Emit JSON output")

    # lint command
    lint_p = subparsers.add_parser("lint", help="Validate (lint) a pipeline without executing")
    lint_p.add_argument("--pipeline", required=True, help="Path to pipeline YAML")
    lint_p.add_argument("--var", action="append", default=[], help="Pipeline variables key=value")
    lint_p.add_argument("--fix-paths", action="store_true", help="Attempt simple path normalizations")
    lint_p.add_argument("--json", action="store_true", help="Emit JSON result")
    lint_p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    lint_p.add_argument("--rewind-to", help="Validate rewind readiness up to this step")

    # clean command
    clean_p = subparsers.add_parser("clean", help="Delete contents of intermediate_file_directory")
    clean_p.add_argument("--pipeline", required=True, help="Path to pipeline YAML")
    clean_p.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    clean_p.add_argument("--debug-only", action="store_true", help="Delete only debug files (intermediate_file_directory/debug/ or outputs/debug/)")
    clean_p.add_argument("--intermediate-only", action="store_true", help="Delete only intermediate files, preserving debug/")
    clean_p.add_argument("--var", action="append", default=[], help="Pipeline variable key=value; repeatable (honored when resolving directories)")

    # version command
    subparsers.add_parser("version", help="Show version")

    # gui command
    gui_p = subparsers.add_parser("gui", help="Launch web-based GUI")
    gui_p.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    gui_p.add_argument("--port", type=int, default=5050, help="Port number (default: 5050)")
    gui_p.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")

    init_p = subparsers.add_parser("init", help="Create a starter LLMFlow environment")
    init_p.add_argument(
        "--update",
        action="store_true",
        help="Regenerate files that carry the '<!-- Generated by llmflow init -->' marker, leaving hand-edited files untouched",
    )
    init_p.add_argument(
        "--sync",
        action="store_true",
        help="Copy ai-context files from the installed LLMFlow package to the current project",
    )
    init_p.add_argument(
        "--no-examples",
        action="store_true",
        dest="no_examples",
        help="Skip example files (hello.gpt, hello-llmflow.yaml, tutorial.md, etc.) — creates directories and structural files only",
    )

    subparsers.add_parser(
        "doctor",
        help=(
            "Check this machine's setup and RESTORE any file sp owns that is missing or has "
            "diverged. Not read-only: it overwrites `policy: generated` files from the shipped "
            "version. Commit or stash first."
        ),
    )

    setup_p = subparsers.add_parser("setup", help="Configure AI provider API keys")
    setup_p.add_argument(
        "--update",
        action="store_true",
        help="Re-run setup to update keys or add new providers",
    )

    models_p = subparsers.add_parser("models", help="List available models by provider")
    models_p.add_argument("--update", action="store_true", help="Update model pricing from installed llm plugins")
    subparsers.add_parser("update-ai-context", help="Regenerate docs/ai-context/ helper files for AI assistants")

    # resource command — one surface for everything the catalog describes (#217).
    res_p = subparsers.add_parser("resource", help="Scripture texts and other catalog resources")
    res_sub = res_p.add_subparsers(dest="resource_command", help="Resource commands")

    res_sub.add_parser("list", help="What the catalog knows, and what this machine has")

    res_add = res_sub.add_parser("add", help="Register a resource so pipelines can name it")
    res_add.add_argument("id", help="Catalog id (e.g. WLC), or the name to register yours under")
    res_add.add_argument("--path", default=None, help="Register something of your own by path")
    res_add.add_argument("--kind", default=None, choices=["tsv", "tei", "usfm"],
                         help="With --path: how to read it. A Paratext project says so itself")
    res_add.add_argument("--versification", default=None, help="With --path: its scheme")
    res_add.add_argument("--no-download", action="store_true", dest="no_download",
                         help="Register without fetching the data yet")

    res_dl = res_sub.add_parser("download", help="Fetch a catalog resource without registering it")
    res_dl.add_argument("id", help="Catalog id (e.g. acai)")
    res_dl.add_argument("--dest", default=None, help="Download destination (default: ~/.sp/data/)")

    # load-db command
    ldb_p = subparsers.add_parser("load-db", help="Load a downloaded dataset into a database (basex, ...)")
    ldb_p.add_argument("driver", nargs="?", default=None, help="Database driver (e.g. basex)")
    ldb_p.add_argument("dataset", nargs="?", default=None, help="Dataset key (e.g. acai, macula-greek)")
    ldb_p.add_argument("--name", default=None, dest="db_name", help="Override database name (default: dataset key)")
    ldb_p.add_argument("--force", action="store_true", help="Drop and recreate database if it already exists")
    ldb_p.add_argument("--source", default=None, help="Load from this path instead of ~/.sp/data/<dataset>/")
    ldb_p.add_argument("--list-drivers", action="store_true", dest="list_drivers", help="List available database drivers")
    ldb_p.add_argument("--register", action="store_true", help="Register database in global registry (~/.sp/)")

    # registry command
    reg_p = subparsers.add_parser("registry", help="Manage global resource registry (~/.sp/)")
    reg_sub = reg_p.add_subparsers(dest="registry_command", required=True)

    # registry list
    reg_list = reg_sub.add_parser("list", help="List registered resources")
    reg_list.add_argument("type", nargs="?", choices=["projects", "datasets", "databases"],
                         help="Resource type to list (default: all)")
    reg_list.add_argument("--json", action="store_true", help="Output as JSON")

    # registry info
    reg_info = reg_sub.add_parser("info", help="Show detailed info about a resource")
    reg_info.add_argument("type", choices=["project", "dataset", "database"], help="Resource type")
    reg_info.add_argument("id", help="Resource ID/name")

    # registry status
    reg_sub.add_parser("status", help="Show registry status and location")

    # registry context
    reg_sub.add_parser("context", help="Generate AI context from registry")


    # context command
    ctx_p = subparsers.add_parser("context", help="Manage AI context files (docs/ai-context/)")
    ctx_sub = ctx_p.add_subparsers(dest="context_command", required=True)

    # context list
    ctx_sub.add_parser("list", help="List available AI context files")

    # context add
    ctx_add = ctx_sub.add_parser("add", help="Register AI context file in global registry")
    ctx_add.add_argument("file", help="Context filename (e.g., basex-patterns.md)")
    ctx_add.add_argument("--description", required=True, help="Brief description of content")
    ctx_add.add_argument("--topics", required=True, help="Comma-separated topics (e.g., basex,xquery,greek)")
    ctx_add.add_argument("--project", help="Project name (default: current directory name)")
    ctx_add.add_argument("--path", help="Full path to file (default: docs/ai-context/<file>)")

    # context search
    ctx_search = ctx_sub.add_parser("search", help="Search AI context registry by topic")
    ctx_search.add_argument("topics", nargs="+", help="Topics to search for (matches any)")
    ctx_search.add_argument("--project", help="Filter by project name")

    # content command (with subcommands)
    content_p = subparsers.add_parser("content", help="Manage content lifecycle")
    content_sub = content_p.add_subparsers(dest="content_command", required=True)

    # content status
    status_p = content_sub.add_parser("status", help="Show content status across stages")
    status_p.add_argument("path", help="Content path (without extension)")
    status_p.add_argument("--config", help="Path to content-stages.yaml (default: ./config/content-stages.yaml)")
    status_p.add_argument("--content-root", help="Content root directory (default: ./content)")
    status_p.add_argument("--json", action="store_true", help="Output result as JSON")

    # content list
    list_c = content_sub.add_parser("list", help="List all files in a stage")
    list_c.add_argument("stage", help="Stage name")
    list_c.add_argument("--config", help="Path to content-stages.yaml (default: ./config/content-stages.yaml)")
    list_c.add_argument("--content-root", help="Content root directory (default: ./content)")
    list_c.add_argument("--json", action="store_true", help="Output result as JSON")
    list_c.add_argument("--with-metadata", action="store_true", help="Include metadata for each file")

    # content diff
    diff_p = content_sub.add_parser("diff", help="Compare content versions across stages")
    diff_p.add_argument("path", help="Content path (without extension)")
    diff_p.add_argument("--from-stage", required=True, help="Source stage name")
    diff_p.add_argument("--to-stage", required=True, help="Destination stage name")
    diff_p.add_argument("--config", help="Path to content-stages.yaml (default: ./config/content-stages.yaml)")
    diff_p.add_argument("--content-root", help="Content root directory (default: ./content)")

    # content gui
    gui_c = content_sub.add_parser("gui", help="Launch web-based content management GUI")
    gui_c.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    gui_c.add_argument("--port", type=int, default=5051, help="Port number (default: 5051)")
    gui_c.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")
    gui_c.add_argument("--content-root", help="Content root directory (default: ./content)")
    gui_c.add_argument("--config", help="Path to content-stages.yaml (default: ./config/content-stages.yaml)")

    # transition command (legacy - kept for backwards compatibility)
    trans_p = subparsers.add_parser("transition", help="Transition content between lifecycle stages")
    trans_p.add_argument("from_stage", metavar="from", help="Source stage name")
    trans_p.add_argument("to_stage", metavar="to", help="Destination stage name")
    trans_p.add_argument("path", help="Content path (without extension)")
    trans_p.add_argument("--config", help="Path to content-stages.yaml (default: ./config/content-stages.yaml)")
    trans_p.add_argument("--content-root", help="Content root directory (default: ./content)")
    trans_p.add_argument("--dry-run", action="store_true", help="Validate without making changes")
    trans_p.add_argument("--json", action="store_true", help="Output result as JSON")

    # sp tools <tool> — developer/collaboration tools (see src/llmflow/tools/)
    tools_p = subparsers.add_parser("tools", help="Developer/collaboration tools")
    tools_sub = tools_p.add_subparsers(dest="tools_command", required=True)
    from llmflow.tools import replay as _replay
    replay_p = tools_sub.add_parser(
        "replay", help="Test a prompt change against captured debug requests, cheaply")
    _replay.add_arguments(replay_p)

    # Standard --version flag (e.g. used by CI smoke tests: llmflow --version)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    return parser


def _collect_cli_variables(pairs):
    variables = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid --var '{item}' (must be key=value)")
        k, v = item.split("=", 1)
        variables[k.strip()] = v.strip()
    return variables


def command_lint(
    pipeline_path: str,
    fix_paths: bool,
    json_mode: bool,
    verbose: bool,
    cli_vars: dict | None = None,
    rewind_to: str | None = None,
):
    from llmflow import load_pipeline

    if verbose:
        print(f"🔍 Linting pipeline: {pipeline_path}")

    result = load_pipeline(pipeline_path).lint(vars=cli_vars, rewind_to=rewind_to)

    if json_mode:
        output = {
            "pipeline": pipeline_path,
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if result.valid:
            print("✅ Pipeline OK")
        else:
            print("❌ Pipeline has errors")
            if result.errors:
                print("Errors:")
                for e in result.errors:
                    print(f"  - {e}")
            if result.warnings:
                print("Warnings:")
                for w in result.warnings:
                    print(f"  - {w}")

    if not result.valid:
        sys.exit(1)


def _make_output_encodable() -> None:
    """Let every command print its glyphs without dying on the console's encoding.

    A Windows console defaults to cp1252, which encodes none of `✓ · ! ✗`, `→`, an em dash, or
    the emoji this CLI uses throughout. `sp doctor` died on the arrow the first time it ran on a
    Windows binary — and it took that long only because doctor was added to the smoke test after
    the previous release.

    UTF-8 where the terminal can take it, `replace` so that a console which cannot degrades to
    `?` instead of a traceback. Fixed once here rather than per printer: the next command to
    print an emoji would otherwise be the next one to fail on someone else's machine.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue  # a captured or replaced stream; nothing to do
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass  # never let output configuration stop the command itself


def main(argv=None):
    _make_output_encodable()

    # Frozen binaries ship no usable system cert store — point SSL at bundled
    # certifi before any network call. See LLMFlow#182.
    from llmflow.utils.ssl_certs import ensure_ca_certs
    ensure_ca_certs()

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "clean":
        from llmflow import load_pipeline

        pipeline_path = Path(args.pipeline)
        if not pipeline_path.exists():
            logger.error(f"❌ Pipeline file not found: {args.pipeline}")
            sys.exit(1)

        # Resolve via the shared engine accessor so `sp clean` honors --var and uses the
        # same ${...} expansion a real run does (LLMFlow#186).
        _clean_vars = _collect_cli_variables(getattr(args, "var", []) or [])
        _intermediate_dir = load_pipeline(pipeline_path).resolve(vars=_clean_vars).intermediate_file_directory

        _debug_only = getattr(args, "debug_only", False)
        _intermediate_only = getattr(args, "intermediate_only", False)

        def _delete_files(files, label):
            if args.dry_run:
                if files:
                    print(f"Would delete {len(files)} file(s) from {label}:")
                    for _f in files:
                        print(f"  {_f}")
                else:
                    print(f"Nothing to delete in {label}")
                return 0
            for _f in files:
                _f.unlink()
                print(f"Deleted: {_f}")
            return len(files)

        def _remove_empty_dirs(root):
            for _d in sorted(root.rglob("*"), reverse=True):
                if _d.is_dir() and not any(_d.iterdir()):
                    _d.rmdir()

        _pipeline_name = pipeline_path.stem

        if _debug_only:
            # Delete debug files only
            if _intermediate_dir:
                _debug_dir = _intermediate_dir / "debug" / _pipeline_name
            else:
                _debug_dir = Path.cwd() / "outputs" / "debug" / _pipeline_name

            if not _debug_dir.exists():
                print(f"⚠️  Debug directory does not exist: {_debug_dir}")
                return

            _files = sorted(f for f in _debug_dir.rglob("*") if f.is_file())
            _n = _delete_files(_files, _debug_dir)
            if not args.dry_run:
                _remove_empty_dirs(_debug_dir)
                print(f"✅ Cleaned {_debug_dir} ({_n} file(s) deleted)")
            return

        if not _intermediate_dir:
            print("⚠️  No intermediate_file_directory declared in this pipeline. Nothing to clean.")
            return

        if not _intermediate_dir.exists():
            print(f"⚠️  intermediate_file_directory does not exist: {_intermediate_dir}")
            return

        if _intermediate_only:
            # Delete everything except the debug/ subdirectory
            _debug_dir = _intermediate_dir / "debug" / _pipeline_name
            _files = sorted(
                f for f in _intermediate_dir.rglob("*")
                if f.is_file() and not f.is_relative_to(_debug_dir)
            )
        else:
            # Delete everything
            _files = sorted(f for f in _intermediate_dir.rglob("*") if f.is_file())

        _n = _delete_files(_files, _intermediate_dir)
        if not args.dry_run:
            _remove_empty_dirs(_intermediate_dir)
            print(f"✅ Cleaned {_intermediate_dir} ({_n} file(s) deleted)")
        return

    if args.command == "version":
        print(__version__)
        return

    if args.command == "gui":
        from llmflow.gui.server import start_server
        start_server(
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser
        )
        return

    if args.command == "list":
        pipelines = list_pipelines(args.dir)
        if args.json:
            print(json.dumps(pipelines, ensure_ascii=False, indent=2))
        else:
            for pipeline in pipelines:
                print(pipeline)
        return

    if args.command == "lint":
        variables = _collect_cli_variables(args.var)
        command_lint(
            args.pipeline,
            args.fix_paths,
            args.json,
            args.verbose,
            cli_vars=variables,
            rewind_to=args.rewind_to,
        )
        return

    if args.command == "init":
        from llmflow.cli_utils import sync_ai_context_files
        init_project(
            Path.cwd(),
            update=getattr(args, "update", False),
            no_examples=getattr(args, "no_examples", False),
        )
        if getattr(args, "sync", False):
            sync_ai_context_files(Path.cwd())
        return

    if args.command == "doctor":
        from llmflow.doctor import doctor_command
        raise SystemExit(doctor_command(Path.cwd()))

    if args.command == "setup":
        from llmflow.setup_command import run_setup
        run_setup(update=getattr(args, "update", False))
        return

    if args.command == "models":
        if getattr(args, "update", False):
            from llmflow.setup_command import run_models_update
            sys.exit(0 if run_models_update() else 1)
        from llmflow.setup_command import run_models
        run_models()
        return

    if args.command == "update-ai-context":
        import importlib.util
        _script = Path(__file__).resolve().parents[2] / "tools" / "update_ai_context.py"
        spec = importlib.util.spec_from_file_location("update_ai_context", _script)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {_script}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
        return

    if args.command == "resource":
        from llmflow import resources

        if args.resource_command == "list":
            rows = resources.report()
            if not rows:
                print("The catalog describes no readable resources.")
                return
            print(f"  {'ID':<12} {'STATUS':<11} {'KIND':<6} {'FROM':<34} LICENCE")
            print(f"  {'-'*12} {'-'*11} {'-'*6} {'-'*34} {'-'*24}")
            for row in rows:
                print(
                    f"  {row['id']:<12} {row['status']:<11} {row['kind'] or '':<6} "
                    f"{row['dataset'] or '':<34} {row['license'] or ''}"
                )
            print("\n  registered = usable now · available = downloaded, run `sp resource add`")
            print("  absent     = not downloaded yet; `sp resource add <ID>` fetches it")
            return

        if args.resource_command == "add":
            # A failure here is a fact about this machine — no network, a locked directory, a
            # name the catalog does not know. Say which; a traceback answers none of them.
            try:
                if args.path:
                    written = resources.register_local(
                        args.id, args.path, kind=args.kind, versification=args.versification
                    )
                else:
                    written = resources.register(args.id, download=not args.no_download)
            except (KeyError, ValueError, OSError, RuntimeError) as error:
                # `str()` on an OSError gives "[Errno 13] Permission denied: <path>"; its
                # `args[0]` gives the bare errno, which told a user only "13".
                message = error.args[0] if isinstance(error, KeyError) else str(error)
                print(f"❌ Could not register '{args.id}': {message}")
                sys.exit(1)
            print(f"✅ Registered '{args.id}' — {written}")
            return

        if args.resource_command == "download":
            from llmflow.download_data import fetch

            entry = next(
                (e for e in resources.catalog() if e.get("id") == args.id), None
            )
            if entry is None:
                known = ", ".join(sorted(str(e.get("id")) for e in resources.catalog()))
                print(f"❌ The catalog has no resource '{args.id}'.\n   It knows: {known}")
                sys.exit(1)
            fetch(entry, dest=args.dest)
            return

        parser.parse_args([args.command, "--help"])
        return

    if args.command == "load-db":
        from llmflow.load_db import run_load_db
        run_load_db(
            driver=args.driver,
            dataset=args.dataset,
            db_name=args.db_name,
            force=args.force,
            source=args.source,
            list_drivers_only=args.list_drivers,
        )
        # run_load_db raises on failure, so reaching here means the load succeeded.
        if args.register and not args.list_drivers:
            from llmflow.registry import Registry

            registry = Registry()
            db_name = args.db_name or args.dataset
            # Re-register cleanly so --force reloads and re-runs stay idempotent.
            if registry.databases.get(db_name):
                registry.databases.unregister(db_name)
            registry.databases.register(name=db_name, type=args.driver)
            print(f"✅ Registered database '{db_name}' in ~/.sp/ registry")
        return

    if args.command == "registry":
        from llmflow.registry import Registry
        registry = Registry()

        if args.registry_command == "list":
            # List registered resources
            if args.type == "projects" or args.type is None:
                projects = registry.projects.list()
                if args.json:
                    print(json.dumps({"projects": projects}, indent=2))
                elif projects:
                    print("Registered Projects:")
                    for p in projects:
                        desc = f" - {p.get('description', '')}" if p.get('description') else ""
                        print(f"  {p['name']:20s} {p['path']}{desc}")
                elif args.type == "projects":
                    print("No projects registered")

            if args.type == "datasets" or args.type is None:
                datasets = registry.datasets.list()
                if args.json:
                    print(json.dumps({"datasets": datasets}, indent=2))
                elif datasets:
                    print("\nAvailable Datasets:")
                    for ds in datasets:
                        print(f"  {ds['id']:25s} v{ds['version']:12s} {ds['format']:6s} {ds['path']}")
                elif args.type == "datasets":
                    print("No datasets registered")

            if args.type == "databases" or args.type is None:
                databases = registry.databases.list()
                if args.json:
                    print(json.dumps({"databases": databases}, indent=2))
                elif databases:
                    print("\nAvailable Databases:")
                    for db in databases:
                        if db['type'] == 'basex':
                            location = f"{db.get('host', 'localhost')}:{db.get('port', 1984)}"
                            print(f"  {db['name']:20s} BaseX at {location}")
                        elif db['type'] == 'duckdb':
                            print(f"  {db['name']:20s} DuckDB at {db.get('path', 'unknown')}")
                        else:
                            print(f"  {db['name']:20s} {db['type']}")
                elif args.type == "databases":
                    print("No databases registered")

        elif args.registry_command == "info":
            # Show detailed info about a resource
            resource = None
            resource_type = None
            if args.type == "project":
                resource = registry.projects.get(args.id)
                resource_type = "Project"
            elif args.type == "dataset":
                resource = registry.datasets.get(args.id)
                resource_type = "Dataset"
            elif args.type == "database":
                resource = registry.databases.get(args.id)
                resource_type = "Database"

            if resource is None:
                print(f"❌ {resource_type} '{args.id}' not found in registry")
                sys.exit(1)

            print(f"{resource_type}: {args.id}")
            print("=" * 60)
            for key, value in resource.items():
                print(f"{key:20s}: {value}")

        elif args.registry_command == "status":
            # Show registry status
            print(f"Registry Location: {registry.path}")
            print(f"Projects:  {len(registry.projects.list())}")
            print(f"Datasets:  {len(registry.datasets.list())}")
            print(f"Databases: {len(registry.databases.list())}")

        elif args.registry_command == "context":
            # Generate AI context
            print(registry.generate_ai_context())

        return

    if args.command == "context":
        from llmflow.context import list_context_files, format_context_list

        if args.context_command == "list":
            # List AI context files in docs/ai-context/
            cwd = Path.cwd()
            context_files = list_context_files(cwd)
            output = format_context_list(context_files)
            print(output)

        elif args.context_command == "add":
            # Register AI context file in global registry
            from llmflow.registry import Registry

            registry = Registry()

            # Determine project name
            project_name = args.project
            if not project_name:
                project_name = Path.cwd().name

            # Determine full path
            file_path = args.path
            if not file_path:
                file_path = str(Path.cwd() / "docs" / "ai-context" / args.file)

            # Parse topics
            topics = [t.strip() for t in args.topics.split(",")]

            # Register
            registry.ai_context.register(
                file=args.file,
                project=project_name,
                description=args.description,
                topics=topics,
                path=file_path
            )

            print(f"✅ Registered {args.file} in global AI context registry")
            print(f"   Project: {project_name}")
            print(f"   Topics: {', '.join(topics)}")

        elif args.context_command == "search":
            # Search AI context registry by topics
            from llmflow.registry import Registry

            registry = Registry()

            # Search
            results = registry.ai_context.search(
                topics=args.topics,
                project=args.project
            )

            if not results:
                print("No AI context files found matching search criteria.")
                if args.project:
                    print(f"  Project filter: {args.project}")
                print(f"  Topics: {', '.join(args.topics)}")
            else:
                print(f"Found {len(results)} AI context file(s):\n")
                for ctx in results:
                    topics_str = ", ".join(ctx.get("topics", []))
                    print(f"  {ctx['file']}")
                    print(f"    Project: {ctx.get('project', 'unknown')}")
                    print(f"    Description: {ctx.get('description', 'No description')}")
                    print(f"    Topics: {topics_str}")
                    if ctx.get('path'):
                        print(f"    Path: {ctx['path']}")
                    print()

        return

    if args.command == "content":
        config_path = Path(args.config) if args.config else None
        content_root = Path(args.content_root) if args.content_root else None

        if args.content_command == "status":
            from llmflow.utils.content_status import get_content_status, format_status

            result = get_content_status(
                path=args.path,
                content_root=content_root,
                config_path=config_path,
            )

            print(format_status(result, json_output=args.json))

            if not result["success"]:
                sys.exit(1)

        elif args.content_command == "list":
            from llmflow.utils.content_list import list_content, format_content_list

            result = list_content(
                stage=args.stage,
                content_root=content_root,
                config_path=config_path,
                with_metadata=args.with_metadata,
            )

            print(format_content_list(result, json_output=args.json))

            if not result["success"]:
                sys.exit(1)

        elif args.content_command == "diff":
            from llmflow.utils.content_diff import diff_content

            result = diff_content(
                path=args.path,
                from_stage=args.from_stage,
                to_stage=args.to_stage,
                content_root=content_root,
                config_path=config_path,
            )

            # diff_content outputs directly
            if not result["success"]:
                logger.error(f"❌ Diff failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        elif args.content_command == "gui":
            from gui.backend.content_app import start_content_gui

            start_content_gui(
                host=args.host,
                port=args.port,
                open_browser=not args.no_browser
            )

        return

    if args.command == "transition":
        from llmflow.utils.content_transition import transition_content

        # Determine config and content root paths
        config_path = Path(args.config) if args.config else None
        content_root = Path(args.content_root) if args.content_root else None

        # Execute transition
        result = transition_content(
            from_stage=args.from_stage,
            to_stage=args.to_stage,
            path=args.path,
            config_path=config_path,
            content_root=content_root,
            dry_run=args.dry_run,
        )

        # Output result
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result["success"]:
                output = result.get("result", {})
                action = output.get("action", "transitioned")
                from_stage = output.get("from", args.from_stage)
                to_stage = output.get("to", args.to_stage)
                source = output.get("source", "")
                dest = output.get("destination", "")

                logger.info(f"✅ Content {action}: {from_stage} → {to_stage}")
                if source:
                    logger.info(f"   Source: {source}")
                if dest:
                    logger.info(f"   Destination: {dest}")

                if args.dry_run:
                    logger.info("   (Dry run - no changes made)")
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"❌ Transition failed: {error}")
                sys.exit(1)

        return

    if args.command == "tools":
        if args.tools_command == "replay":
            from llmflow.tools import replay
            sys.exit(replay.run(args))
        return

    if args.command == "run":
        try:
            variables = _collect_cli_variables(args.var)
            from llmflow import load_pipeline

            try:
                pipeline = load_pipeline(args.pipeline)
            except FileNotFoundError:
                logger.error(f"❌ Pipeline file not found: {args.pipeline}")
                logger.error(f"   Current directory: {os.getcwd()}")
                logger.error("   💡 Tip: Make sure you're running from the correct directory")
                sys.exit(1)

            if not args.skip_lint:
                logger.info("🔍 Validating pipeline...")
                result = pipeline.lint(vars=variables, rewind_to=args.rewind_to)
                if not result.valid:
                    logger.error("❌ Pipeline validation failed:")
                    for error in result.errors:
                        logger.error(f"  - {error}")
                    sys.exit(1)

            try:
                pipeline.run(
                    vars=variables,
                    dry_run=args.dry_run,
                    verbose=args.verbose,
                    log_file=args.log,
                    rewind_to=args.rewind_to,
                    stop_after=args.stop_after,
                    resume=args.resume,
                    skip_lint=True,
                )
            except FileNotFoundError as e:
                # Distinguish between a missing pipeline file and a missing
                # resource (prompt, data file) referenced inside the pipeline.
                if not Path(args.pipeline).exists():
                    logger.error(f"❌ Pipeline file not found: {args.pipeline}")
                    logger.error(f"   Current directory: {os.getcwd()}")
                    logger.error("   💡 Tip: Make sure you're running from the correct directory")
                else:
                    logger.error(f"❌ {e}")
                sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Execution interrupted by user (Ctrl+C)")
            logger.info("   Pipeline stopped.")
            sys.exit(130)  # Standard exit code for SIGINT
        except BrokenPipeError:
            # Output was piped to a command that closed (e.g., head, less)
            # This is normal behavior, exit quietly
            sys.exit(0)
        except PermissionError as e:
            logger.error(f"❌ Permission denied: {e}")
            logger.error("   💡 Tip: Check file/directory permissions")
            sys.exit(1)

        from llmflow.modules.telemetry import models_data_age_days
        age = models_data_age_days()
        if age is not None and age > 60:
            logger.info(f"💡 Model pricing data is {age} days old. Run `sp models --update` to refresh.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
