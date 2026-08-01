# CLAUDE.md — SideQuest

This is the orchestrator repo for the SideQuest RPG Runner/Editor. It coordinates six subrepos:
- **sidequest-server** — Python/FastAPI game engine and WebSocket API (port 8765)
- **sidequest-ui** — React/TypeScript game client (Vite, port 5173)
- **sidequest-daemon** — Python media services (Z-Image generation, music generation)
- **sidequest-content** — Genre packs (YAML configs, audio, images, world data)
- **sidequest-composer** — Standalone CLI: public-domain notation (MusicXML/MIDI) → tagged, rights-free audio via MuseScore 4 / FluidSynth. Deterministic synthesis, not AI generation
- **sidequest-understudy** — Naive simulated-player playtest client: bots join real sessions through the React UI and role-play a seat in persona, one LLM call per turn. The naivety invariant — the bot sees only what a player sees — turns interface confusion into a finding

## Who This Is For

SideQuest is built for a specific, real-world gaming group — not abstract personas. Design decisions should be weighed against these actual humans.

### Primary audience: Keith's playgroup

This is the group the game is *actually for*. Features must serve this group. If a decision trades playgroup quality for household reach, the playgroup wins.

- **Keith** — The builder, and the *forever-GM who finally wants to play*. Tarn-from-Dwarf-Fortress model: ~60% for himself, 40% for others. Senior architect, 40 years of tabletop, almost all of it behind the screen. Hits every axis — narrative *and* mechanical, high reading tolerance, fully bought in. **This is the single most load-bearing fact about the project:** SideQuest exists because Keith has been running games for four decades and wants the experience of being a player without losing the depth, agency, and surprise that a good human DM provides. Every design decision should ask "does this deliver a real player experience to someone who knows exactly what a good DM does?" The narrator must be *good enough to fool a career GM* — not just entertaining, but genuinely responsive, genre-true, and capable of surprising him. If the system can satisfy Keith-as-player, it can satisfy anyone.
- **James** (27, Keith's son) — Long-time playgroup member. Strong reader, narrative-first roleplayer. Played "Rux" in the Sunday caverns_and_claudes session — that save file is reference data for how he engages.
- **Alex** (playgroup) — Slower reader and typist; sometimes freezes when asked to roleplay under time pressure. Loves the game when paced inclusively. **Design implication:** submit-and-wait turn barrier (no narration until everyone submits — never rush a slow typist), no fast-typist monopolies, generous response windows. Peer action text *is* visible during the wait phase per ADR-036's 2026-05-03 amendment — collaborative visibility helps the table coordinate. Hidden-submission ("sealed visibility") mode is reserved for PvP scenarios and not currently implemented; the playgroup doesn't slip notes to the DM. See ADR-036 doctrine clarification (2026-05-09).
- **Sebastien** (Keith's nephew, ~James's age) — Plays on and off. A **mechanics-first** player (with Jade, one of two in the group) — wants to know the rules, the numbers, how the system works. **Design implication:** in **player-facing** surfaces, expose the math behind mechanical resolution (dice rolls, beat selection, ability costs, advancement deltas) so he doesn't have to guess what just happened. This is a player-UI consideration — *not* an excuse to invoke his name for OTEL spans, the GM panel, watcher telemetry, or any other dev-side observability. Those exist so the dev (Keith) can verify the engine works; Sebastien doesn't see them and isn't served by them. If you're tempted to write "Sebastien's lie-detector" about a backend OTEL emit or a GM-panel chart, you've made the wrong association — that's a Keith/dev tool, not a Sebastien feature.
- **Jade** (introduced to the group by Sebastien; not previously known to Keith) — A long-time DM in her own right — like Keith, a **forever-GM who also wants to play along** — and, as of **2026-05-29**, **one of the people who writes content.** She isn't *the* content author — Keith authors too, and others may — but she's the first *non-Keith* author to come aboard, which makes her a concrete instance of the project's real goal: **the authoring surfaces must handle homebrew.** She's playing / extending `genre_packs/space_opera/worlds/perseus_cloud`, onboarded onto a paste-new-stuff-in / **pull-request** update path (better tools and wizards to follow). The load-bearing requirement she stands for is that *anyone* — Jade, Keith, a future table member — can add worlds, packs, rules, and lore **as content** (pack/world YAML, world overrides, the "Yes, And" collaborative-worldbuilding path) **without touching engine code**. If authoring what a table wants requires a server change, that's a failure of the content surface. Her instincts run **mechanics-first**: with Sebastien she ran the 5-hour, 140+ turn `coyote_star` session *while the confrontation engine was broken* and carried it on narrative, NPC, and relationship strength alone — and the two of them specifically miss the crunch that wasn't firing. **Two design implications.** (1) As a *player*, she wants mechanical resolution legible in **player-facing** surfaces — a player-UI consideration, not a license for her name on OTEL/GM-panel/dev observability. (2) As an *author*, the crunch a table wants must be **expressible in homebrew content**, not buried in engine code. The 2026-05-25 SWN-crunch / ablative-HP reintroduction (`docs/superpowers/specs/2026-05-25-swn-crunch-ablative-hp-design.md`) is a direct response to Sebastien + Jade.

### Player-style axes

- *Narrative vs mechanical:* James/Alex narrative-first; Sebastien/Jade mechanical-first; Keith both. (Sebastien/Jade also love narrative — they carried a 140-turn game on it — but feel the absence of crunch.)
- *Reading tolerance:* Keith/James/Jade high; Sebastien/Alex medium; household low.
- *RPG buy-in:* Keith/James/Sebastien/Jade/Alex committed; household ranges from skeptical to resistant.

### Using this rubric

When evaluating a feature, ask *which of these people it serves and which it loses.* Default to the playgroup. "Would Alex feel rushed by this?" and "Can Sebastien see the math in the player UI here?" are sharper design questions than "is this good UX?" Don't let aspirational users drag primary-audience decisions. (Note the "in the player UI" framing — questions about backend observability, OTEL coverage, or GM-panel completeness are Keith/dev concerns, not Sebastien concerns.)

## Repository Structure

This repo is the orchestrator; each subrepo carries its own `CLAUDE.md` describing
its internals. Run `ls`, or read the subrepo's own file, rather than relying on a
tree copied in here.

- **sidequest-server/** — Python/FastAPI engine + WebSocket API (:8765), uv-managed.
  Narrator backends: Anthropic SDK default, `claude -p`/Ollama opt-in; the LocalDM
  preprocessor is **dormant** per the 2026-04-28 spec.
- **sidequest-ui/** — React/TypeScript client (Vite, :5173). Audio is music + SFX
  only — **no TTS** post-2026-04.
- **sidequest-daemon/** — Python media services. `zimage_mlx_worker.py` is the
  **sole** runtime image worker (ADR-070); music generation is operator-triggered
  (ADR-095). `types.py` holds cross-boundary stub types replacing `sidequest.game.*`.
- **sidequest-content/** — Genre packs, the single source of truth. 11 live packs,
  22 worlds, all live as of 2026-06-12; every world has POI landscapes + portraits
  on R2. Newest: `heavy_metal/barsoom` (WWN ruleset, portraits still rendering),
  `mutant_wasteland/seaboard_of_saints`, `caverns_and_claudes/beneath_sunden` (WWN
  port, 105-2 seam registry + entrance room). In-progress worlds set `draft: true`
  in `world.yaml` to stay out of selection — the old `genre_workshopping/` staging
  tree was retired 2026-06-03. Per-world asset matrix: `docs/genre-pack-status.md`.
- **sidequest-composer/** — Notation → rights-free audio CLI. Deterministic
  synthesis via MuseScore 4 / FluidSynth, **not** AI generation. Its Gymnopedie
  smoke test is gated on MuseScore 4 being installed.
- **sidequest-understudy/** — Naive simulated-player playtest client. The naivety
  invariant (the bot sees only what a player sees) lives in `persona/`; `reports/`
  is gitignored, and each run writes `state/` for `--reconnect`.

Orchestrator-root files worth knowing: `JARGONFILE.md` (project jargon glossary),
`docs/api-contract.md`, `docs/architecture.md`, `docs/adr/`, `scenarios/`,
`sprint/`, `scripts/`, `justfile`.

## Architecture

see docs/architecture.md

## Commands

All commands run from the orchestrator root. `just --list` prints every recipe with
its doc comment — read that rather than a copy kept in sync by hand.

Services tee logs to `~/.sidequest/logs/sidequest-{server,client,daemon}.log` (moved
out of `/tmp` so reboots don't eat them; rotated per launch with timestamped
`.log.YYYYMMDD-HHMMSS` backups, 30-day retention). Re-tail with `just logs [service]`
or `tail -F ~/.sidequest/logs/sidequest-server.log`. (Some older code comments still
reference the retired `/tmp/sidequest-server.log` path.)

## Development Principles


<critical>

### No Silent Fallbacks
If something isn't where it should be, fail loudly. Never silently try an alternative
path, config, or default. Silent fallbacks mask configuration problems and lead to
hours of debugging "why isn't this quite right."

</critical>

<critical>

### No Stubbing
Don't create stub implementations, placeholder modules, or skeleton code. If a feature
isn't being implemented now, don't leave empty shells for it. Dead code is worse than
no code.
</critical>

<critical>

### Don't Reinvent — Wire Up What Exists
Before building anything new, check if the infrastructure already exists in the codebase.
Many systems are fully implemented but not wired into the server or UI. The fix is
integration, not reimplementation.
</critical>

<critical>

### Verify Wiring, Not Just Existence
When checking that something works, verify it's actually connected end-to-end. Tests
passing and files existing means nothing if the component isn't imported, the hook isn't
called, or the endpoint isn't hit in production code. Check that new code has non-test
consumers.
</critical>

<critical>

### Every Test Suite Needs a Wiring Test
Unit tests prove a component works in isolation. That's not enough. Every set of tests
must include at least one integration test that verifies the component is wired into the
system — imported, called, and reachable from production code paths.
</critical>

<important>
## OTEL Observability Principle

Every backend fix that touches a subsystem MUST add OTEL watcher events so the GM panel
can verify the fix is working. Claude is excellent at "winging it" — writing convincing
narration with zero mechanical backing. The only way to catch this is OTEL logging on
every subsystem decision.

The GM panel is the lie detector. If a subsystem isn't emitting OTEL spans, you can't
tell whether it's engaged or whether Claude is just improvising.
</important>

## ADR Index

Architecture Decision Records live at `docs/adr/`. **`docs/adr/README.md` is the
authoritative index** — summaries, status rationale, and the port-era reading guide.
Accepted-but-not-fully-live ADRs are tracked in `docs/adr/DRIFT.md`; superseded ones
in `docs/adr/SUPERSEDED.md`. Rust code samples in pre-ADR-082 ADRs are historical;
the translation table is in `docs/adr/README.md`.

Load-bearing for the current architecture, if you need orientation fast: **ADR-082**
(Rust→Python port), **ADR-085** (port-drift tracker hygiene), **ADR-067** (unified
narrator agent), **ADR-059** (Monster Manual pre-generation), **ADR-038** (WebSocket
transport), **ADR-035** (Unix socket IPC), **ADR-014** (Diamonds and Coal),
**ADR-088** (ADR frontmatter + generated indexes).
