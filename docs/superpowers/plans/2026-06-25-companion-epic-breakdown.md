# Companion Seat - Epic Breakdown

## Overview

A full-PC AI companion — "Donut to your Carl" — that joins a live SideQuest session as its own seat over the WebSocket protocol (no browser), with a configurable role dial (pet/peer/hireling) gating type-scoped perception, full mechanical play, and a persistent+evolving bond. Reuses understudy's brain/persona, the engine's perception firewall, and the disposition/OCEAN machinery. Design spec: docs/superpowers/specs/2026-06-25-companion-seat-design.md. Build order: 1.1 unblocks 1.4; 1.4 unblocks 1.5; 1.3 is independent. v1 only (v2 cross-campaign memory is a separate future epic).

**Points:** 16

## Epic 1: Companion Seat — full-PC AI companion over WebSocket

**User Outcome:** A human plays beside a Donut-grade AI companion that joins their session as a real seated PC, plays full turns with crunch in a distinct voice, knows them (pet) or doesn't (hireling) by type, and whose bond shifts over the session.

**Points:** 16

### Story 1.1: Extract sidequest-seat-core (schema-generic backends + persona axes)

As a developer,
I want **a charter-neutral seat-core package whose model backends are generic over a pydantic output schema, plus shared SeatAxes and the Role/RoleDial**,
So that the companion and understudy share one debugged brain without a shipping artifact depending on a test harness.

**Acceptance Criteria:**

**Given** understudy's brain backends hardcode the naive Intent
**When** seat-core is extracted per Plan A (docs/superpowers/plans/2026-06-25-companion-A-seat-core.md) tasks 1–8
**Then** anthropic/ollama/claude_p/make_model decode any pydantic output model, prompt caching + key-stripping behavior is preserved, and SeatAxes + Role/RoleDial ship with tests.
**And** repos: sidequest-seat-core (new). Workflow: tdd.

**Points:** 3

### Story 1.2: Migrate understudy onto seat-core

As a developer,
I want **understudy to depend on seat-core via a uv path source with brain/core and factory as thin Intent-binding shims**,
So that the extraction is real (single source of truth) and understudy's suite stays green.

**Acceptance Criteria:**

**Given** seat-core exists (Story 1.1)
**When** understudy is migrated per Plan A task 9
**Then** the moved backend modules are deleted, brain APIs are preserved via shims, DecideResult.value replaces .intent, Archetype subclasses SeatAxes, and the full understudy pytest run passes.
**And** repos: sidequest-understudy. Workflow: tdd. Depends on 1.1.

**Points:** 2

### Story 1.3: Server companion bond + perception seam

As a player,
I want **the server to recognize a seat as a companion bonded to me and scope its perception by type**,
So that a bonded pet shares my private view while a hireling sees only what's observable.

**Acceptance Criteria:**

**Given** the SESSION_EVENT connect handshake can carry companion metadata
**When** the bond registry, connect-handler registration, and fan-out pet-widening are added per Plan B (docs/superpowers/plans/2026-06-25-companion-B-server-bond-seam.md)
**Then** a pet receives owner-private NARRATION_SEGMENT/SECRET_NOTE and a hireling does not, unknown relationships fail closed, and companion.bond_resolved + companion.routed_as_pet OTEL spans fire, proven by a firewall wiring test.
**And** repos: sidequest-server. Workflow: tdd. Independent of 1.1.

**Points:** 3

### Story 1.4: Companion package core — intent, manifest, persona, dice, protocol, brain, actuation

As a developer,
I want **the sidequest-companion value layer: CompanionIntent, the CompanionDef manifest, the voice/role persona, fair dice, the typed protocol subset with state mirror, the seat-core-backed brain, and actuation**,
So that the companion can think and form valid outgoing frames before any socket exists.

**Acceptance Criteria:**

**Given** seat-core exists (Story 1.1)
**When** Plan C (docs/superpowers/plans/2026-06-25-companion-C-companion-package.md) tasks 1–8 are implemented
**Then** intents validate, definitions load fail-loud, the persona prompt carries voice+bond+never-narrate, dice are fair per system, the mirror tracks self/round/turn/pending, the brain degrades to YIELD on timeout/error, and actuation maps each intent to the right frame — all unit-tested.
**And** repos: sidequest-companion (new). Workflow: tdd. Depends on 1.1.

**Points:** 4

### Story 1.5: Companion run loop, WebSocket transport, CLI, and full-loop wiring

As a player,
I want **the companion to actually connect and play a session end to end: connect, claim seat, do chargen, take turns, answer dice/confrontation prompts, exit cleanly**,
So that I have a playable Donut beside me at the table.

**Acceptance Criteria:**

**Given** the companion value layer exists (Story 1.4)
**When** Plan C tasks 9–11 are implemented (run loop, websockets transport, CLI, wiring test)
**Then** run_companion drives connect→chargen→play→prompt against a Transport, the decide step is timeout-bounded (never stalls the table), the websockets adapter + `companion play` CLI work, and a full-loop wiring test plays a scripted session end to end.
**And** repos: sidequest-companion. Workflow: tdd. Depends on 1.4.

**Points:** 4
