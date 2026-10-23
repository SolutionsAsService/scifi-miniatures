import trimesh, numpy as np
W="/home/openclaw/projects/scifi-miniatures/wayfarer-apc/build/upright/"
m = trimesh.util.concatenate([trimesh.load(W+n+".stl") for n in ("hull-front","hull-rear")])
xs = np.arange(35.0, 45.01, 0.25); ys = np.arange(-17.0, -6.99, 0.25)
O = np.array([(x,y,80.0) for x in xs for y in ys])
loc, idx, _ = m.ray.intersects_location(O, np.tile([0,0,-1.0],(len(O),1)), multiple_hits=True)
top = np.full(len(O), -np.inf); np.maximum.at(top, idx, loc[:,2])
low = O[top < 38.45]
print("n", len(O), "below plane", len(low), "above", int((top > 38.55).sum()), "min", top.min())
print("x values of low:", sorted(set(np.round(low[:,0],2)))[:40])
print("y values of low:", sorted(set(np.round(low[:,1],2)))[:40])
