---
story_id: "126-28"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 126-28: [FATE/TEST] Harden 126-18 opening-prop tests

## Story Details
- **ID:** 126-28
- **Jira Key:** (none — sprint-internal chore)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-20T04:36:10Z
**Repos:** server

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T04:17:19Z | 2026-06-20T04:19:23Z | 2m 4s |
| implement | 2026-06-20T04:19:23Z | 2026-06-20T04:30:45Z | 11m 22s |
| review | 2026-06-20T04:30:45Z | 2026-06-20T04:36:10Z | 5m 25s |
| finish | 2026-06-20T04:36:10Z | - | - |

## Sm Assessment

**Story:** 126-28 — test-hardening follow-up to 126-18 (opening-scene props persist to `room_states`). Pure server-side test work; no production behavior change expected beyond two safe code-hygiene cleanups (top-level import promotion, dropping now-unnecessary `type: ignore`).

**Workflow:** trivial (phased) — setup → implement → review → finish. Single repo: `sidequest-server` (base branch `develop`). No Jira (sprint-internal chore).

**Scope (ACs from story title):**
1. Exercise the *real* snapshot-slimming projection: seed `player_seats` so `party_location()` resolves, then assert `summary["room_states"]` retains the persisted prop (not a path that skips projection — see the 126-18 reviewer gotcha about asserting presence in a slimmed payload that passes for the wrong reason).
2. Add a de-dup / idempotency test (persisting the same opening props twice does not double-write).
3. Assert the wiring-test span payload concretely: `props_persisted == N` and the `prop_ids`, not merely truthy.
4. Assert all 3 props in the forensic test.
5. Cover the chassis-anchor path.
6. Refresh the stale (RED) docstring and drop now-unnecessary `type: ignore` suppressors.
7. Promote the 2 local imports in `persist_opening_props` to top-level.

**Routing:** next phase `implement`, owner **Dev (Agent Smith)**.

**Notes for Dev:**
- This is a *trivial* test-hardening story — keep the implement phase tight; it's exercising existing 126-18 behavior more rigorously, not building new features.
- Heed the memory gotcha: a test asserting presence in a slimmed payload that *skips* projection passes for the wrong reason — seed `player_seats` so `party_location()` resolves and the slimming actually runs.
- `room_states` state needs the `party_location()` key or slimming hides it.
- Scope `ruff` to changed files only — never `ruff format .`.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): `opening_helpers.py` carries 3 pre-existing pyright
  errors unrelated to this story — `mode.value` on the `mode: object` param (l.127),
  `bond_tier: str` passed where `BondTier` literal is expected (l.198), and
  `non_abandoned_player_count` on an `object`-typed value (l.493). Verified pre-existing
  via `git stash` (identical errors on HEAD). Affects
  `sidequest/server/websocket_handlers/opening_helpers.py` (tighten the `mode`/`session_data`
  param types to drop the `object` typing and the attendant `type: ignore[arg-type]` at the
  call sites). Out of scope here (test-hardening story); noting for a future type-hygiene pass.
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the security subagent flagged the pre-existing
  `getattr(opening.setting, "present_props", [])` defensive read at `opening_helpers.py:248`
  — `present_props` is a guaranteed pydantic field (default `[]`), so the `getattr` default
  is dead and reads slightly against the No-Silent-Fallbacks spirit. Pre-existing (not in
  this diff). Affects `sidequest/server/websocket_handlers/opening_helpers.py` (could simplify
  to `opening.setting.present_props` in a future cleanup). Non-blocking. *Found by Reviewer
  during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. All 7 ACs from the story title implemented as written. One
  scope clarification (not a deviation): AC6 says "drop now-unnecessary type:ignore
  suppressors" — I dropped the three that the 126-18 feature made unnecessary
  (`[call-arg]` ×2, `[attr-defined]` ×1 on `present_props`, which is now a real field)
  and KEPT the two `[arg-type]` ignores on `session_data=session_data` (a genuine
  `SimpleNamespace` → `_SessionData` mismatch — those were never "now-unnecessary").

### Reviewer (audit)
- **Dev: "No deviations from spec" + the AC6 type:ignore scope clarification** → ✓ ACCEPTED
  by Reviewer. All 7 ACs implemented as written; verified against the diff. The scope
  clarification is correct: the three dropped suppressors (`[call-arg]` ×2, `[attr-defined]`
  ×1) are unnecessary now that `OpeningSetting.present_props` is a real field (pyright clean
  without them — confirmed), and the two retained `[arg-type]` ignores on
  `session_data=session_data` are genuine `SimpleNamespace` → `_SessionData` mismatches with a
  specific error code (lang-review #3 compliant). No undocumented deviations found.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/tests/server/test_opening_props_persist.py` — hardened the 126-18
  opening-prop suite (the bulk of the story): real snapshot-slimming projection with a
  decoy-room drop assertion (AC1), de-dup/idempotency test (AC2), wiring-span payload
  assertions `props_persisted==3` + `prop_ids` (AC3), all-3-props forensic test (AC4),
  new chassis-anchor seam test (AC5), refreshed stale RED docstring + dropped 3
  now-unnecessary `type:ignore` suppressors (AC6).
- `sidequest-server/sidequest/server/websocket_handlers/opening_helpers.py` — promoted the
  2 local imports in `persist_opening_props` (`RoomState`, `Span` + `SPAN_OPENING_PROPS_PERSISTED`)
  to module top-level (AC7); verified no circular import (`GameSnapshot` stays under
  `TYPE_CHECKING` — it's type-only; `RoomState` is used at runtime so it's a real import).
- `.pennyfarthing/sidecars/dev-patterns.md` (orchestrator) — test-quality pattern: prove
  slimming RAN via a decoy room. Committed + pushed to orchestrator main (de7bb9b).

**Tests:** 11/11 passing in the target file (was 9 — added idempotency + chassis-anchor).
Full opening-seam regression set green: 74 passed, 36 skipped. pyright: no new errors
(3 pre-existing in opening_helpers.py, confirmed via stash). ruff: clean (scoped to changed files).

**Branch:** `feat/126-28-harden-opening-prop-tests` (pushed to sidequest-server origin)

**Handoff:** To review phase (Reviewer / The Merovingian). This is a trivial test-hardening
story — no production behavior change beyond the AC7 import promotion (pure refactor, verified
import-clean) and the AC6 type:ignore drops.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A (GREEN: 26 passed/0 failed/1 pre-existing skip; ruff clean; 0 new pyright errors) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (manually assessed — see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (manually assessed — no try/except in diff) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (manually assessed — see Rule Compliance #6) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (manually assessed — docstrings refreshed, accurate) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (manually assessed — type:ignore drops correct) |
| 7 | reviewer-security | Yes | clean | none | N/A (findings: []; import promotion no-cycle, no ADR-047 gap, no source-text wiring) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (manually assessed — diff is test code, no over-engineering) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (manually enumerated lang-review checklist — see Rule Compliance) |

**All received:** Yes (2 enabled subagents returned, both clean; 7 disabled via `workflow.reviewer_subagents`, manually assessed)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 deferred (pre-existing getattr fallback → Delivery Findings)

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` (13 checks) + server CLAUDE.md rules, for both changed files:

- **#1 Silent exceptions** — PASS. No `try/except` added in the diff; the only production change is two top-level imports.
- **#2 Mutable defaults** — PASS. No new signatures; `persist_opening_props(snapshot, props, *, room_id)` is unchanged (props is required, no default).
- **#3 Type annotations / `type: ignore` codes** — PASS. New test fns annotated `-> None`. Three now-unnecessary suppressors dropped; the two retained `# type: ignore[arg-type]` carry a specific error code (rule #3 satisfied).
- **#4 Logging** — N/A. No logging changed (import-only production edit).
- **#5 Path handling** — PASS. `CONTENT_ROOT` uses `Path(...).resolve().parents[3] / ...` (pre-existing); no new string path concat.
- **#6 Test quality** — PASS / STRENGTHENED. The diff *replaces* truthy-only assertions with concrete value checks (`assert persisted` → `assert len(persisted)==1` + `props_persisted==3` + `prop_ids`). `patch.object` targets are correct (patches `opening_helpers._resolve_opening_post_chargen` where USED, and `Span.open`). No `assert True`, no assertion-free tests, no unreasoned skips. The (ENVELOPE,PERNOD,ASHTRAY) loops assert each label distinctly — not vacuous.
- **#7 Resource leaks** — PASS. `with patch.object(...)` context managers; no bare `open()`.
- **#8 Unsafe deserialization** — PASS. `json.dumps` (serialize) only; pack loaded via the real `GenreLoader` (trusted shipping content, `yaml.safe_load` internally), not user input.
- **#9 Async** — N/A. No async code.
- **#10 Import hygiene** — PASS. KEY for the production change: `RoomState` (used at runtime → correctly a real import, not TYPE_CHECKING), `Span`/`SPAN_OPENING_PROPS_PERSISTED` promoted; security subagent confirmed `sidequest.game.session` and `sidequest.telemetry.spans` import nothing from `sidequest.server.*` → no cycle; `GameSnapshot` stays under TYPE_CHECKING. No star imports.
- **#11 Input validation** — N/A. No new boundary.
- **#12 Dependency hygiene** — N/A. No dependency changes.
- **#13 Fix-introduced regressions** — PASS. Re-scanned; the type:ignore drops and import promotion introduce no new class of issue.
- **Server CLAUDE.md — No Source-Text Wiring Tests** — PASS. No `read_text()`/`getsource()`/source regex; `OpeningSetting.model_fields` reflection is the sanctioned runtime tripwire. Both wiring tests drive the real seam and assert the OTEL span.
- **Server CLAUDE.md — Every Test Suite Needs a Wiring Test** — PASS / STRENGTHENED. Now TWO real-seam wiring tests (location_label + chassis interior_room anchors).
- **OTEL Observability Principle** — PASS. The span payload (`props_persisted` + `prop_ids` + `room_id`) is now concretely asserted in both wiring tests.

## Reviewer Observations

1. `[VERIFIED]` Import promotion introduces no circular import — `opening_helpers.py:9,15` import `RoomState`/`Span`/`SPAN_OPENING_PROPS_PERSISTED`; `sidequest.game.session` and `sidequest.telemetry.spans` import nothing from `sidequest.server.*` (security subagent traced both), `GameSnapshot` stays under `TYPE_CHECKING` (l.27). Evidence: preflight ran 26 tests GREEN + standalone `import` succeeded. Complies with lang-review #10.
2. `[VERIFIED][TEST]` AC1 (`test_persisted_prop_survives_the_real_slimming_projection`) genuinely proves the projection RAN — `test_opening_props_persist.py:213` asserts `set(room_states) == {ROOM_ID}` (decoy room dropped) plus `decoy_prop not in projected` (l.227). This is the load-bearing fix for the 126-18 "passes for the wrong reason" gotcha; the seeded `player_seats["seat-1"]="Margot"` (l.80) is what makes `party_location()` consensus-resolve. Complies with lang-review #6 (concrete, not truthy).
3. `[VERIFIED][TEST]` AC3 span-payload assertions are concrete — `:258` `props_persisted == 3`, `:263-266` every prop id enumerated, `:250` exactly-one-span. Replaces the prior `assert persisted` truthy check. The GM-panel lie-detector is now actually validated.
4. `[VERIFIED][EDGE]` AC5 chassis-anchor test covers the previously-untested `room_id = location_label or interior_room` branch (`:377` asserts `span room_id == interior_room`). Edge-hunter disabled, but I traced the seam manually: chassis lookup falls through to `chassis=None`, `_bootstrap_character_locations_from_opening` early-returns on the `None` `location_label`, `_bind_current_region` returns None (no region_id) → props persist to `interior_room`. Preflight confirms it passes.
5. `[VERIFIED][DOC]` Stale RED docstring refreshed accurately — `:34-65` now describes shipped 126-18 behavior + the 126-28 hardening, removing the false "ALL tests FAIL NOW (RED)" / "SKIP != RED" lines. Matches actual GREEN state.
6. `[VERIFIED][TYPE]` The three dropped `# type: ignore` (`:88,:94` call-arg/attr-defined on `present_props`, `:237`) are correctly removed — the field exists; pyright reports 0 new errors. Retained `[arg-type]` on `session_data` (`:350` + chassis test) is a genuine `SimpleNamespace`→`_SessionData` mismatch (lang-review #3 — specific code present).
7. `[VERIFIED][SIMPLE]` No over-engineering — the idempotency test's partial-re-persist (`ENVELOPE` + `"matchbook"` → appends only `"matchbook"`, l.157) is a minimal, meaningful extra assertion, not gold-plating. Simplifier disabled; manually confirmed no dead code added.
8. `[SEC]` Security subagent: clean (findings: []). Props are authored YAML content-tier strings reaching the narrator via JSON snapshot projection, never raw prompt concat — no ADR-047 sanitization gap. No secrets/leakage.
9. `[SILENT]` No swallowed errors in the diff (no try/except added). Silent-failure-hunter disabled; the only fallback in the touched file (`getattr(..., "present_props", [])`) is pre-existing — logged as a non-blocking Delivery Finding.
10. `[RULE]` Rule-checker disabled; I manually enumerated all 13 lang-review checks + 3 server CLAUDE.md rules above — all PASS, two STRENGTHENED.

## Devil's Advocate

Let me argue this diff is broken. **First angle — the AC1 test could be a false-green in disguise.** It asserts `set(room_states) == {ROOM_ID}`. What if `_build_state_summary` returns a summary with NO `room_states` key at all (e.g. the field was pruned by `exclude_defaults`)? Then `summary.get("room_states", {})` yields `{}`, and `set({}) == {ROOM_ID}` is `False` — the test FAILS loudly, not silently. Good: the empty-dict path is caught, not masked. What if `party_location()` resolved to the *decoy* room instead of ROOM_ID (a seating bug)? Then `room_states` would be `{decoy_room}`, `set != {ROOM_ID}` → fail. The test is robust to mis-seating. **Second angle — the chassis test drives a real pack; what if pulp_noir gains a `le_dome_zinc` chassis_instance later?** Then the lookup would resolve a real chassis (not None), `authored_crew` would populate, but prop persistence still keys off `interior_room` regardless of chassis resolution — the asserts (`room_states[interior_room]`, `span room_id==interior_room`) remain valid. Low fragility. **Third angle — idempotency relies on list-membership (`if prop not in room_state.props`), which is O(n²) across repeated persists and case/whitespace-sensitive.** A prop `"envelope"` vs `"Envelope"` would double-write. But props are authored constants, not free-text, and the production seam fires the same authored list — so divergent casing isn't a real path here; the test pins the exact-match contract it should. **Fourth angle — a confused maintainer could delete the `player_seats` seeding in `_fresh_snapshot` thinking it's redundant** (it looks like decoration next to `character_locations`). That would silently revert AC1 to "passes for the wrong reason." Mitigation present: the inline comment (l.74-79) explicitly marks it "load-bearing, not decoration" and explains the skip path. **Fifth angle — what if `apply_snapshot_slimming` changes its projection shape (e.g. keeps a marker for dropped rooms)?** The `set(room_states) == {ROOM_ID}` assertion would then fail and force a maintainer to re-examine — which is correct behavior for a contract test. None of these uncover a real defect; the strongest residual is the maintainer-deletes-seeding risk, already mitigated by the comment. No new finding.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** authored `present_props` (YAML, content-tier) → `persist_opening_props` → `snapshot.room_states[room_id].props` → `apply_snapshot_slimming` projects to the acting party's room → router/narrator state summary. Safe because the data is structured (never raw prompt concat — `[SEC]` clean) and keyed to `party_location()` so slimming keeps it (the AC1 test now proves this end-to-end).

**Pattern observed:** real-seam wiring tests + OTEL span-payload assertions (the project's sanctioned "No Source-Text Wiring Tests" pattern) at `test_opening_props_persist.py:287` (location anchor) and `:279` (chassis anchor). Both drive `_populate_opening_directive_on_chargen_complete` and assert `opening.props_persisted`.

**Error handling:** `[SILENT]` no swallowed errors added; `[EDGE]` the chassis `room_id = location_label or interior_room` branch is now covered; the empty-props no-op contract is retained. The one pre-existing `getattr` fallback is logged non-blocking.

**Subagent dispatch:** `[TEST]` preflight GREEN (26/0/1); `[SEC]` security clean (findings: []); `[EDGE]`/`[SILENT]`/`[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]` specialists disabled via `workflow.reviewer_subagents` settings and manually assessed (see Rule Compliance + Observations) — all PASS, two STRENGTHENED. Zero Critical/High/Medium findings.

**Handoff:** To SM (Morpheus) for finish-story.