#!/usr/bin/env python3
"""Bundle engine + story + art into one self-contained HTML file."""
import base64, glob, io, json, os, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, Q = 1600, 900, 70

# build.py [story.json] [output.html]
story_file = sys.argv[1] if len(sys.argv) > 1 else "story.json"
story = json.load(open(os.path.join(ROOT, story_file), encoding="utf-8"))
out_name = sys.argv[2] if len(sys.argv) > 2 else "erebus-after-the-garden.html"

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

html = open(os.path.join(ROOT, "src/index.html"), encoding="utf-8").read()

def inject(tag, payload):
    global html
    pat = re.compile(r"/\*__%s__\*/.*?/\*__/%s__\*/" % (tag, tag), re.S)
    if not pat.search(html):
        sys.exit("placeholder not found: " + tag)
    html = pat.sub(lambda m: payload, html, count=1)

inject("STORY", json.dumps(story, ensure_ascii=False, separators=(",", ":")))
inject("ART", json.dumps(art, separators=(",", ":")))

out_dir = os.path.join(ROOT, "docs")
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, out_name)
open(out, "w", encoding="utf-8").write(html)
print(f"\nart {total/1048576:.2f} MB → bundle {os.path.getsize(out)/1048576:.2f} MB")
print("wrote", out)
