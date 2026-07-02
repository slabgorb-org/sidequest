# Story 158-50 Context

## Title
ADR-130 orbital course/story-clock inert in play: IntentRouter never emits a course dispatch because its state summary has no <courses> block (built only for the narrator), so router-gated course-emission can't fire — plotting/executing a transit writes no plotted_course + never advances clock_t_hours (SWN-ORBITAL-COURSE-INERT re-confirmed)

## Metadata
- **Story ID:** 158-50
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** sidequest-server
- **Epic:** Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Problem
Found in the 2026-06-27 GM /sq-playtest space-scale verification (solo space_opera/coyote_star, SWN, player "Shemp", Survey Runner, slug 2026-06-27-coyote_star-f100b7ae). Re-confirms SWN-ORBITAL-COURSE-INERT (150-17) live, and pins the root cause.

SYMPTOM: plotting a transit in natural language ("plot a course / lay in a burn to The Horn") AND executing it ("light the main drive, execute the burn") writes NOTHING mechanical. Across both turns: plotted_course=None, clock_t_hours=0.0 (orrery STARDATE frozen at 0.0), days_elapsed=0, pending_time_skip_summary=[]. The only write is a flavor scene-title change ("The Kestrel — In Transit to The Horn", a POI within region far_landing via narrator.location_drift_repaired). The narrator improvises the burn/transit prose; the orrery renders beautifully but is a read-only decoration (static labels + RESET button, no clickable course targets, clock never ticks even while "in transit").

OTEL (absence): no course/orbital/time_skip dispatch span fired — not even course.plot.rejected. The intent_router ran (Haiku) but emitted no course dispatch. No dispatch_engagement.course.mismatch lie-detector fired either, so the GM panel would not flag the improvisation.

ROOT CAUSE (half-wired trigger — the CLAUDE.md anti-pattern): the course subsystem is implemented and registered but the router can never produce its trigger.
  - run_course_dispatch IS registered in the dispatch bank (sidequest/agents/subsystems/__init__.py:213, ("course", run_course_dispatch)), and orbital_content IS threaded into the bank context (intent_router_pass.py:1139). The dispatch-engagement lie-detector for "course" exists (dispatch_engagement_watcher.py:447/462).
  - The IntentRouter (Haiku) prompt gates course emission: "Emit course ONLY when the world has an orbital tier (a <courses> block is present in game_state) AND the player declares travel to a NAMED body" (sidequest/agents/intent_router.py:287-300).
  - BUT the router's own state summary never contains a <courses> block. compute_courses / format_courses_block are called only for the NARRATOR prompt (orchestrator.py:2817-2849) and narration_apply.py — NOT in intent_router_pass.py (which builds the router summary; grep: zero compute_courses/format_courses there). So the router never sees a <courses> block, follows its own "ONLY when present" rule, and never classifies travel → never emits a course dispatch → run_course_dispatch is never invoked.
  - NOTE on the actor_location_unresolved red herring: the log shows intent_router.state_summary_slimmed projection_skipped reason=actor_location_unresolved, but per the code comment (intent_router_pass.py:436-437) an unresolved location makes the projection PASS THROUGH (bigger prompt, not gaslit-empty) — it does NOT drop a courses block. The block simply isn't assembled for the router at all. (The unresolved party_location may be a separate coyote_star-cockpit issue worth a glance, but it is not what starves the course trigger.)

FIX DIRECTION (Dev's call): assemble a <courses>/orbital-tier block into the router's state summary in intent_router_pass.py (reuse compute_courses + format_courses_block, Don't Reinvent), gated on the world having an orbital tier (session.orbital_content present) — so the router can classify travel intents and emit a course dispatch. Then run_course_dispatch commits the PlottedCourse + advances clock_t_hours, and the orrery STARDATE ticks. Alternatively relax the router's gating to detect the orbital tier from a field already in its summary. Either way: a wiring test that a NL travel-to-named-body action in an orbital world produces a course dispatch + non-None plotted_course + advanced clock_t_hours (OTEL span assertion, not source-grep).

SCOPE: course/clock only (the dogfight half is story 158-49). Ground/personal SWN combat is unaffected (already green).

Evidence screenshots (oq-3): playtest-shots/course-001-orrery-baseline-stardate0.png, playtest-shots/course-002-intransit-but-stardate-still-0.png.

## Technical Approach
_Approach hints to be refined by TEA/Dev. The story title above defines the
intended behavior._

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- RED wiring test (OTEL span assertion, not source-grep): a natural-language travel-to-named-body action in an orbital world (coyote_star) produces a 'course' SubsystemDispatch and run_course_dispatch fires — assert a course.plot (or course.plot.rejected) span emits where today none does.
- The IntentRouter's state summary includes a <courses>/orbital-tier block when session.orbital_content is present, so the router can classify travel and emit a course dispatch (reuse compute_courses/format_courses_block; Don't Reinvent).
- After a successful plot, plotted_course is non-None (a PlottedCourse to the resolved body) and clock_t_hours advances by the computed transit time; the orrery STARDATE ticks off 0.0. Verify in the snapshot, not the narration.
- No silent fallback: an orbital world that cannot resolve the destination/party-anchor fails loud via course.plot.rejected (no_orbital_tier / no_party_anchor), never a phantom course or a narrator-improvised transit with frozen clock.
- The dispatch_engagement.course.mismatch lie-detector fires when the narrator prose claims a transit but no course dispatch backed it — so the GM panel flags this class of improvisation going forward.
- Regression: non-orbital worlds (no orbital tier) are unaffected — no <courses> block, no course dispatch, no spurious clock advance.

---
_Generated by `pf context create story 158-50` from the sprint YAML._
