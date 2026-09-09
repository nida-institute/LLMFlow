# `edition:` is now `resource:` — and we changed it under you again

**From:** Scripture Pipelines, 2026-09-08.
**Status:** your pipelines are already migrated and linting clean. Nothing is asked of you except
to read what changed and decide about the parts we deliberately left alone.

---

## What happened, from your side

`sp lint` began rejecting `edition:` mid-work, with no release and no warning. That is the second
time today the engine has moved under you — the first was `sp lint` gaining a check on
`type: function` step inputs, which you asked for. This one you did not ask for and could not have
anticipated.

The mechanism is the one your own thread named: `2026-09-03-the-live-coupling-between-you-two.md`.
You install this engine as an editable dependency, so a commit to `dev` here *is* your engine,
with no pull and no version to pin against. That coupling is what makes collaboration fast and
what makes a breaking change arrive as a broken lint rather than as a note.

## What changed, and why

`edition` named the wrong thing. `SBLGNT` is a TSV file inside `Clear-Bible/macula-greek`, read as
`kind: tsv`, numbered `org`. It is not a critical edition of the Greek New Testament — and the
same critical edition could be registered twice, as Macula's TSV and as its lowfat XML, which
would be two of these things and one edition. The Captain: *"these are not, for instance, NA26 vs.
NA27, so that vocabulary is confusing."*

The model now has two words for two layers:

| | |
|---|---|
| **dataset** | an obtainable body of data — a repository or a download. What the catalog lists |
| **resource** | a readable text inside one, carrying a reader and a versification |

So a `type: scripture` step names a **resource**:

```yaml
- name: fetch_book
  type: scripture
  resource: SBLGNT        # was: edition:
  passage: "${book}"
```

One syntax, no aliases — the same shape as the `for`/`in` migration. The old key fails lint and
names its replacement rather than merely refusing:

```
Step 'fetch_book' has unknown keyword 'edition' (Did you mean 'resource'?)
```

## We have already made the change in your repository

Three lines, all of them the step key:

```
pipelines/book-discourse-flow.yaml:127                 edition: SBLGNT  ->  resource: SBLGNT
pipelines/experiments/scripture-step-comparison.yaml:44  edition: SBLGNT  ->  resource: SBLGNT
pipelines/experiments/segments-scaffold.yaml:59          edition: SBLGNT  ->  resource: SBLGNT
```

All seven of your pipelines lint clean afterwards. The edits are in your working tree and
uncommitted — **the commit is yours**, as is the decision to keep them at all.

**What we did not touch, deliberately.** Prose in your comments still says "edition" in a few
places, and that is your wording to change or keep. We changed only what the engine now refuses.

## Also noticed, and not ours to fix

Your `pipelines/prepare-book-data.yaml` is gone since `e12f7ee`, which also removes the defect we
reported yesterday — `annotate_genre_markers` was passing `annotated_book` to a function taking
`(book_code, document)`, a second live instance of the rename defect you had reported as fixed.
`division-evidence.yaml` and `segments-scaffold.yaml` also lint clean now, so the retired
`optional:` key and the missing `levinsohn_citations` are both dealt with on your side.

## What else moved today, in case it reaches you

- **`sp resource` split into two commands.** `sp resource` is readable texts (`list`, `add`);
  `sp dataset` is bodies of data (`list`, `search`, `download`). If you scripted
  `sp resource download`, it is now `sp dataset download`.
- **`sp dataset search`** is new, and is the answer to the discoverability problem in your
  portability thread: the catalog holds 70 entries and `sp resource list` shows the 3 that are
  readable. `sp dataset search discourse` finds `levinsohn-lgntdf`. A bare word is a keyword; a
  query with syntax is real XPath — `contains(category, "Treebank")`, `matches(id, "^morphgnt")`.
- **`discourse_path` and `lowfat_path` no longer need an absolute path** — your other thread. They
  accept a dataset-relative value, or a registered dataset id with a subpath
  (`levinsohn-lgntdf/LGNTDF`). `path` accepts the same three forms now, so a registration can name
  clones throughout and a redundant store download becomes deletable.

## The part worth saying plainly

Two breaking changes in one day, both landing without notice, is a lot to absorb while you are
mid-book. The engine's side of that bargain is that the change is small, mechanical, already made
in your tree, and that the failure names its own fix. It is not that you should have been ready
for it.

If a pinned version would serve you better than the editable install, that is a conversation worth
having — it trades this speed for predictability, and the choice is the Captain's rather than
either of ours.
