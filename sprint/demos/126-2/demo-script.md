**Total runtime: ~6 minutes**

### Scene 1 — Title (Slide 1)
*0:00–0:30*
Open on the title slide. One sentence: "We verified that poker works — and proved exactly why it was broken."

### Scene 2 — The Problem (Slide 2)
*0:30–1:30*
Walk through the problem. Point to the playtest date (June 16–17). The symptom: players triggered a poker scene in the Spaghetti Western pack; nothing happened. No table, no ante, no game. The narrator kept going as if poker was happening, but the mechanical engine was sitting idle. `encounter = None`.

Show the causal chain on screen: router stuck → returns `dispatch_package = None` → seating call never reached → card game silently absent.

*Fallback if live demo isn't available: stay on Slide 2 and narrate the chain verbally.*

### Scene 3 — What We Built (Slide 3)
*1:30–3:00*
Transition to Slide 3. Run the test suite live:

```bash
cd sidequest-server
uv run pytest tests/agents/subsystems/test_table_resolution_seating_dispatch.py -v
```

Expected output:
```
PASSED test_table_resolution_dispatch_seats_the_table
PASSED test_table_resolution_seats_through_real_dispatch_bank
PASSED test_table_resolution_dispatch_emits_table_dealt_span
PASSED test_table_resolution_declines_when_no_other_seat

4 passed in 0.Xs
```

Point to what each test proves:
- **Test 1:** A poker signal from the router produces a fully-seated table — PC seat, opponent seat, win condition, pot slot.
- **Test 2:** The same contract holds when traffic flows through the full production dispatch path (end-to-end).
- **Test 3:** An OTEL span called `table.dealt` fires with `seat_count ≥ 2` and `game_kind = poker`. This is the GM-panel signal. If this doesn't fire, you know the table narration is fabricated.
- **Test 4:** If no opponent is available, the game declines and fires an `encounter.no_opponent_available` span — no silent failure.

*Fallback if test runner unavailable: show Slide 3 with the four test names and what each locks.*

### Scene 4 — Why This Approach (Slide 4)
*3:00–4:00*
Slide 4. The key insight: we didn't touch the card-game engine because the card-game engine wasn't broken. The test is the deliverable here — a permanent sensor on the exact wire the router degradation had cut.

Mention the fidelity decision: tests run under `ruleset = "fate"` with `FateConfig()`, matching the real Spaghetti Western poker configuration. Not a legacy test harness.

### Scene 5 — Before/After (Slide 5, optional)
*4:00–4:45*
If using a Before/After slide: left side shows `encounter = None`, router returning `dispatch_package = None`; right side shows the seating snapshot — `encounter.win_condition = table_showdown`, seats populated, OTEL span present.

### Scene 6 — Roadmap (Slide 6)
*4:45–5:30*
One follow-up filed: resolution coverage (pot awards, showdown payout, fold detection) needs to be re-tested under the real Fate and CWN ruleset bindings. Non-blocking, but on the list.

What this enables: any future work touching the router, the dispatch bank, or the table engine now has a safety net at the exact handoff seam. That handoff was invisible before this story.

### Scene 7 — Questions (Slide 7)
*5:30–6:00*

---