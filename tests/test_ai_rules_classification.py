"""Guardrail: every rule declares whether a test can catch it, and who may enforce it.

Two fields, answering two different questions:

- `enforcement` — whether a breach is catchable: guarded, partial, guardable, judgment.
- `scope` — who may do the catching: `language` (the engine, for every user), `project` (a
  repository, over its own files), or `none`.

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

ENFORCEMENT_VALUES = {"guarded", "partial", "guardable", "judgment"}
SCOPE_VALUES = {"language", "project", "none"}


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
