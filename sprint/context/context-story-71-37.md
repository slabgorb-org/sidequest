---
story_id: "71-37"
type: "bug"
points: 5
workflow: "tdd"
repos: sidequest-server
---

# 71-37: Classify person-vs-creature at the NPC invention seam — route beasts to the Monster Manual (ADR-059), not the culture-NPC namer

## Summary

The NPC invention seam currently routes all NPC-like entities through the culture-NPC Markov namer (ADR-091), which produces person names. This causes creatures and beasts to receive inappropriate person names instead of being routed through the Monster Manual (ADR-059) pregeneration path.

The fix requires classifying entities at the seam: route `person` class to the culture namer, route `creature`/`beast` class to Monster Manual.

## Related ADRs

- **ADR-059** — Monster Manual: Server-Side Pre-Generation via Game-State Injection
- **ADR-091** — Culture-Corpus + Markov Naming
- **ADR-014** — Diamonds and Coal (creature/item schema)

## Context

The creature/beast → person-name mapping is a seam issue, not a downstream narrative bug. The namer doesn't know the entity class at invocation time and must be told at the call site.

