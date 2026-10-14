# Repeat-friendly planning and focused editors

Run `python .agents/qa/run-unit.py` and `python .agents/qa/test-release.py`.
Run `node .agents/qa/browser-workflows.cjs` with Playwright available through NODE_PATH and installed Chrome. Browser screenshots go to ignored `runs/print-plan/`.
Through Fusion MCP, execute `verify-print-plan.py` and call its `run` entry point. It creates/closes only its disposable document and reactivates the original document.

## Coverage

- 27 Python/JS parity cases: three preferences, three anchors, ordinary/Husky/2500 mm drawers.
- Coverage, physical bounds, print quantities, exact descriptor equivalence after rotations.
- Narrow browser: design/print navigation, printer preferences across reload, unique/full output, catalog drill-down and per-family state retention, all six creation gates, no horizontal overflow or runtime errors.
- Wide browser screenshots: catalog and editor.
- Native Fusion: symmetric 6x6 layout (one unique body, four placements) and asymmetric padded layout with magnets and screw holes; unique/full intersection geometry under each placement rotation; volume equal to legacy envelope; healthy features. Full native test does not rely on collapsed timeline group health (Fusion returns Unknown for groups).
- Release extraction: new planners and UI helper ship offline with runtime assets.

## Design decisions

New plans use seams centered in the 0.5 mm gap between adjacent cell sockets, giving 0.25 mm boundary margins on each side. The complete drawer envelope and cached cell geometry remain unchanged. Rounded corners and bottom chamfers occur only on original exterior boundaries.

Planner search is bounded: uniform, balanced, centered-remainder, matching-edge partitions and minimum-count dynamic paths. Candidate ranking uses axis diversity, then exact rotated type grouping on finalists. This is a practical optimization, not a proof of globally minimal unique designs across every possible tiling. Repeat-friendly permits at most ceil(1.25 * minimum plate count). Symmetry breaks ties after type/plate counts. No reflected grouping.

New UI requests explicitly choose the new planner. Requests without planning/output fields retain legacy behavior for compatibility. Generated metadata includes the complete placement map in both output modes.

## Production command verification

Husky example through the production creation command: 5 bodies / 21 total prints in 3.25 s on the development machine. Single Undo removes the whole result; Redo restores it. This uses the command handler directly through Fusion MCP, not a simulated HTML Create click.

## Manual follow-up

- In Fusion, visually inspect palette sizing and tooltip focus at your normal docking width.
- Confirm Create via the palette yields the quantities shown; production command Undo/Redo is verified.
- Physical printing remains useful for checking seam mating; no new socket standard or magnet dimensions were introduced.

## Preview camera controls

Run `node .agents/qa/browser-camera.cjs` with the same Playwright setup. Covers both palettes at wide, narrow, and minimum sizes; asserts no vertical preview overflow, keyboard cube face selection, and Home restoration. Captures screenshots under `runs/print-plan/camera-*`. Camera control follows the existing X/right, Y/back, Z/up model convention.
