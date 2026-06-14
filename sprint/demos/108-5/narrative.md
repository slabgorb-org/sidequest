# Narrative

## Problem Statement
Problem: When players entered combat in a Without Number (WWN) game, they faced a generic beat menu that offered no meaningful mechanical guidance — clicking it might resolve as combat, might not, and the outcome depended on narrative interpretation rather than the actual game rules. Why it matters: Players who know the WWN ruleset expected to see Attack, Move-Disengage, Use Item, and Cast Spell as their options — the same four actions the tabletop game defines. Instead they got a vague text box and a gut-feeling menu. The result was a combat experience that felt like improv theater when it should have felt like a real game.

---

## What Changed
Combat in a WWN session now has a proper action bar. When a fight breaks out, four clearly labeled buttons appear: **Attack**, **Move-Disengage**, **Use Item**, and **Cast Spell**. Clicking any of them triggers a real dice roll according to WWN rules — the same math you'd use at a physical table — and the result appears in the dice tray at the bottom of the screen with the numbers laid out plainly.

One thing was deliberately left out: there is no "Brace" or "Full Defense" button. In WWN, defense is passive — your armor class protects you automatically, so there's no action to take. Surfacing a button for it would have been wrong.

There's also a flavor layer: players can still type a free-form action description ("I swing on the chandelier and kick the guard"), and the narrator will weave that into the story. But that flourish is purely color — it does not change the dice result, does not award bonuses, and cannot substitute for pressing an action button. A typed description alone produces no mechanical outcome.

---

## Why This Approach
The WWN ruleset is a finished, published game with defined combat actions. Rather than invent a parallel system or try to infer intent from free text, the engineering decision was to bind the four buttons directly to the rule module that was already running under the hood — the same module handling character stats, to-hit calculations, and damage. The buttons are thin wires to real math, not new logic.

Keeping the narrative rider as flavor-only (and proving it with telemetry) prevents a subtle class of bugs where a well-written action description accidentally improves a player's odds. That guarantee matters more than it sounds: a GM-quality system that lets good typists cheat the dice is neither fair nor trustworthy.

---
