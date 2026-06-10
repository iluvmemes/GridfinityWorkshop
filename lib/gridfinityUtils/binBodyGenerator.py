import adsk.core, adsk.fusion, traceback
import os
import math
import copy

from ...lib import fusion360utils as futil
from . import const, combineUtils, faceUtils, commonUtils, sketchUtils, extrudeUtils, baseGenerator, edgeUtils, filletUtils, geometryUtils, shapeUtils
from .binBodyCutoutGenerator import createGridfinityBinBodyCutout
from .binBodyCutoutGeneratorInput import BinBodyCutoutGeneratorInput
from .baseGeneratorInput import BaseGeneratorInput
from .binBodyGeneratorInput import BinBodyGeneratorInput, BinBodyCompartmentDefinition
from .binBodyTabGeneratorInput import BinBodyTabGeneratorInput
from .binBodyTabGenerator import createGridfinityBinBodyTab
from .binBodyLipGeneratorInput import BinBodyLipGeneratorInput
from .binBodyLipGenerator import createGridfinityBinBodyLip
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

def uniformCompartments(countX, countY):
    compartments: list[BinBodyCompartmentDefinition] = []
    for i in range(countX):
        for j in range(countY):
            compartments.append(BinBodyCompartmentDefinition(i, j, 1, 1))
    return compartments

def createGridfinityBinBody(
    input: BinBodyGeneratorInput,
    targetComponent: adsk.fusion.Component,
) -> tuple[adsk.fusion.BRepBody, adsk.fusion.BRepBody]:

    actualBodyWidth = (input.baseWidth * input.binWidth) - input.xyClearance * 2.0
    actualBodyLength = (input.baseLength * input.binLength) - input.xyClearance * 2.0
    binHeightWithoutBase = input.binHeight - 1
    binBodyTotalHeight = binHeightWithoutBase * input.heightUnit + max(0, input.heightUnit - const.BIN_BASE_HEIGHT)
    features: adsk.fusion.Features = targetComponent.features
    binBodyExtrude = extrudeUtils.createBox(
        actualBodyWidth,
        actualBodyLength,
        binBodyTotalHeight,
        targetComponent,
        targetComponent.xYConstructionPlane
    )
    binBody = binBodyExtrude.bodies.item(0)
    binBody.name = 'Bin body'

    bodiesToMerge: list[adsk.fusion.BRepBody] = []
    bodiesToSubtract: list[adsk.fusion.BRepBody] = []

    # round corners
    filletUtils.filletEdgesByLength(
        binBodyExtrude.faces,
        input.binCornerFilletRadius,
        binBodyTotalHeight,
        targetComponent,
    ).name = 'Bin body corner fillets'

    if input.hasLip:
        lipOriginPoint = adsk.core.Point3D.create(
            0,
            0,
            binHeightWithoutBase * input.heightUnit + max(0, input.heightUnit - const.BIN_BASE_HEIGHT)
        )
        lipInput = BinBodyLipGeneratorInput()
        lipInput.baseLength = input.baseLength
        lipInput.baseWidth = input.baseWidth
        lipInput.binLength = input.binLength
        lipInput.binWidth = input.binWidth
        lipInput.hasLipNotches = input.hasLipNotches
        lipInput.xyClearance = input.xyClearance
        lipInput.binCornerFilletRadius = input.binCornerFilletRadius
        lipInput.origin = lipOriginPoint
        lipBody = createGridfinityBinBodyLip(lipInput, targetComponent)

        if input.wallThickness < const.BIN_LIP_WALL_THICKNESS:
            lipBottomChamferSize = max(const.BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS, input.binCornerFilletRadius - input.wallThickness)
            lipBottomChamferExtrude = extrudeUtils.createBoxAtPoint(
                actualBodyWidth - input.wallThickness * 2,
                (actualBodyLength - input.wallThickness - const.BIN_LIP_WALL_THICKNESS + input.xyClearance) if input.hasScoop else (actualBodyLength - input.wallThickness * 2),
                lipBottomChamferSize,
                targetComponent,
                adsk.core.Point3D.create(
                    input.wallThickness,
                    (const.BIN_LIP_WALL_THICKNESS - input.xyClearance) if input.hasScoop else input.wallThickness,
                    lipOriginPoint.z,
                )
            )
            lipBottomChamferExtrude.name = 'Lip bottom chamfer extrude'
            filletUtils.filletEdgesByLength(
                lipBottomChamferExtrude.faces,
                lipBottomChamferSize,
                lipBottomChamferSize,
                targetComponent,
            )
            lipBottomChamferExtrudeTopFace = faceUtils.getTopFace(lipBottomChamferExtrude.bodies.item(0))
            scoopSideEdge = min([edge for edge in lipBottomChamferExtrudeTopFace.edges if geometryUtils.isCollinearToX(edge)], key=lambda x: x.boundingBox.minPoint.y)

            edgesToChamfer = list(scoopSideEdge.tangentiallyConnectedEdges)[3:] if input.hasScoop else scoopSideEdge.tangentiallyConnectedEdges
            chamferFeatures: adsk.fusion.ChamferFeatures = features.chamferFeatures
            bottomLipChamferInput = chamferFeatures.createInput2()
            bottomLipChamferEdges = commonUtils.objectCollectionFromList(edgesToChamfer)
            bottomLipChamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                bottomLipChamferEdges,
                adsk.core.ValueInput.createByReal(lipBottomChamferSize),
                False)
            chamferFeatures.add(bottomLipChamferInput)
            combineUtils.cutBody(lipBody, commonUtils.objectCollectionFromList(lipBottomChamferExtrude.bodies), targetComponent)

        bodiesToMerge.append(lipBody)

    if not input.isSolid:
        compartmentsMinX = input.wallThickness
        compartmentsMaxX = actualBodyWidth - input.wallThickness
        compartmentsMinY = (const.BIN_LIP_WALL_THICKNESS - input.xyClearance) if input.hasLip and input.hasScoop else input.wallThickness
        compartmentsMaxY = actualBodyLength - input.wallThickness

        totalCompartmentsWidth = compartmentsMaxX - compartmentsMinX
        totalCompartmentsLength = compartmentsMaxY - compartmentsMinY
        
        compartmentWidthUnit = (totalCompartmentsWidth - (input.compartmentsByX - 1) * input.wallThickness) / input.compartmentsByX
        compartmentLengthUnit = (totalCompartmentsLength - (input.compartmentsByY - 1) * input.wallThickness) / input.compartmentsByY

        for compartment in input.compartments:
            compartmentX = compartmentsMinX + compartment.positionX * (compartmentWidthUnit + input.wallThickness)
            compartmentY = compartmentsMinY + compartment.positionY * (compartmentLengthUnit + input.wallThickness)
            compartmentOriginPoint = adsk.core.Point3D.create(
                compartmentX,
                compartmentY,
                binBodyTotalHeight
            )
            compartmentWidth = compartmentWidthUnit * compartment.width + (compartment.width - 1) * input.wallThickness
            compartmentLength = compartmentLengthUnit * compartment.length + (compartment.length - 1) * input.wallThickness
            compartmentDepth = min(binBodyTotalHeight - const.BIN_COMPARTMENT_BOTTOM_THICKNESS, compartment.depth)

            compartmentTabInput = BinBodyTabGeneratorInput()
            tabOriginPoint = adsk.core.Point3D.create(
                compartmentOriginPoint.x + max(0, min(input.tabPosition, input.binWidth - input.tabLength)) * input.baseWidth,
                compartmentOriginPoint.y + compartmentLength,
                compartmentOriginPoint.z,
            )
            compartmentTabInput.origin = tabOriginPoint
            compartmentTabInput.length = max(0, min(input.tabLength, input.binWidth)) * input.baseWidth
            compartmentTabInput.width = input.tabWidth
            compartmentTabInput.overhangAngle = input.tabOverhangAngle
            compartmentTabInput.topClearance = const.BIN_TAB_TOP_CLEARANCE

            [compartmentMerges, compartmentCuts] = createCompartment(
                input.wallThickness,
                compartmentOriginPoint,
                compartmentWidth,
                compartmentLength,
                compartmentDepth,
                input.binCornerFilletRadius - input.wallThickness,
                input.hasScoop,
                input.scoopMaxRadius,
                input.hasTab,
                compartmentTabInput,
                targetComponent,
            )
            bodiesToSubtract = bodiesToSubtract + compartmentCuts
            bodiesToMerge = bodiesToMerge + compartmentMerges

        if len(input.compartments) > 1:
            compartmentsTopClearance = createCompartmentCutout(
                input.wallThickness,
                adsk.core.Point3D.create(
                    compartmentsMinX,
                    compartmentsMinY,
                    binBodyTotalHeight
                ),
                actualBodyWidth - input.wallThickness * 2,
                actualBodyLength - input.wallThickness - compartmentsMinY,
                const.BIN_TAB_TOP_CLEARANCE,
                input.binCornerFilletRadius - input.wallThickness,
                False,
                0,
                False,
                targetComponent,
            )
            bodiesToSubtract.append(compartmentsTopClearance)

    if len(bodiesToSubtract) > 0:
        combineUtils.cutBody(
            binBody,
            commonUtils.objectCollectionFromList(bodiesToSubtract),
            targetComponent
        )
    if len(bodiesToMerge) > 0:
        combineUtils.joinBodies(
            binBody,
            commonUtils.objectCollectionFromList(bodiesToMerge),
            targetComponent
        )

    if input.hasLidMagnets:
        # Pockets sit at the same XY as the base magnet cutouts so the lid (a base
        # profile) aligns. Hollow bin walls are too thin to hold a magnet, so each
        # corner gets a boss joined to the walls right below the lip, and the pocket
        # is cut down into it from the top of the bin walls.
        magnetOffset = const.DIMENSION_SCREW_HOLES_OFFSET - input.xyClearance
        pocketRadius = input.lidMagnetDiameter / 2
        bossSize = magnetOffset + pocketRadius + const.BIN_WALL_THICKNESS
        bossHeight = input.lidMagnetDepth + const.BIN_COMPARTMENT_BOTTOM_THICKNESS
        # 45 degree tapered reinforcement below the ledge transfers press fit
        # loads into the walls. The taper runs all the way down to the wall
        # faces so the boss prints without supports; the dialog validation
        # enforces a bin tall enough to fit ledge + taper.
        bossTaperHeight = max(0, min(
            bossSize - input.wallThickness,
            binBodyTotalHeight - bossHeight,
        ))
        bossBottomZ = binBodyTotalHeight - bossHeight - bossTaperHeight
        filletFeatures: adsk.fusion.FilletFeatures = features.filletFeatures
        chamferFeatures: adsk.fusion.ChamferFeatures = features.chamferFeatures

        binCorners = [
            (0, 0),
            (actualBodyWidth, 0),
            (actualBodyWidth, actualBodyLength),
            (0, actualBodyLength),
        ]
        bossBodies: list[adsk.fusion.BRepBody] = []
        pocketCenters: list[adsk.core.Point3D] = []
        for (cornerX, cornerY) in binCorners:
            bossOriginX = cornerX if cornerX == 0 else cornerX - bossSize
            bossOriginY = cornerY if cornerY == 0 else cornerY - bossSize
            bossExtrude = extrudeUtils.createBoxAtPoint(
                bossSize,
                bossSize,
                bossHeight + bossTaperHeight,
                targetComponent,
                adsk.core.Point3D.create(bossOriginX, bossOriginY, bossBottomZ),
            )
            bossExtrude.name = 'Lid magnet boss extrude'
            bossBody = bossExtrude.bodies.item(0)
            # taper chamfer goes first, on the plain box: two planar chamfers
            # on the straight interior bottom edges, mitering at the sharp
            # inner corner. Chamfering before the corner fillet exists is what
            # lets the taper run the full distance to the wall faces — done
            # after, the chamfer surface would intersect the fillet face and
            # compute would fail.
            if bossTaperHeight > 0.05:
                bossBottomFace = faceUtils.getBottomFace(bossBody)
                bottomEdgesByCornerDistance = sorted(
                    bossBottomFace.edges,
                    key=lambda edge: min(
                        (edge.startVertex.geometry.x - cornerX) ** 2 + (edge.startVertex.geometry.y - cornerY) ** 2,
                        (edge.endVertex.geometry.x - cornerX) ** 2 + (edge.endVertex.geometry.y - cornerY) ** 2,
                    ),
                )
                bossChamferInput = chamferFeatures.createInput2()
                bossChamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                    commonUtils.objectCollectionFromList(bottomEdgesByCornerDistance[-2:]),
                    adsk.core.ValueInput.createByReal(bossTaperHeight),
                    False,
                )
                chamferFeatures.add(bossChamferInput).name = 'Lid magnet boss taper'
            # outer vertical edge follows the bin corner fillet. Fillets must
            # come after the taper chamfer: chamfering through a filleted edge
            # degenerates (equal distance chamfers cannot offset a small
            # convex arc inward further than its radius)
            verticalEdges = [
                edge for edge in bossBody.edges
                if abs(edge.startVertex.geometry.x - edge.endVertex.geometry.x) < const.DEFAULT_FILTER_TOLERANCE
                and abs(edge.startVertex.geometry.y - edge.endVertex.geometry.y) < const.DEFAULT_FILTER_TOLERANCE
            ]
            outerEdge = min(verticalEdges, key=lambda edge: (edge.startVertex.geometry.x - cornerX) ** 2 + (edge.startVertex.geometry.y - cornerY) ** 2)
            bossFilletInput = filletFeatures.createInput()
            bossFilletInput.isRollingBallCorner = True
            bossFilletInput.edgeSetInputs.addConstantRadiusEdgeSet(
                commonUtils.objectCollectionFromList([outerEdge]),
                adsk.core.ValueInput.createByReal(input.binCornerFilletRadius),
                True,
            )
            filletFeatures.add(bossFilletInput).name = 'Lid magnet boss fillet'
            # small blend on the exposed inner corner of the ledge so it does
            # not scratch and matches the bin styling; re-query edges since the
            # outer fillet rebuilt the body
            ledgeVerticalEdges = [
                edge for edge in bossBody.edges
                if abs(edge.startVertex.geometry.x - edge.endVertex.geometry.x) < const.DEFAULT_FILTER_TOLERANCE
                and abs(edge.startVertex.geometry.y - edge.endVertex.geometry.y) < const.DEFAULT_FILTER_TOLERANCE
            ]
            innerEdge = max(ledgeVerticalEdges, key=lambda edge: (edge.startVertex.geometry.x - cornerX) ** 2 + (edge.startVertex.geometry.y - cornerY) ** 2)
            innerFilletInput = filletFeatures.createInput()
            innerFilletInput.isRollingBallCorner = True
            innerFilletInput.edgeSetInputs.addConstantRadiusEdgeSet(
                commonUtils.objectCollectionFromList([innerEdge]),
                adsk.core.ValueInput.createByReal(0.1),
                True,
            )
            filletFeatures.add(innerFilletInput).name = 'Lid magnet boss inner fillet'
            bossBodies.append(bossBody)
            pocketCenters.append(adsk.core.Point3D.create(
                magnetOffset if cornerX == 0 else cornerX - magnetOffset,
                magnetOffset if cornerY == 0 else cornerY - magnetOffset,
                0,
            ))
        combineUtils.joinBodies(binBody, commonUtils.objectCollectionFromList(bossBodies), targetComponent)

        # pockets open at the top of the bin walls (base of the lip), cut downward
        lidMagnetPlaneInput = targetComponent.constructionPlanes.createInput()
        lidMagnetPlaneInput.setByOffset(
            targetComponent.xYConstructionPlane,
            adsk.core.ValueInput.createByReal(binBodyTotalHeight),
        )
        lidMagnetPlane = targetComponent.constructionPlanes.add(lidMagnetPlaneInput)
        lidMagnetPlane.name = 'Lid magnet pocket plane'
        lidMagnetPlane.isLightBulbOn = False
        lidMagnetCutBodies = adsk.core.ObjectCollection.create()
        for pocketCenter in pocketCenters:
            magnetBody = shapeUtils.simpleCylinder(
                lidMagnetPlane,
                0,
                -input.lidMagnetDepth,
                pocketRadius,
                pocketCenter,
                targetComponent,
            )
            lidMagnetCutBodies.add(magnetBody)
        combineUtils.cutBody(binBody, lidMagnetCutBodies, targetComponent)

    return binBody


def createCompartmentCutout(
        wallThickness: float,
        originPoint: adsk.core.Point3D,
        width: float,
        length: float,
        depth: float,
        cornerFilletRadius: float,
        hasScoop: bool,
        scoopMaxRadius: float,
        hasBottomFillet: bool,
        targetComponent: adsk.fusion.Component,
    ) -> adsk.fusion.BRepBody:

    innerCutoutFilletRadius = max(const.BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS, cornerFilletRadius)
    innerCutoutInput = BinBodyCutoutGeneratorInput()
    innerCutoutInput.origin = originPoint
    innerCutoutInput.width = width
    innerCutoutInput.length = length
    innerCutoutInput.height = depth
    innerCutoutInput.hasScoop = hasScoop
    innerCutoutInput.scoopMaxRadius = scoopMaxRadius
    innerCutoutInput.filletRadius = innerCutoutFilletRadius
    innerCutoutInput.hasBottomFillet = hasBottomFillet

    return createGridfinityBinBodyCutout(innerCutoutInput, targetComponent)

def createCompartment(
        wallThickness: float,
        originPoint: adsk.core.Point3D,
        width: float,
        length: float,
        depth: float,
        cornerFilletRadius: float,
        hasScoop: bool,
        scoopMaxRadius: float,
        hasTab: bool,
        tabInput: BinBodyTabGeneratorInput,
        targetComponent: adsk.fusion.Component,
    ) -> tuple[list[adsk.fusion.BRepBody], list[adsk.fusion.BRepBody]]:

    bodiesToMerge: list[adsk.fusion.BRepBody] = []
    bodiesToSubtract: list[adsk.fusion.BRepBody] = []

    innerCutoutBody = createCompartmentCutout(
        wallThickness,
        originPoint,
        width,
        length,
        depth,
        cornerFilletRadius,
        hasScoop,
        scoopMaxRadius,
        True,
        targetComponent,
    )
    bodiesToSubtract.append(innerCutoutBody)

    # label tab
    if hasTab:
        tabBody = createGridfinityBinBodyTab(tabInput, targetComponent)

        intersectTabInput = targetComponent.features.combineFeatures.createInput(
            tabBody,
            commonUtils.objectCollectionFromList([innerCutoutBody]),
            )
        intersectTabInput.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        intersectTabInput.isKeepToolBodies = True
        intersectTabFeature = targetComponent.features.combineFeatures.add(intersectTabInput)
        bodiesToMerge = bodiesToMerge + [body for body in list(intersectTabFeature.bodies) if not body.revisionId == innerCutoutBody.revisionId]
    return (bodiesToMerge, bodiesToSubtract)