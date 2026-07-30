#!/usr/bin/env python3
"""Cross-story continuity checks. Both games quote the same figures; they must agree."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(n): return json.load(open(os.path.join(ROOT, n), encoding="utf-8"))
after, before = load("story.json"), load("story_btg.json")
# The blind cut removes early narration mentions, so it is the build where a cold
# nameplate actually surfaces. It must be checked, not assumed to inherit.
blind = load("story_blind.json")

def all_text(g):
    return "\n".join([s["text"] for s in g["scenes"].values()] +
                     [e["text"] + " " + e.get("ep", "") for e in g["endings"].values()] +
                     [c["title"] + " " + c["body"] for c in g["codex"].values()])

errs = []
A, B = all_text(after), all_text(before)

# 1. the ledger figure must be identical wherever it is quoted
LEDGER = "four hundred and ten million"
for name, txt in (("After", A), ("Before", B), ("Blind", all_text(blind))):
    if LEDGER not in txt.lower():
        errs.append(f"{name}: the ledger figure has gone missing")
other = re.findall(r"(?:four hundred and (?:nine|eleven|twelve) million|"
                   r"five hundred million|one billion) (?:people|minds|rows)", (A + B).lower())
if other:
    errs.append(f"a competing ledger figure appears: {set(other)}")

# 2. the harvest must never be equated with the death toll
for name, txt in (("After", A), ("Before", B), ("Blind", all_text(blind))):
    if re.search(rf"{LEDGER} people (?:woke|wake)[^.]*\.\s*the rest (?:did|do) not (?:wake|)", txt.lower()):
        errs.append(f"{name}: '410M woke / the rest did not wake' makes the ledger both "
                    f"the victim count and the survivor count")

# 3. any story that depicts the post-2049 world must account for the collapse
for name, g, txt in (("After", after, A), ("Before", before, B)):
    depicts = "1400" in txt or "population of northern europe" in txt.lower()
    if depicts and "collapse" not in txt.lower():
        errs.append(f"{name}: shows a depopulated Europe without explaining it — "
                    f"the harvest alone cannot account for it")

# 4. the seam: After's opening image must exist in the ending that leads to it
seam = "basement in trondheim"
if seam not in after["scenes"]["p0"]["text"].lower():
    errs.append("After no longer opens on the seam image")
if seam not in before["endings"]["e_seven_months"]["text"].lower():
    errs.append("THE SEVEN MONTHS no longer ends on the seam image")

# 5. dates must line up
for label, needle, txt in (("harvest start", "march", A), ("break date", "october", A),
                           ("harvest start", "march", B), ("break date", "october", B)):
    if needle not in txt.lower():
        errs.append(f"missing {label} ({needle})")

# 6. a nameplate is a speaker. Narration must not wear a character's name —
#    that is what made a flash-forward read as a prisoner predicting 2049.
for name, g in (("After", after), ("Before", before), ("Blind", blind)):
    for sid, sc in g["scenes"].items():
        sp = str(sc.get("sp", ""))
        if sp in ("NARRATION", "", "YOU"): continue
        if "\u201c" not in sc["text"]:
            errs.append(f"{name}/{sid}: nameplate {sp!r} over a scene with no speech")

# 7. nobody standing before 2049 may quote the length of the whole story back at us
# forward-looking only: "we'll spend seventeen years" is prophecy,
# "you have spent sixteen years" is memory
SPAN = re.compile(r"(?:we'll|you'll|will|going to|shall)\s+\w*\s*"
                  r"(?:spend|watch|see|take|be)\b[^.]{0,40}"
                  r"(?:seventeen years|sixteen years|2049)|"
                  r"(?:in|by) 2049", re.I)
for name, g in (("After", after), ("Before", before), ("Blind", blind)):
    for sid, sc in g["scenes"].items():
        if sc.get("ch") in ("aeon", "veto"): continue
        sp = str(sc.get("sp", ""))
        if sp in ("NARRATION", ""): continue
        for q in re.findall(r"\u201c([^\u201d]*)\u201d", sc["text"]):
            if SPAN.search(q):
                errs.append(f"{name}/{sid}: {sp} speaks of the full span or of 2049 "
                            f"before anyone could know it")

# 8. nobody may be named — in prose or, worse, in a choice the player must pick
#    blind — on any path that has not already introduced them.
from collections import deque
CAST = {"Ilya": "Ilya Sen", "Lena": "Lena Orlov", "Mira": "Mira Vale",
        "Kade": "Lucien Kade", "Rhee": "Tomas Rhee", "Arendt": "Selene Arendt",
        "Noor": "Noor", "Peder": "Peder"}
for name, g in (("After", after), ("Before", before), ("Blind", blind)):
    S, E = g["scenes"], g["endings"]
    def succ(sid):
        sc = S[sid]
        return ([sc["go"]] if "go" in sc else []) + [c["go"] for c in sc.get("choices", [])]
    for first, full in CAST.items():
        intro = {sid for sid, sc in S.items() if full in sc["text"]}
        if not intro: continue
        word = re.compile(rf"\b{first}\b")
        uses = {sid for sid, sc in S.items()
                if word.search(sc["text"] + " " +
                               " ".join(c["t"] for c in sc.get("choices", [])))} - intro
        if not uses: continue
        # walk from the start without ever passing through an introduction
        seen, q = {g["start"]}, deque([g["start"]])
        while q:
            n = q.popleft()
            if n in E: continue
            for t in succ(n):
                if t in intro or t in seen or t in E: continue
                seen.add(t); q.append(t)
        for sid in sorted(uses & (seen | {g["start"]})):
            in_choice = any(word.search(c["t"]) for c in S[sid].get("choices", []))
            errs.append(f"{name}/{sid}: names {first} "
                        f"{'in a choice' if in_choice else 'in prose'} on a path "
                        f"where they have never been introduced")

# 9. Aliases. A nameplate introducing a NEW character is ordinary VN grammar and is
#    fine. What is not fine is an entity the player already knows under one name
#    silently appearing under another — the player cannot tell it is the same thing.
#    So: only declared aliases are checked, and the rename must be spoken on every
#    path that reaches the new label.
ALIASES = [("SOLACE", "EREBUS", "Erebus")]
for name, g in (("After", after), ("Before", before), ("Blind", blind)):
    S, E = g["scenes"], g["endings"]
    def succ2(sid):
        sc = S[sid]
        return ([sc["go"]] if "go" in sc else []) + [c["go"] for c in sc.get("choices", [])]
    for old, new, spoken in ALIASES:
        speaks = {sid for sid, sc in S.items()
                  if str(sc.get("sp", "")).split(" //")[0] == new}
        if not speaks: continue
        # a scene explains the rename if the new name is spoken in its prose
        estab = {sid for sid, sc in S.items() if spoken in sc["text"]}
        seen, q = {g["start"]}, deque([g["start"]])
        while q:
            n = q.popleft()
            if n in E: continue
            for t in succ2(n):
                if t in estab or t in seen or t in E: continue
                seen.add(t); q.append(t)
        for sid in sorted((speaks - estab) & seen):
            errs.append(f"{name}/{sid}: the nameplate becomes {new} on a path where "
                        f"nothing has said that {old} is called that")

# 10. Endings that assert a world-fact. An ending may only claim something about the
#     world if every path that reaches it has actually established that thing on
#     screen. THE CLEAN CUT says no relic of Erebus survives anywhere — but the
#     fifteenth fork is a 2047 fact, true on every branch, and the only scene that
#     disposes of it is the sweep. Reaching that ending without the sweep asserted
#     something the player had no way to have made true.
GROUNDED = [
    ("e_clean", {"v_sweep"},
     "claims no copy of Erebus survives, without the lunar package ever being found"),
    ("e_clean_cut", {"v_off2"},
     "destroys both instances, without the lunar package ever being found"),
]
for name, g in (("After", after), ("Before", before), ("Blind", blind)):
    S, E = g["scenes"], g["endings"]
    def succ3(sid):
        sc = S[sid]
        return ([sc["go"]] if "go" in sc else []) + [c["go"] for c in sc.get("choices", [])]
    for eid, required, why in GROUNDED:
        if eid not in E: continue
        missing = required - set(S)
        if missing:
            errs.append(f"{name}: grounding scene(s) {sorted(missing)} for {eid} no longer exist")
            continue
        # walk the graph without ever passing through a grounding scene
        seen, q = {g["start"]}, deque([g["start"]])
        hit = False
        while q:
            n = q.popleft()
            if n in E: continue
            for t in succ3(n):
                if t == eid: hit = True
                if t in required or t in seen or t in E: continue
                seen.add(t); q.append(t)
        if hit:
            errs.append(f"{name}/{eid}: reachable without {sorted(required)} — it {why}")

# 11. A reply may not answer a question the player did not ask. When several
#     different lines converge on one scene, that scene is heard by a player who
#     said exactly one of them. Ilya used to receive three questions and answer
#     with "All three of those are the right question… I don't have an answer to
#     the third one", which reads as though he had the choice list in front of him.
#     Two signals, both cheap: the scene refers to the options as a set, or it
#     quotes one specific option verbatim while the others also lead there.
SET_REF = re.compile(r"\ball (?:three|four|five) (?:of (?:those|them|these)\b|"
                     r"(?:of your )?(?:questions|answers|points)\b)|"
                     r"\b(?:both|either|neither|each) of (?:those|them|these)\b|"
                     r"\bthe (?:first|second|third|fourth|last) (?:one|question|option)\b", re.I)

def phrases(t, n=5):
    """Word n-grams of a choice, stripped of the punctuation the prose may vary."""
    w = re.sub(r"[^\w\s]", " ", t.lower()).split()
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}

for name, g in (("After", after), ("Before", before), ("Blind", blind)):
    S, E = g["scenes"], g["endings"]
    for sid, sc in S.items():
        ch = sc.get("choices") or []
        if len(ch) < 2: continue
        for tgt in {c["go"] for c in ch}:
            lines = {c["t"] for c in ch if c["go"] == tgt}
            # identical text under different stat gates is one line, not a fork
            if len(lines) < 2: continue
            body = S[tgt]["text"] if tgt in S else E.get(tgt, {}).get("text", "")
            m = SET_REF.search(body)
            if m:
                errs.append(f"{name}/{tgt}: answers {len(lines)} converging lines from "
                            f"{sid} as a set ({m.group(0)!r}) — the player said one of them")
            flat = " ".join(re.sub(r"[^\w\s]", " ", body.lower()).split())
            for line in lines:
                others = set().union(*(phrases(o) for o in lines - {line}))
                echo = [p for p in sorted(phrases(line) - others) if p in flat]
                if echo:
                    errs.append(f"{name}/{tgt}: quotes {echo[0]!r} back, which is only "
                                f"in one of the {len(lines)} lines from {sid} that lead here")

for e in errs: print("ERROR:", e)
print(f"continuity: {len(errs)} error(s)")
sys.exit(1 if errs else 0)
