# Epic 122: Honest Layering — pure logic & utilities below the server tier

## Overview

Corrects a set of **layering-inversion edges** in `sidequest-server`: low-level domain
and utility code that imports *up* into `sidequest/server`. The fix is relocation, not
redesign — pure helpers and pure combat-rules logic move down to the tier their own
dependencies dictate, a new `foundation/` floor is established, and a CI guard enforces
the import-direction law so the inversion cannot return. This is a behavior-preserving
refactor; **no library extraction** and **no new subsystem** are introduced. Implements
ADR-147.

**Priority:** P2
**Repo:** server (`sidequest-server`, gitflow → base `develop`)
**Stories:** 5 (13 points)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **ADR-147 — Honest Layering** (`docs/adr/147-honest-layering-pure-logic-below-server.md`) | *The law*, *The moves*, *Enforcement*, *Non-Goals*, *Implementation Plan* — the authoritative design for this epic |
| **ADR-063 — Dispatch Handler Splitting** (`docs/adr/063-dispatch-handler-splitting.md`) | Established `server/dispatch/`; story 122-2 partially reverses where the *pure-rules* helpers landed (the handler-stage split itself stands) |
| **ADR-117 — Pluggable Ruleset Module System** (`docs/adr/117-pluggable-ruleset-module-system.md`) | `RulesetModule` seam; the rulesets are the consumers reaching up for combat-rules helpers in 122-2 |
| **ADR-142 — Without Number Core Extraction** (`docs/adr/142-without-number-core-extraction.md`) | `game/ruleset/` family that receives the relocated helpers |
| **ADR-131 — Daemon↔Server OOB Contracts** (`docs/adr/131-daemon-server-oob-contracts.md`) | Adjacent layering concern; the *library*-extraction question (declined) is tracked separately, not here |

## Background

### Why this epic exists

A 2026-06-15 coupling audit of `sidequest-server/sidequest/` confirmed the **bulk
dependency flow is correct**: `server/` imports `game/` 65 times across 51 files, and
`game/` knows almost nothing of `server/`. The audit also confirmed three things that
*look* like coupling problems but are healthy and are **explicitly out of scope**:

- `handlers ↔ server` is **not a cycle** — a deliberate lazy-registry seam
  (`server/websocket_session_handler._message_handler_for()` imports handler singletons
  at first dispatch, never at class-definition time).
- `protocol` imported by 110 files is **healthy fan-in** — pure types are meant to be
  widely depended-upon.
- `Session` is **not a god-object** — a deliberately thin 212-LOC strangler-fig
  (5 attributes). The actual central state object is `GameSnapshot` (2,098 LOC, 102
  consumers), which is the canonical save model.

What the audit *did* surface is a small number of **wrong-direction edges**: pure logic
filed too high. Each was traced to its exact import and usage. Five of the six edges are
the same defect — a pure function (and in the worst case, pure *combat rules*) sits under
`server/`, forcing the layers beneath to import upward to reach it.

### The smell that proves it

`game/ruleset/native.py` and `game/ruleset/without_number.py` use **lazy in-method
imports** of `server.dispatch` specifically to dodge circular-import errors at module
load; `game/projection/validator.py` does the same with `server.session_handler`. When
the architecture must use import tricks to avoid eating itself, the tier boundaries are
lying about where the code belongs. This traces to the port history (ADR-082): the
Rust→Python cutover was a 1:1 port that forbade structural refactors, so files landed
wherever their Rust ancestor sat and never moved.

### The edges being corrected

| Importer (lower tier) | Target under `server/` | What is imported | Genuinely server-tier? |
|---|---|---|---|
| `game/ruleset/native.py`, `…/without_number.py` | `server.dispatch.confrontation.find_confrontation_def`, `server.dispatch.damage_roll.resolve_damage_spec_from_beat_and_actor` | **Pure combat-rules logic** | **No** — code comment admits "historical accident" |
| `genre/audio_paths.py`, `game/room_file_loader.py` | `server.asset_urls.resolve_asset_url` | string + `os.environ` + one OTEL span | **No** — pure |
| `game/alias_resolution.py` | `server.slug_fold.fold_to_ascii` | NFKD normalization | **No** — pure |
| `game/builder.py`, `game/cookbook/compose.py` | `server.reference_anchors.{reference_url_for_ability,build_lore_url}` | URL builders | **No** — pure |
| `interior/dispatch.py` | `fastapi` (`APIRouter`/`HTTPException`) | one REST endpoint | Yes, but isolated to 1 of 4 files |
| `orbital/intent.py` | `server.session.Session` | whole `Session`, uses only 4 read-only props + `_snapshot.plotted_course` | Genuine read, but **over-coupled** |

## Technical Architecture

### The law (enforced)

> **Imports flow downward only: `foundation ← {game, genre, orbital, magic, interior} ← server`.**
> Domain and utility code MUST NOT import from `sidequest.server`. A unit belongs in the
> lowest tier its own dependencies permit — not the tier that first needed it.

`server/` may import anything below it. The domain layer may import `foundation/` and
`protocol/`. The `foundation/` floor imports only third-party libs and `protocol/`.

### Story → move mapping

```
122-1  Foundation floor          server/asset_urls.py, server/slug_fold.py,
       (kills 4 edges)           server/reference_anchors.py  ──►  sidequest/foundation/
                                 update importers: genre/audio_paths, game/room_file_loader,
                                 game/alias_resolution, game/builder, game/cookbook/compose

122-2  Rules relocation          server/dispatch/confrontation.find_confrontation_def,
       (highest value/risk)      server/dispatch/damage_roll.resolve_damage_spec_from_beat_and_actor
                                 ──►  game/ruleset/ (sibling of base.py)
                                 DELETE the lazy in-method imports in native.py / without_number.py
                                 NB: partial reversal of ADR-063 placement; the handler-stage
                                 split itself is untouched

122-3  Interior lift            interior/dispatch.py APIRouter + endpoint ──► server/rest.py
                                 interior/loader.py + interior/render.py already pure → stay
                                 Result: interior/ has zero FastAPI imports

122-4  Orbital narrowing        orbital/intent.py: replace `Session` import with a Protocol
                                 exposing only orbital_content, orbital_scope, clock.t_hours,
                                 party_body_id, + plotted_course. server/ constructs & passes it.
                                 (the one step that is design work, not relocation)

122-5  CI guard                 tests/ AST/grep test: FAIL if any module under
       (lands last, enforcing)  foundation|game|genre|orbital|magic|interior imports
                                 sidequest.server. ~20 lines, no import-linter dependency.
```

### Key files

| File | Role in this epic |
|------|-------------------|
| `sidequest/foundation/` (new) | The utility floor — destination for the three pure helpers (122-1) |
| `sidequest/server/asset_urls.py`, `slug_fold.py`, `reference_anchors.py` | Sources moved down in 122-1 |
| `sidequest/server/dispatch/confrontation.py`, `dispatch/damage_roll.py` | Pure-rules helpers moved to `game/ruleset/` in 122-2 |
| `sidequest/game/ruleset/native.py`, `without_number.py` | Lose their lazy server imports in 122-2 |
| `sidequest/interior/dispatch.py` → `sidequest/server/rest.py` | Endpoint lifted in 122-3 |
| `sidequest/orbital/intent.py` | Narrowed to a Protocol in 122-4 |
| `tests/` (new guard test) | The enforcement spine added in 122-5 |

### Sequencing & enforcement contract

Each step is **independently shippable**; the five stories touch largely disjoint files
and do not require a hard `depends_on` chain (server is gitflow, not stacked — a
dependency chain would only risk false-failing the validator). Ordering is doctrinal,
not mechanical: **122-5 (the guard) lands last and enforcing**, locking in 122-1..4. If a
move story slips, the guard will correctly fail by surfacing the remaining violation. The
guard is also the **wiring test** for layer direction (satisfies the project "every test
suite needs a wiring test" rule). Behavior is unchanged end-to-end — the existing test
suite should pass before and after each story, with diffs limited to import paths and (in
122-4) one call signature.

## Cross-Epic Dependencies

**Depends on:**
- None in-flight. The receiving tier `game/ruleset/` already exists (ADR-142, shipped).

**Depended on by:**
- None blocking. This epic *unblocks* future clean reasoning about the domain layer
  (and de-risks any later library-extraction question) but no current epic waits on it.

**Related but out of scope:**
- The daemon↔server **contract library** (ADR-131-adjacent) was weighed in the same
  2026-06-15 investigation and declined for now — tracked separately, not part of 122.
- The `Session`/`GameSnapshot` strangler-fig migration continues on its own track;
  122-4 narrows one *consumer* of `Session` but does not alter `Session` itself.
