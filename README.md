# abcau-radio_playlist.py
abcau-radio_playlist.py — Parse ABC Listen episode tracklists into CSV.
Built for any ABC Listen audioepisode page, which all embed their tracklist in a __NEXT_DATA__ JSON blob.

Output columns: Title, Artist, Album, Duration.
This format imports directly into TuneMyMusic to any audio streaming service.

## Usage:
```
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
```
