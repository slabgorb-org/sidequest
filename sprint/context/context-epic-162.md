# Epic Context: 162

## Epic
- **ID:** 162
- **Title:** NPC origin consolidation — one identity, one arbiter, derived Monster Manual
- **Type:** epic
- **Priority:** p1
- **Status:** backlog

## Description

Consolidate the seven NPC/creature spawn paths per the 2026-07-05 NPC-generation inventory.

**Root causes addressed:**
1. No origin-precedence arbiter (multiple spawn paths fought over creature identity)
2. Name-string identity with per-seam dedup divergence (identity forks: same creature, two names)
3. Shared mutable Monster Manual cache fought over by 4 clones (beneath_sunden purge/reseed livelock, pool runaway)

**Solution sequence (per 2026-07-05 party-mode):**
1. Derive-don't-cache manual (content-sha + session-seed keyed pool)
2. ID-keyed identity + alias ledger (kills two-names-one-enemy)
3. Green Room precedence ADR (single-gate materializer design, seven typed-provenance feeders)

## Stories

### Completed (162-1 through 162-6)
1. **162-1** (DONE): Derive-don't-cache Monster Manual with forensics
2. **162-2** (DONE): Identity by id (not name) — alias ledger
3. **162-3** (DONE): Bestiary generics replace stub minting
4. **162-4** (DONE): Origin-precedence ADR (Green Room)
5. **162-5** (DONE): flickering_reach content reconciliation
6. **162-6** (DONE): space_opera bestiary de-triplication

### In Progress / Backlog
7. **162-7** (BACKLOG): All-sources-one-scene wiring test + understudy identity-split hunt
8. **162-8** (BACKLOG): Dead spawn-path cleanup
9. **162-9** (BACKLOG): 162-1 follow-ups
10. **162-10** (BACKLOG): 162-2 non-blocking follow-ups

## Reference Documents

- `docs/superpowers/specs/2026-07-05-npc-generation-inventory.md` — The seven spawn paths
- `docs/adr/004-lazy-genre-binding.md` — Origin/provenance semantics
- `docs/adr/121-layered-content-resolution.md` — Layered content resolution
- `docs/adr/059-monster-manual.md` — Monster Manual pre-generation via game-state injection
