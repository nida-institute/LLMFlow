import sys
import argparse
import logging
import json
from pathlib import Path

try:
    from importlib.metadata import version
    __version__ = version("llmflow")
except Exception:
    __version__ = "unknown"

from llmflow.runner import run_pipeline
from llmflow.cli_utils import init_project, list_pipelines

logger = logging.getLogger(__name__)


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
    parser = argparse.ArgumentParser(prog="llmflow", description="LLMFlow CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_p = subparsers.add_parser("run", help="Run a pipeline")
    run_p.add_argument("--pipeline", required=True, help="Path to pipeline YAML")
    run_p.add_argument("--var", action="append", default=[], help="Pipeline variables key=value")
    run_p.add_argument("--dry-run", action="store_true", help="Dry run (no LLM calls)")
    run_p.add_argument("--skip-lint", action="store_true", help="Skip linting")
    run_p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    run_p.add_argument("--log", default="llmflow.log", help="Path to log file (default: llmflow.log in cwd)")

    # list command
    list_p = subparsers.add_parser("list", help="List available pipelines")
    list_p.add_argument("--dir", default="pipelines", help="Directory to scan")
    list_p.add_argument("--json", action="store_true", help="Emit JSON output")

    # lint command
    lint_p = subparsers.add_parser("lint", help="Validate (lint) a pipeline without executing")
    lint_p.add_argument("--pipeline", required=True, help="Path to pipeline YAML")
    lint_p.add_argument("--fix-paths", action="store_true", help="Attempt simple path normalizations")
    lint_p.add_argument("--json", action="store_true", help="Emit JSON result")
    lint_p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # version command
    subparsers.add_parser("version", help="Show version")
    subparsers.add_parser("init", help="Create a starter LLMFlow environment")

    return parser


def _collect_cli_variables(pairs):
    variables = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid --var '{item}' (must be key=value)")
        k, v = item.split("=", 1)
        variables[k.strip()] = v.strip()
    return variables


def command_lint(pipeline_path: str, fix_paths: bool, json_mode: bool, verbose: bool):
    from llmflow.utils.linter import lint_pipeline_full

    if verbose:
        print(f"🔍 Linting pipeline: {pipeline_path}")

    result = lint_pipeline_full(pipeline_path)

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


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print(__version__)
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
        command_lint(args.pipeline, args.fix_paths, args.json, args.verbose)
        return

    if args.command == "init":
        init_project(Path.cwd())
        return

    if args.command == "run":
        if not args.skip_lint:
            from llmflow.utils.linter import lint_pipeline_full

            logger.info("🔍 Validating pipeline...")
            result = lint_pipeline_full(args.pipeline)
            if not result.valid:
                logger.error("❌ Pipeline validation failed:")
                for error in result.errors:
                    logger.error(f"  - {error}")
                sys.exit(1)

        variables = _collect_cli_variables(args.var)
        run_pipeline(args.pipeline, vars=variables, dry_run=args.dry_run, verbose=args.verbose, log_file=args.log)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
