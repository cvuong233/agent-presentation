# Mates Last War VN — Lineup System

## Overview
Automated lineup management for clan **Mates** in Last War VN.

## 🌐 Live Lineup Page
**https://cvuong233.github.io/agent-presentation/lastwar/lineup.html**

## Architecture
- **`players.json`** — single source of truth: ranks, battle history, and upcoming lineup state
- **`lineup.html`** — display template only; fetches `players.json` at load time, never edited for data changes
- To update: edit `players.json` → push → GitHub Pages auto-updates

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
- Remove old concepts from active use:
  - no `off[]`
  - no permanent `removed[]` display list for lineup rendering
  - no slot assignment logic (`sm_team` / `hn_team`) driving lineup rebuilds
  - no `last_matches` history
  - no `yc` (yellow card) or `cm` (consecutive miss) tracking

## Official Lineup Rules
- **Main capacity:** 20
- **Sub capacity:** 10
- **Selection order:** by squad power descending — stronger players in main, weaker in subs
- **Registration:** players register fresh each week with their current main squad power
- **No cm rule, no yc rule, no score-based selection** — these are abolished
- **Dayoff:** player misses the upcoming match but is expected back the following cycle
- After each week's registration window, lineups are sorted by power and locked in as **manually edited state**

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
| `players.json` | All data: ranks, `last_matches`, `next_lineup`, player info |
| `lineup.html` | Web UI — GitHub Pages display template |
| `lineup.py` | CLI summary viewer for `next_lineup` |

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
