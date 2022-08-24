from datetime import datetime
from pathlib import Path

from bokeh.io import show
from bokeh.layouts import column
from bokeh.models import HoverTool
from bokeh.plotting import figure

from acorn.reporting import latest_backtest_results_path

from collections import namedtuple

# Declaring namedtuple()
Metrics = namedtuple('Metrics', ['datetime', 'symbol', 'metrics'])

hover = HoverTool(tooltips=[('series', '$name'), ('date', '$x{%F}'), ('value', '$y')],
                  formatters={'$x': 'datetime'},
                  # display a tooltip whenever the cursor is vertically in line with a glyph
                  # mode='vline'
                  )


# §
# 2022-08-24T08:55:17.0045143Z TRACE:: Debug: § 2004-03-17 00:00:00+00:00 WTICOUSD quantity: 109.0 price: 37.406
# 2022-08-24T08:55:17.0052008Z TRACE:: Debug: § 2004-03-18 00:00:00+00:00 WTICOUSD quantity: 109.0 price: 38.465
def parse_section_symbol_log(logpath):
    results = []
    with open(logpath, "r") as f:
        for line in f.readlines():
            if "§" in line:
                _, line = line.split('§')
                date_str, time_str, symbol, *m = line.split()
                dt = datetime.fromisoformat(f'{date_str}T{time_str}')
                metrics = dict(zip([m[i].replace(':', '') for i in range(0, len(m), 2)],
                                   [float(m[i]) for i in range(1, len(m), 2)]))

                results.append(Metrics(dt, symbol, metrics))
    return results


def gen_figure(results, metric, x_range=None, height=80):
    if x_range:
        p = figure(title=metric,  x_range=x_range, x_axis_type="datetime", height=height)
    else:
        p = figure(title=metric,  x_axis_type="datetime", height=height)
    p.add_tools(hover)
    p.line(x=[m.datetime for m in results],
           y=[m.metrics[metric] for m in results],
           name=metric)
    return p


if __name__ == '__main__':
    project = "starter_system"
    base_dir = Path('/Users/markns/workspace/acorn-quantconnect')

    backtest_path = latest_backtest_results_path(base_dir / project)

    results = parse_section_symbol_log(backtest_path / "log.txt")

    pf = gen_figure(results, 'portfolio_value')
    figures = [
        pf,
        gen_figure(results, 'price', pf.x_range),
        gen_figure(results, 'forecast', pf.x_range),
        gen_figure(results, 'returns_vol', pf.x_range),
        gen_figure(results, 'position', pf.x_range),
    ]

    show(column(*figures, sizing_mode="scale_width"))
