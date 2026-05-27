#!/usr/bin/env python3
"""Quick CLI viewer for official next_lineup data."""
import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name('players.json')

with open(DATA_FILE, encoding='utf-8') as f:
    data = json.load(f)

for battle in ['sm', 'hn']:
    print(f'\n{battle.upper()} NEXT LINEUP')
    for slot in ['A', 'B']:
        d = data['next_lineup'][battle][slot]
        print(f"  {slot}: main={len(d['main'])}/{d.get('maxMain',20)} subs={len(d['subs'])}/{d.get('maxSubs',10)} dayoff={len(d['dayoff'])}")
