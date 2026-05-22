---
parent: context-epic-60.md
workflow: tdd
---

# Story 60-3: Diagnose narrator block-0 cache_write churn — prefix drift vs TTL/cadence

> **✅ OUTCOME (2026-05-22): answer = NEITHER drift NOR simple TTL/cadence.** The
> cached prefix is byte-stable (no drift), and the suspected `state` sections are
> User-bucket (uncached — not the cause). The real cause: the narrator's **tool-use
> loop continuation** re-mints the ~11.7k prefix at 5m on every iter-2+ call, because
> the growing `tool_use`/`tool_result` conversation carries no cache breakpoint.
> Fix (60-4): a moving 1h `cache_control` breakpoint on the last continuation message.
> Authoritative write-up + evidence: `sprint/archive/60-3-session.md` → "Dev Diagnosis
> (60-3 — FINAL)". The Business Context below states the *pre-investigation* framing.

## Business Context

Epic 60 identified a ~$0.046/call wasted `cache_write` cost. The root cause is three
`state`-category (volatile) sections — `narrator_available_confrontations`, `trope_beat_directives`,
`npc_roster` — mis-zoned into the cached Early zone of `system_blocks[0]`. Story 60-2
built the observability eyes: a Prompt-tab Zone Breakdown that emits per-block content
digests, real API cache usage, and flags mis-zoned state.

This story (a **1-pt diagnosis spike**) uses those eyes to run an instrumented multi-turn
session and confirm the diagnosis: the churn is the three mis-zoned state sections
(drift evidence), NOT TTL/cadence expiry across slow playtest tempo. The output is a
finding that scopes 60-4's fix and proves the observability is working.

**Success criterion:** Capture a multi-turn `tea_and_murder/glenross` session that shows
`system_blocks[0]` digest changing (and thus re-writing) every turn, and identify which
of the three `state` sections changed to cause the drift. Log the finding, then exit
(no fix — 60-4 fixes).

## Technical Guardrails

- **Instrument, don't speculate.** Use 60-2's OTEL eyes and the Prompt-tab Zone
  Breakdown to observe the churn. Do not attempt to reason through the code; the
  display is the ground truth.
- **Multi-turn cadence matters.** Run at least 3-4 player turns to show the pattern
  repeats and rules out a one-off anomaly.
- **Identify the drifting section.** The Prompt-tab breakdown shows per-section digests.
  Note which of the three `state` sections (confrontations/trope_beat_directives/npc_roster)
  actually changed on a turn where `system_blocks[0]` digest drifted. (The finding
  scopes whether all three need re-zoning or only the active one.)
- **Verify TTL is not the culprit.** Confirm via timestamps that the churn is not due
  to 5m cache TTL expiry between turns — the cache should be fresh on each turn if
  block 0 is byte-stable. If you see TTL expiry in the logs, that is separate evidence
  and should be called out.
- **Use real data.** Run against a live session (or a fixture that mimics playtest
  conditions), not a stub. `tea_and_murder/glenross` is the pack from the 2026-05-21
  playtest that exposed the bug.

## Scope Boundaries

**In scope:**
- Spin up a test session and run 3-4 turns of instrumented narration (leveraging
  60-2's new OTEL fields).
- Observe and log block-0 digest drift and identify which `state` section(s) changed.
- Produce a finding: "block-0 drifts due to [section] changing; other two sections
  stable / also changing" and confirm it's not TTL expiry.
- Document the finding in the session file's "Delivery Findings" section.

**Out of scope:**
- Fixing the mis-zoning (that is 60-4).
- Implementing alternative zone strategies or workarounds.
- Broader performance optimization (ADR-110 snapshot slimming is separate).

## AC Context

(Authoritative ACs live in the sprint YAML; expanded here.)

- Conduct a multi-turn `tea_and_murder/glenross` session with 60-2's OTEL eyes active.
- Confirm `system_blocks[0]` digest drifts (changes) on every turn, invalidating the
  cache write.
- Identify the specific `state`-category section(s) that drift (from the per-section
  digest breakdown in the Prompt tab).
- Rule out TTL expiry as the root cause (confirm cache is fresh, not expired).
- Document findings in the session file: which section drifts, which are stable, and
  whether the pattern is consistent across all 3-4 turns.
- No regression test needed for a spike (diagnosis only); 60-4 will add a fix validation test.

## Assumptions

- 60-2 (OTEL eyes) is complete and emitting per-block digests, cache-usage numbers,
  and mis-zoned-state flags.
- A test fixture or live session against `tea_and_murder/glenross` is available or
  easily spun up.
- The three `state` sections are already visible in the Prompt-tab Zone Breakdown
  (labeled with their `category`).
