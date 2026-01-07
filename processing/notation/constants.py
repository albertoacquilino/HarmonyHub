#!/usr/bin/env python

"""Notation constants and configuration."""

from typing import Dict

INSTRUMENT_CLEFS: Dict[str, str] = {
    "Trumpet": "treble",
    "Piano": "grand staff",
    "Violin": "treble",
    "Clarinet": "treble",
    "Flute": "treble"
}

INSTRUMENT_STAVES: Dict[str, str] = {
    "Trumpet": "staff",
    "Piano": "grand staff",
    "Violin": "staff",
    "Clarinet": "staff",
    "Flute": "staff"
}

DURATION_MAP: Dict[int, float] = {
    1: 0.5,
    2: 1.0,
    4: 2.0,
    8: 4.0
}

PDF_DPI = 300
PDF_PAGE_SIZE = "A4"
PDF_MARGIN = 0.5

SVG_WIDTH = 1000
SVG_HEIGHT = 600
SVG_DPI = 300

PNG_DPI = 300
PNG_WIDTH = 1000
PNG_HEIGHT = 600

LILYPOND_PAPER_SIZE = "a4"
LILYPOND_MARGIN = 0.5
LILYPOND_FONT_SIZE = 14

STAFF_COLOR = "black"
NOTE_COLOR = "black"
LEDGER_LINE_COLOR = "black"
MEASURE_LINE_COLOR = "black"

KEY_DISPLAY_SIZE = 12
KEY_OFFSET_X = 30
KEY_OFFSET_Y = 0

TIME_DISPLAY_SIZE = 16
TIME_OFFSET_X = 70
TIME_OFFSET_Y = 0
