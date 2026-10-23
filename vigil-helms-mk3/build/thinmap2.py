
import json, sys
import numpy as np
from pathlib import Path
from unified_cad_mcp.flotation import read_stl
from unified_cad_mcp.miniature import rotate
rep = json.loads(Path('reports/printability.json').read_text())
out = {}
for name, e in rep['parts'].items():
    tris = read_stl(Path('build/upright')/f'{name}.stl')
    A = np.array(tris, float).reshape(-1,3); B = np.array(rotate(tris, *e['rotate_deg']), float).reshape(-1,3)
    lo, hi = B.min(0), B.max(0); B = B + np.array([-(lo[0]+hi[0])/2, -(lo[1]+hi[1])/2, -lo[2]])
    out[name] = []
    for s in e['printability']['thickness']['thin_spots']:
        if s['min_mm'] < 0.4:
            i = np.argmin(np.linalg.norm(B - np.array(s['at_mm']), axis=1))
            out[name].append((s['area_mm2'], s['min_mm'], A[i].tolist()))
    print(name, len(out[name]), 'spots, total', round(sum(a for a,_,_ in out[name]),2), 'of', e['printability']['thickness']['area_below_supported_mm2'])
Path('build/thinspots.json').write_text(json.dumps(out))
