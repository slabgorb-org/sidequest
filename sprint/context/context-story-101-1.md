# Story 101-1: Align daemon renderer models with server contract

## Story Identity
- **ID:** 101-1
- **Type:** refactor
- **Points:** 3
- **Priority:** p2
- **Epic:** 101 — Split-Brain Remediation — Daemon Renderer Drift & Dead Twins
- **Repos:** daemon
- **Workflow:** tdd

## Title
Align daemon renderer models with server contract — remove CARTOGRAPHY tier + zimage configs, align StageCue.camera typing, add cross-repo contract test

## Story Summary

The daemon and server have a deliberately-duplicated renderer model subset. This subset has drifted:

1. **Daemon RenderTier** still carries `CARTOGRAPHY` (removed server-side 2026-04-28)
2. **Daemon RenderTier** carries two zimage-specific tier configs (not on server)
3. **StageCue.camera** is typed `CameraPreset` enum daemon-side vs plain `str` server-side
4. **No contract test** holds the seam — drift can recur silently

This story resolves all three sources of drift and prevents future recurrence.

## Acceptance Criteria

### 1. Daemon RenderTier Cleanup
- Daemon `RenderTier` no longer defines `CARTOGRAPHY` tier
- Daemon `RenderTier` no longer defines two zimage tier configs (identify exact config names in sidequest_daemon/renderer/)
- Verify by grep that neither term appears in production code post-removal
- All other RenderTier values (IMAGE, PORTRAIT, MUSIC, EMBED, ORCHESTRATION) remain unchanged and functional

### 2. StageCue.camera Type Alignment
- `StageCue.camera` is typed as plain `str` (matching server contract)
- No longer typed as `CameraPreset` enum daemon-side
- Serialization/deserialization of StageCue must accept any string camera value (no validation narrowing)
- Verify by type-checking that server and daemon StageCue definitions are compatible

### 3. Cross-Repo Contract Test
- A new contract test exists (location: suggest `sidequest-server/tests/test_daemon_renderer_contract.py` or `sidequest-daemon/tests/test_server_contract.py`)
- Test asserts that the duplicated-subset model (RenderTier, StageCue, and any other shared types) remains in sync between repos
- Test fails loudly if:
  - Daemon RenderTier fields diverge from server RenderTier fields
  - StageCue fields or types diverge
  - Any shared enum/model field is added/removed/renamed
- Test is wiring test: runs as part of daemon test suite and proves the contract is enforced
- No silent fallbacks: error messages are clear (e.g., "RenderTier.CARTOGRAPHY found in daemon but not in server contract")

### 4. Code Quality
- `ruff check .` passes in daemon repo
- `pytest` passes in daemon repo (new test included)
- No debug code or temporary workarounds left behind
- Branch is clean and ready for review

## Technical Context

### Repos Involved
- **sidequest-daemon**: Remove CARTOGRAPHY, zimage configs, align StageCue.camera, add daemon-side test or fixtures
- **sidequest-server**: May provide reference contract (via `pydantic` models or similar) for the test to validate against

### Key Files (Likely Locations)
- **Daemon models:** `sidequest-daemon/sidequest_daemon/renderer/` (models for RenderTier, StageCue)
- **Daemon media:** `sidequest-daemon/sidequest_daemon/media/` (any RenderTier enum or config)
- **Server models:** `sidequest-server/sidequest/renderer/` or `sidequest/protocol/` (reference RenderTier and StageCue definitions)

### Design Principles
- **No Silent Fallbacks:** If a tier is referenced but no longer defined, fail loudly with a clear error message.
- **Contract-First:** The test must prove the seam holds; code review cannot rely on faith.
- **Cross-Repo Wiring:** The test is the evidence that two separate repos maintain a shared contract. If the test doesn't run in both, it's not a real contract.

## Test Plan

### Unit Tests
1. Verify that RenderTier enum excludes CARTOGRAPHY and the two zimage configs
2. Verify that StageCue.camera accepts any string (no narrowing validation)
3. Verify serialization/deserialization roundtrip for StageCue with arbitrary string camera values

### Integration / Contract Tests
1. Load server RenderTier contract (via import or JSON schema)
2. Load daemon RenderTier definition
3. Assert equality (or subset relationship if intentional)
4. Assert StageCue.camera type is compatible (plain str, not enum)
5. Fail loudly if any field diverges

### Manual Verification
1. Daemon boots without errors: `just daemon-status`
2. Daemon CLI: `python -m sidequest_daemon --help` (no complaints about missing tiers)
3. Play a test scenario that exercises rendering (verify no CARTOGRAPHY fallback kicks in)

## Definition of Done

- [ ] Daemon RenderTier cleaned of CARTOGRAPHY and zimage configs
- [ ] StageCue.camera is plain `str` in daemon matching server
- [ ] Cross-repo contract test exists and passes
- [ ] `ruff check .` and `pytest` green in daemon
- [ ] Session file marked complete
- [ ] Ready for review phase
