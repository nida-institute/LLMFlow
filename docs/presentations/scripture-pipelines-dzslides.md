---
title: Scripture Pipelines
subtitle: AI tools for biblical scholarship
author: "Jonathan Robie · R&D Fellow, Biblica · jonathan.robie@biblica.com"
---

# The Problem

## The Resource Gap

- Too few high-quality biblical resources in most languages
- The need far exceeds what experts can produce
- Western resources often aren't the right fit

## Lost in Translation

- Western systematic theology
- Abstract, academic, inaccessible
- Emotional exegesis, oral cultures, storytelling cultures
- Giving adults resources designed for children

## The Resource Gap

- Study Bibles
- Bible dictionaries and commentaries
- Bible engagement resources
  - Group study guides
  - Individual study guides
- Training materials for pastors, church leaders, and teachers

## The Resource Gap

- Reader's guides to the Hebrew Old Testament and Greek New Testament
- Accessible Greek and Hebrew lexicons
- Grammars and discourse analyses

## A Wealth of Biblical Data

| Category | Key datasets |
|---|---|
| Source texts | Greek NT, Hebrew Bible, LXX — multiple editions |
| Morphology & syntax | Macula Hebrew/Greek, treebanks |
| Discourse analysis | Levinsohn LGNTDF |
| Lexicons & dictionaries | Abbott-Smith, LSJ, Mounce, Tyndale Bible Dictionary |
| Semantic & entity data | UBS semantic domains, ACAI |
| Geography | Pleiades, UBS Bible Routes, Biblica Open Maps |
| Historical context | Papyri, inscriptions, Josephus, Philo, patristics |
| Jewish texts | Sefaria: Talmud, Midrash, Targums, commentaries |
| Your own data | Paratext projects — drafts, back translations, notes |

## A Wealth of Biblical Resources?

- Hebrew Reader's Guide
- Discourse Flow
- Discourse Flow Review Tool
- Narrative and Cultural Commentary
- Exegetical Frameworks for Multiple Audiences

# AI — Promise and Risk

## What AI Does Well

- Summarizes multiple large datasets (imperfectly!)
- Quick first drafts
  - For brainstorming
  - Initial versions of resources
- Rapid prototyping of new resource types
- Extracts data from a wide variety of files
- Vibe coding — writes pipeline code

## Where AI Falls Short

- **Hallucinates** — plausible errors, hard to catch
- **Drifts** — pursues its own goals
- **No self-evaluation** — confident ≠ accurate
- Always confident. Always plausible. Sometimes true.

## Expertise — It Still Matters

- The data is irreplaceable
  - Decades of annotation by domain experts
  - AI reasons from this data; it cannot replace it
- Experts can get it right when AI cannot
  - LLMs go off in dead ends with these datasets
  - They don't understand the data; experts do
- The goal: datasets that AI and people can trust
  - Not AI-generated slop
  - Grounded, verified, scholar-reviewed

## Building Communities of Knowledge

- Knowledge is tested in community
  - Peer review, mentoring, challenge
  - Test everything; hold on to what is good (1 Thess 5:21)
- Creating together
  - Essential for human flourishing
  - How truth is found
  - AI should support communities of knowledge, not replace them

## Keeping the Real Goals in View

- Are they engaging the text, or just approving AI output?
- Are they working together, or each alone with AI?
- Do they own what they produce?
- Do they trust their own judgement?
- Are they becoming more capable, or more dependent?

# The Solution

## Scripture Pipelines

- A declarative pipeline language for AI-assisted resource production
- Built for complex, heterogeneous data — the kind biblical scholarship runs on
- Grounded in Human at the Helm principles

## Scripture Pipelines: How It Works

- **Prompt contracts**: each step declares its inputs and outputs
- **JSON**: shapes what the model focuses on and guarantees what it returns
- **Intermediate artifacts**: every step saved and inspectable
- **Debug files**: exactly what the model saw and said

## The Design Principle

- **The person is in charge**
- AI follows direction, accepts correction
- Design documents, plans, audits, test suites — the person sets the agenda
- [Human at the Helm](https://github.com/nida-institute/human-at-the-helm): scholar commands, AI executes
- The pipeline architect must constantly watch out for AI drift

## Who Does This Work?

- Someone who knows the data
- Someone who understands the need and the users
- A developer with good vibe coding skills
- Built with the communities who need them
- Mentoring people globally — in every role

## Auditing

- AI synthesizes large amounts of data into an audit summary
- Human engages interactively — questions, pushback, clarification
- AI can make proposals; human decides when they agree
- Human decides what to do about it

## You Can't Hit What You Can't See

- Review HTML: efficient interface for auditing large amounts of data
- Scholar marks correct / uncertain / incorrect — can also add notes
- Generates JSON for AI or programs to act on

# What's Next

## Where We Are

- This is still very much alpha
- We are mentoring our very first teams — and learning how to do this
- We will ramp up slowly and deliberately
- We will interview new teams when we have capacity to mentor another team
