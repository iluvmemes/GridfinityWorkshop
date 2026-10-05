# Gridfinity Workshop end-to-end QA

Scope: main Fusion add-in at GridfinityWorkshop.py, with runtime in workshop/; all six bin families and baseplates. Maximum grid size 6x6. Use Fusion MCP and its documented API, not desktop automation. Never modify user documents. Create named disposable QA designs and close only those designs without saving.

## Repeatable sequence
1. Record git revision/dirty state, Fusion version, open documents and command state. Reload add-in via Scripts API; inspect Create menu controls/icons for duplicates. Launch both palette commands with a blank QA design.
2. Run all existing request/layout/preview unit suites. Record each command, exit code and stdout separately. Syntax-check JS and compile Python without generating tracked bytecode.
3. Exercise native HTML palette bridge: six categories, dimensions, height, open/divided/solid interiors, round/square/rectangular channels, spacing, press fit, lids, magazine rotations/cutouts and five fit-test types. Check ready/error/overflow/art reports; capture rendered canvases. Check 2D/3D/Parts. Invalid input must disable Create, preserve last valid mesh, and recover. No model/timeline changes during previews.
4. Exercise generation through the normal create request/command route for baseplate, standard, blank, clasp, cartridge, magazine and fit tests. Verify result and status, document routing, meaningful names, solid bodies, health, timeline groups, constrained layout sketches and editable parameters. Undo/redo transactional in-document families. Imported closure families create separate documents; document that distinction.
5. Run deeper geometry suites: 1x1 through 6x6, split/padded plates, magnet diameters/depths, independent pin allowances, closure clearance, magazine/cartridge interference, optional cutouts, channel spacing, height edits, dovetail retention/slide. Existing overlapping sentinel bodies must remain unchanged.
6. Reload add-in; confirm no duplicate controls and palettes reopen. Close only QA designs. Record pass/fail/not-tested separately, timings, fixes and remaining limitations.

## Case IDs
- START-01 clean session, START-02 registration/restart, START-03 palette launch
- UNIT-01 request validation, UNIT-02 channel/fit planning, UNIT-03 mesh generation
- UI-01 six selectors/art, UI-02 3D control updates, UI-03 2D/parts, UI-04 invalid/recovery, UI-05 no model edits, UI-06 favorites/persistence, UI-07 resize/orbit/zoom
- CREATE-01 baseplate, CREATE-02 standard, CREATE-03 blank, CREATE-04 clasp, CREATE-05 cartridge, CREATE-06 magazine, CREATE-07 fit tests
- CAD-01 plate boundaries/padding/splitting, CAD-02 standard interiors/height, CAD-03 closure dimensions/bores, CAD-04 cartridge dimensions, CAD-05 magazine interference, CAD-06 fit samples, CAD-07 dovetail
- SAFE-01 overlapping bodies preserved, SAFE-02 undo/redo, SAFE-03 invalid request/cleanup
- END-01 reload/duplicates, END-02 disposable cleanup

## Evidence and execution
Store this plan, reusable runners, screenshots and dated run results here under .agents/qa. Existing repository tests may be invoked unchanged; historical JSON files are not fresh evidence. API-level generator tests are integration coverage, not proof of mouse interaction. Native palette bridge tests cover actual HTML/JS/WebGL and bridge responses; synthetic clicks must be identified. Manually unverified pointer interactions and physical print fit must not be reported as passed.

## Running the saved tools
- `python .agents/qa/run-unit.py [output-directory]` executes all eight existing suites plus the new preview-state regression. Outputs command lines, stdout, stderr and exit codes.
- `python .agents/qa/build-harnesses.py` rebuilds the QA-only palette HTML with a base URL pointing to the production assets. The application JS is unchanged; the harness adds narrowly scoped qaSuite/qaCreate bridge actions. Synthetic Create clicks are deferred until after the bridge callback returns.
- Through Fusion MCP, create a disposable anchor and retain it as `sys._gf_qa_anchor`. Set `sys._gf_qa_out` to the dated run folder (optional; default is runs/local).
- Load `fusion-suites.py` using `exec(Path(...).read_text(encoding='utf-8-sig'), namespace)` and call `namespace['run_suite'](name)` once per MCP call. Names: cartridge, magazine, dovetail, fit, clasp, baseplate, bin. Existing assertions are reused; fresh output paths are redirected here. Keep the anchor open; no user documents are required.
- Open the catalog using its registered command. Assign its palette.htmlFileURL to catalog-harness.html; wait for load, then sendInfoToHTML('qaSuite','{}'). Read catalog._last_response in a later MCP call; save the `qa.results` array. Expect 32 cases. Record model counts before/after to prove preview isolation.
- Equivalent baseplate harness action runs 15 cases. Read the add-in root module's _last_response.
- To test creation, load fusion-create-e2e.py. Call request_ready(), then in a separate MCP call verify the qaPing acknowledgement and call prepare(family). The runner now refuses to dispatch without the expected harness version and matching page URL. Repeat the handshake before each case. In a separate call, finish(family) checks native result, feature health and the overlapping sentinel. For standard/blank/magazine/baseplate, execute registered UndoCommand, check_undo in a later call, execute RedoCommand, then check_redo in another call. Finally cleanup closes only QA documents. For clasp/cartridge/tests, finish then cleanup; these are explicitly separate-document workflows.
- Restore both palette URLs to production HTML after testing. Stop/run the add-in through Scripts API, confirm one control per command, then close only QA documents and the anchor.

## Harness cautions
Do not compare Fusion body enumeration order across Undo/Redo; compare identities/names and measurements. Deep-copy UI snapshots immediately because preview stats are mutable. Verify the rendered family matches the selected family when in 3D; a stale but valid mesh is not a pass. Do not call synthetic clicks synchronously from inside the JavaScript bridge handler.
If the MCP transport starts returning empty output or `Stack overflow` in `_NsSanitizedWriter.__getattr__`, record diagnostics and restart Fusion before continuing. Do not mistake a transport failure for a passing or failing geometry test. The first run reached 378 nested writer wrappers; no transport guards were altered.


### Bridge investigation resolution (2026-10-04)
The earlier reload finding was not established as an add-in defect. A traced production handler received inspect correctly; after removing instrumentation, normal inspect, hide/reopen, fresh stop/start, and acknowledged magazine/fit-test Create round trips passed. Browser receipts confirmed creating -> complete and re-enabled Create. No production event-handler change was needed.
The old harness replaced HTML and assumed the next bridge action was ready, then inspected shared last-response/result fields without a page acknowledgement. That cannot distinguish delayed/stale QA state from an actual creation failure. v6 adds qaPing with page URL/version and qaReceipt with bounded status history; fusion-create-e2e.py enforces the handshake. Never infer readiness from a visible panel or elapsed time. If the response has not arrived, wait/poll in another MCP call; do not call prepare or count it as a product failure.
Evidence: runs/2026-10-04/bridge-investigation/RESOLUTION.md. Real pointer gestures remain separate manual coverage.

## Main add-in / release checks

Run `python scripts/build-release.py` to produce an installable ZIP, and `python .agents/qa/test-release.py` to verify isolated extraction, syntax, presets and local asset references. The same checks run in the release workflow. The main entry point is `GridfinityWorkshop.py`; disable the retired `GridfinityUIPreview` registration.

Integration evidence: `runs/2026-10-05-integration/`. Keep screenshot/model presentation changes separate from Undo checks: even changing body visibility can add an undo entry. Rerun creation in a clean disposable document when needed.
