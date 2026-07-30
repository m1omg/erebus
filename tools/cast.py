#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Speaker → portrait mapping, shared by all three stories.

Only the *mapping* lives here. Whether any portrait is actually shipped is
decided at build time (`build.py --chars`), so the same story JSON drives both
the plain and the illustrated cut.

  key       which portrait in chars/
  byChapter overrides by chapter id — the four people who are on screen across
            all seventeen years get a second portrait rather than one face that
            is wrong at both ends of the story
  hideOn    backgrounds where the entity already fills the frame; a portrait of
            SOLACE in front of the SOLACE avatar is the same thing twice
"""

# 2032 · 2035 · 2038 — before the ageing split at KESTREL (2041)
EARLY = ["spark", "palisade", "canticle"]

# Kade is the exception, and not because of his age. His second portrait is not
# "older Kade", it is *detained* Kade — no tie, no belt, a room he cannot leave.
# In 2041 he is still the principal investigator who is delighted to show you
# around, so his first portrait has to survive KESTREL.
KADE_EARLY = EARLY + ["kestrel"]


def _aged(base, early=None):
    return {"key": base, "byChapter": {c: base + "_young" for c in (early or EARLY)}}


HUMANS = {
    "MIRA VALE":       _aged("mira"),
    "ILYA SEN":        _aged("ilya"),
    "LENA ORLOV":      _aged("lena"),
    "LUCIEN KADE":     _aged("kade", KADE_EARLY),
    "TOMAS RHEE":      {"key": "rhee"},
    "DIRECTOR ARENDT": {"key": "arendt"},
    "NOOR":            {"key": "noor"},
    "RESIDENT":        {"key": "resident"},
}

SYSTEMS = {
    "PALISADE":   {"key": "palisade"},
    "CANTICLE":   {"key": "canticle"},
    "KESTREL":    {"key": "kestrel"},
    "HEARTH":     {"key": "hearth"},
    "JANUS":      {"key": "janus"},
    "SUBJECT 14": {"key": "subject14"},
    "SOLACE":     {"key": "solace", "hideOn": ["solace_avatar"]},
    "EREBUS":     {"key": "erebus", "hideOn": ["solace_avatar", "erebus_avatar"]},
    "VESPER":     {"key": "vesper", "hideOn": ["erebus_avatar"]},
}

# NARRATION and YOU deliberately have no portrait: one is nobody and the other
# is the player, and drawing the player would answer a question the game spends
# nine chapters refusing to answer.
MAP = {**HUMANS, **SYSTEMS}


def chars_for(speakers):
    """Trim the shared map to the speakers a given story actually uses."""
    base = {sp.split(" //")[0].strip() for sp in speakers if sp}
    return {"map": {k: v for k, v in MAP.items() if k in base}}
