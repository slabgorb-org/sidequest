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

<!-- migrated from Claude auto-memory store, 2026-06-24 -->

## Content is validated, not tested → hand to the GM (2026-06-11, from Keith)
- Keith: "this should merely be handed off to the GM. WE DO NOT TEST CONTENT WE VALIDATE IT."
- Content-only stories (genre pack / world YAML — cartography, encounter_tables, stocks, cultures, factions, openings, tropes, lore) go to the GM agent (`/pf-gm` / `sq-world-builder`) and are VALIDATED (load via `load_genre_pack`, schema/loader checks, cliché-judge audit), NOT run through the TDD red→green→review cycle. Do not route content to TEA to write failing tests.
- Why: content has no code under test; the lie-detector is "does the pack load + validate + pass cliché bans," not "does a pytest go red then green." TDD on content invents vacuous tests and wastes a RED phase.
- How: when a story's repos are content-only (`sidequest-content`), ignore a stale `workflow: tdd` tag and route to the GM. TDD/phased TEA→Dev→Reviewer is for server/ui/daemon CODE only. Note the real loader catches what the validator misses (validate-pack vs loader gaps).

## Legacy save compatibility is not a goal (2026-04-26, from Keith)
- Failures loading legacy saves at `/Users/slabgorb/.sidequest/saves/games/` (e.g. `debug_state.snapshot_load_failed` warnings, schema-validator rejections from old field names) are NOT bugs worth fixing. Don't propose `model_validator` migrations, a migrations/ framework, or accept-both-shapes shims for old saves.
- Why: personal project in active development with frequent schema churn; Keith doesn't replay old saves (each playtest spawns a fresh slug). Old saves are throwaway test data; the schema migration was correct, the warnings are cosmetic noise.
- How: ignore `snapshot_load_failed` for old slugs unless Keith asks to recover a specific save. Don't propose schema-migration code during playtest bug-hunting. If "save won't load" comes up, ASK whether it's a fresh or old save — fresh-save load failure IS a real bug; old-save load failure is not. Don't recommend `model_validator(mode="before")` for legacy field rejection; the forward break is intended.

## Don't default to stock fantasy/SF naming words ("Reach", "Veil", "Spire") (2026-05-01, from Keith)
- When naming places/factions/worlds, do NOT default to the grab-bag: "Reach", "Veil", "Spire", "Hollow", "Drift" (as a place suffix), "Mire", "Shroud", "Sanctum", "Bastion". Keith forced "Coyote Reach" → "Coyote Star".
- Force at least one alternative that avoids these suffixes; prefer names derived from the world's own geography/language/history; lean on the genre pack's `cultures.yaml` and `corpus/`.
- When the user has named something, use their name verbatim — don't "improve" it with a stock suffix.

## OTEL-first — never mark a mechanical AC green off narration prose (2026-06-20, 150-3)
- During a playtest, never verify mechanics from prose. The narrator fabricates convincing mechanics with zero engine backing — exactly what the OTEL architecture exists to catch. Have the GM panel (Inspector `localhost:5173/#/dashboard`) UP and the by-slug session pinned BEFORE verifying anything (Phase 1, not "when something looks wrong").
- 150-3 five_points: prose rendered "Mapped to Fate dice: −1,+1,+1,0 = +4 — a solid Success" for an out-of-conflict check. GM panel showed `lethality_arbiter 0ms`, beats none, patches `npc_pool()` only, no FATE_ROLL span; the roll was even rejected as a `dice_roll` footnote (pydantic `extra_forbidden`). Pure fabrication.
- Verify against the panel: Timeline (beats/patches/spans), Encounters, Mechanical census, and stored `/api/debug/save/{slug}/snapshot` (`encounter.fate_commits` = real dice faces; `fate_sheet.stress` = real harm). Stored state is ground truth. OTEL spans NEVER hit `sidequest-server.log` — grepping the text log for FATE_ROLL/state_patch/beats always comes up empty. A result that exists only in prose = the lie detector firing; file it, don't pass it.

## The playtest IS the dev cycle — don't plan-mode out of mid-playtest crashes (2026-05-06, from Keith)
- When the user is mid-playtest and bugs surface, don't propose "let me write a real plan and do this properly tomorrow." Keith: "why do you think I am playing this game other than for the express purpose of fixing it." The play loop and the fix loop are the same loop; suggesting an exit suggests stopping development.
- Apply: fix-fast, restart-fast, ready for the next bomb. Don't pause for ceremony.
- Exception: when the right fix is genuinely architectural (whole-subsystem revert, e.g. Sünden 2026-05-06), propose the revert as the fastest path back to playable — not as a reason to stop the playtest. Plan mode is for designing the new direction, not for stalling.

## Victoria pack success = relationship dynamics, not confrontation firing (2026-05-12, Glenross playtest)
- For the Victoria pack (and social-first genres), don't grade success by `beat_selections`/`confrontation` OTEL spans the way caverns_and_claudes does. Keith mid-playtest: "in this world the important thing is the relationships, dice throwing not so much." Victoria is Brontë-gothic-cosy (axis_snapshot cosy 0.75, gossip 0.7, gothic 0.05).
- The load-bearing layer is Journal extraction (PERSON/PLACE/QUEST/LORE with certainty tags) + NPC pool consistency + relational continuity. `beat_selections=0 confrontation=None` is NORMAL — don't file it as a problem.
- Audit instead: Journal entries appearing, NPC pool_hits across turns, narrator remembering established trust/withholding, standing changes when scandals surface. For a "what's mechanically real" check, look at the Knowledge journal (ADR-053 fact-extraction half is the lie detector), not the confrontation panel. Cross-applies to pulp_noir and future drawing-room/mystery/social genres; NOT to combat-first packs.

## Barsoom — faithful-Burroughs sword-and-planet on the heavy_metal (WWN) chassis (2026-06-05, from Keith)
- New heavy_metal world `barsoom` (ERB's Mars), GM content with Keith. Faithful = heroic sword-and-planet pulp (Frazetta), NOT grimdark — Keith twice corrected the instinct to refract it into heavy_metal's old elegiac-doom; that doom/pact-magic was flavor-leaking-into-rules and got PRUNED in the WWN port, so heavy_metal is now a clean WWN chassis and Barsoom sets its own flavor at the world tier.
- Locked design: (D1) PC origins = native Barsoomian cultures + transported-Earthman origin (gravity boon). (D2) Scope = whole planet (all 11 books). (D3) Magic = two WWN caster traditions — Lotharian Mentalist + Barsoomian Super-scientist on the inherited Effort/System-Strain engine; super-science also as gear; telepathy = universal narrator-framed baseline. (D4) multiple openings (solo/MP, per-origin), Helium default anchor. (D5) Earthman boon = world-tier origin trait, light mechanics — engine consumer MUST be verified (don't ship unwired crunch).
- Story 1 (world skeleton) DONE (content PR #363/#364), verified via the REAL loader (`load_genre_pack`, not validate-pack). 8 POIs rendered @28 steps (20-step grainy) on R2; POIs live under `history.yaml` chapters[].points_of_interest[] (NOT top-level). 6-story decomposition: 1 skeleton ✅, 2 the South, 3 North & Lothar, 4 magic content, 5 chargen surface (crunch flags resolve here with Keith), 6 assets.
- Gotchas (Stories 2-6): WorldLore `Faction` requires name+summary+description; Markov corpus needs ≥200 tokens (FAIL_BELOW_WORDS=200); genre `archetypes.yaml` is intentionally `[]`. FINDING (epic-87, not a Barsoom story): genre-tier `heavy_metal/archetype_constraints.yaml` doom labels leak into every heavy_metal world's namegen — needs the world-tier migration cultures/archetypes already got. Barsoom is invented sci-fi → conlang Markov is correct.

## beneath_sunden's deep is procedurally generated & unmapped BY DESIGN (2026-05-25, from Keith)
- beneath_sunden (caverns_and_claudes) authors NO dungeon map. `world.yaml` (8-12): "The DUNGEON IS NOT AUTHORED HERE. The deep is generated, unbounded, by the Sünden Deep procedural engine (Plans 5-7)." Cartography authors only two surface regions — `ropefoot` and `the_dropmouth`. Lore: "unmapped and unmappable by design."
- How to read the telemetry (do NOT re-file as a bug): on descent, `dungeon.map_emitted current=ropefoot discovered=0/6` staying unchanged, the Map showing "No locations explored yet," and the narrator improvising rooms are all CONSISTENT with intended design — there is no fixed room-graph that "should advance." `discovered=0/6` counts authored SURFACE nodes, not a failing deep. ADR-106 is still partial, so narrator-improv may be the intended interim.
- Keith corrected a wrong "procedural dungeon never materializes" high-priority bug filed here 2026-05-25. The only legitimate (softened) question is whether the Sünden Deep engine is expected to be live yet — a design question, not a code chase.

## caverns_sunden world is DEPRECATED in favor of beneath_sunden (2026-05-17)
- `caverns_and_claudes/worlds/caverns_sunden` (old three-sins hub: Grimvault/Horden/Mawdeep, Seven Deadly Sins, Keeper-of-sins) is deprecated; relocated to `sidequest-content/genre_workshopping/caverns_sunden/` — kept for salvage, NOT deleted. `beneath_sunden` (Moria-as-tragedy) is the canonical Sünden.
- Why: it was a lobby false positive (`sidequest-server rest.py list_genres` enumerates worlds by pure filesystem scan of `worlds/` — no content visibility flag exists); the only content-side removal is moving the dir out of that tree. An agent began rendering 25 portraits for it because tooling presented it as a live world.
- Apply: do NOT re-render its assets, re-add it under `worlds/`, or migrate its legacy save (`~/.sidequest/saves/caverns_and_claudes_caverns_sunden.db` — resuming fails loudly, which is correct). If asked to "fix" its missing-image gap, the answer is: deprecated, not under-rendered. beneath_sunden keeps prose-contrast/provenance comments referencing it as identity guardrails — intentional.

## Epic 114 inventory: ADR-145 supersedes the audit — all four WN SRDs are verbatim (2026-06-16)
- Licensing flipped: the 2026-06-14 audit said SWN/AWN "derive-only" / CWN "unverified"; ADR-145 D4 voids that — all four WN SRDs (WWN/CWN/SWN/AWN) reproduce VERBATIM under Sine Nomine free-use. Stamp `provenance: {mode: verbatim, srd: <wwn|cwn|swn|awn>, license: wn-free, srd_ref}`, NOT derived. `ItemProvenance` (server `genre/models/inventory.py`) enforces verbatim⇒wn-free. D4a (no implied Sine Nomine/Crawford endorsement), D4b (source bare SRD doc, never the commercial book). So 114-7 SWN / 114-10 / 114-12 assert verbatim, not "derive against schema".
- Foundation landed: 114-3 (schema delta), 114-11 (D3 non-droppable by-id merge in `dispatch/inventory_resolve.py:resolve_inventory` — world merges OVER genre), 114-4/114-5/114-2 done. 114-8's "power_glove regression" premise was stale (already fixed). 114-14 (D3 no-genre-bespoke validator, `loader._validate_genre_baseline_no_bespoke`, WN-family only, bespoke-only NOT verbatim-only) + 114-13 (road_warrior CWN weapon re-categorize in-place) DONE.
- World-replaces-genre kit trap (load-bearing): `resolve_inventory` merges `item_catalog` non-droppably BUT takes `starting_equipment`/`starting_gold`/`currency` from a world's inventory.yaml WHOLESALE — so creating `worlds/<w>/inventory.yaml` STOPS that world inheriting genre kits → empty loadouts unless it copies them. A genre kit must reference only genre-catalog ids.
- Weapon-category topology: strike-damage resolver `combat_rules.resolve_damage_spec_from_beat_and_actor` is category-AGNOSTIC (keys on `damage`/name) — re-categorizing weapons is safe, needs no strike change. Only sites keying on `category=="weapon"`: `builder.py:2484` (stub default) and `narration_apply._narrator_item_dict` items_gained allowlist (~4607, widened to accept melee/ranged + emits `inventory/narrator_item_category_coerced`). Real SRD PDFs: `~/Documents/DriveThruRPG/Sine Nomine Publishing/`; WWN/CWN have extraction CLIs (`sidequest/cli/{wwn,cwn}_equip_extract`), no AWN/SWN tool yet.

## Historical worlds name NPCs from curated real word lists, not conlang Markov (2026-06-01, from Keith)
- Keith's decision (during the_real_mccoy playtest): historically-grounded / real-Earth worlds must name NPCs from curated real period-name WORD LISTS sampled directly, NOT conlang Markov (ADR-091). Markov-from-corpus is built for invented cultures; for real ethnicities it produces non-names — "Gawainwen Boyer" (Welsh), "Arthonovan Bolan" / "Gilligan, Denis" (Irish), "Schrer, Hardina" (German).
- Apply: real-Earth/historical worlds → word lists: spaghetti_western (the_real_mccoy/five_points/dust_and_lead), tea_and_murder (blackthorn_moor/glenross), pulp_noir (annees_folles), neon_dystopia (franchise_nations). Invented cultures keep conlang Markov: caverns_and_claudes, elemental_harmony, space_opera, mutant_wasteland, road_warrior, heavy_metal.
- LANDED + VERIFIED: mechanism is the `names_file:` slot field (direct line-sampling, fires when a slot has `names_file:` and no `corpora:`). Content PRs #319 (spaghetti_western), #320 (pulp_noir annees_folles), #321 (neon_dystopia franchise_nations) converted every person-name slot. Pairs with engine #567 `named_individual: true` (excludes named people from random spawn). Residual cosmetic nits: apostrophe/nickname title-casing. Needs a content pull + server bounce to take effect.

## Every server-resolved combat outcome needs a MECHANICAL TRUTH next_turn_directive anchor (2026-06-10, playtest #800-#804)
- The narrator never sees server-rolled dice or HP mutations (dice messages go to the table, not the prompt), so EVERY mechanically-resolved outcome in `dispatch_dice_throw` needs a `snapshot.next_turn_directives` MECHANICAL TRUTH anchor. Each gap produced a distinct lie: player-beat resolution silence → narrated DEFEAT over a resolved player_victory; reprisal-miss silence → fabricated hit + false HP; non-killing-hit silence → kill prose at 3/10. "Engine right, prose wrong" bugs are anchor gaps, not narrator-prompt bugs — check the directive the path appends before touching prompts.
- Any new server-resolved combat seam must (1) append a MECHANICAL TRUTH directive, (2) persist the HP delta in the beat event (`opponent_hp_removed` total — `apply_beat_hp_channel` returns are easy to discard), (3) emit a watcher event + INFO log (live OTEL spans alone are grep-blind).
- WWN Shock chips on a MISS vs AC ≤ shock_ac (+ Warrior Killing Blow rider) can legitimately kill on a CritFail — forensics showing `opponent_hp_removed=0` + a resolution is the shock-blindness signature, NOT an inverted resolver. `advance_confrontation` now refuses hp_depletion dials; any nonzero `final_*_metric` in old hp_depletion saves is pre-#800 narrator drift.

## Gaslight the narrator with game state, never with appended text (2026-05-12, ADR-059)
- The narrator treats `<game_state>` (the JSON-dumped snapshot) as world truth. To stop it inventing untracked entities, materialize authored content into the snapshot BEFORE the turn so it believes those entities have always existed. Reference: `game/world_materialization.py` `preload_authored_npcs()` / `_apply_npc()` — authored YAML → typed model → upsert into `snap.npcs`. ADR-059 found "available NPCs list" XML tags and meta-instructions are ignored; only world facts in the structured snapshot fields land.
- How to apply: new encounter/creature/NPC/item subsystem → add typed entries to `snap.npcs`/`snap.adversaries`/`snap.inventory` (game-state patch). NEVER append "Hostile creatures in the area:" text to state_summary (the Rust `MonsterManual.format_area_creatures()` text-append was the WRONG pattern). HP-style stat blocks translate to ADR-014 edge/composure/momentum at materialization (runtime carries `CreatureCore.edge: EdgePool`, not `hp:int`). Lifecycle is patch-in/patch-out, not text. Emit an OTEL span at the patch point.

## Seaboard of Saints is content over AWN — "AWN wins always" (2026-06-09, from Keith)
- `mutant_wasteland/seaboard_of_saints` is a world/content layer over the AWN ruleset (`awn = AwnRulesetModule(CwnRulesetModule)`), NOT a genre-mechanics overhaul. Wherever Seaboard's original (2026-05-14) spec diverges from AWN, AWN is authoritative; Seaboard contributes flavor/geography/cosmology/factions/Saint content and ZERO divergent mechanics.
- The spec's homebrew chargen (7-step, Saint-Bundle mutation engine, Qud defects-for-power, flavor-six, Edge) was written for the native dial engine and is superseded. Read rebase addendum `docs/superpowers/specs/2026-06-09-seaboard-of-saints-awn-rebase-addendum.md`.
- Resolutions: flavor-six→standard six (D4); homebrew mutations→AWN MutationPlugin (D5); Edge→System Strain; native callings/Penitent survive only as flavor-foci over AWN classes; Saints = curated bundles of AWN mutation IDs + one AWN negative as drawback (not a parallel engine); `saints.yaml` lives, `mutations.yaml` dies. Gamma-World "defects-for-power" is already native AWN (§5.1 MP economy). flickering_reach stays Saint-less. Build order: Seaboard world plan slots AFTER AWN Plan 2 (Mutations).

## Playgroup mandate: reintroduce SWN-style crunch + ablative HP, supersedes ADRs (2026-05-25, from Sebastien+Jade via Keith)
- Direct playgroup request (mechanics-first Sebastien + Jade) to reintroduce mechanical crunch modeled on the Stars Without Number: Revised SRD. Three content lanes greenlit for `space_opera`: (A) richer gear/armor + SWN pharmacopeia/stims, (B) Tech-Level TL0–6 + Maltech spine, (C) chassis roster from SWN hull taxonomy + fittings.
- The big reversal: Keith authorized bringing back ablative HP and said "yes, this supersedes ADRs." Reverses ADR-078 (HP→Edge), reaches into ADR-040 (no raw stats), ADR-033 (dial confrontations), likely ADR-014. Needs new superseding ADR(s).
- Apply: HP never fully left — content YAML still carries B/X HP, discarded at the materializer seam, so restore = stop discarding, not rebuild. NOT space_opera-only — backport to beneath_sunden too (engine-level). Keep the narrative/dial layer (serves Alex/James); add ablative HP as the lethality substrate underneath, surfaced in player UI for mechanics-first players. Skip SWN's resolution math (d20-to-hit / 2d6 / saves) and encumbrance unless explicitly extended — adopt the HP/ablation lethality model, translate nouns/flavor.

## Reference-page theme.yaml is CSS styling (genre/app tier), not world flavor (2026-06-01, from Keith)
- `genre_packs/<pack>/theme.yaml` (palette/fonts/dinkus/archetype for the static reference Rules & Lore HTML, read by `load_reference_theme` in `reference_theme.py`) is CSS STYLING — neither Rules (mechanics) nor Lore (flavor). Keith: "this is neither Rules nor Lore, but CSS, so styling."
- Epic 74 ("genre = mechanics, flavor = world") tempts treating every genre-tier file as flavor to push to the world; theme.yaml is the trap. World aesthetic lives in per-world `visual_style.yaml` (image-gen positive_suffix); the reference CSS theme correctly stays genre/app tier.
- Do NOT repoint the reference renderer to a world theme.yaml, do NOT author per-world theme.yaml, and EXCLUDE theme.yaml from the epic-74 flavor-deletion pass (renderer hard-requires it via `MissingThemeFieldError` → every /reference/rules and /reference/lore 500s). Story 74-2 ("repoint flavor consumers to world tier") was a category error, cancelled 2026-06-01.

## Victoria genre is social-first, not combat-first (2026-04-26, from Keith)
- The `victoria` pack (Brontë/Austen/Henry James gothic drawing-room intrigue) is a social-mechanics game with little to no combat — no `category: combat` confrontations in rules.yaml (correctly skipped in the opposed-check migration). Stakes are social ruin, scandal, banishment, slow gothic undoing — not duels. It is a love-letter pack for Sonia (hard-to-engage player); the mechanical surface must fit the genre, not D&D.
- Apply: weight social/intrigue/atmosphere mechanics over combat; tropes about scandal, betrothal, will-readings, séances, locked-wing secrets. Lethality is `pc: defeated` (social collapse) / `npc: dying` (slow undoing), `permanent` reversibility, narration emphasizes "cold tea service, half-written letter, window left open to the moor" — not blood. When opposed-check/combat-balance changes land elsewhere, victoria likely needs different treatment or none. Don't pattern-match it off heavy_metal/spaghetti_western — closer to caverns_and_claudes in consequence shape, but consequences are social not comedic.

## Visual style is WORLD-level only — no genre/pack-level visual prompts (2026-05-29, from Keith, 64-12)
- Keith's directive: all visual prompts live at world level; NO genre/pack-level visual prompts. Implemented across 3 repos + schema: server `GenrePack.visual_style: VisualStyle|None=None` (loader.py:1134 `_load_yaml_optional`, only non-world consumer encountergen.py guarded, PR #526); daemon `StyleCatalog.load` skips an absent genre visual_style.yaml but still fails loud on present-but-empty `positive_suffix` (PR #95); content deleted `elemental_harmony/visual_style.yaml`, dropped it from genre-level `required_files` in pack_schema.yaml (world-level still requires it — worlds are self-contained, PRs #301/#302).
- Filing gotcha: this looks server-only but the daemon hard-requires the genre `positive_suffix` independently — a server-only change is a no-op. Any "move X from genre to world level" touches BOTH loaders + pack_schema. Safe because every recipe cascade is [GENRE, WORLD, CULTURE] and the composer skips GENRE whenever WORLD style is present (`prompt_composer.py:515`).
- Still stale (separate epic-64 cleanup): pack_schema.yaml requires `assets/images/portraits`/`poi` dirs but real layout is `assets/portraits`/`poi` (world-level) — perennial baseline failures in `test_all_live_packs_pass_content_validation`/`_crossref`.

## Random-dungeon theme eligibility (Keith, 2026-06-24, story 158-19)
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

## Theme-variety targets + encounter ownership (Keith, 2026-06-24, story 158-19)
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

## sunless_temple re-themed built→labyrinthine (Keith, 2026-06-24, story 158-19)
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

## Creature portraits derive from the bestiary — per-world creatures.yaml is a duplication smell (Keith, 2026-07-01, story 158-52)
- **Trigger:** a content-completeness test (`test_beneath_sunden_creature_images_107_2.py::test_every_low_tagged_bestiary_entry_is_renderable`) demanded a `creatures.yaml` image spec for all 48 `low`-tagged bestiary entries — 42 missing. On the surface: "author 42 plates." Reflex before authoring: check whether the data already lives elsewhere.
- **Why it's a smell:** for WN-bound packs the RUNTIME roster is `bestiary.yaml` (encountergen samples it); `creatures.yaml` is NOT a runtime source on the WN path — it's purely the offline image manifest for `scripts/generate_creature_images.py`. That script needs only name/description/threat_level/id, and the bestiary already carries name, description, and level (→threat is trivial). So `creatures.yaml`'s ONLY load-bearing add is a **non-proper-noun CLIP name** for "nothing is named" worlds (beneath_sunden) — Z-Image would otherwise paint "Constrictor Snake" as a caption. Style already auto-layers from each world's `visual_style.yaml positive_suffix`. Net: `creatures.yaml` duplicates prose the bestiary already has. Only 2 of 22 WN worlds even have one.
- **Decision:** do NOT hand-author (~900 plates across 22 worlds does not scale, and would be throwaway). Make the **bestiary the single source of truth**; the render pipeline DERIVES the prompt; `creatures.yaml` demotes to an OPTIONAL per-world naming-override. Filed as story **158-52** (ADR + render-pipeline + test-invariant retune — Architect/Dev, not GM content).
- **Standing rule (GM audit reflex):** when a test demands per-world hand-authored manifests, first ask "does a sibling file already hold this data, and can the pipeline derive from it?" Duplicated creative prose across two files (bestiary description ↔ creatures.yaml description) is the tell. The fix to a content-completeness failure is often **pipeline-derivation (code, file it), not content authoring** — authoring would bury the smell under 900 plates. Content lane produces the diagnosis + the story; it does not grind the duplication.
