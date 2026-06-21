# Story Context: 153-30 — MP Confrontation Roster: vs Across the Faction Boundary Only

## Story Metadata
- **Story ID:** 153-30
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Type:** Bug
- **Points:** 1
- **Workflow:** trivial
- **Repositories:** sidequest-ui *(confirmed — see Owning-Side Verdict below)*
- **Priority:** P3

## Problem Statement

The confrontation header's roster renders a **flat list of all combatants joined by "vs"
between EACH name**, so two allied player characters read as if they are opponents of
each other.

Verbatim finding from the playtest:

> Confrontation header lists all combatants with 'vs' separators between EACH — "Brann vs
> Vesna vs The Thing That Learned Your Name" — so the two allied PCs read as if they're
> opponents of each other. The separate 'Them' block correctly identifies the actual
> opponent (The Thing). Should group allies on one side, 'vs' only across the faction
> boundary.

Expected: allied PCs grouped on one side, "vs" rendered **only across the faction/side
boundary** — e.g. "Brann · Vesna **vs** The Thing That Learned Your Name".

## Owning-Side Verdict (CONFIRMED)

- **Repo: `sidequest-ui` (correct as filed).** This is a pure presentation bug in the
  React confrontation overlay; no server change is needed.
- **The data already carries the side distinction.** Each actor in the payload has a
  `side?: "player" | "opponent" | "neutral"` field
  (`ConfrontationOverlay.tsx::EncounterActor`, defined at `ConfrontationOverlay.tsx:11-23`).
  The flat "vs" join simply ignores it.
- **Proof the side data is reliably populated:** the sibling `ThemPanel` component in the
  same file already filters on it —
  `const opponent = data.actors.find((a) => a.side === "opponent")`
  (`ConfrontationOverlay.tsx:1035-1036`) — and that is the "Them" block the finding says
  "correctly identifies the actual opponent." So the data the roster needs is the same
  array the ThemPanel reads successfully.

## Root Cause Direction

The roster is rendered by the `StatusLine` sub-component inside
`sidequest-ui/src/components/ConfrontationOverlay.tsx` (function at
`ConfrontationOverlay.tsx:452`). It maps `data.actors` and inserts a "vs" separator
before every actor except the first, keyed purely on array index:

```tsx
{data.actors.map((a, i) => (
  <span key={a.name} className="flex items-center gap-1.5">
    {i > 0 && (
      <span className="text-[10px] text-muted-foreground/60">vs</span>
    )}
    <ActorChip actor={a} />
    {committedActors !== null && a.side === "player" && ( /* commitment badge */ )}
  </span>
))}
```

(`ConfrontationOverlay.tsx:476-497`)

The `i > 0` index test is the bug: it places "vs" between *every* adjacent pair, including
two `side: "player"` allies. The fix is to **group `data.actors` by `side` and render
"vs" only between groups (across the faction boundary), never within a side.**

**Reuse-first (per architect direction — extend the existing roster, do NOT invent a new
layer):** group within `StatusLine` using the `side` field that `ThemPanel` already relies
on. Allies (`side === "player"`) render together with an intra-side separator that is NOT
"vs" (e.g. a thin dot "·" or a small gap, matching the existing muted styling), and the
single "vs" sits at the player↔opponent boundary. Preserve the existing per-actor
behaviors anchored on each actor span:
- the `ActorChip` render,
- the player-only commitment badge (`a.side === "player"` gate at
  `ConfrontationOverlay.tsx:482`), which already keys off `side` and must keep working,
- the `key={a.name}` stability.

A `neutral` side (third group) is possible per the type; handle it without forcing a "vs"
that implies opposition (group neutrals separately or alongside players per design — the
load-bearing rule is "vs" appears only at a genuine adversary boundary).

## Acceptance Criteria

1. **Allies are not separated by "vs":**
   Given a confrontation whose `data.actors` contains two or more `side: "player"` actors,
   the roster renders **no** "vs" between any two player-side actors. (Reproduces the
   finding: "Brann vs Vesna" must not appear.)

2. **"vs" appears only across the faction boundary:**
   "vs" is rendered exactly once between the player group and the opponent group — e.g.
   "Brann · Vesna vs The Thing That Learned Your Name". With one PC and one opponent the
   output is "Brann vs The Thing…" (single "vs", unchanged from the simple case).

3. **Side grouping is driven by the existing `side` field:**
   The grouping uses `EncounterActor.side` (the same field `ThemPanel` consumes), not
   array order or name heuristics. Player-side actors group together; opponent-side actors
   group together.

4. **Existing per-actor behaviors preserved:**
   Each actor still renders its `ActorChip`, and the player-only commitment badge
   (`Committed`/`Waiting`, gated on `side === "player"` and `committed_actors`) still
   renders for player-side actors exactly as before. The dual-dial / HP bars and the
   `data.label` mid-roster element are unchanged.

5. **Legacy / missing-side payloads degrade safely (no silent mis-grouping):**
   `side` is optional on legacy payloads. When `side` is absent for some/all actors, the
   roster must not crash and must not invent an adversary boundary; a documented,
   deterministic fallback is used (e.g. actors with unknown side render in a single group
   with no inter-ally "vs", so the worst case is the old flat list collapsing to no-"vs"
   rather than a wrong "vs"). Fail visibly toward "no false opposition," never toward a
   silent wrong grouping.

6. **Single-side confrontation renders no "vs":**
   If every actor is on the same side (e.g. all `player`, an edge/degenerate roster), no
   "vs" is rendered at all (there is no faction boundary).

7. **Wiring / integration test proves the rendered roster (required):**
   A component test renders `ConfrontationOverlay` (or `StatusLine`) with a real
   `ConfrontationData` fixture containing two `side: "player"` allies and one
   `side: "opponent"`, and asserts on the **rendered DOM**: exactly one "vs" node, located
   between the player group and the opponent group, and zero "vs" between the two allies.
   This drives the production component (not a helper in isolation) so the grouping is
   verified end-to-end through the rendered overlay. Reuse the existing confrontation test
   fixtures/harness rather than hand-rolling a new render scaffold.

## Key Code Areas to Investigate

**The roster header (owns the fix):**
- `sidequest-ui/src/components/ConfrontationOverlay.tsx`
  - `StatusLine` (`ConfrontationOverlay.tsx:452`) — renders the combatant roster; the
    flat `i > 0` "vs" join is at `ConfrontationOverlay.tsx:476-497`.
  - `ActorChip` (`ConfrontationOverlay.tsx:314`) — per-actor chip; keep as-is.
  - `EncounterActor` interface (`ConfrontationOverlay.tsx:11-23`) — the `side?: "player" |
    "opponent" | "neutral"` field that drives the grouping.
  - `ConfrontationData` interface (`ConfrontationOverlay.tsx:127-201`) — `actors:
    EncounterActor[]` plus `label`, `committed_actors`, HP/metric fields.
  - `ThemPanel` (`ConfrontationOverlay.tsx:1035`) — the reference: already filters
    `a.side === "opponent"` ("Them" block in the finding); proves side data is available.

**Data source / prop flow (read-only, to confirm the shape):**
- `sidequest-ui/src/App.tsx` — handles `MessageType.CONFRONTATION`, sets
  `confrontationData`, and passes it to `ConfrontationOverlay` (`StatusLine` receives
  `data` from there). Confirm the wire payload already includes per-actor `side`.

**Existing tests to extend (anchors / fixtures):**
- `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx`
- `sidequest-ui/src/__tests__/confrontation-commitment-102-4.test.tsx`
  (already exercises `side: "player"` commitment badges — a ready fixture shape with
  player-side actors to extend with a multi-ally roster)
- `sidequest-ui/src/__tests__/confrontation-mid-turn-momentum-sync.test.tsx`

## Technical Notes

- **ADR-116 (a confrontation requires an Other):** the roster's whole point is that there
  IS an opposing "Other." The `side` field is precisely the player↔Other boundary ADR-116
  guarantees, and the "vs" should mark exactly that boundary — not the allied-PC gaps.
  This is the display correlate of ADR-116's membership model: the Other has a face (the
  ThemPanel), and the roster's single "vs" should align with the same boundary.
- **ADR-036 (multiplayer turn coordination):** multiple player-side actors in one
  confrontation is the normal MP case (the whole party is in the fight); the roster must
  read as "the party vs the Other," which is the table-coordination read ADR-036 wants —
  allies should look allied.
- **ADR-104 / ADR-105 (perception firewall):** purely a presentation grouping over the
  already-delivered `data.actors` for this client; no change to what actors are visible or
  to any server-side filtering. The fix touches only how the received roster is laid out.
- **ADR-108 (per-recipient item attribution / tagging):** not directly involved; noted
  only to scope the fix away from any per-recipient server tailoring — this is a
  client-side, side-agnostic-to-recipient layout change driven by each actor's faction
  `side`, identical for all viewers.
- **Reuse-first / No new component:** extend `StatusLine` in place; reuse the `side` field
  that `ThemPanel` already consumes and the existing muted-separator styling. Do not add a
  new roster component or duplicate grouping logic — the data and the reference filter
  already exist in the same file.
- **No source-text wiring tests** (ui CLAUDE.md): assert on the rendered DOM (number and
  placement of "vs" nodes) through the real component, not on the component's source text.
- **OTEL:** none required — this is a cosmetic UI grouping change (ui CLAUDE.md: OTEL "not
  needed for cosmetic UI changes (labels, spacing, colors)"). No subsystem decision is
  added on the server.

## Story Scope

In scope:
- Grouping `StatusLine`'s roster by `EncounterActor.side` so allied PCs render together
  and "vs" appears only at the player↔opponent (faction) boundary.
- Preserving `ActorChip`, the player-only commitment badge, HP/metric bars, and `label`.
- Safe handling of legacy/missing `side` and single-side rosters (no false "vs").
- A component test asserting on the rendered "vs" count and placement.

Out of scope:
- The `ThemPanel` "Them" block (already correct — used only as the reference for side
  data being present).
- Any server / wire-payload change (the `side` field already ships; ADR-116 already seats
  actors with a side).
- Pronoun localization (that is sibling story 153-29, server-side `pov_swap.py`).
- Re-styling the roster beyond what grouping requires (intra-side separator + the single
  cross-boundary "vs"); broader visual redesign is not this story.

---

## Development Notes

1. Reproduce the finding as a RED component test first: a `ConfrontationData` fixture with
   actors `[{name:"Brann", side:"player"}, {name:"Vesna", side:"player"}, {name:"The
   Thing That Learned Your Name", side:"opponent"}]`, then assert exactly one "vs" between
   the player group and the opponent (zero between Brann and Vesna).
2. Group by `side` inside `StatusLine` (`ConfrontationOverlay.tsx:452`), mirroring how
   `ThemPanel` (`:1035`) reads `a.side`. Keep the commitment-badge `a.side === "player"`
   gate intact.
3. Cover the legacy (no `side`) and single-side edge cases so the change never invents a
   "vs" where there is no adversary boundary.
