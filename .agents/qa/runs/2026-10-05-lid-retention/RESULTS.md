# Dovetail retention results

Implemented None, bump/recess, magnetic and combined retention, with fixed 3 mm lid plate and optional stacking lip. Two magnet pairs use 3x2 or 6x2 mm discs, independent press/clearance fits. Default detent interference is 0.10 mm, adjustable 0.05-0.20 mm.

- All 11 local suites pass; release packaging validation passes (111 entries).
- Native cases 0-6 pass: healthy connected solids, zero closed intersection, free runout/removal, localized detent engagement, four 2 mm pockets for magnetic modes, fixed plate thickness, parameterized height edits, overlapping sentinel unchanged.
- 1x1 generation about 0.5-1.2 seconds; 6x6 divided 20U combined retention about 2.93 seconds, on this machine.
- Production request to native command succeeds, existing body preserved; single Undo and Redo verified. See create-standard.json.
- Model screenshots visually reviewed: rear body ledges and underside lid pockets match layout.
- UI automation incomplete: harness qaPing/qaSuite produced no acknowledgement, including after a fresh temporary palette. No automated DOM-control/Create-button pass claimed; ui-results.json contains null. Production catalog restored at v24. Local preview tests pass.
- Physical print validation still required for detent release force and magnet retention. No captive stop. User document retained; disposable QA documents closed.

QA pocket classification initially matched unrelated 1.75 mm cavity corners; corrected to also check the pocket Z span. No geometry change was required.
