---
story_id: "83-2"
jira_key: ""
epic: "83"
workflow: "tdd"
---
# Story 83-2: Culture self-match — named people-group resolves to its own culture (Munchkin→Munchkin)

## Story Details
- **ID:** 83-2
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T10:33:25Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T09:46:21.922229+00:00 | 2026-06-05T09:47:22Z | 1m |
| red | 2026-06-05T09:47:22Z | 2026-06-05T10:01:29Z | 14m 7s |
| green | 2026-06-05T10:01:29Z | 2026-06-05T10:17:35Z | 16m 6s |
| review | 2026-06-05T10:17:35Z | 2026-06-05T10:33:25Z | 15m 50s |
| finish | 2026-06-05T10:33:25Z | - | - |

## Sm Assessment

Story 83-2 is the people-side half of ping-pong #74 (83-1 was the creature side). `_resolve_invented_naming_context` (narration_apply.py:1615 on develop) tags a narrator-invented person/people-group with a RANDOM bound culture via `random.shuffle` — so the Munchkins got culture=Quadling. Fix: when the narrator names a specific people/group/clan, match that name against the bound cultures (culture name + authored aliases/demonyms) and resolve to its OWN culture; fall back to the shuffle ONLY for a genuinely unaffiliated stranger.

Scope: server-only, 3pt, TDD. No Jira, no architecture phase — the seam is known and the design is a matcher + fallback.

Reuse-don't-reinvent: `sidequest/game/alias_resolution.py` (ADR-118, landed via epic 84) gives a word-bounded, case-insensitive, alias-aware `resolve_mention` matcher. TEA/Dev should evaluate leaning on that word-boundary discipline for the culture/demonym match rather than forking a new matcher. Also confirm whether cultures carry authored aliases/demonyms in genre/world YAML and how they load.

No-Silent-Fallbacks: a matched-but-unbuildable corpus must surface loud (`namegen.thin_corpus` exists) — do NOT silently shuffle past a real match that fails to build.

OTEL: the culture-resolution decision (self-match vs shuffle-fallback) must emit a watcher event so the GM panel can see which path fired — TEA asserts the emit.

Routing to TEA (The Architect) for RED.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Bug fix with behavioral + OTEL AC coverage.

**Test Files:**
- `tests/server/test_npc_culture_self_match.py` — 15 tests covering all 5 ACs

**Tests Written:** 15 tests covering 5 ACs
**Status:** RED — 14 failing, 1 passing (shuffle-fallback regression guard already works)
**Branch:** `feat/83-2-culture-self-match-named-people-group`
**Commit:** `e7d09620`

**Failing test command:**
```
cd sidequest-server && uv run pytest tests/server/test_npc_culture_self_match.py -n0 -v
```

**Failure summary (14 failures, all for the right reasons):**
- `test_culture_model_has_aliases_field` — `AttributeError: 'Culture' object has no attribute 'aliases'`
- `test_culture_can_be_constructed_with_aliases` — `ValidationError: extra fields not permitted` (aliases not on model)
- `test_resolve_naming_context_accepts_mention_name_kwarg` — `TypeError: unexpected keyword argument 'mention_name'`
- `test_resolve_naming_context_self_match_returns_matching_culture` — `TypeError: unexpected keyword argument 'mention_name'`
- `test_resolve_naming_context_plural_mention_matches_singular_culture` — `TypeError: unexpected keyword argument 'mention_name'`
- `test_resolve_naming_context_case_insensitive` — `TypeError: unexpected keyword argument 'mention_name'`
- `test_resolve_naming_context_no_match_falls_back_to_shuffle` — `TypeError: unexpected keyword argument 'mention_name'` (will PASS once param added — regression guard)
- `test_resolve_naming_context_alias_match` — `ValidationError: extra fields not permitted`
- `test_resolve_naming_context_alias_plural_authored` — `ValidationError: extra fields not permitted`
- `test_otel_routed_span_records_self_match_strategy` — `AssertionError: span missing 'resolution_strategy' attribute`
- `test_otel_routed_span_records_shuffle_fallback_strategy` — `AssertionError: span missing 'resolution_strategy' attribute`
- `test_self_matched_culture_with_broken_corpus_does_not_silently_shuffle` — `AssertionError: 0 unrouted spans (AC5 bug: silent fallthrough)`
- `test_wiring_munchkin_mention_resolves_to_munchkin_culture_end_to_end` — `AssertionError: got culture='Winkie' not 'Munchkin'`
- `test_wiring_plural_munchkins_resolves_to_munchkin_culture_end_to_end` — `AssertionError: got culture='Winkie' not 'Munchkin'`

**Handoff:** To Dev for implementation

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Gap** (non-blocking): OTEL `reason` misattribution on the self-match corpus-failure path. The `elif naming_unresolved:` branch hardcodes `reason="no_culture_bound"` and logs "no culture bound for the active world", but the new AC5 path (matched culture, corpus fails to build) routes through it — so the GM panel and operator logs cannot distinguish "world bound no cultures" from "the right culture's corpus is broken," and the log line is factually false. Affects `sidequest/server/narration_apply.py` (thread the failure reason out of `_resolve_invented_naming_context` — widen its 4-tuple return to carry strategy + reason — and pass `reason="self_match_corpus_failed"`/`"generation_failed"` at line ~2137; add a `reason` assertion to `test_self_matched_culture_with_broken_corpus_does_not_silently_shuffle`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Multi-named-people-group-per-turn caching. `naming_resolved=True` after the first novel person NPC means a second distinct people-group in the same turn reuses the first's culture generator (Munchkin+Winkie in one turn → Winkie gets a Munchkin name). Pre-existing design (mechanism unchanged by this PR), no test coverage. Affects `sidequest/server/narration_apply.py` (resolve naming context per-mention, or cache per-mention-name rather than once-per-turn). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_resolve_invented_naming_context` returns an under-specified 4-tuple, which forces both the reason misattribution above and a redundant strategy recomputation at `narration_apply.py:2095-2107`. Widening the return (5-tuple or small dataclass carrying `resolution_strategy` + `failure_reason`) fixes both symptoms at the root. Affects `sidequest/server/narration_apply.py`. *Found by Reviewer during code review.*

### TEA (test design)
- **Gap** (non-blocking): `Culture` model has no `aliases` or `demonyms` field yet. Content authors currently have no way to declare plural forms or demonyms in YAML. The fix requires adding `aliases: list[str] = Field(default_factory=list)` to `sidequest/genre/models/culture.py`. This is gated by `extra="forbid"` — without this field, `Culture(..., aliases=[...])` raises `ValidationError`. *Found by TEA during test design.*
- **Gap** (non-blocking): `alias_resolution.py` `_phrase_matches` is a private function (single underscore). Dev should either make it semi-public or import it directly — it's the right word-boundary discipline to reuse for culture self-matching. *Found by TEA during test design.*

## Impact Summary

**Upstream Effects:** 2 findings (2 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** None

- **Gap:** OTEL `reason` misattribution on the self-match corpus-failure path. The `elif naming_unresolved:` branch hardcodes `reason="no_culture_bound"` and logs "no culture bound for the active world", but the new AC5 path (matched culture, corpus fails to build) routes through it — so the GM panel and operator logs cannot distinguish "world bound no cultures" from "the right culture's corpus is broken," and the log line is factually false. Affects `sidequest/server/narration_apply.py`.
- **Gap:** Multi-named-people-group-per-turn caching. `naming_resolved=True` after the first novel person NPC means a second distinct people-group in the same turn reuses the first's culture generator (Munchkin+Winkie in one turn → Winkie gets a Munchkin name). Pre-existing design (mechanism unchanged by this PR), no test coverage. Affects `sidequest/server/narration_apply.py`.

### Downstream Effects

- **`sidequest/server`** — 2 findings

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Alias/plural strategy:** Spec says "singular/plural tolerant ('Munchkin' ~ 'Munchkins')". Tests use BOTH the authored-aliases path (content adds "Munchkins" as an alias) AND a separate plural test — leaving it to Dev to decide whether to handle bare plural via engine heuristic or require the content to carry the alias. The tests for plural assert the BEHAVIOR; Dev picks the implementation path. The authored-aliases path is always tested regardless.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- **TEA — Alias/plural strategy (Dev picks the implementation path; behavior asserted either way)** → ✓ ACCEPTED by Reviewer: sound. The shipped code does exactly this — `_culture_mention_matches` covers (1) exact name, (2) engine `name+"s"` plural heuristic, AND (3) authored `culture.aliases`, so both the authored-alias path and the bare-plural path are satisfied. The tests assert behavior, not implementation, as logged. Verified at `narration_apply.py:1617-1638`.
- **Dev — "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed against the diff — the implementation matches the SM/TEA spec (mention-name self-match first, shuffle fallback second, loud degrade on matched-corpus failure). No undocumented spec divergence found.
- No additional undocumented deviations spotted. (The two confirmed findings are pre-existing-design / observability-precision issues, not spec deviations — they are captured in Delivery Findings, not here.)

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/genre/models/culture.py` — Added `aliases: list[str] = Field(default_factory=list)` to `Culture` model
- `sidequest/server/narration_apply.py` — Added `_culture_mention_matches` helper; modified `_resolve_invented_naming_context` with `mention_name` param and self-match logic; changed `build_from_culture` to go through `_namegen_module` (monkeypatch-friendly); updated caller to pass `mention_name=original_name`; added `resolution_strategy`/`matched_token` determination and pass to routed span
- `sidequest/telemetry/spans/npc.py` — Added `resolution_strategy` and `matched_token` to `npc_invented_name_routed_span` signature, attributes dict, and SPAN_ROUTES extract lambda

**Tests:** 15/15 passing (GREEN)
**Branch:** feat/83-2-culture-self-match-named-people-group (pushed)

**Handoff:** To review phase

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | Lint clean on all 4 changed files; 15/15 tests pass; 1 pre-existing failure (`test_connect_to_evropi_populates_filtered_world_context`) confirmed on develop before this branch — MissingDatabaseUrlError, DB infra issue unrelated to 83-2; regression band 212 passed, 4 errors (same pre-existing DB issues). | confirmed 0, dismissed 0, deferred 0 (clean) |
| 2 | reviewer-edge-hunter | Yes | findings | Multi-NPC-per-turn caching: `naming_resolved=True` after first novel person NPC prevents `_resolve_invented_naming_context` being called for subsequent NPCs in the same turn. A turn with "Munchkins" AND "Winkies" both novel: Munchkin gets Munchkin culture (correct), Winkie silently gets Munchkin-style name (wrong). Pre-existing design; no test covers it. Also: plural heuristic `culture.name + "s"` is English-only and will produce wrong plurals for non-standard forms ("Ox"→"Oxs"), but aliases provide the correct override path. | confirmed 2, dismissed 0, deferred 0 (Major #1 + plural heuristic, both non-blocking/tracked) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | AC5 loud degrade IS real — `naming_unresolved=True` fires `npc_invented_name_unrouted_span`. But `reason="no_culture_bound"` is hardcoded at the caller for ALL unrouted cases, including self-match corpus failure. Span docstring explicitly lists `no_culture_bound` vs `generation_failed` as discriminators; the AC5 path should pass `reason="generation_failed"` (or `"self_match_corpus_failed"`). Test only asserts `severity="warning"`, not `reason`, so it passes. GM panel cannot distinguish "world has no cultures" from "right culture's corpus is broken". | confirmed 1, dismissed 0, deferred 0 (Major #2, Medium, tracked) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (`workflow.reviewer_subagents.test_analyzer=false`) — test domain self-assessed in `[TEST]` below |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (`comment_analyzer=false`) — doc domain self-assessed in `[DOC]` below |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (`type_design=false`) — type domain self-assessed in `[TYPE]` below |
| 7 | reviewer-security | Yes | clean | `_phrase_matches` uses `re.escape(phrase)` — no regex injection. No user-controlled inputs reach raw regex. Culture names are YAML-loaded controlled strings. No SQL, no command execution, no sensitive data exposed. | confirmed 0, dismissed 0, deferred 0 (clean) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (`simplifier=false`) — simplicity domain self-assessed in `[SIMPLE]` below |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (`rule_checker=false`) — rule domain self-assessed in `[RULE]` below |

**All received:** Yes (4 enabled+run returned: preflight, edge-hunter, silent-failure-hunter, security; 5 disabled via settings, pre-filled Skipped)
**Total findings:** 3 confirmed (1 Medium #2, 2 non-blocking edge/plural), 0 dismissed, 0 deferred

## Reviewer Assessment

[PRE] Lint clean. 15/15 tests pass GREEN. The pre-existing `test_connect_to_evropi_populates_filtered_world_context` failure is confirmed pre-existing on develop (MissingDatabaseUrlError — DB infra, unrelated to 83-2). Regression band shows 212 passing with only the known DB-infra errors. Story scope is tight (4 files, two production commits). Wiring is real — both e2e tests load the actual `wry_whimsy` oz pack and confirm `culture="Munchkin"` on the routed span.

[SEC] No security concerns. `re.escape(phrase)` in `_phrase_matches` prevents regex injection. Culture names are YAML-controlled strings, not user input.

[EDGE] **Major finding #1: multi-NPC-per-turn caching — second named people-group silently gets wrong culture.** `narration_apply.py:2079-2086` — `naming_resolved=True` is set after the first novel person NPC. If a single narrator turn invents both "Munchkin" AND "Winkie" as novel people-group NPCs, "Munchkin" correctly self-matches, but "Winkie" skips `_resolve_invented_naming_context` entirely and reuses the cached Munchkin generator. This violates the story's stated invariant ("each named people-group resolves to its own culture") for any turn with two distinct named groups. The dev explicitly acknowledges this as a pre-existing design limit. No test covers it. It's arguably a regression in one direction: before this PR, both would get a random culture; after, the second always gets the first one's culture (consistently wrong vs randomly wrong). This is scoped to a future story but should be tracked.

[EDGE] Plural heuristic `culture.name + "s"` (`narration_apply.py:1634`) is English-only and won't produce correct results for non-standard plurals ("Ox"→"Oxs"). This is mitigated by the `aliases` field — content authors can always add the correct plural. Word-boundary discipline in `_phrase_matches` prevents over-matching on short names. Acceptable for current scope.

[SILENT] **Major finding #2: OTEL `reason` misattribution for self-match corpus failure.** `narration_apply.py:2137` always passes `reason="no_culture_bound"` to `npc_invented_name_unrouted_span`, even in the AC5 path where the actual reason is "self-matched culture corpus failed." The span's docstring explicitly lists `no_culture_bound` vs `generation_failed` as the intended discriminators. The AC5 test only checks `severity="warning"` (passes) but not `reason`. The GM panel receives a misleading reason code that makes two distinct failure modes indistinguishable. Fix: pass `reason="self_match_corpus_failed"` (or `"generation_failed"`) from `_resolve_invented_naming_context`'s corpus-failure return path, e.g. by returning a 5-tuple or an additional flag.

[TEST] Test suite is strong: 15 tests, 5 ACs, **two real-pack e2e wiring tests** (`test_wiring_munchkin_mention_resolves_to_munchkin_culture_end_to_end` and the plural variant) that load the actual `wry_whimsy/oz` pack and assert `culture="Munchkin"` on the routed span — these satisfy the "every suite needs a wiring test" rule end-to-end. One coverage gap, and it is the *direct cause* finding #2 slipped through: `test_self_matched_culture_with_broken_corpus_does_not_silently_shuffle` asserts `severity="warning"` on the unrouted span but never asserts `reason`, so the misattributed `reason="no_culture_bound"` passes uncaught. The follow-on fix MUST add a `reason` assertion to this test. Non-blocking for this story (the loud-degrade behavior under test is correct; only the unasserted label is wrong).

[DOC] `_culture_mention_matches` and the `_resolve_invented_naming_context` docstring additions are accurate and cite ADRs (091, 118) correctly. Comment defect: production comments embed the story number in multiple spots (`culture.py:49`, `npc.py:257/418`, `narration_apply.py` several). Per project convention story refs in comments rot — Low. More serious doc-truth issue folded into finding #2: the `logger.warning` at `narration_apply.py:2141` emits the literal text *"no culture bound for the active world"* on the AC5 corpus-failure path where a culture WAS bound — a factually false operator log, not just a cosmetic tag. This raises finding #2 from "wrong span attribute" to "misleading operator diagnostic," strengthening the case for a prompt follow-on (an operator debugging a bad Munchkin name would be sent to fix world YAML that isn't broken).

[TYPE] `Culture.aliases: list[str] = Field(default_factory=list)` is correctly typed and gated past `extra="forbid"` (the ValidationError that blocked content YAML is resolved). `resolution_strategy`/`matched_token` are bare `str` rather than `Literal["self_match","shuffle_fallback"]` — stringly-typed, but this is **consistent** with every other attribute on the sibling NPC spans in `npc.py` (all `str`), so it is not a new type violation, just an inherited convention. Root structural smell: `_resolve_invented_naming_context` returns a lean 4-tuple `(generator, culture_name, culture_source, naming_unresolved)` that cannot carry the resolution strategy OR the failure reason — this single under-specified return is the common root of both finding #2 (reason misattribution) and the `[SIMPLE]` duplication below. The follow-on should widen this return (5-tuple or a small dataclass) rather than patch the two symptoms separately.

[SIMPLE] The strategy-determination block at `narration_apply.py:2095-2107` re-derives the matched culture (`pack.effective_cultures(world)` + a second `_culture_mention_matches` call) even though the resolver already performed exactly that match internally. Verified consistent (a shuffle_fallback can never re-match because the self-match loop would have caught any matching mention first; a self_match always re-matches the same culture) — so it is not a *bug*, but it is redundant work driven by the lean return tuple noted in `[TYPE]`. Low/Medium; fix alongside the tuple widening, not separately.

[RULE] Project-rule compliance check (CLAUDE.md / SOUL.md): **No-Silent-Fallbacks — COMPLIANT**: the self-match corpus-failure path returns `naming_unresolved=True` and degrades loud rather than shuffling to a wrong culture (`narration_apply.py:1688-1697`); the shuffle path's per-culture skip is the pre-existing, ADR-justified behavior. **Crunch-in-genre/Flavor-in-world — COMPLIANT**: `aliases` is a mechanism field on the genre `Culture` model; the actual demonyms are authored in content YAML. **OTEL-on-every-subsystem-decision (`<important>`) — PARTIAL**: the success path emits `resolution_strategy`/`matched_token` correctly (the SM-mandated self-match-vs-shuffle watcher event fires), but the failure path mislabels `reason` — this is finding #2, and because it matches a stated project rule it is CONFIRMED, not dismissed. I am downgrading its *severity* to Medium (with rationale: AC5's explicit loud-degrade requirement is satisfied; OTEL is `<important>`, not `<critical>`; the path is a rare degraded edge), but I am NOT dismissing it — it is recorded as a tracked Delivery Finding.

Minor: `matched_token` in `_culture_mention_matches` always returns `culture.name` regardless of whether the match was via the name, plural heuristic, or alias. So if "Munchkins" matched via the plural heuristic, `matched_token="Munchkin"` not `"Munchkins"`. Span doc says "the token that matched" — the value is technically "the culture that matched," not the exact token. The test only checks truthy, not exact value.

Nit: Story number in production comment (`culture.py:52` — `# Story 83-2: authored demonyms...`). Story references in comments rot per project conventions.

Wiring confirmed: `mention_name=original_name` flows from `narration_apply.py:2085` through the production call chain. The two e2e tests exercise the real pack (not mocks) and confirm the self-match fires end-to-end. The `_apply_narration_result_to_snapshot` → `_apply_npc_mentions` production chain is the real call site.

### Devil's Advocate

Suppose I argue this code is broken. The strongest case: the OTEL failure path is a *confident lie*, and this project's entire premise is that OTEL is the lie-detector that catches the narrator winging it. When a content author binds the Munchkin culture but ships a thin Munchkin corpus, the engine correctly refuses to mint a wrong-culture name (good) — but then tells the operator, in both the span `reason` and a plain-English log line, "no culture bound for the active world." An operator (Keith) debugging why his Munchkins have no names follows that signal straight to the world YAML, finds cultures bound exactly as expected, and burns an hour on a false trail — the precise failure mode No-Silent-Fallbacks exists to prevent, reincarnated as a not-silent-but-wrong fallback. A skeptic would call that High, not Medium, and reject.

Where the malicious/confused user goes: a narrator turn naming two distinct people-groups ("the Munchkins and the Winkies arrive") — finding #1 — silently brands the second group with the first's culture. A player who knows the lore notices the Winkie elder has a Munchkin name. That's a visible correctness defect in normal multi-NPC play, not an exotic edge.

Stressed-filesystem / unexpected-config angle: `getattr(culture, "aliases", None) or []` defends against a missing attribute, and `re.escape` defends the regex — both hold up. `_culture_mention_matches("", ...)` short-circuits on empty mention. No crash paths found under malformed input.

Why I still don't reject: finding #1's mechanism (second NPC reuses the first's cached generator) is unchanged from develop — this PR makes the *first* NPC correct and leaves the pre-existing cache limit exactly as it was; it is not a regression introduced here. Finding #2's underlying AC ("matched-but-unbuildable corpus must surface loud") is literally met — the span fires at `severity="warning"`; only the discriminator label is wrong, on a rare degraded path. Both are real, both are now tracked as Delivery Findings, and the honest call is APPROVE-with-tracking rather than blocking a correct primary fix on a mislabeled edge.

**Verdict: APPROVED** — The story's primary goal (single named people-group resolves to its own culture) is correctly implemented, tested, and wired. Major finding #1 (multi-NPC caching) is pre-existing design, not a regression introduced here; it belongs in a follow-on story. Major finding #2 (OTEL reason misattribution) is observability quality, not correctness — the loud degrade IS present, just with the wrong `reason` tag. Both should be tracked; neither blocks merging this story.