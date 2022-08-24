from abc import ABC, abstractmethod

from QuantConnect import Symbol, Resolution, Field
from QuantConnect.Algorithm import QCAlgorithm
from QuantConnect.Data import Slice
from QuantConnect.Indicators import IndicatorExtensions, Delay

from acorn.risk import InstrumentRiskEstimator

# systems/provided/rob_system/config.yaml forecast_scalars
# https://qoppac.blogspot.com/2016/01/pysystemtrader-estimated-forecast.html
# calculated using =10/avg(unscaled forecasts from all instruments)

forecast_scalars = dict(
    momentum8=109.473551,
    momentum16=77.45129409,
    momentum32=54.77242347,
    momentum64=38.14611924,
    breakout10=24.30102541,
    breakout20=28.15312063,
    breakout40=30.99295079,
    breakout80=32.53503213,
    breakout160=33.90593672,
    breakout320=34.25142134,
    accel16=115.1031721,
    accel32=81.77387461,
    accel64=57.03119723,

    assettrend2=10.846520114531351,
    assettrend4=7.572334583056326,
    assettrend8=5.190470936448635,
    assettrend16=3.549452858682833,
    assettrend32=2.3449234496490723,
    assettrend64=1.5465144366886119,
    normmom2=12.388305650778637,
    normmom4=8.614429965006694,
    normmom8=5.979138542342214,
    normmom16=4.116536590599602,
    normmom32=2.758872936017786,
    normmom64=1.8706800701120874,
    carry10=27.815707053556984,
    carry125=29.366474500729886,
    carry30=28.384062881349813,
    carry60=28.40072429176199,
    mrinasset160=216.84406362722757,
    mrwrings4=2.1443531683677626,
    relcarry=49.44179741391023,
    relmomentum10=61.24026078373817,
    relmomentum20=86.50746400987076,
    relmomentum40=117.77937298659975,
    relmomentum80=159.87802982511536,
    skewabs180=4.590246757939031,
    skewabs365=2.351483885205172,
    skewrv180=5.244752769697409,
    skewrv365=3.002222097593425,
)


# See https://qoppac.blogspot.com/2021/12/my-trading-system.html
# "Which trading rules to use"

class Rule(ABC):
    @abstractmethod
    def name(self) -> str:
        return "rule"

    @abstractmethod
    def ready(self) -> bool:
        pass

    @abstractmethod
    def forecast(self, data: Slice) -> float:
        pass

    @abstractmethod
    def plot(self) -> None:
        pass


class BreakoutRule(Rule):
    @property
    def name(self):
        return self._name

    def __init__(self, api: QCAlgorithm, name: str, symbol: Symbol, n: int):
        self.api = api
        self._name = name
        self.symbol = symbol
        self.max = api.MAX(symbol, n, Resolution.Daily, Field.Close)
        self.min = api.MIN(symbol, n, Resolution.Daily, Field.Close)

    def ready(self) -> bool:
        return self.max.IsReady

    def forecast(self, data: Slice) -> float:
        avg = (self.max.Current.Value + self.min.Current.Value) / 2

        if not data.ContainsKey(self.symbol):
            self.api.Debug(
                f"{self.__class__.__name__} unable to forecast {self.symbol} for {data.UtcTime} - missing price")
            return 0

        price = data[self.symbol].Price
        signal = (price - avg) / (self.max.Current.Value - self.min.Current.Value)

        return signal * forecast_scalars[self.name]

    def plot(self) -> None:
        pass


class EWMACRule(Rule):
    # todo: systems.provided.rules.ewmac.ewmac_calc_vol uses vol
    def __init__(self, api: QCAlgorithm, name: str, symbol: Symbol, risk: InstrumentRiskEstimator, fast, slow=None):
        slow = slow if slow else fast * 4

        self.api = api
        self._name = name
        self.symbol = symbol
        self.fast_ma = api.EMA(symbol, fast, Resolution.Daily, Field.Close)
        self.slow_ma = api.EMA(symbol, slow, Resolution.Daily, Field.Close)
        self.risk_estimator = risk

    @property
    def name(self) -> str:
        return self._name

    def ready(self) -> bool:
        return self.slow_ma.IsReady

    def forecast(self, data: Slice) -> float:
        # MACf,st = MAft – MAst
        mac = self.fast_ma.Current.Value - self.slow_ma.Current.Value

        # Instrument risk in price units = Instrument risk as percentage volatility × current price
        risk_in_price_units = self.risk_estimator.estimate() * data[self.symbol].Price

        # Risk-adjusted MAC forecast = MAC ÷ instrument risk in price units
        risk_adj_mac = mac / risk_in_price_units

        return risk_adj_mac * forecast_scalars[self.name]

    def plot(self) -> None:
        pass


class AccelRule(Rule):
    def __init__(self, api: QCAlgorithm, name: str, symbol: Symbol, risk: InstrumentRiskEstimator, fast, slow=None):
        slow = slow if slow else fast * 4

        self.api = api
        self._name = name
        self.symbol = symbol
        self.fast_ma = api.EMA(symbol, fast, Resolution.Daily, Field.Close)
        self.slow_ma = api.EMA(symbol, slow, Resolution.Daily, Field.Close)

        self.fast_ma_lag = IndicatorExtensions.Of(Delay(fast), self.fast_ma)
        self.slow_ma_lag = IndicatorExtensions.Of(Delay(fast), self.slow_ma)

        self.risk_estimator = risk

    @property
    def name(self) -> str:
        return self._name

    def ready(self) -> bool:
        return self.slow_ma_lag.IsReady

    def forecast(self, data: Slice) -> float:
        mac = self.fast_ma.Current.Value - self.slow_ma.Current.Value
        risk_in_price_units = self.risk_estimator.estimate() * data[self.symbol].Price
        risk_adj_mac = mac / risk_in_price_units

        mac_lag = self.fast_ma_lag.Current.Value - self.slow_ma_lag.Current.Value
        # TODO: ideally we would use the historic risk and price
        risk_adj_mac_lag = mac_lag / risk_in_price_units

        signal = risk_adj_mac - risk_adj_mac_lag

        return signal * forecast_scalars[self.name]

    def plot(self) -> None:
        pass

# TODO: implement carry rule if possible
