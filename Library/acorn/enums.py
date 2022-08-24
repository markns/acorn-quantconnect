from System import Enum


class CapitalCorrection(Enum):
    FIXED = 0
    FULL_COMPOUNDING = 1
    # TODO implement half compounding
    HALF_COMPOUNDING = 2
