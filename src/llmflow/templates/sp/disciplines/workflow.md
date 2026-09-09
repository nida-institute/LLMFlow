# Workflow Conventions

Rules that hold in every project on this machine, whatever it is written in.

---

## Shell Commands

**Read and edit files with the tools, not the shell.** `Read`, `Edit` and `Write` never require approval; `cat`, `head`, `tail`, `sed -n` and `less` do, and they spend the human's attention on a confirmation that buys nothing. `Read` takes a `file_path` with optional `offset` and `limit`, so reading part of a large file needs no shell plumbing at all.

**Search with whatever the session actually has.** Where `Grep` and `Glob` are present, use them. Where they are not — and they are absent from some installations — `grep` and `find` through bash are correct, not a workaround; there is nothing else, and blocking them would leave a session unable to search at all.

**Issue one command at a time.** A permission rule like `Bash(grep:*)` matches a command that *begins* with `grep`. Chaining with `;` or `&&`, or prefixing with `cd`, matches nothing and prompts the human for every search. Two calls that each run cleanly cost less than one that needs an approval.

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

**Git — no piping.** Never pipe git output (`git log ... | grep ...`, `git status | head ...`). Run the git command alone and filter the result with `Read`, or with `Grep` where the session has it. A pager suppressor (`git log | cat`) is fine — it reads no file.

**Inline code — use a heredoc, not `-c` or `-e`.** Write `hatch run python << 'EOF'` for Python and `node --input-type=module << 'EOF'` for Node. Never `python3 -c "..."` or `node -e "..."` with multiline content — these trigger the approval hook. Use `jq` for JSON queries where possible.

**When the sanctioned tool cannot do the job, ask before doing something else.** The rules above name the tool that normally does a job — the file tools for reading and editing, a heredoc for inline code, a path argument rather than `cd`. Where the named tool genuinely cannot reach, say so and ask for the exception before running anything else: name the operation, why the sanctioned route does not reach it, and what you propose instead. One sentence is enough. Where a legal alternative exists, take it and say nothing — `od -N3 file` reads the first bytes `head -c 3` would.

**A permission prompt is not a request for permission.** It names a command, not a reason. Proceeding and letting the prompt do the asking spends the human's attention on decoding a command instead of judging a case — and that attention is what these rules exist to protect. The alternative is worse than it looks: a standing permission granted to get past one prompt outlives the case it was granted for.

---

## Audit Workflow

**Results require specific evidence.** Provide exact quotes and file locations for every finding — not just pass/fail. The human reads what you cite and decides whether they agree.

**Verdicts belong to the human.** Never write "Approved," "Needs attention," "Requires revision," or any verdict. Leave Overall fields blank or mark `_(reviewer to assess)_`. Audits report facts; the human decides what to do with them.

---

## Design and Code Conventions

**Design comments must reference GH issues.** Any comment explaining why something is done a certain way must cite a GH issue number. Without an issue reference, future sessions cannot tell whether the comment reflects an intentional decision or a stale assumption.

**Checklists state what to do, not what to avoid.** Positive framing only. Every "no X, no Y" exception list is a positive rule that already excludes everything failing it — write the positive rule and delete the list.

---

## Completion Is Claimed With Evidence

**A report of completion is a factual claim.** Making it without having verified it is a false statement, not optimism. The common failure is not deceit — it is finishing three quarters of something, losing track of the rest, and reporting the whole.

**Write the checklist before the work, and tick a box only with its evidence beside it.** Not *done* — *how you know*: a test id, a file and line, a command and its result, a count, a date.

```markdown
- [x] lint rejects the old key — tests/test_key_migration.py::test_the_old_key_is_refused
- [x] downstream callers migrated — 5 sites across 2 repos, all green (2026-09-08)
- [x] docs updated — docs/language.md, docs/architecture.md §3.1
- [ ] changelog entry
```

That turns a claim into something the human checks in one step instead of taking on trust.

**A checklist matters most where no test can reach.** A suite catches an unfinished change to the code it covers. It cannot catch documentation not updated, another repository not migrated, or a reply owed to another project and never sent — and those are exactly the items that get lost, because nothing goes red when they are skipped.

**Report what was actually run.** "These three test files pass" rather than "tests pass"; "the happy path works" rather than "it works". Where part of the work was skipped or deferred, say which part, in the same breath as the part that was done.

## Files the Human Controls

**Never modify `docs/ai-context/` without explicit approval.** These are design documents. Report findings and propose changes in conversation; do not write unilaterally.

**Never create or modify project memory files without explicit approval.** Show proposed content in conversation and wait for approval before writing.

**CLAUDE.md belongs to the human.** Propose additions in conversation — showing exact content — but never write to it without explicit approval.

**Never create or modify a file in a repository belonging to another organisation.** Those trees carry other people's uncommitted work, and a file appearing in one is an act with their name on it. Write the document under the current project and hand over the path, or ask first.
