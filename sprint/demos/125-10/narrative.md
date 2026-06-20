# Narrative

## Problem Statement
Problem: Two separate parts of the SideQuest system each contain their own copy of the rule "this session is a test run," written in different programming languages with no enforcement that they stay identical. Why it matters: If a developer updates one copy and forgets the other, the server and the player interface silently disagree about which sessions are real gameplay — potentially exposing test-run data in the live GM dashboard, or hiding real sessions from it. The bug would be invisible in normal testing because each piece works fine in isolation.

---

## What Changed
Imagine two security guards at opposite ends of a building, each carrying a hand-written list of who is allowed in. If someone updates one list but not the other, the guards give different answers to the same question. This story adds a rule that both lists must always match — and makes an automated check that screams if they ever drift apart.

Technically: the server (Python) and the player interface (TypeScript/React) each had their own copy of the logic that says "a session slug starting with `test-` or `tool-test-` means this is a test run, not a real game." A contract test was added so that any time either copy changes, the test suite catches the mismatch immediately — before the code ships.

---

## Why This Approach
The cleanest fix would be one shared definition that both sides read from. But the server is Python and the UI is TypeScript — they can't share source files directly. Rather than introducing a new build step or code-generation layer (more moving parts, more risk), a contract test achieves the same safety guarantee: it documents the exact rule in one place and verifies both implementations match it on every CI run. Cheap to add, impossible to accidentally bypass, zero new infrastructure.

---
