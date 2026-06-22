# Story 153-3 Context — Architect Design

## Title
[WRY-WHIMSY-NO-FATE-CONTEST-DEFS] port wry_whimsy + pulp_noir confrontation
catalogs to the Fate Contest/Conflict schema + loud loader guard

## Metadata
- **Story ID:** 153-3 · **Type:** bug · **Points:** 5 (now under-pointed — see Scope note)
- **Workflow:** tdd · **Repos:** server, content · **Epic:** 153 (playtest follow-ups)
- **Load-bearing ADR:** ADR-144 (Fate Core Binding replaces the native ruleset).
  Also: ADR-116 (a confrontation requires an Other), ADR-143 (Bind, don't balance),
  ADR-148/151 (Fate dice).

> The sprint YAML carried only a title. This document, written by the Architect
> (the Man in Black) during a design pass, is the **authoritative spec**. It
> supersedes the hypothesis AC-1..AC-5 the setup helper drafted in the session.

---

## Problem (measured, not assumed)

Four packs bind `ruleset: fate`. Their confrontation catalogs were audited by
loading each pack through the real `load_genre_pack` and reading
`resolution_mode` + whether beats are armed:

| Pack | confrontations | native `beat_selection` (armed beats) | already Fate |
|------|---|---|---|
| **wry_whimsy** | 6 | **6/6** (audience, wit_duel, escape, wonder_shock, persuasion, violence) | 0 |
| **pulp_noir** | 3 | **3/3** (standoff, combat, negotiation) | 0 |
| **spaghetti_western** | 5 | **3/5** (standoff, negotiation, chase) | combat=contest, poker=table_resolution |
| **tea_and_murder** | 5 | 0 | 5 (clean — reference) |

A `beat_selection` confrontation on a Fate pack **loads silently** and is seated
as a Fate Conflict (`seat_as_fate_conflict`), but its armed native beats
(`kind`/`base`/`stat_check`) and dial thresholds are **inert** — the FateSheet
stress track is the real engine. That silent-inert-native-crunch is the bug
(SOUL "Bind the Ruleset"; No Silent Fallbacks). The fix is a **loud loader
guard** that forces Fate packs to declare a Fate resolution mode, plus the
**content port** of every native def.

### Why "everything → contest" is wrong (Keith's ruling, 2026-06-21)
A Fate **Contest** is a no-harm competition (first-to-N victories; *"No stress,
no consequences"* per the `ResolutionMode.contest` docstring). A Fate **Conflict**
is a fight — 4dF + ladder, ablative stress → consequences → *Taken Out*. The
Jabberwock (wry_whimsy `violence`) and a `combat` gunfight (pulp_noir) can **kill
you**, so they are Conflicts, not Contests. Mapping a lethal fight to a Contest
would make it literally unable to harm the player.

### Why a new mode is required (reuse analysis)
- Reusing `contest` for combat — **rejected**: contest is no-harm by definition.
- Reusing `opposed_check` — **rejected**: it is the d20 dial path, already banned
  on Fate by `_fate_packs_have_no_opposed_check` (the bleed tripwire).
- Reusing `beat_selection` as the Conflict trigger (relax the armed-beat rule for
  Fate) — **rejected**: `beat_selection` literally means "player rolls d20 vs DC";
  overloading it to also mean "Fate Conflict" conflates the native default with the
  Fate path and **defeats the guard** (you can't ban `beat_selection` if it is also
  how you author a Conflict).

The Fate Conflict **runtime already exists and already runs** — `fate.py`
(`mark_stress`, `take_consequence`, `seed_opponent_fate_sheet`), `fate_conflict.py`,
the `seat_as_fate_conflict` seating branch, the `_seed_fate_opponents` opponent
FateSheet seeding, and the `fate_conflict_seeded_span` lie-detector all run today
for wry_whimsy `violence` (via `beat_selection`). The existing tripwire message
even tells authors to use *"the Contest mode … or a Conflict"* — a concept that is
referenced but has **no enum value**. So this design adds a thin **authoring
handle** for an already-built engine; it does not design a new system.

---

## Decision: add a `conflict` resolution_mode — the lethal sibling of `contest`

### Server changes (sidequest-server)

1. **`ResolutionMode` enum** (`genre/models/rules.py`, ~line 349):
   add `conflict = "conflict"`. Extend the enum docstring: *4dF + ladder, ablative
   stress → consequences → Taken Out, resolved against the Other's FateSheet
   (`fate_conflict.py`); display-only beats; an adversarial Fate path — a fight.
   Fate packs only.*

2. **`ConfrontationDef._validate`** (`genre/models/rules.py`, the contest branch
   ~666–690 and the metric requirement ~565–573): treat `conflict` like `contest`
   for **beat shape** and **metric requirements**:
   - Beats: a `conflict` def carries **display-only** beats (id + label +
     narrator_hint), same as `contest` — the `_DIAL_BEAT_FIELDS` rejection applies
     to it, and the else-branch "armed beats REQUIRED" must **exclude** it. Cleanest:
     `_FATE_DISPLAY_ONLY_MODES = {ResolutionMode.contest, ResolutionMode.conflict}`
     and gate both branches on membership.
   - Metrics: a Conflict's win track is the opponent FateSheet stress (inert
     synthesized metrics at seating), so it needs **no** player/opponent metric.
     Exempt `conflict` from the `dial_threshold` "needs both metrics" rule
     (line ~566: `resolution_mode not in (contest, conflict)`). The contest-only
     `player_metric` requirement (line ~555) stays **contest-only** — do NOT extend
     it to conflict.

3. **Loud loader guard** (`genre/models/rules.py`): a `ruleset: fate` pack's
   confrontations must use only Fate resolution modes. **Allowed:**
   `{contest, conflict, table_resolution, sealed_letter_lookup}`. **Banned:**
   `beat_selection` (native default) and `opposed_check`.
   - Recommended: **generalize** `_fate_packs_have_no_opposed_check` into an
     allowlist guard `_fate_packs_use_fate_resolution_modes` — collect every
     confrontation whose `resolution_mode` is not in the allowed set and raise a
     loud `ValueError` naming the offenders and pointing at contest/conflict.
   - **Test-compat constraint:** `tests/genre/test_fate_no_opposed_check.py`
     asserts `pytest.raises(ValidationError, match="opposed_check")`. The new
     message MUST still contain the offending mode's value, so an `opposed_check`
     offender keeps producing `"opposed_check"` in the message. (If Dev prefers,
     keep the old validator and add a second `…no_native_beat_selection` sibling —
     either is acceptable; the allowlist is DRYer.)

4. **`_requires_opponent`** (`server/dispatch/encounter_lifecycle.py`, ~724–750):
   fold `conflict` in alongside `opposed_check`/`contest` so a Fate Conflict of
   **any** category requires an Other (ADR-116). For this story's defs (all
   `category: combat`) the adversarial-category branch already covers it, but
   adding `conflict` closes the footgun for a future mental/social Conflict. This
   is the **only** runtime-path edit.

5. **No other runtime changes.** `seat_as_fate_conflict = is_fate and
   resolution_mode not in (contest, sealed_letter_lookup)` already routes
   `conflict` into the Fate Conflict seat; `fate_conflict_seeded_span` already
   fires; `_seed_fate_opponents` (is_fate-gated) already seeds the opponent
   FateSheet. Do **not** add a new engine, a new seating branch, or a new span.

6. **OTEL:** the loud guard is a load-time **fail-loud raise** — the exception is
   the signal (mirrors its `opposed_check` sibling, which emits no span). No new
   span for the guard. Runtime conflict observability already exists
   (`fate_conflict_seeded_span`). Reviewers: this is intentional, not a gap.

### Content changes (sidequest-content) — port all THREE native packs

Each ported def: set `resolution_mode`; strip beats to **display-only**
(`id` + `label` + `narrator_hint` only — remove `kind`, `base`, `stat_check`,
`effect`, `risk`, `consequence`, `resolution`, `target_tag`, `deltas`, `reveals`,
`edge_delta`/`target_edge_delta`). For **contest** defs set both metric
`threshold: 3` (the victory tally; keep a `starting` head-start only where the
flavor wants asymmetry). For **conflict** defs **remove** `player_metric` /
`opponent_metric` (synthesized inert at seating). Keep `category`, `mood`,
`intent_verbs`, `escalates_to`.

| Pack | → `contest` (no-harm) | → `conflict` (lethal) | unchanged |
|------|----|----|----|
| **wry_whimsy** | audience, wit_duel, escape, wonder_shock, persuasion | **violence** | — |
| **pulp_noir** | standoff, negotiation | **combat** | — |
| **spaghetti_western** | standoff, negotiation, chase | **combat** (was `contest` → make lethal) | poker (table_resolution) |

> spaghetti_western `combat` is already a (non-native) `contest`. Per the
> lethality ruling a gunfight is a Conflict, so flip it `contest → conflict`. This
> is in-scope by the same principle; log it as a deviation.

tea_and_murder is already clean (5/5 Fate) — it must keep loading (regression guard).

---

## Acceptance Criteria (authoritative — for TEA's RED tests)

- **AC-1 (server):** `ResolutionMode.conflict` exists; a Fate `ConfrontationDef`
  with `resolution_mode: conflict`, display-only beats, and **no** player/opponent
  metric **loads cleanly** (bare `RulesConfig` and through `load_genre_pack`).
- **AC-2 (server, no regression):** `contest` still requires display-only beats
  **and** `player_metric`; a contest def with armed beats or no player_metric still
  fails loud (existing guards untouched).
- **AC-3 (server, the loud guard):** a `ruleset: fate` pack authoring a
  `beat_selection` confrontation **fails pack load** with a `ValidationError`
  naming the offending confrontation; `opposed_check` continues to fail loud.
- **AC-4 (server, Fate-gated):** a non-Fate pack (WN-family / dial fixture) with a
  `beat_selection` confrontation **still loads** — the guard never touches native
  packs.
- **AC-5 (server, wiring):** a `conflict`-mode `combat` def requires an Other
  (`_requires_opponent` True) and seats through the Fate Conflict path
  (`seat_as_fate_conflict` True → `fate_conflict_seeded_span`). Drive it through the
  real seating seam, not a source-text grep.
- **AC-6 (content):** wry_whimsy loads; all 6 use Fate modes (5 contest +
  violence=conflict); no confrontation carries armed beats.
- **AC-7 (content):** pulp_noir loads; all 3 use Fate modes (2 contest +
  combat=conflict); no armed beats.
- **AC-8 (content):** spaghetti_western loads; standoff/negotiation/chase=contest,
  combat=conflict, poker=table_resolution; no armed beats on contest/conflict defs.
- **AC-9 (regression):** tea_and_murder still loads unchanged (no over-rejection).

## Scope note (for SM)
This grew from "port 2 packs + guard" to "new `conflict` resolution_mode +
validators + allowlist guard + `_requires_opponent` + port **3** packs." Honest
re-point ≈ **8**. Flagged as a Delivery Finding; not re-pointed by the Architect.

## Testability notes (for TEA / Fezzik)
- Unit-drive the validators with bare `RulesConfig(ruleset="fate", …)` — mirrors
  `tests/genre/test_fate_no_opposed_check.py` exactly.
- Wiring/guard tests at the `load_genre_pack` boundary: clone a real ported Fate
  pack (tea_and_murder) to `tmp_path`, mutate one def back to native
  `beat_selection` **with armed beats** (so the ONLY rejection reason is the new
  Fate guard, not the existing "beat missing dial field" else-branch), assert raise.
- Real-content tests against wry_whimsy/pulp_noir/spaghetti_western use the
  `genre_paths` helper with `skipif(not pack_path.exists())`.
- AC-5 seating: construct a synthetic Fate snapshot and drive the real seating
  function; assert the conflict span fired (OTEL), per the repo's "No Source-Text
  Wiring Tests" rule.

_Generated by the Architect (design pass) for story 153-3._
