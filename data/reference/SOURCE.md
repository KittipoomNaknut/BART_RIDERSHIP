# Reference data

Source: BART official GTFS feed, https://www.bart.gov/dev/schedules/google_transit.zip
(feed_version 72, valid 2026-01-12 to 2026-08-30, downloaded 2026-10-13).
The BART API (api.bart.gov) was blocked by a Cloudflare check, so the GTFS feed was used instead.

- `stations_geo.csv`: parent stations (location_type = 1) from `stops.txt`. stop_id equals the
  station code in the ridership data; all 50 codes matched and names agree with `src/bart/stations.py`.
- `bart_lines.csv`: one track shape per line colour from `shapes.txt` (Yellow 001C, Orange 003C,
  Green 005A, Red 007A, Blue 011A, Grey 019), every 4th point kept plus the last point. Used only
  as a background on maps.
