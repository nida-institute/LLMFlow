# AI Drift Control in Scripture Pipelines

**Status:** Draft — awaiting Captain review
**Source:** `discourse-flow/tmp/sp-ai-drift-writeup.md`

---

## What Is Actually Happening

Every time an AI violates a boundary — touches a file without authorization, edits related files when only one was mentioned, treats a description of a problem as a request to fix it — the instinctive response is to add a rule. The rule documents the incident. It signals that the human noticed and objected. It promises that the behavior won't happen again.

It doesn't work. The next AI session starts fresh. The new rule is one line in a growing list of prohibitions, and the model that reads it is not the model that wrote it. What accumulates over time is not protection — it is noise. A CLAUDE.md that contains fifty rules is harder for an AI to internalize than one that contains five, and the marginal rule added after incident number thirty is the least likely to be the one that sticks.

This pattern has a name: LLM scolding. The rules are written for the human's benefit, not the AI's. They make the situation feel addressed. They don't change behavior.

The purpose of this document is to state the reality clearly — for developers, for translators setting up their own SP projects, and for anyone who will eventually ask "why does the AI keep doing this despite a well-written CLAUDE.md?" — and to describe what actually has teeth.

---

## What Already Works

The Captain is using `/stand-down` every ~45 minutes per project. This resets context, clears accumulated drift, and creates natural session boundaries. Design documents in `project/plans/` are the authorization basis for any file change — an AI that cannot name a design document covering what it is about to do should stop and ask. Together these form the working discipline: sessions are bounded, changes require a named authorization.

This is not broken. The one gap is `~/.sp/`.

---

## The `~/.sp/` Problem

`~/.sp/` is shared global context. Every AI working on every SP project on this machine reads from it. An AI that writes there without authorization doesn't just affect the current project — it silently modifies the context that every other project uses. This already happened once: a convention file was created in `~/.sp/conventions/` without authorization, without design, without any understanding of the cross-project scope.

That incident produced a rule in one project's CLAUDE.md: "do not write to `~/.sp/` without explicit authorization." That rule does not reach any other project. The next AI session in that project may or may not read it. An AI in any other project has never seen it.

A rule is the wrong fix for this. The right fix is that an AI which tries to write to `~/.sp/` gets a `PermissionError`, not a guideline to weigh.

---

## The Rules That Should Just Be Deleted

Before adding any enforcement mechanism, the accumulated scolding should be removed. The `discourse-flow` CLAUDE.md Design Authority section mixes genuine principles with incident responses. The following are incident responses — each one documents a specific violation and states the obvious corrective. All of them reduce to the discipline that already exists: declare scope, name the design document, get explicit sign-off.

- **"An observation is not a request to act."** The AI described a problem and immediately fixed it.
- **"'It needs to be X' is not the same as 'please do X.'"** Added because the previous rule wasn't enough to stop the same behavior.
- **"When the user references a specific file, act on that file — not on related files."** The AI edited a constellation of files when one was mentioned.
- **"Agreement on where a fix goes is not agreement on what the fix is."** The AI treated location approval as full design approval.
- **"Do not write to `~/.sp/` without explicit authorization."** Real concern, wrong location. This belongs in the filesystem, not in one project's context.

The four Design Authority principles that precede these — the user is the designer, docstrings have no authority, existing behavior has no authority, design documents are authoritative — are worth keeping. Those are principles. The scolding beneath them is an incident log.

The same accumulation has likely happened in other project CLAUDE.md files. Worth auditing after this change lands.

---

## Filesystem Permissions: Specification

### What Gets Locked

Three directories in `~/.sp/` are locked after `sp init` writes to them:

- `~/.sp/conventions/` — global AI context read by every project; written only by `sp init`
- `~/.sp/skills/` — global skills read by every project; written only by `sp init`
- `~/.sp/projects/` — project registry; written only by `sp init`

Two directories are explicitly left writable:

- `~/.sp/data/` — downloaded biblical datasets; written by `sp download-data` at any time
- `~/.sp/user-context/` — the Captain's hand-edited machine-level instructions; never written by `sp`

### The Lock Mechanism

Lock: `chmod -R a-w PATH` — removes write permission for owner, group, and others. The directory cannot be written to by any process running as the current user, including AI tool calls.

Unlock: `chmod -R u+w PATH` — restores write permission for the owner only.

`sp init` uses a context manager for each protected path: unlock if locked → write → lock. This guarantees the lock is always restored even if an exception occurs mid-write.

On first install the directories do not yet exist. The sequence is: create directory → write → lock. The context manager handles both cases.

### `sp init --no-examples`

Already implemented. It still calls `install_global_conventions()` and `install_global_skills()`, so the locking applies automatically with no additional handling required.

### The Human Escape Hatch

No new CLI commands. When the Captain wants to manually edit a convention or skill, they run:

```
chmod -R u+w ~/.sp/conventions/
# edit
chmod -R a-w ~/.sp/conventions/
```

The friction is intentional. The permission is a gate for AI tool calls, not for deliberate human action. A Captain who knows to run chmod is a Captain who has decided to make a change — exactly the authorization the system is trying to require.

### Scope: What This Does Not Protect

Filesystem permissions on `~/.sp/` do not protect project files. An AI can still edit `pipelines/`, `prompts/`, `plugins/`, and everything else in the repo. That surface is governed by the design document discipline and the `/stand-down` rhythm, not by filesystem enforcement.

### Single-Machine Feature

This is a per-machine configuration. Another machine's `~/.sp/` may or may not be locked. There is no portability requirement and no attempt to synchronize permission state across machines.

---

## Tests

Tests live in `tests/test_sp_lock.py` (new file). All tests monkeypatch `Path.home()` to `tmp_path` so they never touch the real `~/.sp/`.

**`test_conventions_dir_locked_after_init`**
After `init_project()` completes, `~/.sp/conventions/` and all files inside it have no write permission for the owner. `os.access(path, os.W_OK)` returns False.

**`test_skills_dir_locked_after_init`**
Same assertion for `~/.sp/skills/`.

**`test_projects_dir_locked_after_init`**
Same assertion for `~/.sp/projects/`.

**`test_data_dir_remains_writable`**
If `~/.sp/data/` exists after init, it is still writable. `sp init` must not lock it.

**`test_user_context_dir_remains_writable`**
If `~/.sp/user-context/` exists after init, it is still writable. `sp init` must not lock it.

**`test_init_succeeds_when_already_locked`**
Run `init_project()` twice. The second run must not raise — it must unlock, write, and relock successfully. Assert conventions dir is locked after the second run.

**`test_write_to_locked_conventions_raises`**
After `init_project()`, a direct attempt to write a file into `~/.sp/conventions/` raises `PermissionError`.

---

## Implementation Notes

The context manager belongs in `cli_utils.py` alongside `install_global_conventions()` and `install_global_skills()`. Something like:

```python
@contextmanager
def _sp_dir_writable(path: Path):
    was_locked = not os.access(path, os.W_OK)
    if was_locked:
        _unlock(path)
    try:
        yield
    finally:
        if was_locked or path.exists():
            _lock(path)
```

Where `_lock(path)` and `_unlock(path)` apply `chmod -R a-w` and `chmod -R u+w` respectively using `os.chmod` recursively. Using `os.chmod` rather than shelling out keeps it testable and cross-platform within POSIX.

---

## Recommended Path

1. Delete the scolding rules from `discourse-flow/CLAUDE.md` — separable, low risk, do first.
2. Write the failing tests in `tests/test_sp_lock.py`.
3. Implement the context manager and lock/unlock calls in `cli_utils.py`.
4. Run the full test suite to confirm no regressions in `test_init.py`.
