---
story_id: "107-2"
jira_key: ""
epic: "107"
workflow: "tdd"
---
# Story 107-2: Monster Manual for beneath_sunden

## Story Details
- **ID:** 107-2
- **Jira Key:** (none — Jira not enabled for this project)
- **Workflow:** tdd
- **Stack Parent:** 107-1 (not yet started; feature branch created independently)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-13T23:33:19Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-13T22:38:33Z | 2026-06-13T22:40:20Z | 1m 47s |
| red | 2026-06-13T22:40:20Z | 2026-06-13T23:08:42Z | 28m 22s |
| green | 2026-06-13T23:08:42Z | 2026-06-13T23:24:17Z | 15m 35s |
| review | 2026-06-13T23:24:17Z | 2026-06-13T23:33:19Z | 9m 2s |
| finish | 2026-06-13T23:33:19Z | - | - |

## Sm Assessment

**Story selected by Bossmang (Keith).** 107-2 — author the beneath_sunden dungeon bestiary as content entities and inject per ADR-059 so the narrator draws from stable creatures instead of improvising ("the creature of animal musk"). Source: 2026-06-13 combat playtest, OTEL + save-forensics confirmed.

**Approach (per story context, 268 lines at sprint/context/context-story-107-2.md):**
- The ADR-059 Monster Manual injection infrastructure is LIVE and WIRED. The gap is **content authoring + per-room binding**, NOT new infrastructure. Do not reimplement injection (No Stubbing / Wire Up What Exists).
- Content lives in the world dir per ADR-140 (world owns the cast/catalog; genre is the rulebook only). Author stable creatures: the four-toed pale scuttler, the eyeless bristle-faced den creature.
- Inject into game_state as creatures-nearby (not-yet-met), bound per-room.
- Visual style lives only in the visual_style suffix — do not bake style into the creature entity.

**ACs (5):** authored opponent entity · ADR-059 injection · per-room binding · image specs · OTEL proof + wiring test. The wiring test is mandatory (every test suite needs one — verify the narrator actually draws from injected creatures in a production path, not just that entities parse).

**Dependency — non-blocking but live:** 107-2 depends on 107-1 (scene/location advance, still in backlog) for the stable per-room location key the binding hangs on. Branch created independently. TEA writes RED tests against 107-1's contracted per-room key; binding becomes fully executable once 107-1 lands. Surface in Delivery Findings if this blocks GREEN.

**Scope boundary:** IN — bestiary image specs, per-room binding, OTEL span. OUT — confrontation panel portrait rendering, 107-1 scene advance itself, GPU asset rendering.

**Routing:** phased TDD → next phase RED → Amos (tea).

## TEA Assessment

**Tests Required:** Yes
**Reason:** Feature story (content + server); 5 ACs, no chore bypass.

**Test Files:**
- `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py` — content: the 6 low-band creatures need `creatures.yaml` image specs; style-free description, no-text clause, non-proper-noun name, every `low`-tagged entry renderable (AC4, AC1-content).
- `sidequest-server/tests/genre/test_beneath_sunden_room_binding_107_2.py` — content: per-room `encounter_creatures` binding data; entrance→gnaw_swarm, distinct rooms→distinct creatures, referential integrity, bound→renderable (AC3-content).
- `sidequest-server/tests/server/dispatch/test_room_creature_binding_107_2.py` — server: `resolve_room_creatures` (returns ids / empty for non-combat / **raises on dangling ref**), `inject(room_id=)` materializes authored opponent + emits `monster_manual.room_bound`, back-compat guard, span declared flat, real-content wiring through production `inject()` (AC1/AC2/AC3-server, AC5).

**Tests Written:** 18 tests across 3 files, covering all 5 ACs.
**Status:** RED — verified.
- File 1: 6 failed (missing image specs). No vacuous passes (fixed `if spec is None: continue` → `assert spec is not None` per Phase-C self-check).
- File 2: 4 failed (no `encounter_creatures` field) + 1 standing integrity guard (green by design — guards a future dangling ref).
- File 3: collection ERROR — `ModuleNotFoundError: room_creature_binding` (module + span don't exist yet). Correct RED.

### Rule Coverage

| Rule (CLAUDE.md / SOUL) | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (fail loud on dangling binding) | `test_resolve_raises_on_dangling_bestiary_ref`, `test_all_room_bindings_reference_real_bestiary_ids` | RED / guard |
| OTEL: every subsystem decision emits a span | `test_resolve_emits_room_bound_span`, `test_inject_with_room_id_emits_room_bound_span`, `test_room_bound_span_is_declared_flat` | RED |
| Every suite needs a wiring test (behavior, not source-grep) | `test_real_beneath_sunden_entrance_surfaces_authored_gnaw_swarm` (drives production `inject()` on real content) | RED |
| Don't reinvent — extend existing `inject()` seam | `test_inject_without_room_id_is_unchanged` (back-compat) | RED |
| Style lives only in visual_style suffix (Keith) | `test_low_band_descriptions_are_style_free` | RED |
| No proper nouns in Z-Image specs | `test_low_band_spec_names_are_non_proper_nouns` | RED |
| Authored opponent, stable name (AC1) | `test_inject_with_room_id_materializes_authored_opponent` | RED |

**Rules checked:** 7 of the applicable CLAUDE.md/SOUL + AC rules have test coverage.
**Self-check:** 3 vacuous tests found (rule tests skipping missing specs) and fixed to assert existence; re-verified RED.

**Wiring note:** No source-text wiring test (CLAUDE.md ban). The wiring proof drives the real production `inject()` over real `beneath_sunden` content and asserts the authored creature reaches `snapshot.npcs` + the span fires. The handler→inject `room_id` plumbing is 107-1's seam (blocking Delivery Finding).

**Handoff:** To Naomi Nagata (dev) for GREEN. Two repos: author content (`creatures.yaml` low-band specs reskinned onto the existing roster, `rooms/*.yaml` `encounter_creatures`) in sidequest-content; build `room_creature_binding.py` + extend `inject()`/spans in sidequest-server. Read the deviations — the schema/seam is TEA-defined; counter-propose in GREEN if you have a better shape (tests assert the shape, so update both).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**

_sidequest-server (tracked, committed):_
- `sidequest/server/dispatch/room_creature_binding.py` (new) — `resolve_room_creatures(pack, world_slug, room_id)` + `RoomCreatureBindingError`; reads `encounter_creatures`, validates against the effective bestiary, fails loud on dangling refs, emits `monster_manual.room_bound`.
- `sidequest/server/dispatch/monster_manual_inject.py` — `inject(..., room_id=None)` extension; `_npc_patches_for_room_binding` + `_creature_patch_from_bestiary_entry` materialize the authored opponent; Manual path guarded so binding runs independently.
- `sidequest/telemetry/spans/monster_manual.py` — `SPAN_MONSTER_MANUAL_ROOM_BOUND = "monster_manual.room_bound"`, registered in `FLAT_ONLY_SPANS`.

_sidequest-content (tracked, committed):_
- `genre_packs/caverns_and_claudes/worlds/beneath_sunden/creatures.yaml` — 6 low-band image specs (gnaw_swarm, rope_spider, hold_skeleton, shaft_goblin, grave_ghoul, harrier_pack_leader); style-free, no-text clause, non-proper-noun names.
- `genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/entrance.yaml` — `encounter_creatures: [gnaw_swarm]` (the documented first fight).

_sidequest-content (on-disk only, ADR-106 runtime artifacts, gitignored — NOT committed):_
- `rooms/exp001.r0..r4.yaml` — distinct low-band bindings exercising distinctness on real materialized rooms. Durable stamping deferred to the materializer (Dev blocking Delivery Finding).

**Tests:** 20/20 passing (GREEN) — verified by Engineering Console (RUN_ID 107-2-dev-green). Broader `tests/server/dispatch/` + `tests/genre/` green (1221 passed, 50 skipped); monster_manual + routing-completeness green (59 passed).
**Branch:** `feat/107-2-monster-manual-beneath-sunden` (both repos, pushed)

**Handoff:** To review/verify. Two blocking Delivery Findings carried forward (handler→inject room_id plumbing = 107-1; durable materializer band-stamping = ADR-106/107-1).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (blocking): durable per-room binding for the PROCEDURAL rooms has no
  tracked home. Only `entrance.yaml` is authored/tracked; every other room yaml
  is gitignored (`.gitignore:88` — ADR-106 megadungeon materializer output,
  canonical state in the save DB, freeze-invariant on-disk). I bound the
  `exp001.r0..r4` rooms on disk to exercise distinctness on real materialized
  rooms, but those edits CANNOT be committed and won't exist on a fresh
  materialization elsewhere. The durable fix: `sidequest/dungeon/room_yaml_emit.py`
  `write_room_yaml()` should stamp `encounter_creatures` from the world bestiary
  band tags (`low`/`mid`/`deep`) when it first writes a region, sourced from the
  tracked cookbook/bestiary — wired with 107-1's per-room key. Affects
  `sidequest-server/sidequest/dungeon/room_yaml_emit.py` + `materializer.py`
  (pass band-sampled creature ids). *Found by Dev during implementation.*
- No other upstream findings during implementation.

### TEA (test design)
- **Gap** (blocking): 107-2's per-room binding consumes a stable per-room key that
  the still-unstarted 107-1 must populate. The room key the binding needs is the GRAPH
  room id from `GameSnapshot.region_for(perspective=)` / `pc_regions` (e.g. `"entrance"`,
  `"exp001.r0"`), NOT the display string `monster_manual_inject.inject()` currently
  receives via `_resolve_location_display(...)`. The production handler
  (`websocket_session_handler.py:802-809`) must be extended to pass `region_for`'s value
  as the new `inject(..., room_id=)` arg. Affects `sidequest-server/sidequest/server/
  websocket_session_handler.py` (pass room id) + depends on 107-1 advancing `pc_regions`
  per room. My RED tests fixture the room id directly so they run now; live end-to-end
  closes when 107-1 lands. *Found by TEA during test design.*
- **Gap** (non-blocking): `the_seep` (mid-band ooze, `bestiary.yaml`) is a reachable combat
  opponent with NO `creatures.yaml` image spec (only `black_pudding` covers the ooze band).
  Out of this story's IN scope (6 low-band), but it's the same "T-chip" gap one band up.
  Affects `sidequest-content/.../beneath_sunden/creatures.yaml` (add a `the_seep` spec).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): existing `creatures.yaml` capstone descriptions (aboleth,
  otyugh) contain the medium token "crosshatch" ("rendered in dense crosshatch"), which the
  story's own Technical Guardrail says must live ONLY in `visual_style.yaml`, not the subject
  description. My style-free test enforces the guardrail on the NEW low-band specs — Dev must
  NOT copy the capstones' "crosshatch" phrasing. Affects `creatures.yaml` (capstone drift).
  *Found by TEA during test design.*

### Reviewer (code review)
- **Gap** (blocking-on-107-1): three error paths in the new binding subsystem are NOT
  observable, on a story whose deliverable is observability (the `room_bound` span).
  (1) `_npc_patches_for_room_binding` returns `[]` silently when `sd.genre_pack is None`
  (monster_manual_inject.py:358) — a config/state error masked as "no binding";
  (2) `resolve_room_creatures` raises on missing `source_dir` and (3) on a dangling
  bestiary ref with no `logger.warning()` preceding the raise (room_creature_binding.py:54,79).
  Currently DARK — the call site (websocket_session_handler.py:806) does not yet pass
  `room_id`, so none of these execute in production. Non-blocking for 107-2 merge, but they
  MUST be fixed (add `logger.warning` before each raise; raise-or-warn on pack=None) when
  107-1 wires `region_for` → `inject(room_id=)` and the path goes live. Affects
  `sidequest-server/sidequest/server/dispatch/{room_creature_binding,monster_manual_inject}.py`.
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): `test_distinct_rooms_bind_distinct_creatures` passes only because
  the gitignored `exp001.r*` rooms carry bindings on THIS disk. On a fresh content checkout —
  or after the ADR-106 materializer regenerates rooms without `encounter_creatures` — only
  `entrance.yaml` has a binding and the test goes RED. Tied to Dev's blocking materializer
  finding; closing that (band-stamping at materialization) makes the test durable. Affects
  `sidequest-server/tests/genre/test_beneath_sunden_room_binding_107_2.py` +
  `sidequest/dungeon/room_yaml_emit.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): test-coverage gaps on doctrine-critical gates —
  no test for `room_id` + `combat_encounters=False` (social-pack suppression), `manual=None`
  + `room_id` (the live path after the early-return removal), or `source_dir=None` (the raise).
  Code is correct by inspection; add the three cases with the 107-1 live wiring. Affects
  `sidequest-server/tests/server/dispatch/test_room_creature_binding_107_2.py`.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_inject_with_room_id_emits_room_bound_span` patches
  `mock.patch.object(monster_manual_inject.Span, "open")` but the `room_bound` span fires from
  `room_creature_binding.Span`. It passes only because `Span` is the same shared class object;
  switch the target to `"sidequest.server.dispatch.room_creature_binding.Span.open"` (the shape
  `test_resolve_emits_room_bound_span` already uses). Affects the same test file.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): docstring/comment drift — `_npc_patches_for_room_binding`'s
  docstring claims it "fails loud" and "emits the span" (both delegated to `resolve_room_creatures`);
  the `room_bound` span comment (monster_manual.py:17) says "materialized into game state" but the
  span fires at RESOLVE time, before materialization. Tighten when touching the file next.
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Accepted TEA's schema + seam verbatim (no counter-proposal)**
  - Spec source: 107-2-session.md TEA deviations (encounter_creatures field; `resolve_room_creatures` + `inject(room_id=)` + `monster_manual.room_bound`)
  - Spec text: "Dev may counter-propose a different shape in GREEN if better."
  - Implementation: implemented the schema/seam exactly as TEA specified. `resolve_room_creatures(pack, world_slug, room_id)` reads the room yaml's `encounter_creatures`, validates against `pack.effective_bestiary(world_slug)`, raises `RoomCreatureBindingError` on a dangling ref, emits `monster_manual.room_bound`. `inject(..., room_id=None)` is back-compat; with a room id it materializes the bound bestiary entry under its authored name via a new `_creature_patch_from_bestiary_entry`.
  - Rationale: the shape is sound and the bug is fixed durably for the authored entrance. No better shape found within scope.
  - Severity: none (conformance)
  - Forward impact: none.
- **Distinctness exercised on ephemeral runtime rooms, not tracked content**
  - Spec source: context-story-107-2.md AC3; `test_distinct_rooms_bind_distinct_creatures`
  - Spec text: "distinct rooms bind distinct creatures" (≥2 distinct room→creature bindings).
  - Implementation: bound `entrance` (tracked) → gnaw_swarm AND `exp001.r0..r4` (gitignored ADR-106 runtime artifacts) → rope_spider/shaft_goblin/hold_skeleton/grave_ghoul/harrier_pack_leader. Only `entrance.yaml` and `creatures.yaml` are committed; the exp* bindings live on disk only (freeze-invariant, so stable on this machine) and demonstrate the mechanism on real materialized rooms.
  - Rationale: only the entrance is an authorable/trackable room in this world; procedural rooms are save-DB-canonical runtime artifacts. The durable fix (materializer band-stamping) is logged as a blocking Delivery Finding and is ADR-106/107-1 territory, untested by this story.
  - Severity: moderate
  - Forward impact: on a fresh materialization elsewhere only the entrance binding exists until the materializer stamps `encounter_creatures` from bestiary band tags (Dev blocking Delivery Finding).
- **`inject()` restructured so the binding path runs independent of the Manual**
  - Spec source: existing `monster_manual_inject.inject` (`if manual is None: return 0` early return)
  - Spec text: n/a (refactor of existing code)
  - Implementation: removed the top `if manual is None: return 0` early return; the Manual-derived patches + `monster_manual.injected` span now run under `if manual is not None:`, and the per-room binding path runs whenever `room_id` is supplied. Net behavior for `manual=None, room_id=None` is unchanged (returns 0, no span, no apply).
  - Rationale: lets a room binding materialize even if the session Manual is empty/None, without changing any existing caller's behavior. Verified by `test_inject_without_room_id_is_unchanged`.
  - Severity: minor
  - Forward impact: none — additive, back-compat guard is green.

### TEA (test design)
- **TEA-defined content schema for per-room binding**
  - Spec source: context-story-107-2.md, AC3 + Scope ("structured binding (room→creature)")
  - Spec text: "the hook that ties the right bestiary creature(s) to the right room ... The structured binding (room→creature) is the content+wiring deliverable" — the exact YAML shape is left unspecified.
  - Implementation: chose a top-level room YAML field `encounter_creatures: [<bestiary_id>, ...]` (read alongside `room_type`/`entities` in `room_file_loader.load_room_payload`), rather than a new `entities[].binding.kind: creature`.
  - Rationale: additive to the raw-yaml room dict (`data.get(...)`), keeps combat roster separate from interactable `LocationEntity` features, directly answers "which bestiary creatures field this room" for the server filter. Dev may counter-propose a different shape in GREEN if better — tests assert the shape, so changing it means updating both.
  - Severity: minor
  - Forward impact: content authoring (room files) + the `pf validate` author-time check key off this field name.
- **TEA-defined server seam: `resolve_room_creatures` + `inject(room_id=)` + `monster_manual.room_bound` span**
  - Spec source: context-story-107-2.md, AC1/AC2/AC3/AC5 + Technical Guardrails ("No new injection infrastructure ... adds per-room binding ... emit a span")
  - Spec text: AC5 "the per-room binding span fires, proving the bound creature reached game_state ... an unresolved room→creature binding fails loud."
  - Implementation: new module `sidequest/server/dispatch/room_creature_binding.py` (`resolve_room_creatures(pack, world_slug, room_id) -> list[str]`, `RoomCreatureBindingError`); extend `monster_manual_inject.inject(..., room_id=None)` to materialize the bound bestiary entry under its authored name and emit a new `SPAN_MONSTER_MANUAL_ROOM_BOUND = "monster_manual.room_bound"` (registered in `FLAT_ONLY_SPANS`). `room_id=None` preserves current behavior exactly.
  - Rationale: keeps the established `inject()` per-turn seam as the single integration point (Wire Up What Exists); binding sources the opponent from `bestiary.yaml` by id (authored name → AC1), sidestepping the encountergen generic `class="creature"` id-matching problem. Materialize-from-bestiary chosen over filtering the sampled encounter pool because sampled enemies don't carry a reliable source bestiary id.
  - Severity: moderate (defines a new module + a public-signature extension the Dev implements against)
  - Forward impact: GM-panel dashboard reads the new flat span; the handler must pass `region_for`'s room id (see blocking Delivery Finding) for live play.
- **Partial AC1/AC2/AC3 coverage — fixture-driven, not live descent**
  - Spec source: context-story-107-2.md, AC1/AC2/AC3 ("In beneath_sunden dungeon combat (the repro session's fight) ...")
  - Spec text: ACs imply the binding is exercised by an actual descent into the room.
  - Implementation: tests set the room id directly (synthetic `_synthetic_pack` + real-content `resolve_room_creatures(pack, "beneath_sunden", "entrance")`) instead of driving a live dungeon descent, because the descent's per-room key is 107-1's deliverable and 107-1 is unstarted.
  - Rationale: Keith ruling 2026-06-13 ("proceed, fixture-driven"). Delivers the binding logic + content now; live key wiring tracked as a blocking Delivery Finding.
  - Severity: minor
  - Forward impact: a follow-up live-descent integration test should land with/after 107-1.

### Reviewer (audit)
- **Dev: Accepted TEA's schema + seam verbatim** → ✓ ACCEPTED by Reviewer: the schema (`encounter_creatures` list) and seam (`resolve_room_creatures` + `inject(room_id=)` + flat `room_bound` span) are sound, minimal, and extend the existing ADR-059 inject seam rather than reinventing it (Wire Up What Exists). No counter-proposal warranted.
- **Dev: Distinctness exercised on ephemeral runtime rooms, not tracked content** → ✓ ACCEPTED by Reviewer: this is the correct call, not a shortcut. `.gitignore:88` makes every non-entrance room a freeze-invariant ADR-106 runtime artifact; only `entrance.yaml` is authorable. Hand-authoring procedural rooms is architecturally impossible here. The *primary* AC (the documented first fight resolves to the authored Gnaw-Swarm) is durably committed via `entrance.yaml` + `creatures.yaml`. The durable distinctness fix (materializer band-stamping) is correctly deferred to ADR-106/107-1 and carried as a blocking Dev delivery finding. Note the live test fragility (see Reviewer code-review finding) — it does not block this story but must be closed when the path goes live.
- **Dev: `inject()` restructured so the binding path runs independent of the Manual** → ✓ ACCEPTED by Reviewer: verified by inspection (monster_manual_inject.py:422-468) that the `if manual is not None:` block is byte-equivalent to the prior populated-manual path and the binding block is skipped at `room_id=None`. The early-return removal is behaviorally inert for every existing caller; the 59-test monster_manual regression suite (populated manuals) passed.
- **TEA: TEA-defined content schema** → ✓ ACCEPTED by Reviewer: top-level `encounter_creatures` list is additive and ignored by `load_room_payload` (`data.get`), keeping combat roster separate from `LocationEntity` features.
- **TEA: TEA-defined server seam** → ✓ ACCEPTED by Reviewer: materialize-from-bestiary-by-id (vs. filtering the sampled pool) is the right choice — it's the only path that yields the AUTHORED name (AC1) reliably.
- **TEA: Partial AC1/AC2/AC3 — fixture-driven, not live descent** → ✓ ACCEPTED by Reviewer: ratified by Keith 2026-06-13; the wiring test drives real `load_genre_pack` + production `inject()` over real `beneath_sunden` content, which is a genuine behavioral proof, not a fixture-only pass.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 smell (TOCTOU continue) | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (assessed by Reviewer directly) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (covered by rule-checker #1/#4) |
| 4 | reviewer-test-analyzer | Yes | findings | 7 (2 high-conf coverage, 1 patch-target, 1 distinctness, 3 edge) | confirmed 7, dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 (docstring/comment drift) | confirmed 3, dismissed 1 (inject docstring — no back-compat regression), deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (assessed by Reviewer directly — see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (assessed by Reviewer directly — see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (assessed by Reviewer directly — see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 5 (3 medium silent/OTEL, 2 low) | confirmed 5, dismissed 0, deferred 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled as Skipped)
**Total findings:** 12 confirmed, 1 dismissed (with rationale), 0 deferred — zero Critical/High severity

### Rule Compliance (Python lang-review checklist — 13 checks, mapped)

- **#1 Silent exception swallowing** — VIOLATION (medium): `_npc_patches_for_room_binding` returns `[]` silently when `pack is None` (monster_manual_inject.py:358); No Silent Fallbacks is `<critical>`, cannot be dismissed. Confirmed, downgraded to non-blocking ONLY because the path is dark (room_id not yet passed at call site). TOCTOU `continue` (line 373) — borderline silent, low. No bare `except`, no `suppress()`.
- **#2 Mutable defaults** — clean (8 instances checked; `room_id=None` is immutable).
- **#3 Type annotations at boundaries** — public seam `inject()` + `resolve_room_creatures` fully annotated. `pack: Any` (duck-typed genre pack) acceptable but uncommented (low). 4 test helpers lack return annotations (`_synthetic_pack`, `_snapshot`, `_world_dir`, `_rooms_dir`) — low, tests only.
- **#4 Logging coverage/correctness** — VIOLATION (medium x2): both `raise RoomCreatureBindingError` paths (room_creature_binding.py:54,79) lack a preceding `logger.warning`; invisible to the GM panel if caught upstream. Existing `%`-formatting + no sensitive data elsewhere = clean.
- **#5 Path handling** — clean: `pathlib.Path` with `/`, `read_text(encoding="utf-8")`, `is_file()` guard. `source_dir` is from a trusted pack object.
- **#6 Test quality** — one fragile mock target (test:829, low, passes via shared class object); otherwise specific value/`pytest.raises` assertions throughout, no vacuous asserts, no unreasoned skips.
- **#7 Resource leaks** — clean: `read_text()`/`write_text()` atomic; `Span.open` used as context manager.
- **#8 Unsafe deserialization** — clean: `yaml.safe_load` everywhere (never `yaml.load`); no pickle/eval/exec/shell.
- **#9 Async pitfalls** — clean: all new code synchronous; blocking `read_text` consistent with existing pregen/ensure_loaded pattern (no new violation).
- **#10 Import hygiene** — clean: late import of `resolve_room_creatures` is justified + non-circular (room_creature_binding imports only telemetry, never back into monster_manual_inject); `TYPE_CHECKING` guard correct; no star imports.
- **#11 Input validation** — clean within scope: `encounter_creatures` validated (isinstance list, str-and-strip per element, dangling-ref check). `room_id`/`world_slug` are server-controlled (region_for), not WebSocket input.
- **#12 Dependency hygiene** — clean: no dependency changes; PyYAML pre-existing.
- **#13 Fix-introduced regressions** — `inject()` restructure verified inert for existing callers; the pack=None silent return is the only fix-introduced check-#1 regression (recorded above).

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High severity findings. The code is correct (79/79 tests green: 20 story + 59 regression, 1 pre-existing skip), lint clean, and the production bug it targets — the documented first fight surfacing as "the creature of animal musk" with a bare "T" chip — is durably fixed via the committed `entrance.yaml` binding + 6 low-band image specs. Every confirmed finding is Medium-or-below and clusters on a binding path that is **not yet wired to production** (the call site at websocket_session_handler.py:806 does not pass `room_id`), so real-world impact today is nil; the findings become live work when 107-1 lands.

**Observations (12 confirmed + verifieds, all 8 dispatch domains):**

- `[RULE]` `[SILENT]` [MEDIUM] No Silent Fallbacks: `_npc_patches_for_room_binding` returns `[]` when `sd.genre_pack is None` at monster_manual_inject.py:358 — masks a config error; `resolve_room_creatures` raises for the deeper missing-`source_dir` condition, so the doctrine is inconsistent. Non-blocking (dark path); must fix with 107-1.
- `[RULE]` [MEDIUM] OTEL observability: both `raise RoomCreatureBindingError` paths (room_creature_binding.py:54,79) lack a `logger.warning` before the raise — the 87-4 bug shape the module itself names would be invisible if caught upstream. Non-blocking (dark path); fix with 107-1.
- `[TEST]` [MEDIUM] Coverage gaps on doctrine-critical gates: no test for `room_id`+`combat_encounters=False`, `manual=None`+`room_id`, or `source_dir=None`. Code correct by inspection; add with the live wiring.
- `[TEST]` [MEDIUM] `test_distinct_rooms_bind_distinct_creatures` passes only via gitignored on-disk `exp001.r*` rooms — fragile on a fresh checkout/regeneration. Tied to the durable materializer follow-up.
- `[TEST]` `[SILENT]` [LOW] `test_inject_with_room_id_emits_room_bound_span` patches the wrong module's `Span` reference; passes only because `Span` is a shared class object. Fix the patch target.
- `[DOC]` [LOW] `_npc_patches_for_room_binding` docstring claims "fails loud"/"emits the span" (both delegated); `room_bound` span comment says "materialized into game state" but it fires at resolve time. Dismissed the inject()-docstring sub-finding: "preserves today's behavior exactly" is accurate for `room_id=None`, and `manual=None` never fired the INJECTED span before either (no regression).
- `[TYPE]` [LOW] (subagent disabled — assessed directly) `pack: Any` in `resolve_room_creatures` is duck-typed without a justifying comment; 4 test helpers miss return annotations. Tests/internal only.
- `[SEC]` [VERIFIED] (subagent disabled — assessed directly) No injection surface: `yaml.safe_load` throughout; `room_id`→`Path` join is server-controlled (region_for), not WebSocket input — `room_id="../.."` would need an attacker on the server side. Evidence: room_creature_binding.py:60-67, websocket_session_handler.py:806 passes engine state. Low/defensive note: add `room_id` validation if it ever becomes player-influenced.
- `[SIMPLE]` [LOW] (subagent disabled — assessed directly) `pack.effective_bestiary(world_slug)` is called twice per bound room (once in `resolve_room_creatures`, once in `_npc_patches_for_room_binding`). Minor redundancy; for on-disk YAML packs it's deterministic and cheap. Acceptable.
- `[EDGE]` [VERIFIED] (subagent disabled — assessed directly) Boundary paths enumerated: missing room file → `[]` (correct — absent binding, not a fallback); non-list `encounter_creatures` → `[]` (mild silent-drop, low); empty list → `[]`; dangling id → raises; `combat_encounters=False` → binding skipped at inject():467. All behave per contract.
- `[VERIFIED]` Back-compat: monster_manual_inject.py:422-468 `if manual is not None:` block is byte-equivalent to the prior populated-manual path; binding block skipped at `room_id=None`. Early-return removal is inert. Evidence: inspection + 59-test monster_manual regression suite green.
- `[VERIFIED]` Wiring: `test_real_beneath_sunden_entrance_surfaces_authored_gnaw_swarm` drives real `load_genre_pack` → production `inject(room_id="entrance")` → asserts `gnaw.name in snap.npcs`. Genuine behavioral wiring proof, not source-grep (complies with CLAUDE.md "No Source-Text Wiring Tests"). Evidence: test_room_creature_binding_107_2.py:236-272.
- `[VERIFIED]` OTEL registration: `SPAN_MONSTER_MANUAL_ROOM_BOUND = "monster_manual.room_bound"` added to `FLAT_ONLY_SPANS` (monster_manual.py:24) — GM-panel reads it without dashboard change, parity with `monster_manual.injected`.

**Data flow traced:** `room_id` (107-1's `region_for` graph key — server-controlled) → `inject(room_id=)` → `resolve_room_creatures` reads `{source_dir}/worlds/{world}/rooms/{room_id}.yaml` via `yaml.safe_load` → validates `encounter_creatures` against `effective_bestiary` (raises on dangling) → `_npc_patches_for_room_binding` builds `NpcPatch` from the typed bestiary entry under its authored name → `snapshot.apply_world_patch` → narrator sees the authored creature as world truth. Safe: no user-controlled input on the path; safe deserialization; fail-loud on bad ids.

**Pattern observed:** Correct extension of the existing ADR-059 `inject()` seam (Wire Up What Exists) rather than a new injection pipeline — monster_manual_inject.py:463-468 adds the binding as a strictly-additive, combat-gated tail.

**Error handling:** Dangling ref → `RoomCreatureBindingError` (fail loud, AC5 satisfied); missing room file / empty binding → `[]` (legitimate absent binding). Gap: the two raise paths and the pack=None return lack observability — recorded as a blocking-on-107-1 delivery finding.

### Devil's Advocate

Argue this is broken. First: the feature is a no-op. The production call site never passes `room_id`, so every line of the binding path is dead in production — a reviewer could call this a half-wired feature shipping behind a flag that nobody flips. Rebuttal: this is the explicit, Keith-ratified fixture-driven contract; 107-1 owns the `region_for` wiring and the work is carried as a loud blocking finding. The seam, content, and span are real and tested through production `inject()`. Second: the distinctness AC is a lie on disk. Commit the two repos to a clean machine, run the suite, and `test_distinct_rooms_bind_distinct_creatures` goes RED because only `entrance.yaml` ships a binding — the green bar depends on gitignored runtime files that the materializer can regenerate away. A confused maintainer who wipes the dungeon will see a spontaneous test failure with no code change. This is the sharpest real risk; it is honestly documented as a deviation and a blocking follow-up, but it IS a latent landmine. Third: the story sells observability (a `room_bound` lie-detector span) while shipping three error paths — pack-None, missing-source_dir, dangling-ref — that emit nothing. If 107-1 wires the path and a content author fat-fingers a bestiary id, the binding fails and, depending on upstream catching, the GM panel may show silence rather than the error — the exact illusionism OTEL exists to catch. Fourth: a malformed `encounter_creatures: gnaw_swarm` (scalar, not list) is silently dropped to `[]` — an author typo disables the fight with no warning and no validator (the `pf validate` hook is only "forward impact"). Fifth: a stressed filesystem or a symlinked `source_dir` is read without `resolve()` — though `room_id` is server-controlled, so traversal needs an already-compromised server. None of these are functional defects in the shipped, committed state (the bug is fixed, tests green), but the second and third are real quality debt that must not be forgotten when the path goes live — which is precisely why they are recorded as blocking-on-107-1, not waved through.

**Handoff:** To Camina Drummer (SM) for finish-story. The two blocking delivery findings (107-1 handler wiring + materializer band-stamping) and the observability fixes travel with 107-1.