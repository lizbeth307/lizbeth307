"""Minimal 2D drawing model shared by the SVG, DXF and PDF writers.

Geometry is stored in model millimetres; a sheet maps it to paper millimetres
with one scale and origin. 1:1 sheets print as templates when the PDF is
printed at 100 % (every sheet carries a 100 mm check bar).
"""
import math

LAYER_STYLE = {
    # layer: (stroke width on paper in mm, dash pattern or None, DXF colour)
    "CUT": (0.50, None, 7),
    "HOLE": (0.35, None, 1),
    "BEND": (0.25, (4.0, 2.0), 5),
    "CENTER": (0.18, (6.0, 1.5, 1.0, 1.5), 3),
    "HIDDEN": (0.25, (2.0, 1.5), 8),
    "DIM": (0.18, None, 4),
    "TEXT": (0.18, None, 7),
    "ENGRAVE": (0.25, None, 6),
    "FRAME": (0.50, None, 7),
    "THIN": (0.18, None, 7),
    "TABLE": (0.18, None, 7),
}


def fmt(v, nd=2):
    """Stable number formatting: fixed rounding, no '-0', no trailing zeros."""
    r = round(float(v), nd)
    if r == 0:
        r = 0.0
    s = f"{r:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


class Sheet:
    def __init__(self, sid, title, subtitle="", size=(420.0, 297.0), scale=1.0, origin=(30.0, 40.0),
                 material="", notes=(), kind="drawing"):
        self.sid = sid
        self.title = title
        self.subtitle = subtitle
        self.size = size
        self.scale = scale
        self.origin = origin
        self.material = material
        self.notes = list(notes)
        self.kind = kind
        self.items = []        # (kind, layer, data) in model space
        self.paper = []        # same tuples in paper space (frame, title block, notes)
        self._labels = []      # model-space boxes of placed labels, for label()

    # ---- model space -------------------------------------------------
    def line(self, p, q, layer="CUT"):
        self.items.append(("line", layer, (tuple(p), tuple(q))))

    def poly(self, pts, closed=True, layer="CUT"):
        pts = [tuple(p) for p in pts]
        for a, b in zip(pts, pts[1:] + (pts[:1] if closed else [])):
            self.line(a, b, layer)

    def rect(self, x, y, w, h, layer="CUT"):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True, layer)

    def rrect(self, x, y, w, h, r, layer="CUT"):
        r = min(r, w / 2.0, h / 2.0)
        if r <= 0:
            return self.rect(x, y, w, h, layer)
        self.line((x + r, y), (x + w - r, y), layer)
        self.line((x + w, y + r), (x + w, y + h - r), layer)
        self.line((x + w - r, y + h), (x + r, y + h), layer)
        self.line((x, y + h - r), (x, y + r), layer)
        self.arc((x + w - r, y + r), r, 270, 360, layer)
        self.arc((x + w - r, y + h - r), r, 0, 90, layer)
        self.arc((x + r, y + h - r), r, 90, 180, layer)
        self.arc((x + r, y + r), r, 180, 270, layer)

    def circle(self, c, r, layer="HOLE"):
        self.items.append(("circle", layer, (tuple(c), float(r))))

    def arc(self, c, r, a0, a1, layer="CUT"):
        """Counter-clockwise arc from a0 to a1 (degrees)."""
        self.items.append(("arc", layer, (tuple(c), float(r), float(a0), float(a1))))

    def text(self, p, s, h=3.0, layer="TEXT", anchor="start", rot=0.0):
        """h is the text height on paper (mm), independent of the scale."""
        self.items.append(("text", layer, (tuple(p), str(s), float(h), anchor, float(rot))))

    def center_mark(self, c, size=4.0):
        x, y = c
        self.line((x - size, y), (x + size, y), "CENTER")
        self.line((x, y - size), (x, y + size), "CENTER")

    def text_box(self, p, s, h, anchor="start"):
        """Approximate model-space box of a text (DejaVu Sans: about 0.75 x font size per character)."""
        w = len(s) * 0.75 * h * 1.4 / self.scale
        hh = h * 1.4 / self.scale
        x0 = p[0] - (w / 2 if anchor == "middle" else w if anchor == "end" else 0.0)
        return (x0, p[1] - 0.25 * hh, x0 + w, p[1] + 0.85 * hh)

    def label(self, p, s, h=2.5, alternatives=()):
        """Place a label at p, or at the first alternative position whose box does not overlap an earlier label."""
        for q in (p,) + tuple(alternatives):
            b = self.text_box(q, s, h)
            if not any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in self._labels):
                break
        else:
            q, b = p, self.text_box(p, s, h)
        self._labels.append(b)
        self.text(q, s, h, "TEXT")

    def hole(self, c, d, label=None, h=2.5, dx=None, dy=None):
        self.circle(c, d / 2.0, "HOLE")
        self.center_mark(c, max(2.0, d / 2.0 + 1.5))
        if label:
            off = d / 2.0 + 1.5
            p = (c[0] + (off if dx is None else dx), c[1] + (off if dy is None else dy))
            step = h * 1.4 / self.scale + 0.6
            w = self.text_box(p, label, h)[2] - p[0]
            alts = [(c[0] + off, c[1] + off), (c[0] + off, c[1] - off - step), (c[0] - off - w, c[1] + off),
                    (c[0] - off - w, c[1] - off - step)]
            alts += [(a[0], a[1] + k * step * s) for k in (1, 2, 3) for s in (1, -1) for a in alts[:2]]
            self.label(p, label, h, alts)

    def dim(self, p, q, off, text=None, h=2.5, nd=1):
        """Aligned dimension between p and q, dimension line shifted by off (model mm, signed, normal)."""
        (x1, y1), (x2, y2) = p, q
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1e-9:
            return
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        a = (x1 + nx * off, y1 + ny * off)
        b = (x2 + nx * off, y2 + ny * off)
        sgn = 1.0 if off >= 0 else -1.0
        ext = 1.5 / self.scale
        self.line((x1 + nx * sgn * 0.8 / self.scale, y1 + ny * sgn * 0.8 / self.scale), (a[0] + nx * sgn * ext, a[1] + ny * sgn * ext), "DIM")
        self.line((x2 + nx * sgn * 0.8 / self.scale, y2 + ny * sgn * 0.8 / self.scale), (b[0] + nx * sgn * ext, b[1] + ny * sgn * ext), "DIM")
        self.line(a, b, "DIM")
        al = 2.2 / self.scale
        aw = 0.7 / self.scale
        for (px, py), s in ((a, 1.0), (b, -1.0)):
            self.line((px, py), (px + s * ux * al + nx * aw, py + s * uy * al + ny * aw), "DIM")
            self.line((px, py), (px + s * ux * al - nx * aw, py + s * uy * al - ny * aw), "DIM")
        ang = math.degrees(math.atan2(uy, ux))
        if ang > 90.0 or ang <= -90.0:
            ang -= 180.0 if ang > 0 else -180.0
        mid = ((a[0] + b[0]) / 2 + nx * sgn * 1.2 / self.scale, (a[1] + b[1]) / 2 + ny * sgn * 1.2 / self.scale)
        if sgn < 0:
            mid = ((a[0] + b[0]) / 2 + nx * sgn * (1.2 + h) / self.scale, (a[1] + b[1]) / 2 + ny * sgn * (1.2 + h) / self.scale)
        self.text(mid, fmt(L, nd) if text is None else text, h, "DIM", "middle", ang)

    def dim_h(self, x1, x2, y, at, text=None, h=2.5):
        """Horizontal dimension of x1..x2 measured at height y, drawn at y = at."""
        self.dim((x1, y), (x2, y), at - y, text, h)

    def dim_v(self, y1, y2, x, at, text=None, h=2.5):
        """Vertical dimension of y1..y2 measured at x, drawn at x = at."""
        self.dim((x, y1), (x, y2), -(at - x), text, h)

    # ---- paper space --------------------------------------------------
    def pline(self, p, q, layer="FRAME"):
        self.paper.append(("line", layer, (tuple(p), tuple(q))))

    def ptext(self, p, s, h=3.0, anchor="start", rot=0.0, layer="TEXT"):
        self.paper.append(("text", layer, (tuple(p), str(s), float(h), anchor, float(rot))))

    def to_paper(self, p):
        return (self.origin[0] + p[0] * self.scale, self.origin[1] + p[1] * self.scale)

    def bbox(self):
        xs, ys = [], []
        for k, _, d in self.items:
            if k == "line":
                for p in d:
                    xs.append(p[0]); ys.append(p[1])
            elif k in ("circle", "arc"):
                (cx, cy), r = d[0], d[1]
                xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
        return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)

    def finish(self, meta):
        """Frame, check bar, notes and title block. meta: dict of title-block lines."""
        W, H = self.size
        m = 8.0
        self.pline((m, m), (W - m, m)); self.pline((W - m, m), (W - m, H - m))
        self.pline((W - m, H - m), (m, H - m)); self.pline((m, H - m), (m, m))
        # 100 mm check bar, bottom left
        x0, y0 = m + 6.0, m + 8.0
        self.pline((x0, y0), (x0 + 100.0, y0), "THIN")
        for i in range(0, 11):
            t = 2.5 if i % 5 else 4.0
            self.pline((x0 + 10.0 * i, y0), (x0 + 10.0 * i, y0 + t), "THIN")
        self.ptext((x0, y0 - 4.0), "Контроль масштабу: 100 мм (друкувати 100 %, без підгонки)", 2.2)
        # title block, bottom right
        tw, th = 150.0, 42.0
        tx, ty = W - m - tw, m
        self.pline((tx, ty), (tx, ty + th)); self.pline((tx, ty + th), (tx + tw, ty + th))
        for k in (1, 2, 3, 4):
            self.pline((tx, ty + k * 7.0), (tx + tw, ty + k * 7.0), "THIN")
        def fit(s, h, width=tw - 4.0):
            n = int(width / (0.75 * h * 1.4))
            return s if len(s) <= n else s[:n - 1].rstrip() + "…"

        self.ptext((tx + 2.0, ty + th - 6.0), fit(self.title, 3.2), 3.2)
        self.ptext((tx + 2.0, ty + 4 * 7.0 + 2.0), fit(self.subtitle, 2.3), 2.3)
        self.ptext((tx + 2.0, ty + 3 * 7.0 + 2.0), f"Креслення {self.sid} · масштаб {meta['scale']} · мм · допуск ±0.2, якщо не вказано", 2.3)
        mat = f"Матеріал: {self.material or '—'}"
        self.ptext((tx + 2.0, ty + 2 * 7.0 + 2.0), fit(mat, 2.3), 2.3)
        if fit(mat, 2.3) != mat:
            self.notes.append(mat)
        self.ptext((tx + 2.0, ty + 1 * 7.0 + 2.0), "SR-RX-v2.1 · MODEL FIT ONLY · фізичні ворота OPEN", 2.3)
        self.ptext((tx + 2.0, ty + 2.0), f"mechanical/build.py · params {meta['params']} · v{meta['version']}", 2.0)
        # notes, top left
        ny = H - m - 7.0
        self.ptext((m + 4.0, ny), self.title, 4.0)
        ny -= 5.5
        if self.subtitle:
            self.ptext((m + 4.0, ny), self.subtitle, 2.6)
            ny -= 4.5
        for n in self.notes:
            self.ptext((m + 4.0, ny), n, 2.3)
            ny -= 3.6


def scale_label(scale):
    if abs(scale - 1.0) < 1e-9:
        return "1:1"
    if scale < 1.0:
        return "1:" + fmt(1.0 / scale, 2)
    return fmt(scale, 2) + ":1"
