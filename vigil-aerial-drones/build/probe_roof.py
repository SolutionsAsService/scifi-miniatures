import trimesh, numpy as np
W="/home/openclaw/projects/scifi-miniatures/wayfarer-apc/build/upright/"
m = trimesh.util.concatenate([trimesh.load(W+n+".stl") for n in ("hull-front","hull-rear")])
xs = np.arange(28, 47.1, 1.0); ys = np.arange(-19, -1.9, 1.0)
O = np.array([(x,y,80.0) for x in xs for y in ys])
loc, idx, _ = m.ray.intersects_location(O, np.tile([0,0,-1.0],(len(O),1)), multiple_hits=False)
H = np.full(len(O), np.nan); H[idx] = loc[:,2]
H = H.reshape(len(xs), len(ys))
print("y:", ys.tolist())
for i,x in enumerate(xs):
    print(int(x), " ".join("%5.2f" % v for v in H[i]))
