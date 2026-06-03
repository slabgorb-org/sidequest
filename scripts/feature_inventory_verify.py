# scripts/feature_inventory_verify.py
"""Evidence verifiers for the feature-inventory generator (Phase 1).

Each function checks one anchor type against the live repo and is pure
(filesystem reads only, no markdown, no orchestration) so it can be unit
tested in isolation.
"""
from __future__ import annotations

import re
from pathlib import Path

_SPAN_CONST_RE = re.compile(r'^SPAN_[A-Z0-9_]+\s*=\s*"([^"]+)"', re.MULTILINE)


def load_span_constants(spans_dir: Path) -> set[str]:
    """Return the set of span name literals declared in telemetry/spans/*.py.

    A span name is 'known to the engine' iff it is declared as a
    ``SPAN_* = "literal"`` module constant. Static parse (no import) keeps
    this doc tool free of server runtime deps, matching the ADR generator.
    """
    names: set[str] = set()
    for path in sorted(spans_dir.glob("*.py")):
        names.update(_SPAN_CONST_RE.findall(path.read_text()))
    return names
