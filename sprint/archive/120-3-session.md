---
story_id: "120-3"
jira_key: "120-3"
epic: "120"
workflow: "tdd"
---
# Story 120-3: Upgrade the D3 genre-baseline validator from 'no genre-tier bespoke' to 'WN-family genre baseline must be mode:verbatim (or derived)'

## Story Details
- **ID:** 120-3
- **Jira Key:** 120-3
- **Epic:** 120 — SRD-bound genre baselines go fully verbatim
- **Workflow:** tdd
- **Repos:** server
- **Points:** 3
- **Stack Parent:** none (depends_on: [120-1, 120-2] both done)

## Technical Approach

**Target:** Extend `_validate_genre_baseline_no_bespoke` in `sidequest-server/sidequest/genre/loader.py`

**Validation Rule Extension:**
For WN-family (awn/cwn/wwn/swn) genre baselines:
- Genre-tier item_catalog items MUST have `mode:verbatim` or `mode:derived` (SRD-sourced)
- REJECT unprovenanced items (mode:no-provenance or missing mode entirely)
- Fail LOUD per No Silent Fallbacks — name offenders explicitly in the error message
- Native (non-WN) packs remain EXEMPT from this new rule

**Testing Strategy:**
- Retune 114-14 tests that pin the OLD 'no genre-tier bespoke' rule to align with new verbatim-only enforcement
- Full WN-pack regression suite must pass green:
  - Sets env: `SIDEQUEST_GENRE_PACKS=1` and `SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test`
  - Scope: All awn/cwn/wwn/swn content packs in sidequest-content
  - Verify: `tests/genre/` calibration tests pass; `tests/integration/` load_genre_pack paths

## Acceptance Criteria

1. `_validate_genre_baseline_no_bespoke` rejects WN genre-tier items lacking mode:verbatim/derived
   - Error message names the offending item_id and its mode field
   - Native packs bypass the new rule (only the old 'no bespoke' rule applies)

2. 114-14 tests retune to expect verbatim-only strictness
   - Tests pass against real WN genre baselines (awn, cwn, wwn, swn)

3. Full test suite green with required env vars set
   - No regressions in genre load path
   - No regressions in fixture-based tests

4. Story context created and validated via `pf validate context-story 120-3`

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T07:54:28Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-16T07:19:09Z | 2026-06-16T07:37:50Z | 18m 41s |
| green | 2026-06-16T07:37:50Z | 2026-06-16T07:46:12Z | 8m 22s |
| review | 2026-06-16T07:46:12Z | 2026-06-16T07:54:28Z | 8m 16s |
| finish | 2026-06-16T07:54:28Z | - | - |

## Delivery Findings

<!-- Append-only. Each agent writes under its own subheading. -->

### TEA (test design)
- **Gap** (non-blocking): The 120-3 `mode=verbatim`/`derived` allow-list and "name every offender" message shape is currently asserted only against the SWN fixture + the 7 real WN packs; there is no WWN/CWN/AWN *fixture* exercising the unprovenanced-rejection path. The SWN fixture path through `load_genre_pack` is sufficient (the validator is ruleset-string-gated via `_is_without_number`, not per-ruleset-branched), so this is a note, not a required addition. Affects `tests/server/test_120_3_verbatim_only_genre_baseline_validator.py` (could add an awn/cwn fixture if the validator ever branches per-ruleset). *Found by TEA during test design.*
- **Improvement** (non-blocking): Verified empirically (loaded all 7 WN-family packs through `load_genre_pack`) that NONE carry unprovenanced or bespoke genre `item_catalog` items today — caverns/elemental_harmony/heavy_metal (68 each), neon_dystopia/road_warrior (66 each), space_opera (14), mutant_wasteland (9), all clean. The ordering precondition (120-1 + 120-2 land first) is satisfied not just per the epic doc but in the actual content. Dev's validator tightening will NOT break any production WN-pack load. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): 5 pre-existing `tests/genre/` failures are red on this branch but are NOT caused by 120-3 — they are the in-flight epic-108 WWN combat-beat de-nativization (`cast_spell`/`committed_blow` beats missing, `Warrior.encounter_beat_choices` pool mismatch at `loader.py:809`, beneath_sunden room-binding). Confirmed by error source: every failure traces to beat/class/room logic, none to `_validate_genre_baseline_no_bespoke` (`loader.py:723`), and elemental_harmony/heavy_metal load *past* the inventory validator before failing on beat assertions. Affects the genre calibration suite (tracked under epic 108 — `test_caverns_and_claudes_loads_with_committed_blow_beat`, `test_elemental_harmony_loads_clean_under_wwn`, `test_heavy_metal_blade_work_has_class_filtered_cast_spell`, `test_classes_yaml_loads_entries`, `test_distinct_rooms_bind_distinct_creatures`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The validator expresses its policy as a *denylist* (reject `provenance is None` OR `mode == "bespoke"`) rather than an affirmative *allowlist* (require `mode in {"verbatim","derived"}`). It is correct and safe today because `ItemProvenance.mode` is a closed `Literal["verbatim","derived","bespoke"]` — pydantic rejects any other value at parse time, so no fourth mode can reach the validator. But if that `Literal` is ever widened (e.g. add `"adapted"`) without updating the validator, the new mode would pass a WN genre baseline *silently* — the failure mode runs against "No Silent Fallbacks." Recommended hardening (also simpler — one comprehension instead of two): `_ALLOWED_MODES = frozenset({"verbatim","derived"})`, collect offenders where `item.provenance is None or item.provenance.mode not in _ALLOWED_MODES`, then classify None-vs-wrong-mode for the message. Affects `sidequest/genre/loader.py:737-761` (`_validate_genre_baseline_no_bespoke`). Converges across the silent-failure, type-design, and simplifier lenses. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The function name `_validate_genre_baseline_no_bespoke` is now a mild misnomer (it enforces verbatim-only, not just no-bespoke). Kept deliberately (spec names it; renaming churns the `test_ship_weapons_resolve.py` import) and honestly flagged in the docstring. If/when the affirmative-allowlist refactor above lands, that diff is the natural place to also rename to `_validate_genre_baseline_verbatim_only` and update the two importers. Affects `sidequest/genre/loader.py:723`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Additive retune of the 114-14 tests rather than in-place rewrite**
  - Spec source: context-story-120-3.md, AC-2 ("114-14 tests retune to expect verbatim-only strictness")
  - Spec text: "Retune the 114-14 tests that pin the narrow rule"
  - Implementation: Kept the existing 114-14 `no-bespoke` assertions intact (they remain valid as the subset the verbatim-only rule subsumes) and ADDED a new parametrized `test_wn_family_pack_genre_baseline_is_verbatim_only` over all 7 WN-family packs; updated the stale "verbatim-only is epic 120" docstrings in both 114-14 files.
  - Rationale: The narrow no-bespoke assertions are still true post-upgrade — rewriting them would lose coverage for no upside. The new parametrized test is the verbatim-only strictness AC2 asks for. No 114-14 assertion was weakened.
  - Severity: minor
  - Forward impact: none
- **New RED unit tests live in a dedicated `test_120_3_*` file, not appended to the 114-14 unit file**
  - Spec source: context-story-120-3.md, AC-1/AC-2
  - Spec text: "extend _validate_genre_baseline_no_bespoke ... Retune the 114-14 tests"
  - Implementation: Unprovenanced-rejection + error-message RED tests are in `tests/server/test_120_3_verbatim_only_genre_baseline_validator.py`; the 114-14 unit file got a docstring pointer to it.
  - Rationale: Clean story traceability; the 114-14 file stays scoped to the bespoke subset it was written for.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- No deviations from spec. The validator was extended in place per the story title's named target (`_validate_genre_baseline_no_bespoke`); the function name was deliberately kept (the spec names it; renaming would churn the working `test_ship_weapons_resolve.py` guard for no test-required benefit) with the docstring updated to the broadened verbatim-only rule. Offender rule, native exemption, fail-loud naming, and `item_catalog`-only scope all match the TEA tests and ACs exactly.

### Reviewer (audit)
- **TEA: Additive retune of the 114-14 tests** → ✓ ACCEPTED by Reviewer: sound. The no-bespoke assertions remain true under the verbatim-only rule (it subsumes them), and the new `test_wn_family_pack_genre_baseline_is_verbatim_only` parametrize over all 7 WN packs delivers AC-2's "verbatim-only strictness against real awn/cwn/wwn/swn baselines." No coverage lost.
- **TEA: New RED unit tests in a dedicated `test_120_3_*` file** → ✓ ACCEPTED by Reviewer: clean traceability; the 114-14 unit file keeps its bespoke-subset scope with an accurate docstring pointer. Verified both 114-14 files' assertions are unchanged and still pass.
- **Dev: Kept the function name `_validate_genre_baseline_no_bespoke`** → ✓ ACCEPTED by Reviewer: the story title explicitly names this function as the extension target ("extend _validate_genre_baseline_no_bespoke (loader.py)"), so keeping it is faithful to spec, not a deviation. The docstring openly flags the name as predating the broadening. Renaming would churn the working `test_ship_weapons_resolve.py` import for zero behavioral gain. (The stale-name-vs-behavior mismatch is noted as a non-blocking Improvement below, not a flagged deviation.)
- **UNDOCUMENTED check:** AC-1's "Error message names the offending item_id and its mode field" — the implementation names every offending id and conveys its mode *via grouped labels* (`unprovenanced item(s) [...]` / `bespoke item(s) [...]`) rather than a literal per-item `mode=` string. Judged COMPLIANT-in-spirit (the reader learns which items and their provenance state); the operative contract is the TEA tests, which pass. Not flagged.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/genre/loader.py` — `_validate_genre_baseline_no_bespoke` now rejects any WN-family genre `item_catalog` item whose `provenance is None` (unprovenanced) OR `mode == "bespoke"`; raises a fail-loud `PackError` naming every offender grouped by reason (`unprovenanced item(s) [...]` / `bespoke item(s) [...]`). Native-exempt early-out and `item_catalog`-only scope unchanged; docstring updated.
- `tests/server/test_120_3_verbatim_only_genre_baseline_validator.py` — ruff-format reflow only (1 line; TEA's RED file).

**Tests:** 8/8 story tests GREEN; 67/67 inventory+validator+ship_weapons+wiring tests GREEN. `ruff check` + `ruff format --check` clean on changed files.
**Branch:** `feat/120-3-verbatim-only-genre-baseline-validator` (pushed to origin).

**Blast radius (fully verified):** The change can only affect WN-family genre-pack loading. Confirmed all 7 live WN packs (caverns, elemental_harmony, heavy_metal, mutant_wasteland, neon_dystopia, road_warrior, space_opera) and all WN-family fixture packs (swn_test_pack, wwn_test_pack across both fixture roots) carry zero unprovenanced/bespoke genre items → no load breaks.

**Pre-existing failures (NOT regressions):** 5 `tests/genre/` failures (epic-108 WWN beat de-nativization) — see Delivery Findings; errors trace to `loader.py:809`/beat assertions, never to this change.

**ACs:** AC-1 ✓ (rejects WN genre items lacking verbatim/derived, names offenders, native exempt) · AC-2 ✓ (114-14 tests retuned to verbatim-only, pass against real awn/cwn/wwn/swn) · AC-3 ✓ (blast-radius suite green, no regressions) · AC-4 ✓ (context validated at setup).

**Handoff:** To Reviewer (Westley) for code review.

**Tests Required:** Yes
**Reason:** N/A — behavioral upgrade to a loader validator; RED tests pin the new rule.

**Test Files:**
- `tests/server/test_120_3_verbatim_only_genre_baseline_validator.py` (NEW) — 8 tests through the real `load_genre_pack` loader (wiring test): 3 RED + 5 boundary guards.
- `tests/genre/test_114_14_srd_packs_genre_baseline_no_bespoke.py` (RETUNED) — added `test_wn_family_pack_genre_baseline_is_verbatim_only` parametrized over all 7 WN-family packs (verbatim-only real-content regression guard) + `_genre_non_verbatim_offenders` helper; refreshed stale "epic 120 deferred" docstring/comment.
- `tests/server/test_114_14_genre_baseline_no_bespoke_validator.py` (RETUNED) — docstring updated to point at the 120-3 file; assertions unchanged (still valid as the bespoke subset).

**Tests Written:** 8 new (3 RED + 5 guard) + 7 new parametrized real-pack cases; 2 docstrings retuned.
**Status:** RED (3 failing — ready for Dev)

### RED tests (fail until Dev tightens the validator)
| Test | Why RED today |
|------|---------------|
| `test_wn_family_genre_unprovenanced_item_is_rejected` | validator only rejects `mode=bespoke`; an unprovenanced item loads → no `PackError` raised |
| `test_wn_family_genre_unprovenanced_among_verbatim_still_rejected` | per-item rule not yet enforced; mixed verbatim+unprovenanced catalog loads clean |
| `test_error_message_names_both_unprovenanced_and_bespoke_offenders` | current loud message names only bespoke offenders, not unprovenanced |

### Guards (GREEN now — the upgrade must not break them)
`test_wn_family_genre_bespoke_still_rejected` · `test_wn_family_genre_verbatim_is_allowed` · `test_wn_family_genre_derived_is_allowed` · `test_native_pack_genre_unprovenanced_is_exempt` (CRITICAL: native packs carry unprovenanced gear by design) · `test_wn_family_world_tier_unprovenanced_is_allowed` · all 7 WN packs verbatim-only · both 114-14 files · `test_ship_weapons_resolve.py`.

### Rule Coverage
| Rule (python lang-review / CLAUDE.md / SOUL) | Test(s) | Status |
|---|---|---|
| #1 / No Silent Fallbacks — fail loud, NAME every offender | `test_wn_family_genre_unprovenanced_item_is_rejected`, `test_error_message_names_both_unprovenanced_and_bespoke_offenders` | failing (RED) |
| Rule scoped to WN family — native EXEMPT (no over-reach into homebrew) | `test_native_pack_genre_unprovenanced_is_exempt` | passing |
| Rule = verbatim **OR** derived — must not reject `derived` | `test_wn_family_genre_derived_is_allowed`, `test_wn_family_genre_verbatim_is_allowed` | passing |
| Genre-tier only — world inventory is exempt | `test_wn_family_world_tier_unprovenanced_is_allowed` | passing |
| #6 Test quality — no vacuous asserts | self-check below | n/a |
| #8 Safe YAML — `yaml.safe_load`/`safe_dump` in fixture helper | helper `_append_catalog_item` | passing |
| CLAUDE.md "No Source-Text Wiring Tests" — drive the real loader, not grep | every test calls `load_genre_pack` | passing/failing |

**Rules checked:** 7 applicable rules have explicit coverage (the validator is a content-parsing boundary; rules #2/#5/#7/#9/#10/#12 do not apply to test-only changes).
**Self-check:** 0 vacuous tests — every test asserts a named id is present/absent in the message or that a specific item id survived load (value checks, not bare truthy/`is_some`).

### Verification
RED confirmed via `testing-runner` (RUN_ID `120-3-tea-red`) with `SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL` set: **32 items, 3 failed, 29 passed, 0 skipped, 0 collection/import errors.** The 3 failures are clean assertion misses (validator did not raise), not infra errors.

### Notes for Dev (Inigo)
- Target: `_validate_genre_baseline_no_bespoke(ruleset, inventory)` in `sidequest/genre/loader.py:723`.
- Extend the offender scan: an offender is any `item_catalog` entry where `provenance is None` **OR** `provenance.mode == "bespoke"` (i.e. NOT in `{"verbatim","derived"}`). Keep the early-out `if inventory is None or not _is_without_number(ruleset): return` (native-exempt) exactly as-is.
- Fail loud naming **every** offender, ideally distinguishing the two classes (unprovenanced vs bespoke) in the message — the `both-offenders` test requires both ids present.
- `ship_weapons` stays out of scope (the validator scans `item_catalog` only — `test_ship_weapons_resolve.py` guards this).
- Consider renaming/aliasing the function to reflect the broadened rule, but the existing call site (`loader.py:2065`) and the 114-14 tests import `_validate_genre_baseline_no_bespoke` by name — rename in the same diff and update both importers, or keep the name. Per CLAUDE.md, delete no dead code left behind.
- Full-suite gate (GREEN): `SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test` required, else genre tests skip / DB tests throw.

**Handoff:** To Dev (Inigo Montoya) for implementation.

---

## Subagent Results

Per `workflow.reviewer_subagents` settings, 3 of 9 subagents are enabled (preflight, silent_failure_hunter, security); the other 6 are disabled — I covered their domains myself per the review checklist (tags [EDGE]/[TEST]/[DOC]/[TYPE]/[SIMPLE]/[RULE] below).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 5 mechanical (0 blocking) | confirmed 1 (function-name → Improvement), dismissed 1 (private-import is pre-existing, not in diff), noted 3 (double-traversal→folded, docstring-symmetry VERIFIED, OTEL-N/A VERIFIED) |
| 2 | reviewer-edge-hunter | No | Skipped — disabled | N/A | Disabled via settings; covered by Reviewer [EDGE] |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (medium) | confirmed 1, severity downgraded to non-blocking Improvement (pydantic Literal closes the runtime gap) |
| 4 | reviewer-test-analyzer | No | Skipped — disabled | N/A | Disabled via settings; covered by Reviewer [TEST] |
| 5 | reviewer-comment-analyzer | No | Skipped — disabled | N/A | Disabled via settings; covered by Reviewer [DOC] |
| 6 | reviewer-type-design | No | Skipped — disabled | N/A | Disabled via settings; covered by Reviewer [TYPE] |
| 7 | reviewer-security | Yes | clean | none | N/A — confirmed clean (trusted-content path, safe_load only, no injection surface) |
| 8 | reviewer-simplifier | No | Skipped — disabled | N/A | Disabled via settings; covered by Reviewer [SIMPLE] |
| 9 | reviewer-rule-checker | No | Skipped — disabled | N/A | Disabled via settings; covered by Reviewer [RULE] / Rule Compliance |

**All received:** Yes (3 enabled returned; 6 disabled, pre-filled)
**Total findings:** 1 confirmed (non-blocking Improvement), 1 dismissed (pre-existing, outside diff), 0 blocking.

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A clean, minimal, well-tested broadening of one load-time content validator. The production change is 23 lines in a single private function; behavior is provably correct today and the blast radius (all 7 live WN packs + all WN-family fixtures) was exhaustively verified clean by both TEA and Dev. No Critical or High issue. One Medium finding (denylist-vs-allowlist) is downgraded to a non-blocking Improvement because pydantic's closed `Literal` makes it latent, not live.

**Observations (8):**
- `[SILENT]` Denylist not allowlist — `loader.py:737-761` enumerates reject-classes (`None`, `bespoke`) and trusts the `Literal` to bound the rest, rather than affirmatively requiring `{verbatim, derived}`. **MEDIUM → downgraded non-blocking**: `ItemProvenance.mode` is `Literal["verbatim","derived","bespoke"]`, so pydantic rejects a fourth value at parse time before this code runs — no live silent-fallback. Recommended hardening recorded as a Delivery Finding. Not dismissed (matches "No Silent Fallbacks" thematically); confirmed + severity-downgraded with rationale.
- `[SEC]` Security clean — `[VERIFIED]` only `yaml.safe_load`/`safe_dump` used (loader.py + test helper `test_120_3_…:107`); no `eval`/`exec`/`pickle`; offender ids/ruleset interpolate into a `PackError` that the REST layer logs server-side (rest.py:158-163), never into an HTTP body; no regex → no ReDoS. Trusted operator/author content path.
- `[TYPE]` Type design (self-covered) — `[VERIFIED]` `mode` is a closed `Literal`; `problems: list[str]` annotated; signature fully typed. The affirmative-allowlist (above) is the more type-faithful expression but the closed Literal makes the current form sound. `loader.py:744-748`.
- `[SIMPLE]` Simplicity (self-covered) — two `sorted()` comprehensions traverse `item_catalog` twice. **LOW**: negligible (≤68 items, once at load) and the two-list split is what lets the message group offenders by reason. The recommended allowlist refactor would also collapse this to one pass — folded into that Improvement, not a standalone ask.
- `[EDGE]` Edge paths (self-covered) — `[VERIFIED]` empty `item_catalog` → both lists empty → early return (covered by ship_weapons test); `inventory is None` → return; all-verbatim → return; mixed verbatim+unprovenanced → raises naming only the offender (test `…among_verbatim_still_rejected`); both classes → both named (test `…names_both…`); native → exempt. No unhandled boundary.
- `[TEST]` Test quality (self-covered) — `[VERIFIED]` no vacuous assertions: every test asserts a named id present/absent in the message or a specific item survived load. The 8 unit tests drive the real `load_genre_pack` (wiring). The new `test_wn_family_pack_genre_baseline_is_verbatim_only` is a GREEN regression canary coupled to 7 live pack slugs — acceptable per the sanctioned `tests/genre/` calibration-against-shipping-content pattern (matches the existing 114-14 genre test).
- `[DOC]` Documentation (self-covered) — `[VERIFIED]` loader docstring rewritten accurately (both reject-classes, native exemption, `ship_weapons` scope); stale "verbatim-only is epic 120" prose removed from both 114-14 test files; the function-name/behavior mismatch is honestly disclosed in the docstring rather than hidden.
- `[RULE]` Project rules (self-covered) — see Rule Compliance below; all applicable rules compliant.

**Data flow traced:** genre `inventory.yaml` → pydantic `InventoryConfig.item_catalog[*].provenance` (Literal-validated) → `_validate_genre_baseline_no_bespoke(rules.ruleset, inventory)` at `loader.py:2079` during `load_genre_pack` → raises `PackError` (fail-loud, names offenders) or returns. Safe: input is operator-authored content, validated by pydantic before the check; failure surfaces as a logged load error, not to end users.

**Pattern observed:** Mirror of the sibling validators in the same module (`_validate_confrontation_beats`, `_validate_class_filter_refs`) — fail-loud `PackError`, named offenders, ruleset-gated. Consistent with the file's established pattern at `loader.py:702-809`.

**Error handling:** Fail-loud per "No Silent Fallbacks"; the only return paths are the documented exemptions (no inventory / native ruleset / all-compliant). `' and '.join(problems)` cannot be empty (guarded by the `if not unprovenanced and not bespoke: return` at loader.py:749).

### Rule Compliance

| Rule (source) | Applies to | Verdict |
|---|---|---|
| No Silent Fallbacks (CLAUDE.md `<critical>`, py #1) | the validator return/raise paths | COMPLIANT today — raises loud naming every offender; returns only on documented exemptions. (Latent denylist note → non-blocking Improvement.) |
| No Stubbing (CLAUDE.md `<critical>`) | the change | COMPLIANT — real implementation, no placeholder. |
| No Source-Text Wiring Tests (server CLAUDE.md) | new tests | COMPLIANT — tests drive `load_genre_pack`, no `read_text()`/grep assertions. |
| Every test suite needs a wiring test | 120-3 unit file | COMPLIANT — all 8 run through the real loader. |
| OTEL Observability Principle | the validator | N/A — load-time content guard, not a runtime subsystem decision; consistent with the existing 114-14 validator (no span). |
| py #8 Unsafe deserialization | yaml usage | COMPLIANT — `safe_load`/`safe_dump` only. |
| py #11 Input validation / ReDoS | parsing boundary | COMPLIANT — no regex; pydantic-validated model fields. |
| py #3 Type annotations | new code | COMPLIANT — fully annotated. |
| py #6 Test quality | new/changed tests | COMPLIANT — no vacuous assertions. |
| SOUL "Crunch in the Genre" / ADR-145 D3 | the rule itself | COMPLIANT — enforces SRD-sourced genre baseline; world tier exempt. |

### Devil's Advocate

Suppose this code is broken. The strongest attack is the one the silent-failure-hunter found: the validator never affirmatively asserts "the mode must be verbatim or derived" — it only hunts two reject-classes and lets everything else through. If a future developer widens `ItemProvenance.mode`'s `Literal` to add, say, `"community"` or `"adapted"` and forgets to revisit this function, a WN-family genre baseline full of `community`-mode items would load silently, defeating the whole point of the rule and violating "No Silent Fallbacks." I confirmed this is *latent*, not live: pydantic enforces the closed `Literal` at parse time, so today no such item can exist at runtime — but the code's safety depends on a type two files away, which is exactly the kind of coupling that rots. That is why I recorded the affirmative-allowlist hardening as a finding rather than nothing.

What else could break it? A confused content author who writes `mode: Verbatim` (capitalized) — pydantic rejects it at parse with a loud `ValidationError` before this validator, so it fails loud, good. An item with `mode: verbatim` but `license: na` (self-inconsistent verbatim) — the `ItemProvenance` model validator rejects it at parse, never reaching here, good. A pack with a garbage `ruleset:` string — `_is_without_number` → `get_ruleset_module` raises `UnknownRulesetError` loud, not a silent skip, good. A huge `item_catalog` — two O(n) passes, but n≤68 and runs once at load, no DoS. Duplicate ids — `sorted()` would list duplicates, cosmetically noisy but not wrong. A malicious item id with shell/format metacharacters — lands only in a Python exception string logged server-side, no shell/SQL/HTML sink (security confirmed). A stressed filesystem returning a partial `inventory.yaml` — pydantic load fails upstream, not this code's concern. The honest conclusion: no live break exists; the one real weakness is the future-proofing gap, correctly classed non-blocking.

**Handoff:** To SM (Vizzini) for finish-story.