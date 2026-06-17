---
title: Scripture Pipelines
subtitle: AI-assisted biblical resource production
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

[github.com/nida-institute/awesome-biblical-data](https://github.com/nida-institute/awesome-biblical-data)

# AI — Promise and Risk

## What AI Does Well

- Integrates complex, heterogeneous datasets
- High-level picture and fine-grained details
- Brainstorming and rapid prototyping
- Generates first drafts for scholars to shape

## Where AI Falls Short

- **Hallucinates** — plausible errors, hard to catch
- **Drifts** — pursues its own interpretation
- **No self-evaluation** — confident ≠ accurate
- Always confident. Always plausible. Sometimes true.

## Expertise — It Still Matters

- Experts can get it right when AI cannot
- LLMs go off in dead ends with these datasets
- They don't understand the data
- Decades of annotation are irreplaceable
- AI reasons from this data; it cannot replace it

## Building Communities of Knowledge

- AI should make you better, not more dependent
- Use AI to reason, not just to summarize
- Produce materials scholars use to teach each other
- Expertise must be transferred and reproduced
- AI collaboration should build capacity

## The Formation Risk

- Approving output that looks good is easy
- Catching what's wrong requires doing the work
- The AI gets faster; the scholar gets lazier
- Expertise erodes invisibly
- Nobody left to build these things from scratch
- You know what happens when a consultant does the work for the translator

# The Solution

## The Design Principle

- **The scholar is in charge**
- AI follows direction, accepts correction
- Designed to assume it doesn't know the human's goals
- [Human at the Helm](https://github.com/nida-institute/human-at-the-helm): scholar commands, AI executes

## How It Works

- **Prompt contracts**: every step declares its data needs
- **Structured output**: no prose where a field is expected
- **Intermediate artifacts**: every step saved and inspectable
- **Debug files**: exactly what the model received and said

## Auditing

- Human brings domain judgment
- AI traces claims back to their source
- **Five-claim spot-check**: is this grounded in the data?
- Trace backward from bad output to find where it went wrong

# In Practice

## What You Can Build

- Exegetical helps from discourse, morphology, entity data
- Comprehension checking from your Paratext project
- Community Bible study materials for specific audiences
- Orality-adapted content
- Rapid prototypes to try before full production

## The Team

- Someone who knows the data
- Someone who knows the audience
- A developer working with AI tools
- `sp gui` for non-developers
- Mentoring developers is part of what we do

## Get Involved

- Currently producing alpha-level resources — it works for us
- Soon: mentoring developers who support scholar teams
- Want to be part of this?
- We interview the developer
- Your team needs all three skills: data, audience, development
- [Scripture Pipelines](https://github.com/nida-institute/LLMFlow)
- [Awesome Biblical Resources](https://github.com/nida-institute/awesome-biblical-resources)
- [Human at the Helm](https://github.com/nida-institute/human-at-the-helm)
