---
story_id: "101-2"
jira_key: ""
epic: "101"
workflow: "tdd"
---
# Story 101-2: Remove all voice-generation references from server

## Story Details
- **ID:** 101-2
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T07:13:54Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T00:00:00Z | 2026-06-10T06:40:21Z | 6h 40m |
| red | 2026-06-10T06:40:21Z | 2026-06-10T06:48:34Z | 8m 13s |
| green | 2026-06-10T06:48:34Z | 2026-06-10T06:56:03Z | 7m 29s |
| review | 2026-06-10T06:56:03Z | 2026-06-10T07:04:59Z | 8m 56s |
| green | 2026-06-10T07:04:59Z | 2026-06-10T07:10:14Z | 5m 15s |
| review | 2026-06-10T07:10:14Z | 2026-06-10T07:13:54Z | 3m 40s |
| finish | 2026-06-10T07:13:54Z | - | - |

## Sm Assessment

**Story:** Remove all dead voice-generation references from the sidequest-server engine. Operator decision 2026-06-09; `/sq-voice` remains orchestrator-level authoring tooling and stays untouched. Daemon is clean (its only `voice` hit is a narrative appearance-regex word — keep).

**Scope — five server surfaces, all scan-verified dead (zero runtime readers):**
1. `genre/models/audio.py` — `VoiceConfig`, `VoicePresets`, `CreatureVoicePreset`, and the `creature_voice_presets` field on `AudioConfig`.
2. `genre/loader.py:27,1691-1692,2008` — the `voice_presets.yaml` optional-load path (file exists in zero packs).
3. `genre/models/pack.py:289` `voice_presets` field + `models/__init__.py` exports.
4. `protocol/enums.py:48-49` `VOICE_SIGNAL` + `VOICE_TEXT` message types (zero emitters/handlers) and the `VOICE_TEXT` routing entry in `game/projection/invariants.py:60`.
5. `game/session.py:141` `Npc.voice_id` (only ever assigned `None` at `world_materialization.py:545,874`).

**Load-bearing caution for TEA/Dev:** `Npc` has `model_config extra=forbid` and persisted Postgres saves may carry `voice_id`. Removal must tolerate or migrate existing snapshots — **the RED phase must include a save-load test of a pre-removal session** so we don't break save compatibility silently. This is the one non-trivial risk in an otherwise mechanical deletion.

**Routing:** Phased TDD → TEA (Amos) for RED. Jira skipped (not configured). Single repo: server.

## TEA Assessment

**Tests Required:** Yes
**Reason:** AC-2 (legacy save compatibility under `extra=forbid`) is real, testable behavior — not a pure mechanical deletion. Bypass not warranted.

**Test Files:**
- `tests/game/test_101_2_voice_removal.py` (new) — full removal contract across all five surfaces + the save-compat shim + OTEL.
- `tests/protocol/test_enums.py` (edited) — removed two `VOICE_*` wire-string tests, flipped variant count 56 → 54.

**Tests Written:** 21 in the new module covering 4 ACs (+1 count test edited in test_enums).
**Status:** RED — verified via testing-runner (`101-2-tea-red`): 17 fail + 1 fail (enum count) = 18 RED drivers; 4 green (3 scope/no-op guards + 1 regression guard `test_migrated_npcs_validate_under_extra_forbid`, which stays green by design since `voice_id` is still a valid field today and the migration keeps it loadable post-removal).

### Rule Coverage

| Rule (server CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| No Source-Text Wiring Tests (AC-3 grep-guard via reflection) | all absence tests use `hasattr`/`model_fields`/enum/dict membership | failing (RED) |
| Wiring test required (no half-wired removal) | `test_s6_strip_voice_id_sub_function_is_registered`, `test_canonicalize_span_fires_when_voice_id_stripped` | failing (RED) |
| OTEL Observability (every subsystem decision emits a span) | `test_voice_id_strip_routed_through_canonicalize_extractor`, `test_canonicalize_span_fires_when_voice_id_stripped` | failing (RED) |
| No Silent Fallbacks (no-op on canonical input, no fabricated work) | `test_migration_no_op_on_snapshot_without_voice_id` | passing (guard) |
| Scope discipline (don't over-delete) | `test_mixer_voice_volume_field_is_retained`, `test_chassis_voice_spec_is_retained` | passing (guard) |

**Rules checked:** 5 of 5 applicable rules have test coverage.
**Self-check:** 0 vacuous tests. Every test has a meaningful assertion; the no-op/scope guards assert retained state to prevent over-deletion.

**Handoff:** To Dev (Naomi) for GREEN. Follow the S3 migration pattern (see Delivery Findings) — add `_migrate_s6_strip_npc_voice_id` + the `s6_voice_id_stripped` extractor key. Do NOT touch `MixerConfig.voice_volume` or `ChassisVoiceSpec`.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-server):**
- `sidequest/genre/models/audio.py` — deleted `VoiceConfig`, `VoicePresets`, `CreatureVoicePreset`, `AudioConfig.creature_voice_presets`; updated module/class docstrings.
- `sidequest/genre/models/__init__.py` — dropped the three voice-model imports + `__all__` entries (kept `AudioEffect`).
- `sidequest/genre/models/pack.py` — dropped `GenrePack.voice_presets` + the `VoicePresets` import.
- `sidequest/genre/loader.py` — dropped the `voice_presets.yaml` optional-load path, the import, and the constructor kwarg.
- `sidequest/protocol/enums.py` — deleted `MessageType.VOICE_SIGNAL` / `VOICE_TEXT`.
- `sidequest/game/projection/invariants.py` — dropped the `VOICE_TEXT` `TARGETED_KINDS` route.
- `sidequest/game/session.py` — deleted `Npc.voice_id`.
- `sidequest/game/world_materialization.py` — dropped the two `voice_id=None` construction kwargs (would `TypeError` otherwise; not covered by RED, caught by the regression sweep).
- `sidequest/game/migrations.py` — added `_migrate_s6_strip_npc_voice_id` + registered it in the `migrate_legacy_snapshot` tuple (AC-2 save-compat shim, mirrors S3).
- `sidequest/telemetry/spans/persistence.py` — added `s6_voice_id_stripped` to the `snapshot.canonicalize` extractor allow-list.

**Tests:** GREEN — verified via testing-runner (`101-2-dev-green`). Both target files pass (98 tests incl. the flipped enum count 54). Full subsystem sweep (genre/protocol/game/telemetry) = 4352 passed, 0 related failures. ruff clean.
**Branch:** `feat/101-2-remove-voice-generation-references` (pushed).

**Handoff:** To Reviewer (Chrisjen) for code review.

### Dev Rework (round-trip 1 — addressing REJECTED verdict)

All six review findings resolved + one pre-existing breakage caught:
- **V1 (HIGH) fixed:** removed the dangling `VoicePresets` import + OPTIONAL entry from `scripts/audit_content_drift.py`. **While fixing it, a SECOND pre-existing dangling import surfaced** — `OpeningHook` (renamed to `Opening` by an earlier narrative rework; broken on `develop` too, not introduced by this story). Fixed it opportunistically (same file, same defect class) so the script actually imports — verified via `exec_module`. Logged as an out-of-scope deviation.
- **V2 (LOW) fixed:** dropped stale `voice_id: None` from `_minimal_npc_dict` in `tests/game/test_npc_pool_migration.py`.
- **DOC fixed:** `migrations.py` S6 docstring corrected (`int | None`, not "always None"); test-module docstring reframed RED→post-removal; negative-guard section header renamed (no longer collides with "Surface 2").
- **FORMAT fixed:** `ruff format` applied to the test file.
- **DOC fixed:** `audio/__init__.py` docstring "three-lane … voice system" → "two-lane ambient music and SFX".

**Tests:** GREEN — testing-runner (`101-2-dev-green-rework`): 134 story-related tests pass; full sweep 4352 passed, only the pre-existing `test_api_contract_aside` (oq-1 checkout path) still red. `scripts/audit_content_drift.py` now imports cleanly. ruff check + format clean on all touched files.
**Branch:** `feat/101-2-remove-voice-generation-references` (pushed, `c02c1e01`).

**Handoff:** Back to Reviewer (Chrisjen) for re-review.

## Subagent Results (Round 1 — REJECTED, historical)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (ruff format on test file) + 1 pre-existing unrelated | confirmed 1, dismissed 0, deferred 1 (pre-existing api-contract path) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (test-quality, low/med) | confirmed 0 blocking, noted 5 non-blocking |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 high + 2 low (stale docstrings) | confirmed 3, dismissed 2 (low/no-change) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 (V1 dangling import HIGH, V2 stale fixture LOW) | confirmed 2 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 HIGH confirmed (blocking), 6 LOW confirmed (non-blocking cleanup), 5 test-quality noted (non-blocking), 2 dismissed/deferred

## Reviewer Assessment (Round 1 — REJECTED, historical)

**Verdict:** REJECTED

The change itself — deleting five dead voice surfaces and adding the S6 save-migration shim — is correct, well-patterned (matches S1–S5 exactly), and cross-repo safe (I confirmed zero readers in UI, daemon, and content packs). But the removal is **incomplete**: it left a dangling `VoicePresets` import in a checked-in tool that will `ImportError` on next run, directly violating AC-3 ("no references remain in production code"). That is a half-wired removal — blocking per the repo's "don't ship 3 of 5 connections" rule.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [RULE] | Dangling `VoicePresets` import + OPTIONAL-list reference — guaranteed `ImportError` on next run; violates AC-3 "no references remain". The story's surface scan missed this reader. | `scripts/audit_content_drift.py:28,77` | Remove `VoicePresets` from the import (keep `AudioConfig`); delete the `("voice_presets.yaml", VoicePresets, False)` entry from `OPTIONAL`. |
| [LOW] [RULE] | Stale `voice_id: None` in NPC test fixture — S6 now strips it silently; misrepresents canonical post-removal Npc shape (footgun for future shape-asserting tests). | `tests/game/test_npc_pool_migration.py:56` | Delete the `"voice_id": None` line from `_minimal_npc_dict()`. |
| [LOW] [DOC] | `_migrate_s6` docstring says voice_id was "always `None` at materialization" — inaccurate. Field was `int \| None`; the PR's own fixture seeds `voice_id: 7`. Code is correct (strips regardless of value); docstring understates the case. | `sidequest/game/migrations.py:374` | Reword to "typed `int \| None`, defaulting to `None` at materialization but potentially carrying an integer in older saves". |
| [LOW] [DOC] | Test module docstring still frames these as "Failing tests" that "fail on the current tree (RED)" — they are GREEN post-merge; misleading to future readers. | `tests/game/test_101_2_voice_removal.py:1` | Reframe the opening paragraph to post-removal verification language. |
| [LOW] | `ruff format --check` flags the new test file (two assert-message reflows). `ruff check` is clean, but format is dirty. | `tests/game/test_101_2_voice_removal.py` | Run `uv run ruff format tests/game/test_101_2_voice_removal.py`. |
| [LOW] [DOC] | `audio/__init__.py` docstring still advertises a "three-lane … voice system" — the voice lane is gone (TTS dropped 2026-04). Pre-existing, but adjacent and the right time. | `sidequest/audio/__init__.py:1` | Update to "two-lane ambient music and SFX" (optional — pre-existing, dev's discretion). |

### Dispatch-tagged observations

- `[RULE]` **Confirmed V1 (HIGH):** dangling `VoicePresets` import in `scripts/audit_content_drift.py:28,77` — verified by direct grep; top-level import → ImportError. Decisive blocker.
- `[RULE]` **Confirmed V2 (LOW):** stale `voice_id: None` fixture at `tests/game/test_npc_pool_migration.py:56` — verified.
- `[DOC]` **Confirmed 3 stale-comment findings** from comment-analyzer (migrations docstring, test-module RED framing, audio/__init__ voice-system). Dismissed 2 low (enum-count comment is arithmetically correct; surface-numbering collision is cosmetic).
- `[TEST]` **Noted, non-blocking:** test-analyzer's 5 findings (no field-value assert on the no-raise test; symbol-name wire test; OTEL `init_tracer` ordering under `-n0`; missing `GenrePack` rejection test; `npcs=None` edge). The symbol-name wire test and the OTEL `init_tracer` pattern are copied verbatim from the established S3 `test_party_location_migration.py` that TEA was directed to mirror — convention-consistent, not defects. The `GenrePack` rejection test is a reasonable symmetry enhancement for a follow-up. None block.
- `[EDGE]` **Subagent disabled** — self-assessed: the only new branch is `_migrate_s6`'s `npcs`-not-a-list / non-dict-entry guards, which match the S2/S5 defensive pattern. The `del npc["voice_id"]` mutates the dict element, not the list under iteration — safe. No unhandled edge.
- `[SILENT]` **Subagent disabled** — self-assessed: `_migrate_s6` has no try/except and no swallowed errors; returns `None` as an explicit no-op (No Silent Fallbacks compliant — span fires only when work happened).
- `[TYPE]` **Subagent disabled** — self-assessed: `_migrate_s6` matches the S1–S5 signature `(out: dict[str, Any]) -> dict[str, Any] | None` exactly. Enum member removal tightens the type boundary (stray wire values now raise ValueError). No stringly-typed regressions.
- `[SEC]` **Subagent disabled** — self-assessed: no new input boundary; migration operates on an already-loaded deep-copied snapshot with isinstance guards. Removing enum members is a stricter (safer) boundary. No injection/auth/secret surface touched.
- `[SIMPLE]` **Subagent disabled** — self-assessed: change is minimal deletion + a 17-line shim mirroring precedent. No over-engineering; `AudioEffect` left dead is flagged as a follow-up (Dev finding), acceptable under scope discipline.

**Data flow traced:** legacy Postgres save dict → `migrate_legacy_snapshot` (deep-copies input) → `_migrate_s6_strip_npc_voice_id` strips `voice_id` from each npc dict before pydantic → `Npc.model_validate` succeeds under `extra=forbid`. OTEL `s6_voice_id_stripped` counter routes to the GM panel via the canonicalize extractor. Safe.

### Rule Compliance (Python lang-review + server rules)

Exhaustive enumeration against the 13 Python checks + 5 server rules (18 total, 61 instances):

- **#1 Silent exceptions:** `_migrate_s6` — no try/except. Compliant.
- **#2 Mutable defaults:** `_migrate_s6` single param no default; all model fields use `Field(default_factory=...)`. Compliant.
- **#3 Type annotations:** `_migrate_s6` fully annotated, matches S1–S5 contract. Compliant.
- **#4 Logging:** module is OTEL-only by design; span attribute emitted. Compliant.
- **#5 Path handling:** loader change only deletes lines; no new `open()`. Compliant.
- **#6 Test quality:** all 17 new tests have real assertions; `AudioConfig` rejection test is the strongest form. Compliant (enhancements noted, non-blocking).
- **#7 Resource leaks / #8 Unsafe deser / #9 Async:** no new resources, deserialization, or async. Compliant.
- **#10 Import hygiene:** `__init__.py`, `loader.py`, `pack.py` removals consistent — BUT `scripts/audit_content_drift.py` left a dangling `VoicePresets` import. **VIOLATION (V1, HIGH).**
- **#11 Input validation:** isinstance guards on `npcs`/`npc`; enum removal tightens boundary. Compliant.
- **#12 Dependency hygiene:** no dep changes. Compliant.
- **#13 Fix-introduced regressions:** stale `voice_id: None` fixture at `test_npc_pool_migration.py:56`. **VIOLATION (V2, LOW).**
- **#14 No Silent Fallbacks:** `_migrate_s6` returns explicit `None` no-op; enum values raise rather than default. Compliant.
- **#15 No Stubbing / dead code:** all surfaces fully deleted, not stubbed. Compliant. (`AudioEffect` now-dead flagged as scope-deferred follow-up — acceptable.)
- **#16 Wiring test:** `test_canonicalize_span_fires_when_voice_id_stripped` drives the full pipeline. Compliant.
- **#17 No Source-Text Wiring Tests:** all reflection/introspection, zero `read_text()`. Compliant.
- **#18 OTEL Observability:** `s6_voice_id_stripped` emitted + extractor allow-listed. Compliant.

### Devil's Advocate

Argue this code is broken. First, the strongest case: the team declared this surface "fully dead, zero readers" and shipped on that confidence — and they were wrong. `scripts/audit_content_drift.py` imports `VoicePresets` at module top level and will hard-crash with `ImportError` the next time anyone audits content drift. If the surface scan missed *that* reader, what else did it miss? The scan was grep-scoped to the package; any tool, notebook, alembic migration, or operator script outside `sidequest/` that touched these symbols is now a latent crash. I checked `scripts/` and `tools/` and found only the one — but the methodology that produced the "zero readers" claim is the same methodology that missed it, so my own confidence is bounded by the same blind spot. A confused operator running the drift auditor post-merge gets a stack trace, not a clean run.

Second, the save-migration angle. `Npc` is `extra=forbid`. The shim strips `voice_id` — but only from `out["npcs"]`. What about NPCs nested elsewhere in a snapshot? If any save shape carries NPC dicts under a different key (an encounter's combatants, a scenario's cast, a chassis interior roster) and those are validated as `Npc`, they would still carry `voice_id` and raise on load — and no test covers that. The migration assumes all NPCs live under the top-level `npcs` list. For the current snapshot schema that's true, but a stressed older save with a different nesting would slip through. Third, the OTEL test calls `init_tracer()` and asserts the returned provider is a `TracerProvider`; under serial `-n0` runs with a pre-initialized tracer that assertion can hard-fail — a future contributor debugging an unrelated change could hit a confusing red. Fourth, a malicious or corrupt save with `npcs` as a dict-of-dicts rather than a list silently skips the strip (isinstance guard returns None) — if such a save also somehow reaches `Npc.model_validate`, it raises. None of these are demonstrated breakages on the current schema, but the dangling import IS a demonstrated, guaranteed crash — which is why this is a rejection, not a nitpick.

## Subagent Results

(Re-review round 2 — after Dev rework addressing the Round-1 REJECTED findings.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | GREEN: 114 targeted pass, 4352 sweep, lint+format clean, IMPORT OK; 1 pre-existing unrelated | confirmed 0 blocking, deferred 1 (pre-existing api-contract path) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | none (fixture removal safe, reflows cosmetic) | N/A |
| 5 | reviewer-comment-analyzer | Yes | clean | none (all 3 Round-1 stale-comment findings resolved) | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | V1 + V2 confirmed RESOLVED; 0 new violations | confirmed 2 resolved |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 confirmed (both Round-1 violations resolved); 0 new; 1 pre-existing unrelated deferred

## Reviewer Assessment

**Verdict:** APPROVED

Re-review of the Dev rework. All Round-1 findings are resolved and the rework introduced no new issues — confirmed by all four re-run subagents plus my own verification (the audit script now imports cleanly via `exec_module`; repo-wide grep for `VoicePresets`/`VoiceConfig`/`CreatureVoicePreset`/`OpeningHook` finds zero dangling references — only an absence-test string, a historical doc-comment, and an ImportError-guard test remain).

**Round-1 findings — disposition:**
- `[RULE]` V1 (HIGH) **resolved** — dangling `VoicePresets` import gone from `scripts/audit_content_drift.py`; the cascade-revealed pre-existing `OpeningHook` dangling import was also fixed (`→ Opening`, the live model). Script imports clean.
- `[RULE]` V2 (LOW) **resolved** — stale `voice_id: None` gone from `_minimal_npc_dict` fixture.
- `[DOC]` 3 stale-comment findings **resolved** — `migrations.py` S6 docstring (`int | None`, not "always None"), test-module RED→post-removal framing, `audio/__init__.py` two-lane. Comment-analyzer re-verified clean.
- `[LOW]` ruff-format **resolved** — `ruff format --check` passes on all 5 touched files.

**Dispatch-tagged observations (re-review):**
- `[RULE]` rule-checker clean — V1/V2 resolved, no new violations against import-hygiene/fix-regression/test-quality.
- `[DOC]` comment-analyzer clean — all prior stale comments corrected, no new ones.
- `[TEST]` test-analyzer clean — fixture removal is a no-op through S6; assert-message reflows are cosmetic; no semantics changed. (The `test_migrated_npcs_validate_under_extra_forbid` no-raise form remains the correct complete assertion for its path — pre-existing, non-blocking.)
- `[EDGE]` `[SILENT]` `[TYPE]` `[SEC]` `[SIMPLE]` subagents disabled via settings — self-assessed unchanged from Round 1: the rework is doc/import/fixture-only with no new logic, edges, error paths, types, security surface, or complexity introduced.

**Data flow re-traced:** unchanged from Round 1 and still safe — legacy save → `migrate_legacy_snapshot` (deep-copy) → S6 strips `voice_id` → `Npc.model_validate` under `extra=forbid` → OTEL `s6_voice_id_stripped` to GM panel.

**Pattern observed:** S6 migration sub-function mirrors the established S1–S5 contract exactly — `sidequest/game/migrations.py:369`.
**Error handling:** `_migrate_s6` guards `npcs` non-list and non-dict entries; explicit `None` no-op (no silent fallback) — `migrations.py:386-396`.
**Handoff:** To SM (Camina) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (rework)
- **Gap** (non-blocking): `scripts/audit_content_drift.py` carried a second, pre-existing dangling import — `OpeningHook` (renamed to `Opening` by an earlier narrative-model rework; broken on `develop`, not introduced by 101-2). Fixed opportunistically since it sat one line below the V1 fix in the same file and blocked the same "script imports cleanly" goal. Affects `sidequest-server/scripts/audit_content_drift.py` (now uses `Opening`). *Found by Dev during rework.*

### Reviewer (code review)
- **Gap** (blocking): The dead-surface scan that produced the story's "zero runtime readers" claim was package-scoped (`sidequest/`) and missed `scripts/audit_content_drift.py`, which imports and references `VoicePresets`. Affects `sidequest-server/scripts/audit_content_drift.py` (remove the import + OPTIONAL entry). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): AC-3's removal guard (reflection tests on the package namespace) does not catch dangling references in dependent scripts/tools outside the package. A future "remove all X" story should add an import-smoke or repo-wide reflection check over `scripts/` + `tools/`. Affects `sidequest-server/tests/` (strengthen the AC-3 guard pattern). *Found by Reviewer during code review.*

### Dev (implementation)
- **Improvement** (non-blocking): `AudioEffect` (`sidequest/genre/models/audio.py:28`) is now referenced only by the removed voice models — it is dead after this story but NOT in 101-2's five-surface scope. Kept it (scope discipline) — candidate for a follow-up cleanup. Affects `sidequest/genre/models/audio.py`, `sidequest/genre/models/__init__.py` (export).
- **Gap** (non-blocking): `tests/protocol/test_api_contract_aside.py::test_api_contract_does_not_lie_about_asides` fails in this `oq-1` checkout — it asserts `docs/api-contract.md` exists at `parents[N]/docs/api-contract.md`, which resolves to `/Users/slabgorb/Projects/oq-1/docs/api-contract.md` (absent here). Pre-existing, unrelated to voice removal (does not touch any changed file). Affects `sidequest-server/tests/protocol/test_api_contract_aside.py` (path resolution / fixture).

### TEA (test design)
- **Improvement** (non-blocking): The GREEN path for AC-2 should add `_migrate_s6_strip_npc_voice_id` to `sidequest/game/migrations.py` and register it in the `migrate_legacy_snapshot` orchestrator tuple, plus add `s6_voice_id_stripped` to the `_extract_snapshot_canonicalize` allow-list in `sidequest/telemetry/spans/persistence.py`. This mirrors the S3 party-location shim exactly — Dev should follow that established pattern, not invent a new save path. Affects `sidequest/game/migrations.py` and `sidequest/telemetry/spans/persistence.py`.
- **Gap** (non-blocking): `MixerConfig.voice_volume` (audio.py:56) and `ChassisVoiceSpec` (ADR-125 chassis voice) are `voice`-named but OUT of scope — they are an audio-mixer dial and rig-voice spec, not TTS generation. Tests assert they are RETAINED. Dev must not delete them while removing the five listed surfaces. Affects `sidequest/genre/models/audio.py`, `sidequest/genre/models/__init__.py`.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Kept `AudioEffect` instead of deleting the now-dead model**
  - Spec source: context-story-101-2.md, "Voice-Generation Surfaces to Remove" (enumerated list)
  - Spec text: lists exactly five surfaces; `AudioEffect` is not among them
  - Implementation: left `AudioEffect` + its export in place though it is now only referenced by the deleted voice models
  - Rationale: story scope is the authority (enumerated 5 surfaces); removing an unlisted model is scope creep and no test requires it. Logged as a non-blocking follow-up finding instead.
  - Severity: minor
  - Forward impact: minor — a follow-up may remove `AudioEffect` once confirmed unused pack-wide
- **Removed two `voice_id=None` construction kwargs not named in the surface list**
  - Spec source: context-story-101-2.md, surface 6 (`game/session.py` Npc.voice_id) + "Only ever assigned None at world_materialization.py:545,874"
  - Spec text: "Only ever assigned None at world_materialization.py:545,874"
  - Implementation: deleted both `voice_id=None` kwargs in `world_materialization.py` alongside the field
  - Rationale: required, not optional — with the field gone under `extra=forbid` these kwargs raise `TypeError`. The context already named these sites; treating it as part of surface 6.
  - Severity: minor
  - Forward impact: none

### Dev (rework)
- **Fixed a pre-existing out-of-scope dangling import (`OpeningHook` → `Opening`) in the audit script**
  - Spec source: Reviewer Assessment V1 (blocking) — "scripts/audit_content_drift.py will ImportError on next run"
  - Spec text: "Remove `VoicePresets` from the import … so the script imports cleanly"
  - Implementation: also changed `OpeningHook` → `Opening` (import + OPTIONAL tuple) in the same file
  - Rationale: `OpeningHook` was renamed to `Opening` by an earlier narrative rework and is dangling on `develop` too — not introduced by 101-2. But fixing only `VoicePresets` would leave the script still ImportError-ing one line later, defeating the reviewer's actual verification goal. Same file, same defect class, one-line fix → fixed it rather than ship a still-broken tool ("fix it right, no half-fixes").
  - Severity: minor
  - Forward impact: none — `Opening` is the live model the loader already uses for `openings.yaml`

### TEA (test design)
- **AC-3 "grep-guard" implemented as reflection/import assertions, not a source grep**
  - Spec source: context-story-101-2.md, AC-3 ("grep-guard or import test proving no references remain")
  - Spec text: "grep-guard or import test proving no voice_presets/VOICE_SIGNAL/VOICE_TEXT references remain in production code"
  - Implementation: Used `hasattr`/`model_fields`/enum-membership/dict-membership reflection checks, never `read_text()` of production source
  - Rationale: server CLAUDE.md "No Source-Text Wiring Tests" forbids grepping production source as a wiring assertion (passes on stray literals, catastrophic-backtrack hang risk). The AC offered "or import test" — chose that branch.
  - Severity: minor
  - Forward impact: none
- **Removed the two VOICE_* wire-string tests in test_enums.py and flipped the variant count 56 → 54**
  - Spec source: context-story-101-2.md, AC-1 (surfaces removed; suite green)
  - Spec text: "All five server voice surfaces removed; ruff + full server test suite green"
  - Implementation: deleted `test_message_type_voice_signal_wire_string` / `test_message_type_voice_text_wire_string` (they assert the deleted surface) and changed `test_message_type_complete_count` to expect 54
  - Rationale: those tests encode the OLD contract; leaving them would make the suite red after GREEN. Absence is now asserted in the new removal-contract module.
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **Dev — Kept `AudioEffect` instead of deleting the now-dead model** → ✓ ACCEPTED by Reviewer: scope discipline is correct; `AudioEffect` is unlisted and removing it is out-of-scope. Flagged as a follow-up finding, which is the right disposition.
- **Dev — Removed two `voice_id=None` construction kwargs** → ✓ ACCEPTED by Reviewer: required, not optional — the context explicitly named `world_materialization.py:545,874`, and the kwargs would `TypeError` once the field is gone. Correctly treated as part of surface 6.
- **TEA — AC-3 grep-guard as reflection/import assertions** → ✓ ACCEPTED by Reviewer: mandated by the server "No Source-Text Wiring Tests" rule; the AC explicitly offered "or import test". HOWEVER — see Reviewer delivery finding: the reflection guard checked only the package namespace and missed the dangling `scripts/` importer (V1). The branch choice was sound; the guard's *coverage* was too narrow. Accepted with that caveat.
- **TEA — Removed two VOICE_* wire-string tests + flipped count 56→54** → ✓ ACCEPTED by Reviewer: correct TDD hygiene; those tests encode the deleted contract and absence is re-asserted in the new module. Count math verified (56−2=54).
- **Dev (rework) — Fixed a pre-existing out-of-scope dangling import (`OpeningHook` → `Opening`)** → ✓ ACCEPTED by Reviewer: the right call. Fixing only `VoicePresets` would have left the audit script still ImportError-ing one line later, defeating the verification goal of my own blocking finding. `Opening` is the live model the loader uses for `openings.yaml`; rule-checker confirmed zero dangling references remain and the rename is even guarded by `test_opening_hook_deleted.py`. Same file, same defect class, one line — correct to fix rather than ship a still-broken tool.