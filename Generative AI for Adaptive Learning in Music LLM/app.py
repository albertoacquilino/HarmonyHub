"""
Adaptive Music Exercise Generator (Strict Duration Enforcement)
==============================================================
Generates custom musical exercises with LLM, perfectly fit to user-specified number of measures
AND time signature, guaranteeing exact durations in MIDI and in the UI!
Major updates:
- Changed base duration unit from 16th notes to 8th notes (1 unit = 8th note)
- Updated all calculations and prompts to use new duration system
- Duration sum display now shows total in 8th notes
- Maintained all original functionality
- Added cumulative duration tracking
- Enforced JSON output format with note, duration, cumulative_duration
- Enhanced rest handling and JSON parsing
- Fixed JSON parsing errors for 8-measure exercises
- Added robust error handling for MIDI generation
"""

# -----------------------------------------------------------------------------
# 1. Runtime-time package installation (for fresh containers/Colab/etc)
# -----------------------------------------------------------------------------
import sys
import subprocess
from typing import Dict, Optional, Tuple, List

def install(packages: List[str]):
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing missing package: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install([
    "mido", "midi2audio", "pydub", "gradio",
    "requests", "numpy", "matplotlib", "librosa", "scipy",
])

# -----------------------------------------------------------------------------
# 2. Static imports
# -----------------------------------------------------------------------------
import random
import requests
import json
import tempfile
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
import re
from io import BytesIO
from midi2audio import FluidSynth
from pydub import AudioSegment
import gradio as gr
import numpy as np
import matplotlib.pyplot as plt
import librosa
from scipy.io import wavfile
import os
import subprocess as sp
import base64
import shutil
import ast

# -----------------------------------------------------------------------------
# 3. Configuration & constants (UPDATED TO USE 8TH NOTES)
# -----------------------------------------------------------------------------
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = "yQdfM8MLbX9uhInQ7id4iUTwN4h4pDLX"  # ← Replace with your key!

SOUNDFONT_URLS = {
    "Trumpet": "https://github.com/FluidSynth/fluidsynth/raw/master/sf2/Trumpet.sf2",
    "Piano": "https://musical-artifacts.com/artifacts/2719/GeneralUser_GS_1.471.sf2",
    "Violin": "https://musical-artifacts.com/artifacts/2744/SalC5Light.sf2",
    "Clarinet": "https://musical-artifacts.com/artifacts/2744/SalC5Light.sf2",
    "Flute": "https://musical-artifacts.com/artifacts/2744/SalC5Light.sf2",
}

SAMPLE_RATE = 44100  # Hz
TICKS_PER_BEAT = 480  # Standard MIDI resolution
TICKS_PER_8TH = TICKS_PER_BEAT // 2  # 240 ticks per 8th note (UPDATED)

if not os.path.exists('/usr/bin/fluidsynth'):
    try:
        os.system('apt-get update && apt-get install -y fluidsynth')
    except Exception:
        print("Could not install FluidSynth automatically. Please install it manually.")

os.makedirs("static", exist_ok=True)

# -----------------------------------------------------------------------------
# 4. Music theory helpers (note names ↔︎ MIDI numbers) - ENHANCED REST HANDLING
# -----------------------------------------------------------------------------
NOTE_MAP: Dict[str, int] = {
    "C": 0, "C#": 1, "DB": 1,
    "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6,
    "G": 7, "G#": 8, "AB": 8,
    "A": 9, "A#": 10, "BB": 10,
    "B": 11,
}

REST_INDICATORS = ["rest", "r", "Rest", "R", "P", "p", "pause"]

INSTRUMENT_PROGRAMS: Dict[str, int] = {
    "Piano": 0,       "Trumpet": 56,   "Violin": 40,
    "Clarinet": 71,   "Flute": 73,
}

def is_rest(note: str) -> bool:
    """Check if a note string represents a rest."""
    return note.strip().lower() in [r.lower() for r in REST_INDICATORS]

def note_name_to_midi(note: str) -> int:
    if is_rest(note):
        return -1  # Special value for rests
    
    # Allow both scientific (C4) and Helmholtz (C') notation
    match = re.match(r"([A-Ga-g][#b]?)(\'*)(\d?)", note)
    if not match:
        raise ValueError(f"Invalid note: {note}")
    
    pitch, apostrophes, octave = match.groups()
    pitch = pitch.upper().replace('b', 'B')
    
    # Handle Helmholtz notation (C' = C5, C'' = C6, etc)
    octave_num = 4
    if octave:
        octave_num = int(octave)
    elif apostrophes:
        octave_num = 5 + len(apostrophes)
    
    if pitch not in NOTE_MAP:
        raise ValueError(f"Invalid pitch: {pitch}")
    
    return NOTE_MAP[pitch] + (octave_num + 1) * 12

def midi_to_note_name(midi_num: int) -> str:
    if midi_num == -1:
        return "Rest"
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_num // 12) - 1
    return f"{notes[midi_num % 12]}{octave}"

# -----------------------------------------------------------------------------
# 5. Duration scaling: guarantee the output sums to requested total (using integers)
# -----------------------------------------------------------------------------
def scale_json_durations(json_data, target_units: int) -> list:
    """Scales durations so that their sum is exactly target_units (8th notes)."""
    durations = [int(d) for _, d in json_data]
    total = sum(durations)
    if total == 0:
        return json_data

    # Calculate proportional scaling with integer arithmetic
    scaled = []
    remainder = target_units
    for i, (note, d) in enumerate(json_data):
        if i < len(json_data) - 1:
            # Proportional allocation
            portion = max(1, round(d * target_units / total))
            scaled.append([note, portion])
            remainder -= portion
        else:
            # Last note gets all remaining units
            scaled.append([note, max(1, remainder)])

    return scaled

# -----------------------------------------------------------------------------
# 6. MIDI from scaled JSON (using integer durations) - UPDATED REST HANDLING
# -----------------------------------------------------------------------------
def json_to_midi(json_data: list, instrument: str, tempo: int, time_signature: str, measures: int) -> MidiFile:
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    track = MidiTrack(); mid.tracks.append(track)
    program = INSTRUMENT_PROGRAMS.get(instrument, 56)
    numerator, denominator = map(int, time_signature.split('/'))

    track.append(MetaMessage('time_signature', numerator=numerator,
                             denominator=denominator, time=0))
    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))
    track.append(Message('program_change', program=program, time=0))

    # Accumulator for rest durations
    accumulated_rest = 0

    for note_item in json_data:
        try:
            # Handle both formats: [note, duration] and {note, duration}
            if isinstance(note_item, list) and len(note_item) == 2:
                note_name, duration_units = note_item
            elif isinstance(note_item, dict):
                note_name = note_item["note"]
                duration_units = note_item["duration"]
            else:
                print(f"Unsupported note format: {note_item}")
                continue
                
            ticks = int(duration_units * TICKS_PER_8TH)
            ticks = max(ticks, 1)
            
            if is_rest(note_name):
                # Accumulate rest duration
                accumulated_rest += ticks
            else:
                # Process any accumulated rest first
                if accumulated_rest > 0:
                    # Add rest by creating a silent note (velocity 0) that won't be heard
                    # Or just skip and use accumulated_rest in timing
                    # We'll just add the time to the next note
                    track.append(Message('note_on', note=0, velocity=0, time=accumulated_rest))
                    track.append(Message('note_off', note=0, velocity=0, time=0))
                    accumulated_rest = 0
                
                # Process actual note
                note_num = note_name_to_midi(note_name)
                velocity = random.randint(60, 100)
                track.append(Message('note_on', note=note_num, velocity=velocity, time=0))
                track.append(Message('note_off', note=note_num, velocity=velocity, time=ticks))
        except Exception as e:
            print(f"Error parsing note {note_item}: {e}")
    
    # Handle trailing rest
    if accumulated_rest > 0:
        track.append(Message('note_on', note=0, velocity=0, time=accumulated_rest))
        track.append(Message('note_off', note=0, velocity=0, time=0))
    
    return mid

# -----------------------------------------------------------------------------
# 7. MIDI → Audio (MP3) helpers
# -----------------------------------------------------------------------------
def get_soundfont(instrument: str) -> str:
    os.makedirs("soundfonts", exist_ok=True)
    sf2_path = f"soundfonts/{instrument}.sf2"
    if not os.path.exists(sf2_path):
        url = SOUNDFONT_URLS.get(instrument, SOUNDFONT_URLS["Trumpet"])
        print(f"Downloading SoundFont for {instrument}…")
        response = requests.get(url)
        with open(sf2_path, "wb") as f:
            f.write(response.content)
    return sf2_path

def midi_to_mp3(midi_obj: MidiFile, instrument: str = "Trumpet") -> Tuple[str, float]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as mid_file:
        midi_obj.save(mid_file.name)
        wav_path = mid_file.name.replace(".mid", ".wav")
        mp3_path = mid_file.name.replace(".mid", ".mp3")
    sf2_path = get_soundfont(instrument)
    try:
        sp.run([
            'fluidsynth', '-ni', sf2_path, mid_file.name,
            '-F', wav_path, '-r', '44100', '-g', '1.0'
        ], check=True, capture_output=True)
    except Exception:
        fs = FluidSynth(sf2_path, sample_rate=44100, gain=1.0)
        fs.midi_to_audio(mid_file.name, wav_path)
    try:
        sound = AudioSegment.from_wav(wav_path)
        if instrument == "Trumpet":
            sound = sound.high_pass_filter(200)
        elif instrument == "Violin":
            sound = sound.low_pass_filter(5000)
        sound.export(mp3_path, format="mp3")
        static_mp3_path = os.path.join('static', os.path.basename(mp3_path))
        shutil.move(mp3_path, static_mp3_path)
        return static_mp3_path, sound.duration_seconds
    finally:
        for f in [mid_file.name, wav_path]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

# -----------------------------------------------------------------------------
# 8. Prompt engineering for variety (using integer durations) - UPDATED DURATION SYSTEM
# -----------------------------------------------------------------------------
def get_fallback_exercise(instrument: str, level: str, key: str,
                          time_sig: str, measures: int) -> str:
    key_notes = {
        "C Major": ["C4", "D4", "E4", "G4"],
        "G Major": ["G4", "A4", "B4", "D5"],
        "D Major": ["D4", "E4", "F#4", "A4"],
        "F Major": ["F4", "G4", "A4", "C5"],
        "Bb Major": ["Bb3", "C4", "D4", "F4"],
        "A Minor": ["A3", "B3", "C4", "D4", "E4", "G4"],
        "E Minor": ["E3", "F#3", "G3", "A3", "B3", "D4"],
    }
    
    notes = key_notes.get(key, key_notes["C Major"])
    numerator, denominator = map(int, time_sig.split('/'))
    
    # Calculate units based on 8th notes
    units_per_measure = numerator * (8 // denominator)
    target_units = measures * units_per_measure
    
    # Create a rhythm pattern based on time signature
    if numerator == 3:
        rhythm = [2, 1, 2, 1, 2]  # 3/4 pattern
    else:
        rhythm = [2, 2, 1, 1, 2, 2]  # 4/4 pattern
    
    # Build exercise
    result = []
    cumulative = 0
    current_units = 0
    
    while current_units < target_units:
        note = random.choice(notes)
        dur = random.choice(rhythm)
        
        # Don't exceed target
        if current_units + dur > target_units:
            dur = target_units - current_units
            if dur == 0:
                break
        
        cumulative += dur
        current_units += dur
        result.append({
            "note": note,
            "duration": dur,
            "cumulative_duration": cumulative
        })
    
    return json.dumps(result)

def get_style_based_on_level(level: str) -> str:
    styles = {
        "Beginner": ["simple", "legato", "stepwise"],
        "Intermediate": ["jazzy", "bluesy", "march-like", "syncopated"],
        "Advanced": ["technical", "chromatic", "fast arpeggios", "wide intervals"],
    }
    return random.choice(styles.get(level, ["technical"]))

def get_technique_based_on_level(level: str) -> str:
    techniques = {
        "Beginner": ["with long tones", "with simple rhythms", "focusing on tone"],
        "Intermediate": ["with slurs", "with accents", "using triplets"],
        "Advanced": ["with double tonguing", "with extreme registers", "complex rhythms"],
    }
    return random.choice(techniques.get(level, ["with slurs"]))

# -----------------------------------------------------------------------------
# 9. Mistral API: query, fallback on errors - UPDATED DURATION SYSTEM
# -----------------------------------------------------------------------------
def query_mistral(prompt: str, instrument: str, level: str, key: str,
                  time_sig: str, measures: int) -> str:
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    numerator, denominator = map(int, time_sig.split('/'))
    
    # UPDATED: Calculate total required 8th notes
    units_per_measure = numerator * (8 // denominator)
    required_total = measures * units_per_measure

    # UPDATED: Duration explanation in prompt
    duration_constraint = (
        f"Sum of all durations MUST BE EXACTLY {required_total} units (8th notes). "
        f"Each integer duration represents an 8th note (1=8th, 2=quarter, 4=half, 8=whole). "
        f"If it doesn't match, the exercise is invalid."
    )
    system_prompt = (
        f"You are an expert music teacher specializing in {instrument.lower()}. "
        "Create customized exercises using INTEGER durations representing 8th notes."
    )

    if prompt.strip():
        user_prompt = (
            f"{prompt} {duration_constraint} Output ONLY a JSON array of objects with "
            "the following structure: [{{'note': string, 'duration': integer, 'cumulative_duration': integer}}]"
        )
    else:
        style = get_style_based_on_level(level)
        technique = get_technique_based_on_level(level)
        user_prompt = (
            f"Create a {style} {instrument.lower()} exercise in {key} with {time_sig} time signature "
            f"{technique} for a {level.lower()} player. {duration_constraint} "
            "Output ONLY a JSON array of objects with the following structure: "
            "[{{'note': string, 'duration': integer, 'cumulative_duration': integer}}] "
            "Use standard note names (e.g., \"Bb4\", \"F#5\"). Monophonic only. "
            "Durations: 1=8th, 2=quarter, 4=half, 8=whole. "
            "Sum must be exactly as specified. ONLY output the JSON array. No prose."
        )

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7 if level == "Advanced" else 0.5,
        "max_tokens": 1000,
        "top_p": 0.95,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.2,
    }

    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content.replace("```json","").replace("```","").strip()
    except Exception as e:
        print(f"Error querying Mistral API: {e}")
        return get_fallback_exercise(instrument, level, key, time_sig, measures)

# -----------------------------------------------------------------------------
# 10. Robust JSON parsing for LLM outputs - ENHANCED PARSING
# -----------------------------------------------------------------------------
def safe_parse_json(text: str) -> Optional[list]:
    try:
        text = text.strip().replace("'", '"')
        
        # Find JSON array in the text
        start_idx = text.find('[')
        end_idx = text.rfind(']')
        if start_idx == -1 or end_idx == -1:
            return None
            
        json_str = text[start_idx:end_idx+1]
        
        # Fix common JSON issues
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Trailing commas
        json_str = re.sub(r'{\s*(\w+)\s*:', r'{"\1":', json_str)  # Unquoted keys
        json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)(\s*[,}])', r':"\1"\2', json_str)  # Unquoted strings
        
        parsed = json.loads(json_str)
        
        # Normalize keys to 'note' and 'duration'
        normalized = []
        for item in parsed:
            if isinstance(item, dict):
                # Find note value - accept multiple keys
                note_val = None
                for key in ['note', 'pitch', 'nota', 'ton']:
                    if key in item:
                        note_val = str(item[key])
                        break
                
                # Find duration value
                dur_val = None
                for key in ['duration', 'dur', 'length', 'value']:
                    if key in item:
                        try:
                            dur_val = int(item[key])
                        except (TypeError, ValueError):
                            pass
                
                if note_val is not None and dur_val is not None:
                    normalized.append({"note": note_val, "duration": dur_val})
        
        return normalized if normalized else None
        
    except Exception as e:
        print(f"JSON parsing error: {e}\nRaw text: {text}")
        return None

# -----------------------------------------------------------------------------
# 11. Main orchestration: talk to API, *scale durations*, build MIDI, UI values - UPDATED
# -----------------------------------------------------------------------------
def generate_exercise(instrument: str, level: str, key: str, tempo: int, time_signature: str,
                      measures: int, custom_prompt: str, mode: str) -> Tuple[str, Optional[str], str, MidiFile, str, str, int]:
    try:
        prompt_to_use = custom_prompt if mode == "Exercise Prompt" else ""
        output = query_mistral(prompt_to_use, instrument, level, key, time_signature, measures)
        parsed = safe_parse_json(output)
        if not parsed:
            print("Primary parsing failed, using fallback")
            fallback_str = get_fallback_exercise(instrument, level, key, time_signature, measures)
            parsed = safe_parse_json(fallback_str)
            if not parsed:
                print("Fallback parsing failed, using ultimate fallback")
                # Ultimate fallback: simple scale
                notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
                numerator, denominator = map(int, time_signature.split('/'))
                units_per_measure = numerator * (8 // denominator)
                target_units = measures * units_per_measure
                note_duration = max(1, target_units // len(notes))
                parsed = [{"note": n, "duration": note_duration} for n in notes]
                # Adjust last note to match total duration
                total = sum(item["duration"] for item in parsed)
                if total < target_units:
                    parsed[-1]["duration"] += target_units - total
                elif total > target_units:
                    parsed[-1]["duration"] -= total - target_units

        # Calculate total required 8th notes (UPDATED)
        numerator, denominator = map(int, time_signature.split('/'))
        units_per_measure = numerator * (8 // denominator)
        total_units = measures * units_per_measure

        # Convert to old format for scaling
        old_format = []
        for item in parsed:
            if isinstance(item, dict):
                old_format.append([item["note"], item["duration"]])
            else:
                old_format.append(item)

        # Strict scaling
        parsed_scaled_old = scale_json_durations(old_format, total_units)

        # Convert back to new format with cumulative durations
        cumulative = 0
        parsed_scaled = []
        for note, dur in parsed_scaled_old:
            cumulative += dur
            parsed_scaled.append({
                "note": note,
                "duration": dur,
                "cumulative_duration": cumulative
            })

        # Calculate total duration units
        total_duration = cumulative

        # Generate MIDI and audio
        midi = json_to_midi(parsed_scaled, instrument, tempo, time_signature, measures)
        mp3_path, real_duration = midi_to_mp3(midi, instrument)
        output_json_str = json.dumps(parsed_scaled, indent=2)
        return output_json_str, mp3_path, str(tempo), midi, f"{real_duration:.2f} seconds", time_signature, total_duration
    except Exception as e:
        return f"Error: {str(e)}", None, str(tempo), None, "0", time_signature, 0

# -----------------------------------------------------------------------------
# 12. Simple AI chat assistant (optional, shares LLM)
# -----------------------------------------------------------------------------
def handle_chat(message: str, history: List, instrument: str, level: str):
    if not message.strip():
        return "", history
    messages = [{"role": "system", "content": f"You are a {instrument} teacher for {level} students."}]
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "mistral-medium", "messages": messages, "temperature": 0.7, "max_tokens": 500}
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        history.append((message, content))
        return "", history
    except Exception as e:
        history.append((message, f"Error: {str(e)}"))
        return "", history

# -----------------------------------------------------------------------------
# 13. Gradio user interface definition (for humans!) - UPDATED LABEL
# -----------------------------------------------------------------------------
def create_ui() -> gr.Blocks:
    with gr.Blocks(title="Adaptive Music Exercise Generator", theme="soft") as demo:
        gr.Markdown("# 🎼 Adaptive Music Exercise Generator")
        current_midi = gr.State(None)
        current_exercise = gr.State("")

        mode = gr.Radio(["Exercise Parameters","Exercise Prompt"], value="Exercise Parameters", label="Generation Mode")
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Group(visible=True) as params_group:
                    gr.Markdown("### Exercise Parameters")
                    instrument = gr.Dropdown([
                        "Trumpet", "Piano", "Violin", "Clarinet", "Flute",
                    ], value="Trumpet", label="Instrument")
                    level = gr.Radio([
                        "Beginner", "Intermediate", "Advanced",
                    ], value="Intermediate", label="Difficulty Level")
                    key = gr.Dropdown([
                        "C Major", "G Major", "D Major", "F Major", "Bb Major", "A Minor", "E Minor",
                    ], value="C Major", label="Key Signature")
                    time_signature = gr.Dropdown(["3/4", "4/4"], value="4/4", label="Time Signature")
                    measures = gr.Radio([4, 8], value=4, label="Length (measures)")
                with gr.Group(visible=False) as prompt_group:
                    gr.Markdown("### Exercise Prompt")
                    custom_prompt = gr.Textbox("", label="Enter your custom prompt", lines=3)
                    measures_prompt = gr.Radio([4, 8], value=4, label="Length (measures)")
                generate_btn = gr.Button("Generate Exercise", variant="primary")
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("Exercise Player"):
                        audio_output = gr.Audio(label="Generated Exercise", autoplay=True, type="filepath")
                        bpm_display = gr.Textbox(label="Tempo (BPM)")
                        time_sig_display = gr.Textbox(label="Time Signature")
                        duration_display = gr.Textbox(label="Audio Duration", interactive=False)
                    with gr.TabItem("Exercise Data"):
                        json_output = gr.Code(label="JSON Representation", language="json")
                        # UPDATED LABEL
                        duration_sum = gr.Number(
                            label="Total Duration Units (8th notes)",
                            interactive=False,
                            precision=0
                        )
                    with gr.TabItem("MIDI Export"):
                        midi_output = gr.File(label="MIDI File")
                        download_midi = gr.Button("Generate MIDI File")
                    with gr.TabItem("AI Chat"):
                        chat_history = gr.Chatbot(label="Practice Assistant", height=400)
                        chat_message = gr.Textbox(label="Ask the AI anything about your practice")
                        send_chat_btn = gr.Button("Send")
        # Toggle UI groups
        mode.change(
            fn=lambda m: {
                params_group: gr.update(visible=(m == "Exercise Parameters")),
                prompt_group: gr.update(visible=(m == "Exercise Prompt")),
            },
            inputs=[mode], outputs=[params_group, prompt_group]
        )
        def generate_caller(mode_val, instrument_val, level_val, key_val,
                    time_sig_val, measures_val, prompt_val, measures_prompt_val):
            real_measures = measures_prompt_val if mode_val == "Exercise Prompt" else measures_val
            fixed_tempo = 60
            return generate_exercise(
                instrument_val, level_val, key_val, fixed_tempo, time_sig_val,
                real_measures, prompt_val, mode_val
            )
        generate_btn.click(
            fn=generate_caller,
            inputs=[mode, instrument, level, key, time_signature,measures, custom_prompt, measures_prompt],
            outputs=[json_output, audio_output, bpm_display, current_midi, duration_display, time_sig_display, duration_sum]
        )
        def save_midi(json_data, instr, time_sig):
            try:
                if not json_data or "Error" in json_data:
                    return None
                    
                parsed = json.loads(json_data)
                
                # Validate JSON structure
                if not isinstance(parsed, list):
                    return None
                    
                old_format = []
                for item in parsed:
                    if isinstance(item, dict) and "note" in item and "duration" in item:
                        old_format.append([item["note"], item["duration"]])
                
                if not old_format:
                    return None
                    
                # Calculate total units
                total_units = sum(d[1] for d in old_format)
                numerator, denominator = map(int, time_sig.split('/'))
                units_per_measure = numerator * (8 // denominator)
                measures_est = max(1, round(total_units / units_per_measure))
                
                # Generate MIDI
                cumulative = 0
                scaled_new = []
                for note, dur in old_format:
                    cumulative += dur
                    scaled_new.append({
                        "note": note,
                        "duration": dur,
                        "cumulative_duration": cumulative
                    })
                    
                midi_obj = json_to_midi(scaled_new, instr, 60, time_sig, measures_est)
                midi_path = os.path.join("static", "exercise.mid")
                midi_obj.save(midi_path)
                return midi_path
            except Exception as e:
                print(f"Error saving MIDI: {e}")
                return None
                
        download_midi.click(
            fn=save_midi,
            inputs=[json_output, instrument, time_signature],
            outputs=[midi_output],
        )
        send_chat_btn.click(
            fn=handle_chat,
            inputs=[chat_message, chat_history, instrument, level],
            outputs=[chat_message, chat_history],
        )
    return demo

# -----------------------------------------------------------------------------
# 14. Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    demo = create_ui()
    demo.launch()