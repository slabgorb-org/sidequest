---
parent: context-epic-85.md
workflow: tdd
---

# Story 85-2: Location surface — pick ONE source of truth for where-am-I (header vs Location tab) — design-first

## Business Context

"Where am I?" is the most basic question a player asks the screen, and right now SideQuest
answers it **twice, with two different answers.** The running header says one thing (a free-text
scene title like *"The Glenross Pub"*), the Location dockview tab says another (the region-level
authored description), and during an intra-region move they visibly disagree — the header
updates, the tab lags. Playtest finding **L105 a/b** (2026-06-04) caught it.

This is not a styling bug; it's a **single-source-of-truth** problem, so the story is
**design-first**: the load-bearing deliverable is a *decision* — which binding is authoritative —
recorded before any implementation. It pays back **Living World** legibility (the world's
geography must read consistently, not contradict itself) and the *Tabletop First, Then Better*
principle that persistent visual state should be trustworthy. It is **decoupled from the
confrontation thread** (85-1/85-3) — same epic, unrelated surface.

## Technical Guardrails

The two bindings, pinned to code:

**Header (free-text scene title):**
- `sidequest-ui/src/hooks/useRunningHeader.ts:20-43` — reads
  `CharacterSummary.current_location` for the current player; **falls back** to the most recent
  `CHAPTER_MARKER.location` from the message stream.
- Type: `current_location: string` — `sidequest-ui/src/types/party.ts:21`.
- Server origin: `sidequest-server/sidequest/server/views.py:442-455` —
  `_resolve_location_display(genre_pack, world_slug, snapshot.party_location(perspective=...))`
  turns a raw room/region id into a display string.
- Emit cadence: rides **PARTY_STATUS**, broadcast **every turn at turn_end**
  (`websocket_session_handler.py:2230-2251`).

**Location tab (region-level payload):**
- `sidequest-ui/src/components/LocationPanel.tsx:41-184` consumes `LocationDescriptionPayload`;
  wrapped by `GameBoard/widgets/LocationWidget.tsx`.
- Type/shape: `sidequest-ui/src/types/payloads.ts:775-793` — `region_id`, `region_name`
  (authored display name), `prose`, `terrain`, `entities[]`, `overlays[]`.
- Server origin: `sidequest-server/sidequest/server/websocket_handlers/map_emit.py:347-622` —
  two source paths (per-room YAML via `load_room_payload`; cartography region fallback).
- Emit cadence: **LOCATION_DESCRIPTION** fires **only when `current_room`/room_id changes**
  (`websocket_session_handler.py:2037-2040`; gate at `map_emit.py:~388`), plus chargen startup
  (`chargen_mixin.py:986-990`) and resume (`room_id_override`).

**The divergence, exactly:** on an intra-region POI move, `snapshot.party_location()` changes →
`current_location` refreshes on the next PARTY_STATUS (every turn) → **header updates
immediately.** But the room_id may not change → `_maybe_emit_location_description` does **not**
re-fire → **the Location tab keeps the stale region.** Two cadences, two triggers, one truth
needed.

**Relevant prior art:** ADR-109 (Persistent Location Descriptions + Mechanical Manifest) owns the
LocationDescription surface; #648 (`discovered_regions` pollution) is the sibling map-state fix
already merged. Read ADR-109 before deciding — it frames the payload as the persistent,
authored location record.

**What NOT to do:**
- Do not "fix" this by making both emitters fire more often and hoping they agree — that's two
  sources of truth running faster, not one. Pick one authority; derive the other from it.
- Do not touch the confrontation panel (85-1/85-3) or map/`discovered_regions` mechanics.
- Do not silently fall back between the two bindings in the client — that masks the very
  divergence this story exists to kill (No Silent Fallbacks).

## Scope Boundaries

**In scope:**
- **The decision (gating deliverable):** record, in a short design note or ADR addendum, which
  surface is the single source of truth for "where am I," and how the other derives from it. Two
  candidate resolutions to weigh (do not pre-commit here — that's the design phase's job):
  1. **Payload-authoritative.** `LocationDescriptionPayload` is the truth; the header *derives*
     its label from the payload's `region_name` rather than the free-text `current_location`.
     Requires LOCATION_DESCRIPTION to re-emit (or the header to re-read) on any move the header
     would reflect — closing the cadence gap.
  2. **Header-authoritative.** `current_location` (free-text scene title) is the truth; the
     Location tab updates its heading to match on every move, with the authored `prose` as
     sub-detail. Cheaper to wire but demotes the structured payload to flavor.
- Implement the chosen resolution so header and Location tab **agree on screen at all times**,
  including across an intra-region POI move.
- A regression test that reproduces the divergence (move within a region) and asserts agreement.

**Out of scope:**
- The confrontation panel work (85-1 done, 85-3 proposed).
- Reworking the LocationDescription content model, the map/cartography system, or
  `discovered_regions` (that was #648).
- New geography, POI authoring, or content changes — this is a binding/plumbing decision.

## AC Context

Because this is design-first, AC-1 is the decision itself; the rest follow from it. Exact AC
wording is the design phase's to finalize once the source-of-truth is chosen — the items below
are the testable shape.

1. **Source-of-truth decided and recorded.** Pass = a design note / ADR addendum names the single
   authoritative binding (payload-authoritative or header-authoritative) and specifies how the
   non-authoritative surface derives from it. This must exist before implementation ACs are
   testable.
   - Test approach: a doc/lint check that the design artifact exists and names the chosen
     authority; reviewers confirm the implementation matches the recorded decision (no drift).

2. **Header and Location tab agree after an intra-region move.** Pass = after a move that changes
   `party_location()` but not the region/room id, the header label and the Location tab heading
   show the **same** place.
   - Edge cases: intra-region POI move (the original defect); cross-region move (both already
     update — must stay agreeing); session resume (`room_id_override`); chargen startup; the
     header fallback-to-`CHAPTER_MARKER` path must also obey the chosen authority.
   - Test approach (UI): drive a fixture through an intra-region move and assert the
     `useRunningHeader` output and the `LocationPanel` heading resolve to the same value; extend
     `useRunningHeader.test.tsx` and `GameBoard/__tests__/GameBoard-location-tab.test.tsx`.

3. **The chosen authority re-propagates on the moves that previously diverged.** Pass = the
   emit/derive path fires (or is read) on the intra-region case, with no stale frame.
   - Test approach (server, if payload-authoritative): extend
     `tests/server/test_location_description_emit.py` to assert LOCATION_DESCRIPTION re-emits (or
     that the header derives from the payload) on an intra-region move; `..._resume.py` for the
     resume case.

4. **No silent fallback between bindings.** Pass = the client does not quietly substitute one
   binding for the other to paper over a missing update; the non-authoritative surface is an
   explicit derivation of the authority.
   - Test approach: assert the derivation path is the only source for the secondary surface (no
     dual-read with a quiet `||` fallback masking divergence).

## Assumptions

- Intra-region POI moves that change `party_location()` without changing room_id are a real,
  reachable state in at least one live world (the playtest hit it in cartography-mode play). If
  the design phase finds room_id *always* changes on a POI move, the fix narrows to aligning the
  two display strings rather than adding an emit.
- `region_name` on `LocationDescriptionPayload` is a suitable header label if the payload-
  authoritative path is chosen (it is the authored display name; `views.py`'s
  `_resolve_location_display` already produces a comparable string today).
- ADR-109 remains the governing ADR for the LocationDescription surface; this story refines its
  emit/derivation contract rather than replacing it.

## Interaction Patterns

- The header is **always visible**; the Location tab is **one dockview panel among several** and
  may not be focused. The authority decision must hold whether or not the player has the Location
  tab open — the header can never be the only correct surface while a closed tab silently rots.
- "Where am I" should read identically the instant a move resolves: same place-name in the
  header and (when opened) at the top of the Location tab, with the tab adding authored `prose`
  as the deeper layer (Diamonds and Coal: header = the name, tab = the detail).

## Visual Constraints

- Reuse the existing header and `LocationPanel` layouts — this is a *binding* change, not a
  visual redesign. The header keeps its compact single-line label; the Location tab keeps its
  `region_name` heading + `prose` body.
- If payload-authoritative: the header label swaps its data source (`current_location` →
  derived-from-payload `region_name`) without changing its visual slot.
