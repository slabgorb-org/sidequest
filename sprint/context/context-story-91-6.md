---
story: 91-6
title: "Gate narrator.cache.both_writes_fired WARNING on cache_read>0 (cold-start dual writes are unavoidable, not a pathology)"
epic: 91
parent: context-epic-91.md
workflow: trivial
type: chore
points: 1
repo: sidequest-server
status: ready
---

# Story 91-6 — Gate `narrator.cache.both_writes_fired` WARNING on `cache_read>0`

## Business Context

`narrator.cache.both_writes_fired` is the regression tripwire for the May 25–30 "1h-churn"
pathology: every warm narrator call was re-minting the stable-prefix 1h cache tier and
re-billing it at the 1h write rate (~$6/M), instead of reading it back. That was fixed on
May 31 (warm 1h re-writes dropped from ~92/day to ~0–4/day, per epic-91 "What is healthy").
The WARNING exists so that if stable-prefix churn ever silently returns, the GM panel lights
up loud before the bill does.

But as written, the warning fires on `cache_write_5m > 0 and cache_write_1h > 0` with no
regard for whether the call is cold or warm. On 2026-06-05 it fired 8 times: **7 were
iter=1 cold starts** where both tiers *must* populate (the prefix is being minted for the
first time — there is nothing to read back), and only **1 was a genuine warm re-write**.
A tripwire that cries wolf on every cold start trains the operator to ignore it — and an
ignored tripwire protects nothing. This story makes the warning fire only when the
pathology it names is actually present.

## Technical Guardrails

- **Keep the warning's purpose intact.** The thing worth screaming about is a *warm* call
  re-writing the 1h stable-prefix tier — stable-prefix churn. That case must stay loud
  (`severity="warn"`, `logger.warning`).
- **Gate on `cache_read > 0`.** A cold start has `cache_read == 0` (nothing cached yet), so
  dual writes are unavoidable and expected — not waste. The warm/pathological case has
  `cache_read > 0` (the read-back is happening) *and* `cache_write_1h > 0` (yet the 1h tier
  is being re-minted anyway). That conjunction is the real signal.
- **Prefer downgrade over deletion for the cold case.** Per the OTEL Observability Principle,
  don't go dark on cold-start dual writes — emit them at DEBUG/INFO (log and/or a non-`warn`
  watcher severity) so the panel can still see them, just without the false alarm. Deleting
  the cold-path emit entirely is acceptable only if the existing `narrator.sdk.usage` event
  already captures the same `5m`/`1h` write split (it does — see lines ~501–513); prefer the
  explicit downgrade.
- **Logging only — touch no cache behavior.** Do not change marker placement, tier split,
  cost math, or the usage-line shape. This is a `severity`/log-level decision plus a guard
  condition. All four fields (`cache_read`, `cache_write_5m`, `cache_write_1h`, `iteration`)
  are already in scope at the emit site (`anthropic_sdk_client.py` ~line 530).

## Scope Boundaries

**In scope:**
- The gating condition on the `both_writes_fired` emit (add the `cache_read > 0` predicate).
- The log-level / `severity` decision for the cold-start case (DEBUG/INFO downgrade vs. fold
  into existing `narrator.sdk.usage`).
- Updating existing tests that reference the warning, plus one new test per case.

**Out of scope:**
- Anything touching cache tiers, marker placement, the 5m/1h split, or `compute_cost_usd`.
- The `narrator.sdk.usage` usage-line *format* — **91-1 owns usage-line/format changes**;
  do not modify its field shape here.
- The cost-runaway detector (`_maybe_emit_cost_runaway`), 91-4's territory.

## AC Context

1. **Cold start emits no warning.** An iter=1 cold-start response (`cache_read == 0`, both
   `cache_write_5m > 0` and `cache_write_1h > 0`) produces **no** `warn`-severity
   `narrator.cache.both_writes_fired` event and **no** `logger.warning`. At most it emits an
   INFO/DEBUG observation.
2. **Warm pathology still WARNs.** A warm response (`cache_read > 0`) with `cache_write_1h > 0`
   still fires the `warn`-severity watcher event and `logger.warning` — the genuine
   stable-prefix-churn pathology stays loud. This is the regression the May-31 fix closed;
   the tripwire must keep guarding it.
3. **Tests updated, one per case.** Existing tests asserting on the warning are reconciled
   with the new gate, and the suite includes at least one test for the cold-start (no-warn)
   case and one for the warm (warn) case. Assert on the emitted watcher event / log record,
   not on source text (per the No Source-Text Wiring Tests rule).

## Assumptions

- The warm/cold distinction is fully determined by `cache_read > 0` on the *same* response
  `usage` object that yields `cache_write_5m` / `cache_write_1h`. **Verified in the read:**
  at the emit site (`anthropic_sdk_client.py` ~line 530) `cache_read` is assigned at line 421
  from `usage.cache_read_input_tokens`, and `cache_write_5m` / `cache_write_1h` at lines
  ~429/434 from the same `usage` — all three plus `iteration` are in local scope. **No
  plumbing is required**; the guard is a single added predicate.
- "Cold start" is operationally just `cache_read == 0` (first mint of the prefix); the story
  does not need to inspect `iteration` to make the call, though iter=1 is the typical cold
  case and remains a useful field to keep in the (downgraded) event payload.
