"""L2 (In1.Cu) GND plane connectivity on the board model (W2 CTRL-4): the components of the plane that the other-net copper
on L2 leaves (zone GND-L2: clearance 0.3 mm, minimum width 0.25 mm, as board_gen fills it), each with the GND vias and THT
GND pads it holds. A frozen route whose L2 signal links split the plane into several components with GND vias fails the
incremental check (route run 43270651486: 495 mm of L2 links left two GND islands that KiCad reported as unconnected).
Conservative: the GND pours on L1/L3/L4 may join such components again. Needs numpy.

  python build/kicad/boards/CTRL/freeze/plane.py <board.kicad_pcb>
"""
import sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import model as M
import router as R

def plane_components(m, g=0.05, clr=0.3, min_w=0.25):
    grid = R.Grid(m, (100.0, 100.0, 150.0, 244.0), g)
    blk = np.zeros(grid.X.shape, dtype=bool)
    for it in m.items:
        if not it.alive or 'In1.Cu' not in it.layers or it.net == 'GND':
            continue
        if it.kind not in ('track', 'via', 'pad', 'npth'):
            continue
        infl = clr
        w = grid.win(it.bbox, infl + 0.1)
        if w is None:
            continue
        blk[w] |= R.shape_dist(grid.X[w], grid.Y[w], it.shape) < infl
    blk |= ~grid.inside
    blk |= grid.dedge < clr
    free = ~blk
    # erosion by min_w/2 (square approximation by 4-neighbour shifts at the grid step)
    k = int(round(min_w / 2 / g))
    core = free.copy()
    for _ in range(k):
        c = core.copy()
        c[1:, :] &= core[:-1, :]; c[:-1, :] &= core[1:, :]; c[:, 1:] &= core[:, :-1]; c[:, :-1] &= core[:, 1:]
        core = c
    # label components (BFS, 4-neighbour)
    lab = np.zeros(core.shape, dtype=np.int32)
    n = 0
    nx, ny = core.shape
    for i0 in range(nx):
        for j0 in range(ny):
            if core[i0, j0] and not lab[i0, j0]:
                n += 1
                stack = [(i0, j0)]; lab[i0, j0] = n
                while stack:
                    i, j = stack.pop()
                    for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                        if 0 <= a < nx and 0 <= b < ny and core[a, b] and not lab[a, b]:
                            lab[a, b] = n; stack.append((a, b))
    comp = collections.defaultdict(list)
    for it in m.items:
        if it.alive and it.net == 'GND' and (it.kind == 'via' or (it.kind == 'pad' and 'In1.Cu' in it.layers)):
            i = int(round((it.at[0] - grid.x0) / g)); j = int(round((it.at[1] - grid.y0) / g))
            r = int((it.size / 2 if it.kind == 'via' else 0.4) / g) + k + 1
            sub = lab[max(0, i - r):i + r + 1, max(0, j - r):j + r + 1]
            ids = set(int(v) for v in np.unique(sub) if v)
            for c in ids:
                comp[c].append(it)
    return comp

def split_count(m):
    """Number of plane components holding GND vias or THT GND pads (1 = one plane)."""
    return len(plane_components(m))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    m = M.Model(sys.argv[1])
    comp = plane_components(m)
    sizes = sorted(((len(v), c) for c, v in comp.items()), reverse=True)
    print('plane components with GND vias/pads:', len(comp), [s for s, _ in sizes[:10]])
    for s, c in sizes[1:10]:
        its = comp[c]
        print('  ', s, [(it.kind, it.ref or '', round(it.at[0] - 100, 2), round(244 - it.at[1], 2)) for it in its[:4]])
