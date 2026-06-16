#!/usr/bin/env python3
"""119-3 de-risk smoke test — does claude-agent-sdk draw the Max subscription?

Before sinking the 8pt port of the narrator's tool-use loop onto claude-agent-sdk
(119-3), prove the premise this whole epic now rests on: a claude-agent-sdk query
authed via the Claude Code subscription login draws the SUBSCRIPTION ledger (the
"Sonnet only" pool on claude.ai), NOT the metered API-platform PAYG ledger that the
raw Messages SDK hit in the 119-1 spike (NO-GO — 400 "credit balance too low").

This is the inverse of scripts/spike_119_1_oauth_billing.py. The Agent SDK runs
through the bundled Claude Code CLI, which authenticates via your subscription
login — so we MUST unset ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN, or the CLI
routes to the metered API (PAYG) and contaminates the read.

  GO   (-> commit 119-3): the query succeeds (is_error False, no 400) AND the
                          claude.ai "Sonnet only" usage bar ticks up. The Agent SDK
                          draws the free subscription — the port delivers free inference.
  NO-GO: it errors with api_error_status 400 / a credit message — the Agent SDK
         also bills PAYG; the whole epic premise is wrong, escalate before porting.

No production code is touched. Run from a shell NOT also doing interactive Claude
Code on Sonnet (this CLI session runs on Opus — a different bar — so a moving
"Sonnet only" bar is attributable to THIS test).

Prereqs: be logged into Claude Code on the Max subscription (you already are).
Run:     uv run --with claude-agent-sdk python scripts/spike_119_3_agentsdk_subscription.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

MODEL = "claude-sonnet-4-6"  # narrator's model; draws the visible "Sonnet only" bar
N_CALLS = 3


def main() -> None:
    # The Agent SDK runs through the bundled Claude Code CLI. If either var is set,
    # the CLI authenticates against the metered API (PAYG) instead of the
    # subscription — the exact ledger we're trying to AVOID. Pop them so the CLI
    # falls through to the subscription login. Fail loud if anything lingers.
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        if os.environ.pop(var, None) is not None:
            print(f"• unset {var} (would have forced the API/PAYG path)")
    leftover = [v for v in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN") if os.environ.get(v)]
    if leftover:
        print(f"✗ {', '.join(leftover)} still set — can't guarantee the subscription path", file=sys.stderr)
        raise SystemExit(1)
    print("✓ no API key / auth token in env — Agent SDK will use the subscription login")

    try:
        import anyio
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ResultMessage,
            TextBlock,
            query,
        )
    except ModuleNotFoundError as exc:
        print(
            f"✗ {exc.name} not importable — run with: "
            "uv run --with claude-agent-sdk python " + sys.argv[0],
            file=sys.stderr,
        )
        raise SystemExit(1)

    async def run() -> None:
        start = datetime.now(timezone.utc)
        print(f"\n▶ window START (UTC): {start.isoformat()}")
        opts = ClaudeAgentOptions(
            model=MODEL,
            max_turns=3,  # agent-loop headroom; a chat reply can structure >1 turn
            allowed_tools=[],  # no tools — minimal turn, just bill one inference
            system_prompt="Reply with exactly one short sentence.",
        )
        for i in range(N_CALLS):
            print(f"\n── call {i} (model={MODEL}) ──")
            saw_result = False
            # A per-call error (e.g. a turn-limit hit) must not abort the run —
            # the billing verdict only needs the credit-error-or-not signal, and
            # the final verdict block must always print.
            try:
                async for msg in query(prompt=f"ping {i} — 119-3 subscription-draw test", options=opts):
                    if isinstance(msg, AssistantMessage):
                        text = "".join(b.text for b in msg.content if isinstance(b, TextBlock))
                        if text:
                            print(f"  assistant: {text.strip()[:120]}")
                    elif isinstance(msg, ResultMessage):
                        saw_result = True
                        print(
                            f"  result: is_error={msg.is_error} "
                            f"api_error_status={msg.api_error_status} "
                            f"num_turns={msg.num_turns} total_cost_usd={msg.total_cost_usd}"
                        )
                        if msg.usage:
                            print(f"  usage: {msg.usage}")
                        if msg.model_usage:
                            print(f"  model_usage: {msg.model_usage}")
                        if msg.is_error:
                            print(f"  ✗ result-level error result={msg.result!r} errors={msg.errors}")
            except Exception as exc:  # noqa: BLE001 — record per-call failure, keep the run going
                print(f"  ✗ call raised: {type(exc).__name__}: {exc}")
            if not saw_result:
                print("  ⚠ no ResultMessage on the stream — inspect output above")
        end = datetime.now(timezone.utc)
        print(f"\n▶ window END (UTC):   {end.isoformat()}")
        print("\nRead the verdict:")
        print("  PRIMARY (dispositive): every call is_error=False, api_error_status=None,")
        print("    service_tier='standard'. The 119-1 raw-SDK probe 400'd on the empty")
        print("    API-platform ledger at the same moment — a call that does NOT 400 cannot")
        print("    be hitting it, so it drew the subscription. This alone settles GO/NO-GO.")
        print("  CONFIRMATORY (weak — don't rely on it): claude.ai -> Usage. A few tiny calls")
        print("    round to <1% of the WEEKLY 'Sonnet only' cap, so that bar may not visibly")
        print("    move; the 5-hr 'Current session' bar moves but is polluted by any")
        print("    concurrent interactive Claude Code session. The no-400 result is the tell.")
        print("  GO  -> commit 119-3 (Agent SDK draws the free subscription).")
        print("  NO-GO -> a 400/credit error above => Agent SDK bills PAYG too; escalate.")
        print("\nNote: total_cost_usd is Claude Code's NOTIONAL cost estimate — it is non-zero")
        print("even on the free subscription and is NOT a PAYG charge. The 400 and the")
        print("claude.ai usage bar are the real signals, not this number.")

    anyio.run(run)


if __name__ == "__main__":
    main()
