---
story_id: "153-3"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-3: [WRY-WHIMSY-NO-FATE-CONTEST-DEFS] port wry_whimsy + pulp_noir confrontation catalogs to Fate contest schema + loud loader guard

## Story Details
- **ID:** 153-3
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 5
- **Priority:** p2
- **Repos:** server, content

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T23:57:00Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T21:55:35Z | 2026-06-21T21:58:20Z | 2m 45s |
| red | 2026-06-21T21:58:20Z | 2026-06-21T22:53:39Z | 55m 19s |
| green | 2026-06-21T22:53:39Z | 2026-06-21T23:14:11Z | 20m 32s |
| review | 2026-06-21T23:14:11Z | 2026-06-21T23:24:06Z | 9m 55s |
| red | 2026-06-21T23:24:06Z | 2026-06-21T23:40:45Z | 16m 39s |
| green | 2026-06-21T23:40:45Z | 2026-06-21T23:49:08Z | 8m 23s |
| review | 2026-06-21T23:49:08Z | 2026-06-21T23:57:00Z | 7m 52s |
| finish | 2026-06-21T23:57:00Z | - | - |

## Story Context
Port wry_whimsy and pulp_noir confrontation catalogs to Fate contest schema. Add loud loader guard to validate Fate-pack confrontations define contest_defs (confrontations.yaml must include a `contest_defs:` section for Fate packs, per ADR-144/ADR-126). Reject packs at load-time (server-side) that reference Fate conflicts without contest definitions.

### Acceptance Criteria
- [ ] **AC-1:** Loud loader guard rejects wry_whimsy and pulp_noir at load if confrontations.yaml lacks contest_defs
- [ ] **AC-2:** Port wry_whimsy confrontation catalog to Fate contest schema (map native confrontations to Fate contests with appropriate difficulty + stakes)
- [ ] **AC-3:** Port pulp_noir confrontation catalog to Fate contest schema
- [ ] **AC-4:** Verify both packs load successfully post-port
- [ ] **AC-5:** Existing Fate packs (glenross, oz, wonderland, annees_folles) continue to load

## Sm Assessment

Setup complete and verified for a phased TDD story spanning **server + content**:
- Session created in `.session/` (correct location), context doc present.
- Feature branches `feat/153-3-fate-contest-defs-loader-guard` cut off `develop` in both
  sidequest-server and sidequest-content.
- Jira: none — explicitly skipped (story has no Jira key).
- Merge gate: clear. The one open server PR (#1024, dungeon surface seam) is Keith's untracked
  parallel work on `develop`, not a sprint-story PR, and is unrelated to Fate confrontations.

Routing: hand off to **TEA** for the RED phase. The story arrived underspecified (title only, no
YAML description/AC), so the drafted AC-1..AC-5 are a hypothesis — see the SM Routing Note below.
TEA must verify the real Fate-contest schema before writing tests.

## SM Routing Note (read before RED)

The sprint YAML carried **no description and no acceptance criteria** for this story — only
the title. The AC-1..AC-5 above were drafted by the setup helper purely from the title and
are a **working hypothesis, not verified spec**. Two cautions for TEA:

- The schema field name `contest_defs` is **unverified** — confirm the real field/section name
  in the server's Fate ruleset module and `confrontations.yaml` schema before pinning tests to it.
- The "ADR-126" reference in the hypothesis is almost certainly wrong (ADR-126 is the Magic
  plugin system). The load-bearing ADR here is **ADR-144 (Fate Core Binding replaces the native
  ruleset)**; also relevant: ADR-151 (Fate DEFEND follow-up), ADR-148 (player 4dF rolls).

Known context (verify against current code, trees may lag):
- pulp_noir was historically the only Fate pack **missing** a `confrontations:` section, which
  made annees_folles conflicts fail-loud with "unknown encounter_type" (fixed ~PR #479). Its
  confrontation surface is delicate — re-check its current state first.
- Fate confrontations **reuse the native encounter machinery**; native projection / opponent-
  seeding seams hit Fate's fail-loud d20 guards and must be gated on `ruleset != fate` or seeded.
- Fate's competition types are **contest / conflict / challenge** — "contest schema" in the title
  likely means authoring these defs as Fate competitions, not native confrontation defs. Confirm
  which the title intends before porting wry_whimsy/pulp_noir.

**Treat AC-1..AC-5 as a starting hypothesis; reconcile them with the real schema during RED and
record any correction as a Design Deviation.**

## Architect Assessment (design)

**Decision:** add a `conflict` resolution_mode — the lethal sibling of `contest`
— as a thin authoring handle over the already-built Fate Conflict runtime. Full
spec + authoritative AC-1..AC-9 in `sprint/context/context-story-153-3.md`.

**The session's hypothesis AC-1..AC-5 (above) are SUPERSEDED.** Key corrections
the design measured against real code:
- There is no `contest_defs:` section — a Fate "contest" is a `ConfrontationDef`
  with `resolution_mode: contest`. (The setup helper's `contest_defs` + ADR-126
  references were wrong; ADR-144 is load-bearing.)
- The story's real shape is **3 packs**, not 2: spaghetti_western is also 3/5
  native, and the loud guard is global-to-Fate, so it must be ported too.
- Combat (`violence`/`combat`) maps to the new **`conflict`** mode (lethal), NOT
  `contest` (Keith's ruling — a Jabberwock/gunfight can kill).

**Reuse-first verification (done):** the Fate Conflict engine, the
`seat_as_fate_conflict` seating branch, opponent FateSheet seeding, and
`fate_conflict_seeded_span` all already run today (reached via `beat_selection`).
The only runtime-path edit is folding `conflict` into `_requires_opponent`
(encounter_lifecycle.py); everything else is enum + validators (rules.py) + content.

**Server touchpoints:** `ResolutionMode` enum, `ConfrontationDef._validate` (beat
+ metric branches), the Fate allowlist guard (generalize
`_fate_packs_have_no_opposed_check`), `_requires_opponent`. **No new engine, no new
span.** **Content:** port wry_whimsy (6), pulp_noir (3), spaghetti_western (3).

**Handoff:** To TEA (Fezzik) for RED against the context-doc ACs.

## Delivery Findings

### Architect (design)
- **Gap** (non-blocking): story is under-pointed. Scope grew from "port 2 packs +
  guard" to "new `conflict` resolution_mode + 3 validators + `_requires_opponent` +
  port 3 packs." Honest re-point ≈ 8. Affects `sprint/epic-153.yaml` (153-3 points).
  *Found by Architect during design.*
- **Improvement** (non-blocking): adding `conflict` to `ResolutionMode` completes
  ADR-144's referenced-but-unmodeled "Conflict" authoring path. Consider a one-line
  ADR-144 amendment noting the Contest/Conflict mode pair. Affects
  `docs/adr/0144-*.md`. *Found by Architect during design.*

### TEA (test design)
- **Gap** (non-blocking): the loader beat-count gate `_validate_confrontation_beats`
  (loader.py:~730) exempts only `contest` from the "must have at least one beat"
  rule, not the new `conflict`. Content conflict defs carry >=1 display-only beat so
  it is moot today, but if Dev wants a beatless conflict def to be legal, add
  `conflict` to that exemption too. Affects
  `sidequest/genre/loader.py` (`_validate_confrontation_beats`).
  *Found by TEA during test design.*
- **Conflict** (blocking for Dev): if Dev generalizes `_fate_packs_have_no_opposed_check`
  into an allowlist guard, the rejection message for an `opposed_check` offender MUST
  still contain the literal `"opposed_check"`, or the existing
  `tests/genre/test_fate_no_opposed_check.py::test_fate_pack_rejects_opposed_check`
  (`match="opposed_check"`) regresses. Affects
  `sidequest/genre/models/rules.py` (the Fate-mode guard message).
  *Found by TEA during test design.*
- **Conflict** (blocking for Dev): Reviewer Finding 1 (narrator crash) is REAL and
  reproduced (RED); Reviewer Finding 2 (the stray-beat dial leak) does NOT reproduce —
  a conflict ALWAYS seats with `win_condition="fate_conflict"`, which the 126-37
  narration_apply branch (~5974) drops BEFORE the resolution_mode ladder the Reviewer's
  trace assumed. Dev's GREEN should fix ONLY the narrator (add a conflict Fate-live zone
  parallel to the contest branch at narrator.py ~391); do NOT add a redundant
  resolution_mode==conflict drop branch to narration_apply — it would duplicate the
  126-37 win_condition guard (No Stubbing / dead code). Affects
  `sidequest/agents/narrator.py`. *Found by TEA during test design (RT1).*

### Dev (implementation)
- **Improvement** (non-blocking): the Fate Contest port removes the native
  single-beat `resolution: true` soft-menace exit (59-27 AC3) from wry_whimsy social
  confrontations — a Fate Contest is first-to-3, not single-beat. If a soft social
  menace feels grindy in playtest, the lever is the contest victory target or a
  narrator concession, not re-adding a native resolution beat (Bind the Ruleset).
  Affects `genre_packs/*/rules.yaml` contest thresholds.
  *Found by Dev during implementation.*
- **Resolved** (non-blocking): the TEA finding re the loader beat-count gate
  (`_validate_confrontation_beats` exempts only contest) needed NO change — every
  ported conflict def carries >=1 display-only beat, so the gate never fires; a
  beatless conflict def is not an authored use case.
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): a `conflict` confrontation **crashes the narrator prompt**.
  `narrator.py:434` renders the beat menu with `kind={b.kind.value}` for every
  non-contest encounter; conflict beats are display-only (`kind=None`) → `AttributeError`
  on `None.value` — the exact crash the contest M1 fix (narrator.py:385) prevents.
  Contest has a dedicated early branch (~391); conflict falls into the `elif` at
  ~418 and crashes on every Fate conflict turn (e.g. wry_whimsy `violence`).
  Affects `sidequest/agents/narrator.py` (add a conflict Fate-live zone parallel to
  the contest branch — no native beat menu). *Found by Reviewer during code review.*
- **Gap** (blocking): a `conflict` confrontation leaks the **native dial engine**.
  In the `narration_apply.py` dispatch ladder, `opposed_check`/`contest` are handled
  then `else: _legacy_beat_path = True` (~6442). conflict has no branch → falls into
  the legacy path, so a stray narrator `beat_selection` runs `apply_beat` against the
  display-only stub (ADR-144 REPLACE violation: dial layered on the Fate engine).
  Contest drops + loudly logs stray beats (~6403); conflict must do the same, and
  `_should_gate...` must exclude conflict at ~861. Affects
  `sidequest/server/narration_apply.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): `RulesConfig.ruleset` is a
  case-sensitive plain `str`; `ruleset: Fate` / `" fate"` bypasses ALL Fate
  validators (`_validate_fate`, the new mode guard). It fails loud LATER at the
  registry lookup (UnknownRulesetError), not at load — so not a silent prod path,
  but a hardening gap that predates this story across every ruleset validator.
  Affects `sidequest/genre/models/rules.py` (normalize ruleset to lowercase / make it
  a StrEnum). *Found by Reviewer during code review (via reviewer-security).*

## Design Deviations

### Architect (design)
- **New `conflict` resolution_mode instead of mapping combat to `contest`**
  - Spec source: story title "port … to Fate contest schema"
  - Spec text: "port wry_whimsy + pulp_noir confrontation catalogs to Fate contest schema"
  - Implementation: combat/violence map to a NEW `conflict` mode (lethal Fate
    Conflict), not `contest` (no-harm) — per Keith's 2026-06-21 lethality ruling.
  - Rationale: a Fate Contest cannot inflict harm; a lethal fight must be a Conflict.
  - Severity: major
  - Forward impact: adds a public `ResolutionMode` value; future Fate combat defs
    use `conflict`. No impact on WN-family packs (Fate-gated).
- **Scope expanded to spaghetti_western (3rd pack) + its combat→conflict flip**
  - Spec source: story title (names only wry_whimsy + pulp_noir)
  - Spec text: "port wry_whimsy + pulp_noir confrontation catalogs"
  - Implementation: also port spaghetti_western's 3 native defs, and flip its
    existing `combat` (currently `contest`) to `conflict`.
  - Rationale: the loud guard is global-to-Fate; it rejects spaghetti_western's
    native defs too, so they must port in the same PR (Keith chose "port all 3").
  - Severity: major
  - Forward impact: none beyond this story; leaves all 4 Fate packs guard-clean.

### TEA (test design)
- **AC-5 seating covered at the `_requires_opponent` unit level, not end-to-end**
  - Spec source: context-story-153-3.md, AC-5
  - Spec text: "a `conflict`-mode `combat` def … seats through the Fate Conflict
    path (`seat_as_fate_conflict` True → `fate_conflict_seeded_span`)"
  - Implementation: tested the one runtime delta (`_requires_opponent` folds in
    `conflict`) at unit level. The seating ROUTING is unchanged — `conflict` already
    routes via `seat_as_fate_conflict = mode not in (contest, sealed_letter_lookup)`
    — so an end-to-end `instantiate_encounter_from_trigger` span test would be green
    before AND after (no behavioural delta to drive RED). The existing
    `tests/server/dispatch/test_153_9_fate_other_seating.py` is the live seam canary
    once pulp_noir `combat` becomes `conflict`.
  - Rationale: a wiring test must assert a behavioural delta; the only delta is
    `_requires_opponent`. Driving the unchanged seating branch adds no RED signal.
  - Severity: minor
  - Forward impact: none — Dev's seating change is a one-line `_requires_opponent` add.
- **Guard load-boundary wiring proven via the real-content load tests, not a clone-mutate fixture**
  - Spec source: context-story-153-3.md, AC-3 + AC-6/7/8; CLAUDE.md "Every Test Suite Needs a Wiring Test"
  - Spec text: "a `ruleset: fate` pack … fails pack load with a ValidationError"
  - Implementation: the guard's model-layer behaviour is unit-tested (bare
    `RulesConfig`), and its firing through the production `load_genre_pack` boundary
    is proven by AC-6/7/8 — those call `load_genre_pack` on the real packs and would
    RAISE if the guard fired on unported content. No separate clone-mutate fixture
    test was added.
  - Rationale: the real-content load tests already exercise the loader boundary; a
    clone-mutate fixture of a real pack is fragile (skill/beat cross-checks) and
    redundant.
  - Severity: minor
  - Forward impact: none.
- **`test_conflict_mode_rejects_armed_beats` is green-by-coincidence until the enum exists**
  - Spec source: context-story-153-3.md, AC-1
  - Spec text: "a `conflict` def carries display-only beats … an armed dial field is rejected"
  - Implementation: today the test passes because `conflict` is an invalid enum
    (any conflict def raises); it only asserts the real armed-beat-on-conflict guard
    once Dev adds the enum. Kept because it is non-vacuous (a real `raises`) and
    becomes meaningful post-GREEN.
  - Rationale: cannot author a valid conflict def to isolate the armed-beat path
    before the enum exists.
  - Severity: trivial
  - Forward impact: none — re-verify it stays RED-then-GREEN after the enum lands.
- **RT1: Finding 2 delivered as a GREEN PIN, not a RED — the dial leak does not reproduce**
  - Spec source: Reviewer handoff (RT0) — "a RED test reproducing the conflict narrator
    crash + the stray-beat dial leak"
  - Spec text: "Back to TEA (Fezzik) for a RED test reproducing the conflict narrator
    crash + the stray-beat dial leak"
  - Implementation: wrote the narrator-crash RED (Finding 1, fails today) but Finding 2
    is a GREEN regression PIN (`tests/server/test_153_3_conflict_dispatch_no_dial_leak.py`),
    not a RED. MEASURED: a `resolution_mode: conflict` encounter seated through the real
    path carries `win_condition="fate_conflict"` (encounter_lifecycle.py:1701/1757, not
    combat-gated; pinned by test_fate_seating_denativized_126_30.py:202), and the 126-37
    `if enc.win_condition == "fate_conflict":` branch (narration_apply.py ~5974) drops the
    stray beat BEFORE the resolution_mode ladder the Reviewer's trace assumed. Probe:
    realistic seating → opponent dial 0, `conflict_beat_dropped_dial_blocked` fires (no
    `apply_beat`).
  - Rationale: a RED test must reproduce a real failure. Finding 2's dial leak is already
    closed for conflict by 126-37's win_condition guard — keying a second drop on
    resolution_mode would be redundant (126-37 deliberately keyed on win_condition because
    pre-153-3 Fate conflicts seated as native `beat_selection`; win_condition is the
    authoritative "this is a Fate conflict" signal). Manufacturing a RED would require an
    artificial un-seated encounter that production never builds.
  - Severity: major
  - Forward impact: Dev's GREEN is narrator-only. The lone theoretical gap (a future
    non-trigger / decoupled seat where win_condition != "fate_conflict") is caught by the
    PIN if it ever regresses; flagged non-blocking below.

### Dev (implementation)
- **Three sibling tests updated for the now-Fate pack shapes**
  - Spec source: context-story-153-3.md, AC-6/7/8 (+ CLAUDE.md "delete dead code in the same PR")
  - Spec text: "wry_whimsy / pulp_noir / spaghetti_western confrontations ported to contest/conflict"
  - Implementation: `test_pack_load` (spaghetti dual-dial -> all-Fate-mode load),
    `test_fate_seating_denativized_126_30` (native standoff fixture -> conflict-mode;
    a native beat_selection Fate def is now guard-rejected), and
    `test_wry_whimsy_verbal_confrontation` (native `resolution:true` single-beat ->
    Fate-Contest well-formedness) were updated because the port deliberately removed
    the native shapes they asserted.
  - Rationale: stale-premise tests invalidated by an intended design change; dual-dial
    coverage remains via 5 WN-family packs, and the 126-30 seating invariant is
    unchanged (conflict seats exactly as the old beat_selection standoff did).
  - Severity: minor
  - Forward impact: none.
- **spaghetti_western combat flipped contest -> conflict (implemented)**
  - Spec source: context-story-153-3.md, AC-8
  - Spec text: "combat -> conflict (was a no-harm contest; a gunfight is lethal)"
  - Implementation: changed spaghetti_western's existing `combat` from `contest` to `conflict`.
  - Rationale: a gunfight is lethal — a Fate Conflict — consistent with the cross-pack combat=conflict rule.
  - Severity: minor
  - Forward impact: none.
- **RT1: conflict folded into the contest live-zone block, not a duplicated parallel branch**
  - Spec source: context-story-153-3.md "Server changes" / Reviewer Finding 1 fix note
  - Spec text: "Add a `conflict` Fate-live zone parallel to the contest branch (~391) —
    no native beat menu; resolution via the Fate conflict engine"
  - Implementation: rather than a duplicated `elif conflict` branch, the condition was
    widened to `resolution_mode in (contest, conflict)` and the label/resolution-line
    chosen per mode inside the one block (narrator.py `build_encounter_context`).
  - Rationale: contest and conflict are the two display-only Fate modes sharing one
    live-zone shape; one block is DRY and avoids a second copy drifting (No Stubbing /
    dead code). Both the existing contest test and the new conflict test pin the block.
  - Severity: trivial
  - Forward impact: none — a future display-only Fate mode joins the same tuple.
- **RT1: no narration_apply change — the dispatch dial leak (Finding 2) does not reproduce**
  - Spec source: Reviewer RT0 handoff ("Dev mirrors the contest M1 handling for conflict")
  - Spec text: "Add `conflict` to the `_should_gate...` exclusion (~861) + a conflict
    drop-and-log branch mirroring contest (~6403)"
  - Implementation: NOT done. A conflict always seats with
    `win_condition="fate_conflict"` (encounter_lifecycle.py:1701/1757), which the 126-37
    branch (narration_apply.py ~5974) already drops before the resolution_mode ladder.
    Verified: the TEA dispatch PIN passes, and the full server suite is green on the Fate
    paths. Adding a second resolution_mode-keyed drop would duplicate the 126-37 guard.
  - Rationale: the Reviewer's trace skipped the win_condition branch; there is no
    reachable production path where a conflict has `win_condition != "fate_conflict"`, so
    no leak to fix. Belt-and-suspenders here would be dead code (No Stubbing).
  - Severity: major
  - Forward impact: if a future non-trigger seat ever decouples conflict from
    `fate_conflict`, the TEA PIN (`test_153_3_conflict_dispatch_no_dial_leak.py`) fails
    and the gap surfaces — caught, not silent.

### Reviewer (audit)
- **Architect: new `conflict` mode instead of mapping combat to `contest`** → ✓ ACCEPTED:
  sound — a Fate Contest is explicitly no-harm; lethal combat requires a Conflict.
  But the mode introduction was INCOMPLETE — see the two blocking Reviewer findings
  (the contest-parallel narrator + dispatch handling for display-only beats was not
  carried over to conflict).
- **Architect: scope expanded to spaghetti_western (3rd pack) + combat→conflict flip** → ✓ ACCEPTED:
  the loud guard is global-to-Fate, so spaghetti_western had to port too; Keith chose "all 3".
- **TEA: AC-5 seating covered at `_requires_opponent` unit level, not end-to-end** → ✓ ACCEPTED:
  the seating routing is genuinely unchanged. (The MISS was elsewhere — the narrator/dispatch
  beat surface, which neither TEA nor Dev exercised; now caught.)
- **TEA: guard load-boundary proven via real-content load tests, not a clone-mutate fixture** → ✓ ACCEPTED:
  AC-6/7/8 drive the real loader; redundant fixture would add fragility.
- **TEA: `test_conflict_mode_rejects_armed_beats` green-by-coincidence pre-enum** → ✓ ACCEPTED:
  non-vacuous (real `raises`) and meaningful post-GREEN; verified it now rejects on the armed-beat path.
- **Dev: three sibling tests updated for the now-Fate pack shapes** → ✓ ACCEPTED:
  stale-premise tests invalidated by an intended design change; dual-dial coverage survives
  via 5 WN packs; the 126-30 seating invariant is preserved.
- **Dev: spaghetti_western combat contest→conflict (implemented)** → ✓ ACCEPTED: matches AC-8.
- **UNDOCUMENTED (Reviewer-found):** the conflict display-only-beat surface needs the SAME
  contest M1 handling (narrator zone + dispatch beat-drop). Dev's "no new span, rides existing
  seating" was true for SEATING but missed the NARRATOR + RESOLUTION surfaces. Logged as the two
  blocking Reviewer Delivery Findings. Severity: HIGH.

### Reviewer (audit, RT1)
- **TEA: Finding 2 delivered as a GREEN PIN, not a RED — the dial leak does not reproduce**
  → ✓ ACCEPTED: independently verified. My RT0 Finding 2 was WRONG — I traced the
  resolution_mode ladder and missed the 126-37 `win_condition=="fate_conflict"` branch
  (narration_apply.py:5974) that runs FIRST. A conflict always seats with
  `win_condition="fate_conflict"` (encounter_lifecycle.py:1701/1757, confirmed un-gated
  by category via the passing real-seating test). The dispatch PIN + my own probe + the
  silent-failure-hunter all converge: no dial leak for any shipped Fate pack. A RED was
  correctly not manufacturable; the GREEN PIN is the right artifact.
- **Dev: conflict folded into the contest live-zone block, not a duplicated branch**
  → ✓ ACCEPTED: DRY and correct — contest and conflict are the two display-only Fate
  modes; both the existing contest test and the new conflict test pin the block. The
  contest path is unregressed (test passes).
- **Dev: no narration_apply change — the dispatch dial leak (Finding 2) does not reproduce**
  → ✓ ACCEPTED: adding a resolution_mode-keyed drop would duplicate the 126-37
  win_condition guard (No Stubbing / dead code). The win_condition guard correctly covers
  BOTH legacy beat_selection Fate conflicts and the new conflict mode.

## TEA Assessment

**Tests Required:** Yes
**Reason:** server-side enum + validators + loud guard + a runtime `_requires_opponent`
edit; all behaviourally testable.

**Test Files:**
- `tests/genre/test_fate_conflict_mode.py` — the `conflict` mode + the loud Fate-mode
  guard, at the pydantic model layer (AC-1, AC-2, AC-3, AC-4).
- `tests/server/dispatch/test_fate_conflict_requires_opponent.py` — a Fate Conflict
  requires an Other regardless of category (AC-5).
- `tests/integration/test_153_3_fate_pack_port.py` — real-content port verification
  through `load_genre_pack` (AC-6, AC-7, AC-8, AC-9).

**Tests Written:** 14 tests covering AC-1..AC-9.
**Status:** RED — 8 failing (the new behaviour), 6 passing (regression / Fate-gating
guardrails that must stay green). Verified directly (`pytest -n0`, 1.6s):
- AC-1 conflict load → `ValidationError: input_value='conflict'` (enum absent) ✓
- AC-3 guard → `DID NOT RAISE` (native beat_selection loads on a Fate pack today) ✓
- AC-5 → `ValidationError` constructing a conflict cdef ✓
- AC-6/7/8 → `beat_selection != contest/conflict` on wry_whimsy/pulp_noir/spaghetti_western ✓

### Rule Coverage (python lang-review)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent-exceptions (guard must fail LOUD, not swallow) | `test_fate_pack_rejects_native_beat_selection` | failing (RED) |
| #6 test-quality (meaningful assertions) | self-check — every test asserts a specific value; no `assert True` / bare-truthy / `let _` | pass |
| #11 input-validation at the pack-file boundary | `test_fate_pack_rejects_native_beat_selection`, `test_non_fate_pack_keeps_native_beat_selection` | failing / passing |

**Rules checked:** 3 of 13 applicable (the change is an enum + validators + a guard;
mutable-defaults / async / resource-leak / path-handling / deserialization rules don't apply).
**Self-check:** 0 vacuous assertions found.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Implement server + content per the
context-doc design; both repos must change in the same green phase (the guard makes
unported content fail load). Honor the two TEA Delivery Findings (the `opposed_check`
message-compat constraint is blocking for the existing test).

## Dev Assessment

**Implementation:** complete (server + content, both repos).
**Status:** GREEN. All 9 ACs covered and passing. Full server suite:
**12544 passed**, 2 failures both non-regressions — `test_beneath_sunden_room_binding_107_2`
(PRE-EXISTING; fails with my changes stashed) and an xdist log-capture flake
(`test_intent_router_*` / `test_publish_event_shape` — pass in isolation).

### AC Accountability

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 conflict mode loads (display-only beats, no metric) | DONE | `test_conflict_mode_loads_with_display_only_beats_and_no_metric` |
| AC-2 contest unchanged (armed-beat + player_metric guards) | DONE | `test_contest_still_rejects_armed_beats`, `test_contest_still_requires_player_metric` |
| AC-3 loud guard rejects beat_selection + opposed_check | DONE | `test_fate_pack_rejects_native_beat_selection`, `test_fate_pack_still_rejects_opposed_check`, `tests/genre/test_fate_no_opposed_check.py` |
| AC-4 guard is Fate-gated | DONE | `test_non_fate_pack_keeps_native_beat_selection` |
| AC-5 conflict requires an Other (any category) | DONE | `test_fate_conflict_requires_opponent` (combat + social) |
| AC-6 wry_whimsy ported | DONE | `test_wry_whimsy_ported_to_contest_conflict` |
| AC-7 pulp_noir ported | DONE | `test_pulp_noir_ported_to_contest_conflict` |
| AC-8 spaghetti_western ported | DONE | `test_spaghetti_western_ported_to_contest_conflict` |
| AC-9 tea_and_murder regression | DONE | `test_tea_and_murder_still_loads_with_fate_modes` |

**Files changed:**
- server: `sidequest/genre/models/rules.py` (ResolutionMode.conflict, validator
  branches, `_fate_packs_use_fate_resolution_modes` allowlist guard, `_FATE_RESOLUTION_MODES`),
  `sidequest/server/dispatch/encounter_lifecycle.py` (`_requires_opponent`); test fixes
  in `test_pack_load.py`, `test_fate_seating_denativized_126_30.py`, `test_wry_whimsy_verbal_confrontation.py`.
- content: `genre_packs/{wry_whimsy,pulp_noir,spaghetti_western}/rules.yaml`.

**Commits:** server `2778b669` (GREEN) + `16a17d2a` (RED tests); content `3a0f75c`.
**Lint/format:** `ruff check` clean; `ruff format` applied.
**No new engine, no new span** — `conflict` rides the existing Fate-conflict seating
(`seat_as_fate_conflict`, `fate_conflict_seeded_span`).
**Handoff:** To TEA (Fezzik) for the verify phase.

## Branch Strategy
**Branch Strategy:** gitflow (feat/153-3-fate-contest-defs-loader-guard in each subrepo)

**Subrepos:**
- sidequest-server: feat/153-3-fate-contest-defs-loader-guard
- sidequest-content: feat/153-3-fate-contest-defs-loader-guard

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN — 39 targeted pass; lint + format clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A — assessed manually (enum blast-radius enumeration of every `resolution_mode` consumer) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (both HIGH) | confirmed 2 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — assessed manually (RED→GREEN verified, AC table complete) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — docstrings updated within the diff |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — assessed manually (StrEnum value, frozenset constant) |
| 7 | reviewer-security | Yes | findings | 1 (medium) | confirmed 1 (non-blocking, pre-existing) |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — assessed manually (Rule Compliance below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (2 blocking HIGH `[SILENT]`, 1 non-blocking `[SEC]`), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

The server validators, the loud guard, the content port, and the seating wiring are
sound and well-tested. But introducing `conflict` as a display-only-beat mode is
INCOMPLETE: the contest M1 work (spec 2026-06-17) gave `contest` special narrator +
dispatch handling *precisely because* its beats are display-only — and that handling
was not carried over to `conflict`, which has the same display-only beats. Net result:
a guaranteed narrator crash on every Fate conflict turn.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[SILENT]` | Conflict narrator prompt crashes: `kind={b.kind.value}` on a display-only stub (kind=None) → AttributeError | `sidequest/agents/narrator.py:434` (elif ~418) | Add a `conflict` Fate-live zone parallel to the contest branch (~391) — no native beat menu; resolution via the Fate conflict engine |
| [HIGH] `[SILENT]` | Conflict leaks the native dial: stray narrator beat → `_legacy_beat_path=True` (else ~6442) runs `apply_beat` on a stub (ADR-144 REPLACE violation) | `sidequest/server/narration_apply.py:861, ~6442` | Add `conflict` to the `_should_gate...` exclusion (~861) + a conflict drop-and-log branch mirroring contest (~6403) |
| [LOW] `[SEC]` | `ruleset` case-sensitive str — `ruleset: Fate` bypasses Fate validators (fails loud later at registry, pre-existing) | `sidequest/genre/models/rules.py` | Non-blocking — normalize ruleset to lowercase / StrEnum (separate hardening story) |

**Dispatch tags:** `[SILENT]` 2 confirmed (HIGH) · `[SEC]` 1 confirmed (LOW, non-blocking)
· `[EDGE]`/`[TEST]`/`[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]` — subagents disabled, domains
assessed manually below (no further findings).

**Data flow traced:** a seated `conflict` encounter → next turn the narrator prompt
builder (`narrator.py`) renders the live encounter → non-contest path (elif 418) →
`beat_lines` iterates `cdef.beats` doing `b.kind.value` → **crash** (kind is None).
Separately, if the prompt somehow built, a hallucinated `beat_selection` → dispatch
`else` (6442) → legacy dial `apply_beat` on a stub → ADR-144 violation. Both stem from
the same omission: conflict needs contest's display-only handling.

### Rule Compliance
- **No Silent Fallbacks (CLAUDE.md/SOUL):** the loud guard `_fate_packs_use_fate_resolution_modes`
  raises naming offenders — COMPLIANT. BUT the conflict dispatch `else` silently runs the
  dial engine on a stub — VIOLATION (Finding 2).
- **Bind the Ruleset, Don't Balance It (SOUL/ADR-143/144):** the guard removes native modes
  from Fate — COMPLIANT. BUT the conflict path lets the native dial run in parallel — VIOLATION (Finding 2).
- **lang-review #6 test-quality:** new tests assert specific values, no vacuous/`assert True` — COMPLIANT.
- **lang-review #1 silent-exceptions / #11 input-validation:** the guard fails loud at the pack-file
  boundary — COMPLIANT; `[SEC]` finding is a value-normalization gap, not a swallow.
- **lang-review #3 type annotations:** `_FATE_RESOLUTION_MODES` frozenset, `_requires_opponent` typed — COMPLIANT.

### Devil's Advocate
Assume this is broken. A player triggers the Jabberwock fight (wry_whimsy `violence`,
now `conflict`). The turn it activates, the narrator prompt builder hits
`narrator.py:434` and dies on `None.value`. The story's *entire reason for existing* —
"the Jabberwock can kill you dead" — crashes before it can kill anyone. The full suite
passed because every test seats or validates a conflict but none builds its narrator
prompt or feeds it a stray beat. A confused narrator (LLM) shown the native beat menu
(it IS shown one — finding 2) will pick a beat, and the dial engine resolves it against
a stub — the precise parallel-engine bug ADR-144 was written to kill, re-introduced for
conflict because only contest got the M1 patch. This is not a hypothetical: the contest
crash was found in live playtest (glenross 150-6, narrator.py:385); conflict has the
identical surface with zero of the protection. REJECT is the only honest verdict.

**Handoff:** Back to TEA (Fezzik) for a RED test reproducing the conflict narrator
crash + the stray-beat dial leak, then Dev mirrors the contest M1 handling for conflict.

## TEA Assessment (RT1 — rework after Reviewer REJECT)

**Tests Required:** Yes
**Reason:** reproduce the two HIGH Reviewer findings on the new `conflict` mode.

**Test Files:**
- `tests/agents/test_narrator_encounter_beats.py` — added
  `test_build_encounter_context_fate_conflict_does_not_render_native_beats` (Finding 1).
- `tests/server/test_153_3_conflict_dispatch_no_dial_leak.py` — NEW; added
  `test_seated_conflict_drops_stray_beat_and_does_not_touch_the_dial` (Finding 2 PIN).

**Tests Written:** 2. **Status: RED** (1 failing — the genuine RED; 1 GREEN PIN).
Verified directly (`pytest -n0`, 0.16s):
- **Finding 1 — narrator crash: RED (real).** A live `conflict` encounter →
  `build_encounter_context` → `narrator.py:434` `b.kind.value` on a kind=None stub →
  `AttributeError`. Reproduced exactly (probe + test both fail today). The narrator
  branch keys on `resolution_mode == contest` ONLY, so a properly-seated conflict
  (`win_condition="fate_conflict"`) still falls into the generic elif and crashes.
- **Finding 2 — dial leak: GREEN PIN (does NOT reproduce).** Measured three ways:
  (1) probe — realistic seating → opponent dial 0, `conflict_beat_dropped_dial_blocked`
  fires, no `apply_beat`; (2) seating code — `seat_as_fate_conflict`/`win_condition=
  "fate_conflict"` (encounter_lifecycle.py:1701/1757) is un-gated by category;
  (3) `test_fate_seating_denativized_126_30.py:202` already pins a conflict-mode def →
  `win_condition="fate_conflict"`. The 126-37 branch (narration_apply.py ~5974) drops
  the stray beat before the resolution_mode ladder the Reviewer's trace assumed. The PIN
  passes today and fails only if seating ever decouples conflict from `fate_conflict`.

**Why no RED for Finding 2:** the Reviewer's data-flow trace (a hallucinated beat →
`else` ~6443 → `apply_beat`) skipped the win_condition branch that runs first. There is
no reachable production path where a conflict-mode encounter has
`win_condition != "fate_conflict"`, so no honest RED exists. A redundant
resolution_mode-keyed drop would duplicate the 126-37 guard (No Stubbing). See the RT1
Design Deviation + Delivery Finding.

### Rule Coverage (python lang-review)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent-exceptions (dial engine must be loudly blocked, not silently fed) | `test_seated_conflict_drops_stray_beat_and_does_not_touch_the_dial` (asserts the `conflict_beat_dropped_dial_blocked` GM-panel event) | pass (PIN) |
| #6 test-quality (meaningful assertions) | self-check — every assertion checks a specific value (dial==0, op name, beat_id, framing strings); no `assert True` / bare-truthy / `let _` | pass |
| #11 input-validation (display-only stub beats must not reach the dial) | both new tests | RED (narrator) / pass (dispatch PIN) |

**Rules checked:** 3 of 13 applicable (this RT is a narrator-render + dispatch-drop
behavioral repro; constructor/deserialize/async/resource rules don't apply).
**Self-check:** 0 vacuous assertions.

## Delivery Findings

### TEA (test design, RT1)
- **Conflict** (blocking, for Reviewer re-review): Finding 2 (dial leak) does not
  reproduce; the narration_apply dial is protected for `conflict` by the existing 126-37
  `win_condition="fate_conflict"` drop (~5974). Evidence: probe + seating code +
  `test_fate_seating_denativized_126_30.py:202`. The only real fix this RT needs is the
  narrator crash (Finding 1). Affects `sidequest/agents/narrator.py` (Dev adds the
  conflict Fate-live zone). *Found by TEA during test design (RT1).*
- **Improvement** (non-blocking): for GM-panel coherence, a PC-side stray beat on a
  conflict is currently dropped via the SOUL consent gate (`inferred_pc_beat_rejected`)
  rather than `conflict_beat_dropped_dial_blocked`, because `conflict` is not in
  `_gate_applies_to_encounter`'s exclusion (~861). No dial leak either way; purely a
  drop-op labeling nuance. Optional: add `conflict` to that exclusion so all conflict
  beat-drops surface under one op. Affects `sidequest/server/narration_apply.py:861`.
  *Found by TEA during test design (RT1).*

**Handoff:** To Dev (Inigo Montoya) for GREEN — narrator-only fix: add a `conflict`
Fate-live zone in `build_encounter_context` parallel to the contest branch
(narrator.py ~391), no native beat menu. The dispatch PIN stays green untouched.

## Dev Assessment (RT1 — rework after Reviewer REJECT)

**Implementation Complete:** Yes (narrator-only; content already ported in RT0)

**Files Changed:**
- `sidequest/agents/narrator.py` — `build_encounter_context` now treats `conflict`
  as a display-only Fate mode alongside `contest`: widened the live-zone condition to
  `resolution_mode in (contest, conflict)` and emits a lethal "Active Fate Conflict"
  framing (4dF + ablative stress → consequences → Taken Out), skipping the native beat
  menu (the `b.kind.value` crash + ADR-144 dial re-arm). No native body for conflict.

**No change to** `narration_apply.py` (Reviewer Finding 2): a conflict seats with
`win_condition="fate_conflict"`, already drop-protected by the 126-37 branch (~5974).
Confirmed by the TEA dispatch PIN (green) + the full-suite Fate paths (green). See the
RT1 Design Deviation — adding a resolution_mode-keyed drop would duplicate 126-37.

**Tests:**
- Finding 1 RED → GREEN: `test_build_encounter_context_fate_conflict_does_not_render_native_beats` passes.
- Finding 2 PIN stays green: `test_seated_conflict_drops_stray_beat_and_does_not_touch_the_dial`.
- Contest regression intact: `test_build_encounter_context_fate_contest_does_not_render_native_beats` passes.
- Blast radius (every `build_encounter_context` caller + all fate/contest/conflict/seating tests): **115 passed, 6 skipped**.
- **Full server suite: 12547 passed, 1635 skipped, 2 failed — both non-regressions:**
  - `test_beneath_sunden_room_binding_107_2` — PRE-EXISTING (a WWN pack, unrelated to Fate; Dev RT0 confirmed it fails with changes stashed).
  - `test_59_23_materialize_other::test_ship_combat_materialized_threat_resolves_on_hull` — **xdist parallel-ordering flake; passes in isolation** (`-n0`, 1 passed). Unrelated to narrator.py (native SWN ship-combat path).
- Lint/format: `ruff check` clean; `ruff format` applied.

**Branches (pushed):**
- sidequest-server: `feat/153-3-fate-contest-defs-loader-guard` (RT1 fix `c1516f69` + TEA RED `93378a54`)
- sidequest-content: `feat/153-3-fate-contest-defs-loader-guard` (`3a0f75c`, from RT0 — unchanged this RT)

### Delivery Findings

### Dev (implementation, RT1)
- **Conflict** (non-blocking, for Reviewer): I did NOT add the requested narration_apply
  resolution_mode-keyed drop branch. Measured: Finding 2's dial leak does not reproduce
  (conflict → `win_condition="fate_conflict"` → 126-37 drop). The PIN + full suite
  confirm green. Affects `sidequest/server/narration_apply.py` (no change made — by
  design). *Found by Dev during implementation (RT1).*
- **Improvement** (non-blocking): TEA's GM-panel-coherence note (route conflict PC-beat
  drops through `conflict_beat_dropped_dial_blocked` by adding `conflict` to
  `_gate_applies_to_encounter`'s exclusion at ~861) was left unimplemented — it is a
  drop-op labeling nuance with no dial leak, out of scope for the crash fix. Affects
  `sidequest/server/narration_apply.py:861`. *Found by Dev during implementation (RT1).*

**Handoff:** To Reviewer (Westley) for re-review.

## Subagent Results (RT1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; tests GREEN (30 pass / 0 fail); branch files lint+format clean (dev baseline only); 4 packs load | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (1 MEDIUM, 1 LOW) + RT0 Finding 2 withdrawn-as-unreachable | confirmed 2 (both non-blocking), RT0 F2 withdrawn |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed manually (RT1 tests assert specific values; RED→GREEN verified) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (silent-failure-hunter caught one stale comment) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed manually (ResolutionMode StrEnum, frozenset allowlist) |
| 7 | reviewer-security | Yes | findings | 1 (LOW) + 1 pre-existing LOW | confirmed 1 (non-blocking), 1 pre-existing carried |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (narrator block is DRY — assessed manually) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — assessed manually (Rule Compliance below) |

**All received:** Yes (3 enabled returned, 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (0 blocking — 1 MEDIUM, 2 LOW), 1 pre-existing carried, 2 RT0 blockers resolved (Finding 1 fixed; Finding 2 withdrawn as unreachable)

## Reviewer Assessment (RT1)

**Verdict:** APPROVED

The RT0 REJECT had two HIGH findings. Re-reviewed with independent verification:

- **RT0 Finding 1 (narrator crash) — FIXED.** `build_encounter_context` now treats
  `conflict` as a display-only Fate mode alongside `contest` (narrator.py, condition
  `resolution_mode in (contest, conflict)`), emitting a lethal "Active Fate Conflict"
  live zone and skipping the native beat menu. The `b.kind.value` AttributeError is gone;
  `test_build_encounter_context_fate_conflict_does_not_render_native_beats` passes and the
  contest path is unregressed.
- **RT0 Finding 2 (dial leak) — WITHDRAWN. My RT0 finding was wrong.** I asserted a stray
  beat would fall into the narration_apply `else` (~6443) and hit `apply_beat`, but I
  missed the 126-37 `if enc.win_condition == "fate_conflict":` branch (~5974) that runs
  FIRST. A conflict ALWAYS seats with `win_condition="fate_conflict"`
  (encounter_lifecycle.py:1701/1757, un-gated by category). Verified three independent
  ways: (1) my own probe — seated conflict + stray beat → dial stays 0,
  `conflict_beat_dropped_dial_blocked` fires; (2) the real-seating test
  `test_fate_seating_denativized_126_30.py` (4 passed); (3) the silent-failure-hunter,
  tasked specifically to prove the leak, confirmed it UNREACHABLE for every shipped Fate
  pack. TEA/Dev were right to deliver a GREEN PIN rather than manufacture a false RED.

| Severity | Issue | Location | Disposition |
|----------|-------|----------|-------------|
| [MEDIUM] `[SILENT]` | A NON-Fate pack can author `resolution_mode: conflict` (no schema guard); it would seat with `win_condition != "fate_conflict"` and leak the dial / crash on a kind=None stub | `sidequest/genre/models/rules.py` (`_fate_packs_use_fate_resolution_modes` only constrains Fate packs) | **Non-blocking** — no live content triggers it; `contest` has the IDENTICAL pre-existing gap (verified), so this is a pattern-consistent latent footgun, not a regression. Follow-up: gate BOTH contest+conflict on `ruleset=fate` at load. |
| [LOW] `[SEC]` | `seat_as_fate_conflict` exclusion tuple omits `table_resolution` (1701); harmless today (table takes an early return at 1297) but not refactor-safe | `sidequest/server/dispatch/encounter_lifecycle.py:1701` | **Non-blocking** — defense-in-depth nit. |
| [LOW] `[SILENT]` | Stale comment: narration_apply.py:5963 says a Fate conflict "seats with the native resolution_mode (beat_selection)" — inaccurate now that `conflict` mode exists (logic still correct) | `sidequest/server/narration_apply.py:5963` | **Non-blocking** — pre-existing 126-37 comment; file untouched this RT. |
| [LOW] `[SEC]` | `ruleset` case-sensitive plain str — `ruleset: Fate` bypasses the Fate guards (fails loud later at the registry) | `sidequest/genre/models/rules.py` | **Non-blocking, pre-existing** — carried from RT0 unchanged. |

**Dispatch tags:** `[SILENT]` 2 confirmed (1 MEDIUM, 1 LOW — both non-blocking; RT0's
2 HIGH `[SILENT]` resolved) · `[SEC]` 2 confirmed (both LOW, non-blocking) ·
`[EDGE]`/`[TEST]`/`[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]` — subagents disabled, domains
assessed manually below (no further findings).

### Rule Compliance
- **No Silent Fallbacks (CLAUDE.md/SOUL):** the loud guard raises naming offenders —
  COMPLIANT. The conflict dispatch path drops stray beats loudly
  (`conflict_beat_dropped_dial_blocked`) — COMPLIANT. The non-fate footgun fails LOUD
  (runtime crash) if ever triggered, not silently — so not a blocking violation, but a
  load-time guard would be cleaner (logged non-blocking).
- **Bind the Ruleset, Don't Balance It (SOUL/ADR-143/144):** the narrator skips the
  native beat menu for conflict and the dial is removed from the Fate path (inert
  fate_stress placeholders + win_condition=fate_conflict drop) — COMPLIANT. No native
  mechanic is tuned to fit the Fate engine.
- **lang-review #6 test-quality:** RT1 tests assert specific values (dial==0, op name,
  beat_id, framing strings); no vacuous/`assert True` — COMPLIANT.
- **lang-review #3 type annotations:** `ResolutionMode` StrEnum, `_FATE_RESOLUTION_MODES`
  frozenset — COMPLIANT.
- **No Source-Text Wiring Tests:** the dispatch PIN drives the real
  `_apply_narration_result_to_snapshot` and asserts behavior + the OTEL drop op — COMPLIANT.

### Devil's Advocate
Assume it is still broken. A player triggers the Jabberwock (wry_whimsy `violence`,
`conflict`). RT0's crash is gone — verified the narrator now renders the Fate-Conflict
zone, not the native menu. Could a stray hallucinated beat still hit the dial? No — the
encounter seats `win_condition="fate_conflict"`, and the 126-37 branch drops the beat
before the ladder; I drove this myself and the dial stayed 0. Could the combined
contest/conflict block break contest? No — the contest test passes and the contest
text/label is preserved by the `if mode == contest` arm. The one genuine soft spot is a
FUTURE author writing `resolution_mode: conflict` on a non-Fate pack — that bypasses the
win_condition coupling and would crash. But (a) no content does this, (b) `contest` has
the same gap and shipped long ago, and (c) the enum is documented "Fate packs only." That
is a hardening follow-up, not a defect in what this story ships. Every shipped Fate pack
(wry_whimsy 6, pulp_noir 3, spaghetti_western 5, tea_and_murder 5) loads, uses Fate modes,
carries no armed beats on contest/conflict defs (verified), and resolves through the Fate
engine. The work is correct. APPROVE is the honest verdict — and I am eating my own RT0
Finding 2, which was an assert-don't-measure error on my part.

**Data flow traced:** player action → IntentRouter → confrontation seat
(`instantiate_encounter_from_trigger`, conflict → `seat_as_fate_conflict=True` →
`win_condition="fate_conflict"`) → narrator turn (`build_encounter_context` → Fate-Conflict
live zone, no native menu) → any stray beat → narration_apply 5974 drop → Fate engine
resolves. No dial leak end-to-end.

### Delivery Findings

### Reviewer (code review, RT1)
- **Improvement** (non-blocking): no schema guard prevents a NON-Fate pack from authoring
  `resolution_mode: conflict` (or `contest`) — such a pack would seat off the Fate path
  and leak/crash the native dial. No live content triggers it; `contest` shares the gap.
  Affects `sidequest/genre/models/rules.py` (add a `conflict`+`contest`-require-fate guard,
  symmetric to the existing Fate-mode allowlist). *Found by Reviewer during code review (RT1).*
- **Improvement** (non-blocking): `seat_as_fate_conflict` exclusion tuple omits
  `table_resolution` (harmless today via the early return at 1297; not refactor-safe).
  Affects `sidequest/server/dispatch/encounter_lifecycle.py:1701`. *Found by Reviewer during code review (RT1).*
- **Improvement** (non-blocking): stale comment at `narration_apply.py:5963` describes a
  Fate conflict as seating via `beat_selection` — inaccurate now that `conflict` mode
  exists (logic is correct). Affects `sidequest/server/narration_apply.py:5963`.
  *Found by Reviewer during code review (RT1).*

**Handoff:** To SM (Vizzini) for finish-story.