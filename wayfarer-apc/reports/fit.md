# Wayfarer APC: does a 30 mm Vigilant fit the openings?

Two independent measurements. (1) `miniature_floor_clearance_check` (unified-CAD-MCP) with the door and hatch openings from the spec: door 26.0 x 23.7 mm, hatch 24.5 x 16.8 mm, bay clear height 24.2 mm. (2) The envelope test in `reports/build.json` (build.py `fit_report`): the measured plan envelope of the assembled Vigilant figures (every Vigil figure package with a viewer mesh, base excluded) slid through the door polygon and the hatch rectangle with 0.5 mm clearance a side; crouched = 65 % of height (Dreyfuss).

## Vigilant on a 32 mm base (rifleman / heavy)

| Check | Value | Limit | Pass |
|---|---|---|---|
| storey clear height vs figure on base | 24.2 | 42.25 | NO |
| door width vs base | 26.0 | 22.4 | yes |
| door height vs figure on base | 23.7 | 36.05 | NO |
| floor hatch fits a fingertip | 16.8 | 10.0 | yes |

all_checks_pass: **False**

## Vigilant on a 25 mm base

| Check | Value | Limit | Pass |
|---|---|---|---|
| storey clear height vs figure on base | 24.2 | 42.25 | NO |
| door width vs base | 26.0 | 17.5 | yes |
| door height vs figure on base | 23.7 | 36.05 | NO |
| floor hatch fits a fingertip | 16.8 | 10.0 | yes |

all_checks_pass: **False**

## Envelope test (measured figures through the openings)

| Figure | Opening | Needs (mm) | Fits |
|---|---|---|---|
| vigil-rifleman | stern door (crouched to 65 % of height, Dreyfuss) | [21.54, 'door 23.7'] | yes |
| vigil-rifleman | stern door (lying, lengthwise) | [24.02, 14.74] | yes |
| vigil-rifleman | stern door (standing) | [32.37, 'door 23.7'] | NO |
| vigil-rifleman | roof hatch (upper body standing in the hatch) | [14.82, 22.43] | yes |
| vigil-rifleman | roof hatch (whole figure passing through, lengthwise) | [14.74, 24.02] | yes |
| vigil-rifleman-mk2 | stern door (crouched to 65 % of height, Dreyfuss) | [21.55, 'door 23.7'] | yes |
| vigil-rifleman-mk2 | stern door (lying, lengthwise) | [24.47, 14.79] | yes |
| vigil-rifleman-mk2 | stern door (standing) | [32.38, 'door 23.7'] | NO |
| vigil-rifleman-mk2 | roof hatch (upper body standing in the hatch) | [14.78, 22.94] | yes |
| vigil-rifleman-mk2 | roof hatch (whole figure passing through, lengthwise) | [14.79, 24.47] | yes |
| vigil-marksman | stern door (crouched to 65 % of height, Dreyfuss) | [17.74, 'door 23.7'] | yes |
| vigil-marksman | stern door (lying, lengthwise) | [32.04, 14.9] | NO |
| vigil-marksman | stern door (standing) | [26.53, 'door 23.7'] | NO |
| vigil-marksman | roof hatch (upper body standing in the hatch) | [14.83, 26.08] | NO |
| vigil-marksman | roof hatch (whole figure passing through, lengthwise) | [14.9, 32.04] | NO |
| vigil-heavy | stern door (crouched to 65 % of height, Dreyfuss) | [21.24, 'door 23.7'] | yes |
| vigil-heavy | stern door (lying, lengthwise) | [22.79, 15.72] | yes |
| vigil-heavy | stern door (standing) | [31.91, 'door 23.7'] | NO |
| vigil-heavy | roof hatch (upper body standing in the hatch) | [14.35, 21.77] | yes |
| vigil-heavy | roof hatch (whole figure passing through, lengthwise) | [15.72, 22.79] | yes |
| vigil-warden | stern door (crouched to 65 % of height, Dreyfuss) | [23.67, 'door 23.7'] | yes |
| vigil-warden | stern door (lying, lengthwise) | [21.86, 14.08] | yes |
| vigil-warden | stern door (standing) | [35.65, 'door 23.7'] | NO |
| vigil-warden | roof hatch (upper body standing in the hatch) | [14.08, 21.54] | yes |
| vigil-warden | roof hatch (whole figure passing through, lengthwise) | [14.08, 21.86] | yes |

Aisle between the benches 40 mm; bay clear height 24.2 mm; seat pitch 18.6 mm.

## Reading

At true 1:56 the Wayfarer's bay is 1.1-1.2 m clear high (the concept's 2.2 m hull with a V-hull floor), so a standing 1.8 m trooper does not fit the storey or door height: those checks fail by design and are an owner decision (DESIGN-LOG.md M5, 'true 1:56 kept'). The openings do pass the figure itself: the door width clears a 32 mm base (tool), a Vigilant passes the door lengthwise and passes a hatch, and the hatches take a Vigilant's upper body standing in them (open-hatch pose).
