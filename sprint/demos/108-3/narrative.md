# Narrative

## Problem Statement
**Problem:** Three of SideQuest's tabletop genre packs — Caverns & Claudes, Heavy Metal, and Elemental Harmony — shipped with a set of combat instructions that the game engine had stopped using. These instructions described a "beat selection" system (choose Strike, Brace, Push, Angle, Committed Blow, Break Contact) from SideQuest's original homegrown combat engine. But when those packs were migrated to the *Without Number* (WN) ruleset, the WN engine took over combat entirely — supplying its own action menu at runtime. The old instructions were dead weight: they contradicted the live engine, cluttered every combat definition with ~50 lines of content that fired nothing, and left a gap where future bugs could quietly slip in.

**Why it matters:** SideQuest's architecture has a hard rule called "Bind the Ruleset, Don't Balance It" (ADR-143). When you adopt an external ruleset like *Without Number*, the engine owns combat — content authors don't write custom combat actions to compete with it. Dead combat instructions in the content files are a sign the handoff didn't complete cleanly. In a worst case, a future author could mistake them for live rules and try to tune them, spending hours on something the engine ignores entirely.

---

## What Changed
Think of each genre pack as a recipe book. The old recipe for "How to Fight" had five detailed steps: Strike, Brace, Push, Angle, and so on. The new chef (the WN engine) already has their own five-step fight process baked in — so our recipe book was carrying a duplicate, conflicting set of steps nobody reads.

This change deleted those duplicate steps from three recipe books:
- **Caverns & Claudes** — removed the "Dungeon Combat" beat list
- **Heavy Metal** — removed the "Blade-work" beat list
- **Elemental Harmony** — removed the "Martial Exchange" beat list

What stayed in each recipe book: the win condition ("defeat the enemy by depleting their HP"), the enemy's stats (strength, armor, hit points, etc.), and the enemy's damage output. Those are the ingredients the engine actually uses. The engine now supplies the combat verbs — attack, move, use item, cast spell — at runtime, not from content files.

Alongside the combat definitions, each pack's character class files had a list of "available combat moves per class." Those lists were also scrubbed of the now-nonexistent combat beats (58 entries removed), while leaving the chase and negotiation options intact — those two confrontation types still use the original SideQuest engine and are unaffected.

Net result: **222 lines deleted**, nothing added except short "do not re-add a beat list here" comments for future authors.

---

## Why This Approach
The simplest, safest fix was pure deletion. No new logic, no replacement system, no migration shim — just removing content that had become orphaned when the WN engine took ownership.

The harder work had already landed in two earlier stories (108-7 and 108-8): the server's genre pack loader was updated to *allow* zero-beat combat definitions under the WN ruleset (previously it would reject them as incomplete), and the WN round engine was updated to synthesize the correct action set when it finds an empty beat list. This story simply cleaned up the content side once the engine was ready to receive it.

The approach also honored a strict scope boundary: chase and negotiation confrontation definitions use a different system ("DIAL" mechanics) that remains native to SideQuest. Those were left byte-for-byte unchanged. Only `win_condition: hp_depletion` combat definitions were touched, and the loader's validation confirms the two categories cannot be confused.

---
