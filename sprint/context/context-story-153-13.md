# Story 153-13 Context

## Title
[glenross-seed-quest] Fate chargen drive-assignment sets a real drive, not the vocation label

## Metadata
- **Story ID:** 153-13
- **Type:** bug
- **Points:** 2
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

On glenross (tea_and_murder, Fate ruleset), Fate chargen's drive-assignment sets `character.drive`
to the vocation label — e.g. `"Episcopal Rector"` — rather than a real aspiration or motivation.
`quest_seed.py::seed_quest_spine` is correct by design (ADR-146 / story 77-2): it uses
`character.drive` as BOTH the quest `title` and `objective`. Because the drive is a vocation echo,
the seeded quest is degenerate:

```
quest_log["seed_drive"].title     == "Episcopal Rector"
quest_log["seed_drive"].objective == "Episcopal Rector"
```

This is a hollow, placeholder-level quest spine. The narrator has nothing meaningful to work from
at turn 0.

The board also notes a minor cosmetic nit (part 2, now **fixed** in server PR #988 / develop):
chargen narration used `"a Episcopal Rector"` (wrong article) instead of `"an Episcopal Rector"`.
That fix (`interpolate_scene_narration` using the `indefinite_article` helper) is already merged;
it is tracked here for AC-completeness only.

## Repro / Evidence

- **Source session:** glenross (Fate), chargen playtest 2026-06-20/21.
- **Observable symptom:** `quest_log.seed_drive` has both `title` and `objective` equal to the
  vocation name, not a drive/aspiration.
- **Root cause (board):** Fate chargen assigned the vocation/calling label to `character.drive`
  during the chargen walk; `quest_seed.py` faithfully copied it.
- **quest_seed.py is NOT the bug.** `sidequest/game/quest_seed.py` line ~64: `source =
  (character.drive or "").strip() or (character.calling_label or "").strip()` — correct; the
  seeder copies whatever is in `character.drive`. The upstream chargen assignment is the defect.
- **Article nit (part 2, already fixed):** `interpolate_scene_narration` in the chargen scene
  templates hardcoded `"a {class}"` regardless of whether the vocation starts with a vowel.
  Fixed by server PR #988.

## Fix Direction

Fate chargen drive-assignment must populate `character.drive` with a real drive
(a genuine aspiration, motivation, or personal goal), not the vocation label. Options:

1. **Content path (preferred):** Supply a `drives:` list per calling in
   `glenross/classes.yaml` (and/or the tea_and_murder genre level), and have the Fate chargen
   handler draw from that list. The glenross classes.yaml currently has no `drives:` field — it
   uses `"Each calling drives:"` only in a comment referring to equipment/beat choices. Content
   needs to be added.
2. **Handler path:** If a drives list is not authored per calling, the Fate chargen handler must
   at minimum not echo the calling label — it should either defer assignment to a chargen step
   (letting the player supply a free-text drive) or draw from a genre-level aspiration pool.

The fix belongs in the Fate chargen drive-assignment path — either the chargen scene handler or
the content — not in `quest_seed.py`.

**Scope note — glenross content:** A confirming grep of
`sidequest-content/genre_packs/tea_and_murder/worlds/glenross/classes.yaml` confirms there is
**no `drives:` or aspiration list** per calling in the content file. Authoring one (per calling or
genre-wide) is within scope of this story if the content path is chosen.

## Acceptance Criteria

1. **Drive is a real drive, not the vocation label.** After Fate chargen completes on glenross
   (and any other Fate pack), `character.drive` holds a genuine aspiration or motivation — not the
   calling/vocation name. `quest_log["seed_drive"].title` and `.objective` are non-degenerate.

2. **Seeded quest is meaningful.** The `seed_drive` quest entry provides a real narrative hook at
   turn 0 that the narrator can use. A chargen walkthrough that produces a quest whose title equals
   the vocation label is a test failure.

3. **Wiring / integration AC.** A test drives the full Fate chargen path for a glenross-like Fate
   pack through the production chargen seam (not by calling `quest_seed.py` directly), creates a
   character, and asserts that `character.drive` is not equal to the vocation `display_name` and
   that `quest_log["seed_drive"]` is non-degenerate.

4. **Article-agreement regression guard (minor / part 2 already fixed).** Chargen narration for
   a vocation beginning with a vowel (e.g. "Episcopal Rector") reads `"an Episcopal Rector"`, not
   `"a Episcopal Rector"`. This is already fixed by PR #988; a guard test ensuring the
   `indefinite_article` helper is exercised on the vocation slot is sufficient.

5. **No silent fallback.** If the calling has no drives list and no player-supplied drive, the
   system must fail or degrade loudly — it must NOT silently use the calling label as the drive.

## Source

- Board: `/Users/slabgorb/Projects/sq-playtest-pingpong-archive-2026-06-21-epic153-capture.md`
  lines 753–775 (BUG-LOW / minor — glenross).
- ADR-144 (Fate Core binding replaces native ruleset).
- ADR-146 (Quest-seed authoring contract — deferred; `quest_seed.py` story 77-2 is the
  implemented seam).
- `sidequest/game/quest_seed.py` — seeder is correct, upstream drive assignment is the bug.
- `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/classes.yaml` — no `drives:`
  list per calling (confirmed by grep).

## Scope Notes

- **In scope:** Fix the Fate chargen drive-assignment to produce a real drive. If the content path
  is chosen, add a `drives:` list per calling to glenross classes.yaml (and optionally at the
  genre/pack level for reuse). Wiring test through the production chargen seam.
- **Out of scope:** Changes to `quest_seed.py` (correct by design). The article-agreement fix
  (already merged, server PR #988). Other Fate chargen steps not related to drive assignment.
- **Content note:** glenross's `classes.yaml` does not supply a drives list — it will need
  content authoring if the content path is taken. This is a server + (optionally) content story.
