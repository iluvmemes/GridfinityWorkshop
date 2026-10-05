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
The source spec is bin-catalog-spec.txt. Clasp and cartridge CAD are validated; magazine generation is also enabled. Standard, blank, clasp, cartridge and
magazine generation are enabled.
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
Magazine generation is described below.
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


Cartridge generation (2026-10-03)
--------------------------------
Select Cartridge > Create cartridge design. Opens a new unsaved design from
presets/cartridge-template.f3d, containing only Body, Lid and Buckle. The original
prototype remains untouched, including its unrelated standard-bin component.
Body length: 30..220 mm; width: 12..80 mm; height: 4..20U. End hardware adds
12.2 mm to length; closed height is 7*U + 3.7 mm. Flat base, no Gridfinity feet
or retention magnet sockets. The minimum closed height is 31.7 mm.

Length, Width, HeightUnits, BuckleExtra, GripThickness and the shared/per-part
pin allowances are editable native parameters. The pull tab matches the clasp
profile. Open/divided interiors have 2 mm walls and floor; channels support
round, square and rectangle shapes, count limits, and linked/independent gaps.
Interior type and counts are chosen at creation. Size edits must preserve room
for the chosen array; manual Fusion edits bypass catalog validation. Names and
recipe/envelope attributes record creation-time values, not live dimensions.

verify-cartridge-generation.py checks eight disposable designs: dimension
boundaries, measured envelopes, body/lid/buckle interference, floor and cavity
containment, actual pin diameters, native size edits and channel spacing edits.
Results: cartridge/verified-generation.json (about 2 seconds per design here).
prepare-cartridge-template.py records the native grip/height template build on
a sanitized disposable prototype copy. Physical buckle engagement still needs
a test print. Fit profiles work for cartridge; the separate working-closure
coupon currently uses the clasp bin geometry. Magazine generation is described below.


Magazine generation (2026-10-03)
--------------------------------
Gridfinity Bins > Cartridge magazine > Create magazine. Default 2x1 holds two
68x17.5 mm cartridges. Footprint 83.5x41.5 mm; 0.3 mm seat clearance per side.
Uses the cartridge body's shared length, width and height (4..20U), with 12.2 mm
additional end hardware length. Orientation 0/90; grid up to 6x6; 1..48 seats.
Capacity and guide height are validated before creation. Unused positions remain
solid. Guide height is measured from the base, minimum 2U; leave at least 10 mm
of cartridge body exposed. Loaded height = cartridge nominal height + 10.7 mm.

Standard cached feet support no magnets, 6.08 mm press fit, 6.5 mm clearance and
custom pockets. Floor is 2 mm above the 5 mm feet. Low 2 mm end stops locate the
shorter body, while upper seats clear the full hinge/buckle envelope. End access
openings expose the buckle; symmetric cartridge bases do not impose a keyed
orientation. Outer guide margins are at least 1.2 mm; internal webs are 1.2 mm.

Creates one named magazine body in the current design through the native command
transaction. Every cut explicitly targets that body. Six modeling features are
grouped in one timeline group. A named guide-height parameter remains editable;
footprint, matched size, clearance, quantity and orientation are chosen at creation.
Names/recipe metadata record creation-time values. No cartridges are generated.

Validation: test-magazine-request.py and verify-magazine-generation.py. Seven
Fusion cases verified actual cartridge solids at every occupied seat (zero overlap),
low stops, floors, foot magnet diameters, dimensions, height edits and an existing
intersecting solid left untouched. About 0.34 seconds for 2x1/two seats; 3.1 seconds
for the tested 6x6/48-seat recipe. Results: magazine/verified-generation.json.
Print a small magazine to verify practical insertion, retention and finger access.


Optional magazine access cutouts
--------------------------------
Buckle access cutouts is an explicit magazine checkbox. New configurations default
to 2U (14 mm overall; 7 mm guides above the floor), cutouts off. Enabling it opens
both closure ends above the low stops. Closed-end magazines use five modeling
features; cutout magazines use six. Saved recipes/favorites predating the checkbox
retain cutouts on, preserving their previous geometry. Selection applies at creation.
Verified on/off at 2U in both 0 and 90 degree orientations with 4U matched cartridges;
end-wall point containment and feature counts agree with the toggle.


Rim-height magazine end stops
----------------------------
End stops now extend flush to the guide rim. The former upper envelope relief
cut is omitted; optional buckle windows still remove their central access area.
Closed ends use four modeling features; access-cutout magazines use five.
With cutouts off, rim height must not exceed cartridge nominal height minus
17 mm, clearing the lowest pull-tab tip for the supported 4 mm maximum grip.
The catalog rejects incompatible short-cartridge/tall-rim combinations and asks
for cutouts or a lower rim. Nine native cases passed including actual cartridge
interference checks in both orientations and on/off cutout configurations.


Standard-bin sliding dovetail lid (2026-10-04)
---------------------------------------------
Select Standard bin > Sliding dovetail lid. The existing rim checkbox becomes
Stacking lip above dovetail lid. Generates two named bodies in the same native
command transaction: bin and removable lid. Standard feet and all magnet options,
including 6.08 mm press fit, remain available. Open, divided and channel interiors
work from 1x1 through 6x6. Original unlidded recipes remain unchanged.

The lid plate is fixed at 3 mm, with no thickness input or named thickness control.
A 2 mm, 45-degree dovetail and 0.3 mm neck lie below the plate. The female rails
have 0.30 mm horizontal clearance per side (about 0.212 mm normal to each slope),
0.30 mm clearance below the tongue and 0.30 mm above the rails. The rear stop
contacts the tongue with the lid flush to the nominal footprint. Slide out toward
-Y/front; there is no detent latch. Rails retain upward movement.

The plate underside is nominal bin height + 2.6 mm. Overall closed height is
nominal + 5.6 mm, or nominal + 9.4 mm with the standard 3.8 mm stacking lip. The
lip is on the lid, preserving the continuous standard stacking profile. Lid and
rails follow the existing named bin-height parameter. Footprint and interior are
chosen at creation. The drawer envelope fit test includes the new closed height.

Print the plain lid flat with its top face on the bed. With the stacking lip,
print dovetail-side down and support the plate overhangs; review the support
interface around the sliding faces. Printed fit, warping and load stiffness still
need validation, especially for large lids. The plate stays 3 mm for all sizes.

verify-dovetail-generation.py checks six isolated designs: both lip options,
1x1/1x6/6x1/2x2/6x6 sizes, open/divided/three channel shapes, min/max heights,
full sliding travel, upward retention, rear stop, actual fixed plate thickness,
standard-foot stacking clearance, native height edits and preservation of an
existing intersecting solid. All passed. About 0.7-1 seconds for small examples,
2.7 seconds for the tested 6x6 divided example. Results: dovetail/verified-generation.json.


Model-derived category art and scoop graphics demo (2026-10-04)
- catalog-art/*.png: six 720 x 560 orthographic visible-edge captures of native BRep models. The old SVG illustrations are no longer used by the catalog.
- Regenerate through Fusion MCP with prepare-model-illustrations.py after opening the catalog. It uses disposable source documents and preserves existing documents.
- Standard-bin category includes a demo-only 25 mm quarter-circle scoop. The production scoop/label generator remains disabled.
- Historical fixed scoop demo remains available through the Python helper; the main catalog now uses the inline preview below.
- scoop_preview.py loads the 1,080-triangle cached mesh once; it never runs CAD generation. Switching styles replaces its graphics group, preserving the camera. Closing the demo document removes the preview.
- scoop-preview-verification.json records the graphics update checks: zero BRep bodies, mesh bodies, sketches, or timeline features before and after. Timings include API update/refresh, not input-to-photon latency.

Category color treatment (v19): run build-styled-catalog-art.py after regenerating native PNG captures. The catalog loads *-styled.svg wrappers: blue/teal ink, subtle family color washes, stronger selected-card state. Embedded source PNG geometry remains unchanged. No live parameter-update implementation was added in this styling pass.

Three.js live study (2026-10-04)
- Historical standalone prototype; the catalog now embeds the shared renderer below.
- Three.js 0.180.0 is bundled in vendor/ with its MIT license; no CDN access at runtime.
- 1..6 cells each way, 2..20U height, optional scoop and simplified rim. Scoop radius is limited by height/depth.
- Meshes are calculated on input, updates coalesce through requestAnimationFrame, old geometries are disposed, and orbit/zoom render on demand.
- This is an approximate shape study: standard feet, stacking interfaces and corners are simplified. No CAD manufacturing logic or export is invoked.
- Run node experiments/fusion-ui/test-three-demo.js for real Three.js geometry checks with a stub renderer. This does not validate WebGL support; that must be checked in Fusion.


Inline Three.js previews (v21)
- Default in the bin catalog and baseplate palette. Existing settings update procedural meshes locally; no Fusion model preparation, cached combination library, or CAD generation.
- Drag to orbit, scroll to zoom, Fit view to reset. Switch to 2D layout for dimensions and spacing. Show lid and Parts expose separate lids.
- Covers all six families, open/solid/divided/channel interiors, scoop and label studies, magazine seat layout/cutouts, test envelopes, and assembled/split baseplates with padding.
- Preview geometry is approximate. Feet, rims, dovetails, closure hardware and socket slopes are simplified; manufacturing remains governed by the existing generators. Scoop/label generation remains disabled.
- Local licensed Three.js runtime; no runtime network dependency. Replaced meshes are disposed and updates coalesce per animation frame.
- Run node experiments/fusion-ui/test-workshop-three.js: real mesh bounds/normals, all families, 1..6 cell cases, invalid capacities and open-cavity ray check. GPU validation is performed separately through the native Fusion palette.
