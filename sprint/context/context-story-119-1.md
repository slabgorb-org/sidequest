# Story 119-1 Context

## Title
Spike (operator-run, go/no-go): does the raw anthropic SDK authed via subscription OAuth draw the Max Agent SDK credit, or still bill PAYG? Anthropic help blesses Claude Agent SDK usage specifically, so raw-Messages-SDK-over-OAuth qualifying is UNVERIFIED. Harness (full recipe in context doc): ant auth login to the Max workspace, unset ANTHROPIC_API_KEY, export the OAuth token as ANTHROPIC_AUTH_TOKEN, fire a few tiny messages.create calls on model claude-haiku-4-5 with the oauth-2025-04-20 beta header. SIGNAL: watch the Agent SDK credit meter in subscription billing draw down (positive); absence from the Console Cost page is a WEAK signal (it commingles interactive 5-hr-cap overage). Confirm the 200 credit is not already exhausted; run from a shell not also doing interactive Claude Code. Deliverable: a written GO/NO-GO that selects 119-2 vs 119-3 plus the reusable snippet. Operator runs the login and reads the meter; agent preps the harness and records the verdict.

## Metadata
- **Story ID:** 119-1
- **Type:** chore
- **Points:** 2
- **Priority:** p1
- **Workflow:** trivial
- **Repo:** server
- **Epic:** Narrator inference on the Max Agent SDK credit — stop paying PAYG

## Problem
The whole epic forks on one unverified fact. Anthropic's help doc says the Agent SDK
credit covers *"Claude Agent SDK usage in your own projects (Python or TypeScript)"* and
*"the `claude -p` command"* — it does **not** promise that the **raw `anthropic` Messages
SDK** (what SideQuest uses today via `messages.create()`) qualifies when authenticated
with a subscription OAuth token. If it does, the migration is a ~2-edit re-auth of one
choke point (119-2). If it doesn't, it's a full port to the `claude-agent-sdk` package
(119-3, ~8pts). A 30-minute experiment settles which — do not start either migration
before this returns a verdict.

## Technical Approach
Operator-run probe (Keith must do the login + read the billing meter; the agent prepares
the snippet and records the verdict).

```bash
ant auth login                                   # browser → choose the Max 20x workspace
unset ANTHROPIC_API_KEY                           # MUST be unset — a set key overrides the
                                                  # token, forfeits the credit, and the API
                                                  # rejects both-set
set -a; eval "$(ant auth print-credentials --env)"; set +a   # exports ANTHROPIC_AUTH_TOKEN
```
```python
import anthropic
c = anthropic.Anthropic()  # picks up the OAuth profile / ANTHROPIC_AUTH_TOKEN
# size to a few cents and fire ~5x so the spend is observable on the meter
for _ in range(5):
    c.messages.create(
        model="claude-haiku-4-5", max_tokens=64,
        messages=[{"role": "user", "content": "ping — billing attribution test"}],
        extra_headers={"anthropic-beta": "oauth-2025-04-20"},  # required on /v1/messages w/ bearer
    )
```

**Measurement protocol (the signal design is the hard part, not the call):**
- **Positive signal:** the **Agent SDK credit meter** (in *subscription / plan billing*,
  NOT the Console "Credits $50.52" nav — that's the pool-3 PAYG buffer) draws **down**.
- **Weak signal:** "did it appear on the Console *Cost* page." The Console commingles
  Keith's personal interactive **5-hour-cap overage** (the Fable/Opus slivers on the
  chart) with API-key spend, so absence there is *suggestive*, not conclusive.
- **Pre-conditions (in order):**
  1. **The credit must be CLAIMED first.** The Agent SDK credit is opt-in — eligible users
     got a one-time "claim your credit" email; you claim once via the Claude account, then it
     auto-refreshes each cycle. **If unclaimed, the credit is inactive and the spike falsely
     reads NO-GO.** Verify it's claimed before running anything.
  2. Confirm the $200 credit is **not already exhausted** this cycle (else a credit-path call
     overflows to PAYG and looks identical to NO-GO).
  3. Run from a shell that is **not** simultaneously doing interactive Claude Code (so pool-1
     overage doesn't pollute the read).
- **Where to read the meter:** the **subscription** side, not the Console. Claude Code
  `/usage`, or claude.ai → Settings → Usage/Billing (the Agent SDK credit section). NOT the
  Console "Credits" nav (that's the pool-3 PAYG buffer) and NOT the Console Cost page (API/PAYG).
  Exact web path is not yet pinned in Anthropic's public docs — `/usage` in Claude Code is the
  most reliable readout.

## Scope
- **In scope:** the auth/billing experiment, a written GO/NO-GO verdict, and the reusable
  test snippet committed to the story session for 119-2/119-3 to reuse.
- **Out of scope:** any server code change. This story changes no production code — it only
  produces the decision that unblocks (and selects between) 119-2 and 119-3.

## Acceptance Criteria
- **AC1 — Verdict recorded.** A clear **GO** (raw `anthropic` SDK over subscription OAuth
  drew the Agent SDK credit) or **NO-GO** (it billed PAYG / was rejected), with the
  observed meter evidence noted.
- **AC2 — Fork selected.** GO ⇒ activate **119-2** and **cancel 119-3**; NO-GO ⇒ activate
  **119-3** and **cancel 119-2** (they are mutually exclusive).
- **AC3 — Reusable artifact.** The working auth snippet (login → token export → tagged
  test call) is captured so the chosen migration story can reuse it verbatim.
- **AC4 — No production change.** Confirm no server code or committed env was modified by
  the spike itself.

---
_Generated by `pf context create story 119-1` from the sprint YAML._
