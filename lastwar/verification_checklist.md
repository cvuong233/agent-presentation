# Lineup Verification Checklist

## BEFORE making Last War lineup changes

- [ ] Confirm you are editing **`next_lineup`**, not rebuilding from scratch
- [ ] Confirm there is **new battle result data** before running `rebuild_lineup.py`
- [ ] If there is no new result data, do **not** rerun the build script
- [ ] Verify the target player exists in `players`
- [ ] Verify the change affects the correct battle (`sm` or `hn`) and slot (`A` or `B`)
- [ ] If moving to `dayoff`, remember they should return next cycle
- [ ] If removing from lineup, add them to `recent_removed[]`
- [ ] Keep capacities within **20 main / 10 subs** for both SM and HN
- [ ] Push `agent-presentation/lastwar/players.json` before reporting success

## WHEN processing fresh battle results

- [ ] Parse all visible players and scores carefully
- [ ] Re-read screenshots to catch missed Mates players
- [ ] **YC step 1 — resets:** every registered player who appears in `scores` gets `yc_[sm|hn] = 0`,
      **including players who played from subs**, and including anyone who was carrying `yc = 1`
- [ ] **YC step 2 — increments:** every registered player absent from `scores` gets `yc_[sm|hn] += 1`
- [ ] Before writing any `yc = 2` ban, confirm the player **entered this battle already at `yc = 1`** —
      a ban is only valid for two *consecutive* misses with no played battle in between
- [ ] Confirm resets used the same battle type (SM play does not clear `yc_hn`, and vice versa)
- [ ] Players in `dayoff[]` were not registered: no card, and no reset
- [ ] Clear expired bans (expiry Saturday passed → `yc = 0`, drop the ban `note`)
- [ ] Apply lineup effects last: `yc = 1` → subs, `yc = 2` → removed from main + subs + waiting
- [ ] Clear `recent_removed[]` for the new lineup cycle
- [ ] Run `rebuild_lineup.py` once to create draft `next_lineup`
- [ ] After the draft exists, stop rebuilding and switch to direct edits only
