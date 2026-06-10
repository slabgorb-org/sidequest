# Story 101-2: Remove all voice-generation references from server

## Summary
Remove all dead voice-generation references from the sidequest-server engine. The voice system was deprecated per operator decision on 2026-06-09. This is a 3-point TDD chore to clean up the server codebase, leaving orchestrator-level authoring tooling (`/sq-voice`) untouched.

## Acceptance Criteria
1. All five server voice surfaces removed; ruff + full server test suite green
2. A pre-removal Postgres save containing voice_id loads without error (tolerant load or Alembic migration)
3. Wiring test: grep-guard or import test proving no voice_presets/VOICE_SIGNAL/VOICE_TEXT references remain in production code
4. Daemon untouched except confirmation note (scene_interpreter regex word is narrative, stays)

## Story Details
- **Type:** chore
- **Points:** 3
- **Priority:** p3
- **Repos:** server
- **Workflow:** tdd
- **Epic:** 101 (Split-Brain Remediation — Daemon Renderer Drift & Dead Twins)

## Voice-Generation Surfaces to Remove

### 1. genre/models/audio.py
- VoiceConfig model
- VoicePresets model
- CreatureVoicePreset model
- creature_voice_presets field on AudioConfig

### 2. genre/loader.py
- Lines 27, 1691-1692, 2008 — voice_presets.yaml optional-load path

### 3. genre/models/pack.py + models/__init__.py
- voice_presets field on pack model
- Related exports in __init__.py

### 4. protocol/enums.py
- Lines 48-49: VOICE_SIGNAL + VOICE_TEXT message types
- Zero emitters/handlers in production code

### 5. game/projection/invariants.py
- Line 60: VOICE_TEXT routing entry

### 6. game/session.py
- Line 141: Npc.voice_id field
- Only ever assigned None at world_materialization.py:545,874

## Key Constraints

### Save Migration
- Npc has model_config extra=forbid and persisted saves may carry voice_id
- Must tolerate existing Postgres snapshots without error
- Either implement tolerant deserialization or create an Alembic migration
- **Verification:** Load a pre-removal session from Postgres; confirm no errors

### Verification Requirements
- grep-guard or import test proving no references remain in production code
- All references must be dead (zero runtime readers, zero pack usage, zero protocol routes)
- Daemon is clean except scene_interpreter.py:64 narrative regex word "voice" — keep untouched

## Context
This story is part of Epic 101 (Split-Brain Remediation), which addresses systematic dead code and split-brain drift discovered in the 2026-06-09 system-wide scan. The voice system was fully deprecated and is confirmed dead across the codebase.
