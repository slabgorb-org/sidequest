---
story_id: "120-4"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 120-4: World-tier equipment_tables override — loader + CharacterBuilder per-slot merge

## Story Details
- **ID:** 120-4
- **Jira Key:** (not used)
- **Workflow:** tdd
- **Repos:** server
- **Stack Parent:** none (but unblocks 120-1)
- **Branch:** feat/120-4-world-tier-equipment-tables-override

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T14:49:25Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T14:04:47Z | 2026-06-15T14:07:33Z | 2m 46s |
| red | 2026-06-15T14:07:33Z | 2026-06-15T14:23:32Z | 15m 59s |
| green | 2026-06-15T14:23:32Z | 2026-06-15T14:41:02Z | 17m 30s |
| review | 2026-06-15T14:41:02Z | 2026-06-15T14:49:25Z | 8m 23s |
| finish | 2026-06-15T14:49:25Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the final wiring inch — connect.py:930-931 currently calls
  `builder.with_equipment_tables(genre_pack.equipment_tables)` (genre-only). Dev must replace it with
  `builder.with_equipment_tables(resolve_equipment_tables(genre_pack, row.world_slug))` — exactly
  mirroring `resolve_classes(genre_pack, row.world_slug)` already wired six lines below at 937. NOTE:
  do NOT "call with_equipment_tables twice" (genre then world) — `with_equipment_tables` SETS
  `self._equipment_tables`, so a second call REPLACES; the merge must happen in the resolver and be
  passed once. The RED suite drives the production data path resolver→builder→kit (test 8) but does
  NOT drive the connect.py handler itself (no existing chargen test does — they construct the builder
  directly); the connect one-liner is verified the same way `resolve_classes`'s is. Affects
  `sidequest/handlers/connect.py:930` + its import block (line 49-52). *Found by TEA during test design.*
- **Improvement** (non-blocking): 120-2 (road_warrior) almost certainly needs this same capability —
  its CWN sweep moves rig/road items off-genre and `the_circuit` likely has class kits referencing
  them. Once 120-4 lands, confirm 120-2's plan reuses `resolve_equipment_tables` rather than
  re-deriving. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): TEA's test file carried an unused `import pytest` (it uses the
  `monkeypatch` fixture via a parameter, no import needed) — a real `F401` that fails `ruff check`
  and would block `server-check`. Dev removed it as part of GREEN (8/8 still pass, behavior
  unchanged). Affects `sidequest/server/tests/server/test_120_4_world_equipment_tables_override.py`
  (already fixed). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the resolver is genre-agnostic (`resolve_equipment_tables(pack,
  world_slug)`), so 120-2 (road_warrior CWN sweep) can reuse it verbatim — `the_circuit`'s
  rig/road kit items become a `worlds/the_circuit/equipment_tables.yaml` override with no server
  change. Echoes TEA's note; confirmed reusable as built. Affects
  `sidequest/server/dispatch/equipment_tables_resolve.py` (no change needed). *Found by Dev during
  implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): PRE-EXISTING path-traversal — `connect.py:519` builds
  `loader.find(genre_slug) / "worlds" / row.world_slug` from a client-supplied `world_slug`
  (CreateGameRequest → PostgreSQL → `row.world_slug`) with no `Path.resolve()` / containment check
  (CWE-22/-59), then `world_dir / "world.yaml"` is `yaml.safe_load`-ed. NOT introduced by 120-4
  (line 519 is outside this diff; the 120-4 resolver uses a safe `pack.worlds.get()` dict lookup) —
  flagged as an upstream observation. Low severity today (no-auth personal LAN server; safe_load = no
  RCE), rises to medium once ADR-119 authenticated identity exposes the server. Affects
  `sidequest/handlers/connect.py:519` (add `world_dir.resolve()` + assert-inside-pack, or validate
  `world_slug` against `^[a-z0-9_-]+$` at the REST boundary). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the resolver's `genre is None → return world` branch emits an
  `op="merged"` OTEL span though no merge occurred (world-only, no genre baseline). Mirrors
  `inventory_resolve`'s empty-baseline behavior, so it's consistent — but the GM panel can't
  distinguish "world extended genre" from "world stood alone, genre had no kits". A future
  `genre_missing=true` span field would disambiguate. Affects
  `sidequest/server/dispatch/equipment_tables_resolve.py:77` (observability only; no behavior change).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned the resolver API + module location**
  - Spec source: session SM Assessment (seams), 120-4 AC1-AC2
  - Spec text: "loader loads worlds/<w>/equipment_tables.yaml; CharacterBuilder merges world-over-genre"
  - Implementation: tests require `resolve_equipment_tables(pack, world_slug) -> EquipmentTables | None` in `sidequest/server/dispatch/equipment_tables_resolve.py` — a new resolver mirroring `inventory_resolve.resolve_inventory` / `class_resolve.resolve_classes` (one resolver per `*_resolve.py`, the established pattern connect.py imports from).
  - Rationale: the merge needs a single testable seam the call site uses; the resolver pattern is how every other world-over-genre chargen surface is wired. Dev may relocate/rename, but must update the test imports if so.
  - Severity: minor
  - Forward impact: Dev creates that module; connect.py imports from it (parallel to class_resolve).
- **Pinned the merge semantics as APPEND (not replace) + the OTEL span contract**
  - Spec source: Keith's Option-B ruling (2026-06-15), session SM Assessment AC2/AC4
  - Spec text: "per-slot APPEND within each class kit (genre items first, then the world's); guaranteed_grants append by kit_id" / "OTEL span fires when the merge engages"
  - Implementation: tests assert class_tables per-slot append (genre-first ordering), world-only slots/kits added, rolls_per_slot carry-through; guaranteed_grants append by kit_id; and an OTEL `state_transition` with `field='resolved_equipment_tables', op='merged', world_slug=<slug>` on the merge path (no `merged` event on the pure-genre path) — mirroring `inventory_resolve._emit_inventory_merged` (`field='resolved_inventory', op='merged'`).
  - Rationale: append (not replace) preserves the original combined kits (the caverns case the parent story needs); the OTEL field/op names mirror the inventory resolver so the GM panel reads them consistently.
  - Severity: minor
  - Forward impact: Dev must match the field/op names or update the OTEL test; the span name parallels the inventory resolver.
- No other deviations from spec.

### Dev (implementation)
- **Merge semantics for `EquipmentTables.tables` and `rolls_per_slot` (AC2 pinned only
  `class_tables` + `guaranteed_grants`)**
  - Spec source: context — TEA "Dev guidance (GREEN)" #3, 120-4 AC2
  - Spec text: "carry/override rolls_per_slot + tables"
  - Implementation: `tables` merges per-slot APPEND (genre-first, mirroring `class_tables`);
    `rolls_per_slot` is world-OVERRIDES-per-key (`{**genre, **world}`). No test pins either field.
  - Rationale: `tables` (the `random_table` fallback flow) is list-valued like `class_tables`, so
    append keeps merge semantics consistent and preserves both genre + world entries (the caverns
    case). `rolls_per_slot` is a per-slot integer count, not a list — union-append is meaningless,
    so world-override-per-key is the only sensible read and matches the inventory resolver's
    `model_copy` override precedent.
  - Severity: minor
  - Forward impact: none for 120-1 (caverns uses `class_tables`/`guaranteed_grants` only). A future
    world that overrides `tables`/`rolls_per_slot` gets append/override respectively; if a different
    contract is later wanted, it changes only the resolver + a new test.
- No other deviations from spec.

### Reviewer (audit)
- TEA "Pinned the resolver API + module location" → ✓ ACCEPTED by Reviewer: the new
  `equipment_tables_resolve.py` mirrors `inventory_resolve`/`class_resolve` exactly (one resolver per
  `*_resolve.py`); connect.py imports it parallel to `resolve_classes`. Sound and consistent.
- TEA "Pinned the merge semantics as APPEND + OTEL span contract" → ✓ ACCEPTED by Reviewer: code
  matches — `_append_by_key` is genre-first, `op="merged"` / `field="resolved_equipment_tables"`
  mirror the inventory resolver. Verified against tests 4/5/7.
- Dev "Merge semantics for `tables` and `rolls_per_slot`" → ✓ ACCEPTED by Reviewer: `tables` append
  (list-valued, consistent with `class_tables`) and `rolls_per_slot` override (`{**genre, **world}` —
  a scalar count, union is meaningless) are the only sensible reads and match the inventory resolver's
  override precedent. Untested but degenerate for the live caverns case; correctly logged. No FLAG.
- No undocumented deviations found: the diff matches the 5 ACs and the logged deviations; nothing
  diverged silently.

## Sm Assessment

**Why this story exists (re-scope, 2026-06-15).** Spun out of 120-1. During 120-1's green
phase, Dev (Inigo) found the caverns verbatim sweep moves 7 no-WWN-analog dungeon items
(`lockpicks, ten_foot_pole, chalk, spellbook, component_pouch, helmet_iron, potion_healing`)
to the world tier, but the genre chargen kits (`equipment_tables.yaml`: `class_tables` +
`guaranteed_grants`) reference them. Keith ruled **Option B** (world-tier kit override) over the
pragmatic "genre kit references world ids" — so genre kits go SRD-pure and the world re-adds the
flavor. That needs a server capability that doesn't exist. 120-4 is that capability; **120-1 is
parked (backlog) depends-on it** and resumes once this merges. Full context: `.session/120-1-session.md`
(Dev note + Delivery Findings). 120-2 (road_warrior) likely needs it too.

**Routing:** tdd / phased → TEA (Fezzik) for RED. Server-only, fixture-tested.

**Acceptance (sprint YAML 120-4 has the 5 ACs):**
1. `World` model gains optional `equipment_tables`; loader loads `worlds/<w>/equipment_tables.yaml`
   when present, None when absent (ADDITIVE — no-op for worlds without one).
2. `CharacterBuilder` merges world-over-genre at chargen: **per-slot APPEND** within each class kit
   (genre slot items first, then the world's), and `guaranteed_grants` **append by kit_id**. A world
   with no `equipment_tables.yaml` is a verified no-op.
3. Fixture-tested: a synthetic WWN pack + world WITH a world `equipment_tables.yaml` proves the merge
   fires at chargen (rolled kit includes world-tier slot items + grants); a sibling world WITHOUT one
   is unchanged.
4. OTEL span attribute fires when the world-equipment_tables merge engages (OTEL principle).
5. Full server suite green; existing genre-only chargen tests NOT broken (caverns-specific test
   updates are 120-1's job, not this story's).

**Seams for TEA/Dev (measured during 120-1):**
- Model: `sidequest/genre/models/pack.py` — `World` (add `equipment_tables`); `EquipmentTables`
  model already exists (used at genre tier today).
- Loader: `sidequest/genre/loader.py` — world assembly (load `worlds/<w>/equipment_tables.yaml`).
- Builder: `sidequest/game/builder.py:~2497-2617` — kit-roll loop reads `self._equipment_tables`
  (genre). The world's must be merged in; `world_slug` is available to chargen
  (`chargen_mixin.py:1242` already calls `resolve_inventory(pack, world_slug)` — same pattern for
  reaching the world's equipment_tables).
- **Doctrine:** ADR-140 (world owns the catalog), ADR-121 (layered per-field resolution). Keep it
  ADDITIVE so it lands green alone.

**Risk:** ensure the no-op path (world without equipment_tables) is explicitly tested so existing
packs/worlds are provably unaffected — that's what lets 120-4 merge independently of 120-1.

**Handoff:** To TEA (Fezzik) for RED.

## Tea Assessment

**Tests Required:** Yes
**Reason:** Server feature (model + loader + resolver + wiring) — a genuine RED→GREEN cycle.

**Test File:**
- `sidequest-server/tests/server/test_120_4_world_equipment_tables_override.py` — 8 tests.
- Fixtures added to `tests/fixtures/packs/wwn_test_pack/`: genre `equipment_tables.yaml` +
  `worlds/test_world/equipment_tables.yaml` (synthetic ids; inert for existing consumers).

**Status:** RED — 8/8 failing as designed; ready for Dev (Inigo).

### Rule Coverage

| AC | Test | Status |
|----|------|--------|
| AC1 — World model field | `test_world_model_declares_equipment_tables_field` | **fail** (not in model_fields) |
| AC1 — loader loads world file | `test_loader_loads_world_equipment_tables` | **fail** (AttributeError) |
| AC1 — no file → None (additive) | `test_loader_world_without_equipment_tables_is_none` | **fail** (AttributeError); GREEN-guard after |
| AC2 — per-slot append | `test_resolve_equipment_tables_appends_world_slots` | **fail** (no resolver module) |
| AC2 — grants append by kit_id | `test_resolve_equipment_tables_appends_guaranteed_grants_by_kit_id` | **fail** (no module) |
| AC2 — no override = no-op | `test_resolve_equipment_tables_no_world_override_is_genre` | **fail** (no module); GREEN-guard after |
| AC4 — OTEL merge span | `test_resolve_equipment_tables_emits_otel_on_world_merge` | **fail** (no module) |
| AC3/AC5 — wiring: merged tables → rolled kit | `test_world_equipment_flows_through_resolver_into_rolled_kit` | **fail** (no module) |

**Rules checked:** Server CLAUDE.md — behavior through real loader/builder; NO source-text wiring
assertions. The model-field test uses a runtime `World.model_fields` reflection (the allowed
"tripwire" pattern, not a source grep). Wiring test (test 8) drives the production data path
resolver→builder→character kit.
**Self-check:** 0 vacuous tests — every test asserts concrete merged structure / kit membership /
span fields. world_torch (sole `light` item) + world_charm (guaranteed grant) are deterministic, so
test 8's assertions are RNG-independent.

**RED evidence (testing-runner, RUN_ID 120-4-tea-red):** Run A — 8/8 fail with the right causes
(missing model field, AttributeError, `ModuleNotFoundError: ...equipment_tables_resolve`); NO
pack-load/YAML errors (fixtures are valid). Run B — 17/17 existing wwn_test_pack consumers PASS
(no regression from the genre fixture).

### Dev guidance (GREEN)
1. `World` model (genre/models/pack.py) — add `equipment_tables: EquipmentTables | None = None`
   (mirror `inventory`).
2. Loader (`_load_single_world`, ~1634-1781) — `_load_yaml_optional(world_path / "equipment_tables.yaml",
   EquipmentTables)`; pass to the `World(...)` ctor (~1754/1781).
3. NEW `sidequest/server/dispatch/equipment_tables_resolve.py` —
   `resolve_equipment_tables(pack, world_slug) -> EquipmentTables | None`: genre tier when no world
   override; else per-slot APPEND of class_tables (genre-first), append guaranteed_grants by kit_id,
   carry/override rolls_per_slot + tables; emit a `state_transition` watcher event
   (`field='resolved_equipment_tables', op='merged', world_slug`) on the merge path (mirror
   `inventory_resolve._emit_inventory_merged`).
4. Wire connect.py:930 → `builder.with_equipment_tables(resolve_equipment_tables(genre_pack,
   row.world_slug))` (import parallel to `resolve_classes`). Do NOT double-call with_equipment_tables.
5. This story is ADDITIVE — keep the no-override path a verified no-op (the GREEN-guard tests pin it).
   Caverns CONTENT lands in the parked 120-1, not here.

**Handoff:** To Dev (Inigo Montoya) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/genre/models/pack.py` — added optional `World.equipment_tables: EquipmentTables | None
  = None` (additive, mirrors `World.inventory`), with a docstring tying it to ADR-140 and the
  resolver.
- `sidequest/genre/loader.py` — `_load_single_world` reads `worlds/<w>/equipment_tables.yaml` via
  `_load_yaml_optional` and passes it to the `World(...)` ctor; absent file → `None`.
- `sidequest/server/dispatch/equipment_tables_resolve.py` (NEW) — `resolve_equipment_tables(pack,
  world_slug)`: pure genre tier when no world override; else per-slot APPEND of `class_tables`
  (genre-first), `guaranteed_grants` append by kit_id, `tables` append, `rolls_per_slot` override.
  Emits a `state_transition` watcher span — `op="merged"` (field `resolved_equipment_tables`,
  `world_slug`) on the world-merge path, `op="resolved"` negative-confirmation on the pure-genre
  path — mirroring `inventory_resolve`.
- `sidequest/handlers/connect.py` — chargen now resolves world-first: replaced the genre-only
  `with_equipment_tables(genre_pack.equipment_tables)` with a single
  `with_equipment_tables(resolve_equipment_tables(genre_pack, row.world_slug))` (no double-set, per
  TEA's explicit warning; ordered parallel to `resolve_classes`).
- `tests/server/test_120_4_world_equipment_tables_override.py` — removed an unused `import pytest`
  (F401 lint fix; 8/8 still pass).

**Tests:** 8/8 passing (GREEN). Regression: `wwn_test_pack` chargen consumers pass (heavy_metal
chargen integration 7/7, TEA's Run B baseline). `ruff check` + `ruff format --check` clean on all
changed files.

**Genre-tier behavior preserved:** for any world with no override, `resolve_equipment_tables`
returns `pack.equipment_tables` unchanged — identical to the prior genre-only call site — so the
change is provably additive for unmigrated packs (verified by the GREEN-guard tests and the
heavy_metal regression).

**Branch:** feat/120-4-world-tier-equipment-tables-override (pushed, commit 62ec1895)

**Handoff:** To next phase (review)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (8/8 story tests + 7/1 regression; lint/format/pyright clean on diff; tree clean) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (boundary paths assessed manually — see [EDGE] observation) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 medium, 2 low) | confirmed 1 (LOW), dismissed 2, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test quality assessed manually — Rule Compliance #6 + [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (docs assessed manually — [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (types assessed manually — Rule Compliance #3 + [TYPE]) |
| 7 | reviewer-security | Yes | findings | 1 (medium-conf, low-sev, PRE-EXISTING / out-of-diff) | confirmed 1 as upstream finding (not a 120-4 blocker), deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (complexity assessed manually — [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (manual rule-by-rule enumeration below — [RULE]) |

**All received:** Yes (3 enabled returned; 6 disabled via settings, pre-filled + assessed manually)
**Total findings:** 2 confirmed (both LOW / non-blocking), 3 dismissed (with rationale), 0 deferred

**Dismissals (with rationale):**
- [SILENT] #2 unknown/typo'd `world_slug` → silent genre fallback (low): DISMISSED — documented,
  intentional, and systemic (identical to `inventory_resolve.py:197`); the diff did not introduce it.
  Reversing it here alone would be inconsistent with the resolver family.
- [SILENT] #3 empty `guaranteed_grants` list for a kit silently treated as "no world grants" (low):
  DISMISSED — empty list is valid YAML and a plausible deliberate authoring choice; no corruption.
- [SEC] connect.py:519 path build is confirmed real but PRE-EXISTING and out-of-diff — recorded as an
  upstream Delivery Finding, not a 120-4 blocker (the resolver path itself is a safe dict lookup).

## Reviewer Assessment

**Verdict:** APPROVED

A tight, additive, well-patterned change. The new resolver is a structural twin of
`inventory_resolve`/`class_resolve`; the loader + model edits are pure-additive optional fields; the
connect.py wiring is a single gated call that preserves the prior genre-tier behavior exactly. 8/8
story tests GREEN, heavy_metal chargen regression clean, lint/format/pyright clean on the diff. No
Critical or High findings; the one security item is pre-existing and out-of-diff. All confirmed
findings are LOW / non-blocking.

**Data flow traced:** `world_slug` (CreateGameRequest → PostgreSQL `sessions` → `row.world_slug`) →
`resolve_equipment_tables(genre_pack, row.world_slug)` (connect.py:935) → `pack.worlds.get(world_slug)`
(safe in-memory dict lookup; unknown slug → None → genre tier) → `_merge_equipment_tables` → builder
`with_equipment_tables` → rolled kit (`character.core.inventory.items`). Safe within the diff: the
resolver never builds a filesystem path from `world_slug`. (The pre-existing connect.py:519 path build
is the only place `world_slug` touches the filesystem — out of scope here, logged as a Delivery Finding.)

**Pattern observed:** resolver-family convention faithfully followed — `equipment_tables_resolve.py`
is a structural twin of `inventory_resolve.py` (genre-tier baseline, world-merge, `op="merged"` /
`op="resolved"` `state_transition` spans, function-local `publish_event` import to avoid a cycle).
equipment_tables_resolve.py:54-120.

**Error handling:** malformed `equipment_tables.yaml` fails loud (`GenreLoadError`, loader.py:165-174);
only file-absent → `None` (the documented additive no-op). `yaml.safe_load` throughout (no CWE-502).
Compliant with "No Silent Fallbacks".

### Observations
- [VERIFIED] Additive contract — `resolve_equipment_tables(pack, None)` and world-without-file both
  return the genre tier unchanged; the prior genre-only call site is behaviorally preserved (same
  `is not None` gate). Evidence: equipment_tables_resolve.py:72-74; connect.py:935-937; GREEN-guard
  tests 3 & 6. Complies with AC1/AC5 + the additive doctrine.
- [VERIFIED] OTEL Observability Principle — both resolution paths emit a `state_transition`
  (`op="merged"` on world-merge, `op="resolved"` negative-confirmation on genre-only). Evidence:
  equipment_tables_resolve.py:74,78; test 7 asserts the `merged` span fires on world-merge and NOT on
  the genre path.
- [VERIFIED] Merge correctness — `_append_by_key` is genre-first, world-only keys appended, shared
  keys concatenated; grants append by kit_id; `rolls_per_slot` overrides per key. Evidence:
  equipment_tables_resolve.py:27-51; tests 4/5 assert `["genre_rope","world_lockpick"]`, the new
  `light` slot, expert_kit's gained utility, and grants `["genre_tonic","world_charm"]`.
- [SILENT][LOW] `genre is None → return world` emits `op="merged"` though no merge occurred — an
  observability-label imprecision on a degenerate, untested edge (no-genre-baseline pack with a world
  override). Confirmed but LOW: it mirrors `inventory_resolve`'s empty-baseline behavior and the
  behavior itself (world stands alone) is correct. equipment_tables_resolve.py:77. Logged as a
  non-blocking Delivery Finding.
- [SEC][LOW, PRE-EXISTING] connect.py:519 builds a filesystem path from client-supplied `world_slug`
  with no `resolve()`/containment check (CWE-22/-59). NOT in this diff; the 120-4 resolver path is
  safe (dict lookup). Does not block 120-4. Captured as an upstream Delivery Finding (ADR-119).
- [TEST][LOW] the connect.py wiring one-liner (935-937) is not exercised by a test that drives the
  connect.py handler itself — the 8 tests call the resolver directly / construct the builder directly
  (test 8 is the resolver→builder→kit wiring test). This matches `resolve_classes`'s coverage level
  exactly (TEA documented it) and is corroborated by the passing heavy_metal chargen integration
  regression. Acceptable: the call is a straight-line mirror of the line six below it.
- [TEST][VERIFIED] No vacuous assertions — every test asserts concrete merged structure / kit
  membership / span fields; `monkeypatch` patches `watcher_hub.publish_event` at the source module
  (the resolver imports it function-locally, so source-attribute patching is the correct target).
  Python checklist #6 PASS.
- [DOC][VERIFIED] Docstrings accurate — module + `World.equipment_tables` + loader comment describe
  the actual append/override semantics and the additive no-op; the fixture YAMLs document the expected
  merged result inline and it matches the tests. No stale/misleading comments.
- [TYPE][VERIFIED] Full annotations at boundaries — `resolve_equipment_tables(pack: GenrePack,
  world_slug: str | None) -> EquipmentTables | None` and all helpers annotated; no `Any`, no
  `# type: ignore` added; pyright clean on the new file. Python checklist #3 PASS.
- [SIMPLE][VERIFIED] No over-engineering — `_append_by_key` is a 2-line dict comprehension reused for
  tables/slots/grants; no dead code, no speculative abstraction. Minimum code to deliver the merge.
- [EDGE][VERIFIED] Boundary paths covered — None `world_slug`, empty-string (`world_slug or ""`),
  unknown slug (→None→genre), world-only slot, genre-only slot, shared slot, world-only kit. Tests
  4/5/6 + the branch structure cover these; the one uncovered edge (genre None + world present) is the
  LOW [SILENT] item above.

### Rule Compliance (python.md #1-13 + SOUL.md + CLAUDE.md)
- #1 Silent exceptions — PASS. New resolver has no try/except; loader's `_load_yaml` raises
  `GenreLoadError` (loud), never swallows.
- #2 Mutable defaults — PASS. No mutable default args in any new/changed signature.
- #3 Type annotations at boundaries — PASS. `resolve_equipment_tables`, `_merge_equipment_tables`,
  `_append_by_key`, `_emit_merged`, `_emit_resolved` fully annotated; `World.equipment_tables:
  EquipmentTables | None`.
- #4 Logging — PASS (N/A). Module uses the project's required OTEL `publish_event` channel, not stdlib
  logging; no error paths to mis-level.
- #5 Path handling — PASS in-diff. Loader uses `world_path / "equipment_tables.yaml"` (pathlib) +
  `read_text(encoding="utf-8")`. (Pre-existing connect.py:519 path build flagged upstream.)
- #6 Test quality — PASS. No vacuous asserts, correct mock target, deterministic fixtures, a real
  end-to-end wiring test (test 8).
- #7 Resource leaks — PASS (N/A). No file/socket/lock in the diff (the read goes through the existing
  `_load_yaml` helper).
- #8 Unsafe deserialization — PASS. `yaml.safe_load` confirmed; no pickle/eval/exec.
- #9 Async pitfalls — PASS. Resolver is sync, pure dict ops; no blocking-in-async.
- #10 Import hygiene — PASS. No star imports; the function-local `publish_event` import is the
  established sibling pattern (avoids a cycle), not a smell.
- #11 Input validation — PASS in-diff (resolver dict-lookup is safe). connect.py:519 boundary flagged
  upstream (pre-existing).
- #12 Dependency hygiene — PASS. No new deps.
- #13 Fix-introduced regressions — PASS. The only fix was removing an unused import + ruff format; no
  new bug class.
- [RULE] SOUL "No Silent Fallbacks" — PASS. Additive None→genre is documented/by-design; misconfig
  (bad YAML) fails loud.
- [RULE] SOUL "OTEL Observability" — PASS. Every resolution decision emits a span.
- [RULE] ADR-140 "World owns the cast/catalog" — PASS. Genre stays the SRD rulebook; the world adds
  flavor gear via override.

### Devil's Advocate
Suppose this is broken. A careless author ships a world `equipment_tables.yaml` whose
`class_tables.warrior_kit.weapon` duplicates a genre item — the merge appends it, so the kit rolls two
identical blades. Corruption? No — append is the specified contract; de-duplication was never required,
and a duplicate only doubles a roll-table weight, harmless. A world ships a kit_id the genre never had?
`_merge_equipment_tables` unions kit_ids, so the world-only kit is added — correct, tested via
expert_kit's new utility slot. `world_slug` is a typo? `pack.worlds.get()` returns None → genre tier,
silently; a confused author sees their gear not appear with no error to chase — that is [SILENT] #2,
but it is the documented, systemic resolver contract (identical in `inventory_resolve`), so reversing
it here alone would be inconsistent; the right fix is a family-wide diagnostic span, logged upstream. A
stressed filesystem hands back a half-written YAML? `_load_yaml` raises `GenreLoadError` at pack-load,
loud and early, before any session starts — good. Genre ships no kits but the world does? The resolver
returns world-only tables and labels the span `merged` — misleading but not corrupting (finding #1),
and no live WWN/CWN/SWN genre has that shape. `world.equipment_tables` present but every list empty?
`_append_by_key` appends nothing; the genre carries through unchanged — correct no-op. Could the test
flake? The wiring test seeds `random.Random(42)` and asserts on `world_torch` (sole `light` item) and
`world_charm` (a guaranteed grant) — both deterministic regardless of seed, so it cannot flake. Could a
player gain mechanical advantage? Only by authoring an over-powered world kit — that is the author's
content decision (ADR-140 puts the catalog in the world's hands), governed by content review, not an
engine flaw. I cannot find a path in this diff that corrupts state, swallows a real error, or grants
advantage beyond authored intent. Safe to merge.

**Handoff:** To SM (Vizzini) for finish-story.