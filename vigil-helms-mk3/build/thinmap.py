
import json, sys
import numpy as np
from pathlib import Path
from unified_cad_mcp.flotation import read_stl
from unified_cad_mcp.miniature import rotate
sys.path.insert(0, '../tools')
pkg = Path('.')
rep = json.loads((pkg/'reports/printability.json').read_text())
HC, HS = np.array([0,0,2.8]), 1.12
for name, e in rep['parts'].items():
    tris = read_stl(pkg/'build/upright'/f'{name}.stl')
    rot = e['rotate_deg']
    rt = rotate(tris, *rot)
    A = np.array(tris, float).reshape(-1,3); B = np.array(rt, float).reshape(-1,3)
    lo, hi = B.min(0), B.max(0)
    d = np.array([-(lo[0]+hi[0])/2, -(lo[1]+hi[1])/2, -lo[2]])
    B = B + d
    th = e['printability']['thickness']
    spots = sorted(th['thin_spots'], key=lambda s: -s['area_mm2'])
    out = []
    tot = 0
    for s in spots:
        if s['min_mm'] >= 0.4: continue
        i = np.argmin(np.linalg.norm(B - np.array(s['at_mm']), axis=1))
        p = A[i]; q = (p - HC)/HS
        out.append((round(s['area_mm2'],2), s['min_mm'], np.round(p,2).tolist(), np.round(q,2).tolist()))
        tot += s['area_mm2']
    print(name, 'below0.4 total', round(tot,2), 'n', len(out))
    for o in out[:9]: print('   ', o)
