"""RED tests for Story 50-18 — scripts/playtest.py ``--fixture`` flag.

Adds the headless counterpart to the UI's ``?scene=NAME`` URL parameter:
``python scripts/playtest.py --fixture combat_test`` must POST
``/dev/scene/combat_test`` (instead of ``POST /api/games``) and skip the
auto-chargen loop because the fixture has already hydrated a character
into the save file.

Contract under test (ADR-092 §Implementation row 7, and the implementation
plan in ``.session/50-18-session.md``):

* ``--fixture <name>`` is parseable via ``parse_args``.
* ``--fixture`` and ``--scenario`` are mutually exclusive at the argparse
  layer — one or the other, never both, never neither.
* The CLI ``--help`` output advertises ``--fixture`` so devs can discover
  it without reading source.
* Internal driver: a helper (``mint_via_scene_harness`` or
  ``post_dev_scene``) targets ``/dev/scene/{name}`` and returns the slug
  the server minted, parallel to ``mint_game_slug`` for ``/api/games``.

All tests RED until Dev wires up the flag in the GREEN phase.

Bypassing the module import (which transitively imports ``httpx`` —
absent from ``pyproject.toml`` on develop as of 2026-05-13) the
``test_help_lists_fixture_flag`` test uses ``subprocess`` to invoke the
CLI; the others import via ``importlib`` and accept a top-level
``ImportError`` as a valid RED signal.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PLAYTEST_PATH = SCRIPTS_DIR / "playtest.py"


def _import_playtest():
    """Import scripts/playtest.py as ``playtest``.

    Mirrors the import shim from ``test_playtest_split.py``. Tests that
    rely on this must tolerate ``ImportError`` (notably ``httpx``: not yet
    in pyproject.toml as of 2026-05-13) as a separate RED signal — once
    Dev wires the dependency in GREEN, the import succeeds and the
    fixture-flag tests start exercising the real argparse surface.
    """
    if "playtest" in sys.modules:
        del sys.modules["playtest"]
    spec = importlib.util.spec_from_file_location("playtest", str(PLAYTEST_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["playtest"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── CLI surface: --help must advertise --fixture ────────────────────────────


def test_help_lists_fixture_flag() -> None:
    """``playtest.py --help`` must advertise ``--fixture`` so devs can
    discover the scene-harness shortcut. Subprocess-driven so we sidestep
    transitive import failures (httpx) in the parser test."""
    result = subprocess.run(
        [sys.executable, str(PLAYTEST_PATH), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (
        f"playtest --help exited {result.returncode}; stderr:\n{result.stderr}"
    )
    assert "--fixture" in result.stdout, (
        "playtest --help output must advertise --fixture for scene-harness mode; "
        f"got stdout:\n{result.stdout}"
    )


def test_help_explains_fixture_replaces_scenario() -> None:
    """The ``--fixture`` help text should make clear that it's an
    alternative to ``--scenario``, not an add-on. Devs reading the help
    output should immediately understand the two flags are mutually
    exclusive (one or the other)."""
    result = subprocess.run(
        [sys.executable, str(PLAYTEST_PATH), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    help_text = result.stdout.lower()
    # The help description should reference either "scene" (the harness name)
    # or "/dev/scene" (the endpoint) so it's discoverable when grepping.
    assert "scene" in help_text, (
        "playtest --help must mention 'scene' in the --fixture description "
        f"so devs can discover the harness; got:\n{result.stdout}"
    )


# ── argparse surface ────────────────────────────────────────────────────────


def test_parse_args_accepts_fixture_flag() -> None:
    """``parse_args(["--fixture", "combat_test"])`` must succeed without
    requiring ``--scenario`` — the flag stands alone."""
    try:
        playtest = _import_playtest()
    except ImportError as exc:
        pytest.fail(
            f"scripts/playtest.py failed to import: {exc!r}. "
            "GREEN phase must add the missing dependency to pyproject.toml "
            "before --fixture wiring is verifiable."
        )

    ns = playtest.parse_args(["--fixture", "combat_test"])
    assert hasattr(ns, "fixture"), (
        "argparse Namespace must expose .fixture after --fixture is wired"
    )
    assert ns.fixture == "combat_test"


def test_fixture_and_scenario_are_mutually_exclusive() -> None:
    """Supplying both ``--fixture`` and ``--scenario`` is an error — the
    two flags select different driver paths and must not be combined."""
    try:
        playtest = _import_playtest()
    except ImportError as exc:
        pytest.fail(f"scripts/playtest.py failed to import: {exc!r}")

    with pytest.raises((SystemExit, argparse.ArgumentError)):
        playtest.parse_args(
            ["--fixture", "combat_test", "--scenario", "scenarios/smoke_test.yaml"]
        )


def test_at_least_one_of_fixture_or_scenario_is_required() -> None:
    """``playtest.py`` with no arguments must NOT silently succeed — one
    of ``--fixture`` or ``--scenario`` is required. (Pre-50-18: --scenario
    was required; we relax to "required group" once --fixture is added.)"""
    try:
        playtest = _import_playtest()
    except ImportError as exc:
        pytest.fail(f"scripts/playtest.py failed to import: {exc!r}")

    with pytest.raises(SystemExit):
        playtest.parse_args([])


# ── Driver surface: a helper to POST /dev/scene/{name} ──────────────────────


def test_module_exports_scene_harness_helper() -> None:
    """The driver must expose a helper that POSTs ``/dev/scene/{name}`` and
    returns the slug — parallel to the existing ``mint_game_slug`` for
    ``POST /api/games``. The function name is left to Dev's discretion
    (``mint_via_scene_harness`` and ``post_dev_scene`` are both reasonable),
    but SOMETHING must be exported so the dispatch layer can call it."""
    try:
        playtest = _import_playtest()
    except ImportError as exc:
        pytest.fail(f"scripts/playtest.py failed to import: {exc!r}")

    # Look for any of the plausible names. RED until at least one exists.
    candidates = [
        "mint_via_scene_harness",
        "post_dev_scene",
        "load_scene_fixture",
        "mint_fixture_slug",
    ]
    exported = [name for name in candidates if hasattr(playtest, name)]
    assert exported, (
        "playtest.py must export a helper that POSTs /dev/scene/{name}. "
        f"Looked for any of: {candidates!r}; found none. "
        "Pick one and add it in GREEN."
    )


# ── Mode dispatch: fixture mode skips chargen ───────────────────────────────


def test_fixture_mode_constructs_playtest_without_chargen() -> None:
    """When ``--fixture`` is in play, the ``Playtest`` driver should treat
    chargen as already-done (the fixture YAML hydrates a Character into
    the save before the WebSocket opens). The slug-connect handshake will
    report ``has_character=True`` and the driver must not re-run chargen.

    Test surface: building the driver with ``fixture=<name>`` (or whatever
    constructor parameter Dev picks) yields ``chargen_done=True`` at
    construction time. The exact constructor signature is left to Dev;
    this test asserts the BEHAVIOR (chargen skipped), not the API shape."""
    try:
        playtest = _import_playtest()
    except ImportError as exc:
        pytest.fail(f"scripts/playtest.py failed to import: {exc!r}")

    # The Playtest class must accept a fixture-mode signal in some form.
    # We try the plausible kwargs in order and require AT LEAST ONE to work.
    pt_class = getattr(playtest, "Playtest", None)
    assert pt_class is not None, "playtest.Playtest class must exist"

    minimal_scenario = {
        "name": "fixture-mode smoke",
        "_genre_slug": "mutant_wasteland",
        "_world_slug": "flickering_reach",
        "mode": "solo",
        "character": {"strategy": "auto"},
        "actions": [],
    }

    # Attempt construction with a fixture signal. Implementations are free to
    # pick the kwarg name; the test enumerates the reasonable ones.
    fixture_kwargs_candidates: list[dict] = [
        {"fixture": "combat_test"},
        {"fixture_name": "combat_test"},
        {"scene_fixture": "combat_test"},
    ]

    constructed = None
    last_err: Exception | None = None
    for extra in fixture_kwargs_candidates:
        try:
            constructed = pt_class(
                minimal_scenario,
                server="ws://localhost:8765/ws",
                rest_base="http://localhost:8765",
                player_name="FixtureTest",
                force_new=True,
                idle_timeout=1.0,
                seed=0,
                **extra,
            )
            break
        except TypeError as e:
            last_err = e
            continue

    assert constructed is not None, (
        "Playtest must accept a fixture-mode parameter "
        f"(tried {[list(k)[0] for k in fixture_kwargs_candidates]!r}). "
        f"Last error: {last_err!r}"
    )

    # The driver must mark chargen as already-done in fixture mode so the
    # AutoChargen state machine never runs.
    assert constructed.chargen_done is True, (
        "fixture-mode Playtest must start with chargen_done=True "
        "(the fixture hydrates a character into the save before WS connect); "
        f"got chargen_done={constructed.chargen_done!r}"
    )
