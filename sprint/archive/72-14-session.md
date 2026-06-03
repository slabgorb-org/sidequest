---
story_id: "72-14"
jira_key: ""
epic: "72"
workflow: "trivial"
---
# Story 72-14: Replace source-text wiring test (_publish_combat_edge_to_npcs occurrence count) in test_npc_registry_combat_stats.py with OTEL-span/behavior assertion

## Story Details
- **ID:** 72-14
- **Jira Key:** (none — personal project)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-03T22:38:46Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T22:25:32Z | 2026-06-03T22:28:42Z | 3m 10s |
| implement | 2026-06-03T22:28:42Z | 2026-06-03T22:33:54Z | 5m 12s |
| review | 2026-06-03T22:33:54Z | 2026-06-03T22:38:46Z | 4m 52s |
| finish | 2026-06-03T22:38:46Z | - | - |

## Sm Assessment

Trivial 1pt test-quality story, single repo (sidequest-server). The target is one
brittle source-text wiring test —
`test_npc_registry_combat_stats.py::test_helper_is_called_from_production_handshake_path`
(lines ~290–307) — which proves wiring by `src.count("_publish_combat_edge_to_npcs(") >= 2`.
Replace it with an OTEL-span / behavior assertion that proves the helper runs on
the real encounter-init path, per the project's OTEL-is-the-lie-detector doctrine.
The same file already has the correct pattern to mirror
(`test_otel_span_emitted_on_npc_edge_publish`, line ~238) using `trigger_encounter`
+ `otel_capture`. If that test already fully covers the prod-path guarantee, the
source-text test is redundant and may be removed outright — Dev's judgment, logged
as a deviation. No production code changes. Context written at
`sprint/context/context-story-72-14.md`. Routing to Dev for the implement phase.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/tests/server/test_npc_registry_combat_stats.py` — replaced
  `test_helper_is_called_from_production_handshake_path` (source-text grep:
  `read_text()` + `src.count("_publish_combat_edge_to_npcs(") >= 2`) with
  `test_edge_publish_helper_is_wired_into_production_handshake`, an OTEL/behavior
  wiring assertion. It drives the real production entrypoint
  (`instantiate_encounter_from_trigger` via the `trigger_encounter` helper) and
  asserts the `npc.edge_published` span fires with `source="encounter_handshake"`
  — behavioral proof the helper is reached on the prod path. Survives harmless
  refactors; fails on real wiring breakage. This is exactly pattern #1 from the
  server CLAUDE.md "No Source-Text Wiring Tests" doctrine.

**Design choice (replace, not delete):** Story title says "Replace ... with
OTEL-span/behavior assertion," so I kept a dedicated, explicitly-named wiring
guard (satisfies "Every Test Suite Needs a Wiring Test" with a self-documenting
name) rather than deleting it as redundant against the AC3 test. Made it distinct
from `test_otel_span_emitted_on_npc_edge_publish` (AC3): that test asserts the
span's *payload* (current/max values); the new wiring test asserts only that the
production entrypoint *reaches* the helper at all.

**Tests:** 6/6 passing (GREEN) for `tests/server/test_npc_registry_combat_stats.py`.
Old test name confirmed gone. `ruff check` + `ruff format --check` clean. No
production code touched.
**Branch:** `feat/72-14-replace-source-text-wiring-test-with-otel-assertion` (pushed)

**Handoff:** To review phase (Granny Weatherwax).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (4 advisory notes) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents` and assessed by Reviewer directly)
**Total findings:** 1 confirmed (LOW, non-blocking), 0 dismissed, 0 deferred

Only `preflight` is enabled in `workflow.reviewer_subagents`; the eight diff-specialists
are disabled in settings. Per the agent definition I pre-filled their rows as
Skipped/disabled and covered their domains myself below (this is a single test-file
change with no production code, so [SEC]/[TYPE]/[SILENT]/[EDGE] surfaces are minimal).

## Reviewer Assessment

**Verdict:** APPROVED

Single test-file change (`tests/server/test_npc_registry_combat_stats.py`, +33/−18, no
production code). Replaces a source-text wiring grep with an OTEL-span behavior
assertion. Preflight GREEN (6/6), lint + format clean, old test name gone, no
cross-file dependents.

**Observations:**

- [VERIFIED] The replacement removes the CLAUDE.md-banned source-text grep
  (`Path(...).read_text()` + `src.count("_publish_combat_edge_to_npcs(") >= 2`) and
  substitutes pattern #1 from the server's "No Source-Text Wiring Tests" doctrine —
  an OTEL span assertion driven through the real production entrypoint. Evidence:
  diff lines replacing the old body with `trigger_encounter(...)` + a filtered
  `get_finished_spans()` assertion. Complies with the doctrine and the OTEL principle.
- [VERIFIED] The new test is **not vacuous**: `assert publish_spans` fails on an empty
  list, and the filter requires both `name == "npc.edge_published"` and
  `source == "encounter_handshake"`. The `otel_capture` fixture (lines 122–138) is the
  same one the passing AC3 test uses, so spans are genuinely captured.
- [VERIFIED] The asserted span genuinely originates from `_publish_combat_edge_to_npcs`
  for this fixture. The combat handshake branches on `cdef.win_condition`
  (`encounter_lifecycle.py:1214–1244`): the `hp_depletion` branch calls
  `_seed_combat_hp_depletion_to_npcs` (span @208), the else branch calls
  `_publish_combat_edge_to_npcs` (span @367). The `test_genre` combat cdef "Wasteland
  Brawl" (`rules.yaml:82–94`) is a **momentum dual-dial** encounter (not hp_depletion),
  so the else branch — the helper — is the one exercised. Wiring guard is real.
- [TEST] [MEDIUM→LOW] Indirect-guard robustness gap: the asserted span family
  (`npc.edge_published` + `source="encounter_handshake"`) is shared by BOTH handshake
  branches. The test specifically guards `_publish_combat_edge_to_npcs` only *because*
  the fixture uses a dial-based combat cdef. If `test_genre`'s combat win_condition ever
  flips to `hp_depletion` (plausible given the active SWN/ablative-HP migration touching
  combat packs), this test would stay green via the *seed* branch while no longer
  guarding the named helper — and its failure message ("_publish_combat_edge_to_npcs is
  no longer called") would become misleading. Downgraded to LOW: the test is correct
  today and this is a strict improvement over the grep. Disambiguator exists for a future
  hardening — the helper's span (@367) emits NO `seed_source` kwarg, whereas the seed
  span (@208) sets `seed_source="opponent_default_stats"`; filtering on that would pin
  the test to the helper branch. Captured as a non-blocking Delivery Finding.
- [DOC] [VERIFIED] Docstring is accurate and self-documenting: it explicitly states the
  behavioral-proof rationale, cites the doctrine, and distinguishes itself from the AC3
  payload test. The "No span ⇒ the call site was removed" claim is true for the current
  fixture (see robustness caveat above). No stale/misleading comments introduced.
- [SIMPLE] [VERIFIED] No over-engineering — reuses existing `trigger_encounter` helper
  and `otel_capture` fixture; no new infrastructure. The one cosmetic hunk
  (`trigger_encounter(...)` reflow at lines 190+) is pure ruff formatting.
- [EDGE] N/A — no new branching/boundary logic; the test is a single linear
  drive-and-assert. (edge-hunter disabled; assessed directly.)
- [SILENT] N/A — no error handling, swallowed exceptions, or fallbacks in a test that
  drives one call and asserts. (silent-failure-hunter disabled; assessed directly.)
- [TYPE] N/A — no type definitions, constructors, or signatures changed; test-only.
  (type-design disabled; assessed directly.)
- [SEC] N/A — test-only change, no auth/input/tenant surface, no secrets. (security
  disabled; assessed directly.)
- [RULE] [VERIFIED] Rule compliance checked below — complies with all applicable rules;
  the change is in fact the *correction* of a rule violation. (rule-checker disabled;
  enumerated directly.)

### Rule Compliance

- **CLAUDE.md "No Source-Text Wiring Tests"** — applies to the changed test. Old test
  VIOLATED it (read_text + count). New test COMPLIES (pattern #1, OTEL span assertion).
  This story exists to fix exactly this violation. ✓
- **CLAUDE.md "Every Test Suite Needs a Wiring Test"** — satisfied: a dedicated,
  explicitly-named wiring test remains in the suite. ✓
- **CLAUDE.md OTEL Observability Principle** — the wiring is proven via the
  `npc.edge_published` span. ✓
- **CLAUDE.md "No Stubbing" / "No half-wired"** — N/A (test-only, no production seam). ✓
- **SOUL.md** — no narrator/agency/genre rules apply to a test change. N/A.

### Devil's Advocate

Could this approval be wrong? The strongest case for rejection is that the new test
*claims more than it proves*. Its name and failure message assert that
`_publish_combat_edge_to_npcs` specifically is wired into production — but mechanically
it only proves that *some* handshake path emitted an `npc.edge_published` span tagged
`encounter_handshake`. Two functions can emit that exact span. So the test's specificity
is an accident of the fixture's `win_condition`, not an intrinsic property of the
assertion. A malicious (or merely careless) future edit could delete the entire
`_publish_combat_edge_to_npcs` call site, change the fixture cdef to `hp_depletion`, and
this test would stay green — the precise failure mode the old grep, for all its ugliness,
would have *caught* (it named the symbol literally). That is a genuine regression in
*specificity*, even as it's an improvement in *refactor-resilience and honesty*.

Is that disqualifying? No. First, the old grep's specificity was itself a lie — it
proved the string appeared twice, not that the call executed; it would pass on a
commented-out call inside an `if False:` block. Second, the test is correct for the
current code and fixture, verified end-to-end. Third, this is a trivial 1-pt
test-quality story with no clean rework edge; bouncing it to harden a LOW, hypothetical,
future-fixture-dependent concern is disproportionate and would stamp a false round-trip.
The right disposition is APPROVE + a recorded, precise, non-blocking hardening note
(filter on absence of `seed_source`) so the specificity gap is not lost. A confused
user reading the failure message could be misled in the hp_depletion-fixture future;
that is exactly what the Delivery Finding documents. Nothing here corrupts data, leaks
information, or breaks production. Ship it; harden later.

**Data flow traced:** player-action → `trigger_encounter` → `instantiate_encounter_from_trigger`
(combat branch, dial cdef) → `_publish_combat_edge_to_npcs` → `npc_edge_published_span`
→ in-memory exporter → test assertion. Safe and real.
**Pattern observed:** OTEL-span behavior wiring test (CLAUDE.md pattern #1) at
`tests/server/test_npc_registry_combat_stats.py:290+`.
**Error handling:** N/A (test-only).
**Handoff:** To SM (Captain Carrot) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### Dev (implementation)
- No upstream findings during implementation. The replacement reused the existing
  `otel_capture` fixture and `trigger_encounter` helper already in the file; no new
  infrastructure needed.

### Reviewer (code review)
- **Improvement** (non-blocking): The new wiring test asserts on the shared
  `npc.edge_published` + `source="encounter_handshake"` span, which is emitted by BOTH
  combat-handshake branches (`_publish_combat_edge_to_npcs` @367 AND
  `_seed_combat_hp_depletion_to_npcs` @208). It specifically guards the helper only
  because the `test_genre` combat cdef is dial-based (non-hp_depletion). To pin the test
  to `_publish_combat_edge_to_npcs` regardless of future fixture changes, tighten the
  span filter to require ABSENCE of `seed_source` (the helper's span @367 omits it; the
  seed span @208 sets `seed_source="opponent_default_stats"`).
  Affects `sidequest-server/tests/server/test_npc_registry_combat_stats.py`
  (add a `seed_source` discriminator to the `publish_spans` filter).
  *Found by Reviewer during code review.*
- **Question** (non-blocking): Confirm `sidequest.telemetry.setup.init_tracer()` is
  idempotent for xdist safety — the `otel_capture` fixture calls it unconditionally and
  adds a `SimpleSpanProcessor` to a shared provider. Pre-existing pattern (AC3 test uses
  the same fixture), not introduced by this change; flagged by preflight as advisory.
  Affects `sidequest-server/tests/server/test_npc_registry_combat_stats.py` (fixture).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### Dev (implementation)
- No deviations from spec. Followed the story title's "Replace ... with
  OTEL-span/behavior assertion" directive and the context's authorization to keep
  a named wiring test. The context permitted outright removal (as redundant with
  the AC3 test) at Dev's discretion; I chose replace-not-delete to preserve an
  explicitly-named wiring guard per "Every Test Suite Needs a Wiring Test." This
  is a design choice within the granted discretion, not a spec deviation.

### Reviewer (audit)
- **Dev's "replace, not delete" design choice** → ✓ ACCEPTED by Reviewer: sound, and
  within the discretion the story context explicitly granted. Keeping a dedicated,
  self-documenting wiring test satisfies "Every Test Suite Needs a Wiring Test" better
  than relying on the AC3 payload test to double as the wiring guard. No undocumented
  deviations found in the diff.