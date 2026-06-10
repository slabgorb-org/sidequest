---
story_id: "101-3"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 101-3: Triage + remove zero-importer server modules: gossip_engine (check ADR-053 partial status), learned_ops, corpus/going_forward, corpus/negatives

## Story Details
- **ID:** 101-3
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Branch:** feat/101-3-remove-zero-importer-modules
- **Branch Strategy:** gitflow (feat/101-3-remove-zero-importer-modules)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-10T12:57:43Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T12:42:43Z | 2026-06-10T12:44:34Z | 1m 51s |
| implement | 2026-06-10T12:44:34Z | 2026-06-10T12:52:17Z | 7m 43s |
| review | 2026-06-10T12:52:17Z | 2026-06-10T12:57:43Z | 5m 26s |
| finish | 2026-06-10T12:57:43Z | - | - |

## Sm Assessment

Setup-only assessment for a 2pt trivial chore (dead-code removal in sidequest-server). The story title is the full spec; there is no separate description or AC set.

**Scope handed to Dev (Julia):** Triage four candidate modules and remove the dead ones:
- `gossip_engine` — **check ADR-053 partial status first.** ADR-053 (Scenario System: clue graph, belief state, gossip propagation) is marked *partial* in the ADR index. Confirm gossip_engine truly has zero non-test importers AND that ADR-053's accepted-but-unimplemented status doesn't intend to wire it. If it's a planned-but-unwired component rather than abandoned dead code, flag it as a Delivery Finding and leave it rather than ripping out a load-bearing-by-design module.
- `learned_ops`
- `corpus/going_forward`
- `corpus/negatives`

**Method:** For each module, grep for non-test importers (production call sites — per the "Verify Wiring, Not Just Existence" principle, existence ≠ wiring, and the inverse: a module with no production consumer is dead). Zero non-test importers → remove the module and any now-orphaned test files. Any production importer → keep and report.

**Watch-outs:**
- The corpus modules sit under the ADR-091 culture-corpus/Markov naming subsystem — verify removal doesn't break corpus CLI entrypoints or the namegen path.
- Per "No Stubbing / dead code is worse than no code," lean toward removal when truly unimported — but gossip_engine's ADR-053 tie is the one genuine judgment call.
- After removal, run `just server-test` / `just server-lint` to confirm nothing downstream referenced these via dynamic import or registry.

**Repos:** server only. Branch `feat/101-3-remove-zero-importer-modules` already cut.

## Dev Assessment

**Implementation Complete:** Yes

**Triage outcome (4 candidates):**
- `sidequest/game/gossip_engine.py` → **KEPT** (ADR-053 accepted/partial; `political_engine.py` seeds beliefs for it to propagate)
- `sidequest/magic/learned_ops.py` → **KEPT** (active `learned_v1` plugin; `magic_init.py:537` seeds state for it; e2e-tested)
- `sidequest/corpus/going_forward.py` → **REMOVED** (behavior-free reservation shell, zero consumers)
- `sidequest/corpus/negatives.py` → **REMOVED** (orphan heuristic, only its own test imported it)

**Files Changed:**
- `sidequest/corpus/going_forward.py` — deleted (reservation-only payload-schema shell; no production consumer)
- `sidequest/corpus/negatives.py` — deleted (orphan `detect_retarget`; not wired into the corpus miner/pipeline)
- `tests/corpus/test_going_forward.py` — deleted (tested only the removed module)
- `tests/corpus/test_negatives.py` — deleted (tested only the removed module)
- `sidequest/protocol/enums.py` — updated stale comment that pointed at the deleted `going_forward.py`; enum members retained (live reservation, count-tested)

**Tests:** corpus/ + protocol/ suites GREEN — 319 passed, 0 failed, 41 skipped (`-n0`). No `ModuleNotFoundError` for removed modules; full-tree grep confirms zero dangling references. Ruff clean.

**Branch:** feat/101-3-remove-zero-importer-modules (push pending)

**Handoff:** To review (Thought Police) — the two KEEP decisions and the going_forward removal are logged as deviations/findings for adversarial scrutiny.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Conflict** (non-blocking): `learned_ops` is named as a removal candidate but is the planned data-layer for the *active, registered* `learned_v1` MagicPlugin. `magic_init.py:537` actively seeds `prepared_spells` state "for the learned_ops.prepare op," `innate_v1_cast.py:7` documents `learned_ops.cast` as the legitimate non-beat data-layer API, and `apply_spell_effect.py:34` forward-references it "once the SDK is the production narrator path." Full e2e coverage in `tests/magic/test_e2e_cnc_memorization.py`. Affects `sidequest/magic/learned_ops.py` (KEPT — needs a magic-wiring story to connect prepare/cast/rest to the live narration path, not deletion). *Found by Dev during implementation.*
- **Conflict** (non-blocking): `gossip_engine` is named as a removal candidate but ADR-053 is *accepted* (impl partial) and `political_engine.py:194` actively seeds witness `BeliefFact`s "so the existing GossipEngine can later propagate it." Affects `sidequest/game/gossip_engine.py` (KEPT — wire-up target, not dead code; live seeding code already points at it). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the `MessageType` members `DISPATCH_PACKAGE` / `NARRATOR_DIRECTIVE_USED` / `VERDICT_OVERRIDE` remain reserved in `sidequest/protocol/enums.py` (count-tested at 41 in `tests/protocol/test_enums.py`) but no longer have pre-reserved payload schemas after `going_forward.py` removal. Affects `sidequest/protocol/enums.py` (when an emitter is built, author the payload schema alongside it per No-Stubbing). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): three `MessageType` members (`DISPATCH_PACKAGE`, `NARRATOR_DIRECTIVE_USED`, `VERDICT_OVERRIDE`) are reserved but unregistered in `_KIND_TO_MESSAGE_CLS` and absent from `_REPLAY_SKIP_KINDS`; if ever emitted they hit the fail-loud `raise ValueError` at `session_handler.py:197`. This is pre-existing (not introduced by 101-3) and *correctly* fail-loud, but a future hardening story could add them to `_REPLAY_SKIP_KINDS` to make the intentional-incompleteness explicit. Affects `sidequest/server/session_handler.py` (optional skip-list entry). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the changelog comment at `tests/protocol/test_enums.py:214` ("Group D Task 7 reserved … for corpus going-forward capture") still reads accurately as history, but a one-line note that the payload schemas were removed in 101-3 would help a future maintainer avoid assuming a `going_forward.py` still backs those slots. Affects `tests/protocol/test_enums.py` (doc-only). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 4 findings (0 Gap, 1 Conflict, 0 Question, 3 Improvement)
**Blocking:** None

- **Conflict:** `learned_ops` is named as a removal candidate but is the planned data-layer for the *active, registered* `learned_v1` MagicPlugin. `magic_init.py:537` actively seeds `prepared_spells` state "for the learned_ops.prepare op," `innate_v1_cast.py:7` documents `learned_ops.cast` as the legitimate non-beat data-layer API, and `apply_spell_effect.py:34` forward-references it "once the SDK is the production narrator path." Full e2e coverage in `tests/magic/test_e2e_cnc_memorization.py`. Affects `sidequest/magic/learned_ops.py`.
- **Improvement:** the `MessageType` members `DISPATCH_PACKAGE` / `NARRATOR_DIRECTIVE_USED` / `VERDICT_OVERRIDE` remain reserved in `sidequest/protocol/enums.py` (count-tested at 41 in `tests/protocol/test_enums.py`) but no longer have pre-reserved payload schemas after `going_forward.py` removal. Affects `sidequest/protocol/enums.py`.
- **Improvement:** three `MessageType` members (`DISPATCH_PACKAGE`, `NARRATOR_DIRECTIVE_USED`, `VERDICT_OVERRIDE`) are reserved but unregistered in `_KIND_TO_MESSAGE_CLS` and absent from `_REPLAY_SKIP_KINDS`; if ever emitted they hit the fail-loud `raise ValueError` at `session_handler.py:197`. This is pre-existing (not introduced by 101-3) and *correctly* fail-loud, but a future hardening story could add them to `_REPLAY_SKIP_KINDS` to make the intentional-incompleteness explicit. Affects `sidequest/server/session_handler.py`.
- **Improvement:** the changelog comment at `tests/protocol/test_enums.py:214` ("Group D Task 7 reserved … for corpus going-forward capture") still reads accurately as history, but a one-line note that the payload schemas were removed in 101-3 would help a future maintainer avoid assuming a `going_forward.py` still backs those slots. Affects `tests/protocol/test_enums.py`.

### Downstream Effects

Cross-module impact: 4 findings across 4 modules

- **`sidequest/magic`** — 1 finding
- **`sidequest/protocol`** — 1 finding
- **`sidequest/server`** — 1 finding
- **`tests/protocol`** — 1 finding

### Deviation Justifications

1 deviation

- **Removed 2 of the 4 named candidate modules, not all 4**
  - Rationale: The story word is **triage**, and the SM assessment explicitly directed checking ADR-053 before removing gossip_engine. All four have zero production *importers*, but gossip_engine and learned_ops are tested, accepted-ADR behavioral implementations that *live production code actively seeds state for* (`political_engine.py` for gossip; `magic_init.py:537` for learned_ops). Deleting them would strand that live seeding code and delete working behavior — the exact "implemented but not yet wired → wire up, don't reimplement/delete" case in CLAUDE.md. The two corpus modules are behavior-free (a reservation-only schema shell + an orphan heuristic) with no seeding pointed at them → genuine No-Stubbing dead code.
  - Severity: minor
  - Forward impact: minor — gossip_engine/learned_ops wiring should be tracked as their own integration stories; the protocol enum reservation (DISPATCH_PACKAGE etc.) is intentionally retained.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Removed 2 of the 4 named candidate modules, not all 4**
  - Spec source: 101-3 session scope / story title ("Triage + remove zero-importer server modules: gossip_engine ..., learned_ops, corpus/going_forward, corpus/negatives")
  - Spec text: "Triage + remove zero-importer server modules" — the title lists four modules as removal candidates.
  - Implementation: Removed `corpus/going_forward.py` and `corpus/negatives.py` (+ their tests). KEPT `gossip_engine` and `learned_ops`.
  - Rationale: The story word is **triage**, and the SM assessment explicitly directed checking ADR-053 before removing gossip_engine. All four have zero production *importers*, but gossip_engine and learned_ops are tested, accepted-ADR behavioral implementations that *live production code actively seeds state for* (`political_engine.py` for gossip; `magic_init.py:537` for learned_ops). Deleting them would strand that live seeding code and delete working behavior — the exact "implemented but not yet wired → wire up, don't reimplement/delete" case in CLAUDE.md. The two corpus modules are behavior-free (a reservation-only schema shell + an orphan heuristic) with no seeding pointed at them → genuine No-Stubbing dead code.
  - Severity: minor
  - Forward impact: minor — gossip_engine/learned_ops wiring should be tracked as their own integration stories; the protocol enum reservation (DISPATCH_PACKAGE etc.) is intentionally retained.

### Reviewer (audit)
- **Removed 2 of the 4 named candidate modules, not all 4** → ✓ ACCEPTED by Reviewer: independently verified. `political_engine.py:211` ("gossip propagation of it is evaluated in later plans, not here") confirms `gossip_engine` is planned-but-unwired by design; `magic_init.py:537` ("The actor will populate this via the learned_ops.prepare op") confirms live seeding points at `learned_ops`, which also carries behavioral e2e coverage (`test_e2e_cnc_memorization`). Deleting either would strand live code and delete working/tested behavior — correctly excluded under CLAUDE.md "wire up what exists, don't delete." The two removed corpus modules are genuinely consumer-free (verified: zero production importers, not in `_KIND_TO_MESSAGE_CLS`, not in the corpus miner pipeline). "Triage" is the operative word in the story title; a 2-of-4 outcome is a valid triage result, not under-delivery.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (env test failure) | confirmed 0, dismissed 1 (pre-existing/unrelated), deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 2 (both medium, latent) | confirmed 0, dismissed 2 (both pre-existing + fail-loud/accurate), deferred 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned, 6 disabled via settings)
**Total findings:** 0 confirmed, 3 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

This is a clean dead-code removal. The diff deletes two consumer-free modules (`corpus/going_forward.py`, `corpus/negatives.py`) plus their dedicated tests, and corrects one comment in `enums.py`. I independently verified the two KEEP decisions and the safety of the two removals before ruling.

**Data flow traced:** event `kind` → `_KIND_TO_MESSAGE_CLS.get(kind)` (`session_handler.py:197`) → payload class. The three reserved `MessageType` members were never keys in this map (verified: zero references to `DISPATCH_PACKAGE`/etc. outside `enums.py`), and nothing imported the deleted payload classes (`DispatchPackageEvent` et al.). Unknown kinds **fail loud** via `raise ValueError` — safe by the No-Silent-Fallbacks rule.

**Pattern observed:** correct application of "wire up what exists, don't delete" — `gossip_engine`/`learned_ops` retained because live seeding code (`political_engine.py:194/211`, `magic_init.py:537`) points at them and they carry behavioral tests; `corpus/*` shells removed because nothing consumes them (No-Stubbing).

**Error handling:** the only error path in the affected area (`session_handler.py:197`) raises on unknown kind — verified unchanged and fail-loud.

**Observations (≥5):**
- [VERIFIED] No stranded imports — `git grep` across `sidequest/` + `tests/` for all removed symbols returns zero hits (corroborated by `[preflight]`). Evidence: preflight grep + my own sweep both clean.
- [VERIFIED] `_KIND_TO_MESSAGE_CLS` (`session_handler.py:66`) never referenced the deleted payload classes — the reserved kinds were unregistered before and after. Evidence: grep shows `DISPATCH_PACKAGE` only in `enums.py`.
- [VERIFIED] KEEP of `gossip_engine` is correct — `political_engine.py:211` defers gossip propagation to "later plans"; ADR-053 accepted/partial. Not dead code.
- [VERIFIED] KEEP of `learned_ops` is correct — `magic_init.py:537` seeds `prepared_spells` for `learned_ops.prepare`; `test_e2e_cnc_memorization` exercises prepare/cast/rest. Deleting it would delete live test coverage of an active subsystem.
- [VERIFIED] `enums.py` comment edit is accurate and narrows nothing — wire-format values unchanged, members retained, count test (`test_message_type_complete_count`) still green per preflight.
- [LOW] `[EDGE]` Pre-existing: three reserved kinds unregistered in `_KIND_TO_MESSAGE_CLS` / absent from `_REPLAY_SKIP_KINDS` (`session_handler.py:66`). Fail-loud, documented at `enums.py:97`, out of scope for this story — logged as a non-blocking delivery finding.
- [LOW] `[EDGE]` `tests/protocol/test_enums.py:214` changelog comment is historical and accurate; optional clarifying note logged as a delivery finding.

**Subagent dispatch tags:**
- `[EDGE]` — 2 findings, both dismissed: (1) `_KIND_TO_MESSAGE_CLS` missing-guard is pre-existing and fails loud at `session_handler.py:197` (No-Silent-Fallbacks compliant), not introduced by this diff; (2) `test_enums.py:214` comment is an accurate historical changelog, not a pointer to deleted code. Both logged as non-blocking delivery findings.
- `[SILENT]` — subagent disabled via settings; reviewer check: the one error path in scope (`session_handler.py:197`) raises loudly, no swallowed errors in the diff (pure deletions + comment).
- `[TEST]` — subagent disabled via settings; reviewer check: deleted tests covered only the deleted modules; remaining `tests/corpus/` + `tests/protocol/` suites green (319 passed). No orphaned fixtures/conftest references (verified).
- `[DOC]` — subagent disabled via settings; reviewer check: the `enums.py` comment was correctly updated to not reference the deleted file; one optional `test_enums.py` changelog clarification logged as a finding.
- `[TYPE]` — subagent disabled via settings; reviewer check: no type/signature changes — diff is deletions + a comment.
- `[SEC]` — clean (reviewer-security returned no findings): deleted code held no validation gate on any inbound path, no auth, no secrets; comment change weakens no contract.
- `[SIMPLE]` — subagent disabled via settings; reviewer check: removal *reduces* complexity (−177 lines of dead code); no new complexity introduced.
- `[RULE]` — subagent disabled via settings; reviewer check in Rule Compliance below.

### Rule Compliance
Project rules applied to this diff (CLAUDE.md / SOUL.md):
- **No Stubbing** ("don't leave empty shells / placeholder modules; dead code is worse than no code"): `corpus/going_forward.py` was a behavior-free reservation shell and `corpus/negatives.py` an orphan — removing them *enforces* this rule. COMPLIANT (the removal is the rule in action).
- **No Silent Fallbacks**: the only error path in the affected area (`session_handler.py:197`) raises `ValueError` on unknown kind — no silent fallback introduced or removed. COMPLIANT.
- **Don't Reinvent — Wire Up What Exists** + **Verify Wiring, Not Just Existence**: `gossip_engine`/`learned_ops` are implemented-but-unwired with live seeding pointed at them — correctly retained for future wiring rather than deleted. COMPLIANT.
- **OTEL Observability**: not applicable — this is a dead-code removal + comment change ("Not needed for: cosmetic changes"), no subsystem decision logic added or modified. N/A.
- **No Source-Text Wiring Tests**: no new tests added; no `read_text()`-style assertions introduced. N/A.

### Devil's Advocate
Let me argue this change is broken. The strongest attack: the story said "remove zero-importer modules" and named four; Dev removed only two, so the story is under-delivered and a reviewer rubber-stamping a 50% completion is negligent. Counter: the story's first word is *triage*, and the SM setup explicitly instructed checking ADR-053 before deleting `gossip_engine` — a 2-of-4 outcome where the other two are demonstrably live-seeded is the correct triage result, not a shortfall. A maintainer who wanted all four gone unconditionally would have written "delete," not "triage."

Second attack: removing `going_forward.py` leaves three orphaned enum members that can now never be deserialized — a latent landmine. If an *older* server instance, mid-rolling-deploy, wrote a persisted event row with kind `DISPATCH_PACKAGE`, a newer instance replaying that row would hit `_KIND_TO_MESSAGE_CLS.get()` → None. But the evidence refutes the severity: those kinds were *never* registered in the map (the payload classes existed only as unconsumed schemas), so this replay hazard is identical before and after this diff — the deletion changes nothing about it — and the path *fails loud* (`raise ValueError`), which is the documented, rule-compliant behavior, not data corruption. No emitter ever produced these kinds (zero references), so no such row can exist.

Third attack: a confused future maintainer reads `test_enums.py:214` ("reserved … for corpus going-forward capture"), greps for `going_forward.py`, finds nothing, and assumes the reservation is bogus — then deletes the enum members and breaks the count test. This is plausible but low-severity (a self-correcting CI failure, not a runtime bug), and I've logged a delivery finding suggesting a one-line clarification. Fourth: could the deleted `detect_retarget` have been a planned input to the corpus miner? Checked — `miner.py` does not import it and never did; it's a genuine orphan. None of these attacks rises to Critical or High. The removal is safe.

**Handoff:** To SM (Winston Smith) for finish-story.