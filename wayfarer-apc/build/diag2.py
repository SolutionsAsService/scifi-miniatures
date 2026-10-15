
import sys, numpy as np, trimesh
sys.path.insert(0, '/home/openclaw/projects/scifi-miniatures/wayfarer-apc/source')
sys.argv=['x']
import options as O
sys.path.insert(0, str(O.PKG.parent / "tools"))
import exosuit as X
from sdfkit import v3
pose = X.Pose(pelvis=(0, 0, 15.8), lean=4.0, twist=8.0, fists=((-6.6, -2.4, 19.6), (6.4, -8.4, 25.2)), head_yaw=12.0)
def hands(g, P):
    X.fist(g, P.fist[0], v3(0, 0, -1), P.fist[0] - P.elbow[0])
    X.open_hand(g, P.fist[1], P.fist[1] - P.elbow[1], v3(0, 0, -1), 1)
body = X.figure(pose, h=0.1, extras=[hands], bbox=((-10.5, -15.0, 16.0), (10.5, 8.0, pose.cut_z + 3.2))).mesh("b")
helm = X.helm("warden").mesh("h"); pack = X.backpack("power").mesh("p")
def bad(m, tag):
    mesh = m.to_mesh()
    w = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3].astype(np.float32).astype(np.float64), np.asarray(mesh.tri_verts), process=True)
    u, cnt = np.unique(w.edges_sorted, axis=0, return_counts=True)
    b = u[cnt != 2]
    print(tag, "bad", len(b), [np.round(w.vertices[a], 3).tolist() for a, _ in b][:4], "comps", len(m.decompose()), flush=True)
mb = O.tm_to_m(body); bad(mb, "body")
mh = O.mx(O.tm_to_m(helm), X.helm_placement(pose)); bad(mh, "helm")
mp = O.mx(O.tm_to_m(pack), X.pack_placement(pose)); bad(mp, "pack")
bad(mb + mh, "body+helm"); bad(mb + mp, "body+pack")
bad((mb + mh + mp).trim_by_plane((0, 0, 1), 16.6), "all trimmed")
print("neck_cut", list(map(float, pose.neck_cut)), "cut_z", pose.cut_z)
