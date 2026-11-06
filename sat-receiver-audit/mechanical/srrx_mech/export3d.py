"""Portable STEP and STL output: the same bytes on every platform with the pinned CAD stack.

OCCT writes the same STEP entities and the same triangulation on Linux and
Windows, but the last bits of the numbers differ with the C library (sin/cos
noise such as 2.22E-16 in place of 0). Both writers here therefore round every
coordinate before it is written:

- STEP: every real number in the DATA section is rounded to 1e-9 mm, which is
  two orders below the OCCT confusion tolerance (1e-7), so the geometry and the
  topology are unchanged; the FILE_NAME time stamp is fixed.
- STL: binary STL written here from the BRep triangulation (absolute chordal
  deflection, single-threaded mesher), vertices rounded to 1e-4 mm, normals
  computed from the rounded triangle.
"""
import math
import re
import struct

STEP_STAMP = "2026-10-24T00:00:00"
_REAL = re.compile(r"'(?:[^']|'')*'|(?<![\w.#])-?\d+\.\d*(?:E[+-]?\d+)?")


def _real(tok, nd=9):
    v = float(tok)
    if abs(v) >= 1e7:      # parameter-space infinities and the like: written as OCCT wrote them
        return tok
    v = round(v, nd)
    if v == 0.0:
        return "0."
    return f"{v:.{nd}f}".rstrip("0")   # keeps the trailing '.' that a STEP real needs


def normalise_step(data):
    """Fixed time stamp, LF line ends and rounded reals in the DATA section."""
    txt = data.decode("utf-8", "replace").replace("\r\n", "\n")
    txt = re.sub(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','%s'" % STEP_STAMP, txt, count=1)
    head, sep, body = txt.partition("\nDATA;\n")
    if sep:
        body = _REAL.sub(lambda m: m.group(0) if m.group(0).startswith("'") else _real(m.group(0)), body)
    return (head + sep + body).encode("utf-8")


def triangulate(shape, deflection=0.05, angular=0.2):
    """(vertices, triangles) of the shape with an absolute chordal deflection in mm.

    The mesher runs single-threaded so the triangle order is fixed; reversed faces
    get their triangles flipped (outward normals), as in build123d Shape.tessellate."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRepTools import BRepTools
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.TopLoc import TopLoc_Location

    BRepTools.Clean_s(shape.wrapped)
    BRepMesh_IncrementalMesh(shape.wrapped, deflection, False, angular, False)
    verts, tris = [], []
    for face in shape.faces():
        loc = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(face.wrapped, loc)
        if poly is None:
            continue
        trsf = loc.Transformation()
        rev = face.wrapped.Orientation() == TopAbs_REVERSED
        base = len(verts)
        for i in range(1, poly.NbNodes() + 1):
            p = poly.Node(i).Transformed(trsf)
            verts.append((p.X(), p.Y(), p.Z()))
        for t in poly.Triangles():
            a, b, c = t.Value(1), t.Value(2), t.Value(3)
            tris.append((base + a - 1, base + c - 1, base + b - 1) if rev else (base + a - 1, base + b - 1, base + c - 1))
    return verts, tris


def stl_bytes(shape, name, deflection=0.05, angular=0.2, nd=4):
    """Binary STL with rounded vertices and a fixed 80-byte header."""
    verts, tris = triangulate(shape, deflection, angular)
    rv = [tuple(round(c, nd) + 0.0 for c in v) for v in verts]
    header = f"SR-RX-v2.1 {name} mm MODEL FIT ONLY".encode("ascii")[:80].ljust(80, b" ")
    out = [header, struct.pack("<I", len(tris))]
    for a, b, c in tris:
        p, q, r = rv[a], rv[b], rv[c]
        u = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
        w = (r[0] - p[0], r[1] - p[1], r[2] - p[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        L = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
        n = tuple(round(x / L, 6) + 0.0 for x in n) if L > 1e-12 else (0.0, 0.0, 0.0)
        out.append(struct.pack("<12fH", *n, *p, *q, *r, 0))
    return b"".join(out), len(tris)


def read_stl(data):
    """(triangle count, bounding box) of a binary STL, for tests and the manifest check."""
    n = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * n:
        raise ValueError("binary STL length does not match its triangle count")
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    for i in range(n):
        vals = struct.unpack_from("<12f", data, 84 + 50 * i)
        for k in range(3):
            for j in range(3):
                v = vals[3 + 3 * k + j]
                lo[j], hi[j] = min(lo[j], v), max(hi[j], v)
    return n, (tuple(lo), tuple(hi))
