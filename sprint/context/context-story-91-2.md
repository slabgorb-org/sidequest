---
parent: context-epic-91.md
workflow: tdd
---

# Story 91-2: Attribute and fix the 8x/turn Haiku volume (caller tags from 91-1; fix retries/fan-out or document budget with per-turn assertion)

## Business Context

The 2026-06-05 cost forensics (pingpong **[COST-1]**, see `context-epic-91.md` Background)
measured the Haiku 4.5 tier at **~575 calls on Jun 4 against ~70 game turns — roughly 8
calls/turn**, where the design expectation is ~1 (the Intent Router classification pass)
plus rare asides. At Haiku's uncached per-call shape (~5.2k input tokens, matching the
router prefix+turn shape), that excess is **~$2.5–3/day of potentially pure waste** — and on
a project where per-turn unit economics make or break the business model (operator, P1),
that is a load-bearing leak, not rounding error.

But the multiplier is also an **agency/correctness smell**. The Intent Router is the
mechanical-engagement spine (ADR-113): it classifies each player action into a
`DispatchPackage` that fires the confrontation/magic/movement/etc. engines *before* the
narrator runs. If classification is firing 8× per turn, either (a) something is re-running
the whole pre-narrator pass several times per player action, (b) the bounded retry is
storming, or (c) legitimate fan-out (e.g. MP per-player) is happening but undocumented and
unbounded. Each of those is a different bug with a different fix, and **we do not yet know
which** — the epic's forensics could see the *volume* but not *attribute* it, because
current OTEL undercounts Haiku badly (only 41 `llm.request` spans captured in 72h against
~6.4M billed tokens). This story closes that gap: read 91-1's per-call caller tags, name the
caller, and either fix it or prove the fan-out is legitimate and fence it with a budget.

This is the OTEL Observability Principle applied to money: an unattributed 8× multiplier is
exactly the kind of "Claude winging it" the GM panel exists to catch — except here the
subsystem winging it is *us*, calling the API more than the turn requires.

## Technical Guardrails

**EVIDENCE-DRIVEN — do not guess.** This story is explicitly sequenced *after* 91-1
(`context-story-91-1.md`) lands the per-call caller tags (`llm.caller` ∈ {`narrator`,
`intent_router`, `aside`, `dungeon_curate`}) on the `llm.request` span and the uniform
`*.sdk.usage` log line. The correct order is: **(1)** confirm 91-1 is merged and the caller
tag is live; **(2)** run one playtest (`just playtest` / `just playtest-scenario`); **(3)**
read the per-turn attribution (group `llm.request` spans by `llm.caller` and by turn id);
**(4)** *then* fix. Do not pre-commit to a root cause from the candidates below — they are
where to *look*, not what to conclude.

**Candidate invocation sites found in code (where a single player action can fan out into
multiple Haiku `decompose` calls):**

- The router fires **once per `_execute_narration_turn`**, via
  `intent_router_pass.build_intent_router_for_session()` →
  `execute_intent_router_pre_narrator_pass(...)` →
  `IntentRouter.decompose(...)` → one `_IntentRouterLlm.emit_tool` SDK round-trip
  (`websocket_session_handler.py:852,879`; `intent_router.py:329`;
  `llm_factory.py:203` `_IntentRouterLlm.emit_tool`, model `_INTENT_ROUTER_MODEL =
  "claude-haiku-4-5-20251001"`).
- **`_execute_narration_turn` has MANY callers** (`grep` shows the same private method
  re-entered from several handlers), so "once per turn execution" ≠ "once per player turn":
  - `handlers/player_action.py:225` and `:643` — the normal submit path.
  - `handlers/dice_throw.py:263` and `:413` — **the dice-resolution replay path (ADR-074)**.
    After a player rolls, the dice handler builds a `replay_text` (e.g.
    `[DOGFIGHT_SHOT_RESOLVED] ...`, `dice_throw.py:255`) and **re-enters
    `_execute_narration_turn`**, which re-runs the full pre-narrator pass — i.e. a *second*
    Haiku classification call for the same player action whose only new input is a dice
    outcome the router does not need to classify. An action that triggers a roll therefore
    costs at least 2 router calls; a confrontation with multiple roll exchanges multiplies
    further.
- **The bounded retry** (`intent_router.py:50` `_MAX_TOTAL_ATTEMPTS = 2`; loop at
  `:322`): every `decompose` is first-attempt + one retry on
  timeout/transport/empty-response/schema-invalid. A deterministic schema confusion (the
  router emitting a stray `narrator_instructions` key — the failure mode `:242`
  `_schema_correction_suffix` exists to fix) doubles the call count for that turn. If
  schema rejections are frequent on the current prompt, the retry is a steady 2× floor.
- **The degrade path** (`websocket_session_handler.py:892–928`) does NOT add a call — it
  emits a synthetic `intent_router.decompose` *span* with no SDK round-trip — but note it
  when reading span counts so you do not double-count a span as a call.
- MP/per-player fan-out: the live decompose pass is documented **single-submitter**
  (`intent_router_pass.py:238` `_normalize_per_player_ids` — `player_name` is THE acting
  character), so the router is NOT currently looped per seat. Verify this holds under a real
  MP playtest before ruling it out.

**Candidate commits from the Jun 2–3 jump** (epic flagged uncached Haiku 525k→713k→3.16M
tokens/day Jun 1→2→3; `git log` in `sidequest-server` for that window shows several commits
that *expanded what the router does or how often it is triggered*):

- `a786f6d1` (Jun 3) **feat(59-27): route verbal/social intent verbs to the Intent Router** —
  re-added per-type `intent_verbs` to the `confrontation_types` projection
  (`intent_router_pass.py:163–193`), enlarging the prompt AND making more action shapes route
  to a confrontation dispatch. Grows per-call tokens; could also grow retry/empty-response
  rates.
- `e4a80f1b` (Jun 2) **feat(wry_whimsy): intent-router witnessed_act classification** +
  `e6418988` (Jun 2) **fix(59-28): touched-this-turn guard** — added the
  `witnessed_act_vocabulary` + `present_npcs` projection (`intent_router_pass.py:201–217`),
  another prompt-size and trigger-surface expansion on political worlds.
- `6dded559` (Jun 2) **feat(equip): honor natural-language equip intent via IntentRouter** —
  added the `equip` subsystem to the router's classifiable surface (system prompt
  `intent_router.py:182`), widening what every action is checked against.
- `db31bcd9` (Jun 4) **feat(59-30): witnesses engagement — witnessed_act + movement** and the
  `1f1ba4b4`/`13b3585f` OTEL turn-attribution fixes — relevant to *reading* the spans
  correctly, less likely to be the volume driver.

These commits all grow per-call **token size** and **trigger surface**; none of them *by
inspection* obviously multiplies the **call count** — which is why the dice-replay re-entry
and the retry loop are the stronger structural suspects for the *count* multiplier. Confirm
against attribution data, not this list.

**Fixes must not silently drop needed calls (No Silent Fallbacks).** If a call is genuinely
required — the dice replay legitimately needs a fresh narration turn, a schema retry
legitimately rescues a turn's dispatch, an MP scenario legitimately needs per-seat
classification — then the right move is **not** to delete the call but to (a) make the
*router* skip on the replay re-entry if classification is redundant (the dice outcome adds no
new player intent to classify), or (b) document the legitimate fan-out and add a **per-turn
call-budget assertion** with a loud OTEL breach event. Never paper over a needed call to make
the number look right.

## Scope Boundaries

**In scope:**
- **Attribution analysis** from 91-1 telemetry: group `llm.request` spans (and the uniform
  `*.sdk.usage` log lines) by `llm.caller` and by turn id; quantify calls-per-turn for the
  `intent_router` caller; identify which invocation site(s) and/or retries produce the
  multiplier; record the evidence in the session.
- **Either** a root-cause fix that brings `intent_router` calls/turn down to the expected
  ratio (e.g. suppress the redundant router run on the dice-replay re-entry of
  `_execute_narration_turn`; tame a retry storm) **OR**, where the fan-out is legitimate, a
  **documented per-turn budget** plus a fail-loud/OTEL **assertion** that the per-turn Haiku
  classification call count stays within it.
- An **OTEL event on budget breach** (the GM-panel lie-detector), and a regression
  test/assertion that would catch a future 8× recurrence.

**Out of scope:**
- The choke point / caller-tag instrumentation itself — that is **91-1** (this story
  *consumes* its tags, does not build them).
- Repairing the dead Intent Router cache / the 4,096-token Haiku floor guard — **91-3**.
- Reducing per-call token size as a cost play, except insofar as a fix incidentally trims the
  prompt (the *count* is this story's target, not the *size*).
- Local-model classification routing — **epic 92** (sibling local-classification epic).
- Cross-model runaway detector (**91-4**) and daily Admin-API reconciliation (**91-5**).

## AC Context

Derive testable ACs from the title. The server's **"Every Test Suite Needs a Wiring Test"**
rule and its corollary **"No Source-Text Wiring Tests"** are in force — do not grep
production source as an assertion; drive the real path and assert on OTEL spans / emitted
behavior.

1. **Attribution evidence recorded in the session.** The analysis names *which caller*
   (expected: `intent_router`) drives the multiplier, *what the multiplier is* on a current
   playtest (calls/turn), and *the structural source* (e.g. "dice-replay re-entry runs the
   pre-narrator pass a second time" and/or "schema-retry rate is N%"). Captured as concrete
   measured numbers, not prose assertion — the epic's whole premise is "do not guess."
2. **Post-fix playtest shows expected ratio or documented budget.** After the fix (or the
   documented-budget decision), a fresh playtest shows `intent_router` Haiku calls/turn at
   the expected ~1 (+ legitimate, documented extras), verified by grouping `llm.request`
   spans by `llm.caller` and turn id — the *same* attribution method as AC1, now showing the
   improvement.
3. **Regression test/assertion that would catch a future 8× recurrence.** A behavior test
   (fixture-driven or OTEL-span-driven, per the server's wiring-test doctrine) that drives a
   representative turn through the real handler path and asserts the per-turn Haiku
   classification call count is within budget — and would **fail** if a future change
   re-introduced the multiplier (e.g. re-added the redundant dice-replay router run). Prefer
   asserting on spans emitted (count of `intent_router` `llm.request` spans for the turn) or
   a counter, not on source text.
4. **OTEL event on budget breach.** When the per-turn classification call count exceeds the
   documented/expected budget, a loud OTEL event fires (e.g.
   `intent_router.call_budget.breach`) carrying the turn id, the observed count, and the
   budget — so the GM panel surfaces a recurrence in production, not just in CI (OTEL
   Observability Principle / GM-panel lie-detector). Emit into the existing telemetry infra
   (ADR-103/132); do not reinvent.

## Assumptions

- **91-1 merged first.** This story cannot start until the `llm.caller` tag and uniform
  usage log line are live on every Anthropic call — 91-1 is the hard dependency and is itself
  the keystone of the epic. If 91-1 is not merged, stop and surface that.
- **The multiplier is reproducible in a current playtest.** The Jun-4 ~8×/turn figure is
  expected to reproduce on the current build (the suspect commits all landed by Jun 4 and are
  on `develop`); the fix is validated by re-running the *same* playtest and re-reading
  attribution. If the multiplier does NOT reproduce, that itself is evidence (something
  already changed) and must be recorded, not assumed away.
- **Current OTEL alone cannot answer this.** Jaeger captured only 41 Haiku
  `llm.request` spans in 72h (trace-limit/sampling undercount) against ~6.4M billed Haiku
  tokens — the Intent Router's existing `intent_router_decompose_span` and the
  `_IntentRouterLlm` `llm_request_span` exist but are sampled away in aggregate. 91-1's
  uniform per-call instrumentation (and reading it locally during a controlled playtest
  rather than from sampled Jaeger aggregates) is what makes attribution possible.
- **The dice-replay re-entry is a strong structural suspect but not confirmed.** The code
  shows `dice_throw.py` re-enters `_execute_narration_turn` (and thus the router) on roll
  resolution; whether that accounts for the bulk of the 8× — versus retry storms, versus the
  Jun 2–3 prompt-surface growth raising empty-response/schema-retry rates — is exactly what
  the attribution pass must settle before any fix lands.
