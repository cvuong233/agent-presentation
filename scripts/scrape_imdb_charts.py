#!/usr/bin/env python3
"""
Scrapes IMDb Most Popular Movies and TV Shows charts.
Source: https://www.imdb.com/chart/moviemeter/ and /chart/tvmeter/
Output: imdb_charts.json (repo root)
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright


def format_votes(count: int) -> str:
    """Format vote count like IMDb: 20K, 1.2M, 3.2K, etc."""
    if not count:
        return ""
    if count >= 1_000_000:
        v = count / 1_000_000
        s = f"{v:.1f}M" if v % 1 else f"{int(v)}M"
    elif count >= 1000:
        v = count / 1000
        s = f"{v:.1f}K" if v % 1 else f"{int(v)}K"
    else:
        s = str(count)
    return s


def extract_entries(next_data: dict) -> list[dict]:
    """Extract chart title entries from IMDb __NEXT_DATA__ JSON."""
    # Path 1: standard chart page structure
    try:
        edges = (
            next_data["props"]["pageProps"]["pageData"]
            ["chartTitles"]["edges"]
        )
    except (KeyError, TypeError):
        edges = []

    # Path 2: alternate structure seen in some IMDb pages
    if not edges:
        try:
            edges = (
                next_data["props"]["pageProps"]["chartTitles"]["edges"]
            )
        except (KeyError, TypeError):
            edges = []

    if not edges:
        raise ValueError("Could not find chartTitles edges in __NEXT_DATA__")

    results = []
    for i, edge in enumerate(edges, 1):
        node = edge.get("currentRank") if "currentRank" in edge else {}
        # Some structures put data directly in edge.node
        if not node and "node" in edge:
            node = edge["node"]
        # If still empty, edge itself might be the node
        if not node:
            node = edge

        imdb_id = node.get("id", "")
        title = (node.get("titleText") or {}).get("text", "")

        # Poster
        poster = ""
        primary_image = node.get("primaryImage") or {}
        raw_url = primary_image.get("url", "")
        if raw_url:
            # Normalise to 500px width
            poster = re.sub(r"_V1_.*?\.jpg", "_V1_UX500_.jpg", raw_url)
            if "_V1_" not in poster:
                poster = raw_url

        # Rating & votes
        rating = ""
        votes = ""
        rs = node.get("ratingsSummary") or {}
        agg = rs.get("aggregateRating")
        if agg is not None:
            rating = str(round(float(agg), 1))
        vc = rs.get("voteCount")
        if vc:
            votes = format_votes(int(vc))

        results.append({
            "rank": i,
            "title": title,
            "imdb_id": imdb_id,
            "poster": poster,
            "rating": rating,
            "votes": votes,
        })

    return results


async def scrape_chart(page, url: str) -> list[dict]:
    print(f"  → {url}")
    await page.goto(url, wait_until="networkidle", timeout=90_000)

    # Try to grab __NEXT_DATA__ (Next.js)
    next_data_raw = await page.evaluate("""() => {
        const el = document.getElementById('__NEXT_DATA__');
        return el ? el.textContent : null;
    }""")

    if next_data_raw:
        next_data = json.loads(next_data_raw)
        entries = extract_entries(next_data)
        if entries:
            return entries

    # Fallback: intercept Apollo/GraphQL state
    apollo_raw = await page.evaluate("""() => {
        for (const key of Object.keys(window)) {
            if (key.startsWith('__APOLLO') || key.startsWith('__IMDb')) {
                try { return JSON.stringify(window[key]); } catch {}
            }
        }
        return null;
    }""")

    if apollo_raw:
        print("  (using Apollo state fallback)")
        # Basic extraction from stringified state
        ids = re.findall(r'"id"\s*:\s*"(tt\d+)"', apollo_raw)
        # Deduplicate preserving order
        seen = set()
        unique_ids = []
        for i in ids:
            if i not in seen:
                seen.add(i)
                unique_ids.append(i)
        if unique_ids:
            return [{"rank": r, "title": "", "imdb_id": i, "poster": "", "rating": "", "votes": ""}
                    for r, i in enumerate(unique_ids[:100], 1)]

    raise RuntimeError(f"Failed to extract chart data from {url}")


async def main():
    out_path = Path(__file__).resolve().parent.parent / "imdb_charts.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = await ctx.new_page()

        print("Scraping IMDb Most Popular Movies …")
        movies = await scrape_chart(page, "https://www.imdb.com/chart/moviemeter/")
        print(f"  ✓ {len(movies)} movies")

        print("Scraping IMDb Most Popular TV Shows …")
        tv = await scrape_chart(page, "https://www.imdb.com/chart/tvmeter/")
        print(f"  ✓ {len(tv)} TV shows")

        await browser.close()

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "movies": movies,
        "tv": tv,
    }
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
