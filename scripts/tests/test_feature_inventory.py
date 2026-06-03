# scripts/tests/test_feature_inventory.py
"""Tests for the feature-inventory generator (Phase 1)."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.feature_inventory_verify import load_span_constants

ROOT = Path(__file__).parent.parent.parent  # repo root


def test_load_span_constants_parses_literals(tmp_path):
    spans_dir = tmp_path / "spans"
    spans_dir.mkdir()
    (spans_dir / "turn.py").write_text(
        'SPAN_TURN = "turn"\n'
        'SPAN_TURN_BARRIER = "turn.barrier"\n'
        "SPAN_ROUTES[SPAN_TURN] = SpanRoute(...)\n"
    )
    (spans_dir / "_core.py").write_text("SPAN_ROUTES = {}\n")
    names = load_span_constants(spans_dir)
    assert names == {"turn", "turn.barrier"}


def test_load_span_constants_against_real_registry():
    """Wiring: the real telemetry/spans dir parses and contains known spans."""
    real = ROOT / "sidequest-server" / "sidequest" / "telemetry" / "spans"
    names = load_span_constants(real)
    assert "turn" in names
    assert "turn.barrier" in names
    assert len(names) > 20  # registry is substantial
