# Story 126-16 Context

## Title
[FATE] Defend-barrier test-quality nits + deferred TEA coverage (match=authorization, list-vs-next span, partial-fill + defense-wins unit tests)

## Metadata
- **Story ID:** 126-16
- **Type:** chore
- **Points:** 1
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** Fate Core playtest follow-ups — annees_folles eval (2026-06-16/17)

## Problem
Deferred test-quality + coverage follow-ups from 126-8 (the server DEFEND barrier, ADR-148/151). 126-8's review APPROVED the implementation but logged test-side gaps; this 1pt chore closes them. Server-only; net change is test-side (assertion-tightening + new characterization tests of already-shipped behavior), no production logic change expected. Three items decoded from the title: (1) match=authorization — tighten a vacuous pytest.raises; (2) list-vs-next span — make span lookups name-keyed not positional; (3) deferred TEA coverage — partial-fill ledger + defense-wins resolution. Grounding files: tests/server/dispatch/test_fate_defense_record.py, tests/game/ruleset/test_fate_defend_spans.py, tests/game/test_fate_pending_defenses.py, sidequest/server/dispatch/fate_conflict.py (dispatch_fate_defense ~1160, _resolve_attack ~590, ledger_full all() gate ~1257).

## Technical Approach
_Grounded by SM context discovery 2026-06-20 (read the cited lines; verify before editing — line numbers drift). This is a server-only, test-side chore: production behavior already shipped in 126-8, so the new coverage tests characterize existing behavior (green-on-arrival is the expected RED outcome for AC3/AC4 — assert that the shipped behavior is correct; only a missing multi-defender fixture is genuinely new) and the nits tighten existing assertions._

**AC1 — match=authorization** (`tests/server/dispatch/test_fate_defense_record.py`):
`test_defend_throw_from_non_defender_is_rejected` (~line 89-112) uses a bare
`pytest.raises(FateConflictError)` (~line 99). `dispatch_fate_defense`
(`fate_conflict.py`) raises that same error from FOUR branches: unknown request_id
(~1185), **authorization** (~1219, message ends `"(authorization)"`), already-filled
(~1224), non-concede-no-faces (~1234) — so the bare match can pass on the wrong branch.
Add `match=` pinned to the authorization branch. NOTE: the sibling
`test_defend_authorization_rejection_emits_watcher_event` (~line 115) already pins via the
`op="fate_defend_authorization_rejected"` field — it's the bare one that's the nit.

**AC2 — list-vs-next span** (`tests/game/ruleset/test_fate_defend_spans.py`):
assertions that fetch via `exporter.get_finished_spans()[0]` (~lines 49, 69, 171) grab a
positional span. The name-keyed convention `next(s for s in exporter.get_finished_spans()
if s.name == "...")` is already used at ~lines 107 and 131. Convert the `[0]` lookups on
any path that can emit more than one span to the name-keyed form. (Run this file with
`-n0` — header note: known span-count deadlock under the parallel runner.)

**AC3 — partial-fill** (`tests/game/test_fate_pending_defenses.py` and/or
`test_fate_defense_record.py`): existing tests cover only SINGLE-entry ledgers (one entry →
`ledger_full=True`). The `parked_conflict` helper (`tests/_helpers/fate_fixtures.py`) builds
one entry. Add a two-defender parked conflict, fill ONE defender → assert `ledger_full=False`
(the `all(...)` gate at `fate_conflict.py` ~1257), then fill the second → `True`.

**AC4 — defense-wins** (`fate_conflict.py` `_resolve_attack` ~590-649): the recorded-PC-
defense branch reads `defense_total` from the ledger (~620-621); harm math is
`shifts = commit.ladder_total - defense_total` (~641); `shifts <= 0` → no harm, and exact
tie (`shifts == 0`) appends a `Momentum vs ...` boost aspect (~644-649). No test currently
drives a RECORDED PC defense that beats/ties the attack. Build the win case and assert: no
harm applied, defender NOT taken out, momentum boost on the exact tie.

**Wiring note (CLAUDE.md):** these are behavior/assertion tests through the real dispatch
and real span emitters — no source-text grepping as a wiring check.

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- match=authorization: test_defend_throw_from_non_defender_is_rejected (test_fate_defense_record.py) tightens its bare pytest.raises(FateConflictError) with match= pinned to the authorization branch, so it cannot pass on a different FateConflictError (unknown / already-filled / no-faces). The authorization rejection message is the one ending in '(authorization)'.
- list-vs-next span: in test_fate_defend_spans.py, span assertions that fetch a span by positional list index (get_finished_spans()[0]) on a path that can emit more than one span are converted to name-keyed next(s for s in ... if s.name == '...') lookups (the convention already used in test_npc_server_defense_tags_role_defense), so each assertion targets the intended span rather than a positional accident.
- partial-fill coverage: a new unit test exercises a MULTI-entry pending_defenses ledger — filling one defender's entry leaves ledger_full=False, filling all entries makes it True — proving the all(...) ledger gate handles partial fills (existing tests only cover the single-entry full-ledger case).
- defense-wins coverage: a new unit test drives a RECORDED PC defense through _resolve_attack where the defense beats/ties the attack (defense_total >= attacker ladder_total -> shifts<=0 -> no harm applied, momentum boost on exact tie, defender NOT taken out), covering the win side of the recorded-defense branch.
- Server suite stays green (no production regression); any new fixture (e.g. a two-defender parked conflict) lives alongside parked_conflict in tests/_helpers/fate_fixtures.py, not pointed at live content.

---
_Generated by `pf context create story 126-16` from the sprint YAML._
