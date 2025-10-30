import sys
import argparse
import logging
import json

try:
    from importlib.metadata import version
    __version__ = version("llmflow")
except Exception:
    __version__ = "unknown"

from llmflow.runner import run_pipeline

logger = logging.getLogger(__name__)


def build_parser():
    parser = argparse.ArgumentParser(prog="llmflow", description="LLMFlow CLI")
    sub = parser.add_subparsers(dest="command")

    # run command (existing)
    run_p = sub.add_parser("run", help="Run a pipeline")
    run_p.add_argument("--pipeline", required=True, help="Path to pipeline YAML")
    run_p.add_argument("--var", action="append", default=[], help="Pipeline variables key=value")
    run_p.add_argument("--dry-run", action="store_true", help="Dry run (no LLM calls)")
    run_p.add_argument("--skip-lint", action="store_true", help="Skip linting")
    run_p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # list command (existing)
    list_p = sub.add_parser("list", help="List available pipelines")
    list_p.add_argument("--dir", default="pipelines", help="Directory to scan")

    # NEW: lint command
    lint_p = sub.add_parser("lint", help="Validate (lint) a pipeline without executing")
    lint_p.add_argument("--pipeline", required=True, help="Path to pipeline YAML")
    lint_p.add_argument("--fix-paths", action="store_true", help="Attempt simple path normalizations")
    lint_p.add_argument("--json", action="store_true", help="Emit JSON result")
    lint_p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # version command (existing)
    sub.add_parser("version", help="Show version")

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
        click.echo(f"🔍 Linting pipeline: {pipeline_path}")

    # Call the linter and get result object
    result = lint_pipeline_full(pipeline_path)

    # Output results
    if json_mode:
        import json as _json
        output = {
            "pipeline": pipeline_path,
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        print(_json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if result.valid:
            print(f"✅ Pipeline OK")
        else:
            print(f"❌ Pipeline has errors")
            if result.errors:
                print("Errors:")
                for e in result.errors:
                    print(f"  - {e}")
            if result.warnings:
                print("Warnings:")
                for w in result.warnings:
                    print(f"  - {w}")

    # Exit with error code if invalid
    if not result.valid:
        sys.exit(1)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print(__version__)
        return

    if args.command == "list":
        # ...existing list logic...
        # keep unchanged
        ...

    if args.command == "lint":
        command_lint(
            pipeline_path=args.pipeline,
            fix_paths=args.fix_paths,
            json_mode=args.json,
            verbose=args.verbose,
        )
        return

    if args.command == "run":
        # existing run path (unchanged)
        # ensure we call lint unless --skip-lint
        if not args.skip_lint:
            from llmflow.utils.linter import lint_pipeline_full

            logger.info("🔍 Validating pipeline...")
            result = lint_pipeline_full(args.pipeline)
            if not result.valid:
                logger.error("❌ Pipeline validation failed:")
                for error in result.errors:
                    logger.error(f"  - {error}")
                sys.exit(1)
        # proceed with run
        variables = _collect_cli_variables(args.var)
        from llmflow.runner import run_pipeline

        run_pipeline(args.pipeline, vars=variables, dry_run=args.dry_run, verbose=args.verbose)
        return

    parser.print_help()


if __name__ == "__main__":
    main()  # Use argparse main(), not Click cli()
