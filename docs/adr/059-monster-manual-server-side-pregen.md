---
id: 59
title: "Monster Manual — Server-Side Pre-Generation via Game-State Injection"
status: accepted
date: 2026-04-03
deciders: [Keith]
supersedes: [56]
superseded-by: null
related: [1, 3, 7, 20]
tags: [code-generation, agent-system]
implementation-status: live
implementation-pointer: null
---

# ADR-059: Monster Manual — Server-Side Pre-Generation via Game-State Injection

## Context

ADR-056 introduced Rust tool binaries (namegen, encountergen, loadoutgen) that the
narrator would call via `claude -p --allowedTools Bash(...)`. After 6+ iterations
(prompt zones, wrapper scripts, env vars, mandatory workflows, casting calls, XML
audition tags), Claude (Sonnet) in single-prompt print mode consistently ignores
tool-calling instructions and writes prose directly.

**Root cause:** `claude -p` is a prose generation task. Tool calling is an interruption
Claude can skip because it can fulfill the request entirely in prose. No amount of
prompt engineering changes this fundamental incentive — proven empirically across
Primacy, Early, Valley, and Recency attention zones.

**Key discovery:** Claude DOES absorb data from the prompt — proven by umlaut
generation matching conlang corpus patterns. It reads the NPC data and generates
names *in the style of* the pool, but invents rather than selects. The data is
reaching Claude; the constraint framing fails.

## Decision

**Embed pre-generated content directly in `<game_state>` as world facts.**

Claude treats `<game_state>` as ground truth — the authoritative description of
the game world. NPCs listed there are used naturally with correct names, dialogue
quirks, and behavioral traits. Enemies listed there are referenced with exact names,
abilities, and attack patterns.

No special XML sections. No meta-instructions. No casting calls. World data in the
world data section.

### The Monster Manual

A persistent JSON file at `~/.sidequest/manuals/{genre}_{world}.json` containing
pre-generated NPCs and encounter blocks. Full stat blocks stored, indexed by
compound key `(name, faction, world)`.

Seeded on first session start by calling tool binaries server-side for each faction
in the genre pack. Grows over play sessions — every generated entry persists.

### Game-State Injection (the validated pattern)

The Monster Manual's formatting methods append to the `state_summary` string that
becomes the `<game_state>` prompt section:

```
NPCs nearby (not yet met by player):
  - Joch Glowvein (wasteland trader, Scrapborn) — blunt, quotes prices in three barter systems
  - Seven Jewsa (village elder, Vaultborn) — reserved, pauses mid-sentence as if buffering

Hostile creatures in the area:
  - Salt Burrower (tier 2, HP 14) — eyeless ambush predator, chitin mandibles
    Abilities: Burrow Ambush, Mandible Crush. Weakness: bright light, fire.
```

The prompt stays lean (~100-200 extra tokens). Full mechanical data (OCEAN profiles,
stat ranges, trope connections) stays in the Manual backend, never in the prompt.

### Two-Tier Data Flow

1. **Prompt** gets names + roles + brief personality/speech quirks
2. **Post-narration gate** matches used names against Manual via compound key lookup
3. **NPC registry** enriched with full stat block from Manual — same gate, same OTEL

### Compound Key

`(name, faction, world)` — because the same name could exist in different factions
or worlds. Lookup is a hash map operation, not string matching on prose.

### Entry Schema

Each entry carries tags for future filtering even if filtering isn't implemented yet:

```rust
pub struct ManualNpc {
    pub data: serde_json::Value,     // full namegen output
    pub name: String,
    pub role: String,
    pub culture: String,
    pub location_tags: Vec<String>,  // biome/terrain for future filtering
    pub state: EntryState,           // Available, Active, Dormant
}
```

### Lifecycle

- **Available** — pre-generated, not yet used in narration
- **Active** — narrator introduced them, in current scene
- **Dormant** — used previously, can return

Transitions: session start seeds → narrator uses name → mark Active → location
change → mark Dormant → seed new batch.

### Bottle Episode Compatibility

Bottle episodes (fixed NPC cast for a scene/quest) use the same pattern. The cast
list IS the "NPCs nearby" section. The Manual serves both open-world exploration
and tightly scripted scenarios.

### What Gets Removed

- `--allowedTools Bash` from Claude CLI invocations
- All tool prompt sections (`<tool_workflow>`, `<casting_call>`, `<on_set>`, `<available_characters>`)
- Sidecar JSONL mechanism (tool_call_parser, sidecar env vars)
- `script_tools` HashMap on Orchestrator
- `register_script_tool()` and wrapper script infrastructure

### What Stays

- Tool binaries (namegen, encountergen, loadoutgen) — called by server, not Claude
- Post-narration NPC gate — validates names, enriches from Manual
- Binary path discovery — paths move to AppState

## Empirical Validation

Tested via `scripts/preview-prompt.py --test` against `claude -p`:

| Approach | Zone | Result |
|----------|------|--------|
| `<tool_workflow>` mandatory steps | Primacy | Zero tool calls across 30+ turns |
| `<available_characters>` list | Early | Claude invents names, ignores list |
| `<casting_call>` audition XML | Early | Claude absorbs style (umlauts!), still invents |
| `<on_set>` actors-on-set framing | Recency | Claude invents, absorbs style |
| **`<game_state>` "NPCs nearby"** | **Valley** | **Claude uses exact names + dialogue quirks + behavior** |
| **`<game_state>` "Hostile creatures"** | **Valley** | **Claude uses exact enemy names + abilities** |

The winning approach places data in the lowest-attention zone. The key is not
attention priority — it's **framing**. Claude treats `<game_state>` as world truth
and meta-instruction sections as advisory.

## Consequences

### Positive

- **Reliable.** Claude uses game_state NPCs naturally — validated empirically.
- **No special framing.** No XML tags, no meta-instructions. Just world facts.
- **Persistent.** Monster Manual grows over sessions. Rich worlds accumulate.
- **Prompt-efficient.** ~100-200 tokens for the pool section.
- **Compatible.** Works with bottle episodes, open-world, multiplayer.
- **Deterministic lookup.** Compound key → full stat block. No string matching.
- **GM prep metaphor.** Pre-roll NPCs before session, pull from deck during play.

### Negative

- **Speculative generation.** Some entries may never be used. Cost: ~50-100ms per
  binary call, negligible vs 3-10s Claude calls.
- **Narrator may still invent.** Game_state embedding works reliably but isn't
  deterministic. Post-narration gate catches inventions and falls back to namegen.
- **Disk I/O.** Manual file read/write per session. Small JSON, not a concern.

### Neutral

- Tool binary sidecar JSONL code becomes dead code. Harmless.
- ADR-056's binaries remain the foundation; only the invocation model changes.
- ADR-057's narrator-crunch separation principle is validated but the mechanism
  is game-state injection, not tool calls.

## Alternatives Considered

### A: Narrator calls tools via --allowedTools (Rejected — ADR-056)
Six iterations failed. Fundamental incentive mismatch in `claude -p` mode.

### B: XML casting/audition sections (Rejected)
Claude absorbs style but invents instead of selecting. Proven by umlaut generation
— data reaches Claude, constraint framing fails.

### C: Meta-instruction constraints ("HARD RULE", "MUST NOT invent") (Rejected)
Claude treats these as advisory. Constraint escalation doesn't change behavior.

### D: Game-state embedding (Accepted)
Claude treats `<game_state>` as world truth. Names, abilities, and dialogue quirks
used correctly on first test. The simplest approach that works.

## Implementation status (2026-05-02)

The Rust era implemented this ADR end-to-end (Manual store + namegen/encountergen/loadoutgen called server-side at turn time + compound-key lookup + post-narration enrichment gate). The 2026-04 port to Python carried the **injection mechanism** but not the **content pipeline** behind it.

What is live:

- The `<game_state>` injection mechanism. `sidequest/agents/orchestrator.py` wraps `state_summary` in `<game_state>` tags and places it in the validated Valley zone.
- OTEL span definitions for `monster_manual` and `pregen` (`sidequest/telemetry/spans/monster_manual.py`, `…/pregen.py`).

What is dark — the Manual + the pipeline that fills `<game_state>` with pre-generated content:

- `MonsterManual` class — zero references in production paths. The persistent JSON file at `~/.sidequest/manuals/{genre}_{world}.json` is never created.
- First-session seeding code that calls tool binaries to populate the Manual — absent.
- `sidequest/cli/encountergen/__init__.py` and `sidequest/cli/loadoutgen/__init__.py` are **1-line empty stubs**. (`namegen` is the exception — it has 22K LOC of working code, but is not registered as a `[project.scripts]` entry and the server does not invoke it.)
- Compound-key `(name, faction, world)` lookup — absent.
- Post-narration NPC gate that matches used names against the Manual and enriches the registry from stat blocks — absent.

What `<game_state>` carries today is the running session snapshot only (`orchestrator.py`: `state_summary = session.model_dump_json(...)`). There is no pre-generated NPC pool, no encounter pool, no enemy stat-block pool being merged in. The narrator therefore continues to invent NPC names and stats — exactly the failure mode this ADR was written to prevent.

Restoration is **P0 RESTORE** in [ADR-087](087-post-port-subsystem-restoration-plan.md) — the highest-priority single item across the entire restoration plan: _"Single biggest hot item. Accepted ADR is currently dark. Without this, NPC names/encounters/loadouts drift into Claude's improvisation."_ ADR-087 also schedules the encountergen/loadoutgen binary RESTORE and the namegen REWIRE as P0 prerequisites in §E. The decision in this ADR stands.

## Correction (2026-07-05, NPC-generation architecture survey) — the 2026-05-02 status section above is STALE

The "What is dark" list above described the state before restoration. It has since
landed (the P0 RESTORE this ADR called for is done) and the section above is now
**wrong on every point except one**. Verified against the current tree line-by-line:

- **`MonsterManual` class — no longer "zero references."** `server/dispatch/monster_manual_inject.py`'s
  `ensure_loaded()`/`inject()` run from `server/websocket_session_handler.py`
  unconditionally in the per-turn flow (~L835-865), with the post-narration gate
  (`mark_all_dormant`/`mark_active_from_narration`) called at ~L1369-1370. The
  `~/.sidequest/manuals/{genre}_{world}.json` file **is** created and grows — 34
  manual files exist on disk as of 2026-07-05, several exceeding 1000 NPCs. Runtime
  evidence: `monster_manual.injected` appears **1158 times** across
  `~/.sidequest/logs/sidequest-server.log*`.
- **First-session seeding code exists.** `server/dispatch/pregen.py:seed_manual`
  (~L326) invokes `namegen`/`encountergen` in-process (imported as
  `namegen_main`/`encountergen_main`) to populate NPCs (3 per culture) and
  encounter blocks whenever `manual.needs_seeding()`.
- **`sidequest/cli/encountergen/__init__.py` is still a 1-line docstring, but that's
  not where the implementation lives.** `sidequest/cli/encountergen/encountergen.py`
  is a real, 836-line implementation (`generate_enemy_from_bestiary` at line 356,
  `main` at line 775) and is exactly what `pregen.seed_manual` calls. The "1-line
  empty stub" framing was misleading for encountergen even read charitably — the
  logic was never in `__init__.py`.
- **`namegen` is wired, just not as a registered console script.** `namegen.py`
  (764 LOC) is still absent from `pyproject.toml`'s `[project.scripts]` (only
  `sidequest-server` is registered) — that half of the old claim holds — but
  "the server does not invoke it" no longer holds: `pregen.py` imports and calls
  `namegen.main()` in-process on every seed pass.
- **`sidequest/cli/loadoutgen/__init__.py` is still genuinely a 1-line placeholder
  stub** ("Placeholder — populated in later phases per ADR-082 port plan.") **and
  is still unwired** — confirmed zero non-test callers anywhere in `sidequest/`.
  `agents/tools/generate_loadout.py` explicitly documents this and returns a fatal,
  non-recoverable `ToolResult` with `tool.loadout.loadoutgen_wired=False` rather
  than confabulate. This is the one part of the original "what is dark" list that
  is still accurate today.
- **Compound-key lookup and the post-narration NPC gate both exist.**
  `MonsterManual.find_npc_by_name`/`find_npc_by_exact_name`/`find_enemy_by_name`
  (`game/monster_manual.py`) provide the lookup; `mark_active_from_narration`
  (`monster_manual_inject.py:816`) is the post-narration gate that scans narration
  text for Available Manual NPC names and flips them Active.

**What remains true:** loadoutgen only. Everything else in the "what is dark"
section has been restored. `<game_state>` today carries a real pre-generated NPC
pool, encounter pool, and (per the 2026-07-02 addendum below) bestiary-derived
creature pool — not just the running session snapshot. Do not cite the 2026-05-02
section's "MonsterManual — zero references" / "namegen … the server does not
invoke it" / "absent" claims (NPCs, encounters, compound-key lookup, post-narration
gate) as current; cite this correction instead. Verified by direct code read
(`websocket_session_handler.py`, `pregen.py`, `encountergen.py`, `namegen.py`,
`monster_manual.py`, `monster_manual_inject.py`, `generate_loadout.py`,
`pyproject.toml`) plus a log grep for `monster_manual.injected` count.

## Amendment (2026-06-20) — Faction/zone-scoped content eligibility (epic-157)

The entry schema above carried `location_tags` *"for future filtering even if filtering
isn't implemented yet"* (see "Entry Schema"). That future filtering is now specified, on
the **faction** axis, by epic-157. Full design:
[`docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md`](../superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md).

**Problem this amends.** The Manual is region-unaware. `monster_manual_inject._npc_patches_for_encounters()`
applies **zero** location filtering, so a sampled bestiary creature is eligible
everywhere — a 4th-voyage gulliver **Yahoo** surfaces on the 1st-voyage **Lilliput shore**
(playtest `2026-06-20-gulliver-e721409c`). The same lack of a region axis exists in the
trope engine and the seed-trope deck.

**Decision.** Content eligibility is scoped by the **faction-group** that controls the
party's current region (Keith, 2026-06-20: "group locations by faction; scope
content-eligibility by the region's faction-group"). The eligibility key is the
**already-authored `Region.controlled_by`** — no new cartography authoring; it is present
in exactly the multi-region worlds with the bleed (gulliver/oz/wonderland/the_circuit/
perseus_cloud) and absent in the 11 single-zone worlds, which are therefore unaffected.

- **Tag** the three pooled, home-less content types — bestiary entries, tropes,
  seed-tropes — with `factions: list[str]` (exact `controlled_by` values, or `"*"` for
  world-global). Authored cartography NPCs (region = zone) and runtime generated walk-ons
  (stamped on activation) are **not** tagged; their zone is derived.
- **Filter** at four seams against one shared predicate
  (`game/zone_eligibility.py`): creature/encounter injection (Seam 1, the headline fix),
  generated-walk-on origin-stamp + **authored-cast push-staging on region entry** via the
  ADR-113 `frontier_hook` observer registry's first real consumer (Seam 2), the trope
  activation gate (Seam 3), and the seed-deck draw (Seam 4).
- **Runtime is permissive** on untagged content; **strictness is a load-time validator**
  (`GenreLoadError` for any untagged/typo'd pooled item in a zoned world). This decouples
  sequencing (engine ships before content tagging) while guaranteeing no untagged content
  reaches production. The validator lands **last**, after all zoned worlds are tagged.
- **OTEL.** Persisted `zone_eligibility.filtered` (exclusions) + `zone_eligibility.cast_staged`
  (region-entry staging) watcher events — the GM-panel lie-detector.

The compound-key culture/faction axis and the injection mechanism in the body above are
unchanged; this amendment adds the region→faction eligibility filter that the entry schema
anticipated. The decision in this ADR stands.

## Addendum (2026-07-02, Story 158-52): the bestiary is the single source of truth for creature-image production

**Context.** The Monster Manual roster this ADR pre-generates is `bestiary.yaml` — the
Without-Number-path roster `encountergen` samples (`creatures.yaml` is *not* a runtime
source on the WN path). But the creature-image renderer
(`scripts/generate_creature_images.py::collect_creatures`) only ever rglobbed
`creatures.yaml`, so creature portraits rendered for exactly **2 of 22** WN-bound worlds
(`beneath_sunden`, `flickering_reach`) — the only two that shipped a hand-authored image
manifest. Every other world had a full bestiary roster and **zero** renderable creatures.
Hand-authoring per-world image manifests (~900 plates across 22 worlds) does not scale
(Keith, 2026-07-01: "something is missing — make the bestiary the source of truth").

**Decision.** `bestiary.yaml` is the **single source of truth for creature-image
production**. `collect_creatures` derives a render creature from each bestiary entry —
`{id, name, description, threat_level ← level, tags}` — with the shipped map
`threat_level = max(1, ceil(level / 2))` (ADR-155). A per-world `creatures.yaml` is demoted to an
**OPTIONAL per-field override** (ADR-121 flavor): where it declares a field for a shared
`id`, that field wins; otherwise the bestiary value stands. This is why portraits now
scale past the two hand-authored worlds — a world needs only its bestiary to become
renderable.

**Naming conceits.** A "nothing is named" world (`beneath_sunden`) would otherwise send a
bestiary proper noun (`"Constrictor Snake"`) into the rendered prompt, which Z-Image
paints as a caption. The decision: a render-only `name_is_secret: true` flag in that
world's `creatures.yaml` declares the conceit and keeps roster proper nouns out of the
rendered prompt; see ADR-155 for the shipped mechanism (the derived name is replaced with
the bestiary entry's `role` line, with per-id override names still winning). The flag
lives in `creatures.yaml` (a render manifest, read only by the render
script and ignored by `encountergen`) — **not** in `bestiary.yaml`, whose server-side
`Bestiary` pydantic model is `extra="forbid"`. **No engine-code change**: this is a
render-pipeline + content change only, consistent with "authoring must handle homebrew
without touching engine code."

**Scope.** This addendum covers creature-image *production* (deriving the render prompt).
It does not add the runtime creature-image *resolver* (server/UI portrait lookup), which
remains ADR-087 P0 debt — rendering more plates does not by itself make them appear
in-play. The decision in this ADR stands.

The authoritative record for creature-image derivation is ADR-155
(`docs/adr/155-bestiary-derived-creature-images.md`).
