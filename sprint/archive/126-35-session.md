---
story_id: "126-35"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-35: [FATE] On-play significant items don't promote to an invokable aspect/extra

## Story Details
- **ID:** 126-35
- **Jira Key:** (none)
- **Repos:** server
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T00:51:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T00:17:41.970462+00:00 | 2026-06-21T00:20:01Z | 2m 19s |
| red | 2026-06-21T00:20:01Z | 2026-06-21T00:37:02Z | 17m 1s |
| green | 2026-06-21T00:37:02Z | 2026-06-21T00:42:24Z | 5m 22s |
| review | 2026-06-21T00:42:24Z | 2026-06-21T00:51:41Z | 9m 17s |
| finish | 2026-06-21T00:51:41Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Improvement** (non-blocking): The engine + apply-path consumer for narrator `grants_aspect` already shipped (126-21/126-25); story 126-35's real net-new surface is the dormant tool-contract (AC1 only). Affects `sidequest/agents/sidecar_extractor.py` (surface `grants_aspect` on the `SidecarExtraction` items_gained schema + a field description). *Found by TEA during test design.*
- **Conflict** (non-blocking): AC2 calls the promoted aspect a "situation" aspect, but the shipped promoter, the 2026-06-18 spec doc, and the existing green test all mint `kind="character"`; tests pin "character". Affects `sidequest/game/ruleset/fate_item_promotion.py` (do NOT change to "situation" without an explicit Keith/Architect ruling). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The 2026-06-18 spec doc's "no protocol model change" advice is stale post-151-4 — `items_gained` is now sidecar-sourced, not game_patch-sourced; the implemented `WithJsonSchema` schema-only override reconciles AC1's "tool-schema" with "no runtime model change". Affects `docs/superpowers/specs/2026-06-18-significant-items-invokable-fate-aspects-design.md` (note the 151-4 cutover changed the live source). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `grants_aspect` text reaches the client-facing FATE_STATE wire raw (`fate_projection.py:226/251`, `FateAspectEntry(text=a.text)`) — uniform across all aspect kinds and React-escaped at render, but a defense-in-depth `sanitize_player_text` at the LLM→state boundary would harden the now-live narrator-promotion path. Affects `sidequest/game/ruleset/fate_item_promotion.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `grants_aspect` has no runtime type enforcement (the schema documents `string`; the runtime stays `dict[str, Any]`); the consumer coerces via `str(...)` so a non-string degrades gracefully, but an `isinstance` guard or a typed entry model (post-151-x) would be cleaner. Affects `sidequest/agents/sidecar_extractor.py` / `sidequest/server/narration_apply.py:5254`. *Found by Reviewer during code review.*
- **Question** (non-blocking): composing a `grants_aspect` phrase is mildly generative, yet the bucket-B extractor is documented "extractive-only, never invent" — per the 2026-06-20 RENDER-NO-SUBJECT amendment (generative fields → narrator-owned), the Architect may wish to confirm whether grants_aspect belongs narrator-owned (game_patch) rather than extractor-read. Affects `sidequest/agents/sidecar_extractor.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Aspect kind is "character", not "situation" (AC2 wording superseded)**
  - Spec source: context-story-126-35.md, AC2
  - Spec text: "promotes the item to a situation Aspect on the FateSheet that is invokable in a 4dF resolution"
  - Implementation: tests assert `aspect.kind == "character"`, matching the shipped promoter (`sidequest/game/ruleset/fate_item_promotion.py::promote_gained_item` mints `Aspect(kind="character")`), the authoritative spec doc `docs/superpowers/specs/2026-06-18-significant-items-invokable-fate-aspects-design.md` (`kind="character"`), and the existing GREEN unit test `test_fate_item_promotion.py::test_narrator_aspect_mints_one_capped_character_aspect`.
  - Rationale: "character" is a permanent character aspect (a found item that becomes part of the PC); a "situation" aspect is transient/scene-scoped. Measured — code + spec + existing test all say "character". Pinning "situation" would force a regression on shipped, tested code.
  - Severity: minor
  - Forward impact: Dev must NOT change the promoter to mint "situation". If Keith/Architect genuinely wants a situation aspect, that is a separate decision against the shipped promoter — flag it, don't silently implement.

- **Engine half pre-shipped (126-21/25): AC2/AC3/AC4 are green-on-arrival contract guards, not RED drivers**
  - Spec source: context-story-126-35.md, AC2 / AC3 / AC4
  - Spec text: AC2 "Full narrator-set WIRING TEST ... invokable in a 4dF resolution"; AC3 "fate.item_promoted fires with source=narrator"; AC4 "an ad-hoc item granted WITHOUT grants_aspect does NOT promote"
  - Implementation: the promoter (`promote_gained_item`) + the apply-path consumer (`narration_apply.py:5254`) already implement all three, so my AC2/AC3/AC4 tests PASS on arrival; only AC1 (the tool-schema surface) is RED. I wrote the AC2/3/4 tests anyway as end-to-end contract guards — the existing tests do NOT cover the `source="narrator"` span, the 4dF-invoke leg for the narrator path, or the fate-PC-no-flag apply path.
  - Rationale: the story's real net-new surface is the narrator CONTRACT (AC1). Coverage was pinned, not omitted, so a regression while wiring AC1 is caught (CLAUDE.md: every suite needs a wiring test).
  - Severity: minor
  - Forward impact: Dev's work is essentially AC1; the AC2/3/4 guards should stay green throughout.

- **AC1 "prompt-zone instruction" pinned via the schema field description, not a prompt-text assertion**
  - Spec source: context-story-126-35.md, AC1
  - Spec text: "surfaces an OPTIONAL grants_aspect field (tool-schema + prompt-zone instruction)"
  - Implementation: `test_extraction_tool_schema_surfaces_grants_aspect` asserts the `grants_aspect` property exists on an items_gained entry AND carries a non-empty `description` (the instruction the Haiku extractor reads). I did NOT grep `_TOOL_DESCRIPTION`/`_SYSTEM_PROMPT` prose (CLAUDE.md No-Source-Text-Wiring-Tests; the 126-25 AC4 precedent treats prompt prose as not behaviorally testable in isolation).
  - Rationale: surfacing the field with a description in `SidecarExtraction.model_json_schema()` is the behavioral, refactor-stable way to prove the narrator is told the field exists. A `dict[str, Any]` schema gives the extractor no signal, so prose-only would (correctly) leave the test red.
  - Severity: minor
  - Forward impact: Dev must surface `grants_aspect` IN the items_gained item schema (a typed entry submodel with a described optional field), not only in prose. Note the spec's "no protocol model change" advice predates the 151-4 cutover that made the sidecar extractor the live `items_gained` source — it is stale.

### Dev (implementation)

- **grants_aspect surfaced via WithJsonSchema (schema-only); runtime entry stays a dict**
  - Spec source: `docs/superpowers/specs/2026-06-18-...-design.md` (Phase 2) vs context-story-126-35.md, AC1
  - Spec text: spec doc — "add an optional grants_aspect key the narrator may set ... no protocol model change"; AC1 — "surfaces an OPTIONAL grants_aspect field (tool-schema + prompt-zone instruction)"
  - Implementation: annotated `SidecarExtraction.items_gained` as `list[Annotated[dict[str, Any], WithJsonSchema(_ITEMS_GAINED_ITEM_SCHEMA)]]` — the EMITTED tool-schema documents an optional `grants_aspect` (with a description = the instruction the reader sees) while the runtime type stays `dict[str, Any]`. Added a matching sentence to `_TOOL_DESCRIPTION`.
  - Rationale: reconciles both spec sources — AC1's "tool-schema" surface is met (the LLM is told the field exists) WITHOUT a runtime protocol model change, so `merge_sidecar_extraction_transactional` and the apply-path consumer keep reading entries as dicts via `.get(...)`. A bare `dict[str, Any]` schema gives the extractor no signal; a strict typed submodel would break the dict-based consumer and TEA's `test_merge_sidecar_extraction_preserves_grants_aspect` guard.
  - Severity: minor
  - Forward impact: none — entries remain dicts; downstream item handling unchanged. A future bucket-B typing story (151-x) can replace `WithJsonSchema` with a real submodel once the consumer is migrated to models.

### Reviewer (audit)
- **TEA: aspect kind "character" not "situation"** → ✓ ACCEPTED by Reviewer: verified — `fate_item_promotion.py:110` mints `kind="character"`, and the 2026-06-18 spec doc + the existing green `test_narrator_aspect_mints_one_capped_character_aspect` agree. Pinning "situation" would regress shipped code. Sound.
- **TEA: engine pre-shipped; AC2/3/4 are green-on-arrival guards** → ✓ ACCEPTED by Reviewer: verified via preflight (43/43 green). Honest scoping, and the guards satisfy the CLAUDE.md every-suite-needs-a-wiring-test mandate. Sound.
- **TEA: AC1 prompt-instruction pinned via the schema description (not a source grep)** → ✓ ACCEPTED by Reviewer: honors CLAUDE.md No-Source-Text-Wiring-Tests; behavioral and refactor-stable. Sound.
- **Dev: grants_aspect via WithJsonSchema (schema-only); runtime stays dict** → ✓ ACCEPTED by Reviewer: verified by silent-failure-hunter + preflight — schema-only override, runtime validation unchanged, the merge + consumer keep reading dicts. Reconciles AC1's "tool-schema" with no runtime model change. Minimal and correct.
- No additional undocumented deviations found.

## Sm Assessment

**Route:** Fresh server-only story (repos: `server`), workflow `tdd` (phased). No Jira key (skipped — consistent with siblings 126-21/126-25, which also carried no Jira key). No `depends_on`. No stale session or archive for 126-35. Branch `feat/126-35-fate-narrator-grants-aspect` created on `sidequest-server` **develop** (base 6f911b05). → **RED phase, owner TEA (Fezzik).**

**Merge gate:** CLEAR. The 3 in-progress stories (150-3, 150-9, 150-11) are all `[PLAYTEST]` full-stack verify sessions, not code stories — and `gh pr list --state open` returns **zero** PRs across server/ui/content. No blocking non-draft PRs.

**Design call — already RESOLVED (out of band by the Architect, 2026-06-20).** The story's "KEITH DESIGN CALL" is closed → **PATH (c): activate the dormant narrator `grants_aspect` lever** (narrator-authored promotion). The decision, the rejected alternatives, the measured facts, and **4 acceptance criteria** are already written into the story description/AC list and the context doc (`sprint/context/context-story-126-35.md`). TEA writes RED directly against those 4 ACs — do NOT re-open the decision.

**Key seams for TEA (server-only):**
- Consumer ALREADY EXISTS and is tested: `sidequest/server/narration_apply.py:5254` reads `entry.get('grants_aspect')`; promoter `sidequest/game/ruleset/fate_item_promotion.py::promote_gained_item` appends the Aspect; consumption test `tests/server/test_fate_item_promotion_wiring.py::test_narrator_grants_aspect_on_invented_item`.
- Net-new (the RED targets): the narrator item-grant **tool-schema** `grants_aspect` field + **prompt-zone** instruction + OTEL `fate.item_promoted` span with `source=narrator` + a **full narrator-set wiring test** (narrator sets the field → `situation` Aspect on FateSheet → invokable in 4dF).
- **Invariant to pin:** an item granted WITHOUT `grants_aspect` does NOT promote (no engine auto-promotion). `FateSheet` has only `aspects: list[Aspect]` — there is **no `extras` field** (story-title "extra" wording is phantom; target is an Aspect kind `situation`).
- **Doctrine:** preserves ADR-144 (Fate has no equipment economy — "a hat is a hat"). Rejected: (b) engine auto-promotion, (a) pure-document.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Net-new narrator tool-contract surface (AC1) + end-to-end wiring/OTEL/invariant guards (AC2/AC3/AC4).

**Test File:**
- `sidequest-server/tests/server/test_fate_narrator_grants_aspect_wiring.py` — 6 tests covering all 4 ACs.

**Tests Written:** 6 tests covering 4 ACs
**Status:** RED — 1 failed, 5 passed (confirmed via testing-runner, `126-35-tea-red-2`, 3.69s).

The single RED is the genuine net-new behavior; the 5 green are contract guards (the engine half shipped in 126-21/126-25). This is the honest surface area: **Dev's real work is AC1** — surface `grants_aspect` on the live narrator item-grant tool-contract.

| AC | Test | Status |
|----|------|--------|
| AC1 (tool-schema surfaces grants_aspect + instruction) | `test_extraction_tool_schema_surfaces_grants_aspect` | **failing (RED)** |
| AC1/AC4 (field is optional, not required) | `test_grants_aspect_is_optional_not_required` | passing (guard) |
| AC1/AC2 (merge carries the field to apply) | `test_merge_sidecar_extraction_preserves_grants_aspect` | passing (guard) |
| AC2 (full narrator path → projection → +2 in 4dF) | `test_narrator_grants_aspect_full_wiring_to_4df` | passing (guard) |
| AC3 (OTEL fate.item_promoted source=narrator) | `test_narrator_promotion_emits_item_promoted_span_source_narrator` | passing (guard) |
| AC4 (no grants_aspect → no promote, no span) | `test_fate_item_without_grants_aspect_does_not_promote` | passing (guard) |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL principle — every subsystem decision emits a span (CLAUDE.md) | `test_narrator_promotion_emits_item_promoted_span_source_narrator` (asserts `source=narrator`) | passing |
| No Source-Text Wiring Tests (CLAUDE.md) | AC1 pinned via `model_json_schema()` behavior (+ field description), not a prose grep | n/a (followed) |
| Every suite needs a wiring test (CLAUDE.md) | `test_narrator_grants_aspect_full_wiring_to_4df` (drives real `_apply_narration_result_to_snapshot`) | passing |
| No auto-economy invariant (ADR-144 / AC4) | `test_fate_item_without_grants_aspect_does_not_promote` + `test_grants_aspect_is_optional_not_required` | passing |
| Back-link integrity (source_gear == real item id) | `test_narrator_grants_aspect_full_wiring_to_4df` (asserts `aspect.source_gear == item["id"]`) | passing |

**Rules checked:** 5 of 5 applicable checks have test coverage.
**Self-check:** 0 vacuous tests. Every test asserts a concrete value; the optional-field guard is non-vacuous once the field is added (it will then read a real `required` list). One self-introduced test bug (a hand-set item id vs the runtime-minted id) was found via testing-runner and fixed before this assessment.

**Dev guidance (to Inigo Montoya):**
- The ONLY failing test is AC1. Surface an optional `grants_aspect` field on the live narrator item-grant tool-contract — the post-151-4 sidecar `SidecarExtraction.items_gained` entry (`sidequest/agents/sidecar_extractor.py`) — with a `description` that instructs the narrator it MAY mark a *significant* item (narrator-authored, never auto-promote). Keep it OPTIONAL.
- Do NOT touch `promote_gained_item` or the apply-path consumer — they already work (the 5 green guards prove it). Aspect kind stays `"character"` (see deviations — AC2's "situation" wording is superseded).
- Watch the `SidecarExtraction.model_validate` path: if you type the item entry, keep it permissive (the existing `tests/agents/test_sidecar_extractor.py` passes bare `{"name": ...}` dicts — those must still validate).

**Handoff:** To Dev (Inigo Montoya) for implementation (GREEN).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/sidecar_extractor.py` — surfaced an optional, described `grants_aspect` field on the live narrator item-grant tool-schema (`SidecarExtraction.items_gained`) via `WithJsonSchema` (`_ITEMS_GAINED_ITEM_SCHEMA`); added a matching significant-item instruction to `_TOOL_DESCRIPTION`. Runtime entries stay free-form dicts (no protocol model change).

**Tests:** 6/6 story tests passing (GREEN). Blast-radius regression: 43/43 green (story 6, sidecar 24, promotion wiring 3, promoter units 10). `ruff check` + `ruff format --check` clean. Verified via testing-runner `126-35-dev-green`.

**Branch:** `feat/126-35-fate-narrator-grants-aspect` (pushed to origin).

**AC coverage:**
- **AC1** (tool-schema surfaces grants_aspect + instruction) — **DONE**: schema field + non-empty description + `_TOOL_DESCRIPTION` sentence. The RED test (`test_extraction_tool_schema_surfaces_grants_aspect`) is now green.
- **AC2** (full narrator path → projection → +2 in 4dF) — already implemented by the shipped promoter; pinned green by `test_narrator_grants_aspect_full_wiring_to_4df`.
- **AC3** (OTEL `fate.item_promoted` source=narrator) — already implemented; pinned green by `test_narrator_promotion_emits_item_promoted_span_source_narrator`.
- **AC4** (no grants_aspect → no promote; no auto-economy) — already implemented; pinned green by `test_fate_item_without_grants_aspect_does_not_promote`.

**Scope discipline:** `promote_gained_item` and the apply-path consumer were NOT touched (already complete per 126-21/126-25). Aspect kind stays `"character"` per the shipped promoter + spec (AC2's "situation" wording superseded — see TEA + Dev deviations). No engine auto-promotion added; ordinary items stay flavor (ADR-144).

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (43/43 tests green, 0 smells, ruff/format clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — manual pass below |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — manual pass below |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — manual pass below |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — manual pass below |
| 7 | reviewer-security | Yes | findings | 4 (1 med→LOW, 1 med→LOW, 2 low) | confirmed 0 blocking, downgraded 2, dismissed-with-rationale 2 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — manual pass below |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — manual pass below |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed-blocking, 2 confirmed non-blocking (downgraded to LOW with verified rationale), 2 dismissed with rationale

### Security subagent finding triage (verified, not rubber-stamped)
- **F1 (med→LOW): no `sanitize_player_text` at the promoter storage seam.** The subagent's premise — a sibling that sanitizes aspect text *at storage* (`fate_conflict.py:727`) — is a **fabricated reference** (file does not exist). Verified architecture: EVERY aspect-creation site stores text raw (`fate_gear.py:98`, `fate_chargen.py:68-70`, `fate.py:524`, `fate_item_promotion.py:110`); ADR-047 sanitizes ALL aspects at the **projection boundary** (`fate_projection.py:64`, `sanitize_player_text(a.text) for a in sheet.all_aspects()`), which covers the narrator-promoted aspect. The dangerous LLM-prompt-injection sink IS covered. Residual = client-wire raw text, which is uniform across all aspects and React-escaped → LOW defense-in-depth, recorded as a non-blocking finding. Not introduced by this diff.
- **F2 (med→LOW): grants_aspect not runtime-type-enforced.** Verified: the consumer coerces with `str(entry.get("grants_aspect","") or "").strip()` (`narration_apply.py:5254`) → a non-string degrades gracefully (no crash), then sanitized at projection. The schema documents `string`. LOW robustness; the Dev deviation already records the schema-only tradeoff. Recorded as non-blocking.
- **F3 (low): "one aspect" is per-item, not per-turn.** Dismissed-with-rationale: pre-existing promoter design (unchanged here); N distinct items → N aspects is intended, each is one `kind="character"` `free_invokes=0` aspect, and invocation costs a fate point (ADR-144 "TRUE not STRONG"). No unbounded free advantage.
- **F4 (low): `additionalProperties: True`.** Dismissed-with-rationale: intentional and documented (the comment explains `_narrator_item_dict` mints id/category downstream); the subagent itself notes "not currently directly exploitable". Tightening is deferred to post-151-x cutover.

## Reviewer Assessment

**Verdict:** APPROVED

A minimal, correct, well-tested change that activates the dormant narrator `grants_aspect` lever (AC1) by surfacing the field on the live sidecar tool-schema via `WithJsonSchema`, with the runtime entry deliberately left a `dict` so the merge + apply-path consumer are untouched. No Critical/High findings. The one genuinely-dangerous sink (LLM-text re-entering the narrator prompt) is sanitized at the ADR-047 projection boundary — verified.

**Observations (≥5):**
1. `[VERIFIED]` WithJsonSchema is schema-only, runtime type unchanged — evidence: `sidecar_extractor.py:139-141` annotates `list[Annotated[dict[str, Any], WithJsonSchema(...)]]`; the 24 `test_sidecar_extractor.py` tests + `test_merge_sidecar_extraction_preserves_grants_aspect` pass → `model_validate` still accepts bare `{"name": ...}` dicts. Complies with No-Silent-Fallbacks (no silent validation tightening).
2. `[VERIFIED]` grants_aspect survives the live chain — evidence: `merge_sidecar_extraction_transactional` (`narration_apply.py:3800`) does `list(extraction.items_gained)` preserving dict keys; consumer at `narration_apply.py:5254` reads `entry.get("grants_aspect")`. Wiring intact end-to-end.
3. `[VERIFIED]` Prompt-injection escalation covered (ADR-047) — evidence: `fate_projection.py:64` sanitizes ALL aspects (incl. narrator-promoted) at the narrator-reentry boundary. The LLM-prompt sink is the one ADR-047 governs, and it is covered.
4. `[VERIFIED]` mechanical-advantage bounded — the promoter (unchanged) caps narrator promotion at one `kind="character"` aspect, `free_invokes=0` (`fate_item_promotion.py:105-124`); the free-text only labels the aspect; the effect is the fixed +2 at fate-point cost (ADR-144 "TRUE not STRONG"). No power faucet introduced.
5. `[SEC]` (LOW, non-blocking) client-wire raw aspect text (`fate_projection.py:226/251`) — uniform across all aspects, React-escaped at render; pre-existing posture, not introduced here. Optional defense-in-depth: sanitize grants_aspect at the LLM→state boundary.
6. `[SILENT]` silent-failure-hunter clean — full chain verified; the non-fatal extractor catch (`sidecar_extractor.py:343-352`) is intentional and loud (logs + `sidecar_extraction.failed` OTEL), not a swallowed error.
7. `[EDGE]` edge-hunter disabled — manual pass: missing/empty grants_aspect → no promote (pinned by `test_fate_item_without_grants_aspect_does_not_promote`); non-string → `str()` coercion (graceful); dedup re-grant → logged no-op (existing `test_dedup_noop_is_logged_not_silent`). No unhandled boundary.
8. `[TEST]` test-analyzer disabled — manual pass: assertions are concrete (schema membership, span attrs, ladder_total == 3); no vacuous `assert True`. `test_grants_aspect_is_optional_not_required` is a weak-but-valid structural guard, sound when paired with the existence test.
9. `[DOC]` comment-analyzer disabled — manual pass: the field comment + schema description accurately match behavior. The class docstring's older "no field is applied this story" note is mildly stale post-151-4 but not touched by this diff.
10. `[TYPE]` type-design disabled — manual pass: WithJsonSchema schema-only is a deliberate, documented type choice; grants_aspect is stringly-typed at runtime (LOW, covered by `str()` coercion — see finding F2).
11. `[SIMPLE]` simplifier disabled — manual pass: the change is minimal (one schema constant + one annotation + one description sentence); no over-engineering, no dead code.
12. `[RULE]` rule-checker disabled — manual pass: see Rule Compliance below — Python checklist clean.

### Rule Compliance (python lang-review checklist, enumerated against the diff)
- **#1 silent exceptions:** no new try/except in the diff. PASS.
- **#2 mutable defaults:** `Field(default_factory=list)` (correct), module constant is a literal. PASS.
- **#3 type annotations:** `_ITEMS_GAINED_ITEM_SCHEMA: dict[str, Any]`; field + helper annotated. `Any` is justified (free-form item entry). PASS.
- **#4 logging:** no new error paths. PASS.
- **#6 test quality:** concrete assertions, no skips, no mock-target errors. PASS.
- **#8 unsafe deserialization:** no pickle/eval/yaml.load; `model_validate` is pydantic-validated structure (the new field is a documented string). PASS (see F2 for the runtime-string nuance — graceful via `str()`).
- **#10 import hygiene:** `Annotated` (typing), `WithJsonSchema` (pydantic) both used; no star imports. PASS.
- **#11 input validation at boundaries:** the LLM-output boundary documents the field (schema) and the relevant trust boundary (narrator-reentry) sanitizes (ADR-047). PASS for the governed sink; client-wire is React-escaped (F1, LOW).
- #5/#7/#9/#12/#13 — not applicable to this diff (no path handling, resources, async, deps, or fix-rescan).

### Devil's Advocate
Suppose this code is broken. A malicious player crafts input designed to make the narrator emit prose that the sidecar extractor reads into `grants_aspect`. Could they (a) inject a prompt back into the narrator, (b) XSS the client, or (c) grant themselves overpowered mechanics? For (a): the value re-enters the narrator only through `build_*` projection paths, and `fate_projection.py:64` runs `sanitize_player_text` over every aspect — so the injection is neutralized at the one boundary ADR-047 governs; the player's original input was already sanitized on the way in, making this at most second-order. For (b): the raw aspect text reaches the client via `FateAspectEntry`, but React escapes text nodes and the preflight found zero `dangerouslySetInnerHTML` — so a `<script>` aspect renders as inert text. For (c): the promoter caps a narrator grant at exactly one `kind="character"` aspect with `free_invokes=0`; the text is a label, the effect is a fixed +2 that costs a fate point to invoke and can be compelled against the player — so "I Am A God" buys the same +2 as "Knows the Hidden Trails." Could a non-string slip through? Yes — `dict[str, Any]` doesn't enforce the schema's `string`, so `grants_aspect: ["a","b"]` is legal at runtime; but the consumer's `str(...)` coercion turns it into a (sanitized, escaped) repr rather than a crash. Could the extractor over-fire and stack aspects? Per item, yes (N items → N aspects) — but that is the shipped, intended per-item model and each invocation costs a fate point. Could a pathologically long aspect bloat state? There is no max-length, but the narration is truncated to 4000 chars upstream. Net: every "broken" path is either covered by an existing boundary, gracefully degraded, or a pre-existing/bounded condition. The change does not introduce a Critical or High defect. The two LOW residuals (storage-time sanitize as defense-in-depth; runtime string enforcement) are recorded as non-blocking follow-ups.

**Data flow traced:** player input (sanitized in) → narrator prose → sidecar extractor `grants_aspect` (schema-documented) → `merge_sidecar_extraction_transactional` (dict preserved) → `narration_apply.py:5254` `str(...).strip()` → `promote_gained_item` (one capped aspect) → FateSheet → {narrator prompt: sanitized at `fate_projection.py:64`; client wire: React-escaped}. Safe.
**Pattern observed:** schema-only contract widening via `WithJsonSchema` — `sidecar_extractor.py:116-141` — keeps the wire type stable while enriching the LLM-facing schema. Good pattern; reusable for the 151-x bucket-B typing work.
**Error handling:** non-string `grants_aspect` coerced via `str()` (graceful); missing field → no promotion (invariant test). No new failure paths.

**Handoff:** To SM (Vizzini) for finish-story.