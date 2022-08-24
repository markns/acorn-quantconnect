import json
import re
from pathlib import Path

scatter_marker_map = {
    'circle': 'circle',
    'square': 'square',
    'diamond': 'diamond',
    'triangle': 'triangle',
    'triangle-down': 'inverted_triangle'
}


def latest_backtest_results_path(project) -> Path:
    path = Path(project)
    list_of_paths = (path / 'backtests').glob('*-*-*_*-*-*');
    return max(list_of_paths, key=lambda p: p.stat().st_ctime)


def results_json(results_path: Path) -> dict:
    results_file = [p for p in results_path.glob("*.json") if re.match(r'\d+.json', p.name)]
    assert len(results_file) == 1
    return json.load(open(results_file[0]))


