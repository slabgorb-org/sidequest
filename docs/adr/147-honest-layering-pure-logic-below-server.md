---
id: 147
title: "Honest Layering — Pure Logic and Utilities Belong Below the Server Tier, Not Inside It"
status: proposed
date: 2026-06-15
deciders: ["Keith Avery", "Atlas (Architect)"]
supersedes: []
superseded-by: null
related: [63, 64, 82, 117, 131, 142]
tags: [codebase-decomposition]
implementation-status: deferred
implementation-pointer: null
---

# ADR-147: Honest Layering — Pure Logic and Utilities Belong Below the Server Tier, Not Inside It

> This ADR records a **layering-correction decision**, not a library extraction. A
> companion investigation (2026-06-15) weighed splitting `sidequest-server`
> subpackages into standalone libraries and concluded the squeeze was not worth it
> — the only cross-repo duplication worth a package is the daemon↔server contract,
> tracked separately. What the investigation *did* surface is a real architectural
> defect independent of any packaging question: several low-level packages import
> **up** into `server/`. This ADR addresses that defect by moving the misfiled code
> down, not by rewriting dependencies.

## Context

SideQuest's package tiers are intended to flow one direction: `server/` (FastAPI,
WebSocket, session orchestration) sits at the top and orchestrates the domain
layer (`game/`, `genre/`, `orbital/`, `magic/`, `interior/`), which in turn rests
on pure types (`protocol/`). A coupling audit of `sidequest-server/sidequest/`
confirmed the **bulk flow is correct** — `server/` imports `game/` 65 times across
51 files; `game/` knows almost nothing of `server/`. Three things initially
flagged as coupling problems are in fact healthy and are explicitly **out of scope**:

- **`handlers ↔ server` is not a cycle.** Handlers are stateless `Protocol`
  objects; `server/websocket_session_handler.py` imports them lazily inside
  `_message_handler_for()` at first dispatch, never at class-definition time. A
  deliberate, documented registration seam. Leave it.
- **`protocol` imported by 110 files is healthy fan-in.** Pure types are *supposed*
  to be widely depended-upon.
- **`Session` is not a god-object.** It is a deliberately thin 212-LOC
  strangler-fig (5 attributes), owning only orbital-clock and scene-end. The actual
  central state object is `GameSnapshot` (2,098 LOC, 102 consumers) — but that is
  the canonical save model, and being widely *read* is its job.

### The presenting defect

A small number of **wrong-direction edges** remain: low-level domain and utility
code reaching up into `server/`. Each one was traced to its exact import and usage:

| Importer (lower tier) | Target under `server/` | What is actually imported | Genuinely server-tier? |
|---|---|---|---|
| `game/ruleset/native.py`, `game/ruleset/without_number.py` | `server.dispatch.confrontation.find_confrontation_def`, `server.dispatch.damage_roll.resolve_damage_spec_from_beat_and_actor` | **Pure combat-rules logic** | **No** — the code comment in `native.py` admits these "happen to live under `server.dispatch` by historical accident" |
| `genre/audio_paths.py`, `game/room_file_loader.py` | `server.asset_urls.resolve_asset_url` | String + `os.environ` read + one OTEL span | **No** — pure |
| `game/alias_resolution.py` | `server.slug_fold.fold_to_ascii` | NFKD text normalization | **No** — pure |
| `game/builder.py`, `game/cookbook/compose.py` | `server.reference_anchors.{reference_url_for_ability,build_lore_url}` | URL builders | **No** — pure |
| `interior/dispatch.py` | `fastapi` (`APIRouter`, `HTTPException`, `Request`, `Response`) | One REST endpoint | Yes, but isolated to 1 of 4 files |
| `orbital/intent.py` | `server.session.Session` | The whole `Session`, but uses only 4 read-only properties + `_snapshot.plotted_course` | Genuine state read, but **over-coupled** |

### The diagnosis

Five of the six edges are **the same defect: pure logic filed too high.** Nothing
in them depends on FastAPI, the request, the socket, or live session behaviour —
they are pure functions (and, in the worst case, pure *combat rules*) that merely
happen to sit under `server/`, forcing the layers beneath to import upward to
reach them.

The smell that proves the layering is dishonest: `native.py` and
`without_number.py` use **lazy in-method imports** of `server.dispatch`
specifically to dodge circular-import errors at module load. `projection/validator.py`
does the same with `server.session_handler`. **When the architecture has to use
import tricks to avoid eating itself, the tier boundaries are lying about where the
code belongs.**

This is consistent with the port history (ADR-082): the Rust→Python cutover was a
1:1 port that forbade structural refactors, so files landed wherever their Rust
ancestor sat. Some pure helpers and rules logic came to rest under the server
crate's descendants and never moved.

## Decision

**Adopt one layering law and execute the file moves that make the codebase obey it.
No new subsystem is invented; existing code relocates to the tier its dependencies
already dictate.**

### The law

> **Imports flow downward only: `foundation ← {game, genre, orbital, magic, interior} ← server`.
> Domain and utility code MUST NOT import from `server/`. A unit belongs in the
> lowest tier its own dependencies permit — not the tier that first needed it.**

`server/` may import anything below it. The domain layer may import the foundation
floor and `protocol/`. The foundation floor imports only third-party libraries and
`protocol/`. Nothing imports upward.

### The moves

1. **Relocate the pure combat-rules logic out of `server/dispatch/`.** Move
   `find_confrontation_def` and `resolve_damage_spec_from_beat_and_actor` (and any
   sibling pure-resolution helpers they pull in) into the **game tier** —
   `game/ruleset/` alongside `base.py`, or a sibling `game/` module; Dev confirms
   the exact module. This is the highest-value move: it puts core combat resolution
   in the domain layer where the rulesets that consume it live, and **deletes the
   lazy-import workarounds** on the combat path. (Note: this is a *partial* reversal
   of where ADR-063's dispatch-splitting placed these functions — ADR-063's
   handler-stage split stands; only the misfiled pure-rules helpers move down.)

2. **Establish a foundation floor** — a new `sidequest/foundation/` package (pure
   helpers, dependencies limited to third-party + `protocol/`) — and move
   `resolve_asset_url`, `fold_to_ascii`, and the `reference_anchors` URL builders
   into it. This single move erases four upward edges at once. The OTEL span emitted
   by `resolve_asset_url` is retained (the watcher API is itself a foundation-level
   concern, ADR-132); it does not couple to the server.

3. **Lift the interior HTTP endpoint up.** Move the `interior/dispatch.py`
   `APIRouter` and its endpoint to `server/rest.py` (where genre-pack search-path
   config is already a first-class concern). `interior/loader.py` and
   `interior/render.py` are already pure and stay put. Result: `interior/` becomes a
   clean domain package with zero FastAPI imports.

4. **Narrow `orbital/intent` to a protocol.** Replace the `Session` import with a
   minimal structural interface (a `Protocol` or a thin read struct) exposing only
   the four properties it uses (`orbital_content`, `orbital_scope`, `clock.t_hours`,
   `party_body_id`) plus the plotted-course field. `server/` constructs and passes
   it. This is the one move that is design work rather than relocation; it is
   sequenced last and is the smallest in blast radius.

### Enforcement

Add a **CI guard** that fails if any module under `game/`, `genre/`, `orbital/`,
`magic/`, `interior/`, or `foundation/` imports from `sidequest.server`. A
~20-line AST/grep test in `tests/` is sufficient (no `import-linter` dependency
required, consistent with ADR-088's "the script is the schema" stance). This makes
the law executable rather than aspirational and satisfies the project's "every test
suite needs a wiring test" rule — the guard *is* the wiring test for layer
direction. The four moves above must land together with the guard, or the guard
lands first as `xfail` and flips to enforcing as each move completes.

## Non-Goals

- **Not a library extraction.** Nothing leaves `sidequest-server` as a pip package.
  The daemon↔server contract library is a separate decision.
- **Not touching the healthy seams.** `handlers ↔ server`, the `protocol` fan-in,
  and the `Session`/`GameSnapshot` split are explicitly preserved.
- **Not a rewrite of `Session` or `GameSnapshot`.** The strangler-fig migration
  (server behaviour moving inward one method at a time) is orthogonal and continues
  on its own track.
- **Not reorganizing `game/`'s internals.** Only the specific misfiled units move.

## Consequences

### Positive

- The lazy in-method imports on the combat-resolution path are deleted; module load
  graph stops fighting itself.
- Four upward edges vanish with one new floor package; the domain layer becomes
  importable without dragging `server/` behind it (which also de-risks any *future*
  extraction question without committing to one now).
- Core combat rules sit in the domain tier with their consumers — easier to reason
  about, test, and (eventually) bind per ADR-117/142.
- The CI guard makes regression structurally impossible rather than eventual.

### Negative

- A spread of files move; imports update across `game/`, `genre/`, `orbital/`,
  `interior/`. Mechanical but non-trivial diff; mostly `git mv` + path edits.
- A new top-level package (`foundation/`) is one more place to know about.
  Mitigated: its charter is narrow and the CI guard documents its constraint.
- Move #4 changes a call signature in the orbital intent path; needs a focused test.

### Neutral

- Behaviour is unchanged end-to-end; this is a placement refactor. Tests should pass
  before and after with no logic edits beyond import paths and the orbital interface.

## Implementation Plan

Sequenced by value and independence; each step is independently shippable behind the
CI guard:

1. **Foundation floor** — create `sidequest/foundation/`; move `asset_urls`,
   `slug_fold`, `reference_anchors`; update the four importers. (Erases four edges.)
2. **Rules relocation** — move `find_confrontation_def` and
   `resolve_damage_spec_from_beat_and_actor` into `game/ruleset/`; delete the lazy
   import workarounds in `native.py` / `without_number.py`.
3. **Interior lift** — move the endpoint to `server/rest.py`; leave `interior/`
   pure.
4. **Orbital narrowing** — introduce the read `Protocol`; drop the `Session` import.
5. **CI guard** — land the no-upward-import test enforcing for all five domain
   packages + `foundation/`.

When all five land, flip this ADR's `implementation-status` from `deferred` to
`live`.
