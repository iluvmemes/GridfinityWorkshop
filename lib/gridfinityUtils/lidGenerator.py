import adsk.core, adsk.fusion, traceback

from . import const, combineUtils, commonUtils, extrudeUtils, shapeUtils, baseGenerator
from .baseGeneratorInput import BaseGeneratorInput
from .lidGeneratorInput import LidGeneratorInput

app = adsk.core.Application.get()
ui = app.userInterface


def createLidBody(
    input: LidGeneratorInput,
    targetComponent: adsk.fusion.Component,
) -> adsk.fusion.BRepBody:
    lidWidth = input.baseWidth * input.basesX - input.xyClearance * 2.0
    lidLength = input.baseLength * input.basesY - input.xyClearance * 2.0

    # The lid is a solid bin without the walls: a gridfinity base interface that
    # indexes into the bin lip exactly like a stacked bin's base, plus a flat
    # plate on top.
    baseInput = BaseGeneratorInput()
    baseInput.originPoint = adsk.core.Point3D.create(-input.xyClearance, -input.xyClearance, 0)
    baseInput.baseWidth = input.baseWidth
    baseInput.baseLength = input.baseLength
    baseInput.xyClearance = input.xyClearance
    baseInput.hasScrewHoles = False
    baseInput.hasMagnetCutouts = False
    baseInput.hasBottomChamfer = True
    baseBodies = baseGenerator.createBaseBodyPattern(
        baseInput,
        input.basesX,
        input.basesY,
        targetComponent,
    )

    # flat plate on top of the base interface
    plateThickness = max(input.lidThickness - const.BIN_BASE_HEIGHT, const.BIN_COMPARTMENT_BOTTOM_THICKNESS)
    plateExtrude = extrudeUtils.createBox(
        lidWidth,
        lidLength,
        plateThickness,
        targetComponent,
        targetComponent.xYConstructionPlane,
    )
    lidBody = plateExtrude.bodies.item(0)
    lidBody.name = 'Lid body'

    # trims the perimeter to the bin footprint and rounds the plate corners
    baseGenerator.cutBaseClearance(baseInput, input.basesX, input.basesY, targetComponent)

    combineUtils.joinBodies(lidBody, commonUtils.objectCollectionFromList(baseBodies), targetComponent)

    # magnet pockets on the underside, 4 outer corners only — same XY as the
    # base magnet cutouts, so they line up with the bin's lid magnet bosses
    magnetOffset = const.DIMENSION_SCREW_HOLES_OFFSET - input.xyClearance
    magnetCorners = [
        adsk.core.Point3D.create(magnetOffset,              magnetOffset,              0),
        adsk.core.Point3D.create(lidWidth - magnetOffset,   magnetOffset,              0),
        adsk.core.Point3D.create(lidWidth - magnetOffset,   lidLength - magnetOffset,  0),
        adsk.core.Point3D.create(magnetOffset,              lidLength - magnetOffset,  0),
    ]
    magnetCutBodies = adsk.core.ObjectCollection.create()
    for cornerPoint in magnetCorners:
        magnetBody = shapeUtils.simpleCylinder(
            targetComponent.xYConstructionPlane,
            -const.BIN_BASE_HEIGHT,
            input.magnetDepth,
            input.magnetDiameter / 2,
            cornerPoint,
            targetComponent,
        )
        magnetCutBodies.add(magnetBody)
    combineUtils.cutBody(lidBody, magnetCutBodies, targetComponent)

    return lidBody
