# Intent Router output slim — cut the latency by cutting the output

**Date:** 2026-06-20
**Author:** Architect (Naomi, design mode) + crew (party mode)
**Status:** Design — ready for implementation plan
**Scope:** `sidequest-server` only. No UI, no new architecture, no second LLM call.
**Related:** ADR-113 (intent router spine), ADR-123 (mechanical-engagement pipeline),
ADR-150 (`action_rewrite` onto the router), Epic 48 (local Qwen classifier),
`docs/superpowers/specs/2026-06-20-intent-router-clarify-loop-PARKED.md`.

May warrant a short ADR once landed (the output contract is an architectural seam);
filed as a spec to follow the brainstorming → plan flow.

---

## Problem

The Intent Router (`IntentRouter.decompose`, `sidequest/agents/intent_router.py`) runs
as a pre-narrator Haiku-via-SDK pass on every player turn and is taking **20–25s**,
stalling the whole turn behind it.

## Diagnosis (measured, not assumed)

Captured with `scenarios/latency_diag_82_9.yaml --span-jsonl` against the live server,
spans read back from Jaeger. The original hypothesis was retry/timeout/grind on
*ambiguous* intent. The data refutes that:

- **100% of the latency is inside the model call.** `latency_ms == sdk_latency_ms` on
  every turn (max gap 1ms). Zero retry/validation overhead.
- **`retry_count = 0` everywhere.** The retry/timeout path is not firing at all.
- **`llm.iteration = 1` on all 271 Haiku calls.** No agentic loop; `max_turns=4` is not
  looping. Each decompose is a single shot.
- **No correlation with confidence.** A `conf=0.95` turn takes ~20s; a `conf=0.2` turn
  takes ~13s. Ambiguity does not predict slowness.
- **0.94 correlation between latency and output tokens** (intent_router caller isolated,
  70 calls). Latency tracks how much JSON the model *generates*, ~10–20 ms/token,
  autoregressive.
- **Input is already cached.** Fresh `llm.input_tokens` ≈ 9; `cache_read` 34–85K (cheap,
  flat). State-summary slimming (ADR-110/126-10) already moved input off the hot path —
  the remaining cost is **output generation + the freshly-prefilled changed state**
  (`cache_write` 3–13K), not retrieval.

Latency distribution (`intent_router.decompose` span): **p50 ≈ 8.6s, p95 ≈ 18.4s,
max ≈ 26.6s.** Output tokens (real gameplay calls): **p50 ≈ 314, mean ≈ 458, max 1655.**

**Conclusion: the router is slow because it generates a large `DispatchPackage` on every
substantive turn — confident turns included. The fix is to make it emit less.**

## Root cause — the schema accreted output nothing reads

`DispatchPackage` (`sidequest/protocol/dispatch.py`) started (commit `46fa5beb`) as a
"Local DM decomposer": per-player subsystem dispatches. Over a year it accreted a
confidence gate (#500), a lethality contract, visibility tags on everything, the
`action_rewrite` move (#952, ADR-150), and a growing subsystem vocabulary. Each addition
is more tokens Haiku must generate, every turn, in series.

Tracing **production consumers** (not tests) shows large parts are emitted and never read:

| Field | Emitted | Read by | Verdict |
|---|---|---|---|
| `per_player[].resolved` — the whole Referent list (`token`/`resolved_to`/`confidence`/`alternatives`/`resolution_note` prose), `dispatch.py:101-115,204` | every pronoun, every turn | **nothing** — every `.resolved` hit in the tree is a different object (`encounter.resolved`, `movement.resolved`, …). Dispatches embed the resolved entity directly in `params` (e.g. `params["opponent"]["name"]`, prompt `intent_router.py:152`) | **DEAD** |
| `action_rewrite.you`, `dispatch.py:265` | every acting turn | **nothing** | **DEAD** |
| `per_player[].lethality` — `LethalityVerdict` with 3 prose fields (`cause`/`narrator_directive`/`soul_md_constraint`), `dispatch.py:186-193,206` | when applicable | `lethality_arbiter.py:89-92` **only** as a decomposer-only-entity fallback; the arbiter computes its own verdicts deterministically from HP=0 and wins on conflict | **near-dead fallback** |
| `VisibilityTag` on **every** dispatch + directive, `dispatch.py:80-93,131,165` | every dispatch/directive | redaction/SECRET_ROUTES (pre-narration) — but the server already hardcodes the common default `VisibilityTag(visible_to="all")` at `intent_router_pass.py:721`; asymmetric visibility is the rare exception | **defaultable** |

`confidence_global` (`dispatch.py:288`) is telemetry-only (it gates nothing today) and the
party flagged it as tax — but it is **kept**: it is ~5 tokens (not a latency lever), it is
live GM-panel telemetry on the `decompose` span, and it is the gating signal the parked
clarify-loop will trigger on. Cutting the future feature's trigger to save 5 tokens is a
bad trade.

We pay Haiku to autoregressively generate prose referent notes and prose lethality
verdicts on most turns, and throw them away.

## The async question — verified empty

Per the chosen "full sync/async tiering" scope, the load-bearing check is: **does any
field require model judgment, get consumed only *after* the narrator runs, and is it
unavailable pre-narration / not server-defaultable?** A full consumer trace says **no**:

- Every model-judgment field — `dispatch[]` + confidence, `narrator_instructions`,
  `action_rewrite`, visibility-for-secrets — is consumed **before** the narrator call
  (dispatch bank `subsystems/__init__.py:290-340`; directives rendered into the prompt
  `orchestrator.py:3090`; redaction `prompt_redaction.py:38-58`; the action_rewrite is
  copied into `NarrationTurnResult` *before* the narrator call and only read mechanically
  afterward at `narration_apply.py:3806`, `websocket_session_handler.py:2823`).
- Post-narration reads (perception fan-out, MP attribution, telemetry) are **mechanical**
  — extract/compare/route — never re-judged, and read the pre-narration copy.

**There is no field that justifies a deferred/parallel enrichment call.** Building a
second Haiku call would be speculative machinery (No-Stubbing / YAGNI). The "tiers"
therefore resolve to: **(1) model emits** (sync hot-path), **(2) server derives/defaults**
(zero model tokens), **(3) deleted** (unconsumed).

## Design

### The principle
The router's only narrator-blocking job is **making mechanical state real before the
narrator runs**. The output contract is exactly what is consumed pre-narration.

### New hot-path contract (what the model emits)
Ordered so the **narrator-critical fields generate first** — output is serial, so field
order *is* latency order; the load-bearing bytes come off the front of the call:

1. `per_player[]`: `player_id`, `dispatch[]` (`subsystem`, `params`, `confidence`,
   `idempotency_key`, `depends_on`), then `narrator_instructions[]` **only when non-empty**
2. `cross_player[]` dispatches
3. `action_rewrite`: **`named` + `intent` only** (kept last — read mechanically, not by the bank)
4. `raw_action`, `turn_id`

### Removed from the model's burden
| Change | Mechanism | Risk |
|---|---|---|
| Cut `resolved[]` entirely | dead; dispatches carry resolved names in `params` | none |
| Cut `action_rewrite.you` | dead | none |
| Cut `lethality[]` from the router | arbiter is authoritative + deterministic on HP=0 | **small behavior delta** — decomposer-only-entity narrative-death verdicts stop passing through. Approved 2026-06-20 |
| Make `VisibilityTag` **omittable** → server defaults `visible_to="all"`; model emits it only for genuine secrets | server already defaults it | low — redaction/SECRET_ROUTES still works when the model opts in |
| Drop `params` open-ended padding | tighten the prompt's per-subsystem param lists to "emit exactly these keys" (already partly stated `intent_router.py:148`) | none |

### System prompt rewrite (secondary win)
Remove the instructions for every cut field — the whole "Resolve referents" step 1, the
`action_rewrite.you` example, the "every dispatch carries a visibility tag" mandate, the
lethality contract. This also **shrinks the cached input prompt** (a cost win) and gives
Haiku less to satisfy, which itself tends to reduce output.

### Belt-and-suspenders safety check (why the lethality cut can't break death RP)
Death narration is driven by the **belt** — `LethalityArbiter.arbitrate()`
(`orchestrator.py:3061`), which on `core.hp.current == 0` calls `_emit()` and appends the
paired `must_narrate` / `must_not_narrate` directives (from `lethality_policy.yaml`) into
the narrator prompt (`orchestrator.py:3090`). That path reads HP + genre policy and **never
touches the router's `lethality[]` field.** The router field is the **suspenders**: the
arbiter's merge loop appends decomposer-only verdicts to `result.verdicts` *without*
calling `_emit`, so they carry **no directives** and don't steer the narrator. Cutting the
router field removes the suspenders; the belt (the mechanic that actually narrates death)
stays fully wired. See `2026-06-20-narrator-honors-mechanical-death-FOLLOWUP.md` for the
separate narrator-compliance follow-up.

### Preserved invariants
- Per-dispatch `confidence` still required, still gates `run_dispatch_bank`
  (`subsystems/__init__.py:340`).
- `CrossAction` witness-union, idempotency-key uniqueness, and the stringified-list
  coercion validators (`dispatch.py:220-397`) unchanged.
- Lethality arbiter's own HP=0 verdicts (`lethality_arbiter.py`) unchanged.
- Redaction firewall (ADR-104/105) intact — visibility still emittable for real secrets.

## Verification

1. **Latency win (the goal).** Re-run `latency_diag_82_9.yaml --span-jsonl`, read spans
   from Jaeger, diff `output_tokens` and `latency_ms` p50/p95/max against the 2026-06-20
   baseline (p50 314 tok / 8.6s; p95 ~18.4s; max 1655 tok / 26.6s). **Target: output p50
   roughly halved (~150 tok), latency p50 down to ~4–5s, and the 15–26s tail crushed**
   (the fat tail is where the prose-per-referent + per-item visibility objects pile up, so
   it should move most). Harness is proven.
2. **No behavior regression — use the lie-detector that already exists.** Run
   `latency_diag_82_9` plus a combat scenario (`combat_otel.yaml` / `combat_stress.yaml`)
   before and after; assert **zero new `dispatch_engagement.{subsystem}.mismatch` spans**
   and **identical dispatch counts**. Deliberately drive a pronoun-heavy turn to prove no
   downstream consumer missed the removed referent list. (Per CLAUDE.md "No Source-Text
   Wiring Tests" — assert on spans/behavior, not on schema source.)
3. **OTEL.** The `intent_router.decompose` span keeps emitting `latency_ms` /
   `sdk_latency_ms` / a token proxy so the GM panel verifies the win live.

## Why this matters beyond the 20 seconds

- **Governance.** This debt is a schema with no consumer gate. Adopt a doctrine line: **no
  field enters the `DispatchPackage` contract without a named production consumer.**
  Otherwise it re-bloats in a quarter.
- **Epic 48 on-ramp.** A slim output is one a local `qwen2.5:7b-instruct` on the M3 Ultra
  can fill *reliably* (the fat contract never could). The latency fix and getting
  classification off the paid API are the same move — and the slim contract is the
  precondition for the parked clarify-loop (which harvests local-router tuning data). See
  the PARKED note.

## Out of scope (deliberately)
- The clarify-loop (parked — quality + tuning, not latency).
- A second/async LLM call (verified unnecessary).
- Optional, defer to implementation: A/B the SDK's `output_format` structured-output path
  vs. a plain forced tool-call to see if constrained decoding adds latency on top of
  generation. Measure only; cheap.
