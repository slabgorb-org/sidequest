---
story_id: "102-5"
jira_key: ""
epic: "102"
workflow: "tdd"
---
# Story 102-5: WN narrator tool contract

## Story Details
- **ID:** 102-5
- **Jira Key:** (Jira not enabled for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/102-5-wn-narrator-tool-contract)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T21:36:46Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T18:57:11Z | 2026-06-10T18:58:44Z | 1m 33s |
| red | 2026-06-10T18:58:44Z | 2026-06-10T19:25:53Z | 27m 9s |
| green | 2026-06-10T19:25:53Z | 2026-06-10T21:16:25Z | 1h 50m |
| review | 2026-06-10T21:16:25Z | 2026-06-10T21:25:47Z | 9m 22s |
| green | 2026-06-10T21:25:47Z | 2026-06-10T21:32:23Z | 6m 36s |
| review | 2026-06-10T21:32:23Z | 2026-06-10T21:36:46Z | 4m 23s |
| finish | 2026-06-10T21:36:46Z | - | - |

## Sm Assessment

Story 102-5 set up for TDD (phased). p2, 8 points, server repo only. WN narrator
tool contract per SWN design §8 (P5 follow-on): build the per-module narrator tool
surface so the narrator drives WN resolution through typed tools rather than improv,
isolated behind tool-level tests + OTEL per the §12 risk note. Story context with
technical approach and ACs: sprint/context/context-story-102-5.md; epic context:
sprint/context/context-epic-102.md. Feature branch
feat/102-5-wn-narrator-tool-contract created from fresh sidequest-server develop
(08298b0b); verified 102-5 not already merged on origin/develop. Builds on freshly
merged 102-2 (PR #806, dice-path cast_spell → WN cast spine) and 102-3 (PR #805,
free-play named cast → WN cast spine). Jira not enabled — skipped. Next agent: TEA
(red phase).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **Gap (non-blocking, TEA):** `adjust_system_strain` and `stabilize_mortal_injury`
  declare `ruleset="cwn"` only (single-slug, 73-15 filter), so an **awn**-bound
  narrator is never advertised them even though `AwnRulesetModule` subclasses CWN
  and the handlers accept awn packs (test_awn_pack_applies_strain). The family-
  declaration seam this story forces (`ruleset=("swn","wwn","cwn","awn")`) is the
  natural fix — Dev should extend those two tools' declarations to `("cwn","awn")`
  in this story or flag for 102-7 (AWN live proof will hit this).
- **Improvement (non-blocking, TEA):** the new-file test-DB gate skips silently
  without `SIDEQUEST_TEST_DATABASE_URL`; RED verification must export it
  (postgresql://$USER@localhost:5432/sidequest_test) or 41 of 44 tests skip.

### Dev (implementation)
- **Improvement (non-blocking):** TEA's `adjust_system_strain` / `stabilize_mortal_injury`
  cwn→`("cwn","awn")` extension is now MECHANICALLY ENABLED by the family-ruleset
  seam this story landed (`@tool(... ruleset=("swn","wwn","cwn","awn"))`), but NOT
  applied — no 102-5 test exercises those two tools, so extending them is out of
  this story's tested scope (minimalist discipline). The fix is a one-line
  `ruleset=("cwn","awn")` on each. Defer to 102-7 (AWN live proof) or a follow-up.
  Affects `sidequest/agents/tools/adjust_system_strain.py` + `stabilize_mortal_injury.py`.
  *Found by Dev during implementation.*
- **Conflict (non-blocking):** the AC4 wiring test
  (`test_102_5_wn_tool_narrator_wiring.py`) shipped with an unsatisfiable
  assertion — `'"hit": true' in json.dumps(whole_call)` can never match a
  JSON-string tool_result content (it serializes escaped), and the alternative
  it implied (a bare-dict tool_result) violates the Anthropic API contract. Dev
  corrected the assertion to read the tool_result block content directly (see
  Design Deviations). No production change was needed. *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

- **TEA (red): tool names `wn_*`, not §8's `swn_*`.** SWN design §8 spells
  `swn_attack` etc. (written SWN-first, pre-family). The epic guardrail "one
  contract, four modules — avoid four parallel tool sets" supersedes the prefix:
  tests pin family names `wn_attack` / `wn_skill_check` / `wn_save` /
  `wn_adjudicate_dead_premise`, with the BOUND module slug parameterizing
  resolution and slug-honest module spans (`wwn.attack.resolved` on wwn,
  `awn.attack.resolved` on awn).
- **TEA (red): `wn_skill_check` carries `skill_level`.** §8's terse signature
  omits it, but skill levels are not stored on CreatureCore — the existing dice
  path takes `skill_level` on the wire payload (CheckThrowPayload). The tool
  mirrors that contract (narrator supplies the sheet-derived level, bounded
  −1..4 by the typed payload).
- **TEA (red): `wn_adjudicate_dead_premise` lands here, 102-4 pending.** Per the
  story guardrail ("whichever story lands first stubs nothing but defines the
  shared type in its own scope"): the tool records the redirect/fizzle ruling +
  reason on a span and mutates nothing mechanical (§8 row 4); 102-4's engine
  signal will consume the same call shape.

### Dev (rework — review round 1)
- **R-1 fix: `_resolve_weapon_damage` now resolves the NAMED weapon, not the first damage-bearing inventory item.** (Supersedes the original isinstance-seam deviation below, which the Reviewer FLAGGED.)
  - Spec source: §8 `swn_attack(attacker, target, weapon)` + Reviewer HIGH finding R-1
  - Spec text: the `weapon` argument names the weapon whose damage applies
  - Implementation: replaced the shared-seam delegation (which matched by no name) with explicit named-weapon resolution — match the inventory item by name/id, then its inline `damage` dict, then the world/genre catalog (`resolve_inventory` by item id, real `GenrePack` only), then the genre unarmed floor for `fists`/etc. A named weapon that isn't carried, or carries no resolvable damage, returns None → loud error. This also resolves security WN-1: a non-GenrePack no longer silently degrades — inline damage still resolves, but the catalog tier requires a real pack and otherwise fails loud.
  - Rationale: the original delegated to `resolve_damage_spec_from_beat_and_actor`, whose priority-2 returns the FIRST item with a damage dict regardless of the named weapon — a multi-weapon actor got the wrong weapon's dice (probe: named Maul 3d6+3, got Dart's 2). Pinned by `test_attack_resolves_the_NAMED_weapon_not_the_first_in_inventory` + `test_attack_naming_a_weapon_the_actor_does_not_carry_fails_loud`.
  - Severity: was HIGH (correctness), now fixed
  - Forward impact: the narrator-named weapon and the engine's dice now agree; the shared seam is no longer used by this tool (its by-name gap was the bug).
- **R-2 fix: pyright regression cleared.** `spec.roll(_RNG)` uses a module-level `random.Random()` instance instead of the `random` module (`:205` reportArgumentType); `_require_wn` reads a local `rules = getattr(...)` and gates `rules is None` so pyright narrows it before `rules.ruleset_config()` (`:74` reportOptionalMemberAccess). `uv run pyright sidequest/agents/tools/wn_tools.py` → 0 errors, restoring the repo's clean baseline.

### Dev (implementation)
- **Damage resolution front-guards the shared seam with `isinstance(pack, GenrePack)`.** *(SUPERSEDED by R-1 above — the seam delegation was removed.)*
  - Spec source: TEA RED notes ("damage via the `resolve_damage_spec_from_beat_and_actor` priority ladder")
  - Spec text: route damage through the existing priority ladder seam
  - Implementation: `_resolve_weapon_damage` passes `pack if isinstance(pack, GenrePack) else None` to the seam. The catalog tier (priority 3) calls `resolve_inventory(pack)`, which dereferences `pack.worlds`/`pack.inventory` — present only on a real `GenrePack`; the §12 test fixtures use a duck-typed `_FakePack`. With a real pack the full ladder runs (inline item → world/genre catalog → unarmed floor); with a non-GenrePack only the actor's own inline-inventory damage resolves, and a no-weapon hit returns None → the caller fails loud.
  - Rationale: production always binds a real `GenrePack`, so the catalog/floor tiers are never lost in production; the guard only narrows resolution for the duck-typed test pack, and it never silently swallows a missing-damage error (still loud per No Silent Fallbacks).
  - Severity: minor
  - Forward impact: none — production callers always pass a `GenrePack`.
- **To-hit modifier is the attribute mod only (`attack_bonus`/`combat_skill` = 0).**
  - Spec source: SWN design §8 attack call shape `swn_attack(attacker, target, weapon)`
  - Spec text: the §8 attack carries no beat / bonus fields
  - Implementation: the narrator tool has no `BeatDef`, so class-progression attack bonus isn't reachable; the to-hit modifier is the better-of(STR,DEX) attribute modifier the bound module computes (`resolve_opponent_attack` with `attack_bonus=combat_skill=0`).
  - Rationale: honest about the data the tool actually has — the beat/dice path still supplies class attack-bonus; the narrator tool resolves from stats.
  - Severity: minor
  - Forward impact: narrator-tool WN attacks omit class attack-bonus progression; a future story wanting it would add a level/class→attack_bonus derivation.
- **Corrected a defective AC4 assertion in `test_102_5_wn_tool_narrator_wiring.py`.**
  - Spec source: AC4 test (TEA RED), the "tool result returns to the model" assertion
  - Spec text: `assert '"hit": true' in json.dumps(fake.messages.calls[1], default=str)...`
  - Implementation: rewrote it to read the tool_result block's `content` string directly and assert `'"hit": true'` is in it.
  - Rationale: a tool_result's `content` is a JSON **string** (the valid Anthropic shape — content is str or content-blocks, never a bare object), so `json.dumps` of the whole call always escapes it (`\"hit\": true`) and the original substring can never match; the only way to satisfy it — embedding a raw dict as tool_result content — would violate the Anthropic API contract. The rewrite is stronger and correct, and production tool-result rendering is unchanged. (See Delivery Findings.)
  - Severity: minor (test-only)
  - Forward impact: none.
- **Updated two stale hardcoded tool-count assertions.**
  - Spec source: `test_73_15_ruleset_tool_filter.py` (excluded_count) + `test_narrator_uses_sdk_client.py` (catalog size)
  - Spec text: native `excluded_count == 6`; full catalog `== 36`
  - Implementation: bumped to `10` and `40` respectively.
  - Rationale: a direct, correct consequence of registering the four WN-family tools (gated from native → +4 excluded; +4 in the unfiltered catalog).
  - Severity: trivial (test-only)
  - Forward impact: none.

### Reviewer (audit)
- **Damage resolution front-guards the seam with `isinstance(pack, GenrePack)`** → ✗ FLAGGED by Reviewer: the guard itself is a defensible test accommodation, BUT it is downstream of a more serious bug — `_resolve_weapon_damage` never receives `args.weapon` at all, so the named weapon is ignored entirely (see HIGH finding R-1). The pack-type boundary should be reworked together with the weapon-selection fix: resolve the *named* weapon's damage explicitly, and treat a non-GenrePack-with-non-None as the loud type error No-Silent-Fallbacks wants (security WN-1), not a silent degrade to None. Re-audit after R-1 fix.
- **To-hit modifier is the attribute mod only (`attack_bonus`/`combat_skill` = 0)** → ✓ ACCEPTED by Reviewer: honest about the data the narrator tool has (no beat → no class progression); the beat/dice path still supplies attack-bonus. Non-blocking; the payload's `attack_total == d20 + modifier` is internally consistent and the span records it.
- **Corrected a defective AC4 assertion in `test_102_5_wn_tool_narrator_wiring.py`** → ✓ ACCEPTED by Reviewer: verified the original (`'"hit": true' in json.dumps(whole_call)`) is unsatisfiable for a valid string-content tool_result (serializes escaped), and the alternative it implied (bare-dict content) violates the Anthropic API contract. The rewrite reads the tool_result block content directly — stronger and correct. Production tool-result rendering is unchanged.
- **Updated two stale hardcoded tool-count assertions (6→10, 36→40)** → ✓ ACCEPTED by Reviewer: factual consequence of registering 4 new gated tools; verified both counts against `default_registry` (excluded 10 on native, catalog 40).

## TEA Assessment

**RED state verified:** 44 story tests — 41 failing, 3 passing as deliberate
regression pins (native-pack exclusion negative-space; 73-15 single-slug filter
behavior; AC5 magic_working mismatch watcher pin). Failures are contract-shaped
(KeyError on unregistered tools / registration assertions), not fixture errors.
Neighboring suites unaffected: 527 passed (test_73_15, dispatch watcher, tools/).
Lint + format clean. Commit `0365dde3` on `feat/102-5-wn-narrator-tool-contract`.

**Test files (sidequest-server):**
- `tests/agents/tools/test_102_5_wn_tool_contract_registration.py` — AC1:
  spec-derived list registered; advertised to all four WN slugs, hidden from
  native (forces the Registry family-ruleset declaration, pinned data-driven on
  a fresh registry with a novel tool name); §8 typed payload schemas (required
  fields, ruling enum redirect|fizzle); ADR-111 substantive descriptions.
- `tests/agents/tools/test_102_5_wn_tool_handlers.py` — AC2+AC3: tool-level
  isolation per §12 (handlers invoked directly with typed payloads). Attack:
  forced hit (AC −100) applies 1d6 inventory-weapon damage to the persisted
  HpPool, forced miss (AC 100) mutates nothing, hit-with-no-resolvable-damage is
  a LOUD error (the 86-1 0-damage lesson), unknown actor/target NOT_FOUND,
  native-pack self-guard. Skill check: 2d6 vs ladder key (hard=12), unknown key
  loud, skill_level 9 schema-rejected. Save: derived target (15−(level−1)),
  "luck" is wwn-vocabulary not swn (module-owned vocabulary, one contract),
  unknown category loud. Dead premise: zero mechanical mutation, ruling enum,
  span carries ruling+reason. Slug honesty: module spans parametrized wwn+awn.
  No-active-session fatal across all four tools.
- `tests/agents/test_102_5_wn_tool_narrator_wiring.py` — AC4: real
  `complete_with_tools` loop (82-9 fake-SDK-transport pattern) + real
  `default_registry.dispatch` + real pg store; asserts the full chain: tool
  result returns to the model, `tool.{cat}.wn_attack` + `wwn.attack.resolved`
  spans, persisted HpPool delta, and no `tool.unknown.*` path.
- `tests/agents/test_102_5_improv_detection_regression.py` — AC5: with the WN
  tools registered via the production import, a dispatched-but-not-engaged
  magic_working still emits `dispatch_engagement.magic_working.mismatch`
  (the contract adds verbs, must not relax the watcher) + a registration
  precondition tying the pin to this story.

**Rule Coverage (lang-review python.md):** #2 mutable defaults — fixtures use
default_factory/None patterns; #3 typed boundaries — typed payload schema tests
+ pydantic args models pinned; #6 test quality — no vacuous assertions (two
is_error-only asserts strengthened to name the offending key; every test asserts
specific values), no skips without reason, parametrized cases hit distinct
paths; #1/#11 fail-loud input validation — unknown actor/target/save/difficulty/
ruling all pinned loud; #9 async — bare async defs per tools-suite convention,
no blocking calls. Checks #5/#7/#8/#10/#12 not applicable to test-only diff.

**Notes for Dev:**
- The Registry seam extension (`ruleset` accepting a slug tuple) is the one
  infrastructure change the tests force; everything else routes to EXISTING
  module surfaces (`attack_params`/`resolve_opponent_attack` math shape,
  `check_params`, `save_params`, damage via the
  `resolve_damage_spec_from_beat_and_actor` priority ladder).
- Span names pinned: `{slug}.attack.resolved`, `{slug}.skill_check.resolved`,
  `{slug}.save.resolved`, `{slug}.dead_premise.adjudicated` (+ registry
  `tool.{category}.{name}` by construction — category not pinned).
- ADR-110/112 token-budget impact of the four new tool descriptions: measure in
  GREEN, don't guess (story assumption #3).
- Run with `SIDEQUEST_TEST_DATABASE_URL` exported or the suite silently skips.
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/tool_registry.py` — `ruleset` widened to `str | tuple[str, ...] | None`; new `_ruleset_advertises` helper drives `tool_definitions(ruleset=...)` family membership (keeps 73-15 single-slug exact-match).
- `sidequest/agents/tools/wn_tools.py` (new) — the four WN-family tools (`wn_attack` WRITE; `wn_skill_check`/`wn_save`/`wn_adjudicate_dead_premise` READ), thin wrappers over the bound `RulesetModule` surface + shared `_require_wn`/`_resolve_actor`/`_resolve_weapon_damage` helpers.
- `sidequest/telemetry/spans/wn.py` (new) — slug-parametrized resolution spans + 16 `SPAN_ROUTES` (4 slugs × 4 events) as `state_transition` for the GM panel.
- `sidequest/agents/tools/__init__.py`, `sidequest/telemetry/spans/__init__.py` — barrel registration.
- `tests/agents/test_102_5_wn_tool_narrator_wiring.py` — corrected the defective AC4 tool_result assertion (see Deviations/Findings).
- `tests/agents/test_73_15_ruleset_tool_filter.py`, `tests/agents/test_narrator_uses_sdk_client.py` — stale tool-count assertions bumped (6→10, 36→40).

**Tests:** 44/44 story tests passing (GREEN). Neighboring suites clean: agents+telemetry 2306 passed, game+dispatch 3108 passed, server 2900 passed. Lint + format clean.

**Story assumption #3 (ADR-110/112 token budget):** measured, not guessed — the four tool descriptions + JSON schemas add ≈ 4,469 chars ≈ **~1,117 tokens** to the advertised toolset for a WN-bound narrator (descriptions 354–405 ch each; schemas 488–954 ch each). These ride the primacy-cached tool block (ADR-111), so the cost is a one-time cache write per session, not per turn. Hidden from native packs (zero cost there).

**Branch:** `feat/102-5-wn-narrator-tool-contract` (commit `2c835233`, pushed)

**Handoff:** To next phase (verify).
## Subagent Results

Reviewer subagent toggles: only `preflight` and `security` enabled; the other
seven are disabled via `workflow.reviewer_subagents` (pre-filled Skipped). I
performed the disabled specialists' domains myself (edge/silent/test/type/simplify)
during the diff read.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 pyright errors (44/44 tests green, lint/fmt clean) | confirmed 2, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (boundary analysis done by Reviewer) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (No-Silent-Fallbacks audit done by Reviewer + security) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (test-quality reviewed by Reviewer) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (type review folded into preflight pyright) |
| 7 | reviewer-security | Yes | findings | 5 (WN-1 silent-degrade, WN-2 unconstrained save/attr, WN-3 roll(random)+neg-bonus, WN-4 READ perception, registry note) | confirmed 1 (corroborates HIGH weapon-select), 2 downgraded, 2 noted |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned with findings; 7 disabled pre-filled Skipped)
**Total findings:** 1 HIGH (weapon-name ignored — my analysis, corroborated by security probe-2), 1 MEDIUM (pyright regression, preflight), plus 3 LOW/by-design (security WN-2/WN-3/WN-4). 1 confirmed-blocking, others non-blocking/noted.

## Reviewer Assessment

**Verdict:** REJECTED

The contract, registry seam, family filtering, slug-honest spans, loud guards, and the full narrator→tool→module→OTEL wiring are well-built and 44/44 tests are green. But the diff ships a HIGH correctness bug that the single-weapon test fixtures never exercise: the `weapon` argument the narrator passes does not select the damage source.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **`weapon` arg ignored for damage selection.** `wn_attack` never threads `args.weapon` into `_resolve_weapon_damage`; the shared seam returns the *first* inventory item carrying a `damage` dict. Probe: actor with Dart(1d2) first + Maul(3d6+3) second, narrator names "Maul" → engine returns `damage: 2` (the Dart). For any multi-weapon actor the narrator's prose and the engine's dice diverge — the exact narrator-vs-engine lie this system exists to prevent. | `sidequest/agents/tools/wn_tools.py` `_resolve_weapon_damage` (~:97-127) + `wn_attack` call site (~:200) | Thread `args.weapon` in; resolve the *named* weapon's damage (match inventory item by name/id, then its inline `damage` or catalog id), fail loud if the named weapon resolves no damage. Needs a multi-weapon regression test. |
| [MEDIUM] | **Pyright regression against a clean baseline.** Repo is pyright-0-errors (verified apply_damage/commit_effort/downed_seam); `wn_tools.py` adds 2: `spec.roll(random)` passes the module where `random.Random` is expected (:205, `reportArgumentType`); `pack.rules.ruleset_config()` after a getattr-chain guard (:74, `reportOptionalMemberAccess`). | `wn_tools.py:205`, `:74` | `:205` → pass a `random.Random` instance (or use `random.randint`-based roll). `:74` → narrow `pack.rules` with a real attribute access/assert so pyright sees non-None. |

**Non-blocking observations (address opportunistically during rework, not gating):**
- `[SEC]` **WN-1** (security, Medium→folded into R-1): the `isinstance(pack, GenrePack) else None` silent type-downgrade in `_resolve_weapon_damage` — fix the boundary honestly when reworking weapon selection (raise on non-None non-GenrePack rather than silently dropping the catalog/floor tiers).
- `[SEC]` **WN-2** (security, downgraded to Low): `WnSaveArgs.save` / `WnSkillCheckArgs.attribute` are unconstrained `str`. Verified NOT a silent fallback — `save_params` raises `ValueError` and `stat_modifier`→`_stat` raises `KeyError` on unknown keys (swn.py:60, "no neutral-10"), both surfaced as loud error ToolResults. A handler-level pre-check (mirroring the `difficulty not in cfg.difficulties` guard) would yield cleaner named errors; nicety, not blocking.
- `[SEC]` **WN-4** (security, Low / likely by-design): the three READ tools have no `_RULES` perception entry, so a check/save for a *non-perspective* PC returns the exact modifier to the narrator context (vs `query_character`'s HP-band coarsening). The narrator is the GM stand-in adjudicating everyone's actions, so unfiltered mechanical truth to the *narrator* (not the client) is defensible — but document the intent or add a coarsening rule. Non-blocking.
- `[SIMPLE]` (Reviewer): leaked module-global loop vars (`_slug/_event/_field`) remain after the `SPAN_ROUTES` registration loop in `wn.py`; harmless (underscore-prefixed, not `*`-exported), no change required.
- `[TYPE]` (Reviewer, = pyright MEDIUM above): the `random` module vs `random.Random` mismatch is the one real type-design nit.
- `[DOC]` (Reviewer): docstrings accurate; `_resolve_weapon_damage`'s docstring claims it "resolves the strike DamageSpec" but omits that it ignores the named weapon — fix the docstring as part of R-1.

**Verified good (evidence-cited):**
- `[VERIFIED]` `[EDGE]` Loud guards across all four tools — unknown actor/target → `NOT_FOUND` (wn_tools.py:166-171), native pack → `ValueError` via `_require_wn` (:68-72) caught by dispatch into a clean error ToolResult (tool_registry.py:290-302, confirmed by `test_attack_on_native_pack_fails_loud_through_dispatch`), no-active-session → `ERROR_FATAL` (:159-161), hit-with-no-damage → loud recoverable error before any HP write (:200-208, `test_attack_hit_with_no_resolvable_damage_fails_loud_not_zero`). No silent 0-damage hit.
- `[VERIFIED]` `[SILENT]` `wn_adjudicate_dead_premise` mutates nothing — no `repository.save` in the handler (:430-470); HP-untouched asserted by `test_dead_premise_adjudication_mutates_nothing`.
- `[VERIFIED]` `[TEST]` Wiring test present and real — `test_narrator_turn_drives_wn_attack_through_production_dispatch` drives the real `complete_with_tools` loop + real `default_registry.dispatch` + real pg store, asserting the `tool.write.wn_attack` + `wwn.attack.resolved` span chain, the persisted HpPool delta, and the absence of `tool.unknown.*`. Satisfies CLAUDE.md's wiring-test mandate.
- `[VERIFIED]` `[RULE]` Slug-honest spans — `_require_wn` returns `module.slug`, so an awn pack emits `awn.attack.resolved` (`test_attack_emits_module_span_with_bound_slug[awn]`); 16 `SPAN_ROUTES` registered, routing-completeness green.
- `[VERIFIED]` `[TYPE]` `_ruleset_advertises` (tool_registry.py:175-188) — str exact-match (73-15) + tuple membership (102-5) + None pass-through; `test_family_ruleset_declaration_is_data_driven` pins it on a fresh registry with a novel name; `test_single_slug_declaration_still_works` confirms no 73-15 regression.

**Data flow traced:** narrator `wn_attack(attacker, target, weapon)` → `default_registry.dispatch` (pydantic-validates args, write-lock) → handler resolves actor stats + target AC → `module.resolve_opponent_attack` (d20+mod vs AC) → on hit `_resolve_weapon_damage` → **HERE the trace breaks: `args.weapon` is dropped; the seam returns the first damage-bearing inventory item** → `apply_hp_delta` + `repository.save` → `wn_attack_resolved_span`. The break is R-1.

**Devil's Advocate:** A WN party is, by genre convention, armed to the teeth — a Soldier carries a rifle *and* a combat knife *and* a sidearm; a Warrior a greatsword *and* a dagger. The very first real multiplayer turn where someone says "I draw my backup knife and finish him" will roll the rifle's 2d8 instead of the knife's 1d4 — or, worse for the narrator's credibility, the reverse: "I bring the greatsword down" rolls the dagger's 1d4 and the GM panel shows weapon=greatsword / damage=3. Sebastien and Jade — the mechanics-first players this epic exists to serve — are exactly the people who will notice the number doesn't match the weapon, and they carried a 140-turn game *on the crunch being right*. The single-weapon fixtures gave a false green; the bug is invisible until a second weapon enters an inventory, which is turn one of real play. This is not a theoretical edge — it is the common case for the target audience, and it lands squarely against the story's own thesis ("the narrator drives WN resolution through typed tools rather than improv"). Resolving the wrong weapon *is* a form of improv the engine can't detect. Reject and fix before this reaches the table.

**Handoff:** Back to Dev (via TEA for the regression test) for fixes — the weapon-selection bug is a testable logic gap.

### Reviewer (code review)
- **Gap (blocking):** `wn_attack` ignores the `weapon` argument when resolving damage — multi-weapon actors get the first inventory item with a `damage` dict, not the named weapon. Affects `sidequest/agents/tools/wn_tools.py` (`_resolve_weapon_damage` + `wn_attack` call site — thread `args.weapon` in and resolve the named weapon, with a multi-weapon regression test). *Found by Reviewer during code review.*
- **Gap (non-blocking):** pyright regression against the repo's 0-error baseline — `spec.roll(random)` (:205, arg-type) and `pack.rules` None-narrowing (:74). Affects `sidequest/agents/tools/wn_tools.py` (pass a `random.Random` instance; narrow `pack.rules`). *Found by Reviewer during code review.*
- **Improvement (non-blocking):** `WnSaveArgs.save` / `WnSkillCheckArgs.attribute` are unconstrained `str`; both fail loud in the module (ValueError / KeyError) so they're not silent fallbacks, but a handler-level membership check (like `difficulty`) would give cleaner named errors. Affects `sidequest/agents/tools/wn_tools.py`. *Found by Reviewer during code review.*
- **Question (non-blocking):** should the READ WN tools (`wn_skill_check`/`wn_save`) coarsen a non-perspective PC's modifier before returning it to the narrator context (cf. `query_character`), or is unfiltered mechanical truth to the GM-narrator intended? Document the decision. Affects `sidequest/agents/narrator_perception_filter.py` (`_RULES`). *Found by Reviewer during code review.*
## Dev Assessment (rework — review round 1)

**Rework Complete:** Yes — addressed both blocking-table findings from the REJECTED review.

**What changed:**
- `sidequest/agents/tools/wn_tools.py` — `_resolve_weapon_damage` rewritten to resolve the NAMED weapon (R-1, the HIGH bug); `_require_wn` restructured + `spec.roll(_RNG)` (R-2, pyright → 0 errors); removed now-unused `BeatDef`/`BeatKind` imports; added `_RNG`, `_UNARMED_TERMS`, `_damage_from_item` helpers.
- `tests/agents/tools/test_102_5_wn_tool_handlers.py` — +2 regression tests: `test_attack_resolves_the_NAMED_weapon_not_the_first_in_inventory` (the multi-weapon probe, now pinned) and `test_attack_naming_a_weapon_the_actor_does_not_carry_fails_loud`.

**Verification (evidence):**
- New regression tests RED before fix (2 failed), GREEN after (`46 passed` across the four 102-5 files, up from 44).
- `uv run pyright sidequest/agents/tools/wn_tools.py` → `0 errors, 0 warnings, 0 informations` (clean baseline restored).
- Regression sweep: `545 passed` (tools/ + 73-15 + narrator-sdk + routing-completeness). Lint + format clean.

**Non-blocking review items:** WN-2 (handler pre-validation) left as-is — verified both `save` and `attribute` already fail loud in the module (ValueError / KeyError), so it's a nicety, not a fix; WN-4 (READ-tool perception) is a documented open question for the perception-filter owner, not changed here.

**Branch:** `feat/102-5-wn-narrator-tool-contract` (commit `dc1825aa`, pushed)

**Handoff:** Back to Reviewer for re-review.
## Subagent Results (round 2 — rework re-review)

Same toggles (only `preflight` + `security` enabled). Both re-run on commit `dc1825aa`.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (46 pass, pyright 0, lint clean, imports purged) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (covered by security probe-1) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (2 new regression tests verified by preflight) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (pyright 0 errors confirms) |
| 7 | reviewer-security | Yes | findings | 2 LOW (R3 swallowed parse-log, R4 whitespace weapon_name) + WN-1 confirmed RESOLVED | confirmed 2 (both LOW/non-blocking), WN-1 closed |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned; 7 disabled pre-filled Skipped)
**Total findings:** 2 LOW (R3, R4) — both non-blocking, captured as delivery findings. Round-1 blockers (HIGH weapon-select, MEDIUM pyright) both fixed and independently re-verified. Round-1 security WN-1 confirmed resolved.

## Design Deviations — Reviewer (audit, round 2)

- **R-1: `_resolve_weapon_damage` resolves the NAMED weapon** → ✓ ACCEPTED by Reviewer: independently re-verified — naming "Maul" (3d6+3) over a first-slot Dart (1d2) now rolls 7-17 (was 2); "Dart" rolls 1-2; a not-carried weapon and an unarmed strike with no floor both fail loud. The named weapon and the engine's dice agree. Pinned by two regression tests (RED→GREEN). Supersedes the round-1 FLAGGED isinstance-seam deviation, which is now moot (the seam delegation was removed).
- **R-2: pyright regression cleared** → ✓ ACCEPTED by Reviewer: `uv run pyright sidequest/agents/tools/wn_tools.py` → `0 errors, 0 warnings, 0 informations`; the repo's clean baseline is restored. `spec.roll(_RNG)` (instance) and the `_require_wn` `rules`-local narrowing are both sound.
- **Security WN-1 (round-1 silent degrade)** → ✓ RESOLVED: the catalog tier is gated on `isinstance(pack, GenrePack)`; a non-GenrePack falls through to `None` → loud caller error. No silent fabrication.

## Reviewer Assessment (round 2)

**Verdict:** APPROVED

The round-1 HIGH (weapon-name ignored) and MEDIUM (pyright regression) are both fixed and independently re-verified, and security WN-1 is closed. The two remaining findings are LOW (non-blocking) and tracked as delivery findings.

**Data flow re-traced:** narrator `wn_attack(attacker, target, weapon)` → dispatch (pydantic-validate, write-lock) → resolve actor stats + target AC → `resolve_opponent_attack` (d20+mod vs AC) → on hit `_resolve_weapon_damage(weapon_name=args.weapon)` → **the trace now closes: the NAMED weapon is matched in inventory (name/id) → inline damage → catalog by id (real pack) → unarmed floor → else loud** → `apply_hp_delta` + `repository.save` → `wn_attack_resolved_span`. The round-1 break is gone.

**Findings (both LOW, non-blocking):**
- `[SEC]` `[SILENT]` **R3** (wn_tools.py:112-123): `_damage_from_item` swallows a `DamageSpec.model_validate` parse error with `except Exception: return None` and no log. Net behavior stays fail-loud at the caller (the hit is refused, never silently zeroed), so it's a diagnostic loss, not a correctness or security defect — but the old shared seam logged a `warning` naming the bad item, and that observability is worth restoring (a `logger.warning("unparseable damage on item %r: %s", item.get("id"), exc)` in both branches). Lang-review #1 / No-Silent-Fallbacks (diagnostic tier).
- `[SEC]` **R4** (wn_tools.py:151): a whitespace-only `weapon_name` (`" "` passes `min_length=1`) strips to `""` and would match a nameless+id-less inventory item. Narrow (requires an LLM whitespace emission AND a nameless damage-bearing item) and deterministic, not exploitable — the realistic outcome is a loud caller error. One-line guard `if not wanted: return None` after the strip closes it. Lang-review #11 (untrusted boundary hardening).

**Verified good (re-checked this round):**
- `[VERIFIED]` `[EDGE]` Named-weapon resolution exhaustive across cases — matched-inline, matched-catalog (real pack only), unarmed floor, not-carried→loud, case-insensitive — confirmed by probe (Maul→7-17, Dart→1-2, "Plasma Lance"→loud, "fists"→loud) and the two new regression tests.
- `[VERIFIED]` `[TYPE]` pyright 0 errors on `wn_tools.py` (clean baseline restored); `_require_wn` narrows `rules` correctly; `spec.roll(_RNG)` passes a real `random.Random`.
- `[VERIFIED]` `[SIMPLE]` Unused `BeatDef`/`BeatKind` imports removed (grep confirms absent); the new helpers (`_damage_from_item`, `_UNARMED_TERMS`, `_RNG`) are minimal and single-purpose.
- `[VERIFIED]` `[TEST]` 46/46 across the four 102-5 files (+2 regression), 17/17 siblings, routing-completeness green, lint/format clean.
- `[VERIFIED]` `[SEC]` WN-1 silent-degrade resolved; `[DOC]` docstrings updated to describe named-weapon resolution; `[RULE]` slug-honest spans and `_ruleset_advertises` unchanged and still green.

**Devil's Advocate (round 2):** Could the named-weapon fix have *narrowed* legitimate resolution — e.g. break the original single-weapon happy path or the unarmed/catalog tiers? Re-checked: the original `test_attack_forced_hit_applies_weapon_damage_to_hp_pool` (single Shard Knife, named "Shard Knife") still passes — inline match. The `test_attack_hit_with_no_resolvable_damage_fails_loud_not_zero` (unarmed "fists", no floor) still fails loud — unarmed-term path returns None. The AC4 wiring test (named "Shard Knife") still drives the full chain and persists the delta. Catalog resolution is exercised only in production (fake packs carry no catalog), but the logic mirrors the seam's priority-3 and is guarded behind `isinstance(pack, GenrePack)`, so a real pack resolves catalog-only weapons and a fake pack fails loud — no regression to the tested paths. The only residue is the two LOW nits, neither of which can land an incorrect hit (both terminate in a loud refusal). The fix is tight; nothing legitimate was lost.

**Handoff:** To SM for finish-story.

### Reviewer (code review — round 2)
- **Improvement (non-blocking):** restore the parse-error diagnostic in `_damage_from_item` — log a `warning` naming the item id + exception before returning None, mirroring the old shared seam (the caller already fails loud, this is observability only). Affects `sidequest/agents/tools/wn_tools.py` (`_damage_from_item`, both except branches). *Found by Reviewer during code review (round 2).*
- **Improvement (non-blocking):** guard a whitespace-only `weapon_name` in `_resolve_weapon_damage` — `if not wanted: return None` after `strip()` so `" "` can't match a nameless inventory item. Affects `sidequest/agents/tools/wn_tools.py` (`_resolve_weapon_damage`). *Found by Reviewer during code review (round 2).*