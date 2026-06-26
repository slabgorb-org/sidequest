---
story_id: "158-32"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-32: Literary NPC name-shuffle corrupts canon — source='world' proper nouns run through ADR-091 shuffle_fallback fracture into multiple registry identities; must be name-locked

## Story Details
- **ID:** 158-32
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-26T11:41:12Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-26T08:30:17+00:00 | 2026-06-26T08:32:16Z | 1m 59s |
| red | 2026-06-26T08:32:16Z | 2026-06-26T10:43:30Z | 2h 11m |
| green | 2026-06-26T10:43:30Z | 2026-06-26T11:24:01Z | 40m 31s |
| review | 2026-06-26T11:24:01Z | 2026-06-26T11:30:43Z | 6m 42s |
| red | 2026-06-26T11:30:43Z | 2026-06-26T11:34:47Z | 4m 4s |
| green | 2026-06-26T11:34:47Z | 2026-06-26T11:37:21Z | 2m 34s |
| review | 2026-06-26T11:37:21Z | 2026-06-26T11:41:12Z | 3m 51s |
| finish | 2026-06-26T11:41:12Z | - | - |

## Sm Assessment

**Routing:** Setup complete → handoff to TEA (Igor) for the `red` phase.

**Story shape:** 3 pts, tdd, p2 bug. Single-repo (`sidequest-server`). Root cause is in the server's ADR-091 naming/registration pipeline — `source='world'` proper nouns are passed through `shuffle_fallback` (Markov mint) instead of being name-locked, fracturing one canonical antagonist into multiple registry identities.

**Reproduction anchor (for TEA's red test):** Playtest pingpong 2026-06-25, heavy_metal/barsoom, session `2026-06-25-barsoom-84c17bdf`, turns 3–4. OTEL: `npc.invented_name_routed original='Salensus Oll' minted='Dentos Foun' culture='Yellow Martian' source='world' strategy='shuffle_fallback'` → `npc.auto_registered name='Dentos Foun'`. Canonical `Salensus Oll` ended up nowhere in the registry; `npc_pool=['Kantos Vah','Neon Sill','Dentos Foun']`.

**Acceptance criteria to drive tests:**
1. `source='world'` proper nouns are name-locked — never run through `shuffle_fallback`/Markov mint.
2. A canonical world name (e.g. `Salensus Oll`) registers exactly once under its canonical form; no minted/disposition variant fracture.
3. OTEL span proves the name-lock path is taken for `source='world'` names (OTEL Observability Principle — GM panel must verify the lock engaged).
4. Regression test reproducing the barsoom turn 3–4 fracture, then proving resolution to a single registry identity.

**Guardrails for downstream agents:**
- Whole-world canon coverage matters: barsoom and every canon-proper-noun world (Dejah Thoris, Tars Tarkas, Helium, Zodanga) — fix at the pipeline, not per-world.
- Latent seating hazard: a phantom minted identity could be seated if WWN combat ever targets the jeddak (ties to FATE/OTHER-seating, ADR-143/151). Keep the lock upstream of registration so seating sees the canonical identity.
- Related: 158-28. Memory refs: `three-divergent-slug-rules`, `npc-reference-recency-scene-guard`.

**No code read by SM** — implementation discovery is TEA/Dev's lane.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — a playtest regression with a concrete reproducible root cause.

**Test Files:**
- `sidequest-server/tests/server/test_authored_npc_roster_loads_158_32.py` — content
  conformance (barsoom/evropi rosters load), loader fail-loud (No-Silent-Fallbacks),
  and the end-to-end fracture regression (preload + Step-1 reconcile, no shuffle).

**Tests Written:** 5 (4 RED + 1 positive control) covering the 4 ACs of the operator-chosen
fix shape ("Content + loader fail-loud", 2026-06-26).
**Status:** RED — verified via testing-runner (`158-32-tea-red-pivot`):
- `test_barsoom_authored_roster_loads_with_canon_names` → FAIL (`world.authored_npcs == []`)
- `test_evropi_authored_roster_loads_non_empty` → FAIL (`== []`)
- `test_loader_fails_loud_on_npcs_yaml_unrecognized_top_level_key` → FAIL (`DID NOT RAISE` — loader silently returns [])
- `test_barsoom_canon_name_does_not_fracture_after_preload` → FAIL (precondition: roster empty)
- `test_loader_accepts_well_formed_npcs_yaml` → PASS (positive control: the loud guard must stay targeted)

### Rule Coverage
| Rule (python lang-review) | Test(s) | Status |
|---------------------------|---------|--------|
| #1 silent exceptions / No Silent Fallbacks | `test_loader_fails_loud_on_npcs_yaml_unrecognized_top_level_key` | RED (failing) |
| #6 test quality (no vacuous, positive control) | `test_loader_accepts_well_formed_npcs_yaml` + meaningful asserts across suite | pass |

**Rules checked:** 2 of 13 applicable lang-review rules have direct test coverage (this is a
content-load + fail-loud story; most rules — async, resource leaks, deserialization — don't apply).
**Self-check:** 0 vacuous tests (every test asserts a specific value/raise; positive control included).

**Implementation pointers for Dev (Ponder):**
- Content: rewrite `sidequest-content/genre_packs/heavy_metal/worlds/{barsoom,evropi}/npcs.yaml`
  → top-level key `npcs:`, entries conforming to `AuthoredNpc` (`extra="forbid"`; map
  `disposition:` string → `initial_disposition: int`, fold `culture`/`location`/`goals` into
  `location_tags`/`history_seeds` or drop). Mirror a working world (e.g. wonderland/npcs.yaml).
- Server: `sidequest/genre/loader.py` (~line 1616) — `npcs_raw.get("npcs", [])` must fail loud
  when a present npcs.yaml yields zero authored NPCs / carries an unrecognized top-level key,
  naming the world. Emit/keep the `npc.authored_loaded` preload spans (already exist).
- Then the EXISTING `preload_authored_npcs` + Step-1 article-fold reconcile handles the fracture —
  do NOT add a new mint-seam lock (that mechanism was considered and rejected by the operator).
- SEQUENCING: land content + loader together. Loud loader before content rewrite breaks every
  heavy_metal-loading test.

**Handoff:** To Dev (Ponder Stibbons) for GREEN.

### TEA Rework (review round 1)

**Trigger:** Reviewer REJECT — HIGH finding: the loader guard catches a *missing* `npcs:` key but a present-but-`null` `npcs:` (`None or []`) silently loads empty, and a non-list `npcs:` raises a world-anonymous error.

**Tests added** (to `tests/server/test_authored_npc_roster_loads_158_32.py`, Group B):
- `test_loader_fails_loud_on_null_npcs_value` — bare `npcs:` (→ `None`) must raise a world-named error.
- `test_loader_fails_loud_on_non_list_npcs_value` — `npcs:` as a mapping/non-list must raise a **world-named** `GenreLoadError`.

**Status:** RED — verified via testing-runner (`158-32-tea-red-rework`): 5 passed (existing, against Dev's live fix), 2 failed:
- `test_loader_fails_loud_on_null_npcs_value` → FAIL (`DID NOT RAISE` — loader does `None or []`).
- `test_loader_fails_loud_on_non_list_npcs_value` → FAIL (raises bare pydantic `ValidationError` naming neither world nor file).

**Dev target:** at `loader.py:1635`, after the existing key guard, validate the `npcs:` value — `None` and non-list must raise a world-named `GenreLoadError`; only an explicit `npcs: []` (empty list) loads clean. ~3 lines, resolves both findings.

**Handoff:** To Dev (Ponder Stibbons) for GREEN (rework).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-content/genre_packs/heavy_metal/worlds/barsoom/npcs.yaml` — rewritten to the
  `AuthoredNpc` schema (`npcs:` key; `location`→`location_tags`, `disposition` string→
  `initial_disposition` int per ADR-020, `goals`+`timeline`→`history_seeds`, `culture` folded
  into role prose). All 10 NPCs preserved (Salensus Oll, Kantos Vah, …).
- `sidequest-content/genre_packs/heavy_metal/worlds/evropi/npcs.yaml` — same conversion. All 13
  NPCs preserved (Srárný Fyzioloniązka, Ebbe, …).
- `sidequest-server/sidequest/genre/loader.py` — fail loud (`GenreLoadError`, names the world) when
  a present `npcs.yaml` carries no top-level `npcs:` key; explicit `npcs: []` stays valid.
- `sidequest-server/tests/fixtures/packs/wwn_test_pack/worlds/test_world/npcs.yaml` — conformed to
  `npcs: []` (was the same malformed `authored_npcs:` shape; no test reads its roster).
- `sidequest-server/tests/server/test_authored_npc_roster_loads_158_32.py` — ruff-format only.

**Tests:** 5/5 story tests GREEN. Loads verified: heavy_metal barsoom=10, evropi=13 authored NPCs;
tea_and_murder/pulp_noir (scenario-tier npcs.yaml, different loader path) still load. Previously-
broken `test_wwn_heavy_metal_chargen` + `test_120_4_world_equipment_tables_override` (the
`wwn_test_pack` fixture) restored to green.

**Regression verification (rigorous — the testing-runner helper initially mislabeled a real
regression as pre-existing, so I confirmed by stash-diff):**
- Full suite stable pre-existing failures = **48** (OTEL span wiring, WWN spell-dispatch, beneath_sunden
  cavern, mutant_wasteland mutation — all ADR-087 territory, none touch genre loading / npcs / preload).
  Baseline = 52 (48 + the 4 RED 158-32 tests); my changes = 48 (4 RED→GREEN, 0 new deterministic).
- Loader-change blast radius is fully contained: the ONLY world-tier `npcs.yaml` lacking `npcs:` were
  barsoom, evropi, and the wwn_test_pack fixture — all three fixed. The 4 scenario-tier `npcs.yaml`
  (tea_and_murder, pulp_noir) load via the separate ScenarioNpc path and are unaffected (verified).

**OTEL:** No new span needed — the fix's effect is observable via the existing `npc.authored_loaded`
(preload) and `pregen.seed_manual`/`authored_npcs_seeded` spans, which now fire non-zero for
barsoom/evropi (they reported nothing while the rosters loaded empty). The loader fail-loud is a hard
`GenreLoadError` (loud by construction).

**Branches:** `sidequest-server@feat/158-32-name-lock-world-proper-nouns` (pushed),
`sidequest-content@feat/158-32-heavy-metal-authored-npc-rosters` (pushed). NOTE: the server branch name
predates the mechanism pivot (it says "name-lock"); the work is content+loader, not a name-lock.

**Handoff:** To Reviewer (Granny Weatherwax) — **two-repo review** (server + content).

### Dev Rework (review round 1)

**Reviewer HIGH/MEDIUM finding addressed.** At `loader.py`, after the missing-key guard, the `npcs:` value is now validated: `npcs_list_raw = npcs_raw["npcs"]`, and `if not isinstance(npcs_list_raw, list): raise GenreLoadError(world-named, "the \`npcs:\` key must be a list …")`. This makes BOTH the null case (`npcs:` → `None`, not a list → raises) and the non-list case (mapping/scalar → raises world-named) fail loud — the `or []` swallow is gone. An explicit `npcs: []` (empty *list*) remains the sole sanctioned empty roster.

**Tests:** 7/7 story tests GREEN (the two rework tests now pass) — verified via testing-runner (`158-32-dev-green-rework`). 32/32 affected-regression tests pass (`test_npc_article_fold_match`, WWN chargen, equipment, pregen placement). All 11 genre packs load under the stricter check (verified) — no world authors a null/non-list `npcs:`, so zero blast radius. Lint + format clean.

**Handoff:** Back to Reviewer (Granny Weatherwax) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A (lint PASS, story 5/5, regression 25/25, barsoom=10/evropi=13) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (edge cases covered by Reviewer — see Rule Compliance) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (1 high, 1 medium) | confirmed 2, dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test quality assessed by Reviewer below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A (safe_load #8, no traversal #11/#5, no info-leak — trusted local content) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (rule-by-rule done by Reviewer below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed (1 HIGH, 1 MEDIUM), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED (round 1 — ✓ RESOLVED in round 2; see "Reviewer Re-Review — Round 2" below; final verdict is APPROVED)

The content rewrite (barsoom 10 + evropi 13 NPCs, all ids/names/prose preserved, schema-conformant) and the loader fail-loud are correct **for the cases the tests cover** — but the fix is **incomplete against its own stated principle**. The loader's guard catches a *missing* `npcs:` key, yet a *present-but-null* `npcs:` (the bare `npcs:` / wrong-indent typo) still slides through `None or []` to a silently-empty roster — the very silent-fallback class this story exists to eliminate. That is a No-Silent-Fallbacks violation (CLAUDE.md `<critical>`), confirmed both by the silent-failure-hunter and by my own probe.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT] | `npcs:` present but null (bare `npcs:`/wrong-indent) → `npcs_raw.get("npcs") or []` yields `[]` → roster silently lost. Re-creates the exact silent-empty-roster the story fixes; violates No Silent Fallbacks and the operator requirement "a present npcs.yaml … must raise a LOUD, world-named error — never silently produce an empty roster." | `sidequest-server/sidequest/genre/loader.py:1635` | After the key guard, read `val = npcs_raw["npcs"]`; treat `None` as deliberate-empty **or** raise a world-named `GenreLoadError` — but make the null branch explicit, not an `or []` swallow. |
| [MEDIUM] [SILENT] | `npcs:` mapped to a non-list (`npcs: 42`, a string, a dict) is truthy, so `or []` passes it through; the comprehension then raises a pydantic/`TypeError` that names neither the file nor the world — undermining the "world-named error" requirement. | `sidequest-server/sidequest/genre/loader.py:1635-1636` | Add `if not isinstance(val, list): raise GenreLoadError(path=f"worlds/{world_path.name}/npcs.yaml", detail="`npcs:` must be a list …")` before validating elements. |

Both findings collapse into one ~3-line fix at the same site.

**Observations (evidence-cited):**
- [HIGH] [SILENT] `npcs: null` → empty roster — proven: `yaml.safe_load("npcs:")` → `{'npcs': None}`, guard at loader.py:1624 sees the key present, `None or []` → `[]`. loader.py:1635.
- [MEDIUM] [SILENT] non-list `npcs:` value → loud but world-anonymous error. loader.py:1635-1636.
- [VERIFIED] The targeted regression (wrong key `authored_npcs:`) IS caught — `yaml.safe_load` of the barsoom-shape file has no `npcs` key → guard raises `GenreLoadError` naming the world. loader.py:1624-1632; proven by `test_loader_fails_loud_on_npcs_yaml_unrecognized_top_level_key` (green). Complies with No Silent Fallbacks for THIS case.
- [VERIFIED] [SEC] YAML parsing is safe — `_load_yaml_raw` uses `yaml.safe_load` (loader.py:199); no eval/pickle; lang-review #8 satisfied. Diacritic-heavy evropi names round-trip intact (`Srárný Fyzioloniązka`, `Ndiziały Zblášzed`, `Glang u Mäinkin empi Gaml`).
- [VERIFIED] Content faithfulness — all 10 barsoom + 13 evropi ids AND names preserved vs the develop source; `initial_disposition` in range (barsoom −60..25, evropi −35..20 ⊂ [−100,100]); one `location_tags` per NPC; zero leftover forbidden keys (culture/location/disposition/goals/timeline) → AuthoredNpc `extra="forbid"` satisfied (and the pack loads).
- [VERIFIED] Blast radius contained — the loader change only governs world-tier `worlds/<slug>/npcs.yaml`; scenario-tier `scenarios/<s>/npcs.yaml` (tea_and_murder, pulp_noir) use the separate ScenarioNpc path and still load. The only world-tier offenders (barsoom, evropi, wwn_test_pack fixture) are all fixed.
- [VERIFIED] [TEST] Test quality (test_analyzer disabled — assessed here): the 5 story tests assert specific values/raises, no vacuous assertions; the positive-control `test_loader_accepts_well_formed_npcs_yaml` proves the guard is targeted. GAP: no test covers `npcs: null` or a non-list `npcs:` — exactly the HIGH finding above (this is why it slipped).

**Disabled-subagent domains (covered by Reviewer):**
- [EDGE] Boundary enumeration of the `npcs:` value space (missing-key / null / non-list / bare-list / empty-file / explicit-`[]`) IS the analysis behind the HIGH+MEDIUM findings — the null and non-list boundaries are unhandled. loader.py:1624-1636.
- [DOC] The new loader comment (loader.py:1616-1623) and the rewritten content YAML headers accurately describe the schema and the regression; no stale/misleading docs introduced.
- [TYPE] No new types or signatures; the `AuthoredNpc` model (`extra="forbid"`) is unchanged and correctly enforced. No stringly-typed API or unsafe cast added.
- [SIMPLE] The guard is appropriately minimal; the only complexity smell is the `or []` shortcut — which is an *over*-simplification that drops the null/non-list cases (the HIGH finding), not excess complexity.
- [RULE] Exhaustive rule mapping in the `### Rule Compliance` section below — #1 and #11 fail until the null/non-list guard lands; #3/#4/#5/#8 compliant.

### Rule Compliance (lang-review/python.md — enumerated against the diff)
- **#1 silent exceptions / No Silent Fallbacks:** the new `raise` is loud and typed; `_load_yaml_raw` catches only `OSError`/`yaml.YAMLError`. **BUT** `or []` on `npcs: null` is a silent default → **VIOLATION** (the HIGH finding). Verdict: fail until fixed.
- **#3 type annotations:** no new public signatures; change is inside `_load_single_world`. Compliant.
- **#4 logging/error severity:** fail-loud via `GenreLoadError` (load-time config error → raise is correct; no mis-leveled log). Compliant.
- **#5 path handling:** `world_path / "npcs.yaml"`, `read_text(encoding="utf-8")`. Compliant.
- **#8 unsafe deserialization:** `yaml.safe_load`. Compliant.
- **#11 input validation at boundary:** partially — the missing-key case is validated; the present-but-null and present-but-non-list cases are NOT (the two findings). Verdict: fail until fixed.

### Devil's Advocate
Assume this loader change is broken. The story's banner is "no present npcs.yaml ever silently loads an empty roster." So the adversary's job is to find a present npcs.yaml that loads empty without a peep — and it exists. A content author (Jade, per CLAUDE.md — a *non-Keith* author on a paste-in/PR path, explicitly the person this homebrew-authoring surface must serve) opens wonderland's npcs.yaml as a template, types `npcs:`, and either forgets to paste the list or pastes it at the wrong indent so PyYAML reads the value as `null`. Result: `{'npcs': None}` → guard sees the key → `None or []` → her entire authored cast vanishes with no error, and her canon NPCs fracture into procedural mints in play — the identical failure mode, the identical silent path, that burned barsoom. The loud guard gives a false sense of completeness: it slams the front door (`authored_npcs:`) while leaving the side window (`npcs:` null) open. Worse, if she instead writes `npcs: {ebbe: ...}` (a mapping, mistaking the shape), the `or []` passes the dict through and she gets a pydantic error that says `AuthoredNpc.model_validate` failed on `'ebbe'` — no filename, no world name, no hint she's in evropi's npcs.yaml. For a story whose explicit deliverable is a *world-named, loud* failure on a malformed roster file, two of the three malformation shapes (null value, wrong-typed value) miss that bar. The content half is solid and faithful; the loader half is 80% there. The remaining 20% is the whole point of the story. A confused author is not an edge case here — the homebrew-authoring audience is a first-class design constraint. Reject, add the null/non-list test, finish the guard.

**Handoff:** Back to TEA (Igor) — add a failing test for `npcs: null` / non-list `npcs:` raising a world-named `GenreLoadError`, then Dev completes the guard.

## Reviewer Re-Review — Round 2

**Final Verdict:** APPROVED

The round-1 HIGH + MEDIUM findings are fully resolved. The reworked loader (loader.py) now reads `npcs_list_raw = npcs_raw["npcs"]` then `if not isinstance(npcs_list_raw, list): raise GenreLoadError(world-named, "the \`npcs:\` key must be a list … got {type}")`. The `or []` swallow is gone; an explicit `npcs: []` (empty list) is the only sanctioned empty roster.

**Re-run subagents (3 enabled, on the reworked diff):**

| # | Specialist | Received | Status | Decision |
|---|-----------|----------|--------|----------|
| 1 | reviewer-preflight | Yes | clean | 7/7 story + 32/32 regression + all 11 packs load + lint clean |
| 3 | reviewer-silent-failure-hunter | Yes | clean | confirmed prior HIGH+MEDIUM resolved; `or []` gone; null/non-list raise world-named; `npcs: []` loads clean; no new swallow |
| 7 | reviewer-security | Yes (re-assessed) | clean | unchanged surface — same `_load_yaml_raw`/`safe_load`; new error string interpolates only a builtin `type(...).__name__`, no attacker data; prior clean result holds |

**All received:** Yes (3 enabled re-run clean; the 6 disabled remain Skipped per `workflow.reviewer_subagents`)

**Verification observations (round 2):**
- [SILENT] [VERIFIED] `or []` swallow removed; `npcs: null` → `None` fails `isinstance(_, list)` → world-named `GenreLoadError`. loader.py (npcs block). Confirmed by silent-failure-hunter + my own trace.
- [EDGE] [VERIFIED] Full `npcs:` value space now covered: missing-key→raise, null→raise, non-list(mapping/scalar)→raise, `[]`→clean-empty, `[entries]`→loads. The positive-control `test_loader_accepts_well_formed_npcs_yaml` + the two new `npcs:null`/non-list tests pin all branches.
- [TEST] [VERIFIED] The two rework tests assert a `pytest.raises` AND that the message names the world/file — not vacuous. 7/7 green.
- [VERIFIED] No blast radius: all 11 genre packs load under the stricter list check (re-confirmed by preflight); no world authors a null/non-list `npcs:`.
- [SEC] [TYPE] [DOC] [SIMPLE] [RULE] No new concerns — the change is a single `isinstance` guard + a typed `raise`; the loader comment accurately documents the null/non-list/`[]` distinction; `AuthoredNpc` unchanged; No-Silent-Fallbacks (#1) and input-validation (#11) now FULLY satisfied (the round-1 fail is cleared).

**Data flow traced:** a malformed `worlds/<slug>/npcs.yaml` (`authored_npcs:` / `npcs: null` / `npcs: <mapping>`) → `_load_yaml_raw` (safe_load) → guard → world-named `GenreLoadError` at load (loud), never a silent empty roster reaching `preload_authored_npcs` → game state.

**Handoff:** To SM (Captain Carrot) for finish-story — **two-repo merge** (sidequest-server + sidequest-content).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): The story's root cause is mis-diagnosed. It is NOT a server name-lock gap — `heavy_metal/worlds/{barsoom,evropi}/npcs.yaml` use top-level key `authored_npcs:` with non-`AuthoredNpc` fields, so `world.authored_npcs` loads `[]`. Affects `sidequest-content/genre_packs/heavy_metal/worlds/{barsoom,evropi}/npcs.yaml` (rewrite to `npcs:` + AuthoredNpc schema). *Found by TEA during test design.*
- **Gap** (blocking): No-Silent-Fallbacks violation in the loader — `npcs_raw.get("npcs", [])` swallows a present-but-malformed npcs.yaml instead of failing loud (this is why the defect reached a playtest). Affects `sidequest-server/sidequest/genre/loader.py` (~line 1616). *Found by TEA during test design.*
- **Question** (blocking): The sprint story is tagged `repos: server`, but the fix REQUIRES the `content` repo (barsoom/evropi npcs.yaml). Only `sidequest-server` has a feature branch; a `sidequest-content` branch is needed too. Affects sprint story `repos` field + branch setup — SM/Dev to reconcile. *Found by TEA during test design.*
- **Improvement** (non-blocking): The loader fail-loud and the content rewrite are one atomic change. Landing the loud loader before the content rewrite makes `load_genre_pack(heavy_metal)` raise and breaks every existing heavy_metal-loading test. Affects Dev's commit ordering. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `test_pregen_bestiary_90_1::test_seed_manual_populates_encounters_for_wwn_world[evropi]` is a PRE-EXISTING FLAKY test — `_generate_encounter` shells out to encountergen which runs with its OWN unseeded randomness (the test's `random.Random(901)` is never threaded into it), so the encounter pool can intermittently come back empty under full-suite/xdist load (isolated: 4/4 pass; full suite: failed 1 run, passed others; baseline full suite also passed it). Not caused by this change deterministically, but evropi's now-non-empty roster may perturb its flake odds. Affects `sidequest-server/sidequest/server/dispatch/pregen.py::_generate_encounter` (thread a seed into encountergen) — a separate test-determinism story. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The `sidequest-server` feature branch is named `feat/158-32-name-lock-world-proper-nouns`, which predates the mechanism pivot (the fix is content+loader, not a name-lock). Cosmetic; the PR title/body should describe the actual change. Affects branch/PR naming only. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The loader fail-loud guard is incomplete — a present-but-`null` `npcs:` (`npcs_raw.get("npcs") or []`) and a present-but-non-list `npcs:` both bypass the loud path, re-creating the silent-empty-roster the story exists to eliminate (No Silent Fallbacks). Affects `sidequest-server/sidequest/genre/loader.py:1635` (validate the `npcs:` value: `None`→explicit-empty branch, non-list→world-named `GenreLoadError`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): TEA's RED suite lacks coverage for the `npcs: null` / non-list `npcs:` cases — add them so the No-Silent-Fallbacks guarantee is fully pinned. Affects `sidequest-server/tests/server/test_authored_npc_roster_loads_158_32.py`. *Found by Reviewer during code review.*
- **(Round 2)** Both Reviewer findings above are RESOLVED — the rework added the value-validation guard + the two missing-edge tests. No new upstream findings during re-review. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Fix mechanism pivoted from "server name-lock" to "content + loader fail-loud"**
  - Spec source: context-story-158-32.md (story title + Problem); story `repos: server`
  - Spec text: "source='world' proper nouns are run through ADR-091 shuffle_fallback instead of being name-LOCKED ... need source='world' names locked."
  - Implementation: Tests target the actual root cause — barsoom/evropi `npcs.yaml` load an empty authored roster (wrong top-level key + non-conforming entries) — via content-conformance + loader fail-loud + a preload/Step-1-reconcile end-to-end regression. NO new mint-seam canon lock is built.
  - Rationale: TEA investigation proved the authored rosters never load (`world.authored_npcs == []`); a server-only mint-seam lock sourced from `world.authored_npcs` would have an empty catalog and could not fix barsoom. Operator chose "Content + loader fail-loud" (AskUserQuestion, 2026-06-26).
  - Severity: major
  - Forward impact: story scope expands into the `heavy_metal` content repo; `repos: server` alone is insufficient (see blocking Question finding). The existing `preload_authored_npcs` + article-fold machinery — not new code — is the runtime fix.
- **(Rework r1) Pinned `npcs: null` → RAISE (malformed), with `npcs: []` reserved as the ONLY sanctioned empty roster**
  - Spec source: Reviewer Assessment HIGH finding + CLAUDE.md `<critical>` No Silent Fallbacks
  - Spec text: reviewer offered "treat `None` as deliberate-empty OR raise"; operator requirement: "a present npcs.yaml that yields zero authored NPCs must raise a LOUD, world-named error — never silently produce an empty roster."
  - Implementation: `test_loader_fails_loud_on_null_npcs_value` asserts a bare `npcs:` (→ `None`) RAISES a world-named error; `test_loader_fails_loud_on_non_list_npcs_value` asserts a mapping/non-list value RAISES world-named. The positive control (`npcs: []` loads clean) is unchanged.
  - Rationale: a null value is ambiguous and most often a typo (key written, list forgotten/mis-indented); the principle says a present file yielding zero must fail loud. Reserving `npcs: []` as the only sanctioned empty keeps deliberate-empty distinguishable from accidental-empty.
  - Severity: minor
  - Forward impact: Dev must make the null branch RAISE (do NOT treat `npcs: null` as empty); the non-list branch must raise a world-named `GenreLoadError`. ~3 lines at loader.py:1635.

### Dev (implementation)
- **Loader raises on a MISSING `npcs:` key, not on a "yields-zero" roster**
  - Spec source: 158-32 session — TEA test-design contract (Group B) + `test_loader_fails_loud_on_npcs_yaml_unrecognized_top_level_key`
  - Spec text: "a present npcs.yaml that yields zero authored NPCs (e.g. the list sits under an unrecognized top-level key) must raise a LOUD, world-named error."
  - Implementation: the loud guard fires when `npcs_raw` is not a mapping OR has no top-level `npcs:` key. An explicit `npcs: []` (key present, empty list) is HONORED as an authored "no NPCs" choice rather than raising.
  - Rationale: "no `npcs:` key" is the precise signature of the real defect (list under `authored_npcs:`); allowing explicit `npcs: []` lets a world legitimately ship an empty roster without the loud guard misfiring (and the `wwn_test_pack` fixture uses exactly this). Matches TEA's passing positive-control test; no failing test requires raising on explicit `npcs: []`.
  - Severity: minor
  - Forward impact: none — both interpretations satisfy the story's tests; this is the narrower, lower-false-positive rule.

### Reviewer (audit)
- **TEA's "Fix mechanism pivoted from server name-lock to content + loader fail-loud"** → ✓ ACCEPTED by Reviewer: the root-cause re-diagnosis is correct and operator-confirmed (AskUserQuestion 2026-06-26); the runtime fix correctly reuses existing preload/reconcile machinery rather than adding a mint-seam lock.
- **Dev's "Loader raises on a MISSING `npcs:` key, not on a 'yields-zero' roster"** → ✗ FLAGGED by Reviewer (round 1) → ✓ RESOLVED (round 2): the rework added a `npcs:`-value list-check so null and non-list values now raise a world-named `GenreLoadError`; only explicit `npcs: []` loads empty. The flagged gap is closed.
- **(Rework r1) TEA's "Pinned `npcs: null` → RAISE, with `npcs: []` reserved as the only sanctioned empty roster"** → ✓ ACCEPTED by Reviewer: the right call — null is ambiguous/typo-prone, so reserving `[]` as the sole explicit-empty form keeps deliberate-empty distinguishable from accidental-empty and fully honors No Silent Fallbacks. Implemented and verified green.