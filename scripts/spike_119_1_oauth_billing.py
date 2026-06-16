#!/usr/bin/env python3
"""119-1 spike harness — subscription-OAuth billing-attribution probe.

Fires a handful of tiny ``claude-haiku-4-5`` ``messages.create`` calls authed via
the ``ant auth login`` OAuth profile (``ANTHROPIC_AUTH_TOKEN``), with
``ANTHROPIC_API_KEY`` forced unset, and prints the wall-clock window plus per-call
usage. Read the GO/NO-GO from the Admin Cost API for the printed UTC window:

  GO   (-> 119-2): these Haiku tokens do NOT appear as a PAYG dollar line
                   (the OAuth-authed call drew the free Max subscription pool)
  NO-GO (-> 119-3): they appear as PAYG cost (raw SDK over OAuth still bills PAYG)

The "Agent SDK credit" is CANCELLED (ADR-101 Amendment 2026-06-15) — there is NO
credit meter to watch; the signal is purely PAYG-line / no-PAYG-line. See
docs/superpowers/specs/2026-06-15-narrator-subscription-oauth-reauth-design.md.

No production code is touched (119-1 AC4). Run from a shell that is NOT also doing
interactive Claude Code, so this session's 5-hr-cap overage doesn't pollute the read.

Prereqs:  ant auth login   (browser -> Max-subscription org)
Run:      uv run --with anthropic python scripts/spike_119_1_oauth_billing.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import NoReturn

MODEL = "claude-haiku-4-5"
N_CALLS = 5
OAUTH_BETA = "oauth-2025-04-20"


def fail(msg: str) -> NoReturn:
    print(f"✗ {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_oauth_token() -> None:
    """Pull ANTHROPIC_AUTH_TOKEN (and ANTHROPIC_BASE_URL) from the active ant
    profile and force ANTHROPIC_API_KEY off. Fail loud — never silently fall back
    to PAYG (SOUL No-Silent-Fallbacks)."""
    # Force the key off before constructing any client: a set key overrides the
    # token and the API rejects both-set. An empty "" still wins its precedence
    # slot, so pop the var entirely rather than blanking it.
    os.environ.pop("ANTHROPIC_API_KEY", None)

    try:
        out = subprocess.run(
            ["ant", "auth", "print-credentials", "--env"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except FileNotFoundError:
        fail("`ant` not found — brew install anthropics/tap/ant, then `ant auth login`.")
    except subprocess.CalledProcessError as exc:
        fail(
            "`ant auth print-credentials --env` failed — run `ant auth login` first.\n"
            f"{exc.stderr.strip()}"
        )

    loaded: list[str] = []
    for raw in out.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip().strip('"').strip("'")
        loaded.append(key.strip())

    if "ANTHROPIC_AUTH_TOKEN" not in loaded:
        fail("ant did not emit ANTHROPIC_AUTH_TOKEN — are you logged in? (`ant auth status`)")

    print(f"✓ loaded from ant profile: {', '.join(loaded)}")
    print("✓ ANTHROPIC_API_KEY forced unset (no both-set, no PAYG fallback)")


def probe(client, *, beta: bool) -> None:
    extra = {"anthropic-beta": OAUTH_BETA} if beta else {}
    label = "with oauth beta header" if beta else "WITHOUT beta header (119-2 §3 probe)"
    print(f"\n── {N_CALLS} calls {label} ──")
    for i in range(N_CALLS):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=64,
            messages=[{"role": "user", "content": f"ping {i} — 119-1 billing attribution test"}],
            extra_headers=extra,
        )
        print(f"  [{i}] model={resp.model} usage={resp.usage}")


def main() -> None:
    load_oauth_token()

    try:
        import anthropic
    except ModuleNotFoundError:
        fail("anthropic not importable — run with: uv run --with anthropic python " + sys.argv[0])

    client = anthropic.Anthropic()  # picks up ANTHROPIC_AUTH_TOKEN

    start = datetime.now(timezone.utc)
    print(f"\n▶ window START (UTC): {start.isoformat()}")

    probe(client, beta=True)

    # Extra pass without the beta header. If THIS succeeds, the SDK auto-adds
    # oauth-2025-04-20 in auth_token mode -> 119-2 needs no manual beta join.
    # If it 400s, 119-2 must comma-join oauth-2025-04-20 + extended-cache-ttl-2025-04-11
    # at every call site that sets anthropic-beta (design spec §3 risk).
    try:
        probe(client, beta=False)
        print("\n✓ no-beta pass SUCCEEDED — SDK auto-adds the oauth beta (119-2 simpler).")
    except Exception as exc:  # noqa: BLE001 — record the verdict, don't abort the spike
        print(f"\n✓ no-beta pass FAILED ({type(exc).__name__}) — SDK does NOT auto-add the oauth beta;")
        print("  119-2 must comma-join oauth-2025-04-20 + extended-cache-ttl-2025-04-11 (spec §3).")

    end = datetime.now(timezone.utc)
    print(f"\n▶ window END (UTC):   {end.isoformat()}")
    print("\nNow read the Admin Cost API for [START, END]:")
    print("  GO   (-> 119-2): these Haiku tokens are NOT a PAYG dollar line (drew the free Max pool)")
    print("  NO-GO (-> 119-3): they show up as PAYG cost")


if __name__ == "__main__":
    main()
