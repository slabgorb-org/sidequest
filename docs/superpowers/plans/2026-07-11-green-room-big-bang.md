# Green Room Big-Bang Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ADR-156 (accepted 2026-07-11, Amendments A+B) as one branch: a single-gate NPC materializer (`GreenRoom.admit`), all production spawn paths routed through it, the opponent-seater made target-first with the 108-2 conscription deleted, attach-before-mint in the mention paths, and the three 166-5 playtest repros as regression fixtures.

**Architecture:** A new pure module `sidequest/game/green_room.py` owns the origin-precedence ladder and the idempotent `admit()` gate, reusing 162-2's `Origin`/`identity_key`/`resolve_roster_npc` unchanged. Every production `snapshot.npcs.append` routes through `admit()`. The seater seats the dispatch's named target (authoritative per Amendment A); an unresolvable name flows to the existing 162-3 generics/frame backing (already seats under the router's name — verified at `encounter_lifecycle.py:512-523`). `_resolve_opponent_from_roster` and its five decline gates are deleted.

**Tech Stack:** Python 3.12 / pydantic v2 / pytest (`uv run pytest`, xdist default) / ruff / pyright. Spec: `docs/superpowers/specs/2026-07-11-green-room-implementation-design.md`. ADR: `docs/adr/156-green-room-npc-origin-precedence.md`.

## Global Constraints

- Repo: **sidequest-server** unless stated; branch **`feat/green-room`** off `develop`; all task commits land on that one branch; ONE PR to `develop` at the end (Keith's big-bang call). Understudy work is a separate small PR in sidequest-understudy gated on the server merge.
- **No Silent Fallbacks** — a candidate with an unknown/stub origin kind raises; nothing half-seated (162-3 rollback contract preserved).
- **No Source-Text Wiring Tests** — wiring is proven by OTEL span assertions and fixture-driven behavior tests only (server CLAUDE.md).
- **OTEL on every arbitration decision** — the `green_room.*` span family (spec §3.5), registered like `telemetry/spans/npc.py`'s `SPAN_IDENTITY_RESOLVED`.
- Test commands: `uv run pytest <path> -v` (add `-n0` when debugging); gates: `uv run ruff check . && uv run ruff format --check . && uv run pyright`.
- Existing tests that pin the conscription (`tests/server/test_opponent_roster_resolution.py` and the 150-2/153-9/153-10 decline tests) are **deleted with their code**, never skipped.
- Reuse, don't reinvent: `Origin`, `OriginKind`, `identity_key`, `normalize_name`, `resolve_roster_npc` (`sidequest/game/origin.py`) are the identity substrate — extend only where a task says so.

---

### Task 1: The ladder, `identity_key` GENERIC fix, and `GreenRoom.admit()`

**Files:**
- Create: `sidequest/game/green_room.py`
- Create: `sidequest/telemetry/spans/green_room.py`
- Modify: `sidequest/game/origin.py:93-106` (`identity_key` — GENERIC keys by name)
- Modify: `sidequest/telemetry/spans/__init__.py` (export the new span names, mirroring how `npc.py` names are exported)
- Test: `tests/game/test_green_room_admit.py`, extend `tests/game/test_162_2_origin_model.py`

**Interfaces:**
- Consumes: `Origin`, `OriginKind`, `identity_key`, `derive_origin`, `normalize_name`, `resolve_roster_npc` from `sidequest.game.origin`; `Npc`, `GameSnapshot` from `sidequest.game.session`.
- Produces (later tasks import these exact names from `sidequest.game.green_room`):
  - `LADDER: dict[OriginKind, int]`
  - `@dataclass MaterializationCandidate(npc: Npc, origin: Origin, source: str, aliases: tuple[str, ...] = ())`
  - `@dataclass AdmitResult(admitted: list[Npc], merged: list[str], aliases_attached: int, dropped: list[str])`
  - `def admit(snapshot: GameSnapshot, candidates: Sequence[MaterializationCandidate]) -> AdmitResult`
  - `def attach_alias(npc: Npc, alias: str, *, from_source: str) -> bool` (dedup + span; returns True if newly attached)

- [ ] **Step 1: Read the span-registration pattern**

Read `sidequest/telemetry/spans/npc.py:50-70` (the `SPAN_IDENTITY_RESOLVED` + `SPAN_ROUTES[...] = SpanRoute(...)` shape) and `sidequest/telemetry/spans/_core.py` for `SpanRoute`'s constructor. The new file in Step 4 mirrors that registration shape exactly — same import style, same route fields.

- [ ] **Step 2: Write the failing tests**

`tests/game/test_green_room_admit.py` (fixtures build minimal `Npc` records the way `tests/server/test_162_2_identity_fork_seating.py` does — reuse its snapshot fixture helpers):

```python
"""Green Room admit() — ADR-156 §4: precedence, additive merge, idempotence."""

import pytest

from sidequest.game.green_room import (
    LADDER,
    AdmitResult,
    MaterializationCandidate,
    admit,
    attach_alias,
)
from sidequest.game.origin import Origin, OriginKind, identity_key
from sidequest.game.creature_core import CreatureCore, Inventory, hp_pool_from_hp
from sidequest.game.session import GameSnapshot, Npc


def _npc(name: str, *, hp: int = 10, creature_id: str | None = None,
         authored_id: str | None = None, kind: OriginKind = OriginKind.MANUAL_POOL) -> Npc:
    return Npc(
        core=CreatureCore(
            name=name, description="d", personality="p",
            inventory=Inventory(), hp=hp_pool_from_hp(hp), armor_class=10,
        ),
        creature_id=creature_id,
        origin=Origin(kind=kind, creature_id=creature_id, authored_id=authored_id),
    )


def _cand(npc: Npc, source: str = "test") -> MaterializationCandidate:
    assert npc.origin is not None
    return MaterializationCandidate(npc=npc, origin=npc.origin, source=source)


def test_ladder_ranks_match_adr_156() -> None:
    assert LADDER[OriginKind.AUTHORED] == 1
    assert LADDER[OriginKind.GENERIC] == 1          # authored content, ADR-156 §5
    assert LADDER[OriginKind.ROOM_BOUND] == 2
    assert LADDER[OriginKind.REGION_POPULATION] == 3
    assert LADDER[OriginKind.MANUAL_POOL] == 4
    assert LADDER[OriginKind.NARRATOR_INVENTED] == 5
    assert OriginKind.EPHEMERAL_STUB not in LADDER  # must never reach admit


def test_admit_appends_new_identity(snapshot: GameSnapshot) -> None:
    result = admit(snapshot, [_cand(_npc("Grazer", creature_id="grazer"))])
    assert [n.core.name for n in result.admitted] == ["Grazer"]
    assert any(n.core.name == "Grazer" for n in snapshot.npcs)


def test_same_identity_two_tiers_highest_wins_dropped_recorded(snapshot: GameSnapshot) -> None:
    authored = _npc("Molgrath", creature_id="thief",
                    authored_id="molgrath", kind=OriginKind.AUTHORED)
    pool = _npc("Molgrath", creature_id="thief", kind=OriginKind.MANUAL_POOL)
    result = admit(snapshot, [_cand(pool, "mm.encounters"), _cand(authored, "preload")])
    assert len(result.admitted) == 1
    seated = result.admitted[0]
    assert seated.origin is not None and seated.origin.kind == OriginKind.AUTHORED
    assert result.dropped == [identity_key(pool.origin, "Molgrath")]


def test_additive_merge_fills_absent_fields_only(snapshot: GameSnapshot) -> None:
    winner = _npc("Molgrath", authored_id="molgrath", kind=OriginKind.AUTHORED)
    winner.pronouns = None
    loser = _npc("Molgrath", authored_id="molgrath", kind=OriginKind.MANUAL_POOL)
    loser.pronouns = "he/him"
    loser.core.description = "SHOULD NOT OVERWRITE"
    admit(snapshot, [_cand(winner), _cand(loser)])
    seated = next(n for n in snapshot.npcs if n.core.name == "Molgrath")
    assert seated.pronouns == "he/him"            # absent → filled
    assert seated.core.description == "d"         # present → untouched


def test_idempotence_never_resets_live_state(snapshot: GameSnapshot) -> None:
    admit(snapshot, [_cand(_npc("Grazer", hp=8, creature_id="grazer"))])
    seated = next(n for n in snapshot.npcs if n.core.name == "Grazer")
    seated.core.apply_hp_delta(-5)                 # wounded in the fight
    seated.disposition.shift(-30)
    admit(snapshot, [_cand(_npc("Grazer", hp=8, creature_id="grazer"))])  # re-inject
    assert seated.core.hp.current == 3             # ADR-139 Inv-2, structural
    assert len([n for n in snapshot.npcs if n.core.name == "Grazer"]) == 1


def test_prose_name_lands_as_alias_not_identity(snapshot: GameSnapshot) -> None:
    bound = _npc("Thief", creature_id="thief")
    mint = _npc("Molgrath the Eyeless", creature_id="thief",
                kind=OriginKind.NARRATOR_INVENTED)
    result = admit(snapshot, [_cand(bound), _cand(mint)])
    assert len(result.admitted) == 1
    seated = result.admitted[0]
    assert seated.core.name == "Thief"
    assert "Molgrath the Eyeless" in seated.aliases


def test_stub_candidate_raises(snapshot: GameSnapshot) -> None:
    stub = _npc("Hold-Dead", kind=OriginKind.EPHEMERAL_STUB)
    with pytest.raises(ValueError, match="EPHEMERAL_STUB"):
        admit(snapshot, [_cand(stub)])


def test_attach_alias_dedups(snapshot: GameSnapshot) -> None:
    npc = _npc("Thief", creature_id="thief")
    assert attach_alias(npc, "Molgrath the Eyeless", from_source="test") is True
    assert attach_alias(npc, "molgrath the eyeless", from_source="test") is False
    assert npc.aliases == ["Molgrath the Eyeless"]
```

Extend `tests/game/test_162_2_origin_model.py`:

```python
def test_identity_key_generic_kind_keys_by_name() -> None:
    """A generics row is a stat DONOR, not an identity (Amendment B): two
    named persons backed by the same row must not collide on the row id."""
    from sidequest.game.origin import Origin, OriginKind, identity_key
    g = Origin(kind=OriginKind.GENERIC, creature_id="wasteland_scavenger")
    assert identity_key(g, "the Scrapborn") == "name:the scrapborn"
    assert identity_key(g, "the courier") == "name:the courier"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/game/test_green_room_admit.py tests/game/test_162_2_origin_model.py -v -n0`
Expected: FAIL — `ModuleNotFoundError: sidequest.game.green_room` and the GENERIC key test failing with `creature:wasteland_scavenger`.

- [ ] **Step 4: Implement**

`sidequest/telemetry/spans/green_room.py` — mirror `npc.py`'s registration shape (from Step 1) for four spans with these names and attribute keys:

- `green_room.materialized` — `{identity_key, canonical_tier, canonical_source, candidates_seen, candidates_dropped, alias_count}`
- `green_room.precedence_conflict` — `{identity_key, winning_tier, losing_tiers}`
- `green_room.alias_attached` — `{identity_key, alias, from_source}`
- `green_room.mint` — `{identity_key, prose_name, source}`

`sidequest/game/origin.py` — in `identity_key`, GENERIC keys by name:

```python
def identity_key(origin: Origin | None, display_name: str) -> str:
    if origin is not None and origin.kind is not OriginKind.GENERIC:
        if origin.authored_id:
            return f"authored:{origin.authored_id}"
        if origin.creature_id:
            return f"creature:{origin.creature_id}"
    elif origin is not None and origin.authored_id:
        return f"authored:{origin.authored_id}"
    return f"name:{normalize_name(display_name)}"
```

(A GENERIC row *with* an authored_id still keys authored — the generics rows are authored content; only the donor `creature_id` is excluded from identity. Update the docstring to say so.)

`sidequest/game/green_room.py`:

```python
"""The Green Room — ADR-156's single-gate NPC materializer (accepted 2026-07-11).

One door onto the stage: every production path that lands an ``Npc`` in
``snapshot.npcs`` routes through :func:`admit`. The ladder arbitrates
IDENTITY (which record is real when feeders collide); it never picks
confrontation targets — that is Amendment A's line (targeting is the
dispatch's named target, `encounter_lifecycle`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from sidequest.game.origin import (
    Origin,
    OriginKind,
    derive_origin,
    identity_key,
    normalize_name,
)

LADDER: dict[OriginKind, int] = {
    OriginKind.AUTHORED: 1,
    OriginKind.GENERIC: 1,
    OriginKind.ROOM_BOUND: 2,
    OriginKind.REGION_POPULATION: 3,
    OriginKind.MANUAL_POOL: 4,
    OriginKind.NARRATOR_INVENTED: 5,
}
# EPHEMERAL_STUB is deliberately absent: a stub reaching the gate is a
# construction error (162-3 made stub-mint a loud failure) — admit() raises.


@dataclass
class MaterializationCandidate:
    npc: "Npc"
    origin: Origin
    source: str
    aliases: tuple[str, ...] = ()


@dataclass
class AdmitResult:
    admitted: list["Npc"] = field(default_factory=list)
    merged: list[str] = field(default_factory=list)
    aliases_attached: int = 0
    dropped: list[str] = field(default_factory=list)


# The live mechanical state admit() must NEVER reset on an already-
# materialized identity (ADR-139 Invariant 2, now structural):
# core.hp, disposition, belief_state, disposition_log, last_seen_location,
# last_seen_turn, non_transactional_interactions, last_development_turn.

_MERGE_FILL_FIELDS = (
    "pronouns", "appearance", "age", "build", "height",
    "location", "region", "current_room", "threat_level",
    "jungian_id", "rpg_role_id", "npc_role_id",
)


def attach_alias(npc: "Npc", alias: str, *, from_source: str) -> bool:
    """Record a prose/stage name against an identity. Dedups against the
    canonical name and existing aliases via normalize_name. Emits
    green_room.alias_attached on a NEW attachment only."""
    q = normalize_name(alias)
    if not q or q == normalize_name(npc.core.name):
        return False
    if any(normalize_name(a) == q for a in npc.aliases):
        return False
    npc.aliases.append(alias)
    from sidequest.telemetry.spans import SPAN_GREEN_ROOM_ALIAS_ATTACHED, Span

    with Span.open(
        SPAN_GREEN_ROOM_ALIAS_ATTACHED,
        {
            "identity_key": identity_key(derive_origin(npc), npc.core.name),
            "alias": alias,
            "from_source": from_source,
        },
    ):
        pass
    return True


def _fill_absent(winner: "Npc", donor: "Npc") -> None:
    """Additive merge: donor fills the winner's ABSENT fields only."""
    for f in _MERGE_FILL_FIELDS:
        if getattr(winner, f, None) is None and getattr(donor, f, None) is not None:
            setattr(winner, f, getattr(donor, f))
    for df in donor.distinguishing_features:
        if df not in winner.distinguishing_features:
            winner.distinguishing_features.append(df)


def admit(
    snapshot: "GameSnapshot", candidates: Sequence[MaterializationCandidate]
) -> AdmitResult:
    from sidequest.telemetry.spans import (
        SPAN_GREEN_ROOM_MATERIALIZED,
        SPAN_GREEN_ROOM_PRECEDENCE_CONFLICT,
        Span,
    )

    result = AdmitResult()
    groups: dict[str, list[MaterializationCandidate]] = {}
    for cand in candidates:
        if cand.origin.kind not in LADDER:
            raise ValueError(
                f"green_room.admit: candidate {cand.npc.core.name!r} carries "
                f"unadmittable origin kind {cand.origin.kind} "
                f"(EPHEMERAL_STUB and unknown kinds never reach the gate — "
                f"No Silent Fallbacks)"
            )
        groups.setdefault(identity_key(cand.origin, cand.npc.core.name), []).append(cand)

    for key, group in groups.items():
        group.sort(key=lambda c: (LADDER[c.origin.kind], c.source))
        canonical = group[0]
        if len(group) > 1:
            with Span.open(
                SPAN_GREEN_ROOM_PRECEDENCE_CONFLICT,
                {
                    "identity_key": key,
                    "winning_tier": LADDER[canonical.origin.kind],
                    "losing_tiers": sorted({LADDER[c.origin.kind] for c in group[1:]}),
                },
            ):
                pass
        alias_count = 0
        for loser in group[1:]:
            _fill_absent(canonical.npc, loser.npc)
            if attach_alias(canonical.npc, loser.npc.core.name, from_source=loser.source):
                alias_count += 1
            result.dropped.append(identity_key(loser.origin, loser.npc.core.name))
        for extra in canonical.aliases:
            if attach_alias(canonical.npc, extra, from_source=canonical.source):
                alias_count += 1

        existing = _find_existing(snapshot, key, canonical.npc.core.name)
        if existing is not None:
            _fill_absent(existing, canonical.npc)
            if attach_alias(existing, canonical.npc.core.name, from_source=canonical.source):
                alias_count += 1
            for a in canonical.npc.aliases:
                if attach_alias(existing, a, from_source=canonical.source):
                    alias_count += 1
            result.merged.append(key)
        else:
            canonical.npc.origin = canonical.origin
            snapshot.npcs.append(canonical.npc)
            result.admitted.append(canonical.npc)
        result.aliases_attached += alias_count

        with Span.open(
            SPAN_GREEN_ROOM_MATERIALIZED,
            {
                "identity_key": key,
                "canonical_tier": LADDER[canonical.origin.kind],
                "canonical_source": canonical.source,
                "candidates_seen": len(group),
                "candidates_dropped": len(group) - 1,
                "alias_count": alias_count,
            },
        ):
            pass
    return result


def _find_existing(snapshot: "GameSnapshot", key: str, name: str) -> "Npc | None":
    """Reconcile by identity key first (id-keyed), then by the resolver's
    name/alias/invented_from legs (catches a legacy unstamped entity whose
    derived key differs)."""
    for npc in snapshot.npcs:
        if identity_key(derive_origin(npc), npc.core.name) == key:
            return npc
    from sidequest.game.origin import resolve_roster_npc

    return resolve_roster_npc(snapshot.npcs, name)
```

(`Npc`/`GameSnapshot` imports are `TYPE_CHECKING`-only, same cycle-avoidance pattern as `origin.py:33-37`.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/game/test_green_room_admit.py tests/game/test_162_2_origin_model.py -v -n0`
Expected: PASS (all).

- [ ] **Step 6: Gates + commit**

Run: `uv run ruff check sidequest/game/green_room.py sidequest/telemetry/spans/green_room.py && uv run pyright sidequest/game/green_room.py`
Expected: clean.

```bash
git checkout -b feat/green-room develop
git add sidequest/game/green_room.py sidequest/telemetry/spans/green_room.py \
        sidequest/game/origin.py sidequest/telemetry/spans/__init__.py \
        tests/game/test_green_room_admit.py tests/game/test_162_2_origin_model.py
git commit -m "feat(green-room): admit() gate — ladder, additive merge, idempotence, alias attach (ADR-156 §4)"
```

---

### Task 2: MM injection feeds candidates through the gate

**Files:**
- Modify: `sidequest/server/dispatch/monster_manual_inject.py` — `inject()` (:745, application section after the patch collection at :800-880) and the four patch builders (`_npc_patches_for_available_humans` :351, `_npc_patches_for_encounters` :492, `_npc_patches_for_region_population` :669, `_npc_patches_for_room_binding` :710)
- Test: `tests/server/test_green_room_mm_feeders.py`

**Interfaces:**
- Consumes: `admit`, `MaterializationCandidate` (Task 1); existing `NpcPatch` builders unchanged in shape.
- Produces: `inject()` return contract unchanged (count of patches applied) so `websocket_session_handler.py:862` needs no edit. Feeder source labels (used by tests and the GM panel): `"mm.available_humans"`, `"mm.encounters"`, `"mm.room_binding"`, `"mm.region_population"`, `"preload_authored"` (Task 3), `"zone_cast"` (Task 3), `"router_opponent"` (Task 4), `"narrator_mention"`/`"prose_extraction"` (Task 5).

- [ ] **Step 1: Read the application seam**

Read `monster_manual_inject.py:880-960` (after the collection block quoted in the spec) to find where `all_patches` + room-binding + region-population patches are applied to `snapshot` (the `_merge_npc_patch`/append loop or `snapshot.apply_*` call). Also confirm how `_npc_patches_for_available_humans` marks authored-backfill entries (the manual's authored rows) vs pregen — grep `authored` within :351-490. Record both findings in the test file's docstring.

- [ ] **Step 2: Write the failing test**

```python
"""MM injection routes through GreenRoom.admit — one identity per creature
regardless of which builders propose it (ADR-156 feeders 1-4)."""

def test_inject_routes_through_admit_spans(mm_session_fixture, span_recorder) -> None:
    # mm_session_fixture: a _SessionData + snapshot with a Manual holding one
    # pregen human, one encounter creature, a room-bound bestiary ref, and a
    # region-population creature for the current room — build it the way
    # tests/server/test_162_7_all_sources_one_scene.py stages its manual.
    from sidequest.server.dispatch import monster_manual_inject

    count = monster_manual_inject.inject(
        mm_session_fixture.sd,
        mm_session_fixture.snapshot,
        current_location="Salt Camp",
        in_combat=False,
        room_id="toods_dome",
    )
    assert count >= 4
    materialized = [s for s in span_recorder if s.name == "green_room.materialized"]
    assert len(materialized) >= 4
    sources = {s.attrs["canonical_source"] for s in materialized}
    assert {"mm.available_humans", "mm.encounters",
            "mm.room_binding", "mm.region_population"} <= sources


def test_reinject_preserves_wounded_hp(mm_session_fixture) -> None:
    """The ADR-139 Inv-2 carve-out is now structural: re-injection on a later
    turn must not heal a wounded creature."""
    from sidequest.server.dispatch import monster_manual_inject

    snap = mm_session_fixture.snapshot
    monster_manual_inject.inject(mm_session_fixture.sd, snap,
                                 current_location="Salt Camp", in_combat=True)
    creature = next(n for n in snap.npcs if n.manual_origin or
                    (n.origin and n.origin.kind.value == "manual_pool"))
    creature.core.apply_hp_delta(-3)
    hp_after_wound = creature.core.hp.current
    monster_manual_inject.inject(mm_session_fixture.sd, snap,
                                 current_location="Salt Camp", in_combat=True)
    assert creature.core.hp.current == hp_after_wound
    assert len([n for n in snap.npcs if n.core.name == creature.core.name]) == 1
```

(`span_recorder` — reuse the existing span-capture fixture the 162-2 tests use; grep `SPAN_IDENTITY_RESOLVED` under `tests/` for its name and import it rather than writing a new one.)

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/server/test_green_room_mm_feeders.py -v -n0`
Expected: FAIL — no `green_room.materialized` spans (patches still applied via the legacy merge loop).

- [ ] **Step 4: Implement**

In `inject()`, replace the patch-application seam found in Step 1: build each applied patch into an `Npc` (the same construction the legacy path used — `GameSnapshot._npc_from_patch` or its local equivalent), wrap in `MaterializationCandidate` with the kind each builder already implies, and make ONE `admit()` call per `inject()`:

```python
from sidequest.game.green_room import MaterializationCandidate, admit
from sidequest.game.origin import Origin, OriginKind

def _candidate(npc, *, kind, source, creature_id=None, authored_id=None):
    return MaterializationCandidate(
        npc=npc,
        origin=Origin(kind=kind, creature_id=creature_id, authored_id=authored_id),
        source=source,
    )
```

Kind mapping (from Step 1's authored-marker finding): available-humans authored-backfill rows → `AUTHORED` + `authored_id`; available-humans pregen rows → `MANUAL_POOL`; encounters → `MANUAL_POOL` + `creature_id`; room-binding → `ROOM_BOUND` + `creature_id`; region-population → `REGION_POPULATION` + `creature_id` (keep stamping `npc.region`, which `derive_origin` relies on for legacy saves). The function's return value becomes `len(result.admitted) + len(result.merged)`. Delete the now-unreachable legacy merge/append lines in this seam — nothing else appends MM entries.

- [ ] **Step 5: Run task tests + the existing MM suite**

Run: `uv run pytest tests/server/test_green_room_mm_feeders.py tests/server -k "monster_manual or inject" -v`
Expected: task tests PASS; existing MM tests PASS (idempotent merge semantics preserved — any existing test asserting description-overwrite on re-inject changes to assert fill-absent, listed in the commit body).

- [ ] **Step 6: Commit**

```bash
git add sidequest/server/dispatch/monster_manual_inject.py tests/server/test_green_room_mm_feeders.py
git commit -m "feat(green-room): MM injection's four builders feed admit() (feeders 1-4)"
```

---

### Task 3: Authored preload, zone-cast promotion, and the seeder/promotion appends route through the gate

**Files:**
- Modify: `sidequest/game/world_materialization.py:543` and `:953` (the two authored appends)
- Modify: `sidequest/server/narration_apply.py:1567` and `:1720` (pool→npcs promotion appends)
- Modify: `sidequest/server/dispatch/encounter_lifecycle.py:465, :525, :567, :797, :816` (seeder appends: pool promotion, generics seat, frame/stub seat, Fate seeder pair)
- Test: `tests/server/test_green_room_append_sites.py`

**Interfaces:**
- Consumes: `admit`, `MaterializationCandidate`, `attach_alias` (Task 1).
- Produces: **zero** direct `snapshot.npcs.append(...)` in production code (spec §5 "done" criterion). The 162-3 generics seat keeps `Origin(kind=GENERIC, creature_id=row.id)` (`encounter_lifecycle.py:523`) — Task 1's `identity_key` change already makes it name-keyed.

- [ ] **Step 1: Write the failing test**

```python
"""Every production append routes through admit() — proven by behavior,
not source text: each path fires green_room.materialized with its source."""

def test_authored_preload_admits(world_fixture, span_recorder) -> None:
    # Drive preload_authored_npcs (world_materialization.py:825) with a
    # 1-NPC authored world fixture (reuse the fixture pack from
    # tests/game/test_world_materialization.py).
    ...
    assert any(s.attrs["canonical_source"] == "preload_authored"
               and s.attrs["canonical_tier"] == 1 for s in span_recorder
               if s.name == "green_room.materialized")


def test_generics_seat_admits_under_router_name(confrontation_fixture, span_recorder) -> None:
    # Drive instantiate_encounter_from_trigger with a materialized_threat
    # naming an unknown person and a pack whose bestiary has one generics row
    # (stage it the way tests/server/test_162_3_generics_last_resort.py does).
    ...
    spans = [s for s in span_recorder if s.name == "green_room.materialized"]
    assert any(s.attrs["canonical_source"] == "seeder.generics" for s in spans)
    seated = confrontation_fixture.snapshot.encounter.actors
    opponent = next(a for a in seated if a.side == "opponent")
    assert opponent.name == "the Scrapborn"       # identity = the named person
```

(Complete the `...` bodies by copying the drive-and-assert shape from the two named existing test files — same fixtures, same invocation, new span assertions. They are cited by exact path so the implementer lifts real code, not invented code.)

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/server/test_green_room_append_sites.py -v -n0`
Expected: FAIL — no `green_room.materialized` spans from these paths.

- [ ] **Step 3: Implement — one mechanical transform per site**

At each of the nine anchors, replace `snapshot.npcs.append(npc)` (and `snap.npcs.append(...)` / `state.npcs.append(runtime)`) with:

```python
from sidequest.game.green_room import MaterializationCandidate, admit
from sidequest.game.origin import Origin, OriginKind

admit(snapshot, [MaterializationCandidate(
    npc=npc,
    origin=npc.origin or Origin(kind=<kind for this site>, creature_id=npc.creature_id),
    source="<site label>",
)])
```

Site → (kind, source): world_materialization :543 → (`AUTHORED` + `authored_id`, `"preload_authored"`); :953 → (`AUTHORED` + `authored_id`, `"worldbuilder_history"`); narration_apply :1567 → (`NARRATOR_INVENTED`, `"pool_promotion"`); :1720 → (`NARRATOR_INVENTED`, `"pool_promotion"`); encounter_lifecycle :465 → (`NARRATOR_INVENTED`, `"seeder.pool_promotion"`); :525 → (existing stamped `Origin(kind=GENERIC, ...)`, `"seeder.generics"`); :567 → (`EPHEMERAL_STUB` path — **do not route through admit**; this is the `allow_synthetic_opponent` degenerate opt-in, which stays a direct append with its warning span, unchanged); :797/:816 → Fate seeder (mirror :465/:525 kinds, sources `"fate_seeder.pool_promotion"` / `"fate_seeder.frame"`). Where the site already canonicalizes the seat name after append (e.g. :474), keep that logic operating on the admitted record (`result.admitted[0]` or the merged existing via `resolve_roster_npc`).

- [ ] **Step 4: Run the full server suite**

Run: `uv run pytest tests/ -x -q`
Expected: PASS. Any failure here is a real semantic regression in a converted site — fix the conversion, not the test (exception: a test asserting duplicate-append behavior that admit now correctly dedups; list any such change in the commit body).

- [ ] **Step 5: Verify zero production appends remain**

Run: `grep -rn "npcs\.append" sidequest/ --include="*.py" | grep -v tests`
Expected: only `encounter_lifecycle.py:567` (the degenerate `allow_synthetic_opponent` opt-in) and non-`snapshot.npcs` list appends. This is a dev-time audit, not a shipped test (No Source-Text Wiring Tests applies to tests).

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/world_materialization.py sidequest/server/narration_apply.py \
        sidequest/server/dispatch/encounter_lifecycle.py tests/server/test_green_room_append_sites.py
git commit -m "feat(green-room): all production spawn paths feed admit() (feeders 5-7 + seeder seats)"
```

---

### Task 4: Target-first seater — delete the 108-2 conscription (Amendment A; this closes 166-5)

**Files:**
- Modify: `sidequest/server/dispatch/encounter_lifecycle.py` — delete `_resolve_opponent_from_roster` (:1313-1450) and its call inside the `materialized_threat` branch (:2071-2095); delete `_reconcile_surfaced_adversary` if its only caller was the conscription (verify with grep); keep the ADR-116 location fallback (:2111-2125) untouched
- Modify: `sidequest/telemetry/spans/encounter.py` — remove `encounter_opponent_resolved_from_roster_span` and `encounter_roster_resolution_skipped_span` definitions
- Delete: `tests/server/test_opponent_roster_resolution.py`; the 150-2/153-9/153-10 decline tests (locate: `grep -rln "roster_resolution_skipped\|opponent_resolved_from_roster" tests/`)
- Test: `tests/server/test_166_5_wrong_other_repros.py`

**Interfaces:**
- Consumes: `resolve_roster_npc` (unchanged); the 162-3 generics/frame backing downstream (unchanged, verified seats under the router name at `:512-523`).
- Produces: the `materialized_threat` branch contract — named target resolves via resolver → seat canonical (`seating_source="roster_resolved"`), else seat as named (`seating_source="materialized"`, backing seeded downstream). No third outcome exists.

- [ ] **Step 1: Write the failing repro tests (the three playtest cases)**

```python
"""166-5 wrong-Other repros as permanent fixtures. Fiction targets win seats.

Repro shapes from ~/Projects/sq-playtest-pingpong.md (2026-07-10) and the
parked coyote_star finding. Fixture style: synthetic pack + snapshot + real
instantiate_encounter_from_trigger, per tests/server/test_162_3_generics_last_resort.py.
"""


def test_salt_camp_brawl_seats_the_named_person_not_the_comob(combat_pack_with_generics) -> None:
    """Chico: router names an unmaterialized person; a co-located MANUAL_POOL
    bestiary creature exists. The person is seated; the herbivore is not."""
    snapshot = combat_pack_with_generics.snapshot
    grazer = mk_manual_pool_creature("Resonance Grazer", creature_id="resonance_grazer",
                                     location="Salt Camp", disposition=-20)
    admit(snapshot, [MaterializationCandidate(npc=grazer, origin=grazer.origin,
                                              source="mm.encounters")])
    enc = instantiate_encounter_from_trigger(
        snapshot=snapshot, pack=combat_pack_with_generics.pack,
        encounter_type="combat", player_name="Chico", npcs_present=[],
        genre_slug="mutant_wasteland",
        materialized_threat=NpcMention(name="the loudest Scrapborn",
                                       role="hostile", side="opponent"),
    )
    opponent = next(a for a in enc.actors if a.side == "opponent")
    assert opponent.name == "the loudest Scrapborn"
    assert all(a.name != "Resonance Grazer" for a in enc.actors)


def test_courier_grapple_same_shape_second_pack(wwn_pack_with_generics) -> None:
    """Groucho: identical shape, WWN pack, ghost-spirit co-located."""
    # Same drive as above with creature "Restless Battlefield Ghost" and
    # threat "the message courier"; assert the courier is seated.
    ...


def test_named_target_matching_roster_alias_seats_canonical(combat_pack_with_generics) -> None:
    """The conscription's one legitimate case survives its deletion: a
    router name that IS a recorded alias seats the bound creature."""
    snapshot = combat_pack_with_generics.snapshot
    thief = mk_manual_pool_creature("Thief", creature_id="thief", location="cavern")
    thief.aliases.append("Molgrath the Eyeless")
    admit(snapshot, [MaterializationCandidate(npc=thief, origin=thief.origin,
                                              source="mm.encounters")])
    enc = instantiate_encounter_from_trigger(
        snapshot=snapshot, pack=combat_pack_with_generics.pack,
        encounter_type="combat", player_name="Keth", npcs_present=[],
        genre_slug="caverns_and_claudes",
        materialized_threat=NpcMention(name="Molgrath the Eyeless",
                                       role="hostile", side="opponent"),
    )
    opponent = next(a for a in enc.actors if a.side == "opponent")
    assert opponent.name == "Thief"               # canonical, one identity


def test_ship_duel_frame_source_unaffected(sealed_letter_pack) -> None:
    """coyote_star shape: sealed-letter dogfight with no named contact still
    seats the def-frame Other (158-34 firewall intact), never a ground creature."""
    # Drive with a co-located personal-scale creature staged; assert the
    # seated opponent is the frame default (cdef.label), not the creature —
    # copy the drive from the 158-34 firewall test
    # (grep -rln "frame_default" tests/ for its file).
    ...
```

(The two `...` bodies are the same drive as the first test with the named substitutions; the ship-duel test copies the existing 158-34 firewall test's drive. Cited by exact greps so real code gets lifted.)

- [ ] **Step 2: Run to verify current failure**

Run: `uv run pytest tests/server/test_166_5_wrong_other_repros.py -v -n0`
Expected: `test_salt_camp_brawl...` and `test_courier_grapple...` FAIL with the co-located creature seated (the conscription firing). The alias and ship-duel tests PASS already (they pin behavior that must survive).

- [ ] **Step 3: Delete the conscription**

In the `materialized_threat` branch (:2071-2095), the block from `resolved_opponent = _resolve_opponent_from_roster(` through the `else: seating_source = "materialized"` collapses to:

```python
        seating_source = "roster_resolved" if known is not None else "materialized"
        npcs_present = [materialized_threat]
```

(The `known`/canonicalization block at :2064-2070 stays — it is the resolver leg, Amendment A step 2.) Delete `_resolve_opponent_from_roster` (:1313 through its end), the `encounter_opponent_resolved_from_roster_span` / `encounter_roster_resolution_skipped_span` imports and definitions, and `_reconcile_surfaced_adversary` **iff** `grep -n "_reconcile_surfaced_adversary" sidequest/` shows the conscription was its only caller. Delete the test files from the Files list. Update the module docstring paragraph that documents the six-strategy stack (:1241-1246 area) to describe the two-outcome contract.

- [ ] **Step 4: Run the repro tests + full suite**

Run: `uv run pytest tests/server/test_166_5_wrong_other_repros.py -v -n0 && uv run pytest tests/ -q`
Expected: all four repro tests PASS; full suite PASS (the deleted tests are gone, nothing else pinned the conscription — if something else fails, it was pinning guess behavior; delete or fix per its intent, recorded in the commit body).

- [ ] **Step 5: Commit**

```bash
git add -A sidequest/server/dispatch/encounter_lifecycle.py sidequest/telemetry/spans/encounter.py tests/
git commit -m "feat(green-room)!: target-first seater — delete the 108-2 conscription (Amendment A, closes 166-5)"
```

---

### Task 5: Attach-before-mint in the mention paths (Amendment B / ADR-156 §6)

**Files:**
- Modify: `sidequest/server/narration_apply.py` — `_apply_npc_mentions` (:2520), the novel-name mint branch (~:3213, was :3173 pre-Task-3 edits — re-anchor by grepping `narrator_invented` in the function) and the invented-name routing (`_generate_invented_name` consumer, the `npc.invented_name_routed` emit site)
- Modify: `sidequest/server/session_helpers.py` — `_auto_mint_prose_only_npcs` (:2104), before its `NpcPoolMember` construction
- Test: `tests/server/test_green_room_attach_before_mint.py`

**Interfaces:**
- Consumes: `attach_alias`, `resolve_roster_npc`.
- Produces: both mint branches share one preamble contract: *resolve → attach → only then mint*. The seated-Other attach rule (exact): an active `snapshot.encounter` with **exactly one** live `side="opponent"` actor whose resolved `Npc.origin.kind` is `GENERIC` or `NARRATOR_INVENTED` and whose `aliases` list is empty is the attachment target for a mention whose `role`/`side` marks it hostile.

- [ ] **Step 1: Write the failing tests**

```python
def test_prose_name_attaches_to_roster_before_minting(narration_fixture) -> None:
    """A mention resolving via resolve_roster_npc (any leg) attaches as an
    alias; no NpcPoolMember is created."""
    snap = narration_fixture.snapshot
    seed_npc(snap, "Thief", creature_id="thief")
    pool_before = len(snap.npc_pool)
    apply_mentions(narration_fixture, mentions=[mention("the Thief")])
    assert len(snap.npc_pool) == pool_before


def test_hostile_mention_attaches_to_lone_unaliased_minted_other(narration_fixture) -> None:
    """The Ihnsch case: seated Other 'the Scrapborn' (GENERIC-backed mint),
    narrator names 'Ihnsch of the Rusted Works' → alias on the seat, no twin."""
    snap = narration_fixture.snapshot
    seat_confrontation(snap, opponent="the Scrapborn",
                       origin_kind=OriginKind.GENERIC)
    apply_mentions(narration_fixture,
                   mentions=[mention("Ihnsch of the Rusted Works", role="hostile")])
    seated = resolve_roster_npc(snap.npcs, "Ihnsch of the Rusted Works")
    assert seated is not None and seated.core.name == "the Scrapborn"
    assert not any(m.name == "Ihnsch of the Rusted Works" for m in snap.npc_pool)


def test_bystander_mention_still_mints(narration_fixture) -> None:
    """A non-hostile mention with a seated Other does NOT glue onto the enemy."""
    snap = narration_fixture.snapshot
    seat_confrontation(snap, opponent="the Scrapborn",
                       origin_kind=OriginKind.GENERIC)
    apply_mentions(narration_fixture, mentions=[mention("Old Weka", role="bystander")])
    assert any(m.name == "Old Weka" for m in snap.npc_pool)


def test_two_seated_others_no_ambiguous_attach(narration_fixture) -> None:
    """Two live opponents → ambiguous → mint, never guess (No Silent Fallbacks)."""
    ...  # same shape as above with two opponent actors; assert pool mint happens
```

(`narration_fixture`, `apply_mentions`, `mention`, `seed_npc`, `seat_confrontation` — reuse/extend the harness in the existing `_apply_npc_mentions` tests: `grep -rln "_apply_npc_mentions" tests/` and lift its fixture names; do not write a parallel harness.)

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/server/test_green_room_attach_before_mint.py -v -n0`
Expected: tests 1, 2 FAIL (pool member minted); 3, 4 PASS (pin current behavior).

- [ ] **Step 3: Implement the shared preamble in both mint branches**

Immediately before each branch constructs a `NpcPoolMember` for a novel name:

```python
from sidequest.game.green_room import attach_alias
from sidequest.game.origin import OriginKind, resolve_roster_npc

hit = resolve_roster_npc(snapshot.npcs, name)
if hit is not None:
    attach_alias(hit, name, from_source="narrator_mention")   # or "prose_extraction"
    continue  # or return, matching the branch's loop shape — no mint
enc = snapshot.encounter
if enc is not None and not enc.resolved and _mention_is_hostile(mention):
    live_others = [a for a in enc.actors if a.side == "opponent" and not a.withdrawn]
    if len(live_others) == 1:
        other = resolve_roster_npc(snapshot.npcs, live_others[0].name)
        if (
            other is not None
            and not other.aliases
            and other.origin is not None
            and other.origin.kind in (OriginKind.GENERIC, OriginKind.NARRATOR_INVENTED)
        ):
            attach_alias(other, name, from_source="narrator_mention")
            continue
# fall through: genuinely novel → existing mint path (unchanged),
# now emitting green_room.mint alongside its existing logging.
```

`_mention_is_hostile(mention)`: `getattr(mention, "side", "") == "opponent" or getattr(mention, "role", "") in ("hostile", "enemy", "opponent")` — define once in `narration_apply.py`, import into `session_helpers.py`. Add the `green_room.mint` span (`{identity_key, prose_name, source}`) at both mint sites. Also route the invented-name namer (`npc.invented_name_routed` site): when the ORIGINAL epithet resolves to a roster identity (the `self_match` case in the 2026-07-10 log), the minted proper name attaches as an alias on that identity instead of registering a new pool entry.

- [ ] **Step 4: Run task tests + narration suite**

Run: `uv run pytest tests/server/test_green_room_attach_before_mint.py -v -n0 && uv run pytest tests/ -k "mention or prose or narration_apply" -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/narration_apply.py sidequest/server/session_helpers.py \
        tests/server/test_green_room_attach_before_mint.py
git commit -m "feat(green-room): attach-before-mint in both mention paths (ADR-156 §6)"
```

---

### Task 6: All-sources-one-scene extension + loud-failure + full gate

**Files:**
- Modify: `tests/server/test_162_7_all_sources_one_scene.py` (locate exact name: `grep -rln "all.sources.one.scene\|all_sources" tests/`) — extend to the eight feeders
- Test: extend `tests/server/test_166_5_wrong_other_repros.py` with the loud-failure case

**Interfaces:**
- Consumes: everything above; no new production code in this task.

- [ ] **Step 1: Extend the 162-7 wiring test**

Add the router-opponent feeder to the staged scene (a confrontation dispatch naming a novel person) and assert, after one full turn drive: (a) exactly one identity per staged creature by `identity_key`; (b) a `green_room.materialized` span per feeder source label (all eight from Task 2's Interfaces list); (c) the named person seated as the confrontation Other.

- [ ] **Step 2: Loud-failure test**

```python
def test_no_target_no_room_no_generics_raises(bare_combat_pack) -> None:
    """Other-requiring type + no named target + empty room + no generics:
    raises, nothing half-seated (162-3 rollback preserved through the refactor)."""
    with pytest.raises((NoOpponentAvailableError, ValueError)):
        instantiate_encounter_from_trigger(
            snapshot=bare_combat_pack.snapshot, pack=bare_combat_pack.pack,
            encounter_type="combat", player_name="Solo", npcs_present=[],
            genre_slug="test", materialized_threat=None,
        )
    assert bare_combat_pack.snapshot.encounter is None
    assert bare_combat_pack.snapshot.npcs == []
```

- [ ] **Step 3: Full gate**

Run: `uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run pyright`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test(green-room): eight-feeder one-scene wiring + loud-failure fixtures"
```

---

### Task 7: Understudy wrong-Other detector (sidequest-understudy repo)

**Files:**
- Modify: `src/understudy/findings/` — the 162-11 identity-split detector module (locate: `grep -rln "two_names_one_enemy" src/`)
- Test: alongside, per that repo's existing detector test layout

**Interfaces:**
- Consumes: the perception layer's aria tokens for the Enemies region + narration log (162-11 established these: region "Enemies", listitem, `log:`).

- [ ] **Step 1: Write the failing detector test** — fixture a perceived page where the Enemies listitem names a creature absent from the last N narration log entries; assert a `wrong_other` finding (severity BEHAVIORAL) is produced; and the inverse fixture (opponent named in narration) produces none.
- [ ] **Step 2: Implement** — in the identity-split detector, add a check: seated-opponent display name (normalized, alias-aware if the panel exposes aliases) not substring-matching any of the last 3 narration entries → finding `wrong_other`. Reuse the module's existing normalization helpers.
- [ ] **Step 3: Run that repo's suite** — `uv run pytest -q` in `sidequest-understudy`. Expected: PASS.
- [ ] **Step 4: Commit + PR** — branch `feat/wrong-other-detector`, PR to that repo's default branch, **gated on the server merge** (note in PR body).

---

### Task 8: Live verification, docs closeout, PR

**Files:**
- Modify (orchestrator repo): `docs/adr/156-green-room-npc-origin-precedence.md` frontmatter (`implementation-status: deferred` → `live`, pointer → the merged PR), rerun `python3 scripts/regenerate_adr_indexes.py`; JARGONFILE "Green Room" entry updated to say "live"

- [ ] **Step 1: Live repro run** — `just server` + a SOLO flickering_reach session; repeat the Salt Camp attack ("grab the loudest one by the collar…"). Verify: confrontation panel opponent is the Scrapborn person (or his prose name), `green_room.materialized` spans visible on the GM panel (`just otel`), no `Resonance Grazer` seat. Capture the snapshot via `/api/debug/save/<slug>/snapshot` **after the turn settles** (the 1-2 s pre-persist window caveat from the playtest file).
- [ ] **Step 2: Understudy live run** — `understudy run` against the same world with the Task 7 detector; expect zero `wrong_other` / `two_names_one_enemy` findings.
- [ ] **Step 3: Open the ONE server PR** — `feat/green-room` → `develop`, title "Green Room: single-gate NPC materializer + target-first seater (ADR-156, closes 166-5)". Body: link spec + ADR, the three repro fixtures, the deleted-conscription inventory (function, five gates, spans, tests), and the live-run evidence from Steps 1-2.
- [ ] **Step 4: Docs closeout + sprint** — after merge: ADR frontmatter flip + index regen + JARGONFILE (orchestrator commit); Drummer closes 166-5 pointing at the fixtures and the epic shell.

---

## Self-Review

**Spec coverage:** §3.1 gate → Task 1. §3.2 feeders 1-4 → Task 2; 5-7 → Task 3; 8 → Tasks 3 (generics seat via admit) + 4 (target-first flow). §3.3 seater collapse + conscription deletion → Task 4. §3.4 attach-before-mint → Task 5. §3.5 OTEL → Tasks 1/2/5. §3.6 verification items 1-7 → Tasks 2 (idempotence), 4 (repros ×3 + alias survival), 5 (attach), 6 (all-sources + loud failure + gates), 7 (understudy), 8 (live run). §4 execution shape → branch/commit/PR steps. §5 done-criteria → Tasks 3 Step 5 (zero appends), 4 (deletion), 6 (fixtures), 8 (docs + spans + live). No gaps found.

**Placeholder scan:** the `...` bodies in Tasks 3/4/5 tests are same-shape substitutions of a fully-written sibling test in the same file, each with an exact grep/path to the real harness to lift — no "figure it out" steps remain. Step-1 read steps carry exact anchors and record-what-you-find instructions.

**Type consistency:** `MaterializationCandidate(npc, origin, source, aliases)`, `AdmitResult(admitted, merged, aliases_attached, dropped)`, `admit(snapshot, candidates)`, `attach_alias(npc, alias, from_source=)`, `LADDER` — used identically in Tasks 2-6. Span names `green_room.materialized/precedence_conflict/alias_attached/mint` consistent across Tasks 1/2/5/6/8. Source labels defined once (Task 2 Interfaces) and reused verbatim.
