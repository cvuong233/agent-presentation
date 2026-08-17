# Mates Last War VN — Lineup System

## Overview
Automated lineup management for clan **Mates** in Last War VN.

## 🌐 Live Lineup Page
Moved off GitHub Pages — the page now lives in its own Vercel deployment
(see `lastwar-line-up-web/` in the LastWar project). This folder
(`agent-presentation/lastwar/`) is data-only now.

## Architecture
- **`players.json`** — single source of truth: ranks, battle history, and upcoming lineup state. Still lives here.
- **`lineup.html`** — no longer hosted in this repo. The frontend (`lastwar-line-up-web`) reads/writes this data through `lastwar-lineup-be` (a small backend on Railway), which holds the GitHub token and commits here via the Contents API. The frontend also has a direct-from-this-repo fallback read path (`raw.githubusercontent.com`) if that backend is ever down.
- To update: same as before for the data (edit `players.json` → push), but the page itself no longer needs a push/redeploy when only data changes.

## Battles
| Battle | Slot A | Slot B | Main | Subs | Reg Opens | Reg Closes |
|---|---|---|---|---|---|---|
| 🏜️ Bão Sa Mạc (SM) | Sat 18:30 ICT | Sun 08:30 ICT | 20 | 10 | Mon 9am | Thu 9am |
| ⛰️ Bão Hẻm Núi (HN) | Thu 21:30 ICT | Fri 08:30 ICT | 20 | 10 | Sat 9am | Tue 9am |

## Official Data Model
- **`next_lineup`** = editable upcoming lineup
- Each `next_lineup.[sm|hn].[A|B]` contains only:
  - `main[]`
  - `subs[]`
  - `dayoff[]`
- Top-level **`recent_removed[]`** = players recently removed from lineup; show once, then clear next lineup cycle
- **`players[name].yc_sm`** / **`players[name].yc_hn`** = yellow card count for that battle type (`0`, `1`, or `2`). See [Yellow Card (YC) Rules](#yellow-card-yc-rules).
- Remove old concepts from active use:
  - no `off[]`
  - no permanent `removed[]` display list for lineup rendering
  - no slot assignment logic (`sm_team` / `hn_team`) driving lineup rebuilds
  - no `cm` (consecutive miss) tracking — replaced entirely by `yc_sm` / `yc_hn`
- **`last_matches`** is kept as the record of who actually played. It is the *only* evidence used to decide YC resets and YC increments — a name in `last_matches.[sm|hn].[A|B].scores` means that player played.

## Official Lineup Rules
- **Main capacity:** 20
- **Sub capacity:** 10
- **Selection order:** by squad power descending — stronger players in main, weaker in subs
- **Registration:** players register fresh each week with their current main squad power
- **No cm rule, no score-based selection** — these are abolished. The **YC rule is live** — see below.
- **Dayoff:** player misses the upcoming match but is expected back the following cycle
- After each week's registration window, lineups are sorted by power and locked in as **manually edited state**

## Yellow Card (YC) Rules

Attendance penalty system. Tracked **per player, per battle type** in `players[name].yc_sm` and
`players[name].yc_hn`. Values are only ever `0`, `1`, or `2`.

### The three transitions

Only three things ever change a YC count. After every battle, for each player who was **registered**
for it (in `main[]` **or** `subs[]`), apply exactly one of the first two:

| # | Situation | Effect |
|---|---|---|
| 1 | **Registered and PLAYED** — name appears in that battle's `scores` (from main **or** from subs) | `yc = 0` |
| 2 | **Registered and DID NOT play** — name absent from that battle's `scores` | `yc += 1` |
| 3 | Ban expires (the following Saturday) | `yc = 0` |

Consequences of the resulting value:

| Value | Meaning | Lineup effect for the next battle of that type |
|---|---|---|
| `0` | Clean | Normal eligible pool — main or subs by power, as usual |
| `1` | One warning | **Forced into `subs[]`** as penalty. Still registered, still eligible to play. |
| `2` | Second warning | **BANNED for 1 week** from that battle type. Removed from `main[]`, `subs[]`, and waiting list. Ban expires the following **Saturday**; they may re-register the week after, starting at `yc = 0`. |

### The rule that keeps getting broken

> **Playing resets the count to 0 — immediately, at that battle, unconditionally.**
> Playing **from subs** counts as playing. There is no such thing as carrying a YC through
> a battle the player showed up for.

Therefore a ban is only ever legitimate when the player's **two misses were consecutive** —
i.e. they went into the battle *already holding* `yc = 1` and missed again. Reaching `yc = 2`
by adding up two misses that had a played battle between them is **always wrong**.

### Worked examples

**Example A — reset (NOT a ban).** This is the case that was previously handled incorrectly.

| Week | State going in | What happened | Result |
|---|---|---|---|
| 1 | `yc_hn = 0`, in main | Did not play | `yc_hn = 1` → forced to subs next week |
| 2 | `yc_hn = 1`, in subs | **Played from subs** | **`yc_hn = 0`** → back to normal pool |
| 3 | `yc_hn = 0`, in main | Did not play | `yc_hn = 1` → forced to subs next week |

After week 3 the player has **one** yellow card and sits in subs. They are **not** banned.
The old bug was carrying week 1's card past the week-2 appearance and incrementing `1 → 2`.

**Example B — ban (correct).**

| Week | State going in | What happened | Result |
|---|---|---|---|
| 1 | `yc_hn = 0`, in main | Did not play | `yc_hn = 1` → forced to subs next week |
| 2 | `yc_hn = 1`, in subs | Did not play **again** | **`yc_hn = 2`** → banned from HN for 1 week |

Two misses back to back, nothing in between. Banned: removed from HN main, subs, and waiting;
`note` records the ban and its expiry Saturday. SM is untouched — their `yc_sm` is a separate count.

### Edge cases

- **Per battle type, independently.** Playing SM does **not** reset `yc_hn`, and vice versa. Only a
  battle of the same type resets that type's count.
- **Missing from subs still counts as a miss.** Being in `subs[]` is not an excuse; a registered sub
  who does not appear in `scores` takes the card. (Rule 1 is what protects a sub who *did* play —
  not their being a sub.)
- **Dayoff is not a miss.** A player in `dayoff[]` was not registered for that battle: no card, and
  no reset either — their count is left exactly as it was.
- **Not registered at all → nothing happens.** YC only applies to players who were in `main[]` or `subs[]`.
- **Waivers.** Game errors / server issues affecting a whole slot, and players carrying an explicit
  waiver note (e.g. `Haizzzzzzzzzzzz`: `"- YC rules waived"`), do not take cards.
- **A revert is a reset.** If a player is later confirmed to have played (wrong IGN, missed in the
  screenshot), set the count to `0` — do not just decrement it.

### Processing order after a battle

1. Read that battle's `scores` from `last_matches`.
2. For **every** registered name, apply transition 1 or 2 above — **resets first, before any
   increment is considered**, so no stale card survives a battle the player appeared in.
3. Clear any ban whose expiry Saturday has passed (`yc = 0`, drop the `note`).
4. Only now, apply the lineup effects: `yc = 1` → subs, `yc = 2` → removed from all pools.

## Fixed Players
- **Fixed Team A (auto-registered every week):** Lerxinhiu, TusEngland, LinLin, zdevils, cường khùng, Haizzzzzzzzzzzz, Rymi68, wolfwitch
- **Fixed Team B (auto-registered every week):** Hải Anh 0612, Hemerage, yologuy
- At the start of each registration period, fixed players are automatically inserted into their team using their last stored power (`players[name].power` in `players.json`). They don't need to manually register.

## Ranks
- **R5:** Lerxinhiu
- **R4:** Haizzzzzzzzzz, cường khùng, LinLin, Rymi68, Hải Anh 0612, yologuy, Hello AE, Hemerage, zdevils
- **R2:** hanubeast
- **R3:** everyone else (see players.json)
- **R1:** Trần Thế Lươn, ntacutiiii

## Files
| File | Purpose |
|---|---|
| `players.json` | All data: ranks, `last_matches`, `next_lineup`, player info. Source of truth. |
| `verification_checklist.md` | Checklist for making lineup changes / processing results |

`lineup.html` used to live here but was moved to `lastwar-line-up-web`
(separate Vercel deployment) to get instant cache invalidation on
deploy instead of GitHub Pages' CDN TTL. `lineup.py` referenced above
was already gone from this folder before this cleanup.

## Bot Behaviour
- **After lineup change:** bot replies with rank counts per affected slot only (e.g. `SM-B: R4:3 R3:14 R2:1 | Sub:2`)
- **Lineup URL:** only sent when user asks, or in cron reminders
- **Never:** send full lineup table unprompted

## Cron Jobs (OpenClaw)
| ID | Name | Schedule | Timeout |
|---|---|---|---|
| `1585c56a` | Mates Lineup Check | Sat/Sun/Mon/Wed 12pm ICT | 90s |

### Cron logic
- **Sat 12pm:** HN reg opened (Sat 9am) → reset HN lineup, announce registration open
- **Sun 12pm:** HN reminder (deadline Tue 9am, 2 days left)
- **Mon 12pm:** HN final reminder (closes tomorrow Tue 9am) + SM reg opened (Mon 9am) → reset SM lineup
- **Wed 12pm:** SM final reminder (closes tomorrow Thu 9am)

## Official Workflow
1. At start of registration period, bot resets the lineup for that battle (clear main + subs)
2. Players text in: name, battle, team, and their current first squad power
3. Bot adds each player to `next_lineup` with their power value
4. Bot reports main/sub slot for each addition — and flags any changes (e.g. a player bumped from main to sub as stronger players register)
5. Push to GitHub → page updates automatically

## Player Management
- **Move to main:** edit `next_lineup.[mode].[slot].main`
- **Move to sub:** edit `next_lineup.[mode].[slot].subs`
- **Set dayoff:** move player into `next_lineup.[mode].[slot].dayoff`
- **Return from dayoff:** put player back into main/subs in the next cycle
- **Remove from lineup:** remove from `next_lineup` and add to `recent_removed[]`
- **Player leaves clan:** remove from roster and add to `recent_removed[]`
- **Change rank:** update `players.[name].rank` + `ranks` lists

## GitHub
Repo: https://github.com/cvuong233/agent-presentation
Push account: mie-vuong (admin collaborator)
Token: stored in ~/.git-credentials (admin, all cvuong233 repos)
