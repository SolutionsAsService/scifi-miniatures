
import json, sys
import numpy as np, trimesh
from pathlib import Path
sys.path.insert(0, '../tools'); sys.path.insert(0, 'source')
import sheet
from render import _hex
rep = json.loads(Path('reports/printability.json').read_text())
spots = json.loads(Path('build/thinspots.json').read_text())
for name in rep['parts']:
    m = trimesh.load(f'build/upright/{name}.stl', process=False)
    cols = sheet.colours(m, None)
    meshes, cl = [m], [cols]
    for area, mn, p in spots[name]:
        s = trimesh.creation.icosphere(1, radius=0.12 + 0.25*min(area,1.0)); s.apply_translation(p)
        meshes.append(s); cl.append(np.tile(_hex('#e0302a'), (len(s.faces),1)))
    M = trimesh.util.concatenate(meshes); C = np.vstack(cl)
    from PIL import Image
    cells = [sheet.draw(M, C, az, el, 380, label=lab) for az, el, lab in ((-35,12,'3/4'),(0,3,'front'),(90,4,'right'),(-90,4,'left'),(180,10,'back'))]
    im = Image.new('RGB', (380*5, 380), (236,237,240))
    for i,c in enumerate(cells): im.paste(c, (380*i, 0))
    im.save(f'build/thin-{name}.png')
