"""Guardrail: every rule declares whether a test can catch it, and who may enforce it.

Two fields, answering two different questions:

- `enforcement` — what holds it: guarded, partial, guardable, gated, judgment.
- `scope` — who may do the catching: `language` (the engine, for every user), `project` (a
  repository, over its own files), `harness` (the operator's permission gates and hooks), or
  `none`.

`gated` is the strongest of the five and the one the first four values could not express. A test
catches a breach before it ships; a **gate stops the act happening at all** — a `PreToolUse` hook,
or an `ask` entry in the operator's settings that puts the command in front of a human. Rules held
that way were being recorded as `judgment`, the weakest value, because the vocabulary had no word
for them.

**A gate is not verifiable from this repository**, which is the cost of the value and is stated
rather than hidden: it lives in the operator's environment, so a fresh clone on another machine has
the rule as `judgment` until that machine is configured. `guard:` names a file these tests can
open; `gate:` names a mechanism they can only take on trust.

The second exists because the first invites a mistake. A rule can be perfectly checkable and
still not be the engine's business: `sp` serves pipelines that publish, that process scripture
in Python with no model, and that are not about scripture at all. A rule of this domain placed
in `sp lint` would make the language refuse programs that are valid in the language.

`scope: none` and `enforcement: judgment` state the same fact from two directions, so they must
agree.

Read through `llmflow.ai_rules`, which is the API for the rules, rather than by parsing
`data/ai-rules.yaml` — the declaration is the source and the accessor is how everything else
reaches it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from llmflow import ai_rules

ENFORCEMENT_VALUES = {"guarded", "partial", "guardable", "gated", "judgment"}
SCOPE_VALUES = {"language", "project", "harness", "none"}


def test_the_data_declares_rules():
    """Asserted directly, so nothing below can pass on an empty set."""
    assert ai_rules.entries(), "data/ai-rules.yaml declares no rules"


@pytest.mark.parametrize("entry", ai_rules.entries(), ids=lambda e: e["id"])
def test_every_rule_declares_both_classifications(entry):
    for field in ("enforcement", "scope"):
        assert field in entry, (
            f"rule `{entry['id']}` declares no `{field}`. A rule nobody has classified is one "
            f"nobody has asked the governing question about, and it silently escapes the "
            f"triage in #230."
        )


@pytest.mark.parametrize("entry", ai_rules.entries(), ids=lambda e: e["id"])
def test_classifications_use_declared_values(entry):
    assert entry["enforcement"] in ENFORCEMENT_VALUES, (
        f"rule `{entry['id']}` has enforcement {entry['enforcement']!r}; "
        f"expected one of {sorted(ENFORCEMENT_VALUES)}"
    )
    assert entry["scope"] in SCOPE_VALUES, (
        f"rule `{entry['id']}` has scope {entry['scope']!r}; "
        f"expected one of {sorted(SCOPE_VALUES)}"
    )


@pytest.mark.parametrize("entry", ai_rules.entries(), ids=lambda e: e["id"])
def test_unenforceable_rules_agree_on_both_axes(entry):
    """`scope: none` means no test can catch it, which is what `judgment` says.

    Declaring a rule guardable while also declaring that nobody may guard it is how a
    scheduled piece of work turns out on inspection to be impossible — which is exactly what
    happened to the source-text rule and the draft-output phrase scan.
    """
    if entry["scope"] == "none":
        assert entry["enforcement"] == "judgment", (
            f"rule `{entry['id']}` is scope: none but enforcement: {entry['enforcement']}. "
            f"If nobody can enforce it, it is judgment; if someone can, say who."
        )
    if entry["enforcement"] == "judgment":
        assert entry["scope"] == "none", (
            f"rule `{entry['id']}` is enforcement: judgment but scope: {entry['scope']}. "
            f"Naming an enforcer for a rule no test can catch is a contradiction."
        )
    if entry["enforcement"] == "gated":
        assert entry["scope"] == "harness", (
            f"rule `{entry['id']}` is enforcement: gated but scope: {entry['scope']}. A gate is "
            f"held by the operator's permission layer, not by the engine or by a repository."
        )
    if entry["scope"] == "harness":
        assert entry["enforcement"] == "gated", (
            f"rule `{entry['id']}` is scope: harness but enforcement: {entry['enforcement']}. "
            f"The harness enforces by gating an act, which is what `gated` names."
        )


@pytest.mark.parametrize("entry", ai_rules.entries(), ids=lambda e: e["id"])
def test_a_guarded_rule_names_its_guard(entry):
    """`enforcement: guarded` means a test fails today — so it must say which."""
    if entry["enforcement"] != "guarded":
        return
    guard = (entry.get("guard") or "").strip()
    assert guard, (
        f"rule `{entry['id']}` is guarded but names no `guard:`. A rule shortened to a "
        f"sentence relies on the field to say where the enforcement lives; without it the "
        f"reader is told a test exists and not which one."
    )


@pytest.mark.parametrize("entry", ai_rules.entries(), ids=lambda e: e["id"])
def test_every_named_guard_exists(entry):
    """A `guard:` naming a file that is not there is worse than naming nothing.

    This is the failure the rule-shortening raised in the first place: a rule that points at
    its test reads as enforced, so a pointer to a deleted or renamed test quietly downgrades
    the rule while looking like an improvement.
    """
    guard = (entry.get("guard") or "").strip()
    if not guard:
        return
    repo_root = Path(__file__).resolve().parent.parent
    for named in (part.strip() for part in guard.split(",")):
        assert (repo_root / named).is_file(), (
            f"rule `{entry['id']}` names {named!r} as its guard, and that file does not "
            f"exist. Point at a real test, or drop the claim to be guarded."
        )


@pytest.mark.parametrize("entry", ai_rules.entries(), ids=lambda e: e["id"])
def test_a_gated_rule_names_its_gate(entry):
    """`gated` claims an act is stopped before it happens, so it must say by what.

    These tests cannot open the operator's settings to confirm it, which is exactly why the claim
    has to be legible: a reader can check `gate:` against their own configuration and find out
    whether the rule is gated *for them*. Naming nothing would leave them unable to.
    """
    if entry["enforcement"] != "gated":
        return
    gate = (entry.get("gate") or "").strip()
    assert gate, (
        f"rule `{entry['id']}` is gated but names no `gate:`. Say which hook or permission entry "
        f"stops the act, since this repository cannot verify it and the reader must."
    )


@pytest.mark.parametrize("entry", ai_rules.entries(), ids=lambda e: e["id"])
def test_a_rule_whose_test_exists_is_not_still_called_guardable(entry):
    """The other direction of `test_a_guarded_rule_names_its_guard`, which is where it drifted.

    That test asks whether a rule claiming a guard has one. Nothing asked the reverse — whether a
    rule *has* a guard while still claiming none — so the classification could go stale the moment
    someone wrote the test and forgot the field. It did: `reference-data-is-json` sat at
    `guardable` — "a test is possible and nobody has written it" — while
    `tests/test_reference_data_is_json.py` was in the repository and passing, and a CHANGELOG
    entry said the rule was enforced.

    The correspondence is derived, not listed: a rule id maps to `tests/test_<id>.py` with dashes
    as underscores. That is a floor rather than a ceiling — `lxml-for-xml` is guarded by
    `test_lxml_not_elementtree.py` and this cannot see it — but it catches the case where someone
    writes the obvious test and leaves the rule saying nobody has.
    """
    if entry["enforcement"] not in ("guardable", "judgment"):
        return

    repo_root = Path(__file__).resolve().parent.parent
    obvious = repo_root / "tests" / f"test_{entry['id'].replace('-', '_')}.py"

    assert not obvious.is_file(), (
        f"rule `{entry['id']}` is classified `{entry['enforcement']}`, but "
        f"{obvious.relative_to(repo_root)} exists. Either that test holds the rule — in which "
        f"case classify it `guarded` or `partial` and name it in `guard:` — or it does not, in "
        f"which case the test is named after a rule it does not check."
    )


def test_the_engine_does_not_claim_domain_rules():
    """A `language` rule must be about the language, not about one application of it.

    Checked as a fixed list rather than inferred: the rules the engine may enforce for every
    user are a deliberate set, and adding to it is a decision. Twice in one session an AI
    proposed moving a domain rule into `sp lint`; this is the check that would have refused it.

    Membership is the engine claiming a rule for every user of the language, so it is added
    only where the rule states a contract the engine can keep without knowing what the
    pipeline is about.
    """
    language_scoped = {e["id"] for e in ai_rules.entries() if e["scope"] == "language"}
    expected = {
        "pipeline-schema",
        "prompts-in-sync",
        "context-is-the-only-channel",
        "use-the-pipeline-language",
        "model-capabilities",
        "separate-output-from-intermediates",
        # A requested key is always present in a payload the engine emits: an empty collection
        # for asked-and-nothing, `null` for could-not-ask, and absent only where the `include:`
        # request list explains the absence. That is a contract a consumer codes against, so
        # the engine can keep it. Which kind of nothing a `null` stands for stays with the
        # domain, and the rule's own text says so.
        "say-which-kind-of-nothing",
    }
    assert language_scoped == expected, (
        "the set of rules the engine enforces for every user has changed.\n"
        f"  newly claimed by the engine: {sorted(language_scoped - expected)}\n"
        f"  no longer claimed: {sorted(expected - language_scoped)}\n"
        "A rule of this domain belongs to a project, not to the language: `sp` also serves "
        "pipelines that publish, that process scripture without a model, and that are not "
        "about scripture at all. If the change is intended, update this list and say why."
    )
