---
story_id: "158-60"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-60: beneath_sunden 107-2 content gates red: low-band bestiary image specs + room-creature binding diversity

## Story Details
- **ID:** 158-60
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Cross-Repo Test Location Note
**IMPORTANT:** This story declares repo `content` (sidequest-content), but the acceptance-gate tests already exist in the `server` repo:
- `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py::test_every_low_tagged_bestiary_entry_is_renderable`
- `sidequest-server/tests/genre/test_beneath_sunden_room_binding_107_2.py::test_distinct_rooms_bind_distinct_creatures`

TEA's RED phase will confirm these are the acceptance gates (tests currently fail). Dev will author content YAML fixes in sidequest-content and run the sidequest-server genre suite to verify GREEN.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-03T15:31:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-03T12:00:43Z | 2026-07-03T12:02:51Z | 2m 8s |
| red | 2026-07-03T12:02:51Z | 2026-07-03T12:11:42Z | 8m 51s |
| green | 2026-07-03T12:11:42Z | 2026-07-03T15:16:26Z | 3h 4m |
| review | 2026-07-03T15:16:26Z | 2026-07-03T15:31:10Z | 14m 44s |
| finish | 2026-07-03T15:31:10Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → next phase `red`, owner **tea** (Amos Burton). Setup complete: session + story/epic context + `feat/158-60-content-gates-107-2` branch on `develop` in `sidequest-content`.

**Nature of the story:** A content-gate cleanup. Two tests already exist and already FAIL on develop (verified pre-existing via git-stash baseline 2026-07-03 during 158-54). They fail on every full-suite run and mask real regressions. There are **no explicit acceptance_criteria in the YAML — the two named tests ARE the acceptance gate.**

**The two gates (make both green):**
1. `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py::test_every_low_tagged_bestiary_entry_is_renderable` — 41 low-band bestiary entries have no image spec (constrictor_snake, giant_bat, drow, gnoll, … full list in the failure output).
2. `sidequest-server/tests/genre/test_beneath_sunden_room_binding_107_2.py::test_distinct_rooms_bind_distinct_creatures` — only one room-creature binding exists (entrance→gnaw_swarm), i.e. a flat pool by another name.

**Two legitimate fix paths (Dev/TEA to decide per entry):**
- Author the missing bestiary image specs + diversify room-creature bindings in `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden`, OR
- Explicitly re-tier entries out of the low band if they are genuinely unreachable early (re-tiering is content YAML too — not a test edit to dodge the gate).

**Cross-repo wrinkle (load-bearing):** declared repo is `content` (the fix is YAML authoring in sidequest-content), but the acceptance-gate tests live in the `server` repo. TEA's RED is mostly *confirm the existing failures are the gate*, not author net-new tests; Dev authors content and runs the `sidequest-server` genre suite to verify GREEN. Do NOT weaken/skip the tests to make them pass — fix the content or re-tier honestly.

**Scope guard:** beneath_sunden low-band bestiary specs + room bindings only. Don't drag in other worlds or unrelated 107-2 debt.

**Provenance:** Dev Delivery Finding from the archived 158-54 session; 107-2 is the originating story.

**Parked/limbo note:** 158-52 sits `in_progress`/phase=review with NO PR opened (handed to Reviewer, never PR'd). No PR → does not trip the merge gate, so it does not block 158-60. It still needs `/pf-reviewer` (or a re-check) to actually land.

## TEA Assessment

**Tests Required:** Yes — but the acceptance gate ALREADY EXISTS (pre-existing 107-2 tests). TEA authored no net-new tests; the pre-existing `tests/genre/test_beneath_sunden_creature_images_107_2.py` + `..._room_binding_107_2.py` ARE the gate. RED confirmed by running them.

**RED state (verified via testing-runner, run_id `158-60-tea-red`):** 1 FAILED / 10 PASSED.
- FAIL: `test_every_low_tagged_bestiary_entry_is_renderable` — 42 low-tagged bestiary entries have no `creatures.yaml` image spec (48 low-tagged total; only the original 6 authored). The 42 are generic WWN-SRD monsters.
- PASS (already green, story premise stale): all 5 room-binding tests incl. the story's named `test_distinct_rooms_bind_distinct_creatures`, plus the original 6-creature image tests. Room binding is FULLY WIRED in production (see Delivery Findings).

**Gate quality:** Both files are honest, non-vacuous gates. The failing test is dynamically keyed to the bestiary's own `low` tags (not a hand-list), so it cannot be gamed. The room tests interlock (`test_bound_creatures_are_renderable` ties a room binding to an image spec). No vacuous assertions found; nothing to fix in the tests.

**Rule coverage:** This is a content-authoring story (YAML), not a typed-language change — the lang-review checklist is N/A. The binding rules are SOUL (*Diamonds and Coal*) + the content constraints already encoded in the passing tests (style-free descriptions, inline no-text/no-caption clause, non-proper-noun names, referential integrity of bindings). Any authored spec must satisfy those (the 5 currently-passing image tests will enforce them on Dev's additions).

**Recommendation to Dev (Naomi) — TEA's read of the unresolved fork (Keith did not answer the design question, so this is the safe default, NOT a ruling):**
- **Prefer Option 1: re-tier + author selectively.** Re-tier the non-beneath_sunden-native / misplaced SRD monsters (e.g. aquatic kuo_toa/sahuagin/giant_octopus, warhorse_skeleton, etc.) OUT of the `low` band in `bestiary.yaml`, and author real diamond-grade `creatures.yaml` specs ONLY for the handful of genuine early dungeon opponents. This makes the gate pass honestly and honors 107-2's intent (early COMBAT opponents deserve authored portraits, not derived coal).
- **Do NOT mass-author 42 specs** for generic SRD trash — that's coal-getting-diamond-treatment (*Diamonds and Coal*).
- **Do NOT edit/weaken the failing test to dodge the gate.** If you conclude 158-52's derivation genuinely obsoletes the explicit-spec requirement (Option 2 — a legitimate position), ESCALATE to Keith and let TEA correct the test — don't reinterpret the acceptance gate unilaterally.
- **Watch the 158-52 interaction:** 158-52's content half (the `name_is_secret` flag) is NOT on the content `develop` branch, so its derivation model is only half-present. Re-tiering also changes encountergen sampling (which monsters appear early) — a real gameplay edit, so exercise world-design judgment per entry.
- **Verify GREEN** by re-running both 107-2 files in `sidequest-server` (they're gated on content being on disk).

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment (GM content pass — GREEN)

**Executed by:** GM (content-only lane), not the Dev agent — Keith activated `/pf-gm` and directed the authoring. The whole fix is content YAML (bestiary + creatures), squarely GM territory.

**Implementation Complete:** Yes. GREEN verified (run_id `158-60-gm-green`).

**Files Changed** (`sidequest-content`, branch `feat/158-60-content-gates-107-2`):
- `genre_packs/caverns_and_claudes/worlds/beneath_sunden/creatures.yaml` — authored **5 new low-band diamond specs**: `darkmantle` (ceiling-smother that kills the light), `piercer` (stalactite that falls point-first), `shadow` (incorporeal strength-drain), `stirge` (weightless flying thirst), `grimlock` (blind cave-humanoid that hunts by sound). Threat types the curated six lack. Same subject-only camera register; medium/style auto-layers from `visual_style.yaml` (descriptions kept style-free; each ends on the no-text/no-caption clause).
- `genre_packs/caverns_and_claudes/worlds/beneath_sunden/bestiary.yaml` — **re-tiered 37 entries `low → mid`** (tags lines ONLY; no other field or prose touched — verified via diff). These were raw WWN-SRD imports (aquatic/agrarian/mounted/redundant/foreign) that inherited a `low` tier tag with no world-design intent. **Keith-approved encounter-table decision (2026-07-03).**

**Fork resolution:** The failing gate demanded a `creatures.yaml` spec for all 48 low-tagged entries; only the 6 curated, world-named natives had them (and all 6 room bindings field only those 6 — they ARE the authored early roster). Per SOUL *Diamonds and Coal*, mass-authoring 42 diamond specs for generic SRD trash was rejected. Instead: author diamonds for the 5 genuinely cave-appropriate keepers (→ an **11-creature curated low band**) and re-tier the other 37 SRD entries to `mid`. The room-binding gate was already green (stale story premise — see TEA findings).

**Tests:** GREEN. 107-2 files 11/11 (incl. the previously-failing `test_every_low_tagged_bestiary_entry_is_renderable`). Full `tests/genre/`: 1177 passed / 49 skipped / 0 failed. Encountergen/bestiary/binding sweep: 79 passed / 31 skipped / 0 failed. **Total 1267 passed, 0 failed — no collateral regression from the re-tier.**

**Not changed:** No server/UI code (content-only). 158-52's `name_is_secret` flag is still absent on develop (its content half remains unlanded — TEA Gap finding; out of scope here).

**Handoff:** To verify (TEA simplify/quality-pass) → review → finish. NOTE: green-phase exit handoff not run by GM (GM is not a tdd phase owner); resume the workflow via `/pf-work` or `/pf-tea` to carry it forward.

## Dev Assessment (Naomi — green-phase close)

**Role:** Dev (phase owner) picking up the parked green phase. The GM authored the content fix and self-verified; my job is to independently confirm GREEN, verify the diff is honest (not gate-gaming), push the branch, and run the exit handoff the GM couldn't (GM is not a tdd phase owner).

**Implementation Complete:** Yes (authored by GM content pass, verified by Dev).

**Independent verification (not trusting the GM's claim):**
- **GREEN re-confirmed** via `testing-runner` (run_id `158-60-dev-green`): both 107-2 gate files **11/11 PASSED**, incl. the previously-RED `test_every_low_tagged_bestiary_entry_is_renderable` — now **PASSED**. Full `tests/genre/` sweep: **1177 passed / 0 failed / 49 skipped**. No regression from the re-tier's encountergen-sampling shift.
- **Diff audited for honesty** (`git diff develop...HEAD`):
  - `bestiary.yaml` — **37** entries re-tiered `low → mid`, and the change is **`tags:`-lines-ONLY** (verified: `grep '^[+-]' | grep -v '^[+-][+-]' | grep -v 'tags:'` → **0** non-tag lines). No stat/role/ability/description field moved under cover of a re-tier.
  - `creatures.yaml` — **5** genuine diamond specs added (darkmantle, piercer, shadow, stirge, grimlock), each subject-only camera register, style-free prose, closing on the no-text/no-caption clause, matching the curated six's format. Real content, not stubs.
- Two files changed, +146 / −37. No server/UI code (content-only).

**Branch:** `feat/158-60-content-gates-107-2` — committed (`83b2cf8`) and **pushed** to origin with upstream tracking. Working tree clean. No PR (SM owns PR creation in finish).

**Tests:** 11/11 gate + 1177 genre-suite passing (GREEN).

**Handoff:** To verify (TEA — Amos) for the simplify/quality pass, then review (Chrisjen).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 | confirmed 3, dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean (1 cosmetic note) | 1 | confirmed 1 (Low cosmetic), dismissed 0, deferred 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled per `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed test-debt (1 Medium, 2 Low) + 1 Low cosmetic; 0 dismissed, 0 deferred. **No Critical/High.**

## Reviewer Assessment

**Verdict:** APPROVED

Content-only YAML change in `beneath_sunden` (bestiary re-tier + 5 new creature image specs). I closed the green phase as Dev before this review, so I held the change to *extra* scrutiny rather than less — independently re-deriving referential integrity, binding safety, and the re-tier's disjointness, and running a full adversarial subagent pass. The shipped content is correct; the only real findings are pre-existing test-coverage gaps that this story widened but did not introduce, and they do not block correct content.

**Data flow traced:** bestiary.yaml `low` tag → `test_every_low_tagged_bestiary_entry_is_renderable` closure → requires a `creatures.yaml` spec by id → daemon Z-Image render. Safe because all 11 low-tagged entries (6 curated + 5 new) resolve to specs; the re-tier removed 37 from that closure without touching any room binding.

### Rule Compliance (exhaustive)

Content-authoring story — the lang-review checklists (Python/TypeScript) are **N/A** (no code changed). SOUL is the governing rule-set, plus the constraints the gate encodes. Every applicable rule enumerated against every instance:

- **SOUL *Diamonds and Coal*** — 42 instances (5 new specs + 37 re-tiers). Compliant. The 5 kept-low (darkmantle, piercer, shadow, stirge, grimlock) are diamond-grade authored portraits for genuine cave threats (ceiling-smother, fall-impale, incorporeal drain, flying thirst, blind sound-hunter) — threat types the curated six lack. The 37 re-tiers are raw WWN-SRD imports (aquatic kuo_toa/sahuagin, mounted warhorse_skeleton, agrarian/foreign reskins) with no world-authored name, no room binding, no world hook — correctly coal, correctly *not* mass-authored. `[RULE]` corroborates (rule 1, 0 violations).
- **Style-free descriptions** — 5/5 compliant (no medium/art tokens; verified manually + `[RULE]` rule 2 word-boundary scan).
- **Inline no-text clause** — 5/5 compliant (each ends on the no-text/no-caption/no-watermark clause; `[RULE]` rule 3).
- **Non-proper-noun `name`** — 5/5 compliant (evocative phrases ≠ bestiary proper nouns, no digits/quotes; `[RULE]` rule 4).
- **Referential integrity (spec→bestiary)** — 5/5 compliant. darkmantle→bestiary:2325 `[monstrosity,low]`, piercer→2345 `[monstrosity,low]`, shadow→3391 `[undead,low,incorporeal]`, stirge→604 `[beast,low,vermin]`, grimlock→851 `[humanoid,low]`. Tag-sets match spec tags. Not orphans.
- **Re-tier is tags-only** — 37/37 compliant. 0 non-tag lines changed (`grep` verified + `[RULE]` rule 6 enumerated all 37 ids). No stat/role/ability/prose moved.
- **Schema validity** — 5/5 compliant (id/name/description/threat_level:int/tags:list — identical shape to the existing six; `[RULE]` rule 7).
- **SOUL *Bind the Ruleset, Don't Balance It*** — N/A. Tier tags are encounter-sampling metadata, not combat math; no ruleset mechanic tuned.

### Observations

- `[VERIFIED]` **Referential integrity of the 5 new specs** — each maps to a real low-tagged bestiary entry with a consistent tag-set (evidence above). The gate only checks bestiary→spec, so I verified spec→bestiary by hand; not orphaned.
- `[VERIFIED]` **Re-tier disjoint from room bindings** — the 6 room-bound creatures (`gnaw_swarm, rope_spider, hold_skeleton, shaft_goblin, grave_ghoul, harrier_pack_leader`) all remain `low` + renderable; zero overlap between the 37 re-tiered ids and any room's `encounter_creatures`. Independently confirmed by `[TEST]` (Q3, all 30 room files) and `[RULE]` (rule 6). The "harrier-band overseer" I suspected was `goblin_boss` (generic SRD), not the bound `harrier_pack_leader` — distinct entries.
- `[VERIFIED]` **Assessment claim "SRD imports only" holds** — the theme-referenced natives `the_seep`/`wight` were already `mid` on `develop` (not in this diff), so no world-native creature was swept into the re-tier. Themes bind by id and carry difficulty via `depth_band`, not the bestiary tier tag, so the tags-only re-tier can't break a theme roster.
- `[TEST]` **[MEDIUM, non-blocking] Gate quality assertions skip the 5 new specs.** `test_every_low_tagged_bestiary_entry_is_renderable` (test file:164) is the only dynamically-scoped test and it asserts **presence only**. The four template-compliance tests (required-fields:94, style-free:109, no-text:127, non-proper-noun:142) iterate the hardcoded `LOW_BAND_IDS` 6-tuple (:40) and never inspect darkmantle/piercer/shadow/stirge/grimlock. `[TEST]` proved it empirically: a `pen-and-ink` leak + a proper-noun spec name both left all 11 tests green. **Content is correct now (verified 68/68), so nothing broken ships** — the gap is that a *future* quality regression on the new specs won't be caught. Pre-existing 107-2 test design; not introduced by this content story. → follow-up.
- `[TEST]` **[LOW, non-blocking] No converse referential-integrity test.** Nothing asserts every `creatures.yaml` spec resolves to a bestiary entry; a phantom orphan spec passed all 14 tests. Not exposed by this diff (all 5 specs verified resolvable). Mirror `test_all_room_bindings_reference_real_bestiary_ids`. → follow-up.
- `[RULE]` **[LOW, cosmetic] Tag-order drift** — `shadow` (`[undead,low,incorporeal]` bestiary vs `[undead,incorporeal,low]` spec) and `stirge` (`[beast,low,vermin]` vs `[beast,vermin,low]`). Same set; consumers do membership checks only. Every other paired entry keeps identical order — cosmetic drift from convention, not a defect.
- `[DOC]` `[VERIFIED]` **Comment block accurate** — all 6 factual claims in the new `LOW-BAND ADDITIONS` header verified true by `[DOC]` (curated-six-above, 37 re-tier, 5 genuine cave keepers, distinct threat types, style-free/auto-layer, SRD-linkage-in-id-only).
- `[EDGE]` N/A (disabled) — content-only YAML, no code branches; boundary check done manually: both files parse, no logic path consumes the diff.
- `[SILENT]` N/A (disabled) — no error-handling code in a content diff. The relevant silent-failure risk (a low creature rendering a blank 'T' chip) is precisely what the gate guards and it passes for all 11.
- `[TYPE]` N/A (disabled) — no typed code; spec schema shape verified via `[RULE]` rule 7.
- `[SEC]` N/A (disabled) — no auth/tenant/input surface in genre-pack content; the descriptions are image prompts in the same register as existing specs (no new injection surface).
- `[SIMPLE]` N/A (disabled) — the re-tier + selective-author is itself the *simpler* path (vs mass-authoring 42 specs), aligned with *Diamonds and Coal*.

### Devil's Advocate

Argue this is broken. **(1) The early band was gutted 48→11, a 77% cut.** A DM or the encounter generator expecting the full low roster now draws from a quarter of it — could sampling under-populate, loop, or error on a depleted tier? Checked: the full genre suite (1177) and encountergen/binding sweep pass with no min-count assertion tripping, and the 11 curated cave-natives are richer and more on-theme than 42 aquatic/mounted/foreign SRD reskins — this is intentional, Keith-approved cleanup, not depletion. **(2) The 'T-chip' bug returns for new content.** The whole story exists because a low creature rendered a bare letter chip with no portrait; I proved the gate would let a *new* low creature ship with a style-leaked or proper-noun spec and stay green — so the exact class of bug is unguarded for future additions. True, but the five specs this story ships are hand-verified compliant, so the regression is latent, not live. **(3) Orphan specs ship silently.** A typo'd or dangling `creatures.yaml` id has no test; it would render nothing and no gate would notice. Latent here (all 5 resolve). **(4) Order-sensitivity.** If any future consumer reads `tags[1]` as "the tier," shadow/stirge would mis-read as incorporeal/vermin-tier — but every consumer today does membership checks. **(5) Rooms beyond exp001.** I worried a deeper expedition room might bind a re-tiered creature; the test-analyzer enumerated all 30 room files and the bound set is exactly the curated six with zero overlap. **(6) A demoted iconic (rust_monster, specter, drow, giant_bat) that *should* stay a low diamond.** Defensible either way, but this is a world-design encounter-table call that is explicitly Keith's, and he made it (2026-07-03); the reviewer does not override a sanctioned design decision, and the kept-five restore the threat-type diversity. **Conclusion:** every attack lands on *future-proofing*, none on a *live* defect. The shipped content is correct and the named acceptance gate passes.

### Dispatch tag coverage

`[EDGE]` `[SILENT]` `[TEST]` `[DOC]` `[TYPE]` `[SEC]` `[SIMPLE]` `[RULE]` — all addressed above (3 disabled-domain N/A with manual coverage, `[TEST]` 3 findings, `[RULE]`/`[DOC]` clean, others N/A).

**Handoff:** To SM (Camina Drummer) for finish-story. Findings are non-blocking test-debt → captured as Delivery Findings for a follow-up gate-hardening story; do not hold this correct content behind cross-repo (server) test infra.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Improvement** (non-blocking): Story premise is half-stale. `test_beneath_sunden_room_binding_107_2.py`
  now PASSES entirely (all 5 tests, incl. the story's named `test_distinct_rooms_bind_distinct_creatures`).
  Six rooms declare `encounter_creatures` (entrance + exp001.r0–r4) and the binding is FULLY WIRED in
  production: `sidequest-server/sidequest/server/dispatch/room_creature_binding.py` (resolver) →
  `monster_manual_inject._append_authored_creatures` → `materializer.py`/`lookahead_worker.py`/
  `session_integration.py` + OTEL (`telemetry/spans/monster_manual.py`, `dungeon_materialize.py`).
  So 158-60's remaining scope is ONLY the creature-image gate. *Found by TEA during test design.*
- **Conflict** (blocking): The sole remaining RED — `test_beneath_sunden_creature_images_107_2.py::test_every_low_tagged_bestiary_entry_is_renderable`
  — demands a `creatures.yaml` image spec for **42** low-tagged bestiary entries (48 low-tagged total,
  only the original 6 have specs; creatures.yaml has 13 specs). The 42 are generic WWN-SRD monsters
  (constrictor_snake, giant_rat, spider, drow, gnoll, hobgoblin, orc_ruffian, kuo_toa, sahuagin,
  giant_octopus, specter, …). Two collisions make the "just author them" path wrong-by-default:
  (1) **158-52 reframed renderability as DERIVED from bestiary.yaml** (its render-script change landed on
  orchestrator `main`), so those 42 are arguably already renderable without an explicit spec — the test
  may be enforcing a now-stale "explicit-spec-required" requirement. (2) SOUL *Diamonds and Coal*: hand-
  authoring 42 diamond-grade specs for generic SRD trash mobs is coal-getting-diamond-treatment.
  Three-way fork — **author 42** / **re-tier the non-beneath_sunden-native monsters out of `low`** /
  **reconcile the test with 158-52's derivation model** — and it decides whether the work is Dev's
  (content) or TEA's (test correction). Needs a Keith design call. *Found by TEA during test design.*
- **Gap** (non-blocking): 158-52's CONTENT change is NOT on the content `develop` branch — `creatures.yaml`
  has no top-level `name_is_secret` flag despite 158-52's Dev Assessment claiming it was added. 158-52 is
  the stalled no-PR story, so only its orchestrator half (render script on `main`) landed. 158-60's baseline
  is therefore muddied by 158-52's partial landing; whoever resolves the fork above should account for the
  fact that 158-52 is not fully merged. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The re-tier moved 37 raw WWN-SRD imports out of `beneath_sunden`'s
  `low` band into `mid`, which shifts encountergen's early-band sampling for this world (fewer generic
  SRD mobs surface at low tier; the 11-creature curated roster now dominates). This is a deliberate,
  Keith-approved encounter-table change, but downstream world-design/playtest should confirm the early
  encounter mix still feels right in-session. Affects `genre_packs/caverns_and_claudes/worlds/beneath_sunden/bestiary.yaml`
  (encounter sampling, not code). *Found by Dev during implementation.*
- **Gap** (non-blocking): Carrying forward TEA's finding — 158-52's content half (`name_is_secret` flag)
  is still NOT on content `develop`, so beneath_sunden's derived-renderability model is only half-present.
  158-60 makes the low band pass via explicit specs + honest re-tier, which is robust either way; but if
  158-52's derivation later lands, the "explicit-spec-required" premise of `test_every_low_tagged_bestiary_entry_is_renderable`
  should be re-examined for redundancy. Affects `genre_packs/caverns_and_claudes/worlds/beneath_sunden/creatures.yaml`
  (no change needed now; flag for the 158-52 lander). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The `beneath_sunden` creature-image gate is not closed under low-band growth.
  `test_every_low_tagged_bestiary_entry_is_renderable` is dynamically keyed off bestiary `low` tags but asserts
  PRESENCE only; the four template-compliance tests (style-free, no-text clause, non-proper-noun name, required
  fields) iterate the hardcoded `LOW_BAND_IDS` 6-tuple, so the 5 specs 158-60 added (darkmantle/piercer/shadow/
  stirge/grimlock) get zero quality-gating (empirically proven: a style leak + a proper-noun spec name both pass).
  The shipped content is verified compliant, so no defect ships — but a future low-band addition can silently
  regress to the exact 'T-chip' class of bug 107-2 fixed. Affects
  `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py` (replace `LOW_BAND_IDS` with the
  bestiary-tag-derived id list used by the dynamic test, so all four shape checks extend to every low entry).
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): No converse referential-integrity test — nothing asserts every `creatures.yaml` spec id
  resolves to a real bestiary entry (a phantom orphan spec passed all 14 relevant tests). Not exposed by this diff
  (all 5 new specs resolve), but latent. Affects `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py`
  (add a converse test mirroring `test_all_room_bindings_reference_real_bestiary_ids`). Bundle with the finding above
  into one gate-hardening follow-up story. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Cosmetic tag-order drift — `shadow` and `stirge` list the tier tag in a different
  position in `creatures.yaml` than in `bestiary.yaml` (same set; every other paired entry keeps identical order).
  Non-functional (membership-only consumers). Affects
  `genre_packs/caverns_and_claudes/worlds/beneath_sunden/creatures.yaml` (reorder for convention consistency, or leave).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- No deviations from spec. TEA authored no net-new tests (the pre-existing 107-2 gate is the acceptance gate) and modified no tests; the failing gate was confirmed as-is.

### Dev (implementation)
- **Resolved the renderability gate by re-tier + selective author, not by authoring specs for all 42 low entries**
  - Spec source: 158-60 SM Assessment ("Two legitimate fix paths") + TEA Assessment ("Prefer Option 1: re-tier + author selectively")
  - Spec text: "Explicitly re-tier entries out of the low band if they are genuinely unreachable early (re-tiering is content YAML too — not a test edit to dodge the gate)."
  - Implementation: Re-tiered 37 misplaced WWN-SRD imports `low → mid` (tags-only) and authored 5 diamond `creatures.yaml` specs for the genuine cave keepers, rather than mass-authoring 42 specs. The naive reading of `test_every_low_tagged_bestiary_entry_is_renderable` (spec-per-low-entry) is satisfied by shrinking the low band to entries that were meant to be there.
  - Rationale: SOUL *Diamonds and Coal* — diamond-grade prose for generic SRD trash mobs is coal-getting-diamond-treatment. The test keys dynamically off the bestiary's own `low` tags, so the re-tier makes it pass honestly (correcting a mis-tagged import, not weakening the detector). This is the exact path the SM listed and TEA recommended — spec-sanctioned, hence severity minor.
  - Severity: minor
  - Forward impact: Encountergen early-band sampling for beneath_sunden shifts (Keith-approved 2026-07-03); logged as a Delivery Finding. No sibling-story code assumptions broken.

### Reviewer (audit)
- **Dev deviation "Resolved the renderability gate by re-tier + selective author"** → ✓ ACCEPTED by Reviewer:
  the re-tier + selective-author path is exactly the fix path the SM Assessment listed and TEA recommended, is
  Keith-approved (2026-07-03), and correctly applies SOUL *Diamonds and Coal* (5 diamonds for genuine cave
  threats; 37 SRD reskins re-tiered rather than mass-authored). Independently verified: re-tier is tags-only
  (0 non-tag lines), disjoint from all room bindings, and no world-native creature was swept in. Not a test dodge.
- **No undocumented deviations found.** The change matches the SM/TEA-sanctioned scope (beneath_sunden low-band
  specs + honest re-tier). The one thing worth flagging as an accepted-with-eyes-open trade is the early-band
  narrowing (48→11) — a real encounter-table shift, but a sanctioned world-design decision, already captured as a
  Dev + Reviewer Delivery Finding for playtest confirmation. No spec deviation slips through unaudited.