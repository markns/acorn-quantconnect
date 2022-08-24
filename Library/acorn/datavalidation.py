from datetime import timedelta

from QuantConnect.Algorithm import QCAlgorithm
from QuantConnect.Data import Slice
from System import Exception


class DataValidator:
    def __init__(self, api: QCAlgorithm, tolerance=0.25):
        self.api = api
        self.high_tolerance = 1 + tolerance
        self.low_tolerance = 1 - tolerance
        self.last_data = None

    def validate(self, data: Slice):
        if self.last_data is None:
            self.last_data = data
            return

        for symbol, bar in data.items():
            if symbol in self.last_data:
                last_bar = self.last_data[symbol]

                pairs = ((bar.Bid.Open, last_bar.Bid.Open),
                         # (bar.Bid.High, last_bar.Bid.High),
                         # (bar.Bid.Low, last_bar.Bid.Low),
                         (bar.Bid.Close, last_bar.Bid.Close),
                         (bar.Ask.Open, last_bar.Ask.Open),
                         # (bar.Ask.High, last_bar.Ask.High),
                         # (bar.Ask.Low, last_bar.Ask.Low),
                         (bar.Ask.Close, last_bar.Ask.Close))
                for val, last_val in pairs:
                    if val > last_val * self.high_tolerance or val < last_val * self.low_tolerance:
                        raise Exception(f'bad data for symbol {symbol}\n'
                                        f'last_bar: {last_bar.EndTime} {last_bar}\n'
                                        f' new_bar: {bar.EndTime} {bar}')

                if bar.EndTime - last_bar.EndTime > timedelta(days=5):
                    self.api.Error(f"bad data for symbol {symbol} - gap between bars greater than 5 days\n"
                                   f'last_bar: {last_bar.EndTime} {last_bar}\n'
                                   f' new_bar: {bar.EndTime} {bar}')

        self.last_data = data
