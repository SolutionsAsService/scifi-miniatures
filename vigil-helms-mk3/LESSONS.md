# VH3 lessons

1. Hand-fixing thin spots on boolean-heavy SDF sculpts does not converge: three dev checks (R1-R3) chased 30+ knife lips,
   slivers and seam folds and every round produced new ones (supported thin area stayed 1.7-8.6 mm2 vs the 0.5 mm2 limit).
2. A morphological filter on the voxel field does converge in one pass: tools/morph.py closing (r 0.26) then opening
   (r 0.25) guarantees every wall holds a 0.5 mm ball and every slot is >= 0.52 mm. Cost per helm: -0.4 to -2.8 mm3
   (~1-2 % volume), convex edges rounded to 0.25 mm - invisible at 30 mm. Measured min wall after: 0.49-0.55 mm.
3. Keep the original field where it is already safe (max/min with the filtered field) so untouched surfaces keep
   sub-voxel smoothness; then the 0.05 mm grid still marches to 160-185 k triangles (under the 300 k checker cap).
4. Check runs dominate wall time (~3 min support plan + ~2 min printability per 180 k-tri part). Cache every MCP result
   by STL sha (tools/cachedcheck.py) so OOM kills / restarts resume instead of re-checking.
5. Never background a capped job from an exec shell with & / nohup: the scope dies with the shell. Use
   tools/capped_run.sh (transient systemd user unit, MemoryMax=1500M, no swap) and poll the log.
