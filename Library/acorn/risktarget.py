from dataclasses import dataclass
from typing import Dict

from acorn.utils import setall


@dataclass
class IDMData:
    idm: float
    theoretical_sr: float
    theoretical_risk_target: float
    risk_target: float
    instrument_level_risk_target: float


RISK_TARGET: Dict[int, IDMData] = {}
IDM = {}
RDM = {}

# Table 44: Instrument diversification multiplier (IDM), theoretical Sharpe ratio (SR),
# theoretical and recommended account level risk targets for multiple asset classes
#
# Number of instruments
# IDM (A)
# Theoretical SR (B) SR = 0.24 × A
# Theoretical risk target (C = B × 0.5) DO NOT USE
# Recommended risk target (account level) (D)
# Recommended instrument level risk target E = A × D
setall(RISK_TARGET, range(1, 2), IDMData(1.00, 0.240, 0.120, 0.12, 0.120))
setall(RISK_TARGET, range(2, 3), IDMData(1.20, 0.288, 0.144, 0.13, 0.156))
setall(RISK_TARGET, range(3, 4), IDMData(1.48, 0.355, 0.178, 0.14, 0.207))
setall(RISK_TARGET, range(4, 5), IDMData(1.56, 0.374, 0.187, 0.17, 0.265))
setall(RISK_TARGET, range(5, 6), IDMData(1.70, 0.408, 0.204, 0.19, 0.323))
setall(RISK_TARGET, range(6, 7), IDMData(1.90, 0.456, 0.228, 0.20, 0.380))
setall(RISK_TARGET, range(7, 8), IDMData(2.10, 0.504, 0.252, 0.23, 0.483))
setall(RISK_TARGET, range(8, 15), IDMData(2.2, 0.528, 0.264, 0.24, 0.528))
setall(RISK_TARGET, range(15, 25), IDMData(2.3, 0.552, 0.276, 0.25, 0.575))
setall(RISK_TARGET, range(25, 30), IDMData(2.4, 0.576, 0.288, 0.25, 0.600))
setall(RISK_TARGET, range(30, 100), IDMData(2.5, 0.600, 0.300, 0.25, 0.625))

# setall(RISK_TARGET, range(1, 2), 12.0)
# setall(RISK_TARGET, range(2, 3), 13.0)
# setall(RISK_TARGET, range(3, 4), 14.0)
# setall(RISK_TARGET, range(4, 5), 17.0)
# setall(RISK_TARGET, range(5, 6), 19.0)
# setall(RISK_TARGET, range(6, 7), 20.0)
# setall(RISK_TARGET, range(7, 8), 23.0)
# setall(RISK_TARGET, range(8, 15), 24.0)
# setall(RISK_TARGET, range(15, 25), 25.0)
# setall(RISK_TARGET, range(25, 30), 25.0)
# setall(RISK_TARGET, range(30, 100), 25.0)

setall(IDM, range(1, 2), 1.0)
setall(IDM, range(2, 3), 1.2)
setall(IDM, range(3, 4), 1.48)
setall(IDM, range(4, 5), 1.56)
setall(IDM, range(5, 6), 1.7)
setall(IDM, range(6, 7), 1.9)
setall(IDM, range(7, 8), 2.1)
setall(IDM, range(8, 15), 2.20)
setall(IDM, range(15, 25), 2.30)
setall(IDM, range(25, 30), 2.40)
setall(IDM, range(30, 100), 2.50)

setall(RDM, range(1, 2), 12.0)
setall(RDM, range(2, 3), 13.0)
setall(RDM, range(3, 4), 14.0)
setall(RDM, range(4, 10), 15.0)
setall(RDM, range(10, 100), 16.0)
