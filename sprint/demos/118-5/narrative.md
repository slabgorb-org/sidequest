# Narrative

## Problem Statement
Problem: When the GM offered a "compel" — a Fate Core mechanic where a player's character flaw creates a complication in exchange for a fate point — the game fired the offer and then went silent. The player had no way to accept or refuse, and the fate-point economy never moved. Why it matters: a compel without a response isn't a mechanic, it's theater. The SRD contract is explicit: accept = earn a fate point, refuse = spend one. Half a loop breaks the one system that makes Fate's economy feel alive to the people playing it.

---

## What Changed
Think of a compel like a contract offer slipped across the table. Before this story, the GM could slide the paper over — but the player had no pen, no ability to sign or tear it up.

F3e closes the loop in two places:

**On the server (the game engine):** The engine now actually remembers that a compel is pending. Previously it announced the offer and forgot about it entirely. Now it parks the compel in a waiting state — who made the offer, which aspect it targets, what the fate-point stakes are — and holds that state until the player responds.

**In the UI (what the player sees):** A prompt now appears when a compel is offered. The player sees two buttons — Accept or Refuse — and the fate-point math spelled out: Accept earns you +1 fate point; Refuse costs you 1. When the player decides, the screen immediately reflects the change to their fate-point total.

The result: a complete, rulebook-compliant compel round-trip. Offer → decision → consequence → updated economy, all without leaving the table to look up the rules.

---

## Why This Approach
The Fate Core SRD is unusually clear about how compels work: the economy mechanic only exists if both sides of the transaction fire. Accept and Refuse aren't optional extras — they're what makes the fate-point economy meaningful at all.

The implementation keeps the fate-point authority strictly on the server. The UI shows the delta as soon as the server confirms it; it never guesses or optimistically adjusts the count. This matches the same "server is the only economy authority" rule already established for aspect invokes — no silent state, no client-side math the server might contradict a beat later.

One design question was left open until the last moment: should the accept/refuse prompt appear as an aside (a side-channel notification per ADR-107) or as a dedicated control inside the Fate panel? The team settled this before implementation began, keeping the feature buildable without waiting on a broader UI architecture decision.

---
