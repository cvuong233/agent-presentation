# ACMB Last War VN — Lineup System

## Overview
Automated lineup management for clan **ACMB** in Last War VN.

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
- **`last_matches`** = historical truth (who played, where, and score)
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

## Official Lineup Rules
- **Main capacity:** 20
- **Sub capacity:** 10
- **Selection order for first draft after results:** by last-match score descending
- **1 YC:** sub for that battle
- **2 consecutive YC:** removed from lineup
- **Dayoff:** player misses the upcoming match but is expected back the following cycle
- **Recent removed:** only for players recently taken out of lineup; clear on next lineup cycle
- After the first draft is created from battle results, the upcoming lineup is **manually edited state**, not something to rebuild from scratch repeatedly

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
| `1585c56a` | ACMB Lineup Check | Sat/Sun/Mon/Wed 12pm ICT | 90s |

### Cron logic
- **Sat 12pm:** HN reg opened → ask for HN results
- **Sun 12pm:** Follow up HN / warn Tue 9am deadline
- **Mon 12pm:** Final HN warning + ask for SM results
- **Wed 12pm:** SM closes Thu 9am → remind to register or ask for results

## Official Workflow
1. User sends battle result screenshots
2. Bot reads scores and updates `last_matches`
3. Bot applies YC / removal consequences from those results
4. Bot runs the build script **once** to create the next draft lineup
5. That draft is stored in **`next_lineup`**
6. After that, all lineup changes are made by **directly editing `next_lineup`**
7. Do **not** rerun the build script unless a new battle result arrives
8. Push to GitHub → page updates automatically

## Player Management
- **Move to main:** edit `next_lineup.[mode].[slot].main`
- **Move to sub:** edit `next_lineup.[mode].[slot].subs`
- **Set dayoff:** move player into `next_lineup.[mode].[slot].dayoff`
- **Return from dayoff:** put player back into main/subs in the next cycle
- **Remove from lineup:** remove from `next_lineup` and add to `recent_removed[]`
- **Player leaves clan:** remove from roster/future results and add to `recent_removed[]`
- **Change rank:** update `players.[name].rank` + `ranks` lists
- **Yellow card:** update `players.[name].yc.{hn|sm}` and `cm.{hn|sm}`

## GitHub
Repo: https://github.com/cvuong233/agent-presentation
Push account: mie-vuong (admin collaborator)
Token: stored in ~/.git-credentials (admin, all cvuong233 repos)
