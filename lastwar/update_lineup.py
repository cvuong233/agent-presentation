#!/usr/bin/env python3
"""Manual next_lineup editor helpers for the official Last War model.

This file intentionally avoids rebuilding from scratch.
Use it only to modify `next_lineup` directly after the one-time draft exists.
"""
import json
import sys
from pathlib import Path

DATA_FILE = Path(__file__).with_name('players.json')


def load_data():
    with open(DATA_FILE, encoding='utf-8') as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def find_and_remove(slot_data, name):
    removed = None
    for section in ['main', 'subs', 'dayoff']:
        arr = slot_data.get(section, [])
        for i, item in enumerate(arr):
            if item['name'] == name:
                removed = arr.pop(i)
                return removed, section
    return None, None


def move_player(mode, slot, name, target):
    data = load_data()
    slot_data = data['next_lineup'][mode][slot]
    entry, source = find_and_remove(slot_data, name)
    if not entry:
        raise SystemExit(f'{name} not found in next_lineup {mode}-{slot}')
    slot_data[target].append(entry)
    save_data(data)
    print(f'Moved {name}: {mode}-{slot} {source} -> {target}')


def remove_player(mode, slot, name, reason):
    data = load_data()
    slot_data = data['next_lineup'][mode][slot]
    entry, source = find_and_remove(slot_data, name)
    if not entry:
        raise SystemExit(f'{name} not found in next_lineup {mode}-{slot}')
    data.setdefault('recent_removed', {'sm': {'A': [], 'B': []}, 'hn': {'A': [], 'B': []}})
    data['recent_removed'].setdefault(mode, {'A': [], 'B': []})
    data['recent_removed'][mode].setdefault(slot, []).append({
        'name': name,
        'rank': entry.get('r'),
        'reason': reason,
        'date': data.get('meta', {}).get('updated', '')
    })
    save_data(data)
    print(f'Removed {name} from {mode}-{slot} ({source})')


if __name__ == '__main__':
    print('Manual next_lineup helper. Import and call move_player/remove_player as needed.')
