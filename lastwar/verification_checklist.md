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
- [ ] Apply YC / consecutive miss updates in player records
- [ ] Clear `recent_removed[]` for the new lineup cycle
- [ ] Run `rebuild_lineup.py` once to create draft `next_lineup`
- [ ] After the draft exists, stop rebuilding and switch to direct edits only
