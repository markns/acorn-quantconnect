from QuantConnect import Resolution, Field
from QuantConnect.Algorithm import QCAlgorithm
from QuantConnect.Indicators import IndicatorExtensions, StandardDeviation, Indicator, IndicatorDataPoint
from QuantConnect.Securities import Security

from acorn.constants import BUSINESS_DAYS_IN_YEAR


# see pysystemtrade sysquant.estimators.vol.mixed_vol_calc
class InstrumentRiskEstimator:
    def __init__(self, api: QCAlgorithm, security: Security, vol_window: int):
        self.api = api
        self.security = security

        daily_returns_pct = self.api.ROC(security.Symbol, 1, Resolution.Daily, Field.Close)
        std_returns_pct = IndicatorExtensions.Of(StandardDeviation(vol_window), daily_returns_pct)
        self.ema_std_returns_pct = IndicatorExtensions.EMA(std_returns_pct, vol_window,
                                                           waitForFirstToReady=False)

        # daily_returns_pct.Updated += self.update_event_handler
        # ema_daily_returns_pct.Updated += self.update_event_handler
        # self.returns_vol_indicator.Updated += self.update_event_handler

        slow_vol_days = BUSINESS_DAYS_IN_YEAR * 20
        slow_std_returns_pct = IndicatorExtensions.Of(StandardDeviation(slow_vol_days), daily_returns_pct)
        self.slow_vol_indicator = IndicatorExtensions.EMA(slow_std_returns_pct, slow_vol_days,
                                                          waitForFirstToReady=False)

        self.slow_vol_indicator = IndicatorExtensions.Of(StandardDeviation(slow_vol_days), daily_returns_pct)

    def estimate(self):
        proportion_of_slow_vol = 0.3
        daily = (self.slow_vol_indicator.Current.Value * proportion_of_slow_vol +
                 self.ema_std_returns_pct.Current.Value * (1 - proportion_of_slow_vol))

        return daily * 16

    def update_event_handler(self, indicator: Indicator, indicator_data_point: IndicatorDataPoint) -> None:
        if indicator.IsReady:
            self.api.Debug(
                f"{self.security.Symbol} Indicator {indicator.Name} {indicator.ToDetailedString()} {indicator.Samples} "
                f"{indicator_data_point.Time} {indicator_data_point.DataTimeZone()} {indicator_data_point.Value}")
