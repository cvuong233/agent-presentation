#!/usr/bin/env python3
"""
Scrapes FUNdex weekly TV/OTT drama buzzworthiness chart and enriches
each entry with TMDB + IMDb metadata.

Source  : https://www.fundex.co.kr  (weekly chart)
Enrich  : TMDB API  (https://api.themoviedb.org/3)
Output  : kdrama_charts.json  (repo root)
"""
import asyncio
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from playwright.async_api import async_playwright

# ── Config ────────────────────────────────────────────────────────────────────
TMDB_API_KEY = "1f54bd990f1cdfb230adb312546d765d"
TMDB_BASE    = "https://api.themoviedb.org/3"
FUNDEX_URL   = "https://www.fundex.co.kr/fundex/funtopChart.do"
CHART_MODE   = "weekly_tv_ott_drama_buzzworthiness"
MAX_ENTRIES  = 20

# ── Helpers ───────────────────────────────────────────────────────────────────

def tmdb_get(path: str, params: dict | None = None) -> dict:
    p = {"api_key": TMDB_API_KEY, **(params or {})}
    r = requests.get(f"{TMDB_BASE}{path}", params=p, timeout=15)
    r.raise_for_status()
    return r.json()


def normalize(s: str) -> str:
    """Lowercase, strip accents, collapse spaces."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def score_title_match(query: str, candidate: str) -> float:
    q, c = normalize(query), normalize(candidate)
    if q == c:
        return 1.0
    if q in c or c in q:
        return 0.8
    # Overlap score
    q_words = set(q.split())
    c_words = set(c.split())
    if not q_words:
        return 0.0
    return len(q_words & c_words) / len(q_words)


def find_tmdb_show(title: str, year: str | None = None) -> dict | None:
    """Search TMDB for a TV show matching title (and optionally year)."""
    params: dict = {"query": title, "include_adult": "false"}
    if year:
        params["first_air_date_year"] = year
    try:
        data = tmdb_get("/search/tv", params)
    except Exception:
        return None

    results = data.get("results", [])
    if not results:
        # Retry without year constraint
        if year:
            return find_tmdb_show(title, None)
        return None

    # Score candidates
    scored = []
    for r in results[:10]:
        name = r.get("name", "")
        orig = r.get("original_name", "")
        score = max(score_title_match(title, name), score_title_match(title, orig))
        pop = r.get("popularity", 0)
        scored.append((score, pop, r))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best_score, _, best = scored[0]

    if best_score < 0.3:
        return None

    match_method = "tmdb_scored_search"
    match_notes  = f"query={title} score={best.get('popularity', 0):.1f}"
    confidence   = "high" if best_score >= 0.8 else "medium" if best_score >= 0.5 else "low"

    return {
        "tmdb_id":       best["id"],
        "tmdb_name":     best.get("name", ""),
        "first_air_date": best.get("first_air_date", ""),
        "backdrop_path": best.get("backdrop_path") or "",
        "match_confidence": confidence,
        "match_method":  match_method,
        "match_notes":   match_notes,
    }


def get_imdb_id(tmdb_id: int) -> str | None:
    try:
        data = tmdb_get(f"/tv/{tmdb_id}/external_ids")
        return data.get("imdb_id") or None
    except Exception:
        return None


# ── Scraper ───────────────────────────────────────────────────────────────────

async def scrape_fundex(page) -> list[dict]:
    """Navigate FUNdex chart page and extract drama rankings."""
    print(f"  → {FUNDEX_URL}")
    await page.goto(FUNDEX_URL, wait_until="networkidle", timeout=90_000)

    # FUNdex is a Korean SPA — wait for chart rows to appear
    try:
        await page.wait_for_selector("table tbody tr, .rank-list li, .chart-item", timeout=20_000)
    except Exception:
        pass  # Try extracting anyway

    # Dump full page text for fallback
    content = await page.content()

    # Strategy 1: look for JSON data embedded in page
    json_match = re.search(r"var\s+chartData\s*=\s*(\[.*?\]);", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except Exception:
            pass

    # Strategy 2: parse table rows via DOM
    rows = await page.query_selector_all("table tbody tr")
    entries = []
    if rows:
        for row in rows[:MAX_ENTRIES]:
            cells = await row.query_selector_all("td")
            texts = [await c.inner_text() for c in cells]
            if len(texts) < 2:
                continue
            rank_text  = texts[0].strip()
            title_text = texts[1].strip() if len(texts) > 1 else ""
            score_text = texts[2].strip() if len(texts) > 2 else ""

            # Try to parse rank
            try:
                rank = int(re.sub(r"\D", "", rank_text) or "0")
            except ValueError:
                rank = len(entries) + 1

            # Link / pjseq
            link_el = await row.query_selector("a[href*=pjseq]")
            href    = await link_el.get_attribute("href") if link_el else ""
            pjseq_m = re.search(r"pjseq=(\d+)", href)
            source_url = (
                f"https://www.fundex.co.kr/fundex/funprogram.do?pjseq={pjseq_m.group(1)}"
                if pjseq_m else ""
            )

            # Poster
            img_el = await row.query_selector("img")
            poster = await img_el.get_attribute("src") if img_el else ""
            if poster and not poster.startswith("http"):
                poster = "https://www.fundex.co.kr" + poster

            entries.append({
                "rank":         rank or len(entries) + 1,
                "title":        title_text,
                "fundex_score": score_text,
                "source_url":   source_url,
                "poster":       poster,
            })
        if entries:
            return entries

    # Strategy 3: list items
    items = await page.query_selector_all(".rank-list li, .chart-item, .program-item")
    for i, item in enumerate(items[:MAX_ENTRIES], 1):
        text    = (await item.inner_text()).strip()
        lines   = [l.strip() for l in text.split("\n") if l.strip()]
        title   = lines[0] if lines else ""
        score   = next((l for l in lines if "%" in l), "")
        link_el = await item.query_selector("a[href*=pjseq]")
        href    = await link_el.get_attribute("href") if link_el else ""
        pjseq_m = re.search(r"pjseq=(\d+)", href)
        source_url = (
            f"https://www.fundex.co.kr/fundex/funprogram.do?pjseq={pjseq_m.group(1)}"
            if pjseq_m else ""
        )
        img_el = await item.query_selector("img")
        poster = await img_el.get_attribute("src") if img_el else ""
        if poster and not poster.startswith("http"):
            poster = "https://www.fundex.co.kr" + poster
        entries.append({
            "rank": i, "title": title, "fundex_score": score,
            "source_url": source_url, "poster": poster,
        })

    return entries


async def get_program_details(page, source_url: str) -> dict:
    """Visit individual program page to get Korean title, genre, year, poster."""
    if not source_url:
        return {}
    try:
        await page.goto(source_url, wait_until="networkidle", timeout=30_000)
        text = await page.inner_text("body")

        # Korean title
        ko_match = re.search(r"[가-힣][가-힣\s,·]+", text)
        korean_title = ko_match.group(0).strip() if ko_match else ""

        # Poster image
        img_el  = await page.query_selector("img.pj-img, .program-img img, .detail-img img")
        poster  = await img_el.get_attribute("src") if img_el else ""
        if poster and not poster.startswith("http"):
            poster = "https://www.fundex.co.kr" + poster

        # Genre
        genre_m = re.search(r"(?:장르|Genre)[^\n:：]*[：:]\s*([^\n]+)", text)
        genre   = genre_m.group(1).strip() if genre_m else ""

        # Year / broadcast date
        year_m  = re.search(r"(20\d{2})", text)
        year    = year_m.group(1) if year_m else ""

        return {"korean_title": korean_title, "poster_detail": poster,
                "genre": genre, "year": year}
    except Exception:
        return {}


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    out_path = Path(__file__).resolve().parent.parent / "kdrama_charts.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
        )
        page = await ctx.new_page()

        print("Scraping FUNdex weekly chart …")
        raw_entries = await scrape_fundex(page)
        print(f"  ✓ {len(raw_entries)} raw entries")

        kdramas = []
        for entry in raw_entries[:MAX_ENTRIES]:
            title      = entry.get("title", "").strip()
            rank       = entry.get("rank", len(kdramas) + 1)
            score      = entry.get("fundex_score", "")
            source_url = entry.get("source_url", "")
            poster     = entry.get("poster", "")

            print(f"  [{rank}] {title}")

            # Get details from program page
            details = await get_program_details(page, source_url)
            korean_title = details.get("korean_title", "")
            genre        = details.get("genre", "")
            year         = details.get("year", "")
            if details.get("poster_detail"):
                poster = details["poster_detail"]

            # English title fallback
            english_title = title

            # TMDB match
            tmdb_info = find_tmdb_show(english_title, year or None)
            time.sleep(0.25)  # rate-limit TMDB

            imdb_id    = None
            tmdb_id    = None
            tmdb_name  = ""
            first_air  = ""
            confidence = ""
            method     = ""
            notes      = ""

            backdrop_path = ""
            if tmdb_info:
                tmdb_id       = tmdb_info["tmdb_id"]
                tmdb_name     = tmdb_info["tmdb_name"]
                first_air     = tmdb_info["first_air_date"]
                backdrop_path = tmdb_info.get("backdrop_path", "")
                confidence    = tmdb_info["match_confidence"]
                method        = tmdb_info["match_method"]
                notes         = tmdb_info["match_notes"]
                imdb_id       = get_imdb_id(tmdb_id)
                time.sleep(0.25)

            item: dict = {
                "rank":          rank,
                "title":         english_title,
                "english_title": english_title,
                "korean_title":  korean_title,
                "year":          year,
                "genre":         genre,
                "fundex_score":  score,
                "source":        "FUNdex",
                "source_url":    source_url,
                "poster":        poster,
            }
            if imdb_id:
                item["imdb_id"] = imdb_id
            if tmdb_id:
                item["tmdb_id"]   = tmdb_id
                item["tmdb_name"] = tmdb_name
            if backdrop_path:
                item["backdropPath"] = backdrop_path
            if korean_title:
                item["original_title_ko"] = korean_title
            if first_air:
                item["first_air_date"] = first_air
            if confidence:
                item["match_confidence"] = confidence
                item["match_method"]     = method
                item["match_notes"]      = notes

            kdramas.append(item)

        await browser.close()

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source":  "FUNdex",
        "mode":    CHART_MODE,
        "count":   len(kdramas),
        "kdramas": kdramas,
    }
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {len(kdramas)} kdramas → {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
