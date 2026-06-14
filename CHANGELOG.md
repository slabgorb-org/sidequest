# Changelog

All notable changes to this orchestrator repo are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Subrepos (`sidequest-server`, `sidequest-content`, `sidequest-daemon`, `sidequest-ui`)
keep their own CHANGELOGs; this file tracks orchestrator-side changes only.
For the cross-repo, product-level feature history, see [`docs/FEATURES.md`](docs/FEATURES.md).

## [Unreleased]

## [1.4.0] - 2026-06-14

> Window 2026-05-26→06-14 — the orchestrator-side arc of Sprint 2624:
> ruleset-bound combat & magic, cost observability, and the reference SPA
> migration. Headlines: the Without Number ruleset becomes the binding
> authority for combat (ADRs 142/143 — bind the ruleset, stop balancing the
> native engine); the architecture-of-record is reconciled (ADRs 117–143
> landed or retroactively recorded); R2 becomes the canonical media source;
> and a new `sidequest-understudy` subrepo joins the fleet.

### Added

**Ruleset combat & magic (Sprint 2624 spine)**
- ADR-143 — a Without-Number binding *replaces* the native combat engine
  (#398): the bound ruleset owns the WN round, native `apply_beat` scaffolding
  is cut, and "bind the ruleset, don't balance it" is promoted to SOUL.md
  doctrine after the WWN-combat dead end was ruled emphatically (2026-06-14).
  Includes the combat action-surface spec (with "full defense" struck) and the
  ruleset chargen-seam spec/plan moving chargen onto `RulesetModule` + a WWN
  substrate.
- ADR-142 — Without Number core extraction: an honest `WithoutNumberRulesetModule`
  base, reparented WN siblings (WWN/SWN/CWN/AWN), a shaped-attribute retune,
  with source spec.
- Pluggable SRD ruleset design corpus (ADR-117): faithful SWN `RulesetModule`
  specs/plans (attack-vs-AC, skill checks, saves, engine-owned 1d8+DEX
  initiative spine, dogfight×SWN); CWN design (foundation/binding, System
  Strain, hacking-as-confrontation `net_run`, `neon_dystopia → CWN`); WWN module
  foundation + `elemental_harmony` binding; `road_warrior → CWN` two-tier rig
  combat; Barsoom sword-and-planet world on the heavy_metal/WWN chassis; 87-2
  heavy_metal WWN classes, chargen & real magic.
- AWN Plan 2 mutation engine — `MutationPlugin` + tables spec/plan, with
  `magic.yaml` reconciliation.
- Light & darkness generic environmental survival-clock spec + implementation
  plan.

**Architecture of record (ADR consolidation)**
- ADRs 118–143 landed or retroactively recorded against live mechanisms:
  ADR-118 Universal Retrieval Layer (+ unified pertinence scorer, lifecycle
  scope, tiered forgetting); ADR-119 authenticated player identity
  (player-vs-character split); ADR-135 reference pages as a public table tool;
  ADR-136 player-facing relationship surface (RELATIONSHIPS projection,
  disposition beat-log, claims-only belief firewall) marked live; ADR-139
  confrontation integrity invariants; ADR-140 (supersedes ADR-120) — genre is
  the rulebook, the world owns the cast & catalog; retroactive Tier-2 ADRs
  120–134 and Tier-3 amendments from an architecture-of-record audit; ADR-091
  real-Earth naming amendment; ADR-115 amended to a direct Postgres port.

**Feature-inventory generator (new tooling)**
- `feature-inventory` — a fail-loud cross-repo coverage generator (manifest
  loader + schema validation, ADR-status / draft-world / wiring-test / module
  verifiers, span-constant registry parser, status-verification rule engine,
  markdown renderer + marker writer, `just` regen/check-guard recipes), seeded
  with a one-time cross-repo coverage census and the Confrontation Engine
  category migrated to a verified manifest.

**R2 media pipeline (R2 is now canonical)**
- R2 becomes the canonical media source: renders upload to R2 on success and the
  docs declare R2 + `r2_manifest.json` the record of truth (#369). Further Epic
  65 work: `r2_manifest.json` existence oracle (1,743 entries, #322),
  `r2_manifest_from_bucket` live-scan rebuild (#332), `r2_pull.py` downloader,
  world-level NPC portraits + display-on-invocation wiring (#308), self-hosted
  fonts from R2 (#350), `--shard i/n` to split render batches across machines
  (#329), per-tier portrait style suffix, and `r2_audit` parsing pack
  `audio.yaml`.
- `render_world_assets.sh` batch POI+portrait gate, an R2-backed live preview
  gallery + `generate_r2_preview.py` asset sheet (#393), portal-picker /
  culture-gate authoring gotchas, and `scripts/render_queue.py` sequential
  render→sync runner with `scripts/README.md` documenting the pipeline (two-venv
  boto3 split, `--steps`/`--force`, never-switch-branches-mid-render, absolute
  R2 paths).
- `render_pd_audio` reconciler (`--bucket`) + composer wiring for the
  public-domain music buckets (#343).

**Cost observability (Sprint 2624 spine)**
- `sq-llm-costs` skill — LLM cost & cache forensics (Layer-0 provenance
  preflight, Haiku visibility) reconciling server-log narrator spend against the
  Anthropic Admin API.
- Dark-spend reconciliation script + GM-dashboard cost endpoints (91-5, #383).

**Reference SPA migration (Sprint 2624 spine)**
- Reference pages → React SPA migration design, plus the reference lore
  projection API map-slice spec/plan (Phase 1 Slice A).

**Playtest, authoring & world design**
- `sidequest-understudy` — new subrepo: a naive black-box simulated-player
  playtest client that joins real sessions via the UI. Wired into `repos.yaml`
  and a `just` recipe; design spec, 13-task TDD plan, reconnect via persisted
  browser state.
- `sq-playtest` generalized to DRIVER/FIXER roles with player host aliases +
  save forensics, and a Phase-0 "what changed since last playtest" test
  manifest.
- heavy_metal OTEL playtest scenarios (87-4) under `scenarios/`.
- wry_whimsy premise substrate plans (bloc content schema + runtime engine).
- Lobby identity genre-grouped picker + scoped theming design; NPC
  relationship-panel design (ADR-136); pool relationship projection + promotion
  (97-1).
- Epic 71 (2026-05-28 playtest): narration POV agreement, dice-overlay wiring,
  peer-action WCAG contrast, orrery far-arc label upright-flip (ADR-094),
  room-graph transition trope-tick (ADR-055), ADR-113 per-dispatch confidence
  gate; 71-19 Glenross ADR-053 scenario authoring; 71-20 fail-loud guard when
  the DB schema is behind the Alembic head (ADR-115).
- Epic 105 (beneath_sunden surface→deep crossing): seam-crossing design + spec
  (#395), `pick_portrait` chargen driver frame (105-1), Monster Manual per-room
  binding (107-2).
- `docs/FEATURES.md` — cross-repo product feature digest + one-time coverage
  census.

### Changed
- All seven repos transferred personal → `slabgorb-org` GitHub org (commercial
  prep); remotes repointed to org SSH paths via `scripts/transfer_to_org.sh`.
- The WN-family genre bindings shipped across the content/server subrepos —
  heavy_metal (WWN), mutant_wasteland (AWN mutations live), Barsoom, Seaboard of
  Saints, road_warrior (CWN); see those subrepos' CHANGELOGs and
  `docs/FEATURES.md` for detail.
- Narrator streaming now defaults **off** in `just server`/`up` (#377),
  reversing the 1.1.0 default.
- `render` `--steps` flag reaches the daemon end-to-end; default raised 15→20
  (#320). `just`/justfile loads server env from `.env` via dotenv-load (ADR-115).
- Top-level docs refreshed to the live pack inventory; orchestrator repo rename
  `orc-quest → sidequest` reflected in README + system-diagram (#322); CLAUDE.md
  reconciled to current genre/world reality and the understudy subrepo.

### Fixed
- `sm-finish` runs `pf.*` modules with the pf-tool interpreter, not the project
  `.venv`.
- `r2_audit` resolver sources audio from `audio.yaml` and drops phantom `params`
  keys; `generate_music` glob descends into `audio/music/themed/` subdirs.
- `render_common.slugify` NFKD-folds non-ASCII (101-8, #386).
- Null `completed_epics`/`completed_stories` in the 2624 sprint archive crashed
  `pf sprint status`; repaired and stubbed as empty lists.
- Restored `api-contract.md` after an accidental wip-sweep deletion.
- leak_audit perception-firewall hardening (ADR-104/105): redact cross_player
  dispatches in `redact_dispatch_package`, extended cross_player coverage,
  multi-key entity extraction.

### Removed

## [1.3.0] - 2026-05-26

> Consolidates the 2026-05-11→05-26 window — the orchestrator did not cut a
> separate 1.2.0 (subrepos did, dated 05-23). Treat this as the orchestrator's
> 1.2.0+1.3.0 combined.

### Added
- JARGONFILE.md project glossary, linked from README and CLAUDE.md.
- Anthropic SDK migration ADR set (ADR-101/102) with Phase E acceptance
  report and parity tooling; ADR statuses flipped post-merge to make the
  SDK the default narrator backend.
- ADR-105 broadcast-layer perception firewall (completes ADR-104);
  ADR-106 runtime procedural Jaquaysed megadungeon (Sünden Deep);
  ADR-107 out-of-band aside channel; ADR-108 MP item attribution;
  ADR-109 persistent location descriptions; ADRs 110/111/112 narrator
  prompt token reduction; ADR-113 Intent Router mechanical-engagement
  spine; ADR-114 ablative HP substrate (supersedes 078); ADR-115 Postgres
  persistence substrate migration; ADR-116 confrontation requires an Other.
- Scene-harness fixture library Wave 1 (12 fixtures across combat tiers,
  genre coverage, social setups, merchant/veteran-drop scenes), with
  caverns fixtures retargeted from deprecated `caverns_sunden` to live
  `beneath_sunden` (stories 51-1/51-2/51-3) and a hydration validation sweep.
- Beneath Sünden design corpus: ADR-106 plus Plans 1–8 (maze-maker port,
  region graph, depth score, theme palette, set-piece/trope-at-attach,
  session integration, world authoring), content cookbook, and
  caverns_sunden retirement.
- New cross-repo scripts: `r2_sync_packs --files` scoped uploads, labeled
  contact-sheet generator for asset review, and org Usage/Cost
  reconciliation via the Admin API.
- Epic 65 R2 asset tracking: `r2_manifest` writer + YAML-derived gap audit,
  skip-existing generation (don't re-render assets already on R2), and dedup of
  shared `_md5_of` between `r2_sync_packs` and `r2_manifest`.
- Reference-pages v3 corpus + epic-63 closeout (Rules/Lore HTML routes, chrome/
  theme, panel hyperlinks, humanization guard, region-header deep-link).
- justfile recipes: `pg-up`/`pg-status` (Postgres substrate),
  `content-validate`/`content-validate-all`, `reference-validate-all`,
  `reference-chrome-validate`, `client-typecheck` (tsc -b) and
  `daemon-test` added to `check-all`.
- Seed-trope engine (Epic 22): schema + deck engine, content for
  tea_and_murder, narrator injection, OTEL routing (SPAN_SEED_FIRED),
  engagement-triggered seed draws.
- Epic 24 world-grounding: JSON Schemas for 7 systems, weather/demographics/
  calendar generators and CLIs, narrator grounding tool call, glenross and
  spaghetti_western calendars, bootstrap loader + ToolContext wiring.
- PRD additions: §12 Competitive Landscape & Differentiation, creator
  authoring & monetization brief; reference-pages v1/v2 specs and plans;
  save-forensics post-mortem page spec/plan; durable telemetry substrate
  (forensics Phases 1–2) specs/plans.
- Genre-pack filesystem schema spec + implementation plan; SWN-crunch
  ablative-HP design spec and gear-pharmacopeia plan.

### Changed
- ADR-115 reframed/amended to a direct Postgres port (Postgres ≠ cloud;
  deployment is a separate axis), reversing the phased strangler.
- Epic 59 reframed to the Intent Router mechanical-engagement spine.
- Promoted road_warrior, spaghetti_western, neon_dystopia, pulp_noir, and
  re-promoted heavy_metal to live; CLAUDE.md/README live pack count updated
  to 10 with corrected pack lists.
- victoria genre pack renamed to tea_and_murder across operational refs.
- Subrepo branch_strategy aligned to gitflow (corrected from
  github-flow/trunk-based); dropped stale Flux reference.
- Persistent log directory with rotation and 30-day retention; `just up`
  routed through `_server-cmd`/`_client-cmd`, defaulted to OTLP export +
  watcher-as-spans, with a machine-global singleton lock and resolved
  ANTHROPIC_API_KEY.
- Top-level docs refreshed for the post-port pack list, ADR index, and
  Anthropic-SDK transport reality; ADR-067 amended for the intent-validator
  inference site.

### Fixed
- 63-13 location validator reports malformed YAML instead of crashing;
  64-4 schema-validates pack file contents.
- Renderer honors explicit POI slug instead of re-slugifying the name.
- close_store partial-teardown reconnect crash wired (61-followup-C).
- Playtest preflight cost guard / cache-aware projection and hard-cap
  oversized-canary guards (Epic 61) to curb narrator cache-write runaway.
- ANTHROPIC_API_KEY provisioned in `just server`/`serve` recipes.

### Removed
- Deprecated `caverns_sunden` retired/superseded by `beneath_sunden`;
  caverns_sunden-coupled scenario fixtures and stale screenshot/migration
  tests removed.
- Dead code dropped: redundant second dispatch-bank run (59-11),
  NpcRegistryEntry (45-52), EncounterTag deprecation alias (45-46),
  module-level run_narration_turn (49-5).

## [1.1.0] - 2026-05-11

> Backfilled 2026-05-29 — this window (post-port, 2026-04-19→05-11) was the most
> under-documented; the earlier three-bullet snapshot missed the bulk of the
> post-port restoration and infrastructure build-out.

### Added
- ADR-098 — stateless narrator turns (supersedes ADR-066), with spec/plan docs.
- Post-port restoration tracking (ADR-082 Phases 2/3): orchestrator epics 41/42 +
  decomposition plans for the chargen and combat ports (StructuredEncounter,
  ResourcePool, TensionTracker/PacingHint, threshold-lore minting to Python).
- OTEL observability restoration (ADR-090): GM dashboard recipe + CI, local
  Jaeger v2 + OTLP `just` tracing recipes, `just otel` retargeted to the served
  `/dashboard`.
- ADR set landed: ADR-086 image-composition taxonomy (Portraits/POIs/Illustrations,
  FACTION→CULTURE rename), ADR-088 frontmatter schema + validator + pre-commit hook
  + auto-generated DRIFT/SUPERSEDED indexes, ADR-089 pre-rendered cavern battle
  maps, ADR-091 culture-corpus/Markov naming, ADR-093 confrontation calibration v1,
  ADR-094 orrery label placement, ADR-096 cavern renderer revival, ADR-097 class
  mechanical surface, ADR-099 salvage hooks, ADR-105 perception firewall, ADR-107
  out-of-band aside channel, ADR-108 MP item attribution, ADR-109 persistent
  location descriptions.
- R2 CDN media migration: Phase A sync + verify scripts (HEAD probe via
  cdn.slabgorb.com), R2 env wired into justfile + `.env.example`, migration
  spec/plan.
- Daemon between-session music generation (script + ADR-095 + docs).
- justfile: `just serve`/`just tunnel` prod-deploy recipes; `client-typecheck`
  (tsc -b) added to `check-all`; `--world` filter on portrait/creature/POI
  generators; Z-Image high-fidelity tier for pre-gen scripts.
- Design corpus: Beneath Sünden / Sünden Deep (ADR-106 + Plans 1–8, content
  cookbook); orbital map / ship map / "plot a course" Kestrel design; save-
  forensics post-mortem specs/plans; durable telemetry substrate specs/plans.
- Story 47-5 sprint scaffolding (Magic Phase 6 playgroup playtest cut-points).
- Narrator streaming enabled by default (recipe + design/plan).

### Changed
- victoria genre pack renamed to tea_and_murder (operational refs).
- road_warrior and spaghetti_western promoted to live; pack count bumped 8→10
  with corrected lists in CLAUDE.md/README.
- ADR-036 amended — peer action text visible during the wait phase; sealed-letter
  doctrine clarified.
- ADR index regenerated; superseded/drift notes split into dedicated docs.
- API-contract handoff doc for the ACTION_REVEAL wire shape.

### Removed
- LoRA pipeline torn out (ADR-032/083/084 superseded): VisualStyle LoRA fields,
  daemon + server LoRA wiring, per-world LoRA YAML, and `/sq-lora` removed;
  pipeline docs archived (epic 43). (The build-out and teardown both fell in this
  window — net removal.)
- ADR-044 (speculative prerendering during TTS) retired; ADR-034 superseded;
  obsolete `sidequest-up.sh` and the CLAUDE.md preamble-sync mechanism removed.

## [1.0.0] - prior

Initial post-Rust→Python-port orchestration baseline (ADR-082): Python
`sidequest-server` stack, justfile rewritten for the Python stack, ADR-085
tracker-hygiene cutover. Not formally tagged at the time; recorded for continuity.
