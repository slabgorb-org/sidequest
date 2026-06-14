---
story_id: "117-2"
jira_key: ""
epic: "117"
workflow: "architecture"
---
# Story 117-2: Design + ADR: quest-seed authoring contract

## Story Details
- **ID:** 117-2
- **Jira Key:** (none)
- **Workflow:** architecture
- **Type:** design
- **Points:** 3
- **Priority:** p1
- **Repos:** server, content
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** architecture
**Phase:** setup
**Phase Started:** 2026-06-14T23:29:30Z
**Branch Strategy:** trunk-based (branching skipped — work happens on the default branch)

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T23:29:30Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Architect (design)
- **Gap** (non-blocking): `Opening` model (`sidequest/genre/models/narrative.py:209`) has `extra="allow"` at top level but `OpeningTone` (`:114`) is `extra="forbid"` — so `quest_seed` must be declared as a typed field on the model, not free-form. 117-3 adds a `QuestSeed` sub-model and a `quest_seed: QuestSeed | None` field on `Opening` (and optionally on the seed_trope model). *Found by Architect during design.*
- **Gap** (non-blocking): the seed must be stashed where the per-turn pipeline can read it. `_populate_opening_directive_on_chargen_complete` (`opening_helpers.py:31`) stashes `opening_seed`/`opening_directive` on `_SessionData`; 117-3 must also stash the resolved `quest_seed` onto the snapshot (proposed: `snapshot.pending_quest_offers: dict[str, QuestSeed]`) so it survives resume (the directive does not — it is consumed once). *Found by Architect during design.*
- **Gap** (non-blocking): the IntentRouter system prompt (`intent_router.py:148-273`) hard-enumerates subsystem keys; adding `quest_offer` requires both a prompt-block addition AND a registered handler in `subsystems/__init__.py` AND an engagement witness in `dispatch_engagement_watcher.py:_WITNESSES`. Three connections, per the no-half-wired rule. *Found by Architect during design.*
- **Improvement** (non-blocking): the existing `detect_unminted_objective` keyword watcher (`dispatch_engagement_watcher.py:591`, 14-phrase `_UNMINTED_OBJECTIVE_MARKERS`) becomes redundant for *seeded* offers once `quest_offer` mints deterministically — but it should be RETAINED as the lie-detector for *un-seeded* improvised objectives (the narrator inventing a job with no authored seed). 117-4 owns retiring/retuning it; do not delete in 117-3. *Found by Architect during design.*

## Architect Assessment

**Decision:** ADR-146 "Quest-Seed Authoring Contract" + design spec (commit `acd33a7` on main, NOT pushed). Authored hooks (`Opening.tone.quest_seed` / seed_trope) carry a machine-readable `QuestSeed`; the Intent Router (ADR-113) classifies the acceptance turn via a new `quest_offer` subsystem; a deterministic handler mints a `QuestEntry` from the seed — no narrator tool-call. New `quest.seeded` OTEL span (source="authored_seed") proves the mint.

**Rationale:** Tabletop-First — a DM who hands you a job has handed you a quest. The acceptance trigger rides the router's objective-reality classification against *named structured offers* (`pending_quest_offers` surfaced in `<game_state>`), NOT a keyword list (the `detect_unminted_objective` 14-phrase anti-pattern). Reuses `QuestEntry`/`quest_log`, the dispatch bank's confidence gate, and the typed `SPAN_ROUTES` feed — no new engine.

**Alternatives Considered:**
- Prompt the narrator harder: rejected — repro IS the narrator not minting despite a clear tool description; makes minting likelier, never deterministic.
- Auto-mint seed at chargen: rejected — un-engaged hook is bait (ADR-014); mint on acceptance, not on author.
- Keyword/regex acceptance detector: rejected — the documented Zork verb-set anti-pattern 117-4 retires.
- New `accept_quest` narrator tool: rejected — same failure one layer up (still narrator's discretion).

**Implementation Guidance (117-3):** (1) `QuestSeed` sub-model + typed `quest_seed` field on `OpeningTone` (extra="forbid" — must be typed) and seed-trope model; (2) `pending_quest_offers: dict[str,QuestSeed]` on `GameSnapshot`, persisted/resume-safe, stashed at `chargen_mixin.py:1399` beside `seed_quest_spine`; (3) `quest_offer` subsystem — prompt block + `run_quest_offer_dispatch` handler (share the 32 cardinality cap, idempotent, fill-don't-clobber stakes) + `_check_quest_offer_engaged` witness; (4) `quest.seeded` span mirroring `quest_created_span`; (5) perseus_cloud floor-boss seed in openings.yaml. OTEL-driven wiring test, not source-grep.

**Handoff:** To 117-3 (implement). 117-4 retunes the keyword watcher to the un-seeded backstop. 117-5 coheres lore under the minted quest.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
