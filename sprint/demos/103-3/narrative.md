# Narrative

## Problem Statement
Problem: Players creating characters always used the same safe, optimized method — point-buy or drop-lowest rolling — which produced predictable, min-maxed characters where everyone's strong stats ended up where they wanted them. Why it matters: This flattens character variety and kills the "happy accident" moments that make tabletop memorable. When you *choose* your stat distribution, you never play the clumsy wizard or the brilliant-but-frail warrior. The randomness is the story.

---

## What Changed
We added a toggle called **Roll the Bones** to the character creation screen. When turned on, the game rolls three six-sided dice for each of your six core attributes — in a fixed order, no cherry-picking. You don't get to assign results where you want them; whatever comes up for Strength is your Strength, full stop.

To keep it from being punishing, players get a **reroll budget of two stats**. You can look at your results and say "not that one" twice — but only twice. The rest you live with.

The mode is available as an opt-in flag at the start of character creation. The UI shows a distinct visual treatment — a dice roll icon, a different background pulse, and a live tally of how many rerolls you have left — so you always know you're in the "old-school" mode and exactly where you stand.

---

## Why This Approach
Three reasons this design is right for SideQuest's audience:

**1. It honors the tradition without punishing newcomers.** 3d6-in-order is the original D&D method — it's what Gary Gygax intended, and experienced players like Keith know exactly what they're signing up for. The 2-stat reroll budget is a modern concession: it prevents the truly unplayable character (three stats under 6) while keeping the stakes real.

**2. It's a flag, not the default.** Forcing random attributes on players who didn't ask for them would be hostile design. This is opt-in at chargen, which respects Alex (who might freeze under pressure) while giving Jade and Sebastien the mechanical crunch they've been missing.

**3. The UI has to do work here.** A hidden mode flag isn't enough — players need to *feel* the difference. The visual treatment (dice icon, remaining-rerolls counter) makes the mode legible at a glance and prevents the worst outcome: a player not realizing they were in hardmode until after character creation.

---
