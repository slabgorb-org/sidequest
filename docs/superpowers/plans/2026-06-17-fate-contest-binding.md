# Fate Contest Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a Fate-bound pack's structured confrontations resolve through Fate's own mechanics (a new Contest mode) instead of the d20 dial engine, by completing the binding — rename the dial engine honestly, add the SRD Contest, re-author the Fate-pack defs, and install a guardrail so the bleed cannot return.

**Architecture:** Four coordinated workstreams. (1) Rename `NativeRulesetModule`→`DialRulesetModule`, slug `native`→`dial`, and fail-loud the three silent `"native"` defaults — pure rename, zero resolution change. (2) Add `fate_contest.py`, a sibling to `fate_conflict.py`, implementing the SRD Contest (opposed 4dF, first-to-3 victories, tie→boost), reached through the existing `FATE_ACTION` dispatch and selected by a `ContestState` stamp on the seated encounter. (3) Re-author the 5 `opposed_check` confrontation defs in the two Fate packs into Contests. (4) A `RulesConfig` model-validator that fails pack load loudly if a Fate pack authors an `opposed_check` def.

**Tech Stack:** Python 3.12 / FastAPI (sidequest-server, uv-managed, pydantic v2, pytest + pytest-xdist, ruff, OpenTelemetry); YAML genre packs (sidequest-content).

## Global Constraints

Every task's requirements implicitly include this section. Values copied verbatim from the spec (`docs/superpowers/specs/2026-06-17-fate-contest-binding-design.md`) and the repo CLAUDE.md files.

- **THE LOAD-BEARING INVARIANT (spec §0):** WN is held **byte-identical**. The dial engine, the `opposed_check` resolution mode, and ADR-093 calibration stay fully intact for the Without Number family (cwn/awn/swn/wwn). **Every behavioral change in this plan is gated on `ruleset == "fate"`.** Any removal of the `opposed_check`→dial path that is *not* so gated regresses road_warrior (cwn) + mutant_wasteland (awn). road_warrior depends on `dial.compute_dc` *harder* than Fate does — its own module raises on `compute_dc`.
- **The rename is pure** — Tasks 1–2 change no resolution behavior for any ruleset. After Task 1 the dial engine is reachable by exactly one production path (`confrontation.py`'s opposed-check DC) plus the registry.
- **No Silent Fallbacks:** a missing pack/ruleset is a configuration error and must raise, never silently become the dial engine.
- **No Stubbing / No half-wired features:** connect the full pipeline. New code must have a non-test consumer.
- **OTEL Observability Principle:** every subsystem decision emits a watcher span (the GM panel is the lie detector). The Contest engine MUST emit `fate.contest.seeded`, `fate.contest.exchange`, `fate.contest.resolved`.
- **No Source-Text Wiring Tests:** never grep production source as a wiring assertion. Drive the flow and assert OTEL spans / typed messages / registry membership. (`sidequest-server/CLAUDE.md`.)
- **Every test suite needs a wiring test** that proves the component is reachable from a production code path.
- **Repos / branches:** server work is in `sidequest-server` (branch off `develop`, github-flow). Content work is in `sidequest-content` (branch off `main`). They are separate git repos; commit in the repo you edited.
- **Commands:** server — `cd sidequest-server && uv run pytest -v` (add `-n0` for serial), `uv run ruff check .`, `uv run ruff format .`, `uv run pyright`. The full suite runs `-n auto` by default.
- **Scope correction (verified against content):** the spec says "~19–20" `opposed_check` Fate defs. The real count is **5** actual `resolution_mode: opposed_check` defs — tea_and_murder ×4 (negotiation, trial, social_duel, scandal) + spaghetti_western ×1. There are no `_from:` confrontation includes and no world-tier `rules.yaml` overrides. `table_resolution` defs (the auctions) are **out of scope** — they route through the ADR-129 table engine, not `dial.compute_dc`.

---

## File Structure

**sidequest-server** (branch off `develop`):

| Path | Responsibility | Change |
|------|----------------|--------|
| `sidequest/game/ruleset/dial.py` | The dial/beat/contest engine (ADR-033) the WN family delegates `compute_dc` to | **Rename** from `native.py`; class `NativeRulesetModule`→`DialRulesetModule`, slug→`"dial"` |
| `sidequest/game/ruleset/registry.py` | slug→module registry | Update import + key (auto-follows slug) |
| `sidequest/game/ruleset/base.py`, `without_number.py` | docstrings referencing the dial engine | Docstring-only honesty edits |
| `sidequest/server/dispatch/confrontation.py` | opposed_check DC offer (the one legit dial path) | `get_ruleset_module("native")`→`("dial")` |
| `sidequest/server/dispatch/pregen.py`, `encounter_lifecycle.py` | three silent `"native"` defaults | Fail-loud |
| `sidequest/cli/encountergen/encountergen.py` | semantic `!= "native"` guard | →`!= "dial"` |
| `sidequest/genre/models/rules.py` | `RulesConfig`, `ConfrontationDef`, `ResolutionMode` | Default slug→`"dial"`; add `ResolutionMode.contest`; add fate-no-`opposed_check` validator |
| `sidequest/game/encounter.py` | encounter state model | Add `ContestState` + `StructuredEncounter.contest` |
| `sidequest/server/dispatch/fate_contest.py` | **NEW** — the SRD Contest engine | `run_fate_contest_exchange`, `FateContestResult`, `FateContestError` |
| `sidequest/server/dispatch/fate_conflict.py` | FATE_ACTION dispatch | Branch to contest engine; reject `attack` in contest |
| `sidequest/telemetry/spans/fate.py` | Fate OTEL spans | Add 3 `fate.contest.*` spans + `SPAN_ROUTES` |
| `tests/genre/test_confrontation_calibration.py` | ADR-093 calibration guard | Scope to non-Fate; add road_warrior; skip negotiation |
| `tests/server/dispatch/test_fate_contest.py` | **NEW** — contest engine + dispatch + no-bleed | New suite |
| `tests/genre/test_fate_no_opposed_check.py` | **NEW** — guardrail validator | New suite |

**sidequest-content** (branch off `main`):

| Path | Change |
|------|--------|
| `genre_packs/tea_and_murder/rules.yaml` | 4 defs: `opposed_check`→`contest` |
| `genre_packs/spaghetti_western/rules.yaml` | 1 def: `opposed_check`→`contest` |

**orchestrator** (`docs/adr/`): ADR-144 amendment, ADR-093 note, ADR-033 rename note.

---

# Phase 1 — Rename `native` → `dial` (pure rename + fail-loud)

### Task 1: Rename the dial engine module, class, slug, and all production references

**Files:**
- Rename: `sidequest/game/ruleset/native.py` → `sidequest/game/ruleset/dial.py`
- Modify: `sidequest/game/ruleset/registry.py:7,13`
- Modify: `sidequest/server/dispatch/confrontation.py:368,371`
- Modify: `sidequest/genre/models/rules.py:1097-1099`
- Modify: `sidequest/server/dispatch/pregen.py:453` (semantic comparison)
- Modify: `sidequest/cli/encountergen/encountergen.py:811` (semantic comparison)
- Modify (docstrings only): `sidequest/game/ruleset/base.py`, `sidequest/game/ruleset/without_number.py:152`
- Test: `tests/game/ruleset/test_registry.py` (extend existing, or create if absent)

**Interfaces:**
- Consumes: `RulesetModule` ABC (`base.py`), `get_ruleset_module(slug)` (`registry.py`).
- Produces: `DialRulesetModule` (slug `"dial"`); `get_ruleset_module("dial")` returns it; `get_ruleset_module("native")` raises `UnknownRulesetError`. The `compute_dc` formula `max(10, min(30, 10 + abs(beat.base) * 2))` is unchanged.

**Out of scope (do NOT rename):** the property `awards_native_turn_xp` (`base.py:111`, `without_number.py`), the OTEL span field `native_scaffolding_suppressed` (`telemetry/spans/wn_round.py`), and the magic-working `mechanism` enum value `"native"` (`magic/models.py:86`, `magic/plugins/*`). These carry the word "native" but are not the ruleset slug; renaming the span field would break GM-panel OTEL routes. Leave them.

- [ ] **Step 1: Write the failing test** (`tests/game/ruleset/test_registry.py`)

```python
import pytest

from sidequest.game.ruleset import get_ruleset_module
from sidequest.game.ruleset.base import UnknownRulesetError
from sidequest.game.ruleset.dial import DialRulesetModule


def test_dial_slug_resolves_and_native_is_gone():
    module = get_ruleset_module("dial")
    assert isinstance(module, DialRulesetModule)
    assert module.slug == "dial"
    with pytest.raises(UnknownRulesetError):
        get_ruleset_module("native")


def test_dial_compute_dc_formula_unchanged():
    # The rename must not move the formula. base=5 -> 10 + 10 = 20.
    from sidequest.genre.models.rules import BeatDef

    module = get_ruleset_module("dial")
    beat = BeatDef(id="b", label="b", kind="strike", base=5, stat_check="Cunning")
    assert module.compute_dc(beat) == 20
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: sidequest.game.ruleset.dial` (and/or `ImportError: DialRulesetModule`).

- [ ] **Step 3: Rename the module file with git**

```bash
cd sidequest-server
git mv sidequest/game/ruleset/native.py sidequest/game/ruleset/dial.py
```

- [ ] **Step 4: Rename the class, slug, and fix the docstring in `dial.py`**

In `sidequest/game/ruleset/dial.py`, replace the module docstring (lines 1–6) and the class header (lines 40–41):

```python
"""DialRulesetModule — SideQuest's dial/beat/confrontation turn, behind the seam.

This is ADR-033's confrontation engine, relocated. It is the shared d20 dial/beat/
contest engine that packs bind via ``ruleset: dial`` AND that the Without Number
family delegates ``compute_dc`` to (their own modules raise on it). It is NOT the
Fate family's engine — a Fate pack resolves through fate_conflict / fate_contest,
never here (spec 2026-06-17 closes that bleed). Selected explicitly by the pack;
never a fallback.
"""
```

```python
class DialRulesetModule(RulesetModule):
    slug = "dial"
```

Then within `dial.py`, update the comment on line ~74 (`# native ignores target_core...`) to read `# the dial engine ignores target_core...` and the helper comment on line ~28 (`relocated native-dial lookup`) to `relocated dial lookup`. No logic changes.

- [ ] **Step 5: Update the registry** (`sidequest/game/ruleset/registry.py`)

```python
from sidequest.game.ruleset.dial import DialRulesetModule
```
(was `from sidequest.game.ruleset.native import NativeRulesetModule`)

```python
    DialRulesetModule.slug: DialRulesetModule(),
```
(was `NativeRulesetModule.slug: NativeRulesetModule(),` — line 13). The dict key auto-follows `.slug`.

- [ ] **Step 6: Update the one production lookup** (`sidequest/server/dispatch/confrontation.py`)

Lines 368–371 become:

```python
        if cdef.resolution_mode == ResolutionMode.opposed_check:
            dial_module = get_ruleset_module("dial")

            def _offer_dc(beat_def: BeatDef) -> int:
                return dial_module.compute_dc(beat_def)
```

- [ ] **Step 7: Update the authored default** (`sidequest/genre/models/rules.py:1097-1099`)

```python
    ruleset: str = (
        "dial"  # bound RulesetModule slug (pluggable-SRD Spec 0). Default = the shared dial engine.
    )
```

- [ ] **Step 8: Update the two semantic comparisons**

`sidequest/server/dispatch/pregen.py:453`: `elif ruleset != "native":` → `elif ruleset != "dial":`
`sidequest/cli/encountergen/encountergen.py:811`: `if pack.rules.ruleset != "native":` → `if pack.rules.ruleset != "dial":`

(The `"native"` literal at `pregen.py:434` is handled in Task 2 — leave it for now; the suite stays green because the default still resolves through the registry until Task 2.)

- [ ] **Step 9: Update the WN docstring** (`sidequest/game/ruleset/without_number.py:150-153`)

```python
    def compute_dc(self, beat) -> int:
        raise NotImplementedError(
            "WN resolves attacks vs target AC via attack_params; compute_dc is the dial engine's."
        )
```

- [ ] **Step 10: Sweep for stragglers**

Run: `cd sidequest-server && grep -rn '"native"' sidequest/ | grep -v 'magic/'`
Expected output: only `pregen.py:434` (handled in Task 2). If any other ruleset-slug literal appears, change it to `"dial"`. Comment-only references to "native" are cosmetic and may be left, but update any that now read falsely (e.g. `confrontation.py` comments calling it "the native module").

- [ ] **Step 11: Run the rename test + the full suite**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_registry.py -v && uv run pytest -q`
Expected: the new tests PASS; the full suite PASS (no resolution change for any ruleset). If a test referenced `NativeRulesetModule` or `sidequest.game.ruleset.native`, update its import to `DialRulesetModule` / `dial` — this is part of the rename, not a behavior change.

- [ ] **Step 12: Lint + commit**

```bash
cd sidequest-server && uv run ruff check . && uv run ruff format .
git add -A && git commit -m "refactor(ruleset): rename native dial engine to 'dial' (spec 2026-06-17 §1)

NativeRulesetModule -> DialRulesetModule, slug native -> dial. Honest name:
it is the shared dial/beat/contest engine the WN family delegates compute_dc
to, not a Fate engine and not a fallback. Pure rename, zero resolution change.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Fail-loud the three silent `"native"` fallbacks

**Files:**
- Modify: `sidequest/server/dispatch/pregen.py:434`
- Modify: `sidequest/server/dispatch/encounter_lifecycle.py:967` (default param) and `:1182` (call site)
- Test: `tests/server/dispatch/test_ruleset_failloud.py` (new)

**Interfaces:**
- Consumes: a `pack` whose `.rules.ruleset` is the bound slug.
- Produces: a missing pack/rules raises `ValueError` instead of defaulting to a slug. No legitimate path may rely on the old default — if one breaks, fix the caller to pass the pack, never restore the default (No Silent Fallbacks).

- [ ] **Step 1: Write the failing test** (`tests/server/dispatch/test_ruleset_failloud.py`)

```python
import pytest

from sidequest.server.dispatch.encounter_lifecycle import instantiate_table_encounter


def test_table_encounter_requires_explicit_ruleset_slug():
    # ruleset_slug is now required (no "native" default). Omitting it is a TypeError
    # at the call boundary — the param has no default.
    import inspect

    sig = inspect.signature(instantiate_table_encounter)
    assert sig.parameters["ruleset_slug"].default is inspect.Parameter.empty, (
        "ruleset_slug must have no default — a missing ruleset is a config error, "
        "not a silent 'native' (spec 2026-06-17 §1, No Silent Fallbacks)"
    )
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_ruleset_failloud.py -v`
Expected: FAIL — the default is currently `"native"`, not `Parameter.empty`.

- [ ] **Step 3: Fail-loud `pregen.py:434`**

```python
    if pack is None or getattr(pack, "rules", None) is None:
        raise ValueError(
            "pregen.seed_manual: pack/rules missing — cannot resolve ruleset. A "
            "missing ruleset is a configuration error, not a silent 'dial' default "
            "(spec 2026-06-17 §1, No Silent Fallbacks)."
        )
    ruleset = pack.rules.ruleset
```
(replaces `ruleset = getattr(getattr(pack, "rules", None), "ruleset", "native") if pack else "native"`)

- [ ] **Step 4: Fail-loud the `encounter_lifecycle.py` default param (`:967`)**

Remove the default so the slug must be supplied:

```python
    seed: int,
    ruleset_slug: str,
    seat_seeds: dict[str, dict] | None = None,
```
(was `ruleset_slug: str = "native",`)

- [ ] **Step 5: Fail-loud the call site (`encounter_lifecycle.py:1182`)**

```python
            ruleset_slug=(
                pack.rules.ruleset
                if pack and pack.rules
                else _raise_missing_ruleset("table_resolution")
            ),
```

Add this module-level helper near the top of `encounter_lifecycle.py` (after imports):

```python
def _raise_missing_ruleset(context: str) -> str:
    raise ValueError(
        f"{context}: pack/rules missing — cannot resolve ruleset slug. A missing "
        f"ruleset is a configuration error, not a silent 'dial' default "
        f"(spec 2026-06-17 §1, No Silent Fallbacks)."
    )
```

- [ ] **Step 6: Run the test + full suite**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_ruleset_failloud.py -v && uv run pytest -q`
Expected: new test PASS; full suite PASS. If a production caller of `instantiate_table_encounter` or `seed_manual` relied on the old default, it surfaces here — fix it to pass `pack.rules.ruleset` (the real packs always have one). Do NOT re-add a default.

- [ ] **Step 7: Lint + commit**

```bash
cd sidequest-server && uv run ruff check . && uv run ruff format .
git add -A && git commit -m "refactor(ruleset): fail-loud the three silent 'native' ruleset fallbacks (spec 2026-06-17 §1)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

# Phase 2 — The Fate Contest engine

### Task 3: Add `ResolutionMode.contest` and the `ContestState` encounter model

**Files:**
- Modify: `sidequest/genre/models/rules.py:331-334` (`ResolutionMode` enum)
- Modify: `sidequest/game/encounter.py` (add `ContestState`; add field to `StructuredEncounter`)
- Test: `tests/game/test_encounter_contest.py` (new)

**Interfaces:**
- Produces: `ResolutionMode.contest = "contest"`; `ContestState(target: int = 3, player_victories: int = 0, opponent_victories: int = 0)` (pydantic `BaseModel`, `extra="forbid"`); `StructuredEncounter.contest: ContestState | None = None`. Consumed by Tasks 5, 6, 7.

- [ ] **Step 1: Write the failing test** (`tests/game/test_encounter_contest.py`)

```python
from sidequest.game.encounter import ContestState, EncounterActor, StructuredEncounter
from sidequest.genre.models.rules import ResolutionMode


def test_resolution_mode_has_contest():
    assert ResolutionMode.contest == "contest"


def test_encounter_carries_optional_contest_state():
    enc = StructuredEncounter(encounter_type="negotiation", category="social", actors=[])
    assert enc.contest is None
    enc.contest = ContestState(target=3)
    assert (enc.contest.player_victories, enc.contest.opponent_victories) == (0, 0)
    assert enc.contest.target == 3
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `cd sidequest-server && uv run pytest tests/game/test_encounter_contest.py -v`
Expected: FAIL — `AttributeError: contest` / `ImportError: ContestState` / `ResolutionMode` has no `contest`.

- [ ] **Step 3: Add the enum member** (`sidequest/genre/models/rules.py`)

In `ResolutionMode` (after `table_resolution = "table_resolution"`), add and extend the docstring:

```python
    beat_selection = "beat_selection"
    sealed_letter_lookup = "sealed_letter_lookup"
    opposed_check = "opposed_check"
    table_resolution = "table_resolution"
    contest = "contest"
```

Add to the docstring: `- ``contest``: Fate Core Contest (ADR-144). Both sides roll 4dF + skill; the higher result scores a victory (2 on a 3+ margin); a tie grants each side a boost. First to N victories (the metric ``threshold``) wins. No stress, no consequences. **Fate packs only.**`

- [ ] **Step 4: Add `ContestState` and the encounter field** (`sidequest/game/encounter.py`)

Add `ContestState` immediately after the `FateSealedCommit` model (it sits near line 185, beside the Fate state types):

```python
class ContestState(BaseModel):
    """First-to-N victory tally for a Fate Contest (ADR-144, spec 2026-06-17).

    The Contest analogue of the Conflict's stress track: each exchange the side
    with the higher 4dF total scores 1 victory (2 on a 3+ margin); a tie grants
    each side a boost and no victory. First side to ``target`` victories wins.
    There is no stress and no consequences — that is what distinguishes a Contest
    from a Conflict. ``target`` is seeded from the cdef's metric threshold (the
    re-authored ``0->3`` victory tally that replaced the ``0->7`` dial)."""

    model_config = {"extra": "forbid"}

    target: int = 3
    player_victories: int = 0
    opponent_victories: int = 0
```

On `StructuredEncounter`, add the field beside `fate_commits` (≈ line 271):

```python
    #: Set when this encounter resolves as a Fate Contest (cdef.resolution_mode ==
    #: contest). None for every Conflict / dial / table encounter. Selects the
    #: contest exchange engine in dispatch_fate_action (spec 2026-06-17 §2).
    contest: ContestState | None = None
```

- [ ] **Step 5: Run the test + commit**

Run: `cd sidequest-server && uv run pytest tests/game/test_encounter_contest.py -v && uv run ruff check . && uv run ruff format .`
Expected: PASS.

```bash
git add -A && git commit -m "feat(fate): add ResolutionMode.contest + ContestState encounter model (spec 2026-06-17 §2)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Define the three `fate.contest.*` OTEL spans

**Files:**
- Modify: `sidequest/telemetry/spans/fate.py` (add 3 span fns + 3 `SPAN_ROUTES` + `__all__`)
- Test: `tests/telemetry/test_fate_contest_spans.py` (new)

**Interfaces:**
- Produces (consumed by Tasks 5, 6):
  - `fate_contest_seeded_span(*, encounter_type: str, target: int, player_seats: int, _tracer=None, **attrs)` → emits `fate.contest.seeded`
  - `fate_contest_exchange_span(*, winner_side: str, victory_delta: int, player_victories: int, opponent_victories: int, round_number: int = 0, _tracer=None, **attrs)` → emits `fate.contest.exchange`
  - `fate_contest_resolved_span(*, winner_side: str, player_victories: int, opponent_victories: int, _tracer=None, **attrs)` → emits `fate.contest.resolved`

- [ ] **Step 1: Write the failing test** (`tests/telemetry/test_fate_contest_spans.py`)

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.telemetry.spans._core import SPAN_ROUTES
from sidequest.telemetry.spans.fate import (
    fate_contest_exchange_span,
    fate_contest_resolved_span,
    fate_contest_seeded_span,
)


def _exporter():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider.get_tracer("t"), exporter


def test_contest_spans_emit_and_route():
    tracer, exporter = _exporter()
    fate_contest_seeded_span(encounter_type="negotiation", target=3, player_seats=1, _tracer=tracer)
    fate_contest_exchange_span(
        winner_side="player", victory_delta=2, player_victories=2, opponent_victories=0,
        round_number=1, _tracer=tracer,
    )
    fate_contest_resolved_span(
        winner_side="player", player_victories=3, opponent_victories=1, _tracer=tracer
    )
    names = {s.name for s in exporter.get_finished_spans()}
    assert {"fate.contest.seeded", "fate.contest.exchange", "fate.contest.resolved"} <= names
    # Each contest span must carry a GM-panel route.
    for key in ("fate.contest.seeded", "fate.contest.exchange", "fate.contest.resolved"):
        assert key in SPAN_ROUTES, f"{key} has no SPAN_ROUTES entry"
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `cd sidequest-server && uv run pytest tests/telemetry/test_fate_contest_spans.py -v`
Expected: FAIL — `ImportError` for the three `fate_contest_*_span` names.

- [ ] **Step 3: Add the `SPAN_ROUTES` entries** (`sidequest/telemetry/spans/fate.py`, after the F1c conflict-exchange routes ≈ line 389)

```python
# --- Fate Contest spans (spec 2026-06-17 §2; GM panel = lie detector) ---------
# The contest engine resolved an exchange — the GM-panel evidence that the
# Contest's 4dF-vs-4dF math ran, not the narrator improvising a social outcome.
# Literal keys (no SPAN_* constant) — the routing-completeness lint only inspects
# SPAN_* module constants (the F1c/F2a precedent).
SPAN_ROUTES["fate.contest.seeded"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "contest_seeded",
        "encounter_type": (span.attributes or {}).get("encounter_type", ""),
        "target": (span.attributes or {}).get("target", 0),
        "player_seats": (span.attributes or {}).get("player_seats", 0),
    },
)
SPAN_ROUTES["fate.contest.exchange"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "contest_exchange",
        "winner_side": (span.attributes or {}).get("winner_side", ""),
        "victory_delta": (span.attributes or {}).get("victory_delta", 0),
        "player_victories": (span.attributes or {}).get("player_victories", 0),
        "opponent_victories": (span.attributes or {}).get("opponent_victories", 0),
        "round_number": (span.attributes or {}).get("round_number", 0),
    },
)
SPAN_ROUTES["fate.contest.resolved"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "contest_resolved",
        "winner_side": (span.attributes or {}).get("winner_side", ""),
        "player_victories": (span.attributes or {}).get("player_victories", 0),
        "opponent_victories": (span.attributes or {}).get("opponent_victories", 0),
    },
)
```

- [ ] **Step 4: Add the three span functions** (after `fate_conceded_span`, ≈ line 642)

```python
def fate_contest_seeded_span(
    *,
    encounter_type: str,
    target: int,
    player_seats: int,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.contest.seeded`` — a Fate Contest was seated (first-to-``target``
    victory tally). The GM-panel evidence the engine instantiated a Contest, not a
    dial confrontation, for a Fate-bound pack (spec 2026-06-17 §2)."""
    attributes: dict[str, Any] = {
        "field": "contest_seeded",
        "encounter_type": encounter_type,
        "target": target,
        "player_seats": player_seats,
        **attrs,
    }
    with Span.open("fate.contest.seeded", attributes, tracer_override=_tracer):
        pass


def fate_contest_exchange_span(
    *,
    winner_side: str,
    victory_delta: int,
    player_victories: int,
    opponent_victories: int,
    round_number: int = 0,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.contest.exchange`` — one resolved contest exchange. ``winner_side``
    is ``player`` / ``opponent`` / ``""`` (a tie); ``victory_delta`` is 0/1/2. The
    running tally lets the GM panel confirm the victory math, not narrator fiat."""
    attributes: dict[str, Any] = {
        "field": "contest_exchange",
        "winner_side": winner_side,
        "victory_delta": victory_delta,
        "player_victories": player_victories,
        "opponent_victories": opponent_victories,
        "round_number": round_number,
        **attrs,
    }
    with Span.open("fate.contest.exchange", attributes, tracer_override=_tracer):
        pass


def fate_contest_resolved_span(
    *,
    winner_side: str,
    player_victories: int,
    opponent_victories: int,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.contest.resolved`` — a Contest reached its victory target. The
    GM-panel record of who won and the final tally (spec 2026-06-17 §2)."""
    attributes: dict[str, Any] = {
        "field": "contest_resolved",
        "winner_side": winner_side,
        "player_victories": player_victories,
        "opponent_victories": opponent_victories,
        **attrs,
    }
    with Span.open("fate.contest.resolved", attributes, tracer_override=_tracer):
        pass
```

- [ ] **Step 5: Export them** — add to `__all__` (≈ line 898), keeping it sorted-ish:

```python
    "fate_contest_exchange_span",
    "fate_contest_resolved_span",
    "fate_contest_seeded_span",
```

- [ ] **Step 6: Run the span test + the routing-completeness suite + commit**

Run: `cd sidequest-server && uv run pytest tests/telemetry/test_fate_contest_spans.py tests/telemetry/test_routing_completeness.py -v && uv run ruff check . && uv run ruff format .`
Expected: PASS.

```bash
git add -A && git commit -m "feat(telemetry): add fate.contest.{seeded,exchange,resolved} spans (spec 2026-06-17 §2/§5)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Implement the Contest engine (`fate_contest.py`)

**Files:**
- Create: `sidequest/server/dispatch/fate_contest.py`
- Test: `tests/server/dispatch/test_fate_contest.py` (new)

**Interfaces:**
- Consumes from `fate_conflict.py`: `_seat_opponent_commits`, `FateConflictError` (for the type hierarchy), and `_watcher_publish`. From `fate_sheet`: `Aspect`. From `telemetry.spans.fate`: `fate_aspect_created_span`, `fate_contest_exchange_span`, `fate_contest_resolved_span`. From `game.encounter`: `StructuredEncounter`, `ContestState`. From `game.session`: `GameSnapshot`. From `ruleset.fate`: `FateRulesetModule`.
- Produces (consumed by Task 7): `FateContestError(ValueError)`; `FateContestResult` (frozen dataclass: `resolution_order: str`, `resolved: bool`, `player_victories: int`, `opponent_victories: int`, `narrator_hints: list[object]`); `run_fate_contest_exchange(*, encounter, snapshot, ruleset, rng, round_number=0, _tracer=None) -> FateContestResult`.
- **Scoring (SRD Contest):** each side's exchange result = the **max** `ladder_total` among its committed actors. Higher side scores 1 victory, or 2 if its margin over the other side is ≥ 3 (succeed-with-style). A tie at the top scores no victory and grants **each** top side a boost (Aspect kind `boost`, 1 free invoke). First side to `contest.target` victories sets `encounter.resolved` + `encounter.outcome`.
- **v1 scope note:** the contest scores by best committed roll per side regardless of the committed action; aspect invokes already fold into `ladder_total` at the shared dispatch seal (Task 7), so they "carry over natively." A distinct `create_advantage`-during-contest branch (place a situation aspect *and* forgo scoring) is a deferred fast-follow — out of v1 scope. `attack` is rejected at dispatch (Task 7), so it never reaches here.

- [ ] **Step 1: Write the failing tests** (`tests/server/dispatch/test_fate_contest.py`)

```python
from __future__ import annotations

import random

from sidequest.game.character import Character
from sidequest.game.creature_core import CreatureCore
from sidequest.game.encounter import ContestState, EncounterActor, StructuredEncounter
from sidequest.game.fate_sheet import FateSheet
from sidequest.game.session import GameSnapshot, Npc
from sidequest.game.ruleset import get_ruleset_module
from sidequest.server.dispatch.fate_conflict import seal_fate_commit
from sidequest.server.dispatch.fate_contest import run_fate_contest_exchange


def _pc(name: str, skills: dict[str, int]) -> Character:
    core = CreatureCore(
        name=name, description="d", personality="p", fate_sheet=FateSheet(skills=skills)
    )
    return Character(core=core, char_class="Agent", race="Human", backstory="b")


def _contest_encounter() -> StructuredEncounter:
    enc = StructuredEncounter(
        encounter_type="negotiation",
        category="social",
        actors=[
            EncounterActor(name="Lady Ash", role="lead", side="player"),
            EncounterActor(name="The Vicar", role="rival", side="opponent"),
        ],
    )
    enc.contest = ContestState(target=3)
    return enc


def _snapshot(enc: StructuredEncounter) -> GameSnapshot:
    snap = GameSnapshot(
        genre_slug="tea_test",
        characters=[_pc("Lady Ash", {"Rapport": 4})],
        npcs=[Npc(core=CreatureCore(
            name="The Vicar", description="d", personality="p",
            fate_sheet=FateSheet(skills={"Rapport": 1, "Empathy": 1}),
        ))],
        encounter=enc,
    )
    return snap


def test_higher_total_scores_one_victory():
    enc = _contest_encounter()
    snap = _snapshot(enc)
    # Player sealed a 5, opponent will roll low (rng all -1: -4 + skill 1 = -3).
    seal_fate_commit(
        encounter=enc, actor=enc.find_actor("Lady Ash"),
        action="overcome", skill="Rapport", difficulty=0, ladder_total=5,
    )
    result = run_fate_contest_exchange(
        encounter=enc, snapshot=snap, ruleset=get_ruleset_module("fate"),
        rng=random.Random(0), round_number=1,
    )
    assert enc.contest.player_victories == 1
    assert enc.contest.opponent_victories == 0
    assert result.resolved is False


def test_margin_of_three_scores_two_victories():
    enc = _contest_encounter()
    snap = _snapshot(enc)
    seal_fate_commit(
        encounter=enc, actor=enc.find_actor("Lady Ash"),
        action="overcome", skill="Rapport", difficulty=0, ladder_total=8,
    )
    # Opponent rolls all -1 (rng below) -> -4 + 1 = -3. Margin 11 >= 3 -> +2.
    run_fate_contest_exchange(
        encounter=enc, snapshot=snap, ruleset=get_ruleset_module("fate"),
        rng=random.Random(0), round_number=1,
    )
    assert enc.contest.player_victories == 2


def test_first_to_three_resolves_with_winner_outcome():
    enc = _contest_encounter()
    enc.contest = ContestState(target=3, player_victories=2)
    snap = _snapshot(enc)
    seal_fate_commit(
        encounter=enc, actor=enc.find_actor("Lady Ash"),
        action="overcome", skill="Rapport", difficulty=0, ladder_total=9,
    )
    result = run_fate_contest_exchange(
        encounter=enc, snapshot=snap, ruleset=get_ruleset_module("fate"),
        rng=random.Random(0),
    )
    assert result.resolved is True
    assert enc.resolved is True
    assert enc.outcome == "player_victory"


def test_tie_grants_each_side_a_boost_and_no_victory():
    enc = _contest_encounter()
    snap = _snapshot(enc)
    # Force a tie: opponent's seated FateSheet Rapport 1, rng all 0 -> 0+1 = 1.
    seal_fate_commit(
        encounter=enc, actor=enc.find_actor("Lady Ash"),
        action="overcome", skill="Rapport", difficulty=0, ladder_total=1,
    )
    run_fate_contest_exchange(
        encounter=enc, snapshot=snap, ruleset=get_ruleset_module("fate"),
        rng=random.Random(0),  # all faces 0 via the Random(0) sequence below is NOT guaranteed
    )
    # Use a deterministic rng that always rolls 0 for the tie assertion:
```

> Note for the tie test: replace the `random.Random(0)` in `test_tie_*` with a deterministic stub so the opponent's 4dF sums to 0 (total = skill 1, matching the player's sealed 1). Add this stub at the top of the file and use it in the tie test:

```python
class _ZeroDice(random.Random):
    """4dF that always rolls 0 on every face -> ladder_total == skill_rating."""

    def choice(self, seq):  # type: ignore[override]
        return 0
```

Then the tie test body asserts:

```python
    run_fate_contest_exchange(
        encounter=enc, snapshot=snap, ruleset=get_ruleset_module("fate"), rng=_ZeroDice(),
    )
    assert enc.contest.player_victories == 0
    assert enc.contest.opponent_victories == 0
    assert any(a.kind == "boost" for a in enc.situation_aspects)
    assert len([a for a in enc.situation_aspects if a.kind == "boost"]) == 2
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_contest.py -v`
Expected: FAIL — `ModuleNotFoundError: sidequest.server.dispatch.fate_contest`.

- [ ] **Step 3: Create `sidequest/server/dispatch/fate_contest.py`**

```python
"""fate_contest.py — the Fate Core Contest engine (ADR-144, spec 2026-06-17 §2).

Sibling to ``fate_conflict.py`` "one tier over": where a Conflict resolves harm
via stress/consequences, a Contest resolves a *goal* — opposed 4dF, first to N
victories, a tie grants a boost. No stress, no consequences. Reached through the
same FATE_ACTION channel and gated by ``isinstance(ruleset, FateRulesetModule)``;
``dispatch_fate_action`` selects this engine when ``encounter.contest is not None``
(stamped from the cdef's ``resolution_mode: contest`` at seating).

The GM panel is the lie detector: every exchange emits ``fate.contest.exchange``
and the win emits ``fate.contest.resolved`` (the OTEL Observability Principle)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from opentelemetry import trace

from sidequest.game.encounter import StructuredEncounter
from sidequest.game.fate_sheet import Aspect
from sidequest.game.ruleset.fate import FateRulesetModule
from sidequest.game.session import GameSnapshot
from sidequest.telemetry.spans.fate import (
    fate_aspect_created_span,
    fate_contest_exchange_span,
    fate_contest_resolved_span,
)

# Shared sealed-commit/opponent-seating substrate lives in fate_conflict; import
# the helpers (one direction only — fate_conflict imports THIS module lazily,
# inside dispatch_fate_action, to break the cycle).
from sidequest.server.dispatch.fate_conflict import (
    _seat_opponent_commits,
    _watcher_publish,
)


class FateContestError(ValueError):
    """A Contest invariant was violated (e.g. run on a non-contest encounter)."""


@dataclass(frozen=True)
class FateContestResult:
    """What one contest exchange produced. Mirrors ``FateExchangeResult`` plus the
    running victory tally so the dispatch result and FateActionHandler can surface
    it (the Sebastien/Jade legibility mandate)."""

    resolution_order: str
    resolved: bool
    player_victories: int
    opponent_victories: int
    narrator_hints: list[object] = field(default_factory=list)


def run_fate_contest_exchange(
    *,
    encounter: StructuredEncounter,
    snapshot: GameSnapshot,
    ruleset: FateRulesetModule,
    rng: random.Random,
    round_number: int = 0,
    _tracer: trace.Tracer | None = None,
) -> FateContestResult:
    """Resolve one sealed Contest exchange.

    Each side's result is the best (max) ``ladder_total`` among its committed
    actors. The higher side scores 1 victory, or 2 on a 3+ margin (succeed with
    style). A tie at the top scores no victory and grants each top side a boost.
    First side to ``contest.target`` victories resolves the encounter."""
    contest = encounter.contest
    if contest is None:
        raise FateContestError(
            "run_fate_contest_exchange requires a contest-mode encounter "
            "(encounter.contest is None) — this is a Conflict; route to "
            "run_fate_exchange (spec 2026-06-17 §2)"
        )

    mental = encounter.category == "social"
    # The Other rolls 4dF from its seated FateSheet, exactly as in a Conflict.
    _seat_opponent_commits(
        encounter=encounter, snapshot=snapshot, ruleset=ruleset, rng=rng,
        mental=mental, _tracer=_tracer,
    )

    # Best committed total per side.
    best: dict[str, tuple[str, int]] = {}
    walked: list[str] = []
    for commit in encounter.fate_commits:
        actor = encounter.find_actor(commit.actor)
        if actor is None:
            continue
        walked.append(commit.actor)
        side = actor.side
        if side not in best or commit.ladder_total > best[side][1]:
            best[side] = (commit.actor, commit.ladder_total)

    player = best.get("player")
    opponent = best.get("opponent")
    hints: list[object] = []
    winner_side = ""
    victory_delta = 0

    if player is not None and opponent is not None:
        p_name, p_total = player
        o_name, o_total = opponent
        if p_total > o_total:
            winner_side = "player"
            victory_delta = 2 if (p_total - o_total) >= 3 else 1
            contest.player_victories += victory_delta
            hints.append(
                f"{p_name} wins the exchange ({p_total} vs {o_total}) — +{victory_delta} victory."
            )
        elif o_total > p_total:
            winner_side = "opponent"
            victory_delta = 2 if (o_total - p_total) >= 3 else 1
            contest.opponent_victories += victory_delta
            hints.append(
                f"{o_name} wins the exchange ({o_total} vs {p_total}) — +{victory_delta} victory."
            )
        else:  # tie at the top — boost to each side, no victory (SRD)
            for name in (p_name, o_name):
                boost = Aspect(text=f"Fleeting Opening by {name}", kind="boost", free_invokes=1)
                encounter.situation_aspects.append(boost)
                fate_aspect_created_span(
                    actor=name, aspect=boost.text, free_invokes=1, _tracer=_tracer
                )
            hints.append(f"Tie ({p_total}={o_total}) — no victory; each side gains a boost.")

    encounter.fate_commits.clear()
    encounter.narrator_hints.extend(str(h) for h in hints)

    if contest.player_victories >= contest.target:
        encounter.resolved = True
        encounter.outcome = "player_victory"
    elif contest.opponent_victories >= contest.target:
        encounter.resolved = True
        encounter.outcome = "opponent_victory"

    fate_contest_exchange_span(
        winner_side=winner_side,
        victory_delta=victory_delta,
        player_victories=contest.player_victories,
        opponent_victories=contest.opponent_victories,
        round_number=round_number,
        _tracer=_tracer,
    )
    if encounter.resolved:
        fate_contest_resolved_span(
            winner_side=("player" if contest.player_victories >= contest.target else "opponent"),
            player_victories=contest.player_victories,
            opponent_victories=contest.opponent_victories,
            _tracer=_tracer,
        )
    _watcher_publish(
        "state_transition",
        {
            "field": "encounter",
            "op": "fate_contest_resolved",
            "encounter_type": encounter.encounter_type,
            "winner_side": winner_side,
            "player_victories": contest.player_victories,
            "opponent_victories": contest.opponent_victories,
            "resolved": encounter.resolved,
            "round_number": round_number,
            "source": "fate_contest",
        },
        component="encounter",
    )
    return FateContestResult(
        resolution_order=", ".join(walked),
        resolved=encounter.resolved,
        player_victories=contest.player_victories,
        opponent_victories=contest.opponent_victories,
        narrator_hints=hints,
    )
```

- [ ] **Step 4: Run the contest tests**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_contest.py -v`
Expected: PASS. If `_seat_opponent_commits` or `Aspect.kind` signatures differ from what's mirrored here, fix this module to match the real signatures (verify against `fate_conflict.py` `_resolve_create_advantage` lines 552–610, which is the canonical boost-creation precedent).

- [ ] **Step 5: Lint + commit**

```bash
cd sidequest-server && uv run ruff check . && uv run ruff format .
git add -A && git commit -m "feat(fate): add the Contest engine — opposed 4dF, first-to-N, tie->boost (spec 2026-06-17 §2)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Stamp the seated encounter with `ContestState` + emit `fate.contest.seeded`

**Files:**
- Modify: `sidequest/server/dispatch/encounter_lifecycle.py` (`instantiate_encounter_from_trigger`)
- Test: extend `tests/server/dispatch/test_fate_contest.py`

**Interfaces:**
- Consumes: `cdef.resolution_mode`, `cdef.player_metric.threshold`, `ResolutionMode.contest`, `ContestState`, `fate_contest_seeded_span`.
- Produces: a seated `StructuredEncounter` whose `.contest` is set (and a `fate.contest.seeded` span fired) iff `cdef.resolution_mode == ResolutionMode.contest`.

- [ ] **Step 1: Write the failing wiring test** (append to `tests/server/dispatch/test_fate_contest.py`)

```python
def test_seating_stamps_contest_state_and_emits_span():
    """instantiate_encounter_from_trigger stamps encounter.contest for a
    contest-mode cdef and fires fate.contest.seeded (the GM-panel wiring proof)."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from sidequest.server.dispatch import encounter_lifecycle as el

    # A minimal fate pack + snapshot that seats a contest-mode negotiation.
    # Build via the project's existing test fixtures for a fate pack (see
    # tests/server/dispatch/test_fate_conflict.py seating helpers); assert:
    #   - returned encounter.contest is not None
    #   - encounter.contest.target == cdef.player_metric.threshold (3)
    #   - a "fate.contest.seeded" span fired
    ...
```

> Implementer note: reuse the fate-pack seating fixture pattern from the existing seating tests in `tests/server/dispatch/` (search for `instantiate_encounter_from_trigger(` in `tests/`). The assertion shape is the three bullets above. This is a behavior/span wiring test, not a source grep (CLAUDE.md No-Source-Text-Wiring-Tests).

- [ ] **Step 2: Run it to confirm it fails**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_contest.py -k seating -v`
Expected: FAIL — `encounter.contest` is `None` (no stamp yet).

- [ ] **Step 3: Locate the construction site**

Run: `cd sidequest-server && grep -n "StructuredEncounter(" sidequest/server/dispatch/encounter_lifecycle.py`
This is the non-table construction inside `instantiate_encounter_from_trigger` (the table path uses `instantiate_table_encounter`). Identify the line where the `StructuredEncounter` for a beat/dial/conflict cdef is built and assigned (the variable is returned / assigned to `snapshot.encounter`).

- [ ] **Step 4: Add the stamp immediately after the encounter is built**

After the `StructuredEncounter(...)` is constructed (call the local `encounter`), add:

```python
    # spec 2026-06-17 §2: a Fate Contest cdef stamps a first-to-N victory tally
    # onto the encounter. dispatch_fate_action reads encounter.contest to select
    # the Contest engine over the Conflict engine. target comes from the authored
    # metric threshold (the 0->3 victory tally that replaced the 0->7 dial).
    if cdef.resolution_mode == ResolutionMode.contest:
        from sidequest.game.encounter import ContestState
        from sidequest.telemetry.spans.fate import fate_contest_seeded_span

        target = cdef.player_metric.threshold if cdef.player_metric is not None else 3
        encounter.contest = ContestState(target=target)
        player_seats = sum(1 for a in encounter.actors if a.side == "player")
        fate_contest_seeded_span(
            encounter_type=encounter.encounter_type, target=target, player_seats=player_seats
        )
```

Ensure `ResolutionMode` is imported at the top of `encounter_lifecycle.py` (it imports `ConfrontationDef` already; add `ResolutionMode` to that import from `sidequest.genre.models.rules`).

- [ ] **Step 5: Run the wiring test + full dispatch suite + commit**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_contest.py -v && uv run ruff check . && uv run ruff format .`
Expected: PASS.

```bash
git add -A && git commit -m "feat(fate): stamp ContestState at seating + emit fate.contest.seeded (spec 2026-06-17 §2)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Route `dispatch_fate_action` to the Contest engine

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py` (`dispatch_fate_action`, `FateDispatchResult`)
- Test: extend `tests/server/dispatch/test_fate_contest.py`

**Interfaces:**
- Consumes: `encounter.contest`, `run_fate_contest_exchange`, `FateContestResult`.
- Produces: when `encounter.contest is not None`, a closed barrier fires `run_fate_contest_exchange` (not `run_fate_exchange`); `payload.action == "attack"` in contest mode raises `FateConflictError`. `FateDispatchResult.exchange` is widened to `FateExchangeResult | FateContestResult | None` (both expose `resolution_order`/`resolved`/`narrator_hints`; consumers read only those shared attrs).

- [ ] **Step 1: Write the failing tests** (append to `tests/server/dispatch/test_fate_contest.py`)

```python
import pytest

from sidequest.protocol.fate import FateActionPayload
from sidequest.server.dispatch.fate_conflict import FateConflictError, dispatch_fate_action
from sidequest.server.dispatch.fate_contest import FateContestResult


def _payload(action: str, skill: str = "Rapport") -> FateActionPayload:
    return FateActionPayload(request_id="r1", action=action, skill=skill, difficulty=0)


def test_dispatch_rejects_attack_in_a_contest():
    enc = _contest_encounter()
    snap = _snapshot(enc)
    with pytest.raises(FateConflictError):
        dispatch_fate_action(
            payload=_payload("attack"), actor_name="Lady Ash", encounter=enc,
            ruleset=get_ruleset_module("fate"), snapshot=snap, rng=_ZeroDice(),
        )


def test_dispatch_runs_contest_engine_when_barrier_closes():
    enc = _contest_encounter()
    snap = _snapshot(enc)  # 1 PC seated -> a single overcome closes the barrier
    result = dispatch_fate_action(
        payload=_payload("overcome"), actor_name="Lady Ash", encounter=enc,
        ruleset=get_ruleset_module("fate"), snapshot=snap, rng=_ZeroDice(),
    )
    assert result.commitment_pending is False
    assert isinstance(result.exchange, FateContestResult)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_contest.py -k dispatch -v`
Expected: FAIL — attack is accepted; the closed barrier runs `run_fate_exchange` (returns a `FateExchangeResult`, not a `FateContestResult`).

- [ ] **Step 3: Widen `FateDispatchResult.exchange`** (`fate_conflict.py`, the dataclass ≈ line 714)

```python
    commitment_pending: bool
    exchange: FateExchangeResult | "FateContestResult" | None
```

Add the import at the top of `fate_conflict.py` under a `TYPE_CHECKING` guard to avoid the import cycle:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sidequest.server.dispatch.fate_contest import FateContestResult
```

- [ ] **Step 4: Reject `attack` in contest mode** (in `dispatch_fate_action`, right after the `actor_obj is None` guard ≈ line 765)

```python
    # spec 2026-06-17 §2: a Contest has no harm — attacks are a Conflict action.
    if encounter.contest is not None and action == "attack":
        raise FateConflictError(
            "'attack' is a Conflict action; this encounter is a Contest (no stress, "
            "no consequences) — use 'overcome' (spec 2026-06-17 §2)"
        )
```

(Place this after `action = payload.action` is bound, before the concede branch.)

- [ ] **Step 5: Branch the barrier-close to the contest engine** (replace the `if fate_barrier_closed(...)` block at the end of `dispatch_fate_action` ≈ lines 914–924)

```python
    if fate_barrier_closed(encounter=encounter, snapshot=snapshot):
        if encounter.contest is not None:
            # Lazy import breaks the fate_conflict <-> fate_contest cycle.
            from sidequest.server.dispatch.fate_contest import run_fate_contest_exchange

            result = run_fate_contest_exchange(
                encounter=encounter,
                snapshot=snapshot,
                ruleset=ruleset,
                rng=rng,
                round_number=round_number,
                _tracer=_tracer,
            )
        else:
            result = run_fate_exchange(
                encounter=encounter,
                snapshot=snapshot,
                ruleset=ruleset,
                rng=rng,
                round_number=round_number,
                _tracer=_tracer,
            )
        return FateDispatchResult(commitment_pending=False, exchange=result, action_roll=outcome)
    return FateDispatchResult(commitment_pending=True, exchange=None, action_roll=outcome)
```

- [ ] **Step 6: Run the dispatch tests + the existing conflict suite (regression) + commit**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_contest.py tests/server/dispatch/test_fate_conflict.py -v && uv run ruff check . && uv run ruff format . && uv run pyright sidequest/server/dispatch/fate_conflict.py sidequest/server/dispatch/fate_contest.py`
Expected: all PASS; pyright clean. The conflict suite proves Task 7 did not regress the Conflict path.

```bash
git add -A && git commit -m "feat(fate): route FATE_ACTION to the Contest engine; reject attack in a Contest (spec 2026-06-17 §2)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

# Phase 3 — Re-author the Fate-pack confrontations (content repo)

> These tasks edit `sidequest-content` (branch off `main`). The conversion replaces `resolution_mode: opposed_check` with `resolution_mode: contest`, drops `opponent_default_stats` (the d20 ability scores the dial used — the Other now rolls 4dF from its seated FateSheet, exactly as in a Conflict), and changes both metric thresholds from `7` to `3` (the `0→7` dial becomes the `0→3` victory tally). Beats stay — they are the per-exchange action menu.

### Task 8: Convert tea_and_murder's 4 `opposed_check` defs to Contests

**Files:**
- Modify: `genre_packs/tea_and_murder/rules.yaml` (defs `negotiation` @217, `trial` @289, `social_duel` @421, `scandal` @497)

**Interface (the conversion recipe, applied to each of the 4 defs):**
- `resolution_mode: opposed_check` → `resolution_mode: contest`
- delete the `opponent_default_stats:` block (and its preceding ADR-093 ≤10 comment)
- `player_metric.threshold: 7` → `3`; `opponent_metric.threshold: 7` → `3`
- keep `player_metric.starting` / `opponent_metric.starting` (the start-line edge, e.g. negotiation's opponent `starting: 3`, is preserved as a victory head-start) — **but** `MetricDef` requires `threshold > starting`, so if any `starting >= 3`, lower it so `threshold(3) > starting`. negotiation's `opponent_metric.starting: 3` must drop to ≤ 2 (use `2` to keep the head-start fiction). scandal's `exposure starting: 3` likewise → `2`.
- keep `beats:`, `category:`, `intent_verbs:`, `mood:`, `label:` unchanged.

- [ ] **Step 1: Convert `negotiation` (@217)**

In `genre_packs/tea_and_murder/rules.yaml`, the `negotiation` def becomes:

```yaml
  - type: negotiation
    label: "Polite Negotiation"
    intent_verbs: [haggle, bargain, barter, offer, deal, price, sell, buy, negotiate]
    on_intent_mismatch: warn
    category: social
    # spec 2026-06-17 §3: a Polite Negotiation is a Fate Contest — both parties
    # roll 4dF + skill for leverage; the higher total scores a victory; first to 3
    # wins. The Other rolls from its seated FateSheet (no d20 opponent_default_stats,
    # no dial.compute_dc) — Fate owns its own confrontation now (ADR-144).
    resolution_mode: contest
    # The 0->3 victory tally (was the 0->7 leverage dial). opponent starts with a
    # 2-victory... no: starting is a head-start on the tally; keep < threshold.
    player_metric:
      name: leverage
      starting: 0
      threshold: 3
    opponent_metric:
      name: leverage
      starting: 1
      threshold: 3
    beats:
      - id: persuade
        label: "Appeal to Reason"
        kind: strike
        base: 2
        stat_check: Cunning
        effect: "opponent considers your argument"
        narrator_hint: "Show the NPC weighing the player's words."
      - id: threaten
        label: "Veiled Threat"
        kind: strike
        base: 3
        deltas:
          crit_fail:
            own: -1
        stat_check: Nerve
        risk: "faction reputation -1 if it fails"
        consequence: "NPC becomes hostile on critical failure"
        narrator_hint: "A polite suggestion with steel beneath. Propriety barely maintained."
      - id: concede_point
        label: "Concede a Point"
        kind: angle
        target_tag: "Real Goal"
        stat_check: Cunning
        effect: "opponent reveals their real goal — sets a leverage tag for the closer"
        narrator_hint: "Strategic retreat. Player gives ground to gain information."
      - id: walk_away
        label: "Take One's Leave"
        kind: push
        base: 0
        stat_check: Nerve
        resolution: true
        consequence: "deal collapses, reputation intact"
        narrator_hint: "Player excuses themselves. The matter is dropped — for now."
    mood: tension
```

> Note: `opponent_metric.starting` was `3` under the old `threshold: 7`; under `threshold: 3` it must be `< 3`. Use `1` (a modest head-start). Do NOT leave it `3` — `MetricDef._validate` raises `threshold must be > starting`.

- [ ] **Step 2: Convert `trial` (@289), `social_duel` (@421), `scandal` (@497)** by the same recipe

For each: set `resolution_mode: contest`, delete `opponent_default_stats:`, set both thresholds to `3`, and ensure each `starting < 3` (trial's are `0/0` → fine; social_duel — check and lower if ≥3; scandal's `exposure starting: 3` → `2`, `containment starting: 0` → fine). Keep beats and all other fields. Update the per-def comment to the spec-§3 framing (Fate Contest, no dial).

- [ ] **Step 3: Validate the pack loads and parses**

Run:
```bash
cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/tea_and_murder --verbose
```
Expected: `tea_and_murder ... PASS`. (This proves the YAML parses through `ConfrontationDef`/`RulesConfig` — `MetricDef` threshold>starting included.)

- [ ] **Step 4: Confirm zero `opposed_check` remain in tea_and_murder**

Run: `cd sidequest-content && grep -cE '^\s*resolution_mode:\s*opposed_check\s*$' genre_packs/tea_and_murder/rules.yaml`
Expected: `0`.

- [ ] **Step 5: Commit (content repo)**

```bash
cd sidequest-content
git add genre_packs/tea_and_murder/rules.yaml
git commit -m "content(tea_and_murder): re-author 4 opposed_check social defs as Fate Contests (spec 2026-06-17 §3)

negotiation/trial/social_duel/scandal: resolution_mode contest, 0->3 victory
tally, opponent rolls 4dF from its FateSheet (no dial.compute_dc). Closes the
cross-ruleset bleed — Fate owns its confrontations (ADR-144).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Convert spaghetti_western's 1 `opposed_check` def to a Contest

**Files:**
- Modify: `genre_packs/spaghetti_western/rules.yaml` (the single `opposed_check` def)

- [ ] **Step 1: Locate the def**

Run: `cd sidequest-content && grep -nE '^\s*-\s*type:|resolution_mode:\s*opposed_check|threshold:|opponent_default_stats:' genre_packs/spaghetti_western/rules.yaml`
Identify the one `opposed_check` def and its metric thresholds.

- [ ] **Step 2: Apply the conversion recipe**

`resolution_mode: opposed_check` → `contest`; delete `opponent_default_stats:`; both thresholds `7` → `3`; ensure each `starting < 3`; keep beats/category/intent_verbs/mood/label. Update the comment to the spec-§3 framing.

- [ ] **Step 3: Validate + confirm zero opposed_check**

Run:
```bash
cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/spaghetti_western --verbose
cd ../sidequest-content && grep -cE '^\s*resolution_mode:\s*opposed_check\s*$' genre_packs/spaghetti_western/rules.yaml
```
Expected: `spaghetti_western ... PASS`; grep prints `0`.

- [ ] **Step 4: Commit (content repo)**

```bash
cd sidequest-content
git add genre_packs/spaghetti_western/rules.yaml
git commit -m "content(spaghetti_western): re-author the opposed_check social def as a Fate Contest (spec 2026-06-17 §3)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

# Phase 4 — Guardrails, calibration scoping, and the no-bleed proof

### Task 10: Guardrail — a Fate pack authoring `opposed_check` fails to load loudly

**Files:**
- Modify: `sidequest/genre/models/rules.py` (`RulesConfig` — new `@model_validator(mode="after")`)
- Test: `tests/genre/test_fate_no_opposed_check.py` (new)

**Interfaces:**
- Consumes: `RulesConfig.ruleset` (1097), `RulesConfig.confrontations` (1169, `list[ConfrontationDef]`), `ResolutionMode.opposed_check`.
- Produces: constructing/validating a `RulesConfig` with `ruleset == "fate"` and any confrontation whose `resolution_mode == opposed_check` raises `pydantic.ValidationError` (= fails pack load). WN packs (cwn/awn/swn/wwn) and the dial default are unaffected (the gate is `ruleset == "fate"` only).

**Ordering:** this must land AFTER Tasks 8–9 (the real Fate packs are converted), or loading tea_and_murder/spaghetti_western would now raise.

- [ ] **Step 1: Write the failing test** (`tests/genre/test_fate_no_opposed_check.py`)

```python
import pytest
from pydantic import ValidationError

from sidequest.genre.models.rules import RulesConfig


def _conf(mode: str) -> dict:
    return {
        "type": "duel",
        "label": "Duel",
        "category": "social",
        "resolution_mode": mode,
        "player_metric": {"name": "x", "starting": 0, "threshold": 3},
        "opponent_metric": {"name": "y", "starting": 0, "threshold": 3},
    }


def test_fate_pack_rejects_opposed_check():
    with pytest.raises(ValidationError, match="opposed_check"):
        RulesConfig(ruleset="fate", confrontations=[_conf("opposed_check")])


def test_fate_pack_allows_contest():
    cfg = RulesConfig(ruleset="fate", confrontations=[_conf("contest")])
    assert cfg.confrontations[0].resolution_mode == "contest"


def test_wn_pack_still_allows_opposed_check():
    # The invariant (spec §0): cwn/awn keep opposed_check via the dial engine.
    cfg = RulesConfig(ruleset="cwn", confrontations=[_conf("opposed_check")])
    assert cfg.confrontations[0].resolution_mode == "opposed_check"
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `cd sidequest-server && uv run pytest tests/genre/test_fate_no_opposed_check.py -v`
Expected: `test_fate_pack_rejects_opposed_check` FAILS (no validator yet — `RulesConfig` accepts it).

- [ ] **Step 3: Add the validator to `RulesConfig`** (`sidequest/genre/models/rules.py`, alongside the existing `@model_validator(mode="after")` siblings ≈ line 1218+)

```python
    @model_validator(mode="after")
    def _fate_packs_have_no_opposed_check(self) -> RulesConfig:
        """spec 2026-06-17 §4 — the bleed tripwire. A Fate-bound pack must resolve
        its confrontations through Fate's own mechanics (Contest / Conflict), never
        the d20 dial's ``opposed_check``. Authoring one is a content error and fails
        pack load loudly (No Silent Fallbacks). The gate is ``ruleset == 'fate'``
        ONLY — the Without Number family (cwn/awn/swn/wwn) legitimately authors
        ``opposed_check`` via the shared dial engine and is untouched (spec §0)."""
        if self.ruleset != "fate":
            return self
        offenders = [
            c.confrontation_type
            for c in self.confrontations
            if c.resolution_mode == ResolutionMode.opposed_check
        ]
        if offenders:
            raise ValueError(
                f"Fate-bound pack authors opposed_check confrontation(s) {offenders!r}; "
                "a Fate pack resolves through the Contest mode (resolution_mode: "
                "contest) or a Conflict, never the d20 dial's opposed_check. See "
                "spec 2026-06-17 §3 for the Contest schema (ADR-144)."
            )
        return self
```

- [ ] **Step 4: Run the guardrail test + the converted-pack load (regression)**

Run:
```bash
cd sidequest-server && uv run pytest tests/genre/test_fate_no_opposed_check.py -v
uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/tea_and_murder
uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/spaghetti_western
```
Expected: tests PASS; both packs `PASS` (they were converted in Phase 3, so the new validator is satisfied).

- [ ] **Step 5: Lint + commit**

```bash
cd sidequest-server && uv run ruff check . && uv run ruff format .
git add -A && git commit -m "feat(genre): fail pack load when a Fate pack authors opposed_check (spec 2026-06-17 §4)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Scope the ADR-093 calibration test to the non-Fate (dial/WN) family

**Files:**
- Modify: `tests/genre/test_confrontation_calibration.py`

**Interfaces:**
- Produces: the calibration suite stays **green and non-vacuous**, now covering the WN family that keeps `opposed_check`. After Phase 3 the *only* pack with `opposed_check` defs is **road_warrior (cwn)** — so it must be in the covered set, or the threshold test passes vacuously for every pack.
- Background (verified): post-conversion `opposed_check` counts — tea_and_murder 0, spaghetti_western 0, road_warrior 2 (negotiation @ threshold **10**, chase @ threshold **7**), mutant_wasteland 0, space_opera 0, elemental_harmony 0, caverns_and_claudes 0. ADR-093 explicitly does **not** calibrate `negotiation` thresholds (see `test_negotiation_thresholds_not_collapsed_below_5`), so the threshold-7 rule must skip `negotiation`-type defs — otherwise road_warrior's intentional `10` would false-fail.

- [ ] **Step 1: Write the change as a test edit, then run red→green**

Edit `tests/genre/test_confrontation_calibration.py`:

(a) `SHIPPED_PACKS` — remove `tea_and_murder` (Fate, now scoped out), add `road_warrior` (the live `opposed_check` cwn pack):

```python
SHIPPED_PACKS = [
    "caverns_and_claudes",
    "elemental_harmony",
    "mutant_wasteland",
    "road_warrior",
    "space_opera",
]
```

(b) `COMBAT_PACKS` — make road_warrior the opposed_check existence tripwire (a WN-regression guard: if someone later converts road_warrior's opposed_check away, this fails loudly):

```python
COMBAT_PACKS: list[str] = ["road_warrior"]
```

(c) `test_opposed_check_thresholds_calibrated_to_7` — skip `negotiation` (ADR-093 leaves negotiation thresholds alone; the ≥5 test owns them):

```python
    for cdef in confrontations:
        ctype = cdef.get("type", "<unknown>")
        if cdef.get("resolution_mode") != OPPOSED_CHECK_MODE:
            continue
        # ADR-093 calibrates combat/chase opposed_checks to 7 but explicitly does
        # NOT touch negotiation thresholds (see test_negotiation_thresholds_*).
        # road_warrior's negotiation is opposed_check @ 10 by design (spec 2026-06-17 §5).
        if ctype == "negotiation":
            continue
        for side in ("player_metric", "opponent_metric"):
            metric = cdef.get(side, {})
            threshold = metric.get("threshold")
            if threshold != CALIBRATED_THRESHOLD:
                offending.append((ctype, side, threshold))
```

(d) Replace the stale module docstring + the long `COMBAT_PACKS` comment block that claims tea_and_murder/mutant_wasteland are "social-only ... no opposed_check ... pass trivially." After Phase 3 the accurate statement is: *Fate packs (tea_and_murder, spaghetti_western) are scoped OUT of ADR-093 — they resolve via the Contest mode and carry zero `opposed_check`. The dial/WN family keeps `opposed_check`; road_warrior (cwn) is the live exemplar and the existence tripwire.* Write that as the new docstring/comments (remove the per-pack "migrated to hp_depletion" paragraphs that no longer explain the active coverage).

- [ ] **Step 2: Run the calibration suite**

Run: `cd sidequest-server && uv run pytest tests/genre/test_confrontation_calibration.py -v`
Expected: all PASS, and `test_combat_pack_exposes_at_least_one_opposed_check_confrontation[road_warrior]` PASSES (road_warrior has 2 opposed_check defs) — proving the WN `opposed_check`→dial path is intact and the suite is non-vacuous.

- [ ] **Step 3: Commit**

```bash
cd sidequest-server
git add tests/genre/test_confrontation_calibration.py
git commit -m "test(calibration): scope ADR-093 to the dial/WN family; cover road_warrior, drop Fate (spec 2026-06-17 §3/§5)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: No-bleed integration test — a Fate contest turn fires `fate.contest.*` and zero `dial`/`compute_dc`

**Files:**
- Modify: `tests/server/dispatch/test_fate_contest.py` (add the integration case)

**Interfaces:**
- Consumes: a seated tea_and_murder-style contest, `dispatch_fate_action`, an `InMemorySpanExporter`.
- Produces: the §0 proof — driving a full contest exchange emits `fate.contest.exchange` (and `fate.contest.resolved` when it ends) and emits **no** dial-engine span (`*.compute_dc`, dial DC) and never calls `get_ruleset_module("dial")`/`"native"`. Span-driven, not source-grep (CLAUDE.md No-Source-Text-Wiring-Tests).

- [ ] **Step 1: Write the integration test** (append to `tests/server/dispatch/test_fate_contest.py`)

```python
def test_contest_turn_fires_contest_spans_and_no_dial(monkeypatch):
    """spec §0/§5 no-bleed proof: a Fate contest exchange resolves through the
    Contest engine — fate.contest.* spans fire and the dial engine is never
    reached (no get_ruleset_module('dial'/'native') call during the turn)."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    import sidequest.game.ruleset as ruleset_pkg

    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("nobleed")

    # Tripwire: fail if anything resolves the dial engine during the turn.
    real_get = ruleset_pkg.get_ruleset_module

    def _guarded_get(slug):
        assert slug not in ("dial", "native"), (
            f"dial engine reached on a Fate contest path (slug={slug!r}) — the bleed "
            "the spec closes (spec 2026-06-17 §0)"
        )
        return real_get(slug)

    monkeypatch.setattr(ruleset_pkg, "get_ruleset_module", _guarded_get)

    enc = _contest_encounter()
    enc.contest = ContestState(target=3, player_victories=2)  # one win ends it
    snap = _snapshot(enc)
    result = dispatch_fate_action(
        payload=_payload("overcome"), actor_name="Lady Ash", encounter=enc,
        ruleset=get_ruleset_module("fate"), snapshot=snap, rng=_ZeroDice(), _tracer=tracer,
    )
    names = {s.name for s in exporter.get_finished_spans()}
    assert "fate.contest.exchange" in names
    assert result.resolved is True and "fate.contest.resolved" in names
    assert not any(".compute_dc" in n or n.endswith(".dial") for n in names)
```

> Note: `dispatch_fate_action` must thread `_tracer` to the contest engine (it already accepts `_tracer`; verify the contest branch in Task 7 passes it — it does). If `get_ruleset_module` is imported into the dispatch module by name rather than module-qualified, patch it where it is *looked up* instead (adjust the `monkeypatch.setattr` target accordingly).

- [ ] **Step 2: Run it**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_contest.py -k no_dial -v`
Expected: PASS — contest spans present, no dial span, no dial-module resolution during the turn.

- [ ] **Step 3: Run the whole server suite (final regression gate)**

Run: `cd sidequest-server && uv run pytest -q && uv run ruff check . && uv run pyright`
Expected: PASS / clean.

- [ ] **Step 4: Commit**

```bash
cd sidequest-server
git add tests/server/dispatch/test_fate_contest.py
git commit -m "test(fate): no-bleed integration — contest turn fires fate.contest.*, never the dial (spec 2026-06-17 §0/§5)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

# Phase 5 — Docs / ADR

### Task 13: Amend ADR-144, note ADR-093 scope, record the ADR-033 rename

**Files:**
- Modify: `docs/adr/0144-*.md` (Fate Core binding) — add the Contest mode
- Modify: `docs/adr/0093-*.md` (opposed_check calibration) — scope note
- Modify: `docs/adr/0033-*.md` (the dial engine) — record `native`→`dial` rename
- Run: `scripts/regenerate_adr_indexes.py`

- [ ] **Step 1: ADR-144 amendment**

Add an "Amendment 2026-06-17 — Contests" section: the Fate binding now includes the Contest mode (opposed 4dF, first-to-N victories, tie→boost). Fate-pack confrontations resolve as Contests (or Conflicts), never `opposed_check`. The Contest engine is `fate_contest.py`, selected by `encounter.contest` (stamped from `resolution_mode: contest`). Spans: `fate.contest.{seeded,exchange,resolved}`.

- [ ] **Step 2: ADR-093 scope note**

Add: opposed_check calibration is scoped to the **dial/WN family**. Fate packs carry zero `opposed_check` (they use Contests); `tests/genre/test_confrontation_calibration.py` now covers road_warrior (cwn) as the live exemplar.

- [ ] **Step 3: ADR-033 rename note**

Add: `NativeRulesetModule`→`DialRulesetModule`, slug `native`→`dial` (the honest name for the shared d20 dial/beat/contest engine the WN family delegates `compute_dc` to). Pure rename, no resolution change.

- [ ] **Step 4: Regenerate indexes + sanity-check**

Run:
```bash
cd /Users/slabgorb/Projects/oq-1 && python scripts/regenerate_adr_indexes.py
git -C . diff --stat
```
Expected: ADR index files regenerate without unrelated churn.

- [ ] **Step 5: Commit (orchestrator repo)**

```bash
cd /Users/slabgorb/Projects/oq-1
git add docs/adr/
git commit -m "docs(adr): ADR-144 Contests; ADR-093 dial/WN scope; ADR-033 native->dial rename (spec 2026-06-17)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**1. Spec coverage:**

| Spec section | Task(s) |
|---|---|
| §1 Rename `native`→`dial` | Task 1 |
| §1 Fail-loud the three fallbacks | Task 2 |
| §2 Fate Contest engine | Tasks 3 (model), 4 (spans), 5 (engine), 6 (seating), 7 (dispatch) |
| §3 Re-author opposed_check → Contest | Tasks 8 (tea_and_murder ×4), 9 (spaghetti_western ×1) |
| §3 ADR-093 scoped to non-Fate | Task 11 |
| §4 Guardrail validator | Task 10 |
| §5 WN regression guard | Tasks 1 (dial resolves/native raises), 11 (road_warrior calibration green) |
| §5 Fate Contest behavior tests | Task 5 (victory/margin/first-to-3/tie→boost) |
| §5 Validator test | Task 10 |
| §5 No-bleed integration | Task 12 |
| §6 Docs/ADR | Task 13 |
| §2/§5 OTEL `fate.contest.*` | Tasks 4, 5, 6 |

All spec sections map to a task. The §7 non-goals are respected: WN resolution is gated out of every change (§0 invariant baked into Global Constraints; Task 1/2 are pure rename+fail-loud; Task 10's validator gates on `ruleset == "fate"`); the dial engine is renamed, not deleted; `fate_conflict.py` stress/consequence behavior is untouched (Task 7 only *branches around* it); no new UI screen (Contest reuses the FATE_ACTION surface).

**2. Placeholder scan:** Task 6's seating wiring test and Task 11's docstring-rewrite are the only steps that reference an existing fixture/comment-prose rather than inlining literal new code, because the exact seating fixture and the prose are local to files the implementer will have open; the *assertions* and the *recipe* are fully specified. All code-bearing steps contain complete code.

**3. Type consistency:** `ContestState`/`StructuredEncounter.contest` (Task 3) are used identically in Tasks 5/6/7. `run_fate_contest_exchange` and `FateContestResult` signatures match between Task 5 (definition) and Task 7 (consumer). `fate_contest_{seeded,exchange,resolved}_span` keyword params match between Task 4 (definition), Task 5 (exchange/resolved), and Task 6 (seeded). `ResolutionMode.contest` is added in Task 3 and consumed in Tasks 6/10. The conversion recipe's `threshold: 3` is consistent with `ContestState(target=cdef.player_metric.threshold)` in Task 6 and the `MetricDef` `threshold > starting` rule flagged in Tasks 8/9.

## Key design decision (flag for the executor)

The spec says "the confrontation def's `resolution_mode` selects contest vs conflict," but the existing Fate Conflict engine is **not** selected by `resolution_mode` — it is gated by `isinstance(ruleset, FateRulesetModule)` in `dispatch_fate_action`, bypassing the `resolution_mode` chain entirely. This plan reconciles the two: the seated encounter is **stamped** with a `ContestState` derived from `cdef.resolution_mode == contest` (Task 6), and `dispatch_fate_action` branches conflict-vs-contest on that stamp (Task 7). This honors both "resolution_mode selects contest vs conflict" *and* "Contests reuse the FATE_ACTION surface." `create_advantage`-during-a-contest (place an aspect, forgo scoring) is deferred as a fast-follow; aspect *invokes* already carry over natively via the shared dispatch seal.
