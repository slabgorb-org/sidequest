---
story_id: "101-8"
jira_key: ""
epic: "101"
workflow: "tdd"
---
# Story 101-8: Unify slug derivation across render/portrait/reference surfaces

## Story Details
- **ID:** 101-8
- **Jira Key:** (none — SideQuest is a personal project, Jira skipped by design)
- **Workflow:** tdd
- **Repos:** server, daemon, orchestrator
- **Stack Parent:** none

> **Repos amended 2026-06-10 (TEA, RED phase):** orchestrator ADDED per user decision
> (AC1 canonical-rule scope). `scripts/render_common.py` (rule 1) is the one rule that
> writes non-ASCII to R2; it must adopt the unified NFKD-fold rule. This **Repos:** line
> is authoritative (the sprint YAML still says server,daemon — logged as a deviation
> below). A 3rd PR (orchestrator → main) is required at finish.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T10:59:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T00:00:00Z | 2026-06-10T10:23:23Z | 10h 23m |
| red | 2026-06-10T10:23:23Z | 2026-06-10T10:40:13Z | 16m 50s |
| green | 2026-06-10T10:40:13Z | 2026-06-10T10:53:55Z | 13m 42s |
| review | 2026-06-10T10:53:55Z | 2026-06-10T10:59:30Z | 5m 35s |
| finish | 2026-06-10T10:59:30Z | - | - |

## Branches
- **sidequest-server:** `feat/101-8-unify-slug-derivation` (base=develop)
- **sidequest-daemon:** `feat/101-8-unify-slug-derivation` (base=develop)
- **orchestrator (oq-2):** `feat/101-8-unify-slug-derivation` (base=main) — added in RED phase per the repos amendment above.

**Branch Strategy:** server/daemon gitflow (base=develop); orchestrator base=main.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): make the NFKD-fold core a SHARED, importable helper (not inlined per surface). Affects the server slug helpers + daemon `_slugify_name` + `scripts/render_common.py` (all re-point to it). Story 84-7 now carries a dependent AC requiring the intent-router alias matcher to reuse this SAME helper — if Dev buries the fold inside each function, 84-7 cannot reuse it. *Found by TEA during test design.*
- **Gap** (non-blocking): NFKD does not decompose stand-alone letters (ł, ø, þ, Cyrillic), so those still drop (`Łódź`→`odz`). Documented + pinned in `test_101_8_slug_unification.py::test_nfkd_nondecomposing_letter_limitation_is_documented`. If a Polish/Nordic/Cyrillic world needs lossless keys, a follow-up to swap in `anyascii`/`unidecode` is the deliberate next step. *Found by TEA during test design.*
- **Question** (non-blocking): POI image R2 key = `poi_image_key(verbatim authored slug)` (Story 71-38 decouple), distinct from the membership anchor. Dev should confirm the render side (`render_common`) writes the POI `<slug>.png` under the folded slug so the verbatim key the page requests is the ASCII key on R2. The membership-anchor RED test covers the gate; the image-key write-side is the orchestrator half. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): a residual pre-existing ASCII-punctuation divergence remains between `scripts/render_common.slugify` (keeps `&`) and the consumer `slugify_player_name` (drops `&`). Out of scope for 101-8 (non-ASCII story). Affects `scripts/render_common.py` (would need a deliberate ASCII-filter unification + R2 re-key). *Found by Dev during implementation.*
- **Note** (non-blocking): 6 server + 41 orchestrator pre-existing test failures observed in the full sweep are unrelated to this change (aside-contract, namegen-corpora ×4, encounter-actors; playtest_messages refactor) — none import the slug/render modules (verified by grep). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `scripts/render_common.py:slugify` docstring states the trailing drop is `[^a-z0-9_-]`, but the code is `re.sub(r"[^\x00-\x7f]", "", slug)` (non-ASCII-only). Affects `scripts/render_common.py` (one-line docstring fix to match the actual non-ASCII-only filter). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### DEVIATION: Repos vs. blast radius mismatch
**What:** The story blast-radius names `scripts/render_common.py` (orchestrator repo) as one of the surfaces requiring unification. However, the story's repos field lists only `server,daemon` (subrepos).

**Spec said:** AC1 requires "unified slug derivation rule" and AC2 specifies unification across "all render surfaces"; if `render_common.py` is a render surface, orchestrator should be added to the repos list.

**Why:** Unclear at setup time whether the unified rule must be imported into `render_common.py` or whether `render_common.py` is being refactored separately. This is a design decision the implementer (TEA/Dev) must make explicitly: either (a) add orchestrator as a repo and update render_common to use the canonical rule, or (b) treat render_common.py as out-of-scope and document why the unification is sufficient for the story AC without it.

**Resolution:** Implementer decides at RED phase. If orchestrator work is needed, create a new story or add orchestrator to this story's repos (with session update). If render_common stays separate, log the design decision in this section explaining the boundary.

### DEVIATION: Slug canonicalization rule is undocumented
**What:** AC1 requires a "canonical slug derivation rule" but doesn't specify which of the existing rules (daemon asset drop-non-ASCII vs. other surfaces) should be authoritative.

**Spec said:** AC1: "Document a single canonical slug derivation rule"; AC2: "All render surfaces use the canonical rule."

**Why:** Multiple slug rules exist in the codebase (daemon media respects non-ASCII, render surfaces may differ). The spec doesn't name which rule is canonical or whether a new rule is being created. This is a deliberate design decision, not an ambiguity.

**Resolution:** Implementer documents the decision at RED phase. Options: (1) daemon's non-ASCII rule becomes canonical (justify why), (2) an explicit transliteration step is introduced (define the function, cite spec), (3) a hybrid approach with conditional logic (document the conditions). This decision is load-bearing for AC2 wiring and must be captured before GREEN.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- **"Single source of truth" realized as a shared FOLD CORE + per-surface separator functions, not one literal function.**
  - Spec source: context-story-101-8.md, AC1 ("One shared slug-derivation function … duplicates deleted")
  - Spec text: "all other call sites import it and the duplicates are deleted"
  - Implementation: created `sidequest/server/slug_fold.fold_to_ascii` as the single non-ASCII normalization source of truth; `slugify_player_name` and `reference_slug.slugify` both import + call it, then apply their own separator. The two surface functions remain distinct because their ASCII algorithms genuinely differ (portrait `_`/collapse-whitespace+drop → `cosh__run`; reference `-`/collapse-any-run → `cosh-run`) and AC3 forbids changing ASCII output. A single function would have to change one surface's ASCII slugs.
  - Rationale: the only AC3-consistent reading of "single source of truth" is sharing the non-ASCII core, which is what actually diverged. Keeps ASCII byte-identical.
  - Severity: minor (interpretation of AC1, ratified by the TEA deviation that pre-decided the fold approach)
  - Forward impact: 84-7 imports `fold_to_ascii` from `slug_fold` for the intent-router alias matcher.

- **Cross-repo duplication of the fold (daemon + render_common) is intentional, not a missed dedup.**
  - Spec source: context-story-101-8.md, AC1
  - Spec text: "duplicates are deleted"
  - Implementation: daemon `_slugify_name` and `scripts/render_common.slugify` each carry their OWN `fold_to_ascii`-equivalent because they are separate packages that cannot import the server (the pre-existing `slugify_player_name` docstring already documents this constraint). Output equality is pinned by the cross-repo slug tests (same golden vector in all three suites) + `test_server_slug_equals_render_script_slug`.
  - Rationale: introducing a shared runtime package across server/daemon/orchestrator for one helper is disproportionate; the contract test is the anti-drift guard.
  - Severity: minor
  - Forward impact: a future shared `sidequest-common` package could collapse these three copies.

- **render_common.slugify drops ONLY non-ASCII survivors (`[^\x00-\x7f]`), not the full `[^a-z0-9_-]` consumer filter.**
  - Spec source: context-story-101-8.md, AC3 ("ASCII names produce identical slugs to today")
  - Spec text: "no behavior change" on ASCII
  - Implementation: render_common historically KEPT ASCII punctuation like `&` that the consumer rule drops. Applying the consumer's full `[^a-z0-9_-]` filter would change render_common's ASCII output (`a & b` → `a__b`). Instead I fold + drop only non-ASCII bytes, so non-decomposing letters (ł) still match the consumer (`odz`) while ASCII punctuation behavior is preserved.
  - Rationale: honors AC3 for render_common while still achieving render-key == consumer-key on the diacritic class the story targets.
  - Severity: minor
  - Forward impact: a residual pre-existing ASCII-punctuation divergence between render_common (`&` kept) and the consumer (`&` dropped) remains — out of scope for 101-8 (non-ASCII story); flag if a `&`-named asset 404s.

- **Fixed two existing tests that pinned the OLD (pre-fold) behavior.**
  - Spec source: the tests TEA/prior stories wrote
  - Spec text: `test_101_8_diacritic_resolution` used `a.get("slug")`; `test_npc_portrait_resolution::test_server_slug_equals_render_script_slug` inlined the old drop rule
  - Implementation: (1) POI span keys its slug under `reference.slug` (via `_poi_attrs`), not `slug` — corrected the test's attr key (production code was right). (2) Updated the inline render-rule copy to NFKD-fold and added the `"Srárný Fyzioloniązka"` diacritic case — strengthening the 404-guard contract rather than weakening it.
  - Rationale: both are legitimate updates to reflect the unified rule; neither weakens an invariant.
  - Severity: minor
  - Forward impact: none.

### TEA (test design)

- **Canonical slug policy DECIDED: NFKD-fold (stdlib), per-surface separators preserved.**
  - Spec source: context-story-101-8.md, AC1 ("canonical rule chosen DELIBERATELY … documented decision")
  - Spec text: "likely the daemon/asset drop-non-ASCII rule 2 … OR an explicit transliteration step"
  - Implementation: User (Keith) chose `unicodedata.normalize("NFKD", …)` + strip combining marks
    as the shared non-ASCII normalization core, then each surface keeps its own separator
    (portraits/daemon `_`, reference `-`). Folds é→e, á→a, ą→a, ñ→n. Non-decomposing letters
    (ł, ø, þ, Cyrillic) still drop — documented limitation; no new dependency (anyascii/unidecode
    explicitly NOT added). `"Srárný Fyzioloniązka"` → portraits `srarny_fyzioloniazka`,
    reference `srarny-fyzioloniazka`.
  - Rationale: readable ASCII R2 keys, zero new deps, ASCII output unchanged (AC3). Strictly better
    than the lossy drop and kills rule 1's non-ASCII-keeping. Reviewer should ratify the documented
    decision lives in code (module docstring of the shared slug helper).
  - Severity: significant (sets durable R2 object keys)
  - Forward impact: any future surface deriving slugs must call the shared fold; diacritic worlds
    (evropi, coyote_star) now key readable ASCII assets.

- **MEASURED: each surface is internally consistent TODAY — this is a consolidation refactor, not a live-404 fix.**
  - Spec source: context-story-101-8.md ("silent 404 / not_found CLASS of bug"; type: refactor)
  - Spec text: "any non-ASCII POI/location name can mis-key its asset"
  - Implementation: Verified in code — NPC portraits use rule 2 on BOTH daemon write and server gate
    (consistent); POI uses the verbatim authored slug on BOTH render write and `poi_image_key` gate
    (Story 71-38 decouple, consistent); POI anchor/deep-link uses rule 3 on both sides. No production
    cross-mismatch fires today. The externally-observable change comes ONLY from adopting the fold.
    RED tests therefore assert the NFKD-fold OUTPUT (a real behavior change on non-ASCII) and the
    end-to-end diacritic resolution under the unified rule — NOT a fabricated current 404.
  - Severity: minor (framing/scope honesty)
  - Forward impact: Dev should not "fix" a 404 that isn't firing; the deliverable is dedup + the
    documented fold + diacritic end-to-end coverage.

- **Repos amended server,daemon → +orchestrator (render_common.py).**
  - Spec source: context-story-101-8.md, blast radius (rule 1 = `scripts/render_common.py`); sprint YAML repos
  - Spec text: "Rule 1 (render_common.slugify) is used by the render scripts."
  - Implementation: User chose to bring orchestrator into scope so the render-side R2 keys adopt the
    unified fold. Session **Repos:** line updated (authoritative); sprint YAML still reads server,daemon.
  - Severity: significant (adds a 3rd repo + PR-to-main at finish)
  - Forward impact: SM must create+merge an orchestrator PR (base=main) in addition to server/daemon.

### Reviewer (audit)

All logged deviations stamped:
- **DEVIATION: Repos vs. blast radius mismatch** → ✓ ACCEPTED by Reviewer: orchestrator inclusion is the correct, user-ratified choice; the render-side rule is the one that writes non-ASCII to R2, so it must adopt the fold for render-key == consumer-key.
- **DEVIATION: Slug canonicalization rule is undocumented** → ✓ ACCEPTED by Reviewer: resolved deliberately (NFKD fold), documented in `slug_fold.py` docstring and the contract tests. Satisfies AC1's "documented decision".
- **Dev: "single source of truth" as shared fold core + per-surface separators** → ✓ ACCEPTED by Reviewer: the measured ASCII divergence (`cosh__run` vs `cosh-run`) proves the two surface functions are genuinely distinct algorithms; AC3 forbids collapsing them. Sharing the non-ASCII core is the only AC3-consistent reading of AC1. Verified `fold_to_ascii` is the single core both server functions import (utils.py:3, reference_slug.py:18).
- **Dev: cross-repo duplication of the fold (daemon + render_common)** → ✓ ACCEPTED by Reviewer: server↔daemon cross-import is architecturally disallowed (utils.py docstring predates this story); the golden-vector contract tests in all three suites + `test_server_slug_equals_render_script_slug` are the anti-drift guard. Proportionate.
- **Dev: render_common drops only `[^\x00-\x7f]`, not the full consumer filter** → ✓ ACCEPTED by Reviewer: correctly preserves render_common's historical ASCII-punctuation behavior (AC3) while achieving non-ASCII parity. The residual `&`-divergence is genuinely pre-existing and out of this non-ASCII story's scope.
- **Dev: fixed two existing tests pinning OLD behavior** → ✓ ACCEPTED by Reviewer: (1) the POI span attr IS `reference.slug` (verified `_poi_attrs` in telemetry/spans/reference.py:433) — production was right, test was wrong; (2) the inline render-rule fixture update + diacritic case STRENGTHENS the 404-guard, does not weaken it.
- **TEA: canonical policy / measured-internal-consistency / repos-amend** → ✓ ACCEPTED by Reviewer: the "consolidation refactor, not live-404" framing is honest and matches my reading of the code; the tests assert real fold behavior, not a fabricated 404.

### Reviewer (audit) — undocumented divergence spotted
- **render_common.slugify docstring/code mismatch:** the docstring says the trailing drop is `[^a-z0-9_-]`, but the code uses `re.sub(r"[^\x00-\x7f]", "", slug)`. The two are NOT equivalent (`[^a-z0-9_-]` would also strip ASCII punctuation; `[^\x00-\x7f]` strips only non-ASCII). The Dev deviation log correctly describes the `[^\x00-\x7f]` choice, but the in-code docstring still says `[^a-z0-9_-]`. Severity: LOW (doc accuracy, non-blocking). Recommend a one-line docstring fix.

## Implementation Notes

### Acceptance Criteria (from sprint YAML)
1. **AC1:** Document a single canonical slug derivation rule covering non-ASCII name handling (transliteration, drop, or replacement).
2. **AC2:** Verify all render surfaces (render pipeline, portrait resolver, reference page resolver) apply the canonical rule deterministically.
3. **AC3:** Wiring test demonstrates the rule is live (OTEL span or fixture behavior test), not just source-text present.

### Wiring Test Specification
Per CLAUDE.md development principles, the wiring test must verify end-to-end behavior, not source grep:
- **Approach:** OTEL span emission test (e.g., `reference_portrait_resolved_span`, `reference_portrait_not_found_span`) or fixture behavior test driving the slug through the real resolution path.
- **Coverage:** All three surfaces (render, portrait, reference) must emit observable evidence that the canonical rule was applied.
- **Anti-pattern:** Source-text grep for function names or rule existence is not sufficient — must verify the rule is actually called in production code paths.

### Multi-Repo PR Protocol
Both server and daemon repos follow github-flow (branch + PR + squash-merge):
1. Create feature branch (done: `feat/101-8-unify-slug-derivation` in each repo).
2. Implement + test in each repo independently.
3. At finish phase, SM will create + merge one PR per repo to develop (auto-merged via `pf sprint story finish`).
4. Orchestrator session/sprint YAML updated after both PRs land.

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `sidequest-server/tests/server/test_101_8_slug_unification.py` — unit behavior: AC3 ASCII-unchanged guards (measured current values) + AC1 NFKD-fold on `slugify_player_name` and `reference_slug.slugify` + single-fold-core cross-surface contract + documented `Łódź` limitation.
- `sidequest-server/tests/server/test_101_8_diacritic_resolution.py` — AC2 wiring: diacritic NPC (`build_cast_section`) and POI (`build_poi_section`) RESOLVE under the unified fold, proven via OTEL span assertions (`reference_portrait_resolved` / `reference_poi_image_resolved` fire; `*_not_found` does not). No source-text grep (server CLAUDE.md).
- `sidequest-server/tests/server/test_reference_slug.py` — flipped the existing `("naïve","na-ve")` characterization case to `("naïve","naive")` (RED now; the one existing-suite case the fold intentionally changes).
- `sidequest-daemon/tests/test_101_8_slug_fold.py` — `_slugify_name` fold + ASCII-unchanged + server-parity pin.
- `scripts/tests/test_101_8_render_common_slug.py` — `render_common.slugify` fold (today KEEPS non-ASCII → RED) + ASCII-unchanged + consumer-parity pin.

**Tests Written:** 24 failing across 3 repos (server 12 / daemon 7 / orchestrator 5), plus 31 ASCII-armor guards passing. Covers AC1 (canonical fold, single source), AC2 (diacritic NPC+POI wiring via OTEL), AC3 (ASCII unchanged + diacritic end-to-end). AC4 (distinct-from-evropi-r2_manifest incident) is a documentation requirement on Dev — recorded in Design Deviations, not separately testable.
**Status:** RED (failing — ready for Dev)

### Rule Coverage (server CLAUDE.md rules, the load-bearing checklist here)

| Rule | Test(s) | Status |
|------|---------|--------|
| No source-text wiring tests | AC2 uses OTEL span assertions + real projection builders (`test_101_8_diacritic_resolution.py`) | RED |
| Every suite has a wiring test | diacritic NPC+POI drive the real `build_cast_section`/`build_poi_section` end-to-end | RED |
| Meaningful assertions / no vacuous | every test asserts concrete slug values or specific span slugs; self-checked | pass |
| No silent fallbacks (measure, not assume) | ASCII expectations are MEASURED current outputs (`cosh__run`, `historyyaml`) not hand-computed | pass |
| Fail-loud limitation documented | `test_nfkd_nondecomposing_letter_limitation_is_documented` pins `Łódź`→`odz` | RED |

**Self-check:** 0 vacuous tests; ASCII guards are intentionally green (regression armor), all fold/diacritic assertions are RED.

### RED verification (measured)
- server: `12 failed, 22 passed` (`SIDEQUEST_DATABASE_URL` set)
- daemon: `7 failed, 5 passed`
- orchestrator: `5 failed, 4 passed`

**Handoff:** To Dev (Inigo). Implement the shared NFKD-fold helper (stdlib `unicodedata`), re-point all four call sites (server ×2, daemon, render_common), delete the duplicated rule, and document the canonical decision + the distinct-from-evropi-incident note (AC4) in the shared helper's docstring. Keep per-surface separators. Make the helper importable so Story 84-7 can reuse it.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/server/slug_fold.py` (NEW) — `fold_to_ascii` shared NFKD core + canonical-decision/AC4 docstring.
- `sidequest-server/sidequest/server/utils.py` — `slugify_player_name` folds first.
- `sidequest-server/sidequest/server/reference_slug.py` — `slugify` folds first.
- `sidequest-server/tests/server/test_101_8_diacritic_resolution.py` — POI span attr key fix (`reference.slug`).
- `sidequest-server/tests/server/test_npc_portrait_resolution.py` — inline render-rule fixture updated to fold + diacritic case (strengthened 404-guard).
- `sidequest-daemon/sidequest_daemon/media/catalogs.py` — `_slugify_name` folds (own `_fold_to_ascii`, mirrors contract).
- `scripts/render_common.py` — `slugify` folds + drops only non-ASCII survivors (AC3-preserving).

**Tests:**
- 101-8 targets GREEN: server `34 passed`; daemon slug `+ test_catalogs` GREEN (full daemon `443 passed`); orchestrator `test_101_8_render_common_slug` `9 passed`.
- Regression sweeps: server full `10136 passed, 7 failed` — 1 was mine (the slug-contract test, now fixed) + 6 pre-existing unrelated (verified: none import slug/render modules). Daemon full `443 passed`. Orchestrator `scripts/tests` `145 passed, 41 failed` — all pre-existing `playtest_messages` refactor failures, none touch render_common/slug.
- Ruff: lint clean; format applied to daemon + orchestrator files.

**Branches (pushed):**
- `sidequest-server` `feat/101-8-unify-slug-derivation`
- `sidequest-daemon` `feat/101-8-unify-slug-derivation`
- orchestrator `feat/101-8-unify-slug-derivation` (base=main)

**ACs:** AC1 ✓ (shared fold core, decision documented), AC2 ✓ (diacritic NPC+POI OTEL wiring), AC3 ✓ (ASCII unchanged + diacritic render-key==consumer-key), AC4 ✓ (distinct-from-evropi note in slug_fold docstring).

**Handoff:** To Westley (Reviewer). Note the 3-repo PR set (server+daemon→develop, orchestrator→main) and the documented residual `&`-punctuation divergence (out of scope).

## Sm Assessment

**Story:** 101-8 — Unify slug derivation across render/portrait/reference surfaces (3pt, p2, tdd, repos: server + daemon).

**Disposition:** Ready for RED. Clean — no stale session/archive, branches created in both subrepos off develop, both context docs present.

**Routing:** Phased TDD → Fezzik (TEA) writes the failing suite, then Inigo (Dev) GREEN, Westley (Reviewer), back to me for finish.

**Load-bearing notes for TEA — read the real YAML, there are FOUR ACs (setup notes above paraphrase 3):**
1. One shared slug fn is the single source of truth; all call sites import it, duplicates deleted. Canonical rule must be chosen DELIBERATELY and documented (likely daemon/asset drop-non-ASCII rule 2 since it names R2 files, OR an explicit transliteration step) — a documented decision, not an assumed default.
2. Wiring test = OTEL span assertion (`reference_portrait_not_found_span` / `reference_portrait_resolved_span` + the POI analog) or fixture behavior test. NOT source-text grep, per server CLAUDE.md.
3. Regression: ASCII names produce identical slugs to today (no behavior change); at least one diacritic case verified end-to-end (render-key == consumer-key).
4. Explicitly note in the implementation this is DISTINCT from the evropi stale-r2_manifest.json blank-portrait incident (fixed separately) — must not be conflated.

**Two open design decisions (logged as deviations above), the implementer's to resolve and document:**
- Whether `scripts/render_common.py` (rule 1, ORCHESTRATOR repo) must import the unified fn. If yes, add orchestrator to Repos: (authoritative) and create its branch/PR per the deviation protocol. If no, document the boundary.
- Which of the three rules becomes canonical (or a new transliteration step). This is the heart of AC1.

**Three rules in conflict on non-ASCII** ("Srárný Fyzioloniązka"): render_common (keeps non-ASCII) → `srárný_...`; slugify_player_name/daemon (drops non-ASCII) → `srrn_...`; reference_slug (hyphenates) → `sr-rn-...`. The POI/map surface uses the hyphenate rule while assets render under another → silent 404. Diacritic-heavy worlds (evropi, coyote_star) are the exposure.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 6 pre-existing (unrelated) | confirmed 0, dismissed 6 (pre-existing/unrelated, none import slug/render modules), deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents` settings — I performed those domains' analysis myself below)
**Total findings:** 1 confirmed (LOW doc mismatch, self-found), 6 dismissed (pre-existing/unrelated), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Because 8 of 9 review subagents are disabled via settings, I performed the edge/silent-failure/test/doc/type/security/simplifier/rule analysis directly on the diff.

### Observations
- [VERIFIED] `fold_to_ascii` is the single non-ASCII core both server surfaces import — `utils.py:3` + `reference_slug.py:18` both `from sidequest.server.slug_fold import fold_to_ascii`; each applies it before its own separator step. Satisfies AC1's "single source of truth" at the only altitude AC3 permits.
- [VERIFIED] ASCII output unchanged — `test_slugify_player_name_ascii_unchanged` / `test_reference_slugify_ascii_unchanged` pin MEASURED current values (`cosh__run`, `historyyaml`); `fold_to_ascii` is a provable no-op on ASCII (NFKD of ASCII is identity, no combining marks). AC3 ✓.
- [VERIFIED] AC2 wiring is behavioral, not source-grep — `test_101_8_diacritic_resolution.py` drives the real `build_cast_section`/`build_poi_section` and asserts `reference_portrait_resolved` / `reference_poi_image_resolved` spans fire with the folded slug (and `*_not_found` does not). Complies with server CLAUDE.md "No Source-Text Wiring Tests".
- [VERIFIED] cross-repo anti-drift — golden vector `"Srárný Fyzioloniązka"` asserted identical (`srarny_…`) in server, daemon, and orchestrator suites + `test_server_slug_equals_render_script_slug` (now folds + diacritic case). A drift on any surface fails a test.
- [VERIFIED] AC4 — the distinct-from-evropi-r2_manifest note lives in `slug_fold.py` docstring.
- [VERIFIED] No silent fallback — `fold_to_ascii` is deterministic, raises nothing, no try/except, no default path. Consistent with "No Silent Fallbacks".
- [VERIFIED] NFKD limitation handled honestly — non-decomposing letters (ł) fall through and are dropped by each surface's filter; pinned + documented (`test_nfkd_nondecomposing_letter_limitation_is_documented`, `Łódź`→`odz`), consistent on render and consumer sides.
- [LOW][DOC] `scripts/render_common.py:slugify` docstring says the trailing drop is `[^a-z0-9_-]`, but the code is `re.sub(r"[^\x00-\x7f]", "", slug)` (non-ASCII-only). Misleading — a maintainer would think ASCII punctuation is stripped. Non-blocking; recommend a one-line docstring correction. (Captured as a delivery finding.)
- [LOW][SIMPLE] the daemon diff carries 2 incidental `ruff format` reflows (a log-message string join, a return wrap) outside the slug change. Format-only, harmless; noted for transparency.

### Devil's Advocate
Could this break? The most dangerous class here is **durable R2 key churn**: changing the slug rule re-keys every diacritic-named asset. A maintainer might assume existing R2 files resolve — they won't until re-rendered. But that is the *explicit, ratified* intent (diacritic worlds get re-rendered; AC accepts it), the daemon writes under the new rule, and the consumer reads under the same rule, so new renders are self-consistent. A confused author could be surprised that `Łódź`→`odz` (lossy) rather than `lodz`; this is documented in three places and pinned by a test, so it cannot regress silently. A malicious input — control chars, RTL marks, zero-width joiners — flows through `unicodedata.normalize` then the `[^a-z0-9…]` / `[^\x00-\x7f]` filters, which strip them; no injection surface (slugs key filesystem/R2 paths, and the filters guarantee `[a-z0-9_-]`-only on the consumer side; render_common keeps its historical ASCII punctuation set, which was already the case). A huge input is O(n) with no backtracking (NFKD + generator + linear regex) — no catastrophic-backtrack risk (the very risk server CLAUDE.md warns about for source-text regexes is absent here). Empty string → empty slug on all surfaces (pinned). Whitespace-only → empty. The one genuine wart — a name starting with a non-decomposing non-ASCII letter yields a leading `_` (`"Ł Foo"`→`_foo`) because render_common's non-ASCII drop runs after `strip("_-")` — but the consumer produces the identical `_foo`, so the render-key == consumer-key contract still holds; cosmetic only. Conclusion: no Critical/High. The only real defect is the LOW docstring inaccuracy.

### Rule Compliance (server CLAUDE.md + SOUL.md, applicable rules)
| Rule | Applies to | Verdict |
|------|-----------|---------|
| No Source-Text Wiring Tests | `test_101_8_diacritic_resolution.py` | ✓ uses OTEL spans + real builders |
| Every suite needs a wiring test | all three suites | ✓ diacritic end-to-end via real projection / catalog paths |
| No Silent Fallbacks | `fold_to_ascii`, all 4 surface fns | ✓ deterministic, no fallback path |
| No Stubbing | new `slug_fold.py` | ✓ real impl, has non-test consumers (utils, reference_slug) |
| Meaningful assertions | all new tests | ✓ concrete values / specific span slugs |
| OTEL on subsystem decisions | resolution path | ✓ reuses existing portrait/POI resolved/not_found spans |

**Data flow traced:** a diacritic NPC name → `cast_portrait_slug` → `slugify_player_name` → `fold_to_ascii` (NFKD) → `srarny_fyzioloniazka` → gated against `portrait_on_r2_slugs` → `reference_portrait_resolved` span + resolved URL. Render side (daemon `_slugify_name` / `render_common.slugify`) folds to the SAME key → no 404. Safe.

**Handoff:** To Vizzini (SM) for finish-story. Note: THREE PRs required — server + daemon → develop, orchestrator → main. One non-blocking LOW (render_common docstring) recommended for a quick follow-up fix.

## Delivery Findings (Reviewer)
See the `### Reviewer (code review)` entries appended in the Delivery Findings section above.