# Workflow Conventions

Rules that hold in every project on this machine, whatever it is written in.

---

## Shell Commands

**Prefer tools over bash.** The Read, Edit, Write, and Grep tools never require approval. Use them for file reads, edits, and searches before reaching for bash.

**Never use `cd /path && command`.** Most tools accept a path directly — use that instead. `cd` before a command triggers approval hooks and is almost never necessary:

- `git -C /path/to/repo <command>` — not `cd /path && git`
- `grep -r pattern /path/` — not `cd /path && grep -r pattern .`
- `find /path/ -name ...` — not `cd /path && find . -name ...`
- `pytest /path/tests/` — not `cd /path && pytest`
- `npm test --prefix /path/` — not `cd /path && npm test`
- `ruff check /path/src/` — not `cd /path && ruff`
- `npx tsc -p /path/tsconfig.json` — not `cd /path && npx tsc`
- `ls /path/` — not `cd /path && ls`

If a tool genuinely has no path argument, use a subshell: `(cd /path && command)` — this does not change the shell's working directory and does not trigger the hook.

**Git — no piping.** Never pipe git output (`git log ... | grep ...`, `git status | head ...`). Run the git command alone; use the Grep tool or Read tool to filter results.

**Inline code — use a heredoc, not `-c` or `-e`.** Write `hatch run python << 'EOF'` for Python and `node --input-type=module << 'EOF'` for Node. Never `python3 -c "..."` or `node -e "..."` with multiline content — these trigger the approval hook. Use `jq` for JSON queries where possible.

---

## Audit Workflow

**Results require specific evidence.** Provide exact quotes and file locations for every finding — not just pass/fail. The human reads what you cite and decides whether they agree.

**Verdicts belong to the human.** Never write "Approved," "Needs attention," "Requires revision," or any verdict. Leave Overall fields blank or mark `_(reviewer to assess)_`. Audits report facts; the human decides what to do with them.

---

## Design and Code Conventions

**Design comments must reference GH issues.** Any comment explaining why something is done a certain way must cite a GH issue number. Without an issue reference, future sessions cannot tell whether the comment reflects an intentional decision or a stale assumption.

**Checklists state what to do, not what to avoid.** Positive framing only. Every "no X, no Y" exception list is a positive rule that already excludes everything failing it — write the positive rule and delete the list.

---

## Files the Human Controls

**Never modify `docs/ai-context/` without explicit approval.** These are design documents. Report findings and propose changes in conversation; do not write unilaterally.

**Never create or modify project memory files without explicit approval.** Show proposed content in conversation and wait for approval before writing.

**CLAUDE.md belongs to the human.** Propose additions in conversation — showing exact content — but never write to it without explicit approval.

**Never create or modify a file in a repository belonging to another organisation.** Those trees carry other people's uncommitted work, and a file appearing in one is an act with their name on it. Write the document under the current project and hand over the path, or ask first.
