---
story_id: "54-3"
jira_key: "54-3"
epic: "Epic 54: Persistent Location Descriptions (Mechanical Manifest)"
workflow: "tdd"
---
# Story 54-3: pf validate locations validator — well-formedness + binding resolution + prose-manifest coherence

## Story Details

- **ID:** 54-3
- **Title:** pf validate locations validator — well-formedness + binding resolution (hard) + prose-manifest coherence (warning); CI integration; per-pack/per-world reporting
- **Points:** 3
- **Priority:** P1
- **Workflow:** tdd
- **Stack Parent:** none (independent story in Epic 54)

## Jira & Sync

This is a **personal project** (SideQuest). No Jira tickets. Sprint tracking only via `sprint/current-sprint.yaml`.

## Repos & Branches

| Repo | Base | Branch |
|------|------|--------|
| orchestrator | main | feat/54-3-validate-locations-validator |
| server | develop | feat/54-3-validate-locations-validator |

Both branches created. Ready to start implementation.

## Story Context

**Parent Epic:** Epic 54 — Persistent Location Descriptions (Mechanical Manifest)

**Predecessor:** 54-2 (schema + WebSocket message) — already complete and merged.

**Successors:** 54-4, 54-5 (content backfill — blocked until validator passes).

**Sibling:** 55-1 (procedural cookbook extension — depends on this story for validation).

**Blocked by:** 54-2 (LocationEntity type, Region.entities[] field, cartography schema) — ✓ COMPLETE

**Unblocks:** 54-4 (glenross backfill), 54-5 (beneath_sunden backfill), 55-1 (cookbook extension).

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-19T19:39:43Z 15:05 UTC

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-19 15:05 | 2026-05-19T19:03:59Z | 3h 58m |
| red | 2026-05-19T19:03:59Z | 2026-05-19T19:13:03Z | 9m 4s |
| green | 2026-05-19T19:13:03Z | 2026-05-19T19:26:47Z | 13m 44s |
| spec-check | 2026-05-19T19:26:47Z | 2026-05-19T19:28:50Z | 2m 3s |
| verify | 2026-05-19T19:28:50Z | 2026-05-19T19:32:00Z | 3m 10s |
| review | 2026-05-19T19:32:00Z | 2026-05-19T19:37:25Z | 5m 25s |
| spec-reconcile | 2026-05-19T19:37:25Z | 2026-05-19T19:39:43Z | 2m 18s |
| finish | 2026-05-19T19:39:43Z | - | - |

## Delivery Findings

No upstream findings — 54-2 landed cleanly; its test suite (`test_location_entity_models.py`) + integration fixture (`test_pf_validate_locations_on_materialized.py`) are ready to support this story's validator implementation.

### TEA (test design)

- **Improvement** (non-blocking): The plan at `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md` specifies the fixture pack file as `genre_pack.yaml`, but the actual sidequest-server loader (loader.py:963) reads `pack.yaml`. Fixtures use the correct filename. Affects the plan doc itself (`docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md`, all references to `genre_pack.yaml`) — should be updated to `pack.yaml` so future agents reading the plan don't repeat the mismatch. *Found by TEA during test design.*

### Reviewer (code review)

- **Improvement** (non-blocking): YAML parse errors uncaught throughout `locations.py` (5 `yaml.safe_load` sites). A malformed `cartography.yaml`, `pack.yaml`, `npcs.yaml`, or `scenarios/*.yaml` crashes the whole multi-pack scan with a YAMLError stack trace instead of recording a clean `MALFORMED_YAML` issue. Affects `sidequest-server/sidequest/cli/validate/locations.py` (wrap each `safe_load` in try/except YAMLError, record a `MALFORMED_YAML` Issue). Worth a 1-pt follow-up story; not blocking 54-3 because real packs currently parse cleanly. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `path.read_text()` called without `encoding="utf-8"` at 5 sites in `locations.py` (lang-review rule #5 / CWE-838). Python's default is UTF-8 on macOS/Linux but locale-dependent on Windows. SideQuest is macOS-only in practice — non-issue today, future-proofing later. Affects `sidequest-server/sidequest/cli/validate/locations.py:129, 148, 162, 449, 465`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Proper-noun regex `[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*` splits CamelCase / O'Brien-style names — relevant for real `tea_and_murder/glenross` content (MacGregor, MacRae, etc.). Generates noisy PROSE_DRIFT warnings on real content; warnings are non-blocking by design and the per-pack allowlist exists as the escape hatch. Affects `sidequest-server/sidequest/cli/validate/locations.py:74`. Future polish, not gating. *Found by Reviewer during code review.*
- **Question** (non-blocking): `validate_locations_in_world(world_dir)` infers `pack_slug = world_dir.parent.parent.name`. Fragile for callers that pass paths not shaped `<pack>/worlds/<world>` — issues get tagged with a meaningless pack string but won't crash. 55-1's caller is canonically shaped, so live consumers are fine. Consider an explicit `pack_dir` parameter in a future refactor. Affects `sidequest-server/sidequest/cli/validate/locations.py:441-443`. *Found by Reviewer during code review.*

- **Gap** (non-blocking): The plan defines only `validate_packs([roots])` as the entry surface, but AC-5 plus 55-1's existing post-materialize test require `validate_locations_in_world(world_dir) -> ValidationResult` as the load-bearing programmatic entry. Tests assert BOTH surfaces. Affects `sidequest-server/sidequest/cli/validate/locations.py` (Dev must implement both functions, with `validate_locations_in_world` as the AC-5 contract). *Found by TEA during test design.*

- **Gap** (non-blocking): Story repos field lists `orchestrator,server`, but the plan's Task 6 requires changes in a third repo (`pennyfarthing-dist` at `/Users/slabgorb/Projects/orc-penny/pennyfarthing/pennyfarthing-dist/`) for the `pf validate locations` adapter, and Task 7 (CI integration via `just check-all`) depends on that adapter. The pennyfarthing repo is currently on an unrelated feature branch (`feat/152-1-remove-mssci-hardcoding`) and cannot be safely re-branched in this session. Affects: SM should open a follow-up branch in pennyfarthing-dist for the adapter + `just check-all` wiring after Dev finishes the server side. The server-side CLI (`python -m sidequest.cli.validate locations`) is callable today and 55-1's integration test consumes the validator's Python entry directly — neither depends on the pf adapter. *Found by TEA during test design.*

## Design Deviations

### TEA (test design)

- **Fixture pack filename is `pack.yaml`, not `genre_pack.yaml`**
  - Spec source: `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md`, Task 1 Step 1
  - Spec text: "Create `sidequest-server/tests/fixtures/validate_locations/wf_ok/genre_pack.yaml`"
  - Implementation: All fixture packs use `pack.yaml`; the validator (Dev's job) must also read `pack.yaml` to match real-content discovery (`sidequest/genre/loader.py:963` uses `pack.yaml`).
  - Rationale: The real loader convention is `pack.yaml`. Using `genre_pack.yaml` would make the fixtures non-representative and the validator unable to discover real packs.
  - Severity: minor
  - Forward impact: Dev must implement `_packs_in()` / pack discovery against `pack.yaml`.

- **Programmatic entry is `validate_locations_in_world(world_dir)` per AC-5, not `validate_packs([roots])` from the plan**
  - Spec source: `sprint/context/context-story-54-3.md`, AC-5
  - Spec text: "Programmatic entry (`validate_locations_in_world(world_dir) -> ValidationReport` or equivalent) returns a structured result with `.errors` and `.warnings` lists. Story 55-1's integration test calls this."
  - Implementation: Tests cover both `validate_packs([roots])` (multi-pack CLI helper) AND `validate_locations_in_world(world_dir)` (per-world AC-5 entry). Story 55-1's `test_pf_validate_locations_on_materialized.py` already `importorskip`s the latter — that exact name + signature is non-negotiable.
  - Rationale: Plan only defined the multi-pack helper. AC-5 + 55-1's existing consumer demand the per-world surface as a first-class export.
  - Severity: minor
  - Forward impact: Dev implements both. The 55-1 importorskip will lift automatically once `validate_locations_in_world` exists in `sidequest.cli.validate.locations`.

- **Symmetric well-formedness clause `flavor_only` + binding tested as `FLAVOR_ONLY_FORBIDS_BINDING` OR `MALFORMED_ENTITY`**
  - Spec source: `sprint/context/context-story-54-3.md`, AC-2
  - Spec text: "Well-formedness check rejects: duplicate `id` within a region, `binding` on `tier=flavor_only`, blank `label`, blank `id`, extra fields."
  - Implementation: Plan §Task 1 only enumerates the `real_object → must have binding` direction. AC-2 also requires the symmetric `flavor_only → must NOT have binding`. Test accepts either a dedicated `FLAVOR_ONLY_FORBIDS_BINDING` code OR a generic `MALFORMED_ENTITY` (e.g., if Dev tightens the pydantic model via a discriminator) — Dev picks the implementation.
  - Rationale: AC-2 is the authoritative scope; the plan is incomplete here. Permissive test code keeps Dev's implementation choice open.
  - Severity: minor
  - Forward impact: Dev adds the symmetric check (or model-level constraint).

- **Adapter (Task 6) deferred to a follow-up branch in pennyfarthing-dist**
  - Spec source: `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md`, Task 6 + Task 7
  - Spec text: Plan calls for adapter at `pennyfarthing-dist/src/pf/validate/adapters/locations.py` plus VALIDATORS registration and `just check-all` integration.
  - Implementation: RED phase covers only the server-side validator. Wiring test uses `python -m sidequest.cli.validate locations --help` as the integration surface. Adapter + `just check-all` work is a follow-up branch.
  - Rationale: Story repos field is `orchestrator,server` (pennyfarthing-dist is a third repo not enumerated), and pennyfarthing is currently on `feat/152-1-remove-mssci-hardcoding` with uncommitted work — re-branching there in this session would interrupt unrelated work. The server-side CLI is the load-bearing surface; the adapter is a thin subprocess shim that ships independently as a separate PR. 55-1's consumer hits the Python entry directly, not the `pf` CLI.
  - Severity: minor
  - Forward impact: AC-6 (CI wiring via `just check-all`) and AC-7's second clause ("listed in `pf validate --help`") are partial. SM tracks a follow-up branch in pennyfarthing-dist. Server-side CLI + programmatic entry + 55-1 consumer all work without the adapter.

### TEA (test verification)

- No verify-phase deviations from spec.

### Architect (reconcile)

Three substantive AC mismatches surfaced during spec-check that were not formalized as Design Deviation entries by TEA or Dev. Logging them now for the audit record:

- **AC-3 spec lists `item` as a resolved binding kind; code is a no-op for `item` per ADR-109 deferral**
  - Spec source: `sprint/context/context-story-54-3.md`, AC-3
  - Spec text: "Binding resolution check resolves `binding.kind in {npc, item, clue, scenario_clue}` against the target subsystem (npcs.yaml etc.). Unresolved refs are hard errors with file:line refs."
  - Implementation: `_check_binding` at `sidequest-server/sidequest/cli/validate/locations.py:303-309` early-returns on `kind == "item"` with an explicit comment citing ADR-109's implementation guidance ("canonical item corpus interface hasn't stabilised yet").
  - Rationale: ADR-109 explicitly defers item-binding resolution until the canonical item-corpus interface firms up post-Epic-54. The validator is correctly permissive (no false-positive errors on item bindings) and the deferral is flagged in source for the future story that lands the item subsystem.
  - Severity: minor
  - Forward impact: A follow-up story (post-Epic-54, after item corpus lands) extends `_check_binding`'s `item` branch to load item ids from the canonical store and resolve refs the same way `npc`/`clue` already do. The four-element kind enum in `LocationEntityBinding` is forward-compatible; no schema change required.

- **AC-3 and AC-4 both call for `file:line` diagnostic context; code emits `file` but `Issue.line` always `None`**
  - Spec source: `sprint/context/context-story-54-3.md`, AC-3 and AC-4
  - Spec text: AC-3 — "Unresolved refs are hard errors with file:line refs." AC-4 — "Warnings carry file:line context."
  - Implementation: `Issue.line: int | None = None` (`locations.py:51`) is declared but never populated. Every diagnostic produced by `_check_well_formed_region`, `_check_binding`, and `_check_prose` carries `file` (absolute path) plus `region_id` (logical location within the file) but no source line number. Surfaced by Reviewer as a [LOW] [RULE] finding.
  - Rationale: PyYAML's `safe_load` discards source positions. Populating `Issue.line` requires either a custom `yaml.compose` parse-tree walk (record token positions per key) or switching to `ruamel.yaml` (carries `lc` line/column on every node). Both are non-trivial scope expansions for a polish-only refinement; `file` + `region_id` give actionable signal for grep + IDE jumps today. The Issue dataclass already accommodates `line`, so populating it later is purely additive — no Issue-shape break.
  - Severity: minor
  - Forward impact: Future polish story can add `line` population without touching any of the seven check helpers or the JSON CLI output schema. Existing tests assert on `code` / `message` / `region_id` / `file` — all unchanged.

- **AC-1 user-facing CLI shape `pf validate locations <pack>` (positional) vs server CLI `--genre-packs-root PATH` (option)**
  - Spec source: `sprint/context/context-story-54-3.md`, AC-1
  - Spec text: "`pf validate locations <pack>` runs every wired world in the pack; exit code 1 on any hard error, 0 otherwise."
  - Implementation: The server-side click command at `sidequest-server/sidequest/cli/validate/locations.py:531` exposes the genre-packs root via `--genre-packs-root PATH` (an option, repeatable, defaulting to `DEFAULT_GENRE_PACK_SEARCH_PATHS` when omitted). The user-facing `pf validate locations <pack>` positional shape is the **adapter's** responsibility — the adapter (deferred to a pennyfarthing-dist follow-up branch per TEA-4) translates the positional `<pack>` arg into `--genre-packs-root <pack>` when invoking the server CLI.
  - Rationale: This is the correct architectural seam. The server CLI is the implementation tier (testable in isolation, no `pf` dependency); the `pf validate` adapter is the user-facing tier (consistent with sibling validators `pf validate adr`, `pf validate sprint`, etc.). Forcing the positional shape into the server CLI would couple it to the pf CLI conventions and complicate direct invocation from CI (`uv run python -m sidequest.cli.validate locations --genre-packs-root ...`) or from 55-1's programmatic consumer (which uses the Python entry directly, not either CLI shape).
  - Severity: minor
  - Forward impact: The pennyfarthing-dist follow-up branch's adapter MUST honour AC-1's positional `<pack>` invocation shape — translate `pf validate locations <pack>` to a subprocess call `uv run python -m sidequest.cli.validate locations --genre-packs-root <pack>`. The two LOW [SILENT] / [RULE] / [SIMPLE] follow-up issues Reviewer surfaced are orthogonal to this seam and remain non-blocking.

### Existing deviations review

Verified the four TEA entries and three Dev entries against the actual code paths, the spec, and the merged-on-develop sibling stories (54-1, 54-2, 55-1):

- All seven entries have all 6 required fields (description, spec source, spec text, implementation, rationale, severity, forward impact).
- Every spec source path resolves to a real document on disk (verified `sprint/context/context-story-54-3.md`, `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md`, and `sidequest/genre/loader.py:963`).
- Every quoted spec text matches the source verbatim.
- Every implementation description matches what `git diff develop...HEAD` shows on the branch.
- Every forward impact prediction is consistent with the downstream story dependencies (54-4, 54-5 content backfill, 55-1 procedural stitch — already landed and now consuming the new validator).

No corrections to existing entries needed.

### AC deferral verification

This story did not produce a formal AC accountability table via an `ac-completion` gate. Cross-referencing Dev's AC table in the Dev Assessment against Reviewer's findings and my own spec-check analysis:

- **AC-1, AC-2, AC-3 (excluding item kind), AC-4, AC-5** — fully delivered, all VERIFIED by Reviewer with line-level evidence.
- **AC-3 (item kind)** — explicitly deferred per ADR-109; logged above under Architect (reconcile).
- **AC-3/AC-4 (line refs)** — partially delivered (file + region_id, no line number); logged above under Architect (reconcile).
- **AC-6 (`just check-all` integration)** — deferred to pennyfarthing-dist follow-up branch; TEA-4 covers the scope rationale.
- **AC-7 (`pf validate --help` listing)** — same disposition as AC-6.

No deferred AC was inadvertently addressed or invalidated during Reviewer's pass. The substantive scope of 54-3 (server-side validator, programmatic entry for 55-1, comprehensive test matrix) is fully shipped.

### Reviewer (audit)

All seven existing deviation entries reviewed and stamped:

- **TEA-1 (pack.yaml filename)** → ✓ ACCEPTED by Reviewer: matches `sidequest/genre/loader.py:963` convention; using `genre_pack.yaml` would have left the validator unable to discover real content. The plan doc should be updated as a tiny follow-up (Tech Writer or any agent touching that file next).
- **TEA-2 (validate_locations_in_world signature)** → ✓ ACCEPTED by Reviewer: AC-5 explicitly names this signature and 55-1's importorskip lock-in makes it non-negotiable. Dev correctly implemented BOTH `validate_packs([roots])` and `validate_locations_in_world(world_dir)`; the cross-story importorskip lift on green confirms the contract holds.
- **TEA-3 (flavor_only symmetric clause)** → ✓ ACCEPTED by Reviewer: AC-2 wording ("`binding` on `tier=flavor_only`") explicitly demands the check. Dev added a dedicated `FLAVOR_ONLY_FORBIDS_BINDING` issue code (actionable for content authors) rather than smearing it into `MALFORMED_ENTITY`. Cleaner than the permissive alternative.
- **TEA-4 (adapter deferred)** → ✓ ACCEPTED by Reviewer: pennyfarthing-dist is a third repo with an unrelated in-flight feature branch (`feat/152-1-remove-mssci-hardcoding`). Forcing a cross-repo branch shuffle in this story would have risked the 152-1 work. Captured as SM follow-up in the assessment handoff section.
- **Dev-1 (regex tightening to `[a-z\-']{0,40}`)** → ✓ ACCEPTED by Reviewer: the original `[a-z\-' ]{2,40}` quantifier was a genuine bug — whitespace in the character class made the regex greedy across word boundaries, so "the well at the centre" matched as a single 30-character head. The fix is correct, tightly scoped, and the test suite proves the fix doesn't regress single-word matching. Bonus: the commit subject + body honestly describe the bundled implementation rather than pretending it was just a one-line fix.
- **Dev-2 (coherence_npc_resolved fixture prose tightened)** → ✓ ACCEPTED by Reviewer: TEA's original prose ("polishing a glass and watching the door") had drift triggers unrelated to the NPC-name-resolution claim under test. Dev's tightened version ("At the bar stands Cassia.") makes the test assert what the docstring says — clean NPC resolution mid-sentence with sentence-initial false-positive avoided. Fixture-only change; no test code modified.
- **Dev-3 (empty orchestrator branch)** → ✓ ACCEPTED by Reviewer: scope-correct. Server is the load-bearing repo; the orchestrator-side `just check-all` edit was deferred to the pennyfarthing-dist follow-up branch (per TEA-4). SM should delete the empty orchestrator branch rather than try to merge nothing.

No undocumented deviations spotted during review.

### Dev (implementation)

- **Definite-noun regex tightened from `[a-z\-' ]{2,40}` to `[a-z\-']{0,40}` (no whitespace)**
  - Spec source: `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md`, Task 3 Step 3
  - Spec text: `_DEFINITE_NOUN_RE = re.compile(r"\b(the|a|an)\s+([a-z][a-z\-' ]{2,40})", re.IGNORECASE)`
  - Implementation: `_DEFINITE_NOUN_RE = re.compile(r"\b(the|a|an)\s+([a-z][a-z\-']{0,40})", re.IGNORECASE)` — drops the space from the class so the head is a single word, not a noun-phrase.
  - Rationale: The plan's greedy whitespace-inclusive quantifier captured across word boundaries — `"the well at the centre"` matched as one phrase instead of `"the well"` + `"the centre"`. That broke `test_allowlist_silences_generic_phrases` (allowlist entries are word-grained) and `test_known_npc_name_in_prose_does_not_warn` (the bar/Cassia phrase ran together). Single-word heads compose correctly with the allowlist + entity-label sets and still cover the real authoring vocabulary (`the well`, `the bar`, `the door`, etc.).
  - Severity: minor
  - Forward impact: Multi-word entity labels (`the iron-bound chest`) no longer match by full-phrase against the head regex; they match by head-stem (`chest`) via `entity_heads`. The fixture matrix exercises both single- and multi-word labels and stays green. If a future author needs to silence a specific multi-word phrase, they add it to `generic_allowlist[]` (which we tokenize twice — full form and article-stripped form — so multi-word allowlist entries still hit).

- **`coherence_npc_resolved` fixture prose tightened to isolate the AC-4 NPC-resolution intent**
  - Spec source: `tests/cli/test_validate_locations.py::test_known_npc_name_in_prose_does_not_warn` docstring
  - Spec text: "The fixture is constructed so NOTHING in the prose should drift — asserts no PROSE_DRIFT warnings at all."
  - Implementation: Changed prose from `"Cassia leans on the bar, polishing a glass and watching the door."` to `"At the bar stands Cassia."`
  - Rationale: TEA's original prose included `"a glass"` and `"the door"` — phrases that have no entity, NPC, or allowlist counterpart in the fixture, so they would correctly drift even with a perfectly-working validator. The test docstring explicitly states the fixture should produce zero drift, so the prose itself was the bug, not the assertion. Tightened to `"At the bar stands Cassia."` — `the bar` resolves to the bar_counter entity (label `the bar`), `Cassia` is mid-sentence (not skipped by sentence-initial guard) and resolves to the `cassia` NPC token. Sentence-initial `"At"` is correctly skipped by the proper-noun guard. Net coverage is exactly what TEA intended: a known NPC name mid-sentence is recognized and does not warn.
  - Severity: minor
  - Forward impact: None — fixture-only change. The AC-4 assertion remains the load-bearing claim; the simplified prose makes it actually testable.

- **Empty orchestrator branch — server-only scope confirms no orchestrator commits needed**
  - Spec source: session file Repos & Branches table; story repos field `orchestrator,server`
  - Spec text: SM created `feat/54-3-validate-locations-validator` in both orchestrator and server with the implication that both would carry commits.
  - Implementation: Server branch has three commits (test + impl + lint cleanup) and is pushed. Orchestrator branch is identical to `main` — zero commits — because all scoped work (validator core, CLI, tests, fixtures) lives in the server repo, and the orchestrator-side CI integration (Task 7's `just check-all` edit) was deferred to a pennyfarthing-dist follow-up per TEA's earlier deviation.
  - Rationale: Adding a no-op commit to the orchestrator branch would be pure ceremony. The empty branch can be deleted by SM's finish ceremony or simply ignored — server PR is the load-bearing artifact for this story.
  - Severity: minor
  - Forward impact: SM should not attempt to create a PR for the empty orchestrator branch. The follow-up branch in pennyfarthing-dist will own the `pf validate --help` registration and the `just check-all` CI wiring.

## Story Specification

### What We're Building

A new `pf validate locations` validator that enforces three checks against every genre pack's location manifests:

1. **Well-formedness (hard error):** entities parse as `LocationEntity`, no duplicate ids per region/room, `real_object` entities must have a binding.
2. **Binding resolution (hard error):** `binding.ref` resolves in the target subsystem (`npcs.yaml`, scenarios, etc.). `location_feature` bindings are free-form.
3. **Prose-manifest coherence (warning, non-blocking):** description prose text must not mention entity names, NPC names, or common-noun phrases that aren't in the manifest, NPC list, or a per-pack `generic_allowlist[]`.

Hard-error checks gate CI. Warning checks are observable but never blocking. **The spec emphasizes: errors are ∈ NO_SILENT_FALLBACK doctrine — failures must be loud and discoverable.**

### Architecture & Cross-Repo Wiring

**Core logic** lives in `sidequest-server/sidequest/cli/validate/locations.py` (Python, importable + CLI-runnable with `--json` flag).

**pf adapter** lives in `pennyfarthing-dist/src/pf/validate/adapters/locations.py` and shells out to the server CLI, parses JSON, returns `ValidateReport`.

**Standalone runnable:** `uv run python -m sidequest.cli.validate locations` (or with `--json` for machine-readable output).

**CI integration:** add `pf validate locations` to the orchestrator's `just check-all` recipe.

### File Map

| File | Action | Responsibility |
|---|---|---|
| `sidequest-server/sidequest/cli/validate/locations.py` | create | Core validator logic (all 3 checks) + Click CLI. |
| `sidequest-server/sidequest/cli/validate/__main__.py` | modify | Register `locations` subcommand in the CLI router. |
| `sidequest-server/tests/cli/test_validate_locations.py` | create | TDD suite (well-formedness, binding resolution, prose coherence). |
| `sidequest-server/tests/fixtures/validate_locations/...` | create | Fixture genre packs (wf_ok, wf_duplicate_id, wf_real_object_no_binding, binding_bad_npc, coherence_drift, coherence_npc_resolved). |
| `pennyfarthing-dist/src/pf/validate/adapters/locations.py` | create | Adapter shelling to server CLI. |
| `pennyfarthing-dist/src/pf/validate/cli.py` | modify | Register "locations" in VALIDATORS dict. |
| `pennyfarthing-dist/src/pf/tests/test_validate_locations_adapter.py` | create | Adapter unit tests (mocked subprocess). |
| `orchestrator/justfile` | modify | Add `pf validate locations` to `check-all` recipe. |
| `orchestrator/.github/workflows/ci.yml` | modify if exists | Add validator to CI matrix (optional — may not exist yet). |

## Acceptance Criteria

From spec §5.1 + plan §Task 1-7:

- [ ] **Well-formedness check:** entities parse via pydantic, detect duplicate ids per region/room, reject real_object without binding. Tests: 3+ covering each error code.
- [ ] **Binding resolution check:** npc/clue/scenario_clue refs resolve against world npcs.yaml + scenarios/*.yaml. location_feature is free-form. Item-binding deferred. Tests: 2+ covering npc resolution + free-form location_feature.
- [ ] **Prose-manifest coherence (warning):** regex scans description for "the X" / proper nouns, flags unresolved tokens. Per-pack `generic_allowlist[]` silences common phrases. Tests: 3+ covering drift detection, allowlist, NPC resolution.
- [ ] **Core CLI runnable:** `python -m sidequest.cli.validate locations [--json] [--genre-packs-root PATH]`. Exits 0 on success, 1 on hard errors. Warnings never block.
- [ ] **pf adapter:** shells to server CLI, parses JSON, returns ValidateReport. Handles subprocess missing gracefully (LocationsCliMissingError).
- [ ] **pf routing:** `pf validate locations` command callable from orchestrator root, lists validators in `pf validate --help`.
- [ ] **CI wired:** `just check-all` includes `pf validate locations`. Pass against real content (no errors; warnings expected on packs without full backfill yet).
- [ ] **Linting & formatting:** ruff format + ruff check pass on all new Python code.
- [ ] **All tests green:** `uv run pytest tests/cli/test_validate_locations.py -v` passes on server side; adapter tests mocked and green.

## Technical Decisions

### 1. Per-pack `generic_allowlist[]` in `genre_pack.yaml`

Standard phrases like "the day", "the weather", "the village" go into a per-pack allowlist to avoid false-positive prose-coherence warnings. Loaded once per pack at validator init; checked during prose scan.

### 2. Item-binding check deferred (placeholder in code)

The canonical item corpus interface isn't yet stabilized (post-54 work). The check is a no-op returning empty set; flagged in code with explicit rationale. Will expand when interface firms up.

### 3. Error codes and severity

Five issue codes:
- `MALFORMED_ENTITY` (error) — pydantic validation failed
- `DUPLICATE_ENTITY_ID` (error) — same id twice in a region/room
- `REAL_OBJECT_REQUIRES_BINDING` (error) — real_object with no binding
- `BINDING_UNRESOLVED` (error) — binding ref doesn't resolve
- `PROSE_DRIFT` (warning) — description mentions unmanaged noun phrase

### 4. Prose tokenization

Two regex patterns:
- Definite phrases: `\b(the|a|an)\s+([a-z][a-z\-' ]{2,40})` → matches "the well", "the notice board", etc.
- Proper nouns: `\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b` → matches "Cassia", "Sludge Fen", etc.

Skip sentence-initial tokens to reduce false positives.

### 5. Loose model loading, strict validator check

Pydantic allows lenient loading (real_object without binding is permitted at model level per test_location_entity_models.py). The validator enforces the cross-field invariant at author time. This lets runtime loading be resilient while CI ensures quality.

## Implementation Plan

See `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md` (Tasks 1-7) for step-by-step breakdown. This file replicates the plan's task structure in checkbox form. Each task is:

1. **Create fixture genre packs** (Tasks 1.1)
2. **Write failing TDD tests** (Tasks 1.2–3)
3. **Implement core validator logic** (Tasks 2–3)
4. **Wire CLI subcommand routing** (Task 4)
5. **Validate real content** (Task 5)
6. **Create pf adapter** (Task 6 — in pennyfarthing repo, separate branch/PR)
7. **Wire into CI** (Task 7)

Each task ends with a commit. Intermediate commits are encouraged; final commits fold into the story's PR.

## Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Prose-coherence warnings produce too many false positives | Per-pack `generic_allowlist[]` + sentence-initial skip + npc-name resolution. Warnings are non-blocking; content authors refine over time. |
| Binding resolution is incomplete (items, etc.) | Placeholder returns empty set; code is explicitly flagged; interface stabilization per ADR spec. Not a blocker for 54-3 scope. |
| Fixture content size explodes | Six minimal packs, each ~5 files. Each pack fits in ~50 lines YAML. Test paths are deterministic (under `tests/fixtures/validate_locations/`). |
| sidequest-server not available when pf adapter runs | LocationsCliMissingError caught and translated to a ValidateReport error. CI can still fail gracefully. |

## Handoff Notes

- **Dev phase:** Implement Tasks 1–5 and 7 in this repo (orchestrator + server branches).
- **Before TEA review:** Commit against the server + orchestrator branches; create a draft PR. Adapter PR is separate (pennyfarthing repo) and can be opened after server PR merges.
- **Before finish ceremony:** All three repos must have merged branches (orchestrator main, server develop, pennyfarthing develop). The validator must be callable via `pf validate locations` from the orchestrator root.

## SM Assessment

Phased TDD story, predecessors 54-1 (ADR) + 54-2 (schema) merged; 55-1 stitch landed today and added `sidequest-server/tests/integration/test_pf_validate_locations_on_materialized.py` — Radar should decide whether the new red-phase tests extend that fixture or live alongside.

Repos field is `orchestrator,server` but the handoff notes call out a third repo (pennyfarthing for the `pf` adapter). Treat the adapter as out-of-scope for this branch unless Charles/Radar decide otherwise — if the adapter does need a branch, it must be opened in pennyfarthing-dist against develop and tracked separately.

Both branches are off the correct bases per repos.yaml (orchestrator/main, server/develop). Routing to Radar for red phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Three-check validator with a structured Issue surface, a CLI exit-code contract, and a programmatic entry already consumed by a sibling story (55-1) — every AC needs at least one paranoia test, several need two or three.

**Test Files:**
- `sidequest-server/tests/cli/test_validate_locations.py` — 23 tests across all seven ACs (AC-1 CLI exit codes, AC-2 well-formedness, AC-3 binding resolution, AC-4 prose coherence + warning-never-blocks, AC-5 programmatic entry, AC-6 multi-pack discovery, AC-7 wiring).
- `sidequest-server/tests/fixtures/validate_locations/` — eleven fixture packs, each constructed so exactly one diagnostic should fire (or none, for the ok cases), so overlapping checks cannot mask each other:
  - `wf_ok` (clean baseline + `generic_allowlist`)
  - `wf_duplicate_id` (DUPLICATE_ENTITY_ID)
  - `wf_real_object_no_binding` (REAL_OBJECT_REQUIRES_BINDING)
  - `wf_flavor_only_with_binding` (symmetric AC-2 clause omitted from the plan)
  - `wf_malformed` (blank id + blank label + extra field, all three must surface independently)
  - `binding_bad_npc` (BINDING_UNRESOLVED via npc)
  - `binding_bad_clue` (BINDING_UNRESOLVED via scenario_clue; includes a scenarios/*.yaml with valid clues to prove the resolver actually looks)
  - `binding_location_feature_ok` (location_feature is free-form; must NOT error even with an obviously-fake ref)
  - `coherence_drift` (PROSE_DRIFT warning + assertion that it stays out of `.errors`)
  - `coherence_npc_resolved` (known NPC name in prose does not warn)
  - `room_level` (per-room `rooms/<id>.yaml` entities — the materializer-emit code path from Epic 55)

**Tests Written:** 23 tests covering all 7 ACs.
**Status:** RED (collection blocked by `ModuleNotFoundError: sidequest.cli.validate.locations` — confirmed by testing-runner, 100% failing on the desired signal).

### Rule Coverage

| Rule (CLAUDE.md / server CLAUDE.md) | Test(s) | Status |
|---|---|---|
| **No Silent Fallbacks** | `test_per_world_entry_accepts_world_with_no_cartography` (negative — empty world is explicit-empty, not a silent error swallow); `test_malformed_entries_report_each_independently` (all three malformed entries reported, not short-circuited) | failing |
| **Every Test Suite Needs a Wiring Test** | `test_cli_subcommand_help_runs` (subprocess hits the real `__main__.py` routing); `test_55_1_consumer_can_import_validate_locations_in_world` (real non-test consumer wiring through Story 55-1) | failing |
| **Verify Wiring, Not Just Existence** | The 55-1 consumer test (above) is the load-bearing wiring assertion — once Dev lands the entry, 55-1's `importorskip` stops skipping and the cookbook→validator pipeline goes green | failing |
| **No Stubbing** | `test_malformed_entry_carries_source_file_path` (every diagnostic has real file/region/pack metadata — placeholder-empty fields would surface) | failing |
| **Tests must not point at live content** (per user memory `feedback_tests_not_point_at_content.md`) | All fixtures are minimal, fixture-pack-only — no reference to `tea_and_murder`, `caverns_and_claudes`, `beneath_sunden`, or any live pack slug | n/a (preventive) |
| **Cliché-judge: avoid pet-word fixtures** (per user memory `feedback_made_up_names.md`) | Fixtures use `village_square`, `the_glenross_arms`-style mundane nouns; no "Reach", "Veil", "Spire", "Hollow", "Drift", "Mire", "Shroud", "Sanctum", "Bastion" | n/a (preventive) |

**Rules checked:** 6 applicable rules have direct or preventive test coverage.
**Self-check:** No vacuous assertions — every test asserts a specific issue code, count, message substring, or structural property. No `assert True`, no `is_none()` on always-None, no bare `let _`-equivalents (Python: `_ = result`).

### Test Paranoia Notes

- **Multi-issue regions:** `wf_malformed` deliberately puts three independently-bad entities in one region. The test asserts `len(malformed) == 3` so that a "report-first-error-and-stop" implementation surfaces as a test failure, not a passing-but-wrong validator.
- **Warning/error confusion:** `test_prose_drift_never_promoted_to_error` is the dedicated guard against the most plausible Dev mistake — accidentally classifying PROSE_DRIFT as an error and breaking CI on every authored pack. Paired with `test_cli_exits_zero_on_warning_only_pack` for the same invariant at the CLI surface.
- **Symmetric AC-2 clause:** Plan only enumerated `real_object → must have binding`. AC-2 also requires `flavor_only → must NOT have binding`. Test accepts either a dedicated `FLAVOR_ONLY_FORBIDS_BINDING` issue code OR a generic `MALFORMED_ENTITY` so Dev can choose whether to add a custom validator check or tighten the pydantic model.
- **Cross-story wiring:** `test_55_1_consumer_can_import_validate_locations_in_world` is the literal wiring assertion that 55-1's `importorskip` ceases to skip. When this test goes green, 55-1's `test_validator_reports_no_hard_errors_on_cookbook_yamls` also goes green automatically — proving the producer/consumer loop closes.

**Handoff:** To Dev (Charles) for implementation. The plan at `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md` is mostly correct; see Design Deviations for the three plan corrections he must apply (`pack.yaml` not `genre_pack.yaml`, both entry surfaces, symmetric flavor-only clause). Adapter (Task 6) + CI wiring (Task 7) deferred to a follow-up pennyfarthing-dist branch — Dev focuses on the server side only.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server repo):**
- `sidequest/cli/validate/locations.py` — new — Three-check validator (well-formedness, binding resolution, prose-manifest coherence) + per-world programmatic entry (`validate_locations_in_world`) + multi-pack CLI helper (`validate_packs`) + click CLI (`main`).
- `sidequest/cli/validate/__main__.py` — modified — Replaced single-target dispatch with a click group that registers both `locations` and `projection-check` subcommands. Direct module entry (`python -m sidequest.cli.validate.projection_check`) preserved.
- `tests/cli/test_validate_locations.py` — created by TEA, unchanged in semantics (ruff format only).
- `tests/fixtures/validate_locations/coherence_npc_resolved/worlds/sample/cartography.yaml` — prose tightened (see Dev deviation).

**Files Changed (orchestrator repo):** None. Empty branch — see Dev deviation about server-only scope.

**Tests:**
- `tests/cli/test_validate_locations.py` — 25/25 passing (TEA wrote 23; ruff formatting did not change test count; the runner-reported 25 vs my expected 23 reflects pytest's counting of two parametrize-free helpers that I'd undercounted — manual verification confirms 25 collected, 25 passed)
- `tests/integration/test_pf_validate_locations_on_materialized.py` — 1/1 passing — Story 55-1's `pytest.importorskip` now activates; the post-materialize cross-story producer/consumer loop is closed
- Full server suite — green, no regressions (reported by testing-runner: 6782 prior passes maintained; nothing regressed)
- `uv run ruff check` — clean on the three changed files
- `uv run ruff format` — applied

**Branch:** `feat/54-3-validate-locations-validator` (server) — pushed to `origin`. Orchestrator branch identical to main — empty.

### Implementation Decisions

1. **Both entry surfaces implemented.** `validate_locations_in_world(world_dir)` for the AC-5 / Story 55-1 consumer contract; `validate_packs(pack_roots)` for the multi-pack CLI helper. The latter routes through `_validate_one_world` so behavior is identical between the two surfaces.

2. **`pack.yaml` is the pack-discovery filename** per the loader convention at `sidequest/genre/loader.py:963` — matches TEA's deviation note.

3. **`FLAVOR_ONLY_FORBIDS_BINDING` is a dedicated issue code,** not piggybacked onto `MALFORMED_ENTITY`. Pydantic's model permits `binding: None | LocationEntityBinding` for any tier, so the constraint is the validator's responsibility. A dedicated code makes the diagnostic actionable for content authors.

4. **`item` bindings are a no-op** per ADR-109 implementation guidance — the canonical item corpus interface isn't stable. Flagged explicitly in source.

5. **Allowlist double-indexed** by full form (`"the day"`) and article-stripped form (`"day"`). Lets per-pack allowlists silence both phrase-grained and head-grained matches without authors having to enumerate every article variant.

6. **Sentence-initial proper-noun skip uses a six-element boundary set** (`. `, `? `, `! `, `.\n`, `?\n`, `!\n`) — captures newline-separated paragraphs as well as space-separated sentences, since `cartography.yaml` description fields use both styles in real content.

### Acceptance Criteria

| AC | Surface | Status |
|----|---------|--------|
| AC-1 | CLI scans every wired world; exit 1 on hard error, 0 otherwise | ✅ — three CLI subprocess tests cover clean/hard-error/warning-only exit codes |
| AC-2 | Well-formedness (duplicate id, blank label/id, extra fields, flavor_only+binding, real_object-no-binding) | ✅ — five fixture packs + five tests; `wf_malformed` proves all three malformed entries surface independently |
| AC-3 | Binding resolution (npc/clue/scenario_clue refs resolve; location_feature free-form) | ✅ — four tests across `binding_bad_npc`, `binding_bad_clue`, `binding_location_feature_ok`, and `wf_ok` negative |
| AC-4 | Prose-manifest coherence (warning never blocks; allowlist silences; NPCs don't warn) | ✅ — four tests including the explicit `test_prose_drift_never_promoted_to_error` guard |
| AC-5 | `validate_locations_in_world(world_dir) -> ValidationResult` with `.errors` / `.warnings` | ✅ — three tests plus the consumer-side `test_55_1_consumer_can_import_validate_locations_in_world` wiring test |
| AC-6 | Validator runs against every wired pack (multi-pack discovery) | ✅ at the validator surface — `test_multi_pack_root_walks_every_pack` proves aggregation across packs. **Partial at the `just check-all` CI gate** — that wiring lives in pennyfarthing-dist (TEA deviation) and is the follow-up branch's job. |
| AC-7 | Wiring — `python -m sidequest.cli.validate locations --help` registered + non-test caller via 55-1 | ✅ at the server-side surface (`test_cli_subcommand_help_runs` + the 55-1 importorskip lifting). **Partial at the `pf validate --help` listing** — pennyfarthing-dist follow-up. |

### Cross-Story Wiring Confirmation

Story 55-1's `tests/integration/test_pf_validate_locations_on_materialized.py` was waiting on `sidequest.cli.validate.locations.validate_locations_in_world`. The `pytest.importorskip` now activates and `test_validator_reports_no_hard_errors_on_cookbook_yamls` PASSES against a fresh materialization. The cookbook → manifest → validator loop is closed.

**Handoff:** To Reviewer (Colonel Potter) — server PR ready at `feat/54-3-validate-locations-validator`. Two follow-ups for SM:
1. Open follow-up branch in `pennyfarthing-dist` for the `pf validate locations` adapter, VALIDATORS dict registration, and orchestrator `just check-all` wiring (AC-6 / AC-7 second clauses).
2. Empty orchestrator branch can be deleted or left as a no-op — no commits land there for this story.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned within documented scope deferrals
**Mismatches Found:** 4 (all minor; all already logged as TEA/Dev deviations or explicit ADR-109 deferrals)

Gate `spec_check` passed structurally. The seven ACs from `context-story-54-3.md` are all covered at the validator surface; partial-coverage rows in Dev's AC table (AC-6, AC-7 second clauses) correspond to the pennyfarthing-dist follow-up branch that TEA explicitly scoped out — that's a known boundary, not drift.

### Substantive mismatches

- **AC-3 / AC-4: `Issue.line` field always `None`** (Missing in code — Behavioral, Minor)
  - Spec: AC-3 — "Unresolved refs are hard errors with file:line refs." AC-4 — "Warnings carry file:line context."
  - Code: `Issue` carries `file` (absolute path) + `region_id`. `line` field is declared (`int | None = None`) but never populated — PyYAML's `safe_load` discards source locations.
  - Recommendation: **D (Defer)** — line tracking requires a custom YAML loader (`yaml.compose` + walking the parse tree, or `ruamel.yaml`). Non-trivial scope expansion for a diagnostic-only refinement. `file` + `region_id` are sufficient for grep + IDE navigation; content authors get actionable signal today. Issue shape already accommodates `line`, so populating it later is purely additive.
  - Forward impact: None for current ACs; future polish.

- **AC-3: `item` binding kind is a no-op** (Missing in code — Behavioral, Minor)
  - Spec: AC-3 — "resolves `binding.kind in {npc, item, clue, scenario_clue}`"
  - Code: `_check_binding` early-returns on `kind == "item"` with an explicit comment citing ADR-109's deferral guidance ("canonical item corpus interface hasn't stabilised").
  - Recommendation: **D (Defer)** — ADR-109 author-time-only scope; the validator is correctly permissive until the item subsystem firms up. Flagged in source, surfaces in Dev assessment.
  - Forward impact: When the item corpus interface lands, a follow-up story extends `_check_binding` to load item ids and resolve.

- **AC-1: CLI shape `pf validate locations <pack>` vs `--genre-packs-root PATH`** (Different behavior — Cosmetic/Architectural, Minor)
  - Spec: AC-1 — "`pf validate locations <pack>` runs every wired world in the pack."
  - Code: server CLI exposes `--genre-packs-root PATH` (option). The `pf` adapter (pennyfarthing-dist follow-up) is the layer that will own the user-facing positional-arg shape.
  - Recommendation: **D (Defer)** — this is the correct seam. The server CLI is the implementation tier; the `pf validate` adapter is the user-facing tier. The adapter can translate `pf validate locations <pack>` into `--genre-packs-root <pack>` at the boundary. TEA + Dev already deferred the adapter to a separate branch.
  - Forward impact: The pennyfarthing-dist adapter must honour the AC-1 invocation shape when it lands.

- **AC-6 + AC-7 (second clauses): adapter + CI wiring missing** (Missing in code — Architectural, Minor)
  - Spec: AC-6 — "CI runs `pf validate locations` … as part of `just check-all`." AC-7 — "listed in `pf validate --help`."
  - Code: Server CLI is callable but unrouted via `pf`; `just check-all` not updated.
  - Recommendation: **D (Defer)** — already triple-logged (TEA Delivery Finding, TEA Design Deviation, Dev Implementation Decision). SM tracks as a pennyfarthing-dist follow-up branch.
  - Forward impact: Open follow-up branch in `pennyfarthing-dist` against `develop`: add `src/pf/validate/adapters/locations.py`, register `"locations"` in the `VALIDATORS` dict, then add `pf validate locations` to `just check-all` in the orchestrator repo (single line).

### Reuse-first audit

- **`Issue` / `ValidationResult` dataclasses** — no existing pattern. `projection_check.py` (the only sibling validator) uses argparse + raises `ValidationError` on first failure; that's a fail-fast shape unsuitable for a multi-issue collector. New dataclasses are appropriate.
- **Pack discovery (`_packs_in`)** — `sidequest/genre/loader.py` has its own pack iteration but loads every pack file through pydantic models on every call (heavy + coupling-prone). Lightweight validator-side discovery against just `pack.yaml` is the right scope.
- **YAML loading** — Dev uses `yaml.safe_load` directly. Loader's private `_load_yaml_raw` could be reused but the validator's needs (raw dicts, no model coercion) are simple enough that direct use is cleaner than reaching into a private helper.
- **CLI dispatch** — Dev migrated `__main__.py` to a click group + preserved direct-module entry to projection_check. Idiomatic click pattern; no over-engineering.

No reuse violations. No new patterns introduced where existing ones would have worked.

**Decision:** Proceed to TEA verify. All mismatches are explicit deferrals already in writing; no rework required from Dev.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (26 passing, lint clean, no regressions vs green-phase baseline)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`sidequest/cli/validate/__main__.py`, `sidequest/cli/validate/locations.py`, `tests/cli/test_validate_locations.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | 1 high (`yaml.safe_load` → loader's `_load_yaml_raw_optional`), 1 medium (`_load_npc_tokens` → shared util), 1 low (`_load_clue_ids` → shared util) |
| simplify-quality | 1 finding | 1 medium (`except Exception` comment "pydantic ValidationError or similar" — clarity nit) |
| simplify-efficiency | clean | No over-engineering, regex pre-compiled, dedup `seen` set in place |

**Applied:** 0 high-confidence fixes (the single high-confidence finding fails its dismissal criterion — see below)
**Flagged for Review:** 1 medium-confidence quality finding (`except Exception` comment)
**Noted:** 3 dismissed findings (rationale below)
**Reverted:** 0

**Overall:** simplify: clean

### Findings dismissed with rationale

- **REUSE-1 (high, dismissed): use `_load_yaml_raw_optional` from genre loader.**
  Architect's reuse-first audit in `## Architect Assessment (spec-check)` already considered and rejected this same reuse opportunity, citing: *"Loader's private `_load_yaml_raw` could be reused but the validator's needs (raw dicts, no model coercion) are simple enough that direct use is cleaner than reaching into a private helper."* The genre loader's `_load_yaml_raw_optional` is explicitly underscore-prefixed (module-private). Reaching into another module's private API to save five lines of `yaml.safe_load(path.read_text()) or {}` would create a coupling debt larger than the duplication it prevents. Dismissed.

- **REUSE-2 (medium, dismissed): extract `_load_npc_tokens` for sharing.**
  Subagent's own rationale: *"if other validators need NPC token extraction."* No other validator needs it today — `projection_check.py` doesn't load NPCs. YAGNI; extract when a second consumer appears.

- **REUSE-3 (low, dismissed): extract `_load_clue_ids` for sharing.**
  Same disposition as REUSE-2 — single consumer, no proven need. Subagent acknowledged "single consumer (locations validator) justifies inline implementation."

### Findings flagged (medium — no auto-apply)

- **QUALITY-1 (medium, flagged): `except Exception` at `locations.py:193` with comment "pydantic ValidationError or similar".**
  Sibling validator `projection_check.py:56` uses the same broad-catch pattern. The intent here is genuinely to catch *any* model-coercion failure (pydantic `ValidationError`, but also `TypeError` from non-dict input, `AttributeError` from misshapen YAML), funnel them into a single `MALFORMED_ENTITY` diagnostic with the original exception message, and continue scanning. A narrower catch (`pydantic.ValidationError` only) would let other failure modes crash the whole validator on the first bad authored row — exactly the opposite of what AC-2's "report each malformed entry independently" requires (verified by `test_malformed_entities_report_each_independently`, which depends on the broad catch). The comment is honest but understated; tightening it is a documentation refinement, not a defect. Reviewer can decide whether to add a single-line comment expansion ("catches all entity-construction failures so one bad row does not halt the scan") or leave as-is.

### Rule Coverage (verify pass)

| Rule | Verification |
|------|--------------|
| No Silent Fallbacks | Validator surfaces every malformed entry via `MALFORMED_ENTITY`; per-world entry returns empty `ValidationResult` only when neither cartography nor rooms exist (clean empty signal, not silent error swallow). Confirmed by `test_per_world_entry_accepts_world_with_no_cartography` and `test_malformed_entries_report_each_independently`. |
| No Stubbing | `item` binding kind is no-op but documented with ADR-109 citation, not a placeholder TODO. |
| Every Test Suite Needs a Wiring Test | `test_cli_subcommand_help_runs` (subprocess) + `test_55_1_consumer_can_import_validate_locations_in_world` (cross-story consumer) both still green. |
| Verify Wiring, Not Just Existence | 55-1's `test_validator_reports_no_hard_errors_on_cookbook_yamls` activates and passes — the producer/consumer loop closed end-to-end. |

**Quality Checks:** All passing — 26/26 tests green, ruff clean on changed files.

### Delivery Findings Capture

(No new upstream findings during verify — simplify pass is clean enough to ship.)

**Handoff:** To Reviewer (Colonel Potter) for code review and merge of `feat/54-3-validate-locations-validator` on `sidequest-server`.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — tests 26/26 green, lint clean, format clean, CLI smoke works, 3 well-ordered commits |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter=false`; covered manually in Devil's Advocate |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings; covered manually in `[SILENT]` finding below |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings; covered manually under `[TEST]` VERIFIEDs |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings; covered manually under `[DOC]` VERIFIEDs |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings; covered manually under `[TYPE]` VERIFIEDs |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings; covered manually under `[SEC]` VERIFIEDs |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings; TEA's verify-phase simplify trio already covered this — see `## TEA Assessment (verify)` Simplify Report |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings; rule-by-rule enumeration done manually below against `gates/lang-review/python.md` (14 rules) |

**All received:** Yes (1 returned, 8 disabled via settings — manual coverage substituted as noted)
**Total findings:** 4 confirmed (all LOW), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Findings

| Severity | Tag | Issue | Location | Disposition |
|----------|-----|-------|----------|-------------|
| [LOW] | [RULE] | `path.read_text()` called without `encoding="utf-8"` — Python's default is UTF-8 on macOS/Linux but locale-dependent on Windows (CWE-838 / lang-review rule #5) | `locations.py:129, 148, 162, 449, 465` | Non-blocking. SideQuest runs on macOS exclusively in practice. Future polish — add `encoding="utf-8"` for parity with CWE-838. |
| [LOW] | [SILENT] | YAML parse errors uncaught — a malformed `cartography.yaml`, `npcs.yaml`, `pack.yaml`, or `scenarios/*.yaml` raises `yaml.YAMLError` and crashes the whole multi-pack scan with a stack trace instead of recording a `MALFORMED_YAML` issue. Defeats the "report every error, don't stop at the first" property `test_malformed_entities_report_each_independently` proves at the entity level. | `locations.py:129, 148, 162, 449, 465` | Non-blocking — real content currently parses cleanly. A `MALFORMED_YAML` issue code + `try/except YAMLError` around each `yaml.safe_load` would be a one-screen follow-up; not gating 54-3. |
| [LOW] | [SIMPLE] | `validate_locations_in_world(world_dir)` infers `pack_slug = world_dir.parent.parent.name` — fragile for callers that pass a path not shaped `<pack>/worlds/<world>`. Issues will be tagged with a misleading `pack` string but won't crash. | `locations.py:441-443` | Non-blocking. 55-1's caller, the CLI's `validate_packs` helper, and the test suite all use canonically-shaped paths. Tighter contract (e.g., explicit `pack_dir` parameter) is a future ergonomics call. |
| [LOW] | [RULE] | `Issue.line` field declared but never populated (PyYAML's `safe_load` discards source positions) | `locations.py:51, throughout` | Confirmed but already flagged by Architect in spec-check as Deferral D. Line tracking requires a custom YAML loader (`yaml.compose` walking the parse tree) — non-trivial scope expansion. `file` + `region_id` give actionable signal for grep + IDE jumps today. |

### VERIFIEDs (rule-by-rule against `gates/lang-review/python.md`)

- [VERIFIED] **Rule #1 (silent exceptions)** — broad `except Exception` at `locations.py:193` is intentional and required by AC-2 (report every malformed entry independently). Verified by `test_malformed_entities_report_each_independently` which puts three independently-malformed entities in one region and asserts all three surface. Narrowing to `pydantic.ValidationError` would let a `TypeError` from non-dict YAML rows crash the scan. Comment "pydantic ValidationError or similar" honestly describes the intent. Compliant with rule #1's "if so, it MUST be handled explicitly" — every catch records an Issue, not a silent pass.
- [VERIFIED] **Rule #2 (mutable defaults)** — none. `ValidationResult.errors`/`.warnings` use `field(default_factory=list)`. No function uses `[]`/`{}`/`set()` as default arg.
- [VERIFIED] **Rule #3 (type annotations)** — every public function (`validate_locations_in_world`, `validate_packs`, `main`) and every private helper (`_packs_in`, `_worlds_in`, `_load_*`, `_check_*`) carries parameter and return annotations. Dataclass fields all typed. `Issue.region_id: str | None`, `Issue.line: int | None` use Python 3.10+ union syntax consistent with the rest of the codebase.
- [VERIFIED] **Rule #4 (logging)** — module does not import `logging`. CLI uses `click.echo(..., err=True)` for human output and `json.dumps` for `--json`. No log-level mismatches.
- [VERIFIED] **Rule #5 (path handling)** — uses `pathlib.Path` throughout; no string concatenation for paths; no hardcoded `/`. *Exception:* `read_text()` without `encoding=` (see LOW finding above).
- [VERIFIED] **Rule #6 (test quality)** — every test in `test_validate_locations.py` asserts a specific issue code, count, message substring, or structural property. No `assert True`, no `assert result`-only truthy checks, no `mock.patch` (no mocking at all — real fixtures + real subprocess). No `pytest.mark.skip` without reason — none used.
- [VERIFIED] **Rule #7 (resource leaks)** — `Path.read_text()` opens and closes the file in one call. No bare `open()`, no `requests`, no `sqlite3`, no threading.
- [VERIFIED] **Rule #8 (unsafe deserialization)** — `yaml.safe_load` everywhere (5 sites). No `pickle`, no `eval`, no `exec`, no `subprocess(..., shell=True)`. CLI subcommand `projection-check` in `__main__.py:35` calls `projection_check_main([genre_dir])` as Python args, not shell. Safe.
- [VERIFIED] **Rule #9 (async)** — module is sync; no `asyncio`, no `await`. N/A.
- [VERIFIED] **Rule #10 (import hygiene)** — no `from x import *`; no circular imports (only inbound import is `sidequest.protocol.models.LocationEntity`); `from sidequest.genre.loader import DEFAULT_GENRE_PACK_SEARCH_PATHS` is lazy inside `main()` body — appropriate.
- [VERIFIED] **Rule #11 (input validation)** — CLI input is validated by click decorators: `--genre-packs-root` is `click.Path(exists=True, file_okay=False, path_type=Path)` (rejects nonexistent paths and files). `--json` is a flag. No SQL, no HTML, no `re.compile` on user input (the two regexes are module-level constants).
- [VERIFIED] **Rule #12 (dependency hygiene)** — no new dependencies added; `pyyaml` + `click` already in `pyproject.toml`. `uv run` resolves from the lockfile.
- [VERIFIED] **Rule #13 (fix regressions)** — three commits: tests-first → impl + regex bug fix → ruff cleanup. The regex fix re-narrowed `[a-z\-' ]{2,40}` to `[a-z\-']{0,40}`. Re-scan vs rules #1–#12: no broadened catch, no new mutable defaults, no new untyped boundary, no new pickle/eval, no new `open()` without context. Clean.
- [VERIFIED] **Rule #14 (state cleanup ordering)** — N/A (no register/commit/send/publish patterns; validator is pure-functional read-only).
- [VERIFIED] **Wiring** — `__main__.py:28` calls `cli.add_command(locations_main, name="locations")`. Subprocess test `test_cli_subcommand_help_runs` confirms `python -m sidequest.cli.validate locations --help` returns 0. Cross-story consumer test `test_55_1_consumer_can_import_validate_locations_in_world` proves the importorskip in `tests/integration/test_pf_validate_locations_on_materialized.py` lifts and the function is callable. End-to-end producer/consumer loop closed.
- [VERIFIED] **Tenant isolation** — N/A. SideQuest is single-tenant by design (`/Users/slabgorb/Projects/oq-2/CLAUDE.md` "personal project under the `slabgorb` GitHub account"). No multi-tenant concerns apply.
- [VERIFIED] **Comment accuracy** — class docstrings honest (`Issue.line` is documented as optional with `None` default). Module docstring accurately describes the three checks. The `except Exception` comment "pydantic ValidationError or similar" is understated but not misleading — see VERIFIED rule #1 above.

### Devil's Advocate

If I wanted to break this code, where would I attack?

**Attack 1 — malformed real-world YAML.** An author edits `tea_and_murder/genre_packs/.../cartography.yaml` and accidentally leaves a tab character or an unclosed quote. `yaml.safe_load` raises `yaml.YAMLError`. The validator crashes mid-scan with a stack trace, no `MALFORMED_YAML` issue, no continuation to other packs. CI runs `pf validate locations` and the operator sees a Python traceback instead of "your cartography file at line 47 has a YAML syntax error." This contradicts the AC-2 design principle ("report each malformed entry independently"). The fix is one `try/except YAMLError` wrapper per `_load_*` helper that records a `MALFORMED_YAML` issue and skips that file. Captured as the LOW [SILENT] finding above — not a blocker for 54-3 (real packs all parse cleanly today) but a known fragility.

**Attack 2 — Unicode/orthography in real packs.** `tea_and_murder/glenross` is full of Scottish names: "St. Maelrubha", "Allt Ross", "MacGregor", "O'Brien". The proper-noun regex `[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*` would split "MacGregor" as "Mac" + "Gregor" (the capital G doesn't satisfy `[a-z]`). If `npcs.yaml` lists `name: MacGregor`, the normalized token is `macgregor`, but the regex emits `mac` and `gregor` as separate proper-noun matches that won't resolve to `macgregor`. Both fire as PROSE_DRIFT warnings. Real authors will see noise. Not a blocker — warnings are non-blocking by design — and the allowlist exists exactly for this kind of false-positive silencing. Future polish: expand the proper-noun regex to support CamelCase / O'Brien / hyphenated names. Worth noting but out of scope.

**Attack 3 — adversarial pack.yaml.** What if `generic_allowlist[]` contains 100,000 entries? The set comparison stays O(1) but memory grows. Acceptable for sane content. What if it contains `null` or `42` or a nested dict? The `isinstance(item, str)` guard at line 166 drops non-string entries silently. Could log a warning but the validator is content-time, not runtime — content authors will notice their allowlist entries aren't taking effect.

**Attack 4 — empty cartography or empty rooms.** Already handled: `data.get("regions") or {}` defaults to empty dict; `for region_id, region_data in regions.items()` over an empty dict is a no-op. Per-room glob `sorted(rooms.glob("*.yaml"))` over an empty dir is a no-op. Zero diagnostics, no crash.

**Attack 5 — symlink loop in pack discovery.** `_packs_in(root)` does single-level `iterdir()` + `is_dir()`. Symlinks to directories are followed but `iterdir()` does not recurse, so no loop. Safe.

**Attack 6 — race condition.** Pure-functional read-only validator. Not applicable.

**Attack 7 — wrong path layout.** `validate_locations_in_world(weird_path)` derives `pack_slug` from `weird_path.parent.parent.name`. If someone passes `tmp_path/single_dir/cartography.yaml`'s parent (i.e., `tmp_path/single_dir`), `pack_slug` becomes the name of `tmp_path`'s parent — some pytest tmp dir. Issues get tagged with a meaningless pack name but no crash, no security issue. Captured as the LOW [SIMPLE] finding above.

**Attack 8 — confused operator runs `pf validate locations` against `/etc`.** The walk finds no `pack.yaml`, returns empty, exits 0. No information leak (no diagnostics emitted). Issue file paths would only contain pack-internal paths, never `/etc/passwd` etc. Operator sees "0 errors, 0 warnings" and learns they pointed at the wrong root. Loud-enough failure.

None of these attacks justify rejection. Three are captured as LOW findings; the rest are non-issues or genuine future polish. The 26 tests + the cross-story 55-1 importorskip lift give high confidence in correctness.

### Data Flow Trace

User input: `pf validate locations` (or direct `python -m sidequest.cli.validate locations`) → click parses `--genre-packs-root` PATH arg (validates exists + is dir) → `validate_packs([roots])` → for each pack with `pack.yaml`: `_load_allowlist` reads `pack.yaml`, then for each world dir: `_load_npc_tokens` reads `npcs.yaml`, `_load_clue_ids` walks `scenarios/*.yaml`, then `_check_well_formed_region` parses each entity through `LocationEntity.model_validate` → records Issue on failure → `_check_binding` checks `binding.ref` against npc/clue sets → `_check_prose` regex-scans description → records PROSE_DRIFT warnings → final `ValidationResult.success` determines exit code.

Safe because: every user-facing path is `click.Path(exists=True)`-validated; every YAML load is `safe_load`; every diagnostic carries `file` for IDE navigation; warnings never escalate to errors (verified by `test_prose_drift_never_promoted_to_error` AND `test_cli_exits_zero_on_warning_only_pack`); errors are surface-and-continue, not abort.

### Pattern Observed

The validator follows the existing `sidequest/cli/validate/projection_check.py` pattern (sole sibling) at the file-organization level and adds a new collector pattern (`ValidationResult.record`) that fits cleanly. The `__main__.py` migration from single-target dispatch to click group is idiomatic and preserves the direct-module entry (`python -m sidequest.cli.validate.projection_check`) for backwards compat. Good neighbor to the existing CLI tree.

### Error Handling

`Exception` catch at `locations.py:193` is broad but intentional and AC-justified (see VERIFIED rule #1). `yaml.YAMLError` is NOT caught — that's the LOW [SILENT] finding above. CLI subprocess in `__main__.py:35` uses `sys.exit(projection_check_main([genre_dir]))` which surfaces the wrapped function's int return code through click; if the wrapped function raises, click's default handling kicks in (good).

### Handoff

PR for `feat/54-3-validate-locations-validator` on `sidequest-server` is ready to be opened and merged against `develop` by SM. No rework required.

**Two follow-ups for SM to track (not blocking THIS PR):**
1. Open follow-up branch in `pennyfarthing-dist` against `develop` for the `pf validate locations` adapter, VALIDATORS dict registration, and `just check-all` integration (AC-6 + AC-7 second clauses). TEA + Dev + Architect all flagged.
2. Empty orchestrator branch `feat/54-3-validate-locations-validator` can be deleted — no commits land there for this story.

**Optional follow-ups to file as new stories (out-of-scope for 54-3):**
- `MALFORMED_YAML` issue code for graceful handling of bad YAML files (one-screen fix).
- `Issue.line` population via custom YAML loader (`yaml.compose` parse-tree walk).
- Proper-noun regex extension for CamelCase / O'Brien / hyphenated names (real-content authoring noise).
- `validate_locations_in_world` tighter contract — explicit `pack_dir` parameter to avoid path-shape inference fragility.

---

## Links

- **Spec:** `docs/superpowers/specs/2026-05-19-persistent-location-descriptions-design.md` (full design + risks + doctrine quotes)
- **Plan:** `docs/superpowers/plans/2026-05-19-story-54-3-pf-validate-locations.md` (task-by-task implementation guide)
- **Epic context:** `sprint/context/context-epic-54.md` (upstream dependencies, story sequence)
- **Related test suite:** `sidequest-server/tests/protocol/test_location_entity_models.py` (54-2's model tests; understanding LocationEntity is prerequisite)
- **Related integration fixture:** `sidequest-server/tests/integration/test_pf_validate_locations_on_materialized.py` (54-2's post-materialize validator fixture)
- **CLAUDE.md:** Project principles ("No Silent Fallbacks", "No Stubbing", "Every Test Suite Needs a Wiring Test")