---
story_id: "126-10"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-10: [PERF/FATE] intent_router_pass 37-81s spikes on Fate worlds — trim build_fate_projection router prompt (separate from 126-9 narrator fix)

## Story Details
- **ID:** 126-10
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-18T10:15:38Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T09:37:38Z | 2026-06-18T09:39:44Z | 2m 6s |
| red | 2026-06-18T09:39:44Z | 2026-06-18T09:53:03Z | 13m 19s |
| green | 2026-06-18T09:53:03Z | 2026-06-18T10:05:29Z | 12m 26s |
| review | 2026-06-18T10:05:29Z | 2026-06-18T10:15:38Z | 10m 9s |
| finish | 2026-06-18T10:15:38Z | - | - |

## Story Summary

**Symptom:** intent_router_pass phase spikes to 37-81s on a SINGLE call (phase_call_counts=1, so NOT thrash) on Fate worlds — observed on pulp_noir/annees_folles (one session avg 162s/turn). Non-Fate worlds show ~4-6s baseline for the same phase.

**Mechanism:** intent_router_pass.py:364-365 injects `build_fate_projection` (the shared narrator/router projector at ~line 234: PC skills + ALL live aspects) into the router state_summary ONLY when `pack.rules.ruleset=='fate'`. This enlarges the router prompt. The router's single Haiku call is structured (output_format set, llm_factory.py:399-405) so #919 already disabled ITS thinking — thinking-off (126-9) will NOT fix this. On the bloated Fate prompt the structured call intermittently can't land the finalize inside the mandatory max_turns=2 floor -> error_max_turns fragility, surfacing as a slow single call.

**Why Separate from 126-9:** 126-9 fixes the narrator (agent_duration_ms, the dominant cost, HIGH confidence, thinking-off). This story is the router-phase Fate prompt bloat (MEDIUM confidence, needs the trim). Do 126-9 first; re-measure; this may shrink once general load drops, but the Fate prompt is the structural lever.

**Lever:** Trim `build_fate_projection` for the ROUTER prompt (the router likely needs far less than the narrator — PC skills maybe, not every live aspect). Confirm empirically on annees_folles turn_telemetry before/after.

## Sm Assessment

**Verdict:** Ready for RED. Diagnosis is pinned, prereq is cleared, repo is single (`server`).

**Why this story, now:** Only p2 in the backlog. Player-facing latency — Fate worlds (pulp_noir/annees_folles) average ~162s/turn with this phase spiking 37–81s on a *single* call vs ~4–6s non-Fate baseline. That's the whole table watching a spinner; it hits every seat. Prereq 126-9 (narrator thinking-off) is merged — the Fate prompt bloat is now the standing structural lever, independent of thinking.

**Routing notes for TEA (Amos):**
- This is a perf story, but **don't write a wall-clock test** — flaky and non-deterministic. Frame RED around the *structural* property that causes the spike: the router's `build_fate_projection` injection (`intent_router_pass.py:364-365`) currently carries the full narrator projection (PC skills + ALL live aspects, ~line 234). Assert the **router variant is bounded** — i.e., it excludes the full live-aspects dump and carries only what the router needs (PC skills, per the lever). A size/content assertion fails RED on the current bloated projection and passes once trimmed.
- Per the **OTEL Observability Principle**: the trim must emit a watcher event on the router projection decision (e.g., `intent_router.decompose` span carrying projection size / aspect-count) so the GM panel can verify the lever engaged — not just that narration looks fine. Add this to the RED expectations.
- **Verify empirically before/after** on `annees_folles` turn_telemetry (`intent_router_pass` phase timing) — that's the acceptance evidence, separate from the deterministic unit gate.
- Key files: `intent_router_pass.py` (injection site ~364-365, projector ~234), `llm_factory.py:399-405` (structured call, thinking already off — do NOT re-touch thinking, that was 126-9).
- **Do not balance native mechanics into this** — pure prompt trim on the router path. No engine reshaping.

**Base branch:** server PRs target per `repos.yaml` — Dev/Reviewer confirm at PR time; do not assume.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Perf/observability bug with a structural lever — deterministic tests pin the trim, the OTEL evidence, and the production wiring; the wall-clock recovery itself stays an empirical playtest gate.

**Test File:**
- `sidequest-server/tests/server/test_fate_classifier_enrichment.py` — extended the existing Fate-classifier-enrichment suite (fixtures `_pc` / `_conflict_snapshot` / `_fate_pack` / `_dial_pack` already present) with a fat-aspect snapshot helper (`_fat_conflict_snapshot`, 9 distinct planted live-aspect texts) + 6 new tests.

**Tests Written:** 6 new — RED state verified by Machine Shop (3 fail, 7 pass; all 3 failures are genuine assertion failures, not import/collection).

RED — the new behavior Dev implements:
- `test_router_fate_block_trims_live_aspects` — router Fate block carries strictly FEWER live aspects + strictly smaller serialized than the full narrator projection (today `intent_router_pass` ships `build_fate_projection` verbatim → 9 < 9 fails).
- `test_fate_vocabulary_span_fires_with_trim_evidence` — `intent_router.fate_vocabulary` span fires once with `bytes_after < bytes_before` + `skill_count` + `genre_slug` (today no span → 0 == 1 fails).
- `test_pre_narrator_pass_ships_trimmed_fate_block` — production `execute_intent_router_pre_narrator_pass` ships the trimmed block to `decompose` (today ships full → 9 < 9 fails).

GREEN guards — pass now, MUST stay green through the fix:
- `test_router_fate_block_preserves_routing_essentials` — per-PC skills + `active_conflict` survive the trim (don't over-trim / AC2).
- `test_narrator_fate_projection_unchanged_by_router_trim` — `build_fate_projection(snap)` (the narrator's exact call at `session_helpers.py:1267`) keeps every live aspect (anti-confabulation, ADR-144 F2b).
- `test_no_fate_vocabulary_span_for_non_fate_pack` — non-Fate packs carry no Fate block and fire no span.

**Status:** RED (3 failing / 7 passing).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL Observability Principle (CLAUDE.md; lang-review #4 observability) | `test_fate_vocabulary_span_fires_with_trim_evidence` | failing (RED) |
| Every Test Suite Needs a Wiring Test (CLAUDE.md) | `test_pre_narrator_pass_ships_trimmed_fate_block` | failing (RED) |
| No Source-Text Wiring Tests (CLAUDE.md) | wiring test is fixture-driven behavior + `decompose` call-arg assertion (not a source grep) | compliant |
| Test quality (lang-review #6 — specific-value assertions, correct mock target) | all 6 (counts / bytes / exact skill dicts; `decompose` patched where used) | self-checked clean |

**Rules checked:** the 2 applicable lang-review rules (#4 observability, #6 test quality) + 2 CLAUDE.md wiring rules have coverage. #1/#2/#3/#5/#7/#8 (exceptions, mutable defaults, boundary types, paths, resource leaks, deserialization) are N/A to a prompt-trim + span change.
**Self-check:** 0 vacuous tests (no `assert True`, no bare-truthy on always-true values).

**Handoff:** To Dev (Naomi) for GREEN — trim `build_fate_projection` at the ROUTER call site only (do NOT touch the narrator call at `session_helpers.py:1267`); add the `intent_router.fate_vocabulary` span (`bytes_before`/`bytes_after`/`skill_count`/`genre_slug`) mirroring `intent_router.confrontation_vocabulary`; then run the annees_folles before/after to satisfy AC1/AC4.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/ruleset/fate_projection.py` — added `trim_fate_projection_for_router(full)` + `_ROUTER_DROP_KEYS`; drops `character_aspects` + `scene_aspects`, keeps skills / fate_points / active_conflict. `build_fate_projection` (the narrator's call) unchanged.
- `sidequest/telemetry/spans/intent_router.py` — added the `intent_router.fate_vocabulary` span (SPAN_ROUTES entry + `intent_router_fate_vocabulary_span`) mirroring the confrontation / witnessed-act vocabulary spans; attrs `skill_count` / `aspects_dropped` / `bytes_before` / `bytes_after` / `genre_slug`.
- `sidequest/server/intent_router_pass.py` — at the Fate gate: build the full projection, trim it for the router, inject the trimmed block, emit the span with full-vs-trimmed bytes. Narrator path (session_helpers) untouched.
- `tests/game/ruleset/test_fate_projection.py` — updated the prior-story F2b "router == full projection" test to the new contract (`router_block == trim_fate_projection_for_router(build_fate_projection(snap))`); docstring AC-3 amended. See deviation.
- `tests/server/test_fate_classifier_enrichment.py` — `ruff format` whitespace only (TEA's RED file).

**Tests:** 18/18 GREEN across the two Fate-projection files (the 3 RED targets now pass; the 3 invariant guards stay green; 12 pre-existing Fate tests green). Lint + `ruff format --check` clean on all changed files.
**Branch:** feat/126-10-trim-fate-router-prompt (pushed)

**Implementation note — keeping "one source of truth":** the trim is a deterministic function of the canonical `build_fate_projection` output (`trim_fate_projection_for_router`), not a second, independently-built router projection. The narrator builds the full projection separately in `session_helpers` and is unaffected — verified green by `test_narrator_fate_projection_unchanged_by_router_trim`.

**Pre-existing failures NOT in scope (baseline-verified via git-stash):** 11 WN sealed-round tests (`tests/integration/test_102_4_wn_sealed_round.py`) + ~70 sibling WN beat-pool failures fail on a CLEAN checkout *without* my changes — empty WN confrontation beat pool, the in-flight epic-108 / ADR-143 "WN owns the round" work (CLAUDE.md: ADR-114/-143 partial). My Fate-only change touches no WN beats / classes / genre loader.

**Handoff:** To verify (TEA simplify pass) → Reviewer.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (18/18 GREEN, ruff/pyright clean, wiring+OTEL+ADR-047 confirmed) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 4 | confirmed 2, dismissed 0, deferred 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 violation + 3 info | confirmed 1, dismissed 2, deferred 1 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled; I self-assessed the 5 disabled domains — see tags below)
**Total findings:** 6 confirmed (all non-blocking LOW/MEDIUM), 2 dismissed (with rationale), 2 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The implementation is correct, minimal, and fully wired. The router now ships a trimmed Fate projection (skills + fate_points + active_conflict; `character_aspects` + `scene_aspects` dropped) while the narrator's full projection is untouched — the F2b "one source of truth" spirit is preserved because the router *trims the canonical projection* (`trim_fate_projection_for_router`) rather than re-deriving it. The trim is observable (the `intent_router.fate_vocabulary` span carries genuine before/after byte evidence). All six confirmed findings are LOW/MEDIUM polish — none are correctness, security, or perf-regression issues, none block per the severity rubric. They are captured below as tracked non-blocking follow-ups.

**Data flow traced:** player action → `execute_intent_router_pre_narrator_pass` → `_build_state_summary(pack=fate)` → `build_fate_projection(snapshot)` (full) → `trim_fate_projection_for_router` (drops aspect channels) → `summary["fate"]` (trimmed) → `decompose(state_summary)` (Haiku router). The narrator flow is **separate**: `session_helpers` builds its own `build_fate_projection(snapshot)` (full) → `TurnContext.fate_state` → `_build_fate_state_section`. Two flows, router trimmed, narrator full — safe; the diff does not touch `session_helpers.py`.

### Observations

- `[VERIFIED]` Narrator untouched — diff stat is 5 files, none is `session_helpers.py`; `build_fate_projection` default unchanged (`fate_projection.py:40`). Guarded by `test_narrator_fate_projection_unchanged_by_router_trim`. Complies with ADR-144 F2b (narrator keeps full anti-confabulation vocabulary).
- `[VERIFIED]` `[SILENT]` (subagent disabled — self-assessed + rule-checker A2): the three `.get(key, empty)` defaults at `intent_router_pass.py:382-386` are NOT silent fallbacks — `build_fate_projection` unconditionally populates `character_aspects`/`scene_aspects`/`skills` (`fate_projection.py:71-77`), and the trim only drops the two aspect keys, so `skills` is always present. Defaults never trigger; no swallowed exceptions in the diff. Benign per the No-Silent-Fallbacks rule.
- `[VERIFIED]` `[SEC]` (subagent disabled — self-assessed + preflight): aspect text is sanitized via `sanitize_player_text` (ADR-047) at the projection source (`fate_projection.py:60-67`). The trim operates on an already-sanitized internal dict; it introduces no new external-input boundary.
- `[VERIFIED]` `[TYPE]` (subagent disabled — self-assessed + rule-checker #3): `trim_fate_projection_for_router(full: dict[str, Any]) -> dict[str, Any]` is fully annotated; `intent_router_fate_vocabulary_span` is annotated `-> Iterator[trace.Span]` matching its 10 sibling span fns. `dict[str, Any]` is the pre-existing projection type — no new stringly-typed API.
- `[VERIFIED]` `[SIMPLE]` (subagent disabled — self-assessed): the trim is a one-line dict comprehension (minimal). The two `_serialize_state_summary` calls (full + trimmed) for the span's byte evidence add negligible telemetry-only work versus the multi-second Haiku call; not over-engineering.
- `[VERIFIED]` `[RULE]` OTEL Observability Principle: the `intent_router.fate_vocabulary` span carries real mechanical evidence (`bytes_before`/`bytes_after` differential, `aspects_dropped`, `skill_count`, `genre_slug`) and is registered in `SPAN_ROUTES` for the GM-panel WatcherSpanProcessor. Rule-checker A1/A3 confirm: real evidence, no stubs, wired end-to-end.
- `[LOW]` `[TEST]` `[RULE]` Weak assertion `assert attrs["skill_count"] >= 1` at `test_fate_classifier_enrichment.py` (matches lang-review rule #6; flagged by BOTH test-analyzer and rule-checker). The fat fixture has exactly 2 PCs, so `== 2` would pin it; `>= 1` passes even if a PC is dropped. **Confirmed, not dismissed** (rule-match). Severity downgraded to LOW because the routing-essentials property it half-guards is *redundantly and strongly guarded* by `test_router_fate_block_preserves_routing_essentials` (exact dict-equality on both PCs' skills). Fix: tighten to `== 2`.
- `[LOW]` `[DOC]` Stale module docstring at `fate_projection.py:12` — "the router and the narrator can never drift on the aspects" is now false by design (the router drops aspects). Confirmed (comment-analyzer HIGH). Doc-only; misleading about a load-bearing F2b invariant. Fix: amend to note the 126-10 trim (router consumes a strict subset, both still derive from one function).
- `[LOW]` `[DOC]` Stale RED marker at `test_fate_projection.py:19` — "All FAIL today: ...fate_projection does not exist yet (RED)" contradicts the now-GREEN suite. Confirmed (comment-analyzer HIGH). Fix: remove/replace the RED-marker sentence.
- `[LOW]` `[DOC]` `aspects_dropped` underdocumented at `intent_router_pass.py:382` — it counts aspect *strings* (e.g. 9), while `_ROUTER_DROP_KEYS` describes "keys" (2). A GM-panel reader could misread the unit. Confirmed (comment-analyzer MEDIUM→LOW). Fix: one-line clarifying comment.
- `[MEDIUM]` `[TEST]` `[EDGE]` No-aspects edge case untested — the span docstring documents `bytes_before == bytes_after` for a Fate turn with no live aspects, but no test pins it (test-analyzer; the disabled edge-hunter domain). Structurally safe (dict comp), but the honest zero-trim path is unverified. Fix: add a skills-only/no-encounter snapshot test asserting the span fires once with `bytes_before == bytes_after`.
- `[LOW]` `[TEST]` Missing positive assertion `attrs["aspects_dropped"] > 0` in the span test despite 9 planted aspects (rule-checker info). Non-vacuous gap. Fix: add the assertion.
- `[LOW]` `[TEST]` Non-Fate branch pinned at unit level (`test_state_summary_omits_fate_block_for_non_fate_pack`) but not end-to-end through `execute_intent_router_pre_narrator_pass` (test-analyzer, deferred — adequately covered).

### Dismissed (with rationale)

- `.get()` empty-collection defaults flagged borderline by rule-checker #13 → **dismissed as benign**: rule-checker's own A2 pass confirms `build_fate_projection` contractually always populates these keys; not a silent fallback (cite: `fate_projection.py:71-77`).
- No `__all__` on `fate_projection.py` (rule-checker #10) → **dismissed as out-of-scope**: pre-existing omission, not introduced by this diff.

### Rule Compliance

Rule-checker swept the full Python lang-review checklist (16 rules, 47 instances). Result: 15 rules fully compliant; **1 violation** — rule #6 (test quality), the `skill_count >= 1` weak assertion (confirmed above, LOW). Project-principle additions: A1 OTEL Observability **compliant** (span carries real before/after evidence), A2 No-Silent-Fallbacks **compliant** (`.get()` defaults contractually safe), A3 No-Stubbing/Verify-Wiring **compliant** (real impl, e2e wiring test). SOUL "Bind the Ruleset, Don't Balance It": **not implicated** — this is a pure prompt trim on the Fate router path, no native-mechanic tuning, no engine reshaping. The Zork Problem / Genre Truth: classification remains open-ended (the trim removes aspect *vocabulary* from the router, not action expressiveness — the narrator retains everything).

### Devil's Advocate

The most dangerous claim in this PR is the unproven one: that the router can still classify a freeform Fate action into the four actions (overcome / create_advantage / attack / defend) *without seeing the live aspects*. The pre-existing comment explicitly said the router needed "the PCs' skills + the live aspects" — and this PR deletes the aspects on a MEDIUM-confidence hunch. A malicious or simply unlucky case: a player types "I flip the overturned table for cover" — `create_advantage` invoking the situation aspect "Overturned Table." The router no longer sees "Overturned Table" in its prompt; if its classification leaned on aspect-name matching, it could now misroute this to `overcome` or miss the create_advantage entirely, and the narrator's downstream handling would diverge. The deterministic suite CANNOT catch this — it proves the data structure shrank, not that classification survived. That risk is real and is exactly what AC2 ("without breaking Fate routing accuracy") guards and AC4 (empirical annees_folles before/after) must verify. It is documented and deferred, not closed. Second attack: the span now fires on EVERY Fate turn, including no-aspect turns where `bytes_before == bytes_after` and `aspects_dropped == 0` — a GM skimming the panel could misread a fate_vocabulary entry as "trim engaged" when nothing was trimmed; the attributes make it honest but the path is untested (F5). Third: a future caller handing `trim_fate_projection_for_router` a dict lacking the aspect keys would silently compute `aspects_dropped == 0` rather than erroring — benign today (sole contractual call site) but a latent foot-gun if the projection grows a second producer. None of these rise to blocking: the routing-accuracy risk is the story's own accepted, gated-on-AC4 risk; the others are LOW. But the routing-accuracy verification is a genuine precondition for calling this story *done*, not merely *merged*.

**Handoff:** To SM (Camina Drummer) for finish-story. **Gating note for SM/Keith:** AC1/AC4 (empirical annees_folles before/after — the 37-81s → ~4-6s proof) are NOT satisfied by the merged unit gate; they remain a required playtest acceptance step. The LOW/MEDIUM polish findings above (2 stale docstrings, `skill_count == 2`, no-aspects edge test) are natural fast-follows to bundle with that AC4 verification touch or fold into epic-125 tech-debt.

## Delivery Findings

### TEA (test design)
- **Improvement** (non-blocking): The narrator and router call `build_fate_projection` at TWO separate sites — narrator at `session_helpers.py:1267`, router at `intent_router_pass.py:365` (`_build_fate_summary = build_fate_projection`). F2b's "one source of truth" is one *function*, two *call sites*. The trim must land at the ROUTER call site (or a `scope` param defaulting to the full/narrator shape) so the narrator's projection is untouched. Affects `sidequest/server/intent_router_pass.py` (router site) and must NOT alter `sidequest/server/session_helpers.py:1267` (narrator site). *Found by TEA during test design.*
- **Question** (non-blocking): The `intent_router_pass.py:359-363` comment asserts the router needs "the PCs' skills + the live aspects" to classify into the four Fate actions — in tension with AC2's lever ("not every live aspect"). Dev/Architect should confirm on annees_folles that dropping aspect text does not degrade routing accuracy before settling the trim depth. Affects `sidequest/server/intent_router_pass.py:359-365` and the `FATE_ROUTING_RULES` prompt the classifier reads. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): The full server suite is red on ~81 WN-family tests (11 in `tests/integration/test_102_4_wn_sealed_round.py` + siblings) — baseline-verified via git-stash to fail on a clean checkout independent of 126-10. Root cause is an empty WN confrontation beat pool (`PackError: ... encounter_beat_choices references beat id(s) not in pool`), the in-flight epic-108 / ADR-143 "WN owns the round" work. Surfaced so the red suite count is not mistaken for a 126-10 regression. Affects the WN ruleset beat pool / `caverns_and_claudes` classes — out of scope here. *Found by Dev during implementation.*
- **Resolved-during-implementation**: TEA's two test-design findings (two-call-site projection; aspect-vs-skill routing tension) were both honored — the trim landed at the router call site only (narrator untouched) and dropped the live-aspect channels while keeping skills. The aspect-vs-routing-accuracy Question remains open for the annees_folles empirical pass (AC4). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Two stale docstrings — `fate_projection.py:12` ("router and narrator can never drift on the aspects", now false by design) and `tests/game/ruleset/test_fate_projection.py:19` (stale "All FAIL today (RED)" marker, suite is GREEN). Affects those two files (amend the docstrings to reflect the 126-10 trim). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Test-quality polish — tighten `assert attrs["skill_count"] >= 1` to `== 2` (matches lang-review rule #6; the fat fixture has exactly 2 PCs), add `assert attrs["aspects_dropped"] > 0`, and clarify the `aspects_dropped` unit (aspect strings, not keys) at `intent_router_pass.py:382`. Affects `tests/server/test_fate_classifier_enrichment.py` + `intent_router_pass.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): No test pins the no-aspects honest path (`bytes_before == bytes_after`, `aspects_dropped == 0`) the span docstring documents. Affects `tests/server/test_fate_classifier_enrichment.py` (add a skills-only/no-encounter Fate snapshot test). *Found by Reviewer during code review.*
- **Question** (non-blocking, gating for "done"): AC1/AC4 — the empirical annees_folles before/after (37-81s → ~4-6s) and Fate routing-accuracy-survives-the-aspect-trim (AC2) are NOT proven by the merged unit gate; they remain a required playtest acceptance step. Affects the story's done-definition (run the annees_folles 2-seat understudy before/after). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (1 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** None

- **Gap:** No test pins the no-aspects honest path (`bytes_before == bytes_after`, `aspects_dropped == 0`) the span docstring documents. Affects `tests/server/test_fate_classifier_enrichment.py`.

### Downstream Effects

- **`tests/server`** — 1 finding

### Deviation Justifications

3 deviations

- **AC1/AC4 (empirical latency + before/after) validated at runtime, not by unit tests**
  - Rationale: CLAUDE.md OTEL Observability Principle — the span is the lie-detector for "the trim engaged"; latency itself is environment-bound and would make the suite flaky.
  - Severity: minor
  - Forward impact: Dev must run the annees_folles before/after to satisfy AC1/AC4; the unit gate alone does not prove the 37-81s → ~4-6s recovery.
- **Exact aspect-trim shape left to the Dev (not hard-asserted)**
  - Rationale: AC2's lever is MEDIUM-confidence and the line-360 comment claims aspects aid routing; the empirical trim depth is the Dev's call (validated on annees_folles, AC4). Over-specifying risks forcing an over-trim that breaks routing accuracy — the exact thing AC2 guards.
  - Severity: minor
  - Forward impact: Dev chooses the trim shape; the suite boxes it (must shrink, must keep essentials) without dictating it.
- **Updated the prior-story F2b "router == full projection" invariant test**
  - Rationale: Story 126-10 (highest spec authority) deliberately diverges the router projection from the narrator's full projection. The "one source of truth" spirit is preserved — the router trims the canonical projection, it does not re-derive Fate state; the narrator still receives the full projection unchanged.
  - Severity: minor
  - Forward impact: future stories editing the Fate projection must keep the router block a pure trim of `build_fate_projection`, not an independent derivation.

## Design Deviations

### TEA (test design)
- **AC1/AC4 (empirical latency + before/after) validated at runtime, not by unit tests**
  - Spec source: context-story-126-10.md, AC1 + AC4
  - Spec text: "measure intent_router_pass + state_summary size on annees_folles ... Verified before/after on a fresh annees_folles 2-seat understudy run (turn_telemetry numbers)"
  - Implementation: AC1/AC4 are wall-clock / turn-telemetry acceptance gates that cannot be made deterministic in pytest (LLM/network-bound, flaky). The RED suite pins the *structural* lever (router block carries fewer live aspects + smaller serialized) and the GM-panel OTEL span (`intent_router.fate_vocabulary`, `bytes_after < bytes_before`) as the deterministic proxy; the empirical before/after stays a Dev/playtest step (sq-playtest annees_folles).
  - Rationale: CLAUDE.md OTEL Observability Principle — the span is the lie-detector for "the trim engaged"; latency itself is environment-bound and would make the suite flaky.
  - Severity: minor
  - Forward impact: Dev must run the annees_folles before/after to satisfy AC1/AC4; the unit gate alone does not prove the 37-81s → ~4-6s recovery.
- **Exact aspect-trim shape left to the Dev (not hard-asserted)**
  - Spec source: context-story-126-10.md, AC2
  - Spec text: "the router likely needs far less than the narrator — PC skills maybe, not every live aspect"
  - Implementation: tests assert the router block carries strictly FEWER planted live-aspects than the full projection AND keeps skills + `active_conflict` — they do NOT mandate which aspect channel (character_aspects vs scene_aspects) survives or a specific cap.
  - Rationale: AC2's lever is MEDIUM-confidence and the line-360 comment claims aspects aid routing; the empirical trim depth is the Dev's call (validated on annees_folles, AC4). Over-specifying risks forcing an over-trim that breaks routing accuracy — the exact thing AC2 guards.
  - Severity: minor
  - Forward impact: Dev chooses the trim shape; the suite boxes it (must shrink, must keep essentials) without dictating it.

### Dev (implementation)
- **Updated the prior-story F2b "router == full projection" invariant test**
  - Spec source: tests/game/ruleset/test_fate_projection.py (Story 116-2 F2b), AC-3 + module docstring
  - Spec text: "the router still carries the fate block, and that block is *exactly* what `build_fate_projection` returns ... the one source of truth guarantee"
  - Implementation: changed the assertion to `router_block == trim_fate_projection_for_router(build_fate_projection(snap))` (+ asserts the aspect channels are dropped and skills / active_conflict kept); renamed the test and amended the docstring AC-3 bullet to note the 126-10 amendment.
  - Rationale: Story 126-10 (highest spec authority) deliberately diverges the router projection from the narrator's full projection. The "one source of truth" spirit is preserved — the router trims the canonical projection, it does not re-derive Fate state; the narrator still receives the full projection unchanged.
  - Severity: minor
  - Forward impact: future stories editing the Fate projection must keep the router block a pure trim of `build_fate_projection`, not an independent derivation.

### Reviewer (audit)
- **AC1/AC4 empirical validation deferred to runtime** (TEA) → ✓ ACCEPTED by Reviewer: latency is environment-bound and would make the suite flaky; the `intent_router.fate_vocabulary` before/after span is the correct deterministic proxy, with the empirical annees_folles run as the playtest acceptance step. Sound.
- **Exact aspect-trim shape left to the Dev** (TEA) → ✓ ACCEPTED by Reviewer: AC2's lever is MEDIUM-confidence; boxing the contract (must shrink, must keep skills + active_conflict) without dictating the channel is the right call. The Dev's choice (drop both aspect channels) is the maximal latency win and is defensible pending AC4.
- **Updated the prior-story F2b "router == full projection" invariant test** (Dev) → ✓ ACCEPTED by Reviewer: Story 126-10 (highest spec authority) legitimately supersedes the prior invariant for the router path. The new assertion (`router_block == trim_fate_projection_for_router(build_fate_projection(snap))`) genuinely preserves the "one source of truth, no re-derivation" spirit — it is actually a *stronger* anti-drift assertion than a loose subset check. The narrator's full-projection invariant is untouched.
- **UNDOCUMENTED — module-docstring not updated alongside the test docstring** → Spec said the F2b doctrine ("never drift on aspects") held; the code now intentionally drifts, but only the *test* docstring was amended — the *source* module docstring at `fate_projection.py:12` was left stale. Severity: L. (Captured as a code-review delivery finding; non-blocking.)