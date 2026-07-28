#!/usr/bin/env python3
"""Launch one codex exec job per batch to render backgrounds into art/."""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]
spec_file = "tools/art_prompts.json"
if args and args[0].endswith(".json"):
    spec_file = args.pop(0)
spec = json.load(open(os.path.join(ROOT, spec_file), encoding="utf-8"))
style = spec["style"]
only = args or None

os.makedirs(os.path.join(ROOT, "art"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "tools/logs"), exist_ok=True)

for batch in spec["batches"]:
    if only and batch["name"] not in only:
        continue
    todo = [im for im in batch["images"]
            if not os.path.exists(os.path.join(ROOT, "art", im["file"]))]
    if not todo:
        print("skip (done):", batch["name"])
        continue
    lines = [
        "You have a built-in image generation tool. Use it to create the images listed below.",
        "Generate them ONE AT A TIME. After each generation, copy the produced PNG from your",
        "generated-images directory to the target path under ./art/ using `cp`. Do not edit,",
        "crop or re-encode. Do not write any other files. Do not ask questions; just do it.",
        "",
        "SHARED ART DIRECTION — append to every prompt verbatim:",
        style,
        "",
        "IMAGES:",
    ]
    for i, im in enumerate(todo, 1):
        lines.append(f"{i}. target ./art/{im['file']}\n   prompt: {im['prompt']}")
    lines += ["", "When all are copied, run `ls -la ./art` and stop."]
    prompt = "\n".join(lines)

    log = open(os.path.join(ROOT, "tools/logs", f"{batch['name']}.log"), "w")
    subprocess.Popen(
        ["codex", "exec", "--sandbox", "workspace-write",
         "--skip-git-repo-check", prompt],
        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print("launched:", batch["name"], f"({len(todo)} images)")
