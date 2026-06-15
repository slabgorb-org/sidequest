---
story_id: "113-3"
jira_key: ""
epic: "113"
workflow: "trivial"
---
# Story 113-3: Relocate combat_design.md / magic_design.md out of runtime genre-pack folders into docs/

## Story Details
- **ID:** 113-3
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-15T03:30:44Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T03:18:30Z | 2026-06-15T03:19:39Z | 1m 9s |
| implement | 2026-06-15T03:19:39Z | 2026-06-15T03:25:18Z | 5m 39s |
| review | 2026-06-15T03:25:18Z | 2026-06-15T03:30:44Z | 5m 26s |
| finish | 2026-06-15T03:30:44Z | - | - |

## Technical Approach

**Scope:** Content-only move of design documentation out of runtime genre-pack folders.

**Files to relocate:**
- `combat_design.md` × 4 (neon_dystopia, pulp_noir, road_warrior, space_opera)
- `magic_design.md` × 3 (neon_dystopia, pulp_noir, space_opera)

**Destination:** `sidequest-content/docs/genre/<genre>/` (keeps design docs near their pack while removing them from the runtime content directory tree)

**Validation approach:**
1. Confirm the YAML loader (genre/loader.py) does not reference .md files in pack roots (loader is YAML-only; harmless to leave but docs belong in docs/).
2. Grep across sidequest-server, sidequest-ui, sidequest-daemon, and sidequest-content repos for any hardcoded references to the old in-pack .md paths.
3. Move files to new destination; verify no .md design docs remain at any pack root.
4. Commit the move with message.

**Branch Strategy:** gitflow (feat/113-3-relocate-design-docs)

## Acceptance Criteria
- Design docs moved out of `genre_packs/<genre>/` into a docs location
- No .md design docs remain at any pack root
- Grep confirms no code or content references the old in-pack .md paths (or references are updated)

## Delivery Findings

No upstream findings.

### Dev (implementation)
- **Improvement** (non-blocking): Orchestrator author-tooling agent definitions still point at the old in-pack design-doc path. Affects `.claude/agents/scenario-designer.md` (lines ~23, ~112, ~130) and `.claude/agents/world-builder.md` (line ~99) — update `genre_packs/{pack}/combat_design.md` → `docs/genre/{pack}/combat_design.md`. These are real orchestrator-repo files outside this story's `content` scope, so they need a separate orchestrator-`main` change; the moved files still exist, so author tooling is degraded, not hard-broken. *Found by Dev during implementation.*
- **Improvement** (non-blocking): Numerous historical orchestrator docs/ADRs/audit reports (ADR-072, `docs/genre_pack_*.md`/`.csv`, `docs/genre-pack-structure.md`, `docs/genre_pack_runtime_inheritance.md`, `docs/design/magic-*.md`) describe the old in-pack layout. These are point-in-time records and were intentionally NOT rewritten. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Confirmed the orchestrator author-tooling agent definitions `.claude/agents/scenario-designer.md` (≈lines 23, 112, 130) and `.claude/agents/world-builder.md` (≈line 99) still point at `genre_packs/{pack}/combat_design.md`. Affects those two files (update path → `docs/genre/{pack}/combat_design.md`). Out of this story's `content` scope (orchestrator repo, separate merge path); the moved files still exist so author tooling is degraded, not broken. Recommend a small orchestrator-`main` follow-up. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

### Dev (implementation)
- No deviations from spec. Destination chosen exactly as the story suggested (`sidequest-content/docs/genre/<genre>/`); the move is content-only via `git mv` (history preserved); the two in-content reference comments were updated per the AC's "(or references updated)" clause.

### Reviewer (audit)
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed — destination matches the story's suggested `docs/genre/<genre>/`, all 7 moves are 100%-similarity renames (no content change), and the 2 in-content reference comments were correctly updated. The orchestrator-side author-tooling / historical-doc references fall outside this story's `content` scope and are correctly captured as non-blocking Delivery Findings rather than undocumented deviations. No undocumented deviations found.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-content):**
- `genre_packs/{neon_dystopia,pulp_noir,road_warrior,space_opera}/combat_design.md` → `docs/genre/<genre>/combat_design.md` (git mv, 4 files)
- `genre_packs/{neon_dystopia,pulp_noir,space_opera}/magic_design.md` → `docs/genre/<genre>/magic_design.md` (git mv, 3 files)
- `genre_packs/space_opera/magic.yaml` — comment reference updated to new path
- `genre_packs/space_opera/progression.yaml` — comment reference updated to new path

**Verification:**
- No `combat_design.md` / `magic_design.md` remain at any pack root (`find` confirms empty)
- Server genre loader is YAML-only — no runtime `.md` reads of pack files (grep confirmed)
- No code or content references the old in-pack paths; the only 2 content references (space_opera YAML comments) were updated
- `space_opera` pack validates **PASS (0 errors, 32 pre-existing warnings)**

**Tests:** N/A — trivial workflow, content-only documentation relocation (no RED phase)
**Branch:** feat/113-3-relocate-design-docs (pushed to origin)

**Handoff:** To review phase (The Merovingian)

## Sm Assessment

**Status:** Ready to handoff to implement phase.
**Session file location:** /Users/slabgorb/Projects/oq-4/.session/113-3-session.md
**Branch:** sidequest-content/feat/113-3-relocate-design-docs (develop base)
**Workflow type:** phased (trivial: setup → implement → review → finish)
**Next agent:** implement phase agent

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled subagents returned clean; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 non-blocking follow-up (orchestrator agent-def path drift, deferred to a separate orchestrator change)

### Rule Compliance

Enumerated every applicable rule against the diff (7 `.md` renames + 2 YAML comment edits in sidequest-content):

- **CLAUDE.md (content) — LFS / asset hosting ("Never commit fresh PNG/JPG/WebP via LFS"):** N/A — all moved files are markdown text, not binary assets; `.gitattributes` LFS rules (`*.png`) do not apply. Compliant.
- **CLAUDE.md (content) — Reference page anchors (slug stability = name stability):** Not triggered — `combat_design.md` / `magic_design.md` are design notes, not reference-page entities (classes/cultures/legends/locations). Reference pages build from rules.yaml/lore, not these `.md` files; no inbound anchors break. Compliant.
- **CLAUDE.md (content) — No silent fallbacks / No stubbing:** N/A — no code changed. Compliant.
- **CLAUDE.md (content) — "No 1898 org / no work GitHub org":** Checked all 9 files — no work-org references introduced ([SEC] confirms). Compliant.
- **SOUL.md — "Crunch in the Genre, Flavor in the World" / ADR-140 (genre→world boundary hygiene):** The move removes non-runtime design docs from the runtime-loaded pack tree, directly serving the epic-113 boundary-hygiene goal. Aligned.
- **Loader contract (YAML-only):** Verified the genre loader never reads pack `.md` files; removing them from pack roots cannot affect runtime. Compliant.

All applicable rules: compliant. No violations.

### Devil's Advocate

Let me argue this change is broken. First attack: a `git mv` reported at "similarity index 100%" can still be wrong if the destination collides with an existing file or the move leaves a half-state — but `find` confirms zero design docs remain at pack roots and the seven destinations under `docs/genre/<genre>/` are newly created, so there is no clobber and no orphan. Second attack: the loader is claimed "YAML-only," but what if some pack globs its own directory for `*.md` and now silently loads nothing where it used to load something? The preflight ran the real `sidequest.cli.validate` against space_opera (the only pack whose YAML changed) and got PASS with 0 errors, and the loader grep shows no `.md` pack reads — so no pack ever consumed these files. Third attack: the two YAML edits are comments, but a careless edit could shift indentation or break the document around them — `yaml.safe_load` succeeds on both files and the diff shows only comment lines changed, so structure is intact. Fourth attack — the real one: stale pointers. The orchestrator's `scenario-designer.md` and `world-builder.md` agent definitions still tell authoring agents to read `genre_packs/{pack}/combat_design.md`, which no longer exists there, so a future content-authoring session could fail to locate the file. But the files still exist (moved, not deleted), are discoverable by name, live in a different repo outside the story's declared `content` scope, and Dev correctly logged this as a non-blocking Delivery Finding for a separate orchestrator change. It degrades author ergonomics; it does not break the running game or this story's AC ("no *code or content* references the old paths" — satisfied). Fifth attack: historical docs/ADRs now misdescribe the layout — but those are point-in-time records and intentionally immutable. Conclusion: no runtime breakage, no AC violation, no data loss; the single real-world consequence is cross-repo doc-pointer drift, properly deferred. Nothing here blocks.

## Reviewer Assessment

**Verdict:** APPROVED

**Change:** Content-only relocation — 7 design docs (`combat_design.md` ×4, `magic_design.md` ×3) moved from `genre_packs/<genre>/` to `docs/genre/<genre>/` via 100%-similarity `git mv`, plus 2 YAML comment cross-reference fixes in `space_opera/magic.yaml` and `progression.yaml`.

**Cause and effect traced:** Old in-pack path → new docs/ path. The only consumers of these paths were (a) the runtime loader — which never read `.md` files (verified YAML-only; space_opera validates PASS), and (b) two in-content YAML comments — which Dev updated to the new path. No runtime cause-effect chain is broken.

**Observations:**
- [VERIFIED] All 7 renames are byte-identical — `git diff develop...HEAD -M` reports `similarity index 100%` for each; no content corruption.
- [VERIFIED] No design `.md` remain at any pack root — `find genre_packs -maxdepth 2` returns zero; new files present under `docs/genre/<genre>/`.
- [VERIFIED] Both YAML comment edits are correct and parse — `magic.yaml` and `progression.yaml` now reference `docs/genre/space_opera/magic_design.md`; `yaml.safe_load` succeeds on both.
- [SEC] reviewer-security: clean — no secrets/credentials in any of the 7 moved files, no injection surface, no work-org references.
- [VERIFIED] No runtime code/content references old paths — preflight grep across all 6 subrepos = zero hits; space_opera pack validates PASS (0 errors, 32 pre-existing warnings).
- [SIMPLE] (simplifier disabled — assessed by Reviewer) Change is minimal and well-scoped: `git mv` + 2 comment edits, simplest sensible destination; no over-engineering, no dead code.
- [DOC] (comment-analyzer disabled — assessed by Reviewer) The 2 edited comments are accurate post-move; no stale or misleading comments introduced.
- [TYPE] N/A — no types changed (docs / YAML-comment only).
- [EDGE] N/A — no logic or branches; a file move has no boundary conditions.
- [SILENT] N/A — no error-handling paths changed.
- [TEST] N/A — trivial workflow, content-only relocation; loader behavior unchanged and revalidated.
- [RULE] (rule-checker disabled — assessed by Reviewer) All applicable content/SOUL rules compliant — see Rule Compliance section.
- [LOW][non-blocking] Orchestrator author-tooling agent-defs (`scenario-designer.md`, `world-builder.md`) still point at old in-pack path — out of content scope, files still exist, deferred to a separate orchestrator follow-up (Delivery Finding).

**Data flow traced:** in-pack `.md` path → docs/ path; only live reference was 2 YAML comments, both updated; loader never touched these files (safe).
**Pattern observed:** clean `git mv` relocation preserving history at `docs/genre/<genre>/`.
**Error handling:** N/A — no executable code in diff.

**Handoff:** To SM (Morpheus) for finish-story.