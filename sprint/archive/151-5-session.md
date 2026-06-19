---
story_id: "151-5"
jira_key: ""
epic: "151"
workflow: "tdd"
---
# Story 151-5: [NARRATOR] Sidecar cutover II — npcs_present (engine-owned side) + async cosmetic fields (mood, visual_scene, footnotes) (ADR-150 step 4)

## Story Details
- **ID:** 151-5
- **Jira Key:** (none — no_jira project)
- **Workflow:** tdd
- **Repos:** server
- **Stack Parent:** 151-2 (done)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T07:04:50Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T05:51:12Z | 2026-06-19T05:53:59Z | 2m 47s |
| red | 2026-06-19T05:53:59Z | 2026-06-19T06:07:53Z | 13m 54s |
| green | 2026-06-19T06:07:53Z | 2026-06-19T06:39:54Z | 32m 1s |
| review | 2026-06-19T06:39:54Z | 2026-06-19T06:52:33Z | 12m 39s |
| red | 2026-06-19T06:52:33Z | 2026-06-19T06:55:40Z | 3m 7s |
| green | 2026-06-19T06:55:40Z | 2026-06-19T06:59:04Z | 3m 24s |
| review | 2026-06-19T06:59:04Z | 2026-06-19T07:04:50Z | 5m 46s |
| finish | 2026-06-19T07:04:50Z | - | - |

## Sm Assessment

**Story selected:** 151-5 — Sidecar cutover II (ADR-150 step 4). Chosen as the active
epic's next unblocked step: 151-4 (cutover I) is `done`, the `depends_on: 151-2` is
`done`, and 151-5 gates the rest of the epic (151-6 → 151-7).

**Scope (routing only):** Continue the field-group cutover off the narrator `game_patch`
hot path onto the post-narration Haiku extractor that landed in 151-2 — this story takes
`npcs_present` (engine-owned side) plus the async cosmetic fields `mood`, `visual_scene`,
`footnotes`. `private_segments` stays narrator-inline (ADR-105 firewall, the one
irreducible field) and is explicitly **out of scope** — that hardening is 151-6.

**Setup state:**
- Session + context written; context seeded with the spec of record
  (`docs/adr/150-...md` step 4), the 151-4 precedent (`sprint/archive/151-4-session.md`),
  and the scope boundary.
- Branch `feat/151-5-sidecar-cutover-ii` created on `develop` (server, gitflow).
- Jira: **skipped** — `no_jira` project, empty `jira_key` (matches 151-4).
- Workflow: `tdd` (phased). First phase **red** → owner **TEA**.

**For TEA (RED):** ACs are not authored in the sprint YAML (no-description story, epic
convention) — define them in RED from ADR-150 step 4 and the cutover-I precedent.
Fixture-based tests only (no live-content coupling). Each moved field must emit
`sidecar_extraction.*` OTEL spans so the GM panel can verify engagement.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Behavioral cutover (retire 4 fields from the game_patch parse, source
them from the post-narration extractor via 2 new merge seams). Not a chore.

**Test Files:**
- `sidequest-server/tests/server/test_151_5_sidecar_cutover_npcs_cosmetic.py` — the
  full RED suite (modeled on the 151-4 transactional-cutover precedent's harness).

**Tests Written:** 19 collected (16 RED + 3 green scope-guards), covering the cutover-II ACs:
- **Retirement** — `extract_structured_from_response` no longer surfaces
  `npcs_present` / `visual_scene` / `scene_mood` / `footnotes` (parametrized ×4) +
  an epic-completion sweep proving ALL 11 bucket-B fields are now retired.
- **Contract trim** — `output_only.md` no longer instructs the four fields; the
  irreducible `private_segments` STAYS (scope guard — its shrink is 151-6).
- **npcs_present** — enrichment from the extractor; **`side` is engine-owned**
  (resolved from `snapshot.encounter.actors`, the extractor's prose-claim ignored);
  sole-source overwrite (No Silent Fallbacks).
- **Cosmetic** — `scene_mood`/`visual_scene`/`footnotes` sourced from the extractor
  (`visual_scene` dict→`VisualScene`); sole-source overwrite.
- **OTEL** — the side-override decision fires a `sidecar_extraction.mismatch` span
  (positive + paranoid no-false-positive negative).
- **Wiring** — both merge seams imported into `websocket_session_handler` (reflection).

**Status:** RED (16 failing — ImportError on the unbuilt seams + retirement/contract
assertions; 3 green scope-guards pass — verified via testing-runner, run 151-5-tea-red).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Every Test Suite Needs a Wiring Test | `test_merge_seams_wired_into_session_handler` | failing |
| No Source-Text Wiring Tests (CLAUDE.md) | reflection on `wsh.__dict__`; artifact asserts are substring on the `output_only.md` deliverable (the blessed 151-3/151-4 exception) | satisfied by construction |
| No Silent Fallbacks / python.md #1 | `test_merge_npcs_present_overwrites_stale_no_fallback`, `test_merge_cosmetic_overwrites_stale_no_fallback` | failing |
| OTEL Observability (CLAUDE.md) | `test_merge_npcs_present_emits_mismatch_span_on_side_override` (+ no-false-positive negative) | failing |
| Engine-owned membership (ADR-150 / SOUL "Bind the Ruleset") | `test_merge_npcs_present_side_from_engine_seated_opponent`, `..._side_neutral_when_engine_unseated` | failing |
| Retirement guard (ADR-150 §Testing strategy) | `test_extract_structured_retires_*` (×5) + `..._still_surfaces_private_segments` | failing / guard-green |
| Test quality, no vacuous asserts (python.md #6) | self-check below | pass |

**Rules checked:** 7 of 7 applicable CLAUDE.md/SOUL/python.md rules have test coverage.
**Self-check:** 0 vacuous tests — every test asserts a specific value (no `assert True`,
no `let _ =`, no `is_none()` on always-None). The one `== []`/no-span negative is paired
with a positive that proves the mechanism exists.

**Handoff:** To Dev (Inigo Montoya) for GREEN. The seam interface is pinned in the test
file's module docstring; the Delivery Findings below flag two open consumer questions.

### Rework (Round-Trip 1) — Reviewer [HIGH] invalid-extractor-side

Reviewer REJECTED the first green: `merge_sidecar_extraction_npcs_present` routes the
Haiku extractor's free-form `npcs_present` dicts through `NpcMention.from_value`, which
RAISES `ValueError` on an out-of-enum `side` (e.g. `"hostile"`) — unwrapped, it crashes
the post-narration turn, violating the epic's NON-FATAL contract. I added **7 failing
tests** (parametrized over `hostile`/`enemy`/`ally`/`friendly` + seated/unseated +
partial-list + mismatch-span) pinning the loud-but-recoverable contract:

- `test_merge_npcs_present_tolerates_invalid_extractor_side[×4]` — bad side must NOT
  raise; mention produced with engine-resolved side (`neutral` unseated) + enrichment.
- `test_merge_npcs_present_invalid_side_resolves_to_engine_seated_opponent` — engine
  opponent wins over the unparseable claim, no crash.
- `test_merge_npcs_present_invalid_side_fires_mismatch_span` — the bad claim fires a
  `sidecar_extraction.mismatch` span (the loud signal), not a crash.
- `test_merge_npcs_present_one_bad_side_does_not_drop_other_mentions` — one malformed
  mention must not abort the whole list.

**Status:** RED (7 failing with `ValueError` today — verified targeted). **Dev fix:** a
per-mention `try/except ValueError` (or read the claimed side defensively without the
strict parse); on a bad/out-of-enum side, build the mention with `side` set to the
engine-resolved value and emit the mismatch span — never raise into the turn pipeline.
The five non-blocking Reviewer findings (span status, unbounded list, exact-name match,
phantom-NPC, getattr) are tracked in Delivery Findings for follow-up, not pinned here.

## Dev Assessment

**Implementation Complete:** Yes
**Branch:** `feat/151-5-sidecar-cutover-ii` (pushed to origin, PR-ready)

**Files Changed — production (4):**
- `sidequest/agents/orchestrator.py` — `extract_structured_from_response` retires
  `npcs_present`/`visual_scene`/`scene_mood`/`footnotes` (surface `[]`/`None`).
- `sidequest/server/narration_apply.py` — NEW `merge_sidecar_extraction_npcs_present`
  (enrichment from extractor, **engine-owned `side`** via `_engine_actor_sides` reading
  `snapshot.encounter.actors`, `sidecar_extraction.mismatch` span on override) + NEW
  `merge_sidecar_extraction_cosmetic` (`scene_mood`/`visual_scene` dict→`VisualScene`/
  `footnotes`). Both sole-source.
- `sidequest/server/websocket_session_handler.py` — imports + calls both seams in the
  post-narration block (after the extractor watcher, before apply).
- `sidequest/agents/narrator_prompts/output_only.md` — removed the four field
  instruction blocks + their guardrails (215→145 lines); `private_segments` kept.

**Files Changed — tests (9):** inverted the OLD-contract assertions to retirement
assertions following the 151-3/151-4 precedent — `test_orchestrator.py`,
`test_narration_extraction.py`, `test_narrator.py`, `test_narrator_prompt.py`,
`test_narrator_sdk_hybrid_split.py`, `test_57_4_recency_guardrails_migration.py`,
`test_61_12_output_format_compaction.py` (REQUIRED_TOKENS pruned with a 151-5 banner),
`test_e2e/test_orchestrator_e2e.py`; removed the two obsolete 151-4 "keeps deferred"
guards (superseded by the 151-5 suite).

**Tests:** GREEN within the 151-5 blast radius — `tests/agents/` (1609 tests), the new
`test_151_5` (17/17), `test_151_4`, and the NPC catch-loop server tests all pass
(verified via testing-runner runs 151-5-dev-green-2 + 151-5-dev-green-sweep). The sweep
surfaced **12 failures, ALL pre-existing content-seeding baseline** failures
(`EncounterSeedError` on caverns_and_claudes WWN bestiary + chargen-e2e sequencing) in
`tests/e2e/` — proven unrelated: `git diff HEAD` touches only the narrator sidecar path
(extract / merge seams / prompt / WS post-narration wiring), nothing in
encountergen/bestiary/chargen/seed. My edited e2e test fails at that pre-existing
`EncounterSeedError` *before* reaching its (correct) updated assertions; not reverted.

### Rework (Round-Trip 1) — fixed Reviewer [HIGH] invalid-extractor-side

**Fix:** `merge_sidecar_extraction_npcs_present` (`narration_apply.py`) now tolerates an
out-of-enum extractor `side`. Since `side` is engine-owned and overwritten, the merge
captures the raw claimed side defensively (`str((raw.get("side") if isinstance(raw,dict)
else None) or "neutral")`) for the `sidecar_extraction.mismatch` witness, then parses
enrichment via `NpcMention.from_value(safe_raw)` where `safe_raw` forces a validator-safe
`side="neutral"` — so `from_value` never sees (and never raises on) the bad value. A
bad/out-of-enum claim now fires the mismatch span and the mention resolves to the
engine-adjudicated side; the merge NEVER raises into the WS turn pipeline (honoring the
epic's NON-FATAL contract). Partial-list integrity preserved (one bad mention no longer
aborts the rest). One-function change; no other code path touched.

**Tests:** GREEN — the 151-5 suite is 26/26 (19 original + 7 rework); the focused
regression sweep (`tests/agents/` + the 151 + NPC catch-loop server tests) is **1588
passed, 0 failed** (run 151-5-dev-green-rework). The 12 `tests/e2e/` content-seeding
baseline failures remain pre-existing and out of scope (unchanged by this one-function
fix). Committed + pushed (`4d0905ac`).

**Note on the 5 non-blocking Reviewer findings:** left as Delivery Findings for follow-up
(not in 151-5's scope) — the span-status-UNSET, unbounded-list cap, exact-name matching,
phantom-NPC grounding, and `getattr` style. None are blocking; flagged for a future
hardening story / 151-6.

**Handoff:** To Reviewer (Westley) for re-review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): `NpcMention.disengaged` provenance is unresolved by ADR-150.
  It is a narrator membership-departure signal (ADR-116 social end-on-no-Other) currently
  emitted in `npcs_present` and consumed by `_apply_opponent_disengagements`. After the
  cutover `npcs_present` comes from the extractor — is `disengaged` engine-owned (like
  `side`) or an extractor prose-read ("the zombie walks away")? I did NOT pin it (left to
  Dev). Affects `narration_apply.merge_sidecar_extraction_npcs_present` +
  `_apply_opponent_disengagements` (`sidequest/server/narration_apply.py:5180`).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): the no-emission lie-detector at
  `narration_apply.py:5293` reads `m.side == "opponent"` on `result.npcs_present` to catch
  "prose named an adversary but engaged nothing". Once `side` is engine-owned, its
  `_no_active_encounter AND _named_opponent` condition may go vacuous (an engine-seated
  opponent always implies an active encounter). Dev should decide whether to read the
  extractor's CLAIMED side (pre-merge) there, or retire it in favor of the new
  `sidecar_extraction.mismatch` witness. Affects `sidequest/server/narration_apply.py:5293`.
  *Found by TEA during test design.*

### Dev (implementation)
- **Resolved TEA Q1 (`disengaged` provenance):** I left `disengaged` as an
  EXTRACTOR-read enrichment field (the merge builds mentions via `NpcMention.from_value`,
  which reads `disengaged` from the extractor dict). Only `side` is engine-owned. Rationale:
  the engine has no other signal for SOCIAL opponent departure (ADR-116 note —
  `opponents_disposition` is morale-only), so the extractor reading "the zombie walks away"
  → `disengaged=True` is the correct source; `_apply_opponent_disengagements` only acts on
  `side="opponent"` mentions, and `side` is now engine-resolved, so a prose-only departure
  cannot withdraw a non-seated actor. No test pinned a stricter contract. *Found by Dev during implementation.*
- **Improvement** (non-blocking): TEA Q2 confirmed — the no-emission lie-detector at
  `narration_apply.py:5293` (`_named_opponent = any(m.side == "opponent" ...)` gated by
  `_no_active_encounter`) is now effectively DEAD: with `side` engine-owned, a
  `side="opponent"` mention implies a seated opponent, which implies an active encounter,
  so `_no_active_encounter AND _named_opponent` can never both hold. I did NOT rewire it
  (out of 151-5's minimal scope; no test required it). 151-6/151-7 should rewire it to read
  the extractor's CLAIMED side (pre-merge) or retire it in favor of the
  `sidecar_extraction.mismatch` witness. Affects `sidequest/server/narration_apply.py:5293`.
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): 151-5 removed the npcs_present/visual_scene EMISSION
  guardrails (CRITICAL ADVERSARY RULE, RECURRING PRESENCE RULE) from `output_only.md`. The
  recurring-NPC / adversary-visibility guarantee now rests on the extractor + the catch-loops
  (`_detect_missed_recurring_npcs` / `_auto_mint_prose_only_npcs`). 151-6 (the prompt shrink
  to "prose + private_segments brief") should consider adding light PROSE-CRAFT guidance that
  the narrator MENTION recurring NPCs + adversaries in prose, so the extractor has text to
  read. Affects `output_only.md` (151-6 scope). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): the npcs_present merge can RAISE into the WS turn pipeline — see the
  [HIGH] finding in the Reviewer Assessment. `NpcMention.from_value` raises `ValueError` on
  an out-of-enum extractor `side`; unwrapped at `narration_apply.py:3678`. Affects
  `sidequest/server/narration_apply.py` (the merge loop). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `sidecar_extraction.mismatch` span on side-override
  leaves OTEL status UNSET (vs `sidecar_extraction_failed_span`'s explicit ERROR), so the GM
  panel surfaces a side disagreement as an INFO breadcrumb. Consider WARNING/ERROR. Affects
  `sidequest/server/narration_apply.py` (the mismatch emit). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `SidecarExtraction.npcs_present` is an unbounded
  `list[dict[str, Any]]` (no `max_length`); a malfunctioning Haiku emitting hundreds of dicts
  amplifies per-turn work. Low risk (API token cap). Consider a capped field + truncation span.
  Affects `sidequest/agents/sidecar_extractor.py:107`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_engine_actor_sides` matches by EXACT name; an extractor
  name differing in case/pluralization from the engine's canonical seated-actor name labels a
  seated OPPONENT's mention `neutral` (and fires a false mismatch span). Engine seating is
  unaffected; only the npcs_present label diverges. Affects
  `sidequest/server/narration_apply.py:3682`. *Found by Reviewer during code review.*
- **Question** (non-blocking): the extractor is a NEW confabulation surface — an
  extractor-invented NPC absent from prose flows into `_apply_npc_mentions` and can be minted;
  the existing catch-loops only catch the inverse (prose-named-but-omitted). Should
  `detect_sidecar_extraction_mismatch` gain a prose-grounding check? Affects
  `sidequest/agents/sidecar_extractor.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `getattr(snapshot, "encounter", None)` — `encounter` is a
  typed always-present field (`session.py:861`); use `snapshot.encounter`. Style only. Affects
  `sidequest/server/narration_apply.py:3653`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, re-review): in the rework's `claimed_side` capture, a
  FALSY-but-present extractor `side` (e.g. `0`, `[]`, `False`) is normalized to `"neutral"`
  by `... or "neutral"` and, when the NPC is also unseated, fires no mismatch span — the
  malformed value goes unobserved. LOW: matches `from_value`'s own `or "neutral"` convention
  (orchestrator.py:430) and a non-string `side` from a JSON-reading Haiku is pathological. A
  future hardening could distinguish absent (`None`) from falsy-present. Affects
  `sidequest/server/narration_apply.py` (the `claimed_side` line). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Two merge seams instead of 151-4's one**
  - Spec source: ADR-150 §Ordering and latency; story title ("async cosmetic fields")
  - Spec text: "npcs_present enrichment … settle before fan-out" (pre-broadcast) vs "mood, visual_scene, footnotes may be spawned via asyncio.create_task … off the critical path"
  - Implementation: pinned `merge_sidecar_extraction_npcs_present` (pre-broadcast, needs the snapshot for engine-owned side) and `merge_sidecar_extraction_cosmetic` (separate) rather than one combined seam
  - Rationale: the two field groups have different latency homes; separate seams are the structural enabler for scheduling cosmetic async
  - Severity: minor
  - Forward impact: Dev implements two functions; 151-6 prompt-shrink unaffected
- **Async scheduling (asyncio.create_task) NOT unit-pinned**
  - Spec source: ADR-150 §Ordering and latency
  - Spec text: cosmetic fields "MAY be spawned via asyncio.create_task and arrive a beat after the prose"
  - Implementation: pinned the seam SEPARATION (the enabler) but not the create_task call itself
  - Rationale: "MAY" is permissive; a fixture unit test of create_task is brittle and couples to the WS event loop. The async behavior (prose not blocked) is a 151-7 playtest-gate concern
  - Severity: minor
  - Forward impact: 151-7 validates the async scheduling end-to-end; Dev may implement cosmetic sync-after-broadcast or async without breaking these tests
- **No npcs_present merge→apply end-to-end test (unlike 151-4's gold/items/companions e2e)**
  - Spec source: 151-4 precedent (`tests/server/test_151_4_sidecar_cutover_transactional.py`)
  - Spec text: 151-4 drove merge→`_apply_narration_result_to_snapshot`→state for each transactional lane
  - Implementation: 151-5 pins the merge result (`result.npcs_present` populated correctly) + the reflection wiring test, but no full npc-mint e2e
  - Rationale: `_apply_npc_mentions` is UNCHANGED and heavily covered by existing tests; an npc-mint e2e would couple to the observation-gate/minter machinery unrelated to this cutover
  - Severity: minor
  - Forward impact: none — the apply path is reused, not modified
- **OTEL `sidecar_extraction.mismatch` emitted from the merge seam**
  - Spec source: ADR-150 §Telemetry; CLAUDE.md OTEL Principle
  - Spec text: "`sidecar_extraction.mismatch` — a lie-detector span … when the extractor's output disagrees with what the engine/state already holds"
  - Implementation: pinned the span to fire from `merge_sidecar_extraction_npcs_present` (the point of the side-override decision), not only the pre-merge `run_sidecar_extraction_watcher`
  - Rationale: the override decision is MADE in the merge; CLAUDE.md requires the decision be observable where it happens
  - Severity: minor
  - Forward impact: Dev emits the span in the npcs merge; the existing watcher's name-vs-cast mismatch is unaffected

### Dev (implementation)
- **Removed the two ADR-111-migrated NPC guardrails from `output_only.md`**
  - Spec source: ADR-150 step 4 (retire npcs_present/visual_scene emission) vs ADR-111 §Decision (which had migrated `npc_intro_visual_constraint` / `npc_extraction_constraint` INTO output_only.md)
  - Spec text: ADR-150 — "each retiring its sidecar emission as the extractor takes over"; ADR-111 — "sidecar-field guardrails go to the sidecar SDK prose"
  - Implementation: removed the "Recurring NPCs" / "Patients on a sickbed count" guardrail prose with the npcs_present/visual_scene blocks; the guardrail CONSTANTS stay dormant (`test_each_constant_carries_its_load_bearing_fingerprint` still pins them); `test_57_4`'s placement test inverted to assert retirement
  - Rationale: ADR-150 supersedes the ADR-111 PLACEMENT for these two guardrails — their host fields are retired, so the recurring-presence/adversary guarantee moves to the extractor + catch-loops
  - Severity: minor
  - Forward impact: 151-6 may relocate prose-craft "mention recurring NPCs" guidance into the prose section (flagged as a Delivery Finding)
- **Cosmetic merge called SYNCHRONOUSLY (not via `asyncio.create_task`)**
  - Spec source: ADR-150 §Ordering and latency; story title ("async cosmetic fields")
  - Spec text: cosmetic fields "MAY be spawned via asyncio.create_task and arrive a beat after the prose"
  - Implementation: `merge_sidecar_extraction_cosmetic` is called inline in the WS handler's post-narration block (sync-after-narration), like the transactional merge
  - Rationale: minimal (the simplest code that passes the seam tests); "MAY" is permissive; the async scheduling is a perf optimization validated in 151-7. The seam is SEPARATE from the npcs merge, so a future async wrap needs no contract change (matches TEA's two-seam deviation)
  - Severity: minor
  - Forward impact: 151-7 may wrap the cosmetic merge in `create_task` for the off-critical-path latency win without changing the seam contract

### Reviewer (audit)
- **TEA — Two merge seams instead of one** → ✓ ACCEPTED: matches ADR-150 §Ordering (npcs pre-broadcast vs cosmetic async); the seam separation is the correct structural enabler.
- **TEA — Async scheduling not unit-pinned** → ✓ ACCEPTED: "MAY" is permissive; async is a 151-7 playtest concern. Sound.
- **TEA — No npcs merge→apply e2e** → ✓ ACCEPTED: `_apply_npc_mentions` is unchanged and well-covered; the merge-result + reflection-wiring tests are adequate at this seam.
- **TEA — OTEL mismatch from the merge seam** → ✓ ACCEPTED: emitting the override decision at the decision point is correct OTEL discipline (note: status-UNSET is a non-blocking follow-up I filed).
- **Dev — Removed the two ADR-111-migrated NPC guardrails** → ✓ ACCEPTED: ADR-150 step 4 retires the host fields' EMISSION, so their emission guardrails go with them; the constants stay dormant and the guarantee moves to extractor + catch-loops. Correctly flagged the 151-6 prose-craft follow-up.
- **Dev — Cosmetic merge called synchronously** → ✓ ACCEPTED: minimal + "MAY"; the separate seam preserves a no-contract-change path to async in 151-7.
- **UNDOCUMENTED (Reviewer):** Spec/contract (ADR-150, `sidecar_extractor.py:17-19`) says the post-narration pass is NON-FATAL and "never raises into the WS turn pipeline." The new `merge_sidecar_extraction_npcs_present` CAN raise into the turn pipeline via `NpcMention.from_value` (unwrapped). Neither TEA nor Dev logged this divergence from the non-fatal contract. **Severity: High.** See the Reviewer Assessment.
  - → ✓ RESOLVED in rework (Round-Trip 1): the merge now reads the claimed side defensively and forces a validator-safe `side="neutral"` into `from_value`, so it never raises; the bad claim surfaces via the `sidecar_extraction.mismatch` span. The non-fatal contract is honored. Confirmed by re-review (preflight 26/26 + silent-failure + security all RESOLVED).
- **Re-review audit (Round-Trip 1):** the rework introduced NO new logged deviations — it is a fix for the round-1 [HIGH], one-function change. The round-1 deviation stamps above stand.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | tests GREEN (222 targeted), lint clean, 0 smells, e2e-preexisting VERIFIED, 1 note (empty-body span) | confirmed 0, dismissed 0, deferred 1 (span note → resolved: span fires) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 1 (from_value raise), deferred 3 (LOW: span status, getattr, cosmetic non-dict) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 1 (from_value raise — corroborates #3), deferred 1 (LOW: unbounded list); VERIFIED firewall intact + engine-side improvement + no log-injection |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 confirmed blocking (HIGH, corroborated by 2 specialists), 5 deferred non-blocking (LOW/Improvement), 0 dismissed

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `merge_sidecar_extraction_npcs_present` routes semi-trusted extractor output through `NpcMention.from_value`, which RAISES `ValueError` on an out-of-enum `side` (e.g. `"hostile"` — a plausible Haiku output, since the extractor model gives NO `side` schema guidance and "hostile" is the old `role` enum value). The call is UNWRAPPED, so the raise propagates into the WS turn pipeline AFTER the Opus call, crashing/degrading the turn. This violates the epic's ratified NON-FATAL contract (`sidecar_extractor.py:17-19`: the post-narration pass "never raises into the WS turn pipeline; the per-field catch-loops are the net"). Compounding: the validated `side` is IMMEDIATELY DISCARDED (overwritten by `engine_side` at :3691) — the validation can only crash, never help. | `sidequest/server/narration_apply.py:3678` (call site `websocket_session_handler.py:1175`, no enclosing try) | Per-mention `try/except ValueError`: on a bad side, build the mention with `side` clamped to the engine-resolved value (membership is engine-owned anyway) and emit the `sidecar_extraction.mismatch` span; never raise into the turn. Add a TEA test: an extraction with `npcs_present=[{"name":"X","side":"hostile"}]` (engine seats X / unseated) → merge tolerates it, side resolves from the engine, mismatch span fires, turn does not crash. |

### Rule Compliance (python.md lang-review checklist, 13 checks vs the changed `.py` files)

- **#1 Silent exceptions** — No swallowed errors. INVERSE problem: an UNHANDLED raise that aborts the turn → the [HIGH] finding (violates the non-fatal contract).
- **#2 Mutable defaults** — Compliant. No mutable default args in `_engine_actor_sides` / the two merges.
- **#3 Type annotations** — Compliant. All three new functions fully annotated (params + returns).
- **#4 Logging/OTEL** — Mostly compliant: the override decision emits `sidecar_extraction.mismatch`. Gap: the `from_value` crash path emits NO span/log before propagating (part of the [HIGH] finding); the mismatch span status is UNSET (LOW, filed).
- **#5 Path handling** — N/A (no path ops).
- **#6 Test quality** — Compliant for what's tested (specific asserts, no vacuous checks; REQUIRED_TOKENS pruned with a banner). Gap: NO test covers the invalid-extractor-`side` path (the [HIGH] finding is untested).
- **#7 Resource leaks** — N/A.
- **#8 Unsafe deserialization** — Compliant. No pickle/eval/unsafe-yaml; `from_value` is plain dict parsing.
- **#9 Async** — Compliant. The merges are sync (no blocking I/O inside the async handler); cosmetic-sync is Dev's logged deviation.
- **#10 Import hygiene** — Compliant. Local runtime imports inside the merges (NpcMention/VisualScene/span) match this file's established circular-import-avoidance idiom; no star imports.
- **#11 Input validation at boundaries** — VIOLATION: the semi-trusted extractor output reaches `from_value` without graceful invalid-`side` handling (the [HIGH] finding). Also the unbounded `npcs_present` list (LOW, filed).
- **#12 Dependency hygiene** — N/A (no dep changes).
- **#13 Fix-introduced regressions** — N/A (first review pass).

### Observations (10)

1. `[HIGH][SILENT][SEC][RULE]` Unwrapped `from_value` raise — crashes the turn on a plausible extractor side; violates the non-fatal contract; validates-then-discards. `narration_apply.py:3678`. CONFIRMED (silent-failure + security).
2. `[LOW][SILENT]` mismatch span status UNSET (not ERROR/WARNING) — GM panel under-surfaces a side disagreement. `narration_apply.py` (mismatch emit). Non-blocking, filed.
3. `[LOW][SILENT]` `getattr(snapshot,"encounter",None)` over a typed always-present field — misleading; use `snapshot.encounter`. `narration_apply.py:3653`. Non-blocking, filed.
4. `[LOW][SILENT]` cosmetic merge silently `visual_scene=None` on a non-dict extractor value, no span/log. `narration_apply.py` (cosmetic). Low-probability (pydantic `dict|None`). Non-blocking, filed.
5. `[LOW][SEC]` `SidecarExtraction.npcs_present` unbounded — per-turn amplification. `sidecar_extractor.py:107`. Low (API token cap). Non-blocking, filed.
6. `[MEDIUM-as-LOW]` exact-name matching can mislabel a seated opponent's mention `neutral`. `narration_apply.py:3682`. Filed as a delivery finding (engine seating unaffected).
7. `[VERIFIED]` Perception firewall intact — `private_segments` untouched in `extract_structured_from_response` (the `_private_segments` path is unchanged); `output_only.md` KEEPS the `private_segments` block + PERCEPTION FIREWALL section (grep: 4 occurrences). Complies with ADR-105 (the SACROSANCT rule). Evidence: prod diff removes only the 4 retired field blocks; firewall section untouched.
8. `[VERIFIED][SEC]` Engine-owned `side` is a genuine security improvement — the merge overwrites the extractor's claimed side with `snapshot.encounter.actors` (`narration_apply.py:3682,3691`), so prose can no longer spoof combatant membership. Complies with SOUL "Bind the Ruleset" / ADR-150.
9. `[VERIFIED]` Sole-source overwrite (No Silent Fallbacks) — `result.npcs_present = mentions` (:3693) and the cosmetic assignments unconditionally overwrite; no fall-back to stale values. Pinned by `test_merge_*_overwrites_stale_no_fallback`.
10. `[VERIFIED]` e2e failures pre-existing — `git diff develop...HEAD` touches zero encounter-seed/bestiary/chargen code; the 12 `EncounterSeedError`/chargen failures are content-tier baseline (preflight VERIFIED).

**Dispatch tags:** `[EDGE]` disabled · `[SILENT]` confirmed (obs 1) + 3 deferred · `[TEST]` disabled (assessed inline: missing invalid-side test — obs 1, rule #6) · `[DOC]` disabled · `[TYPE]` disabled · `[SEC]` confirmed (obs 1) + 1 deferred + 2 verified · `[SIMPLE]` disabled · `[RULE]` disabled (assessed inline in Rule Compliance: #11 violation).

**Data flow traced:** player action → narrator (Opus) prose+game_patch → `extract_structured_from_response` zeroes the 4 fields → `run_sidecar_extraction_watcher` (Haiku) → `SidecarExtraction` → **`merge_sidecar_extraction_npcs_present` (CRASH POINT on invalid `side`)** + `merge_sidecar_extraction_cosmetic` → `_apply_narration_result_to_snapshot` → broadcast. The crash point is the [HIGH] finding.

**Wiring verified:** both seams imported into `websocket_session_handler` (the 151-5 reflection wiring test passes) and called between the watcher and apply (`websocket_session_handler.py:1173-1176`). Reachable end-to-end.

**Error handling / hard questions:** empty extraction → empty result (overwrite, correct). No encounter → `_engine_actor_sides` returns `{}` → all neutral (correct). Invalid `side` → **uncaught crash** (the finding). Huge list → unbounded (LOW). Non-dict `visual_scene` → silent None (LOW). Case-mismatched name → opponent mislabeled neutral (filed).

### Devil's Advocate

This code is broken on a turn that already cost an Opus call. The narrator writes "the bandit lunges," the post-narration Haiku extractor — handed a free-form `list[dict]` schema with *zero guidance* about the `side` enum — reads the prose and emits `npcs_present:[{"name":"the bandit","side":"hostile"}]`. "Hostile" is not a guess from nowhere: it is the exact word the OLD `role` enum used, so a model conflating role and side reaches for it naturally. `NpcMention.from_value` rejects it with a `ValueError`, the merge has no per-mention guard, and the exception rides up through an unwrapped call site into the WS turn pipeline. The player submitted a turn, the engine spent the most expensive model in the stack, and the result is a crashed or degraded turn — the precise failure mode ADR-150 wrote a NON-FATAL contract to prevent. Worse, the rejected field is one the code throws away two lines later, so the system crashes guarding a value it does not use. A confused extractor breaks the game; that is not resilience.

Even setting the crash aside, a malicious or jailbroken extractor turn has room to misbehave: it can invent an NPC that never appears in the prose, and because the catch-loops only police the inverse direction (prose-named-but-omitted), the phantom flows into `_apply_npc_mentions` and gets minted into the pool — a new confabulation surface the narrator-era nets never had to watch. A merely *careless* extractor that re-cases or pluralizes a seated opponent's name ("The Bandits" vs "Bandit") silently demotes that opponent's mention to `neutral` while firing a misleading mismatch span, so the GM panel sees a "disagreement" that is really a string-matching artifact. And an unbounded `npcs_present` list lets a runaway model amplify per-turn work across every concurrent session. None of these are theoretical in the sense of "requires an attacker" — they are ordinary LLM sloppiness against a contract that assumed a disciplined producer. The fix for the blocker is small and the rest are cheap hardening, which is exactly why they should be done before this reaches a real table rather than discovered live by Keith.

**Handoff:** Back to TEA (Fezzik) for red rework — the [HIGH] finding is a testable logic bug (add a failing test for the invalid-extractor-`side` path), then Dev makes it green.

---

# Re-review (Round-Trip 1)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 26/26 GREEN, all 7 rework tests pass, lint clean, 0 smells | confirmed 0, dismissed 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (LOW) — [HIGH] RESOLVED | deferred 1 (falsy-present side, matches existing convention) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A |
| 7 | reviewer-security | Yes | findings | 1 (LOW) — [HIGH] RESOLVED | dismissed 1 (`!r` quoting unchanged, OTEL not an execution surface; "no action needed") |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A |

**All received:** Yes (3 enabled returned; 6 disabled via settings)
**Total findings:** 0 blocking, 1 deferred non-blocking (LOW), 1 dismissed (verified non-issue); the round-1 [HIGH] is RESOLVED by both silent-failure and security specialists.

## Reviewer Assessment

**Verdict:** APPROVED

The round-1 [HIGH] is RESOLVED. The rework makes `merge_sidecar_extraction_npcs_present`
tolerate an out-of-enum extractor `side`: it captures the raw claim defensively
(`str((raw.get("side") if isinstance(raw,dict) else None) or "neutral")`) for the
`sidecar_extraction.mismatch` witness, then forces a validator-safe `side="neutral"` into
`NpcMention.from_value(safe_raw)` — so `from_value` can no longer raise on ANY extractor side
(dict path forced neutral; bare-string/None path takes from_value's no-validation branch).
The merge no longer raises into the WS turn pipeline (the epic's NON-FATAL contract holds),
the bad claim is surfaced loudly via the mismatch span, the engine still adjudicates the real
`side` (no spoofing — a seated opponent resolves to `opponent` regardless of the claim), and
partial-list integrity is preserved (one bad mention no longer aborts the rest). The fix is a
12-line single-function change consistent with the existing `from_value` `or "neutral"`
convention (orchestrator.py:430).

**Dispatch tags:** `[EDGE]` disabled · `[SILENT]` [HIGH] RESOLVED + 1 deferred LOW (falsy-present side) · `[TEST]` disabled (assessed inline: the 7 rework tests pin no-raise / engine-side / mismatch-span / partial-list — specific, non-vacuous) · `[DOC]` disabled · `[TYPE]` disabled · `[SEC]` [HIGH] RESOLVED + 1 dismissed (`!r` quoting, non-issue) · `[SIMPLE]` disabled · `[RULE]` disabled (python.md #11 input-validation — now compliant: bad extractor side degrades loudly, never crashes).

### Observations (re-review)

1. `[VERIFIED]` [HIGH] RESOLVED — `from_value(safe_raw)` cannot raise on any side (dict → forced `"neutral"`; non-dict → from_value's bare-value branch never checks side). Evidence: `narration_apply.py` rework + orchestrator.py:425-451; preflight 26/26.
2. `[VERIFIED]` Loud, not silent — a bad claim (`"hostile"` vs engine `"neutral"`) fires the `sidecar_extraction.mismatch` span with the bad value in `evidence`. Pinned by `test_merge_npcs_present_invalid_side_fires_mismatch_span`.
3. `[VERIFIED][SEC]` No spoofing — `mention.side = engine_side` (from `snapshot.encounter.actors`) is the only persisted write; a prose-claimed opponent cannot survive as anything but the engine's seating. Pinned by `..._invalid_side_resolves_to_engine_seated_opponent`.
4. `[VERIFIED]` Partial-list integrity — the loop has no `break`/`raise`; one malformed mention does not drop siblings. Pinned by `..._one_bad_side_does_not_drop_other_mentions`.
5. `[LOW][SILENT]` Falsy-but-present side (`0`/`[]`) normalized to `"neutral"` without a mismatch span when also unseated — matches the existing `from_value` convention; pathological for a JSON-reading Haiku. Deferred (delivery finding).
6. `[VERIFIED]` No new deviations; round-1 deviation audit stands. The five other round-1 non-blocking findings remain filed as delivery findings for follow-up (not in 151-5 scope).

**Deviation audit (re-review):** stamped in the Design Deviations section — the round-1 UNDOCUMENTED High is marked RESOLVED; the rework added no new deviations.

**Data flow / regression:** the one-function change is exercised by the 26/26 151-5 suite; the focused regression sweep (`tests/agents/` + 151 + NPC catch-loop tests) is 1588 passed / 0 failed. The 12 `tests/e2e/` failures remain pre-existing content-seeding baseline (unchanged).

**Handoff:** To SM (Vizzini) for finish-story.