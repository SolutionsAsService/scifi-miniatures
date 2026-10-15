
import sys, numpy as np, trimesh
sys.argv=['x']; sys.path.insert(0, '/home/openclaw/projects/scifi-miniatures/wayfarer-apc/source')
import options as O, build as B
m = O.commander()
mesh = m.to_mesh()
V = np.asarray(mesh.vert_properties)[:, :3].astype(np.float64); F = np.asarray(mesh.tri_verts)
w = trimesh.Trimesh(V.astype(np.float32).astype(np.float64), F, process=True)
e = w.edges_sorted
u, inv, cnt = np.unique(e, axis=0, return_inverse=True, return_counts=True)
bad = u[cnt != 2]
print("bad", len(bad), [ (np.round(w.vertices[a],4).tolist(), np.round(w.vertices[b],4).tolist(), int(c)) for (a,b),c in zip(bad, cnt[cnt!=2])])
print("tris", len(F), "comps", len(m.decompose()))
