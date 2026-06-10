import adsk.core, adsk.fusion, traceback

from . import const

class LidGeneratorInput():
    def __init__(self):
        self.basesX = 1
        self.basesY = 1
        self.baseWidth = const.DIMENSION_DEFAULT_WIDTH_UNIT
        self.baseLength = const.DIMENSION_DEFAULT_WIDTH_UNIT
        self.magnetDiameter = const.DIMENSION_MAGNET_CUTOUT_DIAMETER
        self.magnetDepth = const.DIMENSION_MAGNET_CUTOUT_DEPTH
        self.xyClearance = const.BIN_XY_CLEARANCE
        self.lidThickness = 0.6
        self.hasHandle = False
        self.handleAlongY = False
        self.handleHeight = 0.6
        self.handleEdgeGap = 0.3
        self.handleCornerFilletRadius = 0.2
        self.handleSideFilletRadius = 0.2
        self.labelWidth = 1.2
        self.labelLength = 4.0
        self.labelMargin = 0.3
        self.labelCornerFilletRadius = 0.15

    @property
    def basesX(self) -> int:
        return self._basesX

    @basesX.setter
    def basesX(self, value: int):
        self._basesX = value

    @property
    def basesY(self) -> int:
        return self._basesY

    @basesY.setter
    def basesY(self, value: int):
        self._basesY = value

    @property
    def baseWidth(self) -> float:
        return self._baseWidth

    @baseWidth.setter
    def baseWidth(self, value: float):
        self._baseWidth = value

    @property
    def baseLength(self) -> float:
        return self._baseLength

    @baseLength.setter
    def baseLength(self, value: float):
        self._baseLength = value

    @property
    def magnetDiameter(self) -> float:
        return self._magnetDiameter

    @magnetDiameter.setter
    def magnetDiameter(self, value: float):
        self._magnetDiameter = value

    @property
    def magnetDepth(self) -> float:
        return self._magnetDepth

    @magnetDepth.setter
    def magnetDepth(self, value: float):
        self._magnetDepth = value

    @property
    def xyClearance(self) -> float:
        return self._xyClearance

    @xyClearance.setter
    def xyClearance(self, value: float):
        self._xyClearance = value

    @property
    def lidThickness(self) -> float:
        return self._lidThickness

    @lidThickness.setter
    def lidThickness(self, value: float):
        self._lidThickness = value

    @property
    def hasHandle(self) -> bool:
        return self._hasHandle

    @hasHandle.setter
    def hasHandle(self, value: bool):
        self._hasHandle = value

    @property
    def handleAlongY(self) -> bool:
        return self._handleAlongY

    @handleAlongY.setter
    def handleAlongY(self, value: bool):
        self._handleAlongY = value

    @property
    def handleHeight(self) -> float:
        return self._handleHeight

    @handleHeight.setter
    def handleHeight(self, value: float):
        self._handleHeight = value

    @property
    def handleEdgeGap(self) -> float:
        return self._handleEdgeGap

    @handleEdgeGap.setter
    def handleEdgeGap(self, value: float):
        self._handleEdgeGap = value

    @property
    def handleCornerFilletRadius(self) -> float:
        return self._handleCornerFilletRadius

    @handleCornerFilletRadius.setter
    def handleCornerFilletRadius(self, value: float):
        self._handleCornerFilletRadius = value

    @property
    def handleSideFilletRadius(self) -> float:
        return self._handleSideFilletRadius

    @handleSideFilletRadius.setter
    def handleSideFilletRadius(self, value: float):
        self._handleSideFilletRadius = value

    @property
    def labelWidth(self) -> float:
        return self._labelWidth

    @labelWidth.setter
    def labelWidth(self, value: float):
        self._labelWidth = value

    @property
    def labelLength(self) -> float:
        return self._labelLength

    @labelLength.setter
    def labelLength(self, value: float):
        self._labelLength = value

    @property
    def labelMargin(self) -> float:
        return self._labelMargin

    @labelMargin.setter
    def labelMargin(self, value: float):
        self._labelMargin = value

    @property
    def labelCornerFilletRadius(self) -> float:
        return self._labelCornerFilletRadius

    @labelCornerFilletRadius.setter
    def labelCornerFilletRadius(self, value: float):
        self._labelCornerFilletRadius = value
