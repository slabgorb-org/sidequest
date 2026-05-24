# 60-7

## Problem

**Problem:** Every time the AI narrator takes a turn in the game, it was writing a full 5-minute cache entry to Anthropic's API — even on turns where the conversation context was supposed to already be cached. This meant each turn cost as much as the very first turn, wiping out the savings the cache was designed to deliver.

**Why it matters:** The previous fix (story 60-4) was supposed to drop per-turn costs from roughly $0.165 per turn to around $0.04 per turn by keeping the game's large "setup" context cached and only paying to process the small new player message each turn. Instead, the fix was silently broken on real API calls: every tool-use turn (which is how the narrator actually works) kept triggering the expensive 5-minute cache write as if the 1-hour cache didn't exist. A 10-turn session was costing ~$1.65 instead of ~$0.40. Over a full playtest group session, that's real money disappearing with no gameplay benefit.

---

## What Changed

Think of the narrator like a chef who has a prep list they do once at the start of the shift (the 1-hour cache — your mise en place) and then a small per-order prep list for each dish (the 5-minute cache — the actual plate). The old fix tried to tell the chef "your mise en place is done, just do per-order work now" — but when the chef went to call out for a special ingredient mid-order (a "tool call" to the game engine), the kitchen forgot the mise en place was already done and started re-prepping the whole station.

The fix does three things:

1. **Diagnosis first, fix second.** Before changing anything, the code now captures the exact message it sends to the Anthropic API on every turn — iteration 1 (the first call) and iteration 2+ (the follow-up calls inside a tool-use loop) — and writes them to disk as JSON files. This made it possible to *see* exactly which cache setting was missing and why, rather than guessing.

2. **Plugged the leak in tool-use loops.** The 1-hour cache header (`anthropic-beta: extended-cache-ttl`) was being attached to the outer narrator call but was silently dropped on the internal follow-up calls inside the tool loop. The fix pins that header on every single `messages.create` call, including the ones that happen mid-turn when the narrator is waiting for game-engine results.

3. **Added a lie-detector alarm.** A new monitoring signal (`narrator.cache.both_writes_fired`) fires any time a single turn triggers both a 5-minute write *and* a 1-hour write simultaneously. That's the signature of the bug returning. The GM dashboard turns visibly red. If this ever regresses, the team knows within one turn — not after a surprise billing statement.

---

## Why This Approach

Three possible causes were on the table before any code changed:

- **Theory A:** The extended-TTL beta header wasn't being sent on the internal calls inside the tool loop.
- **Theory B:** The cache marker was placed in the wrong position in the message structure, so the API couldn't honor it.
- **Theory C:** Both.

The diagnostic capture — dumping the raw API payload to disk for each iteration — was the only way to know which theory was true without just guessing. Guessing would have meant making changes that might fix the symptom by accident while leaving the real cause in place, ready to resurface after the next refactor.

Once the payload diffs confirmed Theory A (the beta header was missing on continuation calls), the fix was surgical: one change, at the right place, for the right reason. The regression test that guards this fix doesn't just check that the code *looks* right — it mirrors the actual API's caching behavior, so a future refactor that breaks the wiring will fail the test, not silently pass it.

---
