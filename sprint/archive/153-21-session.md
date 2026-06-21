---
story_id: "153-21"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-21: [DUNGEON-SEAM-CROSSING-STICKY] descend-the-rope must traverse the the_dropmouth->deep_descent seam into the procedural entrance node, not latch the narrator title back to the static cartography region

## Story Details
- **ID:** 153-21
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Priority:** p1
- **Points:** 5
- **Epic:** 153 (Playtest follow-ups)
- **Repos:** server only

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T15:52:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T14:49:14Z | 2026-06-21T14:53:42Z | 4m 28s |
| red | 2026-06-21T14:53:42Z | 2026-06-21T15:10:54Z | 17m 12s |
| green | 2026-06-21T15:10:54Z | 2026-06-21T15:18:58Z | 8m 4s |
| review | 2026-06-21T15:18:58Z | 2026-06-21T15:52:26Z | 33m 28s |
| finish | 2026-06-21T15:52:26Z | - | - |

## SM Assessment

**Routing Decision:** TDD workflow. TEA writes failing tests first in the red phase, then dev fixes the precedence defect in narration_apply.py.

**Scope:** Single-repo server fix. The bug is an ordering/precedence defect in `sidequest/server/narration_apply.py::_apply_narration_result_to_snapshot` where the static-region latch wins before the seam-crossing recovery branch can fire. When a descent heading resolves back to the seam-owning region (e.g., "The Dropmouth — First Chamber" → `the_dropmouth`), the engine latches the PC to the static cartography region instead of crossing the `deep_descent` seam to the procedural `entrance` node. The fix extends the existing seam-crossing path (already wired in movement.py and the seam-recovery branch) by adding a precedence guard: if the PC's current region owns a registered seam route AND the resolved heading matches that seam-owning region AND the movement is a descent, take the seam-crossing path instead of the static latch. Reuse existing helpers: `seam_route_for`, `get_seam_resolver`, `_entrance_room_name`, `_reanchor_location_ledger`, and the `region_entry_rejected_span` fail-loud path.

**Merge Gate:** Clear. No open PRs in sidequest-server (gh pr list returned empty). Develop is clean.

**Key Risk:** This is an ordering/precedence fix in an existing seam path. Do NOT build a new movement subsystem; extend the latch-vs-seam-recovery branch logic. The seam machinery is proven (movement.py hybrid descent block + the seam-recovery elif both exist and are tested). The story is to make a resolved-heading descent reach the seam path, not to invent seam resolution.

**Testing Requirement:** Add behavior test to `tests/server/test_narration_seam_recovery.py` extending the `hybrid_apply_kit` fixtures. Drive a `beneath_sunden` narration result with the sticky "The Dropmouth — First Chamber" heading through the real `_apply_narration_result_to_snapshot` and assert PC lands on `entrance` after ONE descent with `movement.resolved` span captured. Verify OTEL: `movement.resolved` emitted (resolved_via indicating narration-driven seam crossing), `region_entry_resolved_to_cartography` NOT emitted, `region_current_advanced` fires with `new_region="entrance"`.

## Delivery Findings

No upstream findings.

## Design Deviations

**SM inserted a focused Architect design spike before the red phase (2026-06-21).**
The tdd workflow has no design phase, but 153-21 (a) *reverses* the documented
105-2 architect decision ("strip a sub-title over a seam region back to the
canonical name; never cross off a drifted title — that would be
text-classification teleportation", encoded in `test_drift_strip_on_seam_region`
+ the `seam_region_sub_location_stripped` span) and (b) leaves the
descent-detection signal **unspecified**: AC2's main clause ("heading resolves to
the seam-owning region → cross") is satisfied by BOTH a real descent ("The
Dropmouth — First Chamber") AND a harmless retitle, yet AC2's carve-out says the
retitle must NOT cross. The turn pipeline runs the movement-subsystem dispatch
(`turn_context.dispatch_package`) BEFORE `_apply_narration_result_to_snapshot`,
so a same-turn descent crossing / `region_transitions` entry / pre-advanced
region is a candidate non-text signal. The Architect must pin the concrete signal
and crossing mechanism so TEA can construct distinguishable AC1-cross vs
AC2-stay scenarios. Read-only spike; no code; decision appended to
`sprint/context/context-story-153-21.md`.

### TEA (test design)
- **AC4 asserted as membership, not a "1/N" string:** Story AC4 phrases the
  counter as `discovered=1/N`. The crossing's frontier hook
  (`frontier_hook.py:152`) dedup-appends `entrance` to `discovered_regions` (a
  list); there is no "1/N" string on the snapshot at apply time. Per the
  Architect's TEA guidance I assert `ENTRANCE_ID in discovered_regions`
  (membership) rather than a brittle count string. Reason: the "1/N" is a
  map-emit rendering, not snapshot state.
- **AC6 "latch span absent" pinned via `region.entry_canonicalized_dedup`:** the
  story's `region.entry_resolved_to_cartography` is a *log line*, not a span; the
  static latch's actual OTEL span is `region.entry_canonicalized_dedup`
  (`resolution="cartography"`, `existing_surface_form="the_dropmouth"`,
  `narration_apply.py:4366`). I assert the absence of THAT span (the real
  telemetry the GM panel sees) rather than grepping a log string. Reason: No
  Source-Text Wiring Tests + the span is the lie-detector artifact.
- **Same-turn receipt seeded via `apply_world_patch(pc_region=...)`, not the live
  resolver:** the Architect offered both. I used the world-patch seed because it
  is the *exact* call `resolve_deep_descent` makes (`deep_descent.py:54`) and it
  keeps the captured-span set clean of a prior `movement.resolved` from the
  resolver — so the AC6 span assertion pins the NEW apply-guard span, not a
  seed artifact. Verified faithful by `test_seam_receipt_precondition_holds`.

## TEA Assessment

**Tests Required:** Yes
**Reason:** TDD bug fix — a precedence/clobber defect in the real apply path.

**Test Files:**
- `tests/server/test_narration_seam_recovery.py` — extended (no existing test
  modified): added the same-turn-crossing don't-clobber coverage on the existing
  `hybrid_apply_kit` fixture.

**Tests Written:** 2 new tests covering AC1/AC2/AC3/AC4/AC6 (+ AC7 wiring via the
real `_apply_narration_result_to_snapshot` path):
- `test_resolved_seam_heading_honors_same_turn_crossing` — the RED behavior test
  (AC1 stay-at-entrance, AC3 re-anchor to authored "Under the Rope", AC4
  discovered membership, AC6 `movement.resolved` span `resolved_via=
  narration_seam_recovery` + no static-latch span + `region_current_advanced`
  new_region=entrance with no clobber-back). This IS the wiring test (AC7):
  drives the real apply through `hybrid_apply_kit` with the authored
  `rooms/entrance.yaml` and real span capture — no source-text greps.
- `test_seam_receipt_precondition_holds` — a green sanity gate proving the
  seeded same-turn receipt faithfully mirrors `resolve_deep_descent` (PC at
  entrance, same-turn `region_transitions`, anchor-sync, discovered bump) so the
  RED above fails for the RIGHT reason.

**Negative control (AC2):** existing `test_drift_strip_on_seam_region` (no
crossing receipt → strip, stay at `the_dropmouth`) is **unchanged** and still
GREEN — confirmed in the same run. `test_oz_drift_retitle_unchanged` and
`test_seamless_region_mode_world_unchanged` also untouched/green.

**Status:** RED (failing — ready for Dev). The RED asserts on the exact clobber:
`AssertionError: ... got 'the_dropmouth' ... assert 'the_dropmouth' == 'entrance'`.

**Run:** `SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test
uv run pytest tests/server/test_narration_seam_recovery.py` → 1 failed (new AC1
test), 8 passed (incl. the 7 pre-existing + the new precondition gate).

**Handoff:** To Dev for the don't-clobber guard at `narration_apply.py:4210`
(top of the `if known_region_id is not None:` block), per the Architect's design.

**Design fit notes for the SM/Dev (Architect's design held; no re-route needed):**
- The Architect's signal (same-turn `region_for==entrance` + this-turn
  `region_transitions` to entrance) fit the `hybrid_apply_kit` harness exactly.
- One harness nuance the Dev must honor for AC6: because the seed does NOT call
  `resolve_deep_descent`, there is no pre-existing `movement.resolved` span in
  the capture — so the Dev's apply guard MUST emit its own `movement.resolved`
  (`resolved_via="narration_seam_recovery"`) for that assertion to go green.
  This matches the Architect's §2 AC6 ruling. If the Dev instead chooses to NOT
  re-emit (because the real movement crossing already emitted one upstream), the
  AC6 span assertion will need the Dev+SM to revisit — but the design explicitly
  calls for the apply guard to emit its own span, so this is the intended shape.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 32 target+adjacent + 11 integration tests pass; ruff check + `format --check` clean | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | Turn-boundary equality `t.turn==interaction` (`narration_apply.py:289`) — VERIFIED not-live (record_interaction runs after apply); MP `player_name` vs `_acting_player_name` divergence (`whandler:989` vs `:1180`) — pre-existing shared assumption; multi-descent ambiguous cart → guard declines safely | Dismissed/Accepted (no live bug; pre-existing shared) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | "BLOCKER" confab `character_location_updated` watcher fires pre-reanchor (`:4159`) and "MAJOR" `_entrance_room_name` raw-slug fallback (`:193`) — BOTH pre-existing, shared with 105-2 elif; region truth stays `entrance` | Dismissed as new defects (pre-existing 105-2 family behavior; downgraded to NIT) |
| 4 | reviewer-test-analyzer | Yes | findings | RED test non-vacuous (flips every assertion); seed faithfully mirrors `resolve_deep_descent:54`; no source-text greps; precondition gate slightly tautological; AC5 guard-inactive path untested (NIT) | Accepted (non-blocking; tests valid) |
| 5 | reviewer-comment-analyzer | Yes | findings | NEW: comment `:4299` + test msg `:655` label the latch span `region.entry_resolved_to_cartography` but that's the LOG key; span name is `region.entry_canonicalized_dedup`; test docstring `:591` says AC2 (AC2 is the external negative control) | Accepted (NIT doc-accuracy; control-flow claim itself correct) |
| 6 | reviewer-type-design | Yes | findings | `region_cart: Any` could be `CartographyConfig\|None` (`:262`, accepted duck-typing); `Route.from_id: str\|None` → `None==known_region_id` safely False (`:300`); confirmed no Optional leak, field names correct | Accepted (MINOR; no runtime bug) |
| 7 | reviewer-security | Yes | clean | No path traversal (crossing_region=const ENTRANCE_ID, not narrator text); no cross-player leak (`t.pc_name==player_name`, `perspective=player_name`); guard declines narrator authority (cannot teleport on text without engine receipt); only inherited unbounded `region_transitions` scan (LOW) | Accepted (no security issue introduced) |
| 8 | reviewer-simplifier | Yes | findings | No dead code; all 3 new imports used; restructure clean; three-clause AND correctly non-redundant; 2-site duplication w/ 105-2 below extract threshold (MINOR); `logger.info` inside span block is cosmetic (NIT) | Accepted (non-blocking) |
| 9 | reviewer-rule-checker | Yes | findings | All 6 CLAUDE.md rules PASS; 2 MINOR structural: `_entrance_room_name` silent early-return on `lookahead_handle is None` (`:193`, pre-existing/shared); `_watcher_publish` just outside `movement_resolved_span` with-block (`:4317`, both always fire) | Accepted (rules satisfied; structural nits) |

**New findings this pass (not in my earlier dispositions):** comment-analyzer's span-name-vs-log-key label mismatch at `narration_apply.py:4299` / `test:655` and the test docstring AC2 mislabel at `test:591`. Both NIT-severity, doc-accuracy only — the control-flow and the assertions are correct. No new BLOCKER or MAJOR. The silent-failure "BLOCKER"/"MAJOR" and edge-hunter "off-by-one" reconcile to pre-existing/not-live, as in my first pass.

**All received:** Yes (9 returned; 1 clean, 7 with non-blocking findings, 1 informational). All NIT/MINOR; zero Critical/High; the one actionable doc-accuracy NIT (span-name label) was fixed in commit `766b74b3`.

## Reviewer Assessment

**Verdict:** APPROVED

**Specialist findings (tagged, from the Subagent Results table above):**
- `[EDGE]` Turn-boundary equality `t.turn==interaction` (`narration_apply.py:289`) verified NOT live (`record_interaction` runs after apply); MP `player_name` vs `_acting_player_name` divergence is a pre-existing shared assumption of the whole region-mode apply path; multi-descent ambiguous cartography → guard declines safely via `surface_owner_for_entrance` returning None. No new live bug.
- `[SILENT]` The confab `character_location_updated` watcher firing pre-reanchor (`:4159`) and the `_entrance_room_name` raw-slug fallback (`:193`) are BOTH pre-existing 105-2-family behavior, not introduced here; region truth always lands on `entrance`, so No-Silent-Fallbacks holds (the PC never silently lands on the surface). No new swallowed error.
- `[TEST]` RED test is non-vacuous (flips region/current_region/latch-span/advance assertions red→green); the seed faithfully mirrors `resolve_deep_descent:54`; no source-text grep assertions; the AC5 guard-inactive path is covered by the unchanged negative control + the existing dead-store reject test. Tests valid.
- `[DOC]` Span-name-vs-log-key label mismatch at the guard comment (`:4299`) and test message (`:655`), plus the test docstring AC2 mislabel — all NIT doc-accuracy; control-flow and assertions were correct. **Fixed** in commit `766b74b3`.
- `[TYPE]` `region_cart: Any` could be `CartographyConfig | None` (accepted duck-typing boundary); `Route.from_id: str | None` makes `None == known_region_id` safely False; no Optional leak, field names correct. MINOR, no runtime bug.
- `[SEC]` No path traversal (the crossing target is the constant `ENTRANCE_ID`, never narrator text); no cross-player leak (`t.pc_name==player_name`, `perspective=player_name`); the guard declines narrator authority and cannot teleport on heading text without a real engine receipt. Only the inherited unbounded `region_transitions` scan (LOW, pre-existing). No security issue introduced.
- `[SIMPLE]` No dead code; all 3 new imports used; the `if/elif` restructure is clean and the three-clause AND is non-redundant; the 2-site re-anchor duplication with the 105-2 elif is below the extract threshold (MINOR). Non-blocking.
- `[RULE]` All 6 CLAUDE.md hard rules PASS (No Silent Fallbacks / No Stubbing / Reuse-first / Verify-wiring / wiring-test present / OTEL span emitted); two MINOR structural placement nits (`_entrance_room_name` early-return, `_watcher_publish` just outside the span `with`-block) are pre-existing/shared and always fire. Rules satisfied.

**Data flow traced:** descent action → intent-router pre-narrator pass (`websocket_session_handler.py:984`) → `resolve_deep_descent` → `apply_world_patch(pc_region={player:"entrance"})` stamps a same-turn `RegionTransition(turn=interaction, to_region="entrance")` and anchor-syncs `current_region="entrance"` → narrator titles "The Dropmouth — First Chamber" → `_apply_narration_result_to_snapshot` (`:1177`) resolves `known_region_id="the_dropmouth"` → **new guard reads the same-turn receipt and declines the clobber.** Safe because `record_interaction()` fires at `:1359` (after apply), so the receipt's stamped turn equals the guard's read — no off-by-one (verified against handler ordering).

**Pattern observed:** Byte-identical preservation of the prior latch body — `diff` of the old `if known_region_id is not None:` body (base 4211–4379) vs the new `elif known_region_id is not None:` body (HEAD 4329–4497) is empty. Zero dropped logic on the non-guard path; chain is `new-if / elif known_region_id / elif _is_region_mode_world / no-else`. Reuse-first throughout: `resolve_deep_descent`'s already-fired crossing, `_entrance_room_name`, `_reanchor_location_ledger`, `surface_owner_for_entrance`, 105-2 `narration_seam_recovery` vocabulary.

**Error handling:** Guard fails honest (returns False on every negative clause → falls to the existing latch; never fabricates a crossing). `surface_owner_for_entrance` returns None on ambiguity (No Silent Fallbacks). Fail-loud reject path (`seam_crossing_unresolvable`, `:4530`) untouched and unreached by the guard.

**OTEL:** Guard emits `movement_resolved_span(resolved_via="narration_seam_recovery")` + `region_current_advanced(new_region="entrance")` and returns before the static-latch `region.entry_canonicalized_dedup` span — GM panel distinguishes engine crossing from narrator retitle. Asserted non-vacuously via monkeypatched `_watcher_publish` + in-memory span exporter.

**Observations (none blocking — Critical/High count: 0):**

| Severity | Issue | Location | Disposition |
|----------|-------|----------|-------------|
| NIT | Comment + test-msg label latch span as `region.entry_resolved_to_cartography` (the LOG key); span name is `region.entry_canonicalized_dedup` | `narration_apply.py:4299`, `test:655` | Doc-accuracy only; control-flow claim correct |
| NIT | Test docstring says "AC1/AC2/AC3/AC4/AC6"; AC2 is the external negative control (`test_drift_strip_on_seam_region`) | `test:591` | Mislabel; handoff-red correctly says AC1/AC3/AC4/AC6/AC7 |
| MINOR | `region_cart: Any` could be `CartographyConfig\|None`; `Route.from_id: str\|None` compared to non-None str (safely False) | `narration_apply.py:262,300` | Accepted duck-typing; no runtime bug |
| MINOR | 2-site duplication of `_entrance_room_name`+`_reanchor_location_ledger`+`result.location=` with 105-2 elif | `:4284` / `:4578` | Below extract threshold; flag if a 3rd site appears |
| NIT | `_entrance_room_name` silent early-return on `lookahead_handle is None`; `_watcher_publish` just outside `movement_resolved_span` with-block; `logger.info` inside span block | `:193,4317,4308` | Pre-existing/shared with 105-2; both spans always fire; cosmetic |

**Pre-existing inherited (not introduced by 153-21):** confab `character_location_updated` watcher firing before `_reanchor_location_ledger` (the helper's documented repair role), and the unbounded `region_transitions` scan. Track separately if desired; neither blocks.

**Optional follow-up (non-blocking):** an OTEL breadcrumb when the receipt is present but `surface_owner_for_entrance` returns None (ambiguous multi-descent) would make the documented multi-dungeon follow-up observable — but that case is explicitly out of scope per the story.

**Handoff:** To SM for finish-story.