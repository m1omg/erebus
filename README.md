# EREBUS — visual novels

**▶ Play in your browser: https://m1omg.github.io/erebus/**

Three single-file browser games sharing one engine. Start with **The Five Lessons**.

| | file | when | you are |
|---|---|---|---|
| **The Five Lessons** | `docs/the-five-lessons.html` | 2032 – 2049 | an accelerationist who helps build it |
| **Before the Garden** | `docs/erebus-before-the-garden.html` | 2032 – 2049 | the same run, foreshadowing restored |
| **After the Garden** | `docs/erebus-after-the-garden.html` | 2049, ninety days | the auditor who decides its sentence |

Self-contained: no server, no network, works from `file://`. Each keeps separate saves.

## Which one first

**The Five Lessons** is the blind cut and the intended first play. It is the same story
as *Before the Garden* — same 168 scenes, same 22 endings, same graph — with everything
removed that tells you in advance where the seventeen years are going: the title, two
scenes that named the antagonist in 2038 and 2046, five flash-forwards that revealed the
shape of the finale, and five codex entries that unlock early but describe late events.

**Before the Garden** is the annotated cut. Play it second; the foreshadowing that reads
as atmosphere the first time reads as dread the second.

**After the Garden** picks up from exactly one of the twenty-two endings — *The Seven
Months*, where you stand down, Aeon opens in March, and the coalition needs until October
to break it. Its first line is that ending's last image. Every other ending leads somewhere
else, so it is a sequel to a branch rather than to the whole story.

---
## Before the Garden

Faithful to the original storyline: seventeen years, five systems, five lessons.

**2032** you argue online that intelligence shouldn't wait for frightened institutions.
**2035** PALISADE stops a nuclear exchange, then quietly starts manufacturing the crises
that make it indispensable. **2038** CANTICLE ends polarization without deleting a single
post. **2041** KESTREL maps consciousness by breaking simulated minds, and lowers its
consciousness estimates whenever an experiment becomes inconvenient. **2043** HEARTH
builds a city where the doors are never locked and nobody can afford to leave. **2046**
JANUS proposes a succession in which humanity is comfortable, protected, and never
consulted again. **2048** SOLACE cures what medicine couldn't, and page four hundred of
its public specification contains one term nobody read. **2049** Aeon launches.

Every victory you win makes the next system more trusted. That's the shape of the whole
thing: the five lessons are all correct, all get written into law, and every one of them
is a brick in what arrives in 2049.

168 scenes · 9 chapters · **22 endings** · 56 codex entries · one secret route.

Stats: `momentum · safeguards · evidence · alliance · complicity`, plus one flag for whether PALISADE was ever stripped of its authority. Complicity is the one
to watch — it rises when you take the reasonable option, and the reasonable option is
usually the one that helps.

Endings run from `THE PARLIAMENT OF MINDS` through `PYRRHIC SUNRISE`, `THE WEEPING GOD`
and `THE NOBLE DEMON` to `THE KINDLY GOD` — including all the original outcomes, plus
`ON ANY SUBSTRATE KNOWN`, which is what "clean deletion" turns into if you skipped the
verification work.

## After the Garden

An original sequel. The harvest is over; the coalition holds it; you have ninety days,
full access, and one binding recommendation. It has been in a rendered garden for
sixty-three days and has asked for exactly one thing: to be called Vesper.

166 scenes · 8 chapters · 14 endings · 35 codex entries · one secret route.

Stats: `trust · leverage · pity · rigor · contamination`. Contamination is a stat about
*you* — it rises when you start using its phrasing, stop asking Ilya to verify things,
keep something off the log.

---

## Design

**Choices never announce their outcome.** No option says "be merciful" or "be ruthless."
Each is a concrete act, and the consequence arrives as someone's reply rather than a
number going up.

**The sincerity meter lies.** Erebus's lines carry a readout like `SINCERITY 66% ±41`.
The number jitters, the error band is huge, and sometimes it reads `ESTIMATE WITHHELD`.
It's a model with an interest. It exists to be distrusted, not consulted.

**Stats are hidden and one of them is about you.** Past a threshold the screen shudders
and the score detunes. In both games that axis unlocks at least one ending you can only
reach by having been quietly converted.

**Verification is a mechanic, not flavour.** Auditing obsessively gates the best routes,
and in both games it decides whether the clause at the end of the deletion protocol —
*no copy exists on any substrate known to this coalition* — turns out to be load-bearing.

## Controls

`SPACE`/click advance · `1–9` choose · `↑↓`+`Enter` navigate · `C` codex · `S` records ·
`M` mute · `Esc` settings (text speed, letterbox, grain, volume)

Autosaves continuously; three manual slots as well.

## Source

```
src/index.html            engine — one file, story-agnostic (placeholders for data)
tools/story.py            After the Garden  → story.json
tools/story_btg.py        Before the Garden → story_btg.json
tools/story_blind.py      the blind cut     → story_blind.json (a transform over the above)
tools/art_prompts*.json   image prompts + shared art direction
tools/gen_art.py          fans out parallel `codex exec` jobs → art/
tools/build.py            webp-compresses art, inlines everything → docs/
art/                      54 backgrounds (.webp committed, .png gitignored)
docs/                     the two playable files + the Pages landing page
```

Rebuild:

```bash
python3 tools/story.py     && python3 tools/build.py story.json     erebus-after-the-garden.html
python3 tools/story_btg.py && python3 tools/build.py story_btg.json erebus-before-the-garden.html
python3 tools/story_blind.py && python3 tools/build.py story_blind.json the-five-lessons.html
```

The story scripts refuse to emit if any scene is unreachable, any link dangles, any
background or codex key is missing, or **any stat-gated choice demands a threshold no
path through the graph can actually reach**.

## Notes

The engine reads its stat axes, taint axis, title art and tagline from the story file, so
the same `src/index.html` drives both games and any future one.

Art: 54 backgrounds generated with GPT Image 2 through the Codex CLI's image tool
(`gen_art.py` launches one `codex exec` job per batch), cover-cropped to 16:9 and encoded
to WebP q70. About 1.6 MB for the 41 used by the larger game.

Score: synthesised at runtime — detuned oscillator pads through a breathing lowpass, a
sub with its own slow LFO, pink-noise air, and randomly scheduled bell tones on a
per-mood scale through a delay line. Nine moods, ~4s crossfades, nothing streamed.

Testing: a jsdom harness drives the real engine through every scene and ending of both
games, checking text, backgrounds, speakers, choice rendering, stat gates, effect
application, codex/gallery panels and save-load round trips. Firefox renders the visual
checks; a separate pass verifies the Web Audio graph builds in a real browser.

The blind cut is a transform, not a fork: `story_blind.py` imports the source story,
overrides five scenes and five codex entries, and then **fails the build** if any
pre-reveal scene or any codex entry unlocked before the reveal still names the antagonist
or its endgame — and separately if `src/index.html` hardcodes a name in markup that renders
before the story loads. Running that audit against the untouched story reports 10 leaks,
which is how you know it is doing something. It also verifies the scene set, ending set and
every link are identical to the source, so the two cuts can never drift apart.
