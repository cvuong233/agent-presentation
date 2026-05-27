#!/usr/bin/env python3
"""Create a one-time draft next_lineup from fresh battle results.

Official model:
- `last_matches` = historical truth
- `next_lineup` = editable upcoming lineup
- This script should run only once after new result screenshots are processed.
- After draft creation, future changes must edit `next_lineup` directly.
- No slot-assignment inference, no manual override logic, no repeated rebuild-from-scratch workflow.
"""
import json
import sys
from copy import deepcopy

RANK_ORDER = {"R5": 5, "R4": 4, "R3": 3, "R2": 2, "R1": 1, "?": 0}
MAIN_CAP = 20
SUB_CAP = 10


def ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    d = n % 10
    if d == 1:
        return f"{n}st"
    if d == 2:
        return f"{n}nd"
    if d == 3:
        return f"{n}rd"
    return f"{n}th"


def rank_sort_key(item):
    return RANK_ORDER.get(item.get("r", "?"), 0)


def build_slot(data, battle, slot_letter):
    match = data["last_matches"][battle][slot_letter]
    scores = match.get("scores", {})
    players = data.get("players", {})
    previous = data.get("next_lineup", {}).get(battle, {}).get(slot_letter, {})
    previous_dayoff = {p["name"]: deepcopy(p) for p in previous.get("dayoff", [])}

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    main, subs = [], []

    for pos, (name, score) in enumerate(ranked, start=1):
        if name not in players:
            continue
        p = players[name]
        entry = {
            "r": p.get("rank", "?"),
            "name": name,
            "reason": f"Tuần trước hạng {ordinal(pos)} / {ordinal(pos)} last week",
        }
        yc = p.get("yc", {}).get(battle, 0)
        if yc >= 1:
            entry["reason"] = f"1 thẻ vàng (vắng {battle.upper()}) / 1 YC (missed {battle.upper()})"
            if len(subs) < SUB_CAP:
                subs.append(entry)
            continue

        if len(main) < MAIN_CAP:
            main.append(entry)
        elif len(subs) < SUB_CAP:
            entry["reason"] = "Danh sách chính đã đầy / Main roster full"
            subs.append(entry)

    dayoff = list(previous_dayoff.values())

    return {
        "main": sorted(main, key=rank_sort_key, reverse=True),
        "subs": sorted(subs, key=rank_sort_key, reverse=True),
        "dayoff": sorted(dayoff, key=rank_sort_key, reverse=True),
        "slot": slot_letter,
        "maxMain": MAIN_CAP,
        "maxSubs": SUB_CAP,
        "date": match.get("date", "?"),
        "time": match.get("slot", "?"),
        "period": match.get("slot", "?"),
    }


def main(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # New result cycle => clear per-team recent_removed display buckets before drafting next lineup.
    data["recent_removed"] = {"sm": {"A": [], "B": []}, "hn": {"A": [], "B": []}}
    data["next_lineup"] = {"sm": {}, "hn": {}}
    for battle in ["sm", "hn"]:
        for slot in ["A", "B"]:
            data["next_lineup"][battle][slot] = build_slot(data, battle, slot)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Draft next_lineup created.")
    for battle in ["hn", "sm"]:
        for slot in ["A", "B"]:
            s = data["next_lineup"][battle][slot]
            print(f"  {battle.upper()}-{slot}: {len(s['main'])} main | {len(s['subs'])} subs | {len(s['dayoff'])} dayoff")


if __name__ == "__main__":
    main(sys.argv[1])
