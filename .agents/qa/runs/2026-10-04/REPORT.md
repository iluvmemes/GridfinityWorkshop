# E2E QA run — 2026-10-04

Status: **Initial checkpoint; superseded by FINAL.md after the Fusion restart.**

## Completed
- Clean start confirmed: Fusion 2705.1.25, zero open documents. Add-in stop/run succeeded; exactly two Create-menu controls and four command definitions. Catalog launched through its registered command.
- Nine local suites passed, including a new regression suite. All production Python modules compiled; JavaScript syntax checks passed. See unit-results.json and syntax-results.json.
- **48 deep CAD cases passed across seven suites**: baseplates, standard/blank bins, clasp bins, cartridges, magazines, dovetail lids, and fit coupons. Covered up to 6x6, channels of all three shapes, independent pin bores, magnet fits, envelope measurements, parameter edits, magazine/cartridge interference, lid slide/retention, padding/splitting and existing-body protection. See cad-suite-results.json and per-suite JSON/stdout.
- **32 native catalog UI cases passed after fixes**: all six categories and selector art, live geometry changes, 2D/3D/Parts, invalid/recovery, magazine rotation/cutouts, five fit-test modes, and favorite save/load. These use synthetic DOM events in Fusion's real palette/WebGL renderer, not a mocked browser. Preview exercise left the anchor at 0 bodies and 0 timeline entries with no new documents. See catalog-ui-retest.json.
- Real Create-button route passed for standard (dovetail), blank, clasp and cartridge. Standard and blank each passed one-step Undo and Redo while preserving an overlapping sentinel body. Imported clasp/cartridge workflows correctly created separate documents. See create-*.json.
- Visually inspected the generated clasp screenshot; separate lid/buckle and base are present. Detailed mechanical checks are in the CAD evidence, not inferred from the screenshot.

## Defects fixed
1. **QA-001: Fit tests forced every update into 2D.** fitVisibility now changes only an unsupported Parts view to 3D; 3D and 2D choices persist. Catalog UI rerun verifies correct preview family instead of accepting a stale mesh.
2. **QA-002: Returning to the previous valid settings left an error displayed.** Shared preview now clears geometry-validation errors on a valid cache hit. A real Three.js regression checks invalid input, restoration of the cached geometry, error clearing, and disposal when replacing geometry. Native UI recovery cases also pass.

Assets are cache-versioned to v23. Manufacturing geometry code was not changed for these fixes.

## Measurements
- In the catalog UI rerun, the largest measured mesh-update interval was about 33 ms. This is JavaScript work/renderer submission timing, not input-to-photon latency.
- Native generation timings in the 48 deep cases ranged about 0.22–10.79 seconds. Full suites include additional measurements, geometry comparisons, imports and document cleanup.

## Transport interruption and test-harness correction
The magazine HTML Create route reported `Stack overflow (used 993 kB)`, with no geometry left behind and the sentinel intact. Direct dispatch of the same validated recipe through the normal native command succeeded in about 0.25 s. Diagnostics then found **378 nested `_NsSanitizedWriter` wrappers in sys.stdout**, ending at Fusion CatchOut. MCP script responses became empty and an API documentation query failed to parse its empty output. A subsequent failure traceback recursed in `__getattr__`, outside the generator. This is a transport blocker; no transport guards were modified. Restart Fusion before drawing conclusions about the magazine HTML route.

The QA harness also now defers synthetic Create clicks until the bridge handler returns, matching normal user-event timing. Retest the corrected harness in the fresh MCP session. Do not count the initial synchronous-click magazine failure as a confirmed production defect or as a pass.

## Remaining
- Baseplate palette's 15 UI cases and actual Create/Undo/Redo.
- Magazine actual Create/Undo/Redo in a healthy MCP session.
- Fit-test Create-button route (all five test geometries already passed the deep suite).
- Native resize/orbit/zoom interaction checks, invalid request/rollback route, final add-in reload and duplicate-control check.
- Restore production palette URLs and close QA documents. At interruption only disposable QA documents were present. It is safe to discard those during restart; no user documents were opened or saved.

## Limits / observations
- Native API generation tests do not prove pointer usability or physical printed fit.
- Closure/template families create separate documents; they are not described as an undoable addition to the original design.
- Some generated standard/dovetail sketches report isFullyConstrained=false even though their curves are fixed and native height edits passed. Full constraint status is therefore not asserted across every sketch; source-template seed constraints are explicitly checked by deep suites.
- Existing scoop/label manufacturing remains disabled; 3D only previews these options. This is existing product scope, not a regression.

See ../../README.md for reusable plan and exact runner procedures; test-status.json tracks checkpoint coverage.
