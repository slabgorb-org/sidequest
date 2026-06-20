---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-7: Playtest validation gate

## Business Context

The closing gate (mirrors ADR-113's 59-8): confirm the migration did **not** harm
prose quality and that sidecar fidelity is **at or above** the pre-migration
catch-loop floor. The narrator's bar is Keith's: *good enough to fool a career GM* —
the whole point of freeing its attention was to make the prose better, so a
regression here is a real failure, not a footnote. The GM-panel
`sidecar_extraction.mismatch` rate is the quantitative metric.

## Technical Guardrails

- **Run a playtest** (headless or full per the `sq-playtest` skill) exercising turns
  that touch every migrated field: items, gold, companions, `npcs_present` (incl. a
  confrontation for `side`), `mood`/`visual_scene`/`footnotes`, and single-PC
  perception (`private_segments`) in MP.
- **Measure on the GM panel (OTEL):** `sidecar_extraction.run/.{field}/.mismatch`
  rates; compare sidecar fidelity to the pre-migration baseline (the catch-loop miss
  rate).
- **Pull, don't just restart** (project memory
  `feedback_playtest_verify_pull_not_just_restart`): measure the running binary AFTER
  a FF-pull of server + content; a stale tree masks the truth.
- If a regression is found, **file a follow-up bug** — do not patch within this
  validation story (keep the gate honest).

## Scope Boundaries

**In scope:**
- The validation playtest, the pass/fail criteria, and the metric writeup / sign-off.

**Out of scope:**
- Any code change. Regressions become new stories/bugs, not in-place fixes here.

## AC Context

1. **Coverage:** the playtest exercises items, gold, companions, `npcs_present` (with
   a confrontation), cosmetic fields, and single-PC perception.
2. **Prose unharmed:** narrator prose quality is judged at-or-above pre-migration
   (subjective + Keith sign-off — the career-GM bar).
3. **Fidelity floor:** sidecar fidelity is ≥ the pre-migration catch-loop floor (no
   *more* missed/wrong fields than before the migration).
4. **Mismatch metric:** `sidecar_extraction.mismatch` rate is observable on the GM
   panel and within an agreed tolerance.
5. **Firewall holds in MP:** no single-PC perception leaks into any peer's PART 1.

## Assumptions

- **Depends on 151-6 merged** (full migration complete). Blocked otherwise.
- A measurable pre-migration baseline exists or can be reconstructed (the catch-loop
  miss rate before cutover).
- `sq-playtest` infrastructure is available; the GM panel surfaces the new spans.

## Findings (2026-06-20 — investigation during the gulliver/glenross 150-7 playtest)

Pre-work investigation by FIXER (Agent Smith) before this story is picked up. Two
findings materially change how 151-7 must be run; read before setup.

### 1. The mismatch metric is EPHEMERAL — it cannot be read from stored sessions

`sidecar_extraction.run/.{field}/.mismatch` (and the sibling `intent_router.*` /
`dispatch_engagement.*`) spans stream to the **live** WatcherHub / GM panel only —
they are **NOT persisted** to `turn_telemetry`. Verified against the live dev DB
(`postgresql://slabgorb@localhost:5432/sidequest`): **0 rows** with
`component='sidecar_extraction'` across **every** session, including live ones where
the extractor demonstrably ran (server log shows `llm.sdk.usage
caller=sidecar_extraction`, ~1¢/turn). Persisted components (`persistence`, `genre`,
`validator`, `narrator.sdk`, …) are fine; the agent-pipeline family is the gap. Even
persisted `narrator.sdk` rows drop the `caller` attribute, so cost can't be
attributed by caller from the DB either.

**Implication for AC#4:** the metric is observable **only live, turn-by-turn on the
GM panel** — there is no historical/aggregate record, so the "extensive playtesting"
already run (150-x sweep, glenross/five_points/blackthorn_moor/gulliver) **cannot be
mined to verify fidelity after the fact.** Two viable paths:
  - (a) **Add persistence first** — route the `sidecar_extraction.*` spans into
    `turn_telemetry` (a small SpanRoute/sink change) so a validation run yields an
    aggregatable mismatch rate. Recommended if a defensible numeric AC is wanted.
  - (b) **Run one dedicated live session** and read the mismatch rate off the GM
    panel in real time (the ADR-150 step-6 design intent), recording it manually.
Either way this is real `tdd`/validation work, **not** a "read the logs and close it"
task.

### 2. A real prose/output regression was already found + fixed (RENDER-NO-SUBJECT)

The cutover this gate validates SHIPPED a quality regression that the gate exists to
catch: Story 151-5 routed **`visual_scene`** (generative art-direction) and
**`footnotes`** (the knowledge feed) through the post-narration **never-invent**
reader, which structurally cannot produce them → empty every turn → **zero scrapbook
illustrations on every world** + the journal/`known_facts=0` feed (likely the
carried-forward CLUE-JOURNAL bug). This is exactly an **AC#2/AC#3 failure**.

Per this story's own guardrail ("file a follow-up bug; do not patch within the
validation story"), it was filed (ping-pong RENDER-NO-SUBJECT) and fixed **separately**
by FIXER, NOT inside 151-7:
  - **server PR #994** (merged `8cf556bc`): bucket-B is now **extractive-only**;
    `visual_scene`+`footnotes` restored to narrator-owned (like `private_segments`).
  - **ADR-150 amended** (orchestrator `main` `6ff1b2f`): "bucket-B is
    extractive-only; generative fields stay narrator-owned."

**Implication for AC#1/#3 coverage:** the migrated-field list in the ACs predates the
amendment. Post-amendment the **9 extractive** fields (items×4, gold, companions×2,
`npcs_present`, `scene_mood`) are what the extractor owns and what the mismatch metric
covers. `visual_scene`/`footnotes` are now narrator-owned — validate them NOT as
extractor-fidelity but as **behavior**: a scene-change turn dispatches a render (image
appears, no `render.eligible_no_subject`), and an investigative turn populates
`footnotes` → `known_facts > 0`.

### 3. Restart prerequisite

The running oq-3 stack must FF-pull `develop` (now carries #990 Fate narrate-crash +
#994 RENDER-NO-SUBJECT) and restart before ANY 151-7 validation — otherwise the run
measures a stale binary where rendering is still broken (the recurring
oq-N-lags-develop trap). Confirm renders fire + the journal feed populates post-restart
as the entry gate to the actual fidelity measurement.
