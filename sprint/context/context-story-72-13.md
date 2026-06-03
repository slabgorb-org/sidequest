---
parent: context-epic-72.md
workflow: trivial
---

# Story 72-13: hp_depletion presence-stamp — production-path wiring test + AC2 docstring tighten

**Epic:** 72 (NPC Identity Hardening) · **Points:** 2 · **Type:** chore · **Repo:** sidequest-server

## Business Context

This is a coverage-and-docs follow-up to story **72-8** (done, approved —
`sprint/archive/72-8-session.md`). 72-8 stamped `Npc.last_seen_turn` /
`Npc.last_seen_location` on the two combat opponent-presence seams so an NPC the
party is actively fighting reads as "recently seen" even when the narrator
doesn't name them in prose that turn. It shipped with two **confirmed,
non-blocking** Reviewer gaps. This story closes both.

The 72-8 Reviewer findings ARE the spec for 72-13:

1. **Missing production-path wiring test for the hp_depletion seam.** The dial
   path is wired-tested end-to-end via `trigger_encounter`, but the hp_depletion
   seam (`_seed_combat_hp_depletion_to_npcs`) is exercised only by a *unit* test
   (`test_hp_depletion_seam_stamps_presence`) that calls it directly with a
   `types.SimpleNamespace` cdef — bypassing `instantiate_encounter_from_trigger`
   and the real `ConfrontationDef` accessors. The win_condition dispatch gate
   (~`encounter_lifecycle.py:1173`, threading `acting_character_name=player_name`)
   is verified only by reading the diff. This violates "Every Test Suite Needs a
   Wiring Test" for the hp_depletion path.

2. **AC2 docstring overstates coverage.** The module docstring in
   `test_72_8_presence_last_seen_stamp.py` says AC2 is "guarded by"
   `test_cite_known_npc_updates_last_seen_on_npc`, but that test only exercises
   the prose path's *truthy-location* branch — not the no-location branch.

## Technical Guardrails

**This is a test-and-docstring story. Do NOT change production presence-stamp
behavior.** The production code (`encounter_lifecycle.py`) is already correct per
72-8; this story proves the hp_depletion path is wired through the real entry
point and corrects an overstated docstring.

**Where the work goes:**
`sidequest-server/tests/server/dispatch/test_72_8_presence_last_seen_stamp.py`

**Production code under test (read-only reference):**
- `sidequest/server/dispatch/encounter_lifecycle.py`
  - `_seed_combat_hp_depletion_to_npcs` — the hp_depletion opponent-presence seam.
  - win_condition dispatch gate (~line 1173) that threads
    `acting_character_name=player_name`.
  - `instantiate_encounter_from_trigger` — the real production entry point the
    new test must route through (NOT a direct seam call).
  - `_stamp_encounter_presence` — the helper that writes `last_seen_turn` (always)
    and `last_seen_location` (only when truthy).

**Exemplar to model the e2e test on:**
`sidequest-server/tests/server/test_space_opera_swn_combat_e2e.py` — shows the
`win_condition: hp_depletion` pack wiring, `SIDEQUEST_GENRE_PACKS` setup, and the
`trigger_encounter` → `instantiate_encounter_from_trigger` path. Match its fixture
discipline (real pack or the same synthetic-pack approach it uses); do not invent
a second genre-pack loading path (No Silent Fallbacks).

## Acceptance Criteria

- **AC1 — hp_depletion production-path wiring test.** A new test drives a
  `win_condition: hp_depletion` encounter through `trigger_encounter` /
  `instantiate_encounter_from_trigger` (NOT a direct `_seed_combat_hp_depletion_to_npcs`
  call) and asserts the opponent `Npc` has `last_seen_turn` and
  `last_seen_location` stamped. Assert behavior (`Npc` field state and/or the
  `npc.edge_published` OTEL span attributes), never source-text greps.
- **AC2 — created-branch coverage.** The wiring test (or a sibling) covers the
  CREATE branch: the opponent has **no backing `Npc`** in `snapshot.npcs` before
  instantiation, and after the production path runs the freshly-created opponent
  `Npc` carries the stamped recency fields.
- **AC3 — AC2 docstring tightened.** The module docstring's AC2 "guarded by"
  claim is corrected to accurately describe what
  `test_cite_known_npc_updates_last_seen_on_npc` covers (truthy-location prose
  branch only) — or the no-location prose-path branch is added and the claim made
  true. State which approach was taken in the Dev assessment.
- **AC4 — no regressions.** All existing tests in
  `test_72_8_presence_last_seen_stamp.py` (7) plus the regression set around the
  touched seams stay green. `ruff check` + `ruff format --check` clean.

## Out of Scope

- Any change to production presence-stamp behavior in `encounter_lifecycle.py`.
- The deferred opposed_check / social-opponent presence-stamp (72-8 Reviewer
  finding #2 — separate follow-up, not this story).
- 72-6 eviction / LRU prune.
- The brittle source-text wiring test flagged in 72-8's Dev findings
  (`test_npc_registry_combat_stats.py:297-307`) — note it if touched, but it is
  not in this story's scope.

## Definition of Done

- New production-path wiring test (incl. created-branch) green; AC2 docstring
  accurate; full touched-seam regression set green; ruff clean; PR merged to
  `develop` in sidequest-server.
