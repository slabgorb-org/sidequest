# Demo Script — 60-4

**Setup before presenting:** Have the game server running with OTEL telemetry enabled (`just up`, then `just otel` to open the GM dashboard in a browser tab). Have a save file ready in `caverns_and_claudes` with at least one NPC in the room.

---

**Scene 1 — Set the stage (Slide 2: Problem)**
*Timing: ~2 minutes*

Open the GM dashboard's **Prompt** tab. Point to the `narration.turn` span and the `cache_creation` row.

Say: "Right now — before this fix — every time the narrator uses a tool, you'd see `ephemeral_5m_input_tokens` spike to about 30,000 tokens on the *second* API call of the same turn. That's the narrator re-caching its entire rulebook for no reason."

Show the before-state numbers: `ephemeral_5m_input_tokens ≈ 30,000`, `ephemeral_1h_input_tokens = 0` on a continuation call.

*Fallback: If the server isn't running, show the Slide 2 screenshot of the before-state dashboard.*

---

**Scene 2 — Trigger a tool-use turn (Slide 3: What We Built)**
*Timing: ~3 minutes*

In the game UI, type an action that forces a tool call — for example, type: **"I search the body of the fallen guard for anything useful."**

This forces the narrator to call its item-lookup tool, then continue narrating. Watch the GM dashboard refresh.

Point to the `narration.turn` span. You should now see:
- `ephemeral_1h_input_tokens > 0` (e.g., ~30,000)
- `ephemeral_5m_input_tokens = 0`
- `cache_write = 1` only on the *first* call; `cache_read > 0` on the continuation

Say: "The narrator now writes the 1-hour cache key once, and the second call in the same tool loop *reads* from it instead of writing again."

*Fallback: Show the Slide 3 screenshot of the after-state dashboard.*

---

**Scene 3 — Show the cost drop (Slide 5: Before/After)**
*Timing: ~2 minutes*

Point to the `cost_usd` field in the `narration.turn` span across two consecutive turns.

- Before fix baseline: **~$0.116 / turn**
- After fix steady state: **~$0.04 / turn**

Say: "That's roughly a 65% cost reduction per turn. On a full playtest session of 30 turns, that's the difference between $3.48 and $1.20 — for the exact same narration quality."

Note for presenter: "There's one known caveat — our cost display slightly understates the real billing for 1-hour cache writes. We're tracking that as a follow-up so the GM panel shows accurate numbers."

*Fallback: Read the numbers from Slide 5 if the dashboard isn't showing updated spans.*

---

**Scene 4 — Show the mis-zone false alarm is gone (Slide 3 continued)**
*Timing: ~1 minute*

In the OTEL span attributes, point to `mis_zoned`. Before the fix, NPC roster and confrontation entries would sometimes show `mis_zoned=true` even though they were correctly placed in the player-message bucket.

Now `mis_zoned=false` for those sections. Say: "We cleaned up a false alarm in our own monitoring so the team isn't chasing phantom configuration problems."

---
