---
story_id: "158-29"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-29: Dogfight router→seater→lifecycle — degrade loudly when no engine seats; never wedge the narrator (ADR-153 Plan 2)

## Story Details
- **ID:** 158-29
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-27T12:48:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T12:06:49Z | 2026-06-27T12:08:28Z | 1m 39s |
| red | 2026-06-27T12:08:28Z | 2026-06-27T12:26:45Z | 18m 17s |
| green | 2026-06-27T12:26:45Z | 2026-06-27T12:40:36Z | 13m 51s |
| review | 2026-06-27T12:40:36Z | 2026-06-27T12:48:30Z | 7m 54s |
| finish | 2026-06-27T12:48:30Z | - | - |

## Sm Assessment

**Routing:** Picked up as the next p1 in epic 158 after 158-31 (Plan 1, firewall) shipped in the last commit. This is the foundational ADR-153 Plan 2 piece (router→seater→lifecycle contract, doc d1463a0b). Smallest of the three open p1s (2 pts), no `depends_on`, merge gate clear (0 in-progress / 0 in-review).

**Scope guard for TEA (Igor):** This story is the **dogfight dispatch path only**. When a ship-combat verb routes to the dogfight but the engine *cannot seat*, it must degrade loudly and observably (OTEL) — never leave the narrator grinding the SDK tool loop to max_turns. The GENERAL "narrator max_turns must degrade, not crash" robustness fix is **split out to 158-41** — do **not** solve it here.

**Open disambiguation to resolve from the watcher stream (per the finding):** did the router *fail to emit* a ship-combat dispatch key, or *dispatch-then-reject*? The repro is the coyote_star 2026-06-25 playtest @aed2d812 — verb 'bring guns online, lock a firing solution' produced `intent_router.confrontation_verb_unrouted` (verb_hits dogfight:lock, dogfight:gun). Note: the old native dial_threshold / WN tool-withhold framing is **obsolete** — ADR-153 deletes the native dial; this is purely the routing→seating→degradation contract.

**Tests should cover:** (1) dogfight verb routed but unseated → degrades loudly, (2) observable OTEL span on the degradation, (3) narrator never grinds the SDK tool loop to max_turns on this path. Per project doctrine: every fix touching this subsystem adds OTEL watcher events so the GM panel can verify it.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Scope:** Plan-2 doc Task 1 (force-dispatch injector + `dogfight.forced_dispatch` span) **and** Task 4 (e2e wiring on OTEL + degrade-loud). Tasks 2 (158-30 husk no-resurrect) and 3 (158-35 dice-replay narration anchor) are **sibling stories** — out of 158-29 scope (SM scope guard + spec-authority: story scope > plan).

**Test Files:**
- `tests/server/test_intent_router_dogfight_force_dispatch.py` — 7 unit tests for `force_dispatch_dogfight_on_verb_miss`: strong 2-distinct-verb fires + `dogfight.forced_dispatch` span; single unambiguous strong verb fires; weak single generic verb refrains (over-fire gate); no-dogfight-verb action refrains; live-fight refrains; already-routed-confrontation refrains; no-dogfight-type (`pack=None`) refrains.
- `tests/server/test_dogfight_force_dispatch_wiring.py` — 2 wiring tests through the REAL `execute_intent_router_pre_narrator_pass` (mocked router returning an empty package = the miss): (1) force-dispatch seats a frame-default dogfight, `dogfight.forced_dispatch` + `dogfight.dispatch` fire; (2) frameless def → `dogfight.dispatch.rejected` fires, nothing seated (degrade loud, no crash).
- `tests/fixtures/dogfight_playtest_encounter.py` — added `make_frameless_dogfight_pack()` (test infra: nulls `opponent_default_stats` so the dogfight cannot seat; fails loud if the dogfight def is absent / already frameless).

**Tests Written:** 9 tests covering the ADR-153 §7 router→seater→degrade contract (the 158-29 AC: "degrade loudly when no engine seats; never wedge the narrator").
**Status:** RED — verified for the RIGHT reason (`-n0`, serial per OTEL deadlock rule):
- injector file: `ImportError: cannot import name 'force_dispatch_dogfight_on_verb_miss'` (collection RED — feature symbol absent).
- wiring file: both fail on `assert _spans_named(..., "dogfight.forced_dispatch") == []` (assertion RED — no force-dispatch wired). The frameless fixture + the real pass executed end-to-end (no harness errors), so these go green once Dev wires the injector.

### Rule Coverage

| Rule (lang-review python.md / CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| OTEL lie-detector (CLAUDE.md OTEL principle) | `dogfight.forced_dispatch` asserted in unit + both wiring tests; `dogfight.dispatch` / `.rejected` in wiring | RED |
| #1 silent-exceptions / **No Silent Fallbacks** | `test_force_dispatch_that_cannot_seat_degrades_loud` (rejected span MUST fire; no silent fall-through) | RED |
| #3 type-annotations (public boundary) | injector unit tests pin the kw-only signature + `-> bool` return contract | RED (ImportError) |
| #9 async-pitfalls | wiring tests `await` the real async pass; `AsyncMock` decompose (no missing await) | RED |
| #6 test-quality | self-checked — every test asserts a specific value (bool / span presence-absence / encounter state), no `assert True`, no truthy-on-always-None, mock target is the passed router instance (not a wrong patch target) | clean |
| Over-fire gate (ADR-153 §7 calibration) | `test_does_not_force_dispatch_on_weak_single_generic_verb` + `_on_non_combat_action` (the phantom-seat guard) | RED (ImportError) |
| Wiring test (CLAUDE.md) | `test_router_missed_dogfight_force_dispatches_seats_and_emits_spans` drives the production pre-pass, not the injector in isolation | RED |

**Rules checked:** 7 applicable checks have test coverage (OTEL, #1, #3, #6, #9, over-fire gate, wiring). #2/#5/#7/#8/#11 are not applicable to these test files.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Ponder Stibbons) for GREEN — see Delivery Findings for the three implementation traps (required SubsystemDispatch fields, confidence gate, player_id normalization order).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/telemetry/spans/dogfight.py` — new `SPAN_DOGFIGHT_FORCED_DISPATCH` + `dogfight_forced_dispatch_span` context manager + a `SPAN_ROUTES` entry (routes the span to a `state_transition` watcher event like its dogfight siblings — addresses Igor's finding #4).
- `sidequest/server/intent_router_pass.py` — `force_dispatch_dogfight_on_verb_miss` injector (+ `_STRONG_DOGFIGHT_VERBS`), wired into the `confrontation_verb_unrouted` miss branch, added to `__all__`, imported `PlayerDispatch`.
- `sidequest/agents/subsystems/dogfight.py` — hardened `_resolve_dogfight_type` to a `getattr`-walk (duck-typed-pack safe).

**Igor's three traps, all handled:**
1. **Required `SubsystemDispatch` fields** — the injected dispatch supplies `idempotency_key=f"dogfight-forced-{type}"` + `confidence=1.0` (the plan's snippet omitted both).
2. **Confidence gate** — `confidence=1.0` clears `run_dispatch_bank`'s 0.6 gate, so the force-seat actually seats (a sub-threshold value would degrade to a hint and seat nothing).
3. **player_id normalization** — confirmed `_normalize_per_player_ids` runs at `intent_router_pass.py:866`, BEFORE the injection point (the `confrontation_verb_unrouted` branch ~1010). It maps `player_id → seat_id` only when `player_seats` is bound, else leaves the raw id. The injector matches `pd.player_id in (player_name, seat_id)`, with a single-submitter fallback, then a create-slot fallback — robust across both forms.

**Tests:** 9/9 new tests passing (GREEN). Blast-radius regression: **70 passed, 0 regressions** across the intent-router pre-pass, dogfight dispatch/seating, confidence gate, and player-id normalization suites (`-n0`, serial per OTEL deadlock rule).
**Branch:** `feat/158-29-dogfight-router-force-dispatch` (pushed)

**Pre-existing baseline (NOT my regression — proven):** `tests/server/test_intent_router_degrade_decompose_span.py` (2 tests) fail on develop independent of this change — story 71-29's `MagicMock` pack hits story 158-33's `effective_bestiary` unpack block (`ValueError: not enough values to unpack`). Verified by neutralizing my injection call and re-running: still 2 failed. Plus 3 pre-existing ruff errors in unrelated test files (not in this diff; my changed files are ruff-clean).

**Handoff:** To next phase (verify/review).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | 3 LOW smells | confirmed 3 (all LOW, non-blocking); ruff PASS, 31/31 tests green, degrade-test failures confirmed pre-existing |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge cases assessed manually (see `[EDGE]`) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 1 LOW (line-82 getattr inconsistency), deferred 1 (pre-existing bank swallow), deferred 1 (per-reason suppression span — OTEL improvement) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality assessed manually (see `[TEST]`) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — docs assessed manually (see `[DOC]`) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — types assessed manually (see `[TYPE]`) |
| 7 | reviewer-security | Yes | clean | none | N/A — all 5 security checks compliant |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplification assessed manually (see `[SIMPLE]`) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rules assessed manually (see `### Rule Compliance` + `[RULE]`) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` and assessed manually)
**Total findings:** 2 confirmed (both LOW, non-blocking), 3 deferred (pre-existing / out-of-scope improvements), 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player `action` string → `_confrontation_verb_hits(action, pack)` (lowercased, `[^a-z0-9]+`-tokenized, suffix-stripped, matched by set-membership against authored `intent_verbs`) → filtered to `{dogfight_type}:`-prefixed hits → strong-signal gate (`_STRONG_DOGFIGHT_VERBS` ∪ ≥2 distinct) → `SubsystemDispatch(subsystem="dogfight", confidence=1.0)` injected into the **submitting** seat's `per_player` slot → `run_dispatch_bank` → `run_dogfight_dispatch` → seats a Plan-1 frame-default opponent, or rejects loud via `dogfight.dispatch.rejected`. **Safe because:** the raw action is never logged (only `len(action)`), never enters a span attribute (`verb_hits` carries the matched *authored* verbs, not player text — `[SEC]` confirmed), and the tokenizer regex is a non-backtracking negated char-class (no ReDoS — `[SEC]` confirmed). The injection targets only the submitter's slot (no cross-player leak — `[SEC]` confirmed).

**Pattern observed:** the injector mirrors `inject_environment_clock`'s deterministic post-decompose injection idiom, and the new `dogfight.forced_dispatch` span mirrors the existing `dogfight.dispatch` / `.rejected` span+`SPAN_ROUTES` pair (`telemetry/spans/dogfight.py:344`). Good adherence to established patterns.

**Error handling / degradation:** the seat-or-reject-loud contract is met for the known failure modes — the degraded-path wiring test (`test_force_dispatch_that_cannot_seat_degrades_loud`) drives a frameless pack and asserts `dogfight.dispatch.rejected` fires with nothing seated. The over-fire gate is exercised both directions (`test_does_not_force_dispatch_on_weak_single_generic_verb`, `_on_non_combat_action`).

### Findings (all non-blocking)

| Severity | Tag | Issue | Location | Decision |
|----------|-----|-------|----------|----------|
| LOW | `[SILENT]` | `_resolve_dogfight_type` guards `resolution_mode` + `category` with `getattr` but then accesses `cdef.confrontation_type` bare — incomplete application of the duck-typing rationale the change introduced. Cannot trigger with a real pack (`confrontation_type` is a required field) or any current test fake. | `sidequest/agents/subsystems/dogfight.py:82` | Confirmed (LOW) — tidy-up; complete the `getattr` walk. Non-blocking. |
| MEDIUM→deferred | `[SILENT]` | `run_dispatch_bank`'s bare `except Exception` swallows any `run_dogfight_dispatch` exception *other than* `NoOpponentAvailableError`/`SealedLetterArityError` → WARNING log, no `dogfight.dispatch.rejected` span. **Pre-existing** (not in this diff); the 158-29 known degraded path emits the rejected span and is tested. | `sidequest/agents/subsystems/__init__.py:463` | Deferred — pre-existing, out of 158-29 scope; relates to 158-41 (general degrade-loud). Severity downgraded with rationale: not introduced here, in-scope contract met + tested. |
| MEDIUM→deferred | `[SILENT]` | The four return-False paths in the injector (no type / live fight / already-routed / weak signal) aren't individually observable — no per-reason suppression span. The existing `confrontation_verb_unrouted` INFO log + `confrontation_classified` span already cover "verb hit, nothing seated." | `intent_router_pass.py:280-309` | Deferred — reasonable OTEL-granularity improvement, non-blocking; the miss is already observable at coarse grain. |
| MEDIUM | `[EDGE]` | Over-fire: the ≥2-distinct-generic-verb gate fires on a non-combat action that happens to hit two generic verbs (e.g. "lock the gun cabinet" → `lock`+`gun`). This is the ADR-153-documented calibration tradeoff, gated behind the LLM router *already* declining, so it's a rare second-guess. No test pins this known false-positive boundary. | `intent_router_pass.py:240,296` | Confirmed (MEDIUM, accepted-by-design) — playtest watch; a future test pinning the boundary would be valuable. Non-blocking. |
| LOW | `[SIMPLE]` | Lazy in-function imports of `_resolve_dogfight_type` (a private cross-module symbol) and `dogfight_forced_dispatch_span`. Fragile on rename (runtime not import-time break). The codebase uses local imports elsewhere to dodge cycles, so acceptable, but a top-level import would be sturdier if no cycle exists. | `intent_router_pass.py:277-278` | Confirmed (LOW) — non-blocking style note. |
| LOW | `[SIMPLE]` | `_empty_package` duplicated across the two new test files with slightly different signatures. | test files | Confirmed (LOW) — harmless test duplication. |
| LOW | `[TEST]` | The injector's create-slot and `per_player[0]` fallback branches (empty/mismatched `per_player`) aren't directly unit-tested — all tests hit the `player_name`-match path. | `intent_router_pass.py:289-295` | Confirmed (LOW) — defensive branches; main path well-covered. |

### VERIFIED

- `[VERIFIED]` No PII in logs — `intent_router_pass.py:301` `logger.info` uses `%s` lazy args and logs `len(action)`, never the raw action. Complies with CLAUDE.md no-PII-in-logs / lang-review #4. (`[SEC]` corroborated.)
- `[VERIFIED]` OTEL lie-detector satisfied — `dogfight.forced_dispatch` span fires on every seat (`intent_router_pass.py:299`), registered in `SPAN_ROUTES` (`telemetry/spans/dogfight.py:345`) so it routes to a `state_transition` watcher event like its siblings. Complies with the OTEL Observability Principle. (`[RULE]` lang-review-adjacent.)
- `[VERIFIED]` getattr hardening is NOT a silent fallback — `dogfight.py:74-82`: a real `ConfrontationDef` always carries `resolution_mode`/`category`/`confrontation_type` (required fields), so live behavior is unchanged; only duck-typed test fakes resolve to None (a genuine "no dogfight authored", not a masked error). Complies with No Silent Fallbacks.
- `[VERIFIED]` Confidence clears the gate — injected `confidence=1.0` (`intent_router_pass.py:306`) ≥ the bank's 0.6 per-subsystem threshold, so the force-seat actually seats (the wiring test seats a live encounter, proving it).
- `[VERIFIED]` Idempotency / no replay — `[SEC]` confirmed `run_dispatch_bank` dedups on `idempotency_key` via a `seen` set; the constant `dogfight-forced-{type}` key is injected exactly once per call. No collision/replay.
- `[VERIFIED][TYPE]` `force_dispatch_dogfight_on_verb_miss` is fully type-annotated (keyword-only, `pack: GenrePack | None`, `-> bool`); no stringly-typed surprises, no mutable defaults (lang-review #2/#3).
- `[VERIFIED][DOC]` Comments are accurate — the docstrings and inline comments correctly describe the contract, the over-fire rationale, and the 158-41 scope boundary; no stale/misleading docs in the diff.

### Rule Compliance (lang-review python.md, exhaustive over the diff)

- **#1 silent exceptions** — no bare `except`/swallow introduced in the diff; the injector's early returns are guard clauses, not swallows. The one related concern (bank bare-except) is pre-existing, deferred. ✓ (in-diff)
- **#2 mutable defaults** — none in `force_dispatch_dogfight_on_verb_miss` or the span helper. ✓
- **#3 type annotations** — public injector + span helper fully annotated. ✓
- **#4 logging** — `%s` lazy args, `info` level (an informational seating decision, not an error), `len(action)` not raw text. ✓
- **#5 path handling** — N/A (no path ops). ✓
- **#6 test quality** — every new test asserts a specific value (bool / span presence-or-absence / encounter state); no `assert True`, no truthy-on-always-None, mock target is the passed router instance. One coverage gap noted (fallback branches, LOW). ✓
- **#7 resource leaks** — `with dogfight_forced_dispatch_span(...)` properly scoped. ✓
- **#8 unsafe deserialization** — N/A. ✓
- **#9 async** — injector is sync (pure), correctly called without `await` from the async pass; wiring tests `await` the pass and `AsyncMock` the router. ✓
- **#10 import hygiene** — added to `__all__`; in-function imports flagged LOW (`[SIMPLE]`) but consistent with the module's cycle-avoidance idiom. ✓
- **#11 input validation** — player `action` validated through the existing non-backtracking tokenizer; no injection. ✓ (`[SEC]`)

### Devil's Advocate

Suppose this code is broken. The most dangerous angle is the **phantom-seat**: the force-dispatch is a deliberate *second-guess* of the LLM router. The router saw "lock the gun cabinet," classified it as non-combat, and emitted nothing — correctly. Then this injector overrides that judgment on a purely lexical ≥2-generic-verb hit and seats a *space dogfight* while the player is standing in an armory. A confused player who typed a mundane sentence now faces an enemy fighter with no fiction to justify it — a Rule-of-Cool violation and exactly the "convincing mechanics with no narrative backing" the OTEL lie-detector exists to expose. The mitigations are real but partial: it only fires when the router *already* declined AND no fight is live AND the pack authors a sealed-letter dogfight (space_opera only), so the blast radius is one genre. The ADR explicitly accepted this ("a wrong one mis-seats a fight"), so it is a known, bounded tradeoff — not a hidden defect — but it is genuinely reachable and untested at the false-positive boundary, hence the MEDIUM `[EDGE]` finding and a playtest watch.

A malicious or adversarial user gains nothing: the injection lands only in their own seat, the span leaks no input, and the tokenizer can't be made to backtrack. A stressed pack (duck-typed/fake) is handled by the getattr hardening — except the residual `cdef.confrontation_type` bare access, which a *contrived* fake (sets resolution_mode+category, omits confrontation_type) could trip; in production that path is dead because the field is required. An unexpected exception inside the seater (anything beyond the two caught types) is swallowed by the pre-existing bank catch with only a WARNING — the GM panel would see `forced_dispatch` with no outcome span, a partial-observability hole that predates this story and belongs to the general degrade-loud work (158-41). None of these rise to a Critical or High defect *introduced by this change*; the in-scope contract — seat a router-missed dogfight on a strong signal, or degrade loud — is implemented, wired into the production pre-pass, and verified end-to-end on OTEL. Verdict stands: APPROVED, with the findings logged for follow-up.

**Handoff:** To SM (Captain Carrot) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): `SubsystemDispatch` REQUIRES `idempotency_key` and `confidence` (no defaults, `sidequest/protocol/dispatch.py:106`). The Plan-2 doc's injector snippet constructs `SubsystemDispatch(subsystem="dogfight", params={"type": dogfight_type})` — which raises `ValidationError`. Dev's `force_dispatch_dogfight_on_verb_miss` must supply both (e.g. a stable `idempotency_key` + a gate-clearing `confidence`). Affects `sidequest/server/intent_router_pass.py` (the injector). *Found by TEA during test design.*
- **Gap** (blocking): the injected dogfight dispatch's `confidence` must clear `run_dispatch_bank`'s per-subsystem gate (default **0.6**). A sub-threshold value degrades to a narrator hint and **seats nothing** (cf. `tests/agents/subsystems/test_dogfight_dispatch_wiring.py::test_low_confidence_dogfight_degrades_and_does_not_engage`, which seats nothing at 0.2). The wiring test asserts a real SEAT, so the forced dispatch must carry `confidence ≥ 0.6` (the §7 intent is a deliberate force-seat — use ~1.0). Affects `intent_router_pass.py`. *Found by TEA during test design.*
- **Question** (non-blocking): the injector targets `pd.player_id == player_name`, but the pre-pass also runs `_normalize_per_player_ids`. Dev should confirm the injector fires AFTER normalization (or that its create-slot-if-missing fallback covers a `player:Name` vs `Name` mismatch) so the forced dispatch lands in the submitting seat. The wiring test asserts end-state (seated), so a mismatch will surface as a non-seat — but be deliberate about call-site ordering (~`intent_router_pass.py:915`, after the `confrontation_verb_unrouted` block, before the unregistered-subsystem gate). *Found by TEA during test design.*
- **Improvement** (non-blocking): the new `dogfight.forced_dispatch` span shares `dogfight.py`'s `SPAN_ROUTES`/`SpanRoute` machinery (the existing dogfight spans register there). Dev should verify the new span is routed like its siblings (and added to `__all__` if the module exposes one — it currently does not). Affects `sidequest/telemetry/spans/dogfight.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking, PRE-EXISTING): `tests/server/test_intent_router_degrade_decompose_span.py` (2 tests) fails on develop independent of this story — story 71-29's `MagicMock` pack hits story 158-33's `effective_bestiary(world)` unpack block (`ValueError: not enough values to unpack (expected 2, got 0)`). Proven not-mine by neutralizing the 158-29 injection and re-running (still 2 failed). The 158-33 block already guards `ruleset`/`effective_bestiary` absence on minimal stubs but the MagicMock returns a callable that yields a Mock; a real GenrePack is unaffected. Affects `tests/server/test_intent_router_degrade_decompose_span.py` (the test's pack stub needs `effective_bestiary` configured to return a 2-tuple, or the 158-33 block needs a non-callable-Mock guard). *Found by Dev during implementation.*
- **Improvement** (non-blocking, PRE-EXISTING): 3 ruff errors exist in unrelated `tests/` files (e.g. a `_GRID` cavern fixture) on develop — not in this diff; all six 158-29-touched files pass `ruff check`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): complete the `getattr`-walk in `_resolve_dogfight_type` — `:82` accesses `cdef.confrontation_type` bare while the two guards above use `getattr`. Affects `sidequest/agents/subsystems/dogfight.py` (one-line tidy: `getattr(cdef, "confrontation_type", None)` + guard). Cannot trigger with a real pack (required field). *Found by Reviewer during code review.*
- **Gap** (non-blocking, PRE-EXISTING): `run_dispatch_bank`'s bare `except Exception` (`sidequest/agents/subsystems/__init__.py:463`) swallows any `run_dogfight_dispatch` exception other than `NoOpponentAvailableError`/`SealedLetterArityError` → WARNING log, no `dogfight.dispatch.rejected` span, partial GM-panel observability (`forced_dispatch` fires but no outcome span). Relates to the general degrade-loud work (158-41). Affects `run_dogfight_dispatch` (broaden its except to always emit a rejected span before the bank's catch). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the over-fire gate will mis-seat on a non-combat action with ≥2 distinct generic verbs (e.g. "lock the gun cabinet") — the ADR-153-accepted calibration tradeoff, gated behind a router decline. Worth a playtest watch and a future test pinning the false-positive boundary. Affects `sidequest/server/intent_router_pass.py` (the `_STRONG_DOGFIGHT_VERBS` ∪ ≥2-distinct gate). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): consider a per-reason suppression span (`dogfight.force_dispatch_suppressed` with reason) for the injector's return-False paths so the GM panel can distinguish intentional suppression from a broken gate. Affects `sidequest/server/intent_router_pass.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** 1 BLOCKING items — see below

**BLOCKING:**
- **Gap:** `SubsystemDispatch` REQUIRES `idempotency_key` and `confidence` (no defaults, `sidequest/protocol/dispatch.py:106`). The Plan-2 doc's injector snippet constructs `SubsystemDispatch(subsystem="dogfight", params={"type": dogfight_type})` — which raises `ValidationError`. Dev's `force_dispatch_dogfight_on_verb_miss` must supply both (e.g. a stable `idempotency_key` + a gate-clearing `confidence`). Affects `sidequest/server/intent_router_pass.py`.

- **Improvement:** the over-fire gate will mis-seat on a non-combat action with ≥2 distinct generic verbs (e.g. "lock the gun cabinet") — the ADR-153-accepted calibration tradeoff, gated behind a router decline. Worth a playtest watch and a future test pinning the false-positive boundary. Affects `sidequest/server/intent_router_pass.py`.

### Downstream Effects

- **`sidequest/server`** — 2 findings

### Deviation Justifications

3 deviations

- **Implemented only Plan-2 Tasks 1 & 4 (not 2 & 3)**
  - Rationale: Tasks 2/3 are tracked by sibling stories 158-30 / 158-35; story scope (158-29) is the highest spec authority, and the plan's own Self-Review maps them to those stories
  - Severity: minor
  - Forward impact: 158-30 and 158-35 carry their own RED phases; no coverage lost for 158-29
- **Added `make_frameless_dogfight_pack()` to the shared fixtures module (vs inline)**
  - Rationale: keeps the degraded-path test readable, reuses the Plan-1 fixture module, and the loud guards (raise if the dogfight def is absent / already frameless) honor No Silent Fallbacks — a no-op mutation can't silently stop exercising the un-seatable path
  - Severity: minor
  - Forward impact: a new shared test fixture; sibling stories (158-30 degrade paths) can reuse it
- **Hardened `_resolve_dogfight_type` to a `getattr`-walk (beyond the plan's stated files)**
  - Rationale: the injector now calls this resolver from the pre-narrator pass, which legitimately runs on duck-typed fixture/fake packs (`_FakeConfrontationDef`); direct attribute access raised `AttributeError` and broke 5 existing pre-pass tests (`test_158_2_*`, `test_intent_router_confrontation_classified`). The fix mirrors the `getattr`-walk `_confrontation_verb_hits` already uses in the same path. A real `ConfrontationDef` always carries the required `resolution_mode`, so live behavior is unchanged — only fakes now resolve to None instead of crashing. Not a silent fallback: a fake pack genuinely has no dogfight def.
  - Severity: minor
  - Forward impact: `run_dogfight_dispatch` (the other caller) is unaffected — it only passes real packs; sibling Plan-2 stories that reach this resolver from the pass inherit the hardening

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Implemented only Plan-2 Tasks 1 & 4 (not 2 & 3)**
  - Spec source: `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-2-router-seater-lifecycle.md` (Tasks 1–4)
  - Spec text: the plan bundles Task 1+4 (158-29), Task 2 (158-30), Task 3 (158-35) into one document
  - Implementation: wrote RED tests for Task 1 (force-dispatch injector) + Task 4 (e2e wiring/degrade) only; omitted Task 2 (husk no-resurrect) and Task 3 (dice-replay narration anchor)
  - Rationale: Tasks 2/3 are tracked by sibling stories 158-30 / 158-35; story scope (158-29) is the highest spec authority, and the plan's own Self-Review maps them to those stories
  - Severity: minor
  - Forward impact: 158-30 and 158-35 carry their own RED phases; no coverage lost for 158-29
- **Added `make_frameless_dogfight_pack()` to the shared fixtures module (vs inline)**
  - Spec source: Plan-2 doc Task 4 Step 3
  - Spec text: "If the fixture has no seatable=False knob, build a pack whose dogfight def has no opponent_default_stats"
  - Implementation: added a reusable `make_frameless_dogfight_pack()` factory to `tests/fixtures/dogfight_playtest_encounter.py` with loud guards, instead of mutating inline in the test
  - Rationale: keeps the degraded-path test readable, reuses the Plan-1 fixture module, and the loud guards (raise if the dogfight def is absent / already frameless) honor No Silent Fallbacks — a no-op mutation can't silently stop exercising the un-seatable path
  - Severity: minor
  - Forward impact: a new shared test fixture; sibling stories (158-30 degrade paths) can reuse it

### Dev (implementation)
- **Hardened `_resolve_dogfight_type` to a `getattr`-walk (beyond the plan's stated files)**
  - Spec source: Plan-2 doc Task 1 (lists `intent_router_pass.py` + `telemetry/spans/dogfight.py` as the only modified files)
  - Spec text: the plan's injector calls `_resolve_dogfight_type(pack)` and does not mention modifying it
  - Implementation: changed `_resolve_dogfight_type` in `sidequest/agents/subsystems/dogfight.py` from direct attribute access (`cdef.resolution_mode`) to `getattr(cdef, "resolution_mode", None)` / `getattr(rules, "confrontations", None)`
  - Rationale: the injector now calls this resolver from the pre-narrator pass, which legitimately runs on duck-typed fixture/fake packs (`_FakeConfrontationDef`); direct attribute access raised `AttributeError` and broke 5 existing pre-pass tests (`test_158_2_*`, `test_intent_router_confrontation_classified`). The fix mirrors the `getattr`-walk `_confrontation_verb_hits` already uses in the same path. A real `ConfrontationDef` always carries the required `resolution_mode`, so live behavior is unchanged — only fakes now resolve to None instead of crashing. Not a silent fallback: a fake pack genuinely has no dogfight def.
  - Severity: minor
  - Forward impact: `run_dogfight_dispatch` (the other caller) is unaffected — it only passes real packs; sibling Plan-2 stories that reach this resolver from the pass inherit the hardening

### Reviewer (audit)
- **TEA — "Implemented only Plan-2 Tasks 1 & 4 (not 2 & 3)"** → ✓ ACCEPTED by Reviewer: correct story-scoping; story scope outranks the bundled plan doc, and Tasks 2/3 are tracked by 158-30/158-35. No coverage lost for 158-29.
- **TEA — "Added `make_frameless_dogfight_pack()` to the shared fixtures module (vs inline)"** → ✓ ACCEPTED by Reviewer: reasonable test infrastructure with loud guards; the in-place pydantic mutation it uses is test-only and acknowledged (preflight LOW note — not hazardous).
- **Dev — "Hardened `_resolve_dogfight_type` to a `getattr`-walk"** → ✓ ACCEPTED by Reviewer: necessary and correct (the resolver is now reached from the pre-pass on duck-typed packs); behavior unchanged for real content. **Note:** the hardening is incomplete — `:82` still accesses `cdef.confrontation_type` bare while the two guards above it use `getattr`. Logged as a LOW `[SILENT]` finding; non-blocking (cannot trigger with a real pack's required field), recommended tidy-up.
- No undocumented deviations found — TEA and Dev logged every divergence I can see in the diff.