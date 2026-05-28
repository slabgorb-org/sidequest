---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-11: Retire the orchestrator's redundant second dispatch-bank run

## ⚠️ Staleness Check

**Verified 2026-05-28 — the story is LIVE and accurate. Both `run_dispatch_bank` call sites still exist exactly as the description claims** (line numbers drifted by a few rows; corrected below).

| Call site | Description says | Actual (verified) |
|-----------|------------------|-------------------|
| Pass 1 (canonical engagement) | `intent_router_pass.py:158` | `run_dispatch_bank(...)` at `intent_router_pass.py:161`, inside `execute_intent_router_pre_narrator_pass` (def at `:125`). Full context: `snapshot`, `pack`, `player_name`, `npcs_present`, `additional_player_names` (+ `dungeon_store`/`palette`/`lookahead_handle` for movement) — `intent_router_pass.py:163-176`. |
| Pass 2 (redundant directive re-run) | `orchestrator.py:2538` | `run_dispatch_bank(...)` at `orchestrator.py:2562`, guarded by `if visible_dispatch_package is not None:` at `:2548`. Crippled `bank_context: dict = {"npc_pool": list(context.npc_pool or [])}` at `:2557-2559`. |
| Lethality arbiter consuming pass-2 result | `orchestrator.py:2554` | `LethalityArbiter(...).arbitrate(package=visible_dispatch_package, bank_result=bank_result, ...)` at `orchestrator.py:2579-2584`. |

**The crippling mechanism is confirmed real.** `bank_context` carries only `npc_pool`. The bank's `_filter_context_for_callable` (`subsystems/__init__.py:57`) forwards a context key only if the handler declares it AND it is present in context. Stateful handlers declare kw-only params with **no default** — e.g. `run_confrontation_dispatch(dispatch, *, snapshot, pack, player_name, ...)` (`subsystems/confrontation.py:49-57`); `run_magic_working_dispatch` and `run_scenario_clue_dispatch` are the same shape. With `snapshot`/`pack`/`player_name` absent from `bank_context`, the filter returns `{}`, so `fn(d)` raises `TypeError: missing required keyword-only argument 'snapshot'`. The bank catches it (`subsystems/__init__.py:259-268`), records `result.errors` and sets the subsystem span's `error` attribute — **non-fatal**, exactly as PR #448 (`23a44a13`, "watcher must not crash WS turn-delivery") arranged. The TypeError rows pollute the GM-panel Subsystems tab.

This is genuinely a pre-59-4 leftover. The canonical engagement moved into `intent_router_pass.py` at 59-4 (`e4a3a297`); this older directive-collection re-run in the orchestrator was never retired.

## Business Context

The Intent Router spine (ADR-113, epic 59) exists to make mechanics *real before the narrator runs* so the GM panel is a reliable lie-detector — it shows whether a subsystem actually engaged versus the narrator improvising. That promise is undermined when the **same `run_dispatch_bank` runs twice per turn** and the second run emits spurious `TypeError` error rows for every stateful subsystem. A GM (Keith) scanning the Subsystems tab can no longer trust that a red row means a real engagement failure — it might just be this known-broken second pass. The OTEL observability principle (CLAUDE.md) is specifically about keeping that panel honest; this story restores that signal.

There is also a latent trap. The "obvious" fix — hand the orchestrator the full canonical context so the second run stops raising — would cause every stateful subsystem (confrontation, magic, scenario_clue, movement) to **engage a second time**: a double-instantiated encounter, a double-applied magic working, double-consumed clue facts. The description bans that papering explicitly. The correct outcome is **engage once (pass 1), collect narrator-visible directives without re-exercising side-effecting subsystems.**

This is engineering hygiene, not a product decision — Dev flagged it during the 2026-05-25 confrontation-engagement fix (PR #448) and Keith confirmed it is engineering-only.

## Technical Guardrails

**The single-engagement invariant.** Pass 1 (`intent_router_pass.py:161`) is the canonical, side-effecting engagement and must remain the *only* one. The fix must make the orchestrator's directive/arbiter needs (currently served by pass 2) be met **without** invoking any stateful subsystem a second time.

**What the orchestrator actually needs from pass 2 (and only this):**
1. The aggregated `narrator_directives` block it registers as a Recency-zone `PromptSection` (`orchestrator.py:2588-2599`). Those directives come from `bank_result.directives`, which is the concatenation of each subsystem's `SubsystemOutput.directives` plus each `PlayerDispatch.narrator_instructions` (`subsystems/__init__.py:272, 280-281`).
2. A `BankResult` to feed `LethalityArbiter.arbitrate(bank_result=...)` (`orchestrator.py:2581`).

**Critical nuance on the arbiter (firewall, ADR-104/105).** The current `LethalityArbiter.arbitrate` (`lethality_arbiter.py:57-94`) does **not read `bank_result` at all** — its verdicts are derived from `pc_cores_by_player`/`npc_cores_by_name` HP (`lethality_arbiter.py:70-85`); `bank_result` is a declared-but-unused parameter (docstring: "for future subsystems that emit `data['fatal_hit']` etc.", `lethality_arbiter.py:10-11`). So today swapping which `BankResult` the arbiter sees has **no behavioral effect**. Do not rely on that staying true — design the fix so that *if* the arbiter starts consuming `bank_result.data`, the data it sees is the redacted/narrator-safe view, never canonical-only material. Cross-check 59-9.

**Two design approaches to weigh (do NOT pre-decide — this is for the design phase):**

- **(A) Thread pass-1's `BankResult` through `turn_context` and redact the resulting directives per-entry.** Pass 1 already produces a `BankResult` (`intent_router_pass.py:161`) but currently discards it after the `package` is returned (`:188`); only the *package* survives to `turn_context.dispatch_package` (`websocket_session_handler.py:775`). Approach A would also carry the `BankResult`, then drop directives whose `VisibilityTag.redact_from_narrator_canonical` is set (`protocol/dispatch.py:58`, `112-115`). Note: `redact_dispatch_package` (`prompt_redaction.py:26`) today redacts at the *package* (dispatch + `narrator_instructions`) level, not at the *bank-produced directive* level — directives synthesized inside subsystem handlers (e.g. the arbiter's paired must/must-not, `lethality_arbiter.py:120-133`) would need an equivalent per-directive redaction pass.
- **(B) A directive-collection-only mode of `run_dispatch_bank`** that walks the package and gathers `narrator_instructions` / authored directives **without invoking the registered subsystem callables** (skip the `fn(d, **fn_kwargs)` call at `subsystems/__init__.py:258`). This sidesteps the context problem entirely because no stateful handler runs.

**OTEL discipline (CLAUDE.md OTEL principle, ADR-031/103).** After the change, `intent_router.dispatch_bank` (`telemetry/spans/intent_router.py:71`, documented "once per `run_dispatch_bank` invocation", `:17-18`) and `intent_router.subsystem` (`:82`, the `subsystem_exercise_summary` event, `:19-21`) must each fire **exactly once per turn**. They currently fire twice (once in pass 1, once in pass 2). The validator's `subsystem_exercise_check` (`telemetry/validator.py:308`) consumes the `subsystem_exercise_summary` event — verify it does not start mis-counting after the change.

**No-source-text-wiring-test rule (server CLAUDE.md).** Do not assert "the second `run_dispatch_bank` literal is gone" by grepping `orchestrator.py`. Prove the invariant with an **OTEL span count assertion** (drive a turn, assert `intent_router.subsystem` fired N times = the pass-1 dispatch count, not 2N) and a **behavioral double-dispatch test** (drive a confrontation-shaped turn end-to-end, assert exactly one encounter is instantiated, not two).

## Scope Boundaries

**In scope:**
- Retire the second, redundant `run_dispatch_bank` invocation at `orchestrator.py:2562` and its crippled `bank_context` (`:2557-2559`).
- Provide the orchestrator's `narrator_directives` block (`:2588-2599`) and the arbiter's `bank_result` input (`:2581`) via a non-side-effecting path (approach A or B).
- Per-directive redaction of narrator-visible directives so the firewall is honored without a second engagement.
- Update/verify OTEL: `intent_router.dispatch_bank` + `intent_router.subsystem` fire exactly once per turn.

**Out of scope:**
- Changing pass-1 engagement semantics (`intent_router_pass.py`) — it stays the single source of truth.
- Reworking which signals the `LethalityArbiter` consumes (it currently ignores `bank_result`; that is 59-9 / a future story's concern, not this one). Just don't break it and don't leak.
- New subsystem handlers or dispatch vocabulary (59-5/6/7 territory).
- Any "fix" that hands the orchestrator full canonical context to silence the TypeError — **explicitly banned** (re-engagement trap).
- UI/GM-panel rendering changes (the spurious rows disappear at the source once the second run is retired).

**Explicitly banned (from the story):** papering the TypeError by supplying `snapshot`/`pack`/`player_name` to `bank_context`.

## AC Context

**AC1 — Single-engagement invariant (spans fire once per turn).**
Drive a turn whose router pass produces ≥1 subsystem dispatch through the real pipeline (orchestrator → narrator-prompt assembly). Assert `intent_router.dispatch_bank` fires **exactly once** and `intent_router.subsystem` fires exactly the pass-1 dispatch count — not twice / 2×. This is the OTEL proof, refactor-stable per the server's no-source-text-wiring rule. Reference span defs: `telemetry/spans/intent_router.py:71, 82`.

**AC2 — No double-dispatch (behavioral).**
Drive a confrontation-shaped action end-to-end against a real pack (per memory `project_opposed_check_wiring_trap`, exercise a real engagement path, not a synthetic fixture that no-ops). Assert exactly **one** `StructuredEncounter` is instantiated — pass 1's. Before this story, the second run would re-instantiate if anyone "fixed" the context; after, the second run must not run stateful handlers at all. Equivalent guard for at least one other stateful subsystem (magic or scenario_clue) confirming a single side effect.

**AC3 — No firewall leak through the arbiter (ADR-104/105).**
The arbiter must receive a narrator-safe `BankResult`. Construct a package containing a dispatch/directive tagged `redact_from_narrator_canonical=True` (`protocol/dispatch.py:58`). Assert the directives that reach the narrator `narrator_directives` section (`orchestrator.py:2591-2599`) and the `bank_result` the arbiter sees (`:2581`) contain **no** redacted-only payload. Because the arbiter today ignores `bank_result` (`lethality_arbiter.py:57-94`), this AC also guards the *future* case: the data path must already be redacted so a later arbiter change can't leak. Cross-check 59-9.

**AC4 — Clean Subsystems tab (no spurious TypeError rows).**
After the change, drive a turn with stateful dispatches and assert **zero** `intent_router.subsystem` spans carry an `error` attribute sourced from the missing-context `TypeError` (`subsystems/__init__.py:267`). Equivalently, assert `BankResult.errors` from the (now-removed) second pass no longer exists / is empty. This is the GM-panel-honesty payoff: a red Subsystems row again means a real engagement failure.

**Wiring test (required per server CLAUDE.md).** At least one test must drive the full turn pipeline (the orchestrator's narrator-prompt assembly path that reads `context.dispatch_package`, `orchestrator.py:1622`) — not a unit test of the directive collector in isolation — and assert both the single-fire span count (AC1) and the single side effect (AC2) hold through the real call path.

## Assumptions

- Pass 1 (`execute_intent_router_pre_narrator_pass`) remains the canonical engagement and is unchanged by this story.
- `turn_context.dispatch_package` is pass-1's `DispatchPackage` (`websocket_session_handler.py:775`); the orchestrator reads it at `orchestrator.py:1622` and redacts it into `visible_dispatch_package` (`:1623-1626`). Approach A would additionally thread pass-1's `BankResult` alongside it.
- The `LethalityArbiter` continues to ignore `bank_result` for now (`lethality_arbiter.py:57-94`); this story must not regress that and must keep the data path narrator-safe for when it changes.
- PR #448 (`23a44a13`) already made the second pass non-fatal; this story removes the noise at its source rather than further hardening the swallow.
- "Solo"/single-player turns still produce a package; the single-fire invariant is asserted on a turn that actually dispatches a stateful subsystem.
