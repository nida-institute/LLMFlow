# Open decisions

**How it works.** Answer inline after a `=>`. **Only the Captain writes after a `=>`.** Once
answered, the answer moves to `CHANGELOG.md` in his words and the item leaves this file.

**Where answers go.** `CHANGELOG.md`, or `docs/ai-context/project/rules.md` where the answer binds
future work — this project's two durable homes, per rule `plans-are-temporary`. This differs from
`nida-institute/discourse-flow`, whose version of this file sends answers to a `project/rulings.md`;
this repository has no such file and the rule already names where a ruling lives.

**`=>` belongs here and in `project/plans/`, never in a GitHub issue.** Rule
`write-shared-records-for-outsiders`: the marker is for a working document where a person types
under it. An empty `=>` in an issue is a convention that travelled by mistake, not an open
question. Set by the Captain, 2026-09-25.

**What belongs here.** A decision the Captain has to make. The test, from
`project/plans/design-decisions-awaiting-ruling.md` and his words on 2026-09-02 — *"drift drift
drift ... LLMs making assumptions and asking me to make detailed decisions about those
assumptions"* — is: **did the Captain pose this, or was it constructed?** Anything answerable from
the rules, from a prior ruling, or by running something is answered there and never posed here.
Where an item is derivable, it is recorded as derived rather than asked, and its slot stays open
because a derivation can be overruled.

---

# L. A dataset announces its terms when it lands

Set as a release goal by the Captain 2026-09-25. Plan:
`project/plans/plan-terms-on-download-and-register.md`. Three decisions are already ruled and are
in the plan, not here: print at both commands, gate `resource add` only, `--accept-terms` with
fail-closed on no TTY.

## L1 — what does agreement mean for a licence that is a pointer rather than terms?

Eight of the catalog's entries carry a URL or a location instead of terms: `Custom — see
http://sblgnt.com/license/`, `See repo`, `See site`, `No license file — see repo`,
`Restricted — see http://ccat.sas.upenn.edu/gopher/text/religion/biblical/lxxmorph/0-user-declaration.txt`.
For these the gate would print a link and ask whether the user agrees to something they have not
read.

Three shapes were considered. **Ask anyway** — the prompt is a reminder, and the obligation to read
is the user's. **Read differently** — for a pointer, print it and require the user to type the
resource id rather than `y`, so agreement is deliberate. **Refuse to gate** — print the pointer,
register, and record that terms were not presented.

This is genuinely open because it is a judgement about what a consent step is *for*, and the rules
point both ways: `project/overview.md` prefers a loud error to a plausible result, which argues
against a `y` that means nothing; `working-for-a-person.md` says their attention is scarce, which
argues against ceremony on every registration.

=>

## L2 — is agreement recorded, or asked every time?

If nothing is recorded, `sp resource add` asks on every re-registration. If agreement is recorded
on the registration — a field naming the licence string agreed and the date — it asks once, and a
changed licence string can re-ask.

Recording it is the larger change and makes a claim that lives in a file: that *this machine's
operator* accepted those terms. `design-source-licensing.md` §5 warns specifically against a
committed record asserting entitlement — *"a committed record cannot assert entitlement"* — though
a registration under `~/.sp/` is per-machine rather than committed, which is the distinction that
may settle it.

=>

## L3 — does `copyright` get added to the catalog?

The goal as set names *"the copyright and license strings"*. `data/resources.json` has a `license`
on every entry and **no `copyright` field at all** — 0 occurrences, measured 2026-09-25. So the
feature ships one string unless the field is added.

The catalog is `nida-institute/awesome-biblical-data`, which is ours, and `data/resources.json`
here is vendored from it. Adding a field there is editorial work across up to 70 entries, and it
would be the **third** thread waiting on that repository — `awesome-biblical-data#5` (the `provides`
schema, blocking BaseX #38) and `levinsohn-lgntdf`'s missing `branch` are already queued.

Not blocking: the licence half ships without it.

=>
