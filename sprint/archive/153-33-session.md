---
story_id: "153-33"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-33: [SWN-CHARGEN-NO-SKILLS-FOCI] author space_opera backgrounds + foci so SWN narrative chargen grants skills/foci per WWN SRD §1.3/§1.5 (completes 153-4 deferred AC-2)

## Story Details
- **ID:** 153-33
- **Jira Key:** (none — no Jira integration)
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Workflow:** tdd
- **Type:** Bug
- **Points:** 3
- **Priority:** P2
- **Repository:** sidequest-content (targets `develop`)
- **Stack Parent:** none (not a stacked story)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T05:36:09Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T23:36:10Z | 2026-06-21T23:37:43Z | 1m 33s |
| red | 2026-06-21T23:37:43Z | 2026-06-21T23:50:42Z | 12m 59s |
| green | 2026-06-21T23:50:42Z | 2026-06-22T00:09:09Z | 18m 27s |
| review | 2026-06-22T00:09:09Z | 2026-06-22T00:22:23Z | 13m 14s |
| green | 2026-06-22T00:22:23Z | 2026-06-22T05:28:57Z | 5h 6m |
| review | 2026-06-22T05:28:57Z | 2026-06-22T05:36:09Z | 7m 12s |
| finish | 2026-06-22T05:36:09Z | - | - |

## Sm Assessment

Setup complete. Story 153-33 ([SWN-CHARGEN-NO-SKILLS-FOCI]) is ready for the RED phase.

- **Workflow:** tdd (phased) → setup (SM) → red (TEA) → green (Dev) → review (Reviewer) → finish (SM)
- **Repos:** content (sidequest-content, targets `develop`)
- **Branch:** `feat/153-33-swn-chargen-backgrounds-foci` (cut from sidequest-content `develop` HEAD, clean tree)
- **Story context:** `sprint/context/context-story-153-33.md`
- **Jira:** none (project uses pf sprint, not live Jira)
- **Merge gate:** clear (no open PRs)

**The finding (epic-153 playtest sweep, deferred from 153-4):** SWN narrative chargen cannot grant skills and foci because space_opera defines no backgrounds.yaml or foci.yaml files. The server-side wiring is complete and fully tested (story 153-4); this story completes the content-authoring portion: define space_opera backgrounds + foci per the WWN SRD §1.3/§1.5, integrated with the existing chargen scenes (origins + archetype picker).

**Doctrine reminder for TEA/Dev:** This is the content-authoring complement to 153-4's server fix. The ruleset wiring already invokes `contribute_background_skills()` and `contribute_foci()` — they just had no inputs. The scope here is:
1. Author 5–6 genre-tier backgrounds (flavor-anchored to starship crews / political houses / frontier themes; each background specifies free_skill + quick_skills)
2. Author 8–10 foci (specializations per ADR-095; each focus level-1 entry has skills + a signature ability non-overlapping with class abilities)
3. Author space_opera/skills.yaml with the SWN skill list + space_opera flavor re-descriptions
4. Write integration tests proving chargen reaches background/foci contributions and emits OTEL spans

**ADR-142/143 reminder:** The ruleset-owned chargen seam is correct and proven; the missing piece is content. All skill names MUST be in skills.yaml (No Silent Fallbacks — CLAUDE.md). Foci abilities must not duplicate class signature abilities (ADR-095).

## TEA Assessment

**Tests Required:** Yes
**Reason:** Content-authoring story, but AC-4 mandates a behavioral wiring test that drives the real pack through chargen. The contribution seam (`contribute_background_skills` / `contribute_foci`) is live and proven against *synthetic* fixtures (`tests/game/test_chargen_seam_wiring.py`) — what's missing is proof the **real space_opera content** flows through it. That proof is the RED driver.

**Test Files:**
- `sidequest-server/tests/integration/test_153_33_swn_chargen_backgrounds_foci.py` — drives the real space_opera pack through the **production** chargen-defs seam (`resolve_backgrounds` / `resolve_foci` / `with_chargen_defs`, mirroring `connect.py:968-973`) across all three live worlds.

**Tests Written:** 10 parametrized cases (4 test functions) covering ACs 1, 2, 4, 5.

| Test | Covers | Cases | RED reason |
|------|--------|-------|------------|
| `test_real_swn_chargen_grants_background_skills` | AC-1, AC-4 | 3 worlds | background catalog empty → span `reason=no_matching_background_def`, no skills land |
| `test_real_swn_chargen_grants_foci` | AC-2, AC-4 | 3 worlds | no scene sets `focus_id` → empty foci list, no skills land |
| `test_real_swn_focus_grants_signature_ability` | AC-2 (ADR-095) | 1 | no foci applied → no focus ability on sheet |
| `test_swn_chargen_still_shaped_spread_with_content` | AC-5 | 3 worlds | **PASSES now** — regression guard for the 153-4 14-to-7 spread |

**Status:** RED — 7 failing (all `AssertionError`, production build path executed), 3 passing (AC-5 spread regression guards, correctly green as a baseline). Verified via Machine Shop (testing-runner): no import/collection/attribute errors — the suite drives the real engine cleanly; it fails on the missing-content assertions, which is true RED.

### Rule Coverage

| Rule / Constraint | Test(s) | Status |
|-------------------|---------|--------|
| WWN SRD §1.3 — background grants free_skill + quick_skills | `test_real_swn_chargen_grants_background_skills` (span payload ⊆ char.skills) | failing |
| WWN SRD §1.5 — foci grant level-1 skills + signature ability | `test_real_swn_chargen_grants_foci`, `test_real_swn_focus_grants_signature_ability` | failing |
| OTEL lie-detector — `swn.chargen.{background_skills,foci_applied}` fire with content | both wiring tests assert non-empty span attributes | failing |
| ADR-095 — focus ability distinct from class signature ability | `test_real_swn_focus_grants_signature_ability` (excludes class ability names) | failing |
| AC-5 / 153-4 — shaped 14-to-7 attribute spread preserved | `test_swn_chargen_still_shaped_spread_with_content` | passing (guard) |
| No Silent Fallbacks — every skill name resolves to skills.yaml | existing `test_pack_validator_crossref.py::test_all_live_packs_pass_cross_reference_lint` (CG3) — auto-engages on content landing; not duplicated (see deviation 3) | n/a until content ships |
| CLAUDE.md wiring rule — drives production path, not source-grep | both wiring tests use the real `connect.py` seam + OTEL span assertions (not `read_text()`) | satisfied |

**Rules checked:** all applicable SRD/ADR/CLAUDE rules have test coverage; skill-name resolution delegated to the existing validator crossref (documented).
**Self-check:** 0 vacuous tests. Every assertion checks a concrete value (span JSON payload non-empty + ⊆ char.skills/foci, not bare `is_some`). The 3 green AC-5 cases assert the exact `[14,12,11,10,9,7]` array.

**Handoff:** To Dev (Naomi Nagata) for GREEN. Two repos: author `skills.yaml` + `backgrounds.yaml` + `foci.yaml` (+ `focus_id` scene wiring) in **sidequest-content** (branch `feat/153-33-swn-chargen-backgrounds-foci`); make the server branch's failing tests pass; run full `just server-test` so the validator crossref guard engages. See the two **blocking-adjacent** Delivery Findings (background-id count, missing focus_id wiring) before authoring.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (two repos):**

*sidequest-content* (branch `feat/153-33-swn-chargen-backgrounds-foci`, commit on `develop` base):
- `genre_packs/space_opera/skills.yaml` (new) — 21 WWN/SWN canonical skills, space-flavored header
- `genre_packs/space_opera/backgrounds.yaml` (new) — 11 genre-tier backgrounds covering every origins tag across all 3 worlds (free_skill + quick_skills, SRD §1.3)
- `genre_packs/space_opera/foci.yaml` (new) — 5 vocation foci (crucible), each level-1 skill + out-of-combat signature ability distinct from the class combat ability (ADR-095)
- `genre_packs/space_opera/worlds/{aureate_span,coyote_star,perseus_cloud}/char_creation.yaml` — wired `focus_id` into all 5 crucible choices in each world (15 edits)

*sidequest-server* (branch `feat/153-33-swn-chargen-backgrounds-foci`, commit on `develop` base):
- `tests/integration/test_153_33_swn_chargen_backgrounds_foci.py` — background-skill assertion `==` → `>=` (max-of merge correctness; see deviation 3)

**Design choices:**
- Backgrounds on the per-world **origins** scene (flavor diverges per world); foci on the shared **crucible** vocation scene (identical across worlds → author 5 once, wire identically). The crucible is the "archetype scene" the story context names.
- Foci abilities are **out-of-combat knacks** (Pull Rank, Make It Hold, Know the Lanes, Know a Guy, Read the Room) — keeps them ADR-095-distinct from the class beat abilities AND honors "Bind the Ruleset, Don't Balance It" (no new combat-beat mechanics).

**Tests:** 10/10 passing on the target file (GREEN); regression sweep 133 passed / 0 failed / 2 pre-existing skips across chargen + space_opera + validator. Validator CG1/CG2/CG3 now engages for space_opera and passes (every `background:`/`focus_id` resolves; every skill name in `skills.yaml`). Ruff check + format clean.

**Self-review:**
- [x] Wired end-to-end — `focus_id`/`background:` flow through the real `connect.py` chargen seam into `Character.skills`/`Character.foci`; proven by the wiring test (not source-grep).
- [x] Follows project patterns — mirrors heavy_metal's backgrounds/foci shape and the genre-tier resolution model.
- [x] All ACs met — AC-1 (backgrounds), AC-2 (foci + abilities), AC-3 (skills.yaml), AC-4 (wiring test green + OTEL spans non-empty), AC-5 (shaped spread preserved). Count deviations (11 backgrounds, 5 foci) logged with rationale.
- [x] No Silent Fallbacks — validator enforces every reference resolves.

**Both branches pushed.** **Handoff:** To Reviewer (Chrisjen Avasarala) — review BOTH repos' branches.

### Rework — Round 1 (Reviewer findings addressed)

All 3 Required + both Recommended items from the Reviewer Assessment are fixed:

| # | Reviewer finding | Fix | Location |
|---|------------------|-----|----------|
| R1 | Wrong ADR cite (095→097) | Corrected in both shipped spots | `foci.yaml:11`, test signature-ability docstring |
| R2 | Bare `except Exception` swallow-hole | Replaced with `if scene.allows_freeform: apply_freeform else apply_auto_advance` — no try/except, real `WrongPhaseError` now propagates (confirmed `apply_auto_advance` raises `InvalidChoiceError` exactly when `scene.allows_freeform`) | `test:_build_first_choice_character` |
| R3 | Foci-ability coverage gap (1 of 5) | Parametrized `test_real_swn_focus_grants_signature_ability` over all 5 crucible vocations via a new `crucible_choice` walk param + `_FOCI_BY_CRUCIBLE` table; asserts each focus's named ability lands, is Class-sourced, and is distinct from class abilities | `test:253` |
| r4 | Stale "RED today" docstrings | Reframed module + 2 per-test blocks as regression-guard / "before 153-33" notes | `test` docstrings |
| r5 | Make It Hold ADR-097 boundary | Added "Cannot be used during an active confrontation — that is the Engineer class's Reroute Power, not this focus." | `foci.yaml` mechanical_effect |

**Tests:** 14/14 on the target file (signature-ability now 5 cases), regression sweep 141 passed / 0 failed / 2 pre-existing skips. Validator crossref still clean. Ruff check + format clean. Both branches re-pushed.

**Handoff:** Back to Reviewer for re-review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings at setup.

### TEA (test design)
- **Conflict** (non-blocking): AC-1 says "4–6 background origins," but the three live worlds' existing `char_creation.yaml` scenes already reference **11 distinct `background:` tags** — aureate_span: Core-educated / Frontier-raised / Void-born / Constructed; coyote_star: Outsystem-arrived / Far Landing-raised / Hub-born / Deep Root-adjacent; perseus_cloud: Regency-raised / Yula-born / Void-born / Edge-touched (Void-born shared). A single genre-tier `backgrounds.yaml` must define **all 11** of these ids (or each world ships a world-tier `backgrounds.yaml`, which the story scope explicitly defers). The "4–6" count cannot satisfy the scenes as authored. Affects `genre_packs/space_opera/backgrounds.yaml` and the three `worlds/*/char_creation.yaml` files (Dev/Architect must pick: 11 genre-tier entries, OR rename scene tags to a 4–6 genre set, OR per-world files). *Found by TEA during test design.*
- **Gap** (blocking the foci AC): **No space_opera `char_creation.yaml` sets `focus_id`** in any of the three worlds — the foci seam has zero scene inputs, so `contribute_foci` always runs with an empty list. The context says "the archetype scene references focus IDs," but space_opera has **no `archetype` scene** (its class picker is `crucible`: Officer/Engineer/Pilot/Smuggler/Diplomat). Dev must author `foci.yaml` **and** wire `focus_id` into a choice-bearing scene for every world (heavy_metal attaches `focus_id` alongside `background` on its `origins` choices — the reference pattern). Affects `genre_packs/space_opera/foci.yaml` (new) + `worlds/*/char_creation.yaml` (add `focus_id`). *Found by TEA during test design.*
- **Improvement** (non-blocking): the pack validator's CG1/CG2/CG3 chargen cross-ref checks (`sidequest/cli/validate/pack.py`) are **no-ops while space_opera ships no catalogs**, so today's dangling `background:` tags pass silently (a latent No-Silent-Fallbacks hole). The moment Dev authors `backgrounds.yaml`/`foci.yaml`/`skills.yaml`, `tests/cli/validate/test_pack_validator_crossref.py::test_all_live_packs_pass_cross_reference_lint` begins enforcing that **every** scene `background:`/`focus_id` resolves and every skill name is in `skills.yaml`. Dev should run the full `just server-test` (not only the new 153-33 file) so this guard catches any unreferenced tag. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): three classes — **Operative, Medic, Soldier** (`classes.yaml`) — are NOT crucible choices (the crucible offers only Officer/Engineer/Pilot/Smuggler/Diplomat), and foci are wired to the crucible, so any character who reaches those classes via the archetype path gets **no focus**. They still get their class signature ability; they just miss the chargen focus grant. Affects `genre_packs/space_opera/worlds/*/char_creation.yaml` (would need a focus path for those classes) and `foci.yaml` (3 more foci). Out of scope for 153-33 (the 5 crucible vocations are the visible chargen choices). *Found by Dev during implementation.*
- **Improvement** (non-blocking): foci are vocation-locked — a character's focus is fully determined by their crucible class choice (Officer→chain-of-command, etc.), not an independent pick. SWN foci are normally class-independent. A future enhancement could add a dedicated focus-selection scene so a player picks a focus separate from their vocation. Affects `worlds/*/char_creation.yaml`. *Found by Dev during implementation.*
- **Question** (non-blocking): for the mechanics-first players (Sebastien/Jade), is **one focus** per character enough crunch, or should space_opera grant a second focus (e.g. a disposition focus on the `role` scene)? SRD §1.5 grants one at chargen; the 2026-05-25 crunch-reintroduction spec might want more. Left at SRD-faithful 1 focus for this story; flag for Keith/playtest. Affects `worlds/*/char_creation.yaml` + `foci.yaml`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): the wrong-ADR citation is **upstream** — the story context (`sprint/context/context-story-153-33.md`) itself lists "ADR-095: Class Mechanical Surface", which is where the Dev/foci.yaml/test inherited it. ADR-095 is *Daemon Music Tier via ACE-Step*; the rule is **ADR-097**. The content CLAUDE.md (`sidequest-content/CLAUDE.md`) also mis-maps "095 (class mechanical surface)". Correcting the story context + content CLAUDE.md would stop this propagating to the next chargen story. Affects `sprint/context/context-story-153-33.md` and `sidequest-content/CLAUDE.md`. *Found by Reviewer during code review.*
- **Gap** (non-blocking, confirms Dev's finding): Operative/Medic/Soldier ARE archetype-reachable in chargen (`archetypes.yaml` has "Burned Operative"→Operative and a Medic archetype; `archetype_constraints.yaml` carries Medic/Operative `fallback_name`s), so a character routed to one of those three classes via the archetype path gets a class but **no focus** (foci wire only to the 5 crucible vocations). Not a regression (no one had foci before), but it means 3 of 8 classes are focus-less. A follow-up could author Operative/Medic/Soldier foci + a reachable focus path. Affects `genre_packs/space_opera/foci.yaml` + the chargen scenes. *Found by Reviewer during code review.*
- **Gap** (non-blocking, re-review round 2): the wrong-ADR cite has a third home that 153-33 did NOT touch — `genre_packs/space_opera/classes.yaml:31` still reads "Per ADR-095: exactly ONE signature ability per non-magical role." ADR-095 is *Daemon Music*; the rule is **ADR-097**. Out of scope for this story (classes.yaml is not in the diff), but it's the original source of the mis-cite and should be corrected with the story context + content CLAUDE.md in the same upstream cleanup. Affects `genre_packs/space_opera/classes.yaml:31`. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking, re-review round 2): `test_real_swn_focus_grants_signature_ability` declares the `span_exporter` fixture but never reads it (it asserts on `Character.abilities`, not spans). Harmless (the fixture still installs the tracer), but cosmetically misleading. Cleanup: drop the param, or add a `swn.chargen.foci_applied` span assertion to give the per-focus path real OTEL coverage. Affects `tests/integration/test_153_33_swn_chargen_backgrounds_foci.py:282`. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Integration test authored in sidequest-server, not sidequest-content**
  - Rationale: sidequest-content has no Python test harness (no `pyproject.toml`/`tests/`). The `CharacterBuilder` engine and pytest live only in the server; the 153-4 spread test and the heavy_metal chargen test follow the same cross-repo split. The story spans **two** repos.
  - Severity: minor
  - Forward impact: Dev authors content in sidequest-content AND keeps the server branch green; Reviewer reviews/merges **both** branches; SM's finish must account for two repos.
- **Test parametrized across all three live worlds, not a single genre-tier default**
  - Rationale: all three worlds are live (CLAUDE.md); a one-world fix is a half-wire (No half-wired features). Genre-tier authoring still satisfies this — one pack-level `backgrounds.yaml`/`foci.yaml` covering every world's scene tags is genre-tier, not a per-world override.
  - Severity: minor
  - Forward impact: Dev's genre-tier files must cover all three worlds' scene references (see the AC-1 Conflict finding).
- **No dedicated validator/CG3 RED test in this file**
  - Rationale: a single genre-tier file must cover every world's existing scene tags or the validator (CG1) fails and those worlds grant no skills. "4–6" can't cover 11 distinct tags without per-world files, which the story scope defers. Authored at the genre tier per scope ("genre-tier defaults"), not as per-world overrides.
  - Severity: minor
  - Forward impact: if a world later ships its own `backgrounds.yaml`, this genre set becomes its fallback default (world-first resolution).
- **Authored 5 foci, not the AC's "6–10"**
  - Rationale: the crucible offers exactly 5 vocation choices; one focus per character is SRD-faithful; `progression.yaml` has no focus-advancement consumer and there's no dedicated focus-pick scene, so authoring 6–10 would leave ≥1 unreferenced (dead content — CLAUDE.md). Live precedent: heavy_metal ships 5 foci, caverns 6.
  - Severity: minor
  - Forward impact: a future focus-advancement system or an independent focus-pick scene can extend the catalog; the 3 non-crucible classes (Operative/Medic/Soldier) have no focus yet (see Delivery Finding).
- **Relaxed the background-skill assertion from `==` to `>=` (max-of merge)**
  - Rationale: the builder merges background ∪ focus ∪ scene grants with **max-of**. When a background and the chosen focus grant the same skill (perseus_cloud Regency-raised Lead:0 + Officer/chain-of-command Lead:1), the sheet correctly shows the higher level. `==` encoded a false invariant; the sibling foci assertion already used `>=`. This is a test-correctness fix, not a content workaround — contorting content to dodge the overlap would only mask the next collision.
  - Severity: minor
  - Forward impact: none — the assertion still proves the background skill landed (presence + floor).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Integration test authored in sidequest-server, not sidequest-content**
  - Spec source: 153-33-session.md, "Repository: sidequest-content"
  - Spec text: "Repository: sidequest-content (targets `develop`)"
  - Implementation: AC-4's integration test lives at `sidequest-server/tests/integration/test_153_33_swn_chargen_backgrounds_foci.py` on a matching `feat/153-33-...` branch cut from sidequest-server `develop`. The content YAML stays in sidequest-content.
  - Rationale: sidequest-content has no Python test harness (no `pyproject.toml`/`tests/`). The `CharacterBuilder` engine and pytest live only in the server; the 153-4 spread test and the heavy_metal chargen test follow the same cross-repo split. The story spans **two** repos.
  - Severity: minor
  - Forward impact: Dev authors content in sidequest-content AND keeps the server branch green; Reviewer reviews/merges **both** branches; SM's finish must account for two repos.
- **Test parametrized across all three live worlds, not a single genre-tier default**
  - Spec source: context-story-153-33.md, AC-4 + Constraints ("authors only the genre-tier defaults")
  - Spec text: "Integration test drives the real space_opera pack through the full narrative chargen flow"
  - Implementation: the wiring tests run aureate_span, coyote_star, AND perseus_cloud (each choice-0 walk).
  - Rationale: all three worlds are live (CLAUDE.md); a one-world fix is a half-wire (No half-wired features). Genre-tier authoring still satisfies this — one pack-level `backgrounds.yaml`/`foci.yaml` covering every world's scene tags is genre-tier, not a per-world override.
  - Severity: minor
  - Forward impact: Dev's genre-tier files must cover all three worlds' scene references (see the AC-1 Conflict finding).
- **No dedicated validator/CG3 RED test in this file**
  - Spec source: context-story-153-33.md, AC-3 ("skills.yaml authored") + Constraints ("No Silent Fallbacks")
  - Spec text: "All skill names resolve to entries in a space_opera-specific `skills.yaml`"
  - Implementation: skill-name resolution is left to the existing `validate_pack_structure` CG3 lint, exercised by `test_pack_validator_crossref.py` (synthetic) and `test_all_live_packs_pass_cross_reference_lint` (real packs). I did not duplicate it.
  - Rationale: the validator is a **no-op until catalogs ship**, so a validator assertion cannot be RED now; the existing all-packs test auto-engages on content landing and is the correct enforcement surface. Re-authoring it here would be redundant and would pass trivially today.
  - Severity: minor
  - Forward impact: none — coverage exists; Dev must run full `just server-test`.

### Dev (implementation)
- **Authored 11 genre-tier backgrounds, not the AC's "4–6"** (resolves TEA's AC-1 Conflict finding)
  - Spec source: context-story-153-33.md, AC-1
  - Spec text: "Define 4–6 background origins"
  - Implementation: `genre_packs/space_opera/backgrounds.yaml` defines 11 backgrounds — every `background:` id the three worlds' origins scenes reference (Core-educated, Frontier-raised, Void-born, Constructed, Outsystem-arrived, Far Landing-raised, Hub-born, Deep Root-adjacent, Regency-raised, Yula-born, Edge-touched; Void-born is shared).
  - Rationale: a single genre-tier file must cover every world's existing scene tags or the validator (CG1) fails and those worlds grant no skills. "4–6" can't cover 11 distinct tags without per-world files, which the story scope defers. Authored at the genre tier per scope ("genre-tier defaults"), not as per-world overrides.
  - Severity: minor
  - Forward impact: if a world later ships its own `backgrounds.yaml`, this genre set becomes its fallback default (world-first resolution).
- **Authored 5 foci, not the AC's "6–10"**
  - Spec source: context-story-153-33.md, AC-2
  - Spec text: "Define 6–10 foci"
  - Implementation: `genre_packs/space_opera/foci.yaml` defines 5 vocation foci — one per crucible choice (chain-of-command/jury-rigger/dead-reckoning/black-market-contacts/cultural-fluency). A character is granted exactly ONE focus at chargen (its chosen vocation's), per SRD §1.5.
  - Rationale: the crucible offers exactly 5 vocation choices; one focus per character is SRD-faithful; `progression.yaml` has no focus-advancement consumer and there's no dedicated focus-pick scene, so authoring 6–10 would leave ≥1 unreferenced (dead content — CLAUDE.md). Live precedent: heavy_metal ships 5 foci, caverns 6.
  - Severity: minor
  - Forward impact: a future focus-advancement system or an independent focus-pick scene can extend the catalog; the 3 non-crucible classes (Operative/Medic/Soldier) have no focus yet (see Delivery Finding).
- **Relaxed the background-skill assertion from `==` to `>=` (max-of merge)**
  - Spec source: TEA test `test_real_swn_chargen_grants_background_skills` (the RED I inherited)
  - Spec text: `assert char.skills.get(skill) == level` (background grant lands exactly at its level)
  - Implementation: `assert char.skills.get(skill, -1) >= level` — background skill landed at AT LEAST its floor.
  - Rationale: the builder merges background ∪ focus ∪ scene grants with **max-of**. When a background and the chosen focus grant the same skill (perseus_cloud Regency-raised Lead:0 + Officer/chain-of-command Lead:1), the sheet correctly shows the higher level. `==` encoded a false invariant; the sibling foci assertion already used `>=`. This is a test-correctness fix, not a content workaround — contorting content to dodge the overlap would only mask the next collision.
  - Severity: minor
  - Forward impact: none — the assertion still proves the background skill landed (presence + floor).

### Reviewer (audit)

**TEA deviations:**
- **Integration test in sidequest-server, not content** → ✓ ACCEPTED: correct — sidequest-content has no Python harness; the 153-4 and heavy_metal chargen tests follow the same cross-repo split. Two-repo story is the right shape.
- **Test parametrized across all three live worlds** → ✓ ACCEPTED: agrees with author reasoning; a one-world fix would be a half-wire. Genre-tier authoring still satisfies the constraint (one pack-level file covering all worlds' tags is genre-tier).
- **No dedicated validator/CG3 RED test** → ✓ ACCEPTED: the validator is a no-op until catalogs ship, so it can't be a RED driver; `test_all_live_packs_pass_cross_reference_lint` auto-engages on content landing and is the right enforcement surface (confirmed passing this review).

**Dev deviations:**
- **11 genre-tier backgrounds vs AC's "4–6"** → ✓ ACCEPTED: resolves TEA's AC-1 Conflict; the three worlds' scenes reference 11 distinct tags, so a single genre-tier file must cover all 11. Stays genre-tier per scope. (Re-verified: 11 ids, exact-match to scene references.)
- **5 foci vs AC's "6–10"** → ✓ ACCEPTED: the crucible offers exactly 5 vocations, one focus per character is SRD-faithful (§1.5), `progression.yaml` has no focus consumer, so 6–10 would create dead content. Matches heavy_metal (5). Authoring to the wired choices is the No-Dead-Content-correct call.
- **`==` → `>=` background-skill assertion** → ✓ ACCEPTED: correct max-of-merge contract (a focus may raise a background skill, never lower it); the preceding `assert granted` guard preserves the "background granted nothing" RED signal, so the relaxation does not weaken the test.

**Undocumented deviations spotted:** none beyond the findings already raised. The `ADR-095` citation (which appears in the story context, the Dev deviations/findings, `foci.yaml`, and the test) is a factual-error finding, not a spec deviation — tracked in the Reviewer Assessment.

**Round 2 (re-review):** the rework introduced NO new spec deviations — it addressed reviewer findings (ADR cite, except narrowing, foci-ability coverage, docstrings, Make It Hold clause) without changing scope or contracts. All six logged deviations remain ✓ ACCEPTED as stamped above.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 (1 ADR-cite error, 1 bare-except note, 1 inline-comment note) | confirmed 2, dismissed 1 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 (1 high broad-except, 1 med single-world, 4 low) | confirmed 3, dismissed 3 (defensible/low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 (stale "RED today" docstrings, high) | confirmed 3 (low severity) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 violations / 74 instances (Rule 1 except, Rule 6 coverage, Rule 17 Make-It-Hold) + 71 compliant | confirmed 3, dismissed 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 6 confirmed (after dedup), 0 blocking-by-severity but rejecting on factual-error + test-integrity grounds, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

The implementation is **correct and complete** — all five ACs are met, the validator's CG1/CG2/CG3 cross-ref lint passes for space_opera (every `background:`/`focus_id` resolves, every skill name is in `skills.yaml`), there is zero dead content, zero silent fallbacks, and 157 tests pass. I verified the structural integrity independently (skill resolution, dead-content, ADR-097 distinctness) — it holds. I am **not** rejecting on correctness.

I am rejecting on a **confirmed factual error** plus **test-integrity** issues that are cheap to fix and shouldn't ship in an ADR-/OTEL-disciplined codebase. This is a tight green-rework polish pass, not a redesign.

### Findings

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [DOC] Low (factual) | **Wrong ADR citation.** Cites `ADR-095` for the "focus ability distinct from class signature ability" rule. ADR-095 is *Daemon Music Tier via ACE-Step*; the class-mechanical-surface / one-signature-ability rule is **ADR-097** (verified against `docs/adr/` titles). [RULE]/[DOC] — preflight. | `space_opera/foci.yaml:11` AND `test_153_33_...py:255` | Change `ADR-095` → `ADR-097` in both shipped locations. |
| [TEST] Medium | **Bare `except Exception` in the lie-detector walk helper** swallows any exception from `apply_auto_advance()` (incl. real chargen-FSM failures), converting a broken build into a "passing" test. Flagged HIGH by BOTH test-analyzer and rule-checker. I verified the branch is *unreached* for space_opera's current scenes (no non-confirmation no-choice scene), so it masks nothing today — but it is a latent hole in the very test meant to catch chargen breakage, and the fix is one line. [TEST]/[RULE] | `test_153_33_...py:137-140` | Narrow to the specific exception `apply_auto_advance()` raises for a non-auto-advanceable scene (e.g. `InvalidChoiceError`), or branch on `scene.allows_freeform` instead of exception-driven dispatch. The reference test `test_chargen_seam_wiring.py` calls `apply_auto_advance()` with no try/except. |
| [TEST] Medium | **Foci-ability coverage gap.** `test_real_swn_focus_grants_signature_ability` exercises only `aureate_span` choice-0 (the `chain-of-command` focus). The other 4 foci abilities (Make It Hold, Know the Lanes, Know a Guy, Read the Room) are never asserted to land — a focus authored skill-only (no ability) would pass undetected. [TEST]/[RULE] | `test_153_33_...py:253-282` | Cover all 5 foci abilities (walk crucible choices 0–4, or parametrize), so every focus's signature ability is proven to reach the sheet. |

### Recommended (fix-while-here, non-blocking)

- **[DOC] Stale docstrings.** The module docstring ("RED until the Dev authors the content", line 29) and the two per-test "RED today:" blocks (lines 170, 213) describe the pre-fix state in the present tense; the tests are now GREEN. Reframe as historical ("Before 153-33: …") or drop. [DOC] — comment-analyzer (3× high-confidence).
- **[RULE] "Make It Hold" boundary.** `foci.yaml:57` lacks an explicit "cannot be used during an active confrontation" clause, leaving its separation from the Engineer class's in-combat `Reroute Power` to narrator interpretation ("a few minutes" implies it but doesn't state it). Add one sentence to `mechanical_effect`. [RULE] — rule-checker (Rule 17, medium).

### Dismissed / dispatch-tag coverage

- **[EDGE]** disabled — assessed directly: the only boundary is the choice-0 walk; the `guard < 50` loop bound is correct; empty-grant is guarded by `assert granted` before the per-skill loop. No edge defect.
- **[SILENT]** disabled — assessed directly: the broad-except (above) is the one swallow; `_load_space_opera`'s `except PackNotFound → pytest.skip` is correct (specific exception, loud skip). No other swallowed errors.
- **[TYPE]** disabled — N/A: YAML content + a test; pydantic `extra="forbid"` models validate every field (rule-checker Rule 18, 21 instances clean). No stringly-typed/newtype concerns introduced.
- **[SEC]** disabled — assessed directly: no auth/tenant/secret surface; `json.loads` operates on trusted OTEL span attributes serialized by the production span helper, not external input. No security surface.
- **[SIMPLE]** disabled — assessed directly: the 5-foci/11-background catalog is the minimum that covers the existing scene tags (no over-engineering); content is DRY (genre-tier foci shared across worlds). No unnecessary complexity.
- Dismissed (test-analyzer low-confidence, with rationale): `>=` background assertion is **defensible** (the `assert granted` non-empty guard precedes the loop — an empty grant fails loudly); monkeypatch-tracer dependency is a loud-failure mode, not silent; AbilitySource.Class coupling is correct for current builder behavior.

### Rule Compliance

- **No Silent Fallbacks (CLAUDE.md):** ✓ — all 24 background+foci skill names resolve to `skills.yaml`; all 27 `focus_id`/`background:` tags resolve (rule-checker Rules 14/15; I re-verified independently). The validator (CG1/CG2/CG3) enforces this at load.
- **No Stubbing / no dead content:** ✓ — all 5 foci and 11 backgrounds are referenced by a scene (rule-checker Rule 16; re-verified).
- **ADR-097 (one signature ability per non-magical class; foci distinct):** ✓ on substance — 5 focus abilities (Pull Rank/Make It Hold/Know the Lanes/Know a Guy/Read the Room) are name- and mechanically-distinct from the 8 class abilities; ✗ on **citation** (cites 095, see finding). "Make It Hold" is the thinnest separation (recommended clause).
- **SOUL "Bind the Ruleset, Don't Balance It":** ✓ — focus abilities are out-of-combat knacks resolving via WN skill checks (Lead/Work/Sail/Connect/Convince vs difficulty 10); none introduces a new native combat-beat mechanic.
- **pydantic `extra="forbid"` (Background/Focus/FocusLevel/ClassAbilityDef/MechanicalEffects):** ✓ — no unknown fields (rule-checker Rule 18).
- **CLAUDE.md "No Source-Text Wiring Tests":** ✓ — the test drives the real `connect.py` chargen seam + asserts OTEL spans; no `read_text()` grep.

### Observations (≥5)

1. [VERIFIED] No-Silent-Fallbacks holds — every background/foci skill is in `skills.yaml`; evidence: `skills.yaml` 21 entries ⊇ the 13 background + 5 foci skill names (re-enumerated by hand + rule-checker Rule 14, 24/24 compliant).
2. [VERIFIED] No dead content — `foci.yaml` 5 ids == 5 referenced `focus_id`s; `backgrounds.yaml` 11 ids == 11 referenced `background:` tags (exact set match; rule-checker Rule 16).
3. [VERIFIED] ADR-097 substance satisfied — focus abilities are out-of-combat and distinct from the class beat abilities; evidence: `foci.yaml` mechanical_effects vs `classes.yaml` abilities, 1:1 comparison.
4. [DOC] Wrong ADR number (095→097) at `foci.yaml:11` and `test:255` — factual error in shipped content.
5. [TEST] Broad `except Exception` at `test:137` — latent swallow-hole in the wiring test (unreached today; flagged HIGH ×2).
6. [TEST] Foci-ability coverage gap — 4 of 5 foci abilities unasserted (`test:253`).
7. [VERIFIED] Data flow traced — player choice-0 → scene `mechanical_effects.{background, focus_id}` → `acc.background`/`acc.foci` → `resolve_backgrounds`/`resolve_foci` + `with_chargen_defs` → `contribute_background_skills`/`contribute_foci` (max-of merge) → `Character.skills`/`Character.foci` + OTEL spans. Safe: validator guarantees every tag resolves; max-of merge prevents stacking abuse.
8. [VERIFIED] Wiring is production-reachable — the test mirrors `connect.py:968-973` exactly (`resolve_*` + `with_chargen_defs`), so it proves the live path, not a test-only shortcut.

### Devil's Advocate

Argue this is broken. First: the wiring test is the project's lie-detector, and its walk helper swallows exceptions — so the strongest attack is "this test cannot fail when it should." If a future content edit inserts a no-choice scene mid-walk (a name-entry or autogen step), `apply_auto_advance()` could raise a real FSM error, the bare `except` would reroute to `apply_freeform`, and a mechanically corrupt character could reach `build()` while the suite reports GREEN — the exact "convincing narration with zero mechanical backing" CLAUDE.md warns about. Today the path is unreached, so the attack is latent, not live — but latent holes in a guarantee are how guarantees rot. Second: the foci-ability coverage gap means a careless future author could ship a focus with a skill but no ability (FocusLevel.abilities defaults to `[]`, no validator check), and only `chain-of-command` is ability-asserted — so four of five foci could silently lose their crunch and every test stays green. For Sebastien/Jade (the mechanics-first players this whole crunch-reintroduction serves), a focus that grants a skill but no signature ability is precisely the silent degradation they'd feel and the suite wouldn't catch. Third: a confused maintainer who follows the `ADR-095` pointer to understand the focus/class boundary lands in a music-generation ADR and learns nothing — wasted effort in a codebase that mandates "check the relevant ADR." Fourth: a narrator under pressure could read "Make It Hold" (restore a broken system, a few minutes) as usable mid-firefight, duplicating the Engineer's `Reroute Power` and eroding the one-ability-per-class discipline — the flavor implies out-of-combat but the mechanical_effect doesn't say it. None of these corrupts the shipped data today; all are cheap to close; together they clear the don't-rubber-stamp bar. What a stressed filesystem or odd config would do here is moot — this is static YAML + a deterministic test; the risks are integrity and accuracy, not runtime.

**Handoff:** Back to Dev (Naomi Nagata) for a targeted green-rework — fix the 3 Required items (ADR cite ×2, narrow the except, cover all 5 foci abilities); the 2 Recommended items (docstrings, Make-It-Hold clause) are cheap and worth folding in. Re-run `just server-test` + the validator; tests stay green throughout.
## Subagent Results

_Round 2 — re-review of the rework (4 enabled subagents re-run on the rework diff)._

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 14/14 green, sweep 127 pass, ruff clean, no new smells | confirmed green |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 2 (both round-1 findings RESOLVED; 1 new LOW: unused `span_exporter` param) | confirmed resolved 2, new 1 (non-blocking) |
| 5 | reviewer-comment-analyzer | Yes | findings | round-1 doc fixes confirmed accurate; 1 out-of-scope (classes.yaml:31 ADR-095) | confirmed resolved, 1 out-of-scope finding |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 18 instances — all 3 round-1 violations resolved, no new | confirmed all resolved |

**All received:** Yes (4 enabled re-run, 5 disabled pre-filled)
**Total findings:** 0 blocking; 2 non-blocking (pre-existing out-of-scope ADR cite in classes.yaml; cosmetic unused fixture param)

## Reviewer Assessment

_Round 2 — re-review after rework._

**Verdict:** APPROVED

All five round-1 findings are **verified resolved** by independent subagents plus my own checks — not merely claimed:

| Finding (round 1) | Status | Verified by |
|-------------------|--------|-------------|
| [DOC] Wrong ADR cite (095→097) — foci.yaml + test | ✅ Resolved | grep: 0 `ADR-095`, `ADR-097` in both (me + comment-analyzer) |
| [TEST] Bare `except Exception` swallow-hole | ✅ Resolved | only `except` left is `except PackNotFound` (env guard); `allows_freeform` dispatch matches builder.py:2523 (me + test-analyzer + rule-checker) |
| [TEST] Foci-ability coverage gap (1 of 5) | ✅ Resolved | 5 parametrized cases, each asserts a distinct named ability + source + ADR-097 distinctness; all green (preflight + rule-checker) |
| [DOC] Stale "RED today" docstrings | ✅ Resolved | no present-tense RED language remains (comment-analyzer) |
| [RULE] Make It Hold boundary | ✅ Resolved | confrontation-exclusion clause present, no new combat mechanic, ClassAbilityDef shape intact (rule-checker) |

The rework is **test-only + a 5-line content doc/constraint patch** — no production behavior changed. Validator CG1/CG2/CG3 still passes; 14/14 target tests green; 141 across the sweep; ruff clean. The fix removed the bare except (replaced with explicit `allows_freeform` control flow) and made the foci-ability assertion strictly stronger (named-ability-per-focus). No new substantive issue.

**Data flow re-traced:** crucible choice index `k` → `apply_choice(k)` at the `crucible` scene → `class_hint`+`focus_id` for vocation `k` → `acc.foci` → `contribute_foci` → `Character.foci` + the named ability on `Character.abilities` (source=Class). The parametrized test now proves this for all 5 vocations. Safe.

### Findings (both non-blocking)

| Severity | Issue | Location | Disposition |
|----------|-------|----------|-------------|
| [DOC] Low (out of scope) | `classes.yaml:31` still says "Per ADR-095" for the one-ability-per-class rule — the **pre-existing source** of the wrong cite. NOT in this story's diff (classes.yaml unchanged by 153-33). | `space_opera/classes.yaml:31` | Delivery finding (upstream cleanup); does not block 153-33. |
| [TEST] Low (cosmetic) | `test_real_swn_focus_grants_signature_ability` declares the `span_exporter` fixture but never reads it (asserts on sheet content, not spans). Harmless — the fixture still installs the tracer; the build emits spans regardless. Predates the rework (was in the round-1 single-world test too). | `test:282` | Delivery finding (optional cleanup: drop the param or add a `foci_applied` span assertion). |

### Dispatch-tag coverage

- **[TEST]** test-analyzer — both round-1 findings resolved; 1 new LOW (unused fixture param), non-blocking.
- **[RULE]** rule-checker — 0 violations, all 3 round-1 violations resolved, structural cross-checks clean.
- **[DOC]** comment-analyzer — all round-1 doc fixes accurate; flagged the out-of-scope classes.yaml cite.
- **[EDGE]** disabled — assessed directly: the new `crucible_choice` param is bounded 0–4 (5 crucible choices); `scene.id == "crucible"` matches all 3 worlds; no off-by-one (preflight green confirms each index maps to its vocation).
- **[SILENT]** disabled — assessed directly: the rework REMOVED the one swallow-hole; no `except` swallows remain (only `except PackNotFound → pytest.skip`).
- **[TYPE]** disabled — N/A: `crucible_choice: int = 0` is annotated; the Make It Hold edit is a free-string `mechanical_effect` (ClassAbilityDef `extra="forbid"` intact, rule-checker).
- **[SEC]** disabled — N/A: no security surface; static YAML + deterministic test.
- **[SIMPLE]** disabled — assessed directly: the `allows_freeform` branch is SIMPLER than the prior try/except; `_FOCI_BY_CRUCIBLE` is a tidy data table, no over-engineering.

### Rule Compliance (re-confirmed)

- **No Silent Fallbacks:** ✓ — all skills resolve; validator clean (rule-checker structural checks PASS).
- **No dead content:** ✓ — all 5 foci + 11 backgrounds referenced; `_FOCI_BY_CRUCIBLE` exercises all 5 foci.
- **ADR-097 (distinct foci/class abilities):** ✓ on substance AND citation now (095→097 in the story's files; classes.yaml is upstream/out-of-scope).
- **SOUL Bind-the-Ruleset:** ✓ — Make It Hold clause restricts to out-of-combat; no new beat mechanic.
- **CLAUDE.md No Source-Text Wiring Tests:** ✓ — drives the real seam + OTEL; no `read_text()`.

### Observations (≥5)

1. [VERIFIED] Bare except gone — only `except PackNotFound` (env guard) remains; evidence: grep shows 1 `except` at test:74, the line-147 match is a comment.
2. [VERIFIED] All 5 foci abilities asserted — `_FOCI_BY_CRUCIBLE` × per-focus named-ability check; evidence: preflight lists all 5 parametrized cases passing.
3. [VERIFIED] ADR cite corrected — 0 `ADR-095` in foci.yaml + test; `ADR-097` present in both.
4. [VERIFIED] Make It Hold bounded — confrontation-exclusion clause at foci.yaml:64-65; "Reroute Power" confirmed as Engineer's ability (classes.yaml:173).
5. [DOC] classes.yaml:31 pre-existing wrong ADR cite — out of scope, tracked as finding.
6. [TEST] unused span_exporter param — cosmetic, tracked as finding.
7. [VERIFIED] No production behavior change — rework is test + a doc/constraint string; validator + 141 tests green.

### Devil's Advocate

Argue the rework is broken. The strongest attack: the new `crucible_choice` walk could mis-map — if choice index `k` did not actually route to vocation `k`'s focus, the parametrized test would assert the wrong focus and either falsely pass or falsely fail. But preflight ran all five cases green with the exact `[k-focus_id-ability_name]` ids, and rule-checker confirmed the `_FOCI_BY_CRUCIBLE` table matches the crucible ordering in all three worlds — so the mapping holds. Second attack: dropping the try/except could break the walk if a space_opera scene legitimately needed the freeform fallback that the bare except used to provide. But the only no-choice scene is `confirmation` (which exits the loop), and `pronouns`/origins/etc. all carry choices; the `allows_freeform` branch is the correct dispatch and aligns with the engine's own guard (apply_auto_advance raises exactly when allows_freeform is truthy) — and 14/14 green proves the walk still reaches confirmation for every case. Third: the unused `span_exporter` could mask removed span emission — true in the narrow sense that this one test wouldn't catch it, but `test_real_swn_chargen_grants_foci` DOES assert the `foci_applied` span fires with content, so span coverage exists elsewhere; the gap is cosmetic, not a hole in the suite. Fourth: the Make It Hold clause is prose a narrator could still ignore — but that is true of every ability's mechanical_effect; the clause now states the constraint explicitly, which is the most a content file can do. Nothing here corrupts the shipped data or the production path; the residual items are a pre-existing out-of-scope cite and a cosmetic param. Approve.

**Handoff:** To SM (Camina Drummer) for finish-story. Both branches (sidequest-content + sidequest-server, `feat/153-33-swn-chargen-backgrounds-foci`) are green, pushed, and approved. Two non-blocking delivery findings logged for a future cleanup pass.