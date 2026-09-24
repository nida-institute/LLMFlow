"""Helm's manifest must put every AI-context file on one side of the ownership line.

Plan: `human-at-the-helm/project/plans/design-helm-project-layout.md` §6 test 3, ruling R1 —
the AI context splits into `docs/ai-context/helm/` (Helm's, overwritten on every re-install)
and `docs/ai-context/project/` (the project's, never overwritten).

**Written before the manifest changes**, per §7 step 2. It fails against today's manifest,
which puts all seven files loose in `docs/ai-context/` with nothing to tell a reader that
`drift-patterns.md` is replaced on the next install and `rules.md` is theirs for good. It
passes when R1 lands. That ordering is the point: the distinction R1 asks for becomes
something a machine can show to be wrong, instead of a claim in a document.

Lives in this repository rather than in Helm because Helm ships only markdown and has no way
to run tests — the same reason R2 declined to port `tools/update_plans_index.py` to it. It
reads Helm's actual manifest, so it skips where no clone is present, exactly as the live half
of `test_helm_sync.py` does.
"""

from __future__ import annotations

import yaml

from tests.test_helm_sync import NEEDS_CLONE, _helm_root

AI_CONTEXT = "docs/ai-context/"
HELM_HALF = "docs/ai-context/helm/"
PROJECT_HALF = "docs/ai-context/project/"

# The policy each half must carry. This is the whole of R1 stated as data: a file under
# `helm/` is Helm's and gets overwritten; a file under `project/` is the project's and never
# does. A file in the wrong half is a file whose name promises one thing and whose policy
# does another, which is worse than the loose arrangement it replaces.
REQUIRED_POLICY = {
    HELM_HALF: "create-or-replace",
    PROJECT_HALF: "create-only",
}


def _ai_context_entries() -> list[tuple[str, str, str]]:
    """Every manifest entry that writes into `docs/ai-context/`, as (label, target, policy).

    Groups and single files are read the same way — both carry `target` and `policy`, and
    the distinction between them does not matter to the ownership question.
    """
    manifest = yaml.safe_load(
        (_helm_root() / "manifest.yaml").read_text(encoding="utf-8")
    )
    entries = []
    for group in manifest.get("groups") or ():
        entries.append((f"group {group['id']}", group["target"], group["policy"]))
    for entry in manifest.get("files") or ():
        entries.append((entry["source"], entry["target"], entry["policy"]))
    return [e for e in entries if e[1].startswith(AI_CONTEXT)]


@NEEDS_CLONE
def test_every_ai_context_target_is_in_one_half_or_the_other():
    """No file lands loose in `docs/ai-context/` itself.

    This is the test that fails today. Seven targets sit directly in that directory, and a
    reader looking at the result cannot tell which of them Helm will overwrite.
    """
    loose = [
        (label, target)
        for label, target, _ in _ai_context_entries()
        if not target.startswith(HELM_HALF) and not target.startswith(PROJECT_HALF)
    ]
    assert not loose, (
        "these manifest entries write into docs/ai-context/ without saying whose the file "
        f"is — each must go under {HELM_HALF} or {PROJECT_HALF} (R1): "
        + ", ".join(f"{label} -> {target}" for label, target in loose)
    )


@NEEDS_CLONE
def test_each_half_carries_the_policy_its_name_promises():
    """A file under `helm/` is overwritten; a file under `project/` is never touched.

    Kept separate from the test above so the failure says which fault it is. Being in the
    wrong directory and carrying the wrong policy are different mistakes with different
    fixes, and a single combined assertion would report them as one.
    """
    wrong = [
        (label, target, policy, REQUIRED_POLICY[half])
        for label, target, policy in _ai_context_entries()
        for half in (HELM_HALF, PROJECT_HALF)
        if target.startswith(half) and policy != REQUIRED_POLICY[half]
    ]
    assert not wrong, "\n".join(
        f"{label} -> {target} is {policy}, but everything under that directory must be "
        f"{expected} (R1)"
        for label, target, policy, expected in wrong
    )
