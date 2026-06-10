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
