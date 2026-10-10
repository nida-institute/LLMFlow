"""Lint names the resources a pipeline needs, and offers to install the missing ones (#261).

A pipeline that named an unregistered resource linted clean and failed part-way through the run,
after earlier steps — LLM steps among them — had been paid for. As ruled in
`project/plans/plan-resource-preflight.md` §2:

- an unregistered resource is a lint error, and so is a requested `include:` family whose path
  the registration does not name;
- the table of what is missing is printed only when something is;
- `sp lint` itself offers to install, through the same code as `sp resource add`, licence and all;
- without a terminal, `--install-missing` answers the install and `--accept-terms` the licence —
  one flag per consent;
- a registration made before licences were recorded is offered the licence, not reinstalled.
"""
import io
import json
from types import SimpleNamespace

import pytest
import yaml

from llmflow import cli, load_pipeline
from llmflow import resources as R

CATALOG = [
    {
        "id": "macula-greek-nt",
        "name": "Macula Greek",
        "license": "CC BY 4.0",
        "github": "https://github.com/Clear-Bible/macula-greek",
        "url": "https://github.com/Clear-Bible/macula-greek",
        "provides": [{"id": "SBLGNT", "kind": "tsv", "path": "SBLGNT/tsv/sblgnt.tsv"}],
    },
    {
        "id": "bsb",
        "name": "BSB",
        "license": "Public domain",
        "url": "https://berean.bible",
        "download": "https://example.org/bsb.zip",
        "provides": [{"id": "BSB", "kind": "usfm", "path": "bsb_usfm"}],
    },
]


@pytest.fixture(autouse=True)
def catalog(tmp_path, monkeypatch):
    path = tmp_path / "resources.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    monkeypatch.setattr(R, "catalog_path", lambda: path)
    R.catalog.cache_clear()
    yield path
    R.catalog.cache_clear()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """No test reaches the network: licence texts are not fetched, downloads are recorded."""
    def unreachable(url, accept=None):
        raise OSError(f"no route to {url}")

    downloads = []
    monkeypatch.setattr(R, "_http_get", unreachable)
    monkeypatch.setattr("llmflow.download_data.fetch", lambda item, dest=None: downloads.append(item))
    return downloads


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("SP_HOME", str(tmp_path / "sp"))
    return tmp_path / "sp"


@pytest.fixture
def terminal(monkeypatch):
    """A person at a terminal. `answers` feeds the install question; `agree` answers licences."""
    class Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", Tty())
    state = SimpleNamespace(answers=[], asked=[], agree=True, licences_asked=[])

    def prompt(text, **_):
        state.asked.append(text)
        return state.answers.pop(0)

    def confirm(text, default=False, **_):
        state.licences_asked.append(text)
        return state.agree

    monkeypatch.setattr("click.prompt", prompt)
    monkeypatch.setattr("click.confirm", confirm)
    return state


@pytest.fixture
def no_terminal(monkeypatch):
    class Piped(io.StringIO):
        def isatty(self):
            return False

    monkeypatch.setattr("sys.stdin", Piped("y\n" * 10))


def _register(store, identifier, **fields):
    registrations = store / "registrations"
    registrations.mkdir(parents=True, exist_ok=True)
    entry = {"id": identifier, "kind": "tsv", "path": "/tmp/x.tsv", **fields}
    (registrations / f"{identifier}.yaml").write_text(yaml.safe_dump(entry), encoding="utf-8")


def _agreed(store, identifier, **fields):
    _register(store, identifier, terms={"license": "CC BY 4.0", "via": "prompt"}, **fields)


def _pipeline(tmp_path, *steps, variables=None):
    path = tmp_path / "p.yaml"
    path.write_text(
        yaml.safe_dump({"name": "p", "variables": variables or {}, "steps": list(steps)}),
        encoding="utf-8",
    )
    return path


def _scripture(resource, include=None, name="text"):
    step = {"name": name, "type": "scripture", "resource": resource, "passage": "MRK 1:1",
            "output": name}
    if include:
        step["include"] = include
    return step


# --- what lint finds -----------------------------------------------------------------


def test_an_unregistered_resource_is_a_lint_error_naming_the_fix(tmp_path, store):
    result = load_pipeline(_pipeline(tmp_path, _scripture("BSB"))).lint()
    assert not result.valid
    assert any("sp resource add BSB" in e for e in result.errors)


def test_a_registered_resource_lints_clean(tmp_path, store):
    _agreed(store, "BSB")
    assert load_pipeline(_pipeline(tmp_path, _scripture("BSB"))).lint().valid


def test_a_requested_family_without_its_path_is_a_lint_error(tmp_path, store):
    _agreed(store, "SBLGNT")
    result = load_pipeline(_pipeline(tmp_path, _scripture("SBLGNT", ["ids", "syntax"]))).lint()
    assert not result.valid
    assert any("sp resource set SBLGNT --lowfat-path" in e for e in result.errors)


def test_a_requested_family_with_its_path_lints_clean(tmp_path, store):
    lowfat = tmp_path / "lowfat"
    lowfat.mkdir()
    _agreed(store, "SBLGNT", lowfat_path=str(lowfat))
    path = _pipeline(tmp_path, _scripture("SBLGNT", ["ids", "syntax"]))
    assert load_pipeline(path).lint().valid


def test_a_path_that_names_nothing_is_missing_too(tmp_path, store):
    _agreed(store, "SBLGNT", discourse_path=str(tmp_path / "nowhere"))
    result = load_pipeline(_pipeline(tmp_path, _scripture("SBLGNT", ["discourse"]))).lint()
    assert any("--discourse-path" in e for e in result.errors)


def test_a_resource_inside_a_for_each_is_found(tmp_path, store):
    loop = {"name": "each", "type": "for-each", "for": "thing", "in": "${things}",
            "steps": [_scripture("BSB")]}
    result = load_pipeline(_pipeline(tmp_path, loop, variables={"things": [1]})).lint()
    assert any("sp resource add BSB" in e for e in result.errors)


def test_a_resource_needed_only_under_a_condition_is_a_warning(tmp_path, store):
    """Lint cannot know whether the condition will hold — the starter fetches Greek or Hebrew by
    the passage's testament — so the run may well succeed without it."""
    step = dict(_scripture("BSB"), condition="${passage_info.testament == 'OT'}")
    result = load_pipeline(_pipeline(tmp_path, step, variables={"passage_info": {}})).lint()
    assert result.valid
    assert any("BSB" in w and "condition" in w for w in result.warnings)


def test_a_resource_also_needed_unconditionally_is_still_an_error(tmp_path, store):
    conditional = dict(_scripture("BSB", name="a"), condition="${flag}")
    result = load_pipeline(
        _pipeline(tmp_path, conditional, _scripture("BSB", name="b"), variables={"flag": True})
    ).lint()
    assert not result.valid


def test_a_family_asked_for_only_under_a_condition_is_a_warning(tmp_path, store):
    """The starter names SBLGNT everywhere, and asks for `syntax` only in its Greek step."""
    _agreed(store, "SBLGNT")
    greek = dict(_scripture("SBLGNT", ["syntax"], name="a"), condition="${flag}")
    result = load_pipeline(
        _pipeline(tmp_path, greek, _scripture("SBLGNT", name="b"), variables={"flag": True})
    ).lint()
    assert result.valid, result.errors
    assert any("lowfat_path" in w for w in result.warnings)


def test_a_conditional_resource_is_still_offered(tmp_path, store, terminal):
    terminal.answers = ["y"]
    step = dict(_scripture("BSB"), condition="${flag}")
    _lint(_pipeline(tmp_path, step, variables={"flag": True}))
    assert (store / "registrations" / "BSB.yaml").exists()


def test_a_resource_named_by_a_variable_is_resolved_from_var(tmp_path, store):
    path = _pipeline(tmp_path, _scripture("${text}"), variables={"text": "SBLGNT"})
    _agreed(store, "SBLGNT")
    assert load_pipeline(path).lint().valid
    result = load_pipeline(path).lint(vars={"text": "BSB"})
    assert any("sp resource add BSB" in e for e in result.errors)


def test_a_registration_without_a_licence_record_is_a_warning(tmp_path, store):
    """It opens; only the record of the terms is missing."""
    _register(store, "BSB")
    result = load_pipeline(_pipeline(tmp_path, _scripture("BSB"))).lint()
    assert result.valid
    assert any("BSB" in w and "licence" in w for w in result.warnings)


def test_an_alignment_corpus_is_checked_as_a_dataset(tmp_path, store, monkeypatch):
    monkeypatch.setattr(
        "llmflow.steps.alignment.declared_pairs",
        lambda: {"dataset": "alignments-corpus", "pairs": []},
    )
    step = {"name": "al", "type": "alignment", "source": "SBLGNT", "target": "BSB",
            "spans": "${spans}", "output": "al"}
    result = load_pipeline(_pipeline(tmp_path, step, variables={"spans": []})).lint()
    assert any("sp dataset add alignments-corpus" in e for e in result.errors)


def test_the_library_lint_never_prompts_and_never_writes(tmp_path, store, terminal):
    load_pipeline(_pipeline(tmp_path, _scripture("BSB"))).lint()
    assert not terminal.asked and not terminal.licences_asked
    assert not (store / "registrations" / "BSB.yaml").exists()


# --- what sp lint prints --------------------------------------------------------------


def _lint(path, *flags):
    cli.main(["lint", "--pipeline", str(path), *flags])


def test_nothing_missing_prints_no_table(tmp_path, store, no_terminal, capsys):
    _agreed(store, "BSB")
    _lint(_pipeline(tmp_path, _scripture("BSB")))
    assert "Resources this pipeline needs" not in capsys.readouterr().out


def test_something_missing_prints_the_table(tmp_path, store, no_terminal, capsys):
    with pytest.raises(SystemExit):
        _lint(_pipeline(tmp_path, _scripture("BSB")))
    out = capsys.readouterr().out
    assert "Resources this pipeline needs" in out and "NOT REGISTERED" in out


# --- the offer -----------------------------------------------------------------------


def test_yes_installs_through_resource_add_and_shows_the_licence(
    tmp_path, store, terminal, offline, capsys
):
    terminal.answers = ["y"]
    _lint(_pipeline(tmp_path, _scripture("BSB")))
    registration = yaml.safe_load((store / "registrations" / "BSB.yaml").read_text())
    assert registration["terms"]["via"] == "prompt"
    assert "Public domain" in capsys.readouterr().out
    assert offline, "the download ran, as `sp resource add` would"


def test_no_leaves_it_missing_and_lint_fails(tmp_path, store, terminal):
    terminal.answers = ["n"]
    with pytest.raises(SystemExit) as raised:
        _lint(_pipeline(tmp_path, _scripture("BSB")))
    assert raised.value.code != 0
    assert not (store / "registrations" / "BSB.yaml").exists()


def test_all_installs_the_rest_but_still_asks_each_licence(tmp_path, store, terminal):
    terminal.answers = ["a"]
    _lint(_pipeline(tmp_path, _scripture("BSB", name="a"), _scripture("SBLGNT", name="b")))
    assert len(terminal.asked) == 1, "one install question answers the rest"
    assert len(terminal.licences_asked) == 2, "each licence is its own agreement"


def test_a_declined_licence_leaves_that_resource_missing(tmp_path, store, terminal):
    terminal.answers = ["y"]
    terminal.agree = False
    with pytest.raises(SystemExit):
        _lint(_pipeline(tmp_path, _scripture("BSB")))
    assert not (store / "registrations" / "BSB.yaml").exists()


def test_a_missing_path_names_the_command_and_is_not_guessed(tmp_path, store, terminal, capsys):
    """Nothing declares where Lowfat lives, so no path is invented for the user to accept."""
    _agreed(store, "SBLGNT")
    with pytest.raises(SystemExit):
        _lint(_pipeline(tmp_path, _scripture("SBLGNT", ["syntax"])))
    assert "sp resource set SBLGNT --lowfat-path" in capsys.readouterr().out
    assert not terminal.asked


# --- without a terminal --------------------------------------------------------------


def test_no_terminal_and_no_flag_names_install_missing(tmp_path, store, no_terminal, capsys):
    with pytest.raises(SystemExit):
        _lint(_pipeline(tmp_path, _scripture("BSB")))
    assert "--install-missing" in capsys.readouterr().out


def test_install_missing_without_accept_terms_stops_at_the_licence(
    tmp_path, store, no_terminal, capsys
):
    with pytest.raises(SystemExit):
        _lint(_pipeline(tmp_path, _scripture("BSB")), "--install-missing")
    assert "--accept-terms" in capsys.readouterr().out
    assert not (store / "registrations" / "BSB.yaml").exists()


def test_both_flags_prepare_the_machine(tmp_path, store, no_terminal):
    _lint(_pipeline(tmp_path, _scripture("BSB")), "--install-missing", "--accept-terms")
    registration = yaml.safe_load((store / "registrations" / "BSB.yaml").read_text())
    assert registration["terms"]["via"] == "--accept-terms"


# --- a registration without a licence record -----------------------------------------


def test_an_unrecorded_licence_is_offered_without_reinstalling(
    tmp_path, store, terminal, offline
):
    _register(store, "BSB")
    _lint(_pipeline(tmp_path, _scripture("BSB")))
    registration = yaml.safe_load((store / "registrations" / "BSB.yaml").read_text())
    assert registration["terms"]["via"] == "prompt"
    assert registration["path"] == "/tmp/x.tsv", "the registration is kept, not rewritten"
    assert not offline, "nothing is downloaded to record a licence"


def test_an_unrecorded_licence_is_recorded_by_accept_terms(tmp_path, store, no_terminal):
    _register(store, "BSB")
    _lint(_pipeline(tmp_path, _scripture("BSB")), "--accept-terms")
    registration = yaml.safe_load((store / "registrations" / "BSB.yaml").read_text())
    assert registration["terms"]["via"] == "--accept-terms"


def test_an_unrecorded_licence_without_a_terminal_does_not_fail_lint(
    tmp_path, store, no_terminal
):
    _register(store, "BSB")
    _lint(_pipeline(tmp_path, _scripture("BSB")))  # no SystemExit


# --- sp run inherits it --------------------------------------------------------------


def test_run_stops_before_any_step(tmp_path, store, no_terminal, monkeypatch, capsys):
    ran = []
    monkeypatch.setattr("llmflow.model.Pipeline.run", lambda *a, **k: ran.append(1))
    with pytest.raises(SystemExit):
        cli.main(["run", "--pipeline", str(_pipeline(tmp_path, _scripture("BSB")))])
    assert not ran
    assert "--install-missing" in capsys.readouterr().out


def test_run_installs_with_the_flags_and_then_runs(tmp_path, store, no_terminal, monkeypatch):
    ran = []
    monkeypatch.setattr("llmflow.model.Pipeline.run", lambda *a, **k: ran.append(1))
    cli.main(["run", "--pipeline", str(_pipeline(tmp_path, _scripture("BSB"))),
              "--install-missing", "--accept-terms"])
    assert ran
