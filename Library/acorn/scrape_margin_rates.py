# https://www.oanda.com/eu-en/legal/margin-rates-retail/
import json
import re
import pandas as pd

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
r = requests.get("https://www.oanda.com/eu-en/legal/margin-rates-retail/", headers=headers)

r.raise_for_status()

m = re.search(r'"({.*Japan.*})"', r.text, re.DOTALL)

rates = json.loads(json.loads(m.group(0)))

symbols = pd.read_csv(
    "/data/symbol-properties/symbol-properties-database.csv", comment='#')

rates_df = pd.concat({k: pd.DataFrame(v, columns=['description', 'rate']) for k, v in rates['ALL'].items()})
rates_df = rates_df.droplevel(1).reset_index().rename(columns={'index': 'category'})
rates_df['leverage'] = (1 / rates_df['rate']).astype(int)

df = pd.merge(rates_df, symbols[symbols.market == 'oanda'], how='inner', on='description')

df[['market', 'symbol', 'description', 'leverage']].to_csv('instrument_data.csv', index=False)
