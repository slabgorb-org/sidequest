---
story_id: "90-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 90-1: Encountergen ruleset-awareness — emit WWN/CWN/SWN-aligned enemy stat blocks via the RulesetModule seam so pregen.seed_manual populates the Monster Manual encounters pool for ruleset-module packs (replaces native allowed_classes/class_hp_bases dependency)

## Story Details
- **ID:** 90-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T22:07:14Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T19:28:47Z | 2026-06-05T20:28:55Z | 1h |
| red | 2026-06-05T20:28:55Z | 2026-06-05T21:09:17Z | 40m 22s |
| green | 2026-06-05T21:09:17Z | 2026-06-05T21:57:24Z | 48m 7s |
| review | 2026-06-05T21:57:24Z | 2026-06-05T22:07:14Z | 9m 50s |
| finish | 2026-06-05T22:07:14Z | - | - |

## Sm Assessment

**Story:** 90-1 — the **root story of epic 90** (Ruleset-Module Worlds: Live Combat & Magic Verification Enablement). Make `encountergen` ruleset-aware so `pregen.seed_manual` populates the Monster Manual `encounters` pool for `ruleset: wwn|cwn|swn` packs (currently native-dial-only — it hard-fails `... has no allowed_classes` on RulesetModule packs, leaving evropi/long_foundry at 0 encounters).

**Workflow:** tdd (phased) → setup (SM) → **red (TEA)** → green (Dev) → review (Reviewer) → finish (SM).
**Repos:** `server,content` — primary work is **server** (`sidequest/cli/encountergen/` + `pregen.seed_manual` + the `game/ruleset/` RulesetModule seam); content is the ruleset-module packs whose pools get populated. Feature branch `feat/90-1-encountergen-ruleset-awareness` created + checked out in both.
**Jira:** none — claim skipped.

**Context written and validated:** `sprint/context/context-story-90-1.md` (5921 bytes, parent `context-epic-90.md`). Seeded from the epic-90 scope + 87-4 findings with a Problem, Technical Approach, and **6 DRAFT ACs** (TEA owns the final RED encoding). Keith chose "route to TEA now" over an architect design-pass (2026-06-05) — the RulesetModule seam shape gets pinned by TEA's RED contract.

**Load-bearing routing notes for TEA (Mr. Praline):**
- **The seam is the design crux.** Route enemy-stat generation through the `RulesetModule` ABC (`game/ruleset/{base,registry,native,swn}.py`), making native one module and giving `wwn`/`cwn`/`swn` their own SRD-aligned emission. Detection via the pack's resolved `ruleset:` (registry; unknown → `UnknownRulesetError`, keep fail-loud). Your RED tests pin the seam contract — Keith deferred the design to your tests, so make the contract assertions deliberate.
- **Two regression guards are mandatory:** (1) **native-dial packs unaffected** (caverns_and_claudes still seeds via `allowed_classes`/`class_hp_bases`); (2) **`opponent_default_stats` is untouched** — this story supplies *reachable hostile presence* for free play, NOT how a *triggered* Other seats (87-4 finding (1): WWN already statifies a triggered Other from `opponent_default_stats`). Do not let a test conflate the two.
- **OTEL is required** (Observability Principle): assert a seeding span fires with the ruleset + encounter-count attributes per pack — the GM-panel proof the pool was populated, not silently empty. **No silent fallback**: a ruleset-module pack emits ruleset-aware blocks or fails loud (never a silent empty pool / native fallback).
- **e2e wiring test required** (server CLAUDE.md "Every Test Suite Needs a Wiring Test" + "No Source-Text Wiring Tests"): drive the real `pregen.seed_manual` on a real `wwn` pack and assert the pool is non-empty via behavior/spans, not a source grep.
- ACs 1–6 are in the story context; treat them as the RED checklist but refine wording as you encode.

**Decision:** Setup complete, gate ready. Handoff to TEA (Mr. Praline) for RED.

## TEA RED — Seam Map & Test Plan (working notes, RED in progress)

Seam fully mapped (Explore pass). **RED tests not yet written — paused at a clean
checkpoint; this note is the durable handoff so RED resumes without re-investigating.**

### Ground truth (verified file:line)
- **The hard-fail:** `sidequest/cli/encountergen/encountergen.py:495–501` — `generate_enemy(pack, genre_dir, args, rng) -> EnemyBlock` does `allowed_classes = pack.rules.allowed_classes; if not allowed_classes: print(... "has no allowed_classes" ...); sys.exit(1)`. It is a **bare `sys.exit(1)` to stderr, NOT a typed exception.** Also reads `allowed_races` at `:518`. `class_hp_bases` is gone (ADR-078); HP = `DEFAULT_HP_BASE(=8) * level`.
- **`EnemyBlock`** dataclass (`encountergen.py:60–78`): name, class_, race, level, tier_label, role, hp, abilities, weaknesses, disposition, personality, dialogue_quirks, inventory, stat_scores, ocean(+summary), trope_connections, visual_prompt. → narrative layers (name/OCEAN/tropes/visual) are encountergen's; **combat layer (class/race/level/hp/abilities/stat_scores) is what's allowed_classes-derived today.**
- **pregen** `sidequest/server/dispatch/pregen.py:183–342` `seed_manual(...)`: calls `_generate_encounter` → `_run_cli_capturing_json(encountergen_main, ...)` which returns `None` on the `sys.exit(1)`; then `if data is not None: manual.add_encounter(...)` — i.e. **silently skips** the pool on failure (warning only). OTEL span `SPAN_PREGEN_SEED_MANUAL = "pregen.seed_manual"` already emits `encounters_after` + `combat_encounters` attrs (`:321–339`).
- **RulesetModule** `sidequest/game/ruleset/`: registry (`registry.py`) has **all 5** — native/swn/cwn/wwn/awn (genre CLAUDE.md saying "native+swn only" is STALE). ABC `base.py` methods (find_confrontation, stat_modifier, compute_dc, apply_beat, resolve_damage, attack_params, + optional ship/opponent/trauma/etc.) — **none produces enemy stat blocks.** Modules never read allowed_classes. wwn/cwn/swn subclass swn. Resolve via `get_ruleset_module(pack.rules.ruleset)` (string slug on `pack.rules.ruleset`; `UnknownRulesetError` on unknown — keep fail-loud).
- **Tests/fixtures:** `tests/cli/test_encountergen.py` (CLI, skipif on real content), `tests/server/dispatch/test_pregen.py` (`_stub_pack`, monkeypatch `encountergen_main`/`namegen_main`, `FIXTURE_PACKS` frozen pack), `tests/integration/test_wwn_heavy_metal_combat.py` (real heavy_metal + `otel_capture`). **`otel_capture` fixture:** `tests/server/conftest.py:1005` (InMemorySpanExporter; assert via `otel_capture.get_finished_spans()` → filter by `s.name` + `.attributes`).

### Seam contract — DECIDED: Option B (content bestiary), Keith 2026-06-05
**No new `RulesetModule` ABC method.** For a ruleset-module pack, encountergen reads a
**content-authored bestiary** instead of generating from `allowed_classes`.
- **Branch:** `encountergen.generate_enemy` (and the seed path) — if `pack.rules.ruleset == "native"`
  (or absent) → today's `allowed_classes`/`allowed_races` path, **unchanged** (AC5 guard). Else
  (wwn/cwn/swn/awn) → load the pack's bestiary content and emit `EnemyBlock`s from it.
- **Bestiary file (shape TBD with Keith at resume — pin in RED):** per-pack content, e.g.
  `genre_packs/<pack>/bestiary.yaml` (the ruleset is implicit from `rules.yaml`; the option-B
  preview wrote `bestiary_<ruleset>.yaml` — confirm singular-vs-ruleset-suffixed at resume). A
  bestiary entry supplies the COMBAT layer (name, hp, armor_class, attack/atk_bonus, level/HD,
  role, abilities, optional location/tags); encountergen keeps composing narrative layers
  (OCEAN/tropes/visual_prompt) as today, OR the bestiary entry is emitted closer to verbatim —
  **decide at resume.** Needs a pydantic model in `sidequest/genre/models/` + loader wiring +
  the mandatory-file loader contract question (is bestiary required for ruleset-module packs, or
  optional-but-fail-loud-if-the-ruleset-needs-it?).
- **No silent fallback:** a ruleset-module pack must emit from its bestiary or **fail loud** —
  never the current silent `None` → empty pool. (Fixing pregen's silent-skip is in scope.)
- **Content lift (accepted):** every ruleset-module world authors a bestiary (less reuse than a
  shared SRD floor) — Keith chose this knowingly. heavy_metal evropi + long_foundry each need one
  (Barsoom too, epic 89). A starter bestiary for heavy_metal is part of this story's content side.

### Sub-decisions to settle at resume (before/while writing RED)
1. Bestiary filename/scope: `bestiary.yaml` per pack vs `bestiary_<ruleset>.yaml` vs per-world override.
2. Bestiary schema (the pydantic model fields) + whether encountergen composes narrative layers onto bestiary combat stats or emits the entry largely as-authored.
3. Mandatory-file contract (ADR-120): is bestiary required for ruleset-module packs (fail-loud-if-missing) or optional?
These are content-shape decisions; Keith authors content, so confirm 1–2 with him.

### RED test plan (per AC — to write next; verify each FAILS for the right reason)
1. **No hard-fail (AC1):** drive `generate_enemy` (or `encountergen_main`) on a real `ruleset: wwn` pack (heavy_metal) → assert it does NOT `SystemExit`/print "has no allowed_classes", returns an `EnemyBlock`. (Will fail today: sys.exit(1).)
2. **WWN-shaped stats (AC2):** assert the emitted enemy carries bestiary-authored combat fields (hp/armor_class/attack present, WWN-sane ranges) sourced from the pack's bestiary, not `allowed_classes`. (Fails: no bestiary path today.)
3. **Pool populated (AC3):** `seed_manual` on evropi + long_foundry → `len(manual.encounters) > 0`, entries well-formed. (Fails: 0 today.) Use the real-content/integration pattern, not the stubbed monkeypatch, so it exercises the production path.
4. **OTEL (AC4):** drive seeding with `otel_capture`; assert `pregen.seed_manual` span fires with `encounters_after > 0` for a wwn pack (and ideally a per-generation ruleset attribute). (Fails: encounters_after 0.)
5. **Native regression (AC5):** `enemy_stat_block`/seed on caverns_and_claudes (native) unchanged — same shape/HP as before. (Should pass once native adapter wraps current logic; RED now because the method doesn't exist.)
6. **Generality (AC6):** the bestiary branch keys on `ruleset != native` (ruleset-generic — wwn/cwn/swn/awn all take the bestiary path), NOT a wwn-only special-case. Prove with the wwn pack + assert the branch isn't hardcoded to wwn. (Fails: no bestiary branch.)
- **Wiring/e2e (CLAUDE.md):** AC3+AC4 together are the e2e wiring proof (real pack → real `seed_manual` → non-empty pool + span), behavior/span-asserted, not source-grep. **Regression guard:** add a test asserting `instantiate_encounter_from_trigger` still seats the Other from `opponent_default_stats` unchanged (this story must NOT touch triggered-seating — 87-4 finding (1)).

**Next action on resume (contract = Option B, content bestiary):** confirm sub-decisions 1–2 (bestiary filename + schema) with Keith, draft a starter heavy_metal `bestiary.yaml` + its pydantic model, then write tests 1–6 + the two guards in `tests/cli/test_encountergen.py` + `tests/server/dispatch/test_pregen.py` (+ a bestiary-loader test), run with `SIDEQUEST_GENRE_PACKS` set, confirm RED for the right reason, write the `## Tea Assessment (RED)`, then exit-protocol → Dev (green).

*(Resolved: sub-decisions locked — (1) `bestiary.yaml` per pack root, ruleset implicit; (2) combat-layer-only schema, encountergen composes narrative layers; (3) REQUIRED for ruleset-module packs, fail loud. RED written below.)*

## Tea Assessment (RED)

**Phase:** finish complete. Tests written, confirmed failing for the right reason. Committed `feat/90-1-encountergen-ruleset-awareness` (sidequest-server).

**RED tests added — 7 failing + 1 passing regression lock** (run: `SIDEQUEST_GENRE_PACKS=<content>/genre_packs uv run pytest tests/cli/test_encountergen_bestiary_90_1.py tests/server/dispatch/test_pregen_bestiary_90_1.py -n0` → 7 failed / 1 passed, 41s):

`tests/cli/test_encountergen_bestiary_90_1.py`:
1. `test_ruleset_module_pack_does_not_hard_fail` (AC1) — FAILS: `SystemExit(1)` from `encountergen.py:501`, stderr `"genre 'heavy_metal' has no allowed_classes in rules.yaml"` (the exact 87-4 bug).
2. `test_wwn_enemies_carry_bestiary_combat_fields` (AC2) — FAILS (same hard-fail); once green it pins `armor_class`+`attack_bonus` (WWN-sane ranges) on emitted enemies + `visual_prompt` still composed (narrative layers stay encountergen's).
3. `test_heavy_metal_ships_a_wellformed_bestiary` (content contract) — FAILS: no `bestiary.yaml` at heavy_metal. Pins schema: top-level `entries:` list; required per-entry fields `{id, name, level, hp, armor_class, attack_bonus}` (extras free).
4. `test_bestiary_requirement_is_ruleset_generic` (AC6) — FAILS: **all four** live ruleset-module packs lack bestiaries (heavy_metal wwn, elemental_harmony wwn, neon_dystopia cwn, space_opera swn). Pins the seam as ruleset-generic, not wwn-only.
5. `test_native_pack_still_generates_via_allowed_classes` (AC5) — **PASSES** (regression lock armed): caverns_and_claudes still generates via `allowed_classes`; must stay green after the bestiary branch.

`tests/server/dispatch/test_pregen_bestiary_90_1.py` (the e2e WIRING tests — real pack → real `seed_manual` → behavior+span, no source-grep):
6./7. `test_seed_manual_populates_encounters_for_wwn_world[evropi|long_foundry]` (AC3) — FAIL: encounters pool EMPTY both worlds; log shows the silent-skip (`pregen.encountergen_failed (exit_code=1)`) — the No-Silent-Fallbacks bug this story retires.
8. `test_seed_manual_span_reports_nonzero_encounters` (AC4) — FAILS: `pregen.seed_manual` span fires but `encounters_after=0`. Once green, the GM panel sees a non-empty pool per world.

**Deliberately NOT tested (and why):**
- **`opponent_default_stats` seating guard** — already locked by `tests/integration/test_wwn_heavy_metal_combat.py` (3 tests); duplicating it here would be the redundancy the 87-4 review flagged. The guard requirement is: that suite must still be green at verify.
- **WWN-SRD numeric fidelity of bestiary stats** — bestiary entries are content-authored; "are these numbers WWN-correct" is an authoring/review judgment, not a unit assertion beyond the sanity ranges in test 2.

**Lint:** ruff check + format clean on both files.

**Scope tension for Dev/Keith (also logged in Delivery Findings):** decision 3 (bestiary REQUIRED, fail-loud) + AC6 means **all four** ruleset-module packs need a bestiary in this story, else their `seed_manual` goes from today's silent-0 to a loud failure — a behavior change for elemental_harmony/neon_dystopia/space_opera sessions. Dev options: (a) author all 4 starter bestiaries (content side), or (b) descope to heavy_metal + log a deviation amending test 4 to flag-not-fail for the other packs + file a follow-up story. (a) is contract-faithful; (b) is a legitimate logged deviation if 4 bestiaries blow the 8-pt budget.

**Handoff to Dev (Bicycle Repair Man):** make 1–4 + 6–8 green: bestiary pydantic model + loader wiring (`sidequest/genre/models/`), the `ruleset != native` branch in `generate_enemy` (keep `:495` hard-fail ONLY for native packs missing allowed_classes), retire pregen's silent skip (fail loud for ruleset packs), author `bestiary.yaml` starter(s) (content repo, same feat branch), keep test 5 + the wwn_heavy_metal integration suite green.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**

*sidequest-server* (`feat/90-1-encountergen-ruleset-awareness`, pushed — commits `03537348` + `32b9e3fd`):
- `sidequest/genre/models/bestiary.py` — NEW: `Bestiary`/`BestiaryEntry` pydantic models (required combat layer: id/name/level/hp/armor_class/attack_bonus; `extra="allow"` for SRD color; dup-id + non-empty validation)
- `sidequest/genre/models/pack.py` — `GenrePack.bestiary: Bestiary | None`
- `sidequest/genre/loader.py` — loads pack-root `bestiary.yaml` via `_load_yaml_optional` (malformed → loud `GenreLoadError`)
- `sidequest/cli/encountergen/encountergen.py` — `EnemyBlock` gains optional `armor_class`/`attack_bonus` (dropped from JSON when unset, so native/creatures output is byte-identical); new `generate_enemy_from_bestiary` (tier→level-range sampling, narrative layers still composed); `main()` routes `ruleset != native` to the bestiary with a loud exit-1 when missing; `_emit` helper dedupes output; native `:495` hard-fail untouched
- `sidequest/server/dispatch/pregen.py` — `EncounterSeedError` raised when encounter generation fails for a ruleset-module pack (silent skip retired; native keeps warning-only); `pregen.seed_manual` span gains `ruleset` attribute (AC4); stub-pack-safe `getattr` chain for ruleset resolution
- `tests/cli/test_encountergen_bestiary_90_1.py` — AC6 slug list extended with `mutant_wasteland` (88-2 landed mid-green; deviation logged)

*sidequest-content* (`feat/90-1-encountergen-ruleset-awareness`, pushed — commit `69b78cf`):
- `genre_packs/{heavy_metal,elemental_harmony}/bestiary.yaml` — WWN SRD 1.0 stat lines, 14/13 entries
- `genre_packs/neon_dystopia/bestiary.yaml` — CWN SRD 1.0 foe blocks, 15 entries
- `genre_packs/space_opera/bestiary.yaml` — SWN Revised Free Edition tables, 12 entries
- `genre_packs/mutant_wasteland/bestiary.yaml` — AWN Free Edition foe tables, 14 entries
- All stats extracted from Keith's DriveThruRPG SRD PDFs (3 parallel extraction agents + 1 for AWN); names genre-generic per ADR-120; tiers 1–2 (levels 1–6) fully covered per pack for `pregen` seeding

**Tests:** 8/8 story suite passing (was 7F/1P at RED). Full server suite: 10,944 passed / 0 failed / 344 skipped (post-rebase). Mandatory guards green: `test_wwn_heavy_metal_combat` (3/3, `opponent_default_stats` seating untouched), `test_native_pack_still_generates_via_allowed_classes` (AC5 regression lock), `test_encountergen.py` + `test_pregen.py` suites, live-pack content validation + crossref lint.
**Branch:** `feat/90-1-encountergen-ruleset-awareness` (pushed, both repos)

**Notes for review:**
- Keith decision (2026-06-05, in-session): author ALL starter bestiaries from the Sine Nomine SRDs rather than descope to heavy_metal — resolves TEA's blocking Conflict finding. 88-2's mid-green `ruleset: awn` binding for mutant_wasteland grew this to five packs (deviation logged).
- The branch was rebased mid-green (Keith save-point commit `03537348` includes a `test_pack_load.py` docstring touch-up reflecting 87-4's confrontation changes); full suite re-verified after rebase.
- Two deviations logged (enforcement-point of the REQUIRED contract; AC6 slug-list extension). Both minor.

**Handoff:** To review (The Argument Professional)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (pre-existing lint/format debt on base) | confirmed 0, dismissed 2, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (domain covered by Reviewer directly: tier-fallback pools verified populated for tiers 1–2 in all 5 bestiaries) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (domain covered by Reviewer directly: found ensure_loaded swallow, also caught by rule-checker) |
| 4 | reviewer-test-analyzer | Yes | findings | 10 | confirmed 9, dismissed 1, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 8 | confirmed 8, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (domain covered by Reviewer directly: pydantic field constraints verified, ge=1 bounds, dup-id validator) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (domain covered by Reviewer directly: yaml.safe_load throughout, no eval/pickle/shell, content is operator-authored) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (domain covered by Reviewer directly: dead `rng`/`del rng` lines flagged via test-analyzer) |
| 9 | reviewer-rule-checker | Yes | findings | 5 (67 instances checked across 13 rules) | confirmed 5 (2 downgraded with rationale), dismissed 0, deferred 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 22 confirmed, 3 dismissed (with rationale), 0 deferred

**Dismissals:**
- [preflight] 3 ruff I001 errors + 159 format candidates — all in files ABSENT from the diff, therefore byte-identical to `develop`: pre-existing base-branch debt, not this PR's responsibility.
- [test-analyzer] `attack_bonus` unbounded at model level — negative attack bonuses are SRD-legal (weak/no-skill creatures); no project rule or AC requires a bound, and AC2's int assertion is the agreed contract.

### Rule Compliance (lang-review/python.md, 13 checks × 67 instances + project criticals)

| Check | Verdict | Notes |
|-------|---------|-------|
| 1 Silent exceptions | 1 violation (downgraded M) | `monster_manual_inject.py:95` pre-existing broad except now swallows `EncounterSeedError` — see [RULE]/[SILENT] finding below. All new except blocks specific or noqa'd with rationale. |
| 2 Mutable defaults | compliant (8/8) | `default_factory` used in bestiary.py |
| 3 Type annotations | 1 violation (L) | `_pack_dir_or_skip` missing `-> Path` (test helper) |
| 4 Logging | compliant (10/10) | warning level on all failure paths, lazy %s formatting |
| 5 Path handling | compliant | pathlib throughout; the un-encoded `open` at `encountergen.py:173` is pre-existing, not in diff |
| 6 Test quality | 2 violations (L) | bare truthy `assert output["enemies"]` ×2 (count=2 not pinned); mitigated by per-enemy loops |
| 7 Resource leaks | compliant | with-blocks on sidecar + Span |
| 8 Unsafe deserialization | compliant | `yaml.safe_load` everywhere; JSON parse is in-process trust boundary |
| 9 Async pitfalls | n/a | no async code in diff |
| 10 Import hygiene | 1 violation (L) | bestiary models not exported via `models/__init__` `__all__` (inconsistent with sibling modules) |
| 11 Input validation | compliant | pydantic ge=1 bounds, non-empty + dup-id validators at the content boundary |
| 12 Dependency hygiene | n/a | no dependency changes |
| 13 Fix regressions | 1 violation (downgraded L) | `pregen.py:300` `getattr(...)` defaults ruleset to `"native"` on `pack=None` — see finding below |
| **No Silent Fallbacks** | 1 M + 2 L | ensure_loaded swallow (M); pregen:300 native default (L); CLI flags ignored on bestiary path (L). Tier-pool fallback judged compliant — in-band sampling decision on a validated-non-empty set, mirroring the creatures.yaml precedent, commented. |
| **No Stubbing** | compliant | no placeholders; all five bestiaries fully authored |
| **Verify Wiring** | compliant | non-test consumers: loader→pack field→encountergen→pregen→monster_manual; e2e AC3/AC4 prove the production seed path |
| **OTEL Principle** | 1 violation (M) | success path fully covered (`ruleset` + `encounters_after` on `pregen.seed_manual`); the RAISE path exits before `Span.open` — seeding-failure decision emits no seeding span (per-turn `monster_manual.injected` span still shows `total_encounters=0`) |
| **Test-suite wiring test** | compliant | AC3/AC4 are real-pack → real `seed_manual` → behavior+span; no source-grep tests |

### Devil's Advocate

Assume this is broken. The story sells "fail loud, never a silent empty pool" — but trace the production path: a future ruleset pack ships without a bestiary, `seed_manual` raises `EncounterSeedError`, and `ensure_loaded` (`monster_manual_inject.py:95`) catches `Exception`, logs a warning, and binds the session with an empty pool. At runtime that is *behaviorally identical to the 87-4 bug* — better-worded logs, same empty pool, and now the `pregen.seed_manual` span doesn't even fire on that path (the old code at least emitted `encounters_after=0`). The doctrine the story ships is enforced by CI (the content-contract test names bestiary-less ruleset packs) and by authoring-time validation, not by the runtime. If Keith adds epic-89's Barsoom binding without a bestiary and skips the suite, his session quietly has no reachable hostiles again. Second: nothing pins the failure contract — monkeypatch `_generate_encounter` to return `None` and revert the raise to a warning, and **every test in the suite still passes**. The fail-loud retirement is one revert away from silently un-happening. Third: the stat blocks came from PDF-extraction agents; if an agent hallucinated a number, no test catches it — AC2's 5–22 AC range is the only guard, and TEA explicitly descoped SRD fidelity to authoring judgment. Keith authored-by-proxy; he should spot-check. Fourth: the WIP rebase commit bundles an unrelated `test_pack_load.py` docstring edit — minor scope bleed in history. What saves the verdict: the *story's actual ACs* — populated pools for live packs, span proof, native regression — are all delivered and pinned; the holes are in the *insurance around the failure case*, which is CI-guarded today. These go to a follow-up, on the record, blocking nothing.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `bestiary.yaml` (operator-authored content) → `yaml.safe_load` via `_load_yaml_optional` → `Bestiary` pydantic validation (ge=1 bounds, non-empty entries, dup-id rejection, malformed → loud `GenreLoadError`) → `generate_enemy_from_bestiary` tier-range sampling → `EnemyBlock` → JSON stdout → in-process capture/parse (`_run_cli_capturing_json`) → `manual.add_encounter` (raw dict) → per-turn inject patches via duck-typed `.get()` (`monster_manual.py:198-215`). Safe because: validated at the content boundary, safe_load only, no shell/eval, all downstream consumers tolerate the two new keys.

**Pattern observed:** good — the `_enemy_block_to_dict` None-strip (`encountergen.py:95-100`) keeps native/creatures JSON byte-identical while letting the bestiary path carry its combat layer; mirrors the codebase's serialization-compat idiom. Also good: `EncounterSeedError` message names the file, pack, ruleset, and the log line to check.

**Error handling:** ruleset pack + missing bestiary → encountergen exit 1 with actionable stderr (`encountergen.py` main bestiary branch); pregen converts CLI failure to typed `EncounterSeedError` for ruleset packs, keeps warning-only for native (`pregen.py:~305`); malformed bestiary fails pack load loudly (`loader.py` via `_load_yaml`).

**Findings (none blocking — no Critical/High):**

| Severity | Tag | Issue | Location |
|----------|-----|-------|----------|
| [MEDIUM] | [SILENT][RULE] | `EncounterSeedError` is swallowed by the pre-existing broad `except Exception` at the sole production call site — fail-loud terminates at the session boundary (graceful degradation per ADR-006, OTEL-visible per turn via `monster_manual.injected` `total_encounters=0`, but the story's contract docs oversell runtime behavior) | `monster_manual_inject.py:95` |
| [MEDIUM] | [RULE] | `seed_manual` raises before `Span.open(SPAN_PREGEN_SEED_MANUAL)` — the seeding-failure decision emits no seeding span (old code emitted `encounters_after=0`); emit the span with an error attribute before raising | `pregen.py:~305` vs `:340` |
| [MEDIUM] | [TEST] | The two new failure branches are untested: encountergen exit-1 (no-bestiary ruleset pack) and the `EncounterSeedError` raise — a revert to silent-skip would pass the whole suite | `tests/cli/test_encountergen_bestiary_90_1.py`, `tests/server/dispatch/test_pregen_bestiary_90_1.py` |
| [MEDIUM] | [TEST] | AC4 test doesn't assert the new `ruleset` span attribute (the "which path fired" proof the code comment claims) | `test_pregen_bestiary_90_1.py:79` |
| [MEDIUM] | [TEST] | `Bestiary`/`BestiaryEntry` validators (dup ids, empty entries, ge=1 bounds) have no direct unit tests; content test uses raw `yaml.safe_load`, not `Bestiary.model_validate` | `sidequest/genre/models/bestiary.py` |
| [LOW] | [EDGE][TEST] | Tier-pool fallback (empty tier → full list) untested; verified non-firing for all 5 live bestiaries (tiers 1–2 populated) but unpinned | `encountergen.py` bestiary branch |
| [LOW] | [RULE] | `pregen.py:300` defaults ruleset to `"native"` when `pack=None` — a load-failed ruleset pack takes the warning-only path; moot in practice (load failure breaks the session far earlier, twice-logged) but contract-leaky | `pregen.py:300` |
| [LOW] | [SILENT] | `--class`/`--culture`/`--archetype` silently ignored on the bestiary path (native honors them); dev-facing CLI only | `encountergen.py` bestiary branch |
| [LOW] | [DOC] | Stale docs: `seed_manual` docstring still says "otherwise falls back to humanoid NPCs"; encountergen module docstring omits the bestiary path; AC6 docstring/message says "wwn/cwn/swn" omitting awn; both new test modules carry "RED … FAIL until" framing post-green; `pack.py` bestiary field docstring omits the pregen raise | `pregen.py:208`, `encountergen.py:5`, test files, `pack.py:253` |
| [LOW] | [DOC] | Bestiary header comments claim "hp == average (4.5/HD)" but space_opera/mutant_wasteland use floor (hp 4 at L1, 22 at L5) — header wording should say floor | `space_opera/bestiary.yaml:7`, `mutant_wasteland/bestiary.yaml:8` |
| [LOW] | [TEST][SIMPLE] | Bare truthy `assert output["enemies"]` ×2 (count not pinned); dead `rng = random.Random(90_1); del rng` lines; `_pack_dir_or_skip` missing `-> Path` | `test_encountergen_bestiary_90_1.py:78,105,186-200,42` |
| [LOW] | [TYPE] | `Bestiary`/`BestiaryEntry` not exported in `models/__init__` `__all__` (sibling-module inconsistency) | `sidequest/genre/models/__init__.py` |
| [VERIFIED] | [SEC] | All YAML parsing is `yaml.safe_load` — `loader.py:107,140,230,309,1451`, test file `:135`; no eval/pickle/shell in diff. Complies with lang-review check 8. | — |
| [VERIFIED] | [EDGE] | Native output shape unchanged — `_enemy_block_to_dict` strips None combat keys (`encountergen.py:95-100`); AC5 lock green; all 5 bestiaries populate tiers 1–2 so the pool fallback never fires for live content. Complies with AC5 + No Silent Fallbacks (sampling-decision reading). | — |
| [VERIFIED] | [TEST] | Wiring-test doctrine satisfied — AC3/AC4 drive real pack → real `seed_manual` → pool + span assertions, no source-grep. Complies with CLAUDE.md critical "Every Test Suite Needs a Wiring Test" + "No Source-Text Wiring Tests". | `test_pregen_bestiary_90_1.py` |

**Why the Mediums don't block:** the severity rubric reserves blocking for Critical/High (security, data corruption, missing error handling, races). The error handling here *exists and is correct*; the gaps are failure-path *test* coverage and failure-path *observability* — insurance around a contract whose success path is fully delivered, pinned, and CI-guarded (the content-contract test names any future bestiary-less ruleset pack). All Mediums are captured below as a blocking-for-epic-90 follow-up so they cannot evaporate.

**Subagent coverage:** [EDGE] [SILENT] [TYPE] [SEC] [SIMPLE] domains were settings-disabled; Reviewer covered each directly (tier-fallback verification, ensure_loaded swallow, pydantic constraints, safe_load audit, dead-code flags). [TEST] [DOC] [RULE] specialists ran in full.

**Handoff:** To SM (The Announcer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[Gap, non-blocking] `pregen.namegen_failed (exit_code=1)` also fires for heavy_metal during seeding.** Observed repeatedly in the AC3/AC4 RED runs (both worlds) alongside the expected encountergen failures — namegen exits 1 for some cultures, silently skipped by the same `pregen.py:110` warning-only path. Separate gap from 90-1's encountergen scope (NPC seeding still partially works — evropi had 49 NPCs), but it's the same silent-skip anti-pattern. Also: corpus warning `evropi_zked.txt ... 968 words (threshold 1000)`. Affects `sidequest/server/dispatch/pregen.py` + heavy_metal corpus. Route to a follow-up (epic 90 or corpus hygiene). *Found by TEA during 90-1 RED.*
- **[Conflict, blocking-for-green] Decision-3 fail-loud + AC6 generality forces a 4-pack content lift.** All four live ruleset-module packs (heavy_metal, elemental_harmony, neon_dystopia, space_opera) lack `bestiary.yaml`; under the decided contract their seeding must fail LOUD rather than silently emit 0 encounters — which converts today's silent-0 into a visible failure for three packs that aren't this story's subject. Dev must either author 4 starter bestiaries or descope to heavy_metal with a logged deviation (amending `test_bestiary_requirement_is_ruleset_generic`) + follow-up story. Keith should weigh in. *Found by TEA during 90-1 RED.*
  - **RESOLVED (Dev, 2026-06-05):** Keith chose option (a) — author all starter bestiaries from the real Sine Nomine SRDs (`~/Documents/DriveThruRPG/Sine Nomine Publishing/`). Became a 5-pack lift after 88-2 landed mid-green (see Dev findings below). All five authored + shipped.

### Dev (implementation)
- **Gap** (non-blocking): 88-2 bound `ruleset: awn` to mutant_wasteland mid-story (branch rebase), creating a fifth ruleset-module pack the RED contract predated. Handled in-story: authored `genre_packs/mutant_wasteland/bestiary.yaml` (AWN Free Edition stats) + added the slug to `test_bestiary_requirement_is_ruleset_generic`. Affects `nothing further` (resolved). Watch for the same pattern in future ruleset bindings — the AC6 test now names offenders. *Found by Dev during implementation.*
- **Gap** (non-blocking): TEA's earlier namegen finding stands — `pregen.namegen_failed (exit_code=1)` still fires for some heavy_metal cultures via the same warning-only path in `_run_cli_capturing_json`; 90-1 retired the silent skip for *encounters* on ruleset packs only. NPC-seeding silent-skip is the same anti-pattern. Affects `sidequest/server/dispatch/pregen.py` (namegen branch). Route to epic-90 follow-up per TEA's entry. *Found by Dev during implementation.*
- **Improvement** (non-blocking): bestiary entries carry SRD color (damage/move/morale/skill/save) that `EnemyBlock` doesn't yet surface — only hp/armor_class/attack_bonus reach the Monster Manual. If a future story wants morale checks or damage specs on free-play hostiles, the content is already authored. Affects `sidequest/cli/encountergen/encountergen.py` (EnemyBlock projection). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking-for-epic-90, non-blocking for this PR): the 90-1 fail-loud contract has no failure-path regression tests and degraded failure-path observability — bundle into one follow-up story: (1) test the encountergen exit-1 branch (synthetic ruleset pack, no bestiary → rc 1 + stderr); (2) test the `EncounterSeedError` raise (monkeypatch `_generate_encounter` → None, ruleset pack → raises); (3) emit the `pregen.seed_manual` span (with an error attribute) before raising so the seeding failure is GM-panel-visible at the seeding layer; (4) assert the `ruleset` span attribute in AC4; (5) unit-test the `Bestiary`/`BestiaryEntry` validators; (6) decide whether `ensure_loaded`'s broad except should special-case `EncounterSeedError` (re-raise, or emit a dedicated loud watcher event) — currently graceful degradation per ADR-006 absorbs it. Affects `sidequest/server/dispatch/pregen.py`, `monster_manual_inject.py`, both 90-1 test files. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): doc/content polish sweep — refresh stale docstrings (`seed_manual`, encountergen module header, "wwn/cwn/swn" → "wwn/cwn/swn/awn" in AC6 docstring+message, retire "RED … FAIL until" framing in both 90-1 test modules, extend `pack.py` bestiary field docstring with the pregen raise); fix "hp == average (4.5/HD)" header wording to "floor" in space_opera + mutant_wasteland bestiaries; remove dead `rng`/`del rng` lines; pin `--count` in the two bare truthy asserts; add `-> Path` to `_pack_dir_or_skip`; export bestiary models in `models/__init__` `__all__`. Affects the 90-1 server files + 2 content YAML headers. *Found by Reviewer during code review.*
- **Question** (non-blocking): `--class`/`--culture`/`--archetype` are silently ignored on the bestiary path (native errors-or-honors them). Should the bestiary branch reject unsupported flags loudly, or grow a `--entry <id>` selector? Dev-facing CLI only. Affects `sidequest/cli/encountergen/encountergen.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_bestiary_requirement_is_ruleset_generic`'s pack list is a hand-maintained snapshot (88-2 proved it goes stale mid-flight) — derive the slug list by scanning `genre_packs/*/rules.yaml` for `ruleset != native` so future bindings are auto-covered. Affects `tests/cli/test_encountergen_bestiary_90_1.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Bestiary REQUIRED contract enforced at the generation seam, not as a load-time mandatory file**
  - Spec source: 90-1-session.md, TEA sub-decision 3 ("REQUIRED for ruleset-module packs, fail loud") + ADR-120 mandatory-file loader contract question
  - Spec text: "REQUIRED for ruleset-module packs, fail loud"
  - Implementation: `load_genre_pack` loads `bestiary.yaml` optionally (`GenrePack.bestiary: Bestiary | None`; malformed file still fails loud via GenreLoadError). The REQUIRED contract is enforced at the consumers: encountergen exits 1 with a clear stderr message when `ruleset != native` and no bestiary, and `pregen.seed_manual` raises `EncounterSeedError` instead of silently skipping.
  - Rationale: a load-time mandatory file would break the ~50 test files whose synthetic ruleset-module fixture packs legitimately exercise chargen/dispatch/magic without needing encounters, and would block every non-encounter consumer. The actual doctrine target — "never a silent empty pool" — is fully enforced at the seeding seam, where the bug lived.
  - Severity: minor
  - Forward impact: minor — if a future consumer needs load-time enforcement (e.g. authoring validators), `tools/validate` or the loader can add it; the validator already passes with bestiaries present.
  - → ✓ ACCEPTED by Reviewer: enforcement at the consumer seam is where the 87-4 bug lived and where the contract bites; load-time enforcement would break ~50 synthetic-fixture test files for zero production benefit. Noted (as a separate Medium finding, not a flag on this deviation): the fail-loud terminates at `ensure_loaded`'s pre-existing broad except — see Reviewer Assessment.
- **Extended TEA's `test_bestiary_requirement_is_ruleset_generic` slug list with `mutant_wasteland` and authored a fifth bestiary**
  - Spec source: tests/cli/test_encountergen_bestiary_90_1.py (AC6) + TEA RED assessment ("all four live ruleset-module packs")
  - Spec text: slug tuple `("heavy_metal", "elemental_harmony", "neon_dystopia", "space_opera")`
  - Implementation: added `mutant_wasteland` to the tuple; authored `genre_packs/mutant_wasteland/bestiary.yaml` (AWN Free Edition stats).
  - Rationale: story 88-2 landed mid-green (branch rebase) and bound `ruleset: awn` to mutant_wasteland — a fifth ruleset-module pack the RED contract predates. Under the fail-loud contract its bestiary-less state would loud-fail any seeding path that misses `creatures.yaml`. Strengthening the data-level slug list keeps AC6 honest ("ruleset-generic, not a wwn special case"); Keith's "author all" decision (2026-06-05) covers the fleet, not a count.
  - Severity: minor
  - Forward impact: none — contract covers the whole fleet; future ruleset bindings must add a bestiary or this test names them.
  - → ✓ ACCEPTED by Reviewer: shipping the stale 4-slug list would have made AC6's "ruleset-generic" claim false the day it merged; the data-level extension is the minimal honest fix and the 5th bestiary closes the gap it names. The test's fleet enumeration remains a hand-maintained snapshot — improvement noted in Delivery Findings (derive the slug list from `rules.yaml` scan).

### Reviewer (audit)
- **Bestiary path silently ignores `--class` / `--culture` / `--archetype` CLI flags:** Spec (session + context) never addressed flag behavior on the ruleset branch; native path honors them (match-or-exit), bestiary path neither honors nor rejects them. Not documented by Dev. Severity: L (dev-facing CLI only — pregen passes only `--tier`/`--count`/`--world`; no production caller affected). Recorded as a Low finding, not a flag — but it IS a user-intent silent fallback in CLI context.
- No other undocumented deviations found: the "RulesetModule ABC" routing in the story context's Technical Approach was explicitly superseded by TEA's locked Option B (content bestiary) in the session file — spec-authority hierarchy puts the session decision above the context hint, so that is a documented decision, not a deviation.