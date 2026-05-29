# abcau-radio_playlist

Parse [ABC Listen](https://www.abc.net.au/listen) episode tracklists into CSV — ready to import into [Soundiiz](https://soundiiz.com) or [TuneMyMusic](https://www.tunemymusic.com) and turn into a Spotify (or Apple Music, YouTube Music, etc.) playlist.

Built for **Short Fast Loud** (Double J / triple j), but works on any ABC Listen audio-episode page, since they all embed their tracklist the same way.

## How it works

Every ABC Listen episode page ships its full tracklist inside a `__NEXT_DATA__` JSON blob in the page source. This script reads that blob directly instead of scraping rendered HTML, so it's stable and doesn't break on layout tweaks. It uses the Python standard library only — no dependencies to install.

## Requirements

- Python 3.7+

No `pip install` needed.

## Install

Just grab the script:

```bash
curl -O https://raw.githubusercontent.com/mmrry/ABC-AU_radio_playlist_parse/main/abcau-radio_playlist.py
chmod +x abcau-radio_playlist.py
```

## Usage

```bash
# One episode (writes one CSV named by date + title):
python3 abcau-radio_playlist.py https://www.abc.net.au/listen/programs/short-fast-loud/short-fast-loud/106529050

# Several episodes at once:
python3 abcau-radio_playlist.py URL1 URL2 URL3

# Merge everything into a single CSV (adds Episode + Date columns):
python3 abcau-radio_playlist.py --combined short-fast-loud.csv URL1 URL2

# Flag tracks unlikely to match on Spotify (Unearthed / emerging artists):
python3 abcau-radio_playlist.py --flag-misses URL

# Drop those tracks entirely:
python3 abcau-radio_playlist.py --drop-misses URL

# Parse a saved page offline:
python3 abcau-radio_playlist.py episode.html

# Write output somewhere specific:
python3 abcau-radio_playlist.py --outdir playlists URL
```

### Options

| Flag | Effect |
|------|--------|
| `--combined FILE.csv` | Write all episodes into one CSV (with `Episode` and `Date` columns) instead of one file per episode. |
| `--outdir DIR` | Output directory (default: current directory). Created if missing. |
| `--flag-misses` | Add a `LikelyMiss` column marking tracks that may not match on streaming services. |
| `--drop-misses` | Omit those likely-miss tracks from the output. |

## Output

CSV with the columns Soundiiz and TuneMyMusic read directly:

```
Title,Artist,Album,Duration
FREE TO DIE,HEALTH,ADDENDUM,219
"Hot Pursuit, One and Nothing",XCOMM,Time To Burn,258
```

- `Duration` is in seconds.
- With `--flag-misses`, a `LikelyMiss` column is appended (`yes` / empty).
- Per-episode files are named like `2026-05-27_short-fast-loud-rats-demons-roses.csv`.
- Combined files prepend `Episode` and `Date` columns.

## Importing into a streaming service

**Soundiiz** (recommended — it shows a match-review step):
Playlists → Import → *From a file* → upload the CSV → review and confirm the matches → save to Spotify. Free accounts cap CSV imports at 200 tracks.

**TuneMyMusic** (simpler):
*Let's Start* → *Upload a file* → choose Spotify as the destination.

## The "likely miss" heuristic

ABC plays a lot of unsigned and emerging artists. The script flags a track as a likely miss when:

- the artist has a triple j Unearthed page (`unearthedUrl` is present in the data), or
- the artist name is a single character (e.g. **A**), which tends to mismatch.

This is a starting filter, not a guarantee — the review step in Soundiiz is still where you'll catch any stragglers.

## If it stops working

If ABC changes their page structure and no tracks are found, the script prints a warning and moves on. Open an issue with a sample page and the JSON path can be adjusted.

## License

MIT
