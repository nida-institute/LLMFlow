# Scripture Pipelines Project Tutorial

This repository was initialized with `sp init`. It includes a working example that writes a
reader's guide to a passage in Greek or Hebrew — its less common words, the force of each
infinitive and participle, how its verbs relate — and then explains what the passage's parallel
passages mean in their original context and how this passage uses them.

**Two steps call a model, and every other step is free.** That ratio is the point: the engine
spends its effort fetching the right text, in the right numbering, with the right analyses, so
that the steps which call a model have something to work from.

## 1. Project layout

After running `sp init` in an empty directory, you should see:

```
./
├── outputs/
├── pipelines/
│   └── readers-guide.yaml
└── prompts/
    ├── readers-guide.gpt
    └── parallel-significance.gpt
```

Pipelines live under `pipelines/` and prompt templates under `prompts/`. A run writes its
deliverables into `outputs/` and everything it produced on the way into `intermediate/`.

## 2. Before the first run

The example reads three registered resources — `SBLGNT`, `WLC` and `BSB` — and, for syntax, the
Macula Lowfat trees registered on them. `sp resource list` shows what this machine has. The UBS
Parallel Passages database and the word-frequency tables ship with the engine, so they need
nothing installed.

## 3. Running it

The example takes the passage as a variable and supplies **no default**, because choosing the
passage is the first thing you need to know how to do:

```bash
sp run --pipeline pipelines/readers-guide.yaml --var passage="MAT 19:1-11"
```

Before spending anything, check it:

```bash
sp lint --pipeline pipelines/readers-guide.yaml
sp run --pipeline pipelines/readers-guide.yaml --var passage="MAT 19:1-11" --dry-run
```

`--dry-run` resolves every path and variable and calls no model.

Two variables set how much help the guide gives, as a percentage of each corpus's lemmas: a word
is explained when its lemma falls among the least frequent N%. Set them for your own reading:

```bash
sp run --pipeline pipelines/readers-guide.yaml --var passage="MAT 19:1-11" \
  --var greek_frequency_cutoff=60 --var hebrew_frequency_cutoff=95
```

## 4. What each step does

Open `pipelines/readers-guide.yaml`. Each step carries a `description:` explaining itself; this
is the short version.

**`english`** fetches the passage from `BSB`. Its output names two **members**:

```yaml
output: [english=text, passage_info=reference]
```

`text` is the passage. `reference` is what the engine parsed out of your reference on its way
to fetching it — book code, testament, and the `filename_prefix` that later steps name their
files with. Nothing has to parse the reference a second time. An entry may be written
`variable=member` to rename it, as both are here; which members a step type offers is declared
by the step type, and `sp lint` refuses one that does not exist.

**`greek`** or **`hebrew`** fetches the passage in its own language. Exactly one runs:

```yaml
condition: "${passage_info.testament == 'NT'}"
```

The resource is **named**, never given as a path, so the same pipeline runs on someone else's
machine. And `include:` asks for analyses beside the text:

```yaml
include: [ids, morphology, senses, glosses, syntax, frequency]
```

`syntax` brings the whole sentence each word stands in, so a participle near the edge of the
passage arrives with the verb it depends on. `frequency` gives each word its lemma's count in
the Greek New Testament or the Hebrew Bible.

**`reader_guide`** is the first step that calls a model. Everything it is asked about is handed
to it as a named input; it is not asked what it knows about the passage.

**`parallels`** asks which groups in the UBS Parallel Passages database this passage belongs
to. **`parallel_members`** and **`parallel_chapters`** then fetch the chapter around every member
— once per chapter, using `for-each` with `group_by` — so each parallel can be read in its own
context. **`significance`** is the second model step.

## 5. What you get

```
outputs/
├── 40019001-40019011-readers-guide.md
└── 40019001-40019011-parallel-significance.md
intermediate/
└── 40019001-40019011/
    ├── english.txt
    ├── greek.json
    ├── parallels.json
    └── parallels/
```

The filenames come from `passage_info.filename_prefix`, so a second passage does not overwrite
the first. Commit `outputs/`; `intermediate/` is there to be read, and a re-run clears only its
own.

## 6. Next steps

- **Change the passage.** An Old Testament reference runs the Hebrew branch.
- **Read the prompts.** Both are organised in the section order this project's prompts follow,
  and are worth reading as models for your own.
- **Add a step.** Anything that takes the guide and does something else with it — a summary, a
  different audience — is another `type: llm` step reading `${reader_guide}`.
- **Check your own pipelines** with `sp lint` before running them. It catches an undeclared
  variable, a member a step type does not offer, and a prompt that does not match its contract.
