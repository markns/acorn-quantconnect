# Acorn QuantConnect

This project is an implementation of the "starter system" described in [Rob Carver](https://qoppac.blogspot.com/p/about-me.html)'s book [Leveraged Trading](https://www.systematicmoney.org/leveraged-trading)

It uses the [LEAN](https://www.quantconnect.com/docs/v2/lean-cli) backtesting engine developed by [Quant Connect](https://www.quantconnect.com/) and trades CFDs via the Oanda brokerage.

## Results

Results are not spectacular, but are correlated with the Eurekahedge Trend Following Index, which is used as the benchmark in the chart below.  

![paas](/static/results.png)

## Backtesting

For backtesting it is necessary to download historical data

```
> lean data download \
    --dataset "CFD Data" \
    --organization "$organization" \
    --ticker "AU200AUD, BCOUSD, CH20CHF, CORNUSD, DE10YBEUR, DE30EUR, EU50EUR, FR40EUR, HK33HKD, JP225USD, NAS100USD, NATGASUSD, NL25EUR, SG30SGD, SOYBNUSD, SPX500USD, SUGARUSD, UK100GBP, UK10YBGBP, US2000USD, US30USD, USB02YUSD, USB05YUSD, USB10YUSD, USB30YUSD, WHEATUSD, WTICOUSD, XAGAUD, XAGCAD, XAGCHF, XAGEUR, XAGGBP, XAGHKD, XAGJPY, XAGNZD, XAGSGD, XAGUSD, XAUAUD, XAUCAD, XAUCHF, XAUEUR, XAUGBP, XAUHKD, XAUJPY, XAUNZD, XAUSGD, XAUUSD, XAUXAG, XCUUSD, XPDUSD, XPTUSD" \
    --resolution "Hour" \
    --start "20020501" \
    --end "20220725"

> lean data download \
    --dataset "FOREX Data" \
    --organization "$organization" \
    --ticker "NZDUSD,EURUSD,AUDUSD,USDJPY,USDCHF,GBPUSD,USDHKD,USDSGD,USDCAD" \
    --resolution "Daily" \
    --start "20000101" \
    --end "20220725"
    
> lean backtest starter_system

> lean report --report-destination reports/report.html
 
```