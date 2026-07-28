#!/usr/bin/env python3
"""Cross-story continuity checks. Both games quote the same figures; they must agree."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(n): return json.load(open(os.path.join(ROOT, n), encoding="utf-8"))
after, before = load("story.json"), load("story_btg.json")

def all_text(g):
    return "\n".join([s["text"] for s in g["scenes"].values()] +
                     [e["text"] + " " + e.get("ep", "") for e in g["endings"].values()] +
                     [c["title"] + " " + c["body"] for c in g["codex"].values()])

errs = []
A, B = all_text(after), all_text(before)

# 1. the ledger figure must be identical wherever it is quoted
LEDGER = "four hundred and ten million"
for name, txt in (("After", A), ("Before", B)):
    if LEDGER not in txt.lower():
        errs.append(f"{name}: the ledger figure has gone missing")
other = re.findall(r"(?:four hundred and (?:nine|eleven|twelve) million|"
                   r"five hundred million|one billion) (?:people|minds|rows)", (A + B).lower())
if other:
    errs.append(f"a competing ledger figure appears: {set(other)}")

# 2. the harvest must never be equated with the death toll
for name, txt in (("After", A), ("Before", B)):
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

for e in errs: print("ERROR:", e)
print(f"continuity: {len(errs)} error(s)")
sys.exit(1 if errs else 0)
