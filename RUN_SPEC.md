# Aircraft Market Finder — Run Spec (any type)

Version 1 — 2026-10-28. Built from the Skywagon daily sweeps and the first Pacer run.

## What one run does
1. Read the type profile (profiles/<type>.json). If the type is new, write the profile first and get Rusty's OK on it before searching.
2. Search every source below for that type only. Two search words minimum per site.
3. Clean the data (rules below). One aircraft = one row.
4. Sort each listing: counted (complete airworthy) or shown-not-counted (with the reason).
5. Registry pull and damage screen on every tail or serial.
6. Write data/<type>/<YYYY-MM-DD>.json and a plain run log.
7. Build the page (tools/build.py), check it (test/check.py — broken copy first, must FAIL; real copy must PASS), then publish.

## New type profile
- id, name, groups (each group has its own count, median and average — e.g. Pacer vs Tri-Pacer).
- Models that count, close models that do not (e.g. Colt), factory engine per model and year from the TCDS, with the source.
- Site categories and search words, found on the first run and written into the profile.
- stale_days (default 60).

## Sources (browser pane on the Mac mini unless noted)
- Trade-A-Plane — read every related model tag; model tags are inconsistent. Same-origin fetch, 4 s between pages (it rate-limits).
- Controller — model page /listings/for-sale/<make>/<model>/aircraft plus keyword search. Cloud copy is stale; use the pane.
- Barnstormers — the type's categories plus cat_search.php with price__gte=10000. Split by data-adid.
- GlobalAir, GlobalPlaneSearch, aerogurus — aggregators; follow each to its primary ad. Aggregator prices lag.
- aircraftdealer.com, broker sites, type-club classifieds, AvPay, Plane Sales Australia, Planecheck (bot check).
- Craigslist — every area through www.craigslist.org/search/area/<city>?cat=sss&query=<a|b|c>; one site approval covers all.
- Facebook Marketplace — /marketplace/<city>/search?query=…&radius=805, two terms per city. Some cities fall back to 40 miles; say so.
- Facebook sale groups — /groups/<id>/search?q=<word>&filters=<posts filter>. Open each card as /commerce/listing/<id>/ and read Sold / Out of Stock / Pending on the listing itself.

## Cleaning rules
- Identity: serial first, then tail, then ad link. One aircraft on five sites = one row.
- Asks only. Never average conflicting figures; keep the direct source's figure and note the others.
- "Call for price" is a withdrawn figure, not a cut. Badges like NEW PRICE over an unchanged figure are ignored.
- Foreign prices: keep the native figure, convert to USD on the run date, note the rate.
- Missing fields show "?". If the ad names no engine, use the factory engine and mark it assumed.
- No seller or owner names anywhere.
- Gone ad = "gone", never "sold", unless the ad says sold.

## Counted vs not counted (Rusty, 2026-10-28)
- Counted: has a price and is complete and airworthy.
- Any ad that says "project" is not counted (unairworthy). Same for salvage, parts, shares, trade-only, pending, no price.
- Experimental aircraft of the type count, marked Experimental.
- Foreign listings count, marked with their flag.

## Damage screen
- FAA registry: GitHub mirror simonw/scrape-faa-releasable-aircraft, MASTER-1..9. Find a missing tail from the serial.
- NTSB: CAROL Aviation Search at my.ntsb.gov by registration. Run a known-accident tail first as a control.
- Windsock is not enough on its own — its record starts around 2000 and it missed a 1975 accident.
- Pre-1982 records are often missing. Say so.
- No tail: read the tail off the photos; if not legible, say "not screened".

## Publish
- Site folder: index.html (built), profiles/, data/, tools/. test/ is never published.
- GitHub repository → Cloudflare Pages, same route as skywagon-intel.
