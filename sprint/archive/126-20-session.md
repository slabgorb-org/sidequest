---
story_id: "126-20"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 126-20: [FATE/UX] Inventory empty-state copy for legitimately-empty Fate inventories

## Story Details
- **ID:** 126-20
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-19T12:45:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T12:33:57Z | 2026-06-19T12:35:27Z | 1m 30s |
| implement | 2026-06-19T12:35:27Z | 2026-06-19T12:40:14Z | 4m 47s |
| review | 2026-06-19T12:40:14Z | 2026-06-19T12:45:52Z | 5m 38s |
| finish | 2026-06-19T12:45:52Z | - | - |

## SM Assessment

**Routing decision:** New work, trivial/phased workflow → hand off to Dev (implement phase). No design or RED phase needed for a 1-pt UI copy change.

**Merge gate:** Clear. Only 150-1 in progress (playtest, no PR); no open PRs in any repo.

**Story scope (what Dev must honor):**
- This is a *copy/empty-state* fix in `sidequest-ui`, **not** a tab-visibility change. The native Inventory tab is correctly VISIBLE for Fate now — #419 reversed 126-3's earlier hide. Do NOT re-hide the tab.
- Add explicit empty-state copy to the Inventory panel when there are zero inventory items (e.g. "Nothing in your pockets yet" or a Fate-flavored variant) so a legitimately-empty Fate inventory reads as intentional, not broken.
- Why Fate matters here: signature gear lives as ASPECTS, not inventory lines (wry_whimsy/gear.yaml: "gear is not a carried inventory... compiled into the FateSheet at chargen as aspects"). So an empty inventory is the *normal* Fate state, not an error.
- Find the inventory panel component under `sidequest-ui/src/components/` (look for the Inventory tab render). The empty branch is what needs copy.

**Design implication (CLAUDE.md):** Sebastien/Jade are mechanics-first; this is a player-facing surface, so the copy should make the legitimately-empty state legible rather than mysterious — but keep it light, it's a 1-pt trivial.

**Branch:** `feat/126-20-fate-inventory-empty-state` (base: `develop`, sidequest-ui gitflow).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings. The empty-state was a clean local fix in `InventoryPanel.tsx`; the Fate signal (`showCurrency={false}`) and the visible-tab wiring (#419) were already in place.

### Reviewer (code review)
- **Improvement** (non-blocking): The new empty-state branch is unit-tested in `InventoryPanel.test.tsx` but is never exercised end-to-end through GameBoard — every Fate PC in `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` has a *populated* inventory. Component-level wiring is already proven by that suite (9 tests render `InventoryPanel` via the production widget registry with the real `showCurrency` prop), so the wiring rule is satisfied; this is a coverage top-up, not a gap in reachability. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` (add one test: empty `fateInventory` → click Items tab → assert `inventory-empty` + `/lives in your aspects/i`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Minor unit-assertion strengthening — the `showCurrency=false` test could co-assert the primary line ("Nothing in your pockets yet.") alongside the aspects hint so both `<p>`s are proven to coexist in one render; and the pre-existing `renders with empty items list` test (line 68) now overlaps the new empty-state behavior and could be promoted to assert `inventory-empty`. Affects `sidequest-ui/src/components/__tests__/InventoryPanel.test.tsx`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** The new empty-state branch is unit-tested in `InventoryPanel.test.tsx` but is never exercised end-to-end through GameBoard — every Fate PC in `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` has a *populated* inventory. Component-level wiring is already proven by that suite (9 tests render `InventoryPanel` via the production widget registry with the real `showCurrency` prop), so the wiring rule is satisfied; this is a coverage top-up, not a gap in reachability. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx`.

### Downstream Effects

- **`sidequest-ui/src/components/GameBoard/__tests__`** — 1 finding

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. The story permits "generic / Fate-flavored" copy; I implemented both (generic primary line always, Fate-context secondary line). Note for reviewer: Fate detection reuses the existing `showCurrency={false}` prop — the same no-economy signal the GameBoard already passes only for Fate packs (per `GameBoard-fate-inventory-tab.test.tsx`). No new Fate-detection plumbing was added.

### Reviewer (audit)
- **Dev's `showCurrency`-as-Fate-signal reuse** → ✓ ACCEPTED by Reviewer: verified at `GameBoard.tsx:628` (`showCurrency={fateData == null}`) by the comment-analyzer — `false` ⟺ `fateData != null` ⟺ Fate pack, exactly. Reusing the existing signal instead of threading a new `isFate` prop is the right call for a 1-pt change and matches the established inventory wiring. Documented residual: if a future *native* pack ever passed `showCurrency={false}` (no economy but not Fate) it would wrongly show the "aspects" hint — there is no such caller today, and the inline comment flags it. No new deviation undocumented.

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/components/InventoryPanel.tsx` — render an empty-state block when `data.items.length === 0` (instead of an empty content div under the header). Primary line "Nothing in your pockets yet." always; secondary line "Your signature gear lives in your aspects, not as carried items." gated on `!showCurrency` (Fate). Empty block carries `data-testid="inventory-empty"`. Uses the existing Folio palette/fonts so it reads as the same artifact.
- `sidequest-ui/src/components/__tests__/InventoryPanel.test.tsx` — added 4 tests: empty-state copy shows on empty inventory; Fate aspects hint shows when `showCurrency=false`; aspects hint omitted for native economy pack; empty-state absent when items exist.

**Tests:** 18/18 InventoryPanel + 9/9 GameBoard Fate-inventory regression = 27/27 passing (GREEN). ESLint clean on both changed files.

**Wiring:** `InventoryPanel` is consumed in production via `InventoryWidget` → GameBoard widget registry (the same path the 126-3 reversal restored for Fate). No new component — the empty branch of an already-wired component now renders copy. The `showCurrency` prop the empty-state reads is the one GameBoard already passes (false for Fate, true for native), verified green by the GameBoard regression suite.

**Scope honored:** Empty-state copy only — the Inventory tab stays VISIBLE for Fate (did not touch the #419 visibility gate). No backend/OTEL changes (cosmetic UI copy, exempt per UI CLAUDE.md).

**Branch:** `feat/126-20-fate-inventory-empty-state` (pushed, base `develop`).

**Handoff:** To review (Chrisjen Avasarala / Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 6 observations, 0 blocking | confirmed 0, dismissed 1 (Equip→Equipped misattribution — not in this diff), deferred 0; rest are notes corroborating other agents |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 2 (as non-blocking Improvements: GameBoard empty-path wiring top-up; unit-assertion strengthening), dismissed 0, deferred 3 (low-value coverage nits folded into the same finding) |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — verified all comments accurate vs GameBoard.tsx:628 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (13 rules, 27 instances, 0 violations) | N/A |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 2 confirmed (both non-blocking Improvements), 1 dismissed (with rationale), 0 deferred-as-blocking

## Reviewer Assessment

**Verdict:** APPROVED

A 1-pt cosmetic copy change. Code is correct, fully wired, lint/tsc/test clean, zero rule violations, comments verified accurate. The confirmed findings are test-*completeness* improvements (LOW/MEDIUM severity) — none are Critical/High, so per the blocking rule they do not block. Captured as non-blocking Delivery Findings so they aren't lost.

**Dispatch tags (all 8 accounted for):**
- `[TEST]` — Confirmed (non-blocking): the empty-state branch has solid unit coverage (4 tests, Fate + native × present/absent) but no end-to-end exercise through GameBoard (the 9 GameBoard tests all use a *populated* inventory). Filed as an Improvement. Also flagged: pre-existing line-68 test is now thin, and the Fate test could co-assert both `<p>` lines. None blocking — the behavior is proven at the unit level and the component's production wiring is proven by the existing GameBoard suite.
- `[DOC]` — Clean. comment-analyzer verified all three comment claims against source; `showCurrency={fateData == null}` confirmed at `GameBoard.tsx:628`. The cross-reference to `GameBoard-fate-inventory-tab.test.tsx` is valid and the file exists.
- `[RULE]` — Clean. rule-checker: 13 TypeScript checklist rules, 27 instances, 0 violations. Key props (`key={type}`, `key={`${item.type}-${item.name.trim()}`}`) preserved across the ternary refactor; JSX structurally valid (both branches return legal React children); no `as any` / `@ts-ignore` / non-null assertions; no silent fallbacks; no stubs.
- `[EDGE]` — Subagent disabled via settings. Self-assessed: the only new branch boundary is `data.items.length === 0`; `data.items` is typed `InventoryItem[]` (non-optional), so `.length` is safe. Both branches (empty / non-empty) are unit-tested. No unhandled path.
- `[SILENT]` — Subagent disabled. Self-assessed: the change adds *visible* copy where there was silence — the opposite of a silent fallback. No swallowed errors, no empty catches (no error paths introduced).
- `[TYPE]` — Subagent disabled. Self-assessed: no new types, generics, or casts; `!showCurrency` is a boolean negation on a typed prop with a `= true` default. Compliant.
- `[SEC]` — Subagent disabled. Self-assessed: both new strings are hardcoded literals — no user input, no `dangerouslySetInnerHTML`, no interpolation into markup. No injection surface.
- `[SIMPLE]` — Subagent disabled. Self-assessed: the ternary is the minimal way to render an empty branch; no over-engineering, no dead code. The one residual (single `showCurrency` prop doubling as the Fate signal) is an accepted, documented trade-off, not added complexity.

**Observations (≥5):**
1. `[VERIFIED]` Empty-state branch fires correctly — `InventoryPanel.tsx:135` gates on `data.items.length === 0`; `data.items` is non-optional `InventoryItem[]` (`InventoryPanel.tsx:12`), so no null risk. Unit-tested both ways.
2. `[VERIFIED]` Fate secondary line correctly gated — `!showCurrency` at the new branch mirrors the existing currency-gate at `InventoryPanel.tsx:117`; production passes `showCurrency={fateData == null}` (`GameBoard.tsx:628`). Native packs (default `true`) get only the generic line — proven by the `currency_name: 'credits'` test.
3. `[VERIFIED]` Refactor preserved list keys — `key={type}` and the composite `li` key survive inside the else-branch unchanged (rule-checker rule #6, confirmed); no `key={index}` introduced.
4. `[VERIFIED]` Production wiring intact — `InventoryPanel` → `InventoryWidget` → GameBoard widget registry; 9 GameBoard tests render it end-to-end and stay green. The empty branch reads the same already-wired `showCurrency` prop.
5. `[TEST]` Non-blocking gap — empty-state branch not exercised through GameBoard end-to-end; filed as Improvement.
6. `[VERIFIED]` No backend/OTEL needed — cosmetic UI copy, explicitly exempt per `sidequest-ui/CLAUDE.md` ("Not needed for: Cosmetic UI changes").

**### Rule Compliance**
- "No Silent Fallbacks" (CLAUDE.md) — COMPLIANT: change replaces a silent blank panel with explicit copy. No alternative-path masking.
- "No Stubbing" (CLAUDE.md) — COMPLIANT: empty-state and its 4 tests are fully implemented; no placeholders.
- "Don't Reinvent — Wire Up What Exists" (CLAUDE.md) — COMPLIANT: reuses existing `showCurrency` Fate signal and the already-wired component; no new plumbing.
- "Every Test Suite Needs a Wiring Test" (CLAUDE.md, `<critical>`) — COMPLIANT at the suite/component level: `InventoryPanel` has an integration wiring test via `GameBoard-fate-inventory-tab.test.tsx` (renders through the production registry). The new branch's *own* end-to-end exercise is the non-blocking Improvement above — the rule's reachability requirement is met; the top-up deepens it.
- "OTEL on every backend subsystem" (CLAUDE.md) — N/A: cosmetic UI copy, explicitly exempt.
- SOUL "The Test" / Agency — COMPLIANT: copy describes the world (an empty pocket), never authors player action.

**Data flow traced:** `GameState.inventoryData` (server payload) → GameBoard `inventory` case → `InventoryWidget` (`showCurrency={fateData == null}`) → `InventoryPanel`. When `data.items` is empty, the panel renders the empty-state `<div data-testid="inventory-empty">` instead of a blank content area; the Fate hint appears iff `showCurrency` is `false`. Safe: all inputs are display-only strings/arrays; no mutation, no async, no auth surface.

**### Devil's Advocate**
Argue this is broken. First attack: the ternary refactor could have mangled the existing list render — a dropped paren or a lost `key` would corrupt every non-empty inventory. Checked: rule-checker enumerated both keys as preserved, `tsc --noEmit` is clean project-wide, and 9 GameBoard tests plus 14 pre-existing InventoryPanel tests render the *populated* path green. So the common-case render is intact. Second attack: `showCurrency` is overloaded — it means "this pack has an economy," and the code repurposes it as "this is Fate." A confused future dev could pass `showCurrency={false}` on a non-Fate economy-less pack and get a nonsensical "your gear lives in your aspects" line on a d20 sheet. This is real but hypothetical — there is exactly one caller (`GameBoard.tsx:628`) and it derives the value from `fateData == null`; the inline comment documents the coupling; Dev logged it and I accepted it as a scoped trade-off. Third attack: the empty state could flash during load — if `inventoryData` arrives as `{items: []}` before the real payload, the player briefly sees "Nothing in your pockets yet." That's a pre-existing loading-state concern of the data layer, not introduced here, and the copy reads as intentional either way (which is the whole point of the story). Fourth attack: a malicious server could send a huge `items` array — but that path is unchanged by this diff and the empty branch is `O(1)`. Fifth: the strings are hardcoded English, untranslated — but the entire UI is single-locale today, so no regression. None of these rise to a correctness defect in the changed code. The fix does exactly what the story asked and nothing it didn't.

**Verdict rationale:** No Critical/High findings. Code correct, wired, clean, rule-compliant. Two non-blocking test-coverage Improvements recorded for follow-up. APPROVED.

**Handoff:** To SM (Camina Drummer) for finish-story.