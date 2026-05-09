---
story_id: "45-34"
jira_key: null
epic: "45"
workflow: "trivial"
---
# Story 45-34: ADR-051 amendment + architecture.md update for 45-11 lockstep collapse

## Story Details
- **ID:** 45-34
- **Jira Key:** none (SideQuest does not use Jira)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 1
- **Priority:** p2

## Background

Story 45-11 (PR #101, merged 2026-05-07) chose Strategy A: `record_interaction()` now advances both `interaction` and `round` counters in lockstep, consolidating the two-tier model.

**ADR-051 Problem:** "Two-Tier Turn Counter" explicitly states that `round` should advance only on meaningful narrative beats (location changes, chapter markers, trope escalations) — a two-tier model where `round ≠ interaction`. But reality: `advance_round()` had zero production callers. The two-tier aspiration was never wired.

PR #101 consolidated the implementation: both counters now advance together. This is a **drift** — the implementation no longer matches the ADR spec.

**Action Items:**
1. Amend ADR-051 (or supersede) to document the lockstep semantics. Note the historical drift: `advance_round()` never called, `narrative_log.round_number ≡ interaction_count`. Reference PR #101 as the cutover point.
2. Update `docs/architecture.md` line 191 (cross-reference to ADR-051) to match the amended ADR.
3. **(Non-blocking, nice-to-have)** Add `lookup_failed=True` attribute to `turn_manager.round_invariant` span when `max_narrative_round()` raises, distinguishing instrument failure from divergence. Currently falls back to 0 (misleading "ahead by N" in GM panel). Defensible as-is until GM-panel UI lands; tighten when ready.

## Repository Notes

**Story YAML lists `repos: server`**, but the actual files being edited are in the **orchestrator repo** (`oq-1`):
- `/Users/slabgorb/Projects/oq-1/docs/adr/051-two-tier-turn-counter.md`
- `/Users/slabgorb/Projects/oq-1/docs/architecture.md`

Branch will be created in **orchestrator** (this repo), not in sidequest-server subrepo. Implementer should note this discrepancy.

## Workflow Tracking

**Workflow:** trivial  
**Phase:** finish  
**Phase Started:** 2026-05-09T14:05:21Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-09 | 2026-05-09T13:53:59Z | 13h 53m |
| implement | 2026-05-09T13:53:59Z | 2026-05-09T13:57:55Z | 3m 56s |
| review | 2026-05-09T13:57:55Z | 2026-05-09T14:05:21Z | 7m 26s |
| finish | 2026-05-09T14:05:21Z | - | - |

## Delivery Findings

### Dev (implementation)
- **Improvement** (non-blocking): `advance_round()` and the legacy `advance()` method on `TurnManager` (`sidequest-server/sidequest/game/turn.py:119-128`) remain in the codebase with zero production callers. Affects `sidequest-server/sidequest/game/turn.py` (could be removed in a follow-up cleanup story alongside any unit tests that exercise them). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `scripts/regenerate_adr_indexes.py` crashes with `ValueError: Unknown format code 'd' for object of type 'str'` at line 216 when `implementation-pointer` is a file path (per ADR-088 schema, file paths are valid pointer values). Currently only ADR IDs (ints) work. Affects `scripts/regenerate_adr_indexes.py:216` (`impl_cell` formatter needs to branch on int-vs-string). Not load-bearing for this story — sidestepped by leaving `implementation-pointer: null` since ADR-051 is `live`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `docs/superpowers/specs/completed/2026-04-26-mp-cinematic-mode-wiring-design.md:6` references "ADR-006 (Two-Tier Turn Counter)" — wrong ADR number; ADR-006 is unrelated, the turn-counter ADR is 051. Pre-existing typo in archived spec. Affects that single line; correctable in a future archive-sweep cleanup. *Found by Reviewer during code review.*
- **Question** (non-blocking): The auto-generated ADR README (`docs/adr/README.md:173`) and the auto-generated CLAUDE.md ADR list both still surface "Two-Tier Turn Counter (Interaction vs. Round)" as the index title. This is intentional per ADR-088 amendment convention (preserve title for cross-reference stability), but if the project decides amended-with-historical-aspiration ADRs should carry an inline drift marker in the index, `scripts/regenerate_adr_indexes.py` would need an opt-in field for amendment annotations (e.g., `amendment-note: "lockstep since 45-11"`). Affects `docs/adr/088-adr-frontmatter-schema.md` and `scripts/regenerate_adr_indexes.py`. *Found by Reviewer during code review.*

## Design Deviations

### Dev (implementation)
- **`implementation-pointer` left null instead of file path** → ✓ ACCEPTED by Reviewer: agrees with Dev reasoning; ADR-088 makes the pointer optional for `live` status, and the regen-script bug is a real blocker (Dev filed it as a delivery finding). Pointer can be added later when the script supports file paths.
  - Spec source: SM Assessment in this session file
  - Spec text: SM did not prescribe pointer value; ADR-088 schema permits file paths.
  - Implementation: Set `implementation-pointer: null`; the Python port path appears in the Decision section prose instead.
  - Rationale: `regenerate_adr_indexes.py` crashes on string-typed pointers (see Delivery Findings). ADR-088 requires the pointer only for `partial` or `drift` statuses; ADR-051 is `live` post-amendment.
  - Severity: trivial
  - Forward impact: none — pointer can be added later if/when the regen script supports file paths.

### Reviewer (audit)
- No undocumented spec deviations spotted. Dev's deviation log covers the only judgment call (pointer field). The follow-up amendment commit (9a814c7) addressed reviewer-flagged contradictions in the initial amendment text but is not itself a spec deviation — it's a reconciliation of internal ADR consistency, in scope of the original story description.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 (all informational) | confirmed 0, dismissed 3 (informational/non-blocking; ADR frontmatter validates, regen-clean, no test smells), deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter` |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.silent_failure_hunter` |
| 4 | reviewer-test-analyzer | Yes | clean | none | N/A — docs-only diff, no tests modified, ADR claims spot-checked against `turn.py` and confirmed accurate |
| 5 | reviewer-comment-analyzer | Yes | findings | 6 | confirmed 3 (high: "froze at 1" contradiction, "single-counter in behaviour" tightening, feature-inventory.md stale ref), dismissed 3 (README/CLAUDE.md auto-generated from title field — title intentionally preserved per amendment-marker convention; superpowers/specs/completed ADR-006 typo is pre-existing in archived spec, out of scope), deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.type_design` |
| 7 | reviewer-security | No | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.security` |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.simplifier` |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 0, dismissed 3 (id:51 vs filename 051 — ADR-088 schema explicitly allows int "preferred", validator passed; title semantic drift — warn-only per ADR-088, amendment-marker convention preserves title; implementation-status:partial — incorrect read of amendment, the Decision section was rewritten to describe lockstep which IS what the live code does, so `live` is correct), deferred 0 |

**All received:** Yes (4 returned, 5 skipped via settings)
**Total findings:** 3 confirmed (all addressed in commit 9a814c7), 9 dismissed (with rationale below), 0 deferred

### Confirmed findings + remediation

1. **[DOC] "froze at 1" contradicts Playtest 3 round=65** — `docs/adr/051-two-tier-turn-counter.md:71` (pre-fix). Amendment text claimed `turn_manager.round` froze at 1, but the same paragraph cited Playtest 3 ending with `round = 65`. Reconciled to "lagged behind `interaction`" — matches both the cited numbers and 45-11's root-cause analysis (narrative_log keyed by `interaction` at `websocket_session_handler.py:1525`, no live caller advanced `round` per-interaction). Fixed in 9a814c7.
2. **[DOC] "single-counter in behaviour" reads as contradiction** — `docs/adr/051-two-tier-turn-counter.md:87`. Net-effect paragraph said "single-counter in behaviour" but the Decision section says "two counters that advance in lockstep." Clarified: both fields are persisted and exposed, but always hold the same value because both advance via `record_interaction()`. Fixed in 9a814c7.
3. **[DOC] feature-inventory.md still lists "Two-tier turn counter"** — `docs/feature-inventory.md:74`. Same pre-amendment framing the architecture.md update fixed; mirror that fix here. Bounded boy-scout (one-line table row, same change as architecture.md). Fixed in 9a814c7.

### Dismissed findings + rationale

- **[DOC] `docs/adr/README.md:173` row title is "Two-Tier Turn Counter (Interaction vs. Round)"** — README is auto-generated from frontmatter `title` field (verified via `scripts/regenerate_adr_indexes.py`). Title intentionally preserved per ADR-088 amendment convention: an in-place amendment with `## Amendment` section keeps the title (and ADR ID) stable to avoid invalidating cross-references. The `> Amended 2026-05-09` marker at top of ADR body is the conventional drift signal.
- **[DOC] `CLAUDE.md:271` ADR list still says "Two-Tier Turn Counter"** — same rationale as above; CLAUDE.md ADR block is auto-generated by the same regen script from the same title field.
- **[DOC] `docs/superpowers/specs/completed/2026-04-26-mp-cinematic-mode-wiring-design.md:6` references ADR-006 (wrong)** — pre-existing typo in archived spec (`completed/` directory), not introduced by this PR. Out of scope for a docs-amendment story; would expand the diff into territory unrelated to the lockstep collapse. Suitable for a separate cleanup if anyone is auditing the completed/ specs.
- **[RULE] id:51 vs filename 051 (rule 2)** — ADR-088 schema comment line: `id: 059  # int (preferred) or zero-padded string`. `int` is the *preferred* form. The id field accepts ints; filenames are zero-padded for sort order. `validate_adr_frontmatter.py` passes (`OK: 1 file validated, 0 errors`). False positive — the rule-checker's interpretation is stricter than the schema actually mandates.
- **[RULE] Title semantic drift (rule 4)** — ADR-088 marks this rule warn-only, and the amendment-marker pattern (`> Amended 2026-05-09`) is the documented convention for preserving titles across substantive amendments. Renaming the title would invalidate every existing cross-reference.
- **[RULE] implementation-status should be `partial`** — incorrect reading of the amendment. The Decision section was *rewritten* (lines 30-46) to describe lockstep — the live behaviour. The Amendment section (lines 65-92) is historical context explaining how we got here. After amendment, the ADR's Decision matches reality, so `implementation-status: live` is correct. ADR-088 defines `partial` as "Implementation exists but does not fully satisfy the ADR" — the post-amendment ADR's stated decision IS what the code does.
- **[PRE] implementation-pointer is null** — informational only; ADR-088 requires a pointer for `partial`/`drift` only, optional for `live`. Pointer field also currently breaks `regenerate_adr_indexes.py` when set to a string (Dev's earlier delivery finding). No regression introduced.
- **[PRE] `advance_round()` legacy method removal candidate** — informational; called out in the ADR's own Negative Consequences section. Removal deferred to follow-up cleanup.
- **[PRE] "Felix" attribution not in CLAUDE.md primary audience list** — informational. Felix appears in 45-11 story description verbatim; the name was carried forward as historical evidence, not a playgroup-rubric assertion. Out of scope.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** ADR Decision → live `TurnManager` (`sidequest-server/sidequest/game/turn.py:100-115`) — `record_interaction()` advances both `interaction` and `round` together; `narrative_log.round_number` is keyed by `interaction` at `websocket_session_handler.py:1525`; OTEL span `turn_manager.round_invariant` (`sidequest-server/sidequest/telemetry/spans/turn.py:97`) emits gap/holds every tick as the GM-panel lie detector. Amended ADR matches each of these ground-truth files line-for-line.

**Pattern observed:** [DOC] In-place ADR amendment with explicit `## Amendment` section, status preserved as `accepted`, title preserved for cross-reference stability — matches ADR-088 convention and the pattern used by other amended live ADRs in the tree.

**Error handling:** [VERIFIED] N/A for docs-only diff. Spot-check of frontmatter validation: `python3 scripts/validate_adr_frontmatter.py docs/adr/051-two-tier-turn-counter.md` → `OK: 1 file validated, 0 errors`. Spot-check of index regen: `python3 scripts/regenerate_adr_indexes.py` → no working-tree drift.

**Rule Compliance** (ADR-088 schema, applicable rules only — no language source files in diff):
- Rule 1 (required fields): compliant — all 10 required fields present.
- Rule 2 (id matches filename prefix): compliant — `id: 51` is the int form (preferred per schema comment); validator passes.
- Rule 3 (title): compliant.
- Rule 4 (title matches H1): warn-only; H1 retains conventional `ADR-051: ` prefix; no semantic drift after Decision-section rewrite.
- Rule 5 (status enum): compliant — `accepted`.
- Rule 6 (date is ISO 8601): compliant — `2026-04-01`.
- Rule 7 (deciders/supersedes/superseded-by/related/tags present): compliant.
- Rule 8 (tags from controlled vocabulary): compliant — `turn-management`.
- Rule 9 (implementation-status enum): compliant — `live` is correct because Decision section was rewritten to match implementation.
- Rule 10 (implementation-pointer required for partial/drift): N/A — status is `live`.

**Observations:**
- [VERIFIED] Amended Decision section accurately describes `record_interaction()` lockstep behaviour — `sidequest-server/sidequest/game/turn.py:100-115` matches.
- [VERIFIED] `TurnPhase` code sample in ADR matches `turn.py:25-32` — five-phase `StrEnum` with the listed members.
- [VERIFIED] Path reference `sidequest-server/sidequest/game/turn.py` resolves on disk.
- [VERIFIED] OTEL span name `turn_manager.round_invariant` matches `telemetry/spans/turn.py:80`.
- [VERIFIED] `architecture.md:191` and `feature-inventory.md:74` updated together — no remaining "two-tier" framing as current truth in tracked feature documentation (auto-generated indexes preserve original title by design).
- [VERIFIED] Frontmatter validates and ADR index regen produces no drift.
- [DOC] Amendment text reconciliation (commit 9a814c7) resolved internal contradictions in the initial commit.
- [DOC] All confirmed comment-analyzer findings remediated; dismissed findings have explicit rationale above.
- [TEST] reviewer-test-analyzer returned clean — no test files or production code in diff; ADR factual claims spot-checked against `sidequest-server/sidequest/game/turn.py` (lines 25-32, 100-115, 119) and confirmed accurate. PROJECT_RULES (vacuous assertions, missing error-path tests) N/A for docs-only diff.
- [RULE] reviewer-rule-checker findings (3) all dismissed with rationale: id:51-vs-051 is the schema-preferred int form (validator passes); title semantic drift is warn-only and amendment-marker convention preserves titles intentionally; implementation-status:live is correct because the Decision section was rewritten to describe lockstep (the live behaviour). No project rule violations confirmed.
- [VERIFIED] Diff stays in scope (orchestrator repo only; no spurious changes to sidequest-server, ui, daemon, or content despite the story YAML's `repos: server` field).

### Devil's Advocate

A skeptical reader could argue this amendment buries the lede — the ADR's stated decision changed substantively (from a two-tier rule with narrative-beat advancement to a lockstep rule with no narrative gating), but the title remains "Two-Tier Turn Counter (Interaction vs. Round)" and the `accepted` status is preserved. A reader scanning index titles could infer the ADR documents a live two-tier system. Counter-arguments:
1. The `> Amended 2026-05-09` marker is the second line of the body, before any Context — anyone who actually opens the ADR sees the amendment signal immediately.
2. ADR-088's amendment convention exists precisely to preserve title/ID stability across substantive rewrites, because invalidating cross-references is more harmful than minor index-table drift.
3. The Decision section now describes the live model in plain language; a reader who follows the link reaches accurate text.
4. `docs/architecture.md:191` and `docs/feature-inventory.md:74` were updated to drop the "two-tier" framing — the *active* feature documentation no longer perpetuates the stale model. Only the auto-generated ADR index titles preserve it, and that's intentional.

A reviewer hostile to in-place amendments could insist on a supersession pattern: a new ADR-095 "Lockstep Turn Counter" supersedes ADR-051, with `superseded-by` and `supersedes` cross-links, and ADR-051 status flipped to `superseded`. That would be a defensible alternative — but ADR-088 explicitly permits in-place amendment for cases like this (no fundamental decision reversal, only a recognition that the decision was never wired and the implementation chose a different path). Picking supersession here would set a precedent that *every* drift-resolution requires a new ADR, doubling the catalogue size for what is essentially a clarifying rewrite.

A reader of the contradictory original commit might reasonably ask "if the dev's analysis says round froze at 1, why does production code say `round=65 / max=72`?" The fix in commit 9a814c7 sidesteps this by saying "lagged behind `interaction`" — describing the observable behaviour rather than asserting a mechanism. This is honest about the genuine ambiguity in the source artifacts (the dev's root-cause analysis and the module docstring give different numbers; both are merged) without inventing a reconciliation. A future investigator chasing the divergence has the Playtest 3 data point and the write-site reference to follow.

A worst-case reader misuses `advance_round()` based on its presence in the codebase. Counter: the docstring, the ADR's Negative Consequences section, and grep returning no callers make the warning surface adequate for the maturity level. Removal can land in a follow-up cleanup once the dust settles on the lockstep semantics.

No new findings surfaced from devil's advocacy.

**Handoff:** To SM for finish-story.

---

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `docs/adr/051-two-tier-turn-counter.md` — amended Decision and Consequences for lockstep semantics; added 2026-05-09 Amendment section documenting the drift (`advance_round()` had zero production callers, Felix's Playtest 3 round=65 vs max=72) and the Strategy A cutover via PR #101; added Strategy B alternative for design-history completeness; updated implementation path reference from Rust (`sidequest-game/src/turn.rs`) to Python port (`sidequest-server/sidequest/game/turn.py`); updated `TurnPhase` code sample from Rust enum to Python `StrEnum`.
- `docs/architecture.md` — replaced line 191 "Two-tier turn counter" cross-reference with "Lockstep turn counter" description citing 45-11 / PR #101.

**Tests:** N/A — pure docs change, trivial workflow.

**Branch:** `feat/45-34-adr-051-amendment-architecture-update` (pushed to origin)

**Pre-flight:**
- ADR frontmatter validated via `scripts/validate_adr_frontmatter.py` (OK).
- ADR indexes regenerated via `scripts/regenerate_adr_indexes.py` (no diff — README/SUPERSEDED/DRIFT/CLAUDE.md unchanged because frontmatter unchanged).

**Repo discrepancy confirmed:** Story YAML lists `repos: server` but the actual files are in the orchestrator repo. Branch and commits live in oq-1 (orchestrator). Reviewer should not look for changes in `sidequest-server`.

**Handoff:** To reviewer (review phase).

---

## Sm Assessment

**Scope:** 1pt p2 documentation amendment. ADR-051 currently asserts a two-tier turn-counter model that PR #101 (story 45-11) collapsed into lockstep. ADR is now drift; needs amendment to reflect implemented reality.

**Files in play (orchestrator repo, despite YAML `repos: server`):**
- `docs/adr/051-two-tier-turn-counter.md` — amend (or supersede) to document lockstep semantics, cite PR #101 as cutover, record historical drift (`advance_round()` had zero production callers)
- `docs/architecture.md` line 191 — update cross-reference to match amended ADR

**Repo discrepancy resolved:** Implementation lives in orchestrator, not sidequest-server. Branch was created in orchestrator (`feat/45-34-adr-051-amendment-architecture-update`). The `repos: server` field in story YAML is incorrect for this story — implementer should ignore and work in orchestrator.

**Non-blocking opportunity:** ADR-051 §3 implementation note suggests adding `lookup_failed=True` OTEL attribute on `turn_manager.round_invariant` span when `max_narrative_round()` raises. Defensible to defer; tighten when GM-panel UI lands. Out of scope for this story unless trivial.

**Workflow:** trivial — setup → implement → review → finish. No tests required (pure docs). Reviewer should sanity-check the amended ADR for accuracy against current code (`game/turn_manager.py`, `narrative_log` invariants) and confirm the architecture.md cross-reference still resolves.

**Handoff target:** dev (implement phase).