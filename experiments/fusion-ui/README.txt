Gridfinity Fusion UI Preview
===========================

This is a separate Fusion add-in for evaluating the interface only.
It does not import the generator or create/edit any design geometry.
All sizing and the illustrative top-view drawing run in the local HTML page.
The Create baseplate button is disabled. The Python message handler has no
generation action.

Open in Fusion
--------------
The prototype is linked in Scripts and Add-Ins as GridfinityUIPreview.
Run it there. While running, Design > Utilities > Add-ins contains the
Gridfinity UI Preview command, which reopens the palette after closing it.
The palette initially docks on the right. Drag its native title bar to float
it, and resize it for the wider two-column layout.
Run on Startup is disabled. Stop the add-in to remove its palette and command.

For a new installation, use Scripts and Add-Ins > Add Existing and select
the GridfinityUIPreview folder beside this file.

Supported API lifecycle
-----------------------
Application.scripts.addExisting(folder) registers the add-in.
Script.run(False) runs it as an add-in with persistent event handlers.
Script.stop() calls its cleanup entry point.
Palettes.add displays palette.html using Fusion's embedded browser.
Palette.sendInfoToHTML and adsk.fusionSendData exchange preview state only.
No web server, browser debugging injection, external resources, or UI automation
is required to run this prototype.

Scope
-----
Fit a space / explicit grid size, maximum 6x6, per-side wall clearance,
nine-position alignment, skeletonized/solid illustration, magnet/screw
indicators, print-bed sizing, assembled/exploded print-piece illustration.
The socket and skeleton outlines are exported from the captured Fusion section
curves in experiments/loft-cell/original-profiles.json. The drawing now uses one
continuous material surface per piece and masks for through-openings. The drawing
and split planner remain UI prototypes, not production CAD geometry or a
manufacturing validation. Pockets are illustrated in plan view; depth
is an input only. The existing bin/baseplate/lid generator is unchanged.

Files
-----
GridfinityUIPreview.py       Native palette and command lifecycle
GridfinityUIPreview.manifest Fusion add-in registration
palette.html                Interface markup
palette.css                 Responsive palette layout
palette.js                  Local preview calculations and bounded UI messaging

cell-profiles.js             Captured section outlines (generated)
preview-drawing.js           Continuous plate, socket shading, and opening masks
../build-preview-profiles.py Re-export captured curves to cell-profiles.js
