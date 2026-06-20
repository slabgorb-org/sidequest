# PARKED brainstorming note — Intent Router clarify-loop

**Status:** PARKED (not an active spec). Captured 2026-06-20. Parked in favor of
chasing the router *latency* problem first (see companion design doc
`2026-06-20-intent-router-latency-*`).

**Owner intent:** "I don't want to drop the clarify loop." This note preserves the
idea and — critically — the diagnostic finding that reframes it, so future-us doesn't
re-litigate it as a latency fix.

## The idea (as proposed)

When the sealed turn fires and the Intent Router *cannot determine the player's
intent*, don't push the ambiguity to the expensive narrator. Instead **take a round
and ask the player** — pop a UI prompt ("I didn't quite catch that"), offer a small
set of disambiguation choices plus a free-form box, and feed the answer back through
the (cheap) Intent Router. This emulates the table: when the DM is unclear on what a
player said, they ask.

## Why it was reframed (the load-bearing diagnostic, 2026-06-20)

A headless latency-diag playtest (`scenarios/latency_diag_82_9.yaml`, tea_and_murder/
glenross, span capture via Jaeger) showed the router's 20-25s latency is **NOT**
ambiguity-grind:

- `latency_ms == sdk_latency_ms` on every turn — 100% of the time is in the model
  call; **zero** retry/validation overhead.
- `retry_count = 0` everywhere — the retry/timeout path the original premise assumed
  is not firing at all.
- Latency has **no correlation with confidence** (a `conf=0.95` turn takes ~20s; a
  `conf=0.2` turn takes ~13s) but a **0.94 correlation with output_tokens**.
- p50 ≈ 8.6s, p95 ≈ 18.4s, max ≈ 26.6s — slow on *confident* turns too.

**Conclusion:** the clarify-loop does not reduce latency. Worse, reactively it *adds*
a second router call (another 5-26s of output generation) plus human typing time on
the exact turns it touches — so as a latency fix it is net-negative. It must be sold
on its real merits below, and only after the router itself is fast.

## What it IS good for (the two real axes)

1. **Table-feel / quality.** When the router is *genuinely* unsure (the existing
   per-dispatch confidence gate, default `< 0.6`, in `run_dispatch_bank`), today the
   dispatch silently degrades to a `must_narrate` hint and the **expensive narrator**
   improvises around the ambiguity. Asking the player is the right tabletop move and
   keeps the mechanical spine honest instead of punting to prose.

2. **Epic 48 local-router tuning data (the flywheel).** Epic 48 stood up local Qwen
   (`qwen2.5:7b-instruct`, `SIDEQUEST_CLASSIFICATION_BACKEND=ollama`) with an A/B
   harness vs Claude. Every clarification is a **gold-labeled training pair**:
   `(ambiguous action + state_summary) → (player's disambiguation) → correct intent`.
   You cannot synthesize "what confused the classifier" — it must be harvested from
   real play. Emitting a tuning-corpus record on every clarify turns a UX patch into a
   data flywheel: the more it asks, the less it needs to ask.

## Reuse target when we build it (do NOT invent a new round-trip)

The **Fate DEFEND barrier** (ADR-151) is the battle-tested shape to clone:
`FateDefendRequestPayload` (server→client, carries `request_id`, parks the sealed
round) → `FATE_THROW` (client→server, typed response OR concede). A clarify-loop is
the same: park the round, send `request_id` + the candidate intents, take back a
choice or free-form, re-route. Server: `sidequest/server/session_room.py` barrier +
a new `ACTION_CLARIFY_REQUEST`/`ACTION_CLARIFY_RESPONSE` pair mirroring the Fate
defend payloads. UI: the FateDiceTray/defend-surface mount pattern is the model.

## Trigger gate

Gate on genuine low confidence — `confidence_global` (or per-dispatch confidence)
below the subsystem threshold — NOT on latency. Keep it sparing (the Guitar Solo /
Alex-pacing concern: don't make the whole table wait while one player disambiguates;
prefer asking during input-collection rather than holding a fired barrier).

## Sequencing

Do the latency fix first. Once the router is fast, the clarify round-trip is cheap and
this feature becomes palatable. Revisit after the latency work lands.
