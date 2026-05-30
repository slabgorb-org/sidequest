---
name: sq-playtest
description: Interactive playtest — full-stack (UI + Playwright + UX Designer) or headless (API-only + Python driver). Coordinates cross-workspace bug reporting via ping-pong file with FIXER.
---

# SideQuest Playtest Skill

<run>
You are now the **Playtest SM**. You coordinate an interactive playtest of the SideQuest game engine.

**Two modes:**

- **Full-stack** (default): UI + daemon + Playwright browser + UX Designer for visual testing
- **Headless** (`/sq-playtest headless`): API-only + Python driver for game loop, narration, and backend testing

If the user said "headless" (or "headless playtest", "API playtest", "no UI"), skip to **Headless Mode** below.
Otherwise, proceed with the full-stack flow.

**Architecture (full-stack):**

- this workspace [DRIVER]: drives the playtest — SM + UX Designer + Playwright browser
- other workspace [FIXER]: fixes bugs from the shared ping-pong file — SM + Dev + Architect

Read `sq-playtest/pingpong.md` in this skill directory for the full coordination protocol.

---

## Phase 1: Stack Launch (Full-Stack)

Poll for services- if services are not up, ask the user to start them. (There is no separate save-forensics service to start — save forensics is a set of REST endpoints on the server itself; see Phase 3c.)

Launch Playwright browser

We have a set of host aliases to avoid cross-session contamination.
  127.0.0.1     player1.local
  127.0.0.1     player2.local
  127.0.0.1     player3.local
  127.0.0.1     player4.local

Open a headed browser to the UI:
```
mcp__playwright__browser_navigate(url="player1.local:5173")
```

Take an initial screenshot to confirm the UI loaded. **Always pass `filename` with an absolute path to the shared screenshots dir — never let Playwright drop into cwd:**

Open a tab to the OTEL dashboard: http://localhost:8765/dashboard
(Save forensics is not a webpage — it's REST endpoints under `localhost:8765/api/debug/save/*`. See Phase 3c.)

```
mcp__playwright__browser_take_screenshot(filename="~Projects/sq-playtest-screenshots/000-initial-load.png")
```
---

## Phase 2: Setup

### Initialize ping-pong file 

```bash
mkdir .sq-playtest-screenshots
```

Create the ping-pong file (or reset it if starting a new session):

Write to `~/Projects/sq-playtest-pingpong.md`:

```markdown
# SideQuest Playtest — {today's date and time}

## Protocol

- **DRIVER** (playtest driver): adds new tasks, verifies fixes, takes screenshots
- **FIXER** (fix team): picks up tasks, implements fixes, updates status
- Status flow: `open` → `in-progress` → `fixed` → `verified`
- DRIVER ONLY appends new tasks and updates status to `verified`
- FIXER ONLY updates status to `in-progress` or `fixed`
- Neither side deletes entries — status transitions only

## How to Monitor (for FIXER)

Read this file periodically. When you see new `open` tasks:

1. Update the task status to `in-progress`
2. Fix the issue in the codebase
3. Update the task status to `fixed`
4. If the fix requires a server restart, add a note: `- **Needs restart:** yes`

## Status

Active playtest in progress.

## Tasks (newest first)
```

Tell the user: "Ping-pong file ready at `~/Projects/sq-playtest-pingpong.md`. Tell FIXER to monitor it."

---

## Phase 3: Interactive Playtest Loop

This is the main gameplay loop. Repeat until the user says to stop:

### 3a. Perform a game action

Use Playwright to interact with the game:

```
mcp__playwright__browser_click(...)
mcp__playwright__browser_fill_form(...)
mcp__playwright__browser_navigate(...)
mcp__playwright__browser_press_key(...)
```

Describe what you're doing before each action ("Clicking 'New Game' button").


### 3b. Check logs

Services tee to `~/.sidequest/logs/sidequest-{server,client,daemon}.log` (NOT `/tmp` — that path is retired; some old code comments still reference it). Tail with `tail -F ~/.sidequest/logs/sidequest-server.log` or `just logs server`.

### 3c. Check OTEL and save forensics — the lie detectors

Use these every few turns, not just when something looks broken. The narrator writes convincing prose with **zero mechanical backing**; these surfaces are the only way to catch improvisation masquerading as engine state.

**OTEL dashboard (`http://localhost:8765/dashboard`) — live state + per-turn spans:**

- **② State tab** is the live save snapshot. Read it to check NPCs, location/region, HP, stats, and active tropes against what the narration *claimed*. Expand **Raw JSON ▸** for the full snapshot when a widget looks wrong or empty.
  - **Gotcha:** the "NPC Registry" widget reads the runtime `npc_pool` (who is present in the *current scene*), NOT the authored `npcs` roster. It frequently shows "No NPCs in registry yet" even when the roster is full. Do not trust the widget — check `npcs` in Raw JSON or via the forensics endpoint below.
  - **Gotcha:** the snapshot character block may show `HP: undefined/undefined` even when the in-game panel shows real HP (ADR-114 ablative-HP field mismatch in the dashboard reader). Cross-check the game UI.
- **③ Subsystems**, **⑥ Prompt**, **⑦ Lore** tabs show what fired each turn.

**Save forensics — post-hoc REST endpoints on the server (there is NO separate `:8799` service; that reference is stale):**

```bash
curl -s localhost:8765/api/debug/saves                       # list saves
curl -s localhost:8765/api/debug/save/{slug}/timeline        # per-round event-kind counts + authors
curl -s localhost:8765/api/debug/save/{slug}/snapshot        # full latest snapshot
curl -s localhost:8765/api/debug/save/{slug}/turn/{round}    # one round's events
curl -s localhost:8765/api/debug/state                       # live in-memory state
```

Pipe through `python3 -m json.tool` (or a small extractor) to inspect `npcs`, `npc_pool`, room/region state, footnotes, etc.

**NPC roster signal:** to confirm authored crew / origin-screen NPCs seeded, check the `npcs` array in the snapshot — not the dashboard widget. In `coyote_star` solo, **Kanga Moana-Teru** (original Kestrel crew) is the clear signal: if she is in `npcs`, the roster seeded correctly. If the dashboard says "no NPCs" but Kanga is in `npcs`, that's the widget reading `npc_pool`, not a roster bug.

### 3d. Triage findings

For each finding:

1. Determine the tag: `[BUG]`, `[BUG-LOW]`, `[UX]`, or `[GAP]`
2. Determine priority: `blocking`, `high`, `medium`, `low`
3. Append to the ping-pong file:

```markdown
### [{TAG}] {title}

- **Priority:** {priority}
- **Found by:** {SM | UX Designer}
- **Repro:** {step-by-step reproduction}
- **Status:** open
- **Screenshot:** ~Projects/sq-playtest-screenshots/{NNN}.png
- **Notes:** {additional context}
```

For **blocking bugs**, also prepend an attention signal at the top of the Tasks section:

```markdown
> **ATTENTION FIXER**: Blocking bug added — {brief description}. Please prioritize.
```

### 3e. Monitor ping-pong file (SM owns the sync cycle)

**You are responsible for watching the ping-pong file and driving the fix→verify loop.**

Before each new gameplay action, re-read the ping-pong file:

```bash
cat ~Projects/sq-playtest-pingpong.md
```

**When you see tasks updated to `fixed`:**

1. Check if the task has `Needs restart: yes`
2. If yes → run the full **Sync & Restart** cycle (see Phase 4)
3. If no → re-test the issue directly via Playwright
4. If verified → update status to `verified` in the ping-pong file
5. If not fixed → add a note explaining what's still broken, set status back to `open`

**When you see tasks still `in-progress`:**

- Note them but don't block — continue playtesting other areas

**When the file hasn't changed:**

- Continue normal gameplay loop


---


</run>

<output>
Interactive playtest session:

- Headed Playwright browser for gameplay interaction
- Multiplayer mode with dual Playwright tabs for concurrent player testing

- Cross-workspace bug coordination via ping-pong file at ../Projects/sq-playtest-pingpong.md
- Service restart and log reading capability
  </output>


