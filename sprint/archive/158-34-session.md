---
story_id: "158-34"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-34: Dogfight seating — ship/chassis opponent, ship-scale; never a co-located ground creature (ADR-153 Plan 1)

## Story Details
- **ID:** 158-34
- **Jira Key:** (none — Jira integration not configured)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-27T17:05:59Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T16:29:23.527642+00:00 | 2026-06-27T16:31:33Z | 2m 9s |
| red | 2026-06-27T16:31:33Z | 2026-06-27T16:46:32Z | 14m 59s |
| green | 2026-06-27T16:46:32Z | 2026-06-27T16:56:05Z | 9m 33s |
| review | 2026-06-27T16:56:05Z | 2026-06-27T17:05:59Z | 9m 54s |
| finish | 2026-06-27T17:05:59Z | - | - |

## Sm Assessment

**Story:** 158-34 — Dogfight seating firewall (ADR-153 Plan 1). 2 pts, p3, `tdd` workflow, **server repo only** (sidequest-server).

**Repos:** server (sidequest-server) · **Branch:** `feat/158-34-dogfight-seating-ship-opponent`

**What the story asks (per plan, not for me to design):** When a dogfight seats its opponent, treat `resolution_mode: sealed_letter_lookup` as **ship-scale** so the personal-NPC location fallback can never seat a co-located *ground* creature (e.g. the Monster-Manual "Gengineered Killer" from the 2026-06-25 coyote_star playtest) as the enemy ship. When the router names no opponent, seat a **default ship opponent** from the def frame (`opponent_default_stats`) so the duel always has a ship Other (ADR-116).

**Authoritative references for TEA/Dev:**
- Plan: `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-1-firewall-seating.md`
- ADR-153 (Ace of Aces dogfight, Plan 1), ADR-116 (a confrontation requires an Other), ADR-125 (chassis/rig first-class; the Kestrel lives in `chassis_registry`).
- Per SOUL doctrine: this is a *seating/firewall* fix, not native-dial tuning. Resolution stays bound (ADR-143). Don't balance — bind.

**Setup decisions:**
- **Jira:** explicitly **skipped** — `pf jira` reports integration not configured (no `jira.project`/`jira.url`). No claim/transition performed.
- **Merge gate:** cleared. Resolved blocking non-draft PR #426 (companion-chargen docs spec) by squash-merging it (user-authorized); 0 open PRs remain.
- **Session/context/branch:** all created and verified.

**Routing:** `tdd` is a **phased** workflow → next phase **red**, owned by **TEA (Igor)**. Igor writes the failing test(s) that pin the wrong-scale seating bug and the default-ship-opponent fallback, per the plan above. No implementation planning done by SM.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): 158-34's *literal* functional scope (sealed-letter is ship-scale via the **location-fallback** door; default-from-frame opponent) was already delivered + tested + OTEL-wired under sibling **158-31's PR #1084** (commit `479f7e19`). Verified GREEN: `test_dogfight_seating_scale.py`, `test_dogfight_default_opponent.py`, the `test_dogfight_instantiation_production_path.py` suite, and the `otel_capture` assertion in `test_dogfight_dispatch_wiring.py`. Per the user (2026-06-27), 158-34 stays open to harden the one door #1084 left open (below) rather than close as duplicate.
- **Gap** (blocking): the §6 ship-scale firewall covers only the **location-fallback** door, not the **router** door. `encounter_lifecycle.py` guards both seating branches with `not npcs_present`, so a router-named (`npcs_present`) personal-scale `is_creature` opponent skips both and is seated as the enemy ship — 158-34's exact symptom via a second door. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (the sealed-letter seating path needs an `is_creature` ship-scale guard on router-named opponents; reject + source `frame_default`). *Found by TEA during test design.*
- **Improvement** (non-blocking): in the current (buggy) path the router-named ground creature is not merely seated — it is handed ship frame-HP (`per_actor_state={'frame_hp': 8, 'frame_hp_max': 8}` via `_seed_combat_hp_depletion_to_npcs`). A silent personal→ship promotion; the fix should make the rejection observable (`participant.joined` `source="frame_default"`, asserted by the new test). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `materialized_threat` is a THIRD seating door (a free-string narrator/router threat reconciled via `_resolve_opponent_from_roster`, `encounter_lifecycle.py:1708`) that this fix does NOT ship-scale-firewall — out of scope for 158-34 (the finding + Igor's test target the `npcs_present` router door). If a narrator materializes a ground-creature threat for a dogfight it could still seat personal-scale. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (a follow-up could extend the `is_creature` ship-scale guard to the `materialized_threat` branch). *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): the firewall `_log.warning` says "sourcing a ship Other from the def frame instead", but in the mixed router-named case (a ship AND a creature) the retained ship seats via `router_named`, not `frame_default` — the free-text overstates. The structured `seating_source` span stays accurate. Affects `sidequest/server/dispatch/encounter_lifecycle.py:1727` (reword to "...retaining the ship-scale mention(s) or sourcing from the def frame"). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the firewall predicate `resolution_mode == sealed_letter_lookup` is correct only because today exactly one confrontation is sealed-letter (the ship-scale dogfight). A future sealed-letter confrontation against a *sapient creature* Other (e.g. a talking-dragon parley) would be wrongly stripped. Affects `sidequest/server/dispatch/encounter_lifecycle.py:1721` (when a second sealed-letter confrontation is authored, gate on a ship-scale flag rather than on `sealed_letter_lookup` alone). *Found by Reviewer during code review.*
- **Improvement** (non-blocking, low): the `encounter_sealed_letter_arity_rejected_span` does not distinguish "empty because the firewall stripped creatures" from "empty because the router named nothing." Near-unreachable for the live dogfight (its def carries the validator-required `opponent_default_stats`). Affects `sidequest/telemetry/spans/encounter.py` (add a cause attribute if a frameless sealed-letter def ever ships). *Found by Reviewer during code review.*
- **Gap** (non-blocking): `materialized_threat` remains an un-firewalled third seating door (already logged by Dev); unreachable-with-`npcs_present` today (callers gate it on `not actor_list`), so no current bug. Affects `sidequest/server/dispatch/encounter_lifecycle.py:1708`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Hardened a second seating door beyond the literal symptom**
  - Spec source: context-story-158-34.md, AC + session scope ("never seats a ground creature as the enemy ship")
  - Spec text: "treat resolution_mode: sealed_letter_lookup as ship-scale so the personal-NPC **location fallback** never seats a ground creature as the enemy ship"
  - Implementation: RED test drives the **router** door (`npcs_present=[NpcMention(is_creature=True)]`), not the location fallback — because #1084 already firewalled the fallback door; the router door is the remaining open path to the same symptom.
  - Rationale: 158-34's title/invariant is "ship-scale; never a co-located ground creature" — door-agnostic. Closing one door and leaving the sibling open is exactly the firewall-with-one-gate trap. The router runs first (ADR-113), so the router door is the *more* likely real path.
  - Severity: minor
  - Forward impact: Dev must add an `is_creature` ship-scale guard on router-named sealed-letter opponents; the assertion encodes **reject-and-replace-with-frame-default** (ADR-116 "the duel always has a ship Other"), NOT fail-loud. If the Architect prefers fail-loud, the assertion changes — flag on receiving review.

### Dev (implementation)
- **No deviations from spec.** Implemented exactly the reject-and-replace-with-frame-default contract Igor's test encodes: filter `is_creature` mentions from `npcs_present` for `sealed_letter_lookup` before the seating cascade, letting an all-creature mention set fall through to the existing `frame_default` branch (ADR-116). No new seating branch, no dial/beat touched (ADR-143 doctrine intact — this is a seating firewall, not ruleset balancing). OTEL observability reuses the existing `participant.joined source="frame_default"` flip (the test asserts it) rather than a new span family; paired with a `_log.warning` so the drop is not silent (No Silent Fallbacks). The reject-vs-fail-loud design fork did NOT need an Architect call — reject-and-replace is what the story's ADR-116 "always a ship Other" mandates and what the sibling `test_dogfight_seating_scale.py` already establishes for the location door.

### Reviewer (audit)
- **TEA: "Hardened a second seating door beyond the literal symptom"** → ✓ ACCEPTED by Reviewer: sound. 158-34's title invariant ("ship-scale; never a co-located ground creature") is door-agnostic, and `grep` confirms `sealed_letter_lookup` binds only the ship-scale dogfight — extending the firewall to the router door is in-scope, not scope creep. The router runs first (ADR-113), so it is arguably the *primary* door, making this the more important half of the fix.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed. The implementation matches the test contract exactly (reject-and-replace via fall-through to `frame_default`); no dial/beat touched (ADR-143 intact); the reject-vs-fail-loud fork was correctly resolved toward reject-and-replace per ADR-116 + the sibling location-door test — no Architect call needed.
- **No UNDOCUMENTED deviations found.** The implementation does exactly what TEA's test and the Dev assessment describe; the LOW findings (warning over-specificity, getattr default, arity-span granularity) are observability-precision notes, not spec deviations.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 158-34's literal scope was over-delivered under 158-31's PR #1084, but a genuine in-scope gap remains (the router seating door is not ship-scale firewalled). Per user direction (2026-06-27), harden it rather than close 158-34 as duplicate.

**Test Files:**
- `tests/server/dispatch/test_dogfight_router_named_scale.py` — a router-named personal-scale (`is_creature=True`) opponent must NOT be seated as the dogfight ship; the seater rejects it and sources the default-from-frame ship (ADR-116), recording `participant.joined` `source="frame_default"`.

**Tests Written:** 1 test covering the 1 open AC facet (router-door ship-scale firewall + OTEL observability).
**Status:** RED — confirmed failing for the right reason: the opponent actor is seated as `EncounterActor(name='Gengineered Killer', role='blue', side='opponent', per_actor_state={'frame_hp': 8, 'frame_hp_max': 8})`; assertion `'Gengineered Killer' != 'Gengineered Killer'` fails. No import/fixture error.

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|------|---------|--------|
| #6 test quality (specific-value asserts, non-vacuous) | `test_router_named_ground_creature_is_not_seated_as_dogfight_opponent` — asserts `name != GROUND_CREATURE`, `core.hp.max == 8`, span `source == "frame_default"` | RED (failing) |
| #3 type annotations at boundaries | test fn + `span_capture` fixture both annotated (`-> None`, `-> Iterator[InMemorySpanExporter]`) | n/a (style) |
| OTEL Observability Principle (CLAUDE.md) | span assertion on `participant.joined` `source` — the substitution is GM-panel observable | RED (failing) |

**Rules checked:** test-quality (#6) is the load-bearing applicable rule for a single hardening test; #1/#2/#7/#8/#9/#11 (exceptions, mutable defaults, resources, deserialization, async, input-validation) are not exercised by a sync behavioral test. The fixture uses a context-managed span processor (`try/finally` shutdown — rule #7 clean).
**Self-check:** 0 vacuous assertions (every assert checks a specific value or span attribute).

**Wiring note (CLAUDE.md "Every Test Suite Needs a Wiring Test"):** the test drives the real production seater `instantiate_encounter_from_trigger` and asserts on the real `participant.joined` OTEL span — behavior, not source text. It IS the wiring test.

**Handoff:** To Dev (Ponder Stibbons) for GREEN — add an `is_creature` ship-scale guard on router-named sealed-letter opponents in `encounter_lifecycle.py` so a personal-scale mention is rejected and the seater sources the `frame_default` ship instead (emit `seating_source="frame_default"`). Keep ADR-143 doctrine: this is a *seating firewall*, not dial tuning. Do not weaken the test's assertions — if the frame-default-vs-fail-loud design fork needs an Architect call, raise it.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/server/dispatch/encounter_lifecycle.py` — in `instantiate_encounter_from_trigger`, added a ship-scale firewall *before* the seating cascade: for `resolution_mode == sealed_letter_lookup`, drop `is_creature` mentions from `npcs_present` (with a `_log.warning` naming the rejected creature). The emptied list falls through to the existing `frame_default` branch, which seats a ship Other and records `participant.joined source="frame_default"`. No new branch; no dial/beat touched (ADR-143 intact).
- `tests/server/dispatch/test_dogfight_router_named_scale.py` — Igor's RED test (committed `33029f03`), now GREEN; ruff-format normalization only.

**Approach (minimal):** filter the input, don't add a branch. The cascade's `elif`s are all gated on `not npcs_present`, so removing the personal-scale mentions routes an all-creature set into the frame_default ship seat. Observability reuses the existing seating-source span (the `router_named → frame_default` flip IS the GM-panel lie-detector); `_log.warning` keeps the drop non-silent.

**Tests:** GREEN.
- Target: `test_router_named_ground_creature_is_not_seated_as_dogfight_opponent` — PASS (was RED).
- Seating + dispatch-wiring sweep (5 files, 16 tests) — PASS, no regressions.
- Broad regression: `tests/server/dispatch` + `test_dogfight_dispatch_wiring.py` + `test_dogfight_shot_inputs.py` — **520 passed, 7 skipped, 0 failed** (serial `-n0`).
- `ruff check` + `ruff format` clean on both changed files.

**Branch:** `feat/158-34-dogfight-seating-ship-opponent` — pushed to origin (commits `33029f03` test, `ad3332c2` impl).

**Self-review (judgment checks):**
- [x] Wired: drives the production seater `instantiate_encounter_from_trigger` (the real router-dispatch primitive); behavior asserted via the live OTEL span.
- [x] Follows project patterns: `getattr(m, "is_creature", False)` matches the file's defensive `npcs_present` idiom (bare `list`); reuses the seating-source span; `_log` warning per lang-review #4.
- [x] AC met: a router-named ground creature is never seated as the ship; a ship Other is always seated (ADR-116); the seat is observable (`source="frame_default"`).
- [x] Error handling: the firewall is the error handling (No Silent Fallbacks — logged drop); the un-seatable / arity guards downstream are unchanged.

**One note for Granny (Reviewer):** `materialized_threat` is a third seating door this fix deliberately does NOT cover (out of scope — logged as a Dev Delivery Finding for a possible follow-up). The reject-vs-fail-loud fork was resolved toward reject-and-replace per ADR-116 + the sibling location-door test; flagged here for visibility.

**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (1 style note) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 med, 1 med, 1 low) | confirmed 3 (all downgraded to LOW), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (rules enumerated by Reviewer manually — see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed-blocking, 3 confirmed-LOW (non-blocking, with rationale), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A small, correct, well-tested seating-firewall fix. All mechanical gates green; security clean; the three silent-failure findings all resolve to LOW after verification against caller construction and the `NpcMention` type. No Critical/High. The disabled subagents' domains (edge, test-quality, type, simplify, rules) I covered manually below.

**Data flow traced:** player action → intent-router pass (ADR-113) emits `npcs_present=[NpcMention(is_creature=True)]` → `run_dogfight_dispatch`/`run_confrontation_dispatch` → `instantiate_encounter_from_trigger` → **the new firewall drops the `is_creature` mention** → `npcs_present=[]` → `frame_default` branch seats "Enemy Fighter" ship → `participant.joined source="frame_default"` → `_seed_combat_hp_depletion_to_npcs` mints backing HP=8. Safe: the personal-scale creature never reaches an actor seat; the duel still has a ship Other (ADR-116).

### Subagent findings — adjudication (all tagged)

- `[SILENT]` **F1 (med→LOW): `getattr(m, "is_creature", False)` default could mask a flagless creature.** Downgraded, not dismissed. `NpcMention.is_creature` is a declared field with default `False` (`orchestrator.py:413`) — the getattr default is **unreachable** for a real `NpcMention`, and the downstream seat loop already requires `.name/.side/.role`, so non-`NpcMention` items would fail there regardless. `reviewer-security` independently judged the keep-on-unknown direction the *safer* failure mode (err toward seating, not denial). The firewall is only as strong as the router's `is_creature` labeling — an inherent limit of the discriminator, not a regression. **Non-blocking.**
- `[SILENT]` **F2 (med→LOW): the `_log.warning` "sourcing from the def frame" can be imprecise.** Two sub-cases, both verified non-blocking: (a) the *both-set* path (`npcs_present` + `materialized_threat`) the subagent feared is **unreachable** — both callers (`dogfight.py:132`, `confrontation.py:128`) build `materialized_threat` only `if ... and not actor_list`, so it is `None` whenever `npcs_present` is non-empty; (b) the *reachable* refinement I found myself — when the router names BOTH a ship and a creature, the firewall keeps the ship, which seats via `router_named`, yet the warning still says "from the def frame." The **structured `seating_source` span is accurate in every case** (the real GM-panel lie-detector); only the free-text warning over-specifies. **Non-blocking; reworded-warning recommended as a follow-up.**
- `[SILENT]` **F3 (low): arity-rejected span can't tell firewall-emptied from naturally-empty.** Near-unreachable for the live dogfight (its def carries `opponent_default_stats`, which the `hp_depletion` model validator at `rules.py:607` *requires*), so an all-creature firewall pass still routes to `frame_default`, never the arity guard. A genuine observability nice-to-have for a hypothetical frameless sealed-letter def. **Non-blocking, deferred to a follow-up.**
- `[SEC]` **Security: clean.** No injection/eval surface (list-comp + getattr on typed objects); the warning logs game-entity name strings + an engine enum — no PII/secrets; `is_creature` is router-set, not player-set, so no player bypass / denial-of-encounter. No auth/tenant/perception concern.
- `[EDGE]` (subagent disabled — Reviewer covered): all-creature → `frame_default` ✓; mixed ship+creature → ship retained, arity=1 ✓; empty → unchanged frame_default ✓; non-sealed-letter → firewall skipped (predicate) ✓.
- `[TEST]` (subagent disabled — Reviewer covered): the test asserts specific values (`name != GROUND_CREATURE`, `core.hp.max == 8`, span `source == "frame_default"`) — non-vacuous, lang-review #6 clean. Drives the real production seater + asserts a live OTEL span (a true wiring test, not source-text grep). `span_capture` mirrors the established `otel_capture` pattern with `try/finally` shutdown.
- `[TYPE]` (subagent disabled — Reviewer covered): no new public boundary; locals only; preflight pyright reports zero new errors on the changed lines (1705–1735).
- `[SIMPLE]` (subagent disabled — Reviewer covered): preflight noted the list is scanned twice (`getattr` in the comprehension, then again to build `_rejected`). Lists are 0–2 mentions in practice — a single-pass partition would be marginally tidier but not worth the added code. Acceptable.
- `[DOC]` (subagent disabled — Reviewer covered): the 13-line comment block is accurate and links ADR-153 §6 / ADR-116 / 158-34 / #1084. One nuance: the comment+warning both say "into the frame_default branch," which is precise for the all-creature case but glosses the mixed ship+creature case (see F2). Minor.

### Rule Compliance (python lang-review, enumerated manually — rule_checker disabled)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | No silent exception swallowing / No Silent Fallbacks | ✓ compliant | no try/except added; the drop is `_log.warning`-logged AND flips `seating_source` to `frame_default` on the span — observable, not silent |
| 2 | Mutable default arguments | ✓ n/a | no new function signatures; `_ship_scale_present`/`_rejected` are fresh list comprehensions |
| 3 | Type annotations at boundaries | ✓ compliant | change is inside an existing function; test fn + fixture annotated (`-> None`, `-> Iterator[InMemorySpanExporter]`) |
| 4 | Logging coverage AND correctness | ✓ compliant | `_log.warning(... %s ... %r ...)` — lazy formatting (not f-string); warning level correct for a router-input anomaly; no PII |
| 6 | Test quality | ✓ compliant | specific-value asserts, zero vacuous; one assertion per invariant with distinct failure messages |
| 7 | Resource leaks | ✓ compliant | `span_capture` fixture uses `try/finally: processor.shutdown()` |
| 8 | Unsafe deserialization | ✓ n/a | no pickle/eval/yaml.load surface |
| 11 | Input validation at boundaries | ✓ compliant | filter applied at the correct seam (pre-seating-cascade) on router-produced mentions |

### Observations (5+)

1. `[VERIFIED]` Filter scope is uniquely correct — `grep` of all 11 packs + test fixtures shows `sealed_letter_lookup` is bound to **exactly one** confrontation (`space_opera/dogfight`, `rules.yaml:558`), which is ship-scale. The `resolution_mode == sealed_letter_lookup` predicate cannot wrongly drop a creature in a non-ship sealed-letter context — none exists. Evidence: `genre_packs/space_opera/rules.yaml:552-558` is the sole live definition; `classes.yaml` hits are comments.
2. `[VERIFIED]` ADR-143 / SOUL "Bind the Ruleset" intact — the diff touches only the `npcs_present` seating list; no dial, beat, or ruleset math (`encounter_lifecycle.py:1721-1734`). This is a pure seating firewall.
3. `[VERIFIED]` No caller-aliasing mutation — `npcs_present = _ship_scale_present` rebinds to a fresh list-comprehension result; the caller's `actor_list` is untouched (`dogfight.py:120` passes `list(npcs_present)`).
4. `[VERIFIED]` `materialized_threat` mutual-exclusion — both call sites gate `materialized_threat` on `not actor_list` (`dogfight.py:132`, `confrontation.py:128`), so the both-set misleading-warning path is unreachable today.
5. `[LOW][SILENT]` Warning text over-specifies "from the def frame" in the mixed ship+creature case (structured span still accurate) — recommend rewording on next touch.
6. `[LOW][SIMPLE]` Double scan of `npcs_present` (getattr in the comprehension + again for `_rejected`); negligible at 0–2 mentions.
7. `[VERIFIED]` Observability reuses the canonical seating-source span rather than minting a new family — the `router_named → frame_default` flip IS the lie-detector the OTEL principle asks for; the test asserts exactly that (`participant.joined` `source`).

### Devil's Advocate

Let me argue this code is broken. The firewall keys entirely on `is_creature`, a single boolean the intent router stamps onto an `NpcMention`. The whole defense is therefore only as good as one LLM-set flag. A malicious or confused router that labels a genuine ground creature `is_creature=False` sails the creature straight through — `getattr(m, "is_creature", False)` keeps it, no warning, and 158-34's original bug recurs unguarded. The firewall *advertises* protection it cannot actually guarantee. Worse, the `getattr` default points the wrong way for a firewall: when in doubt, it *keeps* the mention. A reviewer who trusts the comment ("never a ground creature") would be wrong in the mislabeled case. Second angle: the warning message is a lie in the mixed case — the operator reading "sourcing a ship Other from the def frame instead" while the GM panel shows a `router_named` ship seat will distrust the telemetry, and distrusted telemetry is worse than none (it's the OTEL lie-detector lying). Third: the scope predicate `resolution_mode == sealed_letter_lookup` is a *temporal* bet — it's correct only because today exactly one confrontation is sealed-letter. The day someone authors a sealed-letter *social* duel against a sapient *creature* (a talking dragon parley), this firewall silently strips the dragon and the duel can't seat its intended Other; nothing in the code or a test guards that future. Fourth: a stressed path where `npcs_present` holds two creatures and no ship empties the list; if some *other* future caller passed a frameless sealed-letter def, the arity guard raises and the turn degrades — and per F3 the operator can't tell the firewall caused it.

How much of that survives scrutiny? The mislabel case is an inherent limit of the `is_creature` discriminator, not introduced here — the same flag drives the already-merged location-door firewall (#1084); this change is strictly additive defense. The mixed-case warning is real but LOW — the *structured* span is accurate, only the prose over-specifies. The "future sealed-letter social duel" is a genuine latent coupling, but it is a *future* content shape with no current instance and no test demanding it; the right response is the documented Delivery Finding below, not a block. The frameless-degrade is near-unreachable (the model validator forces `opponent_default_stats` on `hp_depletion` defs). None rises to High. The Devil scores points on documentation precision, not on correctness or safety — so the verdict holds, with the findings recorded.

**Error handling:** the firewall IS the error handling for the router-door mis-seat; downstream the No-Opponent and sealed-letter arity guards are unchanged and still fail loud (`encounter_lifecycle.py:1841`, `~1893`).
**Pattern observed:** filter-the-input-then-fall-through-to-the-existing-default-branch (vs. adding a new seating branch) — minimal and idiomatic for this cascade (`encounter_lifecycle.py:1721`).
**Handoff:** To SM (Captain Carrot) for finish-story.