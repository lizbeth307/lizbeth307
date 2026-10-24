"""SVG, DXF (R12, model space, mm) and PDF writers for geom2d.Sheet.

All three are byte-reproducible: fixed number formatting, fixed element order,
no timestamps. The PDF uses matplotlib with its bundled DejaVu font, so Ukrainian
text renders without system fonts.
"""
import io
import math
from xml.sax.saxutils import escape

from .geom2d import LAYER_STYLE, fmt, scale_label

ANCHOR_SVG = {"start": "start", "middle": "middle", "end": "end"}


def _paper_items(sheet):
    """Model items transformed to paper space, followed by the paper items."""
    s, (ox, oy) = sheet.scale, sheet.origin
    out = []
    for kind, layer, d in sheet.items:
        if kind == "line":
            (a, b) = d
            out.append((kind, layer, ((ox + a[0] * s, oy + a[1] * s), (ox + b[0] * s, oy + b[1] * s))))
        elif kind == "circle":
            c, r = d
            out.append((kind, layer, ((ox + c[0] * s, oy + c[1] * s), r * s)))
        elif kind == "arc":
            c, r, a0, a1 = d
            out.append((kind, layer, ((ox + c[0] * s, oy + c[1] * s), r * s, a0, a1)))
        elif kind == "text":
            p, txt, h, anchor, rot = d
            out.append((kind, layer, ((ox + p[0] * s, oy + p[1] * s), txt, h, anchor, rot)))
    return out + list(sheet.paper)


def to_svg(sheet, meta):
    W, H = sheet.size
    f = lambda v: fmt(v, 3)
    y = lambda v: H - v
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(W)}mm" height="{f(H)}mm" viewBox="0 0 {f(W)} {f(H)}">',
        f'<title>{escape(sheet.sid + " " + sheet.title)}</title>',
        f'<desc>SR-RX-v2.1 mechanical drawing, scale {scale_label(sheet.scale)}, mm. MODEL FIT ONLY. params {meta["params"]}</desc>',
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
    ]
    for kind, layer, d in _paper_items(sheet):
        w, dash, _ = LAYER_STYLE.get(layer, LAYER_STYLE["THIN"])
        st = f'stroke="#000" stroke-width="{f(w)}" fill="none"'
        if dash:
            st += f' stroke-dasharray="{" ".join(f(v) for v in dash)}"'
        if kind == "line":
            (a, b) = d
            lines.append(f'<line x1="{f(a[0])}" y1="{f(y(a[1]))}" x2="{f(b[0])}" y2="{f(y(b[1]))}" {st}/>')
        elif kind == "circle":
            c, r = d
            lines.append(f'<circle cx="{f(c[0])}" cy="{f(y(c[1]))}" r="{f(r)}" {st}/>')
        elif kind == "arc":
            c, r, a0, a1 = d
            sweep = (a1 - a0) % 360.0 or 360.0
            p0 = (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)))
            p1 = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
            large = 1 if sweep > 180.0 else 0
            # model arcs are counter-clockwise; with the SVG y axis pointing down that is sweep-flag 1
            lines.append(f'<path d="M {f(p0[0])} {f(y(p0[1]))} A {f(r)} {f(r)} 0 {large} 1 {f(p1[0])} {f(y(p1[1]))}" {st}/>')
        elif kind == "text":
            p, txt, h, anchor, rot = d
            tr = f' transform="rotate({f(-rot)} {f(p[0])} {f(y(p[1]))})"' if rot else ""
            fam = "DejaVu Sans Mono, monospace" if layer == "TABLE" else "DejaVu Sans, Arial, sans-serif"
            lines.append(f'<text x="{f(p[0])}" y="{f(y(p[1]))}" font-family="{fam}" '
                         f'font-size="{f(h * 1.4)}" text-anchor="{ANCHOR_SVG[anchor]}" fill="#000"{tr}>{escape(txt)}</text>')
    lines.append("</svg>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _dxf_text(s):
    out = []
    for ch in s:
        if ch in ("⌀", "Ø"):
            out.append("%%c")
        elif ch == "±":
            out.append("%%p")
        elif ch == "°":
            out.append("%%d")
        elif ord(ch) < 128:
            out.append(ch)
        else:
            return None   # Cyrillic labels stay in the SVG/PDF only
    return "".join(out)


def to_dxf(sheet, only=None):
    """AutoCAD R12 ASCII DXF, model space only, units mm, layers as in geom2d.

    only: restrict to these layers (the board Edge.Cuts files keep CUT and HOLE)."""
    f = lambda v: fmt(v, 4)
    out = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSBASE", "10", "0.0", "20", "0.0", "30", "0.0",
           "9", "$EXTMIN", "10", "0.0", "20", "0.0", "9", "$EXTMAX", "10", "1000.0", "20", "1000.0", "0", "ENDSEC",
           "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", str(len(LAYER_STYLE))]
    for name, (_, _, col) in LAYER_STYLE.items():
        out += ["0", "LAYER", "2", name, "70", "0", "62", str(col), "6", "CONTINUOUS"]
    out += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    for kind, layer, d in sheet.items:
        if only and layer not in only:
            continue
        if kind == "line":
            (a, b) = d
            out += ["0", "LINE", "8", layer, "10", f(a[0]), "20", f(a[1]), "30", "0", "11", f(b[0]), "21", f(b[1]), "31", "0"]
        elif kind == "circle":
            c, r = d
            out += ["0", "CIRCLE", "8", layer, "10", f(c[0]), "20", f(c[1]), "30", "0", "40", f(r)]
        elif kind == "arc":
            c, r, a0, a1 = d
            out += ["0", "ARC", "8", layer, "10", f(c[0]), "20", f(c[1]), "30", "0", "40", f(r), "50", f(a0 % 360.0), "51", f(a1 % 360.0 if a1 % 360.0 else 360.0)]
        elif kind == "text":
            p, txt, h, anchor, rot = d
            t = _dxf_text(txt)
            if t is None:
                continue
            hal = {"start": 0, "middle": 1, "end": 2}[anchor]
            out += ["0", "TEXT", "8", layer, "10", f(p[0]), "20", f(p[1]), "30", "0", "40", f(h / sheet.scale), "1", t, "50", f(rot)]
            if hal:
                out += ["72", str(hal), "11", f(p[0]), "21", f(p[1]), "31", "0"]
    out += ["0", "ENDSEC", "0", "EOF"]
    return ("\n".join(out) + "\n").encode("ascii")


def to_pdf(sheets, meta):
    """One PDF per list of sheets (each sheet one page), via matplotlib."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.lines import Line2D
    from matplotlib.patches import Arc, Circle

    matplotlib.rcParams.update({"pdf.fonttype": 42, "font.family": "DejaVu Sans", "path.simplify": False,
                                "pdf.compression": 6, "svg.hashsalt": "srrx"})
    pt = 72.0 / 25.4
    buf = io.BytesIO()
    with PdfPages(buf, metadata={"Creator": None, "Producer": None, "CreationDate": None,
                                 "Title": "SR-RX-v2.1 mechanical drawings"}) as pdf:
        for sheet in sheets:
            W, H = sheet.size
            fig = plt.figure(figsize=(W / 25.4, H / 25.4))
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_xlim(0, W)
            ax.set_ylim(0, H)
            ax.set_aspect("equal")
            ax.axis("off")
            for kind, layer, d in _paper_items(sheet):
                w, dash, _ = LAYER_STYLE.get(layer, LAYER_STYLE["THIN"])
                ls = (0, tuple(v * pt / (w * pt) for v in dash)) if dash else "solid"
                if kind == "line":
                    (a, b) = d
                    ax.add_line(Line2D([a[0], b[0]], [a[1], b[1]], linewidth=w * pt, color="black", linestyle=ls,
                                       solid_capstyle="round", dash_capstyle="butt"))
                elif kind == "circle":
                    c, r = d
                    ax.add_patch(Circle(c, r, fill=False, linewidth=w * pt, edgecolor="black", linestyle=ls))
                elif kind == "arc":
                    c, r, a0, a1 = d
                    ax.add_patch(Arc(c, 2 * r, 2 * r, theta1=a0, theta2=a1, linewidth=w * pt, edgecolor="black", linestyle=ls))
                elif kind == "text":
                    p, txt, h, anchor, rot = d
                    ax.text(p[0], p[1], txt, fontsize=h * 1.4 * pt, ha={"start": "left", "middle": "center", "end": "right"}[anchor],
                            va="baseline", rotation=rot, rotation_mode="anchor", color="black",
                            family="DejaVu Sans Mono" if layer == "TABLE" else "DejaVu Sans")
            pdf.savefig(fig)
            plt.close(fig)
    return buf.getvalue()
