---
story_id: "153-28"
jira_key: ""
epic: "153"
workflow: "trivial"
---
# Story 153-28: [BENEATH_SUNDEN-AUTHOR-CAMP-CAST] author the surface-camp cast (Brecca Half-Hand + rope-keepers)

## Story Details
- **ID:** 153-28
- **Jira Key:** (none — content-only, no Jira)
- **Workflow:** trivial
- **Stack Parent:** none
- **Type:** chore
- **Points:** 2
- **Priority:** p2

## Context

Playtest follow-up (Sprint 2626). beneath_sunden authors ZERO NPCs today (`pregen.authored_npcs_seeded: inserted=0, total_authored=0`), so Brecca Half-Hand (the surface-camp boss who speaks every turn in chargen) is pure narrator invention rather than a persistent, name-anchored, disposition-tracked NPC.

There is NO `npcs.yaml` in the beneath_sunden world dir — it must be CREATED.

### Deliverable
Author `genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml` with the surface-camp cast:
- **Brecca Half-Hand** — winch-keeper / camp boss; the diamond; missing three fingers from her left hand; speaks during chargen, narrates the ledger, voices the camp's grim economy
- **The rope-keepers** — a short roster (per lore: "Ropefoot is a SHORT roster — a winch-keeper, a few who will not go down again"); no invented strangers; placed at region `ropefoot`

### Canon Sources (beneath_sunden world context)
- **Lore:** Ropefoot is the bootworn camp at the lip of the shaft — winch-house, the kept fire, the board of the unreturned; the camp learned its count by the only method the deep teaches: counting who went down against who came back. The people here are the ones who keep the rope and the ones who have stopped going down and have not yet left.
- **Chargen framing:** Brecca Half-Hand (missing three fingers from left hand, old sweat) counts the bones, arranges the trades, dips the quill for the tally, and reaches beneath the table for the gear pack. Voice: grave, economical, speaking in cargo-cult procedural language of the ledger.
- **Seed tropes:** "A Name on the Board You Half-Knew" — NPCs the camp does not have; the board is the camp's only record; the ropefoot roster cannot afford invented strangers.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-22T21:27:14Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T21:08:27.428408+00:00 | 2026-06-22T21:12:27Z | 3m 59s |
| implement | 2026-06-22T21:12:27Z | 2026-06-22T21:20:39Z | 8m 12s |
| review | 2026-06-22T21:20:39Z | 2026-06-22T21:27:14Z | 6m 35s |
| finish | 2026-06-22T21:27:14Z | - | - |

## Delivery Findings

No upstream findings at setup time.

## Design Deviations

None at setup time.

## Implementation Notes

### AuthoredNpc Schema (from sidequest-server/sidequest/genre/models/authored_npc.py)
- **id** (str, required, min_length=1) — unique identifier for the NPC
- **name** (str, required, min_length=1) — display name
- **pronouns** (str, default="") — he/him, she/her, etc.
- **role** (str, default="") — occupation or title
- **ocean** (dict[str, float] | None, default=None) — OCEAN personality dict with keys O, C, E, A, N (each 0.0–1.0) per ADR-042
- **appearance** (str, default="") — visual description
- **age** (str, default="") — age descriptor
- **distinguishing_features** (list[str], default=[]) — list of physical/behavioral distinguishing marks
- **history_seeds** (list[str], default=[]) — prose snippets for voice/mannerisms/background; narrator extracts verbal tics and uses them
- **initial_disposition** (int, default=0, -100 to 100) — starting standing with the player per ADR-020; warm cast defaults friendly (15–30)
- **location_tags** (list[str], default=[]) — lowercase location/biome substrings for placement awareness; e.g. ["ropefoot", "winch"] so the NPC surfaces as "nearby (not yet met)" when the location matches

### pregen.py _seed_authored_npcs contract
- Reads `pack.worlds[world].authored_npcs` from the loaded `World` object
- Inserts NPCs with `exact=True` dedup (case-insensitive name match)
- Carries `location_tags` through to `ManualNpc.location_tags` so placement-aware selection surfaces the NPC at the right location before narration
- Expected fields in the data blob passed to `manual.add_npc()`: name, role, culture (empty string OK), and optionally ocean_summary (appearance)
- Returns count of inserted + tag-refreshed entries; logs outcome on every successful read

### Template (glenross npcs.yaml structure)
- YAML root: `version`, `world`, `npcs` (list)
- Each NPC is a dict with the AuthoredNpc schema fields above
- Voice notes (mannerisms, tics, signature phrases) go in `history_seeds` as prose; narrator extracts and uses them

## Acceptance Criteria

- [ ] `npcs.yaml` exists in `genre_packs/caverns_and_claudes/worlds/beneath_sunden/`
- [ ] File loads without validator errors
- [ ] Brecca Half-Hand authored with required fields + canon-consistent appearance/voice
- [ ] Rope-keepers roster authored (short, placed at ropefoot, no invented strangers)
- [ ] Names/voice are canon-consistent with beneath_sunden lore (grave, economical, ledger-speak, moria-as-tragedy register)
- [ ] `pregen.authored_npcs_seeded` for beneath_sunden shows `total_authored > 0`

## Route Notes

**This is a CONTENT-authoring story — implement phase should route to a content specialist (gm/writer agent), not engine-Dev.**

## Sm Assessment

**Story:** 153-28 — [BENEATH_SUNDEN-AUTHOR-CAMP-CAST]. Content-authoring follow-up (Sprint 2626), 2 pts, trivial workflow, content repo.

**The gap:** beneath_sunden has no `npcs.yaml` at all → `pregen.authored_npcs_seeded total_authored=0`, so Brecca Half-Hand (the chargen camp boss who speaks every turn) is pure narrator invention with no persistent, name-anchored, disposition-tracked identity. Deliverable: author the Ropefoot surface-camp cast (Brecca + a short rope-keeper roster) into a new `npcs.yaml`.

**Relationship to 153-27 (just shipped):** complementary, NOT the same path. 153-27 was engine recognition of *procedural deep* region ids (the deep is cast-less by design). 153-28 authors the *static surface* (region `ropefoot`) cast via the pregen authored-NPC seeding path (`_seed_authored_npcs` reads `pack.worlds[world].authored_npcs`) — a different mechanism from Seam-2 cast-staging. No overlap, no conflict.

**Setup decisions:**
- **Workflow:** trivial (phased: setup → implement → review → finish). Pure content authoring, no test surface; trivial is correct.
- **Repo/branch:** sidequest-content only; branch `feat/153-28-beneath-sunden-camp-cast` off origin/develop (content trunk is `develop`), created on a freshly-pulled develop (221e901).
- **Jira:** skipped — not configured.
- **Routing override:** per Keith's standing preference (world/pack YAML → content specialist, keep engine code off the main thread), the implement phase goes to the `writer` content agent (not engine-Dev), followed by a `cliché-judge` pass + the content validator as the review bar. The trivial workflow nominally lists `dev` as the implement owner; I am routing the authoring to a content specialist as the SM's coordination call.
- **Research landed in context doc** (`context-story-153-28.md`): AuthoredNpc schema, the `_seed_authored_npcs` contract, the glenross `npcs.yaml` template, beneath_sunden canon (Ropefoot voice, Brecca chargen framing), and 7 acceptance criteria.

**Verdict:** Setup complete and verified — session, context doc, branch confirmed. Ready for content authoring.

## Implementation (content authoring — writer agent)

**Deliverable:** `genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml` (new file). Authored by the `writer` content specialist; commit `7ea3310` on `feat/153-28-beneath-sunden-camp-cast`.

**Cast (4 NPCs — short roster, no invented strangers):**
- **Brecca Half-Hand** (they/them) — winch-keeper / camp boss; the diamond. disp=22.
- **Ondre Drumhand** (he/him) — drum-hand at the winch. disp=20.
- **Salla Who Came Back Thin** (she/her) — went deepest, will not go again; instantiates the `One Who Will Not Go Down Again` seed trope. disp=16.
- **Harmund Fuel-Count** (he/him) — keeps the fire's fuel rota; instantiates the `Cold Has Crept Up the Collar` seed trope. disp=18.

All `location_tags: ["ropefoot"]`, warm-cast `initial_disposition` 16–22 (ADR-020), OCEAN on the 0.0–1.0 schema scale (ADR-042). Voice register grave/ledger-speak, threaded into the world's existing `archetypes.yaml` voice contracts + `seed_tropes.yaml` hooks.

**Canon decision (load-bearing):** Brecca's pronouns are **they/them**, sourced from the real `openings.yaml` chargen framing (the context-doc template had guessed she/her; the writer correctly verified against canon and overrode it). No conflicting Brecca-pronoun reference exists elsewhere in the world (grepped).

**AC verification:**
- AC1/AC2 (file exists + loads, no validator errors): `just content-validate caverns_and_claudes` → **PASS (0 errors, 13 pre-existing pack warnings)**; pydantic schema load clean.
- AC3 (Brecca authored, canon-consistent): yes.
- AC4 (rope-keepers short roster at ropefoot, no invented strangers): 3 others, all rope/fire-anchored; deliberately did NOT instantiate the `Salvager` archetype (would read as the forbidden merchant).
- AC5 (canon voice): cliché-judge confirms register fit.
- AC6 (`total_authored > 0`): load-check shows `authored_npcs = 4` (was 0).

## Subagent Results

Content story (pack YAML only — no code/test surface). The two enabled engine specialists ran on the content diff; the engine code-diff specialists with no YAML surface (edge/silent/type/simplifier/rule-checker/comment) are disabled via settings; `cliché-judge` was added as the content-review specialist.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | content-validate PASS (0 errors); 0 smells; NPC structure OK; flagged Harmund id≠name nit | nit confirmed → fixed (id `harmund_who_keeps_the_fuel` → `harmund_fuel_count`) |
| 2 | reviewer-security | Yes | clean | none (no secrets/PII; no prompt-injection in authored prose per ADR-047) | N/A |
| 3 | cliché-judge | Yes | findings | 1 fix, 1 nit | fix applied (Ondre stock phrase "gone soft over hard", npcs.yaml:120); nit dismissed (Brecca gesture rescued by the count motif) |
| 4 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (no logic-path surface in pack YAML) |
| 5 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (no tests in content repo) |
| 7 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled engine specialists + cliché-judge returned; the rest disabled via settings)
**Total findings:** 2 confirmed-and-fixed (Harmund id, Ondre phrase), 1 nit dismissed; 0 blocking

## Reviewer Assessment

**Verdict:** APPROVED (no blockers; 2 confirmed nits fixed, 1 dismissed). Content-QA path (cliché-judge + validator) plus the 2 enabled engine specialists.

Tagged findings (enabled specialists + content review):
- **[PRE]** reviewer-preflight: `content-validate caverns_and_claudes` PASS (0 errors, 13 pre-existing pack warnings); 0 code smells; NPC structural check clean (4 NPCs, required fields, OCEAN axes, dispositions 16–22 in warm band, tags `["ropefoot"]`). Flagged Harmund `id` (`harmund_who_keeps_the_fuel`) ≠ name slug — **confirmed and fixed** to `harmund_fuel_count` (the other three ids are exact name slugs; brand-new file, no cross-consumers; re-validated).
- **[SEC]** reviewer-security: **clean** — no secrets/tokens/PII; no ADR-047 prompt-injection in the authored prose (history_seeds/appearance/role are pure in-world grave-fantasy; Salla's navigation detail is authored lore in character voice, not a command).
- **cliché-judge:** 0 blockers, 1 fix, 1 nit. Fix (stock phrase "gone soft over hard", Ondre appearance npcs.yaml:120) **applied**; nit (Brecca's "take the count … with their eyes") dismissed — rescued by the count motif. Judge: cast is "clean and earns its specificity"; 3 of 4 NPCs are detail-for-detail instantiations of existing world seed tropes (exemplary).
- **load-check:** pack parses; `total_authored=4`; both fixes confirmed in the loaded model.

All findings resolved; final state committed as `57947d6` on the content feature branch.

**Handoff:** To SM finish — PR to content `develop`, merge, archive.