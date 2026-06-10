# Lid Magnet Pockets — Design (as built)

## Repo
`D:\Code Projects\FusionGridfinityGenerator`

## Status
**Implemented.** This document describes the design as built, for reference and follow-up work.

---

## The design

A lid for a gridfinity bin, held on by magnets, indexing into the standard stacking lip.

### Bin side (`lib/gridfinityUtils/binBodyGenerator.py`, `if input.hasLidMagnets:` block)

A hollow bin has ~1.2mm walls — there is **no material** at the magnet position
(8mm in from the wall), so material is added first:

1. **Corner bosses** — at each of the 4 top corners, a box of size
   `magnetOffset + pocketRadius + BIN_WALL_THICKNESS` is created with its top at
   `binBodyTotalHeight` (top of the bin walls = base of the lip) and height
   `lidMagnetDepth + BIN_COMPARTMENT_BOTTOM_THICKNESS` (pocket depth + 1mm floor).
   - The boss's outer vertical edge is filleted with `input.binCornerFilletRadius`
     so it stays flush with the bin's rounded corner.
   - The inner (diagonal) vertical edge gets the same fillet to blend into the
     compartment.
   - Bosses are joined to the bin body after the compartment cutouts, so they
     survive in hollow bins and merge harmlessly into solid ones.
2. **Pockets** — cut downward (`-lidMagnetDepth`) from a construction plane at
   `binBodyTotalHeight`, i.e. the pocket opening is right where the lip begins.

**XY positions:** `DIMENSION_SCREW_HOLES_OFFSET - xyClearance` from the bin body
origin (and mirrored: `totalWidth/Length - that` on the far sides).

> ⚠️ This is the exact component-space position of the **base** magnet cutouts:
> `baseGenerator.py` places the hole center at absolute
> `DIMENSION_SCREW_HOLES_OFFSET - xyClearance` (the base's `-xyClearance` origin
> offset only shifts the base *rectangle*, not the hole). Do **not** "correct"
> this to `- 2 * xyClearance` — that was a previous wrong turn and misaligns
> everything by 0.25mm.

**Shelled bins:** lid magnets are disabled (`and not isShelled` in
`commands/commandCreateBin/entry.py`), because the shell operation would gut the
bosses. Same pattern as screw holes / base magnet cutouts.

### Lid side (`lib/gridfinityUtils/lidGenerator.py`)

The lid is **a solid bin without the walls**:

1. **Base interface** — a standard gridfinity base pattern
   (`baseGenerator.createBaseBodyPattern`, no screw holes, no per-cell magnet
   cutouts), origin at `(-xyClearance, -xyClearance)`, exactly like the bin
   command does. This indexes into the bin's stacking lip natively — that is
   what the lip exists for.
2. **Flat plate** — a box of `lidThickness - BIN_BASE_HEIGHT` (clamped to ≥ 1mm)
   on top of the base interface (z 0 upward), spanning the bin footprint.
3. **Perimeter trim** — `baseGenerator.cutBaseClearance` trims everything to the
   bin footprint and rounds the plate corners with the standard profile.
4. **Magnet pockets** — 4 pockets cut **upward into the base underside**
   (`z = -BIN_BASE_HEIGHT`, depth `magnetDepth`), at the 4 outer corners only,
   XY = `DIMENSION_SCREW_HOLES_OFFSET - xyClearance` — the standard base magnet
   position, which is also where the bin's bosses are. Alignment is by
   construction.

Model orientation: base profile points down (z < 0), plate up — flip 180° to print.

---

## Verification (after stop/start of the add-in in Fusion)

1. Generate a **hollow** bin with "Add lid magnet pockets" checked → 4 corner
   bosses at the top of the walls, just below the lip, each with a pocket
   opening at the wall top. No errors (this used to fail: the old code cut into
   air and the combine-cut threw).
2. Generate a **solid** bin with the option → pockets at the same positions, no
   visible bosses (merged into the solid).
3. Generate a lid with the same grid dimensions → base profile + plate; the 4
   underside pockets line up with the bin pockets when the lid is dropped into
   the lip.
4. Magnet fit: 6.5mm pocket diameter for 6mm magnets (press fit), 2.4mm depth
   for 2mm magnets with glue clearance (these are the defaults).

## Known limitations / follow-ups

- Boss undersides are flat (a ~12mm bridge over the compartment when printing
  upright). Printable, but a 45° chamfer or cove under the boss (like the
  reference model) would be nicer — follow-up.
- If a label tab is placed at a magnet corner, the pocket cuts into the tab top.
  Functional, cosmetically debatable.
- Lid magnets are 4 corners only; long bins (e.g. 1×4) get no mid-span magnets
  because the bin has no mid-wall bosses. Add paired mid-wall bosses + lid
  pockets if hold strength is insufficient.

## Constants reference (cm, Fusion API units)

```
DIMENSION_SCREW_HOLES_OFFSET = 0.8       # 8mm from nominal cell edge
DIMENSION_MAGNET_CUTOUT_DIAMETER = 0.65  # 6.5mm
DIMENSION_MAGNET_CUTOUT_DEPTH = 0.24     # 2.4mm
BIN_BASE_HEIGHT = 0.5                    # base interface height (0.24+0.18+0.08)
BIN_LIP_EXTRA_HEIGHT = 0.44              # lip is 4.4mm tall above bin body
BIN_WALL_THICKNESS = 0.12                # default wall — why bosses are needed
BIN_XY_CLEARANCE = 0.025                 # 0.25mm default
```
