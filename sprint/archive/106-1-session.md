---
story_id: "106-1"
jira_key: ""
epic: "106"
workflow: "tdd"
---
# Story 106-1: Equip starting armor at chargen and derive AC from the WWN SRD (ramp lever #1) — Leather Armor rolls into inventory with equipped:false so every Warrior fights at unarmored AC 10; equip the rolled armor and recompute armor_class from the WWN SRD armor entry (weapons already auto-equip; gap is armor-specific), with OTEL proving opponent reprisals roll vs the higher AC

## Story Details
- **ID:** 106-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-13T22:31:10Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-13T20:51:03Z | 2026-06-13T20:53:27Z | 2m 24s |
| red | 2026-06-13T20:53:27Z | 2026-06-13T21:05:47Z | 12m 20s |
| green | 2026-06-13T21:05:47Z | 2026-06-13T21:14:50Z | 9m 3s |
| review | 2026-06-13T21:14:50Z | 2026-06-13T21:23:14Z | 8m 24s |
| red | 2026-06-13T21:23:14Z | 2026-06-13T21:40:30Z | 17m 16s |
| green | 2026-06-13T21:40:30Z | 2026-06-13T21:47:35Z | 7m 5s |
| review | 2026-06-13T21:47:35Z | 2026-06-13T21:56:33Z | 8m 58s |
| finish | 2026-06-13T21:56:33Z | 2026-06-13T22:09:45Z | 13m 12s |
| green | 2026-06-13T22:09:45Z | 2026-06-13T22:21:48Z | 12m 3s |
| review | 2026-06-13T22:21:48Z | 2026-06-13T22:31:10Z | 9m 22s |
| finish | 2026-06-13T22:31:10Z | - | - |

## SM → DEV REWORK BRIEF (2026-06-13, post-finish duplicate-work resolution)

**Situation:** Story 106-1 was implemented TWICE in parallel. Develop already carries an independent, simpler 106-1 (`#836` server + `#436` content, merged ~17:19 by Keith from another workspace) BEFORE this oq-1 TDD session ran (20:51–21:56). This session's branch `feat/106-1-equip-starting-armor-derive-ac-wwn-srd` is a second, Reviewer-round-2-APPROVED implementation that conflicts with #836.

**Keith's ruling (2026-06-13):** REPLACE develop's #836 with this session's more thorough implementation (WARN content-gap convention, `max()` multi-piece rule, AC4 reason-branch coverage, 436 tests).

**Content status — DONE, do not touch:** Content PR #437 already merged (leather_armor `armor_class: 13`). Develop content also has #436 (shield_wood 13, helmet_iron intentionally unvalued → loud-fail). Compatible with this server impl. Verify only.

**Server reconciliation surface — `#836` added these to develop; this branch must SUPERSEDE them:**
- `sidequest/server/dispatch/chargen_loadout.py` (+110) — #836's `equip_starting_armor`. CONFLICT. Keep THIS branch's version.
- `sidequest/server/websocket_handlers/chargen_mixin.py` (+23) — #836's chargen-confirm wire. CONFLICT. Keep THIS branch's wire.
- `sidequest/telemetry/spans/chargen.py` (+47) — #836's `chargen.armor_equipped` / `chargen.armor_class_missing` spans + SPAN_ROUTES. This branch uses `chargen_armor_equipped` / `armor_unresolved` in `telemetry/spans/inventory.py` instead. REMOVE #836's competing armor spans + their SPAN_ROUTES so develop doesn't carry two span vocabularies for one subsystem (keep chargen.py if it holds unrelated spans — Dev judgment).
- `tests/server/test_106_1_chargen_armor_equip.py` (563 lines) — #836's tests, reference the OLD span names. DELETE/replace; will fail under this impl. This branch's tests (`test_106_1_chargen_armor_wire.py`, `test_106_1_equip_starting_armor.py`) replace them.

**Dev steps:** rebase branch onto `origin/develop`, resolve conflicts per above, drop #836's superseded spans + tests, full suite green + ruff/pyright clean, push. Then PR #838 goes clean → re-review (Avasarala) → SM finish.

**Open server PR:** `slabgorb-org/sidequest-server#838` (currently CONFLICTING — will clear on rebase). Content #437 already merged.

**Non-blocking carryovers from round-2 review (fix-forward):** two stale docstrings (`inventory.py:387` `(10 → derived)`, `test_106_1_equip_starting_armor.py:23` `WARN/ERROR`); `test_best_armor_max_independent_of_item_order` asserts return value only. Deferred epic-106 content follow-up: shield/helmet AC bonus-semantics (Keith ruling).

---

## Sm Assessment

**Ready for red phase.** Context doc (`sprint/context/context-story-106-1.md`) is unusually complete — confirmed code seams with file:line, a code-grounded root cause, explicit ACs, and the value oracle (WWN SRD). No setup gaps.

**Shape of the work (for TEA's test design):** two-sided bug, two repos.
- **Server**: a deterministic post-build chargen step that (a) equips kit-rolled armor and (b) recomputes `core.armor_class` from the equipped armor's catalog `armor_class`. Home: chargen-confirm wire after `apply_starting_loadout` (`chargen_mixin.py:1239`). Mirror `equip.py` resolve semantics.
- **Content**: add WWN-SRD `armor_class` (leather = 13) to `caverns_and_claudes/inventory.yaml` armor entries. The two are coupled — the AC-derivation test reads the content value.

**Five ACs to cover with failing tests first:** armor equips at chargen (AC1); AC derives from content not a constant — mutate-content-and-AC-follows (AC2); reprisal `ENCOUNTER_OPPONENT_ATTACK` span shows `target_ac=13` (AC3); missing catalog `armor_class` fails LOUD, no silent AC 10 (AC4); no regression — weapons stay equipped, unarmored/no-kit-armor classes stay AC 10, dedup + loadout unchanged (AC5).

**Doctrine flags TEA must honor (these are the gate, not nice-to-haves):**
- **OTEL is the acceptance gate** — emit a chargen armor-derivation span (reuse `telemetry/spans/inventory.py` equip family or add `chargen.armor_equipped`). Prefer OTEL-span + fixture-driven behavior tests over source-text wiring tests (server CLAUDE.md "No Source-Text Wiring Tests").
- **No silent fallback** — AC4 is the contract; missing content value must surface at chargen.
- **No invented numbers** — leather = 13 comes from the WWN SRD armor table; cite the SRD row in the content PR (standing ruling 2026-06-13).

**Watch items (non-blocking, route to Architect/Keith if hit):** the multi-piece armor combination rule (torso + shield + helm in `warrior_kit.armor`) — WWN uses best-armor AC + flat shield bonus, NOT additive. If the SRD is genuinely silent on a combination, **escalate to Keith, do not invent**. Story scope can stay leather-first; note chain_shirt/shield_wood/helmet_iron as follow-on if the combo rule forces them.

**Coordination:** 106-2 also touches `dice.py` (to-hit/damage side, not AC) — coordinate to avoid merge churn. Land server + content PRs together.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3-pt bug fix with mechanical + content surface; behavior must be pinned before Dev.

**Test Files:**
- `sidequest-server/tests/server/test_106_1_equip_starting_armor.py` — unit/behavior on the new `equip_starting_armor` step (AC1, AC2, AC4, AC5) + OTEL gate span.
- `sidequest-server/tests/integration/test_106_1_reprisal_vs_derived_ac.py` — AC3 end-to-end: derived AC reaches the `dice.py` reprisal (`encounter.opponent_attack_resolved` `target_ac`), with an unarmored=10 control.
- `sidequest-server/tests/integration/test_106_1_caverns_armor_content.py` — content half: caverns `leather_armor.armor_class == 13` (WWN SRD).

**Tests Written:** 10 tests covering 5 ACs + the OTEL gate. **Status:** RED (9 failed, 1 passing control) — `10344cae`.

**The contract I pinned for Dev (define these or the tests stay red):**
- New step `equip_starting_armor(character, inventory_config, *, genre, world, player_id)` in `sidequest/server/dispatch/chargen_loadout.py` (alongside `apply_starting_loadout`), called from the chargen-confirm wire (`chargen_mixin.py:1239`) **after** `apply_starting_loadout`.
- Equips armor-category inventory items (flip `equipped`), recomputes `character.core.armor_class` from the equipped armor's catalog `armor_class` (best-armor; **content-derived, never a constant**).
- OTEL span `chargen.armor_equipped` (INFO) with attrs `item_id`, `armor_class`, `ac_before`, `ac_after`, `equipped_after`.
- OTEL span `chargen.armor_unresolved` (WARN/ERROR) when an equipped armor item has no catalog `armor_class` — the No-Silent-Fallback gate. Legitimately unarmored (no armor item) fires NEITHER span and stays AC 10.
- Content: add `armor_class: 13` to `caverns_and_claudes/inventory.yaml` `leather_armor` (cite the WWN SRD row in the content PR).

### Rule Coverage

Language: Python — `.pennyfarthing/gates/lang-review/python.md` (13 checks). Most are N/A to a small chargen step; the applicable ones:

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exception swallowing / No-Silent-Fallback | `test_missing_catalog_armor_class_fails_loud` | failing (RED) |
| #4 logging coverage & correctness (error path is observable) | `test_missing_catalog_armor_class_fails_loud` (loud span), `test_armor_equipped_span_carries_derivation_attrs` | failing (RED) |
| #6 test quality (meaningful assertions, no vacuous) | self-check (Phase C) | passed |

**Rules checked:** 3 of 13 lang-review rules are applicable and have coverage. N/A here: #2 mutable defaults, #3 type-annotation boundaries (Dev's impl concern — flagged for review), #5 path handling, #7 resource leaks, #8 unsafe deserialization, #9 async, #10 import hygiene, #11 input validation, #12 dependency hygiene, #13 fix-regressions (Dev/verify-phase concern).
**Self-check:** 0 vacuous tests — every test asserts a specific value or span; the AC4 negative also asserts the derivation span did NOT fire.

**Handoff:** To Dev (Naomi) for GREEN.

### Red Rework (round 2 — closing Reviewer's testable gaps)

**Tests Required:** Yes — Reviewer REJECTED for missing coverage over a correct implementation ("the gaps are testable"). The impl is sound (Reviewer traced it end-to-end); this round HARDENS coverage so a regression can't slip through green.

**Test Files (this round):**
- `sidequest-server/tests/server/test_106_1_chargen_armor_wire.py` — **NEW. The HIGH wiring test.** Drives the real `_chargen_confirmation` through `handle_message` (45-2 shape, hermetic `flickering_reach` world) and asserts the armor-derivation step fires from the production wire (`chargen_mixin.py:1257`). Roll-agnostic: warrior_kit rolls exactly one armor piece, so exactly one of {`chargen.armor_equipped`, `chargen.armor_unresolved`} MUST fire; branch-asserts AC=13+equipped (leather) or AC=10+loud (shield/helm). Pre-condition asserts NO armor span before confirmation.
- `sidequest-server/tests/server/test_106_1_equip_starting_armor.py` — **+7 tests** added:
  - `test_best_armor_max_wins_over_lower_piece`, `test_best_armor_max_independent_of_item_order`, `test_best_armor_fires_one_equipped_span_per_armor_piece`, `test_best_armor_skips_missing_piece_but_derives_from_valued_one` — the MEDIUM `max()` multi-piece branch (sum/first/order regressions caught).
  - `test_unresolved_reason_is_catalog_armor_class_missing`, `test_unresolved_reason_is_no_catalog_entry`, `test_none_inventory_config_armor_fails_loud_no_catalog_entry` — the MEDIUM AC4 sub-branches + the `reason` GM-panel discriminator.
- `sidequest-server/tests/integration/test_106_1_reprisal_vs_derived_ac.py` — LOW [DOC]: replaced drift-prone `dice.py:1636` line-refs with the symbol `resolve_opponent_attack` / `player_core.armor_class` in two docstrings.

**Wiring-test regression proof (statically airtight):** `grep` confirms the armor spans are emitted ONLY inside `equip_starting_armor` (chargen_loadout.py:388/410), whose ONLY production caller is `chargen_mixin.py:1257`. Remove that line → zero armor spans → the wire test's `total == 1` assertion fails. This is the canonical OTEL wiring-test pattern (server CLAUDE.md "No Source-Text Wiring Tests" — assert the span fired through the real handler).

**Status:** GREEN against the existing (correct) implementation — 18/18 story tests + 51/51 with adjacent regression (chargen_loadout, 45-2 wire, reprisal e2e, content, routing-completeness). These are regression guards: each fails if the specific behavior breaks. Ruff + format clean on all touched test files.

### Rule Coverage (rework)

| Reviewer finding | Test(s) | Status |
|------|---------|--------|
| `[HIGH][TEST]` no production-wire test | `test_chargen_confirm_fires_armor_derivation_through_real_wire` | GREEN (fails if wire dropped) |
| `[MEDIUM][TEST]` `max()` multi-piece untested | `test_best_armor_max_*` (×4) | GREEN |
| `[MEDIUM][TEST]` AC4 `no_catalog_entry` / `None` config / `reason` unasserted | `test_unresolved_reason_*` (×2) + `test_none_inventory_config_*` | GREEN |
| `[LOW][DOC]` drift-prone `dice.py:1636` refs | docstring symbol-name fix (×2) | done |

**Not in TEA's lane (left for Dev/Reviewer):** `[LOW][RULE]` WARNING-vs-ERROR mismatch in `chargen_loadout.py`/`inventory.py` (a source decision, not a test); the `[LOW][DOC]` "AC stays 10" → "AC unchanged" docstring wording in production source; the blocking shield/helmet Keith ruling (escalation, not code).
**Self-check:** 0 vacuous — every new test asserts a specific value/span/reason; the wire test's pre-condition + branch-asserts keep it non-vacuous on both roll outcomes.

**Handoff:** To Dev (Naomi) for GREEN — the [LOW][RULE] WARNING/ERROR alignment and the [LOW][DOC] production-source docstring wording are minor source fixes; all test coverage gaps are now closed and green.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 10/10 story tests GREEN; 47/47 adjacent regression GREEN (chargen_loadout, opponent_reprisal_e2e, cc_chargen_e2e). Ruff clean; pyright clean on new code (the 16 pyright errors in chargen_mixin.py are pre-existing mixin `_room`/attr artifacts, none in the edited region).

**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/chargen_loadout.py` — new `equip_starting_armor(character, inventory_config, *, genre, world, player_id) -> int`: equips armor-category items, derives `core.armor_class` from the equipped armor's catalog `armor_class` (best-armor = max), loud `chargen.armor_unresolved` when a value is missing, silent no-op when genuinely unarmored.
- `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` — wired `equip_starting_armor` into the chargen-confirm path immediately after `apply_starting_loadout`, reusing the same resolved `InventoryConfig`.
- `sidequest-server/sidequest/telemetry/spans/inventory.py` — `chargen.armor_equipped` (INFO) + `chargen.armor_unresolved` (ERROR) spans with `SPAN_ROUTES` registration (GM-panel visible).
- `sidequest-content/genre_packs/caverns_and_claudes/inventory.yaml` — `leather_armor` gains `armor_class: 13` (WWN SRD).

**Branch:** `feat/106-1-equip-starting-armor-derive-ac-wwn-srd` — pushed in both repos (server `cb714678`, content `c2801e0`).

**Wiring note (self-review):** the new step is reachable in production via the chargen-confirm handler, not just the unit tests — `chargen_mixin.py` calls it after the loadout pass. The integration test proves the derived AC reaches `dice.py`'s reprisal `target_ac`.

**Handoff:** To next phase (verify/review). **Flagging for Keith/Reviewer:** see the blocking delivery finding below — leather is fixed but `warrior_kit` also rolls `shield_wood`/`helmet_iron`, which still fail-loud; the ramp is only partially closed until those get WWN-sourced values.

### Green Rework (round 2 — Reviewer LOW source nits)

After TEA closed the test-coverage gaps (HIGH wiring test + MEDIUM max/AC4 branches, all green), the only remaining items in Dev's lane were the two LOW **source** findings. Both addressed; no functional/behavioral change.

**Files Changed (this round):**
- `sidequest-server/sidequest/telemetry/spans/inventory.py` — `[LOW][RULE][DOC]` resolved the WARNING-vs-ERROR mismatch by aligning `chargen.armor_unresolved` **down** to the sibling content-gap convention (`chargen.starting_equipment_missing` = `logger.warning` + unset span status). Dropped `span.set_status(Status(StatusCode.ERROR, …))` from `chargen_armor_unresolved_span`; module comment + helper docstring now say `(WARN)`. Rationale: a missing `armor_class` on an inventory.yaml entry is a **content authoring gap**, not a runtime engine failure like `equip.unresolved` (which legitimately stays ERROR). Log + status + comment now agree on WARN. (`Status`/`StatusCode` import retained — still used by `equip_unresolved_span`.)
- `sidequest-server/sidequest/server/dispatch/chargen_loadout.py` — `[LOW][DOC]` `equip_starting_armor` docstring "AC stays 10" → "AC unchanged (the unarmored default, normally 10 — but a world override may pre-seed it)"; matching inline comment softened. Ruff also normalized two pre-existing multi-line constructs (a ternary + a split log string) that now fit on one line — whitespace-only, no semantic change.

**Not changed (deliberate):**
- `[LOW][DOC]` content SRD locator — the `leather_armor` comment in `inventory.yaml` already names the table and quotes the entry ("Worlds Without Number, Armor: 'Leather, AC 13'"); the WWN SRD has no stable page numbers, and inventing one would be worse. Left as-is.
- `[LOW][DOC]` test-docstring `dice.py:1636` line-refs — already fixed by TEA in the red-rework round (replaced with the `resolve_opponent_attack` symbol name).

**Tests:** 436 GREEN (50 story + adjacent: equip-armor, wire, reprisal-e2e, chargen_loadout, routing-completeness; 386 telemetry). Ruff check + format clean, pyright clean on both changed files. Verified by Engineering Console (testing-runner, RUN_ID `106-1-dev-green`).

**Branch:** `feat/106-1-equip-starting-armor-derive-ac-wwn-srd` — server `f334aee4` (this round) + `7102f5c4` (TEA tests), pushed.

**Handoff:** To Reviewer (Avasarala) — all REJECT findings addressed: HIGH wiring + MEDIUM coverage (TEA), LOW source nits (Dev). The blocking `warrior_kit` shield/helmet shortfall remains a deferred Keith ruling (not this story's code-scope), now machine-documented by the wire test's branch-asserts.

### Green Rework (round 3 — duplicate-implementation reconciliation against develop's #836)

**Why:** At finish, SM (Drummer) discovered 106-1 had been implemented TWICE in parallel — develop already carried an independent, simpler 106-1 (`#836` server + `#436` content, merged ~17:19) before this session's approved branch existed. **Keith's ruling: REPLACE #836 with this session's more thorough implementation.** This round merges develop in and supersedes #836; **zero change to 106-1 behavior or coverage** — the approved code is preserved verbatim.

**What I did:**
- `git merge origin/develop` → two `UU` conflicts (`chargen_loadout.py`, `chargen_mixin.py`), both purely #836-vs-mine on the same function. Resolved to MINE (HEAD): `checkout --ours` on `chargen_loadout.py` (verified only #836 touched it on develop, so ours is the complete correct file), manual hunk-keep on `chargen_mixin.py` (variable name `resolved_inventory` over #836's `loadout_inventory`; identical wiring).
- **Superseded #836's silent ride-ins** (additions on theirs-only, no conflict marker): restored base `sidequest/telemetry/spans/chargen.py` (`git checkout HEAD --`, dropping #836's orphaned `chargen.armor_equipped`/`chargen.armor_class_missing` span defs + SPAN_ROUTES — my spans live in `inventory.py`); `git rm` #836's `tests/server/test_106_1_chargen_armor_equip.py` (asserts the old span vocabulary). Grepped the tree: zero orphan references to #836's symbols remain.
- Kept all unrelated develop progress brought by the merge (#835 region/movement/bearings work — ~24 files auto-merged).
- One incidental in-passing fix: `ruff I001` on `tests/game/pg/test_telemetry_sink_missing_session.py` (develop's pre-existing un-sorted import, committed by 700e7c82; the merge inherited it and it would have reddened this PR's lint gate). One-line import sort, zero behavior. See delivery finding.

**Tests:** Full server suite **11998 passed / 0 failed / 338 skipped** (`uv run pytest`, RUN_ID `106-1-dev-green-rework`). All 18 story-106-1 tests green. `ruff check .` clean (whole repo). pyright clean on changed files. #836's deleted test confirmed not collected.

**Branch:** `feat/106-1-equip-starting-armor-derive-ac-wwn-srd` — pushed (`f334aee4..c9251feb`, merge `9f1160c6` + lint `c9251feb`). **PR `slabgorb-org/sidequest-server#838`: now MERGEABLE / CLEAN** (was CONFLICTING). Content PR `#437` already merged earlier in the finish flow.

**Handoff:** To Reviewer (Avasarala) — re-review the reconciliation. The 106-1 implementation itself is unchanged from the round-2 APPROVED state; what's new is the develop merge, the supersession of #836, and the one incidental lint fix. No behavior delta to re-litigate; verify the merge introduced nothing and #836 left no orphans.

## Subagent Results (Round 3 — reconciliation re-review)

Review surface: `git diff origin/develop...HEAD` (the TRUE 106-1 net diff; local `develop` was stale and showed #835's merged region work — used `origin/develop`). Surface = my impl replacing #836's (`chargen_loadout.py`, `chargen_mixin.py`), `chargen.py` −47 (#836 spans removed), `inventory.py` +124 (my spans), `test_106_1_chargen_armor_equip.py` −563 (#836 test deleted), my 3 test files, + a 2-line inherited lint fix.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 11997 pass / 0 fail (1 unrelated xdist teardown flap, passes isolated); ruff clean; pyright clean on 106-1 files (16 chargen_mixin errors PRE-EXISTING on develop, identical lines); #836 test not collected | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (all Medium) | confirmed 4 as non-blocking fix-forward (none a reconciliation regression) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (high-conf, low-sev) | confirmed 2 — the known round-2 doc carryovers (LOW) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean (3 minor) | 16 rules/61 instances; A1–A5 all compliant | confirmed 0 blocking; 3 minor (test-helper annotation, /tmp test save_dir per convention, span-attr migration note) all non-blocking |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 Critical, 0 High, 4 Medium (coverage fix-forward), 2 Low (doc), 3 minor (rule) — all non-blocking.

## Rule Compliance (Round 3)

The reconciliation preserves the round-2 APPROVED implementation **byte-identical** (verified: `git diff f334aee4 HEAD` on `chargen_loadout.py` + `inventory.py` is empty). So the round-2 Rule Compliance findings (the WARNING/ERROR item, now RESOLVED to WARN; OTEL spans registered; No-Silent-Fallback) carry forward verbatim. New surface this round:

- **No Silent Fallbacks (server CLAUDE.md `<critical>`)** — rule-checker A1: `inventory_config=None` → empty catalog → loud `chargen.armor_unresolved`; `armor_class=None` → loud, reason discriminator; genuinely-unarmored → silent no-op (correct, not a gap). **Compliant.**
- **OTEL Observability Principle** — A2: both `chargen.armor_equipped` + `chargen.armor_unresolved` registered in `SPAN_ROUTES` (inventory.py), GM-panel visible. **Compliant.**
- **No Source-Text Wiring Tests / Every Suite Needs a Wiring Test** — A4/A5: the surviving wire test (`test_106_1_chargen_armor_wire.py`) drives the real `handle_message → _chargen_confirmation → equip_starting_armor` path and asserts exactly one armor span — the HIGH wiring hole from round 1 stays CLOSED through the merge. **Compliant.**
- **Supersession completeness** — `chargen.py` restored to base (−47, #836's spans gone); `#836` test deleted (−563); independent grep for `chargen.armor_class_missing` (the #836 span NAME) returns ZERO across the tree. The `catalog_armor_class_missing` matches are my own `reason` discriminator strings, not #836's span. **No orphans. Compliant.**
- **#3 Type annotations** — one test-internal helper `_equip_starting_armor` lacks annotations (rule exempts private helpers; test-only, no production boundary). Minor.

## Reviewer Assessment (Round 3 — reconciliation re-review)

**Verdict:** APPROVED

This round did not re-author 106-1 — it merged `origin/develop` into the branch and made my round-2-APPROVED implementation supersede a competing, separately-merged implementation (#836) per Keith's explicit ruling. I verified the three things that could have gone wrong in a merge-and-supersede and none did.

**Data flow re-traced (unchanged, re-confirmed live post-merge):** content `armor_class: 13` → `equip_starting_armor` best-armor `max()` → `core.armor_class` → `dice.py` reprisal `target_ac`. The `test_106_1_reprisal_vs_derived_ac` e2e still proves the derived AC reaches dispatch.

**Observations:**
- `[VERIFIED]` **The approved implementation survived the merge byte-identical.** `git diff f334aee4 HEAD -- sidequest/server/dispatch/chargen_loadout.py sidequest/telemetry/spans/inventory.py` is empty. The merge changed no 106-1 logic — evidence the round-2 approval still holds without re-litigation.
- `[VERIFIED]` **#836 superseded cleanly, zero orphans.** Diff shows `telemetry/spans/chargen.py` −47 (restored to base, #836's `chargen.armor_equipped`/`chargen.armor_class_missing` defs + SPAN_ROUTES gone) and `tests/server/test_106_1_chargen_armor_equip.py` −563 (deleted). Independent grep for the #836 span-name string `chargen.armor_class_missing` returns zero. Confirmed by [RULE] A4.
- `[VERIFIED]` **The HIGH wiring test (round-1 reject basis) survives the merge.** `test_106_1_chargen_armor_wire.py` still drives the real handler and asserts exactly one armor span fires from production; preflight confirms it green. The lethality lever cannot silently regress. Confirmed by [RULE] A5 + [preflight].
- `[VERIFIED]` **Suite green against merged develop.** 11997 pass / 0 fail (the lone fail is a pre-existing psycopg xdist-teardown flap on an unrelated 102-5 test, green in isolation — [preflight]); ruff clean repo-wide; pyright clean on changed files. The 16 `chargen_mixin.py` pyright errors are inherited develop debt (identical line numbers on the develop baseline), not introduced here.
- `[MEDIUM][TEST]` **Four non-blocking coverage fix-forwards** ([TEST]): (1) idempotency of `equip_starting_armor` deleted with #836, unreplaced — but the function has exactly one production caller at chargen-confirm (round-2 established) and is not re-run on save-reload, so the double-call risk is theoretical; (2) span `item_name`/`pc_name` attrs unasserted (the #836 test didn't assert them either — not a regression); (3) the span-name constant-string pin deleted with #836 — the global `test_routing_completeness` still guards SPAN_ROUTES registration, only the literal-string pin is gone; (4) unresolved branch doesn't assert `equipped` stays `False`. All Medium → non-blocking; recommend folding into the shield/helmet epic follow-up.
- `[LOW][DOC]` **Two known round-2 carryovers persist** ([DOC], high-confidence): `inventory.py:376` docstring `(10 → derived)` (ac_before may be world-pre-seeded) and `test_106_1_equip_starting_armor.py` module docstring `WARN/ERROR` (now WARN-only). Already logged round-2 as fix-forward; still LOW, still non-blocking.
- `[LOW][RULE]` **Span-attribute schema migration vs #836** ([RULE] #13): my spans use `pc_name`/`item_id`/`item_name`/`equipped_after` where #836 used `class_name`/`armor_item_id`/`equipped`. Intentional — #836 is being superseded and was only live a few hours; no established dashboard consumer. Operational note, not a code violation.

**Dismissed:**
- `[RULE]` `/tmp` test save_dir (#5) — DISMISSED: established test convention across the suite (test_render_backpressure.py, test_multiplayer_party_status.py); the retired-`/tmp` note is about service logs, not test fixtures. rule-checker itself marked it compliant-per-convention.

### Devil's Advocate

Argue this should be rejected. Sharpest angle: I am APPROVING a change that DELETES 563 lines of already-merged, presumably-once-tested code (#836) and replaces a live implementation on develop — is that not a reckless net-negative-coverage move dressed as a "reconciliation"? If #836's test covered an idempotency case and a span-attribute contract that my surviving tests don't, then merging this strictly *reduces* the project's defense against the exact silent-AC-10 regression the story exists to prevent. The test-analyzer flagged precisely this: idempotency gone, `item_name` unasserted, the constant-pin gone. Second angle: the span-attribute schema migration is a real breaking change — anything that read #836's `armor_item_id`/`class_name` now silently gets `None`. Third: I verified "byte-identical" only on two files; the merge touched ~24 others (develop's region/movement work) — am I rubber-stamping a 2568-line merge by looking at two files? Rebuttals. (1) The coverage "loss" is illusory: the load-bearing HIGH wire test — the round-1 reject basis and the only structural defense against silent AC-10 regression — is in MY surviving suite and verified green from the real handler; #836's idempotency/constant-pin gaps are Medium fix-forwards, and #836's test asserted the OLD span vocabulary that no longer exists, so keeping it was never an option. (2) The schema migration breaks nothing real: #836 merged ~17:19 today and is being explicitly superseded hours later per Keith's ruling; there is no aged dashboard consumer of its attribute names, and my SPAN_ROUTES extract + tests are internally consistent. (3) The ~24 other files are develop's own committed, CI-green work that I merged unmodified — `git diff f334aee4 HEAD` empty on the 106-1 impl files proves I didn't perturb them, and the full suite is green against the merged tree, which exercises that integration far more thoroughly than my reading two files would. Nothing rises to High. The implementation was correct and approved; the merge preserved it and removed a duplicate cleanly. APPROVE.

**Handoff:** To SM (Drummer) for finish-story. The 4 Medium coverage fix-forwards + 2 LOW doc carryovers + the standing shield/helmet epic follow-up are recorded as non-blocking delivery findings. PR `slabgorb-org/sidequest-server#838` is MERGEABLE/CLEAN; content `#437` already merged.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 57 passed, ruff/pyright/yaml clean; 3 runtime pack-guard skips (legit) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 4, downgraded 3 to low |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 (all low) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 1, dismissed 2 (convention) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 6 confirmed (1 High, 3 Medium, then folded LOWs), 2 dismissed (with rationale), shield/helmet content gap deferred (escalation, not this story)

## Rule Compliance

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) + server CLAUDE.md `<critical>` rules, enumerated against every changed symbol:

- **#1 Silent exceptions** — `equip_starting_armor` has no `try/except`; the missing-value case is an explicit `None`-check + `continue`, not a swallow. The `with chargen_armor_*_span(...): pass` blocks are **not** exception swallows (no `except`); they match the pervasive telemetry convention (`equip_resolved_span`, `item_resource_depleted_span`, every helper in `inventory.py`). **Compliant.**
- **#2 Mutable defaults** — all new defaults are `str`/`None`/`int` literals. **Compliant.**
- **#3 Type annotations** — `equip_starting_armor` and both span helpers fully annotated incl. return types; `**attrs: Any` is acceptable for OTEL spread. Test helpers are exempt (private). **Compliant.**
- **#4 Logging level** — `logger.warning` on the `armor_unresolved` path while the OTEL span sets `StatusCode.ERROR` and the module comment labels it `(ERROR)`. **Inconsistent — confirmed finding (LOW).** (Note: the sibling content-gap `SPAN_CHARGEN_STARTING_EQUIPMENT_MISSING` uses `logger.warning` too, so warning matches *that* convention — the defect is the comment/span claiming ERROR while the log says WARNING; pick one.)
- **#5 Path handling** — N/A (no paths). **#7 Resource leaks** — spans use `with`. **#8 Deserialization** — dict.get on pydantic-sourced dicts. **#9 Async** — sync fn in sync-compatible call site. **#10 Imports** — explicit named imports, no star added (the `import *` in spans/__init__ is pre-existing). **#11/#12** — no untrusted input, no deps. **All compliant.**
- **#6 Test quality** — assertions are specific (no vacuous); but COVERAGE is incomplete — see findings. **Compliant on quality, gapped on coverage.**
- **server CLAUDE.md `<critical>` — "Every Test Suite Needs a Wiring Test" / "Verify Wiring, Not Just Existence"** — **VIOLATION (High).** All seven `equip_starting_armor` tests call the function directly; nothing drives the `chargen_mixin` confirm path to prove the production wire is live. A refactor that drops the call regresses the exact bug, silently, with every test green.
- **OTEL Observability Principle** — new spans are route-registered in `SPAN_ROUTES` (GM-panel visible). **Compliant.**

## Reviewer Assessment

**Verdict:** REJECTED

The implementation is genuinely good — `equip_starting_armor` is clean, correctly sequenced after `apply_starting_loadout`, content-sourced (no invented numbers), fails loud on the gap, and pyright/ruff/57-test green. I traced the data flow end to end and it holds: content `armor_class: 13` → `core.armor_class` (best-armor max) → `dice.py` reprisal `target_ac`. But it ships with a hole that the project's own `<critical>` rules forbid, and that hole is over the most load-bearing wire in the story.

**Observations:**
- `[HIGH][TEST]` **No wiring test for the production chargen path.** `chargen_mixin.py:1257` calls `equip_starting_armor`, but every test invokes it directly — `tests/server/test_106_1_equip_starting_armor.py` (all 7) + the reprisal integration. `cc_chargen_e2e` uses `builder.build()` directly, NOT the mixin confirm path, so it doesn't cover the wire either. Drop the call and the suite stays green while every Warrior silently reverts to AC 10 — re-breaking ramp lever #1. Violates server CLAUDE.md "Every Test Suite Needs a Wiring Test." Confirmed by [TEST] and my own enumeration.
- `[MEDIUM][TEST]` **best-armor `max()` path untested.** `equip_starting_armor` implements `ac_after = max(...)` across multiple equipped armor pieces (Dev deviation #2), but no test exercises two armor items — the documented multi-piece branch is dead-on-arrival from a coverage standpoint.
- `[MEDIUM][TEST]` **AC4 under-covered.** Only the `catalog_armor_class_missing` reason is exercised; the `no_catalog_entry` path and `inventory_config=None` (both real production branches) are untested, and the `reason` span attribute — the GM-panel discriminator — is never asserted.
- `[LOW][RULE][DOC]` **WARNING-vs-ERROR mismatch** at `chargen_loadout.py` (warning log) vs the `inventory.py` span/comment (ERROR). Pick one; both fire, so it's loud either way, but the lie-detector and the log file disagree. Confirmed by [RULE] and [DOC].
- `[LOW][DOC]` **Docstring "AC stays 10"** is literally false if a world override pre-set AC; should read "AC unchanged." Drift-prone `dice.py:1636` line refs in two test docstrings — use a symbol name. Content SRD citation names the table/value but lacks a locator.
- `[VERIFIED]` **No-invented-numbers honored** — `core.armor_class` derives from `CatalogItem.armor_class` (chargen_loadout.py:`catalog_ac = catalog_item.armor_class`), never a literal; content carries `13`. Complies with the 2026-06-13 WWN-SRD standing ruling.
- `[VERIFIED]` **No silent fallback on the gap** — chargen_loadout.py emits `logger.warning` + an ERROR-status `chargen.armor_unresolved` span before `continue`; AC is not fabricated. Complies with No-Silent-Fallback.
- `[VERIFIED]` **OTEL gate live** — both spans registered in `SPAN_ROUTES` (inventory.py), GM-panel visible.

**Dismissed:**
- `[RULE] with span(): pass` (×2, rule #1) — DISMISSED: not exception swallowing (no `except` clause); it is the established pattern for every span helper in `inventory.py` (`equip_resolved_span`, `item_resource_depleted_span`). The rule-checker itself conceded it matches convention. A `Span.open` raise would be a systemic telemetry failure, not a defect of this diff.

### Devil's Advocate

Argue the code is broken. The most damning angle is the one I'm rejecting on: this is a *silent-regression trap dressed as a fix*. The entire reason this story exists is that a mechanical value (`armor_class`) silently did nothing — "convincing narration with zero mechanical backing," the precise failure the OTEL doctrine and the wiring-test rule exist to kill. And the fix reintroduces the same class of risk one layer up: the production behavior hangs entirely on a single un-guarded call at `chargen_mixin.py:1257`, with no test that fails if it disappears. A future dev refactoring the chargen-confirm handler (splitting the loadout block, reordering, extracting a helper) deletes or bypasses that line, runs the suite, sees 57 green, and ships. Every Warrior is back at AC 10, the meat-grinder returns, and the GM panel — which *would* show the missing `chargen.armor_equipped` span — is never consulted because no test asserts it fires from the real pipeline. That is not hypothetical; it is exactly how the original bug survived. Second angle: a confused content author adds `shield_wood` to a Warrior's hands expecting protection; the kit rolls it; `no_catalog_entry`/`catalog_armor_class_missing` fires and the PC stands at AC 10 — and because that branch has no test asserting the `reason`, a regression in the discriminator (e.g. both reasons collapsing to one string) would pass unnoticed, blunting the GM panel's ability to tell "author forgot the value" from "item isn't in the catalog at all." Third: the `max()` combination is undefended — if a later story values shield as a set-AC by mistake, best-armor would silently pick the wrong piece and no test would catch the swing. None of these are style nits; each is a mechanical-truth failure of the kind SOUL.md's OTEL principle is built to prevent. The fix is correct today and fragile tomorrow, and "correct today" is not the bar for a lethality lever.

**Handoff:** Back to TEA (red rework) — the gaps are testable.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): `warrior_kit.armor` rolls exactly ONE piece from `[leather_armor, shield_wood, helmet_iron]` (no `rolls_per_slot` override; default 1), so the dreaded multi-piece (torso+shield+helm) combination is NOT currently reachable for the Warrior. Affects `sidequest-content/genre_packs/caverns_and_claudes/equipment_tables.yaml` (no change needed now; the best-armor combination rule can stay deferred per story scope). *Found by TEA during test design.*
- **Gap** (non-blocking): `shield_wood` and `helmet_iron` also declare no catalog `armor_class`, so if the Warrior rolls one of those instead of leather, the new step will hit the `chargen.armor_unresolved` fail-loud path. Affects `sidequest-content/genre_packs/caverns_and_claudes/inventory.yaml` (Dev should decide: give all three armor pieces their WWN-SRD values now, or accept the loud span for non-leather rolls). Tests pin leather (the mandatory scope item) only. *Found by TEA during test design.*

#### Red rework (round 2)
- **Gap** (blocking — for Keith, RE-CONFIRMING Dev's + Reviewer's escalation): the new wiring test makes the ramp-lever shortfall undeniable and now machine-verified. `warrior_kit.armor` is a uniform 1-of-3 pick over `[leather_armor, shield_wood, helmet_iron]`, and ONLY `leather_armor` carries `armor_class` (13) — so a real Warrior has only ~1/3 odds of getting AC raised; ~2/3 roll shield/helmet → loud `chargen.armor_unresolved` → still AC 10. The story's stated purpose ("every Warrior fights at AC 10 → fix it", the single biggest survivability lever) is only ~1/3 delivered in production. Affects `sidequest-content/genre_packs/caverns_and_claudes/{inventory.yaml,equipment_tables.yaml}` — needs the same Keith ruling already logged (source shield as +1 via the deferred combination rule / re-key the kit so torso armor is guaranteed / drop shield+helmet from the armor slot). NOT this story's code-scope to fix; the test now branch-documents both outcomes so the fix can't regress silently. *Found by TEA during test design (rework).*
- **No upstream findings** beyond the above — the implementation under test is correct; the rework added the missing coverage (wiring + max + AC4 branches), all GREEN against the existing impl. *Found by TEA during test design (rework).*

### Dev (implementation)
- **Question** (blocking — for Keith): `warrior_kit.armor = [leather_armor, shield_wood, helmet_iron]` rolls ONE piece uniformly, but only `leather_armor` got a WWN-SRD `armor_class` (13). A Warrior who rolls `shield_wood` or `helmet_iron` now fires `chargen.armor_unresolved` and stays at AC 10 — so this "ramp lever #1" only closes for ~1/3 of Warriors. I did NOT invent values: WWN models a shield as a flat **+1 AC bonus** (not a set AC), which the current set-AC `armor_class` model can't express without the deferred combination/bonus rule; and WWN has **no helmet item** at all (genuinely SRD-silent). Affects `sidequest-content/genre_packs/caverns_and_claudes/inventory.yaml` + `equipment_tables.yaml` (needs a Keith ruling: source shield as +1 via the deferred combination rule, drop helmet/shield from the kit's armor slot, or re-key the kit so torso armor is guaranteed). Per the SM watch-item: escalate, do not invent. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `equip_starting_armor` uses best-armor (max catalog `armor_class`) when multiple armor pieces are equipped — a deliberate WWN-faithful placeholder (WWN sets AC from the single best armor, not additive). The shield **+1 bonus** and any layering rule are NOT implemented (deferred per story scope). Affects `sidequest-server/sidequest/server/dispatch/chargen_loadout.py` (a future story owns the combination/bonus rule). *Found by Dev during implementation.*

#### Green rework (round 2)
- **No new upstream findings.** The two LOW source nits are resolved (WARN-vs-ERROR alignment + docstring accuracy); no behavioral change. The blocking `warrior_kit` shield/helmet shortfall (~2/3 of Warriors still fail-loud at AC 10) remains open and unchanged — still a deferred Keith ruling on `sidequest-content/genre_packs/caverns_and_claudes/{inventory.yaml,equipment_tables.yaml}`, NOT this story's code-scope. TEA's new wire test now branch-documents both roll outcomes so the shortfall can't regress silently once Keith rules. *Found by Dev during implementation (rework).*

#### Green rework (round 3 — #836 reconciliation)
- **Gap** (non-blocking): develop HEAD fails `ruff check .` — `tests/game/pg/test_telemetry_sink_missing_session.py` has an un-sorted import block (I001), committed by develop 700e7c82, not by 106-1. The 106-1 merge inherited and fixed it in-passing to keep this PR's lint gate green. Affects `sidequest-server/tests/game/pg/test_telemetry_sink_missing_session.py` (already fixed here; flag is that develop's CI/lint gate apparently let un-sorted imports land — worth a hygiene check on the lint gate). *Found by Dev during implementation (rework).*
- **Process** (non-blocking, for the team): story 106-1 was fully implemented TWICE in parallel (this oq-1 TDD session + Keith's #836/#436 from another workspace) because the keyless story had no cross-workspace lock and the sprint YAML showed it open. ~2 hours of duplicated TDD effort. Affects sprint coordination — a keyless story should be claimed/marked in-progress visibly before work starts in any clone. *Found by Dev during implementation (rework).*
- **No other upstream findings.** The reconciliation preserved the approved implementation; #836's superseded spans/tests removed cleanly with zero orphans (tree grep confirmed). *Found by Dev during implementation (rework).*

### Reviewer (code review)
- **Gap** (blocking): No wiring test proves the production chargen path invokes `equip_starting_armor`. Affects `sidequest-server/tests/server/` (add a test that drives the `chargen_mixin` confirm path via a synthetic SessionData — shape after `test_45_2_chargen_to_playing_wire.py` — and asserts the `chargen.armor_equipped` span fires). *Found by Reviewer during code review.*
- **Gap** (non-blocking): the `equip_starting_armor` `max()` best-armor branch and the AC4 `no_catalog_entry` / `inventory_config=None` branches are untested, and the unresolved span's `reason` attribute is never asserted. Affects `sidequest-server/tests/server/test_106_1_equip_starting_armor.py`. *Found by Reviewer during code review.*
- **Conflict** (non-blocking): `chargen.armor_unresolved` is logged at WARNING but its span/comment declare ERROR. Affects `sidequest-server/sidequest/server/dispatch/chargen_loadout.py` + `sidequest/telemetry/spans/inventory.py` (align the two; warning matches the sibling content-gap convention, so prefer softening the comment OR bump the log — but make them agree). *Found by Reviewer during code review.*
- **Question** (blocking — for Keith, deferred past this story): confirmed Dev's escalation — `warrior_kit.armor` rolls one of `[leather_armor, shield_wood, helmet_iron]`; only leather is valued, so ~2/3 of Warriors still fail-loud at AC 10. WWN models a shield as a +1 bonus (unmodelable in set-AC without the deferred combination rule) and has no helmet item. Affects `sidequest-content/genre_packs/caverns_and_claudes/{inventory.yaml,equipment_tables.yaml}` — needs a Keith ruling, NOT in this story's scope. *Found by Reviewer during code review.*

#### Round 2 (re-review — rework APPROVED)
- **Improvement** (non-blocking): two stale "AC 10"/severity docstrings escaped the rework — the SAME false-precision class as the original DOC fix, one docstring over. (a) `sidequest-server/sidequest/telemetry/spans/inventory.py:387` — `chargen_armor_equipped_span` docstring says `(10 → derived)`; `ac_before` can be a world-pre-seeded non-10 value, so this should read `(pre-chargen value → derived)`. (b) `sidequest-server/tests/server/test_106_1_equip_starting_armor.py:23` — module docstring still says `chargen.armor_unresolved — WARN/ERROR:`, now WARN-only after the alignment. Trivial fix-forward; fold into the shield/helmet content follow-up or a 1-line touch. *Found by Reviewer during code review (round 2).*
- **Improvement** (non-blocking): `test_best_armor_max_independent_of_item_order` asserts only the `equip_starting_armor` return value (`ac == 15`), not `character.core.armor_class == 15` — the state field `dice.py` actually reads. In practice unreachable (the code is `core.armor_class = ac_after; return ac_after` — one value, no order branch) and the sister test asserts state, so it's a thinner-than-ideal assertion, not a hole. Affects `sidequest-server/tests/server/test_106_1_equip_starting_armor.py` (add the state assertion when next touched). *Found by Reviewer during code review (round 2).*
- **Question** (blocking — for the EPIC, NOT this story; RE-AFFIRMING the standing escalation): the ~2/3-of-Warriors shield/helmet AC-10 shortfall is real and now machine-documented by the wire test, but it is a CONTENT/design follow-up requiring a Keith ruling (source shield as +1 via the deferred combination rule / re-key `warrior_kit` so torso armor is guaranteed / drop shield+helmet from the armor slot) — sourcing values now would violate the no-invented-numbers standing ruling. This story's code meets all 5 ACs (AC4 *specifies* fail-loud for an unvalued armor item, which is exactly the shield/helmet behavior). Affects `sidequest-content/genre_packs/caverns_and_claudes/{inventory.yaml,equipment_tables.yaml}` — recommend a dedicated follow-up story under Epic 106. *Found by Reviewer during code review (round 2).*

#### Round 3 (reconciliation re-review — APPROVED)
- **Improvement** (non-blocking): four Medium coverage fix-forwards surfaced by the #836 deletion, none a regression — (1) idempotency of `equip_starting_armor` (single chargen-confirm caller, not re-run on save-reload, so theoretical); (2) span `item_name`/`pc_name` attrs unasserted (the #836 test didn't assert them either); (3) span-name constant-string pin removed (global `test_routing_completeness` still guards SPAN_ROUTES registration); (4) unresolved branch doesn't assert `equipped` stays False. Affects `sidequest-server/tests/server/test_106_1_equip_starting_armor.py` + `test_106_1_chargen_armor_wire.py` (fold into the shield/helmet epic follow-up). *Found by Reviewer during code review (round 3).*
- **Improvement** (non-blocking): the two round-2 doc carryovers persist (`inventory.py` `(10 → derived)`, test module docstring `WARN/ERROR`); still LOW, still fix-forward. *Found by Reviewer during code review (round 3).*
- **Gap** (non-blocking, for the team): develop HEAD is red on `ruff check .` (un-sorted import on `tests/game/pg/test_telemetry_sink_missing_session.py`, committed by 700e7c82) — fixed in-passing by this PR. Worth a look at how un-sorted imports landed on develop past its lint gate. Affects `sidequest-server` lint/CI hygiene. *Found by Reviewer during code review (round 3).*
- **Process** (non-blocking, for the team): confirming Dev's finding — story 106-1 was implemented twice in parallel (this session + #836/#436) because the keyless story had no cross-workspace claim. Recommend a visible in-progress marker before starting keyless work in any clone. *Found by Reviewer during code review (round 3).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Content scope limited to leather_armor; shield_wood/helmet_iron left to fail-loud**
  - Spec source: context-story-106-1.md, Scope + Technical Approach §2
  - Spec text: "leather_armor mandatory; chain_shirt/shield_wood/helmet_iron if the multi-piece rule needs them"
  - Implementation: Added `armor_class: 13` to `leather_armor` only. `shield_wood`/`helmet_iron` (the kit's other two armor candidates) get no value, so rolling them fires `chargen.armor_unresolved` and the PC stays at AC 10.
  - Rationale: WWN models a shield as a +1 bonus (unrepresentable in the set-AC model without the deferred combination rule) and has no helmet item — sourcing either would mean inventing numbers, which the standing ruling (2026-06-13) forbids. Leather is the mandatory, SRD-clear item.
  - Severity: major
  - Forward impact: the epic's "ramp lever #1" only closes for ~1/3 of Warriors until Keith rules on shield/helmet (logged as a blocking Question in Delivery Findings). No code dependency on sibling stories; pure content + a possible kit re-key.
- **best-armor (max) combination chosen for multi-piece AC**
  - Spec source: context-story-106-1.md, Technical Approach §2 ("WWN uses best-armor AC, not additive")
  - Spec text: "torso armor sets AC, a shield grants a flat bonus; resolve from the SRD, not by guessing"
  - Implementation: `equip_starting_armor` derives `core.armor_class = max(catalog armor_class among equipped armor)`. The shield flat-bonus half is NOT implemented.
  - Rationale: best-armor is the WWN-faithful base rule and is all the tested (single-piece) path needs; the shield bonus is part of the deferred combination rule.
  - Severity: minor
  - Forward impact: a future story implementing shield-as-bonus must extend this function rather than replace it.

#### Green rework (round 2)
- **No new spec deviations.** The round-2 change (ERROR→WARN on `chargen.armor_unresolved`) is squarely within spec: context-story-106-1.md AC4 says "fails loud (**warn/error** span)" — both severities are explicitly allowed, and aligning to WARN matches the sibling content-gap convention the Reviewer endorsed. Docstring/comment wording fixes carry no spec implication.

#### Green rework (round 3 — #836 reconciliation)
- **Incidental lint fix outside story scope (develop's pre-existing import-sort debt)**
  - Spec source: dev minimalist-discipline ("don't refactor adjacent code without a failing test")
  - Spec text: implicit — changes should be scoped to the story
  - Implementation: applied `ruff --fix` (I001 import sort) to `sidequest-server/tests/game/pg/test_telemetry_sink_missing_session.py`, a file unrelated to 106-1.
  - Rationale: the `git merge origin/develop` inherited develop's own un-sorted import (committed by 700e7c82); develop HEAD is currently red on `ruff check .`. Left unfixed it would fail THIS PR's lint gate. One-line import reorder, zero behavior change. Surfaced as a delivery finding rather than absorbed silently.
  - Severity: minor
  - Forward impact: none for 106-1. develop should fix/notice its own ruff debt; see delivery finding.
- **No other deviations.** The reconciliation preserves the round-2 APPROVED 106-1 implementation verbatim — no algorithm, structure, or coverage change. #836 was superseded per Keith's explicit ruling (a workflow decision, not a spec deviation).

### TEA (test design)
- **Pinned span names + new function name as the contract**
  - Spec source: context-story-106-1.md, Technical Approach §2–3 ("add a sibling `chargen.armor_equipped` span"; home "alongside `apply_starting_loadout`")
  - Spec text: "reuse the established inventory/equip span family … or add a sibling `chargen.armor_equipped` span in the same module"
  - Implementation: Tests pin a NEW public function `equip_starting_armor` and TWO span names (`chargen.armor_equipped`, `chargen.armor_unresolved`). The unresolved span name was not named in the spec — I coined it (mirrors the existing `equip.unresolved` convention).
  - Rationale: TDD needs a concrete importable seam + stable span names for OTEL assertions; the spec offered the "sibling span" option and I took it. Dev may rename, but must update the tests in lock-step.
  - Severity: minor
  - Forward impact: Dev must define exactly these names (function + 2 spans) or justify a rename in the GREEN commit.
- **AC4 "not silently AC 10" interpreted as a loud span, not an AC mutation**
  - Spec source: context-story-106-1.md, AC4
  - Spec text: "a kit armor item with no catalog `armor_class` fails loud (warn/error span) and does NOT silently leave the PC at AC 10"
  - Implementation: The test asserts the `chargen.armor_unresolved` span fired AND the `chargen.armor_equipped` span did NOT fire. It does NOT assert a specific AC value for the gap case (there is no value to derive, so AC legitimately remains 10 — but loudly, via the span).
  - Rationale: "Not silently" is satisfied by the loud span; prescribing a fabricated AC would violate "no invented numbers".
  - Severity: minor
  - Forward impact: none — Dev surfaces the gap via the span; AC stays 10 in that case by design.
- **Multi-piece armor combination left untested (leather-only)**
  - Spec source: context-story-106-1.md, Scope + Technical Approach §2
  - Spec text: "leather_armor mandatory; chain_shirt/shield_wood/helmet_iron if the multi-piece rule needs them"
  - Implementation: All AC-derivation tests use a single leather piece. No test exercises torso+shield+helm best-armor combination.
  - Rationale: warrior_kit rolls one armor piece (see Delivery Findings); multi-piece is conditional/out of mandatory scope and the SRD combination rule is an escalate-to-Keith item, not something to bake into a test.
  - Severity: minor
  - Forward impact: if a future story makes multi-piece reachable, add combination tests then.

#### Red rework (round 2 — Reviewer gaps)
- **Wiring test hosts on `flickering_reach`, not the story-subject `beneath_sunden`**
  - Spec source: context-story-106-1.md, Title + Problem (the repro is `caverns_and_claudes/beneath_sunden`)
  - Spec text: "a freshly rolled Warrior in `caverns_and_claudes/beneath_sunden` ships with Leather Armor `equipped: true`"
  - Implementation: `test_106_1_chargen_armor_wire.py` drives the real `_chargen_confirmation` against `caverns_and_claudes/flickering_reach`.
  - Rationale: `equip_starting_armor`, `warrior_kit`, and `leather_armor.armor_class` are all GENRE-tier (not world-specific), so any cnc world hosts the identical wire. `beneath_sunden` is the ADR-106 megadungeon whose connect-time init constructs the real Anthropic SDK — the hermeticity guard (`conftest.py::_no_real_anthropic_sdk`) fails the test before chargen. `flickering_reach` is the proven-hermetic world the canonical `test_45_2_chargen_to_playing_wire` walks.
  - Severity: minor
  - Forward impact: none — the wire is genre-tier; if a future change makes armor world-specific, add a beneath_sunden-specific test then.
- **Wiring assertion is roll-agnostic (one-of-two armor spans), not a fixed AC=13**
  - Spec source: context-story-106-1.md, AC1/AC2 (leather → `equipped:true`, AC 13)
  - Spec text: "that Warrior's `core.armor_class` equals the WWN-SRD leather value (13)"
  - Implementation: the wire test asserts EXACTLY ONE of {`chargen.armor_equipped`, `chargen.armor_unresolved`} fires (warrior_kit always rolls one armor piece), then branch-asserts AC=13+equipped when leather rolled and AC=10+loud-fail when shield/helmet rolled. It does not seed the RNG to force leather.
  - Rationale: `warrior_kit.armor = [leather_armor, shield_wood, helmet_iron]` is a uniform 1-pick; only leather is valued today (the blocking shield/helmet gap). A fixed AC=13 assertion would be flaky (~1/3). The one-of-two invariant is a DETERMINISTIC proof of the wire regardless of the roll — and the branch-asserts keep it non-vacuous. AC=13 value-flow is already pinned deterministically by the direct-call tests + the reprisal e2e.
  - Severity: minor
  - Forward impact: once shield/helmet get WWN-sourced values (Keith ruling), the else-branch updates to also assert AC>10.

### Reviewer (audit)
- **TEA #1 (pinned span/function names as the contract)** → ✓ ACCEPTED by Reviewer: TDD needs a concrete importable seam; the names are sensible and mirror the `equip.*` convention. Dev adopted them verbatim.
- **TEA #2 (AC4 "not silently AC 10" = loud span, not an AC mutation)** → ✓ ACCEPTED by Reviewer: correct reading — fabricating an AC would violate no-invented-numbers; the loud span is the right "not silent" signal. (But the `reason` attribute and the `no_catalog_entry` branch still need coverage — captured as a finding.)
- **TEA #3 (multi-piece left untested, leather-only)** → ✗ FLAGGED by Reviewer: reasonable when scoped to "what the kit rolls," but Dev's implementation (deviation #2) actually ships the `max()` best-armor branch, so that code path is now untested. Add the multi-piece test — folded into the rework findings.
- **Dev #1 (content scope leather-only; shield/helmet fail-loud, severity major)** → ✓ ACCEPTED by Reviewer: the escalate-don't-invent call is correct and within story scope (leather mandatory). The real-play consequence (ramp only ~1/3 closed) is a genuine concern but belongs to Keith's ruling, not a code defect — recorded as a deferred blocking Question, not a reason this story's code is wrong.

#### Round 2 (re-review)
- **TEA red-rework #1 (wire test hosts on `flickering_reach`, not `beneath_sunden`)** → ✓ ACCEPTED by Reviewer: the wire under test (`equip_starting_armor`, `warrior_kit`, leather `armor_class`) is entirely genre-tier, so any cnc world exercises the identical path. `beneath_sunden`'s ADR-106 megadungeon connect reaches the real Anthropic SDK and trips the hermeticity guard — `flickering_reach` is the correct hermetic host (same world the canonical 45-2 wire test uses). Sound engineering trade, not a scope reduction.
- **TEA red-rework #2 (roll-agnostic one-of-two-spans assertion, not fixed AC=13)** → ✓ ACCEPTED by Reviewer: `warrior_kit.armor` is a uniform 1-of-3 roll; a fixed AC=13 assert would be ~1/3 flaky. The `total == 1` invariant is a deterministic, refactor-stable proof of the production wire (verified: both spans are emitted ONLY inside `equip_starting_armor`, whose ONLY caller is chargen_mixin.py:1257 — drop it and `total == 0` fails the test), and the per-branch asserts keep it non-vacuous. AC=13 value-flow is independently pinned by the direct-call tests + reprisal e2e.
- **Dev green-rework "no new spec deviations" (ERROR→WARN within AC4's "warn/error" allowance)** → ✓ ACCEPTED by Reviewer: AC4 explicitly permits "warn/error span"; WARN matches the sibling content-gap convention (`chargen.starting_equipment_missing`) and the rule-checker confirmed Rule #4 compliance (content gap ≠ runtime 5xx). The span still fires and stays in `SPAN_ROUTES` — No-Silent-Fallback intact. Not a deviation.

#### Round 3 (reconciliation re-review)
- **Dev round-3 "incidental lint fix outside story scope" (develop's pre-existing import-sort debt on `test_telemetry_sink_missing_session.py`)** → ✓ ACCEPTED by Reviewer: the `git merge origin/develop` inherited develop's own un-sorted import (700e7c82); develop HEAD is red on `ruff check .` and the debt would have failed THIS PR's lint gate. A one-line import reorder (zero behavior, confirmed by [RULE] #6 — "import reorder only, behavior unchanged") is the minimal correct fix, and Dev surfaced it as a delivery finding rather than absorbing it silently. Necessary to ship green; correctly scoped and disclosed.
- **Dev round-3 "no other deviations — approved impl preserved verbatim"** → ✓ ACCEPTED by Reviewer: independently verified `git diff f334aee4 HEAD` is empty on the two 106-1 impl files; the merge re-authored no story logic. Superseding #836 was a workflow decision (Keith's ruling), not a spec deviation. Confirmed.

## Subagent Results

_(Round 2 — re-review of the rework. Same toggle set as round 1: 4 enabled, 5 disabled.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 434 passed; ruff/format/pyright clean; tree clean | N/A — all mechanical gates green |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 3 closed (HIGH wire, MEDIUM max, HIGH AC4); 4 LOW residuals (1 worth fix-forward) |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed WARN/ERROR fully resolved; 1 MEDIUM-confidence LOW-severity doc drift (inventory.py:387); 3 historical-context LOW |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | PASS — 0 rule violations; 1 LOW stale-docstring note (test:23) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 confirmed blocking; 3 originally-rejected gaps CLOSED + verified; ~6 folded LOW/non-blocking residuals (doc drift + thin assertion); 0 dismissed; shield/helmet shortfall re-affirmed as deferred (epic-level, not this story).

## Reviewer Assessment

_(Round 2 — re-review of TEA red-rework + Dev green-rework. Supersedes the round-1 REJECTED verdict above.)_

**Verdict:** APPROVED

The rework closed every finding from my round-1 rejection, and I verified the load-bearing one with my own grep rather than trusting the test name. The implementation was already correct (I traced it end-to-end last round: content `armor_class: 13` → `core.armor_class` best-armor max → `dice.py` reprisal `target_ac`); what was missing was the proof it stays wired. That proof now exists and is non-vacuous.

**Data flow traced (re-confirmed for the wire):** player completes chargen-confirm → `_chargen_confirmation` (chargen_mixin.py) → `apply_starting_loadout` → `equip_starting_armor` (chargen_mixin.py:1257, the ONLY production caller) → `chargen_armor_equipped_span` / `chargen_armor_unresolved_span` (emitted ONLY here, chargen_loadout.py:385/407) → `core.armor_class` mutated → read by the opponent reprisal at resolution. The new wire test drives this whole path through `handle_message` and asserts exactly one armor span fires; sever the 1257 call and the span count drops to 0 and the test fails. This is the OTEL-span wiring pattern server CLAUDE.md mandates ("No Source-Text Wiring Tests").

**Observations:**
- `[TEST]` **HIGH gap CLOSED — production-wire test is sound and non-vacuous.** `test_106_1_chargen_armor_wire.py` drives the real handler; the `total == 1` assertion is load-bearing because the two armor spans are emitted exclusively inside `equip_starting_armor` (verified by grep) and that function has exactly one production caller (chargen_mixin.py:1257). Confirmed independently by [TEST] (Finding 1, HIGH) and my own enumeration.
- `[TEST]` **MEDIUM gap CLOSED — `max()` best-armor branch now covered.** Four new tests exercise max-over-lower, order-independence, one-span-per-piece, and mixed valued/missing batch. Confirmed by [TEST] (no vacuity in the cluster).
- `[TEST]` **MEDIUM gap CLOSED — AC4 discriminator covered.** `no_catalog_entry`, `catalog_armor_class_missing`, and `inventory_config=None` are now distinctly asserted via the `reason` attribute. Confirmed by [TEST] (Finding 4, HIGH).
- `[RULE]` **LOW finding RESOLVED — WARNING/ERROR aligned, and correctly.** The rule-checker (Rule #4) confirms WARN is the right level: a missing `armor_class` is a content authoring gap (sibling `chargen.starting_equipment_missing` precedent), not a runtime 5xx like `equip.unresolved` (which correctly keeps ERROR). The span still fires and stays in `SPAN_ROUTES` — No-Silent-Fallback intact. Verified no orphaned import (`Status`/`StatusCode` still used at inventory.py:285; ruff clean). Confirmed by [RULE] + [DOC].
- `[DOC]` **LOW finding mostly RESOLVED, two stale phrases remain (non-blocking).** The named "AC stays 10" docstring + the test `dice.py:1636` line-refs are fixed. Two escaped: `inventory.py:387` `(10 → derived)` and `test_106_1_equip_starting_armor.py:23` `WARN/ERROR` — same false-precision class, one docstring over. LOW, recorded as fix-forward delivery findings. Confirmed by [DOC] (Finding 2) + [RULE].
- `[TEST]` **LOW — `test_best_armor_max_independent_of_item_order` asserts only the return value, not `core.armor_class`.** Mitigated: the code is a single `core.armor_class = ac_after; return ac_after` (no order branch between them) and the sister test asserts state. Thinner-than-ideal, not a hole. Recorded as fix-forward. Confirmed by [TEST] (Finding 3) + [RULE].
- `[EDGE]` **Not run** — edge-hunter disabled via settings. Self-assessed: the changed surface is docstrings + a one-line span-status removal + tests; boundary conditions in `equip_starting_armor` (None config, empty armor list, missing value, multi-piece) are now explicitly test-covered. No unhandled-path concern.
- `[SILENT]` **Not run** — silent-failure-hunter disabled. Self-assessed: the change REMOVES nothing from the loud path — the unresolved span still fires + logs `warning` + routes to the GM panel. No new swallow; No-Silent-Fallback strengthened by the added AC4 coverage.
- `[TYPE]` **Not run** — type-design disabled. Self-assessed: no type-surface change (a `set_status` line removed; signatures untouched); pyright clean.
- `[SEC]` **Not run** — security disabled. Self-assessed: no auth/input/tenant surface; chargen armor derivation is internal mechanical state. No security delta.
- `[SIMPLE]` **Not run** — simplifier disabled. Self-assessed: the rework SIMPLIFIED (removed a `set_status` call, collapsed two pre-existing multi-line constructs). No new complexity.
- `[VERIFIED]` **All five story ACs met.** AC1 (leather equips), AC2 (AC=13 from content, mutate-follows), AC3 (reprisal vs derived AC — e2e), AC4 (fail-loud, no silent AC10 — and the shield/helmet path is *exactly* this AC's specified behavior), AC5 (no regression — 434 green). Evidence: the 106-1 test suite + reprisal e2e + content test, all passing.
- `[VERIFIED]` **Story is complete-to-scope despite the ~2/3 shield/helmet shortfall.** The scope says "leather mandatory; shield/helmet if the multi-piece rule needs them" + "escalate, do not invent." The code fails loud on shield/helmet exactly as AC4 requires. The ramp shortfall is an epic-level CONTENT follow-up (Keith ruling), not a defect in this story's code.

### Devil's Advocate

Argue this should still be rejected. The sharpest angle: I rejected last round partly citing a `[LOW][DOC]` false-precision string ("AC stays 10"), and I am now approving with the *identical* false-precision pattern still live at `inventory.py:387` ("(10 → derived)") plus a stale "WARN/ERROR" docstring — am I rubber-stamping the exact sin I flagged? No. Last round's rejection basis was the `[HIGH]` untested production wire, a structural hole that could silently re-break the lethality lever; the DOC items were explicitly listed as LOW, non-blocking, fix-opportunistically. The severity contract is unambiguous: only Critical/High block. The wire hole is closed and I verified the closure mechanically (not by trusting a green checkmark — I grepped that the spans have exactly one emitter and that emitter exactly one caller, so the test genuinely fails on regression). Second angle: "you're approving a fix that only helps ~1/3 of Warriors — the meat-grinder persists for the other 2/3, which is the whole point of the story." True and uncomfortable, but the story's ACs are precise: AC4 *mandates* that an unvalued kit armor item fail loud rather than silently sit at AC 10 — which is exactly what shield_wood/helmet_iron do. The story never promised to value shield/helmet; it promised leather + a loud failure for the rest, and explicitly deferred the combination/bonus rule with "escalate, do not invent." Forcing shield/helmet AC values now would manufacture WWN numbers the SRD doesn't define — a worse sin (fabricated mechanics) than an honestly-surfaced content gap. The shortfall is real, it's logged as a blocking *epic* follow-up, and the new wire test now makes it impossible to regress silently. Third angle: "the wire test uses flickering_reach, not the beneath_sunden the bug was found in — you're testing a different world than the repro." But the wire is genre-tier (verified: `equip_starting_armor`, `warrior_kit`, and the leather `armor_class` all live at the genre layer, inherited by every cnc world), and the e2e reprisal test independently proves the derived AC reaches `dice.py`. The world swap is forced by hermeticity (beneath_sunden's connect builds the real SDK) and changes nothing about the path under test. Nothing here rises to High. APPROVE stands.

**Handoff:** To SM (Drummer) for finish-story. Two LOW doc/test nits + the deferred shield/helmet Keith ruling are recorded as non-blocking delivery findings; recommend a dedicated Epic-106 content follow-up for the shield/helmet AC ruling.
- **Dev #2 (best-armor max for multi-piece)** → ✓ ACCEPTED by Reviewer (design) / ✗ FLAGGED (coverage): `max()` is the WWN-faithful base rule and the right placeholder, but shipping the branch untested is the gap above. Accept the design, require the test.