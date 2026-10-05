# Main add-in integration acceptance

Scope: promote the existing workshop without changing manufacturing behavior.

1. Run local request/layout/mesh regressions against workshop/.
2. Build and extract the release independently: check entry point/manifest, offline assets, 39 SMT presets, both templates, license and README images. Exclude experimental/QA/export content.
3. Load the repository root using Fusion's add-in loader. Confirm two named Create buttons, idempotent start, and no palette opening during startup.
4. Open both registered commands; check ready WebGL previews and all six selector assets.
5. Run 32 catalog and 15 baseplate UI cases through native palette bridges.
6. Use deferred real DOM Create clicks for a standard dovetail bin, baseplate, cartridge and clasp bin. Check healthy solids, descriptive names and preservation of an overlapping sentinel. Verify one Undo/Redo on standard bin, separate-document imports for both templates.
7. Capture current preview canvases and actual generated model for README; inspect images. Perform presentation edits separately from transaction tests.
8. Stop, verify cleanup, restart and reopen production URLs. Close only disposable QA documents.

This is migration acceptance, not a repeat of the complete 48-case geometry suite. Manual mouse gestures, physical printing and macOS remain outside this run.
