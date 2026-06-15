# Design Spec — 119-2: Re-auth the Narrator Choke Point to Subscription OAuth

**Date:** 2026-06-15
**Author:** Architect (Neo)
**Status:** Design — gated on 119-1 spike = **GO**. Do not implement until the spike
confirms an OAuth-authed `messages.create()` draws the subscription pool (no PAYG line).
**ADR:** ADR-101, Amendment (2026-06-15). **Epic:** 119. **Repo:** `sidequest-server`.

---

## 1. Goal

Move the single Story-91-1 Anthropic auth choke point off the API key (full PAYG,
~$150/mo) onto subscription OAuth, so the narrator (Sonnet) + classifier/router
(Haiku) + aside + archetype-inference all bill against the free Max subscription
**together**. The tool-use architecture (`complete_with_tools`), caching, OTEL,
and every narration contract are **untouched** — this is an auth change, not an
SDK or architecture change.

**Non-goal (119-3):** porting onto `claude-agent-sdk`. That is the mutually
exclusive NO-GO fallback if the spike shows raw-SDK-over-OAuth still PAYGs.

**Non-goal (119-4):** production token auto-refresh. 119-2 lands the static
env-token path (the spike's recipe, productionized); 119-4 generalizes it to an
auto-refreshing `ant` profile on the host. Design 119-2 so 119-4 is an extension,
not a rewrite (see §6).

---

## 2. The two edit sites

### 2a. `build_async_anthropic()` — `sidequest/agents/llm_factory.py` (~lines 77–97)

**Current:** reads `ANTHROPIC_API_KEY`, raises `LlmClientError` if unset, returns
`AsyncAnthropic(api_key=api_key)`. No OAuth/auth_token/base_url.

**Target — dual-mode, fail-loud (SOUL No-Silent-Fallbacks):**

- Read both `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN`.
- **Both set → raise.** The API rejects a request carrying both an API key and a
  bearer token; do not silently pick one. Fail at construction with a message
  naming the conflict.
- **Neither set → raise** (same loud failure the current code gives, generalized).
- **Token only → `AsyncAnthropic(auth_token=token)`** plus the `oauth-2025-04-20`
  beta (see §3 — this is the load-bearing subtlety).
- **Key only → `AsyncAnthropic(api_key=key)`** (unchanged path; preserved for
  local dev / anyone not logged into a sub, and for fake-SDK test injection which
  never reaches this function).

Keep the late-bound monkeypatch doctrine intact — consumers still look this up
through the module dict (`llm_factory.build_async_anthropic()`), and the wiring
test's fake is unaffected because it injects `sdk=` upstream.

### 2b. `AnthropicSdkClient.__init__` — `sidequest/agents/anthropic_sdk_client.py` (lines 142–147)

**Current:**
```python
self._api_key = os.environ.get("ANTHROPIC_API_KEY")
if sdk is None and not self._api_key:
    raise AnthropicSdkConfigError("ANTHROPIC_API_KEY not set — required …")
```

**Target:** the construction-time credential guard must accept token mode. Compute
a "credential present" boolean from `ANTHROPIC_API_KEY` **or** `ANTHROPIC_AUTH_TOKEN`
and raise only when `sdk is None and` **neither** is present. Keep the failure loud
(no fallback). Note this guard is belt-and-suspenders — `build_async_anthropic()`
(§2a) already fails loud — but it fires on the `sdk is None` real-construction path
and must not wrongly reject token mode.

**`api_key_present` property (lines 240–242):** currently `bool(self._api_key)`.
**Action required:** `grep -rn "api_key_present" sidequest-server` and audit every
consumer. If anything uses it as a "can we make real calls?" health gate, it now
returns a false negative in token mode. Either (a) generalize it to
`credential_present` (api_key OR auth_token) and update call sites, or (b) leave it
literally about the api key and confirm no consumer treats it as a liveness gate.
Decide based on what the grep finds — do not guess.

---

## 3. THE RISK — the `oauth-2025-04-20` beta header and how it composes with the cache beta

This is the part the story's "one-line change" framing hides, and the most likely
way 119-2 ships broken-but-passing-smoke-tests.

OAuth requests to `/v1/messages` require `anthropic-beta: oauth-2025-04-20`. The
codebase **already** sends an `anthropic-beta` header per-request for caching:
`extended-cache-ttl-2025-04-11` (`_EXTENDED_CACHE_TTL_BETA`, `anthropic_sdk_client.py:130`),
applied on the 1h-cache path (`anthropic_sdk_client.py:294`) and by the intent
router (`llm_factory.py:468`). `anthropic-beta` is a **comma-joined multi-value
header** — both betas must ride the same request.

Two failure modes to design against:

1. **Does the SDK auto-add `oauth-2025-04-20` in `auth_token=` mode?** Unknown —
   verify first. The `claude-api` reference says the SDK "honors the same profile
   resolution" as Claude Code and the Agent SDK (implying it may handle the OAuth
   beta automatically), but the raw-curl recipe adds the beta manually. **The
   119-1 spike must record which.** If the SDK auto-adds it → §2a is sufficient and
   nothing else is needed. If it does **not** → proceed to (2).

2. **If the beta must be added manually, a client-level `default_headers={"anthropic-beta": "oauth-2025-04-20"}` will be CLOBBERED, not merged,** on every call that
   passes `extra_headers={"anthropic-beta": _EXTENDED_CACHE_TTL_BETA}` — httpx
   per-request headers override client defaults for the same key. That silently
   **drops the cache beta** (cache stops engaging → cost regression) **or the oauth
   beta** (400 / PAYG), depending on which wins. The safe fix is to **join both
   betas at each call site** that sets `anthropic-beta`, i.e. send
   `"oauth-2025-04-20,extended-cache-ttl-2025-04-11"`. Enumerate every site first:
   `grep -rn "anthropic-beta\|extra_headers\|_EXTENDED_CACHE_TTL_BETA" sidequest-server/sidequest/agents`
   (known: `anthropic_sdk_client.py:294`, `llm_factory.py:468`; re-grep to be sure
   `complete_with_tools` and the other Haiku adapters are covered). Centralize the
   join so a future beta isn't forgotten at one site.

---

## 4. What stays untouched

- `complete_with_tools` (`anthropic_sdk_client.py:248–705`) — the ~120-line manual
  tool-use loop. No changes. (This is the whole point of choosing 119-2 over 119-3.)
- Tool registry / schemas, model routing, cost ledger (ADR-134), perception
  filtering, every narration tool contract.
- Cache TTL logic (1h stable prefix / 5m volatile tail) — but **verify it still
  engages** post-swap (§5).

---

## 5. Verification / acceptance criteria (for TEA)

The smoke test is "narrator still talks." That is **insufficient** — it passes even
if caching silently died (a pure cost regression) or if the call is secretly still
PAYG. Require:

1. **Construction contract (unit, fail-loud):** both-set → raises; neither-set →
   raises; token-only → constructs in token mode; key-only → constructs in key
   mode. No silent fallback on any branch.
2. **Beta-header composition (the §3 guard):** assert the outbound request carries
   **both** `oauth-2025-04-20` **and** `extended-cache-ttl-2025-04-11` in
   `anthropic-beta` on a 1h-cache call. A fake-SDK capture of the request kwargs is
   the cleanest assertion (no live call needed).
3. **Tool loop converges (integration):** drive a real `complete_with_tools` turn
   through the token-mode client (fake SDK) and assert it terminates on `end_turn`
   with the expected tool round-trips — proves the auth swap didn't disturb the loop.
4. **Cache still engages (live, operator/playtest):** on a real session, turn 2+
   shows `cache_read_input_tokens > 0`. This is the only check that catches a
   clobbered cache beta; it needs a real call, so gate it behind the same
   live/opt-in marker the existing cache tests use.
5. **Billing lands free (operator, the actual win):** a real session shows **no
   PAYG line** on the Console for the app's calls. This is 119-1's signal re-run as
   post-merge confirmation; OTEL cost spans (ADR-134) still emit but now measure
   subscription-pool draw, not dollars.

A wiring test (per the server's "every suite needs one") already exists for the
choke point (the monkeypatched-fake path through `build_async_anthropic`); extend
it to assert the token-mode branch is reachable from the production construction
path, not just the key-mode branch.

---

## 6. Runtime / ops (and the 119-4 boundary)

- **`ANTHROPIC_API_KEY` MUST be unset in the server env.** A set key overrides the
  token and the API rejects both-set. Document this in the run recipe (`just server`
  env, deployment env). The §2a both-set guard turns a misconfig into a loud boot
  failure instead of a silent PAYG regression.
- **119-2 uses the static env token** (`ANTHROPIC_AUTH_TOKEN`, from
  `ant auth print-credentials --env`) — the spike's recipe, productionized. The
  token is **short-lived and not auto-refreshed**; a long-running server will see
  it expire.
- **119-4 owns durability:** swap the static env token for an auto-refreshing
  `ant auth login` profile resolved on the host (a bare `AsyncAnthropic()` resolves
  the profile and refreshes). Design 119-2's §2a so token mode is one branch of a
  credential selector — 119-4 then adds a "profile" branch rather than rewriting.
  Do **not** bake a static token into an image or commit it.

---

## 7. Why not just go to 119-3 now?

119-3 (Agent SDK port) is email-*confirmed* free and is the correct fallback, but
it's an 8-point rewrite of `complete_with_tools` onto a different loop/tool model,
re-expressing the Pydantic tool schemas, while preserving every contract + OTEL.
119-2, if the spike is GO, gets the identical billing outcome for the cost of this
spec's seam — with zero architecture risk. Verify cheap-path-first; commit to the
port only on NO-GO. (ADR-101 Amendment 2026-06-15.)
