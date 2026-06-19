**Pre-demo setup (before presenter enters):**
```bash
# Terminal 1 — start the server
just server

# Terminal 2 — start a headless test that generates noisy background signals
just server-test  # (or any concurrent test suite)

# Terminal 3 — start a live playtest session
just client       # Vite on :5173
```
Open `http://localhost:5173/#/dashboard` in browser.

---

**Scene 1 — Problem re-creation (Slide 2: Problem)** *(~60 seconds)*

With two sessions active (the live playtest + the headless test), open the Live tab in the GM panel. Point out:
- The header shows the *test session ID* (`test-444686c1`) — not the playtest session the operator is driving.
- The Timeline reads "TURNS 0 / Waiting for first turn…" even though the playtest already completed several turns.
- Say: "The lie-detector is watching the wrong patient. The game could be improvising every single mechanic right now and we'd never know."

*Fallback if repro is unreliable: show screenshot `docs/bugs/126-23-before.png` (Live header wrong session, timeline stalled) on Slide 2.*

---

**Scene 2 — After the fix (Slide 3: What We Built)** *(~90 seconds)*

Refresh to the fixed build. Two sessions are still running.

- Show the **Session Picker dropdown** now has a "Live sessions" group with two entries (the playtest slug and the test slug).
- Click the playtest session (`annees-folles-...`). The header immediately locks to that session. The Timeline populates with the correct turns.
- In Terminal 2, trigger a burst of test signals: `uv run pytest tests/telemetry/ -x -q`
- Watch the dashboard — the Timeline does **not** jump to the test session. The header stays on the pinned session. Point to this and say: "A concurrent session emitting 400 spans per minute cannot steal this view."
- Click "auto-follow newest" in the picker to demonstrate the restore-to-default path.

*Fallback if session picker is empty: show that even in auto-follow mode the session *labels* are now distinct — the header reflects a real slug, not undefined.*

---

**Scene 3 — Late connect (Slide 3 continued)** *(~45 seconds)*

Disconnect and reconnect the dashboard (close and reopen `#/dashboard`) after the playtest session has already taken 5 turns.

- Select the playtest session from the picker.
- Show that the Timeline immediately shows all 5 prior turns — not "Waiting for first turn…".
- Say: "History is now private per session. A fast test can't push a slow playtest out of memory."

*Fallback: show server test output `uv run pytest tests/telemetry/test_watcher_session_replay_retention.py -v` and point to the three retention tests passing.*

---

**Scene 4 — Test evidence (Slide 4: Why This Approach)** *(~30 seconds)*

```bash
cd sidequest-ui && npx vitest run src/components/Dashboard/__tests__/
cd ../sidequest-server && uv run pytest tests/telemetry/ -v
```
Show 56/56 tests passing — 12 new, 44 regression. Say: "Before writing a line of fix code, we wrote tests that failed on the exact three broken behaviors. All 12 now pass."

---