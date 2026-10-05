# Integration acceptance — 2026-10-05

PASS: main add-in promotion and documentation refresh. Fusion 2705.1.25 on Windows.

- Nine local request/layout/mesh regression suites passed against workshop/.
- Release ZIP independently extracted and checked: Python syntax, local HTML/SVG assets, README images, 39 SMT presets, both F3D templates and Third-party license. No experiments, QA or generated exports included.
- Native root add-in startup registered Gridfinity Baseplates and Gridfinity Bins without opening palettes. Repeated start did not duplicate controls.
- Promoted palettes rendered WebGL; all six model-derived selector images loaded.
- 15 baseplate + 32 catalog UI cases passed, including invalid/recovery and favorites. Catalog sweep left document/body/timeline counts unchanged.
- Deferred real DOM Create clicks passed for standard dovetail bin, baseplate, clasp and cartridge. All generated features healthy; overlapping sentinel preserved. Both imported templates opened separate designs.
- Standard creation passed one Undo and Redo. An initial attempt included screenshot visibility edits before Undo; that measurement was invalid. Repeated in a fresh disposable document with no intervening edits and passed.
- Stop removed controls/commands/palettes. Fresh root reload registered exactly one of each button with no unsolicited palette.
- Current preview canvas captures and actual Fusion model image were visually inspected and added to README. These are canvas/model views, not full-window UI screenshots.

The 48-case deep geometry suite from 2026-10-04 was not repeated: all manufacturing modules and presets were moved byte-for-byte (normalized line endings), with only launcher and baseplate UI wording changes. Manual pointer gestures, physical prints and macOS remain unverified.

See startup.json, restart.json, stop.json, unit-results.json, catalog-ui.json, baseplate-ui.json, create-*.json, preview-isolation.json and release.json.
