# Narrative

## Problem Statement
**Problem:** Players who choose a Fate Core game have no dedicated character creation screen — they drop into a generic form that doesn't speak Fate's language, forcing them to mentally translate phrases like "pick your skills" into concepts like "build your pyramid." Why it matters: Fate is the most narrative, player-driven ruleset in SideQuest's lineup. Its character creation *is* the first act of play. A mismatch between the UI and the rules breaks the fiction before the story begins, and a career GM like Keith — who finally gets to be a player — will notice immediately.

---

## What Changed
Imagine you're signing up for a Fate game night. Before this work, the app handed you a blank form and said "fill in your character." After this work, the app guides you through Fate's own vocabulary, step by step:

1. **Who are you?** — You type your High Concept (a pithy phrase like *"Disgraced Imperial Pilot"*) and your Trouble (*"The Empire Wants Me Dead"*). A live text field keeps you honest — it can't be blank, it can't be a novel.

2. **What else defines you?** — Two more free Aspect slots open up. Same rules, same live feedback.

3. **What are you good at?** — A visual pyramid appears. You drag skills up and down. The pyramid enforces Fate's legality rule (you can't have two Superb skills if you only have one Great) in real time — illegal shapes glow red; legal ones go green. No math required.

4. **What's your signature trick?** — A stunt picker lists available stunts. As you add them, a Refresh counter ticks down from 3. At 1, the picker locks out. You always know how many Fate Points you start with.

5. **The Adjective Ladder** — Every skill rank shows its Fate name (*Average, Fair, Good…*) not just a number, so the game's vocabulary is always on screen.

The whole screen is invisible when you're playing any other ruleset (d20, Without Number, etc.). It only appears when the game engine says "this is a Fate session."

---

## Why This Approach
Three principles drove the design:

**The server decides, the screen reflects.** The UI never invents its own rules. It mirrors what the server says is legal — if the server changes what a valid pyramid looks like, the screen follows automatically. This prevents the "it passed on my screen but the game rejected it" problem.

**Fate's vocabulary, not ours.** Every label, every placeholder, every tooltip uses the words Fate Core uses. Players who know the system feel at home. Players who don't are learning the actual game, not a translation of it.

**Surgically isolated.** The Fate screens live behind a ruleset gate. There's a deliberate test that confirms the Fate UI *never* appears in a d20 or Without Number session. Two separate systems can't bleed into each other's setup flows.

---
