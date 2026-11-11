# Full add-in QA plan

Run against production HTML, JavaScript, CSS and Python. A previous passing run is not evidence for the current revision. Record failures and untested items explicitly.

## Acceptance and evidence

For every valid preview, require a ready WebGL mesh whose family matches the selected family, no preview error, finite nonempty bounds, no runtime errors, and a usable canvas. A stale mesh is a failure even if Create is enabled. Check that geometry matches the selected interior, dimensions, lid and parts. Review screenshots; automated readiness alone is insufficient.

At 1000×780, 480×742 and 360×540, require no horizontal document overflow, reachable scrolling controls, visible footer actions, readable labels/units, and an unobscured preview. Verify focus, invalid, disabled, selected and hover states. Capture whole-palette screenshots for all families and major variants. Keep evidence in outputs/full-qa/<run>/ with a machine-readable case ledger.

## Execution matrix

| Group | Cases and acceptance |
| --- | --- |
| Startup | Open both registered palettes; local styles/art/fonts/Three.js load; no duplicate controls; preserve existing user documents. |
| Defaults | Standard, clasp, cartridge, magazine, custom blank and fit tests at all three sizes. Check mesh family and status, proportions, feet versus flat bases, cavity versus solid, and Create gating. |
| Views | Every family: 3D, 2D, Parts, return to 3D. Fit view, orbit, zoom, orientation cube, expand/compact. Hidden views must not overlap. |
| Standard | 1×1 2U and 6×6 20U; open/divided; round/square/rectangular channels; valid spacing and overcapacity recovery; rim; base magnets off/press/clearance/custom; dovetail lid; retention none/bump/magnet/both; both magnet sizes/fits; show/hide lid; flat/stacking lid; engraved/embedded/raised lettering; both fonts, multiline and color swatches. |
| Clasp | Minimum/default height, open/divided/channels; lid visibility and Parts; buckle play, grip, pin allowance and per-part overrides; invalid bore and recovery. |
| Cartridge | Minimum/default height; body length/width; flat base, closure and channels; no base magnet controls; shared dimensions with magazine. |
| Custom blank | Default 1U solid, taller solid, optional rim, 2U open; invalid 1U open and recovery. Ray checks distinguish solid top from cavity floor. |
| Magazine | Both orientations, capacity, seat count, cutouts on/off, matched cartridge dimensions/height, invalid overcapacity and recovery. |
| Fit tests | Pin ladder, working closure, magnet ladder, spacing samples, envelope gauge; source copy and selected-fit application; valid sample ranges and rejection. |
| Lettering | Dialog at all three sizes; both fonts, text/SVG source, preview, multiline, operation and depth; invalid text/SVG; close/reopen; disabled unavailable actions. |
| Baseplate | Fit-space/grid modes; anchors/padding, skeleton/solid, magnets/screws, press fit/depth; 1×1 and 6×6; large split drawer; print list, unique/layout output; 2D/3D; invalid grid/bed and recovery. |
| Persistence | Family state retained across navigation; favorite save/load; printer fit profiles; reload persistence. Use isolated browser storage and restore native user storage. |
| Native bridge | Run UI suites in Fusion's embedded browser; record actual response acknowledgement, rendered family and errors; preview-only actions leave body/timeline counts unchanged. Synthetic DOM events are labelled. |
| Generation | Run existing native CAD suites in disposable QA designs: baseplate, standard/blank, clasp, cartridge, magazine, fit tests, dovetail. Check solid bodies, dimensions, feature health, parameters, sentinel preservation and cleanup. Never save or edit user documents. |
| Packaging | Run every saved unit suite and release extraction/local asset checks. Record commands, outputs and exit codes. |

## Reporting

Separate automated browser, native embedded-browser, native CAD and human visual evidence. Report the number of cases, failures, fixes and remaining gaps. Physical print fit, exhaustive option combinations, other operating systems and other DPI/GPU configurations remain outside this run. Do not label these passed.

## Saved runners

- `node scripts/qa/run-visual.cjs outputs/full-qa/<run>`: 64 catalog scenarios, eight baseplate scenarios and a lettering dialog check at each of three sizes. Saves screenshots and `visual-results.json`.
- `node scripts/qa/run-interactions.cjs outputs/full-qa/<run>`: persistence, profiles, orbit/zoom, focus/validation, expansion, swatches, fit application, both fonts and valid/invalid SVG import. Saves `interaction-results.json`.
- `python .agents/qa/run-unit.py outputs/full-qa/<run>`: every saved unit suite, with individual command/output/exit records.
- `python .agents/qa/test-release.py`: build/extract the offline release, verify assets and compile sources. Set TEMP/TMP to a writable test folder when required by the execution sandbox.
- `scripts/qa/visual-cases.js` and `native-visual.js`: shared catalog scenarios and an asynchronous Fusion bridge wrapper. Build a QA-only copy of catalog.html with a base URL to workshop/, append these scripts in that order, load through palette.htmlFileURL, then send `qaFullVisual`. Collect `catalog._last_response.qa` in a later Fusion call. It must acknowledge `kind: full-visual`; save results and decode optional default-preview images. Restore the production URL afterward.
- Reuse `.agents/qa/baseplate-harness.js`, `fusion-suites.py` and `fusion-create-e2e.py` for native baseplates, CAD suites and Create/Undo/Redo checks; the detailed procedure is in `.agents/qa/README.md`. Keep disposable documents and live callback acknowledgements; never infer readiness from elapsed time.
- `scripts/qa/native-labels.py`: execute through Fusion MCP with `sys._qa_module` pointing at the running add-in and `sys._gf_qa_out` at the run folder. Checks all three label modes and production colored 3MF exports in disposable designs.

The browser runners require Playwright and installed Chrome. Use the desktop bundled runtime when the project has no Node dependencies. This adds no dependencies or build steps to the add-in.
