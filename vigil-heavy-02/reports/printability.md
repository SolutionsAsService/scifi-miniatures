# Vigilant Heavy Gunner 0.2 (power armour): quick printability screen

One unified-CAD-MCP `miniature_printability_check` per part, upright as modelled (MSLA resin, Formlabs limits). A quick screen, not a full certification: no support plans, gap or detail checks.

**Result: NOT YET PASSING**

| Part | Result | Volume mm3 | Min wall mm (single ray) | Supported thin area mm2 (<= 0.5) | Fails |
|---|---|---|---|---|---|
| backpack | PASS | 299.39 | 0.423 | 0 | none |
| base | FAIL | 2839.18 | 0.001 | 4.8865 | minimum wall (supported) = 4.8865, suction cups = 175.939 |
| figure | FAIL | 2363.9 | 0.03 | 1.7593 | minimum wall (supported) = 1.7593 |
| helm | PASS | 132.75 | 0.078 | 0.0899 | none |

Assembly interference (sdfkit, exact): [{'a': 'Vigilant heavy gunner 0.2', 'b': '32 mm base', 'overlap_mm3': 0.044}]
