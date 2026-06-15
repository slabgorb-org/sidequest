---
story_id: "117-7"
jira_key: ""
epic: "quest-seed-lifecycle"
workflow: "tdd"
---
# Story 117-7: Render quest-related lore in QuestsPanel

## Story Details
- **ID:** 117-7
- **Jira Key:** (no Jira — kanban tracking only)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T05:55:42Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T05:33:14.571709Z | 2026-06-15T05:35:07Z | 1m 52s |
| red | 2026-06-15T05:35:07Z | 2026-06-15T05:44:36Z | 9m 29s |
| green | 2026-06-15T05:44:36Z | 2026-06-15T05:49:33Z | 4m 57s |
| review | 2026-06-15T05:49:33Z | 2026-06-15T05:55:42Z | 6m 9s |
| finish | 2026-06-15T05:55:42Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Improvement** (non-blocking): The mirror boundary guard validates `quest_log` is an array but does not validate each entry's `related_lore`. Affects `sidequest-ui/src/hooks/useStateMirror.ts` (the `MessageType.QUESTS` guard, ~line 227) — a version-skew entry lacking `related_lore` passes the guard and reaches the panel, so the panel must defensively treat a missing list as empty (covered by a render test). Not in scope to harden the mirror guard here; flagged for a future hardening pass if old-save skew becomes real.
- **Improvement** (non-blocking): `related_lore[].fact_id` is the server's stated dedup key against the broader KnownFacts surface (per models.py QuestLoreEntry docstring). Affects `sidequest-ui/src/components/QuestsPanel.tsx` — a future story could dedup a lore fragment already shown in the KnowledgeJournal. Out of scope for 117-7 (render-only).

### Dev (implementation)
- **Gap** (non-blocking): A pre-existing ESLint hard error blocks `npm run lint` on the whole repo (and on `develop` — verified by checking out develop and re-linting). Affects `sidequest-ui/src/components/Dashboard/source/useForensicSource.ts:61-64` (`react-hooks/set-state-in-effect` — synchronous setState calls inside an effect). NOT introduced by 117-7 (which touches only payloads.ts + QuestsPanel.tsx); flagged so Reviewer's lint gate treats it as pre-existing. My own changed files lint clean (eslint exit 0).

### Reviewer (code review)
- **Improvement** (non-blocking): The `quests-lore` testid is emitted once per quest without a per-quest suffix, and no test renders two lore-bearing quests. Affects `sidequest-ui/src/components/QuestsPanel.tsx` (consider `data-testid={`quests-lore-${q.quest_id}`}`) and `src/components/__tests__/QuestsPanel.test.tsx` (add a two-lore-quests scoping case using `getAllByTestId`/`within`). Fast-follow; runtime is correct and consistent with the existing `quests-entry` repeated-testid pattern. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The lore header `"What I've learned about this job"` is genre-incoherent for non-job quests (dungeon crawl, space missions). Affects `sidequest-ui/src/components/QuestsPanel.tsx` — a future story could source the label from the genre theme. The current label is spec-mandated by the 117-7 story title, so this is deferred, not a defect. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Empty/whitespace `content` and empty/duplicate `fact_id` are not guarded client-side (blank line under header; React duplicate-key warning). Affects `sidequest-ui/src/components/QuestsPanel.tsx` — server contract (content = readable fragment; fact_id = unique clue id per 50-14, deduped) makes these unreachable in practice; harden only if a real payload exhibits them. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

2 deviations

- **Typed `related_lore` as REQUIRED, not optional, on `QuestLogEntry`**
  - Rationale: Honest to the server contract and consistent with the other required `QuestLogEntry` fields (quest_id/title/objective/status). An optional field would imply "may be absent" when the wire always carries it.
  - Severity: minor
  - Forward impact: Dev must add the field as required (not `?:`). One defensive runtime test (`?? []`) still tolerates a version-skew payload that omits it, so requiredness does not force a white-screen on old saves.
- **Added a per-fact-key rendering test (duplicate-content fragments) beyond the literal AC**
  - Rationale: Enforces a stable `key={fact_id}` and guards the lang-review React-key anti-pattern; `fact_id` is the server's stated dedup key.
  - Severity: minor
  - Forward impact: Dev should key the lore list on `fact_id`.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Typed `related_lore` as REQUIRED, not optional, on `QuestLogEntry`**
  - Spec source: context-story-117-7.md (title) — "QuestLogEntry has no related_lore field"
  - Spec text: "(1) sidequest-ui src/types/payloads.ts QuestLogEntry has no related_lore field, so the typed data is invisible"
  - Implementation: Tests require `related_lore: QuestLoreEntry[]` (required), mirroring the server model `related_lore: list[QuestLoreEntry] = Field(default_factory=list)` (always emitted, never None, `extra: forbid`). Existing sibling fixtures (QuestsPanel.test.tsx, GameBoard-quests-tab.test.tsx, useStateMirror.quests.test.ts) were updated to add `related_lore: []`.
  - Rationale: Honest to the server contract and consistent with the other required `QuestLogEntry` fields (quest_id/title/objective/status). An optional field would imply "may be absent" when the wire always carries it.
  - Severity: minor
  - Forward impact: Dev must add the field as required (not `?:`). One defensive runtime test (`?? []`) still tolerates a version-skew payload that omits it, so requiredness does not force a white-screen on old saves.
- **Added a per-fact-key rendering test (duplicate-content fragments) beyond the literal AC**
  - Spec source: lang-review/typescript.md, check #6 (React/JSX)
  - Spec text: "key={index} on lists where items can be reordered/inserted/deleted"
  - Implementation: A test renders two distinct facts (different `fact_id`) with identical `content` and asserts both render — fails under `key={index}`-collapse or `key={content}`.
  - Rationale: Enforces a stable `key={fact_id}` and guards the lang-review React-key anti-pattern; `fact_id` is the server's stated dedup key.
  - Severity: minor
  - Forward impact: Dev should key the lore list on `fact_id`.

### Dev (implementation)
- No deviations from spec. Implemented exactly the contract Argus's tests demanded: `QuestLoreEntry {fact_id, content}` + required `related_lore: QuestLoreEntry[]` on `QuestLogEntry`, and a `quests-lore` block per quest rendering each fragment's `content` under the "What I've learned about this job" label, keyed on `fact_id`, defensive `?? []`, suppressed when empty. Two test-fixture typecheck fixes (a stale 77-5 `QuestLogEntry` literal missing `related_lore`, and `questsData ?? null` in the wiring test) completed the required-field migration TEA began — these change no assertion intent.

### Reviewer (audit)
- **TEA — `related_lore` typed REQUIRED not optional** → ✓ ACCEPTED by Reviewer: honest to the server model (`Field(default_factory=list)`, never None) and consistent with QuestLogEntry's other required fields. Dev's `?? []` runtime guard covers the version-skew gap, so requiredness costs no robustness.
- **TEA — per-fact-key duplicate-content test (lang-review #6)** → ✓ ACCEPTED by Reviewer: correctly enforces `key={fact_id}` over `key={index}`; verified the implementation keys on `fact_id` (QuestsPanel.tsx:132).
- **Dev — "No deviations from spec" + two test-fixture compile fixes** → ✓ ACCEPTED by Reviewer: the stale-fixture `related_lore: []` and `questsData ?? null` are mechanical type-conformance edits that change no assertion intent; verified in the diff.
- **No undocumented deviations found.** The implementation matches the AC set exactly (label text, content-only render, fact_id key, empty-suppression, defensive guard).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — typecheck/tests/lint all green |
| 2 | reviewer-edge-hunter | Yes | findings | 9 | confirmed 5 (all non-blocking), dismissed 2 (contract-unreachable), deferred 2 (spec-mandated label + cast-bypass cosmetic) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([SILENT] below) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([TEST] below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([DOC] below) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([TYPE] below) |
| 7 | reviewer-security | Yes | clean | 0 | N/A — XSS impossible (escaped text node), fact_id not DOM-exposed, no leakage |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([SIMPLE] below) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([RULE] below) |

**All received:** Yes (3 enabled returned; 6 disabled via settings, domains self-assessed)
**Total findings:** 0 confirmed-blocking, 5 confirmed non-blocking, 2 dismissed (with rationale), 2 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A clean, surgical, render-only change that surfaces the `related_lore` the server has projected since 117-5. The production diff is two files: a typed protocol field and a per-quest render block. Tests are strong (11 new, meaningful assertions, an end-to-end wiring test), the full suite is green (2207/2207), typecheck clean, and the changed production files lint clean. No Critical or High production defect exists.

**Data flow traced:** server `QuestLoreEntry {fact_id, content}` → WebSocket `QUESTS` message → `useStateMirror` full-replace (`questsData = p`, threads the field opaquely — confirmed by the wiring test's "mirror preserves related_lore" assertion) → `QuestsWidget` → `QuestsPanel` renders `{lore.content}` as an escaped React text node. Safe end-to-end: no raw HTML sink, no LLM relay, no cross-session path introduced.

**Observations:**
- [VERIFIED] Lore block lives inside the `quest_log.map` entry, so a lore-bearing quest always has a `quest_log` entry → `isEmptySpine` (requires `quest_log.length === 0`) can never swallow it — evidence: QuestsPanel.tsx:30-36 vs the block at :119-135.
- [VERIFIED] `{lore.content}` is an escaped React text child; no `dangerouslySetInnerHTML` anywhere in the diff (grep 0) — XSS not reachable. Evidence: QuestsPanel.tsx:133 + reviewer-security confirmation.
- [VERIFIED] `fact_id` is used only as `key={lore.fact_id}` (QuestsPanel.tsx:132), never rendered to the DOM; the "content not fact_id" test asserts `queryByText("clue_ledger")` is absent.
- [EDGE][MEDIUM] Duplicate `data-testid="quests-lore"` across multiple lore-bearing quests would break `screen.getByTestId` (singular) in the positive-render and wiring tests. **Non-blocking:** runtime renders both correctly, it mirrors the component's existing repeated-testid pattern (`quests-entry`/`quests-orphan-anchor`, which tests read via `getAllByTestId`), and no current fixture has two lore-bearing quests. Coupled coverage gap: the "scopes each quest's lore" test only separates lore-vs-no-lore (escort has empty lore), not lore-vs-lore. Recorded as a fast-follow.
- [EDGE][MEDIUM] Empty/whitespace `content` passes the `.length > 0` guard and renders a blank line under the header — cosmetic; server contract makes empty content unlikely. Non-blocking.
- [EDGE][MEDIUM] Empty-string or duplicate `fact_id` within one quest's lore would trigger a React duplicate-key warning. **Non-blocking:** `fact_id == originating clue id` (50-14) is server-unique and non-empty; the server dedups the projection (QuestLoreEntry docstring).
- [EDGE][dismissed] `isEmptySpine` doesn't inspect `related_lore` — contract-unreachable (lore always rides a `quest_log` entry; the edge-hunter concurs). Documentation-only.
- [EDGE][dismissed] Orphan-anchor branch has no lore slot — contract-unreachable (lore attaches to `QuestLogEntry`, not `QuestAnchorEntry`; edge-hunter concurs).
- [EDGE][deferred] `"What I've learned about this job"` is genre-incoherent for non-job quests (dungeon/space). **Deferred — spec-mandated:** the label is the story title's exact words; a genre-neutral label sourced from the theme is a valid future improvement, recorded as a Delivery Finding.
- [EDGE][deferred] Null `content`/`fact_id` via a buggy server bypasses TS types through the `as unknown` cast — `{null}` renders nothing (no crash); cosmetic only.
- [SEC] reviewer-security: clean — XSS impossible, `fact_id` not DOM-exposed, no cross-player leakage, ADR-047 surface unchanged.
- [SILENT] Self-assessed (disabled): the `(q.related_lore ?? [])` guard is documented graceful degradation that *suppresses* the block (renders nothing) rather than fabricating data — complies with No-Silent-Fallbacks. No swallowed errors.
- [TEST] Self-assessed (disabled): 11 tests, all with meaningful assertions; no vacuous `assert(true)`/`let _ =`. Casts (`as unknown as QuestsPayload`) are the established malformed-payload idiom from `useStateMirror.quests.test.ts`. Gap: no two-lore-quests render case (see EDGE-MEDIUM above). Non-blocking.
- [DOC] Self-assessed (disabled): comments accurately cite 117-5 + the server model. Minor nit — the QuestLoreEntry block comment was appended to the existing QuestLogEntry spine comment, so the "rich shape (log+anchors+stakes)" line now precedes QuestLoreEntry rather than QuestLogEntry (payloads.ts:925-933). Cosmetic, LOW, non-blocking.
- [TYPE] Self-assessed (disabled): `QuestLoreEntry` is a clean dedicated interface (no stringly-typing, no `Record<string,any>`); required `related_lore` mirrors the server. Good type design.
- [SIMPLE] Self-assessed (disabled): `(q.related_lore ?? [])` is evaluated twice (guard + map) — could hoist to one `const`. LOW readability nit, non-blocking; no over-engineering or dead code.
- [RULE] Self-assessed (disabled, lang-review/typescript.md): #6 keys on `fact_id` not index — compliant; #4 uses `??` not `||` — compliant; #1 `as unknown as` only in test fixtures (established idiom) — compliant. No violations.

**Rule Compliance:** lang-review/typescript.md checks applicable to this render-only diff — #4 (null/undefined, `??` used correctly at QuestsPanel.tsx:123/131): compliant; #6 (React key not index — `key={lore.fact_id}` at :132; no `dangerouslySetInnerHTML`): compliant; #1 (type-safety escapes — `as unknown as` only in test fixtures, matching the existing malformed-payload idiom): compliant; #2/#3/#5/#7/#9-#13 (generics/enums/modules/async/build/security): not exercised by this diff. SOUL.md: "legible mechanics in the player UI" — directly served. No-Silent-Fallbacks — the `?? []` suppresses, never fabricates.

**Devil's Advocate:** Suppose this code is broken. The most dangerous angle is the content itself: `related_lore[].content` is server-projected from ScenarioClue facts, and SOUL.md's "Yes, And" lets player- and LLM-authored text become canon — so `content` can contain attacker-controlled markup. If the panel ever used `dangerouslySetInnerHTML`, a player who wrote a clue containing `<img onerror=...>` could land stored XSS in every tablemate's browser. I checked: it does not — `{lore.content}` is a JSX text expression, which React renders via a text node, escaping all markup. Confirmed by reviewer-security and by grep (zero raw-HTML sinks). Second angle: a malicious/buggy server sends 10,000 lore fragments or a 1 MB content string — the panel renders them all unbounded, which could jank the dock. But that is a pre-existing property of every list in this panel (`quest_log`, `quest_anchors` are equally unbounded), not a regression this story introduces, and the server owns projection size. Third angle: a confused author writes two clues with the same `fact_id` — React logs a duplicate-key warning and may mis-order the second fragment; the server's dedup (and the clue-id == fact_id uniqueness invariant) prevents this in practice, and the failure mode is a console warning, not data loss or a crash. Fourth angle: the empty-spine guard — could a quest with lore but no title/stakes vanish? No: any lore rides a `quest_log` entry, and a non-empty `quest_log` forces the populated branch. Fifth: the version-skew payload that omits `related_lore` entirely — the `?? []` guard renders the quest with no lore block and never throws, proven by the dedicated test. The one genuine residual is the duplicate-`quests-lore`-testid coverage gap: the suite does not actually render two lore-bearing quests, so a future regression where lore leaks across quests at scale would not be caught by the current tests. That is a coverage improvement worth a fast-follow, not a defect in the shipped code — the per-entry render structure is correct by construction.

**Pattern observed:** pure presentational component, typed `data` prop, empty-state-first, theme-driven styling, repeated per-entry testids read via `getAllByTestId` — consistent with RelationshipsPanel/LocationPanel siblings (QuestsPanel.tsx).

**Error handling:** `?? []` defensive guard for version-skew (QuestsPanel.tsx:123/131); empty-suppression prevents a dangling header; no throw path. Verified by the "omits related_lore" test.

**Handoff:** To Themis the Just (SM) for finish-story.

## Sm Assessment

**Story selected:** 117-7 — Render quest-related lore in QuestsPanel (p1, 3pts, tdd, UI-only).

**Why now:** The server-side projection landed in 117-5 (server #876) *in the previous commit* — the QUESTS payload already carries `related_lore` (list of `{fact_id, content}`) under each quest entry, but the client drops it. The coherence is "on the wire but unseen." This is the visible payoff of 117-5 and directly answers Keith's stated symptom: "knowledge has multiple references but nothing pulls them into a coherent picture." Player-facing legibility per CLAUDE.md (legible mechanics in the player UI). Smallest p1, single repo, lowest risk.

**Dependency check:** depends_on 117-5 — **done** (verified). Unblocked.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New player-facing render surface + a new typed protocol field. Behavior (lore block) and contract (type parity with the server) both need coverage.

**Test Files:**
- `src/types/__tests__/quests-protocol.test.ts` — type parity: extends the suite with a `related_lore` describe block (3 tests). Imports `QuestLoreEntry`, requires `QuestLogEntry.related_lore: QuestLoreEntry[]` with `{fact_id, content}`. Compile-time guard (enforced at `tsc -b`, not vitest runtime).
- `src/components/__tests__/QuestsPanel.test.tsx` — render behavior: new "related lore (Story 117-7)" describe block (6 tests) + `related_lore: []` added to two existing fixtures. Covers: lore block renders every fragment's `content` under the "what I've learned" label; content (not fact_id) is shown; no block for empty lore; per-quest scoping (no cross-quest leakage); duplicate-content fragments both render (stable `fact_id` key); graceful when `related_lore` is absent (version skew).
- `src/components/GameBoard/__tests__/QuestsWidget-lore-wiring.test.tsx` — **wiring (new file, 2 tests):** drives a `QUESTS` wire message with `related_lore` through the REAL `useStateMirror`, then renders the production `QuestsWidget` with the mirrored snapshot and asserts the lore block surfaces. Proves the field survives the mirror's full-replace and reaches the panel via a production consumer (CLAUDE.md: "Every Test Suite Needs a Wiring Test").
- Fixture-only updates (compile under required field): `src/components/GameBoard/__tests__/GameBoard-quests-tab.test.tsx`, `src/hooks/__tests__/useStateMirror.quests.test.ts`.

**Tests Written:** 11 new tests covering the 6 ACs below (+ 2 existing fixtures touched).
**Status:** RED (failing — ready for Dev). Verified by `117-7-tea-red` runner.

### Acceptance Criteria (defined by TEA — none in YAML)
- **AC1** — A quest carrying `related_lore` renders a "What I've learned about this job" block (`data-testid="quests-lore"`) listing each fragment's `content`.
- **AC2** — A quest with empty `related_lore` renders NO lore block (no dangling header).
- **AC3** — Lore is scoped to its owning quest entry; a fragment on quest A never appears under quest B.
- **AC4 (no fabrication)** — the player sees the `content` string, never the internal `fact_id`; the rich nested `{fact_id, content}` shape — which a thin `Record<string,string>` could not carry — renders.
- **AC5 (type parity)** — `QuestLogEntry.related_lore: QuestLoreEntry[]` (`{fact_id, content}`), required, mirroring the server (`extra: forbid`, never None).
- **AC6 (wiring)** — `related_lore` threads through the real `useStateMirror` full-replace and renders via the production `QuestsWidget`.

### Rule Coverage

| Rule (lang-review/typescript.md) | Test | Status |
|------|------|--------|
| #6 React/JSX — `key={index}` anti-pattern | `renders both fragments even when their content is identical (stable per-fact keys)` | failing |
| #4 null/undefined — missing optional handled gracefully | `does not throw when a quest entry omits related_lore (version-skew wire payload)` | failing |
| #8 test quality — meaningful assertions, no `as any` in assertions | self-check below | n/a |

**Rules checked:** 3 of 13 lang-review rules are directly applicable to this render-only UI change (most concern async/enums/error-handling/build-config, none of which this change touches). The applicable ones have coverage.
**Self-check:** 0 vacuous tests. Every test has a meaningful `getByText`/`getByTestId`/`toHaveLength`/`not.toBeInTheDocument` assertion on a specific value. The two `as unknown as QuestsPayload` casts (version-skew + wire-message construction) mirror the established idiom in `useStateMirror.quests.test.ts` (malformed-payload tests) — they construct deliberately off-contract wire input, not assertion-side type laundering.

### RED Verification (runner `117-7-tea-red`)
- **vitest:** exit 1 — 5 failed / 31 passed. Failures are all the `quests-lore` render assertions (QuestsPanel positive-render + scoping + duplicate-content + wiring render). Negative tests (empty/missing lore) correctly pass.
- **typecheck:** `tsc` (file-scoped) reports `TS2353: 'related_lore' does not exist in type 'QuestLogEntry'` at the fixture sites + missing `QuestLoreEntry` export. The build gate `tsc -b` follows project refs and fails on these.
- Both dimensions are RED for the right reason: no type field, no render block.

**Handoff:** To Hephaestus the Smith (Dev) for the GREEN phase — (1) add `QuestLoreEntry {fact_id, content}` + required `related_lore: QuestLoreEntry[]` to `src/types/payloads.ts`; (2) render the `quests-lore` block in `src/components/QuestsPanel.tsx`, keyed on `fact_id`, label "What I've learned about this job", content-only, defensive `?? []`, no block when empty. No mirror change needed — full-replace already threads the field.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (production):**
- `src/types/payloads.ts` — added `QuestLoreEntry {fact_id, content}` interface and required `related_lore: QuestLoreEntry[]` on `QuestLogEntry`, mirroring the server pydantic model (always emitted, never None).
- `src/components/QuestsPanel.tsx` — added a `data-testid="quests-lore"` block inside each quest entry: a "What I've learned about this job" header (FONT_DISPLAY) followed by each fragment's `content` (inkSoft), keyed on `fact_id`. Guarded with `(q.related_lore ?? [])` so a version-skew wire entry that omits the field degrades to no-block rather than throwing; suppressed entirely when the list is empty.

**Files Changed (test fixtures, to compile under the now-required field):**
- `src/types/__tests__/quests-protocol.test.ts` — added `related_lore: []` to the pre-existing 77-5 `log` fixture.
- `src/components/GameBoard/__tests__/QuestsWidget-lore-wiring.test.tsx` — `questsData ?? null` coercion for the `QuestsWidget` prop type.

**No mirror change:** `useStateMirror`'s QUESTS full-replace (`questsData = p`) already threads `related_lore` through opaquely — verified by the wiring test's "mirror preserves related_lore" assertion.

**Tests:** 36/36 affected tests passing (GREEN). Full UI suite: 2207/2207 passing (no regressions). `tsc -b` clean. My changed source files lint clean (eslint exit 0).

**Known pre-existing issue (not mine):** `npm run lint` fails on `Dashboard/source/useForensicSource.ts:61` — a `react-hooks/set-state-in-effect` error present on `develop` (verified). See Delivery Findings.

**Branch:** `feat/117-7-render-quest-lore` (pushed to origin).

**Handoff:** To Hermes Psychopompos (Reviewer) for code review.

**Scope (two gaps, sidequest-ui, base develop):**
1. `src/types/payloads.ts` — `QuestLogEntry` has no `related_lore` field, so the typed data is invisible to the client.
2. `src/components/QuestsPanel.tsx` — renders only title/status/objective/anchor; needs a "What I've learned about this job" block listing the related lore under each quest.

**Required wiring test:** a `QuestsMessage` carrying `related_lore` must render the lore block (jsdom) — proves the projection is consumed end-to-end, not just typed.

**Routing:** phased TDD → next phase RED, owner TEA (Argus Panoptes). UI-only; no server/content changes expected. Watch that the wiring test asserts the lore block renders from a realistic payload shape matching the server's 117-5 projection.