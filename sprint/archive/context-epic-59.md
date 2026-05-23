# Epic 59: Confrontation Engagement Regression — Narrator Stops Firing advance_confrontation

## Overview

The SDK narrator stopped engaging the confrontation engine for social
confrontations. In `tea_and_murder` (Glenross), the narrator writes full
standoff / negotiation prose but never calls `advance_confrontation`, so no
engine state stands behind the scene — a direct SOUL/OTEL "winging it"
violation. This epic gets the narrator to actually declare social
confrontations and restores a non-keyword OTEL lie-detector so the same
regression cannot ship silently again.

**Priority:** P1
**Repo:** sidequest-server
**Stories:** 1 (5 points)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **Confrontation intent-validator plan** (`docs/superpowers/plans/2026-05-20-confrontation-intent-validator.md`) | The narrator-declared-intent model and intent-mismatch detection that landed via PR #266/#243 — adjacent infrastructure this epic builds on |
| **Confrontation intent-validator design** (`docs/superpowers/specs/2026-05-20-confrontation-intent-validator-design.md`) | Design rationale for `intent_verb_set` derivation and `on_intent_mismatch` |
| **ADR-033 Confrontation Engine — Resource Pools** (`docs/adr/033-confrontation-engine-resource-pools.md`) | What `advance_confrontation` drives: ConfrontationDefs, beats, resource pools |
| **ADR-093 Confrontation Difficulty Calibration** (`docs/adr/093-confrontation-difficulty-calibration.md`) | Calibration of social confrontation types |
| **ADR-067 Unified Narrator Agent** (`docs/adr/067-unified-narrator-agent.md`) | Amended 2026-05-20 — inference site wired via intent validator |
| **ADR-111 Narrator Guardrails into Tool Descriptions** (`docs/adr/111-narrator-guardrails-into-tool-descriptions.md`) | SDK tool selection keys on the tool DESCRIPTION, not the system prompt — central to the suspected root cause |
| **ADR-031 Game Watcher — Semantic Telemetry** (`docs/adr/031-game-watcher-semantic-telemetry.md`) | The OTEL lie-detector pattern this epic must restore |

## Background

This is a **post-Epic-50 regression**, surfaced in the 2026-05-21 Glenross
(`tea_and_murder`) solo playtest. `tea_and_murder` is a social-first pack whose
confrontation types are negotiation / trial / auction / social_duel / scandal.
During the playtest the narrator was handed an explicit social escalation
(blocking an NPC's path, calling a bluff, threatening to fetch the Sergeant) and
returned a textbook standoff in prose — with **zero engine state behind it**.
Every turn logged `confrontation=None`, `beat_selections=0`, and across ~6 turns
`advance_confrontation` was invoked **0 times** despite the narrator making 1–4
tool calls per turn (apply_world_patch, commit_known_fact, etc.). No
`confrontation.intent*` spans fired.

**Why the regression is silent.** Epic 50 changed the architecture in two ways:

1. **Keyword auto-trigger → narrator-declared-intent.** Commits `79cea7a`
   (derive `intent_verb_set` per ConfrontationDef), `60027da`
   (validate(action_rewrite, declared, pack)), and `ad9381b` (enumerate the
   then-"Victoria" social types) moved confrontation engagement from a
   keyword-pattern auto-trigger to a model where the narrator must *declare* an
   intent that the engine then validates.
2. **Deleted the lie-detector.** Commit `93c7659` removed
   `_CONFRONTATION_TRIGGER_PATTERNS` — the keyword detector that used to flag
   "narrator described a confrontation but never engaged the engine." With it
   gone, a narrator that simply never declares anything produces no warning.

The intent-validator work merged on 2026-05-20 (PR #266 docs/ADR amendment,
PR #243 `on_intent_mismatch` + `intent_verbs` config across 7 packs) added an
**intent-*mismatch*** detector — it fires when the narrator declares an intent
that doesn't match. That is useless for this bug, where the narrator declares
*nothing*. So the architecture shifted to declared-intent, the keyword
lie-detector was deleted, and in practice the SDK narrator now never declares a
social confrontation in this pack — and nothing catches it.

The tool is **registered** (`agents/tools/advance_confrontation.py`,
`agents/tools/__init__.py`) and `output_only_sdk.md` §4 carries strong TRIGGER
CRITERIA including negotiation, social_duel, and scandal ("Err on the side of
triggering"). So this is a **behavior / wiring gap, not a missing tool.**

## Technical Architecture

**Confrontation engagement path (current, declared-intent model):**

```
player social escalation
  → SDK narrator turn (tools offered incl. advance_confrontation?)
      → narrator must DECLARE a confrontation intent
          → validate(action_rewrite, declared, pack) against derived intent_verb_set
              → advance_confrontation tool call → confrontation state set
                  → confrontation.intent* OTEL spans emitted
```

Today the chain breaks at the **declare** step: the narrator emits prose and
never declares, so nothing downstream fires.

**Key files (orientation — Dev/TEA confirm during implementation):**

| File | Role |
|------|------|
| `sidequest-server/sidequest/agents/tools/advance_confrontation.py` | The tool itself (registered) |
| `sidequest-server/sidequest/agents/tools/__init__.py` | Tool registration / per-turn tool list assembly |
| `output_only_sdk.md` (narrator prompt) §4 | TRIGGER CRITERIA prose (system-prompt zone) |
| `genre_packs/tea_and_murder/rules.yaml` | ConfrontationDefs, `intent_verbs`, `on_intent_mismatch` (PR #243) |
| Telemetry / watcher module | Where the restored non-keyword lie-detector span lives |

**Confirmed root cause (Architect, 2026-05-22) — supersedes the original
suspected vectors.** Engagement is NOT a call to `advance_confrontation` (that
tool only *advances* an active encounter and errors if none exists). Engagement
is the narrator setting the structured **`confrontation` field**
(`orchestrator.py:304`), which the server consumes at `narration_apply.py:2531`
to create the StructuredEncounter. That field is populated **only on the legacy
`claude -p` JSON-sidecar path** (`orchestrator.py:841/880/2643+`). On the
default `anthropic_sdk` backend (ADR-101/102) **no tool writes it**:
`apply_world_patch` omits it, `advance_confrontation` can't start, and
`generate_encounter` — where ADR-111/57-4 stranded the social trigger criteria
— is a stub that always returns a fatal error. The SDK prompt
(`output_only_sdk.md` §4) compounds it by routing STARTING to
`advance_confrontation`. The Epic 50 → SDK migration left confrontation
*engagement* (vs *advancement*) with no tool path. **Fix direction:** give the
SDK narrator an engagement-field writer (reuse-first: extend `apply_world_patch`),
relocate the trigger criteria onto that live tool, correct the prompt, and
extend the lie-detector to the no-emission case. See `context-story-59-1.md`
→ Architecture Decision for full detail.

**Regression-proofing (the OTEL mandate).** The fix must restore a *non-keyword*
lie-detector: a watcher event that flags "narration reads as a confrontation but
`advance_confrontation` was not called this turn," replacing the deleted
`_CONFRONTATION_TRIGGER_PATTERNS`. This honors the project rule that every
subsystem decision emits an OTEL span so the GM panel can catch winging-it.

## Cross-Epic Dependencies

**Depends on:**
- Epic 50 (Victoria / `tea_and_murder` social confrontation wiring) — provides
  the declared-intent model, `intent_verb_set` derivation, and the `rules.yaml`
  confrontation/intent config this epic repairs. This epic is a regression fix
  *on top of* Epic 50's architecture shift.
- Confrontation intent-validator work (PR #266 / #243, merged 2026-05-20) —
  provides `on_intent_mismatch` + `intent_verbs`; this epic complements it by
  fixing the *non-declaration* case it cannot catch.

**Depended on by:**
- None currently. (UX note: the resolved class-move labels from the playtest
  Character→Abilities fix are the same social-confrontation beat vocabulary, so
  a working confrontation UI benefits once this engine engages — informational,
  not a blocking dependency.)
