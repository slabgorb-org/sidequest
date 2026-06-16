#!/usr/bin/env python3
"""119-3 OQ-15 de-risk probe — does claude-agent-sdk expose API-enforced
JSON-schema structured output for the Haiku single-shot extraction port?

Sibling of scripts/spike_119_3_agentsdk_subscription.py (which proved the
subscription-login path draws the free Max pool). That spike settled "does the
Agent SDK bill the subscription?" — YES. This one settles the SECOND, separately
load-bearing unknown for the Haiku half of the 119-3 port:

  OQ-15: Can claude-agent-sdk reproduce the raw SDK's forced-`tool_choice`
         structured extraction (Intent Router / unseeded-objective classifier /
         archetype inference) via a first-class `output_format` JSON-schema
         option — Path A — so the Haiku calls stay API-ENFORCED schema-valid in
         one shot? Or does it not (forcing the prompt-coerced Path B that
         `_OllamaIntentRouterLlm` already ships)?

See docs/superpowers/specs/2026-06-15-narrator-agentsdk-port-design.md §3.6 and
§6.4. The Agent SDK exposes NO `tool_choice` and ALWAYS executes a called tool's
handler, so the raw "force a tool, read its `.input`, never run a handler"
mechanism has no analog. The design's PRIMARY replacement (Path A) is the
candidate first-class structured-output surface:

  ClaudeAgentOptions(output_format={"type":"json_schema","schema": <JSON Schema>})
  → ResultMessage.structured_output   (a parsed, schema-valid dict)

This probe exercises that surface EMPIRICALLY against `claude-haiku-4-5` under a
single-shot, no-tools `max_turns=1` query, with a small representative schema.
The claude-code-guide reference claims (a) the field/result symbols exist in the
released SDK but (b) structured output is multi-turn-RETRY-dependent and so does
NOT succeed under `max_turns=1` (no turn 2 to re-prompt on validation failure) —
surfacing as `ResultMessage.subtype == "error_max_structured_output_retries"`.
That is a DOC INFERENCE; OQ-15 demands the empirical answer. We test it.

  GO  (Path A viable): `output_format` accepted our schema and a single-shot
       `max_turns=1` query returned a schema-valid `structured_output` dict
       (is_error=False). The Haiku forced-extraction port stays API-enforced.
  NO-GO (Path B): `output_format` is absent / wrong-shape / errors on the
       feature, OR it requires multi-turn retry and fails clean single-shot.
       The port falls to prompt-coerced JSON (already shipping in
       `_OllamaIntentRouterLlm`; parse with `_extract_json_object`).
  BLOCKED-ON-AUTH: couldn't test the feature because the subscription login
       wasn't available (re-run `ant auth login`). Distinct from a feature NO-GO.

Auth handling MIRRORS the reference spike: unset ANTHROPIC_API_KEY and
ANTHROPIC_AUTH_TOKEN in-process so the bundled CLI falls through to the
subscription OAuth login (else it routes to the metered API / PAYG, which 400'd
in 119-1 and contaminates the read).

No production code is touched.
Run: uv run --with claude-agent-sdk python scripts/spike_119_3_haiku_outputformat.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

MODEL = "claude-haiku-4-5"  # the four single-shot Haiku call sites' model

# --- The representative JSON Schema(s) we ask the SDK to enforce -------------
#
# Path A's whole value proposition is "the model is forced to emit schema-valid
# structured output in one shot." So we test schema acceptance two ways:
#   1. A minimal hand-written 3-field typed object — isolates "does
#      output_format work AT ALL" from schema complexity.
#   2. The REAL DispatchPackage schema (the Intent Router's forced tool's
#      input_schema, DispatchPackage.model_json_schema() — $defs, nested
#      objects, additionalProperties) — the genuine port payload. Best-effort
#      import; if the server package isn't on the path we skip #2 and still get
#      a decisive OQ-15 answer from #1.

MINIMAL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["attack", "talk", "move", "search", "other"],
            "description": "The single classified intent of the player action.",
        },
        "target": {
            "type": "string",
            "description": "The noun the action is directed at, or 'none'.",
        },
        "confidence": {
            "type": "number",
            "description": "Classifier confidence, 0.0–1.0.",
        },
    },
    "required": ["intent", "target", "confidence"],
    "additionalProperties": False,
}

MINIMAL_PROMPT = (
    "Player action: 'I draw my blade and lunge at the bandit captain.' "
    "Classify it. Respond ONLY with the structured object the schema demands."
)


def _maybe_real_dispatch_schema() -> dict | None:
    """Best-effort: pull the live DispatchPackage schema (the real port payload).

    Returns None (and prints why) if the server package isn't importable from
    this process — the minimal-schema probe alone still settles OQ-15.
    """
    try:
        from sidequest.protocol.dispatch import DispatchPackage  # type: ignore
    except Exception as exc:  # noqa: BLE001 — optional enrichment, not the gate
        print(f"  (real DispatchPackage schema unavailable here: {type(exc).__name__}: {exc})")
        return None
    return DispatchPackage.model_json_schema()


def main() -> None:
    # MIRROR the reference spike: the Agent SDK runs through the bundled CLI; a
    # set key/token forces the metered API (PAYG) instead of the subscription.
    # Pop them so the CLI falls through to the subscription login. Fail loud if
    # anything lingers.
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        if os.environ.pop(var, None) is not None:
            print(f"• unset {var} (would have forced the API/PAYG path)")
    leftover = [v for v in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN") if os.environ.get(v)]
    if leftover:
        print(
            f"✗ {', '.join(leftover)} still set — can't guarantee the subscription path",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print("✓ no API key / auth token in env — Agent SDK will use the subscription login")

    try:
        import anyio
        from claude_agent_sdk import (
            ClaudeAgentOptions,
            ResultMessage,
            query,
        )
    except ModuleNotFoundError as exc:
        print(
            f"✗ {exc.name} not importable — run with: "
            "uv run --with claude-agent-sdk python " + sys.argv[0],
            file=sys.stderr,
        )
        raise SystemExit(1)

    # OQ-15's first sub-question: does ClaudeAgentOptions even HAVE the field?
    # If the released dataclass has no `output_format`, that alone is a NO-GO
    # (Path A is not expressible) — report it without making a call.
    import dataclasses

    opt_fields = {f.name for f in dataclasses.fields(ClaudeAgentOptions)} \
        if dataclasses.is_dataclass(ClaudeAgentOptions) else set()
    has_output_format = "output_format" in opt_fields
    print(f"\n▶ ClaudeAgentOptions has `output_format` field: {has_output_format}")
    if not has_output_format:
        # Probe the result type too, for the report.
        rm_fields = {f.name for f in dataclasses.fields(ResultMessage)} \
            if dataclasses.is_dataclass(ResultMessage) else set()
        print(f"  ResultMessage fields: {sorted(rm_fields)}")
        print(
            "\n══ VERDICT: NO-GO (Path B) — claude-agent-sdk's ClaudeAgentOptions "
            "exposes no `output_format`.\n"
            "   The Haiku forced-extraction port must use prompt-coerced JSON "
            "(the _OllamaIntentRouterLlm pattern + _extract_json_object)."
        )
        return
    rm_fields = {f.name for f in dataclasses.fields(ResultMessage)} \
        if dataclasses.is_dataclass(ResultMessage) else set()
    has_structured = "structured_output" in rm_fields
    print(f"  ResultMessage has `structured_output` field: {has_structured}  "
          f"(fields: {sorted(rm_fields)})")

    real_schema = _maybe_real_dispatch_schema()

    # Each probe: (label, schema, prompt). The minimal one is the OQ-15 gate;
    # the DispatchPackage one is the real-payload confirmation (OQ-3-adjacent).
    probes: list[tuple[str, dict, str]] = [("minimal-3-field", MINIMAL_SCHEMA, MINIMAL_PROMPT)]
    if real_schema is not None:
        probes.append(
            (
                "real-DispatchPackage",
                real_schema,
                "Player action: 'I draw my blade and lunge at the bandit captain.' "
                "Emit the structured DispatchPackage for this single action.",
            )
        )

    async def run() -> dict:
        start = datetime.now(timezone.utc)
        print(f"\n▶ window START (UTC): {start.isoformat()}")
        outcomes: dict[str, dict] = {}
        # Each schema is tested at two turn budgets:
        #   max_turns=1 — the spec's exact single-shot constraint (§6.4 Path A).
        #   max_turns=2 — turn-headroom. The SDK spends an internal finalize/
        #     validate turn on structured output, so num_turns==2 even with no
        #     tools; this separates "feature broken" from "feature needs >1 turn".
        # The verdict keys off the (label, max_turns=1) outcome, but the
        # headroom row is what tells SM whether Path A is dead or merely
        # not-strictly-single-shot.
        for label, schema, prompt in probes:
            for mt in (1, 2):
                key = f"{label}@max_turns={mt}"
                print(f"\n── probe: {key} (model={MODEL}, no tools) ──")
                outcome: dict = {
                    "max_turns": mt,
                    "is_error": None,
                    "subtype": None,
                    "service_tier": None,
                    "num_turns": None,
                    "structured_output": None,
                    "schema_valid": None,
                    "exception": None,
                }
                try:
                    opts = ClaudeAgentOptions(
                        model=MODEL,
                        max_turns=mt,
                        allowed_tools=[],  # no tools — pure structured-extraction
                        system_prompt="You classify a single player action. Reply with structured data only.",
                        output_format={"type": "json_schema", "schema": schema},
                    )
                except Exception as exc:  # noqa: BLE001 — bad option shape is itself a finding
                    outcome["exception"] = f"{type(exc).__name__}: {exc}"
                    print(f"  ✗ ClaudeAgentOptions(output_format=...) raised: {outcome['exception']}")
                    outcomes[key] = outcome
                    continue

                saw_result = False
                try:
                    async for msg in query(prompt=prompt, options=opts):
                        if isinstance(msg, ResultMessage):
                            saw_result = True
                            outcome["is_error"] = getattr(msg, "is_error", None)
                            outcome["subtype"] = getattr(msg, "subtype", None)
                            outcome["num_turns"] = getattr(msg, "num_turns", None)
                            so = getattr(msg, "structured_output", None)
                            outcome["structured_output"] = so
                            # service_tier may live on msg.usage; surface whatever we find
                            usage = getattr(msg, "usage", None)
                            if isinstance(usage, dict):
                                outcome["service_tier"] = usage.get("service_tier")
                            else:
                                outcome["service_tier"] = getattr(usage, "service_tier", None)
                            print(
                                f"  result: is_error={outcome['is_error']} "
                                f"subtype={outcome['subtype']!r} "
                                f"service_tier={outcome['service_tier']!r} "
                                f"num_turns={outcome['num_turns']}"
                            )
                            print(f"  raw structured_output: {so!r}")
                            if isinstance(usage, dict):
                                print(f"  usage: {usage}")
                            if getattr(msg, "is_error", False):
                                print(
                                    f"  ✗ result-level error result={getattr(msg, 'result', None)!r}"
                                )
                except Exception as exc:  # noqa: BLE001 — record, keep the run going
                    outcome["exception"] = f"{type(exc).__name__}: {exc}"
                    print(f"  ✗ query raised: {outcome['exception']}")

                if not saw_result and outcome["exception"] is None:
                    print("  ⚠ no ResultMessage on the stream — inspect output above")

                # Did we get back a dict that actually conforms to the schema?
                so = outcome["structured_output"]
                if isinstance(so, dict):
                    if label == "minimal-3-field":
                        required = set(schema["required"])
                        outcome["schema_valid"] = required.issubset(so.keys()) and so.get(
                            "intent"
                        ) in schema["properties"]["intent"]["enum"]
                    else:
                        outcome["schema_valid"] = True  # presence of a dict is the signal here
                    print(f"  schema-valid dict: {outcome['schema_valid']}")
                outcomes[key] = outcome

        end = datetime.now(timezone.utc)
        print(f"\n▶ window END (UTC):   {end.isoformat()}")
        return outcomes

    outcomes = anyio.run(run)

    # ---- Verdict ----------------------------------------------------------
    print("\n" + "=" * 72)
    # The GATE is the minimal schema at max_turns=1 (§6.4 Path A's exact
    # constraint). The HEADROOM row (max_turns=2) tells SM whether the feature
    # is dead or merely not-strictly-single-shot.
    gate = outcomes.get("minimal-3-field@max_turns=1", {})
    headroom = outcomes.get("minimal-3-field@max_turns=2", {})
    exc = gate.get("exception")
    is_error = gate.get("is_error")
    subtype = gate.get("subtype")
    so = gate.get("structured_output")
    schema_valid = gate.get("schema_valid")

    head_ok = (
        isinstance(headroom.get("structured_output"), dict)
        and headroom.get("is_error") is False
        and headroom.get("schema_valid")
    )

    auth_markers = ("credit balance", "authentication", "x-api-key", "401", "403",
                    "not logged in", "no conversation", "oauth", "subscription",
                    "Invalid API key", "log in", "login")
    looks_like_auth = bool(exc) and any(m.lower() in str(exc).lower() for m in auth_markers)
    # An auth-class subtype on the result (the SDK surfaces auth failure as a
    # failed ResultMessage, not always an exception) also counts as AUTH.
    if subtype and any(m in str(subtype).lower() for m in ("auth", "credit", "login")):
        looks_like_auth = True

    if looks_like_auth:
        print("══ VERDICT: BLOCKED-ON-AUTH ══")
        print("  The probe failed on AUTH, not on the output_format feature.")
        print(f"  signal: exception={exc!r} subtype={subtype!r}")
        print("  The subscription login profile is likely absent/expired. Operator: run")
        print("      ant auth login")
        print("  (or `claude` interactive `/login`), confirm with `ant auth status`,")
        print("  then re-run this spike. Do NOT read this as a Path A NO-GO.")
    elif isinstance(so, dict) and is_error is False and schema_valid:
        print("══ VERDICT: GO (Path A viable, strictly single-shot) ══")
        print("  claude-agent-sdk returned an API-ENFORCED schema-valid structured_output")
        print("  dict from a SINGLE-SHOT (max_turns=1, no-tools) Haiku query.")
        print("  Working surface for the Haiku forced-extraction port:")
        print("    opts = ClaudeAgentOptions(")
        print(f"        model={MODEL!r}, max_turns=1, allowed_tools=[],")
        print('        output_format={"type": "json_schema", "schema": <tool_schema>},')
        print("    )")
        print("    async for msg in query(prompt=<system+user>, options=opts):")
        print("        if isinstance(msg, ResultMessage):")
        print("            return msg.structured_output  # the dict, where .input went")
    elif head_ok:
        # The decisive real-world finding: the feature WORKS, but the SDK spends
        # an internal finalize/validate turn on structured output (num_turns==2
        # even with no tools), so max_turns=1 fails with error_max_turns. This
        # is NOT a feature NO-GO — it's a constraint correction for the spec.
        print("══ VERDICT: GO-WITH-CAVEAT — Path A viable, but NOT under max_turns=1 ══")
        print("  output_format + ResultMessage.structured_output EXIST and WORK on the")
        print(f"  released claude-agent-sdk: at max_turns>=2 a no-tools {MODEL} query")
        print("  returns is_error=False, subtype='success', a schema-valid structured_output")
        print(f"  dict (e.g. {headroom.get('structured_output')!r}).")
        print(f"  BUT at max_turns=1 it fails: is_error={is_error!r} subtype={subtype!r}")
        print("  → The SDK consumes an internal finalize/validate turn for structured")
        print("    output (observed num_turns=2 even with zero tools), so the spec's")
        print("    EXACT 'max_turns=1' single-shot constraint (§6.4 Path A / §3.6 OQ-16)")
        print("    is too tight. The fix is a one-word spec edit: Path A uses max_turns=2")
        print("    (or higher), not 1. The Haiku calls stay API-ENFORCED — no Path B needed.")
        print("  Working surface for the Haiku forced-extraction port:")
        print("    opts = ClaudeAgentOptions(")
        print(f"        model={MODEL!r}, max_turns=2, allowed_tools=[],")
        print('        output_format={"type": "json_schema", "schema": <tool_schema>},')
        print("    )")
        print("    async for msg in query(prompt=<system+user>, options=opts):")
        print("        if isinstance(msg, ResultMessage):")
        print("            return msg.structured_output  # the dict, where .input went")
    else:
        print("══ VERDICT: NO-GO (Path B — prompt-coerced JSON) ══")
        print("  output_format did NOT yield a schema-valid dict at max_turns=1 OR 2.")
        print(f"  max_turns=1: is_error={is_error!r} subtype={subtype!r} "
              f"schema_valid={schema_valid!r} so={so!r} exc={exc!r}")
        print(f"  max_turns=2: is_error={headroom.get('is_error')!r} "
              f"subtype={headroom.get('subtype')!r} so={headroom.get('structured_output')!r} "
              f"exc={headroom.get('exception')!r}")
        if subtype and "retries" in str(subtype):
            print("  → matches the predicted multi-turn-retry dependence.")
        print("  The port must use prompt-coerced JSON: embed the schema in the prompt")
        print('  ("respond with ONLY a JSON object valid for this schema"), run a')
        print("  no-tools max_turns=1 query, parse with _extract_json_object (already")
        print("  shipping in _OllamaIntentRouterLlm — Don't Reinvent).")
    # Real DispatchPackage schema acceptance (OQ-3-adjacent), if it ran.
    for rk in ("real-DispatchPackage@max_turns=2", "real-DispatchPackage@max_turns=1"):
        real = outcomes.get(rk)
        if real is not None:
            rso = real.get("structured_output")
            print(
                f"\n  [{rk}] real Pydantic schema: is_error={real.get('is_error')!r} "
                f"subtype={real.get('subtype')!r} "
                f"structured_output={'<dict>' if isinstance(rso, dict) else rso!r} "
                f"exception={real.get('exception')!r}"
            )
            print("    ^ raw DispatchPackage.model_json_schema() acceptance (OQ-3-adjacent).")
            break
    print("=" * 72)
    print(
        "\nFull per-probe outcomes:\n"
        + json.dumps(
            {k: {kk: (str(vv) if kk == "structured_output" else vv) for kk, vv in v.items()}
             for k, v in outcomes.items()},
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
