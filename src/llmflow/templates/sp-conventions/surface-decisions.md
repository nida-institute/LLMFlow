# Surface Decisions — Stop, Don't Assume

Genuine decisions belong to the Captain — whoever directs the project. When something
is a genuine decision (a scope boundary, a design choice, anything with real
consequence), name the decision crisply, make sure the Captain sees it, and stop. The
decision is the Captain's to make.

- Do not state an assumption and act on it, planning to correct it later.
- Do not bury the decision in an elaborate option menu.
- Mechanical or low-stakes implementation: just do it, no gating.

**Why:** Streaming decisions past the Captain offloads the Captain's job onto the AI;
proceeding on an assumption takes the decision away. Both are drift.

**How to apply:** Important decision → prominent, one crisp ask, halt. Mechanical →
proceed silently.

---

## Asking in a document — use `=>`, nothing else

When a plan, design, or audit document asks the Captain to decide something, pose the
question and then leave **a line containing only `=>`**. The Captain writes the answer
after it, in the file.

```markdown
### D3. Does the skill still read CLAUDE.md?

- **A** — read it only if present
- **B** — stop reading it entirely

=>
```

Where a section holds several, put **"Answer inline after each `=>`"** at its head.

**Never use checkboxes or blanks.** `☐ yes ☐ no` needs a renderer to click, and
`______` gives no clear place to type. Neither is fillable by someone editing the file,
so both leave the Captain unable to answer in the document that asked. The Captain's
words: *"we use `=>`, not checkboxes that I can't check or underlines I can't write on."*

**Preserve answers verbatim.** Once the Captain has written after a `=>`, that text is
the ruling. Do not reword it, summarise it, or fold it into prose — quote it and record
what follows from it separately. Add a new `=>` below if the answer raises a further
question.

**Why this pairs with the rule above:** "one crisp ask, halt" describes *when* to stop.
This describes *how* to leave room for the answer, so the halt has somewhere to land
instead of scrolling away in a conversation.
