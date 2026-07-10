# Story 164-7 Context

## Title
Tavern+vault archetypes, e2e enter/map/grid/exit + tavern_enter_trace scenario (plan tasks 13–14)

## Metadata
- **Story ID:** 164-7
- **Type:** story (CAPSTONE of Epic 164)
- **Points:** 3
- **Priority:** p1
- **Workflow:** spdd (YAML tags it "superpowers"; the real workflow is spdd)
- **Repos:** server, content, orchestrator
- **Epic:** 164 — Mapping Track B — Site system (seam contract, archetypes)
- **Spec:** `docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md` (§1/§3/§4)
- **Plan:** `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` — **Tasks 13–14** (B2 acceptance target)

## Problem
Epic 164 generalized the procedural-dungeon machinery (formerly hard-fenced to
`beneath_sunden`) into a first-class **Site** system: SiteRegistry, symmetric
enter/exit seam resolvers, scene context, `DUNGEON_MAP→SITE_MAP` protocol cutover,
UI handling, and (164-6) the archetype catalog schema + bounded one-txn
materialization + site single-writer. **Everything is built but nothing exercises
the tavern/vault archetypes end-to-end.** This story authors the two reference
archetypes as *content*, attaches them to real world nodes, and proves the whole
enter → map → grid → exit loop — the acceptance target that closes Track B (B2).

Siblings 164-1..164-6 are all done + approved. This is the last non-follow-up story
in the epic. B3 (minted-on-the-fly sites) and B4 (visual polish) are OUT OF SCOPE.

## Technical Approach

### Task 13 — Tavern + vault archetype content + e2e handler wiring
Author archetypes as **content** (no engine change — that's the whole point; if this
needs a server change, that's a content-surface failure):

- **Content (content repo):**
  - Create `genre_packs/tea_and_murder/site_archetypes.yaml` — `tavern` archetype:
    `interior_algorithm: roomcorridor`, `grid_width: 15`, `grid_height: 20`,
    `cell_scale_feet: 5`; room vocab: common room / kitchen / cellar / private parlour;
    feature palette: hearth / bar / stairs.
  - Create `genre_packs/space_opera/site_archetypes.yaml` — `vault` archetype:
    `interior_algorithm: roomcorridor`, larger grid (~25×25), `cell_scale_feet: 5`;
    room vocab: antechamber / reliquary / security-lock / data-core.
  - `blackthorn_moor/cartography.yaml` — add `sites:` block: `blackthorn_arms`
    (name "The Blackthorn Arms", archetype `tavern`, `attached_to: thornkirk`,
    `extent: bounded`). `thornkirk` already narrates "The Blackthorn Arms pub" — natural fit.
  - `aureate_span/cartography.yaml` — add `sites:` block: `kesh_vault`
    (name "The Vaal-Kesh Vault", archetype `vault`, `attached_to: underspine`,
    `extent: bounded`). No `routes:` required — `SiteDecl.attached_to` IS the seam ownership.
- **Server test (server repo):** `tests/server/test_site_enter_exit_handler.py` —
  handler-level wiring test. **STUB the intent-router pass** (feed a pre-built
  `enter_site` dispatch per the flaky-test rule), drive the real turn-dispatch path
  (or `run_movement_dispatch` + the map-emit helpers), assert:
  1. after `enter_site` → PC region is the site entrance;
  2. `_maybe_emit_dungeon_map` emits `SITE_MAP` with `site_id=="blackthorn_arms"`;
  3. `_maybe_emit_tactical_grid` / `_maybe_build_runtime_cavern_payload` emits
     `TACTICAL_GRID` for the entrance room;
  4. after `exit_site` → PC back on `thornkirk`, world cartography owns the scene
     (`MAP_UPDATE`, no `SITE_MAP`).
  Use span assertions for mechanical facts (`site.enter` / `site.materialize.commit` /
  `site.exit`). If the tactical grid needs `SIDEQUEST_OUTPUT_DIR`, set it to `tmp_path`.

### Task 14 — `tavern_enter_trace` headless playtest scenario
Create `scenarios/tavern_enter_trace.yaml` in the **orchestrator repo** (THIS repo,
`/Users/slabgorb/Projects/oq-2` — the plan's `oq-3` path is a stale clone reference;
scenarios live in whichever orchestrator clone you're in). Model on
`scenarios/sunden_descend_trace.yaml`. Actions walk into the Blackthorn Arms, look
around the interior, step deeper, and leave. Top-of-file comment block names the
spans to assert. Run `just playtest-scenario tavern_enter_trace` (with `--span-jsonl`)
against the running stack; verify mechanics via spans — **never credit narration prose**.

## Scope
- **In scope:** two archetypes (tavern, vault) as content; two site declarations on
  real world nodes; one server handler wiring test; one headless scenario + span
  assertions; e2e verification in the running stack; content-validator pass.
- **Out of scope:** any engine/schema change (the machinery is built); B3 minted
  sites; B4 per-archetype visual polish; 164-9 ambiguous-descriptor disambiguation.

## Acceptance Criteria
- **AC-1** — `tea_and_murder/site_archetypes.yaml` (tavern) and
  `space_opera/site_archetypes.yaml` (vault) authored per the schema and passing
  `python -m sidequest.cli.validate pack` for both packs.
- **AC-2** — `blackthorn_moor` declares site `blackthorn_arms` (tavern on `thornkirk`)
  and `aureate_span` declares site `kesh_vault` (vault on `underspine`), both `bounded`.
- **AC-3** — `test_site_enter_exit_handler.py` proves the loop: `enter_site` →
  `SITE_MAP` (`site_id=="blackthorn_arms"`) + `TACTICAL_GRID` emitted; `exit_site` →
  PC back on `thornkirk`, world scene resumes (`MAP_UPDATE`, no lingering `SITE_MAP`).
  Includes a wiring test proving reachability from a production code path.
- **AC-4** — `scenarios/tavern_enter_trace.yaml` exists with actions + a span-assertion
  comment block; a scenario run emits `site.enter`, `site.materialize.commit`
  (exactly once across re-entries, node_count≥3), `dungeon.map_emitted` (SITE_MAP),
  `tactical_grid.emitted` (TACTICAL_GRID), `site.exit` — and NONE of
  `site.enter_unresolved`, `movement.unresolved`, `dispatch_engagement.movement.mismatch`.
- **AC-5** — e2e verified in the running stack: walk into the pub, Map tab shows the
  tavern local map + tactical grid + breadcrumb, exit returns to the world map.

## Watch-outs (SM notes for TEA/Dev)
- **Content-surface discipline (CLAUDE.md, Jade's requirement):** archetypes and site
  declarations are homebrew *content*. If authoring them requires touching engine code,
  that's a content-surface failure — surface it as a Delivery Finding, don't paper over it.
- **No Silent Fallbacks:** 164-3/164-6 both drew HIGH review findings for silent
  defaults on the site path. Any missing archetype / unresolved site must fail LOUDLY
  with a diagnostic + OTEL span — mechanical facts get spans, not just prose.
- **OTEL is the lie detector:** every enter/materialize/exit must emit spans. Verify
  the pipeline via spans; the scenario explicitly asserts negative spans too.
- **Stale path:** plan Task 14 references `/Users/slabgorb/Projects/oq-3`; we are in
  `oq-2`. The scenario file belongs in this repo's `scenarios/`.
- **orchestrator repo is trunk-based** (no feature branch created) — scenario commits
  land per local convention; server + content have `feat/164-7-...` branches.

---
_Enriched by SM (Vizzini) from plan tasks 13–14. Auto-stub replaced 2026-07-10._
