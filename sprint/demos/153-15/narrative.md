# Narrative

## Problem Statement
**Problem:** During character creation, players received a clunky confirmation message — "The Pilot from Spacer space" — where "Spacer space" is redundant and reads like a grammatical hiccup. **Why it matters:** The character confirmation screen is the emotional payoff moment at the end of a multi-step character-building flow. When a player finishes crafting who they are and the game confirms it back with garbled phrasing, it breaks immersion at exactly the wrong moment — like a waiter reading your order back incorrectly right before they disappear into the kitchen.

---

## What Changed
Think of a character sheet being read aloud. Before this fix, the game was saying *"You are The Pilot from Spacer space"* — technically informative but clunky. After the fix, it says *"You are The Spacer Pilot"* — the origin becomes an adjective that naturally describes the class. Clean, confident, genre-true. Three world templates (Aureate Span, Coyote Star, Perseus Cloud) got updated to use this new phrasing, and a regression test was added to make sure no future change accidentally brings the old wording back.

---

## Why This Approach
The text didn't live where the team initially expected — it was in the game's content layer (YAML configuration files), not the server code. Once the root location was confirmed, the fix was a one-line reorder in each template rather than a code change. This is actually the ideal outcome: prose lives in content files, which means writers can adjust it without touching the engine. The test added on the server side acts as a guard: it loads the real templates and verifies the rendered result, so if anyone edits a template incorrectly in the future, the automated test suite catches it immediately.

---
