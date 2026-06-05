# Story 84-5 Context

## Title
WI-2 Lifecycle-aware scope — dormant quest/trope indexing + active→floor routing; per-type active/dormant predicate (amends ADR-118 §D2)

## Metadata
- **Story ID:** 84-5
- **Type:** story
- **Points:** 5
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** sidequest-server
- **Epic:** 84 — ADR-118 Amendment — Unified Pertinence Scorer & Tiered Forgetting
- **Stack parents (merged):** 84-1, 84-4, 84-2, 84-3

## Problem
ADR-118 Amendment §A2 (DORMANT-ONLY, amends §D2): an **active** quest/trope is *pressure on the
table* — it applies whether or not anyone named it, so it rides the FLOOR (always in turn
context). A **dormant/completed** one is a *note* — looked up only when referenced ("what was
that quest about the smuggler?"), so it is INDEXED and recalled by pertinence. Today the index
holds only `npc|location|faction|relationship`; dormant quests/tropes are NOT recall-able, so a
finished quest the player asks about cannot surface. 84-5 adds the per-type active/dormant
predicate + the dormant projector path.

## Investigation findings (codebase, confirmed this RED phase) — READ THIS FIRST

### THE CRITICAL FINDING: active quests AND active tropes ALREADY reach the narrator prompt
This is the **inverted 84-3 trap** — 84-3 shipped a projector nothing rendered (dead code); here
the risk is the OPPOSITE: routing active quests/tropes through a NEW "active floor → narrator
section" would **DOUBLE-RENDER** what already reaches the prompt. Confirmed:
- **Active tropes** (`status == "progressing"`) already render via
  `trope_tick.select_foreground_tropes(snapshot.active_tropes)` →
  `render_foreground_block`/`render_background_block` → `TurnContext.pending_trope_context`
  (Early zone) + `TurnContext.active_trope_summary` (Valley zone, registered as the
  `active_tropes` section, `orchestrator.py:2283-2293`). This IS the §A2 "active trope rides the
  floor" behavior — already live, via the trope engine, NOT retrieval.
- **Active quests** (the whole `quest_log: dict[str, QuestEntry]`) already reach the prompt via
  `state_summary_json` — `quest_log` is in `_STATE_SUMMARY_KEYS` (`session_helpers.py:225`), so
  every quest (all statuses) is dumped into the `state_summary` Valley section
  (`session_helpers.py:1071`, registered `orchestrator.py`).

**Consequence (the routing decision):** §A2 "active→floor reaches narrator" is ALREADY satisfied
for both types by existing mechanisms. 84-5's net-new work is the **DORMANT→INDEX side** + a
routing PREDICATE whose job is to ensure **only DORMANT quests/tropes are projected into the
EntityStore** (active ones are NOT indexed — they ride their existing floor path and must not be
double-rendered). The "active→floor" AC is satisfied by asserting the EXISTING render still
fires for an active quest/trope AND that the active one is NOT projected into the index.

### Models + status values (verified)
- **`QuestEntry`** (`session.py:437`): `title: str`, `objective: str`, `status: str = "active"`,
  `anchor_id: str | None`. Lives in `snapshot.quest_log: dict[str, QuestEntry]` (keyed by quest
  id). `extra="ignore"`; legacy string statuses coerced in.
  **Predicate:** `status == "completed"` → DORMANT (index); any other status → ACTIVE (floor).
- **`TropeState`** (`session.py:583`): `id: str`, `status: str = "dormant"`, `progress: float`,
  `beats_fired: int`, `fire_cooldown_until`, `last_fired_turn`. Lives in
  `snapshot.active_tropes: list[TropeState]`. Carries only the `id` — name/description live in
  **`TropeDefinition`** (`genre/models/tropes.py:1`: `id`, `name`, `description`), joined via the
  genre pack (`sd.genre_pack.tropes`, keyed by id — same join `session_helpers.py:1124` uses).
  **Predicate:** `status == "progressing"` → ACTIVE (floor); `"dormant"` / `"resolved"` →
  DORMANT (index). The ADR-128 governor (`trope_tuning.py`) caps `progressing` at 3, so the
  active set is bounded by construction.

### EntityType / fail-loud chain (the KNOWN TRAP — hit on 84-3)
`EntityType` currently has `NPC|LOCATION|FACTION|RELATIONSHIP` (`entity_card.py:45-51`). Adding
`QUEST` and `TROPE` each needs the FULL 3-registration or `pertinence.score_card` /
`EntityCard.new` fail loud (`pertinence._applicable_signals` raises on undeclared types;
`EntityCard.new` raises on a missing `_ID_NAMESPACE` entry):
1. `EntityType.QUEST = "quest"` + `_ID_NAMESPACE[QUEST]="quest"`; `EntityType.TROPE = "trope"` +
   `_ID_NAMESPACE[TROPE]="trope"`.
2. `SIGNAL_APPLICABILITY[QUEST] = {mention, recency, sim}` and `[TROPE] = {mention, recency, sim}`
   — **NOT `here`**: a quest/trope is not physically "present" the way an NPC/location is; a
   dormant note surfaces by being NAMED (mention) or TOPICALLY similar (sim), decayed by recency.
3. `retrieve_turn_context._finish` `by_type` buckets for QUEST + TROPE
   (`retrieval_orchestration.py:256-264`), surfaced as `retrieved_quests` / `retrieved_tropes`.

### Sync + retrieval seams to mirror (84-3 RELATIONSHIP pattern)
- `entity_sync.sync_entity_cards` projects cards per type with a `_has_*_to_project` gate +
  `_apply_typed_card(store, card, result, "<type>_count")` (`entity_sync.py:147-240`). 84-5 adds
  quest + trope loops + `quest_count`/`trope_count` on `EntitySyncResult` — **DORMANT-ONLY**
  (the gate is the dormant predicate; an active quest/trope is NOT projected).
- Dispatch `entity_sync.sync_for_turn` emits the counts on the `accretion.entity_sync` span +
  watcher event (mirror `relationship_count`, `entity_sync.py` dispatch).

## §A2 mechanism decision (TEA + Dev)
- **DORMANT → INDEX (net-new):** `project_quest_card(quest_id, quest_entry)` and
  `project_trope_card(trope_state, trope_def)` produce SUMMARY-style cards; `sync_entity_cards`
  projects ONLY dormant ones (predicate gate). They surface in retrieval (`retrieved_quests`/
  `retrieved_tropes`) by mention/sim and render into the narrator prompt via the
  `session_helpers` → `build_narrator_prompt` Valley-section seam (the same seam 84-3 wired for
  relationships) — so a dormant note reached on recall is NOT dead code.
- **ACTIVE → FLOOR (already live — do NOT duplicate):** active quests ride `state_summary`;
  active tropes ride `select_foreground_tropes`. 84-5 must NOT project active quests/tropes into
  the index and must NOT add a second active-render path. The predicate ROUTES: active → leave
  on the existing floor; dormant → index. The active-floor AC asserts the existing render still
  fires AND the active card is absent from the index.

## Acceptance Criteria

> Each AC has failing test coverage written in the RED phase (see Test Coverage).

- **AC-1 — Per-type active/dormant predicate.** `quest_is_dormant(entry) == (status == "completed")`
  and `trope_is_dormant(state) == (status != "progressing")` (i.e. dormant for "dormant"/"resolved",
  active only for "progressing"). Pure, exhaustive over the known statuses. *Tests:*
  `test_quest_completed_is_dormant`, `test_quest_active_is_not_dormant`,
  `test_trope_progressing_is_active`, `test_trope_dormant_and_resolved_are_dormant`.

- **AC-2 — `project_quest_card` summary content, deterministic.** A dormant `QuestEntry` projects
  to a `quest:<id>` `EntityCard` whose content carries title + objective + status; deterministic
  (same entry → byte-identical content/metadata, for 75-6 reproject); never blank (EntityCard
  rejects blank content — a title-less quest still yields non-blank content). *Tests:*
  `test_project_quest_card_content`, `test_quest_card_id_namespace`,
  `test_quest_card_deterministic`, `test_quest_card_not_blank_when_sparse`.

- **AC-3 — `project_trope_card` summary content, deterministic.** A dormant `TropeState` + its
  `TropeDefinition` projects to a `trope:<id>` card carrying name + description + (optionally)
  progress/beats; deterministic; never blank. *Tests:* `test_project_trope_card_content`,
  `test_trope_card_id_namespace`, `test_trope_card_deterministic`,
  `test_trope_card_uses_definition_name`.

- **AC-4 — QUEST + TROPE EntityType 3-registration, NO fail-loud regression.** Both types are in
  `EntityType`, `_ID_NAMESPACE`, AND `SIGNAL_APPLICABILITY`; `score_card` on a quest card and on
  a trope card does NOT raise; `applicable` = `{mention, recency, sim}` (no `here`); a bogus type
  still raises (guard intact). *Tests:* `test_quest_trope_entity_types_registered`,
  `test_quest_trope_in_id_namespace`, `test_quest_trope_in_signal_applicability`,
  `test_score_card_on_quest_does_not_fail_loud`, `test_score_card_on_trope_does_not_fail_loud`,
  `test_quest_trope_signals_exclude_here`, `test_bogus_type_still_fails_loud`.

- **AC-5 — DORMANT-ONLY sync: only dormant quests/tropes are indexed.** `sync_entity_cards`
  projects a `quest:<id>` card for a COMPLETED quest and a `trope:<id>` card for a DORMANT/
  RESOLVED trope, and does NOT project an ACTIVE quest or a PROGRESSING trope into the store
  (the active ones ride their existing floor). `quest_count`/`trope_count` tallies count only the
  projected (dormant) cards. *Tests:* `test_sync_indexes_dormant_quest`,
  `test_sync_indexes_dormant_trope`, `test_sync_does_not_index_active_quest`,
  `test_sync_does_not_index_progressing_trope`, `test_sync_quest_trope_counts`.

- **AC-6 — DORMANT → retrieval: a dormant quest/trope surfaces on mention/sim.**
  `retrieve_turn_context` returns a dormant quest card in `retrieved_quests` (and a dormant trope
  in `retrieved_tropes`) when the player references it; absent → `None` (zero-byte-leak). New
  `retrieved_quests`/`retrieved_tropes` fields exist on `RetrievedEntities`. *Tests:*
  `test_retrieved_quests_trades_fields_exist`, `test_dormant_quest_surfaces_in_retrieval`,
  `test_dormant_trope_surfaces_in_retrieval`, `test_no_dormant_quest_yields_none`.

- **AC-7 — DORMANT → narrator prompt (the render seam — no dead code).** A retrieved dormant
  quest/trope renders through `_build_turn_context` → a `retrieved_quests`/`retrieved_tropes`
  Valley section in the assembled narrator prompt (the 84-3 seam). No card → no section
  (zero-byte-leak). *Tests:* `test_dormant_quest_renders_into_prompt`,
  `test_dormant_trope_renders_into_prompt`, `test_no_quest_section_when_empty`.

- **AC-8 — ACTIVE → FLOOR reaches narrator, NOT double-rendered, NOT indexed.** For an ACTIVE
  quest: it still reaches the prompt via the EXISTING `state_summary` path AND is NOT in the
  index. For a PROGRESSING trope: it still renders via the EXISTING `active_tropes`/foreground
  path AND is NOT in the index — and no `retrieved_tropes` section duplicates it. *Tests:*
  `test_active_quest_reaches_prompt_via_existing_path_not_index`,
  `test_progressing_trope_renders_via_existing_path_not_retrieval`.

- **AC-9 — Trope-governor cap interplay: the active set is bounded.** Because the ADR-128 governor
  caps `progressing` tropes at 3, the active (floor) trope set is ≤3, and everything else is
  dormant → indexed. A snapshot with 3 progressing + N dormant tropes indexes exactly the N
  dormant. *Tests:* `test_active_trope_set_bounded_by_governor_cap`.

- **AC-10 — OTEL: the active/dormant routing decision is observable.** The sync sweep emits
  `quest_count`/`trope_count` (dormant-projected) on the `accretion.entity_sync` span + watcher
  event so the GM panel sees how many notes were indexed vs left on the floor. *Tests:*
  `test_sync_emits_quest_trope_counts_on_span`.

- **AC-11 — WIRING (two e2e paths).** (a) ACTIVE: a snapshot with an active quest drives the live
  `_build_turn_context`/prompt and the quest reaches the narrator via the existing path, with no
  index projection. (b) DORMANT: the live `sync_for_turn` indexes a completed quest, and driving
  `retrieve_turn_context` + the render seam surfaces it in the narrator prompt on mention.
  Behavior + span only — no source grep. *Tests:* `test_e2e_active_quest_to_prompt`,
  `test_e2e_dormant_quest_index_to_prompt`.

- **AC-12 — Quality gate.** All ACs fail before GREEN; tree clean; correct branch; `just
  server-check` green; no fail-loud regression in the 84-1 scorer (fill loop untouched); no
  double-render of active quests/tropes; the routing emits OTEL. **No dead wiring: dormant cards
  reach the narrator (index → retrieve → render); active cards are not re-projected.**

## Test Coverage (RED — failing tests in place)
- `sidequest-server/tests/game/test_lifecycle_predicates.py` — `quest_is_dormant`/`trope_is_dormant`
  pure predicates (AC-1).
- `sidequest-server/tests/game/test_quest_trope_card_projector.py` — `project_quest_card` +
  `project_trope_card` (AC-2, AC-3). Synthetic `QuestEntry`/`TropeState`+`TropeDefinition`.
- `sidequest-server/tests/game/test_quest_trope_entity_type.py` — QUEST+TROPE 3-registration +
  fail-loud guard (AC-4). Run `-n0` if a scorer span fires.
- `sidequest-server/tests/game/test_lifecycle_sync_routing.py` — DORMANT-ONLY sync + counts +
  active-not-indexed + governor cap (AC-5, AC-9). Run `-n0`.
- `sidequest-server/tests/game/test_dormant_retrieval.py` — dormant→retrieval surfaces + new
  fields (AC-6). Run `-n0`.
- `sidequest-server/tests/server/test_lifecycle_render_wiring.py` — dormant→prompt render +
  active→existing-path-not-double-render + the two e2e wiring paths + OTEL (AC-7, AC-8, AC-10,
  AC-11). Run `-n0`.

## Notes for Dev
- **DON'T double-render active quests/tropes.** They already reach the prompt (quests via
  `state_summary` quest_log dump; active tropes via `trope_tick.select_foreground_tropes`). The
  predicate ROUTES — active stays on its existing floor path, only DORMANT gets projected into
  the index. AC-8 pins "active reaches prompt via existing path AND is not indexed."
- **The fail-loud trap (3-registration) hits TWICE** — QUEST and TROPE each need enum +
  `_ID_NAMESPACE` + `SIGNAL_APPLICABILITY`. Land each type's three together. AC-4 canaries both.
- **SIGNAL_APPLICABILITY = `{mention, recency, sim}` for both** (no `here` — a quest/trope is not
  physically present). A dormant note surfaces by mention or topical similarity.
- **Trope card needs the TropeDefinition** for name/description (TropeState carries only `id`).
  Join via `sd.genre_pack.tropes` keyed by id — the same join `session_helpers.py:1124` uses.
  Don't fabricate a name from the id.
- **DORMANT-ONLY projection:** the sync gate is the dormant predicate. A completed quest / a
  resolved trope projects; an active quest / a progressing trope does NOT.
- **Render the dormant card or it's dead** (the 84-3 lesson): `_build_turn_context` must render
  `retrieved_quests`/`retrieved_tropes` into Valley sections via the `render_entity_section` seam,
  with `TurnContext` fields + the orchestrator section-registration loop entries — exactly the
  4-connection pattern 84-3 used for relationships. AC-7/AC-11 pin the full chain.
- **Determinism** (75-6 reproject): stable content ordering, no `set` iteration in content.

---
_Acceptance criteria authored by TEA (Amos Burton) in the RED phase from ADR-118 §A2 (DORMANT-ONLY)
+ §D2 + ADR-128 (trope lifecycle, governor cap) + ADR-137 (quest substrate) + live investigation.
**Load-bearing finding: active quests/tropes ALREADY reach the prompt — 84-5's net-new work is the
DORMANT→INDEX side + a routing predicate that prevents double-rendering the active set.**
Supersedes the generated placeholder._
