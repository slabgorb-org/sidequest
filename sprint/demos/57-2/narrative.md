# 57-2

## Problem

Problem: After a major refactor in May 2026, there was an open question about whether any of the narrator's instruction files were accidentally left empty — silent blanks that the AI storyteller would load and use, contributing nothing but still eating up expensive processing budget. Empty instruction files are a subtle class of bug: the system doesn't crash, it just quietly sends blank rules to the AI on every turn, costing tokens while delivering no value.

Why it matters: The narrator AI for SideQuest runs on a per-turn token budget. Sending empty files inflates that bill invisibly. More critically, if a file labeled "combat rules" or "player agency guardrail" is blank, the AI lacks those guardrails entirely — it might improvise combat incorrectly or ignore player agency without anyone noticing, because nothing breaks loudly.

---

## What Changed

The team ran a full inventory of the 11 instruction files that feed the narrator AI. Think of these files as pages in the narrator's rulebook — one covers combat, one covers dialogue, one defines the narrator's voice, and so on.

The audit found that all 11 files have real content. No blanks. No stubs. The concern that triggered this story — that five files from a recent reorganization might have been left as empty shells — turned out to be a memory artifact from an earlier draft state, not current reality.

The deliverable is a single new document (`AUDIT.md`) placed alongside the instruction files themselves. It records the findings, file sizes, and how the files connect to the AI narrator — so the next time someone asks "are any of these empty?", the answer is a 30-second table scan rather than a full re-investigation.

One small correction was also made during review: the audit document initially misattributed which part of the code registers the instruction files. The reviewer traced the actual call chain and corrected two lines so the documentation accurately reflects how the system works.

---

## Why This Approach

**Why write a document instead of a test?** The goal was to close the investigation quickly and credibly. A document placed right next to the files it audits is the lowest-friction answer — any developer opening that directory in the future sees the audit log immediately. A test would be more robust long-term (and one is flagged for future work), but for a one-point audit story, the doc earns its place.

**Why not just close it as "no bug found" with no artifact?** Because Epic 57 is an ongoing effort to trim narrator costs across several stories (57-3, 57-4, 57-5). Future passes may revisit the same question. A durable log means those future engineers append a dated entry rather than repeat the investigation from scratch.

**Why correct the attribution in review rather than send it back to dev?** The correction was two lines in a doc file — well within scope and faster than a roundtrip. Accurate institutional memory is the whole point of the document; letting a wrong call-chain description sit would undermine it.

---
