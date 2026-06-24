---
story_id: "158-20"
jira_key: ""
epic: "158"
workflow: "trivial"
---
# Story 158-20: WWN bestiary-curation recipe — generalize the beneath_sunden pattern (world_register genre-truth gate → tone curation → WWN stat ladder → pack-validate) as the per-world contract + reusable tooling

## Story Details
- **ID:** 158-20
- **Jira Key:** (none — content validation story; no Jira)
- **Workflow:** trivial (phased: setup → implement → review → finish)
- **Stack Parent:** none
- **Epic:** 158 — Playtest sweep follow-ups
- **Points:** 2 | **Priority:** p3 | **Type:** chore

## Acceptance Criteria

### AC-1: Per-world bestiary contract documented
Document the four-stage WWN bestiary-curation recipe as a formal **per-world contract**. The contract must specify:

1. **Fidelity Statement (world_register gate):** The narrative register, tone constraints, allowed creature types, denied types/tags/name-globs, humanoid-only constraints, reskinning rules, and marquee exemptions (ADR-014 Diamonds-and-Coal). Reference beneath_sunden's pattern as the proven instance.

2. **Tone Curation:** The process of selecting and filtering SRD/stat blocks against the fidelity statement and resolving CR→level conversions for the target world's ruleset.

3. **WWN Stat Ladder:** The canonical SRD conventions for the target ruleset (level == HD, hp == average per HD, ascending AC, attack_bonus, morale ladder, save formula). Document per-ruleset variations (WWN vs. CWN vs. SWN if applicable).

4. **Pack-Validate Gate:** Proof that the curated pack passes `load_genre_pack` (the real wiring gate, stronger than `validate pack`; see project doctrine in MEMORY.md). The gate must verify both the world_register schema and that no denied entries appear in the final bestiary.

The contract document should live in `sidequest-content/docs/` (new or update existing bestiary-curation docs) and be referenced from the recipe itself.

### AC-2: Reusable tooling
Deliver at least one Python script in `sidequest-content/tools/` that supports applying the contract to a new world's bestiary. Tooling must:

- Accept a world slug and bestiary input (SRD-sourced YAML or CSV) as parameters
- Apply the world_register fidelity gate (deny/allow filters)
- Validate CR→level conversions for the target ruleset module (via the ruleset's documented ladder)
- Output a curated bestiary.yaml ready for pack-validate and load_genre_pack
- Audit and document any dropped/reskinned entries with reason (tone, type, tag, name_glob mismatch, CR conversion edge case)

The script should exercise itself against the beneath_sunden world_register and bestiary as proof of concept (no new fixtures required; use the existing curated-live pack).

### AC-3: Reference documentation
Create or update a cookbook design doc (reference prior art: `docs/superpowers/specs/2026-06-12-beneath-sunden-wwn-port-design.md` and `docs/superpowers/specs/completed/2026-05-16-beneath-sunden-content-cookbook-design.md`) documenting the generalized recipe for stories 158-21..25 to follow. The doc must include:

- The four-stage contract with beneath_sunden as the reference instance
- The world_register schema (per world.yaml YAML anchor or inline)
- Example CR→level conversions for each target ruleset (WWN, CWN, SWN if mixed)
- The deny/allow/reskin audit trail template so each world story documents its choices
- Pointer to the tooling (script name, flags, example invocation)
- Validation proof requirement (load_genre_pack + cliché-judge on output)

### AC-4: Validation
Gate on `load_genre_pack` for beneath_sunden (the reference instance) to confirm the recipe tooling and documentation are wired correctly. No regressions to the existing world.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-24T18:20:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-24T14:37:58Z | - | - |
| implement | 2026-06-24T14:37:58Z | 2026-06-24T17:03:26Z | 2h 25m |
| review | 2026-06-24T17:03:26Z | 2026-06-24T18:20:52Z | 1h 17m |
| finish | 2026-06-24T18:20:52Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): GATE 2 (tone curation — "never comic, never cute") is NOT machine-encoded in `world_register.yaml` (it has no biome/locomotion/role fields). The proven beneath_sunden pattern dropped ~61 entries here by *human judgment*. The tooling can only automate **GATE 1** (genre-truth deny/allow/glob), the CR→level conversion, the reskin, and the drop audit. The contract/recipe (AC-1/AC-3) must state explicitly that GATE 2 remains a documented human curation pass — do not let the prose imply the tool fully curates. Affects `tools/bestiary_curator/` + the recipe doc.
- **Gap** (non-blocking): `armor_class` and `morale` are **archetype-driven, not level-derived** (header: "ascending AC 12-17 by armor archetype"; "morale 12 = Fearless for mindless undead/oozes/constructs"). The ladder helpers (`level_to_hp/save/attack_bonus`) are pure functions of level, but the curator needs an archetype→AC/morale mapping to emit a complete (load_genre_pack-valid) stat block. Tests pin AC∈[12,18] and morale∈[2,12] (presence + band), not exact values — Dev owns the mapping. Affects `tools/bestiary_curator/`.
- **Improvement** (non-blocking): The bestiary banner cites an audit trail of `sunden_gate.py / tone_curate.py`, but **neither script was ever committed** (one-off local tools / aspirational prose). 158-20 is exactly the work of making GATE 1 + conversion real, committed, and reusable. Consider updating the bestiary banner's "Full audit trail" line to point at the real `tools/bestiary_curator/` once it lands. Affects `genre_packs/caverns_and_claudes/worlds/beneath_sunden/bestiary.yaml` (comment only).
- **Question** (non-blocking): AC-4 gates on `load_genre_pack`, which lives in `sidequest-server`. The tool suite is deliberately **server-free** (pyyaml only) to stay fast/self-contained. Recommend the load_genre_pack proof be a CLI `--validate` step + a story-acceptance check the Reviewer runs (beneath_sunden already loads; regenerating an equivalent bestiary that still loads is the proof), rather than a unit test pulling the whole server into this tool's env. If a wired load_genre_pack test IS wanted, add `sidequest-server` as an editable dep exactly like `tools/cavern_renderer/pyproject.toml`. Affects `tools/bestiary_curator/`.

### Dev (implementation)
- **Improvement** (non-blocking): On the real beneath_sunden corpus, GATE 1 alone keeps 208 / drops 108; the shipped bestiary is 192. The ~16 difference is the GATE-2 tone pass + dedup the tool deliberately does NOT do. When a 158-21..25 author runs the tool, expect the kept count to exceed the final roster — the human tone pass trims further. Documented in the recipe; flagging so the Reviewer doesn't read "208 kept" as a bug. Affects `docs/bestiary-curation-recipe.md` (already noted).
- **Improvement** (non-blocking): Acted on TEA's finding — the bestiary banner's "Full audit trail: sunden_gate.py / tone_curate.py" still names uncommitted scripts. I did NOT edit `bestiary.yaml` this story (out of scope; no test covers it), but a one-line banner update pointing at `tools/bestiary_curator/` would close the loop. Affects `genre_packs/caverns_and_claudes/worlds/beneath_sunden/bestiary.yaml` (comment only) — candidate for a 158-21 rider.
- **Gap** (non-blocking): The curator emits the mechanical skeleton only (`id/name/level/hp/armor_class/attack_bonus/save/morale/skill/tags`) — no `damage`/`move`/`description`/`abilities`. That is intentional (158-12: narrator owns creature prose; author fleshes the rest), but a per-world author must still hand-add `damage`/`move` for full play. Documented in the recipe + `curate.py` docstring. Affects per-world `bestiary.yaml` authoring (158-21..25).

### Reviewer (code review)
- **Gap** (blocking → RESOLVED `e1afaf9`): No input validation — malformed/empty config silently yielded wrong-or-empty output, violating the `<critical>` No Silent Fallbacks rule. `register.py:32` `safe_load(...) or {}` turned an empty `world_register.yaml` into a zero-config register (empty `allow_types`) that dropped the ENTIRE corpus and returned `kept=[]` with exit 0; `cr_to_level` mapped a negative CR silently to level 1; `curate_world` passed a `None`/non-list corpus into `for row in corpus` → cryptic `TypeError`/`string indices`. **Fixed inline** with fail-loud guards in `register.py`/`ladder.py`/`curate.py` + 13 pinning tests (`test_validation.py`); re-verified 101/101 green, happy path unchanged. *Found and resolved by Reviewer during code review.*
- **Improvement** (non-blocking): `_slug()` (`curate.py`) can emit an empty id for an all-punctuation name and does not detect id collisions across two corpus rows; both surface only at `load_genre_pack`/play. Low impact for SRD names, but the foundation tool will run on five more worlds. Affects `tools/bestiary_curator/bestiary_curator/curate.py`. *Found by Reviewer during code review.*

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Wrote RED tests on a `trivial`-workflow story (no formal red phase)**
  - Spec source: workflow tag (`trivial`: setup → implement → review → finish)
  - Spec text: trivial workflow has no TEA/red phase; content is normally VALIDATED not TEA-tested
  - Implementation: At the user's explicit request ("let's get some tests first"), TEA wrote and RED-verified a test suite for the **tooling** deliverable (genuine, testable Python), then handed to Dev for GREEN without completing the implement phase.
  - Rationale: The "reusable tooling" half of 158-20 is real code with a deterministic contract (gate, stat ladder, audit) — exactly what TDD protects. The content YAML half stays VALIDATED (load_genre_pack), unchanged.
  - Severity: minor
  - Forward impact: Dev implements `tools/bestiary_curator/` to GREEN; phase stays `implement`.
- **`level_to_hp` pinned to a ground-truth lookup table, not the prose formula**
  - Spec source: bestiary.yaml header / banner, AC-3
  - Spec text: "hp == average (4.5/HD rounded)"
  - Implementation: Tests pin the canonical live ladder {1:5,2:9,3:14,4:18,5:22,6:27,7:32,8:36,9:40,10:45}. No single Python rounding mode reproduces it (banker's `round(4.5)`=4 breaks L1; round-half-up(40.5)=41 breaks L9). The curator must reproduce the proven instance, so the test pins observed output, and the Dev may implement it as a table or a custom rounding rule.
  - Rationale: Pinning a guessed formula would make the RED test itself wrong; ground truth from the validated pack is authoritative.
  - Severity: minor
  - Forward impact: 158-21..25 worlds may need their own ladder if a different ruleset/HD die applies — the contract should parameterize the ladder per ruleset.
- **Created project scaffold (pyproject.toml + docstring-only package stub)**
  - Spec source: TEA role boundary (tests only, no source)
  - Spec text: TEA "CANNOT modify source files, implement features"
  - Implementation: Created `tools/bestiary_curator/pyproject.toml`, `.gitignore`, and a docstring-only `bestiary_curator/__init__.py` so `uv run pytest` builds and RED fails on missing *names* (clean signal). The stub carries ZERO behaviour; Dev implements the entire public API.
  - Rationale: Mirrors the house `tools/cavern_renderer/` convention so the suite is runnable and the RED is watchable; the stub is package-marker scaffold, not implementation.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **`armor_class` / `morale` derived from level/type proxies, not true "armor archetype"**
  - Spec source: bestiary.yaml banner / TEA finding, AC-2
  - Spec text: "ascending AC 12-17 by armor archetype"; "morale 12 = Fearless for mindless undead/oozes/constructs"
  - Implementation: AC = `min(12 + level//2, 17)` (level-band proxy); morale = `12` for Undead/Ooze/Construct else `8`. The SRD corpus rows carry no armor or intelligence data, so true archetype derivation is impossible from the input — these are sane defaults the per-world author tunes by hand (GATE 2). Tests pin only the band ranges (AC∈[12,18], morale∈[2,12]).
  - Rationale: Honest defaults beat fabricated precision; the recipe documents AC/morale as author-tuned. Matches TEA's flagged finding.
  - Severity: minor
  - Forward impact: 158-21..25 authors hand-tune AC/morale per creature after running the tool.
- **GATE 2 (tone curation) intentionally NOT automated — tool scope is GATE 1 + ladder + audit**
  - Spec source: story title ("tone curation" is one of four stages), AC-1/AC-2
  - Spec text: "world_register genre-truth gate → tone curation → WWN stat ladder → pack-validate"
  - Implementation: The tool automates GATE 1 (deterministic genre-truth) + the stat ladder + the drop audit. GATE 2 ("never comic, never cute") stays a documented HUMAN pass — the `world_register` schema has no biome/locomotion/role fields to encode it, and 158-12 keeps curation deterministic/LLM-free. On beneath_sunden, GATE 1 keeps 208; the shipped 192 reflects the human GATE-2 + dedup trim.
  - Rationale: Encoding tone judgment would either fabricate rules or pull an LLM back into curate; the recipe makes the human pass explicit instead.
  - Severity: minor
  - Forward impact: Each 158-21..25 story includes a human tone pass after running the tool (documented in the recipe checklist).

### Reviewer (audit)
- **TEA — Wrote RED tests on a `trivial`-workflow story** → ✓ ACCEPTED by Reviewer: user-directed ("let's get some tests first"); the tooling half is genuine testable Python, so a RED pass is correct craft. The content/YAML half stays validated, unchanged.
- **TEA — `level_to_hp` pinned to a ground-truth table, not the prose formula** → ✓ ACCEPTED by Reviewer: I verified no single rounding mode reproduces the live ladder (banker's breaks L1, half-up breaks L9). Pinning the proven instance is right; `ladder.py` implements it as `_HP_LADDER`. Forward note (per-ruleset ladder) is sound.
- **TEA — Created project scaffold (pyproject + docstring-only stub)** → ✓ ACCEPTED by Reviewer: mirrors `tools/cavern_renderer/`; stub carried zero behaviour and was replaced by real exports in GREEN (verified `__init__.py`). No stubbing-rule violation remains.
- **Dev — `armor_class`/`morale` derived defaults, not true archetype** → ✓ ACCEPTED by Reviewer: the SRD corpus carries no armor/intelligence data, so honest level/type proxies beat fabricated precision; documented in the recipe and logged. Tests pin band ranges only.
- **Dev — GATE 2 (tone) intentionally NOT automated** → ✓ ACCEPTED by Reviewer: correct scope and squarely SOUL-aligned (tone is judgment; 158-12 keeps curate LLM-free). The recipe makes the human pass explicit. This is a deliberate boundary, not a gap.

## Notes

### Context for Implementation

- **Proven Pattern:** beneath_sunden/world_register.yaml (genre-truth gate), beneath_sunden/bestiary.yaml (WWN stat ladder with provenance audit)
- **Target Audience:** Stories 158-21..25 will follow this recipe for their respective worlds (barsoom, evropi, long_foundry, burning_peace, shattered_accord)
- **Ruleset Variation:** Different packs may use different rulessets (WWN, CWN, SWN); the contract must handle per-ruleset stat-ladder variations
- **Validation:** Content stories are VALIDATED not TEA-tested — gate on `load_genre_pack` + cliché-judge, not a RED phase
- **Tooling Reference:** Existing tools in `sidequest-content/tools/` (audit_poi_slug_mismatches.py, split_cultures.py) show style/conventions for content-side scripts

## TEA Assessment

**Tests Required:** Yes (for the *tooling* deliverable — at the user's explicit request)
**Reason:** The "reusable tooling" half of 158-20 is genuine, deterministic Python (genre-truth gate + WWN stat ladder + drop audit). The content/recipe half (AC-1/AC-3 docs, the regenerated bestiary YAML) stays VALIDATED via `load_genre_pack`, not TEA-tested.

**Test Files:** (`tools/bestiary_curator/`, a self-contained `uv` project mirroring `tools/cavern_renderer/`)
- `tests/test_ladder.py` — WWN stat ladder: `cr_to_level`, `level_to_hp`, `level_to_save`, `level_to_attack_bonus`
- `tests/test_gate.py` — `apply_genre_truth_gate` against the real `world_register.yaml`
- `tests/test_curate.py` — end-to-end `curate` / `curate_world` on the real 316-row corpus (the **wiring test**)
- `tests/conftest.py` — reference-instance path fixtures (beneath_sunden); `pyproject.toml` + docstring-only `bestiary_curator/__init__.py` scaffold

**Tests Written:** ~40 cases across 4 ACs (AC-1 gate, AC-2 tooling, AC-3 ladder contract, AC-4 wiring/validation seam)
**Status:** RED (verified — 3 modules fail collection on missing `bestiary_curator` API; `cannot import name 'WorldRegister'/'cr_to_level'`). Scaffold builds clean; only the implementation is absent.

### Contract the GREEN implementation must satisfy (public API of `bestiary_curator`)

```python
WorldRegister.from_yaml(path) -> WorldRegister      # parses world_register.yaml
apply_genre_truth_gate(corpus_row: dict, reg) -> GateDecision
    # GateDecision: .kept (bool), .reason (str|None), .name (output name, reskinned), .reskinned (bool)
    # order: marquee-exempt FIRST, then deny.types / deny.tags / deny.name_glob (case-insensitive)
    #        / allow_types miss; reskin applied to kept names
cr_to_level(cr: float) -> int                       # empirical bands, deep-cap <=10 (see test_ladder)
level_to_hp(level) -> int                           # canonical ladder {1:5..10:45} — NOT naive round()
level_to_save(level) -> int                         # 15 - level//2
level_to_attack_bonus(level) -> int                 # == level
curate(corpus: list[dict], reg) -> CurationResult   # .kept: list[stat-block dict], .dropped: list[GateDecision]
curate_world(world_dir: Path) -> CurationResult     # loads corpus/monsters.yaml + world_register.yaml
```
- Every kept stat block must carry `{id, name, level, hp, armor_class, attack_bonus, save, morale, tags}` to pass load_genre_pack. `hp/save/attack_bonus` are ladder-exact; `armor_class`/`morale` are archetype-driven (Dev's mapping; tests only pin band ranges).
- Do NOT edit the tests to fit the implementation. If a test is genuinely wrong, log a deviation and fix it — but the values are ground-truth from the live pack, so prefer matching them.
- See the three **Delivery Findings (Gap/Question)** above before coding: GATE 2 stays a documented human step; AC-4 load_genre_pack proof is a CLI/acceptance step, not a server-pulling unit test.

**Rules checked:** No `.pennyfarthing/gates/lang-review/python.md` rule beyond meaningful-assertions applies to a pure author-time tool; every test asserts a concrete value/membership/range (self-checked — no vacuous assertions).
**Handoff:** To Dev (Ponder Stibbons) for implementation — phase stays `implement`.

## Dev Assessment

**Implementation Complete:** Yes (full story per user scope choice: tooling + CLI + docs + AC-4)

**Files Changed:** (all in sidequest-content, branch `feat/158-20-wwn-bestiary-curation-recipe`)
- `tools/bestiary_curator/bestiary_curator/ladder.py` — WWN stat ladder (cr_to_level deep-cap bands; level_to_hp canonical table; level_to_save; level_to_attack_bonus)
- `tools/bestiary_curator/bestiary_curator/register.py` — `WorldRegister.from_yaml` (parses world_register.yaml)
- `tools/bestiary_curator/bestiary_curator/gate.py` — `GateDecision`, `apply_genre_truth_gate` (GATE 1; marquee-first, deny type/tag/glob, allow miss, reskin)
- `tools/bestiary_curator/bestiary_curator/curate.py` — `CurationResult`, `curate`, `curate_world` (gate + convert + drop audit)
- `tools/bestiary_curator/bestiary_curator/cli.py` + `__main__.py` — `python -m bestiary_curator <world_dir> [--out]`
- `tools/bestiary_curator/bestiary_curator/__init__.py` — public API exports (replaced RED stub)
- `tools/bestiary_curator/pyproject.toml` — added `[project.scripts]` console entry
- `docs/bestiary-curation-recipe.md` — the four-stage per-world contract + audit template + 158-21..25 checklist (AC-1, AC-3)

**Tests:** 88/88 passing (GREEN). ruff lint + format clean.

**AC coverage:**
- AC-1 (per-world contract documented) — `docs/bestiary-curation-recipe.md` (four stages, world_register schema, audit template)
- AC-2 (reusable tooling) — `bestiary_curator/` package + CLI; **proven** to emit load-ready stat blocks: all 208 curated beneath_sunden entries validate against the real server `BestiaryEntry` schema, and `Bestiary(entries=...)` constructs
- AC-3 (reference documentation) — same recipe doc: CR→level table, ladder table, deny/allow/reskin audit-trail template, tooling pointer, validation-proof requirement
- AC-4 (validation) — `load_genre_pack('genre_packs/caverns_and_claudes')` passes, beneath_sunden present, no regression (pack unmodified)

**Wiring:** `cli.py` (console + `python -m`) is the non-test consumer of the library; curator output validated through the server's real `BestiaryEntry`/`Bestiary` models (cross-repo wiring proof).

**Branch:** feat/158-20-wwn-bestiary-curation-recipe (pushed)
**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (88/88 green, lint+format clean, 0 smells; 3 cli.py prints are intended stderr audit) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 (register empty-config, corpus None/non-list, negative-CR, missing-cr KeyError, empty allow_types) | confirmed 4 (3 folded into the block finding + 1 diagnostics), 1 dup of register |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 (register.py silent fallback — note: its "keeps the entire corpus" reasoning is WRONG; empty allow_types DROPS all, verified) | confirmed (severity calibrated; reasoning corrected) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Reviewer performed manual rule enumeration (see Rule Compliance) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed blocking-cluster (input validation), 2 confirmed non-blocking (diagnostics, slug), 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED (after inline rework — initial verdict was REJECTED; see Rework Resolution)

The happy path was excellent, but a foundation tool that five more worlds (and a new non-Keith author) will run cannot ship with no input validation when "No Silent Fallbacks" is a `<critical>` project rule. Three independent HIGH-confidence subagent findings flagged silent-default behaviour on malformed config — I could not dismiss findings that match a stated project rule, so I required fail-loud hardening. **The author (per Keith's "fix now" direction) added the guards + 13 fail-loud tests inline (commit `e1afaf9`); I re-reviewed and the blocking findings are resolved.**

| Severity | Issue | Location | Resolution |
|----------|-------|----------|--------------|
| [HIGH→RESOLVED] | No input validation → silent wrong/empty output (violated `<critical>` No Silent Fallbacks). Empty/`null` `world_register.yaml` → zero-config register → entire corpus dropped, exit 0. Negative CR → silent level 1. | `register.py`, `ladder.py` `cr_to_level`, `gate.py` (empty `allow_types`) | **FIXED** `e1afaf9`: `from_yaml` raises on non-mapping/empty data AND empty `allow_types`; `cr_to_level` raises on `cr < 0`. Pinned by `test_validation.py`. Verified ✓. |
| [MEDIUM→RESOLVED] | Corpus shape not validated → cryptic `TypeError`/`string indices` crash instead of a file-named error. | `curate.py` `curate`/`curate_world` | **FIXED** `e1afaf9`: `curate` raises if corpus is not a non-empty `list`, and per-row if a row is not a `dict`. Pinned by `test_validation.py`. Verified ✓. |
| [LOW] | `_slug()` can emit an empty id (all-punctuation name) and does not detect id collisions across rows; surfaces only at load/play. | `curate.py` `_slug` | Deferred — non-blocking; recorded as a delivery finding for a 158-21..25 rider. Low impact for SRD names. |

### Rework Resolution

After the REJECTED verdict, a focused TDD micro-cycle landed the fail-loud guards (commit `e1afaf9` on the feat branch):
- `test_validation.py` — 13 tests pinning each fail-loud path (empty/comment-only/non-mapping register, empty/missing `allow_types`, negative CR, `None`/empty/dict-shaped/non-dict-row corpus), all written RED-first and watched fail before the guards landed.
- Guards added to `register.py` (`from_yaml`), `ladder.py` (`cr_to_level`), `curate.py` (`curate`).
- **Re-verification:** full suite 101/101 green; ruff lint + format clean; CLI still curates beneath_sunden (kept 208 / dropped 108); all 208 entries still validate as `Bestiary`; `load_genre_pack` unaffected. Happy path provably unchanged — the guards bite only on malformed input.

The remaining `[LOW]` slug observation is non-blocking and recorded for a follow-up. No Critical/High issues remain.

### Observations (tagged by source)

- `[SILENT]` `[SEC]` [HIGH] Silent empty-config → whole-corpus drop — `register.py:32`. Both the silent-failure-hunter (high conf) and security agent flagged the `or {}` fallback; I confirmed the *direction* myself (security agent said "keeps the corpus" — wrong; empty `allow_types` makes `type_ not in []` always true → drops all). Violates No Silent Fallbacks.
- `[SILENT]` [HIGH] Negative CR → silent level 1 — `ladder.py` `cr_to_level`: `cr <= 0.5` fires first band for any `cr < 0`. This is the genuinely-silent case (plausible-but-wrong output), the exact failure mode the project's lie-detector ethos exists to catch.
- `[SILENT]` [MEDIUM] Corpus `None`/dict shape → cryptic crash — `curate.py:103`. Loud but misleading; the real error (wrong YAML shape) is masked.
- `[SILENT]` [MEDIUM] Missing `name`/`cr` → contextless `KeyError` — `gate.py:43`, `curate.py:69`.
- `[VERIFIED]` YAML parsed safely — `register.py:32`, `curate.py:103`, `conftest.py`, `test_curate.py` all use `yaml.safe_load` (4 instances, 0 `yaml.load`). Output via `yaml.safe_dump`. Complies with the safe-load rule.
- `[VERIFIED]` No Stubbing — `__init__.py` exports the real API (`curate/gate/ladder/register`); the RED docstring-only stub was fully replaced in GREEN. No empty shells remain.
- `[VERIFIED]` Wiring proven — `tests/test_curate.py::curate_world` runs the real pipeline on the real 316-row corpus (the wiring test); `cli.py` is the non-test consumer; AC-2 proof validates all 208 curated entries through the server's real `BestiaryEntry`/`Bestiary` models. This is a genuine cross-repo wiring check, not existence-only.
- `[VERIFIED]` Ladder + gate logic correct — `ladder.py` `_HP_LADDER` matches the live beneath_sunden ladder; `gate.py` checks marquee FIRST (exemption precedence per ADR-014), then deny type/tag/glob (case-insensitive `fnmatchcase`), then allow-miss; reskin applied to kept names only. Traced against the live `world_register.yaml`.
- `[SEC]` No ReDoS / injection — `_slug` uses an anchored char-class `[^a-z0-9]+` (linear); `fnmatchcase` globs are author-controlled local data; no eval/subprocess/network/secrets. Local author-time tool.
- `[EDGE]` / `[TEST]` / `[DOC]` / `[TYPE]` / `[SIMPLE]` / `[RULE]` — subagents disabled via `workflow.reviewer_subagents`; not run. I performed the rule check manually (see Rule Compliance) and a manual edge/type pass (the input-validation findings above are the edge-case gaps).

### Rule Compliance (manual enumeration — rule_checker disabled)

- **No Silent Fallbacks** (`<critical>`, content CLAUDE.md): **VIOLATIONS** at `register.py:32` (empty register → silent zero-config), `ladder.py` `cr_to_level` (negative CR → silent level 1), and by extension `gate.py:60` (empty `allow_types` → silent whole-corpus drop). This is the blocking finding. `curate.py:103` partially violates (crashes, but masks the real cause).
- **No Stubbing** (`<critical>`): COMPLIANT — every module has real behaviour; the RED stub was replaced (`__init__.py`).
- **Don't Reinvent — Wire Up What Exists** (`<critical>`): COMPLIANT — mirrors `tools/cavern_renderer/` (uv subproject) rather than inventing a new harness; reuses the existing `world_register.yaml`/`corpus` artifacts.
- **Verify Wiring / Every Test Suite Needs a Wiring Test** (`<critical>`): COMPLIANT — `test_curate.py` end-to-end on real data + CLI consumer + BestiaryEntry-schema validation.
- **OTEL Observability**: N/A — author-time offline CLI, not a runtime game subsystem making narration/engine decisions. The rule governs backend subsystem decisions in the game loop, which this is not.
- **YAML safe_load not load**: COMPLIANT (4/4).

### Data flow traced

`world_dir` (CLI arg) → `curate_world` → reads `corpus/monsters.yaml` + `world_register.yaml` (`yaml.safe_load`) → per row, `apply_genre_truth_gate` → kept rows → `_stat_block` (`cr → cr_to_level → level_to_hp/save/attack_bonus`) → `CurationResult.kept` (dicts) → `yaml.safe_dump` to stdout/`--out`; drops → stderr audit. **Safe on the happy path; the malformed-input branches are where it goes silent/cryptic (findings above).**

### Devil's Advocate

Assume this is broken. The project explicitly serves a *new, non-Keith author* (Jade) who must add worlds "without touching engine code" — and this is the foundation tool five WWN worlds will run. Picture that author authoring a new `world_register.yaml`: she nests `allow_types` one level too deep, or typos the key, or saves the file empty while iterating. She runs `python -m bestiary_curator … --out bestiary.yaml`, watching the file, not stderr. The tool exits 0 and writes a YAML with an empty `entries` list — no error, no exception. She's now debugging "why is my bestiary empty" with zero signal from the tool: the precise "why isn't this quite right" hours-sink the No-Silent-Fallbacks rule was written to prevent. Worse is the CR path: SRD listings routinely use fractional notation (`1/4`, `1/2`) and "—"/"varies" for unrated entries. `float("1/4")` raises mid-run with no monster name; a homebrew generator emitting `cr: -1` for "unrated" silently yields a **level-1 stat block** that looks perfectly valid sitting among 200 others — a convincing fabrication from garbage input, exactly what the project's OTEL/lie-detector philosophy is built to expose. A dict-shaped corpus crashes with `string indices must be integers`, pointing at Python internals instead of the file. None of these is caught by the 88 tests, because every test feeds well-formed input or the real (valid) pack. The happy path is bulletproof; the malformed-input underbelly is unguarded — and shipping it unguarded propagates the gap across five downstream stories and the very author the project exists to empower. **What is NOT broken:** the gate decision order, the ground-truth ladder, the reskin/marquee precedence, the wiring, and the safe-load discipline are all correct and well-tested — so the fix is narrow (add fail-loud guards + tests), not a redesign.

**Handoff:** To SM (Captain Carrot) for finish-story. The REJECTED findings were resolved inline (fail-loud rework `e1afaf9`, 101/101 green); no Critical/High issues remain. Approved.

## Repos
- **Primary:** sidequest-content (branch: feat/158-20-wwn-bestiary-curation-recipe)