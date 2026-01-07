<div align="center">
  <img width="561" height="212" alt="image" src="https://github.com/user-attachments/assets/f9a451aa-8237-4aa6-a335-df192f5682a7" />

</div>

<h1 align="center">GSoC 2025(INCF)</h1>


## **Project Title:** *HarmonyHub: Using Generative AI for Adaptive Learning in Music CLI Version*  
**Organization:** INCF  
**Contributor:** **Priyanshu Tiwari**  
**Mentors:** Alberto Acquilino • Mirko D'Andrea • Keerthi Reddy Kambham • Thrun • Oscar  
**Hugging Face Repo:** [🔗 Music LLM](https://huggingface.co/spaces/SHIKARICHACHA/adaptive-music-exercise-generator)

---

## 📜 **Executive Summary**

**HarmonyHub** is an **AI-driven adaptive music education platform** that leverages the **Mistral LLM API** to generate **personalized, rhythmically precise, and melodically coherent** practice exercises in real time. Designed for **students, educators, and self-taught musicians**, the system dynamically adapts to user-defined parameters:

- 🎹 **Instrument**: Piano, Violin, Trumpet, Clarinet, Flute
- 🔤 **Difficulty Level**: Beginner, Intermediate, Advanced
- ⏱ **Time Signature & Key**: e.g., 4/4 in C Major, 6/8 in A Minor
- 🎯 **Practice Focus**: Rhythmic, Melodic, Technical, Expressive, Sight-Reading, Improvisation
- 🎼 **Rhythmic Complexity**: Basic, Syncopated, Polyrhythmic

Generated exercises are delivered in **MIDI**, **MP3**, and **JSON** formats, accompanied by:
- Real-time **sheet music visualization** via VexFlow
- Interactive **AI music theory assistant**
- No-code **Gradio interface** for instant access

HarmonyHub bridges **generative AI** and **music cognition**, offering an intelligent, accessible, and scalable tool for modern music pedagogy.

## Project Structure

The project has been refactored into a modular structure:

```
├── lib/                    # Core music generation functionality
│   └── music_generation/   # Music generation modules
│       ├── constants.py    # Configuration and constants
│       ├── generator.py    # Exercise generation logic
│       └── theory.py       # Music theory helpers
├── processing/             # Processing modules
│   ├── audio/              # Audio processing
│   │   └── converter.py    # MIDI to audio conversion
│   ├── midi/               # MIDI processing
│   │   └── converter.py    # JSON to MIDI conversion
│   └── visualization/      # Visualization tools
│       └── visualizer.py   # Piano roll visualization
├── tests/                  # Test suite
│   ├── lib/                # Tests for lib modules
│   └── processing/         # Tests for processing modules
├── cli.py                  # Command-line interface
└── requirements.txt        # Project dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Generate a music exercise

```bash
python cli.py generate --instrument Trumpet --level Intermediate --key "C Major" --time-signature "4/4" --measures 4 --output-format all
```

### Generate a metronome track

```bash
python cli.py metronome --tempo 60 --time-signature "4/4" --measures 4
```

### Convert a JSON exercise to MIDI or MP3

```bash
python cli.py convert --input-file exercise.json --output-format mp3 --instrument Piano
```

### Display available options

```bash
python cli.py info
```

## Module Overview

### lib/music_generation

- **constants.py**: Configuration values and constants
- **generator.py**: Core music generation logic using LLM
- **theory.py**: Music theory helpers for note conversion

### processing/midi

- **converter.py**: Convert JSON note data to MIDI files

### processing/audio

- **converter.py**: Convert MIDI files to MP3 audio

### processing/visualization

- **visualizer.py**: Generate piano roll visualizations

### processing/notation

- **constants.py**: Configuration for sheet music rendering (clefs, durations, PDF/SVG settings)
- **sheet_music.py**: Convert JSON exercises to music21 Score objects and render to PDF/SVG/PNG

## Sheet Music Generation

HarmonyHub now includes professional sheet music generation using the **music21** library with optional **LilyPond** backend for high-quality PDF output.

### Features

- **Multiple Output Formats**: PDF, SVG, PNG
- **Professional Quality**: Uses LilyPond when available, falls back to music21
- **Automatic Clef Selection**: Correct clef per instrument (treble for wind/strings, grand staff for piano)
- **Full Notation Support**: Key signatures, time signatures, tempos, correct note durations
- **Error Handling**: Graceful degradation if LilyPond unavailable

### Usage Examples

Generate exercise with sheet music:

```bash
# Generate PDF sheet music
python cli.py generate --instrument Trumpet --level Intermediate --output-format pdf

# Generate all formats (JSON, MIDI, MP3, PDF, SVG, PNG)
python cli.py generate --instrument Piano --output-format all

# Convert existing JSON to PDF
python cli.py convert --input-file exercise.json --output-format pdf
```

## Testing

Run the test suite:

```bash
python -m unittest discover tests
```

For sheet music tests specifically:

```bash
python -m pytest tests/processing/test_sheet_music.py -v
```

## Error Handling

The application is designed to fail gracefully when errors occur, with no automatic fallbacks. Error messages are displayed to help diagnose issues.



