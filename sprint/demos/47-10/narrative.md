# 47-10

## Problem

Problem: Mages and Clerics in Caverns & Claudes could cast any spell at any time with no preparation requirement, no slot economy, and no visual feedback — the core B/X fantasy of a wizard carefully choosing their daily spells simply didn't exist. Why it matters: the memorization ritual *is* the magic system for this genre. Without it, casters feel like vending machines. Keith — a forty-year DM playing as a player for the first time — will immediately notice if the Mage doesn't feel like a Mage. Getting this wrong means the flagship class plays like a broken fantasy.

---

## What Changed

Think of this like setting up a library card system for magic.

Before this story, spells were available whenever a caster wanted them — no planning, no limits, no drama. Now:

**Spell setup happens automatically.** When a Mage or Cleric starts a session, the game seeds their character with a full starting spell library, an empty "prepared" list, and a set of spell slot counters — all without any manual configuration. It just works at session start.

**Classes now know they're magical.** The Mage and Cleric character classes got proper B/X D&D spell tables baked in — the Mage uses Intelligence to set save difficulty, the Cleric uses Wisdom. The Cleric also gets the Turn Undead ability unlocked.

**The world configures magic too.** The Sünden world now has a magic configuration file that declares which magic plugins are active, adds a "divine favor" meter for Clerics (a bidirectional bar ranging from pious to fallen), and hooks up the narrator to understand the magic system.

**You can't cast what you haven't prepared.** A new gate blocks the "cast spell" action entirely when the character has nothing prepared — not a hard error, but a visual pulse: the prepared list shimmers for about half a second, the failed spell name appears crossed out in the log, and the narrator gently redirects. No popup, no interruption to the fiction.

**Some spells skip the dice entirely.** Magic Missile doesn't ask for a saving throw — it just hits. Cure Light Wounds just heals. The system now knows the difference between spells that need an opposed roll and spells that auto-apply, and handles each correctly.

**A new UI panel shows the full picture.** The character sheet now has a magic section: a collapsible list of known spells, prepared spells organized by level with slot indicators, spent spells shown with strikethrough (visible until rest), a divine favor bar for Clerics, and a Turn Undead button that's only enabled when undead are present in the scene.

**The GM panel sees everything.** Every cast emits a telemetry span carrying actor, spell, slot consumed, whether a save was skipped, and the result — so Keith watching the GM dashboard can verify the magic system is actually doing its job, not improvising.

---

## Why This Approach

**Why pulse-not-popup for rejections?** Modals freeze the fiction. A table-top DM doesn't pause the game and open a dialog box — they say "you can't do that" in-character and move on. The pulse animation keeps time moving, the crossed-out spell name gives clear feedback without drama, and the narrator nudge handles the story beat.

**Why seed state at session start instead of lazily?** Lazy initialization hides bugs. If spell slots are seeded up front when a session loads, you get an immediate, obvious failure if something is misconfigured — instead of a mysterious "magic didn't work" halfway through a dungeon. The integration test verifies a fresh session has bars and collections present with no test-only help.

**Why OTEL on every cast?** Claude is excellent at writing convincing narration that sounds like spells are working even when they're not. The only way to verify the magic system is actually engaged — rather than the narrator improvising — is real telemetry on every decision. Keith watching the GM panel should be able to see `innate_v1.cast` firing and confirm slot consumption is happening mechanically, not fictionally.

**Why distinguish null-stat spells explicitly?** The alternative is checking for zero saves after the fact, which produces wrong behavior for spells that *should* be resisted. Marking certain spells as "no save required" at the catalog level lets the validator catch mistakes (you can't have a null save with a non-none effect) and keeps the resolution code clean.

---
