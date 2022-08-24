import decimal
import os

import pandas as pd

import json
from datetime import datetime
from pathlib import Path
import glob
import re


def group_series(values, n=5):
    lst = [datetime.fromtimestamp(v['x']) for v in values]
    indices = [i + 1 for (x, y, i) in zip(lst, lst[1:], range(len(lst))) if n < abs((x - y).days)]
    # pad start index list with 0 and end index list with length of original list
    result = [values[start:end] for start, end in zip([0] + indices, indices + [len(values)])]
    return result


def setall(d, keys, value):
    for k in keys:
        d[k] = value


def round_to_lot_size(q, lot_size):
    # num_digits = decimal.Decimal(str(lot_size)).as_tuple().exponent * -1

    if lot_size == 0.01:
        return round(q, 2)
    elif lot_size == 0.1:
        return round(q, 1)
    elif lot_size == 1:
        return round(q, 0)
    elif lot_size == 10:
        return round(q, -1)
    elif lot_size == 100:
        return round(q, -2)
    else:
        raise Exception(f"unknown lot size {lot_size}")


def load_margin_rates():
    margin_rates_csv = os.path.join(os.path.dirname(__file__), 'instrument_data.csv')
    margin_rates = pd.read_csv(margin_rates_csv, index_col='symbol')
    leverage = margin_rates.leverage.to_dict()
    return leverage
