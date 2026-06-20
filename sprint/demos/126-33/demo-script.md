**Pre-demo setup:** Have the GM dashboard open in the browser at `localhost:5173/#/dashboard`. Have a terminal ready in `sidequest-server/`.

**Scene 1 — Set the stage (Slide 2: Problem)**
*(~0:30)*
Open the session archive or describe the Oz scenario verbally: "During a session set in Oz, the narrator described Dorothy receiving her silver shoes at turn 7. But the shoes had already been granted earlier in the session. The result was an inventory list reading `['silver shoes', 'silver shoes']` — two identical entries." Show a static slide or a printed JSON snippet:
```json
"inventory": [
  {"name": "silver shoes", "id": "narrator:silver_shoes", "quantity": 1},
  {"name": "silver shoes", "id": "narrator:silver_shoes", "quantity": 1}
]
```
*Fallback if no printed snippet: use the Before/After slide.*

**Scene 2 — Reproduce the bug (Slide 5: Before/After — "Before" half)**
*(~1:00)*
Run the test suite against the pre-fix branch (or show a saved RED run output):
```bash
cd sidequest-server
uv run pytest tests/server/test_126_33_inventory_dedup.py -v 2>&1 | head -30
```
Point to the 6 failing lines — specifically `test_regrant_same_item_does_not_create_duplicate_stack` (the Oz turn-7 repro) and `test_regrant_emits_inventory_dedup_watcher_event`. The output shows `AssertionError: Expected 1 item, got 2`.
*Fallback: show saved terminal screenshot from RED phase.*

**Scene 3 — Show the fix working (Slide 5: Before/After — "After" half)**
*(~1:30)*
Switch to the merged branch and re-run:
```bash
uv run pytest tests/server/test_126_33_inventory_dedup.py -v
```
All 8 tests green. Call out the two key tests:
- `test_regrant_same_item_does_not_create_duplicate_stack` → `PASSED` (the Oz scenario is fixed)
- `test_regrant_emits_inventory_dedup_watcher_event` → `PASSED` (the GM panel gets its log)

**Scene 4 — GM panel lie-detector (Slide 3: What We Built)**
*(~2:00)*
Point to the OTEL dashboard. Explain: "When a duplicate is caught, the system emits an `item_gain.deduped` event tagged with the item name and the player it was for. An operator reviewing a session can confirm whether the dedup fired — the fix is never invisible." If the dashboard is live, show the span. *Fallback: show a screenshot of the dashboard with the `item_gain.deduped` event visible.*

**Scene 5 — Broader test suite (Slide 3: What We Built)**
*(~2:30)*
```bash
uv run pytest tests/server/test_126_33_inventory_dedup.py tests/server/test_item_gain_catalog_resolution.py tests/server/test_inventory_wiring.py -v --tb=no -q
```
Show `54 passed` — the 8 story tests plus 46 neighboring inventory-path tests. No regressions.

---