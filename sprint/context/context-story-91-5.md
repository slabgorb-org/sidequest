---
parent: context-epic-91.md
workflow: tdd
---

# Story 91-5: Dark-spend detector — automated three-layer reconciliation (instrumented vs Admin API), loud alert on >10% gap, GM dashboard surface

## Business Context

This story is **the regression tripwire** for epic 91. The originating incident
(pingpong **[COST-1]**, 2026-06-05 — see `context-epic-91.md` Background) went unnoticed
for *days*: ~half the daily Anthropic bill was invisible to all internal accounting and
nothing automatically compared the org bill against what SideQuest thought it was
spending. The Haiku tier crept from 525k → 713k → 3.16M uncached tokens/day across
Jun 1→2→3 with no alarm, because the only thing that *could* have caught it was a human
running `/sq-llm-costs` by hand.

This story **automates that skill's manual three-layer methodology** — it is, in the
epic author's framing, "this whole incident, automated." Concretely: once 91-1 has
landed and every Anthropic call emits an instrumented usage record (log line +
`llm.request` span + `cost_usd` + caller tag through the single choke point), the
instrumented totals become a *ground truth of what we think we spent*. The Admin API
(`scripts/anthropic_usage.py`) is the *ground truth of what we were actually billed*.
**Any gap between the two = a NEW uninstrumented caller** — exactly the failure mode
[COST-1] was — and it must alert **loudly, within a day**, never silently accrue.

The reconciliation logic itself already exists as the `/sq-llm-costs` skill
(`.claude/skills/sq-llm-costs/SKILL.md`): three layers (server logs / Jaeger / Admin
API), healthy baselines (narrator 76–82% cache hit, 6.5–8¢/turn), and a red-flags table
("Admin $ ≫ log $ ⇒ uninstrumented caller"). This story turns that human procedure into
a repeatable automated check that surfaces on the GM dashboard the operator (Keith)
already watches.

## Technical Guardrails

- **Reuse `scripts/anthropic_usage.py` — extend, don't rewrite.** Same doctrine as the
  rest of epic 91 (91-1 consolidates `compute_cost_usd` / `_record_haiku_usage_on_span`
  rather than reinventing them). The script already speaks both endpoints the Admin layer
  needs: `cost_report` (billed cents per day bucket) and `usage_report/messages`
  (token + cache breakdown, with `group_by[]=model` already wired). The reconciliation
  needs **per-model** Admin totals — the script already passes `group_by[]: ["model"]`
  to the usage endpoint, so the per-model structure is there in `--raw`; the daily-summary
  print path just collapses it. Add a programmatic entry point that returns the
  per-model token/cost structure instead of (only) printing it.
- **Respect the script's design note: org-billing has no turn counts.** The in-code
  comment (lines 33–39) is explicit and load-bearing: health *bands* are deliberately
  NOT applied in this script because daily-$ "punishes you for playing more" and the
  meaningful per-turn signal lives server-side on the `narration.turn.total_cost_usd`
  span (`anthropic_cost.cost_band`). **Do not** add per-turn band logic here. This
  story compares **per-model totals over a window**, not per-turn economics — the gap
  detector is a *volume reconciliation*, not a unit-cost judgement.
- **UTC-vs-local bucketing caveat is real and must not false-positive.** Admin API
  buckets are **UTC** (`_rfc3339` / `_day_floor` snap to midnight UTC); the server log
  rotations the instrumented side may read from are **rotation-stamped local time**
  (per SKILL.md Layer 1: "each day can include the prior evening's tail"). A naïve
  same-calendar-day compare will smear ±1 day at boundaries. See AC-4 for the resolution
  (compare a rolling multi-day window, or define a tolerance band, so a single day's
  edge-smear can't trip the 10% gate).
- **`ANTHROPIC_ADMIN_KEY` is a SEPARATE admin key (`sk-ant-admin…`), not the inference
  key.** The cost/usage endpoints reject `sk-ant-api…` keys (401/403). The existing
  script has a *deliberately soft* fallback to `ANTHROPIC_API_KEY` "only so the failure
  is a clear 401 rather than 'no key'." For the **automated detector** that softness is
  wrong — a 401 buried in an exception is not a loud alert. **Fail loud if the admin key
  is absent: raise a typed error** (AC-3). Never fall back to the inference key and
  never let an auth failure masquerade as "zero gap, all clean."
- **Decide and document the trigger mechanism.** Options: (a) operator-run `just` recipe,
  (b) cron, (c) server-startup job / daemon. **Recommendation: operator-run `just`
  recipe + GM dashboard surface first — no daemons.** This matches the project's
  "operator-triggered" stance for non-gameplay infrastructure (cf. music generation is
  operator-run via a script, ADR-095), keeps the Admin-API polling under explicit human
  control (rate-limit-friendly, see Assumptions), and avoids standing background
  processes the operator can't see. The red phase should still leave the door open to a
  later cron wrapper, but the v1 wiring target is: `just <recipe>` runs the
  reconciliation, prints the per-model report, and (on a >10% gap) emits the loud alert
  that lands on the dashboard.
- **Alert path rides existing WatcherHub / dashboard events — do NOT build a new
  notification system.** `sidequest/telemetry/watcher_hub.py::publish_event(event_type,
  fields, *, component=, severity=...)` is the one true semantic-event bus (ADR-132,
  builtins-pinned singleton). A >10% gap publishes a `publish_event(...,
  severity="error")` event; the GM dashboard (`/dashboard`, served by
  `sidequest/server/dashboard.py`, listening on `/ws/watcher`) already renders watcher
  events by component/severity and replays its 2000-event ring buffer on refresh. The
  loud alert is therefore: **log ERROR + `publish_event(severity="error")` watcher event
  + dashboard surface** — three channels, all pre-existing.

## Scope Boundaries

**In scope:**
- A reconciliation that compares **instrumented per-model totals** (from 91-1's
  instrumentation — see Assumptions for source-of-truth choice) against **Admin API
  per-model totals** over a defined window.
- **>10% gap = loud alert** on all three channels: log `ERROR` + WatcherHub
  `publish_event(severity="error")` + GM dashboard surface.
- **Per-model breakdown in the output** — the report attributes the gap by model
  (Sonnet / Haiku / Opus), matching the SKILL.md red-flags table ("group by
  api_key_id + model; match per-call token shape to known call sites"). A gap on the
  Haiku line specifically is the [COST-1] signature.
- A clean (<10% gap) run produces a report with **no alert fired** (AC-2).

**Out of scope:**
- **Fixing whatever the gap reveals.** The detector *detects*; if it surfaces a new
  uninstrumented caller, that's a *new story* filed with the evidence (same discipline
  as the `/sq-llm-costs` skill: "code bugs go to the dev lane via pingpong/backlog;
  never fix code from this skill").
- **Changing instrumentation** — that's 91-1. This story *consumes* 91-1's instrumented
  totals; it does not add, move, or alter any usage log line or span.
- **Billing for non-Anthropic backends.** Epic 92 (local LLM calls) are `cost_usd=0` by
  definition and the Admin API never bills for them, so they are out of the
  reconciliation's denominator entirely — a local call is neither in the instrumented
  Anthropic totals nor in the Admin totals.

## AC Context

All ACs are testable with fixtures — the Admin API response shape and the instrumented
totals are both injectable so the reconciliation logic runs offline (the live Admin call
is gated the way the epic gates its other live-API assertions, e.g. the composer
Gymnopedie smoke test).

1. **Gap fires with attribution.** Given fixture Admin per-model totals and fixture
   instrumented per-model totals with a **>10% gap on at least one model**, the
   reconciliation fires the alert **and the alert carries per-model attribution** (which
   model, instrumented $ vs Admin $, gap %). Assert the `ERROR` log AND a watcher event
   with `severity="error"` were emitted.
2. **Clean report, no alert.** Given totals within the 10% band on every model, the run
   produces a clean report and **fires no alert** — no `ERROR` log, no error-severity
   watcher event. (Guards against a trigger-happy detector that cries wolf and trains the
   operator to ignore it.)
3. **Missing admin key = loud typed error.** With `ANTHROPIC_ADMIN_KEY` unset, the
   detector raises a **typed error** (not a bare `sys.exit`, not a silent fallback to
   `ANTHROPIC_API_KEY`, not a "zero gap" clean run). The script's existing soft fallback
   is acceptable for the *manual* CLI but the automated detector path must fail loud.
4. **Day-boundary smear does not false-positive.** Construct totals where the *only*
   discrepancy is a single day's worth of spend straddling the UTC/local boundary (the
   Admin bucket counts it on day N, the instrumented side on day N+1). The detector must
   **not** report a >10% gap. Resolution: either compare a **rolling 7-day window** (so a
   one-day edge-smear is <15% of the denominator and well under threshold once spread) or
   define an explicit **boundary tolerance** — the red phase picks one and documents it.
5. **GM dashboard shows the reconciliation result (wiring test).** A reconciliation run
   on the production path produces an event/endpoint **reachable from the GM dashboard**.
   Per the server's "no source-text wiring tests" rule, this is a *behavior* test: drive
   the reconciliation, assert the `publish_event` reached the WatcherHub (subscribe a
   test sink to the hub and assert the event arrives), OR assert the dashboard projection
   endpoint returns the latest reconciliation result. Either proves the surface is wired,
   not merely defined.

## Assumptions

- **91-1 is merged.** Instrumented per-model totals exist and are queryable. **Choosing
  the source of truth for "instrumented totals" is THE design decision of this story** and
  belongs to the red phase — the candidates are:
  - **Server log aggregation** (the `narrator.sdk.usage`-style lines 91-1 generalizes
    across all callers) — the `/sq-llm-costs` Layer-1 approach, parseable but
    rotation-local-timestamped and string-fragile.
  - **An in-process counter** — 91-1's choke point increments per-model cost/token
    tallies in memory; cheap and exact but lost on restart and scoped to one process.
  - **An OTEL/Jaeger query** over the `llm.request` spans 91-1 emits — the Layer-2
    approach, but Jaeger's `limit` truncates by trace (SKILL.md warns: "never use it for
    absolute call counts").
  The red phase must pick one and justify it; the rest of the story (window definition,
  fixture shape, day-boundary handling) follows from that choice.
- **Admin API rate limits tolerate daily polls.** The detector runs at most ~daily
  (operator-triggered), well within the org usage/cost report rate limits; no
  high-frequency polling, no standing daemon hammering the endpoint.
