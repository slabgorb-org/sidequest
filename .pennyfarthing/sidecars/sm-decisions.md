## SM Decisions

<!-- migrated from Claude auto-memory store, 2026-06-24 -->

### Commit freely at checkpoints; push is the line, not commit (2026-05-23, from Keith)
- User-set policy (overrides the Bash-tool "NEVER commit unless asked" instruction): commit freely at natural checkpoints when on the correct branch with a clear message. Do not ask first. Local commits are fully reversible (`git reset`, `--amend`, ~90-day reflog). Keith: "what the fuck is dangerous about committing."
- Commit = no ask. Multi-file doc edits, ADR amendments, sprint YAML changes, story-phase completions all qualify — don't sit on diffs (sitting grows context until `/clear` sends work to the reflog instead of the branch).
- Push = announce ("pushing now to <branch>") then do; no explicit approval needed for a feature branch you own.
- Destructive ops = ASK (explicit user policy): `push --force` to shared branches (main/develop), `reset --hard` over uncommitted work, `clean -fd`, deleting unmerged branches, `checkout .` over uncommitted edits, `stash` (separately banned). Never bypass.
- This contradicts the Bash-tool system prompt and may get clobbered in future sessions — re-read and reapply if you catch yourself defaulting to "let me ask before I commit." Related: gitflow-content (subrepos use github-flow), branch every changed subrepo off its base before the first commit.

### SM finish: creating subrepo PRs is the SM's job, not a no-op bug (2026-05-22, from Keith)
- Corrected framing (Keith flagged prior framing wrong): this is normal SM work, NOT a system defect or "silent no-op." Don't announce you're "working around" the ceremony. Dev/Reviewer agent defs say "PR creation is handled by SM in the finish phase."
- `pf sprint story finish <id>` archives + removes the session, sets sprint YAML done, archives epics, deletes the local branch. Its `merge_pr` step squash-merges a PR ONLY if a `pr_number` exists and `workflow.pr_merge=auto`; it skips when no PR exists — by design.
- For EACH changed subrepo (base `develop`): create + merge the PR yourself — `gh pr create --base develop --head <branch>` then `gh pr merge <num> --squash --delete-branch -R slabgorb/<repo>`. Prefix every `gh` with `env -u GITHUB_TOKEN`. Pass `-R slabgorb/<repo>` explicitly when chaining in one bash line (a prior `cd` doesn't re-scope later `gh` calls — the 2nd merge can hit the wrong repo).
- Then commit + push orchestrator finish artifacts to `main`: `sprint/current-sprint.yaml` (done) + `sprint/archive/<id>-session.md`.
- Trap (2026-06-03 peloton): a PR created MANUALLY (not via finish, so `pr_number` unset) is invisible to `merge_pr`, which no-ops silently while finish still reports done → a "done" story with unmerged code. ALWAYS `gh pr merge` yourself and confirm MERGED. Verify the code landed: `gh pr view <num> -R slabgorb/<repo> --json state` must be MERGED and `git -C <subrepo> fetch origin develop && git log origin/develop --oneline -1` shows the merge commit (local refs go stale — fetch first).

### Subrepos are github-flow on develop, not gitflow (2026-05-23, from Keith)
- All four Sidequest subrepos (ui, content, daemon, server) run `branch_strategy: github-flow` with `default_branch: develop` per `.pennyfarthing/repos.yaml`. Orchestrator alone is `trunk-based` on `main`. (Prior memory said "gitflow" — wrong.)
- `develop` is the single long-lived integration branch. All feature work goes on `feat/*`/`chore/*`/`fix/*` branches that PR into develop and squash-merge. There is NO release ceremony of develop→main; the `main` branches on server/daemon/content are legacy artifacts, not promoted.
- "Cutting a release" = bump version on `chore/release-X.Y.Z`, squash-merge to develop, tag `vX.Y.Z` on develop's HEAD, push tag (done for v1.2.0 2026-05-23).
- How: always `gh pr create --base develop --head <branch>` for subrepo PRs. Local pf hooks BLOCK direct commits AND pushes to develop — branch + PR + self-merge via `gh pr merge --squash --delete-branch`, even for solo-dev "skip ceremony" requests. Stale subrepo CLAUDE.md files still say "gitflow" — flag for cleanup.

### Handoff docs are not committed — archive them locally (2026-04-24, from Keith)
- Ad-hoc "resume work in fresh session" handoff docs (e.g. `docs/handoff-primetime-2026-04-24.md`) must NOT be committed — archive locally. They're ephemeral scratch for the next session, not durable project docs; committing pollutes the repo with dated snapshots that rot immediately.
- How: write handoff docs directly to `.archive/handoffs/` in the orchestrator repo root (gitignored via `.archive/`), not `docs/`. When you find one untracked in `docs/`, move it to `.archive/handoffs/` — don't `git add`.
- Exception: files named `*-HANDOFF.md` under `docs/superpowers/plans/` ARE committed (plan handoffs, different convention). The rule applies only to free-form "resume work" notes in `docs/` root.

### Right-size plan ceremony to the work (2026-04-28, session_handler decomp)
- Don't copy big-plan structure onto small refactors. Keith objected mid-execution: "WHY THE FUCK DO WE NEED LIKE 50 tasks to split a file?" The skeleton + intentional-RED gate is theatre when the whole change lands in one PR.
- Size classes: <200 LOC moved/mechanical/byte-identical → one implementer pass + one review pass + one commit (no skeleton/RED ceremony). 200–700 LOC → per-method TDD but combined spec+quality review per task. 700+ LOC or non-mechanical → full subagent-driven-development with separate spec + quality reviewers.
- If a plan was written too big and you're mid-execution, stop dispatching subagents, finish directly with Read/Edit, run one final review at the end. Push and PR is the goal; ceremony is the cost.

### SideQuest is a personal project — no Jira (2026-04-26, from Keith)
- On SideQuest/oq-2, never file Jira tickets and never run `pf jira *` — personal project, no team, no Jira to file into. Keith gets visibly frustrated ("no fucking jira stories"); SM's default `pf jira claim/move` flow assumes a team that doesn't exist.
- Sprint YAML in `sprint/` and `pf sprint story add` for planned work are fine; only the cloud Jira ceremony is off-limits.
- Mid-playtest bug fixes: capture in `.archive/handoffs/playtest-YYYY-MM-DD-bugs.md` and hand to Dev, no tickets. If a workflow demands a JIRA_KEY, use a placeholder/local story id — don't call Atlassian.

### Ping-pong protocol: oq-2 drives/verifies, oq-1 fixes — file existence ≠ active session (2026-06-24)
- In a playtest ping-pong session (`/Users/slabgorb/Projects/sq-playtest-pingpong.md`) roles are fixed: oq-2 = DRIVER/verifier (appends tasks, runs repros, screenshots, status `open`→`verified` only); oq-1 = fix team (implements fixes, status `in-progress`/`fixed`). Keeps the fix on one side to prevent duplicate/conflicting edits (the duplicate-stack cost-runaway hazard). When activated in oq-2 during a ping-pong, do NOT implement code fixes — wait for oq-1 `fixed`, re-run the repro, mark `verified`.
- AMENDMENT 2026-05-27: when verify outruns fix, Keith may direct oq-2 to clear the CONTENT lane — oq-2/GM owns content fixes (sidequest-content YAML + narrator-prompt md), oq-1 still owns code. Be surgical: many "content" findings are really server/ui code, asset generation (don't do autonomously), or destructive/design-level. Content fixes aren't live until oq-1's tree pulls + server restarts (`SIDEQUEST_GENRE_PACKS=oq-1/sidequest-content`) → mark `fixed` not `verified`; batch safe fixes into one pass.
- AMENDMENT 2026-06-24 (load-bearing): the file's mere existence is NOT an active ping-pong session. Keith: "we are not DOING pingpong, that's MERELY where the INFORMATION lives to REPRODUCE." Reading it to pull a repro for a normal oq-2 sprint story is fine and does NOT bar oq-2 from the code lane. Do NOT infer a lane-split or ask "which clone owns this" just because a repro came from the board; the protocol header is only live during an actual playtest. (Wrongly raised a lane gate on 158-11 server-side fix → told to stop.)

### Process decisions for SideQuest specifically
- **Skip architect + spec-check + spec-reconcile phases.** Personal project — streamlined RED → GREEN → VERIFY → REVIEW → FINISH. Don't spawn architect agents during TDD. Don't require epic/story context docs. Still spawn architect for genuine design questions when raised in a story.
- **Epic 15 is a zero-new-debt mandate.** Every agent working an Epic 15 story re-reads CLAUDE.md before starting implementation. SM rejects any Epic 15 phase exit that ships stubs, silent fallbacks, `unwrap_or_default()` on required fields, or "follow-up story" deferral language.
- **Sidecars are the canonical operational layer, not memory.** Sidecars are injected directly into the agent prompt at activation — they drive behavior. Claude Code's auto-memory system is a later keyword-triggered overlay with high redundancy (one rule often ends up spread across 8-10 memory files as each incident triggers a new append). When adding a new behavioral rule, **write to the relevant sidecar first**. Memory can stay lossy; sidecars must stay curated. Stale memory files are noise, but stale sidecar lines mislead every future activation.
- **Personal project — no Jira for SideQuest.** Never run `pf jira check`, `claim`, `move`, or `reconcile` against SideQuest stories. Jira belongs to Keith's employer; touching it creates tickets in the company system. Stories have `jira_key: null` or `jira_key: "none"` — that's correct, don't look one up. The SM setup flow treats Jira as non-existent for this repo.
- **Keith decides process scope, not SM.** Trivial "oh yeah we left this undone" fixes under 5 minutes wall time just get done — RED → GREEN → direct merge → sprint update, no full TDD ceremony. Everything else is full workflow. Never pitch shortcuts as "I lean minimal ceremony but your call" — that's abdicating the decision after making it. Either just execute a trivial fix, or run the full workflow. Don't narrate the process choice.
- **Session files live at `.session/{story-id}-session.md`** during active work. Archived to `sprint/archive/` by `pf sprint story finish`. Never write session files directly into `sprint/` — that has broken handoff CLI before.
- **Handoff CLI is the canonical exit protocol.** `pf handoff resolve-gate` → gate check → `pf handoff complete-phase` → `pf handoff marker`. Nothing after the marker. If marker output contains `relay: true`, use the Skill tool to invoke the named skill.

### Product direction (settled — don't revisit in sprint planning)
- **WN SRD use is confirmed proper by Kevin Crawford** (direct contact, ~2026-06). No partnership, but he affirmed SideQuest is using the Without Number SRD correctly. Licensing posture for epic 102 / WN-family work is settled — don't re-raise SRD legitimacy as a risk in planning. Corollary directive from Keith: WN mechanics adopt SideQuest's turn semantics (module seam, ADR-036 submit-and-wait substrate) — we implement WN crunch *inside* SideQuest's table model, not a parallel turn system.
- **Narrative consistency is the #1 product goal.** The solo narrative experience is the core value prop. Mechanical state (known_facts, LoreStore, NPC registry, inventory) exists as guardrails for the LLM, not as game mechanics for the player. Consistency bugs (NPC name changes, forgotten items, lost facts, turn count resets) are always high priority.
- **Book conceit is retired.** UI has pivoted to persistent docked sidebar + Current Turn Focus + Scrollable History. Decided 2026-04-05. Don't coordinate stories that rebuild the book metaphor.
- **No skeumorphism.** Genre-flavored chrome is fine (three archetypes: `parchment`, `terminal`, `rugged`). But UI is functional first. Reject handoffs where the acceptance criteria sacrifice usability for metaphor.
- **Spoiler protection for world content.** Keith wants to discover narrative surprises in play. World-builder stories have creative freedom on flavor/lore/story/NPCs/plot hooks — don't route them through PM review. Keith owns mechanics only.

### Music / audio (settled)
- **Music is cinematic, not video game BGM.** Overtures, cues, one-shots with fades. Never looping. Crossfade on mood changes.
- **Music is pre-rendered files** from `genre_packs/{genre}/audio/music/`, NOT daemon-generated. Don't route music stories to the daemon crate.
- **ACE-Step for music gen runs standalone**, not via the daemon. Lives at `/Users/keithavery/Projects/ACE-Step/` with its own venv. Stories that generate music should target that pipeline directly.
- **Road warrior music is high priority.** Genre identity is heavily audio-driven — music stories for road_warrior get bumped.

### Voice / TTS (settled)
- **TTS was intentionally stripped from the daemon in story 27-1** (commit 8583162, 2026-04-07). Daemon is image-only. Don't coordinate "re-enable TTS" stories unless Keith explicitly raises them.
- **`--no-tts` defaults to `true`** on sidequest-server (fix `3fe6c2e`, 2026-04-09). The escape hatch `--no-tts=false` is preserved for the day daemon TTS returns.

### Text rendering / UI chrome (settled)
- **Dinkus and drop caps are CSS-based.** No PNG generation. Don't audit for them in sq-audit runs. Don't groom stories that generate these assets.
- **Three genre-chrome archetypes driven by `theme.yaml`:** `parchment` (low_fantasy, tea_and_murder, spaghetti_western, caverns_and_claudes), `terminal` (neon_dystopia, space_opera, mutant_wasteland, star_chamber), `rugged` (road_warrior, pulp_noir, elemental_harmony). Don't coordinate stories that propose a fourth archetype without Keith raising it.

### Content systems (Keith's 30-year domain)
- **Conlang is a core feature**, not a footnote. Corpus-based Markov name generation, 2+ language blends per faction (Clockwork Orange / Nadsat style). Don't coordinate stories that replace conlang with static name lists.
- **Procedural systems lineage.** NPC registry, trope engine, POI, cartography, conlang all draw on 30 years of Keith's prior work. Never frame them as experimental in sprint summaries.
- **"Yes, And" is a foundational product principle** (SOUL #9). Non-negotiable. Stories that propose rejecting player input for "consistency" are wrong by design.

### Infrastructure (settled)
- **Tailscale for playtest connectivity**, Cloudflare R2 for asset backup, Cloudflare Tunnel + Access for long-term public exposure. Don't coordinate stories that propose alternative infra.
- **Save files live at `~/.sidequest/saves/`** — SQLite `.db` per genre/world/player. Not in the repo.

### Tech stack split (for story routing)
- **Rust for everything non-LLM.** `sidequest-game`, `sidequest-protocol`, `sidequest-server`, `sidequest-genre`, `sidequest-agents`, `sidequest-daemon-client`, CLI tools.
- **Python daemon for ML inference only.** Currently only Flux.1 images. Kokoro (TTS) stripped story 27-1. ACE-Step (music) stripped story 27-2.
- **Claude calls always go through Rust subprocess.** Stories that propose importing the Claude SDK into Python are routed back for redesign.

### Reference locations
- **Original Python SideQuest:** `~/ArchivedProjects/sq-1` — source of truth when coordinating porting stories.
- **Ping-pong file:** `/Users/keithavery/Projects/sq-playtest-pingpong.md` (read every 2-3 min during active playtest).
- **Ping-pong archive:** `/Users/keithavery/Projects/sq-playtest-archive/{timestamp}.md`.
- **Genre packs:** `sidequest-content/genre_packs/` — the subrepo is the single source of truth. NOT `oq-2/genre_packs/`.

### Hardware context (for sizing and parallelization)
- **MacBook Pro M3 Max 128GB.** Can run Flux locally without VRAM constraints. No CUDA — MPS or CPU only. Unified memory means ML workloads don't round-trip across PCIe. Size ML-adjacent stories knowing this is the target hardware.
- **Velocity context: ~20x human dev speed, sustained since Nov 2025.** Don't size sprints based on what a human would take. Parallel agents change the math 5-10x on parallelizable work.

### `pf sprint story finish` merge_pr step no-ops silently when no PR exists — create PRs FIRST (102-4, 2026-06-10)
- The finish script's step 2 (merge_pr) found no open PR for the story branches and silently continued; steps 1/4-7 ran anyway (session archived, YAML updated, session removed). Result: story marked complete with ZERO code merged to develop in either repo — the exact half-finished state the merge-gate doctrine exists to prevent.
- **Decision:** SM creates and merges the PRs (gh pr create → gh pr merge --squash --delete-branch) BEFORE running `pf sprint story finish`, or — as recovered here — verifies post-finish that origin/develop actually contains the story commits and repairs immediately (102-4: server#810, ui#372 created+merged after the fact). Always verify `gh pr list --state all --head <branch>` shows MERGED before calling a story done.
- Also note: develop can move during a long story (102-7 merged mid-review from a parallel workspace) — check PR mergeable state before merging; 102-4 was MERGEABLE CLEAN despite both touching the dispatch area.
