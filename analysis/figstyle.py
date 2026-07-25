"""Shared figure style for the dialect-bias manuscript.

Palette and typography follow the project's existing house style in
`paper/figures-src/figcommon.tex`: one restrained, print-safe scheme used by every
figure, colourblind-safe (blue against rust) and separable in greyscale.

Also provides `check_overlaps`, the label-collision gate that every figure must pass
before it is saved: every text bounding box is tested against every other text
bounding box and against every plotted line.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import Bbox

# ---- palette, from figcommon.tex -------------------------------------------
BLUE      = "#36597A"   # figblue    primary data hue
BLUEMID   = "#6E92B4"   # figbluemid
BLUELIGHT = "#C9D7E4"   # figbluelight
BLUEPALE  = "#EEF2F6"   # figbluepale
RUST      = "#B26839"   # figrust    contrast category
INK       = "#262626"   # figink     text
GRAY      = "#767676"   # figgray    de-emphasised

SAE_C  = BLUE
DIA_C  = RUST

# ---- printed width ---------------------------------------------------------
# JHSS single Word file, US Letter with 1 inch margins -> 6.5 inch text column.
TEXTWIDTH = 6.5

def use_style():
    plt.rcParams.update({
        "font.size": 8.5,
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Liberation Serif", "Times New Roman"],
        "mathtext.fontset": "dejavuserif",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.linewidth": 0.6,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8.5,
        "legend.fontsize": 8,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "savefig.bbox": None,
    })

# ---- label-overlap gate ----------------------------------------------------
def _text_bboxes(fig, renderer):
    out = []
    def add(t, tag):
        try:
            s = t.get_text()
        except Exception:
            return
        if not s or not s.strip() or not t.get_visible():
            return
        try:
            bb = t.get_window_extent(renderer=renderer)
        except Exception:
            return
        if bb.width <= 0 or bb.height <= 0:
            return
        out.append((tag, s.strip(), bb))
    for i, ax in enumerate(fig.axes):
        for t in ax.texts: add(t, f"ax{i}.text")
        for t in ax.get_xticklabels(): add(t, f"ax{i}.xtick")
        for t in ax.get_yticklabels(): add(t, f"ax{i}.ytick")
        add(ax.title, f"ax{i}.title")
        add(ax.xaxis.label, f"ax{i}.xlabel")
        add(ax.yaxis.label, f"ax{i}.ylabel")
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts(): add(t, f"ax{i}.legend")
    for t in fig.texts: add(t, "fig.text")
    return out

def _line_points(fig):
    """Every plotted line, as display-space sample points."""
    pts = []
    for i, ax in enumerate(fig.axes):
        for ln in ax.lines:
            if not ln.get_visible():
                continue
            xd, yd = ln.get_xdata(), ln.get_ydata()
            if len(xd) == 0:
                continue
            xy = np.column_stack([np.asarray(xd, float), np.asarray(yd, float)])
            xy = xy[np.isfinite(xy).all(axis=1)]
            if len(xy) == 0:
                continue
            # densify so a long segment cannot skip through a label box
            if len(xy) > 1:
                dense = []
                for a, b in zip(xy[:-1], xy[1:]):
                    dense.append(np.linspace(a, b, 24))
                xy = np.vstack(dense)
            disp = ax.transData.transform(xy)
            pts.append((f"ax{i}.line", disp))
    return pts

def check_overlaps(fig, name="figure", ignore_pairs=(), verbose=True):
    """Return a list of collisions. Empty list means the figure passes."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = _text_bboxes(fig, renderer)
    lines = _line_points(fig)
    collisions = []

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            t1, s1, b1 = texts[i]
            t2, s2, b2 = texts[j]
            if (s1, s2) in ignore_pairs or (s2, s1) in ignore_pairs:
                continue
            inter = Bbox.intersection(b1, b2)
            if inter is not None and inter.width > 0.5 and inter.height > 0.5:
                collisions.append(
                    f"TEXT/TEXT  {t1} {s1!r}  vs  {t2} {s2!r}  "
                    f"(overlap {inter.width:.1f} x {inter.height:.1f} px)")

    for tag, s, bb in texts:
        shrunk = Bbox.from_extents(bb.x0 + 1.0, bb.y0 + 1.0, bb.x1 - 1.0, bb.y1 - 1.0)
        if shrunk.width <= 0 or shrunk.height <= 0:
            continue
        for ltag, pts in lines:
            inside = ((pts[:, 0] >= shrunk.x0) & (pts[:, 0] <= shrunk.x1) &
                      (pts[:, 1] >= shrunk.y0) & (pts[:, 1] <= shrunk.y1))
            if inside.any():
                collisions.append(
                    f"TEXT/LINE  {tag} {s!r}  vs  {ltag}  "
                    f"({int(inside.sum())} sample points inside the label box)")
                break

    if verbose:
        print(f"[overlap gate] {name}: {len(texts)} text boxes, {len(lines)} lines, "
              f"{len(collisions)} collisions")
        for c in collisions:
            print("   COLLISION:", c)
        if not collisions:
            print("   PASS: no text/text or text/line collisions detected")
    return collisions

def save(fig, path, name=None, ignore_pairs=()):
    """Run the gate, refuse to save on collision."""
    name = name or path
    col = check_overlaps(fig, name=name, ignore_pairs=ignore_pairs)
    if col:
        raise SystemExit(f"REFUSING TO SAVE {path}: {len(col)} label collisions detected")
    fig.savefig(path)
    print(f"   saved {path}")
    return col
