**Setup (before the demo):** Have two terminal panes open — one running the server with two WWN characters loaded in a session, one ready to run the targeted test.

**Scene 1 — Slide 2: Problem (2 minutes)**
Open a saved multiplayer session with two characters in a WWN combat encounter. Have player 1 submit their attack. Show the server log: `wwn.round.committed` appears once. Now have player 2 submit their attack. Show the log: instead of `wwn.round.committed` appearing a second time and the round resolving, the log shows `'Rux' has already committed` — the engine rejected the second commit because it thought it was a duplicate from player 1. The round hangs. No `wwn.round.resolved` span appears. Narration never fires.

**Fallback if live session isn't available:** Show the skipped test file with the `@pytest.mark.skip(reason=_MP_WIRE_BLOCKED)` annotation visible — it tells the story of a quarantined safety net.

**Scene 2 — Slide 3: What We Built (2 minutes)**
Switch to the test terminal. Run:
```bash
cd sidequest-server && uv run pytest tests/integration/test_102_4_wn_round_wire_wiring.py::test_mp_wire_first_commit_seals_second_commit_fires_the_round -v
```
Show the test passing green. Highlight the assertion output:
- After commit 1: zero `wwn.round.resolved` spans — the barrier is correctly OPEN
- After commit 2: exactly one `wwn.round.resolved` span — the barrier closed, round fired once

**Fallback:** Show the test file itself at the assertion block (around line 188-257) — the spec is readable in plain English from the span names.

**Scene 3 — Slide 4: Why This Approach (1 minute)**
Point to the `player_seats` dictionary in the code: `{"player-1": "Rux", "player-2": "Vex Calder"}`. This is the directory the fix consults. Note that the solo-player path is untouched — the fix only activates when a second player seat is present.

**Scene 4 — Slide 5: Before/After (1 minute)**
Show side-by-side: old server log with the stuck `already committed` error vs. new log with two sequential `wwn.round.committed` entries followed by `wwn.round.resolved`.

---