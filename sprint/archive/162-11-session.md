---
story_id: "162-11"
jira_key: ""
epic: "162"
workflow: "tdd"
---
# Story 162-11: Understudy perception real-UI aria fidelity

## Story Details
- **ID:** 162-11
- **Jira Key:** (none — Jira not configured for this story)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-08T00:00:56Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-07T22:44:22.119967+00:00 | 2026-07-07T22:46:24Z | 2m 1s |
| red | 2026-07-07T22:46:24Z | 2026-07-07T22:59:30Z | 13m 6s |
| green | 2026-07-07T22:59:30Z | 2026-07-07T23:10:06Z | 10m 36s |
| review | 2026-07-07T23:10:06Z | 2026-07-07T23:28:00Z | 17m 54s |
| red | 2026-07-07T23:28:00Z | 2026-07-07T23:39:42Z | 11m 42s |
| green | 2026-07-07T23:39:42Z | 2026-07-07T23:46:27Z | 6m 45s |
| review | 2026-07-07T23:46:27Z | 2026-07-08T00:00:56Z | 14m 29s |
| finish | 2026-07-08T00:00:56Z | - | - |

## Sm Assessment

**Selected:** 162-11 (p1, 3pts, tdd) — the only p1 in the backlog, top priority.

**Problem:** The `two_names_one_enemy` (162-7) understudy detector, and the tool-wide `log:`/panel perception assumptions, parse aria tokens — region "Enemies", `listitem`, `log:` — that do not exist in the sidequest-ui DOM. The detector returns `None` on every real session, so identity-fork detection is inert in production. This is a perception-fidelity gap between what understudy's `perceive()` expects and what the UI actually exposes.

**Scope (understudy + ui):**
1. Capture the real ConfrontationOverlay/narration aria via `perceive()` against a live session — establish ground truth for what the UI emits today.
2. Add perceivable ARIA roles to the opponent-name + narration surfaces in sidequest-ui **only if** the capture shows they're missing (don't invent tokens the detector expects; reconcile to reality).
3. Reconcile understudy detector regexes + wiring fixtures so identity-fork detection fires in a live confrontation.

**Why it matters:** The fix benefits all understudy detectors, not just `two_names_one_enemy` — it re-grounds the whole perception layer against real UI aria. Per the naivety invariant, understudy must see only what a player sees; the aria surface *is* that view, so it must be real.

**Acceptance criteria** (see `sprint/context/context-story-162-11.md` for detail):
- Real ARIA captured from ConfrontationOverlay/narration surfaces and documented.
- UI exposes perceivable roles on opponent-name + narration surfaces (if gap confirmed).
- `two_names_one_enemy` detector fires in a live/fixture confrontation (not `None`).
- Wiring test proves the detector is reachable from a real perceive() path.

**Routing:** tdd phased workflow → RED phase → **tea** (Amos Burton) writes failing tests that assert the detector fires against real-UI aria. This is a cross-repo change (understudy detector + ui aria); TEA should pin the failing behavior before Dev touches either side.

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `sidequest-ui/src/components/__tests__/ConfrontationOverlay.aria-enemies-162-11.test.tsx` — the opponent surface must expose `role="region"` named "Enemies" with each foe a named `listitem`, scoped to foes only (player excluded). (AC2, AC3)
- `sidequest-ui/src/components/__tests__/NarrationScroll.aria-log-162-11.test.tsx` — the narration stream must be `role="log"` + `aria-live="polite"` on the scroll surface. (AC1, AC2)
- `sidequest-understudy/tests/wiring/fixture_identity_fork_realdom.html` — NEW fixture: faithful reproduction of the real ConfrontationOverlay/NarrationScroll DOM (portrait chip + nested name span in a listitem; narration paragraph nested under the log) with the target roles applied.
- `sidequest-understudy/tests/wiring/test_identity_fork_realdom_162_11.py` — wiring test driving the REAL run loop over that fixture; asserts `two_names_one_enemy` surfaces in findings.json through the real `perceive() → aria_snapshot → detector` path. (AC3, AC4, AC5)

**Tests Written:** 7 tests (6 UI + 1 understudy wiring) covering AC1–AC5.
**Status:** RED (verified — see below). AC6 (no regressions) is a GREEN-phase gate.

### RED verification (run inline)
- UI: `npx vitest run` → **6 failed / 6** — `getByRole('region', {name:/enemies/i})` and `getByRole('log')` both "Unable to find" (roles absent; component renders fine — failure is role-absence, not a crash).
- Understudy: `uv run pytest tests/wiring/` → **1 failed (mine) / 3 pre-existing passed** — no `two_names_one_enemy` signal emitted against real-DOM markup (`signals: []`). Ruff clean.

### Root-cause evidence for Dev (GREEN)
Captured `aria_snapshot()` of the real-DOM fixture:
```
- region "Enemies":
  - listitem: T Thief
- log:
  - paragraph: Molgrath the Eyeless lunges at you from the dark.
```
Two concrete reconciliation gaps this exposes:
1. **`_LOG` (findings/detect.py):** matches only inline `log: <text>`. Playwright renders the real narration as `- log:` with the prose on a CHILD `- paragraph:` line → `narration` parses empty → detector returns `None` (the primary inert-in-production cause).
2. **`_LISTITEM` / `_enemy_labels`:** the ActorChip portrait initial is read as text, so the label is `T Thief`, not `Thief`. Harmless for the fork case here, but in the consistent-naming case it would produce a FALSE fork (`Thief` ≠ `T Thief`). GREEN should either strip the chip initial from the perceived label or expose the clean name as the listitem's accessible name (UI side).

Two valid GREEN paths (story decision tree): fix the detector parser to read nested `log:`/`listitem` accessible text, and/or shape the UI roles so aria_snapshot yields clean `listitem "Thief"` / inline `log:` tokens. The tests pin the OUTCOME (finding fires against real-shaped markup), not the mechanism.

### Rule Coverage
| Rule source | Check | Enforced by |
|-------------|-------|-------------|
| SOUL "No Silent Fallbacks" | detector must not silently return `None` on valid real input | understudy wiring test (asserts finding fires) |
| understudy CLAUDE.md "No half-wired features" / "Every Test Suite Needs a Wiring Test" | detector reachable end-to-end through real perceive() path | `test_identity_fork_realdom_162_11.py` (real run loop) |
| Naivety invariant | detection reads screen-visible aria only (no creature_id/alias/OTEL) | fixture is plain DOM; no engine identity available |
| lang-review python.md §Test quality | no vacuous assertions / no assertion-less tests | new pytest asserts non-empty findings + grade ∈ {behavioral,confirmed} |

**Rules checked:** test-quality + silent-fallback + wiring rules have coverage. The remaining python.md/typescript.md checks apply to Dev's GREEN implementation (detector parser + UI role additions).
**Self-check:** 0 vacuous tests — every test asserts a specific role/name/finding, not a truthy placeholder.

**Handoff:** To Dev (Naomi Nagata) for GREEN — reconcile the detector's `log:`/`listitem` parsing to real aria_snapshot output AND add the region/listitem/log roles to ConfrontationOverlay + NarrationScroll so all 7 tests pass.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/components/ConfrontationOverlay.tsx` — the roster opponent group is now an ARIA `region` named "Enemies" whose foes are `listitem`s; the portrait chip takes a `decorative` prop (`aria-hidden`) and each foe carries an `sr-only` clean name, so the listitem's accessible name is the foe name without the portrait-initial glyph. Scoped to foes only (`group.every(side==="opponent")`) — never the player.
- `sidequest-ui/src/components/NarrationScroll.tsx` — narration stream is now `role="log"` + `aria-live="polite"` so aria_snapshot presents it as `log:` and appended beats are announced.
- `sidequest-understudy/src/understudy/findings/detect.py` — new `_narration`/`_node_text` read Playwright's real NESTED log (`- log:` opener + prose on child `- paragraph:` lines) as well as the inline `log: <text>` form. Once inside a log region, child lines are read as prose (a literal "log:" in narration is never re-parsed as a node). The `two_names_one_enemy` narration extraction now calls `_narration(lines)`.

**Root cause fixed:** the detector was inert not because its regexes were wrong but because the live UI emitted none of the aria tokens it greps for, and Playwright nests `role=log` prose under a child line. Fix is UI-side (emit the roles) + a small detector reconciliation (read nested log). The portrait-initial contamination (`T Thief`) is fixed at the source (decorative `aria-hidden` portrait + `sr-only` name) so the real UI yields a clean `listitem: Thief`.

**Tests:** 7/7 story tests passing (GREEN).
- UI: 6/6 new tests pass; **full suite 2557/2557** (311 files) — no regressions. ESLint clean, `tsc --noEmit` clean.
- Understudy: new real-DOM wiring test passes; **full suite 268/268** — no regressions. Ruff clean.

**Verification:** the understudy wiring test drives the real `perceive() → aria_snapshot → detector` path over a file:// fixture (real Playwright), which is the strongest automated proof for a perception change. Captured aria_snapshot of the fixed-shape fixture confirms `region "Enemies"` + `listitem` + nested `log:` are read and the fork fires. No visual change (sr-only names + aria metadata only); no OTEL needed (understudy is a test harness, UI change is accessibility metadata, not a backend subsystem decision).

**Branch:** `feat/162-11-understudy-perception-aria-fidelity` (pushed — understudy `18dceea`, ui `b9cac24`).

**Handoff:** To verify/review phase.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The `_LOG` narration parser reads only inline `log: <text>`; real aria_snapshot nests the prose under `- log:` as a child `- paragraph:` line. This makes the detector inert against the real narration surface. Affects `sidequest-understudy/src/understudy/findings/detect.py` (`_LOG` / narration extraction must read child text lines). *Found by TEA during test design.*
- **Improvement** (non-blocking): The `_enemy_labels` listitem parser captures the ActorChip portrait initial ("T Thief"), which can produce a false fork in the consistent-naming case. Affects `sidequest-understudy/src/understudy/findings/detect.py` and/or `sidequest-ui/src/components/ConfrontationOverlay.tsx` (strip the chip initial, or expose the clean opponent name as the listitem accessible name). *Found by TEA during test design.*
- **Gap** (non-blocking): The opponent NAME is visible text only in `ThemPanel`; the `dial-scoreboard` roster renders foes as portrait initials with the name in a `title`. The "Enemies" region + named listitems will need the name to be a perceivable list-item child, not just a tooltip. Affects `sidequest-ui/src/components/ConfrontationOverlay.tsx`. *Found by TEA during test design.*
- (Rework R1) No new upstream findings during rework — the review's blocking findings are now pinned by failing tests; Dev's GREEN is the 3 changes listed in the TEA Assessment (Rework). *Found by TEA during rework.*

### Dev (implementation)
- **Improvement** (non-blocking): The "Enemies" region lives on the roster opponent group, which lists ALL foes; `ThemPanel` (the single-opponent spotlight) still exposes no region/listitem role. If a future understudy detector wants the spotlight foe specifically, `ThemPanel` would need its own roles. Affects `sidequest-ui/src/components/ConfrontationOverlay.tsx` (`ThemPanel`). *Found by Dev during implementation.*
- **Improvement** (non-blocking): Other narration-reading understudy detectors (if any beyond `two_names_one_enemy`) now benefit from the nested-`log:` parser only if they route through `_narration`; any that inline-grep `_LOG` directly should adopt the helper. Affects `sidequest-understudy/src/understudy/findings/detect.py`. *Found by Dev during implementation.*
- No blocking upstream findings during implementation.
- (Rework R1) No new upstream findings — the review's blocking findings are fixed and mutation/regression-verified. *Found by Dev during rework.*

### Reviewer (code review)
- **Conflict** (blocking): `_LOG = re.compile(r"\blog\s*:\s*(.+)$")` — `(.+)` matches a whitespace-only remainder, so a bare `log:` opener with ANY trailing space is misrouted to the inline branch, drops the nested child prose, and `two_names_one_enemy` returns `None` on a valid fork — the exact silent-fallback the story exists to kill (SOUL "No Silent Fallbacks"). Latent under today's DOM (no trailing space) but fragile. Affects `sidequest-understudy/src/understudy/findings/detect.py` (require a non-whitespace char, e.g. `r"\blog\s*:\s*(\S.*)$"`, so `_LOG_OPEN` reliably wins; add a unit test that reproduces the None). *Found by Reviewer during code review.*
- **Gap** (blocking): Nothing in EITHER repo guards the story's central property — a clean perceived foe name (portrait initial excluded). The UI test asserts `li.textContent` (which includes the aria-hidden "T"), and the understudy fixture omits the `aria-hidden` the shipped `ActorChip` sets, so both stay green even with the guard removed (mutation-verified). Affects `sidequest-ui/src/components/__tests__/ConfrontationOverlay.aria-enemies-162-11.test.tsx` (assert the listitem's portrait is `aria-hidden` and the perceived name has no initial) and `sidequest-understudy/tests/wiring/fixture_identity_fork_realdom.html` (add `aria-hidden` to the portrait to match the shipped DOM; add a CONSISTENT-naming case that fails on contamination). *Found by Reviewer during code review.*
- **Gap** (blocking): The new `_narration`/`_node_text` helpers — the core of the fix — have no direct unit coverage; only one wiring-test DOM shape exercises them. Affects `sidequest-understudy/tests/test_two_names_one_enemy.py` (add pure-function cases: nested `log:`, literal "log:" in prose, `text "quoted"` node, empty/whitespace paragraph, two sequential log regions, trailing-space opener). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `role="listitem"` is applied without a `role="list"`/`role="group"` parent (WCAG 1.3.1 aria-required-parent) — works in aria_snapshot but is real screen-reader debt. Affects `sidequest-ui/src/components/ConfrontationOverlay.tsx` (wrap the foe listitems in a `role="list"` inside the "Enemies" region). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `NarrationScroll` is only tested with `messages={[]}`, so no test proves narrated text is a DOM descendant of the `role="log"` node. Affects `sidequest-ui/src/components/__tests__/NarrationScroll.aria-log-162-11.test.tsx`. *Found by Reviewer during code review.*
- (Re-Review R1) **Improvement** (non-blocking, fast-follow): the two understudy fixtures omit the `role="list"` wrapper the shipped `ConfrontationOverlay.tsx:595` now renders, so their "faithful reproduction" comment overstates fidelity. Detector is verified-tolerant (no test compromised). Affects `sidequest-understudy/tests/wiring/fixture_identity_fork_realdom.html` + `fixture_identity_consistent_realdom.html` (add a `role="list"` wrapper, or soften the claim). *Found by Reviewer during re-review.*
- (Re-Review R1) **Improvement** (non-blocking, fast-follow): non-null assertion `.find(...)!` (typescript.md #1) on an `Array.find()` result. Affects `sidequest-ui/src/components/__tests__/ConfrontationOverlay.aria-enemies-162-11.test.tsx:79` (guard the result). *Found by Reviewer during re-review.*
- (Re-Review R1) **Improvement** (non-blocking, fast-follow): two UI test-file headers still say "Story 162-11 (RED)" (the Python file was reworded). Affects `ConfrontationOverlay.aria-enemies-162-11.test.tsx:7` + `NarrationScroll.aria-log-162-11.test.tsx:11`. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC4 live-stack test rendered as a real-DOM Playwright fixture, not a full server+UI e2e run**
  - Spec source: context-story-162-11.md, AC4
  - Spec text: "A scenario ... runs understudy against the real server + real UI, and the two_names_one_enemy detector fires"
  - Implementation: The RED wiring test drives the real understudy run loop over a static HTML fixture that faithfully reproduces the live ConfrontationOverlay/NarrationScroll DOM (captured via aria_snapshot), rather than standing up a live server + Vite UI in the unit suite.
  - Rationale: A full server+UI e2e is heavy and flaky for a per-commit RED gate; the fixture exercises the same `perceive() → aria_snapshot → detector` path with the real DOM shape, which is where the production-inert bug lives. A true end-to-end confirmation belongs in the manual/`sq-playtest` pass, not the automated RED suite.
  - Severity: minor
  - Forward impact: Dev/Reviewer should still confirm the detector fires in one real live session (manual or playtest) before finish; the automated suite proves the parser reconciliation, not the live wire.
- **(Rework R1) Clean-name guard asserts the portrait's `aria-hidden` attribute + sr-only name, not the listitem's computed accessible name**
  - Spec source: Reviewer Assessment [HIGH] #2a (and its NOTE)
  - Spec text: Reviewer suggested `getByRole('listitem', { name: /^thief$/i })` to assert the clean name.
  - Implementation: Used `within(item).getByTestId('actor-portrait')).toHaveAttribute('aria-hidden','true')` + `getByText('Thief')` instead of a role-name query.
  - Rationale: `listitem` is NOT a name-from-content role, so its computed accessible name is empty even when the markup is correct — `getByRole('listitem',{name})` would resolve nothing and the test would fail on GREEN code. The attribute+text assertion is the faithful guard that goes red iff the `aria-hidden` guard is removed (the regression review demonstrated).
  - Severity: minor
  - Forward impact: none — the assertion is stricter, not weaker; it directly pins the mechanism the story relies on.

### Dev (implementation)
- **Portrait-initial contamination fixed UI-side (decorative aria-hidden + sr-only name), not by sanitizing the detector label**
  - Spec source: context-story-162-11.md, AC3 + TEA Assessment "Root-cause evidence" item 2
  - Spec text: "GREEN should either strip the chip initial from the perceived label or expose the clean name as the listitem's accessible name (UI side)."
  - Implementation: Chose the UI-side path — the ActorChip portrait is marked `aria-hidden` (it is genuinely decorative) and an `sr-only` clean name is the listitem's accessible text, so the real UI's aria_snapshot yields `listitem: Thief`. The detector's `_enemy_labels`/`_LISTITEM` was left unchanged (no label sanitization).
  - Rationale: Fixing at the aria source is the correct accessibility model (decorative glyph should not be in the a11y tree) and avoids fragile label-stripping heuristics (e.g. a real name like "T'Challa"). TEA's real-DOM fixture still emits the contaminated `T Thief`, which the detector tolerates — so the wiring test also proves robustness to the un-hidden form.
  - Severity: minor
  - Forward impact: TEA's `fixture_identity_fork_realdom.html` intentionally left as the pre-fix (`T Thief`) shape; the real fixed UI emits the clean `listitem: Thief`. A future fixture refresh could mirror the clean form, but the current fixture is a stronger (robustness) test as-is.
- **(Rework R1) No new deviations.** Applied TEA's three specified GREEN changes verbatim (`_LOG` `(\S.*)`, `_node_text` bare-node `""`, `role="list"` wrapper). The R1-flagged fixture-fidelity rationale above is superseded: the fixture now carries the shipped `aria-hidden` and the aria-hidden guard is mutation-verified, so the "leave it as T Thief for robustness" claim no longer applies.

### Reviewer (audit)
- **TEA — AC4 rendered as a real-DOM Playwright fixture, not a full server+UI e2e** → ✓ ACCEPTED by Reviewer: sound and correctly scoped. The file:// fixture exercises the real `perceive() → aria_snapshot → detector` path, which is where the inert-in-production bug lives; a live server+UI e2e is disproportionate for the per-commit gate. The forward-impact note (confirm once in a live session before finish) stands as a reasonable non-blocking follow-up.
- **Dev — Portrait-initial contamination fixed UI-side (aria-hidden + sr-only), not detector label-strip** → ✗ FLAGGED by Reviewer: the *implementation choice* (fix at the aria source) is correct and I endorse it. What I flag is the deviation's **rationale/forward-impact** claim that leaving the fixture emitting `T Thief` makes it "a stronger (robustness) test." Empirically it does the opposite: because the fixture omits the `aria-hidden` the shipped `ActorChip` now sets, the wiring test passes for the WRONG reason (the fork logic tolerates the extra "T"), and NO test — UI or understudy — verifies the shipped clean `listitem: Thief`. Removing `aria-hidden` keeps the whole suite green. The fixture has silently diverged from what ships on day one (repo CLAUDE.md: "Verify Wiring, Not Just Existence"). Added as blocking review findings (see Reviewer Assessment); the fixture must gain `aria-hidden` and a contamination-catching case.
- **UNDOCUMENTED (Reviewer):** `_LOG` regex accepts a whitespace-only capture, so a trailing-space `log:` opener silently drops narration (Conflict finding above). Neither TEA nor Dev logged this; it is a regression of the very invariant ("No Silent Fallbacks" / detector-not-inert) the story enforces. Severity: High.

**Re-Review (round-trip 1) deviation audit:**
- **TEA (Rework R1) — clean-name guard asserts the portrait's `aria-hidden` attribute + sr-only name, not the listitem's computed accessible name** → ✓ ACCEPTED by Reviewer: correct — `listitem` is not a name-from-content role, so `getByRole('listitem',{name})` resolves empty even on correct markup; the attribute+text assertion is the faithful guard. Independently **mutation-verified** by reviewer-test-analyzer (deleting `aria-hidden` turns exactly this test red).
- **Dev (Rework R1) — no new deviations; applied TEA's 3 changes verbatim** → ✓ ACCEPTED by Reviewer: confirmed — `_LOG` `(\S.*)`, `_node_text` bare-node `""`, `role="list"` wrapper all present and correct. The prior FLAG on the R1 fixture-robustness rationale is now **resolved** (the fixture carries the shipped `aria-hidden`; the guard is mutation-verified).

## Subagent Results (Re-Review — round-trip 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (understudy 282, UI 2561, ruff/eslint/tsc clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (my own pass + rule-checker: `_LOG` silent-fallback now RESOLVED, empirically confirmed) |
| 4 | reviewer-test-analyzer | Yes | findings | mutation-verified all 5 guards genuine; 3 low-conf edge notes | confirmed test net sound; 3 non-blocking (1 unreachable) |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 (stale headers ×3, fixture fidelity claim ×2) | confirmed 5 Low/Med, all non-blocking |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (rule-checker covered: non-null-assertion flagged) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (no trust boundary) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (my pass: `const foes` hoist is minimal, no dead code) |
| 9 | reviewer-rule-checker | Yes | findings | 3 prior RESOLVED (1 recurrence: list-fidelity); 2 new (non-null-assert, fixture list-wrapper) | confirmed 3 non-blocking Low/Med |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 blocking; 3 confirmed non-blocking (fixture list-fidelity Med; non-null-assert Low; stale headers Low)

## Reviewer Assessment (Re-Review — round-trip 1)

**Verdict:** APPROVED

The rework resolved every blocking R1 finding, and reviewer-test-analyzer **independently mutation-verified all five guards** (revert each fix → the exact target test goes red → restore → green). I re-confirmed the three fixes first-hand: `_LOG.search("- log: ")` now returns `None` (silent-fallback closed), `_enemy_labels` correctly extracts `['Thief']` through the real `region → list → listitem` nesting, and the detector does not false-fork on consistent naming. Correctness is airtight.

| Severity | Issue | Location | Disposition |
|----------|-------|----------|-------------|
| [MEDIUM] `[RULE]`/`[DOC]` | The two understudy fixtures omit the `role="list"` wrapper the shipped `ConfrontationOverlay.tsx:595` now renders, so their "faithful reproduction as it ships" comment overstates fidelity — a recurrence of the R1 fidelity class. **Non-blocking** because, unlike R1, the detector is verified-tolerant of the interposed `- list:` line (`_enemy_labels` indent-scan skips it) — no test passes for the wrong reason and no property is left untested; the markup tests a valid shape. | `tests/wiring/fixture_identity_fork_realdom.html`, `fixture_identity_consistent_realdom.html` | Recommend (fast-follow): add a `role="list"` wrapper to both fixtures so the "faithful" claim is true, or soften the claim. |
| [LOW] `[TYPE]`/`[RULE]` | Non-null assertion `.find((li) => …)!` on an `Array.find()` result (typed `T \| undefined`) — matches typescript.md #1. Test-only; the fixture DATA guarantees a match, so worst case is an opaque `TypeError` instead of a clean assertion failure if the fixture changes. | `ConfrontationOverlay.aria-enemies-162-11.test.tsx:79` | Recommend: guard the result (`const item = …; expect(item).toBeDefined();`). |
| [LOW] `[DOC]` | The two UI test-file header banners still read "Story 162-11 (RED)" (the Python file was reworded; these were missed) — stale now that the fix ships in the same diff. Matches repo TDD-header convention. | `ConfrontationOverlay.aria-enemies-162-11.test.tsx:7`, `NarrationScroll.aria-log-162-11.test.tsx:11` (+ inline "RED until" at aria-list test) | Recommend: reword to past-tense/contract framing. |

### Rule Compliance
Re-enumerated the r2 diff against `python.md`/`typescript.md`, SOUL, and the naivety invariant (rule-checker's 29-rule pass corroborated):
- **SOUL "No Silent Fallbacks":** the R1 `_LOG` violation is RESOLVED — `(\S.*)` requires content so the bare-opener regex wins; empirically `_LOG.search("- log: ") → None`. COMPLIANT.
- **WCAG 1.3.1 aria-required-parent:** `role="listitem"` now has a `role="list"` parent (`ConfrontationOverlay.tsx:595`). COMPLIANT in production.
- **Naivety invariant:** all changed code reads only `aria_snapshot()` text; no creature_id/alias/OTEL. COMPLIANT.
- **python.md #2/#3/#6 (defaults/annotations/test-quality):** `_node_text`/`_narration` fully annotated, no mutable defaults; new pytest assertions are specific. COMPLIANT.
- **typescript.md #1 (type-safety-escapes):** ONE violation — the test-file non-null assertion (LOW, above). **typescript.md #4 (`??`/`||`):** `aria-hidden={decorative || undefined}` is correct (boolean → omit-when-false); `li.textContent ?? ''` correct. COMPLIANT. **#6 (React keys / vacuous every):** `key={a.name}` stable; `group.length > 0 && group.every(...)` guards the empty-array `.every()===true` gotcha. COMPLIANT.
- **Verify Wiring:** the wiring tests drive the REAL `run_table` loop over real Playwright — genuine wiring. The fixture list-wrapper gap (MEDIUM above) is a fidelity-claim inaccuracy, not a wiring break.

### Devil's Advocate
Assume it's still broken. The scariest residue is the fixture that lies: it says "faithful reproduction as it ships" but omits a role the component now renders — the exact trap I died on in R1, recurring one round later. If I wave that through, am I training the pipeline that fidelity claims are decorative? I checked the teeth: `_enemy_labels` walks by indent and only collects `_LISTITEM` matches, so an interposed `- list:` line is skipped, not mis-parsed — I ran `region→list→listitem` through the real function and got `['Thief']`, and the consistent case returned `None`. So the drift is genuinely inert *today*; the detector is forward-compatible with both shapes. The non-null `!` could bite a future editor who changes the fixture cast, but it's a test — it fails loudly (a TypeError in a test IS a failure), just less legibly. The stale "(RED)" headers mislead a reader into thinking the tests are pending, but the suite is green and the sibling Python file already models the correct wording. None of these can reach a player or corrupt state; none leave a story property unverified (test-analyzer's mutation sweep is my evidence, not my hope). The one thing I will NOT do is pretend the fixture gap is zero — it's a real, if minor, honesty debt, recorded as a Medium fast-follow so it isn't silently inherited. The correctness case, though, is closed: three independent passes (mine, test-analyzer's mutations, rule-checker's empirical regex+Playwright runs) agree the blocking bugs are dead.

**Subagent lens coverage (dispatch tags):** `[SILENT]` — `_LOG` fallback RESOLVED (rule-checker + my repro). `[TEST]` — test-analyzer mutation-verified all guards genuine; net sound. `[DOC]` — comment-analyzer: stale headers + fixture fidelity-claim (Low/Med). `[RULE]` — rule-checker: 3 prior RESOLVED, 2 new non-blocking (non-null-assert, fixture list-wrapper). `[TYPE]` — non-null assertion (Low). `[SEC]` — N/A, local harness input, no trust boundary. `[SIMPLE]` — `const foes` hoist + ternary wrapper is minimal, no dead code. `[EDGE]` — trailing-space opener now handled; zero-opponent group + 3-faction multi-region are low/unreachable (single opponent group only).

**Data flow traced (unchanged, now hardened):** opponent `EncounterActor.name` → `humanizeActorName` → sr-only span in `role="listitem"` in `role="list"` in `role="region" "Enemies"` → `aria_snapshot()` → `perceive()` → `two_names_one_enemy` (`_enemy_labels` + `_narration`, both now robust to nesting + whitespace) → `SignalKind.TWO_NAMES_ONE_ENEMY`. End-to-end wired and verified.

**Handoff:** To SM (Camina Drummer) for finish-story. Non-blocking fast-follows recorded in Delivery Findings.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (2825 tests pass, ruff/eslint/tsc clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (covered by rule-checker + my own pass — found the `_LOG` silent-fallback) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 3 (1 High, 2 Medium), noted 3 Low |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 as Low (non-blocking, matches repo TDD-header convention) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (my own pass: `decorative?: boolean`, `??`/`||` usage all compliant) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (no trust boundary; snapshot is local harness input) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (my own pass: no dead code; helpers are minimal) |
| 9 | reviewer-rule-checker | Yes | findings | 4 violations (2 py meta + 2 SOUL) | confirmed 2 blocking (silent-fallback, fixture-fidelity), 1 Low (listitem-parent), 1 Low latent (quoted-log) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 3 confirmed blocking, 6 confirmed non-blocking (Low), several corroborated across subagents

## Reviewer Assessment

**Verdict:** REJECTED

Two independent subagents (test-analyzer, rule-checker) plus my own first-hand reproduction converge on the same conclusion: the production code *works today*, but (a) it carries a latent silent-fallback in exactly the code the story adds, and (b) the story's central correctness property — a clean perceived foe name — is guarded by **no** test in either repo. The implementation direction is right; the work is not done.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[SILENT]`/`[RULE]` | `_LOG`'s `(.+)` matches a whitespace-only remainder, so a `log:` opener with a trailing space is routed to the inline branch, drops the nested prose, and `two_names_one_enemy` returns `None` on a valid fork. Reproduced first-hand (`detector (TRAILING space): None`). Matches SOUL "No Silent Fallbacks". Latent under today's DOM but fragile. | `sidequest-understudy/src/understudy/findings/detect.py` (`_LOG`, line ~19) | Tighten to `r"\blog\s*:\s*(\S.*)$"` so `_LOG_OPEN` reliably wins the bare-opener; add a unit test that drives a trailing-space opener and asserts the fork still fires. |
| [HIGH] `[RULE]`/`[TEST]` | Fixture divergence + weak assertion: the wiring fixture omits the `aria-hidden` the shipped `ActorChip` sets, so it emits `listitem: T Thief` and the test passes for the *wrong reason*; the UI test asserts `li.textContent` (includes the hidden "T"). Removing `aria-hidden={decorative}` keeps the ENTIRE suite green (mutation-verified). Nothing proves the shipped UI yields the clean `listitem: Thief` — the story's core property. ("Verify Wiring, Not Just Existence".) | `sidequest-understudy/tests/wiring/fixture_identity_fork_realdom.html` + `sidequest-ui/.../ConfrontationOverlay.aria-enemies-162-11.test.tsx` | Add `aria-hidden="true"` to the fixture portrait to match production; add a CONSISTENT-naming wiring case that FAILS on contamination; in the UI test assert the listitem's portrait is `aria-hidden` and the perceived name has no initial. NOTE: do **not** use `getByRole('listitem',{name})` — `listitem` has no name-from-content, so that query resolves empty even when correct. |
| [MEDIUM] `[TEST]` | The new `_narration`/`_node_text` helpers (the fix's core) have zero direct unit tests; only one wiring-DOM shape exercises them. Untested: literal "log:" in prose, `text "quoted"` node, empty/whitespace paragraph, two sequential log regions, the trailing-space opener from finding #1. | `sidequest-understudy/tests/test_two_names_one_enemy.py` | Add pure-function cases mirroring the existing FORKED/CONSISTENT/NO_COMBAT style. |
| [MEDIUM] `[TEST]` | `NarrationScroll` tested only with `messages={[]}` — no test proves narrated text is a descendant of the `role="log"` node (a refactor moving segments to a sibling would pass). | `sidequest-ui/.../NarrationScroll.aria-log-162-11.test.tsx` | Render with a populated `messages` array; assert `within(getByRole('log')).getByText(...)`. |
| [LOW] `[RULE]` | `role="listitem"` has no `role="list"`/`role="group"` ancestor (WCAG 1.3.1 aria-required-parent). Works in aria_snapshot; real screen-reader debt. | `sidequest-ui/.../ConfrontationOverlay.tsx` (StatusLine) | Wrap the foe listitems in a `role="list"` inside the "Enemies" region. |
| [LOW] `[DOC]` | Committed test headers say "Story 162-11 (RED)" / "RED today: ..." though the same diff makes them GREEN. Matches repo TDD-header convention (162-7 file does the same), so non-blocking. | 4 new test files | Optional: reword to past tense or describe the pinned contract. |
| [LOW] | `_LOG` recognizes only the colon form, never a quoted `log "text"` label form (`_LISTITEM` supports both). Latent — today's DOM emits bare `log:`. | `detect.py` (`_LOG`) | Note only; add the alt if Playwright ever labels the log node. |

### Rule Compliance
Enumerated every changed symbol against `.pennyfarthing/gates/lang-review/{python,typescript}.md`, SOUL.md, and the understudy naivety invariant.
- **Python — annotations (rule 3):** `_node_text(line: str) -> str`, `_narration(lines: list[str]) -> str`, `two_names_one_enemy(...) -> str | None` — all fully annotated. COMPLIANT.
- **Python — mutable defaults (rule 2):** no mutable defaults on the 3 functions. COMPLIANT.
- **Python — test quality (rule 6):** the wiring test asserts specific values (`code == 0`, `len(run_dirs) == 1`, non-empty `two_names`, grade ∈ set) — non-vacuous. COMPLIANT. But coverage of the new helpers is thin (see [MEDIUM] findings).
- **Python — No Silent Fallbacks (SOUL, `<critical>`):** VIOLATION — `_LOG` whitespace capture (see [HIGH] #1). This is a rule-matching finding and cannot be dismissed.
- **Naivety invariant (understudy CLAUDE.md, `<critical>`):** COMPLIANT — `_node_text`/`_narration` read only the passed `snapshot` text; the sr-only span surfaces `humanizeActorName(a.name)`, the same player-visible name `ThemPanel` already shows — no creature_id/alias/OTEL smuggled in. Verified.
- **TS — null/undefined (rule 4):** `aria-hidden={decorative || undefined}` is correct (`decorative` is a strict boolean; `??` would render `aria-hidden={false}`); matches the existing `disabled || undefined` idiom in the same file. `li.textContent ?? ''` correctly uses `??` (nullable string). COMPLIANT.
- **TS — React keys (rule 6):** `key={a.name}` per actor is stable-identity (good). `key={`roster-group-${gi}`}` is index-derived but pre-existing and bounded to ≤2 never-reordered groups — not a new violation.
- **TS — a11y:** listitem-without-list is a WCAG 1.3.1 gap ([LOW]); repo has no `eslint-plugin-jsx-a11y` so lint won't catch it.

### Devil's Advocate
Assume this is broken. The whole story is "the detector was silently inert; make it fire." The fix adds `_narration`, whose job is to survive whatever shape Playwright's `aria_snapshot()` emits for a `role="log"`. But I *reproduced* a shape — a `log:` opener with one trailing space — where `_narration` returns `""` and the detector returns `None`: the identical failure the story was filed to eliminate, re-created inside the fix. Today's Chromium happens not to emit that space, so we are one browser/Playwright upgrade, one `white-space` CSS change, or one differently-rendered node away from the detector going silently dark again — and no test would notice, because the only test of the nested path is a single hand-authored fixture. A confused future maintainer "cleans up" `ActorChip` by dropping the `aria-hidden` (it looks redundant next to an sr-only span) and every test stays green while real screen-reader users — and the understudy bot — start reading the foe as "T Thief," re-arming the false-fork bug in the consistent-naming case. The fixture that is supposed to be "a FAITHFUL reproduction of the real DOM" already isn't: it lacks the `aria-hidden` the component ships, so the green wiring test is a comfort blanket, not proof. A stressed input — an empty `<p>` node — makes `_node_text` emit the literal token "paragraph:" into the narration string; harmless today (lowercase, no proper-noun match) but it shows the helper trusts its input shape. And the `listitem`s float with no `list` parent, so a real screen reader may not announce "list, 1 item" at all — the accessibility win is partial. None of these are hypothetical: three of them I ran. The implementation is on the right track, but "the tests pass" is currently doing a lot of unearned work.

**Subagent lens coverage (dispatch tags):** `[SILENT]` (disabled subagent) — covered by rule-checker + my repro: the `_LOG` fallback is the headline. `[TEST]` — test-analyzer + my analysis: guard untested, helpers uncovered, NarrationScroll empty-only. `[DOC]` — comment-analyzer: substantive comments accurate; only the "RED today" framing is stale (Low). `[RULE]` — rule-checker: No-Silent-Fallbacks violation + fixture divergence + listitem-parent. `[TYPE]` (disabled) — my pass: prop/null-handling all compliant. `[SEC]` (disabled) — my pass: no trust boundary, local harness input only, N/A. `[SIMPLE]` (disabled) — my pass: helpers are minimal, no dead code, no over-engineering. `[EDGE]` (disabled) — my pass + test-analyzer: boundary gaps are the trailing-space opener and empty-paragraph node, both captured above.

**Data flow traced:** UI `EncounterActor.name` (opponent) → `humanizeActorName` → sr-only span inside `role="listitem"` inside `role="region" "Enemies"` → Playwright `aria_snapshot()` → understudy `perceive()` → `two_names_one_enemy` `_enemy_labels`/`_narration` → `SignalKind.TWO_NAMES_ONE_ENEMY`. The flow is wired end-to-end; the break points are the two [HIGH] findings on the perception→detector seam.

**Handoff:** Back to TEA (Amos Burton) for RED rework — write the failing tests (trailing-space None reproduction; clean-name guard; `_narration`/`_node_text` unit cases), then Dev tightens `_LOG` and hardens the fixture/UI assertions to GREEN.
## TEA Assessment (Rework — round-trip 1)

**Tests Required:** Yes — pinned every blocking review finding as a failing test before Dev touches source.

**RED (fail on current code — Dev must make these GREEN):**
- `tests/test_two_names_one_enemy.py::TestNarration::test_trailing_space_opener_still_reads_nested_prose` — a `log:` opener with a trailing space must still read the nested prose (currently `''`). [Review HIGH #1]
- `tests/test_two_names_one_enemy.py::TestDetectorNestedRealDom::test_flags_fork_with_trailing_space_log_opener` — the end-to-end detector must fire on that shape (currently `None`). [Review HIGH #1]
- `tests/test_two_names_one_enemy.py::TestNodeText::test_bare_role_node_has_no_text` — a bare `- paragraph:`/`- list:` node must yield `""`, not leak the role token. [Review MEDIUM]
- `tests/test_two_names_one_enemy.py::TestNarration::test_empty_paragraph_node_leaks_no_role_token` — narration must not contain `"paragraph:"` noise. [Review MEDIUM]
- `sidequest-ui/.../ConfrontationOverlay.aria-enemies-162-11.test.tsx > wraps the foe listitems in a list` — foe listitems need a `role="list"` ancestor (WCAG 1.3.1). [Review LOW, pinned]

**GREEN-on-arrival guards (green now; fail if the fix/fidelity regresses — honest classification per the mixed-bundle rule):**
- `ConfrontationOverlay...> hides the decorative portrait ...` — asserts the foe listitem's portrait is `aria-hidden`; **fails if `decorative`/`aria-hidden` is removed** — the exact regression review proved was previously invisible. [Review HIGH #2a]
- `fixture_identity_fork_realdom.html` — now carries the shipped `aria-hidden` so aria_snapshot emits the CLEAN `listitem: Thief` (verified); the fork wiring test now exercises the real clean label, not `T Thief`. [Review HIGH #2b]
- `tests/wiring/test_identity_fork_realdom_162_11.py::test_consistent_naming_does_not_false_fork` (new `fixture_identity_consistent_realdom.html`) — consistent naming must NOT fork; **false-forks (fails) if the fixture drifts back to a non-aria-hidden portrait.** [Review HIGH #2b]
- `_narration`/`_node_text` coverage: inline, nested, literal-`log:`-in-prose, quoted node, two sequential logs. [Review MEDIUM #3]
- `ConfrontationOverlay...> gives each foe its own listitem` (2+ foes). [Review LOW]
- `NarrationScroll...> renders narrated text inside the log region` — narrated text must be a DESCENDANT of the `role="log"` node (all prior tests rendered empty). [Review MEDIUM #4]

**What Dev must change for GREEN:**
1. `detect.py` `_LOG` → require a non-whitespace char after the colon, e.g. `re.compile(r"\blog\s*:\s*(\S.*)$")`, so a bare/whitespace-only opener falls through to `_LOG_OPEN`.
2. `detect.py` `_node_text` → return `""` for a role node with no inline text (a bare `- role:`), so no role token leaks into the narration string.
3. `ConfrontationOverlay.tsx` → wrap the foe `role="listitem"`s in a `role="list"` inside the Enemies region (the detector's region-scan tolerates the intermediate `- list:` line).

**RED verification:** understudy full suite → **4 failed (intended) / 278 passed**; ruff clean. UI targeted → **1 failed (list-parent, intended) / 9 passed**; eslint clean. Both wiring tests GREEN over the aria-hidden fixtures (fork fires on clean `listitem: Thief`; consistent does not fork).

**Comment cleanup:** reworded the stale `(RED)` / "RED today" headers in the 4 new 162-11 files to describe the pinned contract (comment-analyzer LOW).

**Branches:** `feat/162-11-...` (understudy `fecd9fd`, ui `dde6d97`).

**Handoff:** To Dev (Naomi Nagata) for GREEN — apply the 3 changes above so all 5 RED tests pass, keeping the guards green.
## Dev Assessment (Rework — round-trip 1)

**Implementation Complete:** Yes — applied TEA's 3 specified changes; all previously-RED tests now GREEN.

**Files Changed:**
- `sidequest-understudy/src/understudy/findings/detect.py` — (1) `_LOG` now requires a non-whitespace char after the colon (`r"\blog\s*:\s*(\S.*)$"`), so a bare/whitespace `log:` opener falls through to `_LOG_OPEN` and its nested prose is read instead of matching inline with an empty capture (closes the silent-fallback that returned `None` on a valid fork). (2) `_node_text` returns `""` for a bare `- role:` node, so the role token never leaks into the narration string.
- `sidequest-ui/src/components/ConfrontationOverlay.tsx` — the foe `role="listitem"`s are now wrapped in a `role="list"` (WCAG 1.3.1 aria-required-parent). Hoisted the foe items into a `const foes`; the enemy group renders them inside a `role="list"` span using the SAME flex container (layout byte-identical); allied groups unchanged.

**Review findings addressed:**
| Finding | Fix | Verified |
|---------|-----|----------|
| [HIGH] `_LOG` whitespace silent-fallback | `(\S.*)` capture | `test_trailing_space_opener...` + `test_flags_fork_with_trailing_space_log_opener` GREEN |
| [HIGH] clean-name guard untested / fixture divergence | fixture carries shipped `aria-hidden` (TEA); aria-hidden guard test | **mutation-verified**: deleting `aria-hidden` fails `hides the decorative portrait...` (1 failed); restored → 6/6 GREEN |
| [MED] `_node_text` / `_narration` no unit coverage | `_node_text` bare-node returns `""`; 15 helper unit tests | all GREEN |
| [MED] NarrationScroll empty-only | populated-content test asserts text within `role="log"` | GREEN |
| [LOW] `listitem` without `list` parent | `role="list"` wrapper | `wraps the foe listitems in a list` GREEN |

**Tests:** all rework tests GREEN.
- Understudy: **full suite 282/282** (up from 278; the 4 silent-fallback tests + guards now pass). Ruff clean.
- UI: **full suite 2561/2561** (up from 2557). ESLint clean, `tsc --noEmit` clean.
- The aria-hidden guard was **mutation-tested** (removed the attribute → the guard test failed → restored → green), directly answering the review's "removing aria-hidden keeps the suite green" concern.

**Branches:** `feat/162-11-...` (understudy `750805f`, ui `68bdf9b`).

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review.