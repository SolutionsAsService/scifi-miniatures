# Vigil helm library 0.3 (VH4): printability and detail report

Measured with the unified-CAD-MCP `miniature_printability_check` (MSLA resin, Formlabs limits) and `miniature_detail_resolution_check` (engraved-detail limit 0.4 mm, marginal 0.3-0.4) on the final print meshes, upright as modelled. 16 helms in one in-process batch of the same functions the MCP serves; VH4-16 and VH4-18 re-measured through MCP calls after their last fix. The print files were confirmed identical (volume and triangle count) to the measured meshes.

**Result: PASS on all 18** (closed, manifold, one shell, no enclosed voids, supported wall under 0.4 mm over at most 0.22 mm2 against a 0.5 mm2 limit, 0 recesses that fill in).

| Helm | Supported thin area mm2 (<= 0.5) | Min wall mm (single ray) | Resolving recesses | Edge loops | Fills | Marginal (0.3-0.4) | Measured by |
|---|---|---|---|---|---|---|---|
| VH4-01 Lineguard | 0.0312 | 0.346 | 22 | 19 | 0 | 6 | batch (same functions, in-process) |
| VH4-02 Marshal | 0.0367 | 0.349 | 23 | 21 | 0 | 8 | batch (same functions, in-process) |
| VH4-03 Plummet | 0.0 | 0.466 | 18 | 19 | 0 | 5 | batch (same functions, in-process) |
| VH4-04 Sightline | 0.0333 | 0.164 | 23 | 16 | 0 | 4 | batch (same functions, in-process) |
| VH4-05 Ironclad | 0.0899 | 0.078 | 21 | 22 | 0 | 3 | batch (same functions, in-process) |
| VH4-06 Breacher | 0.083 | 0.118 | 16 | 18 | 0 | 3 | batch (same functions, in-process) |
| VH4-07 Sentinel | 0.0417 | 0.253 | 16 | 22 | 0 | 1 | batch (same functions, in-process) |
| VH4-08 Raptor | 0.0357 | 0.197 | 17 | 24 | 0 | 3 | batch (same functions, in-process) |
| VH4-09 Diver | 0.0704 | 0.315 | 8 | 6 | 0 | 2 | batch (same functions, in-process) |
| VH4-10 Stillwater | 0.0088 | 0.4 | 15 | 16 | 0 | 3 | batch (same functions, in-process) |
| VH4-11 Hunter | 0.2174 | 0.313 | 11 | 13 | 0 | 2 | batch (same functions, in-process) |
| VH4-12 Specter | 0.1722 | 0.336 | 10 | 6 | 0 | 1 | batch (same functions, in-process) |
| VH4-13 Herald | 0.0324 | 0.267 | 24 | 16 | 0 | 4 | batch (same functions, in-process) |
| VH4-14 Longsight | 0.0208 | 0.135 | 13 | 15 | 0 | 5 | batch (same functions, in-process) |
| VH4-15 Deckhand | 0.0809 | 0.058 | 12 | 25 | 0 | 2 | batch (same functions, in-process) |
| VH4-16 Mender | 0.1893 | 0.004 | 18 | 32 | 0 | 6 | MCP call |
| VH4-17 Wright | 0.0907 | 0.257 | 26 | 17 | 0 | 8 | batch (same functions, in-process) |
| VH4-18 Grimward | 0.1198 | 0.089 | 25 | 16 | 0 | 6 | MCP call |

Min wall is the thinnest single ray, usually an inside corner; the pass criterion is the area. Advisory on every helm: 'minimum wall (unsupported)' (thin spots braced on fewer than two sides; fine on supports). Marginal recesses hold on a tuned 8K MSLA printer but not at the conservative limit: print a detail coupon.

Not yet run: `miniature_support_plan` per helm (print pose) and `miniature_gap_check`; source/check.py runs both (about 90 minutes for 18 helms) and rewrites this report.
