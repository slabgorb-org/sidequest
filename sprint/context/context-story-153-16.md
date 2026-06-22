# Story 153-16 Context

## Title
[CHARGEN-NAME-PROSE-REJECT] accept the full natural-language name answer or surface why it was rejected

## Metadata
- **Story ID:** 153-16
- **Type:** bug
- **Points:** 1
- **Priority:** p3
- **Workflow:** trivial
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

During road_warrior chargen, step v asks: *"What do they call you? And what do they call the rig?"*

A full prose answer — *"They call me Riggs. The rig's name is The Anvil — a black, armored wall on wheels."* — was **silently rejected** and re-prompted with "Give your rider a road name and your rig a name. Both matter." No explanation was given for the rejection. A terser form — *"Riggs and his rig The Anvil"* — parsed fine (→ name `Riggs`, rig `The Anvil`).

This is the Zork problem: the open-input field invites natural language but quietly narrows it. The player gets no signal about what went wrong.

## Repro / Evidence

- **Session:** road_warrior chargen, step v (name + rig name prompt)
- **Failing input:** `"They call me Riggs. The rig's name is The Anvil — a black, armored wall on wheels."`
  - Result: silent re-prompt, no error surfaced
- **Passing input:** `"Riggs and his rig The Anvil"`
  - Result: parsed correctly
- **Source:** playtest capture lines 270–276

## Fix Direction

Two acceptable resolutions (pick one):

1. **Accept the prose form** — extract the name and rig name from natural-language input (the player said "They call me Riggs" and "The rig's name is The Anvil"; both are parseable). This is the preferred SOUL-aligned path.
2. **Surface the rejection** — if the parser cannot extract a clear name/rig pair from a given answer, respond with a specific failure reason instead of a silent re-prompt. "I need a name for your rider and a name for the rig — I couldn't pick them out from your answer" is better than a blank re-ask.

Do not leave the silent reject in place. SOUL: "Never silently narrow open input."

## Acceptance Criteria

1. A prose name answer of the form *"They call me X. The rig's name is Y — [description]."* either (a) is accepted and extracts `X` as the rider name and `Y` as the rig name, OR (b) produces a specific, visible rejection message explaining what is missing or ambiguous — no silent re-prompt.
2. The existing terse form (`"Riggs and his rig The Anvil"`) continues to parse correctly.
3. A test covers the prose-form input path and asserts the correct outcome (accepted with correct extraction, OR explicit rejection message — no silent empty re-prompt).

## Source

- Playtest capture `sq-playtest-pingpong-archive-2026-06-21-epic153-capture.md`, lines 270–276 (`[UX-LOW / chargen name step silently rejects a natural-language answer]`)
- SOUL "The Zork Problem" (ADR-002): never silently narrow open input

## Scope Notes

Trivial workflow. Touches the chargen name-parsing step for road_warrior (and potentially any other genre with a compound name prompt). No narrator involvement — this is input parsing only.
