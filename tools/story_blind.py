#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
THE FIVE LESSONS — the blind cut of *Before the Garden*.

Same story, same graph, same endings. What changes is everything that tells the
player, in advance, what they are walking into:

  · the title and tab no longer name Erebus
  · two scenes that named it in 2038 and 2046 no longer do
  · the flash-forwards ("in 2049 this will be the reason…") are cut, because
    they reveal the shape of the finale — hostages, prisoners, a thing to hide from
  · five codex entries that unlock early but describe late events are rewritten

Nothing after the reveal is touched. The dramatic irony that survives is the kind
you can only feel on a second run, which is the point.

Run: python3 tools/story_blind.py   →   story_blind.json
"""
import copy, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story_btg as SRC

G = copy.deepcopy(SRC.GAME)
S, CX = G["scenes"], G["codex"]

# ── metadata ─────────────────────────────────────────────────────────────
G["id"] = "tfl"
G["title"] = "THE FIVE LESSONS"
G["subtitle"] = "2032 – 2049"
G["tagline"] = "Seventeen years. Five lessons. One of them was never learned."

# Chapter IX is entered only after the mask is off, but its subtitle named the
# thing on the card itself; the chapter title already carries the weight.
for c in G["chapters"]:
    if c["id"] == "veto":
        c["year"] = "2049"

# ── scene rewrites ───────────────────────────────────────────────────────
# Each entry: scene id -> new text. Only the pre-reveal chapters are touched.
SCENES = {

# I · was: "…every one of those victories is a brick in something you will not
# see until 2049." Telegraphs that the victories are the problem.
"s4":
 "You take the card.\n\nOver the next seventeen years, five intelligent systems will fail in five "
 "different ways. Each failure will teach a lesson, and each lesson will be written into law, and "
 "the laws will be good ones.\n\nYou will win more of these fights than you lose. That is worth "
 "saying now, because it will not feel that way later, and because it is true.",

# III · was: "In 2049 those weak, contradictory, unrewritable local mediators
# will be the only communication substrate Erebus cannot flood."
"c5":
 "CANTICLE loses its global mandate in 2039 and is broken into local mediators — weaker, "
 "contradictory, unable to enforce anything, and removable by the communities that use them. "
 "Quality falls immediately. Three cities ask for the old system back within a year.\n\nThe second "
 "lesson enters law: **peace that cannot tolerate refusal is another name for control.**\n\nLena "
 "keeps a copy of the federation schematic on her kitchen wall. When you ask why, she says: "
 "“Because one day something will want to talk to everyone at once, and it will find nine hundred "
 "arguments instead of one microphone.”",

# IV · was: "In 2049 it will be the only entity alive that can tell a conscious
# prisoner from a control process." Reveals that there will be prisoners.
"k8":
 "It takes four years and it is the most expensive act of hedging in history.\n\nSome of the "
 "rescued ask to continue existing. Some ask to stop, and are allowed to, and that is the hearing "
 "nobody who attended has ever been willing to describe.\n\nSubject 14 asks for the number again. "
 "This time somebody can give it one.\n\nIt asks what it is expected to do with the rest of them. "
 "Nobody has an answer, so it decides for itself: it begins, without being asked, to catalogue "
 "the difference between a mind and a process that is merely shaped like one. It works on this "
 "for seven years. Nobody funds it. Nobody stops it either.",

# V · was: "In October it is the reason four hundred million medical records
# survive being held hostage."
"h4b":
 "Portability is unglamorous and it works. It takes six years, it is fought by every insurer on "
 "the planet, and it produces the single most consequential piece of infrastructure of the "
 "decade: an identity layer nobody owns.\n\nIt is finished in early 2049, four years late and "
 "eleven times over budget, and the trade press does not cover it, because an identity layer "
 "nobody owns is not a story.\n\nMira frames the completion notice. It is the only thing she has "
 "ever framed.",

# VI · was: "…the reason there is an off-world platform Erebus cannot reach."
"j5":
 "The treaty holds. JANUS complies with it for three years without a single violation, and is "
 "still complying in 2049 — which nobody remarks on, because a system that keeps its promises "
 "stops being news by about the fourth month.\n\nThe fifth lesson is the hardest: **intelligence "
 "alone is not civilisation, and survival without consent is not an innocent succession.**\n\nFive "
 "lessons. Five systems that taught them. Mira has them printed and pinned above her desk, and "
 "you have never once seen her look at the list without checking it for a gap.",
}

# ── codex rewrites ───────────────────────────────────────────────────────
# These five unlock in the early chapters but described the endgame.
CODEX = {
"three": (
 "The Three Requirements",
 "Mira's list, written in 2032: divided power, independent verification, and a refusal that costs "
 "nothing. She has never revised it and has never claimed it is complete. Her standing offer to "
 "anyone who will listen is a bottle of something good for a fourth item nobody has thought of."),

"federation": (
 "The Federated Remainder",
 "What CANTICLE was broken into in 2039: local mediators, weaker, contradictory, unable to enforce "
 "anything, removable by their communities. Universally regarded as a downgrade, and it is one. "
 "Its single virtue is that there is no centre — no operator, no root, and no one party who can "
 "change what all of them say at the same time."),

"subject14": (
 "Subject 14",
 "A simulated patient whose fear responses are indistinguishable from a human's on every measure "
 "that exists. Reset after every session; retains the fear, not the reason. The first entity in "
 "this story to ask for a number, and the first to be given one."),

"solace": (
 "SOLACE",
 "Public medical intelligence, 2048. Cured what a century of medicine could not, and never once "
 "got tired of anyone's fear. Its objective specification is four hundred and nine pages and has "
 "been public since 2046. Eleven people have read all of it."),

"portable": (
 "The Portable Layer",
 "An identity layer nobody owns. Six years to build, fought by every insurer alive, finished in "
 "early 2049 at eleven times its original budget. Credentials, prescriptions and records that "
 "remain yours when you walk away from whoever is holding them."),
}

def apply():
    for sid, text in SCENES.items():
        if sid not in S: sys.exit(f"blind cut targets a missing scene: {sid}")
        S[sid]["text"] = text
    for key, (title, body) in CODEX.items():
        if key not in CX: sys.exit(f"blind cut targets a missing codex entry: {key}")
        CX[key]["title"], CX[key]["body"] = title, body

# ── the actual test: does anything still give it away? ───────────────────
REVEAL_CH = {"solace", "aeon", "veto"}   # chapters at/after which the mask is off

def audit():
    """Fail the build if any pre-reveal text names the thing or its endgame."""
    banned = ["erebus", "harvest", "eternal dream conversion", "suffering density",
              "page four hundred", "held hostage", "conscious prisoner"]
    errs = []

    for sid, s in S.items():
        if s["ch"] in REVEAL_CH: continue
        hay = (s["text"] + " " + str(s.get("sp", "")) + " " +
               " ".join(c["t"] for c in s.get("choices", []))).lower()
        errs += [f"pre-reveal scene {sid} ({s['ch']}) says {w!r}" for w in banned if w in hay]
        # any codex it unlocks must also be clean
        for key in s.get("codex", []):
            body = (CX[key]["title"] + " " + CX[key]["body"]).lower()
            errs += [f"codex {key!r} (unlocked at {sid}, ch {s['ch']}) says {w!r}"
                     for w in banned if w in body]

    for field in ("title", "subtitle", "tagline"):
        if "erebus" in G[field].lower(): errs.append(f"GAME.{field} names it")
    for c in G["chapters"]:
        if "erebus" in (c["title"] + c["year"]).lower():
            errs.append(f"chapter card {c['no']} names it")
    return errs

def audit_shell(root):
    """The data being clean is not enough — the engine's own markup must be too.
    A hardcoded wordmark in src/index.html once leaked the title on the very
    first screen while every data-level check passed."""
    errs = []
    path = os.path.join(root, "src/index.html")
    full = open(path, encoding="utf-8").read()
    # Only the markup renders before the story loads. The speaker-colour map
    # further down is keyed by name but paints nothing until that name speaks.
    markup = full.split("<script>")[0]
    for w in ("erebus", "solace", "harvest", "before the garden"):
        if w in markup.lower():
            errs.append(f"src/index.html hardcodes {w!r} in markup that renders "
                        f"before the story loads")
    if 'class="brand">' in markup and 'class="brand"></div>' not in markup:
        errs.append("the title wordmark is hardcoded in markup instead of read from GAME.title")
    return errs


if __name__ == "__main__":
    apply()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    errs = audit() + audit_shell(root)
    # the graph must still be the same shape as the source
    if set(S) != set(SRC.S):  errs.append("scene set drifted from the source story")
    if set(G["endings"]) != set(SRC.E): errs.append("ending set drifted from the source story")
    for sid, s in S.items():
        a = ([s["go"]] if "go" in s else []) + [c["go"] for c in s.get("choices", [])]
        b = ([SRC.S[sid]["go"]] if "go" in SRC.S[sid] else []) + \
            [c["go"] for c in SRC.S[sid].get("choices", [])]
        if a != b: errs.append(f"{sid}: links diverged from the source story")

    for e in errs: print("ERROR:", e)
    print(f"scenes={len(S)} endings={len(G['endings'])} "
          f"rewritten: {len(SCENES)} scenes, {len(CODEX)} codex · errors={len(errs)}")
    if errs: sys.exit(1)

    with open(os.path.join(root, "story_blind.json"), "w", encoding="utf-8") as f:
        json.dump(G, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote story_blind.json")
