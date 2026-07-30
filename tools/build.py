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
# Portraits are generated against a flat chroma-key magenta screen and the alpha
# channel is recovered here.
#
# The first two attempts both keyed on luminance against a black backdrop, and
# both were wrong for the same reason: these are deliberately low-key portraits,
# and a measurement across Mira's coat reads 0, 4, 5, 7, 9, 11, 14, 16, 19 while
# the backdrop's own noise reaches 21. The subject is *as dark as the background*.
# No threshold separates them, so the silhouette came out as islands of bright
# folds, hole-filling had no closed outline to fill, and alpha fell back to a rim
# ramp — which is a figure you can see the furniture through.
#
# Magenta separates by hue instead, which is independent of how dark the subject
# is, and because the backdrop colour is known exactly the same key also
# unpremultiplies the spill back out of the edges.
CH_H, CH_Q = 1080, 72

def key_score(a):
    """How magenta a pixel is: magenta has both R and B high and G at zero."""
    return np.minimum(a[..., 0], a[..., 2]) - a[..., 1]


def backdrop(a):
    """Measure the portrait's own backdrop from its border rather than assuming
    one. The generator does not hit the same magenta twice — measured across the
    cast it ranges from 140 to 248 — so a fixed threshold keys one portrait
    correctly and leaves another half transparent."""
    e = 20
    edge = np.concatenate([a[:e].reshape(-1, 3), a[-e:].reshape(-1, 3),
                           a[:, :e].reshape(-1, 3), a[:, -e:].reshape(-1, 3)])
    score = np.median(key_score(edge))
    if score < 40:
        return None                      # black field, not a chroma screen
    keyed = edge[key_score(edge) > score * 0.8]
    return score, np.median(keyed, axis=0)


def matte(im):
    """RGBA with a recovered alpha channel.

    Two kinds of portrait need two different keys, and which one an image needs
    is read off the image itself rather than configured, so it cannot drift:

    · the cast stands against a flat magenta screen and is keyed by hue, which
      works no matter how dark they are. Luminance keying was tried twice and is
      simply not possible here: measured across Mira's coat the values run
      0, 4, 5, 7, 9, 11, 14, 16, 19 while a black backdrop's own grain reaches
      21, so the subject is *as dark as the background* and no threshold
      separates them. What that produced was a figure you could see the
      furniture through.

    · the five entities made of light keep a black field, because for them
      luminance *is* the alpha — a hard cut-out edge on a thing woven from
      filaments looks like a sticker, and putting them on a lit screen made the
      generator stop treating them as light sources at all."""
    a = np.asarray(im, dtype=np.float32)
    bd = backdrop(a)
    if bd is None:
        lum = np.asarray(im.convert("L"), dtype=np.float32)
        alpha = np.clip(lum / 70.0, 0, 1) ** 0.85
        fg = a
    else:
        score, bg = bd
        lo, hi = score * 0.12, score * 0.88
        alpha = 1.0 - np.clip((key_score(a) - lo) / (hi - lo), 0, 1)
        # observed = alpha*fg + (1-alpha)*bg  →  recover fg, which is also what
        # takes the magenta spill back out of hair and shoulders
        ea = np.maximum(alpha, 1e-3)[..., None]
        fg = np.clip((a - (1.0 - ea) * bg) / ea, 0, 255)
    out = Image.fromarray(fg.astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8)))
    return out, (bd is not None)


def opacity_of_core(rgba):
    """Median alpha well inside the silhouette. A chroma-keyed portrait is a
    person, and a person is opaque; this is the number that was 0.3 when you
    could see a desk through Mira's coat."""
    a = np.asarray(rgba.split()[-1], dtype=np.float32) / 255.0
    solid = Image.fromarray(((a > 0.9) * 255).astype(np.uint8))
    # erode by blurring and re-thresholding, so edge pixels cannot flatter it
    core = np.asarray(solid.filter(ImageFilter.GaussianBlur(9)), np.float32) / 255.0 > 0.97
    return float(np.median(a[core])) if core.any() else 0.0

# every portrait that depicts a person, including the aged variants
HUMAN_KEYS = {k for c in CASTSPEC.HUMANS.values()
              for k in [c["key"], *(c.get("byChapter") or {}).values()]}

# ── does the portrait depict the person the script describes? ────────────
# The prompt is the only machine-readable description of what the image contains,
# so this compares prompt against prose. It cannot see the pixels — but both
# failures found this way were failures of the prompt: a resident the script calls
# "She is fifty-one" was prompted as "a person of about thirty-five", so the
# generator was free to choose, and chose a man in his thirties; Rhee was
# prompted eleven years older than the sentence that introduces him.
PROMPTS = {}
_spec = json.load(open(os.path.join(ROOT, "tools/char_prompts.json"), encoding="utf-8"))
for _b in _spec["batches"]:
    for _im in _b["images"]:
        PROMPTS[os.path.splitext(_im["file"])[0]] = _im["prompt"]

TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70}
ONES = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
        "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
AGE = r"(?:twenty|thirty|forty|fifty|sixty|seventy)(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|\d{1,2}"

def age_of(word):
    word = word.lower()
    if word.isdigit():
        return int(word)
    a, _, b = word.partition("-")
    return TENS[a] + ONES.get(b, 0)

GENDER = {"woman": "f", "girl": "f", "man": "m", "boy": "m"}
PRONOUN = {"she": "f", "her": "f", "hers": "f", "he": "m", "him": "m", "his": "m"}

def script_says(prose, speaker):
    """Gender and stated age of a character, taken from the prose itself."""
    counts = {"f": 0, "m": 0}
    for w in re.findall(r"\b(she|her|hers|he|him|his)\b", prose, re.I):
        counts[PRONOUN[w.lower()]] += 1
    # a third-person scene may mention somebody else; require a clear majority
    lead = max(counts, key=counts.get)
    other = counts["m" if lead == "f" else "f"]
    gender = lead if counts[lead] >= 3 and counts[lead] >= 2 * max(other, 1) else None
    # only an age whose grammatical subject is this character — "Aeon's public
    # launch is eleven weeks out" is not somebody's age
    subj = "|".join(["She", "He", "They"] + [w.title() for w in speaker.split()])
    ages = [age_of(m) for m in re.findall(rf"\b(?:{subj}) (?:is|was) ({AGE})\b", prose)]
    return gender, ages

def check_script_agreement(name, speaker, prose):
    prompt = PROMPTS.get(name)
    if not prompt:
        return                                   # hand-made portrait, nothing to compare
    said_g, said_ages = script_says(prose, speaker)
    drawn = {GENDER[w.lower()] for w in re.findall(r"\b(woman|girl|man|boy)\b", prompt, re.I)}
    if said_g and drawn and said_g not in drawn:
        sys.exit(f"portrait {name!r}: the script calls {speaker} "
                 f"{'she' if said_g == 'f' else 'he'} and the prompt draws a "
                 f"{'woman' if 'f' in drawn else 'man'}")
    if said_g and not drawn:
        sys.exit(f"portrait {name!r}: the script calls {speaker} "
                 f"{'she' if said_g == 'f' else 'he'} but the prompt leaves the "
                 f"gender unstated — the generator will pick one")
    drawn_ages = [age_of(m) for m in re.findall(rf"\babout ({AGE})\b", prompt)]
    if said_ages and drawn_ages and not any(abs(a - b) <= 2
                                            for a in said_ages for b in drawn_ages):
        sys.exit(f"portrait {name!r}: the script says {speaker} is {said_ages[0]}, "
                 f"the prompt draws about {drawn_ages[0]}")

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
    shown = {}
    for s in story["scenes"].values():
        sp = (s.get("sp") or "").split(" //")[0].strip()
        c = cmap.get(sp)
        if not c or s["bg"] in (c.get("hideOn") or []):
            continue
        key = (c.get("byChapter") or {}).get(s["ch"], c["key"])
        shown.setdefault(key, (sp, []))[1].append(s["text"])
    dead = wanted - set(shown)
    if dead:
        sys.exit("portraits that no scene can ever show: " + ", ".join(sorted(dead)))
    for name in sorted(wanted):
        sp, texts = shown[name]
        check_script_agreement(name, sp, "\n".join(texts))
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
        arr = np.asarray(im, dtype=np.float32)
        bd = backdrop(arr)
        subject = (key_score(arr) < bd[0] * 0.5) if bd else \
                  (np.asarray(im.convert("L"), dtype=np.float32) > 12)
        box = Image.fromarray((subject * 255).astype(np.uint8)).getbbox()
        if box:
            pad = round(im.width * 0.02)
            im = im.crop((max(0, box[0] - pad), 0, min(im.width, box[2] + pad), im.height))
        if im.height > CH_H:
            im = im.resize((round(im.width * CH_H / im.height), CH_H), Image.LANCZOS)
        im, keyed = matte(im)
        # People are opaque. The entities made of light are not, and are the only
        # portraits allowed onto the black-field path — a person who ends up there
        # is the bug the user reported: a coat you can see the furniture through.
        if name in HUMAN_KEYS:
            if not keyed:
                sys.exit(f"portrait {name!r} is a person but has no chroma backdrop — "
                         f"luminance keying cannot separate a dark subject from a dark field")
            core = opacity_of_core(im)
            if core < 0.95:
                sys.exit(f"portrait {name!r} came out translucent (core alpha {core:.2f}) — "
                         f"the key did not separate the subject from its backdrop")
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
