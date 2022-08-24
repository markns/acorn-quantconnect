from collections import defaultdict
from datetime import date
from math import copysign

from AlgorithmImports import *
from QuantConnect import Resolution, Market
from QuantConnect.Algorithm import QCAlgorithm
from QuantConnect.Data import Slice
from QuantConnect.Securities.Cfd import Cfd

from acorn.datavalidation import DataValidator
from acorn.enums import CapitalCorrection
from acorn.forecast import Forecaster
from acorn.risk import InstrumentRiskEstimator
from acorn.risktarget import RISK_TARGET, IDMData
from acorn.rules import BreakoutRule, EWMACRule, AccelRule
from acorn.utils import round_to_lot_size, load_margin_rates

# https://qoppac.blogspot.com/2020/03/how-much-risk-should-we-take.html

NOTIONAL_TRADING_CAPITAL = 25_000
EXPOSURE_DEVIATION_THRESHOLD = 0.2
VOLA_WINDOW = 35
TRACE = True

# trading capital should be fixed (or half-compounded) in backtest and variable in live
# https://qoppac.blogspot.com/2016/06/capital-correction-pysystemtrade.html
CAPITAL_CORRECTION = CapitalCorrection.FIXED
# CAPITAL_CORRECTION = CapitalCorrection.FULL_COMPOUNDING


EXCLUDE_INSTRUMENTS = {
    'CH20CHF',  # bad data 2003-03-21,  9/19/2017 - years of 8641.5 values

    'XAGAUD', 'XAGCAD', 'XAGCHF', 'XAGEUR', 'XAGGBP', 'XAGHKD', 'XAGJPY',
    'XAGNZD', 'XAGSGD',
    'XAUAUD', 'XAUCAD', 'XAUCHF', 'XAUEUR', 'XAUGBP', 'XAUHKD', 'XAUJPY', 'XAUNZD',
    'XAUSGD', 'XAUXAG',

    'DE10YBEUR',

    # Markets too safe (Annual % std. dev < 5.0):
    'USB02YUSD',  # 2003-05-13
    # ['BTP3', 'CNH-onshore', 'EDOLLAR', 'ETHANOL',
    # 'EURIBOR', 'JGB', 'JGB-SGX-mini', 'KR3', 'SHATZ', 'US2', 'US3']

}

INCLUDE_INSTRUMENTS = {
    # # # equity
    # 'CH20CHF',
    # 'AU200AUD',
    # 'JP225USD',
    # 'NAS100USD',
    # 'SPX500USD',
    # 'SG30SGD',
    # 'UK100GBP',
    # 'US2000USD',
    # 'US30USD',
    # # # # fixed income
    # 'UK10YBGBP',
    # 'USB02YUSD',
    # 'USB05YUSD',
    # 'USB10YUSD',
    # 'USB30YUSD',
    # metals
    'XAGUSD',
    'XAUUSD',  # data ends 2019-02-25?
    'XCUUSD',
    'XPDUSD',
    'XPTUSD',
    # # # commodities
    'BCOUSD',
    'CORNUSD',
    'NATGASUSD',
    'SOYBNUSD',
    'SUGARUSD',
    'WHEATUSD',
    'WTICOUSD',
}

# INCLUDE_INSTRUMENTS = set()
INSTRUMENTS = INCLUDE_INSTRUMENTS - EXCLUDE_INSTRUMENTS


# https://qoppac.blogspot.com/2020/12/dynamic-trend-following.html
# https://gist.github.com/robcarver17/61fd128d4210a27b20b7358a3efed7f0

class PositionDirection(Enum):
    NONE = 0
    LONG = 1
    SHORT = 2


class Position:

    def __init__(self, api: QCAlgorithm, cfd: Cfd, capital, idm_data: IDMData,
                 forecaster: Forecaster,
                 risk_estimator: InstrumentRiskEstimator):
        self.api = api
        self.cfd = cfd
        self._capital = capital
        self.idm_data = idm_data
        self.forecaster = forecaster
        self.risk_estimator = risk_estimator

        self.trend = None
        self.last_position = PositionDirection.NONE
        self.high_watermark = 0
        self.stop_loss_gap = None

    def on_data(self, data: Slice):

        if not self.forecaster.ready():
            return

        forecast, raw_forecast_data = self.forecaster.forecast(data)
        # forecast = self.forecaster.forecast(data)

        buying_power = self.api.Portfolio.GetBuyingPower(self.cfd.Symbol, OrderDirection.Buy)
        portfolio_value = self.api.Portfolio.TotalPortfolioValue
        margin_remaining = self.api.Portfolio.MarginRemaining / len(self.api.Portfolio)

        ideal_notional_exposure = self.notional_exposure(forecast)
        # TODO: better to halve the trading capital if only trading one instrument.
        if margin_remaining * self.cfd.Leverage < abs(ideal_notional_exposure):
            capped_notional_exposure = copysign(margin_remaining * self.cfd.Leverage, ideal_notional_exposure)
        else:
            capped_notional_exposure = ideal_notional_exposure

        # CFD (per contract) exposure = (CFD contracts × price × contract size) ÷ FX Rate
        position = self.api.Portfolio[self.cfd.Symbol]
        assert data[self.cfd.Symbol].Price == self.cfd.Price
        fx = self.fx_instrument_to_account()
        current_exposure = (position.Quantity * self.cfd.Price * self.cfd.ContractMultiplier) * fx

        # average exposure is the size of position for a forecast of 10
        # Average exposure = [target risk % × capital] ÷ instrument risk %
        target_risk = self.target_risk()
        raw_target_risk = self.raw_target_risk()
        average_exposure = (target_risk * self.capital) / self.risk_estimator.estimate()
        exposure_deviation = (capped_notional_exposure - current_exposure) / average_exposure

        raw_position_size = self.position_size(capped_notional_exposure)
        position_size = round_to_lot_size(raw_position_size, self.cfd.SymbolProperties.LotSize)

        if TRACE:
            self.api.Debug(f"§ {self.api.UtcTime} {self.cfd.Symbol} "
                           f"position: {position.Quantity} "
                           f"price: {self.cfd.Price} "
                           f"capital: {self.capital:.2f} "
                           f"raw_target_risk: {raw_target_risk:.2f} "
                           f"target_risk: {target_risk:.2f} "
                           f"returns_vol: {self.risk_estimator.estimate():.2f} "
                           f"forecast: {forecast:.1f} "
                           f"ideal_exposure: {ideal_notional_exposure:.1f} "
                           f"capped_exposure: {capped_notional_exposure:.1f} "
                           f"current_exposure: {current_exposure:.1f} "
                           f"average_exposure: {average_exposure:.1f} "
                           f"exposure_deviation: {exposure_deviation:.2f} "
                           f"fx: {fx:.2f} "
                           f"lot_size: {self.cfd.SymbolProperties.LotSize} "
                           f"leverage: {self.cfd.Leverage} "
                           f"raw_pos_size: {raw_position_size:.2f} "
                           f"pos_size: {position_size:.1f} "
                           f"portfolio_value: {portfolio_value:.2f} "
                           f"buying_power: {buying_power:.2f} "
                           f"margin_used: {self.api.Portfolio.TotalMarginUsed:.2f} "
                           f"margin_remaining: {self.api.Portfolio.MarginRemaining:.2f}"
                           )
            self.api.Debug(
                f"∞ {self.api.UtcTime} {self.cfd.Symbol} "
                f"{[f.name + ': ' + f'{round(f.forecast, 2)}' for f in raw_forecast_data]}")

        if abs(exposure_deviation) > EXPOSURE_DEVIATION_THRESHOLD:
            order_quantity = round_to_lot_size(position_size - position.Quantity, self.cfd.SymbolProperties.LotSize)
            if order_quantity != 0:
                self.api.Debug(f"{data.UtcTime} {self.cfd.Symbol} sending order {order_quantity}")
                self.api.MarketOrder(self.cfd.Symbol, order_quantity)

    @property
    def capital(self):
        if CAPITAL_CORRECTION == CapitalCorrection.FULL_COMPOUNDING:
            return self.api.Portfolio.TotalPortfolioValue / len(INSTRUMENTS)
        else:
            return self._capital

    def notional_exposure(self, forecast: float) -> float:
        # Formula 14: Notional exposure from risk and capital
        # Notional exposure = (target risk % × capital) ÷ instrument risk %
        # the instrument risk is the annualised standard deviation of returns.

        notional_exposure = ((forecast / 10) * self.target_risk() * self.capital) / self.risk_estimator.estimate()
        return notional_exposure

    def target_risk(self) -> float:
        return self.raw_target_risk() * self.idm_data.idm

    def raw_target_risk(self) -> float:
        # The target risk is the annual standard deviation that you want on your account.

        # Target risk should be the set at the lowest, most conservative, value from the following list:
        # * maximum risk possible given leverage allowed by brokers or exchanges
        # Formula 15: Risk target possible given maximum leverage
        # Risk target = (Maximum leverage factor × instrument risk)
        risk_given_max_leverage = self.cfd.Leverage * self.risk_estimator.estimate()
        #
        # * maximum risk possible given prudent leverage limits
        # todo: add prudent leverage risk limits
        # Formula 16: Prudent leverage factor
        # Prudent leverage factor = Maximum bearable loss ÷ worst possible instrument loss
        # Formula 17: Maximum risk target given prudent leverage
        # Prudent maximum risk target = Prudent leverage factor × instrument risk
        #
        # * maximum risk given your own personal appetite for risk
        # See Table 11: Chances of a given annual loss when running the Starter System
        personal_appetite = 0.25
        #
        # * optimal risk level given the expected profitability of your trading system
        # Formula 18: Prudent ‘half Kelly’ risk target from Sharpe ratio:
        # Prudent risk target = Expected Sharpe ratio ÷ 2
        half_kelly = self.idm_data.risk_target  # nb. idm_data.risk_target is already SR % 2

        return min(risk_given_max_leverage, personal_appetite, half_kelly)

    def fx_account_to_instrument(self) -> float:
        if self.cfd.QuoteCurrency.Symbol == self.api.AccountCurrency:
            return 1
        else:
            # todo: euro instruments not working
            return 1 / self.cfd.QuoteCurrency.CurrencyConversion.ConversionRate

    def fx_instrument_to_account(self) -> float:
        if self.cfd.QuoteCurrency.Symbol == self.api.AccountCurrency:
            return 1
        else:
            # todo: euro instruments not working
            return self.cfd.QuoteCurrency.CurrencyConversion.ConversionRate

    def position_size(self, notional_exposure: float):
        # Calculating position sizes for a given trade is a two-step process.
        # Step one: determine the required notional exposure in your home currency for your chosen instrument.
        # For example, we may want to take £7,500 of long exposure to the Euro Stoxx 50 equity index.
        # Our desired notional exposure is the same regardless of the product we are using.

        # Step two: calculate what that exposure corresponds to in units of the relevant product:
        # how many futures or CFD contracts; or how many £ or $ per point of spread bets.

        # contracts = (Exposure home currency × FX Rate) ÷ (price × contract size)
        fx = self.fx_account_to_instrument()
        contracts = (notional_exposure * fx) / (self.cfd.Price * self.cfd.ContractMultiplier)

        return contracts


class StarterSystem(QCAlgorithm):

    def Initialize(self):
        # self.SetTimeZone("America/New_York")
        self.SetTimeZone("UTC")
        self.SetAccountCurrency("USD")
        self.SetBenchmark(SecurityType.Index, "EUREKAHEDGE")
        self.SetBrokerageModel(BrokerageName.OandaBrokerage, AccountType.Margin)
        self.SetStartDate(2003, 1, 1)
        # self.SetStartDate(2020, 1, 1)
        # self.SetEndDate(2004, 6, 1)
        # self.SetEndDate(2003, 6, 25)
        self.SetEndDate(2022, 7, 1)
        self.SetCash(NOTIONAL_TRADING_CAPITAL)  # Set Strategy Cash
        self.data_validator = DataValidator(api=self)
        self.positions = []

        leverage = load_margin_rates()

        config_instrument = self.GetParameter("instrument")
        if config_instrument == '$INSTRUMENT':
            instruments = sorted(INSTRUMENTS)
        else:
            instruments = [config_instrument]

        for ticker in instruments:
            cfd = self.AddCfd(ticker, Resolution.Hour,
                              market=Market.Oanda,
                              leverage=leverage[ticker],
                              fillDataForward=False)
            self.Debug(f"Added cfd {cfd.Symbol}")

            # TODO: Failed to assign conversion rates for the following cash: EUR,HKD.
            #  Attempting to request daily resolution history to resolve conversion rate
            if cfd.QuoteCurrency.Symbol in ['HKD', 'EUR']:
                self.RemoveSecurity(cfd.Symbol)
                self.Debug(f"Excluding cfd {cfd.Symbol} with currency {cfd.QuoteCurrency.Symbol}")
                continue

            risk_estimator = InstrumentRiskEstimator(self, cfd, VOLA_WINDOW)

            rules = [
                (0.3 / 4, EWMACRule(self, 'momentum8', cfd.Symbol, risk_estimator, 8)),
                (0.3 / 4, EWMACRule(self, 'momentum16', cfd.Symbol, risk_estimator, 16)),
                (0.3 / 4, EWMACRule(self, 'momentum32', cfd.Symbol, risk_estimator, 32)),
                (0.3 / 4, EWMACRule(self, 'momentum64', cfd.Symbol, risk_estimator, 64)),
                (0.3 / 6, BreakoutRule(self, 'breakout10', cfd.Symbol, 10)),
                (0.3 / 6, BreakoutRule(self, 'breakout20', cfd.Symbol, 20)),
                (0.3 / 6, BreakoutRule(self, 'breakout40', cfd.Symbol, 40)),
                (0.3 / 6, BreakoutRule(self, 'breakout80', cfd.Symbol, 80)),
                (0.3 / 6, BreakoutRule(self, 'breakout160', cfd.Symbol, 160)),
                (0.3 / 6, BreakoutRule(self, 'breakout320', cfd.Symbol, 320)),
                (0.3 / 3, AccelRule(self, 'accel16', cfd.Symbol, risk_estimator, 16)),
                (0.3 / 3, AccelRule(self, 'accel32', cfd.Symbol, risk_estimator, 32)),
                (0.3 / 3, AccelRule(self, 'accel64', cfd.Symbol, risk_estimator, 64)),
            ]

            forecaster = Forecaster(rules)

            capital = round(NOTIONAL_TRADING_CAPITAL / len(instruments), 0)

            idm_data = RISK_TARGET[len(self.Portfolio)]

            position = Position(self, cfd, capital,
                                idm_data,
                                forecaster, risk_estimator)
            self.positions.append(position)

        self.last_processed_date = defaultdict(lambda: date(1970, 1, 1))
        self.data = []

    def OnEndOfAlgorithm(self) -> None:
        for k, v in self.Portfolio.items():
            self.Debug(f"{k} {v}")

        # df = pd.DataFrame(self.data, columns=['datetime', 'price', 'daily_return', 'returns_vol', 'position'])
        # df = df.set_index('datetime')
        # # df = df.resample('1B').first()
        # df.to_pickle(f'/Results/data.pkl')

    def OnData(self, data: Slice):
        # self.Debug(f"{data.UtcTime} price: {data['CORNUSD'].Price}")
        # return

        self.data_validator.validate(data)

        for position in self.positions:
            if position.cfd.Exchange.ExchangeOpen:
                if (data.UtcTime.date() > self.last_processed_date[position.cfd] and
                        data.ContainsKey(position.cfd.Symbol)):
                    position.on_data(data)
                    self.last_processed_date[position.cfd] = data.UtcTime.date()

                    # self.Debug(f"price: {data['CORNUSD'].Price}")
                    # return
