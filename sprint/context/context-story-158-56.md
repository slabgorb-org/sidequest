# Story 158-56 Context

## Title
Mutation picker in the confrontation overlay — client sends mutation_id on the mutation beat commit (158-54 UI half)

## Metadata
- **Story ID:** 158-56
- **Type:** chore/feature
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repos:** ui
- **Epic:** 158 — Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Problem
Story 158-54 (server, completed) wired the AWN mutation use path into the primary dice-roll combat system. The server now expects a `DiceThrowPayload.mutation_id` field naming which owned mutation the player is using on a `mutation_resolution` beat — the same contract as the spell picker (story 102-2).

Currently, the confrontation overlay has no UI mutation picker, so:
1. A live client cannot send `mutation_id` on a mutation beat commit
2. A mutation-beat commit from a real player raises a `DiceDispatchError` (missing required field) or silently resolves as a generic stat throw

The UI half must render a mutation picker widget in the confrontation overlay when a `mutation_resolution` beat is active, and ride the chosen mutation ID on the `DICE_THROW` payload.

## SCOPE CHANGE (TEA RED, 2026-07-07) — ui → server,ui

The original story assumed this was `ui`-only ("list the PC's owned positives
(`mutation_state.positive_ids`)"). **That premise is false:** the owned-mutation
list is NOT projected to the client today. The server projects a *derived*
`spellcasting` economy block onto the CONFRONTATION payload for the spell picker
(messages.py:1029) — raw `magic_state`/`mutation_state` never leave the server.
There is **no mutation twin** of that projection, and the UI snapshot has no
`mutation_state` at all. A `ui`-only picker would render empty (half-wired).
User authorized expanding to **server + ui** (one story, end-to-end). See TEA
Delivery Findings.

## Wire Contract (corrected against 158-54 + the real projection code)
- **Payload field:** `DiceThrowPayload.mutation_id: str | None` — names which owned mutation to use (EXISTS server-side, 158-54; must be ADDED to the UI `DiceThrowPayload` type + threaded through the commit chain).
- **Precedent:** the 102-2 **spell picker**, entirely in `sidequest-ui/src/components/ConfrontationOverlay.tsx` (`SpellPicker`, `CAST_SPELL_BEAT_ID`, `handleSpellChoose`) + server `build_confrontation_payload` `spellcasting` projection. Mirror it; do NOT author a parallel picker framework. (`CavernActionPanel` is the D&D action bar, NOT the confrontation commit path — ignore it.)
- **Beat detection:** the generic mutation beat is marked `mutation_resolution: true` on the beat model (`genre/models/rules.py:201`, real content: `mutant_wasteland` "Wasteland Brawl" beat `id: mutant_ability`), and that marker IS already projected to the client (beats are `model_dump(mode="json")`'d at `confrontation.py:323`). Detect via `beat.mutation_resolution === true` — **NOT** a `beat_resolution_type` string (that field does not exist) and **NOT** a hardcoded beat id.
- **Mutation list source (server projection — the new work):** a `mutation_economy` block on `ConfrontationPayload`, the `spellcasting` twin. Derived in `build_confrontation_payload` / `_frame_for` (confrontation.py:724) from `snapshot.mutation_state.characters[recipient_actor].positive_ids` joined to the pack's `MutationCatalog` (`pack.mutations`) for display names + strain_cost. Shape: `{"owned": [{"id","name","strain_cost"}, ...]}`. `None` for non-mutants / non-AWN packs — never a fabricated empty economy. Scoped to the recipient (162-10 decoy lesson).
- **Server dispatch (already done, 158-54):** a `mutation_resolution` commit with no `mutation_id` → loud `DiceDispatchError`; the spine is `awn.mutation.used`/`.refused`.

## Technical Approach

### Scope
- Render a mutation picker (dropdown/list) in the confrontation overlay when a `mutation_resolution` beat is the active beat
- Extract the player character's owned mutations from snapshot (`mutation_state.positive_ids`)
- Send `mutation_id` on `DICE_THROW` payload when the player commits a mutation beat
- Pattern the implementation after the existing spell picker (102-2) for consistency

### Acceptance Criteria (corrected + server AC added — pinned by the RED suite)

**Server (`build_confrontation_payload` + `ConfrontationPayload`) — new:**
- **AC0 — mutation_economy projection:** the CONFRONTATION payload carries a `mutation_economy` block `{owned:[{id,name,strain_cost}]}` for a recipient who owns positive mutations, derived from `snapshot.mutation_state` + `pack.mutations`; `None` for non-mutants / no catalog; scoped to the recipient (no decoy leak); accepted by `ConfrontationPayload` (extra="forbid"). *(Pinned by `test_confrontation_payload_mutation_economy_158_56.py`, 5 tests.)*

**UI (`ConfrontationOverlay` + `App`/`GameBoard` + `payloads.ts`):**
1. **Picker visibility:** when the active beat carries `mutation_resolution === true` AND `data.mutation_economy` is present, clicking it opens a picker (`data-testid="mutation-picker"`) instead of committing — detection by the boolean marker, not `beat_resolution_type`, not a hardcoded id.
2. **Mutation list:** the picker lists `data.mutation_economy.owned` by `data-mutation-id`, each showing its name and a machine-readable `data-strain-cost` (Sebastien/Jade player-visible math — the `casts_remaining` analog).
3. **Mutation id on commit:** choosing a mutation commits with the id in its own slot: overlay `onBeatSelect(beatId, spellId?, mutationId?)` → `("mutant_ability", undefined, "structure/iron_hide")`; the id rides `DICE_THROW.mutation_id` (add `mutation_id?: string` to the UI `DiceThrowPayload`; latch a `pendingMutationIdRef` + conditional-spread, mirroring `spell_id` at App.tsx:1973). The typed `player_action` still rides alongside (Zork guardrail).
4. **Reject unmutated commit:** a `mutation_resolution` beat with no `mutation_economy` must NOT bare-commit `onBeatSelect("mutant_ability")` (No Silent Fallbacks — the server would raise the missing-`mutation_id` `DiceDispatchError`). Defer/disable.
5. **Regression:** non-mutation beats commit immediately (no picker, no mutation_id); the 102-2 spell picker (`cast_spell`/`spell_id`) is unaffected.
6. **Wiring test:** a real `DICE_THROW` with a valid `mutation_id` lands on the wire through App's production commit chain (GameBoard prop-trap harness). *(Pinned by `mutation-throw-wiring-158-56.test.tsx`.)*

**Arity note (deviation):** spell and mutation picks are mutually exclusive, so `mutationId` gets its own positional slot (overlay `(beatId, spellId?, mutationId?)`; GameBoard/App `(beatId, playerAction?, spellId?, mutationId?)`) — the direct positional mirror of how `spell_id` was added, rather than refactoring the cast path into an options object.

## Related Context
- **158-54 server session:** `/Users/slabgorb/Projects/oq-1/sprint/archive/158-54-session.md` — documents the dice-path mutation contract and player-visible beat markers
- **102-2 spell picker:** refer to spell-picker implementation for the UI pattern (may be in CavernActionPanel or a subcomponent)
- **Snapshot contract:** `GameState.character.mutation_state` carries the owned mutation IDs; resolve each ID to a mutation definition in the genre pack (similar to spell resolution)

---
_Generated by `pf context create story 158-56` for setup phase._
