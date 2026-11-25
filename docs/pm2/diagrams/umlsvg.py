"""Small SVG renderer for the PM2 UML diagrams.

Styles follow the CSE454 labs: PlantUML-like object, class, sequence and
collaboration diagrams, and the lavender rounded states of the state-diagram lab.
SVG files are converted to PNG with PyMuPDF.
"""
import math
from xml.sax.saxutils import escape

from PIL import ImageFont

_FONTS = {}
INK = "#181818"
BOX_FILL = "#F1F1F1"
SEQ_FILL = "#E6E6E6"
STATE_FILL = "#EEEDFC"
STATE_LINE = "#5B4BC4"
STATE_TEXT = "#23205C"
STATE_EDGE = "#1F2937"
ACTION_RED = "#C0392B"


def _font(size, bold=False, italic=False):
    key = (size, bold, italic)
    if key not in _FONTS:
        name = "arial"
        if bold and italic:
            name = "arialbi"
        elif bold:
            name = "arialbd"
        elif italic:
            name = "ariali"
        _FONTS[key] = ImageFont.truetype(f"C:/Windows/Fonts/{name}.ttf", size)
    return _FONTS[key]


def tw(text, size=13, bold=False, italic=False):
    return _font(size, bold, italic).getlength(text)


class Box:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    def top(self, f=0.5):
        return (self.x + self.w * f, self.y)

    def bottom(self, f=0.5):
        return (self.x + self.w * f, self.y + self.h)

    def left(self, f=0.5):
        return (self.x, self.y + self.h * f)

    def right(self, f=0.5):
        return (self.x + self.w, self.y + self.h * f)


class SVG:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.items = []

    # primitives -------------------------------------------------------
    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1.0, rx=0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" ry="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
            f'stroke-width="{sw}"{d}/>')

    def polyline(self, pts, stroke=INK, sw=1.0, dash=None, fill="none"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.items.append(f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def polygon(self, pts, fill=INK, stroke=INK, sw=1.0):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.items.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=1.0):
        self.items.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=13, anchor="start", bold=False, italic=False, fill="#000000",
             underline=False):
        weight = ' font-weight="bold"' if bold else ""
        style = ' font-style="italic"' if italic else ""
        self.items.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}"{weight}{style}>{escape(s)}</text>')
        if underline:
            w = tw(s, size, bold, italic)
            x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
            self.line(x0, y + 2.5, x0 + w, y + 2.5, stroke=fill, sw=1)

    def rich(self, x, y, parts, size=13, anchor="start"):
        """parts = [(text, colour, bold)] drawn on one baseline."""
        total = sum(tw(t, size, b) for t, _, b in parts)
        if anchor == "middle":
            x -= total / 2
        elif anchor == "end":
            x -= total
        for t, colour, b in parts:
            self.text(x, y, t, size=size, fill=colour, bold=b)
            x += tw(t, size, b)

    # arrows -------------------------------------------------------------
    def head(self, tip, frm, kind="filled", color=INK, size=10, sw=1.0):
        (x, y), (fx, fy) = tip, frm
        dx, dy = x - fx, y - fy
        n = math.hypot(dx, dy) or 1
        ux, uy = dx / n, dy / n
        px, py = -uy, ux
        bx, by = x - ux * size, y - uy * size
        half = size * 0.45
        a = (bx + px * half, by + py * half)
        b = (bx - px * half, by - py * half)
        if kind == "filled":
            self.polygon([tip, a, b], fill=color, stroke=color)
        elif kind == "open":
            self.polyline([a, tip, b], stroke=color, sw=sw)
        elif kind == "hollow":
            half = size * 0.55
            a = (bx + px * half, by + py * half)
            b = (bx - px * half, by - py * half)
            self.polygon([tip, a, b], fill="#FFFFFF", stroke=color)
        elif kind in ("diamond", "hollowdiamond"):
            mid = (x - ux * size, y - uy * size)
            back = (x - ux * size * 2, y - uy * size * 2)
            a = (mid[0] + px * half, mid[1] + py * half)
            b = (mid[0] - px * half, mid[1] - py * half)
            fill = color if kind == "diamond" else "#FFFFFF"
            self.polygon([tip, a, back, b], fill=fill, stroke=color)

    def arrow(self, pts, head="filled", dash=None, color=INK, sw=1.0, tail=None, size=10):
        self.polyline(pts, stroke=color, sw=sw, dash=dash)
        if head:
            self.head(pts[-1], pts[-2], head, color, size, sw)
        if tail:
            self.head(pts[0], pts[1], tail, color, size, sw)

    # output -------------------------------------------------------------
    def svg(self):
        body = "\n".join(self.items)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width:.0f}" height="{self.height:.0f}" '
                f'viewBox="0 0 {self.width:.0f} {self.height:.0f}">\n'
                f'<rect x="0" y="0" width="{self.width:.0f}" height="{self.height:.0f}" fill="#FFFFFF"/>\n'
                f'{body}\n</svg>\n')

    def save(self, base_path, zoom=2.0):
        import fitz
        svg_path = base_path + ".svg"
        with open(svg_path, "w", encoding="utf-8") as fh:
            fh.write(self.svg())
        doc = fitz.open(svg_path)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pix.save(base_path + ".png")
        doc.close()
        return base_path + ".png"


def title(svg, text, y=24):
    svg.text(svg.width / 2, y, text, size=14, anchor="middle", bold=True)


# ---------------------------------------------------------------------------
# Object and class boxes (PlantUML style)
# ---------------------------------------------------------------------------

def object_box(svg, x, y, name, attrs, min_w=0, size=13):
    pad, lh = 9, 17
    w = max([tw(name, size) + 2 * pad] + [tw(a, size) + 2 * pad for a in attrs] + [min_w])
    head_h = 24
    h = head_h + (len(attrs) * lh + 8 if attrs else 0)
    svg.rect(x, y, w, h, fill=BOX_FILL, stroke=INK, rx=3)
    svg.text(x + w / 2, y + 16.5, name, size=size, anchor="middle", underline=True)
    if attrs:
        svg.line(x, y + head_h, x + w, y + head_h)
        for i, a in enumerate(attrs):
            svg.text(x + pad, y + head_h + 16 + i * lh, a, size=size)
    return Box(x, y, w, h)


_KIND = {
    "class": ("C", "#ADD1B2"),
    "interface": ("I", "#B4A7E5"),
    "enum": ("E", "#EB937F"),
    "record": ("R", "#F3D37E"),
    "abstract": ("A", "#A9DCDF"),
}


def class_box(svg, x, y, name, attrs=(), ops=(), kind="class", stereo=None, min_w=0, size=12, fill=BOX_FILL):
    pad, lh = 8, 15.5
    letter, colour = _KIND[kind]
    name_w = tw(name, size + 1, bold=False) + 30
    st_w = tw(stereo, size - 1, italic=True) + 30 if stereo else 0
    w = max([name_w, st_w, min_w] + [tw(a, size) + 2 * pad for a in list(attrs) + list(ops)])
    head_h = 34 if stereo else 26
    a_h = len(attrs) * lh + 6 if attrs else 6
    o_h = len(ops) * lh + 6 if ops else 6
    h = head_h + a_h + o_h
    svg.rect(x, y, w, h, fill=fill, stroke=INK, rx=2)
    # circled letter
    total = 22 + tw(name, size + 1)
    lx = x + (w - total) / 2
    cy = y + (head_h / 2 + (3 if stereo else 0))
    svg.circle(lx + 9, cy, 9, fill=colour, stroke=INK)
    svg.text(lx + 9, cy + 4.5, letter, size=12, anchor="middle", bold=True)
    if stereo:
        svg.text(lx + 22 + tw(name, size + 1) / 2, y + 12, stereo, size=size - 1, anchor="middle", italic=True)
        svg.text(lx + 22, y + 28, name, size=size + 1, italic=(kind == "abstract"))
    else:
        svg.text(lx + 22, y + 18, name, size=size + 1, italic=(kind == "abstract"))
    yy = y + head_h
    svg.line(x, yy, x + w, yy)
    for i, a in enumerate(attrs):
        svg.text(x + pad, yy + 14 + i * lh, a, size=size)
    yy += a_h
    svg.line(x, yy, x + w, yy)
    for i, o in enumerate(ops):
        svg.text(x + pad, yy + 14 + i * lh, o, size=size)
    return Box(x, y, w, h)


def label_line(svg, p1, p2, text=None, m1=None, m2=None, size=12, off=(6, -5)):
    """Association label and multiplicities near the ends of a straight link."""
    if text:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        w = tw(text, size)
        svg.rect(mx + off[0] - 2, my + off[1] - size + 1, w + 4, size + 4, fill="#FFFFFF", stroke="#FFFFFF", sw=0)
        svg.text(mx + off[0], my + off[1], text, size=size)
    for m, p, q in ((m1, p1, p2), (m2, p2, p1)):
        if m:
            dx, dy = q[0] - p[0], q[1] - p[1]
            n = math.hypot(dx, dy) or 1
            ux, uy = dx / n, dy / n
            svg.text(p[0] + ux * 14 - uy * 9 - 3, p[1] + uy * 14 + ux * 9 + 4, m, size=size - 1)


# ---------------------------------------------------------------------------
# Sequence diagram (monochrome PlantUML style with boundary/control/entity)
# ---------------------------------------------------------------------------

def _seq_head(svg, kind, x, y, label):
    """Draw a participant head centred on x with its top at y; return height."""
    size = 13
    if kind == "actor":
        svg.circle(x, y + 8, 8, fill=SEQ_FILL)
        svg.line(x, y + 16, x, y + 34)
        svg.line(x - 12, y + 22, x + 12, y + 22)
        svg.line(x, y + 34, x - 10, y + 48)
        svg.line(x, y + 34, x + 10, y + 48)
        svg.text(x, y + 63, label, size=size, anchor="middle")
        return 68
    if kind in ("boundary", "control", "entity"):
        r = 13
        cy = y + 15
        svg.circle(x, cy, r, fill=SEQ_FILL)
        if kind == "boundary":
            svg.line(x - r - 9, cy - r, x - r - 9, cy + r)
            svg.line(x - r - 9, cy, x - r, cy)
        elif kind == "control":
            svg.polyline([(x + 1, cy - r - 4), (x - 4, cy - r), (x + 1, cy - r + 4)], sw=1.2)
        else:
            svg.line(x - r, cy + r + 1, x + r, cy + r + 1)
        svg.text(x, y + 47, label, size=size, anchor="middle")
        return 52
    w = tw(label, size) + 20
    svg.rect(x - w / 2, y, w, 30, fill=SEQ_FILL, rx=2)
    svg.text(x, y + 19.5, label, size=size, anchor="middle")
    return 30


def _head_width(kind, label):
    base = tw(label, 13) + 20
    return max(base, 50)


def sequence(base_path, heading, parts, msgs, frames=(), gap=40, step=31, left=50):
    """parts: [(id, label, kind)]; msgs: dicts f,t,text,kind in call|ret|self|create|void.

    frames: dicts kind, guard, start, end (message indices), parts (id_left, id_right),
    optional else_at / else_guard.
    """
    ids = [p[0] for p in parts]
    idx = {pid: i for i, pid in enumerate(ids)}
    widths = [_head_width(k, l) for _, l, k in parts]
    n = len(parts)
    xs = [0.0] * n
    xs[0] = left + widths[0] / 2
    for i in range(1, n):
        xs[i] = xs[i - 1] + widths[i - 1] / 2 + widths[i] / 2 + gap
    # widen gaps until every label fits
    for _ in range(6):
        for m in msgs:
            a, b = idx[m["f"]], idx[m["t"]]
            need = tw(m["text"], 12) + 34
            if a == b:
                if a + 1 < n and xs[a + 1] - xs[a] < need + 10:
                    d = need + 10 - (xs[a + 1] - xs[a])
                    for j in range(a + 1, n):
                        xs[j] += d
                continue
            lo, hi = min(a, b), max(a, b)
            if xs[hi] - xs[lo] < need:
                d = need - (xs[hi] - xs[lo])
                for j in range(hi, n):
                    xs[j] += d
    right_extra = 0
    for m in msgs:
        if m["f"] == m["t"] and idx[m["f"]] == n - 1:
            right_extra = max(right_extra, tw(m["text"], 12) + 50)
    width = xs[-1] + max(widths[-1] / 2, right_extra) + 40

    top = 46
    head_h = 68 if any(k == "actor" for _, _, k in parts) else 52
    created = {m["t"]: i for i, m in enumerate(msgs) if m["kind"] == "create"}

    # y positions of messages, with room for frame labels
    ys = []
    y = top + head_h + 28
    frame_starts = {fr["start"]: fr for fr in frames}
    frame_ends = {fr["end"]: fr for fr in frames}
    else_points = {fr["else_at"]: fr for fr in frames if "else_at" in fr}
    for i, m in enumerate(msgs):
        if i in frame_starts:
            y += 26
        if i in else_points:
            y += 22
        if m["kind"] == "create":
            y += 10
        ys.append(y)
        y += step + (14 if m["kind"] == "self" else 0) + (30 if m["kind"] == "create" else 0)
        if i in frame_ends:
            y += 10
    bottom = y + 10
    height = bottom + head_h + 20
    svg = SVG(width, height)
    title(svg, heading)

    # activations via call/return stack
    acts = []
    stack = {pid: [] for pid in ids}
    for i, m in enumerate(msgs):
        if m["kind"] == "call":
            depth = len(stack[m["t"]])
            stack[m["t"]].append((ys[i], depth))
        elif m["kind"] == "void":
            depth = len(stack[m["t"]])
            acts.append((m["t"], ys[i], ys[i] + 12, depth))
        elif m["kind"] == "ret" and m.get("pop", True) and stack[m["f"]]:
            y0, depth = stack[m["f"]].pop()
            acts.append((m["f"], y0, ys[i], depth))
    for pid, st in stack.items():
        for y0, depth in st:
            acts.append((pid, y0, bottom - 6, depth))

    # lifelines
    for i, (pid, label, kind) in enumerate(parts):
        y_start = top + head_h
        if pid in created:
            y_start = ys[created[pid]] - 15 + _head_h(kind)
        svg.line(xs[i], y_start, xs[i], bottom, stroke="#555555", dash="5,4")

    # activation bars
    for pid, y0, y1, depth in sorted(acts, key=lambda a: a[3]):
        x = xs[idx[pid]] - 5 + depth * 5
        svg.rect(x, y0, 10, max(y1 - y0, 10), fill="#FFFFFF", stroke=INK)

    # frames (drawn under the messages)
    for fr in frames:
        a, b = idx[fr["parts"][0]], idx[fr["parts"][1]]
        x0 = xs[a] - widths[a] / 2 - 6
        x1 = xs[b] + max(widths[b] / 2, 40) + 6
        y0 = ys[fr["start"]] - 40
        y1 = ys[fr["end"]] + 16
        svg.rect(x0, y0, x1 - x0, y1 - y0, fill="none", stroke=INK, sw=1.2)
        lab = fr["kind"]
        lw = tw(lab, 12, bold=True) + 16
        svg.polygon([(x0, y0), (x0 + lw, y0), (x0 + lw, y0 + 12), (x0 + lw - 6, y0 + 18), (x0, y0 + 18)],
                    fill="#EEEEEE", stroke=INK)
        svg.text(x0 + 6, y0 + 13, lab, size=12, bold=True)
        gw = tw(fr["guard"], 12, bold=True)
        svg.rect(x0 + lw + 5, y0 + 2, gw + 6, 16, fill="#FFFFFF", stroke="#FFFFFF", sw=0)
        svg.text(x0 + lw + 8, y0 + 14, fr["guard"], size=12, bold=True)
        if "else_at" in fr:
            ye = ys[fr["else_at"]] - 30
            svg.line(x0, ye, x1, ye, dash="5,4")
            ew = tw(fr["else_guard"], 12, bold=True)
            svg.rect(x0 + 5, ye + 2, ew + 6, 16, fill="#FFFFFF", stroke="#FFFFFF", sw=0)
            svg.text(x0 + 8, ye + 14, fr["else_guard"], size=12, bold=True)

    def act_edge(pid, y, toward):
        """x where an arrow meets the activation bar of pid at height y."""
        x = xs[idx[pid]]
        depth = -1
        for p, y0, y1, d in acts:
            if p == pid and y0 - 0.5 <= y <= y1 + 0.5:
                depth = max(depth, d)
        if depth < 0:
            return x
        bx = x - 5 + depth * 5
        return bx if toward > 0 else bx + 10

    # messages
    for i, m in enumerate(msgs):
        y = ys[i]
        a, b = idx[m["f"]], idx[m["t"]]
        if m["kind"] == "self":
            x = act_edge(m["f"], y, -1)
            x = max(x, xs[a] + 5)
            svg.arrow([(x, y), (x + 32, y), (x + 32, y + 14), (x + 1, y + 14)], head="filled")
            svg.text(x + 8, y - 5, m["text"], size=12)
            continue
        direction = 1 if b > a else -1
        x1 = act_edge(m["f"], y, -direction) if m["kind"] != "ret" else act_edge(m["f"], y - 0.1, -direction)
        if m["kind"] == "create":
            hw = widths[b] / 2 if _head_h(parts[b][2]) == 30 else 15
            x2 = xs[b] - direction * hw
            _seq_head(svg, parts[b][2], xs[b], y - 15, parts[b][1])
        else:
            x2 = act_edge(m["t"], y, direction)
        if m["kind"] == "ret":
            svg.arrow([(x1, y), (x2, y)], head="open", dash="5,4", size=9)
        else:
            svg.arrow([(x1, y), (x2, y)], head="filled", dash="5,4" if m["kind"] == "create" else None)
        svg.text(min(x1, x2) + (18 if direction < 0 else 8), y - 5, m["text"], size=12)

    # heads top and bottom
    for i, (pid, label, kind) in enumerate(parts):
        if pid not in created:
            _seq_head(svg, kind, xs[i], top + (head_h - _head_h(kind)), label)
        _seq_head(svg, kind, xs[i], bottom, label)
    return svg.save(base_path)


def _head_h(kind):
    return {"actor": 68, "boundary": 52, "control": 52, "entity": 52}.get(kind, 30)


# ---------------------------------------------------------------------------
# Collaboration (communication) diagram
# ---------------------------------------------------------------------------

def actor_icon(svg, x, y, label):
    svg.circle(x, y + 8, 8, fill=BOX_FILL)
    svg.line(x, y + 16, x, y + 34)
    svg.line(x - 12, y + 22, x + 12, y + 22)
    svg.line(x, y + 34, x - 10, y + 48)
    svg.line(x, y + 34, x + 10, y + 48)
    svg.text(x, y + 63, label, size=13, anchor="middle")
    return Box(x - 14, y, 28, 50)


def clip(box, toward):
    """Point where the ray from the box centre to `toward` leaves the box."""
    cx, cy = box.cx, box.cy
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    tx = (box.w / 2) / abs(dx) if dx else float("inf")
    ty = (box.h / 2) / abs(dy) if dy else float("inf")
    t = min(tx, ty)
    return (cx + dx * t, cy + dy * t)


def link(svg, b1, b2, name=None, m1=None, m2=None, name_off=(6, -6)):
    p1 = clip(b1, (b2.cx, b2.cy))
    p2 = clip(b2, (b1.cx, b1.cy))
    svg.line(p1[0], p1[1], p2[0], p2[1])
    label_line(svg, p1, p2, name, m1, m2, off=name_off)
    return p1, p2


def _label_bg(svg, x, y, text, size=12, anchor="start"):
    w = tw(text, size)
    x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    svg.rect(x0 - 2, y - size + 1, w + 4, size + 4, fill="#FFFFFF", stroke="#FFFFFF", sw=0)
    svg.text(x, y, text, size=size, anchor=anchor)


def comm_link(svg, b1, b2, messages, side=1, shift=0.0, gap=18, dx=0, dy=0, draw_line=True):
    """Link between two boxes with numbered messages.

    messages: [(text, forward)] where forward means b1 -> b2.
    side: +1 puts the labels below/right of the link, -1 above/left.
    """
    p1 = clip(b1, (b2.cx, b2.cy))
    p2 = clip(b2, (b1.cx, b1.cy))
    if draw_line:
        svg.line(p1[0], p1[1], p2[0], p2[1])
    if not messages:
        return
    ddx, ddy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(ddx, ddy) or 1
    ux, uy = ddx / n, ddy / n
    mx = p1[0] + ddx * (0.5 + shift) + dx
    my = p1[1] + ddy * (0.5 + shift) + dy
    horizontal = abs(ux) >= abs(uy)
    k_total = len(messages)
    for k, (text, forward) in enumerate(messages):
        sx, sy = (ux, uy) if forward else (-ux, -uy)
        if horizontal:
            if side > 0:
                cy = my + 16 + k * gap
            else:
                cy = my - 10 - (k_total - 1 - k) * gap
            w = tw(text, 12) + 30
            x0 = mx - w / 2
            # arrow parallel to the link (horizontal component only for readability)
            hx = 1 if sx >= 0 else -1
            ax0, ax1 = (x0, x0 + 22) if hx > 0 else (x0 + 22, x0)
            svg.rect(x0 - 2, cy - 12, w + 4, 19, fill="#FFFFFF", stroke="#FFFFFF", sw=0)
            svg.arrow([(ax0, cy - 4), (ax1, cy - 4)], head="filled", size=7)
            svg.text(x0 + 28, cy, text, size=12)
        else:
            cy = my - (k_total * gap) / 2 + k * gap + 8
            vy = 1 if sy >= 0 else -1
            cx = mx + side * 12
            svg.arrow([(cx, cy - 7 * vy - 4), (cx, cy + 7 * vy - 4)], head="filled", size=7)
            if side > 0:
                _label_bg(svg, cx + 8, cy, text)
            else:
                _label_bg(svg, cx - 8, cy, text, anchor="end")


def comm_self(svg, box, messages, where="top"):
    """Self link drawn as a loop above (or below) the box."""
    if where == "top":
        x0, x1 = box.x + box.w * 0.62, box.x + box.w * 0.9
        y0 = box.y
        svg.polyline([(x0, y0), (x0, y0 - 22), (x1, y0 - 22), (x1, y0)])
        for k, text in enumerate(messages):
            svg.arrow([(x0 + 4, y0 - 30 - k * 16), (x1 - 4, y0 - 30 - k * 16)], head="filled", size=7)
            svg.text(x1 + 4, y0 - 26 - k * 16, text, size=12)


# ---------------------------------------------------------------------------
# State diagram (CSE454 state-diagram lab style)
# ---------------------------------------------------------------------------

def state_box(svg, x, y, name, activities=(), min_w=150, size=15):
    lh = 18
    w = max([min_w, tw(name, size, bold=True) + 40] + [tw(a, 12) + 28 for a in activities])
    if activities:
        h = 34 + len(activities) * lh + 10
    else:
        h = 48
    svg.rect(x, y, w, h, fill=STATE_FILL, stroke=STATE_LINE, sw=2, rx=14)
    if activities:
        svg.text(x + w / 2, y + 23, name, size=size, anchor="middle", bold=True, fill=STATE_TEXT)
        svg.line(x, y + 33, x + w, y + 33, stroke=STATE_LINE, sw=1.2)
        for i, a in enumerate(activities):
            svg.text(x + 14, y + 33 + 18 + i * lh, a, size=12, fill=ACTION_RED)
    else:
        svg.text(x + w / 2, y + 29.5, name, size=size, anchor="middle", bold=True, fill=STATE_TEXT)
    return Box(x, y, w, h)


def initial(svg, x, y):
    svg.circle(x, y, 9, fill=STATE_EDGE, stroke=STATE_EDGE)
    return (x, y)


def final(svg, x, y):
    svg.circle(x, y, 12, fill="#FFFFFF", stroke=STATE_EDGE, sw=2)
    svg.circle(x, y, 7, fill=STATE_EDGE, stroke=STATE_EDGE)
    return (x, y)


def transition(svg, pts, label=None, at=None, anchor="start", action=None, size=13):
    svg.arrow(pts, head="open", color=STATE_EDGE, sw=1.6, size=12)
    if label is not None or action:
        parts = []
        if label:
            parts.append((label, STATE_EDGE, False))
        if action:
            parts.append(((" " if label else "") + "/ " + action, ACTION_RED, False))
        svg.rich(at[0], at[1], parts, size=size, anchor=anchor)


def note(svg, x, y, lines, size=12, fill="#FEFFDD"):
    pad, lh = 10, 16
    w = max(tw(l, size) for l in lines) + 2 * pad + 8
    h = len(lines) * lh + 12
    f = 10
    svg.polygon([(x, y), (x + w - f, y), (x + w, y + f), (x + w, y + h), (x, y + h)], fill=fill, stroke=INK)
    svg.polyline([(x + w - f, y), (x + w - f, y + f), (x + w, y + f)])
    for i, l in enumerate(lines):
        svg.text(x + pad, y + 18 + i * lh, l, size=size)
    return Box(x, y, w, h)


def ortho(svg, pts, head="open", dash=None, size=10, tail=None):
    svg.arrow(pts, head=head, dash=dash, size=size, tail=tail)


def object_size(name, attrs, size=13):
    pad, lh = 9, 17
    w = max([tw(name, size) + 2 * pad] + [tw(a, size) + 2 * pad for a in attrs])
    h = 24 + (len(attrs) * lh + 8 if attrs else 0)
    return w, h


def object_at(svg, cx, cy, name, attrs=()):
    w, h = object_size(name, attrs)
    return object_box(svg, cx - w / 2, cy - h / 2, name, list(attrs))
