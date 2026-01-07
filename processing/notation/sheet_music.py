#!/usr/bin/env python

"""Sheet music generation using music21 and optional LilyPond."""

import os
import uuid
import json
import shutil
import tempfile
import subprocess
from typing import Optional, List, Dict, Any, Tuple

import music21
from music21 import stream, note, instrument, meter, tempo, key, metadata

from lib.music_generation.theory import note_name_to_midi, clean_note_string
from .constants import (
    INSTRUMENT_CLEFS,
    DURATION_MAP,
    PDF_DPI,
    SVG_DPI,
    PNG_DPI,
)


def get_clef_for_instrument(instrument_name: str) -> str:
    """Get the appropriate clef for an instrument."""
    return INSTRUMENT_CLEFS.get(instrument_name, "treble")


def duration_units_to_quarter_length(duration_units: int) -> float:
    """Convert 8th note units to music21 quarterLength."""
    if duration_units in DURATION_MAP:
        return DURATION_MAP[duration_units]
    return duration_units * 0.5


def validate_score(score: music21.stream.Score) -> bool:
    """Validate that a music21 Score is properly formed."""
    try:
        if not isinstance(score, music21.stream.Score):
            return False
        if len(score.parts) == 0:
            return False
        first_part = score.parts[0]
        has_notes = any(isinstance(element, note.Note) for element in first_part.flat.notesAndRests)
        
        return has_notes
    except Exception as e:
        print(f"Score validation error: {e}")
        return False


def get_instrument_music21(instrument_name: str) -> music21.instrument.Instrument:
    """Get music21 instrument object for given instrument."""
    instrument_map = {
        "Trumpet": music21.instrument.Trumpet(),
        "Piano": music21.instrument.Piano(),
        "Violin": music21.instrument.Violin(),
        "Clarinet": music21.instrument.Clarinet(),
        "Flute": music21.instrument.Flute(),
    }
    
    return instrument_map.get(instrument_name, music21.instrument.Trumpet())


def parse_key_signature(key_str: str) -> music21.key.Key:
    """Parse key signature string (e.g., 'C Major', 'G Major')."""
    try:
        key_parts = key_str.split()
        if len(key_parts) >= 2:
            tonic = key_parts[0]
            mode = key_parts[1].lower()
            return music21.key.Key(tonic, mode)
        else:
            return music21.key.Key('C', 'major')
    except Exception as e:
        print(f"Warning: Could not parse key signature '{key_str}': {e}")
        return music21.key.Key('C', 'major')


def parse_time_signature(time_sig_str: str) -> music21.meter.TimeSignature:
    """Parse time signature string (e.g., '4/4', '3/4')."""
    try:
        return music21.meter.TimeSignature(time_sig_str)
    except Exception as e:
        print(f"Warning: Could not parse time signature '{time_sig_str}': {e}")
        return music21.meter.TimeSignature('4/4')


# ============================================================================
# Main Functions
# ============================================================================

def json_to_music21_score(
    json_data,
    instrument_name: str,
    key_sig: str,
    time_signature: str,
    tempo_bpm: int,
    measures: int
) -> Optional[music21.stream.Score]:
    """Convert JSON note data to a music21 Score object."""
    try:
        # Parse JSON if it's a string
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON string: {e}")
                return None
        
        # Create score and part
        score = music21.stream.Score()
        part = music21.stream.Part()
        
        # Add instrument
        inst = get_instrument_music21(instrument_name)
        part.insert(0, inst)
        
        # Add metadata
        score.metadata = metadata.Metadata()
        score.metadata.title = f"{instrument_name} Exercise"
        score.metadata.composer = "HarmonyHub"
        
        # Add key signature
        key_obj = parse_key_signature(key_sig)
        part.append(key_obj)
        
        # Add time signature
        time_sig_obj = parse_time_signature(time_signature)
        part.append(time_sig_obj)
        
        # Add tempo marking
        tempo_marking = tempo.MetronomeMark(number=tempo_bpm)
        part.append(tempo_marking)
        
        # Add notes from JSON data
        for note_item in json_data:
            try:
                # Handle both object format and legacy array format
                if isinstance(note_item, dict):
                    note_name = note_item.get('note', 'C4')
                    duration_units = int(note_item.get('duration', 2))
                else:
                    # Legacy format [note, duration]
                    note_name, duration_units = note_item
                    duration_units = int(duration_units)
                
                # Clean note string (remove ornamentation)
                note_name = clean_note_string(str(note_name))
                
                # Validate note name
                try:
                    note_name_to_midi(note_name)
                except ValueError:
                    print(f"Warning: Invalid note '{note_name}', skipping")
                    continue
                
                # Convert duration
                quarter_length = duration_units_to_quarter_length(duration_units)
                
                # Create and add note
                note_obj = note.Note(note_name, quarterLength=quarter_length)
                part.append(note_obj)
                
            except Exception as e:
                print(f"Warning: Error processing note {note_item}: {e}")
                continue
        
        # Add part to score
        score.append(part)
        
        # Validate score
        if not validate_score(score):
            print("Warning: Generated score failed validation")
            return None
        
        return score
        
    except Exception as e:
        print(f"Error creating music21 score: {e}")
        return None


def render_score_to_pdf(
    score: music21.stream.Score,
    output_path: Optional[str] = None,
    use_lilypond: bool = True,
    dpi: int = 300
) -> Optional[str]:
    """Render music21 Score to PDF (MuseScore→LilyPond→reportlab fallback)."""
    try:
        # If no output path provided, create a temporary file
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            output_path = temp_file.name
            temp_file.close()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        # Ensure output path ends with .pdf
        if not output_path.endswith('.pdf'):
            output_path = output_path.rsplit('.', 1)[0] + '.pdf'
        
        # Try MuseScore first (most common on Mac)
        try:
            print("Attempting to render PDF via MuseScore...")
            result = subprocess.run(
                ['mscore', '-o', output_path, '-F', '-'],
                input=score.write('musicxml'),
                capture_output=True,
                timeout=10,
                text=True
            )
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"✓ PDF successfully created via MuseScore: {output_path}")
                return output_path
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        
        # Try LilyPond backend second (best quality alternative)
        if use_lilypond:
            try:
                # Check if LilyPond is available
                result = subprocess.run(
                    ['lilypond', '--version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print("Attempting to render PDF via LilyPond...")
                    temp_ly = tempfile.NamedTemporaryFile(suffix='.ly', delete=False)
                    temp_ly.close()
                    
                    score.write('lily', fp=temp_ly.name)
                    
                    # Compile LilyPond to PDF
                    subprocess.run(
                        ['lilypond', '-o', output_path.rsplit('.', 1)[0], temp_ly.name],
                        capture_output=True,
                        timeout=30
                    )
                    
                    if os.path.exists(output_path):
                        print(f"✓ PDF successfully created via LilyPond: {output_path}")
                        try:
                            os.remove(temp_ly.name)
                        except:
                            pass
                        return output_path
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
                print(f"LilyPond rendering not available: {e}")
        
        # Fallback: Generate PNG and convert to PDF using PIL
        print("Falling back to PNG → PDF conversion...")
        try:
            # Generate PNG first
            png_path = output_path.rsplit('.', 1)[0] + '_temp.png'
            png_result = render_score_to_image(score, png_path, format='png', dpi=dpi)
            
            if png_result and os.path.exists(png_result):
                try:
                    # Try PIL first
                    from PIL import Image
                    
                    img = Image.open(png_result).convert('RGB')
                    img.save(output_path, 'PDF')
                    
                    # Clean up temp PNG
                    try:
                        os.remove(png_result)
                    except:
                        pass
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                        print(f"✓ PDF successfully created via PNG conversion: {output_path}")
                        return output_path
                except Exception as pil_error:
                    print(f"PIL conversion failed: {pil_error}, trying ImageMagick...")
                    # Try ImageMagick as fallback
                    try:
                        subprocess.run(
                            ['convert', png_result, output_path],
                            capture_output=True,
                            timeout=10
                        )
                        if os.path.exists(output_path):
                            try:
                                os.remove(png_result)
                            except:
                                pass
                            print(f"✓ PDF successfully created via ImageMagick: {output_path}")
                            return output_path
                    except Exception as im_error:
                        print(f"ImageMagick conversion failed: {im_error}")
        except Exception as e:
            print(f"PNG to PDF conversion failed: {e}")
        
        # Last resort: Create a professional-looking PDF with reportlab
        print("Creating professional PDF with reportlab...")
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 18)
            title = f"Sheet Music Exercise"
            c.drawString(inch, height - inch, title)
            
            # Metadata
            c.setFont("Helvetica", 12)
            y_pos = height - 1.5 * inch
            
            # Get instrument info
            instrument_names = []
            for part in score.parts:
                inst = part.getInstrument()
                if inst:
                    instrument_names.append(inst.instrumentName)
            
            if instrument_names:
                c.drawString(0.5 * inch, y_pos, f"Instrument: {', '.join(instrument_names)}")
                y_pos -= 0.25 * inch
            
            # Key and Time signature
            key_info = str(score.flat.getElementsByClass('Key')[0]) if score.flat.getElementsByClass('Key') else "C Major"
            time_info = str(score.flat.getElementsByClass('TimeSignature')[0]) if score.flat.getElementsByClass('TimeSignature') else "4/4"
            tempo_info = score.flat.getElementsByClass('MetronomeMark')[0].number if score.flat.getElementsByClass('MetronomeMark') else "Unknown"
            
            c.drawString(0.5 * inch, y_pos, f"Key: {key_info} | Time: {time_info} | Tempo: {tempo_info} BPM")
            y_pos -= 0.35 * inch
            
            # Note listing
            c.setFont("Helvetica", 10)
            c.drawString(0.5 * inch, y_pos, "Notes:")
            y_pos -= 0.2 * inch
            
            # Get all notes
            notes_list = []
            note_count = 0
            for element in score.flatten().notesAndRests:
                if hasattr(element, 'pitch'):
                    note_name = str(element.pitch)
                    duration = element.quarterLength
                    notes_list.append((note_name, duration))
                    note_count += 1
            
            # Display notes in a grid format
            col_width = 2 * inch
            cols = 3
            col = 0
            
            for note_name, duration in notes_list:
                duration_name = {0.5: "8th", 1.0: "Q", 2.0: "H", 4.0: "W"}.get(duration, f"{duration}QL")
                note_text = f"{note_name} ({duration_name})"
                
                x_pos = 0.5 * inch + (col * col_width)
                c.drawString(x_pos, y_pos, note_text)
                
                col += 1
                if col >= cols:
                    col = 0
                    y_pos -= 0.25 * inch
                
                if y_pos < 0.5 * inch:
                    break
            
            # Footer
            c.setFont("Helvetica", 8)
            c.drawString(0.5 * inch, 0.3 * inch, f"Generated by HarmonyHub | {note_count} notes total")
            
            c.showPage()
            c.save()
            
            if os.path.exists(output_path):
                print(f"✓ Professional PDF created: {output_path}")
                print(f"  Contains: {note_count} notes, {key_info}, {time_info}, {tempo_info} BPM")
                return output_path
        except ImportError:
            print("reportlab not installed, creating minimal PDF...")
            # Create a very minimal PDF if reportlab not available
            try:
                with open(output_path, 'wb') as f:
                    f.write(b'%PDF-1.4\n')
                    f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
                    f.write(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
                    f.write(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n')
                    f.write(b'4 0 obj\n<< /Length 50 >>\nstream\nBT\n/F1 12 Tf\n50 750 Td\n(Sheet Music) Tj\nET\nendstream\nendobj\n')
                    f.write(b'xref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000203 00000 n\n')
                    f.write(b'trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n303\n%%EOF\n')
                
                if os.path.exists(output_path):
                    print(f"✓ Minimal PDF created: {output_path}")
                    return output_path
            except Exception as e:
                print(f"Failed to create minimal PDF: {e}")
        except Exception as e:
            print(f"reportlab PDF creation failed: {e}")
        
        print("Warning: PDF generation failed completely")
        return None
        
    except Exception as e:
        print(f"Error rendering PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def render_score_to_image(
    score: music21.stream.Score,
    output_path: Optional[str] = None,
    format: str = 'png',
    dpi: int = 300
) -> Optional[str]:
    """Render music21 Score to PNG or SVG image."""
    try:
        # If no output path provided, create a temporary file
        if output_path is None:
            suffix = f'.{format.lower()}' if format.lower() in ['svg', 'png'] else '.png'
            temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            output_path = temp_file.name
            temp_file.close()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        if format.lower() == 'svg':
            try:
                # SVG rendering via musicxml
                if not output_path.endswith('.svg'):
                    output_path = output_path.replace('.svg', '') + '.svg'
                
                # Use MusicXML as intermediate for SVG
                score.write('svg', fp=output_path)
                
                if os.path.exists(output_path):
                    print(f"SVG successfully created: {output_path}")
                    return output_path
            except Exception as e:
                print(f"SVG rendering failed: {e}")
                print("Falling back to PDF...")
                # Fallback to PDF when SVG unavailable
                pdf_output = output_path.replace('.svg', '') + '.pdf'
                return render_score_to_pdf(score, pdf_output, dpi=dpi)
        
        if format.lower() == 'png':
            try:
                if not output_path.endswith('.png'):
                    output_path = output_path.replace('.png', '') + '.png'
                
                # Use matplotlib backend for PNG
                score.write('png', fp=output_path, dpi=dpi)
                
                if os.path.exists(output_path):
                    print(f"PNG successfully created: {output_path}")
                    return output_path
            except Exception as e:
                print(f"PNG rendering failed: {e}")
                # Try alternative PNG method
                try:
                    import matplotlib.pyplot as plt
                    fig = score.show('MusNotation')
                    fig.savefig(output_path, dpi=dpi)
                    plt.close(fig)
                    
                    if os.path.exists(output_path):
                        print(f"PNG successfully created (matplotlib): {output_path}")
                        return output_path
                except Exception as e2:
                    print(f"Matplotlib PNG rendering also failed: {e2}")
                    print("Falling back to PDF...")
                    # Fallback to PDF when PNG unavailable
                    pdf_output = output_path.replace('.png', '') + '.pdf'
                    return render_score_to_pdf(score, pdf_output, dpi=dpi)
        
        print(f"Warning: Image rendering failed for format {format}")
        return None
        
    except Exception as e:
        print(f"Error rendering image: {e}")
        return None


# ============================================================================
# Convenience Functions
# ============================================================================

def create_sheet_music_files(
    json_data: List[Dict[str, Any]],
    instrument_name: str,
    key_sig: str,
    time_signature: str,
    tempo_bpm: int,
    measures: int,
    output_dir: str = './temp_notation'
) -> Dict[str, Optional[str]]:
    """Create sheet music files (PDF, SVG, PNG) from JSON note data."""
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        'pdf': None,
        'svg': None,
        'png': None,
        'score': None
    }
    
    try:
        # Create score
        score = json_to_music21_score(
            json_data,
            instrument_name,
            key_sig,
            time_signature,
            tempo_bpm,
            measures
        )
        
        if score is None:
            print("Error: Could not create music21 score")
            return results
        
        results['score'] = score
        
        # Generate PDF
        pdf_path = os.path.join(output_dir, f'sheet_music_{uuid.uuid4().hex}.pdf')
        pdf_result = render_score_to_pdf(score, pdf_path)
        if pdf_result:
            results['pdf'] = pdf_result
        
        # Generate SVG
        svg_path = os.path.join(output_dir, f'sheet_music_{uuid.uuid4().hex}.svg')
        svg_result = render_score_to_image(score, svg_path, format='svg')
        if svg_result:
            results['svg'] = svg_result
        
        # Generate PNG
        png_path = os.path.join(output_dir, f'sheet_music_{uuid.uuid4().hex}.png')
        png_result = render_score_to_image(score, png_path, format='png')
        if png_result:
            results['png'] = png_result
        
        return results
        
    except Exception as e:
        print(f"Error creating sheet music files: {e}")
        return results
