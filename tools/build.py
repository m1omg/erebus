#!/usr/bin/env python3
"""Bundle engine + story + art into one self-contained HTML file."""
import base64, glob, io, json, os, re, sys
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cast as CASTSPEC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, Q = 1600, 900, 70

# build.py [story.json] [output.html] [--chars]
argv = [a for a in sys.argv[1:] if a != "--chars"]
with_chars = "--chars" in sys.argv[1:]
story_file = argv[0] if len(argv) > 0 else "story.json"
story = json.load(open(os.path.join(ROOT, story_file), encoding="utf-8"))
out_name = argv[1] if len(argv) > 1 else "erebus-after-the-garden.html"

needed = {s["bg"] for s in story["scenes"].values()} | {e["bg"] for e in story["endings"].values()}
needed.add(story.get("titleArt", "title_ash"))

art, total = {}, 0
for name in sorted(needed):
    # prefer the full-resolution PNG; fall back to the committed WebP
    src = os.path.join(ROOT, "art", name + ".png")
    if not os.path.exists(src):
        src = os.path.join(ROOT, "art", name + ".webp")
    if not os.path.exists(src):
        sys.exit("missing art: " + name)
    im = Image.open(src).convert("RGB")
    # cover-crop to 16:9 then resize
    tr = W / H
    r = im.width / im.height
    if r > tr:
        nw = int(im.height * tr)
        im = im.crop(((im.width - nw) // 2, 0, (im.width + nw) // 2, im.height))
    elif r < tr:
        nh = int(im.width / tr)
        im = im.crop((0, (im.height - nh) // 2, im.width, (im.height + nh) // 2))
    im = im.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=Q, method=6)
    b = buf.getvalue()
    total += len(b)
    art[name] = "data:image/webp;base64," + base64.b64encode(b).decode()
    print(f"  {name:18s} {len(b)/1024:7.1f} KB")

# ── cast ────────────────────────────────────────────────────────────────
# Portraits are generated on a pure black field, so the alpha channel has to be
# recovered here. Blend modes were the obvious shortcut and they are wrong:
# `lighten` loses the subject wherever the background is brighter than they are,
# which on a lecture-theatre screen deletes a person's head.
CH_H, CH_Q = 1080, 72

def _sweep(seen, bg, axis):
    """Propagate `seen` along one axis, in both directions, stopping at any
    non-background pixel. Whole runs move in a single vectorised pass, which is
    what makes this viable — a pixel-at-a-time flood took minutes per portrait."""
    for flip in (False, True):
        s = np.flip(seen, axis) if flip else seen
        b = np.flip(bg, axis) if flip else bg
        n = s.shape[axis]
        idx = np.arange(n).reshape((-1, 1) if axis == 0 else (1, -1))
        wall = np.maximum.accumulate(np.where(~b, idx, -1), axis=axis)
        lit = np.maximum.accumulate(np.where(s, idx, -1), axis=axis)
        r = (lit > wall) & b
        if flip:
            r = np.flip(r, axis)
        seen = seen | r
    return seen


def fill_holes(mask):
    """Flood the background inward from the border; whatever the flood never
    reaches is interior, and interior is opaque however dark it happens to be —
    which is how an unlit black coat stops being a hole in the middle of a
    person."""
    bg = ~mask
    seen = np.zeros_like(bg)
    seen[0], seen[-1], seen[:, 0], seen[:, -1] = bg[0], bg[-1], bg[:, 0], bg[:, -1]
    for _ in range(64):
        before = seen.sum()
        seen = _sweep(_sweep(seen, bg, 1), bg, 0)
        if seen.sum() == before:
            break
    return mask | (bg & ~seen)

def matte(im, glow):
    """RGBA with alpha recovered from luminance."""
    a = np.asarray(im.convert("L"), dtype=np.float32)
    if glow:
        alpha = np.clip(a / 70.0, 0, 1) ** 0.85      # stays translucent
    else:
        solid = fill_holes(a > 14)
        core = Image.fromarray((solid * 255).astype(np.uint8))
        soft = np.asarray(core.filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255.0
        # The ramp is what keeps loose hair and rim light from being cut off, but
        # applied everywhere it also paints the prompt's volumetric haze across
        # the scene as a halo. Confine it to a narrow band around the silhouette.
        near = np.asarray(core.filter(ImageFilter.GaussianBlur(7)), np.float32) / 255.0
        edge = np.clip(a / 48.0, 0, 1) * np.clip(near * 2.4, 0, 1)
        alpha = np.maximum(soft, edge)
    out = im.convert("RGBA")
    out.putalpha(Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8)))
    return out

cast, ctotal = {}, 0
if with_chars:
    cmap = story.get("chars", {}).get("map", {})
    chapters = {c["id"] for c in story["chapters"]}
    wanted = set()
    for c in cmap.values():
        wanted.add(c["key"])
        # the ageing map is written against the seventeen-year story; the
        # ninety-day one has none of those chapters and needs none of the
        # younger portraits
        wanted.update(v for k, v in (c.get("byChapter") or {}).items() if k in chapters)

    # Which portraits can any scene actually select? A portrait that ships but
    # is never reachable means a chapter mapping is wrong — that is how Kade's
    # detained portrait ended up standing in for him in 2041, eight years early.
    shown = set()
    for s in story["scenes"].values():
        c = cmap.get((s.get("sp") or "").split(" //")[0].strip())
        if not c or s["bg"] in (c.get("hideOn") or []):
            continue
        shown.add((c.get("byChapter") or {}).get(s["ch"], c["key"]))
    dead = wanted - shown
    if dead:
        sys.exit("portraits that no scene can ever show: " + ", ".join(sorted(dead)))
    for name in sorted(wanted):
        src = os.path.join(ROOT, "chars", name + ".png")
        if not os.path.exists(src):
            src = os.path.join(ROOT, "chars", name + ".webp")
        if not os.path.exists(src):
            sys.exit("missing portrait: " + name)
        im = Image.open(src).convert("RGB")
        # Trim the black margins horizontally only. Cropping vertically too would
        # normalise every subject to the same height and destroy the relative
        # scale the prompts were written for — a hovering shell is not a person.
        gs = im.convert("L").point(lambda v: 255 if v > 12 else 0)
        box = gs.getbbox()
        if box:
            pad = round(im.width * 0.02)
            im = im.crop((max(0, box[0] - pad), 0, min(im.width, box[2] + pad), im.height))
        if im.height > CH_H:
            im = im.resize((round(im.width * CH_H / im.height), CH_H), Image.LANCZOS)
        im = matte(im, name in CASTSPEC.GLOW)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=CH_Q, method=6)
        b = buf.getvalue()
        ctotal += len(b)
        cast[name] = "data:image/webp;base64," + base64.b64encode(b).decode()
        print(f"  ~{name:16s} {len(b)/1024:7.1f} KB")

html = open(os.path.join(ROOT, "src/index.html"), encoding="utf-8").read()

def inject(tag, payload):
    global html
    pat = re.compile(r"/\*__%s__\*/.*?/\*__/%s__\*/" % (tag, tag), re.S)
    if not pat.search(html):
        sys.exit("placeholder not found: " + tag)
    html = pat.sub(lambda m: payload, html, count=1)

inject("STORY", json.dumps(story, ensure_ascii=False, separators=(",", ":")))
inject("ART", json.dumps(art, separators=(",", ":")))
inject("CAST", json.dumps(cast, separators=(",", ":")))

out_dir = os.path.join(ROOT, "docs")
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, out_name)
open(out, "w", encoding="utf-8").write(html)
print(f"\nart {total/1048576:.2f} MB"
      + (f" + cast {ctotal/1048576:.2f} MB ({len(cast)} portraits)" if cast else "")
      + f" → bundle {os.path.getsize(out)/1048576:.2f} MB")
print("wrote", out)
