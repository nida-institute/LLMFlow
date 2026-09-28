# Scripture Pipelines Project Tutorial

This repository was initialized with `sp init`. It includes a working example that writes
passage commentary for small-group leaders and preachers — and that shows, on a real task,
what the engine is actually for.

**Four steps, and three of them call no model.** That ratio is the point: the engine spends
its effort fetching the right text, in the right numbering, with the right analyses, so that
the one step which does call a model has something to work from.

## 1. Project layout

After running `sp init` in an empty directory, you should see:

```
./
├── outputs/
├── pipelines/
│   └── commentary.yaml
└── prompts/
    └── commentary.gpt
```

Pipelines live under `pipelines/`, prompt templates under `prompts/`, and generated content
is written into `outputs/`.

## 2. Running it

The example takes the passage as a variable and supplies **no default**, because choosing the
passage is the first thing you need to know how to do:

```bash
sp run --pipeline pipelines/commentary.yaml --var passage="MRK 1:1-8"
```

Before spending anything, check it:

```bash
sp lint --pipeline pipelines/commentary.yaml
sp run --pipeline pipelines/commentary.yaml --var passage="MRK 1:1-8" --dry-run
```

`--dry-run` resolves every path and variable and calls no model.

## 3. What each step does

Open `pipelines/commentary.yaml`. Each step carries a `description:` explaining itself; this
is the short version.

**`subject`** fetches the Greek from `SBLGNT` with word ids and discourse features. Note two
things. The resource is **named**, never given as a path — the engine resolves where it lives,
so the same pipeline runs on someone else's machine. And its output names two **members**:

```yaml
output: [subject=text, passage_info=reference]
```

`text` is the passage. `reference` is what the engine parsed out of your reference on its way
to fetching it — book code, testament, and the `filename_prefix` that the later steps name
their output files with. Nothing has to parse the reference a second time.

An entry may be written `variable=member` to rename it, as both are here. Which members a step
type offers is declared by the step type; `sp lint` refuses one that does not exist.

**`english`** fetches the same verses from `BSB`, for the commentary to quote.

```yaml
versification: org
```

That line is the whole reason this step is worth reading. It states which numbering **your
reference** is written in — the Greek is numbered `org` — so the engine maps the reference
before reading the English, and the two line up verse for verse. Leave it out and it defaults
to `eng`. In Mark the two agree; elsewhere they do not, and the run reports success either way.
This is the habit taught on a passage where getting it wrong is invisible.

**`parallels`** asks which groups in the UBS Parallel Passages database this passage belongs
to — synoptic parallels, and Old Testament passages quoted in the New. An empty list means the
database was consulted and found none. That is an answer, not a failure.

**`commentary`** is the only step that calls a model. Everything it is asked about is handed to
it as a named input. It is not asked what it knows about the passage.

## 4. What you get

```
outputs/
├── 41001001-41001008-english.txt
├── 41001001-41001008-parallels.json
└── 41001001-41001008-commentary.md
```

The filenames come from `passage_info.filename_prefix`, so a second passage does not overwrite
the first.

## 5. Next steps

- **Change the passage.** `--var passage="MRK 1:6"` narrows everything, parallels included.
- **Read `prompts/commentary.gpt`.** It is organised in the section order this project's
  prompts follow, and it is worth reading as a model for your own.
- **Add a step.** Anything that takes the commentary and does something else with it — a
  summary, a different audience, a translation — is another `type: llm` step reading
  `${commentary}`.
- **Check your own pipelines** with `sp lint` before running them. It catches an undeclared
  variable, a member a step type does not offer, and a prompt that does not match its contract.
