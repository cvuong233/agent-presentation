# agent-presentation

## LastWar lineup work (`lastwar/`)

`lastwar/players.json` is the single source of truth. **Read `lastwar/README.md` before editing it**,
and walk `lastwar/verification_checklist.md` before reporting success. Those two files are the rules;
do not restate or reinterpret them here.

One rule is repeated here because it has been misapplied more than once:

> A yellow card resets to `0` the moment a registered player **plays** a battle — including when they
> play **from subs**. A `yc = 2` ban is only valid when the player entered that battle *already
> holding* `yc = 1` and missed again. Two misses with a played battle between them is `yc = 1`, never a ban.

`yc_sm` and `yc_hn` are separate counts; playing one battle type never resets the other.

Full rules, worked examples, and edge cases: [`lastwar/README.md`](lastwar/README.md#yellow-card-yc-rules).
