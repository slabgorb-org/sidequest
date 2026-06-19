---
story_id: "151-6"
jira_key: ""
epic: "151"
workflow: "tdd"
---
# Story 151-6: [NARRATOR] Shrink output_only.md to prose + private_segments brief; add perception-firewall guard test (ADR-150 step 5)

## Story Details
- **ID:** 151-6
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** 151-5 (merged to server develop)

## Workflow Tracking
**Workflow:** tdd
**Phase:** review
**Phase Started:** 2026-06-19T09:34:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T08:17:49Z | 2026-06-19T08:21:16Z | 3m 27s |
| red | 2026-06-19T08:21:16Z | 2026-06-19T08:37:02Z | 15m 46s |
| green | 2026-06-19T08:37:02Z | 2026-06-19T09:34:30Z | 57m 28s |
| review | 2026-06-19T09:34:30Z | - | - |

## Sm Assessment

**Story 151-6** — ADR-150 step 5: shrink `output_only.md` to a prose + perception-firewall + `private_segments` brief, and add a permanent perception-firewall guard test.

**Readiness:** Dependency chain satisfied — 151-5 merged to server `develop` (confirmed via pull; it already trimmed `output_only.md` by ~70 lines in the sidecar cutover). 151-3/151-4 likewise complete. All bucket-B and `action_rewrite` fields are off the narrator hot path, so the shrink is no longer premature. Per the context Assumptions, `private_segments` is the sole remaining sidecar-owned field after the cutovers — and it **stays narrator-inline** (generation-entangled, ADR-105 MOVE-not-COPY). Do not move it to the extractor.

**Setup state:** Session + context (`sprint/context/context-story-151-6.md`, 5 ACs) in place. Feature branch `feat/151-6-shrink-output-only-firewall-guard` created off `develop` and checked out in `sidequest-server` (0 commits ahead — clean start). Server-only story; base branch is `develop`. Merge gate clear (no open PRs). Jira not enabled — skipped.

**Routing:** tdd (phased) → next phase **red** (TEA). The load-bearing test is the perception-firewall guard: a turn carrying single-PC perception must emit it **only** in `private_segments` and the test must fail on ANY trace of it in PART 1 (label, summary, or ordinary narration). This is the regression tripwire for ADR-105 — write it as non-negotiable.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** n/a

**Test Files:**
- `sidequest-server/tests/agents/test_151_6_output_only_shrink_firewall_guard.py` — 10 tests across all 5 ACs (red `a5f1b438`; consolidated + extended `6a09130f`; marker-guard aligned to Architect `724dca8a`).

> **Consolidation note (TEA, 2026-06-19 — "take the best" directive):** two parallel
> TEA red efforts existed on this branch — this SDK-driven file (`a5f1b438`) and a
> second `tests/server/test_151_6_output_only_shrink_firewall.py` (24 tests). They
> were consolidated into THIS file: it has the stronger end-to-end wiring (AC2
> cache-ride + AC4 routing drive the real `run_narration_turn`), and the duplicate's
> one genuine edge — a *directive* AC1 test pinning the specific recap header to
> remove (a size ceiling doesn't say WHAT to cut) plus a retired-field regression
> sweep — was grafted in (`6a09130f`). The duplicate file was removed. Implementation
> (`output_only.md` shrink) was NOT started — confirmed: only test files changed on
> the branch; `output_only.md` untouched.
>
> The grafted marker guard was then **narrowed (`724dca8a`) to match the green-phase
> Architect decision** (below): it asserts ONLY the 8-category `TOOL-OWNED MECHANICS`
> recap is removed — NOT that the `NATIVE TOOLS` opener is removed (the Architect
> keeps it to preserve 151-1's marker). This **resolves** the 151-1 coupling
> Delivery Finding: 151-1's `OUTPUT_ONLY_MARKER` is preserved by design, so 151-1
> needs no change.

**Tests Written:** 10 tests covering 5 ACs (2 RED shrink drivers + 8 firewall/cache/routing/retention/byte-stability tripwires).
**Status:** RED — `2 failed, 8 passed` (verified via testing-runner, `-n0`, no collection errors).

The two RED tests are the behavior-changing deliverable (shrink + recap removal); the rest are the permanent guards the story exists to codify (see Design Deviations).

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 shrink (ceiling) | `test_output_only_is_a_short_brief` | **RED** (7891 ≥ 5000 chars) |
| AC1 shrink (markers) | `test_output_only_drops_tool_owned_recording_manual` | **RED** (TOOL-OWNED MECHANICS recap still present; NATIVE TOOLS opener stays) |
| AC1 retired-fields | `test_output_only_omits_all_retired_sidecar_fields` | green (must stay) |
| AC1 retention | `test_output_only_brief_retains_firewall_and_private_segments` | green (must stay) |
| AC2 byte-stable | `test_shrunk_output_only_carries_no_per_turn_interpolation` | green tripwire |
| AC2 cached prefix | `test_shrunk_output_contract_rides_cached_system_prefix` | green tripwire |
| AC3 no-sweep guard | `test_private_segments_is_not_a_post_narration_extractor_field` | green tripwire (the non-negotiable one) |
| AC3 only-in-private | `test_single_pc_perception_appears_only_in_private_segments_never_part1` | green tripwire |
| AC3 leak-strip | `test_firewall_strips_leaked_perception_from_part1` | green tripwire |
| AC4 routing | `test_turn_result_carries_private_prose_segments_with_anchor` | green tripwire (end-to-end SDK) |

### Rule Coverage

Language: Python. The `.pennyfarthing/gates/lang-review/python.md` checklist targets the *changed production `.py` files*. 151-6's production change is a **markdown prompt shrink** (`output_only.md`) — no new/changed production Python — so checks #1–#5, #7–#12 have no applicable production surface. The one rule that governs my own deliverable is #6 (test quality):

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality — meaningful assertions, no vacuous truthy checks | all 8 tests (every assertion checks a specific value/membership, not bare truthiness) | passing |
| #6 test quality — no source-text wiring tests (CLAUDE.md) | firewall/routing guards drive real `extract_structured_from_response` / `run_narration_turn` and interrogate the real `SidecarExtraction` model — no `getsource`/`read_text` grep | passing |
| #6 test quality — correct mock target | no mocks used; real production paths + the shared `FakeAnthropicSdkClient` scripted double (151-1 pattern) | passing |

**Rules checked:** 1 of 13 lang-review rules has applicable surface (the rest target production `.py` Dev is not adding); covered.
**Self-check:** 1 near-vacuous assertion found and FIXED before commit — the original byte-stability test's convoluted boolean (always true because the file contains `{}`) was replaced with a `re.search(r"\{[A-Za-z_]\w*\}")` named-placeholder detector (a real, non-vacuous check).

**Handoff:** To Dev (Hephaestus the Smith) for the shrink — make `test_output_only_is_a_short_brief` green by cutting the TOOL-OWNED MECHANICS recap from `output_only.md` down to the prose + firewall + `private_segments` brief, keeping the four retained tokens and (per the Delivery Finding) a sentinel 151-1 still recognizes. Do NOT move `private_segments` to the extractor — the no-sweep guard will catch it.

## Architect Decision (green-phase consult)

**Trigger:** Dev (Hephaestus) surfaced a conflict in the green phase — AC1's shrink-to-<5000-chars collides with (a) ADR-150 §non-goal ("8 tool-owned categories out of scope"), (b) `test_50_24` pinning the tool enumeration as load-bearing dice anti-fabrication coverage, (c) `test_61_9`'s `begin_confrontation` sentinel, and (d) ADR-111 (migrate tool guidance → tool descriptions) being **deferred**. Concern: removing the enumeration could strand the live narrator's when-to-call guidance.

**Verdict: NOT a blocker. The shrink proceeds. The conflict is structural test-coupling, not a real regression.**

**Decisive findings (verified):**
1. The per-tool `description=` strings **already carry adequate "when to use" cues** for every tool the narrator sees each turn via the ADR-102 tool defs — `roll_dice` ("Use whenever a check, save, or damage roll is needed"), `apply_world_patch` ("prefer a typed tool when one exists"), `advance_confrontation` ("Use during structured confrontations (combat, chase, trial, poker, debate)"), `apply_status`, `tick_tropes`, etc. The 8-category enumeration in `output_only.md` is **redundant** for when-to-call.
2. ADR-111's "guardrails live in the tool description" pattern is **already partially live** — `test_57_4::test_apply_world_patch_tool_description_carries_location_guardrail` proves the location guardrail migrated into `apply_world_patch.description`. Removing the enumeration is consistent with the established direction, not a leap.
3. The **one genuinely-additive** piece NOT in any tool description is the **anti-fabrication rule** (+ player-vs-NPC dice routing). ADR-150 §non-goal explicitly preserves `roll_dice` anti-fabrication; `test_50_24` guards it. It MUST survive — relocated into the PART 1 prose-honesty clause (it *is* part of "write the prose").
4. `test_50_24` / `test_61_9` are coupled to the **old enumerated layout**; their coverage *concerns* stay valid, their *structural assumptions* are obsolete under ADR-150 step 5.

**No-Silent-Fallbacks check:** no live guidance is lost — when-to-call lives in the tool descriptions (verified adequate); anti-fabrication is explicitly preserved in the brief. Cleared.

**Implementation guidance to Dev:**
1. **Rewrite `output_only.md`** to the brief, < 5000 chars, keeping:
   - Opening framing **including the literal "You are running with NATIVE TOOLS."** (preserves 151-1 `OUTPUT_ONLY_MARKER`).
   - A 1–2 sentence pointer: most state is recorded by CALLING native tools (each tool's own description says when); a mechanic narrated without its tool is LOST. (Compact — NOT the 8-category recap.)
   - PART 1 prose instruction (location header).
   - **Compact anti-fabrication clause** (MUST/MANDATORY-grade): never write a roll/check/save/contest/damage **number** unless a tool produced it THIS turn (the worst lie); player uncertain actions are engine-resolved (defer to the returned face, never pre-write the tier); `roll_dice` is the private NPC/background path. Must still contain a MUST/MANDATORY token, an anti-fabrication anchor, the trigger words (check/save/damage), and NO self-gating loophole (`test_50_24`).
   - PART 2 game_patch + `private_segments` spec + PERCEPTION FIREWALL (keep ~verbatim — load-bearing) + always-emit `{}`.
   - Retain tokens for TEA's guard: `private_segments`, `anchor_pc`, `firewall`, `PART 1`/`prose`.
2. **Update `test_50_24`** — its `_dice_section()` slices "7. DICE RESOLUTION"→"8. SCENARIO-CLUE"; those numbered headers are gone post-shrink. Re-anchor the slice to the new anti-fabrication clause (or assert whole-doc now that sibling MUST-language is removed, so it is no longer vacuous). **Preserve all four concern-assertions** (MUST/MANDATORY, no loophole, anti-fab anchor, trigger enumeration). Retire/adapt `test_other_tool_categories_keep_mandatory_language` — its `apply_status`/location/`tick_tropes` anchors ARE the enumeration ADR-150 step 5 removes; the "don't soften sibling sections" purpose no longer applies (no sibling sections remain). Coverage preserved on the new structure.
3. **Update `test_61_9`** (lines ~205, ~275) — re-point the `begin_confrontation` sentinel (a *retired* tool, brittle) to a shrink-stable SDK-prose discriminator, e.g. `private_segments` or the `NATIVE TOOLS` framing. Intent (NARRATOR_OUTPUT_ONLY is the tool-use prose, not legacy full-sidecar prose) preserved.
4. **`test_57_4`** — no change (it expects guardrails absent from output_only.md and present in the tool description; both unaffected).
5. **Log the test edits as Dev deviations** (6-field format) — spec-driven, coverage-preserving test modernizations under ADR-150 step 5.

**Scope boundary (note for reviewer):** the full ADR-111 consolidation (ALL when-to-call cues into descriptions; the §non-goal Phase-2 tool-category *extraction*) remains future work and is NOT a prerequisite here — 151-6 removes redundant re-explanation only.

**Resolution category:** Option A (update tests to the better structure the implementation reveals), coverage preserved. Handing back to Dev to implement in the green phase.

## Dev Assessment

**Story 151-6 — COMPLETE (green phase) via Option A (shrink-in-place), per explicit user directive.**

**State on resume (post context-clear):** `output_only.md` was already shrunk in the working tree (uncommitted) by a prior pre-clear Dev session — Option A: the 8-category `TOOL-OWNED MECHANICS` recap was collapsed into compact inline bullets, PART 2 was rewritten to the single `private_segments` field + firewall, and `tests/agents/test_61_9_sdk_commitment.py` re-pointed its sentinel `begin_confrontation` → `advance_confrontation`. The loaded brief is < 5000 chars (4866). The authoritative `test_151_6_output_only_shrink_firewall_guard.py` (10 tests) and every coupled test were **already GREEN**.

**Decision:** The green-phase Architect Decision and the resume handoff both scoped Option B (migrate the tool-category rules into per-tool `description=` fields; true ~2800-char brief; re-point ~5 coupled tests). On resume I surfaced the discrepancy — the handoff's premise ("`output_only.md` UNTOUCHED, 7891 chars") was false; a prior session had already landed Option A and all tests were green. The user directed: **"Use the existing stuff please"** → ship the already-green Option A; **defer the ADR-111 tool-description migration** to a follow-up story.

**Verification (evidence):**
- `test_151_6_output_only_shrink_firewall_guard.py`: **10 passed** (`-n0`).
- Full `tests/agents` + `tests/magic`: **2239 passed, 54 skipped, 0 failed** (35s).
- `ruff check` + `ruff format --check` clean on the one touched `.py` (`test_61_9`); `output_only.md` is markdown (no ruff).
- Brief retains the load-bearing content: `NATIVE TOOLS` opener (151-1 `OUTPUT_ONLY_MARKER`), PART 1/PART 2 framing, the anti-fabrication clause (MUST/MANDATORY + check/save/damage triggers + no self-gating), `private_segments` + `anchor_pc`, the PERCEPTION FIREWALL rule (~verbatim), always-emit `{}`. No `{identifier}` str.format placeholders. `private_segments` is **not** in `BUCKET_B_FIELDS`/`SidecarExtraction` — the no-sweep guard holds.

**Production diff (3 files):** `sidequest/agents/narrator_prompts/output_only.md` (shrink) + `tests/agents/test_50_24_dice_contract_parity.py` (re-anchor the `_dice_section()` slice to the new `- DICE —` → `PART 2` bullet structure) + `tests/agents/test_61_9_sdk_commitment.py` (sentinel re-point). No other files touched. (`test_50_24` initially read clean in `git status` due to a git stat-cache artifact; its content already carried the prior session's re-anchor — that is why the coupled-test run found it green using the new anchors.)

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The 151-6 shrink may delete the sentence "You are running with NATIVE TOOLS." — the opening framing line of `output_only.md` — which is exactly the `OUTPUT_ONLY_MARKER` that `tests/agents/test_151_1_output_only_cache_promotion.py` greps for in two tests (`test_output_contract_rides_cached_system_prefix`, `test_output_contract_absent_from_per_turn_user_message`). If Dev removes/rewrites that opening line, those 151-1 tests go RED and break AC5 (full suite green). Affects `tests/agents/test_151_1_output_only_cache_promotion.py` (Dev must EITHER preserve a sentence 151-1 still recognizes OR update `OUTPUT_ONLY_MARKER` to a shrink-stable sentinel — my new cache test deliberately anchors on `private_segments`, which AC1 retention keeps). *Found by TEA during test design.*
- **Improvement** (non-blocking): `tests/agents/test_adr105_b3_private_segments.py::test_both_assemblers_carry_private_prose_segments` proves the firewall-field carry-through via `inspect.getsource` source-text grep — the pattern CLAUDE.md *No Source-Text Wiring Tests* forbids (passes on a literal present even if wiring is broken; fails on harmless refactor). My `test_turn_result_carries_private_prose_segments_with_anchor` is the behavioral replacement (drives a real turn, asserts the result field). Affects `tests/agents/test_adr105_b3_private_segments.py` (retire the source-grep test in a follow-up; out of 151-6 scope). *Found by TEA during test design.*

### Dev (green phase)
- **Gap** (non-blocking): the resume handoff described `output_only.md` as "UNTOUCHED (7891 chars / 146 lines)", but the working tree already carried an uncommitted Option-A shrink (the brief at < 5000 chars) plus the `test_61_9` sentinel re-point from a prior pre-clear Dev session — and all 10 authoritative + all coupled tests were already green. Handoff premises can lag working-tree state across a context clear; verify `git status` / `git diff develop` on resume before trusting a "file untouched" claim. *Found by Dev on resume.*
- **Improvement** (non-blocking): the ADR-111 tool-description migration (the Option-B work the Architect Decision + handoff scoped) is **deferred, not done**. `output_only.md` still carries the eight tool-category rules inline (~4.9k chars vs a ~2.8k true brief). A follow-up story should MOVE them into the per-tool `description=` fields — severities/scene-end cadence → `apply_status.py`, beat tiers (CritFail…CritSuccess) → `advance_encounter_beat.py`, dice anti-fab + NPC-private routing → `roll_dice.py`, location/time → `apply_world_patch.py`, magic → `apply_spell_effect.py` — and re-point `test_narrator_prompt.py` / `test_50_24_dice_contract_parity.py` / `test_61_12_output_format_compaction.py` to the new homes. `test_61_12` forbids silent omission: migrate + re-assert, never delete. *Found by Dev.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC1 encoded as a brevity ceiling, not an exact-content equality**
  - Spec source: context-story-151-6.md, AC1
  - Spec text: "`output_only.md` contains only the prose + perception-firewall + `private_segments` brief; the bucket-B / `action_rewrite` recording instructions are gone."
  - Implementation: `test_output_only_is_a_short_brief` asserts `len(NARRATOR_OUTPUT_ONLY) < 5000` chars (current 7891), plus a positive retention test for the `private_segments`/`anchor_pc`/firewall/PART-1 tokens — rather than asserting the exact final wording.
  - Rationale: the bucket-B and `action_rewrite` field instructions are ALREADY absent on this branch (verified via grep — 151-3/4/5 removed them), so "instructions are gone" is already satisfied and offers no RED signal. The only behavior-changing, RED-able deliverable left is total size (cutting the ~92-line TOOL-OWNED MECHANICS recap). A content-equality assertion would dictate Dev's prose; a brevity ceiling encodes the AC without over-prescribing. Ceiling sits ~2.2k above a faithful brief (~2.8k) and ~2.9k below the current manual.
  - Severity: minor
  - Forward impact: Dev has latitude on exact wording provided the brief lands < 5000 chars and retains the four required tokens.
- **AC3 "fails on ANY trace … (label, summary, or ordinary narration)" — backstop covers label + near-duplicate; the prompt covers terse paraphrase**
  - Spec source: context-story-151-6.md, AC3
  - Spec text: "the guard test fails on ANY trace of it in PART 1 (label, summary, or ordinary narration)."
  - Implementation: the guard drives the real `extract_structured_from_response` and asserts (a) a correctly-partitioned turn leaves ZERO trace in PART 1, and (b) the two leak forms the mechanical backstop deterministically catches — a self-labelled aside and an ordinary-narration near-duplicate (Jaccard ≥ 0.5) — are stripped. It does NOT assert the backstop catches a low-token-overlap *paraphrased* summary.
  - Rationale: ADR-150 calls `_scrub_public_prose` "a mechanical backstop, not the primary mechanism"; a deterministic token-overlap scrub cannot catch an arbitrary terse paraphrase without semantic analysis the design explicitly declines. That leak form is defended by the narrator's retained MOVE-not-COPY prompt rule (covered by the AC1 retention test), not the scrub. Demanding the scrub catch it would be an un-meetable RED.
  - Severity: minor
  - Forward impact: the "summary" leak form's defence is the retained firewall prompt rule, not the extractor scrub.
- **Only AC1 is RED; AC2/AC3/AC4 are green-at-write-time regression tripwires**
  - Spec source: story title + context-story-151-6.md (AC3 "add a permanent guard"); ADR-150 §Perception-firewall guard
  - Spec text: "add a permanent perception-firewall guard test … so no future optimization sweeps `private_segments` into the extractor."
  - Implementation: 1 genuinely-failing test (the shrink); 7 tests that pass at write-time and codify already-correct firewall/cache/routing behavior as permanent tripwires.
  - Rationale: the firewall path already works (existing ADR-105 B3 suite is green), so a "codify the tripwire + shrink the file" story has green guard tests by construction — RED would require breaking working production code. This is flagged so the Reviewer is not surprised that 7 of 8 tests pass in RED phase.
  - Severity: minor
  - Forward impact: none — Dev's only behavior change is the AC1 shrink.
- **Consolidated two parallel TEA red files into one; added a directive marker driver (now 2 RED, not 1)**
  - Spec source: user "take the best and proceed" directive (2026-06-19) + context-story-151-6.md AC1
  - Spec text: AC1 "`output_only.md` contains only the prose + perception-firewall + `private_segments` brief".
  - Implementation: a second TEA red file (`tests/server/test_151_6_output_only_shrink_firewall.py`, 24 tests) existed in parallel; it was removed and its one genuine edge — a directive test asserting the `TOOL-OWNED MECHANICS` recap header is removed (vs. the surviving file's size-ceiling-only AC1 RED) plus a retired-field sweep — grafted into the kept SDK-driven file (`6a09130f`). The marker test was then narrowed (`724dca8a`) to assert ONLY the recap header is gone, matching the green-phase Architect decision (NATIVE TOOLS opener stays). Net: AC1 now has 2 RED drivers (ceiling + recap removal).
  - Rationale: a pure byte-ceiling lets a rewrite "shrink" without removing the right structure; the directive marker test pins the 8-category recap removal the Architect's plan calls for. Narrowing to one marker avoids contradicting the Architect's NATIVE-TOOLS retention (which preserves 151-1's marker).
  - Severity: minor
  - Forward impact: the earlier "Only AC1 is RED (1 failing)" deviation is updated — 2 tests now fail, both AC1. The 151-1 coupling Delivery Finding is resolved (NATIVE TOOLS opener retained by Architect ruling).

### Dev (green phase)
- **Shipped AC1 as Option A (shrink-in-place), not the Architect/handoff's Option B (migrate to tool descriptions)**
  - Spec source: resume handoff "THE DECISION (2026-06-19): Option B — Full migrate to tool descriptions"; this session's "## Architect Decision" (green-phase consult)
  - Spec text: "Shrink output_only.md to a true ~2800-char brief. MOVE the tool-category RULES … into the per-tool `description=` fields … Update the ~5 coupled test files to assert on the tool descriptions instead."
  - Implementation: shipped the prior pre-clear session's already-green Option-A shrink — `output_only.md` < 5000 chars with the `TOOL-OWNED MECHANICS` recap removed but the tool-category guidance retained as compact **inline** bullets. The rules were NOT relocated into tool `description=` fields; the coupled tests were NOT re-pointed (they pass unchanged because the asserted tokens remain inline in `NARRATOR_OUTPUT_ONLY`).
  - Rationale: on resume the file was already shrunk and ALL 10 authoritative + all coupled tests were green; every 151-6 AC is satisfied by Option A (file < 5000; permanent firewall/no-sweep guard; cache-ride + routing tripwires intact). ADR-111 is marked *deferred* and the handoff said "keep scope to what 151-6 needs." I surfaced the handoff's stale premise (file untouched / 7891 chars) to the user, who directed "Use the existing stuff please" → commit Option A, defer the migration. No coverage was gutted — the enumeration's rules remain literally present (strictly lower narrator-regression risk than relocating them).
  - Severity: moderate (chosen architecture differs from the Architect/handoff plan; coverage preserved and every AC met)
  - Forward impact: the ADR-111 tool-description migration remains a clean follow-up (logged as a Dev Delivery Finding). Until then the coupled tests assert the tool-category tokens inline in `NARRATOR_OUTPUT_ONLY`; a future migration MUST re-point them (test_61_12 forbids silent omission).
- **`test_61_9` SDK-prose sentinel re-pointed `begin_confrontation` → `advance_confrontation`**
  - Spec source: this session's "## Architect Decision" item 3; handoff coupled-test list
  - Spec text: "re-point the `begin_confrontation` sentinel (a *retired* tool, brittle) to a shrink-stable SDK-prose discriminator … intent (NARRATOR_OUTPUT_ONLY is the tool-use prose, not legacy prose) preserved."
  - Implementation: the two `TestConstantAndFileRename` / `TestBuildOutputFormatSignature` assertions in `test_61_9_sdk_commitment.py` now check `advance_confrontation` (a live tool the brief still routes to) instead of `begin_confrontation` (retired in 59-4 / ADR-113, present only as a "was retired" aside in the pre-shrink recap the shrink removed). (Authored by the prior pre-clear session; logged here as it is part of the committed diff.)
  - Rationale: the shrink deleted the recap that mentioned `begin_confrontation`, so the sentinel had to anchor on a token the brief still contains; the test's discriminating purpose (SDK tool-use prose vs. legacy full-sidecar prose) is preserved.
  - Severity: minor
  - Forward impact: none — coverage preserved on a stable, live-tool token.
- **`test_50_24` `_dice_section()` re-anchored off the removed numbered headers**
  - Spec source: this session's "## Architect Decision" item 2; handoff coupled-test list
  - Spec text: "its `_dice_section()` slices '7. DICE RESOLUTION' → '8. SCENARIO-CLUE'; those numbered headers are gone post-shrink. Re-anchor the slice to the new anti-fabrication clause … Preserve all four concern-assertions (MUST/MANDATORY, no loophole, anti-fab anchor, trigger enumeration)."
  - Implementation: `_dice_section()` now slices `text.find("- DICE —")` → `text.find("PART 2", start)` — the dice bullet + the standalone `ANTI-FABRICATION` paragraph that ends at the PART 2 boundary — instead of the deleted `7.`/`8.` numbered headers. All four dice anti-fab assertions (MUST/MANDATORY token, no self-gating loophole, anti-fabrication anchor, the `check`/`save`/`damage` trigger words) and `test_other_tool_categories_keep_mandatory_language` (apply_status/location/tick_tropes anchors, still inline under Option A) pass unchanged. (Authored by the prior pre-clear session; logged here as it is part of the committed diff.)
  - Rationale: the shrink removed the numbered-category headers the old slice depended on; re-anchoring to the surviving `- DICE —` bullet + anti-fab paragraph keeps the MUST assertion meaningful (sliced region, not whole-doc) while preserving every concern.
  - Severity: minor
  - Forward impact: a future ADR-111 migration that moves the dice rule into `roll_dice.description` must move this assertion's home again (and may shrink the anti-fab paragraph to a compact prose clause per ADR-150 §non-goal).