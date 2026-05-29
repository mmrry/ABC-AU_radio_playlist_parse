#!/usr/bin/env python3
"""
abcau-radio_playlist.py — Parse ABC Listen episode tracklists into CSV.

Built for Short Fast Loud (and any ABC Listen audioepisode page, which all
embed their tracklist in a __NEXT_DATA__ JSON blob).

Usage:
    # One or more episode URLs:
    python3 abcau-radio_playlist.py URL [URL ...]

    # Local saved HTML files work too:
    python3 abcau-radio_playlist.py page1.html page2.html

    # Combine everything into a single CSV instead of one-per-episode:
    python3 abcau-radio_playlist.py --combined all_episodes.csv URL URL

    # Mark likely Spotify misses (Unearthed/emerging artists) in a column:
    python3 abcau-radio_playlist.py --flag-misses URL

    # Drop those likely-miss tracks entirely:
    python3 abcau-radio_playlist.py --drop-misses URL

Output columns: Title, Artist, Album, Duration[, LikelyMiss]
This format imports directly into Soundiiz and TuneMyMusic.
"""

import argparse
import csv
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from urllib.request import Request, urlopen
except ImportError:  # pragma: no cover
    print("Python 3 required.", file=sys.stderr)
    sys.exit(1)

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)

UA = "Mozilla/5.0 (compatible; tracklist-exporter/1.0)"


def load_html(source: str) -> str:
    """Fetch a URL or read a local file."""
    if source.startswith(("http://", "https://")):
        req = Request(source, headers={"User-Agent": UA})
        with urlopen(req, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    return Path(source).read_text(encoding="utf-8", errors="replace")


def extract_next_data(page_html: str) -> dict:
    """Pull and parse the __NEXT_DATA__ JSON blob."""
    m = NEXT_DATA_RE.search(page_html)
    if not m:
        raise ValueError("No __NEXT_DATA__ block found — not an ABC Listen page?")
    return json.loads(m.group(1))


def dig(d: dict, *keys):
    """Safely walk nested dicts; return None if any key is missing."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def parse_episode(page_html: str) -> dict:
    """Return {'title', 'date', 'slug', 'tracks': [...]} for one episode."""
    data = extract_next_data(page_html)
    doc = dig(data, "props", "pageProps", "data", "documentProps") or {}

    title = html.unescape(doc.get("title") or "episode")
    # Published date for a tidy filename, if present.
    date = ""
    dateline = doc.get("datelinePrepared") or {}
    published = dateline.get("publishedDate")
    if published:
        try:
            date = datetime.fromisoformat(
                published.replace("Z", "+00:00")
            ).strftime("%Y-%m-%d")
        except ValueError:
            date = ""

    items = dig(doc, "tracklistPrepared", "items") or []
    tracks = []
    for it in items:
        artist = (it.get("artist") or "").strip()
        track_title = (it.get("title") or "").strip()
        if not artist and not track_title:
            continue
        # An 'unearthedUrl' marks emerging/Unearthed artists — the ones
        # most likely to be missing from or mismatched on Spotify.
        # Single-letter artist names ("A") also match poorly.
        likely_miss = bool(it.get("unearthedUrl")) or len(artist) <= 1
        tracks.append(
            {
                "Title": html.unescape(track_title),
                "Artist": html.unescape(artist),
                "Album": html.unescape((it.get("release") or "").strip()),
                "Duration": it.get("duration") or "",
                "LikelyMiss": "yes" if likely_miss else "",
            }
        )

    return {"title": title, "date": date, "tracks": tracks}


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "-", text).strip("-") or "episode"


def write_csv(path: Path, tracks: list, *, flag_misses: bool, drop_misses: bool):
    fields = ["Title", "Artist", "Album", "Duration"]
    if flag_misses:
        fields.append("LikelyMiss")
    rows = [t for t in tracks if not (drop_misses and t["LikelyMiss"])]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="ABC Listen tracklist -> CSV")
    ap.add_argument("sources", nargs="+", help="Episode URLs or local HTML files")
    ap.add_argument("--combined", metavar="FILE.csv",
                    help="Write all episodes into one CSV instead of per-episode")
    ap.add_argument("--outdir", default=".", help="Output directory (default: .)")
    ap.add_argument("--flag-misses", action="store_true",
                    help="Add a LikelyMiss column for Unearthed/emerging artists")
    ap.add_argument("--drop-misses", action="store_true",
                    help="Omit likely-miss tracks entirely")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    combined_tracks = []
    total_episodes = 0

    for src in args.sources:
        try:
            ep = parse_episode(load_html(src))
        except Exception as e:  # noqa: BLE001 — report and keep going
            print(f"  ! Failed on {src}: {e}", file=sys.stderr)
            continue

        if not ep["tracks"]:
            print(f"  ! No tracks found in {src}", file=sys.stderr)
            continue

        total_episodes += 1

        if args.combined:
            for t in ep["tracks"]:
                row = dict(t)
                row_with_ep = {"Episode": ep["title"], "Date": ep["date"], **row}
                combined_tracks.append(row_with_ep)
        else:
            name = f"{ep['date'] + '_' if ep['date'] else ''}{slugify(ep['title'])}.csv"
            path = outdir / name
            n = write_csv(path, ep["tracks"],
                          flag_misses=args.flag_misses,
                          drop_misses=args.drop_misses)
            print(f"  + {path}  ({n} tracks)")

    if args.combined:
        path = outdir / args.combined
        fields = ["Episode", "Date", "Title", "Artist", "Album", "Duration"]
        if args.flag_misses:
            fields.append("LikelyMiss")
        rows = [t for t in combined_tracks
                if not (args.drop_misses and t.get("LikelyMiss"))]
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"  + {path}  ({len(rows)} tracks across {total_episodes} episodes)")

    if total_episodes == 0:
        sys.exit("No episodes parsed.")


if __name__ == "__main__":
    main()
