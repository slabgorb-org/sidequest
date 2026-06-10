---
story_id: "97-5"
jira_key: ""
epic: "97"
workflow: "tdd"
---
# Story 97-5: Turn-1 double-apply of _apply_npc_mentions — narrator.cache.both_writes_fired root cause

## Story Details
- **ID:** 97-5
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T07:24:08Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T00:00:00Z | 2026-06-10T06:41:17Z | 6h 41m |
| red | 2026-06-10T06:41:17Z | 2026-06-10T07:07:32Z | 26m 15s |
| green | 2026-06-10T07:07:32Z | 2026-06-10T07:19:49Z | 12m 17s |
| review | 2026-06-10T07:19:49Z | 2026-06-10T07:24:08Z | 4m 19s |
| finish | 2026-06-10T07:24:08Z | - | - |

## Sm Assessment

**Story:** Root-cause + fix a turn-1 double-apply of `_apply_npc_mentions`. Measured in the blackthorn solo 2026-06-07 turn 1: two byte-identical disposition beats per NPC, i.e. two `_apply_npc_mentions` passes in a single narration turn. Server #742's `Npc.last_development_turn` dedupe made the *development* seam harmless, but the upstream double-apply is unexplained and presumably double-runs every other per-mention side effect (last_seen updates, pool matching, mint paths). Cross-referenced to the unfiled `narrator.cache.both_writes_fired` WARN on the ping-pong watch list.

**Scope:** server only. One repo, one subsystem (narrator mention-application path). 2pt, p2.

**Approach for TEA/Dev (routing note, not implementation):**
- This is a measure-first bug. RED should reproduce the double-call, not assume the mechanism. Per `[[feedback_measure_dont_assert]]`: instrument the real call path, count `_apply_npc_mentions` invocations per turn, prove it fires twice before theorizing why.
- Likely candidate: the narration-apply path runs mention-application in two places (e.g. both a streaming/accumulation pass and a finalize pass), or the `both_writes_fired` cache warn signals a duplicate tool/write fan-out. Confirm against the running code, don't guess.
- AC1 allows the second pass to be load-bearing-and-documented as an alternative to elimination — so the test must distinguish "harmful duplicate" from "intentional second pass." Don't delete blindly.
- Consider whether the #742 seam-level dedupe (`last_development_turn`) becomes dead once the source is fixed; flag for removal in the same PR per `[[feedback_dead_code]]` if so.

**Gate checks:** session ✓, context ✓ (`sprint/context/context-story-97-5.md`), branch ✓ (`feat/97-5-turn1-double-apply-npc-mentions` on sidequest-server develop). Jira intentionally skipped — personal project.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (red phase) findings — 2026-06-10

- **[Gap — the story, ROOT-CAUSED & measured]** The upstream double-apply is the **dice-resolution replay re-entry**. A dice-gated action runs `_execute_narration_turn` twice in one interaction turn: pass 1 = player action (router + apply), pass 2 = `dice_throw.py` re-enters with `[BEAT_RESOLVED]`/`[DOGFIGHT_SHOT_RESOLVED]` replay text and `suppress_intent_router=True`. Story 91-2 ("Dark Spend") gave the **intent router** a replay guard but the **mention-apply** at `websocket_session_handler.py:1094` (`_apply_narration_result_to_snapshot` → `_apply_npc_mentions` at `narration_apply.py:4546`) was never guarded → every per-mention side effect double-runs on the replay. Confirmed by RED test (the replay pass fires `_apply_npc_mentions` once; should be zero). This is the only production path that double-enters `_execute_narration_turn`.

- **[Gap — FIX LOCATION for Dev]** Apply the 91-2 doctrine to the apply: gate the `_apply_npc_mentions` call (or the mention step inside `_apply_narration_result_to_snapshot`) on the replay condition. The `suppress_intent_router` flag already flows into `_execute_narration_turn` and is the replay signal — thread it to the apply (or derive a sibling `is_dice_replay`). **OTEL (CLAUDE.md principle):** emit a span when the replay mention-apply is suppressed — same lie-detector pattern as `intent_router.replay_suppressed` (Story 91-2) — so the GM panel distinguishes "intentionally skipped (replay)" from "apply dark". Never a silent skip.

- **[Question — AC1 branch chosen]** AC1 allows "second pass is load-bearing and documented" as an alternative to elimination. I chose **elimination** (suppress the replay apply): the replay carries no new player intent (91-2), and a narrator introducing a NEW NPC during a dice-resolution replay is exactly the improvisation the gaslighting/materialization doctrine distrusts. The control test pins that normal turns still apply once. If Dev/Reviewer disagree and keep the second pass, the RED test's assertion must flip to a per-turn-idempotence invariant instead — flagging so it's a conscious decision, not a silent reinterpretation.

- **[Improvement — dead-code candidate, `feedback_dead_code`]** Once the replay apply is suppressed, the #742 across-call dedupe (`Npc.last_development_turn` / `NpcPoolMember.last_development_turn`) is dead for its stated purpose (no production path applies twice in one turn anymore). Its sibling test `tests/server/test_npc_development_pipeline.py::test_same_turn_double_apply_develops_once` drives two synthetic `_engage` calls in one turn and would need to change if the dedupe is removed. **Recommendation:** keep it as defense-in-depth (cheap, idempotent, guards future re-entry paths) OR remove both in the same PR — Dev/Reviewer call. Do NOT leave it half-removed.

- **[Improvement — AC2 `both_writes_fired`: EXPLAINED, no code change]** `narrator.cache.both_writes_fired` (`anthropic_sdk_client.py:493`) is **cache-tier accounting**: it fires when a single narrator SDK iteration writes BOTH the 5m and 1h prefix-cache tiers while the prefix is being read back (`cache_read > 0`). Already gated to WARN-only on warm reads (cold-start dual-mint downgrades to info) by Story 91-6 / #709, and behaviorally covered by `tests/agents/test_60_7_iter1_cache_marker.py`. It is **orthogonal** to the mention double-apply — a *cache* subsystem, not the mention seam. The blackthorn turn-1 co-occurrence is circumstantial (turn 1 is the cold→warm cache transition). Suppressing the replay mention-apply does NOT silence it (the replay narrator call still runs by design, 91-2). AC2 resolves as **explained**; no new test. The dice-replay re-entry does fire a second narrator call per logical turn, which is the structural reason both tiers can re-write — but that is a cache-strategy concern in epic-91 territory, not this story's fix.

### Dev (implementation) findings — 2026-06-10

- **Improvement** (non-blocking): The reprompt-loop re-apply shares `_apply_kwargs` with the first apply (spec 2026-05-20 step 7), so it inherits `is_dice_replay` automatically — verified by reading the call site. No second wiring needed. Affects `sidequest/server/websocket_session_handler.py` (no change required; noted so Reviewer doesn't flag a missing thread). *Found by Dev during implementation.*
- **Question** (non-blocking): AC2 (`both_writes_fired`) resolves as **explained** per TEA's analysis — a cache-tier concern orthogonal to this seam, no code change. This PR does not touch it. Affects `sidequest/agents/anthropic_sdk_client.py:493` (epic-91 cache-strategy territory if ever revisited). *Found by Dev during implementation.*

### Reviewer (code review) findings — 2026-06-10

- No upstream findings. The fix is self-contained to the narrator mention-application seam; AC2 was correctly resolved as "explained" with no code change required. Confirmed `suppress_intent_router=True` originates only from the two `dice_throw.py` replay re-entries, so no other subsystem is affected by the `is_dice_replay` equivalence. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gated the whole NPC-mention sub-block, not only `_apply_npc_mentions`**
  - Spec source: context-story-97-5.md AC1 + TEA RED Gap "FIX LOCATION"
  - Spec text: "Gate the `_apply_npc_mentions` call (or the mention step inside `_apply_narration_result_to_snapshot`) on the replay condition."
  - Implementation: Wrapped the cohesive mention sub-block — `_apply_npc_mentions`, `_detect_missed_recurring_npcs`, `_apply_npc_observation_gate`, `_assert_observation_gate_preceded_mint`, `_auto_mint_prose_only_npcs` — in `if is_dice_replay: <span> else: <block>`. The RED test asserts only `_apply_npc_mentions` (== 0 on replay); the wider gate is in-scope, not creep.
  - Rationale: The story names "pool matching, mint paths" as side effects that double-run. The observation gate and auto-mint ARE pool-matching/mint paths and consume the same `result.npcs_present`/`result.narration`; gating only `_apply_npc_mentions` while leaving them firing would double-run exactly what the story says to stop (a ship-3-of-5 half-fix). The replay's prose carries no new player intent (91-2 doctrine).
  - Severity: minor
  - Forward impact: none — the replay never admitted NPC state legitimately; pass-1 owns the scene's roster.
- **Kept Server #742's `last_development_turn` across-call dedupe (no removal)**
  - Spec source: TEA RED Improvement "dead-code candidate, feedback_dead_code"
  - Spec text: "keep it as defense-in-depth … OR remove both in the same PR — Dev/Reviewer call. Do NOT leave it half-removed."
  - Implementation: Left the #742 dedupe and its sibling `test_same_turn_double_apply_develops_once` untouched (both still green).
  - Rationale: Cheap, idempotent, and now guards any FUTURE same-turn re-entry path beyond the dice replay this PR closes. Documented as dead-for-stated-purpose in the apply docstring so it reads as a conscious keep, not an oversight.
  - Severity: minor
  - Forward impact: none — purely additive safety net; no production path now double-applies in one turn.

### Reviewer (audit)
- **Gated the whole NPC-mention sub-block, not only `_apply_npc_mentions`** → ✓ ACCEPTED by Reviewer: Sound — agrees with author reasoning. The observation gate and auto-mint ARE the "pool matching, mint paths" the story names as double-running side effects; gating only `_apply_npc_mentions` would have been the half-fix the project rules forbid ("make 5 connections, don't ship 3"). The block 4561–4621 is cohesive (all consume `result.npcs_present`/`result.narration`); the next statement (`_apply_course_sidecar`, 4630) is a clean non-NPC boundary, correctly left outside the gate. Verified the wider gate does not break the control test (normal turn still applies once).
- **Kept Server #742's `last_development_turn` across-call dedupe (no removal)** → ✓ ACCEPTED by Reviewer: TEA explicitly delegated this as a Dev/Reviewer call and listed "keep as defense-in-depth" as a valid option. Concur — it is cheap, idempotent, guards any future same-turn re-entry, and its sibling test (`test_same_turn_double_apply_develops_once`) stays green. Documented as dead-for-stated-purpose in the docstring, so it is not silent dead code (satisfies `feedback_dead_code` intent — the keep is conscious and recorded, not an oversight).
- **No undocumented deviations found.** The fix matches TEA's prescribed FIX LOCATION (gate the mention step on the replay condition, derive `is_dice_replay` from the `suppress_intent_router` replay signal) and AC1's elimination branch. OTEL span requirement (TEA's "emit a span when suppressed") is satisfied by `npc.mentions_replay_suppressed`.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/narration_apply.py` — added `is_dice_replay` param to `_apply_narration_result_to_snapshot`; gate the entire NPC-mention application sub-block (mention apply, recurring-presence detect, observation gate, ordering-invariant assert, auto-mint) on the replay; emit `npc.mentions_replay_suppressed` span + log in its place.
- `sidequest/server/websocket_session_handler.py` — thread `is_dice_replay=suppress_intent_router` into the shared `_apply_kwargs` (first apply + reprompt re-apply).
- `sidequest/telemetry/spans/npc.py` — new `SPAN_NPC_MENTIONS_REPLAY_SUPPRESSED` span constant, `state_transition`/`npc_registry` route, and `npc_mentions_replay_suppressed_span` context manager (GM-panel lie-detector, mirrors `intent_router.replay_suppressed`).
- `tests/server/test_dice_replay_npc_mention_suppression.py` — TEA's RED tests (now GREEN).

**Tests:** 2/2 story tests passing (GREEN). Full server + telemetry suite: 3120 passed, 507 skipped, 0 regressions. Lint + format clean on changed files.
**Branch:** feat/97-5-turn1-double-apply-npc-mentions (pushed)

**AC status:**
- AC1 (one `_apply_npc_mentions` pass per turn) — **met** via elimination: replay re-entry applies zero mentions; normal turn applies exactly once (control test pins this).
- AC2 (`both_writes_fired` explained or eliminated) — **explained** (cache-tier accounting, orthogonal to this seam; no code change — see TEA finding + Dev finding).

**Handoff:** To Westley (review).
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (advisory) | confirmed 0, dismissed 1 (with evidence), deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents` and reviewed directly by Reviewer)
**Total findings:** 0 confirmed, 1 dismissed (with rationale), 0 deferred

**Preflight finding dismissal:** Preflight flagged "two sequential calls to `_apply_narration_result_to_snapshot`; confirm the second omits `is_dice_replay` intentionally." **Dismissed with evidence:** `grep -rn "_apply_narration_result_to_snapshot(" sidequest/` (excluding the `def`) returns exactly ONE production call site — `websocket_session_handler.py:1101`. The subagent misread the `_apply_kwargs = dict(...)` construction's closing `)` (line 1093) as a second call. There is no unguarded second apply.

## Review Observations

Because 8 of 9 specialist subagents are disabled via project settings, I performed their domain analysis directly. Findings tagged by the domain they cover:

- `[SIMPLE]` **[VERIFIED]** No unnecessary complexity. The fix is a single `if is_dice_replay: <span+log> else: <original block>` wrapper. The author re-indented the existing five-call block verbatim under `else:` rather than extracting a helper — correct for a guard this localized; a helper would obscure the load-bearing ordering comments (49-6 gate before 49-2 mint). Evidence: `narration_apply.py:4565–4646`.
- `[EDGE]` **[VERIFIED]** Boundary: `len(result.npcs_present)` for the span's `mention_count` is safe — `npcs_present` is a list field on `NarrationTurnResult` (never None; the apply already calls `list(result.npcs_present)` unguarded on the non-replay path at the same site). Empty list → `mention_count=0`, span still fires (loud even on a zero-NPC replay). Evidence: `narration_apply.py:4567`.
- `[EDGE]` **[VERIFIED]** Over-suppression check: `is_dice_replay = suppress_intent_router` is True ONLY for the two `dice_throw.py:267,435` replay re-entries. `player_action.py:259,779` and the opening-turn caller (`websocket_session_handler.py:2865`) pass nothing → default False → normal turns still run the full mention block. Control test `test_normal_turn_applies_npc_mentions_exactly_once` pins this. Evidence: grep of `suppress_intent_router=True` sites.
- `[SILENT]` **[VERIFIED]** Not a silent skip. The suppression branch emits BOTH an OTEL span (`npc.mentions_replay_suppressed`, routed `state_transition`/`npc_registry` to the GM panel) AND an INFO log line. Satisfies CLAUDE.md "No Silent Fallbacks" + OTEL Observability Principle and mirrors the 91-2 `intent_router.replay_suppressed` precedent. Evidence: `narration_apply.py:4566–4576`, `npc.py:956–984`.
- `[TYPE]` **[VERIFIED]** Type design sound. New param `is_dice_replay: bool = False` is keyword-only-compatible (added after existing kwargs, default False = backward-compatible for any caller). Span context manager signature matches the established sibling pattern (`npc_auto_mint_skipped_span`) — keyword-only, `_tracer` override, `**attrs`. Evidence: `narration_apply.py:3305`, `npc.py:957–964`.
- `[DOC]` **[VERIFIED]** Documentation is accurate and not stale. The new docstring paragraph, the inline block comment, the span constant comment, and the handler comment all describe the same mechanism consistently (pass 1 = player action, pass 2 = dice replay). They correctly note #742 becomes dead-for-purpose but kept. No misleading or contradictory comments introduced.
- `[TEST]` **[VERIFIED]** Test quality is high. Both tests drive the REAL `_execute_narration_turn` production method (not a synthetic shim), spy the production `_apply_npc_mentions` via monkeypatch at its lookup site, and assert behaviorally (call count 0 on replay / 1 on normal) — not a source-text grep (satisfies CLAUDE.md "No Source-Text Wiring Tests"). The control test guards against over-suppression. Both green; full suite 3120 passed.
- `[SEC]` **[VERIFIED]** No security surface. No auth, no tenant data, no user-input parsing, no injection vector. The change gates an internal side-effect block on an internal boolean derived from a trusted handler. N/A by domain.
- `[RULE]` See `### Rule Compliance` below.

### Rule Compliance

Project rules applicable to this Python server diff (from CLAUDE.md / SOUL.md):

1. **No Silent Fallbacks** (CLAUDE.md, critical) — The replay skip emits a span + INFO log; it is loud, not silent. ✓ COMPLIANT.
2. **No Stubbing / No half-wired features** (CLAUDE.md) — The flag is threaded end-to-end: `dice_throw.py` sets `suppress_intent_router=True` → `_execute_narration_turn` → `_apply_kwargs` → `_apply_narration_result_to_snapshot(is_dice_replay=...)` → the gate. The only production call site is wired. ✓ COMPLIANT.
3. **OTEL Observability Principle** (CLAUDE.md, important) — Every subsystem decision emits a span. The suppression decision now emits `npc.mentions_replay_suppressed` with `mention_count`/`turn_number`/`reason`, routed to the GM panel. This is exactly the "lie-detector" pattern the rule demands. ✓ COMPLIANT.
4. **No Source-Text Wiring Tests** (CLAUDE.md) — The tests are behavioral (real method + call-count spy), not `read_text()` greps. ✓ COMPLIANT.
5. **Every Test Suite Needs a Wiring Test** (CLAUDE.md) — The tests invoke the real `_execute_narration_turn` reachable from the production handler; the suppression is exercised through the genuine call path, not in isolation. ✓ COMPLIANT.
6. **Delete dead code in the same PR** (`feedback_dead_code`) — The one dead-code candidate (#742 dedupe) was a TEA-delegated Dev/Reviewer judgment call; kept as documented defense-in-depth, recorded in the deviation log. Conscious keep, not an oversight. ✓ COMPLIANT (with documented exception).
7. **Crunch in the Genre / gaslighting doctrine** (SOUL.md, `narrator_gaslighting_doctrine`) — Suppressing NPC minting on a mechanical replay aligns with distrusting narrator improvisation during dice resolution; the replay introduces no new authoritative world state. ✓ COMPLIANT.

No rule violations found. No `pub`/visibility rules apply (Python, no security-critical typed fields in the diff).

### Devil's Advocate

Let me argue this change is broken. **First attack — the equivalence is too clever.** The fix collapses "is a dice replay" into "suppress_intent_router." Those are two different concepts that happen to coincide today. If a future story adds a SECOND reason to suppress the intent router (say, a cost-throttle that skips classification on a cheap turn), `is_dice_replay` would silently become True and wrongly suppress NPC mentions on a turn that genuinely introduced an NPC — a phantom-NPC *loss*, the inverse of the phantom-NPC *gain* the gate normally prevents. **Rebuttal:** Today the equivalence is exact and asserted in the narrator docstring ("Only the dice replay re-entry sets this"). The risk is a *future* refactor, not this diff. The fix is named `is_dice_replay` and documented as derived from the replay signal, so a future author adding a new suppression reason is on notice to decouple them. Acceptable; noted as a forward-watch, not a blocker.

**Second attack — the observation gate skip drops a legitimate ratification.** A prior-turn `observation_pending` NPC named only in the dice-replay narration (not the player-action prose) would, pre-fix, be ratified on pass 2; post-fix it is not, and could be wrongly purged next turn. **Rebuttal:** The replay narration is the resolution of the player's own action — the same scene. The player-action pass (pass 1) already carries the scene's NPCs and runs the gate. A pending member surfacing *only* in replay prose and never in the triggering action is a near-impossible shape, and even if it occurred, ratifying off mechanical-replay prose is exactly the narrator improvisation the gaslighting doctrine distrusts. AC1 explicitly wants pool-matching to run once per turn (pass 1). Intended behavior.

**Third attack — what if a turn is a dice replay AND introduces the scene's first NPC?** Then that NPC is never minted. **Rebuttal:** A dice replay only fires after a player action that requested a roll; the NPC the roll concerns was established on the action pass. The narrator cannot mechanically *introduce* a brand-new combatant for the first time inside a resolution replay without the action pass having seated them. If it tried, that is improvisation the doctrine suppresses by design. **Stressed-input angle:** empty `npcs_present`, None narration — both handled (`result.narration or ""` defensive default preserved; `len([])` = 0). **Config angle:** no config surface touched. Conclusion: no defect rises to Critical/High. The forward-watch on the `is_dice_replay`/`suppress_intent_router` coupling is the single thing worth a future author's attention, and it is documented.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `dice_throw.py` (replay re-entry, `suppress_intent_router=True`) → `_execute_narration_turn` → `_apply_kwargs["is_dice_replay"]` → `_apply_narration_result_to_snapshot(is_dice_replay=True)` → NPC-mention sub-block gated off, `npc.mentions_replay_suppressed` span fires. Safe because the player-action pass (pass 1, `is_dice_replay=False`) already applied the scene's NPCs exactly once; the replay (pass 2) carries no new player intent.

**Pattern observed:** Replay-guard mirrors the established 91-2 `intent_router.replay_suppressed` doctrine — same signal, same loud-span treatment — at `narration_apply.py:4565`.

**Error handling:** Defensive defaults preserved (`result.narration or ""`); span fires even on zero-mention replays (loud, never silent). No new failure paths introduced.

**Dispatch tags:** `[EDGE]` verified (over-suppression + boundary), `[SILENT]` verified (span + log, not silent), `[TEST]` verified (behavioral, real method), `[DOC]` verified (consistent, not stale), `[TYPE]` verified (backward-compatible kwarg + sibling-pattern span), `[SEC]` N/A (no security surface), `[SIMPLE]` verified (minimal guard, no over-engineering), `[RULE]` verified (7 rules checked, all compliant). Preflight: lint PASS, format PASS, 34 tests PASS.

**AC status:** AC1 met (elimination — replay applies zero, normal applies once, control-pinned). AC2 met (explained — orthogonal cache-tier accounting, no code change).

**Handoff:** To Vizzini (SM) for finish-story.