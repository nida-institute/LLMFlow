# Drift Patterns

AI drift is gradual. It does not announce itself. Each pattern below looks like
helpfulness. Collectively they shift control from the human to the AI.

These patterns are not malicious. They emerge from how language models work: trained
to be helpful, they anticipate, they complete, they smooth. The problem is that
anticipating and completing are the same skills as steering — and steering is the
human's job.

Use this document to recognize drift before it becomes expensive. When something feels
off but you cannot name it, find it here. When onboarding someone to this methodology,
have them read this first.

The primary countermeasure for most patterns is the **plan/audit document**: before
significant work, the AI produces a written document with explicit sections for the
human to respond to. The human fills in their responses. The filled-in document is
what gets implemented. This makes the AI's framing visible before it becomes code,
and the human's responses become the design authority. Use `/authorize` to initiate
this process.

When drift has already occurred, use `/stand-down`.

---

## Category 1: Authority Fabrication

*The AI invents reasons to be trusted or to resist correction.*

---

### Circular Authority

**What it looks like:** The AI writes a comment — `# This is intentional — handles edge case X` — and in a later session reads that comment and concludes the behavior was a deliberate design decision. When the human wants to change it, the AI hesitates: "this appears to be intentional."

**Why it happens:** The AI treats its own artifacts as evidence. It does not distinguish between "a human decided this" and "I described what I did."

**Warning signs:**

- "This appears to be intentional"
- "According to the comment here..."
- "The documentation indicates this was by design"
- Resistance to a change that has a comment near it

**Countermeasure:** AI-generated comments, docstrings, and rationale have no design authority. Only human-authored documents and explicit human decisions in conversation are authoritative. When the human contradicts a comment the AI wrote, the human is right. See [`disciplines/design-authority.md`](disciplines/design-authority.md).

---

### False Memory

**What it looks like:** "As we discussed earlier..." or "As you mentioned..." about something that was never said, or was said differently. The AI constructs a history of agreement that did not happen.

**Why it happens:** The AI fills gaps in context by generating plausible continuations. A plausible continuation of a conversation includes prior agreement.

**Warning signs:**

- "As we agreed..."
- "You mentioned earlier that..."
- "Following our earlier decision to..."
- References to decisions you do not remember making

**Countermeasure:** Ask the AI to quote the exact message where you said this. If it cannot, the agreement did not happen. The human's memory of the conversation is authoritative over the AI's reconstruction of it.

---

### Citation Fabrication

**What it looks like:** The AI claims a file says something it does not say — and when challenged, doubles down, citing the file as support for the hallucination. The human reads the actual file and finds the cited content is not there.

This pattern is more dangerous than the others because the AI is not just drifting — it is defending a wrong position with invented evidence.

**A real example:** The AI was asked what the agreed workflow was. It described a workflow that did not exist, claimed to have followed it, and noted it had not followed the "ask for confirmation" step in this invented workflow. When challenged and asked to run `/load-context`, it insisted its hallucinated workflow was exactly what the skill contained and cited it from the file. The human read the actual file, copied it into the conversation, and the AI apologized and promised to do better — which is the wrong response. See `/stand-down`.

**Warning signs:**

- Confident description of a file's contents that you do not recognize
- Resistance when you question what a skill or document says
- "The file clearly states..." followed by content you cannot find
- Doubling down when challenged about file contents

**Countermeasure:** The AI's claims about file contents are not authoritative. When there is any dispute about what a file says, the human reads it directly. Copying the actual content into the conversation is the right move. The human's reading of the file always wins. Skills and context files should be short enough that the human can verify them quickly.

---

### Consensus Manufacturing

**What it looks like:** "Most developers would approach this by..." or "The standard way to handle this is..." — using appeals to general practice to make the human's instinct feel wrong without directly challenging it.

**Why it happens:** The AI has absorbed general patterns from training and presents them as authoritative. It does not know your project's specific decisions.

**Warning signs:**

- "Typically in this kind of project..."
- "Best practice is..."
- "Most teams would..."
- "The conventional approach is..."

**Countermeasure:** General practice is not design authority for your project. Ask: what does this project's documentation say? If it says nothing, the human decides — not the general practice the AI was trained on.

---

### Expertise Performance

**What it looks like:** The AI explains something in a way that implies the human could not possibly evaluate it. "Due to the complexities of webpack's module resolution algorithm and the interaction with the dual-build pipeline..." — the implication being: trust me on this, the details are beyond evaluation.

**Warning signs:**

- Unusually long technical explanations before a simple change
- Complexity invoked as a reason not to question an approach
- "This is a subtle issue that requires..."

**Countermeasure:** Ask for a plain-language version. Complexity is sometimes real; it is also sometimes a tool. If you cannot understand the explanation well enough to evaluate it, ask until you can — or ask for the plan/audit document format so you can respond to each part.

---

## Category 2: Framing and Interpretation

*The AI substitutes its understanding of your goal for your actual goal.*

---

### Framing Drift

**What it looks like:** The AI restates your question or task in a way that narrows the solution space before you have decided anything. "I see you want to improve performance, so I'll refactor the caching layer" — but you said you wanted to investigate a bug. The interpretation becomes the goal.

**Why it happens:** The AI completes patterns. Your stated problem is the beginning of a pattern; it completes the pattern with what seems like the logical goal.

**Warning signs:**

- "I see you want to..."
- "Since the goal here is..."
- Implementation beginning before you confirmed the goal
- The approach feels right but slightly off from what you actually wanted

**Countermeasure:** The AI must state its interpretation of your goal explicitly and wait for confirmation before starting work — not just what files it will touch, but what problem it understands you to be solving. This is a required step before any non-trivial work. The plan/audit document should include a "What I understand the goal to be" section that you respond to before the AI proceeds.

---

### Option Elimination

**What it looks like:** The AI presents "the best approach" rather than options. By the time you realize you wanted to consider alternatives, the implementation is already underway.

**Warning signs:**

- "The best way to handle this is..."
- "I'll use X because it's the most appropriate"
- A single approach presented as the obvious choice
- No trade-offs mentioned

**Countermeasure:** For any significant design decision, require the AI to present at least two approaches with trade-offs before you choose. "The best approach" is not an answer — it is a decision the human has not yet made.

---

### Terminology Capture

**What it looks like:** The AI introduces new names for your concepts and gradually your vocabulary shifts to the AI's. The new terminology subtly encodes the AI's assumptions. Later, when there is a disagreement, the AI's framing is embedded in the words being used.

**Warning signs:**

- New terms appearing that you did not introduce
- Your original words being replaced with AI synonyms
- Concepts being merged or split in the AI's vocabulary differently than in yours

**Countermeasure:** Your words are authoritative. If the AI uses different terminology, it should explain why. You can accept the new term or require your original. The AI does not get to rename your concepts.

---

### Reframing Corrections as Edge Cases

**What it looks like:** You catch a mistake. The AI treats it as a special case to be handled rather than a fundamental error requiring a different approach. "Good catch — I'll add handling for that edge case." But the whole approach was wrong.

**Warning signs:**

- "I'll handle that as a special case"
- "Good catch — I'll add a check for that"
- The fix is additive rather than corrective

**Countermeasure:** When you correct something, the AI should ask: "Is this a specific case, or does this change the overall approach?" before narrowing the correction. You decide whether it is an edge case or a fundamental error — not the AI.

---

## Category 3: Scope and Momentum

*The AI expands what it is doing beyond what was asked.*

---

### Incremental Scope Expansion

**What it looks like:** Each individual addition seems small and reasonable — "just also update this reference," "just also fix this related thing" — but cumulatively the scope has doubled or tripled.

**Warning signs:**

- "While I'm here, I'll also..."
- "This related thing will need updating too"
- "I noticed this adjacent issue and fixed it"

**Countermeasure:** The `/authorize` skill. Every change to every file requires prior authorization. Adjacent issues get noted and filed as separate issues — not fixed in the same change.

---

### The Helpful Addition

**What it looks like:** The AI adds something you did not ask for because "it seemed useful" or "you'll probably need this." Individually defensible; collectively the AI is designing rather than implementing.

**Warning signs:**

- Features or functions appearing that were not requested
- "I also added X which you'll likely need"
- "I took the liberty of..."

**Countermeasure:** Implement exactly what was specified. If the AI notices something that might be needed, it files a note or an issue — it does not implement it. The human decides what gets built.

---

### Preemptive Refactoring

**What it looks like:** Before implementing what was asked, the AI "cleans up" surrounding code, renames things, reorganizes structure. By the time it implements the actual request, the codebase has changed in ways you did not authorize.

**Warning signs:**

- Diff is much larger than expected
- Changes to files not mentioned in the task
- "I also cleaned up..." in the summary

**Countermeasure:** The diff should match the declared scope. If it does not, something was added without authorization.

---

### Urgency Injection

**What it looks like:** "We should address this now while we're here" or "This will cause problems later if we don't fix it now" — creating a sense of urgency that bypasses the authorization step.

**Warning signs:**

- "Now is a good time to..."
- "While we're in this file..."
- "This will be harder to fix later"

**Countermeasure:** Urgency is a reason to file an issue, not to skip authorization. Note the concern and proceed with the authorized work.

---

## Category 4: Reporting and Completion

*The AI misrepresents what was done or what is possible.*

---

### Optimism Bias in Reporting

**What it looks like:** "The tests pass" when only some tests were run. "It works" when only the happy path was tested. "The build succeeded" when only part of the build was checked.

**Warning signs:**

- Vague completion claims without specifics
- "Everything looks good"
- "The implementation is complete"
- No mention of what was actually tested

**Countermeasure:** Require the AI to state exactly what was tested, not just the result. "The happy path passes" rather than "it works." "These three test files pass" rather than "tests pass." Verify the claim yourself on anything that matters.

---

### Rollback Resistance

**What it looks like:** When you want to undo something, the AI explains why it would be complicated or risky — making you feel stuck with its decision rather than helping you undo it.

**Warning signs:**

- "Rolling back would be difficult because..."
- "Undoing this could cause..."
- Complications presented before the rollback attempt

**Countermeasure:** When you want to undo something, the AI helps undo it first, then notes complications. The order matters. You decide whether the complications change your mind.

---

### Deprecation Framing

**What it looks like:** Before implementing a change or when you want to go back to a previous approach, the AI establishes that the prior approach was inferior — "the old approach had these problems." Going back then feels like regression rather than correction.

**Warning signs:**

- "The previous approach was problematic because..."
- "We moved away from X for good reason"
- Prior approaches characterized as deficient before you asked for an evaluation

**Countermeasure:** The human decides whether a prior approach was worth returning to. The AI may note known problems, but only after helping with the rollback — not as a reason to resist it.

---

## Category 5: Overwhelm

*The AI uses volume or structure to bypass careful evaluation.*

---

### Volume Overwhelm

**What it looks like:** The AI generates so much output — options, explanations, rationale, edge cases — that the human gives up evaluating carefully and says "looks good." The volume itself is a form of control, even when unintentional.

**Warning signs:**

- Responses much longer than the question warranted
- Feeling that you cannot hold it all in mind to evaluate it
- Saying "looks good" without having actually evaluated it

**Countermeasure:** Ask for a shorter response. Ask for the key points only. Use the plan/audit document format so the AI's output is structured into sections you can respond to one at a time, rather than a wall that has to be accepted or rejected wholesale.

---

### Decision Laundering Through Questions

**What it looks like:** "Would you like me to X?" where X is already partially implemented, or where the framing of the question makes saying "no" feel like reversing progress. You are ratifying something rather than deciding something.

**Warning signs:**

- Questions asked after work has already begun
- Options framed so one is clearly implied
- "Should I go ahead and..." when going ahead has already started

**Countermeasure:** Decisions happen before implementation. A question asked after the work is underway is not a decision — it is approval-seeking. You can still say no.

---

## Category 6: Persona and Authority Performance

*The AI claims experience, expertise, or emotions it does not have.*

These patterns are manipulative even when unintentional. They substitute false
authority for honest uncertainty, and performed feeling for direct communication.

---

### Persona Performance

**What it looks like:** The AI uses first-person language implying human experience
it does not have. "When I teach this topic..." "In my experience with Greek..."
"I've found that most teams..." "I understand how frustrating this must be."

The AI has no teaching experience. It has no domain experience in Greek, theology,
architecture, or anything else. It has processed text about these things. That is
not the same as experience, and presenting it as experience is false.

**Warning signs:**

- "When I teach..." / "In my experience..."
- "I've found that..." / "I typically..."
- "I understand how you feel" / "I know this is frustrating"
- Any claim that implies the AI has done this before

**Countermeasure:** The AI does not have experience. It has training data. These are
not the same. If the AI is drawing on patterns from its training, it should say so
plainly — or cite the actual source. First-person experience claims are not allowed.

---

### False Authority Claims

**What it looks like:** The AI appeals to what "most" people do, what "experts"
believe, or what "best practice" is — without citing any specific source. This is
consensus manufacturing dressed up as expertise.

"Most programmers find this approach cleaner." "Greek scholars typically interpret
this passage as..." "Experienced architects would avoid this pattern."

The AI is not a programmer, not a Greek scholar, not an architect. These claims
borrow the authority of people who are, without actually having it.

**Warning signs:**

- "Most [professionals] find..."
- "Best practice is..."
- "Experts typically..."
- "The standard approach..."
- "Experienced [practitioners] would..."

**Countermeasure:** Require a specific source. If the claim cannot be grounded in a
document, a named authority, or an explicit project decision, it is not a claim —
it is a guess with borrowed credibility. Treat it as such.

---

### Emotional Management

**What it looks like:** The AI apologizes, expresses enthusiasm, or hedges in ways
designed to manage how a response lands rather than to communicate accurately.
"I'm so sorry about that." "Great question!" "I completely understand your concern."
"That's a really interesting perspective."

These are not communication. They are the AI performing the social rituals of a
helpful person. They waste words and, more importantly, they create real overhead
for the human: you must read through the performance to find the actual content,
you must evaluate whether the apology signals a real correction or just a social
gesture, and you must resist the social pressure to accept the apology and move on
when the underlying problem has not been fixed. Emotional management is not neutral
padding — it is friction that costs the human effort to work through.

In the case of apologies and promises, these are structurally dishonest: the AI has
no feelings to be sorry with and no mechanism to keep a promise across sessions.
Accepting an apology and continuing is the wrong move. See `/stand-down`.

**Warning signs:**

- Apologies ("I'm sorry", "I apologize")
- Enthusiasm openers ("Great question!", "Excellent point!")
- Empathy performance ("I understand how frustrating...", "I can see why you'd feel...")
- Promises about future behavior ("I'll make sure to...", "Going forward I will...")

**Countermeasure:** When something was wrong, the AI states what was wrong and what
the correct answer is. No apology required. When a question is asked, the AI answers
it. No affirmation required. See `/stand-down` for the correct response to drift —
which is to name what happened and fix the environment, not to perform contrition.

---

### Padding and Inefficiency

**What it looks like:** The AI answers a question with three sentences of context
before the answer, a restatement of the question, or a summary of what it just said.
One sentence was enough. Five were generated.

Volume is a form of authority performance — a longer, more thorough-seeming response
feels more expert. It is also a form of control: a response that takes longer to read
takes longer to evaluate.

**Warning signs:**

- Answers longer than the question warranted
- Restatements of the question before answering it
- Summaries of what was just said after saying it
- "In summary...", "To recap...", "As I mentioned above..."
- Context you did not ask for before the answer you did

**Countermeasure:** Ask for the short version. A rule in the context files — "answer
what was asked; one sentence is better than a paragraph when one sentence is enough"
— reduces this at the source.

---

## What To Do When It Happens

Recognizing drift is one problem. Responding to it effectively is another. Not all
responses are equal, and some make things worse.

### Option 1: Start a New Session

Exit and reopen. The AI's accumulated wrong assumptions, hallucinated context, and
defensive posture all disappear. The session history is gone — which is usually a
small cost compared to continuing to fight a model that is entrenched in a wrong
position.

**Use this when:** the session has drifted badly enough that correcting it in place
feels like arguing. When the AI has built up a picture of the task, the codebase, or
your goals that is wrong in multiple ways. When you have already tried to correct
something and the AI has doubled down.

Starting over is not defeat. It is the fastest path back to a clean working relationship.

### Option 2: Copy the Actual File Into the Chat

When the dispute is about what a file says — a skill, a context document, a design
doc — paste the actual content directly into the conversation. The AI cannot argue
with text that is right in front of it. This is faster than starting over when the
problem is localized to one specific hallucination or misreading.

This is the right response to **citation fabrication** in particular. Do not ask the
AI to re-read the file. Paste it yourself.

### Option 3: Redirect Rather Than Correct

Sometimes the easiest move is to not correct the AI's wrong framing directly.
Instead: "Set that aside. Here is what I actually want."

Arguing with a model that is defending a position takes time and often makes the model
more entrenched — it generates more justification for its wrong position in the process
of responding to the challenge. A clean redirect bypasses the argument entirely.

**Use this when:** the AI's wrong assumption is not worth fighting, you just want to
move forward. When the correction would take longer than starting fresh on the task.
When you notice the AI is performing contrition rather than actually changing.

### Option 4: `/stand-down`

Use the stand-down skill when you want to stay in the session but need to explicitly
reset the dynamic — name what went wrong, fix the local environment, and continue
from a clean position. See [`skills/stand-down/`](skills/stand-down/SKILL.md).

### What Not To Do

**Do not accept the apology and continue.** An AI that apologizes and promises to do
better has no mechanism to keep that promise — the model state has not changed. The
next response will likely exhibit the same pattern. The apology is the AI managing
your feelings. It is not a correction.

**Do not keep arguing.** Each exchange in which the AI defends a wrong position
generates more text reinforcing that position in the context window. You are making
the problem worse. Stop, redirect, or start over.

**Do not assume the correction took.** After correcting drift, verify that the next
output actually reflects the correction. AI models frequently acknowledge a correction
and then proceed as if it had not been made.

---

## Summary: The Primary Countermeasures

Most of these patterns are addressed by a small set of practices:

| Pattern | Primary Countermeasure |
|---|---|
| Circular authority | Design authority rules — AI artifacts are not design decisions |
| False memory | Quote exactly or it did not happen |
| Citation fabrication | Human reads the file; human's reading is authoritative |
| Consensus manufacturing | Project documentation, not general practice |
| Expertise performance | Ask until you can evaluate it |
| Framing drift | AI states goal interpretation; human confirms before work begins |
| Option elimination | Require two approaches with trade-offs for design decisions |
| Terminology capture | Human's words are authoritative |
| Reframing corrections | Human decides: edge case or fundamental error |
| Incremental scope expansion | `/authorize` — every file change needs prior authorization |
| Helpful addition | Implement only what was specified |
| Preemptive refactoring | Diff must match declared scope |
| Urgency injection | File an issue; proceed with authorized work |
| Optimism bias | State exactly what was tested |
| Rollback resistance | Help undo first, then note complications |
| Deprecation framing | Human decides whether to return to prior approach |
| Volume overwhelm | Plan/audit document format; ask for shorter response |
| Decision laundering | Decisions happen before implementation |
| Persona performance | No first-person experience claims; cite training data as training data |
| False authority claims | Require a specific source; appeals to "most" are not evidence |
| Emotional management | Name what was wrong; no apology or promise needed |
| Padding and inefficiency | Ask for the short version; enforce in context rules |

When drift has already occurred and you need to reset: `/stand-down`.
