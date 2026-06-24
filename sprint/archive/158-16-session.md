---
story_id: "158-16"
jira_key: ""
epic: "158"
workflow: "trivial"
---
# Story 158-16: beneath_sunden seeds an empty quest spine — author opening active_stakes/quest_seed so the Quests tab isn't blank on driveless WWN PCs

## Story Details
- **ID:** 158-16
- **Type:** bug
- **Points:** 1
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Repos:** content
- **Branch Strategy:** gitflow (feat/158-16-beneath-sunden-quest-spine-seed)

## Special Notes
**Content-Only Story:** This story is content authoring only (sidequest-content YAML/fixtures). It will be validated via `load_genre_pack` + cliché audit, not unit-tested. Per project convention, content-only stories route to the GM/world-builder for validation, not Dev for a RED phase.

## Acceptance Criteria
- beneath_sunden's opening authors a non-empty active_stakes/quest_seed so a freshly-created driveless WWN PC sees a populated Quests tab
- The pack still loads cleanly via load_genre_pack
- New quest-seed content passes a cliché audit

## Sm Assessment

**Routing:** Content-only story (`repos: content`), no code. Per project convention (Keith's standing guidance: "content is validated, not tested"), this routes to the **GM/world-builder** for authoring + validation — `load_genre_pack` + cliché audit — **not** Dev's implement phase or a TEA RED phase. The `trivial` workflow's formal `implement` owner is `dev`; I am deliberately diverging to `gm` because there is no code to implement, only world YAML to author and validate.

**Merge gate:** Clear. `sidequest-content` has zero open PRs. The only open PR anywhere is an unrelated dependabot bump in `sidequest-server` (#1063, pydantic-settings) — not a sprint-story PR, does not block.

**Scope:** `beneath_sunden` (caverns_and_claudes WWN port) seeds an empty quest spine — driveless WWN PCs (no `drive` motivation) land on a blank Quests tab because the world's opening authors no `active_stakes`/`quest_seed`. Fix is content authoring in the world's opening so the spine is non-empty even for driveless PCs.

**Precedent (pointer, not prescription):** The glenross_drive fix (153-13) handled the analogous "world missing a drive scene → `drive='' → quest_seed` falls back" pattern. Quest-seed/crunch loads from content tiers; authored opening lives in the world's `openings.yaml` / `world.yaml`. The GM should locate the actual seed mechanism before authoring — do not assume the file.

**Standalone (no Jira):** `jira_key` empty. Skip all Jira ceremony at finish.

**Next agent:** gm (world-builder validation, not Dev).

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-24T14:16:28Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-24T13:47:08Z | 2026-06-24T13:51:09Z | 4m 1s |
| implement | 2026-06-24T13:51:09Z | 2026-06-24T14:06:09Z | 15m |
| review | 2026-06-24T14:06:09Z | 2026-06-24T14:16:28Z | 10m 19s |
| finish | 2026-06-24T14:16:28Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[GM / implement] Fix delivered + validated (non-blocking).** Root cause traced before authoring (per SM's "locate the mechanism, don't assume the file"): `seed_quest_spine` (server `game/quest_seed.py`) runs *after* `materialize_from_genre_pack`, which copies the FRESH history chapter's `active_stakes` onto the snapshot. With beneath_sunden authoring no `active_stakes` (history) and no `quest_seed` (openings), a WWN PC with empty `drive`+`calling` hit the empty-source branch → `severity="warning"` span, no quest minted → blank Quests tab (`quest_log {}`, `quest_anchors []`, `active_stakes ""`).
  - **Edit A (load-bearing):** authored `active_stakes` on all four maturity chapters in `history.yaml`. Materialization sets `snap.active_stakes`, so `seed_quest_spine` takes the **defer** path (`if snapshot.active_stakes.strip()`) — non-empty stakes for EVERY PC, drive or no drive.
  - **Edit B (complementary):** authored a **giverless** `tone.quest_seed` (`the_unspent_hold`, anchor `the_dropmouth`) on both openings. `mint_quest_offer` never reads `giver`, and stashing is bait-not-mint — so the world's no-quest-giver conceit holds; the router mints a tracked QuestEntry only when the player chooses the rope (acceptance = the descent).
  - **Validation (content = validated, not unit-tested):** `load_genre_pack(caverns_and_claudes)` PASS; `validate.pack` PASS (0 errors, 13 pre-existing warnings, **0 new**); end-to-end harness — FRESH materialize → non-empty `active_stakes`; a constructed **driveless** `Character` through `seed_quest_spine` → defers, stakes preserved, no competing `seed_drive` quest. Cliché audit PASS (only new entity "The Unspent Hold" derives from the world's existing "unspent hold" idiom).
  - **Reviewer note:** content-only diff (+52 lines, 2 YAML files, no engine change). No `.py`/`.ts` touched, so the python/typescript lang-review gate extensions are no-ops. Branch `feat/158-16-beneath-sunden-quest-spine-seed` (sidequest-content), commit `db48758`, pushed.

### Reviewer (code review)

- **Improvement** (non-blocking, FIXED in review): the authored `quest_seed.stakes` was a near-verbatim duplicate of the fresh chapter's `active_stakes`. `mint_quest_offer` (server `game/quest_offer.py:114`) only fills `active_stakes` from the seed when empty (fill-don't-clobber), and materialization always sets the chapter `active_stakes` first — so the seed-level stakes could never surface (the router bait surfaces `quest_id`/`title`/`giver`, not `stakes`). Removed the inert duplicate from both openings (commit `42ffc57`); chapter owns the stakes line, quest_seed owns the quest. *Found by reviewer-silent-failure-hunter (high confidence), confirmed and fixed during review.*
- **No further upstream findings.** Preflight GREEN (loader + validator), security clean. The drive-spine warning path in `quest_seed.py` is unchanged and remains the loud-fail signal for any world that authors NO stakes — this fix simply moves beneath_sunden onto the documented "world-authored spine wins" defer path.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)

- **Workflow phase divergence (documented in SM Assessment):** the `trivial` workflow's `implement` phase was executed by the **GM**, not Dev. The SM logged this deliberately (content-only story → "content is validated, not tested" convention). → ✓ **ACCEPTED by Reviewer:** correct routing for a content-only YAML story; there is no code to implement, and the GM ran the proper content gates (`load_genre_pack` + validator + cliché). No undocumented deviations found in the diff.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (loader + validator both GREEN, 0 new warnings) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 | confirmed 1 (LOW), fixed in review |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 confirmed (LOW, fixed in `42ffc57`), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Content-only change (sidequest-content YAML, 3 commits on `feat/158-16-beneath-sunden-quest-spine-seed`: `db48758` fix, `42ffc57` review cleanup). No engine code touched. The fix is correct at the mechanism level, validated end-to-end, and respects the world's authored voice.

**Data flow traced (input → Quests tab):** `history.yaml` chapter `active_stakes` → `materialize_from_genre_pack` copies the FRESH chapter onto `snapshot.active_stakes` (`world_materialization.py:316-317`) → `seed_quest_spine` sees non-empty stakes and **defers** (`quest_seed.py:53`) instead of degrading to a blank spine → `build_quests_payload` projects `active_stakes` (`projection/quests.py:140`) → non-blank Quests tab for a driveless PC. Independently re-confirmed by the author's harness: FRESH materialize yields non-empty `active_stakes`; a constructed driveless `Character` makes the seed defer (stakes preserved, no competing `seed_drive` quest, `quest_log` empty until the player takes the rope).

**Pattern observed:** giverless self-directed `quest_seed` (`openings.yaml` solo + MP). `giver` defaults to `""` and is never read by `mint_quest_offer` — so the world's no-quest-giver conceit (`avoid_at_all_costs: "an old man approaches you with a quest"`) holds. The quest mints only on player acceptance (taking the rope), which is the world's own core action. Correct use of the bait-not-mint contract (`quest_offer.py:30-43`).

**Error handling / loud-fail integrity:** the loud-warning path in `seed_quest_spine` for a truly empty seed is **unchanged** — this fix moves beneath_sunden onto the documented "world-authored spine wins" defer branch, it does not weaken the No-Silent-Fallbacks guard. The one redundancy finding (seed `stakes` shadowed by chapter `active_stakes`) was removed so no inert authored field remains.

**Dispatch-tag coverage:**
- `[SILENT]` — silent-failure-hunter: 1 finding (redundant seed `stakes`), **CONFIRMED** as LOW and **FIXED** in `42ffc57`. Not a true silent failure (the discard is intentional fill-don't-clobber), but it left an inert duplicate field — removed for clean content.
- `[SEC]` — security: clean; authored in-world prose, no injection structure, no secrets, no leak (player-facing strings carry no model-directive force).
- `[EDGE]`, `[TEST]`, `[DOC]`, `[TYPE]`, `[SIMPLE]`, `[RULE]` — subagents disabled via settings for this review. Reviewer covered their domains directly: edge (driveless PC + empty-drive path proven in harness; both solo/MP openings carry the seed), test (content is validated-not-tested — loader + validator + harness all green), doc (YAML comments added are accurate; the giverless rationale matches `mint_quest_offer` behavior), type (pydantic `QuestSeed`/`HistoryChapter` schemas accept the content with `extra="forbid"` — validated by the live loader), simplify (removed the redundant `stakes`; remaining content is minimal), rule (SOUL "Crunch in Genre, Flavor in World" + "No Silent Fallbacks" + the world's authored avoid-list all satisfied).

**Rule compliance:** SOUL.md "Crunch in the Genre, Flavor in the World" — stakes/quest authored at WORLD tier (correct); no genre/engine change. "No Silent Fallbacks" — loud-fail seed path preserved; redundant inert field removed. "Diamonds and Coal" / "Yes, And" — the quest is promoted on the player's own action (taking the rope), not forced. World authored avoid-list ("no quest-giver", "no NPC hook", "never explain Sünden") — honored: giverless seed, no `present_npcs`, no proper-noun explanation of the name.

**Devil's Advocate:** Could a driveless PC still hit a blank tab? Only if FRESH-chapter materialization failed to set `active_stakes` — but the harness proves it's set, and `materialize_from_genre_pack` raises `HistoryParseError` loudly on parse failure rather than silently emptying. Could the quest_seed mint twice or leak? `mint_quest_offer` is idempotent (first-writer-wins) and consumes the pending offer. Could the giverless seed confuse the router into fabricating a quest-giver? The router bait surfaces `quest_id`/`title`/`giver=""`; an empty giver gives no NPC role to invent, and the narrator's own `avoid_at_all_costs` reinforces no-giver — the worst case is the router simply waits for the player to act, which is the intended behavior. Could the `anchor: the_dropmouth` dangle? It's a real POI slug in this world's `history.yaml`; even if it didn't resolve, the projection tolerates an anchor with no cohered lore (returns empty, never crashes). Could the new active_stakes prose read as doom-narration and violate the world's tone? It's grave but self-directed and never falsely hopeful — consistent with the existing chapter atmosphere it sits beside. No failure mode found that the diff introduces.

**Handoff:** To SM (Captain Carrot) for finish-story.