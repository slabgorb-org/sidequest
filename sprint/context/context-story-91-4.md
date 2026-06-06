---
parent: context-epic-91.md
workflow: tdd
story: 91-4
title: "Cross-model runaway coverage — extend ADR-134 detector + per-session cumulative cost to all call sites and models"
points: 2
type: feature
epic: 91
repo: sidequest-server
---

# Story 91-4 Context

> **Sequencing.** Naturally follows 91-1 (consumes the single SDK choke point /
> caller-tag seam) but can be **drafted in parallel** — the red phase below can be
> written against the existing detector contract before 91-1's factory consolidation
> lands. The wiring/AC items that require a non-narrator *production* call path
> (AC-4) assume 91-1 has landed; everything else can be specced and red-tested now.

## Business Context

The ADR-134 runaway detector is SideQuest's **hard-kill backstop against pathological
spend** — the only mechanism that terminally stops billing when cumulative session
spend crosses a catastrophe line ($10/session default, env-overridable). But today it
**only watches the narrator loop.** Both the rolling-baseline detector
(`_maybe_emit_cost_runaway`) and the per-session cumulative ceiling
(`_check_cost_ceiling` / `_update_session_cumulative`) live inside
`AnthropicSdkClient.complete_with_tools` and are fed *only* by narrator turns.
Every other SDK spender — the Intent Router (ADR-113, Haiku), asides (ADR-107), the
dungeon-materializer curate (`CallType.SCRATCH`) — flows through *separate*
`AsyncAnthropic` constructions in `llm_factory.py` (`_AsideLlm`, `_IntentRouterLlm`)
that never touch the ceiling at all.

The **[COST-1]** incident (cost forensics, 2026-06-05) proved this blind spot is not
hypothetical: the **Haiku 4.5 tier alone burns $3.3–3.5/day — roughly *half* the daily
Anthropic bill — and ~97% of it emits neither a usage log line nor an OTEL span.** A
Haiku runaway today (e.g. the unexplained ~8 router calls/turn, or a retry loop) is
**completely invisible to the ceiling**: it could run a session's true cost far past
$10 while `_session_cumulative_cost_usd` — fed only by Sonnet narrator turns — reads
well under the cap and never trips the kill. The hard-kill that exists to bound a
billing catastrophe is structurally watching the *cheaper, well-behaved* half of the
bill and ignoring the half that actually went dark.

This story makes the ceiling **model-agnostic and all-call-site**: every billable SDK
call for a session, regardless of model or caller, contributes to the same per-session
cumulative pot that the $10 hard-kill enforces, and emits attribution telemetry so the
GM panel can see *who* spent.

## Technical Guardrails

### EXTEND the detector — never fork it

This is an **epic-level hard constraint** (epic 91 §Cross-Epic Dependencies:
*"91-4 extends the existing detector; it must not fork it"*). There must be **one**
per-session cumulative tracker, **one** ceiling value, **one** terminal-refusal path,
**one** `session.cost_ceiling_exceeded` event shape. A parallel detector for
non-narrator spend would defeat the entire point — two pots that each stay under $10
can sum to $20, exactly the conflation ADR-134's "Alternatives considered" rejected for
the global-vs-per-session question. The cumulative pot is **per-`session_id` dollars,
model-agnostic by construction** (ADR-134 §Invariants: "Session-id keying… keyed on
`session_id`, never instance-wide"). Joining Haiku spend to that same pot is the
*natural* reading of the ceiling, not a new mechanism.

### Red-phase design decisions to surface

These are the genuine forks the TEA/Architect must pin down in the red phase; each has a
recommended answer grounded in the ADR, but the test names should make the decision
explicit:

**(a) Does non-narrator (Haiku) spend join the same cumulative pot, or a parallel
window?**
*Recommended: the same `_session_cumulative_cost_usd[session_id]` pot.* The ceiling is
per-session **dollars**, model-agnostic — ADR-134's hard-kill contract is "this session
has spent $X of its $10," and a dollar of Haiku is the same catastrophe risk as a dollar
of Sonnet. A parallel window would re-introduce the global-vs-per-session conflation the
ADR explicitly rejected. **The ceiling must see total session spend.**

**(b) Baseline windows are tuned for narrator call *shapes* — do non-narrator costs
join the K=10 rolling deques?**
*Recommended: NO — cumulative-pot-only for non-narrator callers; full fingerprinting
stays narrator-scoped (at least for this story).* The rolling-baseline detector
(`_cost_baseline`, `_input_tokens_baseline`, K=10) and its four triggers
(`cost_multiple`, `io_fingerprint`, `input_absolute`, `cost_absolute`) are calibrated
to **narrator turn shapes**: the warmup floors ($0.03 cost, 12k input), the
60K-in/12-out fingerprint, the $0.30 absolute cost floor. Haiku router calls are *tiny*
(~$0.005, ~5k input, ~100 output). Pumping many small Haiku costs into the same K=10
deque would **distort the rolling mean downward**, lowering the narrator's own trip
thresholds and producing false `cost_multiple`/`io_fingerprint` alarms on legitimate
Sonnet turns — the deque would no longer represent the narrator baseline it was tuned
for. The clean split: **non-narrator callers feed the cumulative *ceiling* pot only;
the fingerprint detector remains narrator-shaped.** (A future story may add
per-caller/per-model baseline windows if Haiku runaway-*detection*, not just
ceiling-bounding, is wanted — but that is out of scope here; the absolute cumulative
ceiling already bounds the catastrophe.)

**(c) Calls outside a session context need a `session_id` or an explicit exemption.**
ADR-134 §Invariants is emphatic: *"`session_id=None` is a hard bypass, not a synthesized
key… the contract is 'off for None,' not a magic `<no-session>` bucket"* (No Silent
Fallbacks). The dungeon-curate worker (`materializer.py`, `CallType.SCRATCH`) currently
has no `session_id` plumbed. Two acceptable outcomes — and the choice **must be loud,
not silent**:
  - **Plumb the real `session_id`** through to curate so its spend joins the session pot
    (preferred when the call is genuinely session-scoped — a curate fired *for* a live
    session).
  - **Explicit exemption** for a genuinely session-less job, accompanied by an **OTEL
    event** recording that an un-ceilinged call was made (so the GM panel / 91-5
    reconciliation can see the exempted spend rather than have it vanish). A silent
    `session_id=None` that bypasses the ceiling *and* emits no telemetry is exactly the
    dark-spend hole [COST-1] found — forbidden.

### The seam: detector state should move to the 91-1 choke point

Today the detector state (`_cost_baseline`, `_session_cumulative_cost_usd`,
`session_cost_ceiling_usd`, `_session_ceiling_announced`) lives **inside
`AnthropicSdkClient`** — which is *one of three* `AsyncAnthropic` construction sites
(narrator, plus `_AsideLlm` and `_IntentRouterLlm` in `llm_factory.py`). The natural
architecture is to lift the per-session cumulative-cost + ceiling machinery to the
**91-1 factory choke point** so *every* call — narrator, router, aside, curate — passes
through the same enforcement on its way out. The narrator client then becomes a *consumer*
of the shared ceiling rather than its sole owner. This is the "Don't Reinvent — Wire Up
What Exists" path: 91-1 builds the single seam; 91-4 makes the existing detector live at
that seam instead of behind the narrator-only door. If 91-1 has not yet landed when this
story is implemented, the fallback is to expose the ceiling/cumulative API on a shared
object the factory injects into all clients — but the destination is the choke point.

## Scope Boundaries

**In scope:**
- All-model, all-call-site **per-session cumulative cost** accumulation: narrator
  (Sonnet), Intent Router (Haiku), asides (Haiku), dungeon curate (`SCRATCH`) — every
  billable SDK call for a `session_id` adds to the one cumulative pot.
- **Ceiling enforcement on non-narrator calls**: a non-narrator caller that pushes
  cumulative across the ceiling triggers the same terminal `AnthropicSdkCostCeilingExceeded`
  → typed `session.cost_ceiling_exceeded` path; subsequent calls for that session
  (narrator *or* non-narrator) are terminally refused.
- **OTEL/watcher events for non-narrator contributions**: every non-narrator billable
  call emits its spend to the watcher with a **caller tag** so the GM panel can
  attribute *who* spent (component naming derived from the caller, alongside the existing
  `narrator.sdk` events).
- Resolution of the `session_id=None` curate question per guardrail (c) — plumb or
  loudly exempt.

**Out of scope:**
- **Changing ceiling values or trigger thresholds.** `_SESSION_COST_CEILING_USD=$10`,
  the warmup floors, `_COST_TRIGGER_MULTIPLE`, the absolute floors, and
  `SIDEQUEST_SESSION_COST_CEILING_USD` are **operator-tunable config and stay as-is**.
  This story changes *what feeds* the pot, not *where the line is*.
- **Reconciliation against the Anthropic Admin API** (that is 91-5 — instrumented totals
  vs ground truth, gap-alert).
- **The choke-point construction itself** (91-1 — sole `AsyncAnthropic` site, uniform
  usage log line + `llm.request` span, caller tags). 91-4 *consumes* the caller tag;
  it does not build it.
- Adding per-caller/per-model **rolling-baseline fingerprint** windows (deferred — see
  decision (b); only the cumulative *ceiling* goes cross-model here).
- The Intent Router cache repair / 8×-per-turn volume hunt (91-2/91-3).

## AC Context

Testable acceptance criteria (TDD red phase writes these to fail against today's
narrator-only detector):

1. **Cross-model cumulative drives the kill.** A simulated **Haiku** call sequence
   (each call individually well under any per-call trigger) accumulates per-session
   cumulative cost across the ceiling and triggers the **same typed
   `session.cost_ceiling_exceeded` path** as a narrator overrun: raises
   `AnthropicSdkCostCeilingExceeded` carrying `session_id` / `cumulative_cost_usd` /
   `ceiling_usd`, the watcher event fires (severity `error`, component naming consistent
   with ADR-134), and the next call for that session is **terminally refused at the
   pre-flight check** — no grovelling, no recovery, per ADR-134 §Invariants
   ("Terminal refusal — no recovery"). Use a lowered ceiling in the test
   (`SIDEQUEST_SESSION_COST_CEILING_USD`) so the sequence is small.

2. **Narrator-only behavior unchanged (regression gate).** The full existing detector
   suite stays green: the four triggers, the warmup floors, the baseline-ceiling clamp,
   the announced-once dedup, `reset_baselines` *not* clearing the cumulative tracker,
   and `session_id=None` bypassing both mechanisms all behave exactly as before for the
   narrator path. **No fork** means no regression — this AC is the proof the detector
   was extended, not duplicated.

3. **Watcher event carries a caller tag.** Each non-narrator billable contribution
   surfaces a watcher event whose payload includes a **caller** discriminator (derived
   from 91-1's caller tag / `CallType`) so the GM panel can attribute **WHO spent** —
   `intent_router` vs `aside` vs `curate` vs `narrator`. This is the OTEL Observability
   Principle applied to money: a non-narrator dollar that hits the pot but emits no
   attributable event re-creates the [COST-1] dark-spend hole.

4. **Wiring test — production non-narrator path increments the pot.** A behavior test
   that drives a **real production non-narrator call path** (the Intent Router pass via
   the factory choke point, or an aside) and asserts the per-session cumulative pot
   actually increased and/or the contribution event fired — not an in-isolation unit
   call. Per the server's "Every Test Suite Needs a Wiring Test" + "No Source-Text
   Wiring Tests" rules: drive the flow and assert the **emitted watcher event** /
   observable cumulative state, **not** a grep of source for a call. (The canonical
   shape is an OTEL/event assertion or a fixture-driven behavior test, as the server
   CLAUDE.md prescribes.)

## Assumptions

- **91-1 lands first** (or is co-developed): the single SDK choke point exists and every
  call carries a **caller tag**, so 91-4 can route any call through one ceiling and stamp
  contributions with WHO. Red-phase tests for AC-1/2/3 can be authored against the
  existing detector contract in parallel; AC-4's *production*-path wiring assumes the
  choke point.
- **Ceiling semantics are per-`session_id` regardless of model.** The $10 hard-kill is a
  per-session **dollar** budget; a dollar is a dollar whether Sonnet, Haiku, or Opus
  spent it. This is the load-bearing reading that makes "extend, don't fork" coherent.
- **ADR-134's exact trigger taxonomy** as read in the ADR / code is authoritative:
  four triggers with priority `io_fingerprint > input_absolute > cost_multiple >
  cost_absolute`, exactly one event per call; pre-flight + post-iter ceiling
  enforcement; announced-once dedup via `_session_ceiling_announced`; the typed
  `AnthropicSdkCostCeilingExceeded` carrying actionable fields. 91-4 changes **what feeds
  these mechanisms** (now all models / all call sites), **not the taxonomy itself**.
- The dungeon-curate worker was **idle during the [COST-1] window** but must still be
  instrumented (epic 91 key-files note) — it is the concrete instance of the
  guardrail-(c) `session_id=None` decision.
