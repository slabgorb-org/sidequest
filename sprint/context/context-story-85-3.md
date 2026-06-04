---
parent: context-epic-85.md
workflow: tdd
---

# Story 85-3: Confrontation mode — spatial promotion to a dockview panel (opponent portrait + stakes + Guitar-Solo party action)

## Business Context

A confrontation is the **drama peak** of a scene — the chase, the trial, the duel — and SOUL's
*Cost Scales with Drama* says the highest-drama moment should command the **most** screen. Today
it gets the least: a thin bottom strip beneath an empty board. 85-1 made that strip legible and
well-spaced; **85-3 is Tier B — the real answer to "use space well"**: promote the confrontation
into a focused **dockview panel** that claims the board canvas while an encounter is active.

This is the story where three SOUL principles finally get paid in full inside the encounter:
**Cost Scales with Drama** (the peak moment gets the canvas), **Diamonds and Coal** (an opponent
**portrait** + **stakes line** give the dial a face and legible stakes; ADR-116 — a confrontation
requires an *Other*), and above all **The Guitar Solo** — a *"Meanwhile at the table"* row puts
the non-soloing players' concurrent verbs in the reclaimed space, so one player's spotlight never
becomes the rest of the table watching a screen they can't touch. The crunch players
(Sebastien, Jade) still get every Tier A win (scoreboard dial, anchored die, beat ledger) — now
with room to be excellent rather than merely un-broken.

It builds atop **85-1** (Tier A polish, done). It carries a **confirmed server dependency** and a
**gating design decision** that must both be resolved before UI code.

## Technical Guardrails

**GATING DECISION (operator/Architect — before any code).** Does confrontation mode **SPLIT**
with the narration panel (prose left, confrontation right — keeps the soloist reachable and the
table reading along; the Duchess's recommendation, `docs/design/confrontation-space-usage.md:147-152`)
or **TAKE OVER** the board full-screen (most cinematic, hides running prose)? This choice gates
panel sizing, focus behavior, and what the other dockview panels do while a confrontation is
live. Record it (ADR addendum or design note) before red.

**CONFIRMED server dependency — opponent portrait + stakes are NOT on the payload today.** Both
explorers verified this on client *and* server:
- `ConfrontationPayload` (server) — `sidequest-server/sidequest/protocol/messages.py:1270-1341` —
  carries `actors`, dials, beats, hp, beat-impacts, initiative/table_state. **No portrait, no
  stakes.**
- `EncounterActor` — `sidequest-server/sidequest/game/encounter.py:~44` — has `name, role, side,
  withdrawn, per_actor_state`. **No `portrait_url`.**
- `ConfrontationPayload`/`ConfrontationData` (client) — `sidequest-ui/src/types/payloads.ts:109-156,187-193`
  — also lack portrait/stakes (the loose interface has a `[key: string]: unknown` catch-all, so
  new fields are wire-compatible, but the typed consumer surface must be extended).

The infrastructure to *fill* those fields already exists — wire it, don't reinvent (Don't
Reinvent):
- **Portrait:** `sidequest-server/sidequest/server/emitters.py` `_resolve_npc_portrait_url()`
  already resolves a world-scoped NPC portrait from `portrait_manifest.yaml` (used today for
  scrapbook NPC refs, `messages.py:248-259`). Add `portrait_url` to `EncounterActor` and resolve
  it inside `build_confrontation_payload()`.
- **Stakes:** the concept *exists* — `active_stakes: str` lives on `GameSnapshot`
  (`sidequest-server/sidequest/game/session.py`), set by the `set_stakes` narrator tool
  (`sidequest-server/sidequest/agents/tools/set_stakes.py`; `protocol/models.py active_stakes`).
  It is simply **not threaded onto the CONFRONTATION payload** — add a `stakes` field and populate
  it from `snapshot.active_stakes` in the build function.

**Dockview pattern is READY — reuse it (Don't Reinvent):**
- Registration: `sidequest-ui/src/components/GameBoard/GameBoard.tsx:636-694` (`onDockviewReady`,
  `api.addPanel`); dynamic data-gated panels added/removed in a `useEffect` (`GameBoard.tsx:704-739`)
  anchored to the `character` panel; panel ids from `widgetRegistry.ts:16-157`.
- Character / Inventory / Map already follow this exact pattern — confrontation mode is a new
  `WidgetId` + registration + an "encounter active" add/remove gate.

**Current mount (what you are replacing/promoting):**
- `ConfrontationOverlay` mounts as a strip in `GameBoard.tsx:542-553`, rendered at `:579` between
  the dockview workspace (`:809`) and the InputBar (`:598`). Visibility gates on
  `confrontationData != null` (set in `App.tsx:~1099` on the CONFRONTATION message). That null-gate
  is the natural "encounter active" signal for auto-focusing the new panel.

**"Meanwhile at the table" needs NO new data** — it reuses peer-action/seat data already broadcast
(`ACTION_REVEAL`); pure UI.

**What NOT to touch:**
- Confrontation **mechanics** (dice → dial → tag-fire, stat/kind/DC) — sound and verified (#647).
  This is spatial presentation + two additive payload fields, not a rules change.
- The Tier A internals 85-1 just landed — the scoreboard dial, `auto-fit` grid, anchored die,
  caption wrap, beat ledger move *into* the new panel; don't re-solve them.
- The location surface (85-2) — unrelated.

## Scope Boundaries

**In scope:**
- **Gating decision recorded:** SPLIT vs TAKE-OVER, with panel-focus/sizing consequences, written
  down before implementation.
- **Server half (confirmed needed):**
  - Add `portrait_url` to `EncounterActor`; resolve via `_resolve_npc_portrait_url()` inside
    `build_confrontation_payload()`.
  - Add `stakes` to `ConfrontationPayload`; populate from `snapshot.active_stakes`.
  - OTEL: emit a watcher event when the confrontation payload is built with portrait/stakes, so
    the GM panel can confirm the fields are populated (not improvised) — per the OTEL principle.
- **Client half:**
  - A new dockview **Confrontation panel** (`WidgetId` + registration), auto-focused while
    `confrontationData != null`, dismissed on resolution — following the existing add/remove gate.
  - Opponent **portrait + name + their last beat** on the THEM side; **stakes line** up top.
  - A **"Meanwhile at the table"** row of the non-soloing players' concurrent verbs (from
    `ACTION_REVEAL`); collapses to nothing in solo play.
  - The Tier A surfaces (scoreboard dial, stretched beats, anchored die, beat ledger) rehomed into
    the panel's 2-D space.
- A wiring test proving the panel mounts/auto-focuses on CONFRONTATION and unmounts on resolution.

**Out of scope:**
- Re-deriving Tier A legibility (85-1, done).
- Changing confrontation mechanics, dial math, or beat resolution.
- The location surface (85-2).
- New portrait *generation* — this reuses existing `portrait_manifest.yaml` art; if an opponent
  has no manifest portrait, the panel degrades gracefully (name-only THEM side), it does not block.

## AC Context

AC-1 is the gating decision; the payload fields and the panel follow it.

1. **SPLIT-vs-TAKEOVER decided and recorded.** Pass = a design note/ADR addendum states whether
   confrontation mode splits with narration or takes over, and what the other dockview panels do
   while active. Implementation must match the recorded choice.
   - Test approach: doc check that the artifact exists and names the choice; reviewer confirms the
     panel layout matches it.

2. **`portrait_url` on the confrontation payload (server).** Pass = `build_confrontation_payload()`
   resolves and includes each opponent actor's `portrait_url` via `_resolve_npc_portrait_url()`.
   - Edge cases: opponent with a manifest portrait (URL present); opponent with none (field
     absent/empty — must not error, panel degrades to name-only); multi-actor THEM side.
   - Test approach (server): build a confrontation payload with a fixture opponent that has a
     manifest portrait and assert `actors[i].portrait_url` is populated; assert a no-portrait
     opponent yields an empty/absent field without raising. Add a wiring assertion that the field
     reaches the emitted CONFRONTATION message.

3. **`stakes` on the confrontation payload (server).** Pass = the payload carries
   `snapshot.active_stakes` as `stakes`.
   - Edge cases: stakes set via `set_stakes` (string present); no stakes set (empty string, not
     null/error); stakes changing mid-confrontation re-propagate.
   - Test approach (server): set `active_stakes` on a snapshot, build the payload, assert
     `stakes` matches; assert empty-stakes default is a clean empty string.

4. **Confrontation dockview panel mounts + auto-focuses while active.** Pass = on a CONFRONTATION
   message the Confrontation panel is added to the dockview and focused; on resolution it is
   removed.
   - Edge cases: encounter starts (panel appears + focuses); resolves (panel removed, focus
     returns); encounter starting while another panel is focused; rapid start→resolve.
   - Test approach (UI): drive the CONFRONTATION → resolution lifecycle and assert the panel id is
     registered/focused then removed; extend the confrontation-wiring suite
     (`src/__tests__/confrontation-wiring.test.tsx`).

5. **Opponent portrait + name + last beat render on the THEM side; stakes line renders up top.**
   Pass = given a payload with `portrait_url` + `stakes`, the panel shows the portrait, opponent
   name, their last beat, and the stakes; given no portrait, it shows name-only without breaking.
   - Test approach (UI): render with a portrait+stakes fixture and assert the nodes; render with a
     no-portrait fixture and assert graceful degradation.

6. **"Meanwhile at the table" row shows peers' concurrent verbs; collapses in solo play.** Pass =
   with multiple seated players the row lists their `ACTION_REVEAL` verbs; with one player it
   renders nothing (no empty husk).
   - Edge cases: 0 peers (collapsed), 1 peer, many peers; a peer with no action yet.
   - Test approach (UI): render multi-seat and solo fixtures; assert presence/absence of the row
     and its entries.

7. **SPLIT/TAKEOVER layout matches the decision; narration reachability honored.** Pass = if
   SPLIT, the narration prose remains visible alongside the confrontation (Guitar Solo: soloist
   reachable); if TAKEOVER, the panel claims the canvas per the recorded choice.
   - Test approach (UI): assert the panel's position/sizing relationship to the narration panel
     matches AC-1's recorded decision.

## Assumptions

- The split-vs-takeover decision lands as **SPLIT** unless the operator/Architect overrides — it
  is the Duchess's recommendation and the literal embodiment of *keep the band playing*. The
  context does not pre-commit it; AC-1 makes it explicit either way.
- `_resolve_npc_portrait_url()` is reusable for opponent actors as-is (it resolves by NPC name
  against the world's `portrait_manifest.yaml`); confrontation opponents are named NPCs, so the
  same lookup applies. If an opponent is an unnamed/abstract foe (e.g. "the storm"), the
  no-portrait degradation path (AC-2/AC-5) covers it.
- `ACTION_REVEAL` already carries enough per-peer verb text for the "Meanwhile" row without a new
  payload — confirmed reuse, no server change for the Guitar-Solo strip.
- The two additive payload fields (`portrait_url`, `stakes`) are backward-compatible: the client's
  loose `ConfrontationPayload` has a catch-all, and the strict `ConfrontationData` type is being
  extended in this story, so older clients ignore them and the new client reads them.

## Interaction Patterns

- **Confrontation is a mode.** Entering it should *re-focus the workspace* on the encounter (auto-
  focus the panel), not merely reveal a strip; exiting returns focus to the prior layout.
- The beat → roll → result → dial → ledger chain from 85-1 stays one continuous spatial flow,
  now with room: opponent on the right (with a face), your beats stretching across the center,
  stakes overhead, the table's concurrent action along the bottom.
- In **SPLIT** mode the running narration stays readable beside the confrontation so the soloist
  is reachable and the table reads along; in solo play the "Meanwhile" row simply isn't there.

## Accessibility Requirements

- Carry forward every 85-1 a11y guarantee into the panel: dial numerals/title at WCAG AA 4.5:1,
  beat tiles keyboard-reachable in DOM order with a visible focus ring (sole commit path),
  `aria-live` hint on locked-Enter, distinct role/label on the resolution beat, and
  `prefers-reduced-motion` on die/dial animation.
- The new opponent portrait needs alt text (opponent name); the stakes line must be a real text
  node (screen-reader legible), not a background image.
- Auto-focusing the panel must move focus predictably (and reversibly on resolution) so keyboard
  users are not stranded.

## Visual Constraints

- Reuse the **existing dockview** look and the panel chrome of Character/Inventory/Map — this is a
  new panel in the established system, not a bespoke overlay.
- Rehome the Tier A elements (tug-of-war scoreboard dial, `auto-fit` beat grid with
  `minmax(150px, 1fr)`, anchored die, beat-history ledger) into the panel's 2-D space; do not
  restyle them — 85-1 already settled their look.
- The reference wireframe is `docs/design/confrontation-space-usage.md:116-133` (Tier B layout):
  opponent portrait right, stakes top, beats center, "Meanwhile at the table" bottom, die under
  the committed tile.
