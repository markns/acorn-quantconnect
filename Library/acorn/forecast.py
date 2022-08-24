from collections import namedtuple
from typing import Dict, Tuple, List

from QuantConnect.Data import Slice

from acorn.rules import Rule

FORECAST_CAP = 20


def capped_forecast(raw_forecast) -> float:
    if raw_forecast > 0:
        return min(FORECAST_CAP, raw_forecast)
    elif raw_forecast < 0:
        return max(-FORECAST_CAP, raw_forecast)
    else:
        return 0.0


Forecast = namedtuple('Forecast', 'name weight forecast')

class Forecaster:
    def __init__(self, rules: List[Tuple[float, Rule]]):
        self.rules = rules

    def forecast(self, data: Slice) -> (float, List[Forecast]):
        forecasts = []
        for weight, rule in self.rules:
            rule_forecast = rule.forecast(data)

            forecast = capped_forecast(rule_forecast)

            forecasts.append(Forecast(rule.name, weight, forecast))

        return sum([f.weight * f.forecast for f in forecasts]), forecasts

    def ready(self):
        return all([rule.ready() for _, rule in self.rules])
