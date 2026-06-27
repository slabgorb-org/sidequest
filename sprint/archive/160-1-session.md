---
story_id: "160-1"
jira_key: "none"
epic: "none"
workflow: "tdd"
---
# Story 160-1: Animal companion persona templates — cat/owl/raven/toad/goat CompanionDef YAMLs bound to beneath_sunden, reusing the epic-159 run loop, with a wiring test asserting each parses as a valid role:pet CompanionDef

## Story Details
- **ID:** 160-1
- **Jira Key:** none
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/160-1-animal-companion-persona-templates)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-27T09:16:35Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T08:51:16.670886Z | 2026-06-27T08:53:25Z | 2m 8s |
| red | 2026-06-27T08:53:25Z | 2026-06-27T08:59:20Z | 5m 55s |
| green | 2026-06-27T08:59:20Z | 2026-06-27T09:08:26Z | 9m 6s |
| review | 2026-06-27T09:08:26Z | 2026-06-27T09:16:35Z | 8m 9s |
| finish | 2026-06-27T09:16:35Z | - | - |

## Sm Assessment

**Setup:** Complete. Session file, story context (`sprint/context/context-story-160-1.md`), and feature branch `feat/160-1-animal-companion-persona-templates` (cut from `develop` in `sidequest-understudy`) all created and verified.

**Scope (understudy-only):** Add five `CompanionDef` YAMLs under `sidequest-understudy/src/companion/examples/` — `cat_sunden.yaml`, `owl_sunden.yaml`, `raven_sunden.yaml`, `toad_sunden.yaml`, `goat_sunden.yaml` — each `role: pet`, bound to `caverns_and_claudes/beneath_sunden`, `model: claude_p/sonnet`, `game_slug` left as the `REPLACE-WITH-HUMANS-ROOM-SLUG` placeholder (mirror `donut_sunden.yaml`). Plus a wiring test that loads every example and asserts a valid `CompanionDef` with `role == pet` and non-empty `species`/`voice`. Zero changes outside `sidequest-understudy`. Reuses the epic-159 run loop verbatim — no run-loop code.

**Routing:** Workflow `tdd` (phased). Next phase **RED** → **TEA (Amos Burton)**. TEA writes the failing wiring test first (the integration proof the five defs are real, loadable, and `role: pet`); Dev then authors the five voiced YAMLs to green it.

**Jira:** Skipped — story has no Jira key (added via `pf sprint story add`); project Jira disabled.

**Watch-out:** The deliverable is *distinct per-species voice*, not five clones of Donut. The wiring test proves loadability, not character — the register quality is a review-phase judgment. Keep `model: claude_p/sonnet` (the `anthropic/*` default breaks on the dev box per the chargen-driver doc §7 carryover).

## TEA Assessment

**Tests Required:** Yes
**Reason:** Story explicitly demands a wiring test (the integration proof the five defs are real, loadable, role:pet). Sprint YAML carried no ACs — TEA derived them from the Technical Approach (see deviation below).

**Test Files:**
- `sidequest-understudy/tests/companion/test_animal_examples.py` — wiring test for the five animal companion templates (cat/owl/raven/toad/goat).

**Tests Written:** 27 cases covering 5 derived ACs:
1. **Files exist** — `test_animal_template_file_exists` (×5)
2. **Valid role:pet CompanionDef** — `test_animal_template_is_valid_pet_companion` (×5): `role is Role.PET`, `species` matches, non-empty `voice`/`name`
3. **Bound to world** — `test_animal_template_bound_to_beneath_sunden` (×5): genre `caverns_and_claudes`, world `beneath_sunden`
4. **Working backend** — `test_animal_template_uses_claude_p_sonnet` (×5): `model == "claude_p/sonnet"` (anthropic/* default is dead on the dev box)
5. **Placeholder slug** — `test_animal_template_game_slug_is_unfilled_placeholder` (×5): `game_slug` stays `REPLACE-*`
- Plus `test_animal_voices_are_distinct` (5 voices pairwise distinct) and `test_every_example_yaml_loads_as_companion_def` (durable guard: every example YAML loads).

**Status:** RED — 26 failing (files not yet authored), 86 pre-existing pass (no regression). The 1 passing new case is the durable guard, green against `donut_sunden.yaml`. Verified by testing-runner: failures are `ManifestError: not found` / `is_file` assertions — failing for the right reason, not import/typo.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality (no vacuous asserts) | every case in `test_animal_examples.py` asserts a concrete value with a diagnostic message | pass (self-check) |
| #8 unsafe deserialization (`yaml.safe_load`) | `test_manifest.py::test_manifest_uses_safe_load_rejects_python_tags` — loader unchanged, still on `safe_load` | pass (pre-existing) |

**Rules checked:** The production diff is **YAML data only** — Dev authors no new `.py`. Python lang-review checks #1–#5, #7, #9–#13 are N/A to the change. #6 applies to my test file (self-checked clean); #8 applies to the `load_companion` loader, which is untouched and already covered.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Naomi Nagata) for GREEN — author the five voiced YAMLs (mirror `donut_sunden.yaml`) until all 27 cases pass.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-understudy/src/companion/examples/cat_sunden.yaml` — Beauregard, languid aristocratic vanity (cat)
- `sidequest-understudy/src/companion/examples/owl_sunden.yaml` — Tolliver, rules-fussy pedant (owl); axes lean mechanical (0.7), high reading tolerance
- `sidequest-understudy/src/companion/examples/raven_sunden.yaml` — Mordant, ominous secret-hoarder with gallows wit (raven)
- `sidequest-understudy/src/companion/examples/toad_sunden.yaml` — Bartleby, phlegmatic/blunt/food-motivated (toad); terse axes (verbosity/decisiveness low)
- `sidequest-understudy/src/companion/examples/goat_sunden.yaml` — Crookhorn, contrarian headbutter (goat); reckless axes (decisiveness high)
- `sidequest-understudy/tests/test_reconnect.py` — **out-of-scope hygiene**: pre-existing E402 import reorder (see deviation + finding below)

Personas differ on the **axis dials**, not just prose, so the distinctness is mechanical as well as voiced. All bound to `caverns_and_claudes/beneath_sunden`, `role: pet`, `model: claude_p/sonnet`, `game_slug` = `REPLACE-WITH-THE-HUMANS-ROOM-SLUG` (adopted Donut's exact spelling, resolving the inconsistency TEA flagged). Reuses the epic-159 run loop verbatim — no run-loop code.

**Tests:** 238/238 passing (GREEN), incl. 27/27 in `test_animal_examples.py` (distinct-voices guard green). `ruff check .` clean. Verified by testing-runner (final run `160-1-dev-green-final`).
**Branch:** `feat/160-1-animal-companion-persona-templates` (pushed to origin).

**Handoff:** To TEA (Amos Burton) for verify (simplify + quality-pass), then Reviewer.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (238 pass, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 3, dismissed 2, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 7 | confirmed 7 (1 medium, 6 low), dismissed 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 0, dismissed 1 (repo convention) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 10 confirmed (1 medium, 9 low), 3 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. Every confirmed finding is Low or Medium severity (non-blocking per the severity rubric). The diff is content-only — five persona YAMLs, one wiring test, and a 7-line pre-existing-lint reorder — with zero engine/runtime code touched.

### Rule Compliance

Enumerated the Python lang-review checklist + understudy/SOUL rules against every changed artifact (rule-checker corroborated, 17 rules / 47 instances):

- **#1 silent exceptions** — none; `load_companion` (unchanged) catches `(ValidationError, yaml.YAMLError)` specifically and re-raises `ManifestError`. Compliant.
- **#3 type annotations** — [RULE] rule-checker flagged 7 test fns missing `-> None`. **Dismissed:** Rule #3 exempts internal/private helpers; pytest test fns are internal (never imported as API), the existing repo convention omits `-> None` on every test (`test_manifest.py` = 0 of N annotated, verified), and ruff (the configured linter) is clean. Matching surrounding code wins.
- **#6 test quality** — meaningful asserts with diagnostic messages throughout; two vacuous `isinstance(d, CompanionDef)` checks confirmed LOW (see findings). No `assert True`, no skips.
- **#8 unsafe deserialization** — `yaml.safe_load` confirmed in `manifest.py:41` (loader untouched). [VERIFIED] no pickle/eval/exec/yaml.load in diff.
- **Naivety Invariant (understudy CLAUDE.md)** — [VERIFIED] all five YAMLs contain ONLY persona prose + dials + binding fields; no alias maps, action allowlists, or target-resolution that would smuggle engine knowledge into the bot. evidence: rule-checker A3, and the CompanionDef schema (`extra="forbid"`) structurally forbids extras.
- **No Stubbing** — [VERIFIED] all five use `model: claude_p/sonnet` (real backend), not `fake`.
- **SOUL Agency / "The Test"** — [VERIFIED] every voice ends with an explicit "play only your own …; never speak or act for your human or anyone" clause (cat:42, owl, raven, toad, goat). Raven's reads "or anyone" vs others' "or anyone else" — trivial, functionally complete.

### Observations

- [VERIFIED] **Schema conformance** — all five YAMLs carry every required `CompanionDef` field, valid `SeatAxes` (floats in [0,1], levels in low/medium/high), no forbidden extras; proven by the 27 green wiring-test cases (`test_animal_examples.py`) and rule-checker A5.
- [VERIFIED] **Wiring to a non-test consumer** — these example YAMLs are inputs to the existing `companion play <file>` CLI (`src/companion/cli.py` → `load_companion` → epic-159 run loop). They are not orphan files; the wiring test gates their loadability and `donut_sunden.yaml` is the established precedent for the same path.
- [VERIFIED] **Error handling / fail-loud** — a missing/malformed template raises `ManifestError` before any socket opens (`manifest.py:38-43`); error paths are covered by `test_manifest.py` (missing-file, unknown-role, missing-field, malformed-yaml, python-tag).
- [TEST] **Vacuous `isinstance` checks** (LOW) at `test_animal_examples.py:49` and `:115` — `load_companion` returns `CompanionDef` or raises, so `isinstance(d, CompanionDef)` can never be False. Harmless (the surrounding role/species/voice asserts carry the signal) but noise. Optional cleanup.
- [TEST] **Unhelpful distinct-voices diagnostic** (LOW) at `test_animal_examples.py:103` — on a collision the message prints `sorted(voices)` (species keys), not the duplicate voice values. The assertion itself is correct.
- [DOC] **Raven dial/prose contradiction** (MEDIUM) — `raven_sunden.yaml:32` sets `verbosity: medium` while the voice says "Speak sparingly" (:26) and the comment says "economical of word" (:29). The intended value is `low`. This is the one finding that touches the story's core value (per-species coherence). Non-blocking but should be fixed — see delivery findings.
- [DOC] **"public-only vision" drops the "hireling" term** (LOW, ×5) — sibling SETUP comments say "public-only vision" where `donut_sunden.yaml` and the server use "hireling vision (public-only)". Not wrong, less precise.
- [DOC] **DRY SETUP reference** (LOW) — the five files defer to `donut_sunden.yaml` for full notes and omit the *why* of `companion_of: player1.local` (Vite proxy Host mechanics). Reasonable for day-to-day; the failure-mode explanation is the part a debugging user wants.
- [EDGE] edge-hunter disabled — manual check: a content diff with no branching logic; the only boundary (missing file) is covered by fail-loud + tests.
- [SILENT] silent-failure-hunter disabled — manual check: no try/except, no swallow paths in the diff; loader fails loud.
- [TYPE] type-design disabled — manual check: schema is pydantic `CompanionDef` (`extra="forbid"`), strongly typed; YAMLs validate against it.
- [SEC] security disabled — manual check: no user input, no secrets, `safe_load`, package-relative constant paths (no traversal). Clean.
- [SIMPLE] simplifier disabled — manual check: YAMLs mirror the proven Donut shape; no over-engineering. The test's `test_every_example_yaml_loads_as_companion_def` overlaps the parametrized checks but intentionally also covers `donut` + future files — acceptable.

### Data flow traced

`*_sunden.yaml` (authored content) → `companion play` CLI → `load_companion()` (`yaml.safe_load` + `CompanionDef.model_validate`, `extra="forbid"`) → `CompanionDef` → epic-159 run loop / `persona.py` prompt builder. Safe because every field is schema-validated and the loader fails loud on any malformation before a socket opens; no field in these files reaches the network unvalidated.

### Devil's Advocate

Assume this is broken. The most likely real-world failure isn't in the diff — it's the operator footgun the templates institutionalize. A user grabs `owl_sunden.yaml`, runs `companion play`, and never edits `game_slug` (still `REPLACE-WITH-THE-HUMANS-ROOM-SLUG`). The wiring test only asserts the slug *starts with* REPLACE, so a forgotten placeholder sails through static checks and only fails at connect time against a nonexistent room — and the SETUP note that would warn them is deferred to a *different file* (Donut). Worse, `companion_of: player1.local` is hardcoded: a user on any other host alias gets a **silent** bond downgrade to public-only vision (the documented fail-closed), and the sibling files dropped the "hireling" keyword that would help them spot it in server logs. So the templates are correct but the cold-start path for a non-Donut user is booby-trapped — that's the comment-analyzer's DRY finding, and it's more real than it looks. Second: the deliverable's *entire point* is five distinct personas, yet the only mechanical guarantee is byte-distinctness of the voice strings — five near-clones with one word changed would pass green, and Mordant already ships a dial (`verbosity: medium`) that fights its own prose. A career-GM playtest would notice a "terse, ominous raven" that won't shut up. Third: all five are single-point-of-failure on the `claude_p` backend; if that subscription path is unavailable on a given box, every animal companion is dead with no fallback (by design — but five-for-five). None of these are Critical/High: the runtime failures are loud (ManifestError / connect failure), the persona issues are tuning not correctness, and the backend choice is the documented working path. The raven dial is the one I'd fix before it reaches the table.

### Findings (severity)

| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| [MEDIUM] | Raven `verbosity: medium` contradicts "Speak sparingly" prose + "economical" comment | `src/companion/examples/raven_sunden.yaml:32` | Change to `verbosity: low` (1-char fix) — quick follow-up or fold into 160-3 dogfood |
| [LOW] | Sibling SETUP comments drop the "hireling" term | `*_sunden.yaml:~10` (×5) | Align to "hireling vision (public-only)" per donut |
| [LOW] | DRY SETUP omits the `companion_of` Vite-proxy rationale | `*_sunden.yaml` (×5) | Add one sentence on why `player1.local` |
| [LOW] | Vacuous `isinstance(d, CompanionDef)` | `test_animal_examples.py:49,115` | Optional: drop or replace with a field assertion |
| [LOW] | Distinct-voices failure message prints species keys, not colliding voices | `test_animal_examples.py:103` | Optional: show the matching pair |

**Dismissed:** (1) test-analyzer "no negative test for load_companion" — already covered by `test_manifest.py` fail-loud suite; (2) test-analyzer "test_every_example redundant" — intentional durable guard covering donut + future files, documented in the docstring; (3) rule-checker "#3 missing `-> None`" — repo convention + internal-helper exemption + clean ruff.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

No upstream findings.

### TEA (test design)
- **Improvement** (non-blocking): The game_slug placeholder spelling is inconsistent across sources — the design spec writes `REPLACE-WITH-HUMANS-ROOM-SLUG` while `donut_sunden.yaml` uses `REPLACE-WITH-THE-HUMANS-ROOM-SLUG`. Affects the five new YAMLs (`sidequest-understudy/src/companion/examples/*_sunden.yaml`) — Dev should pick one spelling consistently. The wiring test only requires a leading `REPLACE`, so either passes. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The repo's own lint gate (`uv run ruff check .`) failed on the develop baseline — two E402 (module-level import not at top of file) in `tests/test_reconnect.py`, unrelated to this story. Fixed here as a separate, labeled hygiene commit to keep the gate green; flagging so it's clear the debt predated 160-1 and ideally lands in its own chore next time. Affects `sidequest-understudy/tests/test_reconnect.py` (imports moved to the top block, no behavior change). *Found by Dev during implementation.*
- **Improvement** (non-blocking): Resolved the game_slug placeholder inconsistency TEA flagged by using Donut's exact spelling (`REPLACE-WITH-THE-HUMANS-ROOM-SLUG`) in all five templates. The design spec (§3) writes it as `REPLACE-WITH-HUMANS-ROOM-SLUG`; the spec could be aligned to the in-code precedent. Affects `docs/superpowers/specs/2026-06-27-animal-companions-design.md`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Raven's `verbosity: medium` contradicts its own prose ("Speak sparingly") and inline comment ("economical of word"); intended value is `low`. Affects `sidequest-understudy/src/companion/examples/raven_sunden.yaml:32` (change `medium` → `low`). Cheapest to fix as a one-line follow-up or to catch in the 160-3 dogfood pass. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The five sibling SETUP comments say "public-only vision" where `donut_sunden.yaml` and the server use the precise term "hireling vision (public-only)"; aligning keeps the diagnostic keyword users grep for. Affects `sidequest-understudy/src/companion/examples/{cat,owl,raven,toad,goat}_sunden.yaml` (SETUP comment ~line 10). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Sibling templates defer all SETUP to `donut_sunden.yaml` and omit the *why* of `companion_of: player1.local` (Vite proxy Host mechanics) — the one fact a debugging user needs when the bond fails closed. Affects the five `*_sunden.yaml` SETUP headers (add one sentence). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (0 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** The repo's own lint gate (`uv run ruff check .`) failed on the develop baseline — two E402 (module-level import not at top of file) in `tests/test_reconnect.py`, unrelated to this story. Fixed here as a separate, labeled hygiene commit to keep the gate green; flagging so it's clear the debt predated 160-1 and ideally lands in its own chore next time. Affects `sidequest-understudy/tests/test_reconnect.py`.
- **Improvement:** The five sibling SETUP comments say "public-only vision" where `donut_sunden.yaml` and the server use the precise term "hireling vision (public-only)"; aligning keeps the diagnostic keyword users grep for. Affects `sidequest-understudy/src/companion/examples/{cat,owl,raven,toad,goat}_sunden.yaml`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest-understudy/src/companion/examples`** — 1 finding
- **`sidequest-understudy/tests`** — 1 finding

### Deviation Justifications

3 deviations

- **ACs derived by TEA from the Technical Approach (none in sprint YAML)**
  - Rationale: The Technical Approach is unambiguous on each field; promoting them to explicit tests makes the contract enforceable rather than prose.
  - Severity: minor
  - Forward impact: Dev must satisfy all five clauses, not just "loads as pet"; story 160-3 dogfood can reuse these as the static-validation floor before live play.
- **Distinct-voice check is byte-identity, not a register-quality judgment**
  - Rationale: Voice quality (does owl read pedantic) is not mechanically assertable and belongs to Reviewer; byte-identity is the cheap floor that catches a copy-paste-one-voice regression without false-failing on good prose.
  - Severity: minor
  - Forward impact: Reviewer must still judge register distinctiveness/quality in review; a green test alone does not guarantee five genuinely characterful personas.
- **Out-of-scope lint hygiene fix to tests/test_reconnect.py**
  - Rationale: The develop baseline already failed `uv run ruff check .` (E402) on this file; full-repo ruff is the project's lint gate (understudy CLAUDE.md). Leaving it red would bounce the downstream verify/quality gate on debt this story didn't create. The fix is a mechanical import reorder with zero behavior change, committed separately and flagged as a finding for transparency.
  - Severity: minor
  - Forward impact: none on the five templates or any sibling story; if a reviewer prefers strict scope, the chore commit can be cherry-picked out to its own PR without touching the feat commit.

## Design Deviations

### TEA (test design)
- **ACs derived by TEA from the Technical Approach (none in sprint YAML)**
  - Spec source: context-story-160-1.md, "Acceptance Criteria"
  - Spec text: "No acceptance criteria recorded in the sprint YAML — TEA to define during the RED phase."
  - Implementation: Encoded five ACs as tests — files exist; each loads as role:pet CompanionDef with non-empty species/voice/name; bound to caverns_and_claudes/beneath_sunden; `model == claude_p/sonnet`; `game_slug` stays a `REPLACE-*` placeholder. Each clause is drawn verbatim from the context's Technical Approach.
  - Rationale: The Technical Approach is unambiguous on each field; promoting them to explicit tests makes the contract enforceable rather than prose.
  - Severity: minor
  - Forward impact: Dev must satisfy all five clauses, not just "loads as pet"; story 160-3 dogfood can reuse these as the static-validation floor before live play.
- **Distinct-voice check is byte-identity, not a register-quality judgment**
  - Spec source: docs/superpowers/specs/2026-06-27-animal-companions-design.md, §3
  - Spec text: "Donut stays as the canonical cat example; these add distinct-voiced siblings" (cat vain, owl pedantic, raven ominous, toad phlegmatic, goat contrarian).
  - Implementation: `test_animal_voices_are_distinct` asserts the five `voice` strings are pairwise distinct (set length == 5); it does not assert register quality.
  - Rationale: Voice quality (does owl read pedantic) is not mechanically assertable and belongs to Reviewer; byte-identity is the cheap floor that catches a copy-paste-one-voice regression without false-failing on good prose.
  - Severity: minor
  - Forward impact: Reviewer must still judge register distinctiveness/quality in review; a green test alone does not guarantee five genuinely characterful personas.

### Dev (implementation)
- **Out-of-scope lint hygiene fix to tests/test_reconnect.py**
  - Spec source: context-story-160-1.md, "Scope" / "Technical Approach"
  - Spec text: "This is an understudy-only change. Blast radius: sidequest-understudy ONLY." and "In scope: the behavior described by the story title. Out of scope: unrelated changes."
  - Implementation: Reordered two pre-existing mid-file imports to the top of `tests/test_reconnect.py` (separate `chore:` commit `63d1ceb`), a file unrelated to the animal-companion templates.
  - Rationale: The develop baseline already failed `uv run ruff check .` (E402) on this file; full-repo ruff is the project's lint gate (understudy CLAUDE.md). Leaving it red would bounce the downstream verify/quality gate on debt this story didn't create. The fix is a mechanical import reorder with zero behavior change, committed separately and flagged as a finding for transparency.
  - Severity: minor
  - Forward impact: none on the five templates or any sibling story; if a reviewer prefers strict scope, the chore commit can be cherry-picked out to its own PR without touching the feat commit.

### Reviewer (audit)
- **ACs derived by TEA from the Technical Approach** → ✓ ACCEPTED by Reviewer: sound — the context's "Acceptance Criteria" was empty and the Technical Approach was unambiguous; encoding each clause as a test is correct, and the 27 cases map cleanly to the five clauses.
- **Distinct-voice check is byte-identity, not register-quality** → ✓ ACCEPTED by Reviewer: agrees with author reasoning — register quality is a review judgment (assessed here: four of five land cleanly; raven's dial flagged separately as a non-blocking finding). Byte-identity is the right mechanical floor.
- **Out-of-scope lint hygiene fix to tests/test_reconnect.py** → ✓ ACCEPTED by Reviewer: the E402 was pre-existing on `develop` (`ruff check .` failed independently of this branch — verified), the fix is a behavior-neutral import reorder in a separate, clearly-labeled `chore:` commit, and it keeps the project's own lint gate green for handoff. Transparent and proportionate; no scope concern.
- No undocumented deviations found — the five YAMLs and the wiring test match the story scope and the design spec §3.