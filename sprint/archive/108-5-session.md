---
story_id: "108-5"
jira_key: null
epic: "108"
workflow: "tdd"
---
# Story 108-5: WN Combat Player Action Surface

## Story Details
- **ID:** 108-5
- **Epic:** 108 (WN Combat System Refactor)
- **Title:** WN combat player action surface — WN action buttons replace native beat menu; flavor rider constrained flavor-only
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** sidequest-ui, sidequest-server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-14T11:34:16Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T11:05:53+00:00 | 2026-06-14T11:08:02Z | 2m 9s |
| red | 2026-06-14T11:08:02Z | 2026-06-14T11:22:39Z | 14m 37s |
| green | 2026-06-14T11:22:39Z | 2026-06-14T11:29:41Z | 7m 2s |
| review | 2026-06-14T11:29:41Z | 2026-06-14T11:34:16Z | 4m 35s |
| finish | 2026-06-14T11:34:16Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The UI half of 108-5 is already fully wired by prior stories (102-2 spell_id, 102-4 sealed round, 106-4 item-use, combat-player-echo). The flavor-rider wire contract — typed flourish rides `DICE_THROW.player_action`, bare button press omits it, InputBar locks plain Enter during confrontation — holds today; my two UI guards pass green. Affects `sidequest-ui/src/App.tsx` + `InputBar.tsx` (no production change expected — Dev's UI work is verification, not implementation). The substantive new code is server-side only.
- **Gap** (non-blocking): AC1 ("WN action buttons replace the native beat menu") is satisfied by *which beats the server sends*, which is content de-nativization — explicitly story **108-3**, out of scope here. The UI renders the server-authored `beats[]` generically; until 108-3 strips the native beat list, beneath_sunden/heavy_metal will still surface native tiles. Affects `sidequest-content` combat defs (108-3), not this story's code. No test written for AC1's button *roster* — see deviation.
- **Improvement** (non-blocking): The new `wwn.action.flavor_rider` span pairs with 108-1's `wwn.native_scaffolding_suppressed` (both fire in the same WN round — confirmed in the RED wire-test span dump). Dev should emit the rider span on the WN combat path when `payload.player_action` is non-empty, and register a `SPAN_ROUTES` entry (mirror `wn_native_scaffolding_suppressed_span` in `telemetry/spans/wn_round.py`). Slug-honest (`wwn.*`).

### Dev (implementation)
- **Question** (non-blocking): The subrepo remotes are under the GitHub org **`slabgorb-org`** (e.g. `git@github.com:slabgorb-org/sidequest-server.git`), not `slabgorb` as the per-repo CLAUDE.md files and several memory notes state. Both story branches pushed to `slabgorb-org`. Affects the SM finish step (`gh pr create -R slabgorb-org/sidequest-server` / `-R slabgorb-org/sidequest-ui`, not `slabgorb/...`) and the stale CLAUDE.md "All repos live under github.com/slabgorb/" line. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The `affected_mechanics` attribute is emitted as a constant `False` (the structural attestation — the dispatch resolves the d20/weapon dice without consulting `player_action`; the green guard `test_rider_removes_identical_opponent_hp` is the runtime proof). This mirrors how 108-1's `native_scaffolding_suppressed` always attests suppression and lets the test prove it. If a future story ever adds a path where a rider *could* feed resolution, that path must compute and pass the real value rather than defaulting. Affects `sidequest/telemetry/spans/wn_round.py::wn_flavor_rider_span`. *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **No standalone AC1 test for the WN button roster**
  - Spec source: context-story-108-5.md, AC1
  - Spec text: "The confrontation overlay displays the Without Number action button set instead of native beats … Attack / Use Item / Move-Disengage / Cast … Explicitly excluded: Brace / total-defense button."
  - Implementation: No test asserts the specific button roster renders. The UI renders the server-authored `beats[]` generically; the roster is decided by content de-nativization (story 108-3, out of scope per spec §Scope). A roster test here would test 108-3 content, not 108-5 code (project rule: don't test content via the UI). The "no Brace button" exclusion likewise lands in 108-3's beat-list strip.
  - Rationale: Testing the roster now would couple 108-5 tests to content that another story owns and that isn't on disk yet — a prod-rows-in-tests anti-pattern. 108-5's code-level contribution is the rider OTEL + the (already-wired) rider/lock contract.
  - Severity: minor
  - Forward impact: 108-3 must carry the WN-button-roster + no-Brace assertions when it strips the native beat lists.
- **AC2 covered transitively, not via a standalone dice-tray render test**
  - Spec source: context-story-108-5.md, AC2
  - Spec text: "Each button fires a real WN roll via WithoutNumberRulesetModule … the ADR-074 dice tray renders the WN attack roll."
  - Implementation: The real WN roll is exercised by the green guard `test_rider_removes_identical_opponent_hp` (asserts the bound module removed opponent HP > 0 through the production dispatch) and by the wire test's `wwn.round.resolved`/`encounter.beat_applied` spans. The UI dice-tray render is exercised via `onDiceThrow` firing in the UI guards (the dice-settled signal), not a separate InlineDiceTray render assertion.
  - Rationale: 108-1 already proves the WN roll resolves; re-asserting it standalone would duplicate. The dice tray is unchanged ADR-074 infrastructure (a WWN attack IS a d20 throw) — no new render behavior to pin.
  - Severity: minor
  - Forward impact: none.
- **AC4 (bare combat free-text) — no new test; existing coverage relied upon**
  - Spec source: context-story-108-5.md, AC4
  - Spec text: "A bare text submission (text with no action button) is not submitted during combat."
  - Implementation: The UI InputBar Enter-lock is already asserted by `InputBar.test.tsx` (does not submit on Enter when `confrontationActive`); not re-proven here. No server test is written because the server cannot resolve a combat outcome without a `beat_id` (the throw path requires one) — the invariant is structural, and the lock is UI-side per the spec ("UI-side lock only").
  - Rationale: Avoid duplicating existing InputBar coverage; the server half is a structural impossibility, not a behavior needing a guard.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- No deviations from spec. The `wwn.action.flavor_rider` span was implemented exactly as the AC specifies (`attached=true`, `affected_mechanics=false`, slug-honest). The only implementation choice — placing the emit at a single chokepoint in `dispatch_dice_throw` (the WN hp_depletion combat guard) rather than inside the sealed-round branch — covers both the sealed and legacy WN combat paths with one guarded call and is consistent with TEA's suggested locus; it does not change behavior the tests pin.

### Reviewer (audit)
- **TEA: No standalone AC1 test for the WN button roster** → ✓ ACCEPTED by Reviewer: correct scoping — the button roster is content de-nativization (108-3); testing it here would couple 108-5 to content another story owns. Forward impact (108-3 carries the no-Brace + roster assertions) is logged.
- **TEA: AC2 covered transitively, not via a standalone dice-tray render test** → ✓ ACCEPTED by Reviewer: the real WN roll is exercised by `test_rider_removes_identical_opponent_hp` (HP removed via the bound module) and the wire test's `wwn.round.resolved`/`encounter.beat_applied`; the dice tray is unchanged ADR-074 infrastructure.
- **TEA: AC4 (bare combat free-text) — existing coverage relied upon** → ✓ ACCEPTED by Reviewer: the InputBar Enter-lock is already pinned by `InputBar.test.tsx`; the server cannot resolve combat without a `beat_id` (structural). Re-proving would duplicate.
- **Dev: No deviations from spec; single-chokepoint emit locus** → ✓ ACCEPTED by Reviewer: verified the guard covers both the sealed (wwn) and legacy (swn) WN combat paths; placement at L711 sits after the `cdef is None` guard (L379) and all input validation (stat L493, cast L466-475), so the span fires only on a validated throw. Sound.
- No undocumented deviations found.

## Sm Assessment

**Routing:** Phased TDD. setup (done) → **red (TEA/Fezzik)** → green (Dev) → review (Reviewer) → finish (SM).

**Dependency:** 108-1 (WN round engine core cut, ADR-143) — MERGED (server PR #849). The bound `WithoutNumberRulesetModule` resolution path this story renders against is live on `develop`. No blocker.

**Repos:** `sidequest-server` (WN roll wiring + OTEL) and `sidequest-ui` (action buttons replacing the native beat menu). Both branched: `feat/108-5-wn-combat-action-surface` off `develop`.

**Spec:** `docs/superpowers/specs/2026-06-14-wn-combat-action-surface-design.md`

**Acceptance criteria for the RED phase (failing tests first):**
1. WN action buttons — Attack / Use Item / Move-Disengage / Cast — replace the native beat menu in the combat surface.
2. **No Brace / total-defense button.** Defense is passive AC in WWN; a brace/full-defense action must NOT be offered (per ADR-143 amendment striking "full defense" from the WN action set).
3. Each button fires a *real* WN roll via the bound `WithoutNumberRulesetModule` (the 108-1 resolution path), rendered in the ADR-074 dice tray.
4. `DICE_THROW.player_action` is retained as an **RP-flavor rider only** — narrator hook, ZERO mechanics (the "chandelier swing"). Assert it affects no mechanical outcome.
5. A bare combat free-text submission (no action button) does **not** resolve to a combat outcome.
6. OTEL `wn.action.flavor_rider{affected_mechanics=false}` is emitted, proving the rider stayed flavor-only.

**Doctrine guardrail for implementers (SOUL / ADR-143):** Bind the ruleset, don't balance it. The native beat menu / dials / per-beat reprisal are *removed* from the WN combat path — not converted, gated, or tuned to coexist with the bound WN roll. If anyone catches themselves making a native mechanic "work with" the WN action surface, stop.

**Wiring requirement (CLAUDE.md):** Every test suite needs a wiring test — the action buttons must be proven reachable from a production UI path and the WN roll proven to hit the real bound module, not a synthetic fixture. The flavor-rider OTEL is the lie-detector that the rider carried no mechanics.

Handing the red phase to Fezzik.
---
## TEA Assessment

**Tests Required:** Yes
**Phase:** finish

**Test Files:**
- `sidequest-server/tests/integration/test_108_5_wn_flavor_rider.py` — the WN flavor-rider OTEL contract (3 RED + 3 green-guard).
- `sidequest-server/tests/integration/_wn_round_102_4.py` — extended the shared `dispatch_throw` helper with an optional `player_action` rider (backward-compatible).
- `sidequest-ui/src/__tests__/wn-flavor-rider-108-5.test.tsx` — 2 App-level wiring guards on the outbound `DICE_THROW`.

**Tests Written:** 8 tests (6 server, 2 UI) across the in-scope ACs.
**Status:** RED — 3 server span tests fail for the right reason (`wwn.action.flavor_rider` does not exist yet); 5 guards pass (3 server inertness/attach/no-false-positive, 2 UI wire-contract).

**RED verification (measured, not asserted):**
```
server: 3 failed, 3 passed  (SIDEQUEST_DATABASE_URL set, content on disk, -n0)
  FAIL test_attached_rider_emits_flavor_rider_span        ← span missing
  FAIL test_flavor_rider_span_marks_mechanics_unaffected  ← span/attrs missing
  FAIL test_flavor_rider_span_wired_end_to_end            ← span missing (round DID resolve: wwn.round.resolved fired)
  PASS test_rider_removes_identical_opponent_hp           ← green guard
  PASS test_rider_reaches_narrator_replay_text            ← green guard
  PASS test_absent_rider_emits_no_flavor_rider_span       ← green guard
ui: 2 passed (both guards — UI contract already wired)
```

### What Dev must build (GREEN)
The single new production behavior: emit `wwn.action.flavor_rider` on the WN combat dispatch path when `payload.player_action` is non-empty, carrying `attached=True` and `affected_mechanics=False`, slug-honest (`wwn.*`). Mirror `wn_native_scaffolding_suppressed_span` in `sidequest/telemetry/spans/wn_round.py` and register a `SPAN_ROUTES` entry. Emit point: `dispatch_dice_throw` in `sidequest/server/dispatch/dice.py` (the WN sealed-round branch, near the existing `payload.player_action` handling ~L485 / the replay-text build ~L982-999). Reachable from the handler→dispatch→round chain (the wire test demands it). Do NOT thread the rider into resolution — it must stay inert (the green guards enforce this).

### Rule Coverage

| Rule (source) | Test(s) | Status |
|---|---|---|
| OTEL Observability Principle — every subsystem decision emits a span (CLAUDE.md / AC5) | `test_attached_rider_emits_flavor_rider_span`, `test_flavor_rider_span_marks_mechanics_unaffected`, `test_flavor_rider_span_wired_end_to_end` | RED (failing) |
| Wiring test required — span reachable from production chain (CLAUDE.md) | `test_flavor_rider_span_wired_end_to_end` (server), both UI guards (outbound DICE_THROW) | RED (server) / pass (UI) |
| No covert mechanization — rider is inert (SOUL "Bind the Ruleset"; AC3) | `test_rider_removes_identical_opponent_hp`, `test_rider_reaches_narrator_replay_text` | pass (guard) |
| No false-positive telemetry (python-review #6 test quality; OTEL signal hygiene) | `test_absent_rider_emits_no_flavor_rider_span` | pass (guard) |
| Slug-honesty invariant (WN family spans are `wwn.*`) | `test_attached_rider_emits_flavor_rider_span` (dishonest-slug assertion) | RED (failing) |
| Rider opt-in, never fabricated (AC3/AC4 UI; spec rider contract) | UI `OPT-IN: bare button press carries no player_action key` | pass (guard) |

**Rules checked:** The python lang-review checklist is primarily Dev production-hygiene (silent excepts, mutable defaults, async pitfalls, etc.) — not applicable to test authoring. The load-bearing rules for this story are the OTEL Observability Principle and test-quality (#6); both are covered above.
**Self-check (python-review #6):** All 8 tests assert specific values (span presence, `is True`/`is False` attrs, exact HP equality, `PLAYER_ACTION:` substring, payload field values). No vacuous `assert True` / truthy-only / always-None assertions. No `let _ =`. Clean.

**Handoff:** To Inigo Montoya (Dev) for the GREEN phase — implement the `wwn.action.flavor_rider` span (server only; the UI guards confirm no UI production change is needed).
---
## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/telemetry/spans/wn_round.py` — added `wn_flavor_rider_span` helper + a `{slug}.action.flavor_rider` `SPAN_ROUTES` entry per WN family slug (swn/wwn/cwn/awn), mirroring `wn_native_scaffolding_suppressed_span`. Slug-honest; `_require_family_slug` enforced.
- `sidequest-server/sidequest/server/dispatch/dice.py` — import `wn_flavor_rider_span`; emit it on the WN combat path (`isinstance(ruleset, WithoutNumberRulesetModule) and cdef.win_condition == "hp_depletion" and payload.player_action.strip()`). The rider still rides into `replay_action_text` unchanged; the dice are resolved without consulting it.
- `sidequest-server/tests/integration/test_108_5_wn_flavor_rider.py` — `ruff format` reflow only (no behavior change; TEA-authored).
- (UI: no production change — TEA's two wire-contract guards already pass against the existing App. Branch pushed for the SM to PR.)

**Tests:** 6/6 server GREEN (the 3 formerly-RED span tests now pass; the 3 green guards stayed green). 2/2 UI guards green. No regressions — `test_108_1` + `test_102_4` + `tests/telemetry/` = 388 passed, 6 skipped.
**Lint/format:** `ruff check` clean; `ruff format --check` clean on all changed files.
**Branches (pushed):**
- `sidequest-server` `feat/108-5-wn-combat-action-surface` (production + tests)
- `sidequest-ui` `feat/108-5-wn-combat-action-surface` (guard tests only)

**What was built:** The single new production behavior — the `wwn.action.flavor_rider` OTEL lie-detector (AC5). It proves the player's RP-flavor rider was attached as narrator color only and never entered mechanical resolution, pairing with 108-1's `native_scaffolding_suppressed` to show the WN round resolved on the button and only on the button. The inertness it attests is independently enforced by the green guard comparing opponent HP with/without the rider.

**Verification command (reproducible):**
```
SIDEQUEST_DATABASE_URL="postgresql://$USER@localhost:5432/sidequest_test" \
  uv run pytest tests/integration/test_108_5_wn_flavor_rider.py -p no:randomly -n0 -q
# → 6 passed
```

**Handoff:** To Westley (Reviewer) for code review.
---
## Delivery Findings (Reviewer)

### Reviewer (code review)
- **Improvement** (non-blocking): The test module docstring of `tests/integration/test_108_5_wn_flavor_rider.py` still reads "RED today (the span does not exist yet)" — now stale post-GREEN. Affects that file's header (a one-line note that these are the now-passing 108-5 tests would prevent a future reader mistaking them for still-failing). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The `affected_mechanics` span attribute is a hardcoded constant `False` — it is a documentary attestation, not a runtime-computed lie-detector. The actual inertness enforcement is the green guard `test_rider_removes_identical_opponent_hp`. This matches the 108-1 `native_scaffolding_suppressed` precedent and conforms to the AC (which literally specifies `affected_mechanics=false`), so it is accepted; flagged only so a future story that adds a rider-can-affect-resolution path computes the real value. Affects `sidequest/telemetry/spans/wn_round.py::wn_flavor_rider_span`. *Found by Reviewer during code review.*

---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (396 passed, 0 failed, 6 pre-existing skips; 0 code smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [SILENT] below) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [TEST] below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [DOC] below) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [TYPE] below) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [SEC] below) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [SIMPLE] below) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [RULE] below) |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents`, their domains assessed by Reviewer directly per the gate's "assess the domain yourself" rule)
**Total findings:** 0 confirmed blocking, 0 dismissed, 2 deferred (non-blocking improvements logged in Delivery Findings)

---
## Reviewer Assessment

**Verdict:** APPROVED

**Scope:** A tightly-scoped, additive observability change implementing AC5 — the `{slug}.action.flavor_rider` OTEL lie-detector. Server production delta is ~50 LOC across two files (`telemetry/spans/wn_round.py` helper + route; `server/dispatch/dice.py` emit). UI delta is test-only. No mechanical-resolution code was touched (SOUL "Bind the Ruleset" honored — purely additive telemetry, nothing tuned or gated).

**Data flow traced:** player types a flourish → `DICE_THROW.player_action` → `dispatch_dice_throw` → guard `isinstance(ruleset, WithoutNumberRulesetModule) and cdef.win_condition=="hp_depletion" and player_action.strip()` at `dice.py:711` → `wn_flavor_rider_span(slug=ruleset.slug, ...)` → `Span.open("{slug}.action.flavor_rider", {attached:True, affected_mechanics:False})`. The same `player_action` independently flows into `replay_action_text` (`dice.py:982-999`); the d20/weapon dice are resolved without reading it. Safe because: the emit sits AFTER the `cdef is None` guard (`dice.py:379`) and all input validation (stat `:493`, cast-shape `:466-475`), so the span fires only on a validated throw; `ruleset.slug` is always one of swn/wwn/cwn/awn (verified: `wwn.py:45`, `swn.py:46`, `cwn.py:21`, `awn.py:28`), so `_require_family_slug` never trips for a real WN module (fail-loud-by-design otherwise).

**Pattern observed:** the new helper + `SPAN_ROUTES` entry mirror `wn_native_scaffolding_suppressed_span` directly above them (`telemetry/spans/wn_round.py`) — same slug-parametrized family registration, same `Span.open(...)` idiom, same `_require_family_slug` guard. Consistent with the module.

**Error handling:** `_require_family_slug` RAISES on an unknown slug (No Silent Fallbacks) — the opposite of a swallow. No try/except added; no error paths introduced.

### Observations (tagged by domain; 8 subagent domains covered by Reviewer)
- [VERIFIED] No closure bug in the `for _slug in WN_FAMILY_SLUGS` loop — the `extract` lambda references only `span` (its parameter), never `_slug`; the route key uses `f"{_slug}.action.flavor_rider"` eagerly. Evidence: `wn_round.py` new SPAN_ROUTES block; corroborated independently by reviewer-preflight.
- [EDGE][VERIFIED] Boundary: `payload.player_action` empty/whitespace → guard's `.strip()` is falsy → no span (and `test_absent_rider_emits_no_flavor_rider_span` pins it). `beat_id` None → `payload.beat_id or ""` → span records `""`, harmless. cdef None → impossible at L711 (guarded at L379).
- [SILENT][VERIFIED] No swallowed errors or silent fallbacks added. The one defaulting expression (`payload.beat_id or ""`) defaults an optional field for display, not a masked failure.
- [TEST][VERIFIED] Test quality is strong: `test_rider_removes_identical_opponent_hp` pins `random.randint` to min, runs the strike twice, and asserts `removed_rider == removed_plain` AND `removed_plain > 0` (so the equality is not vacuously `0 == 0`). The wire test asserts the `wwn.round.resolved` precondition before the rider assertion, distinguishing "round didn't run" from "span missing". No vacuous assertions; OTEL bools assert via `is True`/`is False` (preserved by InMemorySpanExporter — confirmed by GREEN run). A genuine wiring test (`test_flavor_rider_span_wired_end_to_end`) drives the real `WebSocketSessionHandler`.
- [DOC][LOW] The test module docstring still says "RED today (the span does not exist yet)" — stale now that the span exists and the tests pass. Non-blocking (logged as a Delivery Finding). The `dice.py` emit comment is accurate ("the text still rides into replay_action_text below, but the d20/weapon dice are computed without consulting it").
- [TYPE][VERIFIED] `wn_flavor_rider_span` is fully keyword-only and typed (`slug: str`, `actor: str`, `beat_id: str`, `affected_mechanics: bool = False`, `-> None`); `**attrs: Any` mirrors the sibling helpers. No stringly-typed escape; slug constrained at runtime by `_require_family_slug`.
- [SEC][VERIFIED] The freeform `player_action` text is NOT placed into any span attribute (only `actor=character_name` and `beat_id` are) — no user text in telemetry, so no new injection/PII surface in the span. The rider's existing path to `replay_action_text`/narrator is unchanged (ADR-047 sanitization upstream). No auth/secret changes.
- [SIMPLE][LOW] `affected_mechanics` is a parameter (default `False`) the caller never overrides — mildly speculative, but it mirrors the family-helper shape and is explained by the documentary-attestation design. Not worth churn.
- [RULE][VERIFIED] OTEL Observability Principle satisfied — the new subsystem decision emits a span AND registers a `SPAN_ROUTES` entry so the watcher translator types it for the GM panel. No-source-text-wiring-test rule honored (the wire test asserts via `otel_capture`, not a source grep). python-review checklist: no silent excepts (#1), no mutable defaults (#2), boundaries typed (#3), import added in alpha order (#10), test quality clean (#6).

### Rule Compliance
| Rule (source) | Instances in diff | Verdict |
|---|---|---|
| OTEL Observability Principle (CLAUDE.md) — every subsystem decision emits a span + route | `wn_flavor_rider_span` + `SPAN_ROUTES["{slug}.action.flavor_rider"]` | ✓ compliant |
| No Silent Fallbacks (CLAUDE.md) | `_require_family_slug` raises on bad slug; no new fallback | ✓ compliant |
| No-source-text wiring tests (server CLAUDE.md) | `test_flavor_rider_span_wired_end_to_end` asserts via `otel_capture` | ✓ compliant |
| Every test suite needs a wiring test (CLAUDE.md) | wire test drives `WebSocketSessionHandler.handle_message` | ✓ compliant |
| SOUL "Bind the Ruleset, Don't Balance It" | change is additive telemetry; no native mechanic tuned/gated against WN | ✓ compliant |
| python-review #3 type annotations at boundaries | `wn_flavor_rider_span` signature fully annotated | ✓ compliant |
| python-review #6 test quality | no vacuous/always-None/`assert True`; meaningful values asserted | ✓ compliant |
| python-review #10 import hygiene | `wn_flavor_rider_span` added in alphabetical position | ✓ compliant |
| Slug-honesty (WN family spans are `{slug}.*`) | helper uses `f"{slug}.action.flavor_rider"`, `_require_family_slug` enforced | ✓ compliant |

### Devil's Advocate
Let me argue this code is broken. **First attack — the span is a rubber stamp.** `affected_mechanics` is hardcoded `False`; if a future Dev regressed the dispatch to feed `player_action` into a to-hit bonus, the span would *still* cheerfully report `False`, and the GM panel — the supposed lie detector — would be lying. Is the "lie detector" actually detecting anything? Rebuttal: the span's job here is to mark *that a rider was present on a resolved button action* (visible signal the panel can correlate); the *inertness* is enforced by `test_rider_removes_identical_opponent_hp`, which pins the RNG and asserts byte-identical HP removal with and without the rider — that test WOULD fail on the hypothetical regression. So the detection exists; it lives in the test, with the span as the panel-visible breadcrumb. This is the same division 108-1 uses. Accept, with a non-blocking note for the future. **Second attack — the guard fires in the wrong places.** Could the span fire when it shouldn't (e.g., a dial confrontation under a WN pack)? No: the guard requires `cdef.win_condition == "hp_depletion"`, which excludes chase/negotiation dial confrontations — exactly the scope the spec carves out. Could it fail to fire when it should (MP, second player's rider)? Each player's `DICE_THROW` is a separate `dispatch_dice_throw` call, so each rider gets its own span. **Third attack — crash surface.** Does `ruleset.slug` or `cdef.win_condition` throw? `cdef` is guaranteed non-None by the L379 guard; `ruleset.slug` resolves to a family slug for every WN subclass (verified). A non-WN ruleset short-circuits the `isinstance` and never touches `.slug`. **Fourth attack — a confused user.** A player who types only whitespace gets no rider span (`.strip()` falsy) and a pure mechanical action — correct, matches the UI opt-in guard. **Fifth — concurrency.** The span is opened-and-closed synchronously within the dispatch; no shared state mutated. Nothing here breaks. The devil goes hungry.

**Conclusion:** No Critical or High findings. Two non-blocking Low/Improvement notes (stale RED docstring; documentary-attestation `affected_mechanics`) logged as Delivery Findings. Tests green (396 passed, 0 failed), lint and format clean, wiring proven end-to-end, project rules satisfied, doctrine (SOUL Bind-the-Ruleset, OTEL) honored.

**Handoff:** To Vizzini (SM) for finish-story.