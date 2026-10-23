import trimesh, numpy as np
W="/home/openclaw/projects/scifi-miniatures/wayfarer-apc/build/upright/"
m = trimesh.util.concatenate([trimesh.load(W+n+".stl") for n in ("hull-front","hull-rear")])
xs = np.arange(14.0, 47.01, 0.25); ys = np.arange(-19.0, 2.01, 0.25)
O = np.array([(x,y,80.0) for x in xs for y in ys])
loc, idx, _ = m.ray.intersects_location(O, np.tile([0,0,-1.0],(len(O),1)), multiple_hits=True)
top = np.full(len(O), -np.inf); np.maximum.at(top, idx, loc[:,2])
H = top.reshape(len(xs), len(ys))
flat = np.abs(H - 38.5) < 0.03
# best square pad (side a) fully flat
best = []
for a in (10.0, 9.0, 8.0):
    n = int(a/0.25)
    for i in range(len(xs)-n):
        for j in range(len(ys)-n):
            if flat[i:i+n+1, j:j+n+1].all():
                best.append((a, xs[i]+a/2, ys[j]+a/2))
    if best: break
print("found", len(best))
import collections
if best:
    a = best[0][0]
    c = np.array([(b[1], b[2]) for b in best])
    print("side", a, "x range", c[:,0].min(), c[:,0].max(), "y range", c[:,1].min(), c[:,1].max())
    # candidates nearest to (38, -11)
    d = np.hypot(c[:,0]-38, c[:,1]+11); k = np.argsort(d)[:8]
    print("nearest", c[k].tolist())
# summarize non-flat rows by y
nf = ~flat
print("nonflat x cols with y<-2:", sorted(set(np.round(xs[np.where(nf[:, ys< -2].any(axis=1))[0]],2)))[:80])
