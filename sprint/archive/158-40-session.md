---
story_id: "158-40"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 158-40: Dogfight full relative-position state graph — author beam/overhead/scissors/overshoot + extend-and-return (ADR-153 Plan 4)

## Story Details
- **ID:** 158-40
- **Jira Key:** None (Jira integration not configured)
- **Workflow:** tdd (phased)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-02T09:47:04Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-02T08:21:20Z | 2026-07-02T08:23:56Z | 2m 36s |
| red | 2026-07-02T08:23:56Z | 2026-07-02T08:50:40Z | 26m 44s |
| green | 2026-07-02T08:50:40Z | 2026-07-02T09:30:43Z | 40m 3s |
| review | 2026-07-02T09:30:43Z | 2026-07-02T09:47:04Z | 16m 21s |
| finish | 2026-07-02T09:47:04Z | - | - |

## Sm Assessment

**Setup complete; routing to TEA (red phase).** Session, story context (`sprint/context/context-story-158-40.md`), and feature branch `feat/158-40-dogfight-position-graph` (sidequest-content, base `develop` per gitflow) are in place; sprint status is `in_progress`.

- **Jira:** explicitly skipped — integration not enabled for this project (no key).
- **Repos correction (authoritative here):** epic YAML records `repos: pennyfarthing`, a data-entry error — that repo does not exist in `.pennyfarthing/repos.yaml`. The story is pure content authoring in `sidequest-content/genre_packs/space_opera/dogfight/`, so **repos = content**. `pf sprint story update` has no `--repos` flag; the finish flow reads repos from this session (161-2 precedent), so the stale YAML is non-blocking.
- **Dependencies verified:** Plans 1–3 (158-31 firewall, 158-29 router/lifecycle, 158-39 opponent brain) are all done/approved — this story is unblocked.
- **Scope guard for TEA:** geometry + gun_solution only — the firewall stands; no damage tables, no server engine changes. If a server-side test surface turns out to be needed (fixture packs exist at `sidequest-server/tests/fixtures/packs/swn_test_pack/dogfight/`), record the cross-repo expansion in this session before acting on it.

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `sidequest-server/tests/genre/test_state_graph_models.py` — AC-1: `InteractionCell.next_state`, `ConfrontationDef.interaction_tables` registry, back-compat empty default; GREEN guard pinning the §2 firewall (`damage` still rejected on the cell model)
- `sidequest-server/tests/genre/test_state_graph_loader.py` — AC-2: `_from:`-list resolution keyed by `starting_state`, duplicate/missing fail-loud (path-proof match phrases), parent-traversal rejection, single-table auto-registration back-compat; GREEN guard on the fixture-builder constants
- `sidequest-server/tests/game/test_encounter_dogfight_state.py` — AC-3: `dogfight_state` default/round-trip/legacy-dump back-compat (resume-safe)
- `sidequest-server/tests/server/dispatch/test_sealed_letter_next_state.py` — AC-4: outcome carries cell `next_state`; None = stay; extend-and-return FORCES merge over the cell's authored target (+ pins the geometry reset so transition and reset can't drift apart)
- `sidequest-server/tests/server/dispatch/test_dogfight_state_machine.py` — AC-5 + AC-8 wiring through `_apply_narration_result_to_snapshot`: instantiation stamps entry state (plain fixture pack — back-compat), turn advances state + NEXT turn provably resolves from the new state's table (distinguishing narration hint), extend-and-return walks back to merge, `dogfight.state_transition` spans in walk order, unknown target state raises
- `sidequest-server/tests/cli/test_state_graph_validator.py` — AC-6 + AC-7 on synthetic packs (per `feedback_no_content_in_unit_tests`): graph closure, unreachable-table rejection, damage-key-in-view firewall (views are open dicts — the validator is the ONLY enforcement point), descriptor-schema↔registry mvp consistency both directions (this forces the six-state space_opera graph), `_from:`-pointer following
- `sidequest-server/tests/_helpers/state_graph_fixture.py` — tmp_path state-graph rewrite of `swn_test_pack` (shared fixture untouched; see deviations)
- `sidequest-server/tests/genre/test_dogfight_content_loading.py` — UPDATED: two stale 158-31-era tests replaced with post-firewall pins (no-native-dial; maneuvers-metadata coverage) — file back to 9/9 green

**Tests Written:** 25 failing + 3 green doctrine guards, covering all 8 ACs
**Status:** RED (verified by testing-runner, three runs). Every failure names a missing 158-40 surface: `next_state` rejected (`extra="forbid"`), `interaction_tables` unknown field, `dogfight_state` missing, `SealedLetterOutcome.next_state` missing, validator rules absent. Collateral suites green: updated conformance file 9/9, sealed-letter + dispatch-integration + firewall-validator 30/30.

**Branches:** `feat/158-40-dogfight-position-graph` — server pushed (commits `test: add failing tests...` + `test: harden 158-40 RED...`); content branch created on fresh develop, no commits yet (Dev's Task 6 authoring lands there).

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions / fail-loud | `test_duplicate_starting_state_fails_loud`, `test_missing_starting_state_fails_loud`, `test_unknown_next_state_fails_loud`, `test_rejects_dangling_next_state` | failing (RED) |
| #3 type annotations at boundaries | `test_cell_next_state_defaults_none`, `test_dogfight_state_defaults_none` (typed `str \| None` optional-field contracts) | failing (RED) |
| #6 test quality | Self-check below; value-specific assertions throughout (hints, span attrs, registry identity) — the 161-2 reviewer's value-blind-fields lesson applied | done |
| #8 unsafe deserialization | loader path uses `yaml.safe_load` (pre-existing); traversal rejection re-pinned for the new list path — `test_from_list_rejects_parent_traversal` | failing (RED) |
| #11 input validation at boundaries | same traversal test + validator boundary rules (dangling/unreachable/damage-in-view) | failing (RED) |

**Rules checked:** 5 of 5 applicable lang-review rules have test coverage (#2/#4/#5/#7/#9/#10/#12 have no surface in a tests-only diff; Dev's green diff re-scans all 13).
**Self-check:** 3 spurious/wrong-reason results found by verification and fixed — two loader tests passed via pytest tmp_path name leaking into the error's embedded path (match patterns now space-containing phrases a path cannot satisfy), one models test failed on chained `ConfrontationDef` combat validators rather than the missing field (arrange now seeds hp/armor_class/dexterity). No vacuous assertions remain; `test_accepts_closed_graph` passes vacuously until the validator rules exist (labeled as a non-regression guard).

### Notes for Dev (Naomi)

- The implementation plan is `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-4-state-graph.md` — Tasks 1–7 in order; the RED suite maps 1:1 onto its interfaces.
- The two loader fail-loud tests pin the plan's error phrases: "duplicate interaction_tables starting_state" / "missing starting_state" — keep those phrases (or adjust the match with a logged deviation).
- Plan Task 4's entry-state snippet (`next(iter(cdef.interaction_tables), None)`) is dict-order-dependent; the tests pin entry == the single/first table's `starting_state` ("merge"). Prefer an explicit rule (e.g. the legacy `interaction_table.starting_state`, else first list entry) over dict-iteration luck.
- Green MUST include `python -m sidequest.cli.validate` against live space_opera (Plan Task 7 Step 3) — per `feedback_no_content_in_unit_tests`, pytest never pins live content, so the validate CLI run is where AC-6's six-state graph is enforced on the real pack.
- Content Task 6 lands on the EXISTING `feat/158-40-dogfight-position-graph` branch in sidequest-content (already on fresh develop with #511's maneuver metadata).
- `_MERGE_STARTING_GEOMETRY` in sealed_letter.py stays hardcoded per the plan's self-review (schema-driven reset is an acknowledged follow-up, not this story).

**Handoff:** To Dev for implementation (GREEN).

## Finish State (SM, awaiting human merge)

**Story status: `in_review`** — both PRs are open, CLEAN, and MERGEABLE, awaiting Keith's merge (the auto-mode review gate correctly refused agent self-merge of agent-reviewed PRs):
- **server:** slabgorb-org/sidequest-server **#1105** (head `feat/158-40-dogfight-position-graph` @ `0eac309a` — includes a clean merge of develop after #1103/158-53 landed mid-story). NOTE: #1104 was CLOSED superseded — the finish-preflight subagent created it with head `main` (an old ref) instead of the feature branch, which is why it reported CONFLICTING; #1105 is the corrected PR.
- **content:** slabgorb-org/sidequest-content **#512** (head @ `046e121`), MERGEABLE.

**After Keith merges both:** run `/pf-work` (or `/pf-sm`) — the finish flow resumes with `pf sprint story finish 158-40`, then the sprint-completion commit. Per the 159-5 sidecar lesson, VERIFY both PRs report `state: MERGED` before the finish ceremony.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (mechanical GREEN both repos; 9/10 residual full-suite failures reproduced on develop HEAD 199ad304, 1 xdist flake serial-clean; 0 code smells) | N/A — 3 newly-catalogued pre-existing failures filed as a delivery finding |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [EDGE] observations) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [SILENT] observations) |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (mutation-tested the keystone; verified match= path-proofing; 0 vacuous/value-blind assertions) | confirmed 3 (1 MEDIUM per-state shape guards, 1 LOW frameless path already Dev-filed, 1 LOW non-list branch) |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 5 (all LOW doc-staleness; 3 high-confidence, 2 medium verified against diff) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [TYPE] observations) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain self-assessed; my own pass found the validator traversal gap, independently corroborated by rule-checker #5/#11 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see [SIMPLE] observations) |
| 9 | reviewer-rule-checker | Yes | findings | 8 rule-matches → 4 distinct issues (18 rules × 67 instances swept) | confirmed 4 (downgraded severities with rationale below; dismissed 0) |

**All received:** Yes (4 enabled returned — preflight, test-analyzer, comment-analyzer, rule-checker; 5 disabled via settings and self-assessed)
**Total findings:** 12 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Correct, wired, doctrine-true cross-repo work — the dogfight's relative-position graph is real, observable, and the §2 firewall held everywhere. All 8 ACs verified: 58/58 story tests green (test-analyzer additionally MUTATION-TESTED the AC-5/AC-8 keystone — disabling state advancement and breaking table selection were both caught, so the second-turn-uses-the-new-table proof is genuine, not decorative), full suite 14,466 passed with every residual failure reproduced on develop or confirmed an xdist-only flake, live space_opera validates 0 errors with the six-state graph closed and reachable. Every finding below is quality/robustness — none is Critical or High, so none blocks.

**Data flow traced:** player maneuver → `BeatSelection.beat_id` → commits dict (narration_apply:6060s) → current-state table selected from `cdef.interaction_tables` keyed by `enc.dogfight_state` (unknown state raises, narration_apply:6056-6062) → `resolve_sealed_letter_lookup` validates the maneuver against `maneuvers_consumed` (illegal input raises, sealed_letter.py:163-171) → cell views merge into `per_actor_state` → extend-and-return may force `next_state="merge"` (sealed_letter.py:334) → transition gate rejects unregistered targets, emits `dogfight.state_transition(from,to)`, advances `enc.dogfight_state` (narration_apply:6172-6188) → field serializes with the encounter (resume-safe, round-trip tested). Safe: every skew point (bad maneuver, bad state, bad content) raises loudly; content is triple-gated (pydantic `extra="forbid"`, loader fail-louds, validator CLI).

**Pattern observed (good):** identity-preserving back-compat via `model_validator` — `_autoregister_single_table` (genre/models/rules.py:578) registers the SAME `InteractionTable` object so every consumer reads one registry shape and `d.interaction_tables["merge"] is d.interaction_table` holds; model-level (not loader-level) placement means direct constructions in tests/fixtures get it too.

**Error handling:** unknown transition target → `ValueError` naming the state and the registry (narration_apply:6174-6178, tested with the ghost_state pack); duplicate/missing `starting_state` and parent traversal → `GenreLoadError` with pinned phrases (loader.py:336-367, all three tested); registry-empty sealed-letter def → loud at both the seater (encounter_lifecycle:1916) and the apply seam (narration_apply:6040).

**Observations (12 confirmed findings + VERIFIEDs):**

- `[SEC]/[RULE]` **MEDIUM** — validator-side `_from:` resolution has no traversal guard: `_resolve_raw_state_tables` reads `pack_dir / entry["_from"]` directly (cli/validate/rules.py:149) while the runtime loader rejects absolute/`..` paths (`_resolve_from_pointer`). Found independently by my security pass and rule-checker #5/#11 (CWE-22/59). Consequences: a content PR (Jade's onboarding path is PR-based) could make `pf validate rules` read outside the pack, AND a traversal-using pack validates clean yet fails to load — a validator/loader verdict split. Downgrade rationale vs High: dev-local/CI read-only tool, runtime path fully guarded + tested, no file content echoed beyond YAML-parse errors. Fix is ~5 lines mirroring the loader.
- `[RULE]` **MEDIUM** — the legacy-save `dogfight_state` fallback (`enc.dogfight_state or (...)`, narration_apply:6054) fires with zero log/span. Rules #4/#14/#17 (matched by rule-checker; cannot dismiss). The default itself is sound documented back-compat, but the GM panel cannot distinguish "resumed from stamped state" from "state was None and defaulted" — a corrupted state on a current save is invisible. One `logger.warning` or an attr on the next transition span closes it.
- `[RULE]/[SILENT]` **MEDIUM** — beat_filter's menu fallback (beat_filter.py:388-389) reads the FIRST registry table with no enforced invariant that per-state `maneuvers_consumed` agree; the code comment admits the condition but nothing checks it. A future state with a divergent maneuver set silently shows the wrong menu. Cheapest durable fix: a `_check_state_graph` rule requiring identical `maneuvers_consumed` across a def's tables (they are identical in all six today — verified).
- `[TEST]` **MEDIUM** — the three live-content cell-shape guards (16-cell cross product, no orphan pairs, populated narration) still run ONLY against the merge table (test_dogfight_content_loading.py:90s fixture), while the story's content deliverable is five MORE tables; neither pytest nor `_check_state_graph` would catch a future 15-cell or empty-hint drift in beam/overhead/scissors/overshoot/tail_chase. Content verified defect-free today (test-analyzer script + Dev's checks). Fix: parametrize over `interaction_tables.values()` or add the three checks to the validator (the better home per `feedback_no_content_in_unit_tests`).
- `[RULE]` **LOW** — `_check_state_graph`'s own YAML-parse `except: return` (cli/validate/rules.py:205) records nothing, relying on call-order coupling with `_check_confrontation_firewall` (which records RULES_LOAD_FAILURE first; single caller, comment documents it). Rule #1 match — confirmed, not dismissed; downgraded because the coupling is real, commented, and covered today. A distinct issue code or a shared parse helper removes the coupling.
- `[TEST]` **LOW** — the frameless sealed-letter zero-npcs raise path has no test post-realignment (test-analyzer corroborates Dev's own filed finding — tracked, not dropped).
- `[TEST]` **LOW** — loader's `interaction_tables`-not-a-list branch untested (loader.py:343).
- `[DOC]` **LOW** ×5 — (1) narration_apply:6029 comment cites the renamed beats test and asserts the deleted "dogfight beats ARE the maneuvers" premise; (2) test_dogfight_content_loading.py:16 docstring still pins the singular-table shape; (3) descriptor_schema.yaml:154 preamble still says "MVP ships with ONE starting state" above six mvp states; (4) SealedLetterOutcome/resolver docstrings omit the new `next_state` in their field enumerations (sealed_letter.py:74,141); (5) rules.yaml:560 pre-existing comment describes a single adjacent table file under the six-file registry.
- `[EDGE]` **LOW** (self-assessed, edge-hunter disabled) — extend-and-return targets literal `"merge"`: a future sealed-letter pack whose registry lacks a merge state gets a loud apply-seam raise on the first dissolving engagement (correct per fail-loud, but the coupling between the E&R rule and the merge-state convention is only enforced at runtime; a validator rule "registry must contain the E&R target" would move it to authoring time). Also: a def authoring BOTH `interaction_table` and `interaction_tables` is legal to the model and unvalidated for consistency between them — obscure, loud-at-runtime if skewed.
- `[SIMPLE]` **LOW** (self-assessed, simplifier disabled) — the entry-state derivation appears three ways (encounter_lifecycle:2168-2174 stamp, narration_apply:6054 fallback, beat_filter:388 menu); a single `cdef.entry_interaction_table()` helper would keep the three from drifting. No dead code otherwise — rule-checker #15 confirmed 10/10 new symbols have live production consumers.
- `[TYPE]` (self-assessed, type-design disabled) — see VERIFIEDs; no stringly-typed regressions: `next_state`/`dogfight_state` are open-set content ids where `str | None` is the correct type (states are pack-authored, not an enum).
- `[SILENT]` (self-assessed, silent-failure-hunter disabled) — the two flagged fallbacks above are the only candidates; every other new degrade path raises or records (loader ×3, apply seam ×2, seater ×1, validator issue-records ×5).

**VERIFIEDs (evidence + rule compatibility):**
- `[VERIFIED][TYPE]` auto-registration preserves identity — genre/models/rules.py:578-586 assigns the same object (`{self.interaction_table.starting_state: self.interaction_table}`); pinned by `test_single_table_def_autoregisters_backcompat` (`is` assertion). Complies with AC-2 back-compat + one-lookup-shape (No Silent Fallbacks: consumers never branch on shape).
- `[VERIFIED]` wiring — `dogfight_state_transition_span`'s only non-test call site is the production apply path (narration_apply:6183) and `SPAN_ROUTES[SPAN_DOGFIGHT_STATE_TRANSITION]` is registered with from/to extraction (telemetry/spans/dogfight.py:48-58); the state-machine suite drives production `_apply_narration_result_to_snapshot`, not the resolver (rule-checker #16/#17 corroborate). Complies with OTEL Observability Principle for the transition itself.
- `[VERIFIED][EDGE]` extend-and-return already-at-merge is a no-op transition — narration_apply:6172 guards `next_state != current_state`, so no span/no error when E&R fires in merge; the reset remains visible via `extend_and_return_triggered` on the cell_resolved span (sealed_letter.py:319-325). Correct: no state change occurred.
- `[VERIFIED][SEC]` runtime `_from:` list resolution inherits the traversal guard — loader.py:346 delegates each entry to `_resolve_from_pointer` (absolute/`..` rejection at loader.py:391-406), pinned by `test_from_list_rejects_parent_traversal`. The gap is validator-side only (finding above).
- `[VERIFIED][RULE]` §2 firewall — rule-checker #18: 5/5 instances compliant; no damage/dial fields anywhere in the diff; `_ALLOWED_VIEW_KEYS` (cli/validate/rules.py:117-133) actively strengthens enforcement on the open-dict views the pydantic model cannot police; all four new content tables audited by their authors + validator (0 errors live).
- `[VERIFIED]` Guitar-Solo/SOUL neutrality — the diff adds no narration constraints and no player verb gating; the maneuver menu still derives from content (`maneuvers_consumed`), preserving the open-verb doctrine (beat_filter synthesis unchanged in shape).

### Rule Compliance (lang-review/python.md + CLAUDE.md doctrine, exhaustive — rule-checker sweep of 18 rules × 67 instances, cross-checked)

- **#1 silent exceptions** — validator parse-error `return` (rules.py:205): **finding above** (LOW, mitigated by documented call-order). Other 2 except-paths record issues: compliant.
- **#2 mutable defaults** — 6/6 new defaults immutable or default_factory: compliant.
- **#3 annotations at boundaries** — 7/7 new/changed signatures + fields typed: compliant.
- **#4 logging** — dogfight_state fallback unlogged: **finding above** (MEDIUM). Raise-without-log on content errors matches file convention: compliant.
- **#5 path handling** — validator `_from:` traversal gap: **finding above** (MEDIUM). All read_text calls carry encoding; loader delegates to the guarded resolver: compliant.
- **#6 test quality** — 9 files, 0 vacuous/value-blind/skipped/mock-misuse; keystone mutation-tested; match= patterns path-proof: compliant.
- **#7 resource leaks / #9 async / #12 dependencies** — no instances in diff: N/A.
- **#8 unsafe deserialization** — 3/3 yaml.safe_load: compliant.
- **#10 import hygiene** — local span import matches file convention (16+ precedents); no cycles (telemetry.spans is a leaf); `__all__` correct: compliant.
- **#11 input validation** — validator traversal (finding above); loader list validation + pydantic extra=forbid boundaries: compliant.
- **#13 fix-regressions** — hardening commit re-scanned: compliant.
- **No Silent Fallbacks** — beat_filter menu invariant + unlogged state fallback: **findings above**; all other degrade paths loud: compliant.
- **No Stubbing / Verify Wiring / OTEL** — 10/10 symbols consumed, span production-wired + routed; resume-fallback observability gap is the one OTEL finding.
- **Bind the Ruleset (§2 firewall)** — 5/5 compliant; validator strengthens it.

### Devil's Advocate

Assume it's broken. **The save that outlives its map.** A player quits mid-duel in `scissors`; next week a content PR renames or deletes the scissors table. On resume, every turn raises "no interaction table for state 'scissors'" — the duel is wedged, and unlike 158-41's narrator degrade, nothing converts this into a player-facing "the engine could not resolve that." Loud-over-silent is doctrine (reference-page anchors break loudly by design), and content-save skew is a pre-existing class, but note the failure LOOPS: the encounter can neither advance nor resolve until content restores the state or the save is edited. If graph authoring becomes frequent (Jade authoring packs), a "resolved-state migration" or E&R-style reset on unknown-state-resume may be kinder — I'm recording the observation, not blocking on it, because today's graph is append-only and space_opera-only. **The unfair sky.** Red (the player) can EARN tail_chase; blue's mirror geometry yields scissors — a mechanics-first player comparing mirrored plays will see the asymmetry. The SWN math (gun_solution, geometry modifiers) carries the real lethality and IS symmetric per cell; the asymmetry is which RPS table hosts the next beat. Dev logged it, the rationale (role-fixed tables prevent geometric teleports) is sound, and a mirrored-states follow-up is filed — accepted, watch it in playtest. **The menu that lies.** If per-state maneuver sets ever diverge, beat_filter shows the entry state's menu while the resolver enforces the active state's — the player could be offered a maneuver the resolver then rejects loudly mid-turn. Today all six sets are identical; the MEDIUM finding demands the invariant be enforced, not assumed. **The validator that trusts.** A malicious content PR can point `_from:` outside the pack and the validator reads it; it can also hide a `damage:` key in a view — caught; a 15-cell table — NOT caught (MEDIUM finding); an off-enum bearing (`"0230"`, already shipped in tail_chase) — not caught, pre-existing, filed by Dev. The validator's blind spots are now enumerated findings rather than unknowns. Nothing here rises to Critical/High; the engine fails loud at every skew point I could construct.

**Handoff:** To SM for finish-story.

## Dev Assessment

**Implementation Complete:** Yes — all 8 ACs green, engine + content halves both landed.

**Files Changed (sidequest-server, commit f023b4fe):**
- `sidequest/genre/models/rules.py` — `InteractionCell.next_state`; `ConfrontationDef.interaction_tables` registry + identity-preserving single-table auto-registration (AC-1)
- `sidequest/genre/loader.py` — `interaction_tables` `_from:`-list resolution keyed by `starting_state`; duplicate/missing/traversal fail-loud (AC-2)
- `sidequest/game/encounter.py` — `StructuredEncounter.dogfight_state`, serialized (AC-3)
- `sidequest/server/dispatch/sealed_letter.py` — `SealedLetterOutcome.next_state`; extend-and-return forces `merge` (AC-4)
- `sidequest/server/dispatch/encounter_lifecycle.py` — entry-state stamp at instantiation; registry-aware table gate (AC-5)
- `sidequest/server/narration_apply.py` — current-state table selection, transition advance, unknown-state raise, `dogfight.state_transition` span (AC-5)
- `sidequest/telemetry/spans/dogfight.py` — the transition span + watcher route (AC-5)
- `sidequest/cli/validate/rules.py` — state-graph rules: closure, reachability, view-key firewall, schema↔registry mvp consistency, `_from:`-following (AC-6/7)
- `sidequest/game/beat_filter.py` — maneuver menu survives registry-only defs (wiring the plan missed)
- Test realignments: `tests/server/test_encounter_lifecycle.py` (§6 contract), `tests/genre/test_dogfight_content_loading.py` (registry fixture), arrange/helper fixes in the state-graph test files (see deviations)

**Files Changed (sidequest-content, commit on feat/158-40-dogfight-position-graph, pushed):**
- `genre_packs/space_opera/rules.yaml` — six-table `interaction_tables` registry (merge entry-first)
- `dogfight/interactions_{beam,overhead,scissors,overshoot}.yaml` — NEW, 16-cell tables each, BFM-doctrine-grounded (Shaw/Boyd/Boelcke), firewall-clean views
- `dogfight/interactions_mvp.yaml` (+5 transitions), `dogfight/interactions_tail_chase.yaml` (+3 transitions incl. overshoot + two explicit merge re-entries)
- `dogfight/descriptor_schema.yaml` — beam/overhead promoted to mvp; scissors/overshoot added with initial descriptors

**Graph shape (verified):** closed + all six states reachable from merge — merge→{beam, scissors, tail_chase}, tail_chase→{merge, overshoot}, beam→{overhead, scissors}, overhead→{beam, overshoot, scissors, tail_chase}, scissors→{tail_chase}, overshoot→{beam, scissors}; extend-and-return provides the runtime reset to merge from any dissolving engagement.

**Tests:** 54/54 story tests + 4/4 state-machine wiring (serial) GREEN; full suite 14,467 passed / 341 skipped / 0 NEW regressions (5 pre-existing failures + 3 xdist flakes classified in Delivery Findings). `python -m sidequest.cli.validate.rules` over ALL live packs: 0 errors, 0 warnings (AC-6 live enforcement). ruff check/format + pyright clean on every changed file.

**Branches:** `feat/158-40-dogfight-position-graph` — server f023b4fe pushed; content pushed.

**Handoff:** To Reviewer for code review (tdd: green → review).

## Cross-Repo Expansion (TEA, red phase — per SM scope guard)

**Repos: server + content** (was: content only). The story YAML/description says "pure content authoring," but the authoritative implementation plan `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-4-state-graph.md` (written for this exact story) specifies server engine work in Tasks 1–5 and 7: `InteractionCell.next_state`, a `ConfrontationDef.interaction_tables` registry, loader `_from:`-list resolution, `StructuredEncounter.dogfight_state`, resolver/apply state machine, `dogfight.state_transition` OTEL span, and a validate-CLI graph-closure guard. This is not optional: both `InteractionCell` and `ConfrontationDef` are `extra="forbid"` pydantic models, so authoring `next_state:`/`interaction_tables:` in content **without** the server schema makes the space_opera pack fail to load at all. Content-only delivery is unimplementable as specced.

**Branches:** `feat/158-40-dogfight-position-graph` in BOTH `sidequest-server` and `sidequest-content` (both created off fresh `origin/develop`). ACs (8) recorded on the story via `pf sprint story update --add-ac`.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Conflict** (blocking, resolved in-phase): story description says "pure content authoring" but ADR-153 §3 + Plan 4 require server engine work (schema, loader, resolver, apply seam, OTEL, validator); recorded the cross-repo expansion above and split the RED tests server-side accordingly. Affects `sprint/epic-158.yaml` (158-40 description understates scope — future plan-decomposed stories should carry the plan doc path in the YAML). *Found by TEA during test design.*
- **Gap** (non-blocking, fixed in-phase): `sm-setup` branched sidequest-content from a stale local `develop` (tip #509, missing merged PR #511 — the 158-39 maneuver-metadata content), so the loaded dogfight def had `maneuvers: []`. Fixed by `git fetch origin develop:develop` + resetting the empty feature branch onto it. Affects `pennyfarthing-dist` setup flow (sm-setup should `git fetch` before branching, or fail loud when local base is behind origin). *Found by TEA during test design.*
- **Gap** (non-blocking, fixed in-phase): two conformance tests in `sidequest-server/tests/genre/test_dogfight_content_loading.py` (`test_dogfight_has_dual_track_metrics`, `test_dogfight_beats_cover_every_consumed_maneuver`) assert the native dial/beats shapes that 158-31 (ADR-153 §2 firewall) deleted from live content — they fail today against any checkout with sidequest-content present, and have since content #508 merged (2026-06-27). 158-31's server-side test sweep missed them. Removed in this story's RED commit with rationale. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): the existing `interactions_tail_chase.yaml` uses bearing values outside the descriptor-schema octant enum (`0230`, `0830`, `10`, `02` vs the schema's eight octants) — pre-existing content drift surfaced while authoring the new tables (which are strict). The state-graph validator checks view KEYS only, not enum VALUES. Affects `sidequest-content/genre_packs/space_opera/dogfight/interactions_tail_chase.yaml` (normalize bearings) and optionally `sidequest-server/sidequest/cli/validate/rules.py` (add view-VALUE enum checking against descriptor_schema). *Found by Dev during implementation (via scenario-designer audit).*
- **Gap** (non-blocking): a stale §6 seating test survived Plan 1's realignment sweep — `test_sealed_letter_empty_npcs_present_raises_without_consuming_fallback` (tests/server/test_encounter_lifecycle.py) still asserted the pre-§6 "got 0 npcs_present" refusal, contradicting the passing `test_dogfight_zero_npcs_seats_default_ship_from_frame`; it has been failing on any tree since §6 landed (2026-06-27). Realigned to the §6 contract in this story per the standing 2026-06-27 ruling (its true guard — the co-located bystander is never promoted into the duel — is preserved). Affects nothing further. *Found by Dev during implementation.*
- **Gap** (non-blocking): five pre-existing full-suite failures unrelated to 158-40, confirmed by isolation + root-cause triage (run 158-40-dev-green-2): `test_scenario_bind.py` ×2 + `test_45_2_chargen_to_playing_wire.py` (pregen namegen "no cultures available"), `test_102_7`/`test_103_10` mutation-span tests (WN engine drops narrator beats — `wn_combat_beat_dropped_engine_owns_round`, ADR-143 edge), and `test_beneath_sunden_creature_images_107_2.py` (42 bestiary entries missing image specs). Affects those suites' own stories (need separate tracker entries). *Found by Dev during implementation.*
- **Question** (non-blocking): the frameless sealed-letter zero-npcs path ("leave npcs_present empty so the arity guard fails loud" — encounter_lifecycle §6 else-comment) appears to have no dedicated test after the realignment; worth a small guard test in a follow-up. Affects `sidequest-server/tests/server/test_encounter_lifecycle.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the validator's `_from:` resolution should mirror the loader's absolute/`..` rejection, and `_check_state_graph` should enforce two more invariants — identical `maneuvers_consumed` across a def's tables (beat_filter's menu assumes it) and the cell-shape trio (full cross product, no orphan pairs, populated narration) for EVERY table, not just merge. Affects `sidequest-server/sidequest/cli/validate/rules.py` (add checks) and `sidequest-server/tests/genre/test_dogfight_content_loading.py` (or parametrize the shape guards). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the legacy-save `dogfight_state` entry-state fallback should emit a `logger.warning` or span attribute so the GM panel can distinguish a defaulted state from a stamped one (OTEL doctrine). Affects `sidequest-server/sidequest/server/narration_apply.py:6054`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): three previously-uncatalogued PRE-EXISTING full-suite failures reproduced on develop HEAD `199ad304` by preflight: `test_106_1_chargen_armor_wire.py::test_chargen_confirm_fires_armor_derivation_through_real_wire`, `tests/integration/test_wwn_scene_harness_fixture_proof.py::test_hydrated_wwn_fixture_drives_cast_spell_and_ablates_hp`, `test_153_19_character_location_cleanup_wiring.py::test_orphan_location_cleanup_fires_on_real_chargen_commit` — beyond the five already filed by Dev. Affects the tracker (chargen-wire test health needs its own story). *Found by Reviewer during code review.*
- **Question** (non-blocking): resuming a save whose `dogfight_state` names a since-removed content state raises loudly EVERY turn — the duel wedges rather than degrading (contrast 158-41's narrator degrade doctrine). Acceptable for an append-only graph today; if pack authoring churn grows, consider an unknown-state-on-resume reset-to-entry with a loud span. Affects `sidequest-server/sidequest/server/narration_apply.py` (design question, not a defect). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 1 Question, 0 Improvement)
**Blocking:** None

- **Question:** resuming a save whose `dogfight_state` names a since-removed content state raises loudly EVERY turn — the duel wedges rather than degrading (contrast 158-41's narrator degrade doctrine). Acceptable for an append-only graph today; if pack authoring churn grows, consider an unknown-state-on-resume reset-to-entry with a loud span. Affects `sidequest-server/sidequest/server/narration_apply.py`.

### Downstream Effects

- **`sidequest-server/sidequest/server`** — 1 finding

### Deviation Justifications

9 deviations

- **Loader tests build tmp_path pack copies instead of editing the shared swn_test_pack fixture**
  - Rationale: in RED, `interaction_tables`/`next_state` are rejected by `extra="forbid"` — editing the shared fixture would turn every existing dogfight suite red for the wrong reason and mask the real RED signal.
  - Severity: minor
  - Forward impact: Dev may migrate the shared fixture in green if Task 5's integration needs it; the single-table shape must stay covered either way (back-compat AC-2 test pins it).
- **E2E graph walk drives the fixture pack, not live space_opera content**
  - Rationale: project rule `feedback_no_content_in_unit_tests` + 96-1 doctrine ("validators validate content; tests test fixtures") outranks the plan text; content-only changes must never turn server tests red.
  - Severity: minor
  - Forward impact: Dev's green MUST include running `python -m sidequest.cli.validate` against live space_opera (Plan 4 Task 7 Step 3) — that is where AC-6's six-state graph is enforced on real content.
- **Validator rules extended beyond Plan 4's single closure check**
  - Rationale: AC-6's "graph connected / six states / firewall" needs a content-side enforcement point; cell views are open dicts so the pydantic model cannot catch a damage key inside them; the schema-consistency rule is what forces the six-state space_opera graph without pytest-pinning live content.
  - Severity: minor (additive)
  - Forward impact: Dev implements 4 more checks in `sidequest/cli/validate/rules.py` — bounded, same raw-YAML pattern as the existing firewall check.
- **Two stale 158-31-era conformance tests replaced (not part of this story's spec)**
  - Rationale: leaving known-red stale tests poisons RED verification; TEA owns test maintenance; the replacements pin the CURRENT doctrine instead of deleting coverage.
  - Severity: minor
  - Forward impact: none (delivery finding filed so 158-31's miss is on record).
- **Extend-and-return content override hook left untested**
  - Rationale: the plan explicitly defers the override hook; testing an unbuilt hook would be stubbing.
  - Severity: minor
  - Forward impact: if a playtest demands per-pack E&R tuning, that is a NEW story with its own red.
- **Fixed-role asymmetric states; blue-advantage geometry routes to symmetric states**
  - Rationale: entering a red-pursues table with blue actually behind red would make every subsequent cell's authored views geometrically wrong (state teleport). Mirrored blue-perspective state variants double the content and are not in the six-state scope.
  - Severity: minor
  - Forward impact: a future "mirrored asymmetric states" story if playtest wants true blue-perspective tail chases; delivery finding filed. Also: overhead's inbound edge is via beam (`[loop, straight]`), not directly from merge — merge's `[loop, loop]` cell is authored "merge resumed" and keeping it stateless respects the existing content.
- **Dev fixed three mechanical defects in TEA's test infrastructure (contracts unchanged)**
  - Rationale: broken arranges block GREEN for reasons outside the tested contract; every assertion is untouched.
  - Severity: minor
  - Forward impact: none.
- **Green-phase test realignments (two files, contracts preserved)**
  - Rationale: the seating test was already failing on develop (it contradicted the passing §6 integration test); the fixture read the field this story's content change vacated. Neither changes what is guarded.
  - Severity: minor
  - Forward impact: none.
- **beat_filter reads the registry's entry table for registry-only defs (consumer the plan missed)**
  - Rationale: without it, live content's move to `interaction_tables` breaks the player's maneuver menu (PackError) — a half-wired feature.
  - Severity: minor
  - Forward impact: if per-state maneuver sets ever diverge, the menu must become state-aware (noted in code comment).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **Loader tests build tmp_path pack copies instead of editing the shared swn_test_pack fixture**
  - Spec source: Plan 4 (2026-06-26-dogfight-rebuild-plan-4-state-graph.md), Task 2 Step 2
  - Spec text: "Edit tests/fixtures/packs/swn_test_pack/.../rules.yaml's dogfight def to use interaction_tables: [...] as part of this step."
  - Implementation: `tests/_helpers/state_graph_fixture.py` copies the fixture into tmp_path and rewrites the copy; the shared fixture stays byte-identical.
  - Rationale: in RED, `interaction_tables`/`next_state` are rejected by `extra="forbid"` — editing the shared fixture would turn every existing dogfight suite red for the wrong reason and mask the real RED signal.
  - Severity: minor
  - Forward impact: Dev may migrate the shared fixture in green if Task 5's integration needs it; the single-table shape must stay covered either way (back-compat AC-2 test pins it).
- **E2E graph walk drives the fixture pack, not live space_opera content**
  - Spec source: Plan 4, Task 7 Step 1
  - Spec text: "Create tests/server/dispatch/test_dogfight_graph_e2e.py: load the real space_opera pack, seat a dogfight, drive maneuver pairs..."
  - Implementation: the walk lives in `test_dogfight_state_machine.py` against the tmp_path state-graph fixture; live-content shape enforcement moved to validator rules (closure, reachability, view-key firewall, schema↔registry mvp consistency).
  - Rationale: project rule `feedback_no_content_in_unit_tests` + 96-1 doctrine ("validators validate content; tests test fixtures") outranks the plan text; content-only changes must never turn server tests red.
  - Severity: minor
  - Forward impact: Dev's green MUST include running `python -m sidequest.cli.validate` against live space_opera (Plan 4 Task 7 Step 3) — that is where AC-6's six-state graph is enforced on real content.
- **Validator rules extended beyond Plan 4's single closure check**
  - Spec source: Plan 4, Task 7 Step 2
  - Spec text: "assert every cell next_state has a registered table"
  - Implementation: four additional rules under test — unreachable-table rejection, damage-key-in-view firewall, descriptor-schema↔registry mvp consistency (both directions), and `_from:`-pointer following.
  - Rationale: AC-6's "graph connected / six states / firewall" needs a content-side enforcement point; cell views are open dicts so the pydantic model cannot catch a damage key inside them; the schema-consistency rule is what forces the six-state space_opera graph without pytest-pinning live content.
  - Severity: minor (additive)
  - Forward impact: Dev implements 4 more checks in `sidequest/cli/validate/rules.py` — bounded, same raw-YAML pattern as the existing firewall check.
- **Two stale 158-31-era conformance tests replaced (not part of this story's spec)**
  - Spec source: story description / Plan 4 (neither mentions them)
  - Spec text: n/a — `test_dogfight_has_dual_track_metrics` and `test_dogfight_beats_cover_every_consumed_maneuver` asserted the dial/beats shapes 158-31 deleted, and have been failing against live content since content #508 (2026-06-27).
  - Implementation: replaced with post-firewall pins (`test_dogfight_carries_no_native_dial`, `test_dogfight_maneuvers_metadata_covers_every_consumed_maneuver`).
  - Rationale: leaving known-red stale tests poisons RED verification; TEA owns test maintenance; the replacements pin the CURRENT doctrine instead of deleting coverage.
  - Severity: minor
  - Forward impact: none (delivery finding filed so 158-31's miss is on record).
- **Extend-and-return content override hook left untested**
  - Spec source: ADR-153 §3 ("an engine rule with a content override hook, per ADR-077 Open Question #5")
  - Spec text: see above; but Plan 4 Risks: "start with the simple engine rule, add the content override only if playtest demands it."
  - Implementation: tests pin the engine rule (reset→merge as a real transition, forced over cell next_state); no content-hook surface tested.
  - Rationale: the plan explicitly defers the override hook; testing an unbuilt hook would be stubbing.
  - Severity: minor
  - Forward impact: if a playtest demands per-pack E&R tuning, that is a NEW story with its own red.

### Dev (implementation)
- **Fixed-role asymmetric states; blue-advantage geometry routes to symmetric states**
  - Spec source: ADR-153 §3 / Plan 4 Task 6 (the six-state graph + its example transition)
  - Spec text: Plan 4's example transitions merge `[straight, loop]` ("Blue reverses onto Red's six") → `tail_chase`; but `interactions_tail_chase.yaml`'s authored role convention is "Red is the PURSUER".
  - Implementation: asymmetric states are role-fixed (tail_chase/overhead = red advantage, overshoot = red disadvantage). Blue-advantage geometries transition to SYMMETRIC states with the advantage encoded in descriptors: live merge `[straight, loop]` → `scissors` (not tail_chase); `[loop, straight]` (red gains the six) → `tail_chase`. Mirror cells route symmetrically (`[bank, straight]`/`[straight, bank]` both → `beam`) so neither seat gets a free state advantage from mirrored geometry.
  - Rationale: entering a red-pursues table with blue actually behind red would make every subsequent cell's authored views geometrically wrong (state teleport). Mirrored blue-perspective state variants double the content and are not in the six-state scope.
  - Severity: minor
  - Forward impact: a future "mirrored asymmetric states" story if playtest wants true blue-perspective tail chases; delivery finding filed. Also: overhead's inbound edge is via beam (`[loop, straight]`), not directly from merge — merge's `[loop, loop]` cell is authored "merge resumed" and keeping it stateless respects the existing content.
- **Dev fixed three mechanical defects in TEA's test infrastructure (contracts unchanged)**
  - Spec source: the RED suite itself (tests are the spec for green)
  - Spec text: n/a — arrange/helper bugs, not assertion changes
  - Implementation: (1) fixture-builder tmp copies renamed to keep the pack dir name `swn_test_pack` (lethality_policy.yaml pins genre_key == dir name; masked in RED because rules-load failed first); (2) `_inline_table`'s `next_state` indent moved from table level (12 sp) to cell level (16 sp) — at table level both graph-validator tests exercised nothing; (3) two model-test arranges seeded the reserved combat keys (hp/armor_class/dexterity) required by chained ConfrontationDef validators.
  - Rationale: broken arranges block GREEN for reasons outside the tested contract; every assertion is untouched.
  - Severity: minor
  - Forward impact: none.
- **Green-phase test realignments (two files, contracts preserved)**
  - Spec source: the RED suite + ADR-153 §6 (2026-06-27 ruling on stale seating tests)
  - Spec text: `test_sealed_letter_empty_npcs_present_raises_without_consuming_fallback` asserted the pre-§6 "got 0 npcs_present" refusal; `test_dogfight_content_loading.py`'s `dogfight_table` fixture read the singular `interaction_table`.
  - Implementation: the seating test realigned to the §6 frame-default contract (renamed `..._seats_frame_default_never_location_fallback`; its true guard — the co-located bystander is never promoted into the duel — now asserted directly against the seated actors). The conformance fixture reads `interaction_tables["merge"]` (live content moved to the registry, so the legacy field is None).
  - Rationale: the seating test was already failing on develop (it contradicted the passing §6 integration test); the fixture read the field this story's content change vacated. Neither changes what is guarded.
  - Severity: minor
  - Forward impact: none.
- **beat_filter reads the registry's entry table for registry-only defs (consumer the plan missed)**
  - Spec source: Plan 4 (Tasks 1–7 file list)
  - Spec text: plan names models/loader/encounter/sealed_letter/encounter_lifecycle/narration_apply/validate — `sidequest/game/beat_filter.py` is absent.
  - Implementation: the sealed-letter maneuver-menu synthesis falls back to the first registered table when `interaction_table` is None (registry-only content); per-state menus are identical in authored content.
  - Rationale: without it, live content's move to `interaction_tables` breaks the player's maneuver menu (PackError) — a half-wired feature.
  - Severity: minor
  - Forward impact: if per-state maneuver sets ever diverge, the menu must become state-aware (noted in code comment).

### Reviewer (audit)
- **TEA: tmp_path pack copies instead of editing the shared fixture** → ✓ ACCEPTED by Reviewer: editing the shared fixture in RED would have poisoned every dogfight suite with wrong-reason failures; the tmp_path builder keeps the RED signal clean and the shared single-table fixture still pins back-compat.
- **TEA: e2e drives the fixture pack, not live space_opera** → ✓ ACCEPTED by Reviewer: `feedback_no_content_in_unit_tests`/96-1 doctrine outranks the plan text; live enforcement moved to the validate CLI, which I confirmed runs clean on the six-state graph. My [TEST] MEDIUM finding notes the validator subset should also carry the cell-shape trio — an extension, not a reversal.
- **TEA: validator rules extended beyond Plan 4's closure check** → ✓ ACCEPTED by Reviewer: all four additions are tested, generic (no live-content pinning), and two of my own findings ask for MORE of exactly this.
- **TEA: stale 158-31-era conformance tests replaced** → ✓ ACCEPTED by Reviewer: the replacements pin CURRENT doctrine (no-dial, maneuvers-metadata) and both pass against live content; deleting without replacement would have dropped coverage.
- **TEA: extend-and-return content override hook left untested** → ✓ ACCEPTED by Reviewer: Plan 4's Risks section explicitly defers the hook; testing an unbuilt surface is stubbing.
- **Dev: fixed-role asymmetric states; blue-advantage routes to symmetric states** → ✓ ACCEPTED by Reviewer: the alternative (entering a red-pursues table with inverted actual geometry) produces authored views that lie about the fiction — worse than the asymmetry. SWN resolution stays symmetric per cell; the asymmetry is table-hosting only. Watch in playtest; mirrored-states follow-up is filed as a finding.
- **Dev: three mechanical fixes to TEA's test infrastructure** → ✓ ACCEPTED by Reviewer: verified all three change arranges/helpers only — every assertion contract is untouched (test-analyzer independently confirmed no weakened assertions in the hardening commit).
- **Dev: green-phase test realignments (§6 seating test + conformance fixture)** → ✓ ACCEPTED by Reviewer: I verified the §6 contradiction myself — `test_dogfight_zero_npcs_seats_default_ship_from_frame` (passing, Plan-1-authored) and the old raise-expectation cannot both hold; the realigned test still asserts the bystander is never seated, by name. The fixture realignment follows the content's registry move.
- **Dev: beat_filter reads the registry's entry table** → ✓ ACCEPTED by Reviewer AS the necessary wiring the plan missed — paired with my [RULE] MEDIUM finding: the identical-maneuvers invariant it assumes must become a validator check, not a comment.

## Notes

### Story Context
- **Title:** Dogfight full relative-position state graph — author beam/overhead/scissors/overshoot + extend-and-return (ADR-153 Plan 4)
- **Points:** 5
- **Type:** feature
- **Priority:** p3
- **Repos:** content (sidequest-content) — note: epic YAML listed "pennyfarthing" as error; correct repo is content
- **Branch Strategy:** gitflow (feat/158-40-dogfight-position-graph)

### Key References
- ADR-153: The Ace of Aces Dogfight (docs/adr/ADR-153.md)
- Plan 1 (158-31, done): Firewall — resolve via SWN hp_depletion; delete native dial + beats
- Plan 2 (158-29, done): Router→seater→lifecycle contract; degrade loudly when no engine seats
- Plan 3 (158-39, done): Opponent brain — narrator-motivated maneuver selection + disposition fallback
- Plan 4 (this story): Full relative-position state graph (beam/overhead/scissors/overshoot) + extend-and-return rule

### Content Location
Pure content authoring in sidequest-content/genre_packs/space_opera/dogfight/:
- descriptor_schema.yaml (beam + overhead currently stubbed as 'future')
- interactions_mvp.yaml (existing interactions)
- interactions_tail_chase.yaml (existing tail_chase interactions)
- maneuvers_mvp.yaml (existing maneuvers)
- pilot_skills.yaml (existing skills)

### Dependency Status
- Plan 1 (158-31, firewall): DONE, approved
- Plan 2 (158-29, router/lifecycle): DONE, approved
- Plan 3 (158-39, opponent brain): DONE, approved
- This story (Plan 4): UNBLOCKED — can proceed