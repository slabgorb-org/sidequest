# GM Decisions

Standing rulings and doctrine from the operator (Keith) that govern GM/content
work. Append new decisions; don't rewrite history. Convert relative dates to
absolute.

## 2026-06-21 — `factions: ["*"]` is the behavior-preserving unblock for zoned worlds

**Context:** Epic-157 (faction/zone-scoped content eligibility) tagged only 4 of
the **7** live zoned worlds. 157-5/157-6 covered gulliver, oz, wonderland,
the_circuit. Missed: `space_opera/perseus_cloud`, `space_opera/coyote_star`,
`tea_and_murder/glenross` — all declare `controlled_by` regions (→ zoned) but had
ZERO faction tags. The strict load validator (157-7, fail-loud) would `GenreLoadError`
on them and break develop.

**Ruling (Keith, 2026-06-21):** "Tag the 3 worlds first" → **world-global `["*"]`
everywhere.** `"*"` is behavior-identical to untagged at the runtime predicate
(`is_eligible`: both short-circuit to eligible), so blanket `["*"]` satisfies the
validator's non-empty requirement and changes NOTHING in play. It is also the
*correct* semantic for a cozy single-zone-of-many world like glenross (content is
village-wide; per-household gating would over-suppress). Real per-faction scoping
(content hides outside its zone) is a genuine game-feel change — Keith owns it; do
NOT do it unilaterally. Offer it as a follow-up, don't assume it.

**Reusable pattern:** zoned world = any region with truthy `controlled_by`
(`no_one`/`null` hubs count only if the string is truthy). Validator scope is per
world: `bestiary.entries` + RESOLVED `tropes` (post-inheritance; only world tropes
emitted, child `factions` override parent) + `seed_tropes`. Genre-tier pooled files
are parents only, never validated directly. Verify with `uv run python -m
sidequest.cli.validate pack <pack>` + a loader sim checking every resolved pooled
item has non-empty factions ⊆ {`"*"`} ∪ controlled_by-slugs.

## 2026-06-13 — WWN SRD is the authority for any WWN-bound mechanical question

**Ruling (Keith, verbatim intent):** "When asked 'what should this be like' for
anything under the WWN SRD, the answer is: **use the SRD.**"

**Scope:** Any world/pack bound to the WWN ruleset (`ruleset: wwn` in `rules.yaml`,
ADR-117) — e.g. `caverns_and_claudes/beneath_sunden`, `heavy_metal/barsoom. When a
mechanical value, behavior, or magnitude is unspecified or in doubt — heal amounts,
XP/advancement scale and award model, AC, attack/save math, system strain, effort,
encounter/morale, item effects — **do not invent a number or port a native/legacy
value. Source it from the Worlds Without Number SRD** and cite which SRD rule was
used.

**How to apply:**
- Content authoring: when adding/repairing a WWN-world item or rule, pull the value
  from the WWN SRD, not the native/legacy genre default.
- Playtest findings: when a WWN subsystem produces a value, the correctness oracle is
  the WWN SRD. A value that matches an OSR/D&D-scale (e.g. XP in the hundreds at L1) is
  a **mismatch finding**, because WWN uses small-integer XP (L2 ≈ 3 XP) and
  expedition/goal-based XP, not per-kill XP.
- When wiring an effect (e.g. a healing potion), the magnitude question goes to the
  SRD first; only escalate to Keith if the SRD is genuinely silent.

**Concrete instances this ruling already resolves (2026-06-13 beneath_sunden playtest):**
- *Potion of Mending heal magnitude* → use the WWN SRD healing value, not an invented number.
- *XP scale / award model* → WWN expedition-XP and small-integer scale, not the native
  135-at-L1 number observed on a fresh Warrior.

## 2026-06-13 — Epic 106 ramp rulings (Keith, answering the 106-1 Delivery Findings)

Four blocked-story rulings resolved so Epic 106 (WWN combat hardening for
`beneath_sunden`) can run. All defer to WWN where the SRD speaks.

- **106-2 reprisal model → WWN initiative round (full-defend).** Adopt the WWN
  initiative round so a player can declare full defense and avoid reprisal. Reuses the
  ~80%-built `wn_round.py` infra the Architect found. The beat model does *not* become
  the reprisal authority; WWN initiative does. This is ramp lever #2.
- **helmet_iron → model shield/helmet as +AC modifiers.** Don't drop the item. WWN
  gives helmets no *base* AC, so `helmet_iron` must not occupy the body-armor roll slot
  that leaves ~1/3 of Warriors at AC 10. Model helmet (and shield) as additive AC
  modifiers stacked on body armor, per WWN shield handling. Followup to 106-1.
- **106-4 consumable-use heal magnitude → RESOLVED (Keith, 2026-06-13).**
  - *Scarcity/slot:* **guaranteed heal for everyone.** Every kit (warrior/mage/expert)
    starts with exactly one Potion of Mending; additionally a **30% chance the guaranteed
    potion is a *better* one instead** (upgrade only — never worse, never zero). This
    makes the kit deterministic enough to test the beat-scan while preserving an upside roll.
  - *Magnitude:* WWN SRD has **no standard healing potion (genuinely silent)**, so per the
    escalation clause this went to Keith. Anchored to the WWN-family heal idiom (CWN Lazarus
    Patch = 1d6+level): **Potion of Mending = `1d6+2`; Potion of Mending (Greater) = `2d6+2`.**
    L1 Warrior pool ≈ 10, so base ≈ half a pool — a reprieve, not a reset; keeps the lethal ramp.
- **106-5 death-state → true WWN dying window.** Implement a real WWN dying/down state,
  not terminal-dead-only. Caveat carried into the story: the WWN d6 stabilize clock is
  currently unactionable in solo play — the story must address the solo actuator gap,
  not ship a clock nothing can advance.

## 2026-06-14 — Remove the native combat engine under a Without Number binding. DO NOT balance it. (Keith, emphatic)

**Ruling (Keith, verbatim intent):** *"We have tried in the past to make native work
with WWN. This is a DEAD END. We are going to use the Without Number engine so we don't
have to balance. All this 'we were trying to balance native tricks with this other
stuff' — YES, that's the thing we failed at, because the scope was too much. PLEASE get
this clear in ALL documentation — we keep UNDOING it."*

**The point.** We bind Without Number **so that we never have to balance combat.** WN's
published math IS the balance. Layering the native dial/beat engine underneath a WN
binding and tuning the seam re-creates the exact open-ended balancing problem the binding
was meant to eliminate. That hybrid is the dead end. We keep reverting to it because the
reflex — and stale design docs — say "keep `beat_selection`, layer WWN on top."

**Ruling, concretely.** Under a WN binding (`ruleset: wwn` now; `swn`/`cwn`/`awn` staged,
same rule), combat resolves through the Without Number initiative-round engine
(`wn_round.py`). The native ADR-033 beat engine is **DELETED from the WN combat path, not
gated/tuned**: the `strike`/`brace`/`push`/`angle` beat kinds, the edge / fleeting-tag /
"Counter Stance" system, the per-beat auto-reprisal, and the inert dial metrics. **Brace
is not a WWN action.** Each side acts on its own initiative; attack `d20 + hit vs AC`,
weapon dice, Shock, morale, WN saves/lethality/XP.

**This SUPERSEDES** the "Option A full-defend" balance path (#839) and **every**
"tune/convert/gate the native beat" finding: #192 mitigation magnitude, #442
Counter-Stance conversion, Brace tuning. Those are resolved by **removal**, not
adjustment. No agent ships another native-balance patch under a WN world.

**Architecture-of-record:** ADR-143 (`docs/adr/143-wn-binding-replaces-native-combat-no-balancing.md`).
**Doctrine:** SOUL.md → *Bind the Ruleset, Don't Balance It*. **Owner of the rework
spec/epic:** Architect (Neo). FIXER does **not** ship native-balance patches.

**Still valid work (NOT native, not affected by this ruling):** light pool; helmet/armor
AC from the WWN SRD; the guaranteed-heal grant (#843); the Monster Manual per-room
creature binding feeding the WN seater (the WN round must seat its Other from the bound
room roster, per ADR-116, not improvise one — this is the 107-2 finding, and it is a
*seating* fix, not a balance patch). Dial **chase/negotiation** confrontations are not WN
combat and keep the native dial engine even in WN packs.

### Random-dungeon theme eligibility (Keith, 2026-06-24, story 158-19)
- **It's a RANDOM DUNGEON, not an authored progression.** Themes must be broadly
  eligible at EVERY depth — every depth offers MULTIPLE theme choices (target ≥2–3),
  never collapses to one. The opening descent was monotone ("water every time")
  because drowned_cavern was the only theme with min=0; the others were deep-gated.
- **Depth tunes ENCOUNTERS, not THEMES.** Do NOT stratify themes into depth bands to
  form a strict shallow→deep staircase. A theme can appear at any depth; what scales
  with depth is encounter DIFFICULTY — handled by the cookbook `cr_bands`
  (shallow/mid/deep CR by depth, `cookbook/affinities.yaml`) and per-creature
  `depth_band` entries in a theme's creature_table (easy rows shallow, hard rows deep).
  drowned_cavern at depth 5 = shallow creatures; drowned_cavern at depth 50 = deep
  creatures. Same theme, scaled threat.
- **Anti-domination invariant (replaces "narrow drowned's max"):** drowned must be
  1-of-N at every depth, INCLUDING deep — not banished from the deep. The fix is wide
  overlapping bands across the whole palette, not capping drowned shallow. (This
  overturned the original 158-19 AC-2 "narrow drowned_cavern's max" framing and the
  TEA test `test_drowned_cavern_no_longer_dominates_deep_slot`.)
- **Two orthogonal axes (confirmed):** `theme` (drowned/bone/etc.) → interior generator
  + narrator register + depth eligibility + quest. `look` (necropolis/sunken/delvehold)
  → cookbook RACE faction → creatures. Theme does NOT pick the race; `look` does. The
  theme's own creature_table is currently decorative (Plan 6 deferred) — keep its refs
  REAL (existing bestiary ids / newly-authored gated entries), never phantom.

### Theme-variety targets + encounter ownership (Keith, 2026-06-24, story 158-19)
- **≥5 themes eligible PER STRATUM, not 2-3.** "Having 2 or so per stratum will be
  repetitive" — quests + encounters ride on themes, so a thin per-stratum set repeats
  fast. Flatten all themes to {0,null} so every depth offers the full grab-bag.
  beneath_sunden: 5 existing + 3 new seeds = 8 broadly-eligible themes (clears the 5 floor).
- **Keith owns/seeds ENCOUNTERS.** "Trust me, I can come up with seeds for encounters."
  Do NOT author new creature stat lines for new themes. New themes reference REAL existing
  bestiary ids in creature_table; signature big-bads (the animated suit, the fungal
  spawner, the coffin-thing) are SET-PIECES (prose + trope), not wandering-monster rows.
  Keith layers encounter seeds on top later.
- **Test invariant follow-on:** the TEA shallow-variety test floor (≥2) should rise toward
  ≥5 per stratum to match this bar; the drowned-banishment test is dropped entirely
  (see "Random-dungeon theme eligibility").

### sunless_temple re-themed built→labyrinthine (Keith, 2026-06-24, story 158-19)
- **Why:** flattening all themes to {0,null} (random-dungeon eligibility) made
  `sunless_temple` (generator_class `built` → roomcorridor) shallow-eligible, but
  beneath_sunden ships NO roomcorridor cookbook look (only depthfirst/cellular/prim) and
  `KNOWN_GENERATOR_BINDINGS` excludes roomcorridor — so roomcorridor is unmaterializable
  here and the materializer fail-loud'd at the look seam (seed-dependent red across
  session/projection tests). Keeping it roomcorridor would need SERVER code (extend
  KNOWN_GENERATOR_BINDINGS + author a look + dim-validation) — out of the content lane.
- **Decision:** content-only re-theme to `labyrinthine` (algorithm depthfirst, params {},
  braid_ratio 0.3), binding the existing **necropolis** look. Chosen over cellular because
  the look picks the MONSTER FACTION: cellular→sunken is ooze-heavy + "drowned/wet"
  register (wrong for a dry colonnaded temple); depthfirst→necropolis is undead-heavy +
  "mausoleum-formal, straight lines" (right — matches the temple's own acolyte-shade /
  altar-horror creature_table). braid 0.3 = hall connectivity, not a pristine trap maze.
- **Supersedes** the earlier "validate region dims before dispatch" delivery finding —
  that was a mis-diagnosis (the failure fired earlier, at look resolution, dim-independent).
- **Standing rule:** beneath_sunden supports 3 generator families (depthfirst/cellular/prim).
  Do not author or flatten a `built`/roomcorridor theme into its eligible pool without the
  server-side roomcorridor support landing first.
