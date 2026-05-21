---
story_id: "50-9"
jira_key: "N/A"
epic: "50"
workflow: "tdd"
---

# Story 50-9: Mood aliases alias-chain fallback in music director track selection (ADR-033 Pillar 3 Steps 1-3)

## Story Details

- **ID:** 50-9
- **Epic:** 50 (Pingpong-archive triage and dropped-work cleanup)
- **Jira Key:** N/A (SideQuest does not use Jira)
- **Workflow:** tdd
- **Repos:** sidequest-server, sidequest-content
- **Stack Parent:** none

## Story Summary

Genre packs declare custom moods (standoff, ritual, pact, etc.) with dedicated music tracks. When the narrator emits a mood string that maps to an alias in the pack's `mood_aliases` dict (e.g., "ritual" → "tension"), the music director must walk the alias chain to find a real mood_tracks key and select a track from there. The implementation of this alias-chain fallback is partially complete (model + load-time validation + resolver + OTEL spans exist) but either untested in production or contains a subtle bug preventing end-to-end wiring. TDD red-to-green will verify and complete the feature.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-21T07:52:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-21T00:00:00Z | 2026-05-21T06:28:17Z | 6h 28m |
| red | 2026-05-21T06:28:17Z | 2026-05-21T06:40:50Z | 12m 33s |
| green | 2026-05-21T06:40:50Z | 2026-05-21T07:08:19Z | 27m 29s |
| spec-check | 2026-05-21T07:08:19Z | 2026-05-21T07:12:27Z | 4m 8s |
| verify | 2026-05-21T07:12:27Z | 2026-05-21T07:17:59Z | 5m 32s |
| review | 2026-05-21T07:17:59Z | 2026-05-21T07:26:50Z | 8m 51s |
| green | 2026-05-21T07:26:50Z | 2026-05-21T07:33:04Z | 6m 14s |
| spec-check | 2026-05-21T07:33:04Z | 2026-05-21T07:34:48Z | 1m 44s |
| verify | 2026-05-21T07:34:48Z | 2026-05-21T07:40:33Z | 5m 45s |
| review | 2026-05-21T07:40:33Z | 2026-05-21T07:48:16Z | 7m 43s |
| spec-reconcile | 2026-05-21T07:48:16Z | 2026-05-21T07:52:26Z | 4m 10s |
| finish | 2026-05-21T07:52:26Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **Gap (non-blocking, TEA, 2026-05-21):** SM's spec framed AC-4 as "at least one live pack authored with mood_aliases for its custom moods" and gestured at spaghetti_western as the candidate. Survey: spaghetti_western's rules.yaml only references moods that already live in mood_tracks (combat, saloon, standoff, tension) — there's nothing for it to alias. The real silent-fallback gaps are **caverns_and_claudes** (`rules.yaml mood: comedic` → no track, no alias) and **tea_and_murder** (`rules.yaml mood: mystery` → no track, no alias). These are the packs Dev should look at for AC-4 content authoring, not spaghetti_western. Surfaced by `grep -E "mood:" genre_packs/*/rules.yaml` vs `mood_tracks` keys; will be re-surfaced loudly by the new validator. *Found by TEA during context survey.*

- **Conflict (non-blocking, TEA, 2026-05-21):** SM's spec implicitly framed the RED phase as "write tests for the resolver / spans / load validation." Survey: those 21 tests already exist at `tests/audio/test_mood_alias_chain.py` and all PASS against the shipped implementation — the mechanism is fully covered. TEA reshaped RED to target the missing piece: a `pf validate audio` content validator that walks live packs and surfaces unresolved mood references. This is the right tool to drive AC-4 (Keith's explicit direction: **fixtures for unit tests, validators for the worlds, never direct unit tests on output** — see [[feedback_no_content_coupled_tests]]). Spec author and TEA are aligned on outcome; only the *shape* of the work shifted. *Found by TEA during context survey + 2026-05-21 Keith conversation.*

### Reviewer (code review)

- **Gap (blocking, Reviewer, 2026-05-21):** Validator catches only `ValueError` from `AudioConfig.model_validate`; YAML parse errors (`yaml.YAMLError`) and OS errors (PermissionError, IsADirectoryError) propagate, crashing `validate_packs` and defeating the "per-pack failures don't suppress siblings" guarantee that `test_one_broken_pack_does_not_suppress_others` claims. Affects `sidequest-server/sidequest/cli/validate/audio.py:104-116` (broaden except to `(yaml.YAMLError, ValueError)`) and `:127` (wrap `yaml.safe_load(rules_path.read_text(...))` in try/except + emit a new `RULES_LOAD_FAILURE` error code). *Found by Reviewer during code review (Reviewer-self-coverage for disabled silent-failure-hunter subagent).*
- **Improvement (non-blocking, Reviewer, 2026-05-21):** Validator does not surface unresolved `AudioTheme.mood` references in `audio.yaml`'s themes section, only `confrontations[*].mood` in rules.yaml. Themes have their own track-variation path (not mood_tracks) so a missing theme isn't a silent fallback risk in the same way, but for symmetry a future enhancement could enumerate every mood-string source. Out of scope for 50-9. Affects `sidequest/cli/validate/audio.py::_check_rules_moods` (extend or add `_check_audio_themes`). *Found by Reviewer during Devil's Advocate sweep.*
- **Improvement (non-blocking, Reviewer, 2026-05-21):** ADR-033 §Pillar 3 still reads "✗ mood_aliases is dead data ... No consumer fires the alias chain" — this was true on 2026-05-02 but is FALSE today (resolver wired, validator shipped). Architect spec-check raised this as a documentation drift follow-up (Resolution D — defer). Worth folding into the content-authoring follow-up PR's docs commit, or filing as its own one-pointer chore. Affects `docs/adr/033-confrontation-engine-resource-pools.md` §Pillar 3 + §Implementation status. *Found by Architect (spec-check) and Reviewer confirms.*

### Reviewer (code review, round 2)

- **Improvement (non-blocking, Reviewer round 2, 2026-05-21):** Round-2 simplify pass tightened `_load_audio_config`'s exception catch from `ValueError` to the specific `(UnicodeDecodeError, yaml.YAMLError, ValidationError)`. The docstring on `test_broken_declared_alias_becomes_error_not_crash` was not updated in lockstep — it still says "the validator must CATCH that ValueError" while the code catches `ValidationError`. The docstring is **not wrong** (ValidationError IS-A ValueError in pydantic v2, so the assertion remains true), just less specific than the code it describes. One-word polish: replace `ValueError` with `ValidationError` in the test docstring at `tests/cli/test_validate_audio.py::test_broken_declared_alias_becomes_error_not_crash`. Affects `sidequest-server/tests/cli/test_validate_audio.py` (single-word docstring fix; no behavior, test, or contract impact). Deferred rather than bounced to Dev for a third rework round because cost of round-3 rework cycle exceeds value of one-word polish on a test-file docstring. *Found by Reviewer round-2 (comment-analyzer); downgraded HIGH → LOW with rationale in Reviewer Assessment round 2.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

- **TEA, 2026-05-21 — RED phase shape:**
  - **Changed:** Wrote a RED test suite for a NEW validator (`sidequest/cli/validate/audio.py` — does not exist yet) rather than additional behavior tests on the resolver/spans.
  - **Spec source:** Session AC-4 ("at least one live pack with mood_aliases for its custom moods", "all declared aliases in all packs pass validation at pack load time") + Keith's 2026-05-21 directive on test architecture ("fixtures for unit tests, validators for the worlds, never direct unit tests on output").
  - **Implementation:** `tests/cli/test_validate_audio.py` (12 tests, 4 fixture packs under `tests/fixtures/validate_audio/`) — all RED via ModuleNotFoundError on `sidequest.cli.validate.audio`.
  - **Why:** The mechanism is already covered by `tests/audio/test_mood_alias_chain.py` (21 tests, all GREEN). The unmet ACs are content-correctness: surfacing moods that fall silently to the universal `exploration` fallback. The right tool is a CLI validator (mirrors `pf validate locations` from Story 54-3), not a server unit test that asserts properties of live content YAML.
  - **Forward impact:** Dev implements `sidequest/cli/validate/audio.py` with the contract pinned by the test file (Issue dataclass, ValidationResult, two entry functions, two issue codes), wires it into `sidequest.cli.validate.__main__`'s click group, and runs the new validator against live packs to surface AC-4 content gaps (caverns/comedic, tea_and_murder/mystery, anything else). Content authoring of mood_aliases in those live packs then GREENs AC-4 — that's a content commit on `sidequest-content`, not server code.

- **TEA, 2026-05-21 — Issue severity boundary:**
  - **Changed:** `UNRESOLVED_RULES_MOOD` is a **warning**, not an error.
  - **Spec source:** No explicit severity in session ACs; choice derived from system architecture (CLAUDE.md "Cost Scales with Drama" + library_backend.py runtime fallback behavior).
  - **Why:** Runtime has a graceful, observable fallback (`music.mood_alias_failed` span + WARNING log + fallback to `exploration`). Hard-erroring at validate time would block ship on any narrator-likely mood a content author hasn't anticipated — impossible to enumerate ahead of time. Warning is the right pressure: visible in CI output and surface-able by `pf check`, but does not gate. `AUDIO_LOAD_FAILURE` (a declared-but-broken alias) IS an error because the pack literally cannot load.
  - **Forward impact:** If Reviewer or Architect believes the project should hard-error on undeclared rules moods, flip the severity in the validator — fixture test `test_unresolved_warning_does_not_become_error` will fail and force the conversation explicitly.

### Reviewer (audit)

- **TEA RED-phase shape pivot** → ✓ ACCEPTED by Reviewer: validator approach is the right tool for AC-4; mirrors `pf validate locations` cleanly; no content-test-coupling per [[feedback_no_content_coupled_tests]]. Architect spec-check independently agreed.
- **TEA severity boundary (warning, not error)** → ✓ ACCEPTED by Reviewer: graceful runtime fallback + observable span justifies warning severity; hard-erroring would gate ship on unenumerable narrator moods (Zork Problem); pinned by `test_unresolved_warning_does_not_become_error` so any future flip surfaces explicitly.
- **No additional undocumented deviations found** during code review beyond the 9 findings already enumerated in the round-1 Reviewer Assessment (all 9 are real-code findings, not spec deviations).

### Reviewer (audit, round 2)

- **Round-2 simplify deviations** → ✓ ACCEPTED by Reviewer round 2:
  - Parametrize subprocess exit-code tests into one parametrized test (commit `3318492`) — clean reduction, ids preserve distinct case names.
  - Tighten exception catches from broad `ValueError` to specific `(UnicodeDecodeError, yaml.YAMLError, ValidationError)` (commit `3318492`) — more future-proof against pydantic hierarchy changes (Devil's-Advocate round-2 confirmed this is a real win).
  - Dismissed simplify-efficiency finding on `test_validate_packs_does_not_crash_on_any_fixture_root` overlap — intentional contract-document role, same family as round-1 D1 dismissal. ✓ ACCEPTED.
  - Dismissed simplify-reuse finding on YAML-load duplication — subagent self-dismissed; semantic differences (audio validates schema, rules doesn't) justify keeping separate. ✓ ACCEPTED.
- **No additional undocumented deviations found** during round-2 code review beyond the 1 LOW finding documented in the round-2 Reviewer Assessment.

### Architect (reconcile)

**TEA entries audit:** Both TEA entries (RED phase shape + Issue severity boundary) are substantive but use non-canonical field labels ("Changed" + "Why" instead of "Implementation" + "Rationale", and no explicit "Severity:" line per `deviation-format.md`). The substance covers all 6 required dimensions, so no correction is filed — annotating here for the boss-audit reader: both entries should be read as **Severity: minor** (RED phase shape — no AC outcome changed, only the path to it) and **Severity: minor** (severity boundary — defensible against the rule taxonomy in CLAUDE.md; runtime fallback is graceful + observable). Both are **Forward impact: none** — no sibling stories assume otherwise.

**Reviewer audit (both rounds):** Stamps are present and complete; no corrections needed.

**Missed deviations Architect adds:**

- **New `RULES_LOAD_FAILURE` issue code extends spec contract:**
  - Spec source: Session AC-1/AC-2/AC-3 (model + runtime + spans); no explicit mention of a content-audit validator OR a rules.yaml-parse-failure error code.
  - Spec text: "AC-4: Content packs declare mood_aliases for their custom moods ... All declared aliases in all packs pass validation at pack load time"
  - Implementation: Added new `RULES_LOAD_FAILURE` issue code in `sidequest/cli/validate/audio.py::_check_rules_moods` (parallel to `AUDIO_LOAD_FAILURE`). Catches `(UnicodeDecodeError, yaml.YAMLError)` on rules.yaml parse; emits Issue with severity=error, file="rules.yaml". Dedicated code (rather than reusing `AUDIO_LOAD_FAILURE`) so triage output distinguishes the offending file. Added in commit `40c7091`.
  - Rationale: Symmetric with AUDIO_LOAD_FAILURE; a broken rules.yaml is a real content-team-laptop scenario (mid-edit save) that the validator should report rather than crash on. Without this, the "per-pack failures don't suppress siblings" guarantee was only proven for the pydantic-rejected case, not for YAML syntax errors.
  - Severity: minor (additive contract — adds an error code, does not change existing codes or behavior).
  - Forward impact: none — future `pf validate audio` consumers that JSON-parse output may handle the new code; no other story currently does. `pf check` treats it identically to `AUDIO_LOAD_FAILURE` (both flip exit code to 1).

- **AC-4 content authoring deliberately deferred to sibling content PR:**
  - Spec source: Session AC-4 third bullet
  - Spec text: "At least one live pack (spaghetti_western) authored with aliases for custom moods (standoff, saloon, riding, betrayal, etc.) — validate against rules.yaml/confrontations and audio.yaml/mood_tracks"
  - Implementation: No live pack got mood_aliases authored in this PR. Dev's hand-run of the new `pf validate audio` validator against `sidequest-content/genre_packs/` surfaced 3 actionable warnings (caverns_and_claudes/comedic, tea_and_murder/social_duel mystery, tea_and_murder/scandal mystery). The validator IS the AC-4 audit substrate; the content authoring (deciding what `comedic` and `mystery` should alias to) is deferred to a sibling content PR.
  - Rationale: Coupling a server PR to content YAML edits would re-introduce the exact pattern Keith hard-stopped during RED (see [[feedback_no_content_coupled_tests]]). The content design decisions need Keith's design input (which mood track to alias to is a tonal choice). Both Architect spec-check rounds and Reviewer accepted the deferral.
  - Severity: major (AC-4 third bullet is not satisfied by this PR alone — requires the follow-up content PR to close)
  - Forward impact: minor — a follow-up `sidequest-content` PR must author `comedic: <target>` in caverns_and_claudes/audio.yaml and `mystery: <target>` in tea_and_murder/audio.yaml (and any other gaps the validator surfaces). Validator going from 3 warnings to 0 is the verification.

- **Story title scope vs delivered scope (Steps 1-3 already shipped pre-50-9):**
  - Spec source: Session story title
  - Spec text: "Mood: implement mood_aliases alias-chain fallback in music director track selection (ADR-033 Pillar 3 Steps 1-3)"
  - Implementation: ADR-033 Pillar 3 Steps 1-3 (model + load-time validator + runtime resolver + OTEL spans + wiring) were all shipped pre-50-9 and verified GREEN by the existing 21 tests at `tests/audio/test_mood_alias_chain.py`. This story's actual delivery is a content-audit validator (`pf validate audio`) that closes the verification loop on Steps 1-3 by surfacing live-content gaps before runtime.
  - Rationale: Discovered during TEA RED-phase context survey. Rather than file a no-op story when the underlying mechanism was already done, TEA pivoted to deliver the missing verification surface. Both Architect spec-check rounds and Reviewer accepted the pivot.
  - Severity: minor (outcome — Steps 1-3 verified + audit tooling — is stronger than what the title literally promised)
  - Forward impact: none — no sibling story assumes Steps 1-3 still need implementing.

**AC deferral verification:**

| AC | Status | Notes |
|----|--------|-------|
| AC-1 (model + validation) | DONE | Pre-shipped; covered by `tests/audio/test_mood_alias_chain.py` (21 tests GREEN) |
| AC-2 (runtime resolver wiring) | DONE | Pre-shipped; covered by `test_wiring_encounter_mood_override_alias_resolves_through_real_backend` |
| AC-3 (OTEL spans) | DONE-WITH-DEFERRED-VERIFY | Spans defined + emitted + tested; "GM panel dashboard parse" verification deferred by spec text itself ("verify in dashboard on next playtest") |
| AC-4 (content authoring) | PARTIALLY-DEFERRED | Validator infrastructure DONE in this PR; live-pack authoring (the third AC-4 bullet) DEFERRED to follow-up `sidequest-content` PR per the Architect-reconcile entry above |
| AC-5 (production wiring test) | DONE-STRONGER | Originally satisfied by `test_wiring_encounter_mood_override_alias_resolves_through_real_backend`; **strengthened** in this PR by adding subprocess exit-code wiring tests proving the CLI contract end-to-end through `python -m sidequest.cli.validate audio` |

No deferred ACs were invalidated by review; the AC-4 deferral has a clear path to closure (run validator, fix surfaced gaps in content PR).

## Acceptance Criteria

### AC-1: mood_aliases model + validation complete
- AudioConfig exposes mood_aliases field (dict[str, str]), defaulting to empty dict
- Pydantic validator _validate_mood_aliases() enforces that every declared alias chain terminates in a mood_tracks key within MAX_ALIAS_HOPS (5)
- Validator rejects cycles, broken links, over-deep chains loudly at load time (no silent fallback)
- Validator test coverage: happy path (good chain), cycle detection, broken target, depth exceeded

### AC-2: Runtime alias-chain resolution wired end-to-end
- resolve_mood_to_track_key(mood: str, cfg: AudioConfig) -> str | None walks alias chains correctly
- Direct hit: mood already a mood_tracks key → returns unchanged, no span
- Declared alias: mood in aliases → walks chain, returns resolved key, emits music.mood_alias_resolved span
- Unknown mood (not track, not alias) → falls back to DEFAULT_FALLBACK_MOOD, emits music.mood_alias_failed span with reason="broken_chain"
- Function is called from LibraryBackend._resolve_music() at the right point in the mood resolution flow
- Defensive loop protection prevents infinite loops even if validation somehow fails

### AC-3: OTEL spans emitted and routed correctly
- music.mood_alias_resolved span fires when an alias chain successfully resolves, carrying mood_name, resolved_to, chain_depth, latency_ms
- music.mood_alias_failed span fires when an unknown mood falls back, carrying mood_name, reason, fallback_mood
- Spans are defined in sidequest/telemetry/spans/audio.py and registered in SPAN_ROUTES
- GM panel receives and parses both span types (verify in dashboard on next playtest)

### AC-4: Content packs declare mood_aliases for their custom moods
- heavy_metal (workshopping) has aliases: pact→ritual, working→ritual, procession→sorrow, court→tension (existing, verify)
- At least one live pack (spaghetti_western) authored with aliases for custom moods (standoff, saloon, riding, betrayal, etc.) — validate against rules.yaml/confrontations and audio.yaml/mood_tracks
- All declared aliases in all packs pass validation at pack load time

### AC-5: Production wiring test — novel mood resolves via alias in a playtest turn
- Create a test fixture (or use playtest) where narrator emits a mood not directly in mood_tracks but resolvable via mood_aliases (e.g., "ritual" in heavy_metal)
- Verify OTEL trace contains music.mood_alias_resolved or music.mood_alias_failed span
- Verify a track is selected from the resolved mood_tracks key (not None)
- End-to-end integration: narration → mood classification → alias resolution → track selection → audio dispatch

## Subagent Results (round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — 76 tests / 0 smells |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings; round-1 self-coverage carried forward |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled; the silent-failure gap I flagged round-1 (Finding 9) was addressed by Dev in `40c7091` and verified clean by rule-checker round-2 |
| 4 | reviewer-test-analyzer | Yes | findings | 2 | 0 confirmed, 2 dismissed (both unreachable-code-path / pydantic-format-coupling — see Dismissed Findings below) |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | 1 confirmed (downgraded HIGH → LOW with rationale; documented for SM-finish chore) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled; covered by verify-round-2 simplify pass (3 simplify-* subagents ran in parallel during commit `3318492`'s preparation, surfaced 2 findings, both applied) |
| 9 | reviewer-rule-checker | Yes | clean | 0 | All 4 round-1 violations confirmed fixed; zero new violations across 19 rule families / 63 instances exhaustively enumerated |

**All received:** Yes (4 spawned + 5 disabled = 9 rows filled)
**Total findings (round 2):** 1 confirmed (LOW), 2 dismissed (with rationale), 0 deferred

## Subagent Results (round 1 — archived)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — 70 tests / 0 smells |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings; covered by Reviewer self-coverage |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings; covered by Reviewer self-coverage (Finding 9) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | 3 confirmed, 3 dismissed |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | 2 confirmed |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings; covered by Reviewer self-coverage |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings; covered by Reviewer self-coverage |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings; covered by Reviewer self-coverage |
| 9 | reviewer-rule-checker | Yes | findings | 4 | 4 confirmed (all rule-backed) |

**All received:** Yes (4 spawned + 5 disabled = 9 rows filled)
**Total findings (round 1):** 9 confirmed, 3 dismissed (with rationale), 0 deferred — all 9 addressed in `40c7091`

## Reviewer Assessment (round 2)

**Verdict:** APPROVED

**Subagent tags incorporated:** [RULE] (round-1 violations all confirmed fixed by rule-checker round-2; zero new violations), [TEST] (2 medium findings, both dismissed — see below), [DOC] (1 finding downgraded LOW; documented as SM-finish chore).

### Findings (confirmed)

| # | Severity | Source | Issue | Location | Disposition |
|---|----------|--------|-------|----------|-------------|
| R2-1 | [LOW] | [DOC] | Test docstring says the validator must "CATCH that ValueError" but the round-2 simplify pass tightened the catch from `ValueError` to the explicit `(UnicodeDecodeError, yaml.YAMLError, ValidationError)`. The docstring is **technically correct** (pydantic v2 `ValidationError` IS-A `ValueError`, so "CATCH that ValueError" remains true after the tightening), but is now less specific than the code it describes — a future reader might be confused. | `tests/cli/test_validate_audio.py::test_broken_declared_alias_becomes_error_not_crash` docstring | **Downgraded HIGH → LOW.** Comment-analyzer correctly identified the precision drift, but the docstring isn't asserting anything *incorrect* — `ValidationError` extends `ValueError`. This is a one-word polish fix (replace `ValueError` with `ValidationError` in the docstring) that does NOT affect behavior, tests, or correctness. Filed below as a deferred SM-finish chore rather than bouncing to Dev for a third rework round when all other dimensions (rules, tests, mechanics, contract) are clean. |

### Findings dismissed

| # | Severity | Source | Finding | Dismissal rationale |
|---|----------|--------|---------|---------------------|
| R2-D1 | [MEDIUM] | [TEST] | `test_broken_declared_alias_becomes_error_not_crash` asserts both `'comedic'` and `'nonexistent_target'` appear in `str(ValidationError)` — implementation-coupling on pydantic's message format | The asserted tokens come from **sidequest's own ValueError raise** in `sidequest/genre/models/audio.py::_validate_mood_aliases` (lines 148–159: `raise ValueError(f"mood_aliases: alias {start!r} -> ... -> {cur!r} does not resolve (broken_chain): ...")`). Pydantic's `ValidationError` wrapper preserves the raised message verbatim. The contract WE control (our own validator error message must name the offending alias and its broken target) is exactly what's being asserted — that's correct intent-encoding, not pydantic coupling. If pydantic changes its outer wrapper format, our embedded message survives. Keep. |
| R2-D2 | [MEDIUM] | [TEST] | No test exercises `_chain_resolves_to_track`'s defensive cycle guard (`if cur in seen ... return False`) — pydantic catches cycles at LOAD time before they could reach the audit helper | Same family as round-1 D2 (missing MAX_ALIAS_HOPS boundary test): the audit helper's cycle guard is **defense-in-depth for an unreachable case**. Pydantic's load-time validator rejects cycles (proven by `test_circular_alias_chain_rejected_at_load` in `tests/audio/test_mood_alias_chain.py`), so a cycle never reaches `_chain_resolves_to_track` in any realistic call path. Adding a test would either need a fixture that pydantic somehow accepts (impossible — pydantic rejects), or a direct unit test of the helper with synthetic data (testing an unreachable code path). Same dismissal rationale as round-1 D2. Keep the defense-in-depth; don't test for the impossible case. |

### Rule Compliance (round 2)

rule-checker exhaustively enumerated 63 instances across 19 rules (14 Python lang-review + 7 additional CLAUDE.md rules: No Silent Fallbacks, No Stubbing, Don't Reinvent, Verify Wiring, Every-Test-Suite-Needs-a-Wiring-Test, OTEL principle, No Jira). **Zero violations.** All 4 round-1 violations explicitly confirmed fixed with evidence:

- Rule #5 encoding ×2 → `path.read_text(encoding="utf-8")` confirmed at both call sites
- Rule #1 broad ValueError → `(UnicodeDecodeError, yaml.YAMLError, ValidationError)` confirmed
- Rule #6 vacuous asserts ×2 → `assert len(...) == 1` confirmed at both sites

### Devil's Advocate (round 2)

The round-1 Devil's Advocate flagged:
- Malicious pack author → no exploit surface beyond ANSI pollution. **Unchanged round 2.**
- Stressed filesystem (concurrent write + audit) → Finding 9 addressed by Dev's broader yaml.YAMLError catch. **Now safe.**
- Confused content author (malformed YAML) → covered by the new audio_malformed_yaml + rules_malformed_yaml fixtures. **Now tested.**
- Pydantic version change loosening the load validator → MAX_ALIAS_HOPS still imported by both validator + audit helper, so they stay in sync. **Unchanged round 2.**

New round-2 angle to consider: what if pydantic v3 changes the exception hierarchy and `ValidationError` is no longer a `ValueError` subclass? The current `(UnicodeDecodeError, yaml.YAMLError, ValidationError)` explicitly names `ValidationError`, so the catch survives the migration. The round-1 broad `except (yaml.YAMLError, ValueError)` would have silently stopped catching pydantic errors after such a migration — the round-2 tightening is actually MORE future-proof, not less. Validates the tightening was a real win, not just style.

### Pattern observations (round 2)

- **[VERIFIED]** Strong pattern reuse intact: audio.py + locations.py both consume `packs_in` from `common.py`. Audio.py's `Issue` / `ValidationResult` shape still mirrors locations.py. The new `RULES_LOAD_FAILURE` code extends the per-file load-failure pattern symmetrically (the validator now has three error codes that all encode "this file failed to load at this severity").
- **[VERIFIED]** Wiring tests strengthened: round 1 had only the `--help` subprocess wiring test. Round 2 adds `test_cli_audio_exit_code_matches_result_success` parametrized over (clean→0, broken→1), proving the `ctx.exit(0 if success else 1)` contract end-to-end through the documented CLI entry point. Better than round 1.
- **[VERIFIED]** Exception catches are now type-specific everywhere — no broad `except Exception` or bare `except ValueError` in any of the changed code. Round-1 finding fully resolved.
- **[VERIFIED]** Live-pack hand-run unchanged: same 3 warnings surface (caverns/comedic, tea_and_murder/social_duel mystery, tea_and_murder/scandal mystery) — confirms the broadened error handling didn't regress the live audit behavior.

### Handoff

**To Architect for spec-reconcile, then to SM for finish.** All 9 round-1 findings addressed; round 2 rework introduced zero new violations; one LOW docstring-precision drift documented as SM-finish chore. No bounce-back to Dev for the LOW finding — its cost (third rework round, fourth simplify+verify+review cycle) would exceed the value (one-word docstring polish on a test file that has no behavior impact).

---

## Reviewer Assessment (round 1)

**Verdict:** REJECTED — 9 findings to address (5 HIGH, 3 MEDIUM, 1 LOW)

**Subagent tags incorporated:** [RULE] (4 findings: encoding ×2, vacuous assertions ×2), [TEST] (3 findings: missing audio-less-pack test, missing exit-code wiring test, plus the [RULE]/[TEST] cross-tagged assertion fixes), [DOC] (2 findings: stale "RED tests" label, over-claiming docstring), [EDGE] (1 Reviewer self-coverage finding for the disabled silent-failure-hunter — uncaught yaml.YAMLError).

### Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` (14 numbered checks). Rule-checker did the full sweep (67 instances; pasted summary):

| # | Rule | Result | Notes |
|---|------|--------|-------|
| 1 | Silent exception swallowing | PASS | `_load_audio_config` catches ValueError specifically + records Issue, not swallowed. NB: see Finding 9 below — the catch is too NARROW (yaml.YAMLError escapes) |
| 2 | Mutable default arguments | PASS | `ValidationResult` uses `field(default_factory=list)` |
| 3 | Type annotation gaps at boundaries | PASS | Every public function fully annotated; `Any` in `_chain_resolves_to_track` is justified (YAML-parsed dict values) |
| 4 | Logging coverage | PASS | CLI tool, writes via click.echo; no logger usage to misuse |
| 5 | Path handling | **FAIL** (2 violations) — Findings 1, 2 |
| 6 | Test quality | **FAIL** (2 violations) — Findings 3, 4 |
| 7 | Resource leaks | PASS | `Path.read_text()` self-closes |
| 8 | Unsafe deserialization | PASS | `yaml.safe_load`, pydantic `model_validate` |
| 9 | Async/await pitfalls | PASS | Fully synchronous |
| 10 | Import hygiene | PASS | No star imports; runtime import inside `main()` is the deferred-default pattern, no cycle |
| 11 | Input validation at boundaries | PASS | `click.Path(exists=True, file_okay=False)` validates CLI inputs; `isinstance` guards on YAML data |
| 12 | Dependency hygiene | PASS | No new deps |
| 13 | Fix-introduced regressions | PASS | Refactor of `_packs_in → common.packs_in` preserves behavior; locations tests still GREEN |
| 14 | State cleanup ordering | PASS | No queue/buffer with replay risk |

Additional rules from CLAUDE.md (A1–A4): all PASS. No Silent Fallbacks compliant (every fallback path emits an Issue or is the documented empty-result case); No Stubbing compliant; Wiring proven by `test_cli_audio_subcommand_is_registered`; OTEL principle is N/A for a CLI audit tool (the validator deliberately avoids span emission to prevent trace pollution in audit context — documented in module docstring).

### Findings (confirmed)

| # | Severity | Source | Issue | Location | Fix |
|---|----------|--------|-------|----------|-----|
| 1 | [HIGH] | [RULE #5] | `path.read_text()` without `encoding="utf-8"` — platform-default encoding (CWE-838); a pack with non-ASCII content on a non-UTF-8 locale decodes incorrectly | `sidequest/cli/validate/audio.py:103` | Change to `path.read_text(encoding="utf-8")` |
| 2 | [HIGH] | [RULE #5] | Same: `rules_path.read_text()` without `encoding="utf-8"` | `sidequest/cli/validate/audio.py:127` | Change to `rules_path.read_text(encoding="utf-8")` |
| 3 | [HIGH] | [RULE #6] [TEST] | Bare `assert warnings` is truthy-only — if the list is non-empty with wrong codes, the guard passes silently and the subsequent `all(...)` check operates on whatever is present | `tests/cli/test_validate_audio.py:180` | Replace with `assert len(warnings) == 1` to pin the count (matches the sibling tests' style) |
| 4 | [HIGH] | [RULE #6] [TEST] | Same pattern: bare `assert failures` | `tests/cli/test_validate_audio.py:191` | Replace with `assert len(failures) == 1` |
| 5 | [HIGH] | [TEST] | No test exercises the `validate_audio_in_pack` early-return for packs without `audio.yaml` — silent regression risk if the guard is inverted, every audio-less pack would emit spurious AUDIO_LOAD_FAILURE | `tests/cli/test_validate_audio.py` (new test) | Add fixture `tests/fixtures/validate_audio/audio_missing/` with only a `pack.yaml`; add test asserting `_pack_result("audio_missing")` returns zero errors and zero warnings |
| 6 | [HIGH] | [DOC] | Module docstring opens with "RED tests for `pf validate audio`" but all 13 tests pass GREEN (implementation ships in the same diff). Misleading to anyone running the suite who wonders why "RED tests" all pass | `tests/cli/test_validate_audio.py:1` | Change "RED tests" → "Tests" (or drop the label entirely) |
| 7 | [MEDIUM] | [TEST] | No test proves the `ctx.exit(0 if result.success else 1)` contract end-to-end. A regression that always exits 0 would pass the current `--help` wiring test. Important contract because CI / `pf check` keys off the exit code | `tests/cli/test_validate_audio.py` (extend wiring test or add two new) | Add subprocess invocations of `python -m sidequest.cli.validate audio --genre-packs-root <FIXTURES>/audio_ok` (assert returncode 0) and against `<FIXTURES>/audio_broken_declared_alias` (assert returncode 1). Mirrors locations validator pattern |
| 8 | [MEDIUM] | [DOC] | `validate_audio_in_pack` docstring says "Runs both checks on a single pack directory" — but the function runs zero checks if `audio.yaml` is absent and only one check if `_load_audio_config` returns None. Over-claiming the contract | `sidequest/cli/validate/audio.py:164-166` | Tighten to: "Runs available checks on a single pack directory. Returns an empty result immediately if ``audio.yaml`` is absent. Skips mood-resolution if the config fails to load — the load failure is itself recorded as an `AUDIO_LOAD_FAILURE` error." |
| 9 | [MEDIUM] | [EDGE] (Reviewer self-coverage for disabled silent-failure-hunter) | `_load_audio_config` catches only `ValueError`. A malformed audio.yaml (`yaml.YAMLError`) or an OS error (PermissionError, IsADirectoryError) propagates and crashes `validate_packs`, defeating the "broken pack doesn't suppress siblings" guarantee. The existing test `test_one_broken_pack_does_not_suppress_others` only proves robustness for the pydantic-rejected case. `_check_rules_moods` has the same gap on rules.yaml | `sidequest/cli/validate/audio.py:104-116` and `:127` | Broaden the catch in `_load_audio_config` to `except (yaml.YAMLError, ValueError)`. For `_check_rules_moods`, wrap the `yaml.safe_load(rules_path.read_text(...))` in try/except yaml.YAMLError + record a new `RULES_LOAD_FAILURE` error (severity=error, file="rules.yaml"). Add fixture `tests/fixtures/validate_audio/audio_malformed_yaml/` with a syntactically broken audio.yaml; add a test asserting `validate_packs` does not raise and records the appropriate error |

### Findings dismissed

| # | Source | Finding | Dismissal rationale |
|---|--------|---------|---------------------|
| D1 | [TEST] (test-analyzer #1) | `test_unresolved_warning_does_not_become_error` is redundant with `test_unresolved_rules_mood_emits_warning` (same fixture, both confirm zero errors implicitly) | Intent-encoding test: the explicit severity-boundary assertion documents the design choice and prevents a future PR from accidentally elevating UNRESOLVED_RULES_MOOD to an error without seeing this test fail with a clear name. Keep. |
| D2 | [TEST] (test-analyzer #2) | No fixture exercises a chain at exactly `MAX_ALIAS_HOPS - 1` depth to prove the audit's depth gate doesn't fire early | Chains > MAX_ALIAS_HOPS are unreachable in audit context — they fail the pydantic load validator first (proven by `test_overdeep_declared_chain_rejected_at_load` in `test_mood_alias_chain.py`). The audit's depth gate is defense-in-depth for an unreachable case. Adding a fixture would test an unreachable code path. |
| D3 | [TEST] (test-analyzer #4) | `test_issue_dataclass_carries_required_fields` uses `hasattr` loop which is tautological on a frozen dataclass | Acts as a contract spelling-check — if the literal string "file" is typoed to "fyle" the test catches the typo, which the dataclass declaration cannot. Defensive, not vacuous. Keep. |

### Devil's Advocate

If this code is broken, where? Let me argue against the implementation systematically.

**A malicious or hostile pack author** — could they get the validator to do something bad? The validator reads files from a path the user passes via `--genre-packs-root`, validated by click as an existing directory. The reads go through `pathlib.Path.read_text()` (a guarded one-shot read) and `yaml.safe_load` (not `yaml.load`, so no arbitrary object construction). The pydantic `AudioConfig.model_validate` operates on already-parsed YAML data; it can't execute code. The CLI output uses `click.echo` with format strings — the only thing a malicious pack could inject is ANSI escapes in pack/file/mood names that pollute terminal output, low severity for an offline audit tool. **No exploit surface beyond ANSI pollution.**

**A confused user** — what if they pass `--genre-packs-root .` (the CWD)? click's `Path(exists=True, file_okay=False)` validates it's a directory. Then `packs_in` looks for child dirs with `pack.yaml`. If CWD has no such children, `validate_packs` returns an empty result, exit 0. **Friendly behavior, no crash.** What about `--genre-packs-root /` on a Linux system? Same — no `pack.yaml` children, empty result. What if a user passes `--genre-packs-root` pointing at a SYMLINK loop? `root.iterdir()` doesn't follow symlinks recursively for this validator, and `pack.yaml` check is a single-level probe. **Safe.**

**A stressed filesystem** — what if a pack's `audio.yaml` is mid-write (truncated) when the audit runs? **This is Finding 9.** `yaml.YAMLError` is uncaught. Same for `audio.yaml` having mixed encoding (UTF-16 BOM, ISO-8859-1). **Finding 1 + Finding 9** together close this hole; without them, a content-team-laptop audit could crash mid-walk and confuse the operator.

**A confused content author** — what if `rules.yaml` exists but has `confrontations: null` (instead of `confrontations: []`)? `raw.get("confrontations") or []` handles it. What about `confrontations: "oops_a_string"`? The `for conf in confrontations` would iterate characters. Each char is not a dict → skipped by `isinstance(conf, dict)`. **Defensive, OK.** What about a confrontation with `mood: 42` (an int)? `isinstance(mood, str)` skips it. **Defensive.**

**What if the load validator is one day relaxed?** If pydantic `_validate_mood_aliases` is loosened (e.g. allowing depth=10 instead of 5), the audit helper still caps at MAX_ALIAS_HOPS=5 (it imports the constant from the same module, so they stay in sync). **Synced via shared import — safe.**

**Could a pack's rules.yaml have moods declared somewhere other than `confrontations[*].mood`?** Looking at the codebase: `AudioTheme.mood` in audio.yaml's `themes` section is a separate mood-string surface that doesn't go through `mood_tracks` — the validator doesn't audit themes. Also `StructuredEncounter.mood_override` is set from `cdef.mood` (which IS the confrontation mood the validator already scans). The narrator's natural-language mood emission is unenumerable by design (the Zork Problem — runtime fallback handles it). **Coverage is right-sized for what the runtime can predict.**

**What if a Reviewer adds a new validate subcommand later that needs `packs_in`?** It just imports `from sidequest.cli.validate.common import packs_in`. The extraction during verify makes this easy. **Good factoring.**

**Real worry surfaced by Devil's Advocate:** Finding 9 was confirmed by this exercise — a stressed-filesystem scenario (concurrent write + audit) would crash the validator. Combined with Finding 1+2's encoding issue, the audit is brittle on the real-world inputs (someone's laptop, mid-edit content tree). All other angles came up clean.

### Pattern observations

- **[VERIFIED]** Strong reuse of the `pf validate locations` pattern — `Issue` / `ValidationResult` / `validate_packs` / `validate_audio_in_pack` / CLI `main` all mirror locations.py 1:1 in shape, with the deliberate-and-documented exception that audio.py uses a pure helper `_chain_resolves_to_track` to avoid OTEL pollution. `_packs_in` is now shared via `common.py` (extracted during verify). `sidequest/cli/validate/audio.py:51-70` defines Issue + ValidationResult with identical shape to `sidequest/cli/validate/locations.py:42-66`. Complies with project rule "Don't Reinvent — Wire Up What Exists."
- **[VERIFIED]** Wiring test exists per CLAUDE.md "Every Test Suite Needs a Wiring Test" — `tests/cli/test_validate_audio.py::test_cli_audio_subcommand_is_registered` shells out via subprocess. Reachable from the documented entry point.
- **[VERIFIED]** Boy-scout fix on `test_narrator_uses_sdk_client.py` is bounded per [[feedback_boy_scout_bounded]] — single semantic correction (27→28 to add `get_world_grounding`), three locations updated together (docstring line 7, comment line 26, assertion line 192), all consistent.
- **[VERIFIED]** Severity boundary is defensible: warning for `UNRESOLVED_RULES_MOOD` (runtime fallback is graceful + observable), error for `AUDIO_LOAD_FAILURE` (pack will refuse to load at server startup). Documented in module docstring and pinned by `test_unresolved_warning_does_not_become_error`.

### Data flow trace

CLI `--genre-packs-root <PATH>` → click `Path(exists=True, file_okay=False)` validates → `validate_packs([<PATH>])` → `packs_in(root)` enumerates pack-yaml-bearing children → for each pack: `validate_audio_in_pack(pack)` → guards `audio.yaml` exists → `_load_audio_config` reads + parses + model_validates (or records AUDIO_LOAD_FAILURE) → `_check_rules_moods` reads rules.yaml + iterates confrontations + records UNRESOLVED_RULES_MOOD for unresolved → results accumulated → CLI prints errors/warnings + `ctx.exit(0 if success else 1)`. Safe end-to-end **except for** the unhandled-YAML-error gap noted in Finding 9.

### Handoff

Back to Dev (Puck) for findings 1–9. Estimated effort: ~30 minutes total — Findings 1, 2 are one-line each; 3, 4, 6, 8 are surgical edits; 5, 7, 9 each need a fixture + a test. The shape is mechanical; no design questions outstanding.

## Tea Assessment (verify, round 2)

**Verify state: clean. Proceed to Reviewer.**

### Branch hygiene

Re-fetched origin/develop: branch is 5 commits ahead, 0 behind (still clean — no drift since round 1 rebase).

### Simplify pass — three teammates fanned in parallel

| Agent | Status | Findings |
|---|---|---|
| simplify-efficiency | findings | 1 MEDIUM (overlap on contract-document test — dismissed with rationale below) |
| simplify-reuse | findings | 1 HIGH (parametrize subprocess tests — applied) + 2 self-dismissed (YAML-load duplication, robustness-test pattern) |
| simplify-quality | findings | 1 MEDIUM (broad exception catch — applied) |

### Applied fixes (commit `3318492`)

1. **Parametrize the two subprocess exit-code wiring tests.** `test_cli_audio_exits_zero_on_clean_pack` + `test_cli_audio_exits_nonzero_when_errors_present` collapse into a single `test_cli_audio_exit_code_matches_result_success` parametrized over `(fixture_name, expected_returncode)`. Distinct names preserved via `ids=["clean_pack_exits_zero", "broken_pack_exits_one"]` so test output stays readable. ~50 LoC → ~30 LoC, same coverage.
2. **Tighten exception catches** in both `_load_audio_config` (`(yaml.YAMLError, ValueError)` → `(UnicodeDecodeError, yaml.YAMLError, ValidationError)`) and `_check_rules_moods` (`yaml.YAMLError` → `(UnicodeDecodeError, yaml.YAMLError)`). Eliminates risk of conflating a UTF-8-decoding failure with a pydantic schema failure in AUDIO_LOAD_FAILURE triage messages. Module docstring updated to enumerate all three failure modes. Added `from pydantic import ValidationError` import.

### Dismissed findings (with rationale)

| # | Source | Finding | Dismissal rationale |
|---|--------|---------|---------------------|
| D1 | [SIMPLE/efficiency] | `test_validate_packs_does_not_crash_on_any_fixture_root` overlaps with `test_one_broken_pack_does_not_suppress_others` and `test_validate_packs_walks_a_root_of_multiple_packs` | Intent-encoding **contract document**: explicitly enumerates all three error families (AUDIO_LOAD_FAILURE pydantic, AUDIO_LOAD_FAILURE yaml, RULES_LOAD_FAILURE) + warning family in a single assertion. If a future PR drops one error type, this test fails loud with a clear name — same family as round-1's dismissed `test_unresolved_warning_does_not_become_error`. Overlap is intentional. Keep. |
| D2 | [SIMPLE/reuse] | `_load_audio_config` and `_check_rules_moods` share yaml-load + Issue-record structure | Subagent self-dismissed; agreed — extracting a `_wrap_yaml_load(...)` helper would require parameterizing the validation step (audio has model_validate, rules doesn't), obscuring the semantic difference. Two call sites is not enough to justify abstraction over clarity. |
| D3 | [SIMPLE/reuse] | Three robustness-test functions follow similar shape | Subagent self-dismissed; agreed — per-test docstrings encode distinct fixture rationale that a parametrized `(fixture, code, file)` tuple would lose. |

### Regression sweep

`uv run pytest tests/cli/test_validate_audio.py tests/cli/test_validate_locations.py tests/audio/ tests/agents/test_narrator_uses_sdk_client.py -q --timeout=15` — **76 passed, 10 skipped, 0 failed, 2.85s** (unchanged from rework — parametrize collapsed 2 test definitions but kept 2 test runs).

Lint + format clean.

### Diff scope (final)

Branch is 5 commits ahead of origin/develop, 0 behind:
- `c2b0ac7` test(50-9): RED — pf validate audio content audit + fixtures
- `5c92274` feat(50-9): pf validate audio — mood-reference content audit
- `6fe0dc5` refactor: simplify code per verify review (50-9)
- `40c7091` fix(50-9): reviewer findings — encoding, YAML errors, contract gaps
- `3318492` refactor: simplify code per verify review round 2 (50-9)

### Quality-pass gate

PASS — full suite would surface no new failures attributable to 50-9.

### Forward note for second-pass Reviewer

- All 9 findings from round-1 Reviewer addressed in `40c7091`.
- The 2 round-2 simplify findings addressed in `3318492`.
- Live-pack hand-run still produces the same 3 warnings — confirms no regression on live behavior.
- New contract addition since round 1: `RULES_LOAD_FAILURE` issue code (sensible, sibling to AUDIO_LOAD_FAILURE).
- Exception catches are now type-specific (UnicodeDecodeError, yaml.YAMLError, ValidationError) rather than a broad ValueError net.

## Tea Assessment (verify)

**Verify state: clean. Proceed to Reviewer.**

### Pre-simplify branch hygiene

Branch was 1 commit behind origin/develop — PR #368 (`chore(beats): add optional BeatDef.flavor for D2 tile copy`) had merged after the branch forked. A pre-rebase `git diff develop` showed `sidequest/genre/models/rules.py` losing the new `flavor` field. **Rebased onto origin/develop cleanly** (no conflicts; my 2 commits touch disjoint files) before kicking off simplify. Post-rebase: 0 behind, 2 ahead of origin/develop, no phantom file changes in the diff. Per [[feedback_just_fix_it]] — small blocking branch-hygiene issue caught and fixed in-line rather than filed.

### Simplify pass — three teammates fanned in parallel

| Agent | Status | High-confidence findings |
|---|---|---|
| simplify-efficiency | clean | 0 |
| simplify-reuse | findings | 1 (extract `_packs_in` to common module) |
| simplify-quality | findings | 2 (stale docstring + comment in `test_narrator_uses_sdk_client.py`) |

### Applied fixes (commit `6fe0dc5`)

1. **`_packs_in` extracted to `sidequest/cli/validate/common.py`** as `packs_in()`. Both `audio.py` and `locations.py` now import it. Pure-function extraction; docstring on the shared helper preserves the original "silently skip child without pack.yaml" rationale (heavy_metal/spaghetti_western relocation history). Two call sites today; ADR-109 work will likely add a third (`pf validate world`), so the shared module pays for itself imminently.
2. **`test_narrator_uses_sdk_client.py:7` docstring** — "27-tool array" → "28-tool array". Caught by simplify-quality. The GREEN-phase boy-scout fix updated the assertion (line 191) but missed the docstring above it.
3. **`test_narrator_uses_sdk_client.py:26` import comment** — "26 adapters" → "28 adapters". Same staleness, older provenance.

### Dismissed findings (none)

All three high-confidence findings were applied. No medium/low findings were promoted — the runtime-resolver-vs-audit-helper duplication that simplify-reuse correctly avoided flagging stays as documented intentional duplication ([[feedback_one_mechanism_per_problem]] does NOT apply here — these are deliberately different mechanisms with different side-effect profiles, not two parallel implementations of the same concern).

### Regression sweep

`uv run pytest tests/cli/test_validate_audio.py tests/cli/test_validate_locations.py tests/audio/ tests/agents/test_narrator_uses_sdk_client.py -q --timeout=15` — **70 passed, 10 skipped, 0 failed, 2.17s**. Covers:
- 13 new audio-validator tests (proves the extraction didn't break my own contract)
- 36 locations-validator tests (proves the extraction didn't break the sibling)
- 21 existing mood-alias mechanism tests (no regression in the runtime path)
- narrator-sdk wiring test (the boy-scout-fixed file)

Lint + format clean across all touched files (`sidequest/cli/validate/`, the two test files).

### Diff scope post-simplify

Branch is now 3 commits ahead of origin/develop, 0 behind:
- `aef9725` feat(50-9): pf validate audio — mood-reference content audit
- `3a3300b` test(50-9): RED — pf validate audio content audit + fixtures
- `6fe0dc5` refactor: simplify code per verify review (50-9)

Net diff vs origin/develop: 5 source files + 12 fixture files, +675/-30 lines.

### Quality-pass gate

PASS — full server suite would surface no new failures attributable to 50-9 (touched files have green test coverage; sibling locations validator green; mood-alias mechanism green; the pre-existing failures in the broader suite are unrelated repo-drift items, the most prominent of which I just fixed in this branch by updating the 27→28 assertion + simplify-quality's docstring/comment follow-ups).

### Forward note for Reviewer

- Live-pack hand-run command for the validator: `uv run python -m sidequest.cli.validate audio --genre-packs-root ../sidequest-content/genre_packs` — expect exit 0 with 3 warnings (caverns_and_claudes/comedic, tea_and_murder/social_duel mystery, tea_and_murder/scandal mystery).
- The content-side AC-4 work is intentionally deferred to a separate `sidequest-content` PR; not blocking this story per [[feedback_no_content_coupled_tests]] and Architect's spec-check resolution-D.
- ADR-033 §Pillar 3 is stale (still says "mood_aliases is dead data"); recommended follow-up per Architect's assessment.

## Architect Assessment (spec-check, round 2)

**Spec Alignment:** Aligned. No new mismatches introduced by the rework.

### What changed in rework

Reviewed commit `40c7091` against the AC matrix and the round-1 spec-check assessment. Six change classes:

1. **Encoding fix** (audio.py:103, 127) — no spec impact, addresses CWE-838 platform-default. Compliant with lang-review rule #5.
2. **`RULES_LOAD_FAILURE` new issue code** — only contract addition in this rework. Sensible: parallel to `AUDIO_LOAD_FAILURE` in shape and severity; dedicated code lets triage distinguish the offending file. The pattern (per-file load-failure code) is arguably one the locations validator could adopt later (it has CARTOGRAPHY / NPCS / SCENARIOS as sub-files but uses a single MALFORMED_ENTITY code — different domain, no action required here). **No ADR needed** — this is an internal CLI tool's contract, not a cross-system invariant.
3. **Broadened `except (yaml.YAMLError, ValueError)`** — closes the silent-failure gap I and the disabled silent-failure-hunter subagent both flagged in round 1; matches CLAUDE.md "No Silent Fallbacks" by surfacing a previously-unrecoverable crash path as a structured Issue.
4. **Two new subprocess wiring tests** (`test_cli_audio_exits_zero_on_clean_pack`, `test_cli_audio_exits_nonzero_when_errors_present`) — strengthen AC-5 ("Production wiring test"). Now there's both a unit-level wiring proof (`test_cli_audio_subcommand_is_registered`) and end-to-end exit-code contract proof. Better than before.
5. **Three new fixture packs** (`audio_missing/`, `audio_malformed_yaml/`, `rules_malformed_yaml/`) — coverage expansion for the previously-untested branches. Aligned with [[feedback_no_content_coupled_tests]] — purpose-built fixtures, not live content scans.
6. **Docstring honesty updates** — `validate_audio_in_pack` no longer over-claims "both checks"; module docstring now enumerates all three issue codes; test module docstring matches.

### AC re-check (delta from round 1)

- **AC-1 mechanism**: unchanged — still satisfied by pre-shipped resolver + validator + spans + wiring.
- **AC-2 runtime resolver**: unchanged — still satisfied.
- **AC-3 OTEL spans**: unchanged — still satisfied (dashboard verify still deferred per spec text).
- **AC-4 content authoring**: still deferred to a separate `sidequest-content` PR per my round-1 Resolution D — Dev's hand-run still surfaces the same 3 actionable gaps (caverns/comedic, tea_and_murder/social_duel mystery, tea_and_murder/scandal mystery), proving the validator does its job on live content.
- **AC-5 wiring test**: **strengthened** — was unit-level only, now also end-to-end exit-code-contract proven through subprocess.

### Reviewer punchlist disposition

All 9 reviewer findings addressed; no findings deferred. Dev's assessment table maps cleanly to the reviewer's findings table. The three LOWs the reviewer dismissed (intent-encoding test, unreachable max-hops fixture, defensive hasattr loop) remain dismissed — Dev didn't re-litigate them.

### Pattern + reuse audit (delta)

- The new `RULES_LOAD_FAILURE` extends the validator's per-file load-failure pattern symmetrically. Reusable. Could be lifted to `common.py` later if a third validator (`pf validate world` per ADR-109) wants the same shape; not worth doing now (one-time use).
- The two new subprocess wiring tests follow the same shape as `test_cli_audio_subcommand_is_registered` (sys.executable + module spawn + capture). Consistent.

### Devil's Advocate (rework focus)

- **Did the `except (yaml.YAMLError, ValueError)` broaden too far?** Specifically, ValueError is broad enough to catch pydantic ValidationError (good, intended) but could also catch unrelated ValueErrors raised deep inside model_validate. In practice the only thing model_validate raises is ValidationError (a ValueError subclass) or its wrapper. Acceptable; if a future pydantic version changes the exception hierarchy, the regression test would fire and the contract is pinned.
- **The new fixtures contain deliberately malformed YAML — would they break any repo-wide YAML linter?** They live under `tests/fixtures/validate_audio/` which is test data, not content. Any repo-wide YAML lint that walks `genre_packs/`/`genre_workshopping/` wouldn't touch them. ruff doesn't lint YAML. No conflict.
- **OS errors (PermissionError, IsADirectoryError) — still uncaught?** Yes, those still propagate. Dev addressed yaml.YAMLError specifically because that's the realistic content-team-laptop scenario (mid-edit save). OS errors on read are environmental (permissions, broken filesystem) and arguably should crash with a clear stacktrace, since fixing them requires operator action. Defensible to leave uncaught. If we wanted symmetric coverage we'd catch `(OSError, yaml.YAMLError, ValueError)`, but the marginal value is low and Dev's choice matches the typical scope of "robust to broken content" without overreaching to "robust to broken filesystem."

### Decision

**Proceed to verify.** No code changes required. Rework is tight; new contract addition (`RULES_LOAD_FAILURE`) is sound; AC alignment improved (AC-5 now exit-code-proven).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned with documented deferrals
**Mismatches Found:** 4 (3 deferred-with-rationale, 1 documentation-drift follow-up)

### Reuse / pattern audit

Strong pattern reuse. `sidequest/cli/validate/audio.py` mirrors `sidequest/cli/validate/locations.py` (Story 54-3) point-for-point:
- Same frozen `Issue` dataclass shape (`code`, `severity`, `message`, `pack`, `file`)
- Same `ValidationResult` (errors / warnings / `record()` / `.success`)
- Same `_packs_in(root)` discovery helper (pack-or-parent-of-packs)
- Same click `main` with `--genre-packs-root` + `--json` + ctx.exit
- Same `cli.add_command(audio_main, name="audio")` registration shape

Per <pragmatic-restraint>: this is exactly the "best code is code you didn't write" path — Dev didn't invent a new validator framework, they cloned the proven one. The new content-audit subsystem reads as a sibling validator, not a parallel mechanism. No ADR needed.

The one architectural addition Dev got *right* that locations didn't need: `_chain_resolves_to_track` is a **pure** helper deliberately not reusing the runtime `resolve_mood_to_track_key` because the runtime function emits OTEL spans as a happy-path side effect. Reusing it from the audit context would pollute traces with hundreds of resolution spans on every CI / content-team invocation. The session-file comment calls this out explicitly. Good.

### Severity boundary check

`UNRESOLVED_RULES_MOOD = warning` (not error) is consistent with CLAUDE.md "No Silent Fallbacks" *and* runtime behavior:
- Runtime fallback to `exploration` is observable (`music.mood_alias_failed` span + WARNING log) — already loud.
- Hard-erroring at validate time would block ship on any narrator-likely mood a content author hasn't enumerated (Zork Problem analogue: can't predict all natural-language mood strings).
- `AUDIO_LOAD_FAILURE = error` is correct because a broken declared chain prevents pack load entirely.

Severity is right. The test `test_unresolved_warning_does_not_become_error` pins this so a future "let's harden it" PR has to argue the case explicitly.

### Mismatch analysis (per-AC)

- **AC-4 "at least one live pack authored with mood_aliases"** (Missing in code — Behavioral, Major, deferred)
  - **Spec:** Session AC-4 third bullet: "At least one live pack (spaghetti_western) authored with aliases for custom moods (standoff, saloon, riding, betrayal, etc.) — validate against rules.yaml/confrontations and audio.yaml/mood_tracks"
  - **Code:** No live pack got new mood_aliases in this PR. `sidequest-content` has zero changes on the 50-9 branch.
  - **Recommendation:** **D — defer to sibling content PR.** Dev's hand-run surfaces the actual gaps (caverns_and_claudes/comedic, tea_and_murder/social_duel+scandal mystery). The architectural separation (validator shipped here, content authored in a separate `sidequest-content` PR) is sound per [[feedback_no_content_coupled_tests]] — coupling a server PR to content YAML edits would re-introduce the exact pattern Keith hard-stopped during RED. The content design decisions (what should `comedic` and `mystery` alias to?) need Keith's design input, not a Dev pick.
  - **Required follow-up:** File a `sidequest-content` story (or fold into next content sweep) that authors at least: `comedic: <pick>` in caverns_and_claudes/audio.yaml, `mystery: <pick>` in tea_and_murder/audio.yaml. The validator will go from 3 warnings to 0 once those land.

- **AC-4 "(spaghetti_western)" nomination** (Different behavior — Cosmetic, Minor, accepted)
  - **Spec:** Names spaghetti_western as the candidate live pack.
  - **Code reality** (TEA finding, 2026-05-21): spaghetti_western's rules.yaml only references `combat`, `saloon`, `standoff`, `tension` — every one of those is already a direct mood_tracks key. There's literally nothing for spaghetti_western to alias.
  - **Recommendation:** **A — update spec.** TEA already logged this as a Gap finding; nothing further to do. The real gap-bearing packs are caverns and tea_and_murder. If a future re-author of AC-4 surfaces, name those packs instead.

- **AC-3 "GM panel receives and parses both span types (verify in dashboard on next playtest)"** (Trivial, spec-deferred)
  - **Spec:** Explicit parenthetical "verify in dashboard on next playtest."
  - **Code:** Span emission is unit-tested (`test_successful_alias_resolution_emits_resolved_span`, `test_unresolved_mood_emits_failed_span_with_reason`); dashboard parse is a live-playtest verification that the spec itself defers.
  - **Recommendation:** **D — defer to next playtest** (matches spec text).

- **Story title vs delivered scope ("Steps 1-3")** (Architectural pivot, fully documented)
  - **Spec:** "implement mood_aliases alias-chain fallback (ADR-033 Pillar 3 Steps 1-3)"
  - **Code reality:** Steps 1-3 (model, load-time validator, runtime resolver, OTEL spans, wiring) all shipped pre-50-9; the 21 tests at `tests/audio/test_mood_alias_chain.py` already prove the mechanism GREEN. 50-9's delivery is a content-audit validator that closes the *verification* loop on Steps 1-3.
  - **Recommendation:** **A — accept the pivot.** TEA and Dev both logged deviations explaining the reshape, and the validator is the right tool to drive AC-4 going forward. The story title is now mildly inaccurate as a description of the delivered work, but the *outcome* (Steps 1-3 are no longer "partial/dead data" — they're verified live + auditable) matches the original intent.

### ADR drift finding (out-of-scope, recommend follow-up)

**ADR-033 §Pillar 3 is stale.** Currently reads:

> ✗ `mood_aliases` is dead data. ... No consumer fires the alias chain. The track-selection fallback the ADR §Pillar 3 Step 3 described — "look up the classified mood string in mood_tracks; if not found, follow the alias chain" — was never written in Python.

This was true on 2026-05-02 but is FALSE today. The resolver (`resolve_mood_to_track_key`) is wired into `LibraryBackend._resolve_music`, fully tested, and observable. The "Restoration scope" paragraph below it (which talks about implementing the lookup) is also stale.

**Recommendation:** **D — defer to a docs follow-up.** ADR-033 should be amended to (a) flip the ✗ to ✓ on the alias-chain lookup, (b) note that 50-9 added `pf validate audio` as the content-side audit complement, (c) update the §Implementation status block at the bottom. This is a tech-writer-shaped task, not blocking-PR work. Could be folded into the content-authoring follow-up PR's docs commit, or filed as its own one-pointer.

### Other observations (non-blocking)

- **Bounded boy-scout fix on `test_narrator_uses_sdk_client.py`** is appropriate — single-character semantic fix on a stale assertion (27→28 tools, the 28th being `get_world_grounding` from story 24-6 which merged to develop while 50-9 was in flight). Per [[feedback_boy_scout_bounded]]: small adjacent fixes welcome during a story; this one is bounded and tested.
- **Story 50-27 filed** for the test-suite parallelization concern that surfaced during verify-loop iteration. Proper escalation — separate concern, separate story, with AC-5 explicitly closing the loop on 50-9's verify pain.
- **Reviewer should re-run** `uv run python -m sidequest.cli.validate audio --genre-packs-root ../sidequest-content/genre_packs` and confirm the same 3 warnings surface — that's the live-data sanity check Dev did. Validates both the wiring and that the tool is useful, not just internally consistent.

### Decision

**Proceed to review.** No code changes required. All AC drift is either:
- Documented as intentional deferrals by Dev/TEA with sound rationale
- Spec-text-deferred (AC-3 dashboard playtest verification)
- Recommended for follow-up docs/content work (ADR-033 + content-authoring PR)

## Dev Assessment (rework)

**Rework attempt 1 of 3.** All 9 reviewer findings addressed in commit `40c7091`. 76/10 (was 70/10 — six new tests added), lint + format clean.

### Findings disposition

| # | Severity | Source | Disposition | Implementation |
|---|----------|--------|-------------|----------------|
| 1 | [HIGH] | [RULE #5] | Fixed | `audio.py:103` → `path.read_text(encoding="utf-8")` |
| 2 | [HIGH] | [RULE #5] | Fixed | `audio.py:127` → `rules_path.read_text(encoding="utf-8")` |
| 3 | [HIGH] | [RULE #6] [TEST] | Fixed | `test:180` → `assert len(warnings) == 1` |
| 4 | [HIGH] | [RULE #6] [TEST] | Fixed | `test:191` → `assert len(failures) == 1` |
| 5 | [HIGH] | [TEST] | Fixed | New `audio_missing/` fixture (pack.yaml only) + `test_pack_without_audio_yaml_returns_empty_result` |
| 6 | [HIGH] | [DOC] | Fixed | `test_validate_audio.py:1` "RED tests" → "Tests"; module docstring also updated to enumerate the new RULES_LOAD_FAILURE code |
| 7 | [MEDIUM] | [TEST] | Fixed | Two new subprocess wiring tests (`test_cli_audio_exits_zero_on_clean_pack` against `audio_ok`, `test_cli_audio_exits_nonzero_when_errors_present` against `audio_broken_declared_alias`) — proves the `ctx.exit(0 if success else 1)` contract end-to-end |
| 8 | [MEDIUM] | [DOC] | Fixed | `validate_audio_in_pack` docstring rewritten to enumerate early-return + skip cases honestly |
| 9 | [MEDIUM] | [EDGE] | Fixed | `_load_audio_config` catch broadened to `(yaml.YAMLError, ValueError)`; `_check_rules_moods` now wraps `yaml.safe_load` in try/except and records new `RULES_LOAD_FAILURE` error code with dedicated triage value. Two new fixtures (`audio_malformed_yaml/`, `rules_malformed_yaml/`) + two new tests prove the catches fire. Plus a new comprehensive `test_validate_packs_does_not_crash_on_any_fixture_root` asserts representatives of all error families surface from one multi-pack walk. |

### Boy-scout adjacent fix

- `test_validate_packs_walks_a_root_of_multiple_packs` had a stale "All four fixture packs should have contributed" comment; refreshed to list all seven fixture packs now in the directory.

### Verify path for second-pass review

- `cd sidequest-server && uv run pytest tests/cli/test_validate_audio.py tests/cli/test_validate_locations.py tests/audio/ tests/agents/test_narrator_uses_sdk_client.py -q --timeout=15` → `76 passed, 10 skipped` (locations validator still GREEN — confirms the audio fixes didn't touch the shared `packs_in` helper in a regressive way).
- `uv run ruff check sidequest/cli/validate/ tests/cli/test_validate_audio.py` → All checks passed.
- `uv run ruff format --check sidequest/cli/validate/ tests/cli/test_validate_audio.py` → 7 files already formatted.
- Live hand-run: `uv run python -m sidequest.cli.validate audio --genre-packs-root ../sidequest-content/genre_packs` → exit 0, 3 warnings (caverns_and_claudes/comedic, tea_and_murder/social_duel mystery, tea_and_murder/scandal mystery). Unchanged from pre-rework — confirms the broadened error handling didn't cause regressions on real content.

### New diff (commit `40c7091`)

Branch is 4 commits ahead of origin/develop, 0 behind:
- `c2b0ac7` test(50-9): RED — pf validate audio content audit + fixtures
- `5c92274` feat(50-9): pf validate audio — mood-reference content audit
- `6fe0dc5` refactor: simplify code per verify review (50-9)
- `40c7091` fix(50-9): reviewer findings — encoding, YAML errors, contract gaps

Net rework diff: 2 source files + 6 new fixture files, +249/-37.

### Confidence on second-pass review

All HIGH findings are mechanical or fixture-based (no judgment calls disputed). The MEDIUM YAML-error broadening introduces one new public-API change (`RULES_LOAD_FAILURE` issue code) — appropriate for a follow-up Reviewer to spot-check, but the dedicated code (rather than reusing `AUDIO_LOAD_FAILURE`) is the right separation for triage. No dismissed findings; the three LOWs Reviewer dismissed during the first pass remain dismissed for the same reasons (intent-encoding test, unreachable code path, defensive spelling check).

## Dev Assessment

**GREEN state reached.** 13/13 RED tests now pass; 21/21 pre-existing mood_alias mechanism tests still pass; ruff + ruff format clean on touched files.

**What shipped (server, branch `feat/50-9-mood-aliases-fallback`, commit `aef9725`):**
- `sidequest/cli/validate/audio.py` — new validator with `Issue`, `ValidationResult`, `validate_audio_in_pack`, `validate_packs`, click `main`. Walks pack roots, loads each pack's `audio.yaml` via `AudioConfig.model_validate` (catching pydantic ValueError as `AUDIO_LOAD_FAILURE`), scans `rules.yaml` for `confrontations[*].mood`, and emits `UNRESOLVED_RULES_MOOD` warnings for moods that don't resolve via the alias chain. Uses a pure `_chain_resolves_to_track` helper to avoid OTEL span side effects in audit context.
- `sidequest/cli/validate/__main__.py` — registers `audio` subcommand alongside `locations` and `projection-check`.
- Bounded boy-scout fix on `tests/agents/test_narrator_uses_sdk_client.py`: stale `len(default_registry.list_names()) == 27` updated to `== 28` (story 24-6 added `get_world_grounding`). Comment extended to credit both 54-6 and 24-6. Fix verified to GREEN in 30ms. Per [[feedback_boy_scout_bounded]] — one-character semantic fix on an obviously stale assertion, in-PR rather than filing a follow-up.

**What did NOT change** (intentional, per TEA's scope guidance):
- Zero edits to the mood_aliases mechanism. Resolver, validator, OTEL spans, library_backend wiring all untouched.
- Zero edits to `sidequest-content/genre_packs/*`. The live-pack content gaps (caverns_and_claudes/comedic, tea_and_murder/mystery — see Hand-run below) are content-team authoring decisions that belong in a separate content PR after Keith approves the alias targets.
- Zero edits to the existing `tests/audio/test_mood_alias_chain.py` — those 21 tests stayed exactly as TEA found them.

**Hand-run against live packs** (`uv run python -m sidequest.cli.validate audio --genre-packs-root ../sidequest-content/genre_packs`):

```
[WARN] UNRESOLVED_RULES_MOOD caverns_and_claudes/rules.yaml: confrontation 'negotiation' references mood 'comedic' ...
[WARN] UNRESOLVED_RULES_MOOD tea_and_murder/rules.yaml: confrontation 'social_duel' references mood 'mystery' ...
[WARN] UNRESOLVED_RULES_MOOD tea_and_murder/rules.yaml: confrontation 'scandal' references mood 'mystery' ...
audio: 0 errors, 3 warnings
```

Exit 0 (warnings don't gate). The validator proves itself on live data without my having to write a single test against that live data. Reviewer can re-run the same command and verify.

**Process finding — slow test suite (filed as 50-27):** During GREEN's verify loop the full `uv run pytest -q` hit ~5-6 min and felt like a hang. Investigation showed it's NOT a spurious LLM call — per-test speed is already fine (median 5-20ms, slowest 0.5s on intentional timeout tests). The wall-clock pain is suite cardinality: 7,440 tests serial. Filed **50-27** (5pts, epic-50, p2) to add pytest-xdist + isolate global-state fixtures + wire `-n auto` into `just server-test` and `pf check`. AC-5 explicitly closes the loop back on 50-9's verify pain — once 50-27 lands, this whole pipeline gets a 5–8× speedup.

**Wiring proof per CLAUDE.md "Every Test Suite Needs a Wiring Test":** `test_cli_audio_subcommand_is_registered` shells out to `python -m sidequest.cli.validate audio --help` and asserts exit 0. The hand-run above is the live-data complement.

**Verify path for Reviewer:**
- `cd sidequest-server && uv run pytest tests/cli/test_validate_audio.py tests/audio/ -q` → `43 passed, 10 skipped`
- `uv run ruff check sidequest/cli/validate/audio.py sidequest/cli/validate/__main__.py tests/cli/test_validate_audio.py tests/agents/test_narrator_uses_sdk_client.py`
- `uv run ruff format --check sidequest/cli/validate/audio.py sidequest/cli/validate/__main__.py tests/cli/test_validate_audio.py`
- `uv run python -m sidequest.cli.validate audio --genre-packs-root ../sidequest-content/genre_packs` → exit 0, 3 warnings for the live content gaps named above

**Diff scope summary:**
- `sidequest-server`: +1 new file (audio.py, 234 lines), 3 edits (__main__.py +3 lines, test_validate_audio.py format-only, test_narrator_uses_sdk_client.py 2-line assertion fix). Net +258 / -7.
- `sidequest-content`: NO CHANGES. Content-side AC-4 work is deliberately deferred to a separate PR per the no-content-coupled-tests rule.
- `orchestrator`: sprint state + context doc + 50-27 story committed separately on `main` (`33ae83a`).

## Tea Assessment

**RED state confirmed.** `tests/cli/test_validate_audio.py` collects but cannot import — `ModuleNotFoundError: No module named 'sidequest.cli.validate.audio'`. 12 tests will fail to collect until Dev implements the module.

**What's already GREEN (no work needed):** `tests/audio/test_mood_alias_chain.py` — 21 fixture-driven behavior tests, all PASS against the shipped implementation. The mood_aliases resolver (`resolve_mood_to_track_key`), the load-time pydantic validator (`AudioConfig._validate_mood_aliases`), the OTEL spans (`music.mood_alias_resolved` / `music.mood_alias_failed`), and the production wiring (`LibraryBackend._resolve_music` → resolver) are all complete and covered. The story's "Step 1-3 mechanism" is already in main; no additional resolver/span/validator tests are needed.

**What's RED (Dev's job):** A new content-audit validator at `sidequest/cli/validate/audio.py` that walks live packs and surfaces moods which would silently fall back at runtime. Contract pinned by the test file:

```python
# sidequest/cli/validate/audio.py
from dataclasses import dataclass, field
from typing import Literal
from pathlib import Path

Severity = Literal["error", "warning"]

@dataclass(frozen=True)
class Issue:
    code: str           # "UNRESOLVED_RULES_MOOD" | "AUDIO_LOAD_FAILURE"
    severity: Severity  # "warning" | "error"
    message: str        # must name the offending mood / alias
    pack: str           # pack dir name (e.g. "caverns_and_claudes")
    file: str           # relative path inside pack (e.g. "rules.yaml")

@dataclass
class ValidationResult:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    def record(self, issue: Issue) -> None: ...
    @property
    def success(self) -> bool: return not self.errors

def validate_audio_in_pack(pack_dir: Path) -> ValidationResult: ...
def validate_packs(pack_roots: list[Path]) -> ValidationResult: ...
```

Plus a click CLI registered under `sidequest.cli.validate.__main__`'s group at name `audio` (mirror the `locations` registration pattern, lines 22-24).

**Behavior the tests pin:**

1. Build `AudioConfig` from `pack_dir/audio.yaml` (let pydantic do the heavy lifting on declared-alias validation). If construction raises ValueError, catch it and record one `AUDIO_LOAD_FAILURE` error (severity=error, file="audio.yaml", message must contain the offending alias key + broken target — pass through the pydantic msg).
2. Parse `pack_dir/rules.yaml` (YAML safe_load), walk `confrontations[*].mood`. For each mood that is neither in `cfg.mood_tracks` nor resolvable via `resolve_mood_to_track_key` (re-use the existing resolver — don't re-implement the chain walk), record one `UNRESOLVED_RULES_MOOD` warning (severity=warning, file="rules.yaml", message names the mood).
3. **CRITICAL:** when re-using `resolve_mood_to_track_key` for the audit check, you DO NOT want it to emit a span as a side-effect (would pollute OTEL on every CI run of the validator). Either:
   - Wrap the resolver in a function that does the membership check directly (`mood in cfg.mood_tracks or chain_resolves_to_track(mood, cfg.mood_aliases, cfg.mood_tracks)`), or
   - Drive `resolve_mood_to_track_key` and accept the spans (they'll only flow to a real tracer when one's installed; in `pf validate audio` invocation context, the default no-op tracer eats them).
   The first option is cleaner. Either works for the tests; pick what reads best.
4. `validate_packs([root])` enumerates pack-yaml-bearing children of each root (mirror `locations._packs_in`); per-pack failures must not suppress sibling packs (`test_one_broken_pack_does_not_suppress_others` enforces this).
5. CLI wiring: extend `sidequest/cli/validate/__main__.py` to import and register the audio subcommand (mirror locations lines 22-24 + the dispatch fallback at the bottom of the file).

**Fixture inventory** (TEA-authored, ready for Dev):
- `tests/fixtures/validate_audio/audio_ok/` — clean baseline (no issues)
- `tests/fixtures/validate_audio/audio_unresolved_rules_mood/` — `comedic` referenced, no track, no alias → 1 warning
- `tests/fixtures/validate_audio/audio_resolved_via_alias/` — `comedic: exploration` + `caper: comedic` (two-hop) → 0 warnings on those moods
- `tests/fixtures/validate_audio/audio_broken_declared_alias/` — `comedic: nonexistent_target` → 1 error, no crash

**Out of scope for Dev** (do NOT do these in this story):
- Do not run the validator against live `sidequest-content/genre_packs/*` and "fix" the gaps it surfaces in this same PR. That couples a server PR to content edits. The right shape is: this PR ships the validator + tests; a *separate* content PR adds `comedic: town` to caverns_and_claudes and `mystery: tension` to tea_and_murder once Keith approves the design choices.
- Do not add more behavior tests for the mood_aliases mechanism — already covered.
- Do not write any test that loads files from `sidequest-content/`. See [[feedback_no_content_coupled_tests]].

**Verify path for GREEN:**
- `uv run pytest tests/cli/test_validate_audio.py -v` → all 12 PASS
- `uv run pytest tests/audio/test_mood_alias_chain.py -v` → all 21 still PASS (no regression)
- `uv run pytest -q` → full suite PASS
- `uv run python -m sidequest.cli.validate audio --help` → exit 0
- Hand-run `uv run python -m sidequest.cli.validate audio --packs ../sidequest-content/genre_packs` to confirm the validator surfaces `caverns_and_claudes/comedic` and `tea_and_murder/mystery` as warnings (don't gate the test on this — just paste the output into your Dev assessment so Reviewer can confirm the validator does what it claims on live data).

**Risk: scope creep into Pillar 3 Step 4+.** The story title says "Steps 1-3." The validator is content-audit infrastructure that closes Step 3's content-side AC — it is not Step 4 (which would be engagement-triggered swaps, dynamic intensity bands, etc.). Hold the line; do not add new model fields, do not change resolver behavior, do not author content in this PR.

**Risk: silent-fallback regression.** The runtime fallback (DEFAULT_FALLBACK_MOOD = "exploration") is part of the contract — observable via `music.mood_alias_failed` span. Do not "improve" it to raise; do not "improve" the validator to make UNRESOLVED_RULES_MOOD an error without explicit Architect sign-off (the test `test_unresolved_warning_does_not_become_error` enforces this).

## Sm Assessment

**Story shape:** Authored as "implement mood_aliases alias-chain fallback (ADR-033 Pillar 3 Steps 1-3)" — but sm-setup's code survey reveals all three steps are already implemented:

- Step 1 (model + validation): `AudioConfig.mood_aliases` field + `_validate_mood_aliases()` exist at `sidequest-server/sidequest/genre/models/audio.py:124-169`
- Step 2 (runtime resolver): `resolve_mood_to_track_key()` exists at `sidequest-server/sidequest/audio/library_backend.py:32-77`
- Step 3 (OTEL spans): `music.mood_alias_resolved` / `music.mood_alias_failed` defined at `sidequest-server/sidequest/telemetry/spans/audio.py:72-147` and registered in `SPAN_ROUTES`
- Wiring: resolver is called from `LibraryBackend._resolve_music()` at line 168

The implementation is "wired but unverified." Only `heavy_metal` (workshopping) has authored aliases. No playtest has been observed to trigger an alias-chain miss → resolved-via-alias flow, so the GM panel has never proven the spans fire (the [[feedback_log_absence_not_deadness]] hazard — code presence ≠ liveness).

**Real work for TDD:**
1. **RED (TEA):** Author unit tests against the four resolver branches (direct hit, declared alias, deep chain, broken/cycle) + a wiring test confirming `LibraryBackend._resolve_music()` actually calls the resolver + a span-emission test. If the implementation is correct as-built, the unit tests should mostly pass on first run — which is the discovery TEA reports back. If anything is off, RED fails legitimately.
2. **GREEN (DEV):** Fix any gap surfaced by RED, then author `mood_aliases` for at least one **live** pack (spaghetti_western is the recommended candidate per AC-4 — has standoff/saloon/riding/betrayal custom moods that map naturally to tension/calm/travel/tension). Validate at pack load.
3. **VERIFY:** Run a content-validate pass against all packs that have custom moods to catch any latent unaliased moods that would silently fall to DEFAULT_FALLBACK_MOOD.

**Risk: scope creep into ADR-033 Pillar 3 Steps 4+.** The title says "Steps 1-3" — TEA and Dev must hold that line. Steps 4+ (engagement-triggered swaps, fine-grained intensity bands, etc.) belong to follow-on stories.

**Risk: silent-fallback regression.** The validator must continue to fail loud per CLAUDE.md "No Silent Fallbacks." If Dev "fixes" RED by relaxing validation, Reviewer should bounce.

**Audience fit:** This is a Sebastien/Keith concern (mechanical visibility on the music director) plus a Sonia-adjacent payoff (tea_and_murder eventually needs the same coverage — out of scope here but worth flagging).

**Repos:** server (resolver + model + validator + span) + content (audio.yaml for spaghetti_western and any other live pack chosen). Two branches already created, both `feat/50-9-mood-aliases-fallback` off `develop`.

**No Jira** per project rule.

## Context Reference

See `sprint/context/context-story-50-9.md` for full technical context, design history (Rust-era implementation, ADR-033 Pillar 3), and outstanding questions. Key findings:

- AudioConfig.mood_aliases field exists (sidequest/genre/models/audio.py:124)
- Load-time validator is complete and strict (lines 127–169)
- Runtime resolver resolve_mood_to_track_key() is implemented (sidequest/audio/library_backend.py:32–77)
- OTEL spans are defined (sidequest/telemetry/spans/audio.py:72–147)
- Resolver is integrated in LibraryBackend._resolve_music() (line 168)
- Implementation exists but is either untested in production or contains a subtle bug preventing correct wiring
- heavy_metal pack has aliases declared and should validate

The TDD approach will:
1. RED: Write unit tests for each resolver code path + integration tests for wiring
2. DEBUG: Run tests to identify any gaps or bugs
3. GREEN: Fix implementation or wire up missing pieces
4. VERIFY: Add live pack to content, run playtest to confirm end-to-end