# Aircraft Market Finder

Facts-only record of aircraft advertised for sale, one page per aircraft type. Asking prices, not sales.

- profiles/<type>.json — what counts as the type, search words, factory engines
- data/<type>/<date>.json — one file per search run
- tools/build.py — builds index.html from the profiles and runs
- RUN_SPEC.md — how a run is done

Build: `python3 tools/build.py .`
