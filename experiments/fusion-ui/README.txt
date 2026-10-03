Gridfinity Workshop Fusion palette
==================================

Run GridfinityUIPreview from Fusion Scripts and Add-Ins. Open the palette from
Design > Solid > Create > Gridfinity Workshop, or its promoted toolbar icon.
The Utilities > Add-ins shortcut is also retained. For a new installation,
Add Existing and select the GridfinityUIPreview folder. Run on Startup is off.

Create baseplate now creates real geometry in the active parametric design.
Fit a drawer or choose a grid up to 6x6; select solid/skeletonized, magnet pockets
(including 6.08 mm press fit), screws, alignment and print-bed size.
Pieces are separate bodies in their assembled positions, split at cell boundaries.
In Part designs they are added to the root; designs supporting components get a
new component. Cuts and splits explicitly target only newly generated plate bodies.
One Create action is one native Fusion command and one undo transaction.

Generation
----------
The standard socket and skeleton cutters are cached SMT geometry. Create arrays
copies into one base feature, then cuts a native extruded/filleted/chamfered blank.
It does not run the original generator or rebuild the mating profile from sketches.
Four uniquely named gf_*_padding_* user parameters drive the fully constrained
blank sketch; use Change Parameters to edit exterior padding. Grid size, hardware
and print seams are selected at creation time. Increasing padding later can exceed
the original print-bed size. The preview is local SVG and creates no CAD geometry.
The separate original bin/baseplate/lid generator remains unchanged.

Verification
------------
generation-verification.json records Fusion tests through 6x6: exact symmetric
BRep difference against reference plates, connected solids, feature health,
editable padding, bed fit and preservation of an overlapping unrelated body.
verify-generation.py is an explicit integration harness for a disposable test
session. prepare-generator-presets.py rebuilds the two cached cutter assets from
the captured source geometry. test-request.py checks input/layout boundaries.

The native Palette and command APIs handle lifecycle and undo. HTML uses the
supported adsk.fusionSendData / Palette.sendInfoToHTML bridge. No web server,
external resources, injected browser automation or PC control is required.

Command icon
------------
The shaded 2x2 plate icon has transparent skeleton centers and magnet pockets.
resources/16x16.png, 32x32.png and 64x64.png are native Fusion command assets.
Run build-command-icon.py with Pillow to regenerate them. Stop removes both
Create and Add-ins controls; starting again registers one of each.

Layout and print names
----------------------
New layouts receive a design-local GF01, GF02, ... identity. Body names include
drawer/grid source, piece number, layout row/column, piece grid size, finished
width/depth in mm, style and magnet diameter/depth. R1C1 is the upper-left piece
in the palette; rows run down and columns run right. Sketches, features, seams
and timeline groups share the layout identity. Body dimensions in names record
creation-time settings; later manual parameter edits do not automatically rename
them. Existing user bodies and names are left unchanged.

Bin catalog interface
-----------------------------
Solid > Create > Gridfinity Bins opens the separate bin catalog palette. Six
selectors cover standard, clasp, cartridge, indexed magazine, custom blank and fit tests.
The source spec is bin-catalog-spec.txt. Clasp CAD is validated; cartridge
grip and magazine envelopes remain proposed values pending prototype validation.
Standard, blank and clasp generation are enabled.
The working baseplate command is separate and remains enabled. Favorites are
local browser configurations; the cartridge and magazine share size settings.

Bin generation first iteration
------------------------------
Standard bins and custom blanks can now be created from Gridfinity Bins. Supported
interiors: open, regular compartments, round/square/rectangle magnet channels, and
solid stock. Standard cached feet and stacking rims support 1x1 through 6x6.
Base magnets include 6.08 mm press fit, 6.5 mm clearance, custom, or none.
Height is a named Fusion parameter; nominal height excludes the 3.8 mm stacking
rim extension. Native cavity bottoms sit 7 mm above the bottom of the feet.
Cached hardware is generated once per diameter/depth, then copied with the feet.
Cartridge and magazine families remain previews pending mechanical work.
Scoop and label ledge are rejected explicitly until implemented. Footprint and
interior layout changes require a new bin; only the named height is supported for
post-creation editing (keep it at least 14 mm). Native command failure rolls back
all geometry, and Create is one undo action. Original prototype files are unchanged.

Clasp generation
----------------
Clasp opens a NEW unsaved Fusion design with named Body, Lid and Buckle components.
The supported archive import runs from an native palette HTMLEvent, outside
command events. Import never modifies the active user's design; a failed import
or build closes only its own failed document. Closing the new design discards it;
it is not a single-command undo in the source document.

Footprint: 2..6 cells long, 1..6 cells wide. Height: 6..20U, nominal height includes
5 mm feet; closed height is nominal + 3.7 mm. Grid, height and closure dimensions
are native parameters. Open and divided cavities resize with CellsL/CellsW; channel
size/counts are chosen at creation and re-center when grid dimensions change.
When editing parameters directly, preserve the catalog limits and sufficient room
for the chosen channel array. Fusion parameter edits bypass catalog validation.
Part names record creation-time dimensions; rename them after manual size edits.

Default extra buckle play is +0.20 mm TOTAL: original 0.10 mm total becomes
0.30 mm total, or 0.15 mm per side. Pin bore stays independent. GripThickness is
2..4 mm; thinner tested tabs failed the existing edge chamfer. It is not outward
projection. Base magnets: off, 6.08 mm press, 6.5 mm clearance, custom diameter/depth.
Open, divided, round, square and rectangular channels use explicit body-only cuts.
The 2 mm floor is above the feet. The clasp reserves 12.2 mm for end hardware.

presets/clasp-template.f3d is a local parameterized copy of the user's reference.
parameterize-clasp.py documents its height/closure mapping and foot correction.
The original foot tapered from 41.5 mm over the whole 2.4 mm top section; the new
one adds the 0.25 mm clearance land, uses a 2.15 mm taper and 37.2 mm waist. The
rounded top land has 0.204 mm3 less material per foot than the clipped source cache
and no excess outside that standard reference. Native patterns keep grid edits
working. Original channel/window cuts stay suppressed. Side windows are not yet
an option. The original user's source documents remain untouched.

verify-clasp-generation.py runs a six-case native integration matrix. Evidence:
clasp/verified-generation.json. All checked features healthy, each role one solid,
zero assembly overlap, fully constrained storage seeds and a grid/height edit test.
Measured creation: 2.5..3.6 seconds for 2x1 cases; 8.24 seconds for 6x6/20U divided
with magnets. These include archive import and feature recompute. A test print
is still needed for latch flex/engagement, pin fit and magnet press fit.

Fit controls and calibration (2026-10-03)
---------------------------------------
Channel separation is the edge-to-edge material between adjacent channels, not
magnet-to-hole clearance. Default 1 mm, range 1..30 mm. Length/width spacing can
be linked or independent. Preview capacity and Python validation use the same
spacing formula; exceeding either axis is an error. Clasp exposes ChannelGapX/Y
as native parameters. Standard-bin recipes support the same inputs at creation.

Pin fit now uses physical PinDiameter + PinAllowance, measured across the full
bore diameter. Shared allowance is the default. Optional independent allowances
cover body hinge, lid hinge, lid latch and buckle. Effective bores are displayed;
the permitted effective range is 1.80..2.70 mm. Buckle lateral play is independent.
Old recipes retain body/lid hinge PinHole and lid-latch/buckle PinHole+0.20 mm;
migration exposes those differences as explicit overrides. New recipes have no
hidden additions. Native derived bore parameters follow the linked allowance.

Gridfinity Bins has a sixth selector, Fit tests. All tests open a new design:
- Pin ladder: 1..7 separate blocks, horizontal bores, engraved actual diameters.
- Working closure: actual 2x1 / 6U clasp template with body below z=12 mm removed;
  keeps the entire lid, buckle and closure interface. Reduced closed height 28.7 mm.
  Print the three parts separately with the same orientations as the full parts.
- Magnet ladder: engraved diameters, pockets opening underneath like bin feet.
  Default sweep includes 6.08 mm. Print with the text up; roof thickness is 2 mm.
- Channel spacing: 2..5 channels on each axis, round/square/rectangle, selectable
  stack depth 3..120 mm, linked or single-axis spacing sweep. Floor thickness 2 mm.
  Each coupon has a low engraved tab. Test one loaded coupon at a time, away from
  other magnets. Separation is not a guarantee against magnetic stack ejection.
- Drawer envelope: 3 mm footprint frame with optional posts at the closed height.
The requested set must fit inside a 251.5 x 251.5 mm area. No oversized truncation.

Copy source settings takes dimensions and fit settings from a catalog recipe.
After printing, select a sample and Apply selected settings to source. The next
creation uses the result; existing Fusion designs do not change. Closure applies
its current fit settings. Envelope tests are dimensional checks, not fit presets.
Printer/material profiles store named measured allowances, spacings and magnet
fits locally. No automatic material shrinkage assumptions are made. Favorites
continue to store the full catalog state, including migration of older entries.

Checks: test-bin-request.py, test-fit-test-request.py, test-channel-layout.js,
test-fit-tests.js, and verify-fit-generation.py (Fusion MCP). Measurement evidence
is clasp/fit-measurement-verification.json. It covers actual cylindrical bore
sizes, all channel centers, parameter edits, floor/pocket containment, reduced
closure height, gauge height, connected solids, feature health, and preservation
of every previously open design. Preview and native catalog routes are also checked.
