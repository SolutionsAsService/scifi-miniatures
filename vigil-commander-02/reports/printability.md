# Vigilant Commander 0.2 (power armour): quick printability screen

One unified-CAD-MCP `miniature_printability_check` per part, upright as modelled (MSLA resin, Formlabs limits). A quick screen, not a full certification: no support plans, gap or detail checks.

**Result: NOT YET PASSING**

| Part | Result | Volume mm3 | Min wall mm (single ray) | Supported thin area mm2 (<= 0.5) | Fails |
|---|---|---|---|---|---|
| backpack | PASS | 209.71 | 0.352 | 0.0021 | none |
| base | FAIL | 2835.21 | 0.001 | 5.7052 | minimum wall (supported) = 5.7052, suction cups = 164.254 |
| figure | FAIL | 2110.81 | 0.008 | 0.6978 | minimum wall (supported) = 0.6978 |
| helm | PASS | 121.51 | 0.349 | 0.0367 | none |

Assembly interference (sdfkit, exact): [{'a': 'Vigilant commander 0.2', 'b': '32 mm base', 'overlap_mm3': 0.041}]
