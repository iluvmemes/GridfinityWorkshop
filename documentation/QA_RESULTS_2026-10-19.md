# Full add-in QA results — 2026-10-19

Executed on Windows in Fusion 2705.1.30, against the working tree based on commit `90e51ef9256f5bc8902b3dfff48cb769208bc6da`. The tree contained existing uncommitted work; this run did not reset or commit it. Source hashes and dirty status are saved in the evidence metadata.

**Result: all final executed checks passed.** This is the coverage below, not certification of every possible setting combination or physical print fit.

## Coverage and results

| Layer | Executed | Result | Evidence under outputs/full-qa/2026-10-19/ |
| --- | --- | --- | --- |
| Browser visual matrix | 219 cases: 64 catalog scenarios, eight baseplate scenarios and lettering dialog, each at 1000×780, 480×742 and 360×540 | PASS; zero runtime errors | visual-results.json, browser-stdout.txt, individual PNGs |
| Browser interactions | 24 checks: favorites/reload, fit profiles, family persistence, orbit/zoom/home, expansion, swatches, invalid/focus recovery, fit copy/apply, both fonts and valid/invalid SVG at three sizes | PASS | interaction-results.json, interactions-stdout.txt, interaction PNGs |
| Fusion embedded catalog | 64 scenarios at each of 1000, 480 and 390 px widths: 192 cases | PASS; current rendered family required, valid Create enabled, invalid Create disabled | native-1000-results.json, native-480-results.json, native-390-results.json |
| Fusion embedded baseplate | 15 scenarios at 1000 and 360 px widths: 30 cases | PASS | native-baseplate-1000-results.json, native-baseplate-360-results.json |
| Unit suites | All 21 saved JavaScript/Python suites | PASS | unit-results.json, including command, stdout, stderr and exit code |
| Native CAD suites | Standard/blank, baseplate, clasp, cartridge, magazine, fit tests, dovetail | All seven PASS | cad-suite-results.json and suite-specific JSON/stdout |
| Native lettering geometry | Both fonts × raised/engraved/separate, side/bottom faces, nested SVG island, assembly-context placement: ten cases | PASS | lettering-native.json |
| Native labeled lids/export | Cutout, raised and embedded lids; solid bodies, healthy features, production colored 3MF, millimeter units, one assembly and expected material meshes | All three PASS | native-label-results.json, label-*.3mf |
| Actual creation route | Baseplate plus all six families, through synthetic DOM Create click → production HTML bridge → native command/import | All seven PASS; existing sentinel solid preserved | create-*.json |
| Transactionality | Baseplate, standard, blank and magazine | One Undo restores sentinel-only design; Redo restores result | singleUndoVerified and redoVerified in create-*.json |
| Restart | Main add-in stop/start, controls, both palettes and production bridge acknowledgements | PASS; no duplicate control within a toolbar panel | restart-results.json, post-restart-inspect.json |
| Loaded source audit | 127 loaded top-level Python functions compared with compiled current source | All match | loaded-source-check.json |
| Offline packaging | Build and isolated extraction, source compilation, 39 SMT presets, fonts/templates and local HTML/SVG assets | PASS; 133 archive entries | release-stdout.txt |
| Cleanup/isolation | Disposable anchor stayed at zero bodies/timeline; all QA designs closed; original three documents retained and original active document restored | PASS | cleanup-results.json |

Fusion enforces a 390 px minimum catalog width, so 360 px catalog testing is browser-only. Native minimum-width testing used 390 px. Baseplate supports 360 px natively. Fit tests intentionally hide Parts; that matrix entry verifies fallback to 3D rather than an unavailable Parts workflow.

## Visual review

Reviewed the final screenshot contact sheets across all three browser sizes, full-size compact fit-test/blank examples, lettering dialogs and the 18 native default canvas captures. Checked solid/open interiors, dividers/channels, closure lids, exploded parts, magazine direction/cutouts, baseplate solid/skeleton/print views, label modes, error presentation, visible actions and responsive layout. Native capture sheets show the actual Fusion WebGL output; whole-palette browser PNGs provide layout evidence.

Final contact sheets are `review-final-<width>-*.jpg`; native defaults are `native-defaults-review.jpg`. Individual PNG names match case IDs in visual-results.json. Earlier diagnostic sheets and screenshots may remain in the ignored evidence directory; the final ledgers and `review-final-*` sheets determine this run's result.

## Findings and fixes

1. **Compact orientation HUD overlap:** the cube covered the last fit-test samples at narrow sizes. Reserved a 110 px WebGL strip for a smaller compact HUD, preserving the model aspect ratio in the remaining area. Added viewport-reservation assertions and reran the visual matrices and unit suites.
2. **Retired add-in running:** `GridfinityUIPreview` was running and configured for startup alongside the main add-in. Stopped it and disabled its startup setting. Restarted the main add-in and verified one control per intended command/panel, then reopened and inspected both production palettes. This is a local Fusion configuration fix.
3. **Custom blank regression:** revalidated the preceding fix for 1U solid stock, taller stock, optional rim, 2U open envelope and invalid 1U-open recovery. The default blank renders a solid 7 mm top rather than retaining a previous hollow mesh. Solid-top ray tests remain in the geometry suite.

Test-only corrections during execution included the engraving enum (`cutout`), selecting a favorite before reloading it, blurring an invalid field before asserting its error, awaiting asynchronous SVG reads and adding setViewport to the renderer test double. These were harness errors, not product failures. Final ledgers contain the corrected rerun results.

## Limits

- Browser pointer/keyboard tests and native synthetic DOM tests are identified above; they do not constitute a manual native mouse check of every control or every cube face/edge/corner.
- Camera-menu exhaustive direction coverage, every option combination, native operating-system file dialogs and physical print/retention fit were not exhaustively tested.
- Only this Windows/Fusion/GPU/display environment was tested. macOS, alternative DPI configurations and other Fusion versions remain unverified.
- Preview feet, closures and related mechanical interfaces remain simplified as described by the application; native CAD checks provide the manufacturing geometry evidence.

The reusable plan is [QA_PLAN.md](QA_PLAN.md). Runners are under scripts/qa/ and the existing .agents/qa/ suite directory.
