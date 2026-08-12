# Working with AI Assistants on Scripture Pipelines Repos

This guide explains how to work on a Scripture Pipelines (LLMFlow) repository — the
engine, or a consumer repo like `discourse-flow` — using an AI coding assistant, in
whatever environment suits you: terminal, a point-and-click editor, or the browser
(no command line required).

## The one idea: `AGENTS.md`

Every Scripture Pipelines repo carries an **`AGENTS.md`** at its root. This is an open,
cross-tool standard (originated by OpenAI's Codex, now stewarded by the Linux
Foundation) that most AI coding tools read automatically. It holds the project's
orientation and rules; it points to `docs/ai-context/` for detail.

- **`AGENTS.md`** — the shared source of truth. Read by Codex, Gemini CLI, Cursor,
  VS Code + Copilot, Windsurf, Zed, and many others.
- **`CLAUDE.md`** — Claude Code reads this one, not `AGENTS.md`. In these repos it is a
  one-line `@AGENTS.md` import plus Claude-only slash-command skills, so Claude Code
  ends up with the same instructions as everyone else.
- **`docs/ai-context/`** — the deeper reference `AGENTS.md` points to. Two lanes: sp-managed
  files (`index.md`, `overview.md`, `rules.md`, `github-workflow.md`), refreshed by
  `sp init --update`, and **`project.md`** — this repo's own context, which `sp` never
  overwrites. Put project-specific facts there; see `docs/consumer-repo-layout.md`.

**Precondition — the tool must have the repo open.** These files only help a tool that
has the project's folder loaded (or a connected GitHub repo). A plain chat window with
no repo loaded cannot see them.

## Pick your environment

### Terminal (command-line) agents

| Tool | Reads | Notes |
|---|---|---|
| **Claude Code** (Anthropic) | `CLAUDE.md` → `AGENTS.md` | Adds `/`-command skills (`/load-context`, `/audit-*`, `/commit-ready`, `/stand-down`). |
| **Codex CLI** (OpenAI) | `AGENTS.md` | Reads it natively. |
| **Gemini CLI** (Google) | `AGENTS.md` | Reads it natively (also reads `GEMINI.md`). |

Launch the agent from inside the repo directory. It picks up `AGENTS.md` at start.

### GUI editors — point-and-click, no terminal

**Cursor**, **VS Code + GitHub Copilot**, **Windsurf**, and **Zed** all read `AGENTS.md`.
Use **`File → Open Folder…`** and select the repo — that's it, no commands. The built-in
assistant is then oriented automatically.

### Browser / cloud agents — nothing installed locally

**OpenAI Codex in ChatGPT** and **Google Jules** connect a GitHub repo in the browser,
load the files server-side, read `AGENTS.md`, and work — no install, no terminal.

### Not repo-aware

The plain **ChatGPT**, **Claude**, and **Gemini** chat windows do **not** load a repo,
so they never see `AGENTS.md`. Either paste the relevant files in yourself, or use one
of the repo-aware tools above.

## No command line? Two GUI paths

1. **Local, in an editor:** install **GitHub Desktop** (a point-and-click app), use it to
   clone the repo, then open that folder in **Cursor** or **VS Code**.
2. **Fully in the browser:** use a cloud agent (**Codex in ChatGPT**, **Jules**) and
   connect the GitHub repo — no files on your machine at all.

## Universal vs Claude-only

- **Universal** (in `AGENTS.md`, every tool gets it): project orientation, the hard rules
  and prohibitions, build/test/run commands.
- **Claude Code only**: the slash-command **skills** (`/load-context`, `/audit-prompts`,
  `/commit-ready`, `/stand-down`, …). These are a Claude Code feature. Other tools have
  their own custom-command mechanisms; the underlying **procedures** live in
  vendor-neutral docs (e.g. `docs/audits/`) that any tool can read.

## Running pipelines

Whatever assistant you use for editing, pipelines themselves run through the `sp` CLI
(`sp run --pipeline …`). If your assistant has terminal access it can run them for you;
otherwise run them yourself in a terminal. See [getting-started.md](getting-started.md).

## Session continuity — handing off between sessions

An AI assistant forgets everything when a session ends. Two habits keep long-running,
multi-session work coherent:

- **Orient at the start.** In Claude Code, run `/load-context`; other tools read
  `AGENTS.md` automatically — point them at `docs/ai-context/index.md` and
  `project/TODO.md` as well.
- **Exit cleanly when a task is done** (`/exit` in Claude Code) rather than letting one
  session sprawl across unrelated tasks — a fresh session keeps focus sharp for both you
  and the assistant.
- **Write a `HANDOFF.md` before exiting when there's significant in-flight context.** In
  Claude Code, run **`/handoff`** — it writes `project/HANDOFF.md` (active threads, what's
  in flight, open decisions, established facts, key files/issues). In other tools, ask the
  assistant to write the same file. The next session reads `HANDOFF.md` and
  `project/TODO.md` first.

`project/TODO.md` and `HANDOFF.md` matter more than chat history — they survive across
sessions and across tools.

---

_The tool lists above are current as of 2026 and this space moves fast — check a tool's
own docs before relying on a specific behavior. The durable rule: put project
instructions in `AGENTS.md`, and every repo-aware assistant will read them._
