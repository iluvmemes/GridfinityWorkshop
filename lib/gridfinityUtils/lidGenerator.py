import adsk.core, adsk.fusion, traceback
import math

from . import const, combineUtils, commonUtils, extrudeUtils, filletUtils, shapeUtils, baseGenerator
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

    # The lid is a solid bin without the walls: a gridfinity base profile plus a
    # flat plate on top. The bin lip only engages the outer perimeter, so instead
    # of a per-cell base pattern the profile is generated as one monolithic
    # "base" stretched over the whole footprint — a single solid piece with no
    # cell subdivisions on the underside.
    baseInput = BaseGeneratorInput()
    baseInput.originPoint = adsk.core.Point3D.create(-input.xyClearance, -input.xyClearance, 0)
    baseInput.baseWidth = input.baseWidth * input.basesX
    baseInput.baseLength = input.baseLength * input.basesY
    baseInput.xyClearance = input.xyClearance
    baseInput.hasScrewHoles = False
    baseInput.hasMagnetCutouts = False
    baseInput.hasBottomChamfer = True
    baseBodies = [baseGenerator.createSingleGridfinityBaseBody(baseInput, targetComponent)]

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
    baseGenerator.cutBaseClearance(baseInput, 1, 1, targetComponent)

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

    if input.hasHandle:
        createLidHandle(input, lidBody, lidWidth, lidLength, plateThickness, targetComponent)

    return lidBody


def createLidHandle(
    input: LidGeneratorInput,
    lidBody: adsk.fusion.BRepBody,
    lidWidth: float,
    lidLength: float,
    plateThickness: float,
    targetComponent: adsk.fusion.Component,
):
    # lift handle: raised bar spanning the lid edge to edge, centered on the
    # other axis, doubling as the label platform. The flat top is the label
    # recess plus an equidistant labelMargin border; from the border the ends
    # ramp straight down to the lid edges (run derived, no separate input).
    handleTopZ = plateThickness + input.handleHeight
    recessLength = input.labelLength + const.LID_LABEL_RECESS_CLEARANCE
    recessWidth = input.labelWidth + const.LID_LABEL_RECESS_CLEARANCE
    # user editable blend radii, safety-clamped against the handle height so
    # the features can always compute (the dialog enforces the same bounds)
    sideFilletRadius = max(0.0, min(input.handleSideFilletRadius, input.handleHeight - 0.05))
    # the visible flat border around the recess is labelMargin on all four
    # sides measured to where curvature starts — the handle is widened to
    # reserve room for the side fillet on top of the border
    handleWidth = recessWidth + (input.labelMargin + sideFilletRadius) * 2.0
    spanLength = lidLength if input.handleAlongY else lidWidth
    # the bar stops handleEdgeGap short of the lid edges, leaving a flat
    # reveal of lid surface around the handle ends
    handleSpanLength = spanLength - input.handleEdgeGap * 2.0
    if input.handleAlongY:
        handleOrigin = adsk.core.Point3D.create((lidWidth - handleWidth) / 2.0, input.handleEdgeGap, plateThickness)
        handleBoxWidth, handleBoxLength = handleWidth, handleSpanLength
        transitionPlane = targetComponent.yZConstructionPlane
    else:
        handleOrigin = adsk.core.Point3D.create(input.handleEdgeGap, (lidLength - handleWidth) / 2.0, plateThickness)
        handleBoxWidth, handleBoxLength = handleSpanLength, handleWidth
        transitionPlane = targetComponent.xZConstructionPlane
    handleExtrude = extrudeUtils.createBoxAtPoint(
        handleBoxWidth,
        handleBoxLength,
        input.handleHeight,
        targetComponent,
        handleOrigin,
    )
    handleExtrude.name = 'Lid handle extrude'
    handleBody = handleExtrude.bodies.item(0)

    # end ramps: the flat top ends one labelMargin past the recess, then a
    # straight ramp drops to zero height at the bar end (handleEdgeGap short
    # of the lid edge), with a tangent blend at the top corner drawn directly
    # in the profile sketch. The blend's tangent point lands exactly at the
    # end of the border, so the corner is pulled back by the blend setback
    # (solved iteratively — the setback depends on the ramp angle which
    # depends on the corner position).
    tangentTopOffset = (spanLength - recessLength) / 2.0 - input.labelMargin - input.handleEdgeGap
    cornerFilletRadius = max(0.0, min(input.handleCornerFilletRadius, input.handleHeight, tangentTopOffset - 0.1))
    rampRun = tangentTopOffset
    cornerSetback = 0.0
    for _ in range(3):
        rampAngle = math.atan2(input.handleHeight, rampRun)
        cornerSetback = cornerFilletRadius * math.tan(rampAngle / 2.0)
        rampRun = tangentTopOffset - cornerSetback
    transitionSketch: adsk.fusion.Sketch = targetComponent.sketches.add(transitionPlane)
    transitionSketch.name = 'Lid handle transition sketch'
    sketchLines = transitionSketch.sketchCurves.sketchLines
    sketchArcs = transitionSketch.sketchCurves.sketchArcs

    def toSketch(spanPosition: float, z: float) -> adsk.core.Point3D:
        if input.handleAlongY:
            modelPoint = adsk.core.Point3D.create(0, spanPosition, z)
        else:
            modelPoint = adsk.core.Point3D.create(spanPosition, 0, z)
        point = transitionSketch.modelToSketchSpace(modelPoint)
        point.z = 0
        return point

    for (edgePosition, direction) in [(input.handleEdgeGap, 1), (spanLength - input.handleEdgeGap, -1)]:
        cornerPosition = edgePosition + direction * rampRun
        if cornerFilletRadius > 0.01:
            # blend arc tangent to the flat top and the ramp
            tangentTopPoint = toSketch(cornerPosition + direction * cornerSetback, handleTopZ)
            arcMidPoint = toSketch(
                cornerPosition + direction * (cornerSetback - cornerFilletRadius * math.sin(rampAngle / 2.0)),
                handleTopZ - cornerFilletRadius + cornerFilletRadius * math.cos(rampAngle / 2.0),
            )
            tangentRampPoint = toSketch(
                cornerPosition - direction * cornerSetback * math.cos(rampAngle),
                handleTopZ - cornerSetback * math.sin(rampAngle),
            )
            sketchLines.addByTwoPoints(toSketch(edgePosition, handleTopZ), tangentTopPoint)
            sketchArcs.addByThreePoints(tangentTopPoint, arcMidPoint, tangentRampPoint)
            sketchLines.addByTwoPoints(tangentRampPoint, toSketch(edgePosition, plateThickness))
        else:
            # zero radius: sharp crease where the flat top breaks into the ramp
            sketchLines.addByTwoPoints(toSketch(edgePosition, handleTopZ), toSketch(cornerPosition, handleTopZ))
            sketchLines.addByTwoPoints(toSketch(cornerPosition, handleTopZ), toSketch(edgePosition, plateThickness))
        sketchLines.addByTwoPoints(toSketch(edgePosition, plateThickness), toSketch(edgePosition, handleTopZ))

    transitionCutProfiles = commonUtils.objectCollectionFromList(list(transitionSketch.profiles))
    transitionCutInput = targetComponent.features.extrudeFeatures.createInput(
        transitionCutProfiles,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )
    transitionCutInput.setTwoSidesExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(100)),
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(100)),
    )
    transitionCutInput.participantBodies = [handleBody]
    transitionCut = targetComponent.features.extrudeFeatures.add(transitionCutInput)
    transitionCut.name = 'Lid handle transition cut'

    # fillet along the plateau side edges; the tangent chain carries it over
    # the corner blends and down the ramps for a uniform soft outline. The
    # handle width reserves room for it, so the fillet never reaches the
    # recess border.
    acrossMin = handleOrigin.x if input.handleAlongY else handleOrigin.y
    sideTopEdges = []
    for edge in handleBody.edges:
        startPoint = edge.startVertex.geometry
        endPoint = edge.endVertex.geometry
        if abs(startPoint.z - handleTopZ) > const.DEFAULT_FILTER_TOLERANCE or abs(endPoint.z - handleTopZ) > const.DEFAULT_FILTER_TOLERANCE:
            continue
        startAcross = startPoint.x if input.handleAlongY else startPoint.y
        endAcross = endPoint.x if input.handleAlongY else endPoint.y
        if abs(startAcross - endAcross) > const.DEFAULT_FILTER_TOLERANCE:
            continue
        if min(abs(startAcross - acrossMin), abs(startAcross - (acrossMin + handleWidth))) < const.DEFAULT_FILTER_TOLERANCE:
            sideTopEdges.append(edge)
    if len(sideTopEdges) > 0 and sideFilletRadius > 0.01:
        filletFeatures: adsk.fusion.FilletFeatures = targetComponent.features.filletFeatures
        sideFilletInput = filletFeatures.createInput()
        sideFilletInput.isRollingBallCorner = True
        sideFilletInput.edgeSetInputs.addConstantRadiusEdgeSet(
            commonUtils.objectCollectionFromList(sideTopEdges),
            adsk.core.ValueInput.createByReal(sideFilletRadius),
            True,
        )
        filletFeatures.add(sideFilletInput).name = 'Lid handle side fillet'

    # label recess in the center of the handle top, slightly oversized so the
    # label drops in; long side runs along the handle span
    if input.handleAlongY:
        recessBoxWidth, recessBoxLength = recessWidth, recessLength
    else:
        recessBoxWidth, recessBoxLength = recessLength, recessWidth
    recessExtrude = extrudeUtils.createBoxAtPoint(
        recessBoxWidth,
        recessBoxLength,
        const.LID_LABEL_RECESS_DEPTH,
        targetComponent,
        adsk.core.Point3D.create(
            (lidWidth - recessBoxWidth) / 2.0,
            (lidLength - recessBoxLength) / 2.0,
            handleTopZ - const.LID_LABEL_RECESS_DEPTH,
        ),
    )
    recessExtrude.name = 'Lid label recess extrude'
    # rounded recess corners to match die-cut label corners; clamped so the
    # radius can never degenerate the pocket outline
    labelCornerFilletRadius = max(0.0, min(
        input.labelCornerFilletRadius,
        min(recessBoxWidth, recessBoxLength) / 2.0 - 0.05,
    ))
    if labelCornerFilletRadius > 0.01:
        filletUtils.filletEdgesByLength(
            recessExtrude.faces,
            labelCornerFilletRadius,
            const.LID_LABEL_RECESS_DEPTH,
            targetComponent,
        ).name = 'Lid label recess corner fillet'
    combineUtils.cutBody(handleBody, commonUtils.objectCollectionFromList(recessExtrude.bodies), targetComponent)

    combineUtils.joinBodies(lidBody, commonUtils.objectCollectionFromList([handleBody]), targetComponent)
