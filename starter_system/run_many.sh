#!/usr/bin/env bash

set -e

for i in NAS100USD JP225USD SPX500USD SG30SGD UK100GBP US2000USD US30USD UK10YBGBP USB02YUSD USB05YUSD USB10YUSD USB30YUSD XAGUSD XAUUSD BCOUSD CORNUSD NATGASUSD SOYBNUSD SUGARUSD WHEATUSD WTICOUSD XCUUSD XPDUSD XPTUSD; do
  echo $i
  sed "s/\$INSTRUMENT/$i/g" starter_system/config_template.json > starter_system/config.json
  lean backtest starter_system
done

cp starter_system/config_template.json starter_system/config.json