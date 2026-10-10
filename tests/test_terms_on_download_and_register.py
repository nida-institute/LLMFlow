"""A dataset announces its terms when it lands, and registering agrees to them (#252).

`sp resource list` showed the licence of what a machine already had, and the two commands that put
something new on it — `sp resource add` and `sp dataset download` — said nothing. As ruled in
`project/plans/plan-terms-on-download-and-register.md` §2 and §2a:

- both commands print the licence, and a link to the agreement;
- registering asks for agreement, with `--accept-terms` for scripts, and fails closed without a
  terminal; downloading prints and proceeds;
- the licence string is a summary agreed to, and any pointer in it is recorded beside it;
- the full text is fetched when it can be, saved beside the registration, and hashed;
- a licence that only points elsewhere, and whose text could not be fetched, is shown and not
  gated;
- agreement is recorded on the registration, because a user needs it when publishing, and
  `sp resource terms` reads it back.
"""
import base64
import hashlib
import io
import json

import pytest
import yaml

from llmflow import cli
from llmflow import resources as R

CATALOG = [
    {
        "id": "macula-hebrew",
        "name": "Macula Hebrew",
        "license": "CC BY 4.0",
        "github": "https://github.com/Clear-Bible/macula-hebrew",
        "url": "https://github.com/Clear-Bible/macula-hebrew",
        "provides": [{"id": "WLC", "kind": "tsv", "path": "WLC/tsv/macula-hebrew.tsv"}],
    },
    {
        "id": "sblgnt",
        "name": "SBLGNT",
        "license": "Custom — see http://sblgnt.com/license/",
        "github": "https://github.com/LogosBible/SBLGNT",
        "url": "https://sblgnt.com",
        "provides": [{"id": "SBLGNT", "kind": "tei", "path": "data/sblgnt.xml"}],
    },
    {
        "id": "odd-one",
        "name": "A text under a licence with no standard page",
        "license": "Open",
        "github": "https://github.com/example/odd-one",
        "url": "https://example.org/odd-one",
        "provides": [{"id": "ODD", "kind": "tsv", "path": "odd.tsv"}],
    },
    {
        "id": "acai",
        "name": "ACAI",
        "license": "CC BY-SA 4.0",
        "github": "https://github.com/BibleAquifer/ACAI",
        "url": "https://github.com/BibleAquifer/ACAI",
    },
    {
        "id": "repo-only",
        "name": "A text whose licence is only a pointer",
        "license": "See repo",
        "github": "https://github.com/example/repo-only",
        "url": "https://github.com/example/repo-only",
        "provides": [{"id": "SEEREPO", "kind": "tsv", "path": "x.tsv"}],
    },
]

MIT_TEXT = "MIT License\n\nCopyright (c) Example\n\nPermission is hereby granted, free of charge,\n"


@pytest.fixture(autouse=True)
def web(monkeypatch):
    """The network, as a table of URL → (status, content type, body). Anything else is offline."""
    pages = {}

    def get(url, accept=None):
        if url not in pages:
            raise OSError(f"no route to {url}")
        return pages[url]

    monkeypatch.setattr(R, "_http_get", get)
    return pages


def _github_licence(text):
    body = {
        "content": base64.b64encode(text.encode()).decode(),
        "encoding": "base64",
        "html_url": "https://github.com/x/y/blob/main/LICENSE",
        "license": {"spdx_id": "MIT"},
    }
    return 200, "application/json", json.dumps(body).encode()


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    path = tmp_path / "resources.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    monkeypatch.setattr(R, "catalog_path", lambda: path)
    R.catalog.cache_clear()
    yield path
    R.catalog.cache_clear()


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("SP_HOME", str(tmp_path / "sp"))
    return tmp_path / "sp"


@pytest.fixture
def terminal(monkeypatch):
    """A terminal whose user answers the prompt with whatever the test sets."""
    answers = []

    class Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", Tty())

    def confirm(text, default=False, **_):
        answers.append(text)
        return answer["value"]

    answer = {"value": True}
    monkeypatch.setattr("click.confirm", confirm)
    return answer


@pytest.fixture
def no_terminal(monkeypatch):
    class Piped(io.StringIO):
        def isatty(self):
            return False

    # `yes | sp resource add X` — input is there, and still nobody read the terms.
    monkeypatch.setattr("sys.stdin", Piped("y\n" * 10))


def _add(*argv):
    cli.main(["resource", "add", *argv, "--no-download"])


def _registration(store, identifier):
    path = store / "registrations" / f"{identifier}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None


# --- the link to the agreement -------------------------------------------------------


def test_a_url_inside_the_licence_is_the_link():
    assert R.licence_link(CATALOG[1]) == ("http://sblgnt.com/license/", "licence")


def test_a_standard_licence_links_to_its_own_page():
    assert R.licence_link(CATALOG[0]) == (
        "https://creativecommons.org/licenses/by/4.0/", "licence",
    )


def test_otherwise_the_link_is_the_source_page_and_says_so():
    """Never mistaken for the agreement: it is where the agreement may be found."""
    assert R.licence_link(CATALOG[2]) == ("https://example.org/odd-one", "source-page")


def test_a_licence_with_nothing_but_see_is_only_a_pointer():
    assert R.is_pointer("See repo")
    assert R.is_pointer("See site")
    assert not R.is_pointer("CC BY 4.0")
    assert not R.is_pointer("Open")


def test_a_summary_that_also_points_is_a_summary():
    """`Apache-2.0`, `Restricted`, even `Custom` say something before they point elsewhere."""
    assert not R.is_pointer("Apache-2.0 (code) — see LICENSE.md for data terms")
    assert not R.is_pointer("Custom — see http://sblgnt.com/license/")
    assert not R.is_pointer("Restricted — see http://example.org/declaration.txt")


def test_the_pointer_is_the_part_that_sends_you_elsewhere():
    assert R.pointer_of("Apache-2.0 (code) — see LICENSE.md for data terms") == (
        "see LICENSE.md for data terms"
    )
    assert R.pointer_of("CC BY 4.0") is None


# --- fetching the full text ----------------------------------------------------------


def test_a_repository_s_licence_is_fetched_through_github(web):
    web["https://api.github.com/repos/Clear-Bible/macula-hebrew/license"] = _github_licence(MIT_TEXT)
    fetched = R.fetch_licence_text(CATALOG[0])
    assert fetched["text"] == MIT_TEXT
    assert fetched["sha256"] == hashlib.sha256(MIT_TEXT.encode()).hexdigest()
    assert fetched["source"] == "https://github.com/x/y/blob/main/LICENSE"


def test_a_plain_text_url_in_the_licence_is_fetched(web):
    url = "http://example.org/declaration.txt"
    web[url] = (200, "text/plain; charset=utf-8", b"You declare that you will not sell it.\n")
    fetched = R.fetch_licence_text({"license": f"Restricted — see {url}"})
    assert fetched["text"].startswith("You declare")
    assert fetched["source"] == url


def test_a_github_blob_link_is_fetched_as_the_raw_file(web):
    raw = "https://raw.githubusercontent.com/b/levinsohn/master/LICENSE.md"
    web[raw] = (200, "text/plain", b"Not for sale.\n")
    fetched = R.fetch_licence_text(
        {"license": "freely distributable. See https://github.com/b/levinsohn/blob/master/LICENSE.md"}
    )
    assert fetched["text"] == "Not for sale.\n"


def test_a_web_page_is_a_link_and_not_text(web):
    """Scraping HTML would put markup in the record; the named page stays the record."""
    url = "http://sblgnt.com/license/"
    web[url] = (200, "text/html", b"<html>...</html>")
    fetched = R.fetch_licence_text(CATALOG[1])
    assert "text" not in fetched
    assert "web page" in fetched["reason"]


def test_a_named_url_is_not_replaced_by_the_repository_s_licence(web):
    """The string names its terms; another file from the same repository may be other terms."""
    web["http://sblgnt.com/license/"] = (200, "text/html", b"<html/>")
    web["https://api.github.com/repos/LogosBible/SBLGNT/license"] = _github_licence(MIT_TEXT)
    assert "text" not in R.fetch_licence_text(CATALOG[1])


def test_a_repository_without_a_licence_file_says_so(web):
    web["https://api.github.com/repos/Clear-Bible/macula-hebrew/license"] = (404, "", b"")
    assert "no licence file" in R.fetch_licence_text(CATALOG[0])["reason"]


def test_offline_says_so(web):
    assert "could not reach" in R.fetch_licence_text(CATALOG[0])["reason"]


def test_nothing_to_fetch_from_says_so(web):
    assert "nowhere" in R.fetch_licence_text({"license": "Open"})["reason"]


# --- sp dataset download -------------------------------------------------------------


def test_download_prints_the_licence_before_fetching(catalog, store, monkeypatch, capsys):
    seen_at_fetch = {}

    def fetch(entry, dest=None):
        seen_at_fetch["out"] = capsys.readouterr().out

    monkeypatch.setattr("llmflow.download_data.fetch", fetch)
    cli.main(["dataset", "download", "acai"])
    assert "CC BY-SA 4.0" in seen_at_fetch["out"]
    assert "https://creativecommons.org/licenses/by-sa/4.0/" in seen_at_fetch["out"]


def test_download_does_not_ask(catalog, store, monkeypatch, no_terminal):
    """Downloading a file you then delete is not agreement to anything."""
    monkeypatch.setattr("llmflow.download_data.fetch", lambda entry, dest=None: None)
    cli.main(["dataset", "download", "acai"])  # no terminal, no flag, and no exit


# --- sp resource add: printing -------------------------------------------------------


def test_add_prints_the_licence_before_writing(catalog, store, terminal, monkeypatch, capsys):
    seen_at_write = {}
    real = R._write_registration

    def write(target, banner, entry):
        seen_at_write["out"] = capsys.readouterr().out
        return real(target, banner, entry)

    monkeypatch.setattr(R, "_write_registration", write)
    _add("WLC")
    assert "CC BY 4.0" in seen_at_write["out"]
    assert "https://creativecommons.org/licenses/by/4.0/" in seen_at_write["out"]


def test_add_by_path_says_there_is_no_licence(store, tmp_path, no_terminal, capsys):
    mine = tmp_path / "mine.tsv"
    mine.write_text("id\ttext\n", encoding="utf-8")
    cli.main(["resource", "add", "MINE", "--path", str(mine), "--kind", "tsv"])
    out = capsys.readouterr().out
    assert "no catalog licence" in out.lower()
    assert _registration(store, "MINE") is not None


# --- sp resource add: the gate -------------------------------------------------------


def test_no_terminal_and_no_flag_exits_and_names_the_flag(catalog, store, no_terminal, capsys):
    with pytest.raises(SystemExit) as raised:
        _add("WLC")
    assert raised.value.code != 0
    assert "--accept-terms" in capsys.readouterr().out
    assert _registration(store, "WLC") is None


def test_accept_terms_registers_without_prompting(catalog, store, no_terminal):
    _add("WLC", "--accept-terms")
    assert _registration(store, "WLC")["terms"]["via"] == "--accept-terms"


def test_a_declined_prompt_leaves_no_registration(catalog, store, terminal, monkeypatch):
    """The check that the gate is a gate."""
    fetched = []
    monkeypatch.setattr("llmflow.download_data.fetch", lambda *a, **k: fetched.append(a))
    terminal["value"] = False
    with pytest.raises(SystemExit) as raised:
        cli.main(["resource", "add", "WLC"])
    assert raised.value.code != 0
    assert _registration(store, "WLC") is None
    assert not fetched, "declining comes before the download, not after it"


def test_an_agreed_prompt_records_the_agreement(catalog, store, terminal):
    _add("WLC")
    terms = _registration(store, "WLC")["terms"]
    assert terms["license"] == "CC BY 4.0"
    assert terms["agreed_to"] == "summary"
    assert terms["link"] == "https://creativecommons.org/licenses/by/4.0/"
    assert terms["link_kind"] == "licence"
    assert terms["via"] == "prompt"
    assert terms["presented"] is True
    assert str(terms["agreed"])


def test_a_summary_that_points_is_asked_and_records_its_pointer(catalog, store, no_terminal):
    with pytest.raises(SystemExit):
        _add("SBLGNT")
    _add("SBLGNT", "--accept-terms")
    terms = _registration(store, "SBLGNT")["terms"]
    assert terms["agreed_to"] == "summary"
    assert terms["pointer"] == "see http://sblgnt.com/license/"


def test_an_unfetched_pointer_is_registered_without_asking(catalog, store, no_terminal, capsys):
    """Asking someone to agree to a link they have not followed is a `y` that means nothing.
    Shown, registered, and recorded as shown."""
    _add("SEEREPO")
    terms = _registration(store, "SEEREPO")["terms"]
    assert terms["presented"] is True
    assert "agreed" not in terms and "via" not in terms
    assert "https://github.com/example/repo-only" in capsys.readouterr().out


def test_a_pointer_whose_text_was_fetched_is_asked(
    catalog, store, no_terminal, web, monkeypatch
):
    """Once the text is in hand there is something real to agree to."""
    monkeypatch.setattr("llmflow.download_data.fetch", lambda *a, **k: None)
    web["https://api.github.com/repos/example/repo-only/license"] = _github_licence(MIT_TEXT)
    with pytest.raises(SystemExit):
        cli.main(["resource", "add", "SEEREPO"])
    cli.main(["resource", "add", "SEEREPO", "--accept-terms"])
    assert _registration(store, "SEEREPO")["terms"]["agreed_to"] == "text"


# --- the saved text ------------------------------------------------------------------


def test_the_fetched_text_is_shown_saved_and_hashed(
    catalog, store, terminal, web, monkeypatch, capsys
):
    monkeypatch.setattr("llmflow.download_data.fetch", lambda *a, **k: None)
    web["https://api.github.com/repos/Clear-Bible/macula-hebrew/license"] = _github_licence(MIT_TEXT)
    cli.main(["resource", "add", "WLC"])
    assert "Permission is hereby granted" in capsys.readouterr().out
    terms = _registration(store, "WLC")["terms"]
    saved = store / "registrations" / "WLC.licence.txt"
    assert terms["text"] == str(saved)
    assert saved.read_text(encoding="utf-8") == MIT_TEXT
    assert terms["text_sha256"] == hashlib.sha256(MIT_TEXT.encode()).hexdigest()


def test_no_download_fetches_no_licence_and_says_so(catalog, store, terminal):
    _add("WLC")
    assert "--no-download" in _registration(store, "WLC")["terms"]["text_not_fetched"]


def test_a_failed_fetch_still_asks_and_says_why(catalog, store, terminal, monkeypatch):
    monkeypatch.setattr("llmflow.download_data.fetch", lambda *a, **k: None)
    cli.main(["resource", "add", "WLC"])
    terms = _registration(store, "WLC")["terms"]
    assert terms["via"] == "prompt"
    assert "could not reach" in terms["text_not_fetched"]


def test_changed_text_under_the_same_summary_is_asked_again(
    catalog, store, no_terminal, web, monkeypatch
):
    monkeypatch.setattr("llmflow.download_data.fetch", lambda *a, **k: None)
    url = "https://api.github.com/repos/Clear-Bible/macula-hebrew/license"
    web[url] = _github_licence(MIT_TEXT)
    cli.main(["resource", "add", "WLC", "--accept-terms"])
    web[url] = _github_licence(MIT_TEXT + "Except for commercial use.\n")
    with pytest.raises(SystemExit):
        cli.main(["resource", "add", "WLC"])


def test_agreement_is_asked_once(catalog, store, no_terminal):
    """L2: recorded, so re-registering the same terms does not ask again — here, with no
    terminal and no flag, which would otherwise fail closed."""
    _add("WLC", "--accept-terms")
    _add("WLC")
    assert _registration(store, "WLC")["terms"]["via"] == "--accept-terms"


def test_changed_terms_are_asked_again(catalog, store, no_terminal, monkeypatch):
    _add("WLC", "--accept-terms")
    changed = [dict(CATALOG[0], license="CC BY-NC 4.0"), *CATALOG[1:]]
    catalog.write_text(json.dumps(changed), encoding="utf-8")
    R.catalog.cache_clear()
    with pytest.raises(SystemExit):
        _add("WLC")
    assert _registration(store, "WLC")["terms"]["license"] == "CC BY 4.0"


# --- sp resource terms ---------------------------------------------------------------


def test_terms_lists_every_registration_and_what_was_agreed(catalog, store, no_terminal, capsys):
    _add("WLC", "--accept-terms")
    _add("SEEREPO")
    capsys.readouterr()
    cli.main(["resource", "terms"])
    out = capsys.readouterr().out
    assert "WLC" in out and "https://creativecommons.org/licenses/by/4.0/" in out
    assert "SEEREPO" in out and "not agreed" in out


def test_terms_names_where_the_agreed_text_is_saved(
    catalog, store, no_terminal, web, monkeypatch, capsys
):
    monkeypatch.setattr("llmflow.download_data.fetch", lambda *a, **k: None)
    web["https://api.github.com/repos/Clear-Bible/macula-hebrew/license"] = _github_licence(MIT_TEXT)
    cli.main(["resource", "add", "WLC", "--accept-terms"])
    capsys.readouterr()
    cli.main(["resource", "terms", "WLC"])
    assert "WLC.licence.txt" in capsys.readouterr().out


def test_terms_can_name_the_resources_a_publication_used(catalog, store, no_terminal, capsys):
    _add("WLC", "--accept-terms")
    _add("SEEREPO")
    capsys.readouterr()
    cli.main(["resource", "terms", "WLC"])
    out = capsys.readouterr().out
    assert "WLC" in out and "SEEREPO" not in out


def test_terms_for_a_registration_that_predates_the_record_says_so(catalog, store, capsys):
    registrations = store / "registrations"
    registrations.mkdir(parents=True)
    (registrations / "WLC.yaml").write_text("id: WLC\nlicense: CC BY 4.0\n", encoding="utf-8")
    cli.main(["resource", "terms", "WLC"])
    assert "sp resource add WLC" in capsys.readouterr().out


def test_terms_for_something_not_registered_is_an_error(catalog, store, capsys):
    with pytest.raises(SystemExit) as raised:
        cli.main(["resource", "terms", "NOPE"])
    assert raised.value.code != 0
    assert "NOPE" in capsys.readouterr().out
