"""Plugins load when running a pipeline, and not otherwise (LLMFlow#178).

Discovery used to fire at import time — twice, from `plugins/loader.py:73` and
`runner.py:57` — so `sp --version` and `sp --help` printed two pairs of "Loading
plugins…/Loaded N plugin(s)" before doing anything, and every command paid for it.

Safe to defer because `discover_plugins()` mutates `plugin_registry` in place rather than
rebinding it, so modules that imported the dict see later population.
"""
import subprocess
import sys

import pytest

PLUGIN_NOISE = ("Loading plugins", "Loaded ")


def _sp(*args):
    """Run the CLI in-process-equivalent via -m, returning combined output."""
    proc = subprocess.run(
        [sys.executable, "-m", "llmflow.cli", *args],
        capture_output=True, text=True,
    )
    return proc.stdout + proc.stderr


def _plugin_lines(output):
    return [ln for ln in output.splitlines() if any(n in ln for n in PLUGIN_NOISE)]


class TestNoDiscoveryForNonPipelineCommands:
    @pytest.mark.parametrize("args", [("--version",), ("--help",)])
    def test_no_plugin_loading(self, args):
        out = _sp(*args)
        assert _plugin_lines(out) == [], (
            f"sp {' '.join(args)} loaded plugins; it does not run a pipeline:\n{out}"
        )

    def test_version_is_reported(self):
        """Guards #184: metadata must resolve, so this must not print 'unknown'."""
        out = _sp("--version")
        assert "unknown" not in out.lower(), out

    def test_version_names_the_sp_command(self):
        """`--version` should say `sp`, not the old `llmflow` branding."""
        out = _sp("--version")
        assert out.strip().startswith("sp "), out


class TestDiscoveryOnlyWhenRunningAPipeline:
    """`sp lint` validates a pipeline but does not execute steps, and the linter never
    reads the registry — so it should not load plugins either."""

    def _pipeline(self, tmp_path, body):
        p = tmp_path / "p.yaml"
        p.write_text(body, encoding="utf-8")
        return str(p)

    def test_lint_does_not_load_plugins(self, tmp_path):
        path = self._pipeline(tmp_path,
            'name: t\nsteps:\n  - name: s\n    type: save\n'
            '    content: "hi"\n    saveas: "outputs/x.md"\n')
        out = _sp("lint", "--pipeline", path)
        assert _plugin_lines(out) == [], f"lint loaded plugins:\n{out}"

    def test_lint_still_accepts_a_plugin_step(self, tmp_path):
        """Regression guard: lint must not start rejecting plugin types once discovery
        no longer runs at import."""
        path = self._pipeline(tmp_path,
            'name: t\nsteps:\n  - name: x\n    type: xpath\n'
            '    inputs:\n      path: a.xml\n      xpath: "//v"\n    output: r\n')
        out = _sp("lint", "--pipeline", path)
        assert "unknown keyword" not in out and "Unknown step type" not in out, out

    def test_dry_run_loads_plugins_exactly_once(self, tmp_path):
        """A dry run goes through run_pipeline, so discovery fires — once."""
        path = self._pipeline(tmp_path,
            'name: t\nsteps:\n  - name: s\n    type: save\n'
            '    content: "hi"\n    saveas: "outputs/x.md"\n')
        out = _sp("run", "--pipeline", path, "--dry-run")
        starts = [ln for ln in out.splitlines() if "Loading plugins" in ln]
        assert len(starts) == 1, f"expected one discovery, got {len(starts)}:\n{out}"


class TestRegistryIsPopulatedInPlace:
    """The property that makes deferral safe: importers keep a live view."""

    def test_discovery_mutates_rather_than_rebinds(self):
        from llmflow.plugins import plugin_registry as imported_early
        from llmflow.plugins.loader import discover_plugins, plugin_registry

        assert imported_early is plugin_registry
        returned = discover_plugins()
        assert returned is imported_early, (
            "discover_plugins must populate the existing dict, not replace it — "
            "otherwise modules that imported it early would see an empty registry"
        )


class TestVersionSurvivesTheDistributionRename:
    """The distribution was renamed `llmflow` -> `scripture-pipelines` (f5e4d8f), but the
    console script is `sp` under both. Anyone with an older install still has a working
    `sp` whose distribution is named `llmflow`, and if that copy is earlier on PATH it
    shadows the released binary. Asking only for the new name yielded `unknown`.
    """

    def test_resolves_under_either_distribution_name(self, monkeypatch):
        import importlib

        seen = []

        def fake_version(name):
            seen.append(name)
            if name == "llmflow":
                return "0.2.1.18"
            raise importlib.metadata.PackageNotFoundError(name)

        monkeypatch.setattr("importlib.metadata.version", fake_version)
        import llmflow.cli as cli

        assert cli._resolve_version() == "0.2.1.18"
        assert "scripture-pipelines" in seen, "must try the current name first"

    def test_prefers_the_current_name(self, monkeypatch):
        monkeypatch.setattr("importlib.metadata.version",
                            lambda name: "9.9.9" if name == "scripture-pipelines" else None)
        import llmflow.cli as cli

        assert cli._resolve_version() == "9.9.9"

    def test_unknown_says_why(self, monkeypatch):
        """`unknown` alone is a dead end; it should hint at the cause."""
        import importlib

        def absent(name):
            raise importlib.metadata.PackageNotFoundError(name)

        monkeypatch.setattr("importlib.metadata.version", absent)
        import llmflow.cli as cli

        v = cli._resolve_version()
        assert "unknown" in v and "source" in v.lower(), v
