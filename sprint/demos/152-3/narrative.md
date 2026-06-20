# Narrative

## Problem Statement
**Problem:** After recent combat engine updates to the *Worlds Without Number* (WWN) ruleset, two automated character-creation tests began failing with cryptic `[None x6]` errors, blocking future work and hiding whether the character-creation flow actually worked.

**Why it matters:** Character creation is the front door of every SideQuest session. If the automated safety net for that flow is broken, the team loses confidence that chargen still works across WWN-based worlds (Caverns & Claudes, Elemental Harmony, Heavy Metal/Barsoom). Broken tests also leave the door open for real regressions to slip through undetected.

---

## What Changed
Think of character creation as a wizard with multiple screens. The test code had a helper that walked through those screens automatically — but it was written assuming there was only *one* decision screen, the one where you pick your class (Warrior, Expert, or Mage).

A previous update added a *second* screen: picking your character's background (trade, craft, profession, etc.). The helper didn't know about this new screen. When it hit that second screen looking for a "class hint" that wasn't there, it got confused and returned six blank answers — `[None, None, None, None, None, None]` — causing both tests to crash before they could verify anything.

The fix taught the test helper to recognize *which* screen it's on: pick a class on the class-selection screen; pick a background on the background screen. The rest of the assertions were also updated to match the new combat rules from stories 152-1 and 152-2: WWN classes no longer have private per-class combat moves — every character uses the same universal action menu (Attack, Cast Spell, Total Defense, Fighting Withdrawal).

Critically, **zero production code was changed**. The character-creation content was always correct; only the test scaffolding needed updating.

---

## Why This Approach
The root cause was a *brittle assumption* baked into the test helper: "every choice screen is a class-selection screen." Rather than patching around it, the fix removed the assumption entirely — the walk now inspects each screen and picks an appropriate choice based on what that screen actually offers.

This approach is preferable to deleting the assertions (which would just hide the problem) or adding production-code workarounds (which would change behavior to match a broken test, not fix the test to match correct behavior). The test is now resilient to future chargen screens being added without requiring another fix like this one.

---

## Before/After
| | Before (broken) | After (fixed) |
|---|---|---|
| **Test behavior** | `_build_character` hits `the_trade` screen, finds no class hint in 6 background choices, returns `[None, None, None, None, None, None]`, test crashes | Walk detects `the_trade` screen, picks a background choice; detects `the_calling` screen, picks the target class — reaches confirmation |
| **Error message** | `AssertionError: target_class Warrior not in [None, None, None, None, None, None]` | No error — both `test_cc_chargen_e2e` and `test_class_signature_wiring` green |
| **Combat assertions** | Checked for `committed_blow` in `class_moves`; expected Mage to have per-class beats from `encounter_beat_choices` | Reflects the synthesized action set: no per-class combat beats; all WN classes share Attack / Cast / Total Defense / Fighting Withdrawal |
| **Signature abilities** | Could not be asserted (test crashed before reaching them) | Killing Blow / Veteran's Luck (Warrior), Read the Ledger (Expert), Read the Worked Stone (Expert) — all asserted and green |
| **Production impact** | None | None — test-only changes |
