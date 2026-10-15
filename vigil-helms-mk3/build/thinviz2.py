
import json, sys
import numpy as np, trimesh
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../tools'); sys.path.insert(0, 'source')
import sheet
from render import _hex
dc = json.loads(Path('build/dev/devcheck.json').read_text())
names = sys.argv[1:] or list(dc)
for name in names:
    m = trimesh.load(f'build/dev/{name}.stl', process=False)
    meshes, cl = [m], [sheet.colours(m, None)]
    for area, mn, p, q in dc[name]['spots']:
        s = trimesh.creation.icosphere(1, radius=0.08 + 0.2*min(area,1.0)); s.apply_translation(p)
        meshes.append(s); cl.append(np.tile(_hex('#e0302a'), (len(s.faces),1)))
    M = trimesh.util.concatenate(meshes); C = np.vstack(cl)
    views = ((-35,12,'3/4'),(0,3,'front'),(90,4,'right'),(-90,4,'left'),(180,10,'back'),(0,-60,'below'))
    cells = [sheet.draw(M, C, az, el, 400, label=lab, rad=4.6, center=np.array([0,0.3,3.2])) for az, el, lab in views]
    im = Image.new('RGB', (400*6, 400), (236,237,240))
    for i,c in enumerate(cells): im.paste(c, (400*i, 0))
    im.save(f'build/dev/thin2-{name}.png')
