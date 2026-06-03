---
story_id: "72-13"
jira_key: ""
epic: "72"
workflow: "trivial"
---
# Story 72-13: hp_depletion presence-stamp: production-path wiring test through instantiate_encounter_from_trigger + created-branch coverage; tighten 72-8 AC2 docstring

## Story Details
- **ID:** 72-13
- **Jira Key:** (none)
- **Epic:** 72 (NPC Identity Hardening)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-03T19:44:59Z
**Repos:** sidequest-server

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T19:30:02Z | 2026-06-03T19:32:42Z | 2m 40s |
| implement | 2026-06-03T19:32:42Z | 2026-06-03T19:40:58Z | 8m 16s |
| review | 2026-06-03T19:40:58Z | 2026-06-03T19:44:59Z | 4m 1s |
| finish | 2026-06-03T19:44:59Z | - | - |

## SM Assessment

**Story:** 72-13 — hp_depletion presence-stamp: add a *production-path* wiring test through `instantiate_encounter_from_trigger` (incl. the created-branch where the opponent has no backing `Npc`); tighten the 72-8 AC2 docstring. Epic 72 (NPC Identity Hardening), 2pt chore, trivial workflow, sidequest-server only.

**Why it matters:** Story 72-8 stamped `last_seen_turn`/`last_seen_location` on the two combat opponent-presence seams and shipped approved, but its Reviewer logged two confirmed (non-blocking) gaps that this story closes:
1. The hp_depletion seam (`_seed_combat_hp_depletion_to_npcs`) is verified only by a *unit* test (`test_hp_depletion_seam_stamps_presence`) that calls it directly with a `types.SimpleNamespace` cdef — bypassing `instantiate_encounter_from_trigger` and the real `ConfrontationDef` accessors. The dial path IS wired-tested via `trigger_encounter`; the hp_depletion dispatch gate (win_condition branch threading `acting_character_name=player_name`) is verified only by reading the diff. This violates "Every Test Suite Needs a Wiring Test" for the hp_depletion path.
2. The new-test module docstring overstates AC2 coverage: it says AC2 is "guarded by" `test_cite_known_npc_updates_last_seen_on_npc`, but that test only exercises the prose path's truthy-location branch, not the no-location branch.

**Where to work:**
- `sidequest-server/tests/server/dispatch/test_72_8_presence_last_seen_stamp.py` — add a `trigger_encounter` test against a real `win_condition: hp_depletion` pack (model on `tests/server/test_space_opera_swn_combat_e2e.py`), asserting the opponent `Npc`'s stamped `last_seen_turn`/`last_seen_location`, **including the CREATE branch** (opponent has no backing `Npc` before instantiation). Tighten the AC2 docstring claim (or add the missing no-location prose-path test).
- Production code under test (no changes expected): `sidequest/server/dispatch/encounter_lifecycle.py` — `_seed_combat_hp_depletion_to_npcs`, the win_condition dispatch gate (~1173), `instantiate_encounter_from_trigger`, `_stamp_encounter_presence`.

**Scope guardrails:** Test-and-docstring story — do NOT change production presence-stamp behavior. Drive the real seam (No Source-Text Wiring Tests — assert `Npc` field state / OTEL span attributes, not source greps). Do not regress the existing 7 tests. Do not implement the deferred opposed_check-social-opponent stamp (separate follow-up). Tests must point at a fixture/synthetic `hp_depletion` pack or the real space_opera SWN pack as the e2e exemplar does — confirm `SIDEQUEST_GENRE_PACKS` wiring matches that exemplar.

**Reference:** `sprint/archive/72-8-session.md` (Reviewer findings — the spec for this story), `sprint/context/context-story-72-13.md`.

**Decision:** Setup complete; context written. Scope is small and fully specified by 72-8's Reviewer findings. Handing to Dev for the implement phase. No open questions.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): The brittle source-text wiring test flagged in 72-8's Dev findings is still present — it asserts `_publish_combat_edge_to_npcs(` appears ≥2× in `encounter_lifecycle.py`. Affects `tests/server/test_npc_registry_combat_stats.py:297-307` (replace with an OTEL-span / fixture-driven behavior assertion per CLAUDE.md "No Source-Text Wiring Tests"). Explicitly out of 72-13's scope, but adjacent to this story's wiring-test theme and worth a dedicated trivial follow-up. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The hp_depletion seam's direct-call unit test (`test_hp_depletion_seam_stamps_presence`, SimpleNamespace cdef) is now partially redundant with the new production-path tests, but retained as a fast isolated check of the seam in isolation. If a future refactor changes the seam signature, both will need updating. Affects `tests/server/dispatch/test_72_8_presence_last_seen_stamp.py` (no action needed now). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The new real-pack tests gate on `_has_real_content()` = `GENRE_PACKS_DIR.is_dir()` while `_space_opera_pack()` resolves via `find_pack_path` (which also checks `genre_workshopping/`). If space_opera were ever moved to `genre_workshopping/` with `genre_packs/` absent, the skipif would skip even though the pack is findable. Harmless today (space_opera is a live pack and this mirrors the sanctioned `test_space_opera_swn_combat_e2e.py` guard exactly), and the `PackNotFound`→`pytest.skip` in `_space_opera_pack()` keeps it loud-but-safe. Affects `tests/server/dispatch/test_72_8_presence_last_seen_stamp.py` (no action needed; carry the same note already implicit in the e2e exemplar). *Found by Reviewer during code review.*
- Dev's two findings (brittle source-text wiring test at `test_npc_registry_combat_stats.py:297-307`; partial redundancy of the direct-seam unit test) reviewed and corroborated — both correctly scoped OUT of 72-13. The source-text wiring test is a legitimate trivial follow-up under epic 72's "Every Test Suite Needs a Wiring Test" theme. *Confirmed by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- AC3 resolution choice (not a spec deviation — the story offered both): tightened the AC2 docstring claim to accurately scope what `test_cite_known_npc_updates_last_seen_on_npc` covers (truthy-location prose branch only) and pointed at the presence path's own no-location coverage, rather than adding a new no-location *prose-path* test. The prose path is explicitly out of 72-13's production scope (72-8 said "do not regress prose path"), and the presence path's no-location branch is already covered by `test_presence_no_resolved_location_stamps_turn_not_location`. The story context (AC3) sanctions either approach.
- No deviations from spec.

### Reviewer (audit)
- **AC3 resolution choice (docstring-tighten over new prose test)** → ✓ ACCEPTED by Reviewer: The story context (AC3) explicitly sanctions either approach ("Tighten the claim ... — or the no-location prose-path branch is added"). The chosen tightening is accurate to the source: `test_cite_known_npc_updates_last_seen_on_npc` (verified at `tests/server/test_npc_pool_narration_apply.py:57-72`) sets `character_locations["Hero"]="TavernRow"`, so it only exercises the truthy-location branch — the docstring now says exactly that. The presence path's no-location branch IS covered locally by `test_presence_no_resolved_location_stamps_turn_not_location`. Tightening (not adding a prose test) is the proportionate choice for a test-and-docstring story whose stated scope excludes touching the prose path. Sound.
- No **undocumented** spec deviations found. No production code changed; the diff is confined to the named test module, exactly as the story scoped.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/tests/server/dispatch/test_72_8_presence_last_seen_stamp.py` — (1) tightened the module AC2 docstring to accurately scope the prose-path no-regression coverage (truthy-location branch only) and point at the presence path's own no-location test (AC3); (2) added `Character` + `genre_paths` imports; (3) added three production-path wiring tests driving the real `space_opera` `win_condition: hp_depletion` combat through `trigger_encounter` → `instantiate_encounter_from_trigger`: CREATE branch (opponent materialized by the seam is presence-stamped — AC1+AC2), OVERWRITE branch (pre-existing stale opponent refreshed in place, no duplicate — AC1), and an OTEL proof that the stamp rides the `npc.edge_published` span with `created=True` through production. All three gate on `_has_real_content()` (filesystem) and skip gracefully when sidequest-content is absent.

**No production code changed** — test-and-docstring story only; the presence-stamp behavior shipped in 72-8 is correct and now proven through the production dispatch gate.

**Tests:** 9/9 passing (GREEN) — 6 pre-existing + 3 new. `ruff check` + `ruff format --check` clean.

**Branch:** feat/72-13-hp-depletion-presence-wiring-test (sidequest-server, pushed)

**Handoff:** To review phase (Granny Weatherwax / Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 9/9 green, ruff check+format clean, 0 smells |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (workflow.reviewer_subagents.edge_hunter=false) — edge cases assessed by Reviewer directly |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — silent-failure surface assessed by Reviewer directly |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — test quality assessed by Reviewer directly |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — docstring accuracy assessed by Reviewer directly |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — no type surface in this diff (test-only) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — no security surface (local test, no I/O sink) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — complexity assessed by Reviewer directly |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — project rules enumerated by Reviewer in Rule Compliance |

**All received:** Yes (1 enabled subagent returned clean; 8 disabled via settings, pre-filled and non-blocking)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 non-blocking Improvement (skipif/find_pack_path asymmetry — deferred, harmless, mirrors sanctioned exemplar)

### Rule Compliance

Enumerated against CLAUDE.md (server) + SOUL.md for every changed unit (1 file, test-only, +200/-4):

- **No Silent Fallbacks** — COMPLIANT. `_space_opera_pack()` raises→`pytest.skip` on `PackNotFound` (loud skip, not a silent alt-path); the `skipif(_has_real_content)` guard is an explicit content gate, not a fallback. No alternative pack path is silently tried.
- **No Stubbing** — COMPLIANT. No stubs/placeholders; the helpers (`_spacer`, `_space_opera_pack`, `_opponent_npc`) are fully-wired test fixtures with real call sites in the three new tests.
- **No Source-Text Wiring Tests** — COMPLIANT (and the point of the story). All three new tests assert behavior — `Npc` field state (`last_seen_turn`/`last_seen_location`), no-duplicate count, and OTEL `npc.edge_published` span attributes — never `read_text()`/regex on production source. This is exactly the sanctioned alternative #1 (OTEL span assertions) + #2 (fixture-driven behavior) from the CLAUDE.md rule.
- **Every Test Suite Needs a Wiring Test** — COMPLIANT/STRENGTHENED. The new `test_hp_depletion_presence_stamp_production_path_*` tests ARE the integration/wiring proof for the hp_depletion path, driving `trigger_encounter`→`instantiate_encounter_from_trigger`→win_condition gate (`encounter_lifecycle.py:1216`)→`_seed_combat_hp_depletion_to_npcs`. This closes the precise gap 72-8's Reviewer flagged.
- **Tests don't point at live content** — EXCEPTION APPLIES (not a violation). The rule has a documented sanctioned exception for production-seating proofs (`test_space_opera_swn_combat_e2e.py` header). The new tests cite that rationale inline, gate on `_has_real_content()`, and skip gracefully when content is absent. The SM/story context (AC1) explicitly blessed "the real space_opera SWN pack as the e2e exemplar does." Citing the contradicting sanctioned-exception text per the dismissal rule.
- **OTEL Observability Principle** — COMPLIANT. No subsystem behavior changed (test-only), and the span test additionally asserts the existing `npc.edge_published` lie-detector signal fires through production with `created=True`.
- **No production code changed** — VERIFIED: `git diff develop...HEAD` touches only `tests/server/dispatch/test_72_8_presence_last_seen_stamp.py`.

## Reviewer Assessment

**Verdict:** APPROVED

**Scope:** Test-and-docstring-only change in one file (`tests/server/dispatch/test_72_8_presence_last_seen_stamp.py`, +200/-4). No production code touched — confirmed via `git diff develop...HEAD`. Closes the two confirmed non-blocking gaps 72-8's Reviewer logged.

**Data flow traced:** `trigger_encounter(snap, pack, "combat", "Vesh", npcs_present=[NpcMention(name="Corsair", side="opponent")])` → `instantiate_encounter_from_trigger` → seating block (`encounter_lifecycle.py:1074-1078`, stamps only PRE-EXISTING roster Npcs, creates none) → `cdef.category=="combat"` + `win_condition==hp_depletion` gate (`:1216`) → `_seed_combat_hp_depletion_to_npcs` (`:1221`) → CREATE branch (`:178`) materializes the "Corsair" `Npc` and `_stamp_encounter_presence` writes `last_seen_turn=6`/`last_seen_location="Docking Ring"` → span emitted with `created=True`. The test asserts each link behaviorally. Safe — this is the real production gate, not a fixture shortcut.

**Observations (≥5):**
- [VERIFIED] CREATE branch is genuinely exercised and `created=True` is correct — evidence: the 72-12 seating block at `encounter_lifecycle.py:1074-1078` builds `_npc_by_name` and stamps **only** actors that already resolve to a roster Npc (`if _seated_npc is not None`); it never appends a new Npc. With no pre-existing "Corsair", the Npc is therefore created by the seam (`:178`, `created = npc is None` → True), so the span's `created=True` assertion proves the materialization path, not a pre-seed artifact.
- [VERIFIED] Production wiring (not a direct-seam call) — evidence: the three new tests route through `trigger_encounter` → `instantiate_encounter_from_trigger`; the win_condition gate at `:1216` selects `_seed_combat_hp_depletion_to_npcs` only for `WinCondition.hp_depletion`, which `test_world_loads_clean_under_swn` confirms is space_opera combat's win condition. This is precisely the "Every Test Suite Needs a Wiring Test" gap 72-8 left for the hp_depletion path.
- [VERIFIED] OVERWRITE branch + no-duplicate — evidence: pre-seeded "Corsair" (`_make_npc`, stale turn=2/"Old Hold") is matched by `by_name.get(actor.name)` at the seam, re-stamped to turn=8/"Docking Ring"; `len(corsairs)==1` confirms in-place refresh. The 72-12 seating block also stamps it with the SAME turn/location (both read `snapshot.turn_manager.interaction` + `party_location(perspective=player_name)`), so no double-advance — consistent with the test's single expected value.
- [DOC] Docstring tighten is accurate — evidence: `test_cite_known_npc_updates_last_seen_on_npc` (`test_npc_pool_narration_apply.py:57-72`) sets `character_locations`, exercising only the truthy-location prose branch; the revised module docstring now states exactly that and redirects the no-location claim to the presence path's own `test_presence_no_resolved_location_stamps_turn_not_location`. No stale/misleading comment remains. (comment-analyzer disabled — assessed directly.)
- [TEST] Assertions are non-vacuous — evidence: each new test asserts specific values (`==6`, `==8`, `=="Docking Ring"`, `created is True`, `len==1`) with diagnostic messages, and the CREATE test pins the precondition (`assert _opponent_npc(...) is None`) so a regression that pre-seeds the opponent would fail loudly. No `assert True`, no skips, no implementation-coupled greps. (test-analyzer disabled — assessed directly.)
- [SIMPLE] Proportionate — evidence: three focused tests + three small helpers, mirroring the established `_seated_combat`/`_player_character`/`_STATS` shape from `test_space_opera_swn_combat_e2e.py`. No over-engineering. (simplifier disabled — assessed directly.)
- [EDGE] Boundary paths covered — CREATE (no backing Npc), OVERWRITE (stale Npc), and no-resolved-location (pre-existing local test) are all present; the only uncovered combat-seam variant (opposed_check social opponent) is explicitly a separate deferred 72-8 follow-up, out of scope. (edge-hunter disabled — assessed directly.)
- [SILENT] No swallowed errors — `_space_opera_pack()` converts `PackNotFound` into an explicit `pytest.skip` (loud), not a silent empty return; the seam under test fails loud elsewhere. No empty except. (silent-failure-hunter disabled — assessed directly.)
- [TYPE] No type surface — test-only diff; helper return types are annotated (`-> Character`, `-> Npc | None`). No stringly-typed API or unsafe cast introduced. (type-design disabled — assessed directly.)
- [SEC] No security surface — local in-process test, no network/file-write sink, `location` is fiction-layer data to an in-memory snapshot. (security disabled — assessed directly.)
- [RULE] See Rule Compliance above — all applicable CLAUDE.md/SOUL.md rules COMPLIANT; the "tests don't point at content" rule's sanctioned-exception text applies and is cited. (rule-checker disabled — enumerated directly.)

**Error handling:** The content-absent path is the only failure mode — handled by `skipif(_has_real_content())` + `PackNotFound`→`pytest.skip`. Preflight confirms all 3 ran (content present), so the skip path is structural insurance, not the tested path.

### Devil's Advocate

Could this approve a green-but-hollow test? The sharpest attack: a test that "drives the production path" but whose assertions would pass even if presence-stamping were ripped out. I checked. If `_stamp_encounter_presence` were a no-op, the CREATE test's `last_seen_turn == 6` would fail (the freshly-created core defaults `last_seen_turn` to 0, not the encounter turn), and the OVERWRITE test would still read the stale `turn=2`/"Old Hold" — both fail loudly. So the assertions are load-bearing, not decorative. Second attack: does the test only *look* like it hits the production gate while actually short-circuiting? The seating block at `:1074-1078` runs for every encounter type and DOES stamp pre-existing Npcs — could it be the one doing the work in the OVERWRITE test, masking a broken seam? Possibly for OVERWRITE — but the CREATE test isolates the seam cleanly: the seating block provably creates nothing (it only mutates existing roster entries), so the only code that can produce a stamped "Corsair" there is the hp_depletion seam itself. The `created=True` span assertion further pins it to the seam's create branch, which the seating block cannot emit. Third attack: content coupling — if space_opera's authored combat win_condition silently flipped to `dial_threshold`, these tests would exercise `_publish_combat_edge_to_npcs` instead and the `created=True`/hp_depletion claims would be quietly wrong. Mitigation: `test_world_loads_clean_under_swn` already pins `combat.win_condition == hp_depletion` for the same pack, so a flip fails THAT test first — the coupling is guarded upstream. Fourth: a confused maintainer could read the skipif and assume the tests are optional; the inline comment block (12 lines) explains the sanctioned-exception rationale, mitigating that. Fifth: filesystem race — `GENRE_PACKS_DIR.is_dir()` evaluated at decoration time vs `find_pack_path` at call time could disagree if content is deleted mid-run; vanishingly unlikely in a test run, and the result is a loud skip, not a false pass. None of these rise to a blocking defect. The change is honest and the assertions bite.

**Handoff:** To SM (Captain Carrot Ironfoundersson) for finish-story.