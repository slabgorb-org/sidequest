**Setup:** Server running locally with the GM dashboard (`just otel`) open in a browser. Narrator session active with `space_opera / perseus_cloud`.

**Slide 2: Problem** *(2 minutes)*
Open the GM dashboard *before* the fix and show the NPC event stream. Point out: no `npc.spawn_disposition` events appear when a new character enters the scene. The narrator invents a contact named "Irenka Voss." Irenka materializes. Nothing in the panel confirms her starting disposition. "We couldn't see this. We had to guess."

**Slide 3: What We Built** *(3 minutes)*
With the fix live, trigger the same scenario. Type in the terminal:
```bash
just server    # confirm server is on :8765
just otel      # open GM panel at localhost:8765/dashboard
```
Ask the narrator to introduce a new character. Watch the GM dashboard — within the next narration response, an `npc.spawn_disposition` event fires. Show the panel entry:
- `npc_name: "Irenka Voss"`
- `disposition: 0`
- `provenance: "default_neutral"`
- `is_creature: false`

"Zero. Neutral. Provenance: default_neutral. We can see it. We can prove it."

Now trigger a monster encounter (or use the debug command to inject a creature patch). Show the same panel entry for the creature:
- `disposition: -20`
- `provenance: "default_creature_hostile"`
- `is_creature: true`

"Creatures still arrive hostile. That's correct and intentional."

*Fallback if live demo fails:* Switch to **Before/After slide** showing the two panel states side by side.

**Slide 4: Why This Approach** *(90 seconds)*
"We expected to flip a number. We traced the code and found the number was already right. The gap was that we couldn't *see* it. We added the readout instead of changing a value we didn't fully understand."

**Before/After slide** *(1 minute)*
Walk through the comparison table below. Emphasize: behavior unchanged, visibility added.

---