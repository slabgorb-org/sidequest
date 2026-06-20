---
story_id: "126-36"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-36: [UX-LOW] Solo session uses party-scale framing in openings + quest briefs

## Story Details
- **ID:** 126-36
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** content, server

## Story Description

dust_and_lead opening establishing_narration (openings.yaml the_drifters_offer) reads 'pours four small glasses … waits for the party'; narrator then says 'fifty each for two riders' in a solo game. Make the authored opening party-count-aware (singular for solo) and tell the narrator the seat count so quest briefs scale ('a rider' vs 'two riders').

## SM Assessment

Setup complete and verified: session in `.session/`, story context written, feature branch
`feat/126-36-solo-party-scale-framing` created in **both** content and server subrepos, story
marked `in_progress`. Jira explicitly SKIP (integration not configured). Workflow `tdd` (phased)
→ next owner is **TEA (red)**. ACs are title-defined; the routing note below frames the
two-surface scope and the one design question TEA must resolve before fixing a test shape.
No blockers. Cleared for handoff to TEA.

## SM Routing Note (Vizzini → TEA)

This 2-pt UX bug spans two surfaces. Keep them distinct:

- **content** — `sidequest-content/genre_packs/spaghetti_western/worlds/dust_and_lead/openings.yaml`,
  opening `the_drifters_offer`. `establishing_narration` hardcodes party-scale framing
  ("pours four small glasses … waits for the party"). Quest-brief prose also reads "fifty
  each for two riders." Authored prose is **VALIDATED via `load_genre_pack`, not unit-tested**
  — do not write a RED unit test against YAML prose. (Project doctrine: content is validated,
  not tested.)
- **server** — the narrator/opening-render must know the **seat/party count** so framing
  scales singular ("a rider") vs plural ("two riders"). This is the **testable seam** — the
  RED phase belongs here.

**Load-bearing question for TEA → Architect (answer before writing tests):** can an authored
opening be party-count-aware *today*? Either (a) the opening schema already supports solo-vs-party
variant prose / a placeholder the server fills, or (b) this needs a server change to expose
seat_count to opening rendering **and** into the narrator prompt that writes quest briefs.
That answer decides whether the content change is variant-authoring or templating, and how big
the server slice is. Confirm where `establishing_narration` is rendered and where the narrator
prompt is assembled before committing to a test shape.

**Scope guard:** this is filed p3/2pt. If openings already support variants/conditionals, the
fix is small. If they don't, surface to Architect — don't let a UX framing bug balloon into a
schema epic. Record the finding under Delivery Findings either way.

## TEA Assessment

**Tests Required:** Yes
**Reason:** The server half is real, unit-testable behavior (narrator-prompt
assembly + OTEL). The content half is validated, not unit-tested (see deviation).

**Test Files:**
- `sidequest-server/tests/agents/test_party_scale_signal.py` — 9 RED cases (one
  parametrized over [2,3,4]) for the always-on `party_scale` narrator-prompt
  section + `narrator.party_scale` OTEL span.

**Tests Written:** 9 cases (RED). Verified failing via testing-runner — all fail on
the intended assertions (`section is None` / `no narrator.party_scale span`), clean
collection, no setup/import/fixture/DB errors. The OTEL failure confirms
`build_narrator_prompt` runs and emits its other spans (`narrator.seed_context`,
`narrator.verbosity_tier`, …) but not yet ours.

**Status:** RED (failing — ready for Dev)

### The fix (contract for Dev, derived from measured seams)

Root cause: `register_party_peer_section` (`prompt_framework/core.py:978`) returns
early on an empty peer list (zero-byte-leak), so a SOLO session registers **no**
party section — the narrator has zero seat-count ground truth and improvises
"fifty each for two riders." `party_peers` excludes self, so **seat count =
1 + len(context.party_peers)**.

Server work (makes the tests green):
1. Register an always-on `party_scale` `PromptSection` in `build_narrator_prompt`
   (`agents/orchestrator.py` ~2320, beside the party_peer block) — fires for solo
   AND MP, every turn. Solo content signals a single player; MP content states the
   exact seat count ("<n> player(s)").
2. Emit an always-fire `narrator.party_scale` OTEL span (attr `player_count`),
   modelled on `SPAN_NARRATOR_SEED_CONTEXT` (`telemetry/spans/narrator.py`) — fires
   even solo (player_count=1) so the GM panel can prove the signal engaged.

Content work (NOT unit-tested — see Delivery Findings / deviation): neutralise the
verbatim party-scale wording in `dust_and_lead/openings.yaml` `the_drifters_offer`
(and sibling `sangre_del_paso_main_street_noon`), validate via `load_genre_pack`.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL on subsystem decision (CLAUDE.md) | `test_party_scale_emits_otel_span_solo`, `test_party_scale_otel_span_carries_seat_count_mp` | failing |
| Wiring (real production seam, not source-grep) | all tests drive real `Orchestrator.build_narrator_prompt`; OTEL span = wiring assert | failing |
| #6 Test quality (no vacuous asserts) | every presence check (`section is not None`, `assert spans`) is followed by a specific value assertion; parametrized cases assert distinct counts | n/a (self-check) |
| #9 Async/await (no missing awaits) | all cases `@pytest.mark.asyncio` + `await build_narrator_prompt` | n/a (self-check) |

**Rules checked:** test-only diff — applicable lang-review checks are #6 (test
quality) and #9 (async); both satisfied. Project OTEL + wiring rules covered by the
span tests against the real prompt-assembly seam (no source-text wiring tests —
compliant with the "No Source-Text Wiring Tests" rule).
**Self-check:** 0 vacuous tests (no `assert True`, no dangling truthy checks).

**Handoff:** To Dev (Inigo) for implementation — server signal + content edit.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server — `feat/126-36-solo-party-scale-framing` @ ddfcf468):**
- `sidequest/telemetry/spans/narrator.py` — new `SPAN_NARRATOR_PARTY_SCALE =
  "narrator.party_scale"`; added to `FLAT_ONLY_SPANS` + `__all__` (re-exported via
  `spans/__init__.py`'s `from .narrator import *`).
- `sidequest/agents/prompt_framework/core.py` — new `register_party_scale_section`
  helper (sibling of `register_party_peer_section`, but ALWAYS registers; singular
  copy for solo, exact `<n> players` copy for MP).
- `sidequest/agents/orchestrator.py` — `build_narrator_prompt` now computes
  `1 + len(context.party_peers)` and, inside a `narrator.party_scale` span
  (`player_count` attr), registers the section every build (solo included).

**Files Changed (content — `feat/126-36-solo-party-scale-framing` @ 1a4277b):**
- `genre_packs/spaghetti_western/worlds/dust_and_lead/openings.yaml` — neutralised
  party-scale wording in the two `mode: either` (solo-capable) openings:
  `the_drifters_offer` ("pours four small glasses … waits for the party" → "uncorks
  a bottle … pours, and waits for you"; "find the party / buy them a meal" → "find
  you / buy you a meal") and `sangre_del_paso_main_street_noon` ("The party is in
  town. The party has water and the party has eyes" → "You are in town. You have
  water and you have eyes"). `silver_canyon_buffalo_soldiers` left untouched
  (`mode: multiplayer`, never fires solo).

**Tests:** 9/9 GREEN (`tests/agents/test_party_scale_signal.py`). Regression: 1499
passed / 0 failed in `tests/agents/`; 90 passed / 0 failed across the prompt
blast-radius (party-peer identity, player-count gate, snapshot-slimming, seven-field
projection, drama-aware length limit, turn-context wiring, narrator pre-prompt).
Content validated via `load_genre_pack` (spaghetti_western loads, 3 openings, no
"four"/"the party" remaining in the edited prose).

**Branches:** both pushed to origin (`slabgorb-org/sidequest-server`,
`slabgorb-org/sidequest-content`).

**Handoff:** To verify/review.

## [SUPERSEDED] Round-Trip 0 Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (format-check FAIL) | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (`<=1` floor) | confirmed 1 (downgraded LOW), dismissed 0 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed (both LOW), 0 dismissed, 0 deferred

## [SUPERSEDED] Round-Trip 0 Rule Compliance

Checklist source: `.pennyfarthing/gates/lang-review/python.md` + CLAUDE.md/SOUL.md.

- **No Silent Fallbacks (CLAUDE.md, `<critical>`):** `register_party_scale_section`
  `player_count <= 1` (core.py:1041) silently maps 0/negative → solo framing. Today
  unreachable (`1 + len(list) ≥ 1`), but it's a public method accepting a bare int with
  no precondition. **VIOLATION (LOW)** — `[SILENT]` finding F2. Every other code path
  fails loud (`len(None)` → TypeError propagates; `Span.open` re-raises).
- **OTEL on subsystem decisions (CLAUDE.md):** `narrator.party_scale` span added,
  fires every build incl. solo. **COMPLIANT** — span constant + FLAT_ONLY_SPANS +
  `__all__` re-export all present.
- **No Source-Text Wiring Tests (CLAUDE.md):** tests drive real
  `build_narrator_prompt` + assert on the OTEL span/rendered section, no `read_text()`
  grep. **COMPLIANT.**
- **Python #6 Test quality:** all asserts check specific values; no `assert True`,
  no dangling truthy. **COMPLIANT.**
- **Python #6 (sub-rule) ruff format:** `tests/agents/test_party_scale_signal.py`
  fails `ruff format --check` (2 expressions over-wrapped). **VIOLATION (LOW)** —
  `[preflight]` finding F1. Production files (orchestrator/core/narrator) all pass.
- **Python #9 Async:** all tests `@pytest.mark.asyncio` + `await`. **COMPLIANT.**
- **No Stubbing / Wire up what exists:** reuses `PromptSection.new` +
  `register_section`, mirrors `register_party_peer_section` and `seed_context`.
  **COMPLIANT.**

## Reviewer Observations

1. `[VERIFIED]` Injection-safe: `register_party_scale_section` interpolates ONLY the
   integer `player_count` into prose (core.py:1052-1057) — no player-authored string —
   evidence corroborated by `[SEC]` (clean). ADR-047 surface: none.
2. `[VERIFIED]` Wiring is real: the section + span are registered in
   `build_narrator_prompt` (orchestrator.py:2349), the production per-turn assembler;
   `[TEST]` self-assessed — the 9 tests exercise that exact seam (solo/MP/scaling/
   every-turn/OTEL). Not existence-only.
3. `[VERIFIED]` Always-on contract met: unlike `register_party_peer_section` (MP-only,
   early-return), the new section has no early-return — solo (the bug) gets the signal.
   Evidence: core.py has no `if not ...: return` guard; test
   `test_party_scale_section_registers_for_solo` passes.
4. `[LOW][preflight]` `tests/agents/test_party_scale_signal.py` fails
   `ruff format --check` — pure reflow (collapse a list-comp and an `any(...)` to one
   line each). No logic impact. Fix: `uv run ruff format`.
5. `[LOW][SILENT]` `register_party_scale_section` `player_count <= 1` floor silently
   absorbs 0/negative into solo framing (core.py:1041). Add a fail-loud precondition
   `if player_count < 1: raise ValueError(...)` and make the branch `== 1`, per the
   No-Silent-Fallbacks rule. Unreachable today; hardens the public contract.
6. `[VERIFIED][SEC]` OTEL span carries only `{"player_count": int}` — no PII/secret;
   MP firewall safe (a table-global headcount, not peer secrets). Evidence:
   orchestrator.py:2349.
7. `[VERIFIED]` Content edit is count-neutral 2nd person and the loader accepts it
   (Dev `load_genre_pack` PASS; preflight `content_validation` PASS). "three parties"
   (factions) correctly left intact; `silver_canyon` (`mode: multiplayer`) untouched.
8. `[TYPE]` (subagent disabled — reviewer self-assessed): `player_count: int`, no
   stringly-typed API; `PromptSection.new(...)` typed. No type concerns.
9. `[DOC]` (subagent disabled — reviewer self-assessed): the new docstring, the
   orchestrator comment, and the span comment all accurately describe the always-on,
   solo-included behavior. No stale/misleading docs.
10. `[SIMPLE]` (subagent disabled — reviewer self-assessed): minimal; the local
    `from ...spans import ... Span` mirrors the adjacent `seed_context` block (accepted
    pattern, not a smell). No dead code beyond the proposed precondition (a guard, not a stub).
11. `[EDGE]` (subagent disabled — reviewer self-assessed): boundary is player_count=1
    (solo) — covered; ≥2 covered (2,3,4); 0/negative unreachable — see `[SILENT]` F2.
12. `[RULE]` (subagent disabled — reviewer self-assessed): see Rule Compliance — two
    LOW violations (format, silent-fallback), rest compliant.

### Devil's Advocate

Assume this code is broken. The most dangerous claim is "the narrator now scales quest
briefs correctly," because nothing here *tests the narrator's actual output* — the tests
assert the prompt SECTION exists and says "1 player", but an LLM told "1 player" can still
write "fifty each for two riders" if a stronger competing cue exists. The competing cue is
exactly the cold-open prose, which is why the content edit is load-bearing and was done;
still, the fix is *probabilistic*, not deterministic — the section is a guardrail, not an
enforcement. That's acceptable for a narration-tuning story (the OTEL span lets Keith
verify the signal fired; the GM panel is the lie-detector), but worth naming: this story
reduces, not eliminates, the chance of a party-scaled brief. A confused author writing a
new `mode: either` opening will re-introduce the bug in their prose — the server signal
helps, but authored hard-counts still leak verbatim through the cold-open path (Dev's
non-blocking finding flags a future content sweep — correct). A malicious user can't do
much: the only injected datum is a derived integer (`[SEC]` confirmed). The stressed-input
angle: if `context.party_peers` is ever `None` (contract violation), `len(None)` raises
loud BEFORE the section — acceptable. The unbounded angle: a 50-seat session would render
"50 players" — fine, bounded by the session seat cap. The real residual risk the
devil surfaces is the `<=1` floor (already a finding): a future refactor that makes
`player_count` 0 produces a *plausible-but-wrong* solo prompt with no turn-time error — the
precise failure mode (convincing prose, no mechanical backing) the project's OTEL doctrine
exists to catch. The fail-loud guard closes that. Net: no Critical/High, two LOWs worth
fixing in a quick green-rework.

## [SUPERSEDED] Round-Trip 0 Reviewer Assessment (REJECTED — fixes verified in re-review below)

**Verdict:** REJECTED (both findings LOW, but one is a FAILING mechanical gate
[`ruff format --check`] and the other matches the `<critical>` No-Silent-Fallbacks rule;
TDD has a working green rework edge, so the clean path is a fast bounce, not shipping a
format-failing + silently-floored PR.)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW] `[preflight]` | `tests/agents/test_party_scale_signal.py` fails `ruff format --check` (2 over-wrapped expressions; pure reflow) | `tests/agents/test_party_scale_signal.py:46,107` | `cd sidequest-server && uv run ruff format tests/agents/test_party_scale_signal.py`; commit |
| [LOW] `[SILENT]` | `register_party_scale_section` `player_count <= 1` silently maps 0/negative → solo framing (No-Silent-Fallbacks) | `sidequest/agents/prompt_framework/core.py:1041` | Add `if player_count < 1: raise ValueError(f"player_count must be >= 1, got {player_count!r}")` at method top; change branch to `== 1` |

Dispatch tags present: `[preflight]` (F1), `[SILENT]` (F2 confirmed), `[SEC]` (clean),
`[EDGE]`/`[TEST]`/`[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]` (subagents disabled — reviewer
self-assessed, see Observations 8-12 + Rule Compliance).

**Data flow traced:** player action → `build_narrator_prompt` → `_player_count =
1 + len(context.party_peers)` (always ≥1) → integer-only into the `party_scale` section
prose + the `narrator.party_scale` span attribute → narrator LLM prompt. Safe: no
untrusted string enters; span leaks no PII.

**Pattern observed:** correct sibling-mirroring of `register_party_peer_section` +
`narrator.seed_context` (always-emit span) at core.py:1024 / orchestrator.py:2338.

**Handoff:** Back to Dev (Inigo) for the two LOW fixes (green rework). No new tests
needed — existing 9 stay green (guard never fires; format is cosmetic).

## Dev Assessment (Rework — Round-Trip 1)

**Implementation Complete:** Yes

Addressed both Reviewer (Westley) LOW findings exactly as specified; no scope beyond
the two fixes.

**Files Changed (server — `feat/126-36-solo-party-scale-framing` @ ab3e2c37):**
- `sidequest/agents/prompt_framework/core.py` — `register_party_scale_section` now
  fails loud on `player_count < 1` (`raise ValueError(f"player_count must be >= 1,
  got {player_count!r}")`) and narrows the solo branch from `<= 1` to `== 1`. Closes
  the No-Silent-Fallbacks finding (F2 `[SILENT]`): 0/negative no longer silently
  maps to solo framing. Unreachable today (`1 + len(party_peers) ≥ 1`) but hardens
  the public contract — exactly the plausible-but-wrong failure mode OTEL doctrine
  exists to catch.
- `tests/agents/test_party_scale_signal.py` — `ruff format` reflow of the two
  over-wrapped expressions (F1 `[preflight]`). Pure cosmetic; no logic change.

**Verification:**
- `ruff format --check` PASS on both the test file and `core.py` (prod file already
  passed; verified unchanged).
- `ruff check` PASS on `core.py`.
- `tests/agents/test_party_scale_signal.py` — 9/9 GREEN (guard never fires; tests
  pass player_count ∈ {1,2,3,4}).
- Working tree clean; committed `ab3e2c37`; pushed to `slabgorb-org/sidequest-server`.

**No new tests:** Per Reviewer scope — the guard is unreachable in production and the
existing 9 cover all reachable behavior. Adding a test for an unreachable path is low
value and out of the rework scope.

**Handoff:** Back to review (Westley) — both LOW findings resolved.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T07:37:53Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T06:49:06.566803+00:00 | 2026-06-20T06:52:23Z | 3m 16s |
| red | 2026-06-20T06:52:23Z | 2026-06-20T07:06:48Z | 14m 25s |
| green | 2026-06-20T07:06:48Z | 2026-06-20T07:16:09Z | 9m 21s |
| review | 2026-06-20T07:16:09Z | 2026-06-20T07:24:45Z | 8m 36s |
| green | 2026-06-20T07:24:45Z | 2026-06-20T07:29:28Z | 4m 43s |
| review | 2026-06-20T07:29:28Z | 2026-06-20T07:37:53Z | 8m 25s |
| finish | 2026-06-20T07:37:53Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): Story 126-36 has TWO surfaces; the RED tests cover only the
  **server** seat-count signal. The **content** half — neutralising the verbatim
  party-scale wording in `dust_and_lead/openings.yaml` `the_drifters_offer`
  (`first_turn_invitation`: "pours four small glasses … waits for the party") — is
  NOT covered by a unit test (per doctrine: content is validated, not unit-tested).
  Dev MUST make this content edit in green; verify via `load_genre_pack` + GM/cliché
  review. Measured: the solo cold-open emits `first_turn_invitation` **verbatim**
  (`websocket_session_handler.py` consume step, ~2865; suppressed only when
  `len(characters) > 1`), so the narrator never regenerates that line — the server
  seat-count signal CANNOT fix it. Two surfaces fix two distinct symptoms.
  Affects `sidequest-content/genre_packs/spaghetti_western/worlds/dust_and_lead/openings.yaml`
  (the_drifters_offer prose). *Found by TEA during test design.*
- **Improvement** (non-blocking): The sibling opening `sangre_del_paso_main_street_noon`
  (same world, `mode: either`, so it also fires solo) leans on the same "The party
  is in town / The party has water" framing and will read wrong in a solo game.
  Dev should neutralise it in the same content pass while editing the file.
  Affects same `openings.yaml`. *Found by TEA during test design.*
- **Question** (non-blocking): The fix pins a contract — section name `party_scale`,
  span `narrator.party_scale` with attribute `player_count`. If Keith prefers
  different naming, it's a cheap rename in the tests. Flagging so the choice is
  visible, not buried. Affects `sidequest-server/tests/agents/test_party_scale_signal.py`.
  *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The same solo-party-scale-framing bug class likely
  exists in other packs' `mode: either` / `mode: solo` openings beyond dust_and_lead
  (any opening that hard-codes "the party"/a player headcount in authored prose).
  This story fixed only the two dust_and_lead openings in scope; a future sweep across
  `genre_packs/**/worlds/**/openings.yaml` would catch the rest now that the server
  seat-count signal exists. Affects `sidequest-content/genre_packs/**/openings.yaml`.
  *Found by Dev during implementation.*
- **Resolved** (non-blocking): TEA's two content findings (the_drifters_offer +
  sibling sangre_del_paso_main_street_noon) are both addressed in this story —
  neutralised to count-free second person, validated via `load_genre_pack`.
  *Found by Dev during implementation.*
- **Resolved** (non-blocking): Reviewer's two blocking LOW findings (`[SILENT]`
  player_count floor + `[preflight]` ruff format) are both fixed in the
  Round-Trip 1 green rework (commit ab3e2c37); no new upstream findings surfaced.
  *Found by Dev during rework.*

### Reviewer (code review)
- **Improvement** (blocking, this story): `register_party_scale_section` `player_count
  <= 1` silently absorbs 0/negative into solo framing — add a fail-loud precondition
  per the No-Silent-Fallbacks rule. Affects `sidequest-server/sidequest/agents/prompt_framework/core.py:1041`
  (guard + `== 1` branch). *Found by Reviewer during code review.*
- **Improvement** (blocking, this story): `tests/agents/test_party_scale_signal.py`
  fails `ruff format --check` (pure reflow). Affects that file (run `ruff format`).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): I concur with Dev's cross-pack sweep finding — once
  the seat-count signal is verified in playtest, a sweep of other `mode: either`/`solo`
  openings for hard-coded party framing would close the bug class. Affects
  `sidequest-content/genre_packs/**/openings.yaml`. *Found by Reviewer during code review.*
- **Resolved** (non-blocking): Both blocking Round-Trip 0 findings (the `[SILENT]`
  player_count floor and the `[preflight]` ruff format) are verified fixed in the
  re-review (commit `ab3e2c37`); the `[SILENT]`/`[SEC]`/preflight subagents returned
  clean. No new upstream findings during the re-review. *Found by Reviewer during
  re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Content half not unit-tested (test omission)**
  - Spec source: 126-36 story title (session scope); context-story-126-36.md
  - Spec text: "Make the authored opening party-count-aware (singular for solo)"
  - Implementation: No server unit test asserts on `dust_and_lead` opening prose;
    RED tests cover only the server seat-count signal (`party_scale` section +
    `narrator.party_scale` span). The content edit is verified via `load_genre_pack`
    + GM review during green/review.
  - Rationale: Project doctrine — content is validated, not unit-tested; "tests must
    not point at live content" (a fixture asserting on a real pack slug is the
    prod-rows-in-tests anti-pattern). The verbatim cold-open prose is emitted
    unchanged by the cold-open path, so only the content edit fixes that authored
    line; that's a validation concern, not a server-behavior assertion.
  - Severity: minor
  - Forward impact: Dev must perform the content edit in green (see Delivery
    Findings); Reviewer/GM validate the prose. Without it, the verbatim opening
    line stays party-scaled even after the server signal lands.

### Dev (implementation)
- **Content prose made count-neutral, not count-variant**
  - Spec source: 126-36 story title (session scope)
  - Spec text: "Make the authored opening party-count-aware (singular for solo)"
  - Implementation: Rewrote the two solo-capable `dust_and_lead` openings to
    count-FREE second person ("you", "pours", "uncorks a bottle … pours") rather
    than authoring separate singular-vs-plural variant prose. The openings are
    `mode: either` (fire solo AND party), so count-neutral prose reads correctly
    for both; the per-turn server `party_scale` signal supplies the actual count
    to the narrator's generated text.
  - Rationale: A literal singular-for-solo / plural-for-party split would require
    opening-schema templating or variant fields — the schema has none today (TEA
    Explore: `Opening` prose is verbatim, no placeholders). SM's scope guard was
    explicit: don't balloon a p3/2pt UX bug into a schema epic. Count-neutral
    prose + the server seat-count signal achieves "singular for solo" with zero
    schema change.
  - Severity: minor
  - Forward impact: none. If a future story wants per-count variant opening prose,
    that's a deliberate schema feature, not blocked by this.

### Reviewer (audit)
- **TEA: Content half not unit-tested** → ✓ ACCEPTED by Reviewer: sound — content is
  validated, not unit-tested (project doctrine), and the loader (`load_genre_pack`)
  PASS plus the preflight content-validation check cover the wiring. Tests-pointing-at-
  live-content correctly avoided.
- **Dev: Content prose made count-neutral, not count-variant** → ✓ ACCEPTED by Reviewer:
  agrees with author reasoning — the Opening schema has no templating/variant fields
  (TEA Explore confirmed), so count-neutral 2nd person is the only no-schema-change way
  to satisfy "singular for solo" for a `mode: either` opening. Honours SM's scope guard
  (don't balloon a p3/2pt UX bug into a schema epic). No undocumented deviations found
  in the diff.
---

## Subagent Results

Re-review of the green rework (Round-Trip 1). Same toggle config as Round-Trip 0
(`workflow.reviewer_subagents`): preflight, silent_failure_hunter, security enabled;
the other six disabled.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (9/9 green, ruff format+check PASS on all 4 changed files, tree clean) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A — confirms F2 fix is genuinely fail-loud |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned clean; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Re-review of Inigo's green rework (Round-Trip 1). Both Round-Trip 0 LOW findings are
verified fixed, all three enabled subagents returned clean, and no new findings
surfaced.

**What was reviewed:** the rework commit `ab3e2c37` (2 files: `core.py` guard +
`test_party_scale_signal.py` reflow) plus re-verification of the full story diff
(`orchestrator.py` party_scale registration + span at ~2349, `core.py`
`register_party_scale_section`, `narrator.py` `SPAN_NARRATOR_PARTY_SCALE` constant +
FLAT_ONLY_SPANS + `__all__`, and the 9-case test file).

**Fix verification:**
- **F2 `[SILENT]` — FIXED.** `core.py:1041` now `if player_count < 1: raise
  ValueError(f"player_count must be >= 1, got {player_count!r}")`; the solo branch is
  narrowed from `<= 1` to `== 1`. `[SILENT]` subagent confirms this is genuinely
  fail-loud: no swallow, `Span.open` is a bare `@contextmanager` that re-raises,
  `context.party_peers` is `field(default_factory=list)` (orchestrator.py:759) so
  `len()` can't hit None, and the `==1`/`else` partition is exhaustive over the
  reachable domain (≥1) with no silent-wrong path.
- **F1 `[preflight]` — FIXED.** `ruff format --check` PASS on the test file and all
  three production files.

**Observations:**
1. `[VERIFIED]` Fail-loud guard correct — `core.py:1041-1042` raises before any branch;
   `==1` vs `else` is exhaustive over reachable values (≥1). Rule checked: CLAUDE.md
   **No Silent Fallbacks** — now COMPLIANT (this was the Round-Trip 0 violation).
2. `[VERIFIED][preflight]` Format clean — `ruff format --check` PASS on test + 3 prod
   files; Round-Trip 0 `[preflight]` finding closed. Rule checked: Python #6 ruff
   format — COMPLIANT.
3. `[VERIFIED]` Tests green — 9/9 pass; the guard never fires (reachable domain ≥1) so
   existing coverage is intact and there is no regression. Rule checked: tests-green
   gate — COMPLIANT.
4. `[VERIFIED][SEC]` Injection-safe — only the integer `player_count` is interpolated
   into prose (`core.py:1051-1057`); the span carries `{player_count: int}` only. No
   PII, MP-firewall safe. `[SEC]` subagent clean (ADR-047 + ADR-104/105 enumerated, 0
   violations). Rules checked: ADR-047 sanitization, ADR-104/105 firewall — COMPLIANT.
5. `[VERIFIED][SILENT]` No silent path — `[SILENT]` subagent clean; a `ValueError`
   raised inside `with Span.open(...)` propagates unchanged (no `except`/`suppress` in
   `telemetry/spans/span.py`). Rule checked: No Silent Fallbacks — COMPLIANT.
6. `[VERIFIED]` Wiring real — the section + span are registered in
   `build_narrator_prompt` (`orchestrator.py:2349`), the production per-turn assembler;
   the 9 tests drive that exact seam (OTEL span = wiring assert). Rule checked: No
   Source-Text Wiring Tests — COMPLIANT (no `read_text()` grep).

**Dispatch tags present:** `[preflight]` (F1 fixed), `[SILENT]` (F2 fixed, subagent
clean), `[SEC]` (clean). Disabled subagents — reviewer self-assessed:
- `[EDGE]` (disabled — self-assessed): boundaries are player_count=1 (solo, covered),
  ≥2 (covered 2/3/4), and <1 which now raises loud rather than silently absorbing — the
  Round-Trip 0 silent edge is closed. No edge concerns.
- `[TEST]` (disabled — self-assessed): 9 tests drive the real `build_narrator_prompt` +
  OTEL span; no vacuous asserts (every presence check is paired with a value assert).
  Rework added no test — the guard is unreachable in production (`1 + len(list) ≥ 1`),
  so a test for it would be low-value; the existing suite covers all reachable
  behavior. Acceptable.
- `[DOC]` (disabled — self-assessed): docstring + orchestrator/span comments accurately
  describe the always-on, solo-included behavior; the new guard is self-evident. No
  stale/misleading docs.
- `[TYPE]` (disabled — self-assessed): `player_count: int`; no stringly-typed API;
  `PromptSection.new(...)` typed. No type concerns.
- `[SIMPLE]` (disabled — self-assessed): minimal 2-line guard; no dead code, no
  over-engineering, no stub (a precondition is not a stub).
- `[RULE]` (disabled — self-assessed): see Rule Compliance — all applicable rules
  compliant; the one Round-Trip 0 rule violation (No-Silent-Fallbacks) is now fixed.

### Rule Compliance

Checklist source: `.pennyfarthing/gates/lang-review/python.md` + CLAUDE.md/SOUL.md.
Enumerated against every changed symbol.

- **No Silent Fallbacks (CLAUDE.md `<critical>`):** `register_party_scale_section`
  (the only function with a branch on external input) raises `ValueError` on
  `player_count < 1`. **COMPLIANT** (was the VIOLATION in Round-Trip 0).
- **ruff format (Python #6 sub-rule):** all 4 changed files
  (`orchestrator.py`, `core.py`, `narrator.py`, `test_party_scale_signal.py`) pass
  `ruff format --check`. **COMPLIANT** (was VIOLATION in Round-Trip 0).
- **OTEL on subsystem decisions (CLAUDE.md):** `narrator.party_scale` span fires every
  build incl. solo; constant in `FLAT_ONLY_SPANS` + `__all__`. **COMPLIANT.**
- **No Source-Text Wiring Tests (CLAUDE.md):** tests drive real `build_narrator_prompt`
  + assert the OTEL span / rendered section; no `read_text()` grep. **COMPLIANT.**
- **No Stubbing / Wire up what exists:** reuses `PromptSection.new` + `register_section`;
  mirrors `register_party_peer_section` + `seed_context`. **COMPLIANT.**
- **Python #9 Async:** all 9 tests `@pytest.mark.asyncio` + `await`. **COMPLIANT.**

### Devil's Advocate

Assume this rework is broken. The narrowest attack: the change swapped `<= 1` for two
statements — a `< 1` raise and an `== 1` branch. If those don't partition the integer
line correctly, a value could fall through to the wrong prose. Enumerate: player_count
≤ 0 → raises (loud, correct); player_count == 1 → solo prose (correct); player_count ≥
2 → `else` party prose with the exact count (correct). The partition is total and
disjoint over all ints — no fall-through. Could the guard itself break a caller? Only if
production ever legitimately passes 0 — but `_player_count = 1 + len(context.party_peers)`
is provably ≥1, and `party_peers` defaults to `[]` (it cannot be None without a loud
`TypeError` upstream), so the guard is dead in production and live only for a future
mis-caller — exactly its purpose. Could a malicious user reach it? No: the only datum is
a server-derived seat count; no player string flows into the function or the span (the
`[SEC]` subagent enumerated ADR-047 and ADR-104/105 and found 0 violations). Could the
`ValueError` itself leak? Its message interpolates `player_count!r`, a derived integer —
no freetext, no injection vector, and it's a server-side raise not surfaced to the
client. Could the reflow have changed test semantics? No — `ruff format` only rewraps;
the assertions, tokens, and parametrize values are byte-identical in meaning, and the
preflight re-ran all 9 green. The residual risk is the same one named in Round-Trip 0
and unchanged by this rework: the fix is a *probabilistic* narrator guardrail, not
deterministic enforcement — an LLM told "1 player" can still write a plural if a
stronger competing cue exists. That's inherent to a narration-tuning story, mitigated by
the load-bearing content edit and made auditable by the always-fire OTEL span (the GM
panel is the lie-detector). Net: no Critical/High/Medium/Low findings remain. APPROVED.

**Data flow traced:** player action → `build_narrator_prompt` → `_player_count =
1 + len(context.party_peers)` (always ≥1) → `register_party_scale_section` (guard is
unreachable in prod) → integer-only into the `party_scale` prose + the
`narrator.party_scale` span attribute → narrator LLM prompt. Safe: no untrusted string
enters; the span leaks no PII.

**Pattern observed:** correct fail-loud precondition mirroring the project's
No-Silent-Fallbacks discipline; sibling-mirrors `register_party_peer_section` +
`narrator.seed_context` (always-emit span) at `core.py:1024` / `orchestrator.py:2338`.

**Handoff:** To SM (Vizzini) for finish-story.