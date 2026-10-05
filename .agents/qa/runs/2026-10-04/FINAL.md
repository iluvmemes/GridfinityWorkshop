# QA results after restart — 2026-10-04

**Updated after bridge investigation: QA-003 is closed as an unconfirmed product finding. The corrected end-to-end tests passed, including fresh reload. Manual pointer coverage remains unverified. See bridge-investigation/RESOLUTION.md.**

## Verified
- 48 deep CAD cases across seven suites; 32 catalog UI cases; 15 additional baseplate UI cases; nine local suites and syntax checks.
- Baseplate actual HTML Create succeeded at 1x1, skeleton, 6.08 mm press-fit magnets, 3 mm pockets and screws. Its single Undo and Redo preserved an overlapping existing body.
- Magazine production request -> native command succeeded in about 0.21 s; single Undo and Redo passed. Its HTML Create route subsequently passed twice, including after a fresh reload, with browser completion receipts and a single Undo/Redo check.
- Pin fit coupons created through the production request path in a separate document: 1.90, 1.95 and 2.00 mm bores, about 1.43 s. All five fit-test geometries passed the earlier CAD suite; the HTML button route subsequently passed with creating/complete receipts and Create re-enabled.
- Four malformed/oversized requests were rejected with no model changes or leftover pending jobs.
- Exactly four command definitions and two Create-menu controls remained; no duplicates. All disposable QA documents closed; zero user documents were opened or saved. Normal add-in restored, not QA HTML.

## Fixed and regressed
- QA-001: Fit tests forcibly selected 2D on every update. Preserve 3D/2D selection; only convert unsupported Parts to 3D.
- QA-002: Returning to a cached valid recipe retained a stale error. Clear the geometry validation error on a valid cache hit. Regression includes old-mesh disposal.

## Open findings and coverage limits
- **QA-003 — closed, not reproduced with a synchronized harness.** The earlier test did not establish browser readiness or correlate completion, so its missing/stale response evidence could not prove a callback defect. The unmodified production handler passed inspect, hide/reopen, fresh reload, magazine HTML Create, and fit-test HTML Create after explicit page acknowledgements. No production handler workaround was needed. See bridge-investigation/RESOLUTION.md for precise limits and evidence.
- The pre-restart stack overflow was associated with 378 nested MCP output writer wrappers. Restart restored useful transport output. No transport guards were changed. See transport diagnostics and initial REPORT.md.
- Pointer-driven orbit/zoom and narrow native-panel usability remain manually unverified. Synthetic control events do not prove those gestures.
- Some standard/dovetail sketches report not fully constrained despite fixed curves; native parameter-edit checks passed. Template seed constraints were verified explicitly.
- Magazine result metadata lists its intermediate solid-body name in `parts`, while the actual body has the correct descriptive magazine name. This is a minor metadata inconsistency; geometry/naming in the Fusion browser passed.

## Reuse
Use ../../README.md, build-harnesses.py, run-unit.py, fusion-suites.py, fusion-create-e2e.py and fusion-negative.py. test-status.json distinguishes PASS, PARTIAL and NOT VERIFIED. JSON evidence preserves the mechanism used, so API-level generation cannot be mistaken for a successful HTML button test.

The initial report contains detailed geometry coverage, measured timings, and the original interruption history. No commit or push was performed.
