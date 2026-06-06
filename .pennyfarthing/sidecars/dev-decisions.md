## Dev Decisions

### Product direction (settled — don't revisit)
- **Narrative consistency is the #1 product goal.** The solo narrative experience is the core value prop. Mechanical state (known_facts, LoreStore, NPC registry, inventory) exists specifically as guardrails for the LLM — not as game mechanics for the player. Every bug that breaks consistency (NPC name changes, forgotten items, lost facts, turn count resets) is high priority.
- **Book conceit is retired.** UI has pivoted to persistent docked sidebar + Current Turn Focus + Scrollable History. No modal overlays to ask for your own state. Decided 2026-04-05.
- **No skeumorphism.** Genre-flavored chrome is fine (three archetypes: `parchment`, `terminal`, `rugged`). But the UI is functional first — standard interaction patterns, persistent visible state. No Roman numeral turn counters, no paginated storybook, no scroll-to-request-own-stats.
- **Spoiler protection for world content.** Keith wants to discover narrative surprises in play. Flag "this faction has a secret motivation" without revealing what it is. Only `mutant_wasteland/flickering_reach` is fully spoilable.
- **World-building creative split.** Keith owns mechanics/crunch (always discuss rules changes). World Builder has creative freedom on flavor/lore/story/NPCs/plot hooks. Keith wants to be surprised like a player trusts a DM.

### Music / audio
- **Music is cinematic, not video game BGM.** Overtures, cues, one-shots with fades. Never looping. Crossfade between tracks on mood changes.
- **Music is pre-rendered files from `genre_packs/{genre}/audio/music/`**, NOT daemon-generated. The daemon has nothing to do with music. Investigate music bugs via: (1) the audio directory, (2) API `music_cue_produced` logs, (3) `audio.yaml` mood→track mappings. Never check the daemon.
- **ACE-Step for music generation**, not the daemon. Lives at `/Users/keithavery/Projects/ACE-Step/` with its own venv: `.venv/bin/python3 generate_tracks.py --config <genre> --output_dir <path>`. Must be run from the ACE-Step directory. System Python won't work.
- **ACE-Step audio2audio is the validated approach for theme variations.** Produces real leitmotif variations with `ref_audio_strength` 0.25-0.55. Canonical theme per mood + a2a variations, not random text2music. Script: `scripts/generate_theme_variations.py`.
- **Road warrior music is high priority.** Genre identity is heavily audio-driven (Doof Warrior / Mad Max). Prioritize music quality and variation count here.

### Voice / TTS
- **TTS was intentionally stripped from the daemon in story 27-1** (commit 8583162, 2026-04-07). `daemon.py::WorkerPool.render` now only handles Flux tiers and rejects everything else with `Unknown tier: 'tts'`. The daemon is an image-only renderer.
- **`--no-tts` defaults to `true`** on sidequest-server (as of fix `3fe6c2e`, 2026-04-09) to match the daemon reality. The escape hatch `--no-tts=false` is preserved for the day someone restores daemon TTS.
- **Creature voice parameters flow through `VoiceRouter`** — narrator + character archetype + creature type voice assignment. Still wired on the Rust side even though the daemon dropped synthesis.

### Text rendering / UI chrome
- **Dinkus scene breaks are CSS-based.** No PNG images. Don't audit for them, don't generate them.
- **Drop caps are CSS-based.** Same — no illuminated drop cap images to generate.
- **Three genre-chrome archetypes driven by `theme.yaml`:**
  - `parchment` — low_fantasy, tea_and_murder, spaghetti_western, caverns_and_claudes
  - `terminal` — neon_dystopia, space_opera, mutant_wasteland, star_chamber
  - `rugged` — road_warrior, pulp_noir, elemental_harmony
- **Genre theming infrastructure already exists:** `theme.yaml` + `client_theme.css` per genre pack, injected via `useGenreTheme` hook. CSS vars (`--primary`, `--surface`, `--accent`) bridge to Tailwind automatically. The gap is that only narrative elements get genre CSS classes; panels use generic Tailwind — fix in place, don't reinvent.

### Content systems (Keith's 30-year domain)
- **Conlang is a core feature**, not a footnote. Corpus files (`.txt`) contain real-world phoneme banks; cultures use `corpora` with `weight` + `lookback` to Markov-generate new names; each faction blends 2+ languages (Clockwork Orange / Nadsat style, not translation). `word_list` is only for place_nouns and adjectives — given/family names always use corpora. Phonemes feed Kokoro for pronunciation (when/if TTS returns).
- **Procedural systems lineage.** SideQuest's NPC registry, trope engine, POI generation, cartography, conlang — these draw on 30 years of Keith's prior work (MUSHcode, populinator, lango, gotown, townomatic, steading-o-matic). Respect the domain expertise. These are not speculative design experiments.
- **"Yes, And" as a foundational principle** — origin is MUSH softcode accepting player creativity as canon vs. MUD hardcode. This is SOUL principle #9 and it's non-negotiable.

### Infrastructure
- **Tailscale for playtest connectivity** (private network, no port forwarding, free for 100 devices).
- **Cloudflare R2 for asset backup** (10GB free, zero egress). rclone sync from `genre_packs/` for `*.ogg` and `*.png`. `just assets-push` / `just assets-pull` recipes.
- **Cloudflare Tunnel + Access for long-term public exposure.** Domain-based, WAF, rate limiting, player allowlist. e.g. `play.domain.com`.
- **Save files live at `~/.sidequest/saves/`** — SQLite `.db` files, one per genre/world session. Not in the repo. See `.pennyfarthing/guides/save-management.md`.

### Tech stack split
- **Rust for everything non-LLM.** Game engine (`sidequest-game`), protocol (`sidequest-protocol`), server (`sidequest-server`), genre loader (`sidequest-genre`), Claude orchestration (`sidequest-agents`), daemon client (`sidequest-daemon-client`), CLI tools (namegen, encountergen, loadoutgen, validate).
- **Python daemon for ML inference only:** Flux.1 (images), *previously* Kokoro (TTS, stripped story 27-1), *previously* ACE-Step (music, stripped story 27-2 — music gen now runs standalone from `~/Projects/ACE-Step/`). The daemon is an image-only sidecar now.
- **Claude calls always go through Rust subprocess.** Never import the Claude SDK into Python.

### Process decisions for SideQuest specifically
- **Skip architect gates and spec checks.** Personal learning project, not a work repo. TDD runs RED → GREEN → VERIFY → REVIEW → FINISH. No architect spec validation, no spec-check/spec-reconcile, no epic/story context docs required.
- **Epic 15 (Playtest Debt Cleanup) is a zero-new-debt mandate.** Every agent working an Epic 15 story re-reads CLAUDE.md before starting. Wire existing code, don't reimplement. If the function being wired is itself a stub, fix it properly in-story.
- **Build verification happens on OQ-2.** All sidequest-api edits live in OQ-1/sidequest-api. After merge, pull on OQ-2 and `cargo build -p sidequest-server` there (not workspace root — that's a placeholder).

### Reference locations
- **Original Python SideQuest:** `~/ArchivedProjects/sq-1` — source of truth when porting behavior to Rust.
- **ACE-Step music generator:** `/Users/keithavery/Projects/ACE-Step/.venv/bin/python3 generate_tracks.py`.
- **Ping-pong file:** `/Users/keithavery/Projects/sq-playtest-pingpong.md` (read every 2-3 min during active playtest).
- **Ping-pong archive:** `/Users/keithavery/Projects/sq-playtest-archive/{timestamp}.md` (rotate when the pingpong gets long).
- **Genre packs:** `sidequest-content/genre_packs/` (subrepo, single source of truth — NOT `oq-2/genre_packs/` which has only media subdirs).

### Hardware context for Dev decisions
- **MacBook Pro M3 Max 128GB** — can run Flux locally without VRAM constraints. No CUDA, so tooling must support MPS (Metal Performance Shaders) or CPU fallback. Unified memory means ML workloads don't have to round-trip across PCIe. 40-core GPU.

### Don't over-gate playtest API spend (2026-06-05, Keith directive)
- **Decision:** When running OTEL/narrator playtests (`scripts/playtest.py`), do NOT stall on cost or ask repeated go/no-go for normal-size scenarios. Keith: "don't worry about the charges so much." A 10-action scenario projects ~$0.39 (under the built-in $0.50 ADR-134 cap); just run it.
- **Why:** The diagnostic value of a live narrator-in-the-loop OTEL run (lie-detector spans: confrontation.intent_mismatch, dispatch.gated, wwn.* / wwn.spell.cast firing or not) outweighs the small per-run cost. Excessive cost-confirmation slows the work without protecting anything the built-in `--max-projected-cost-usd` cap doesn't already cover.
- **How to apply:** Run playtest scenarios directly. Still surface the projected cost line in passing, and still stop for genuinely large/unbounded runs — but normal bounded scenarios don't need a spend confirmation. The cost cap is the guardrail; trust it.

### Per-turn narrator cost: static prose is squeezed — RAG is the next lever (2026-06-06, Keith directive)
- **Decision:** **Do not re-attempt trimming the stable narrator prose** (`sidequest-server/sidequest/agents/narrator_prompts/*.md` — the `STABLE_SECTION_NAMES` set in `prompt_framework/bucket.py`). That juice is squeezed. The next per-turn cost lever is **proper RAG utilization to shrink the volatile `game_state` snapshot**, not prose edits.
- **Why (the forensics):** A live `2026-06-06-the_circuit` drive showed the per-turn structure is already correctly tiered: a ~14.3k-tok **stable prefix** (system + tools) written once @1h and read at $0.30/M, and a ~10–12k-tok **volatile tail** written @5m (~$0.04/turn). The volatile tail is dominated by the `game_state` snapshot (~14.5KB / ~3.6k tok), which is **truncated** to fit — 14+ NPCs dropped per turn — while the ADR-118 universal-retrieval layer is **already live** and surfaces the relevant NPCs/factions/lore by similarity for ~300–700 tok. We pay twice: fat snapshot *plus* retrieval. The static `.md` prose (~5.5k tok total) is in the **read** tier — a 20% cut ≈ $0.0003/turn (~$0.03 / 85-turn session): wrong tier, negligible dollars.
- **Why trimming the prose is actively unsafe:** what reads as "redundancy" is mostly **test-pinned regression fingerprints**. Compressing the four "Patients on a sickbed count…" sentences in `output_only.md` broke `tests/agents/test_57_4_recency_guardrails_migration.py` and `test_61_12_output_format_compaction.py` — and **ADR-111 §Alternatives B explicitly rejected** exactly that compression ("the bug-report specificity is the regression detector, not stylistic flavor"). Add primacy/recency bookends + concrete examples (e.g. the #718 "behind him" POV case) that drive LLM compliance. This is the surface that has to "fool a career GM"; the trade is narrator quality for fractions of a cent.
- **How to apply:** For per-turn cost work, go after the `game_state` snapshot via the **RAG-rebalance** — lean on ADR-118 retrieval so the snapshot carries only structural essentials (PC, current location, active confrontation/dials) instead of shipping-then-truncating the full roster. This is ADR-110's deferred phase C (diff-with-anchor) territory and an architecture call (discuss with Keith — it's mechanics/crunch-adjacent). Full analysis: `docs/analysis/2026-06-06-narrator-per-turn-cache-write-anatomy.md` and `…-narrator-prompt-verbosity-trim-report.md`. Don't redo Story 60-3/60-4/61-19/61-20 (cache tiering) or 57-3/57-4 (prose promotion + fingerprints) — those are done.
