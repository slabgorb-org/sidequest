---
story_id: "108-3"
jira_key: ""
epic: "108"
workflow: "trivial"
---
# Story 108-3: Content de-nativize WWN combat defs

## Story Details
- **ID:** 108-3
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** 108-7 (dependency resolved; 108-7 completed 2026-06-15)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-15T10:06:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T09:42:33Z | 2026-06-15T09:44:21Z | 1m 48s |
| implement | 2026-06-15T09:44:21Z | 2026-06-15T09:59:09Z | 14m 48s |
| review | 2026-06-15T09:59:09Z | 2026-06-15T10:06:10Z | 7m 1s |
| finish | 2026-06-15T10:06:10Z | - | - |

## Story Context

**Task:** Content de-nativize WWN combat defs across four genre packs.

Strip from each COMBAT confrontation def in genre rules.yaml (win_condition:hp_depletion):
- `resolution_mode: beat_selection`
- Entire native beats list (strike/cast_spell/brace/committed_blow/break_contact + variants)
- `edge_config` (if present)
- Momentum/dial metrics

Also strip orphaned `encounter_beat_choices` from each WN class in classes.yaml.

Result: combat def = `win_condition: hp_depletion` + `opponent_default_stats` + `opponent_damage` DamageSpec only.

**Targets (verify these match the live world list):**
1. caverns_and_claudes — 'Dungeon Combat' (primary verify: beneath_sunden)
2. heavy_metal — 'Blade-work' (verify: evropi, long_foundry, barsoom)
3. elemental_harmony — 'Martial Exchange'

**Leave untouched:**
- Chase/negotiation DIAL defs (ADR-143 scope: WN combat only)

**Spec Document:**
- docs/superpowers/specs/2026-06-14-108-3-wwn-combat-denativize-strip-spec.md

**Validation:** `load_genre_pack` must pass for all three WWN packs after stripping.

**Workflow Route:** trivial → gm agent for implement phase (no TDD required; content-only).

## Delivery Findings

**Implemented (gm, 2026-06-15) — content de-nativize complete, validated.**

De-nativized all three WWN combat defs and cleaned the orphaned class beat choices:
- `caverns_and_claudes` Dungeon Combat, `heavy_metal` Blade-work, `elemental_harmony` Martial Exchange: stripped `resolution_mode: beat_selection` + the entire native `beats:` list (strike/cast_spell/brace/committed_blow/break_contact and the EH elemental_burst/guard/yield variants). No `edge_config`/momentum/dial metrics existed as structured fields (momentum was narrative text inside beats — gone with them). Kept `win_condition: hp_depletion` + full six-ability `opponent_default_stats` + `opponent_damage` DamageSpec (1d8/1d8/1d6 — ADR-139 Inv-3 teeth intact). Left a short comment in each def so no future reader "fixes" the intentional zero-beat shape.
- `classes.yaml` (all three packs): removed the orphaned **combat-beat** entries from every class's `encounter_beat_choices` (58 list-item removals total) while **keeping** the chase/negotiation DIAL entries — the DIAL defs stay native under ADR-143, so their beats remain a valid pool. No class ended up with an empty list. Updated the stale header comments that documented the now-removed cast_spell/combat-class_filter gating.
- DIAL defs (chase/negotiation) byte-unchanged — verified via diff (zero DIAL-def lines in the rules.yaml diff).
- Strip-spec (`docs/superpowers/specs/2026-06-14-108-3-...md`) corrected: the pre-108-7 "BLOCKED / zero-beat-is-false" premise replaced with the RESOLVED note + the encounter_beat_choices mixed-pool sharpening; the 107-2 rider marked DESCOPED; the workflow-tag housekeeping marked reconciled to `trivial`.

**Validation (the named gate):** `load_genre_pack` passes clean for all three edited packs (combat `beats=0`, `win=hp_depletion`, all classes load) AND for the full 11-pack set (0 failures — no collateral). `validate pack` CLI: all three PASS, 0 errors, no new beat/combat warnings.

**FINDING — stale signature-ability prose references vanished combat beats (route to Keith, NOT fixed here).** Several ADR-095 signature abilities describe their trigger in terms of native combat beats that no longer exist:
- `caverns_and_claudes/classes.yaml:71` — "on a successful strike beat, deal bonus damage"
- `heavy_metal/classes.yaml:77,81,262` — "single committed strike", "on a successful strike beat", "take a strike beat, spend 1 Effort"
- `elemental_harmony/classes.yaml:98,235,270,274,368` — "use an elemental_burst beat", "an incoming strike that would reduce your HP to a **guard beat**", "successful strike beat", "push beat (yield or vanish)"

These are PROSE only (no structured `trigger_beat:` field), so they don't break `load_genre_pack`. But two things make this Keith's call, not a content-strip edit: (1) rewording maps a mechanical trigger onto the WN action model (attack/move/item-use/cast) — crunch, his lane; (2) the EH defender reaction keyed on a *guard beat* has no obvious WN-round equivalent (wn_round.py supplies no defend/guard action), so its trigger genuinely needs a mechanical decision, and the server-side dispatch hookup is 108-7/108-8 territory. Recommend a follow-up story: "re-anchor WWN signature-ability triggers to the WN round" (content prose + confirm server dispatch fires under synthesized attack).

**Scope boundary (informational):** CWN (road_warrior, neon_dystopia), AWN (mutant_wasteland), SWN (space_opera) packs still carry `resolution_mode: beat_selection` combat defs — out of 108-3's WWN-only scope, owned by epics 114-x. Same de-nativization pattern will apply there under ADR-143 doctrine.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

**Routing: gm did the implement phase, not dev.** The `trivial` workflow generically owns `implement` with `dev`, and the activation phase-check emitted a "hand off to dev" redirect. SM deliberately routed to gm per the story's explicit `→ gm agent` intent because this is 100% content YAML surgery on genre packs (gm's lane; dev writes code, and there is no code here). Honored that — the work is content-only and load-validated. Flagging so the review/finish path expects gm as the implementer.

## Sm Assessment

**Blocker cleared.** 108-3's hard dependency, 108-7 (server: make WN combat beat-optional), is `done` as of 2026-06-15. The wn_round.py action set now supplies combat actions, so the native beat lists in content are genuinely orphaned and safe to strip. This was the live blocker — confirmed before seating.

**Scope is content-only YAML surgery** under ADR-143 (bind the ruleset, don't balance it) and ADR-139 Inv-3. For each WWN COMBAT def (`win_condition: hp_depletion`): strip `resolution_mode: beat_selection`, the native beats list (strike/cast_spell/brace/committed_blow/break_contact + guard/yield variants), `edge_config`, and momentum/dial metrics. Strip orphaned `encounter_beat_choices` from each WN class in classes.yaml. End state: combat def = `win_condition: hp_depletion` + `opponent_default_stats` + `opponent_damage` DamageSpec only.

**Guardrails for the implementer:**
- LEAVE chase/negotiation DIAL defs untouched — ADR-143 scope is WN *combat* only. Do not let the strip bleed into dial-based confrontations.
- Verify the live target list against actual world files before editing; the story names beneath_sunden (c&c), evropi/long_foundry/barsoom (heavy_metal), and elemental_harmony, but confirm 'Dungeon Combat' / 'Blade-work' / 'Martial Exchange' def names match what's on disk.
- Correct the strip-spec at docs/superpowers/specs/2026-06-14-108-3-wwn-combat-denativize-strip-spec.md — its zero-beat premise was authored pre-108-7 and is now wrong.
- The 107-2 Torchdeep/Torchhold/Bileden rider is **DESCOPED** (names absent from content; likely procedural/server per ADR-106). Do not chase it.

**Validation:** `load_genre_pack` must pass clean for all three WWN packs after the strip. Content-only, no engine changes — no TDD red phase required (trivial workflow).

**Routing:** Story explicitly routes to the **gm** agent (assignee gm), not the default dev. This is genre-pack content authoring in gm's lane. Honoring story intent over the trivial-default dev route.
---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — all 3 packs load PASS (beats=0, hp_depletion, opponent_damage preserved); 11-pack sweep PASS; validator 0 errors; 0 code smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 2 (consolidated, non-blocking), deferred 3 (server-repo, low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 10 | confirmed 1 (consolidated, non-blocking) — all 10 are the same finding-class gm already flagged |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 16 instances | N/A — all 5 doctrine rules COMPLIANT |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 2 confirmed (non-blocking), 3 deferred (server-repo, non-blocking), 0 blocking

### Rule Compliance

Enumerated against SOUL.md / ADR-143 / ADR-139 (the doctrine governing this change). Backed by reviewer-rule-checker's exhaustive 16-instance pass, independently spot-verified.

- **SOUL "Bind the Ruleset, Don't Balance It" / ADR-143** — combat def = hp_depletion + opponent_default_stats + opponent_damage ONLY (no resolution_mode/beats/edge_config/momentum). Checked all 3 combat defs (Dungeon Combat, Blade-work, Martial Exchange): **COMPLIANT** ×3. Load probe confirms beats=0 on each.
- **SOUL "Crunch in the Genre, Flavor in the World"** — diff touches genre-tier rules.yaml/classes.yaml only, zero world-tier files: **COMPLIANT** (6/6 files genre-tier).
- **ADR-143 scope = WN combat only; DIAL defs untouched** — checked all 6 DIAL defs (3 chase + 3 negotiation): every DIAL beat pool present and unmodified. Independently verified only the `combat` defs carry `hp_depletion` (DIAL defs win_condition=None → cannot be misclassified by the loader's combat-optional gate): **COMPLIANT** ×6.
- **ADR-139 Inv-3 (mechanically-capable Other)** — opponent_damage retained (1d8/1d8/1d6) + full six-ability opponent_default_stats retained on each combat def: **COMPLIANT** ×3.
- **No Silent Fallbacks / fail-loud** — every class's encounter_beat_choices had its combat-beat entries REMOVED (not emptied); all 16 classes retain only valid DIAL beats; no class left empty: **COMPLIANT** ×16. Loader's stale-ref fail-loud invariant (loader.py:765) holds.

### Observations

- [VERIFIED] Combat defs de-nativized correctly — `resolution_mode` + entire `beats:` list removed; `win_condition: hp_depletion` + `opponent_default_stats` (six abilities + hp/AC/dexterity) + `opponent_damage` + `mood` retained. Evidence: content diff hunks + preflight load probe (beats=0, hp_depletion, opp_damage=1d8/1d8/1d6). Complies with ADR-143 + ADR-139 Inv-3.
- [VERIFIED] DIAL defs byte-unchanged and cannot be misclassified — only the 3 `combat` defs carry `win_condition: hp_depletion`; the 6 DIAL defs are `category: movement|social` with `win_condition: None` and retain all their beats. Evidence: independent yaml dump of all 9 confrontations. The loader's beat-optional gate keys on `category==combat AND hp_depletion`, so no DIAL def is at risk.
- [VERIFIED] No class left with empty `encounter_beat_choices` — all 16 classes retain their chase/negotiation DIAL beats after the combat-beat removal. Evidence: yaml load of all 3 classes.yaml; zero empty lists. This preserves the chase/negotiation mechanic that ADR-143 leaves native.
- [RULE] reviewer-rule-checker: 0 violations across 16 instances; fail-loud stale-ref invariant confirmed at loader.py:765. Confirmed.
- [DOC] reviewer-comment-analyzer: 10 stale `mechanical_effect` prose references to removed combat beats (strike/guard/elemental_burst/push beats) across all 3 packs — e.g. EH/classes.yaml:99 "Elemental Gate" (`elemental_burst beat`) now contradicts the same file's refreshed header, EH:236 "Iron Body" written entirely in guard-beat vocabulary. **Confirmed as a real finding but NON-BLOCKING** (see assessment rationale) — gm pre-flagged this; routed to follow-up.
- [TEST] reviewer-test-analyzer: the WN-beat-optional loader's **live-content** wiring test was explicitly DEFERRED by 108-7 ("AC4 verified by 108-3, not here") and is now orphaned — no server test asserts the 3 live packs load with `beats==[]`, and no negative test exercises the stale-class-ref fail-loud path. **Confirmed, NON-BLOCKING, cross-repo** (sidequest-server) — routed to follow-up.
- [EDGE] reviewer-edge-hunter — disabled via settings; boundary conditions on a pure-deletion YAML diff assessed manually (empty-choices and DIAL-misclassification checks above): no edge defects.
- [SILENT] reviewer-silent-failure-hunter — disabled via settings; the loader's fail-loud behavior (the only error path touched) is confirmed by rule-checker at loader.py:765 — no swallowed errors.
- [TYPE] reviewer-type-design — disabled via settings; N/A to a content YAML diff (no type definitions).
- [SEC] reviewer-security — disabled via settings; N/A — no auth/input/secret surface; content-only genre data.
- [SIMPLE] reviewer-simplifier — disabled via settings; the change is a net −222-line deletion, the opposite of over-engineering; the added comments are intentional anti-regression guards.

### Devil's Advocate

Let me argue this change is broken. First attack: the de-nativization silently neuters combat for these three packs — strip the beats and the WN engine had better actually supply an action set, or every fight becomes a no-op. Rebuttal: 108-7 + 108-8 landed (the loader gate is WN-conditional and wn_round.py synthesizes attack on zero-beat defs), and the preflight load probe shows the combat def resolving with hp_depletion + a 1d8/1d6 opponent_damage — the Other keeps its teeth (ADR-139 Inv-3). Second attack: the change creates a self-contradicting file — EH/classes.yaml's header now declares "no combat beats appear in any class's choices," yet the same file's "Iron Body" and "Elemental Gate" abilities still narrate a `guard beat` and an `elemental_burst beat`. A player reading their sheet sees mechanics that no longer exist; a narrator fed that prose may invent a beat-selection step the engine doesn't offer — a Zork-Problem regression and exactly the kind of "winging it" OTEL is meant to catch. This is the strongest objection, and it is real. But it does not make the *strip* wrong — it exposes downstream prose that the story did not scope and, critically, cannot be fixed without deciding the WN-round trigger semantics for each ability (what IS the WN equivalent of a guard beat when wn_round.py has no defend action?). That decision is a mechanical-design call (Keith's lane) and partly server dispatch (108-7/108-8) — and per ADR-143, converting a native mechanic "to make it work with" the binding is the exact trap the doctrine forbids. Forcing gm to reword these in a content-strip story would push the work into a SOUL violation. Third attack: a future editor re-adds a beats list and nothing fails — load still passes because a populated beats list is valid. True, and that is the test-analyzer's orphaned-wiring-test finding: there is no automated guard asserting `beats==[]` on the live packs. That is a genuine gap — but a regression-guard gap in a *different repo*, not a correctness defect in this diff. Conclusion: the strip is correct, complete, and doctrinally clean; the two surfaced issues are real, non-blocking, and belong to follow-up work — not a rejection.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** A combat action in beneath_sunden/evropi/etc. → loader resolves the de-nativized `combat` def (beats=0, hp_depletion) → wn_round.py (108-8) supplies attack/move/item-use/cast and synthesizes the attack → opponent_damage (1d8/1d6) applies on the Other's turn. Safe: the action set is engine-supplied, not content-authored, and the Other retains damage (ADR-139 Inv-3). Verified via preflight load probe.

**Pattern observed:** Clean doctrine-compliant strip — native scaffolding *removed*, not balanced (ADR-143), with intentional anti-regression comments left in each def (e.g. caverns_and_claudes/rules.yaml:147 "Do not re-add a beats list here"). Net −222 lines.

**Error handling:** The only error path touched is the loader's fail-loud validation. The fail-loud stale-class-ref invariant (loader.py:765) is preserved — confirmed by rule-checker; every class had its combat-beat refs fully removed, so no stale-ref condition exists.

**Dispatch tag summary:** [RULE] clean (0/16 violations) · [DOC] 10 stale-prose findings → non-blocking follow-up · [TEST] orphaned live-content wiring test → non-blocking cross-repo follow-up · [EDGE]/[SILENT]/[TYPE]/[SEC]/[SIMPLE] disabled, assessed manually, no defects.

**Why APPROVED despite [DOC]/[TEST] findings:** Both are real but (a) outside this content-strip story's scope (strip defs + choices — not reword ability mechanics, not author server tests), (b) the content is correct, complete, doctrinally clean, and load-validated, and (c) the fixes require either a Keith-owned mechanical decision (WN-round trigger semantics — which ADR-143 forbids resolving by native-mechanic conversion) or server-repo test authoring (gm is a content-only, no-code agent). Rejecting back to gm would force a SOUL violation. Captured as non-blocking delivery findings with concrete follow-up recommendations instead.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Design Deviations

### Reviewer (audit)

- **Routing: gm did the implement phase, not dev** → ✓ ACCEPTED by Reviewer: correct call. The diff is 100% genre-pack YAML (rules.yaml/classes.yaml) with zero code; that is gm's content lane and outside dev's. The `trivial`-workflow generic `dev` ownership is a default, and the story's explicit `→ gm agent` intent rightly overrides it. The work is load-validated and doctrinally clean — the routing produced a correct result.
- No undocumented spec deviations found. The implementation matches the strip-spec's per-pack targets and the "leave DIAL defs untouched" constraint exactly; the spec's stale pre-108-7 premise was correctly corrected rather than silently followed.

## Delivery Findings

### Reviewer (code review)

- **Improvement** (non-blocking): Stale signature-ability `mechanical_effect` prose references native combat beats removed by this change (10 instances across all 3 packs). Affects `genre_packs/caverns_and_claudes/classes.yaml` (:75 Killing Blow, :135 Read the Ledger), `genre_packs/heavy_metal/classes.yaml` (:84 Killing Blow, :140 Read the Ledger, :265 Stoke the Working), `genre_packs/elemental_harmony/classes.yaml` (:99 Elemental Gate `elemental_burst beat`, :236 Iron Body `guard beat`, :275 Killing Blow, :329 Lore Advantage, :369 Open Road `push beat`). These are prose (not loader-validated, do not break load) but now misdescribe the mechanical surface and in EH directly contradict the refreshed header. Rewording requires deciding each ability's WN-round trigger semantics (a mechanical-design call — Keith's lane — and partly server dispatch via 108-7/108-8); per ADR-143 this must NOT be resolved by converting a native mechanic to fit the binding. Recommend a follow-up story: "re-anchor WWN signature-ability triggers to the WN round." *Found by Reviewer during code review (corroborates gm's implement-phase finding; expanded from ~9 to 10 instances by reviewer-comment-analyzer).*
- **Gap** (non-blocking): The WN-beat-optional loader's **live-content** wiring test is orphaned. 108-7's `sidequest-server/tests/genre/test_wn_beat_optional_loader.py` explicitly deferred AC4 ("all three WWN packs load once 108-3 strips them") to 108-3, but 108-3 is content-only (`repos: content`) and gm cannot author server pytest. No server test now asserts the 3 live packs load with `combat_def.beats == []`, and no negative test exercises the stale-class-ref fail-loud path (loader.py:765). Affects `sidequest-server/tests/genre/` (add a parametrized live-pack load + `beats==[]` assertion over the 3 packs, plus a stale-ref PackError negative test). A future edit that re-adds a beats list would pass load silently with no guard. *Found by Reviewer during code review (reviewer-test-analyzer).*