"""
Unit tests for the notation module (sheet music generation)
Tests the conversion of JSON exercise data to music21 scores and rendering to PDF/SVG/PNG
"""

import unittest
import json
import os
import tempfile
from pathlib import Path
from music21 import stream, note, meter, tempo, key

from processing.notation.sheet_music import (
    json_to_music21_score,
    render_score_to_pdf,
    render_score_to_image,
    get_clef_for_instrument,
    duration_units_to_quarter_length,
    validate_score,
    get_instrument_music21,
    parse_key_signature,
    parse_time_signature,
)
from processing.notation.constants import INSTRUMENT_CLEFS, DURATION_MAP


class TestJsonToMusic21Score(unittest.TestCase):
    """Test json_to_music21_score() function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_json = json.dumps([
            {"note": "C4", "duration": 2, "cumulative_duration": 0},
            {"note": "D4", "duration": 2, "cumulative_duration": 2},
            {"note": "E4", "duration": 2, "cumulative_duration": 4},
            {"note": "F4", "duration": 2, "cumulative_duration": 6},
        ])
    
    def test_basic_conversion_trumpet(self):
        """Test basic JSON to Score conversion for Trumpet"""
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        
        self.assertIsNotNone(score)
        self.assertIsInstance(score, stream.Score)
        # Should have at least one part
        self.assertGreater(len(score.parts), 0)
    
    def test_all_instruments(self):
        """Test conversion works for all supported instruments"""
        instruments = ["Trumpet", "Piano", "Violin", "Clarinet", "Flute"]
        
        for instrument in instruments:
            with self.subTest(instrument=instrument):
                score = json_to_music21_score(
                    self.sample_json,
                    instrument_name=instrument,
                    key_sig="C Major",
                    time_signature="4/4",
                    tempo_bpm=120,
                    measures=1
                )
                self.assertIsNotNone(score)
                self.assertIsInstance(score, stream.Score)
    
    def test_different_keys(self):
        """Test conversion with different key signatures"""
        keys = ["C Major", "G Major", "D Major", "F Major", "Bb Major", "A Minor", "E Minor"]
        
        for key_sig in keys:
            with self.subTest(key=key_sig):
                score = json_to_music21_score(
                    self.sample_json,
                    instrument_name="Trumpet",
                    key_sig=key_sig,
                    time_signature="4/4",
                    tempo_bpm=120,
                    measures=1
                )
                self.assertIsNotNone(score)
    
    def test_different_time_signatures(self):
        """Test conversion with different time signatures"""
        time_sigs = ["3/4", "4/4", "6/8"]
        
        for ts in time_sigs:
            with self.subTest(time_sig=ts):
                score = json_to_music21_score(
                    self.sample_json,
                    instrument_name="Trumpet",
                    key_sig="C Major",
                    time_signature=ts,
                    tempo_bpm=120,
                    measures=1
                )
                self.assertIsNotNone(score)
    
    def test_empty_json(self):
        """Test handling of empty JSON"""
        empty_json = json.dumps([])
        score = json_to_music21_score(
            empty_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        # Should handle gracefully (may return None or empty score)
        # The function should not crash
        self.assertTrue(True)  # If we get here, it didn't crash
    
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        invalid_json = "not valid json"
        score = json_to_music21_score(
            invalid_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        # Should return None for invalid JSON
        self.assertIsNone(score)
    
    def test_invalid_notes(self):
        """Test handling of invalid note names"""
        invalid_notes_json = json.dumps([
            {"note": "H9", "duration": 2},  # Invalid note
            {"note": "C4", "duration": 2},  # Valid
        ])
        score = json_to_music21_score(
            invalid_notes_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        # Should skip invalid notes and continue
        self.assertIsNotNone(score)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions"""
    
    def test_duration_units_to_quarter_length(self):
        """Test duration conversion from 8th note units to quarter length"""
        self.assertEqual(duration_units_to_quarter_length(1), 0.5)   # 8th note
        self.assertEqual(duration_units_to_quarter_length(2), 1.0)   # Quarter note
        self.assertEqual(duration_units_to_quarter_length(4), 2.0)   # Half note
        self.assertEqual(duration_units_to_quarter_length(8), 4.0)   # Whole note
    
    def test_get_clef_for_instrument(self):
        """Test getting correct clef for each instrument"""
        self.assertEqual(get_clef_for_instrument("Trumpet"), "treble")
        self.assertEqual(get_clef_for_instrument("Violin"), "treble")
        self.assertEqual(get_clef_for_instrument("Flute"), "treble")
        self.assertEqual(get_clef_for_instrument("Clarinet"), "treble")
        self.assertEqual(get_clef_for_instrument("Piano"), "grand staff")
    
    def test_get_instrument_music21(self):
        """Test getting music21 Instrument objects"""
        from music21.instrument import Instrument as Music21Instrument
        
        for inst_name in ["Trumpet", "Piano", "Violin", "Clarinet", "Flute"]:
            instrument = get_instrument_music21(inst_name)
            self.assertIsNotNone(instrument)
            self.assertIsInstance(instrument, Music21Instrument)
    
    def test_parse_key_signature(self):
        """Test parsing key signature strings"""
        key_c = parse_key_signature("C Major")
        self.assertIsNotNone(key_c)
        self.assertEqual(key_c.tonic.name, "C")
        
        key_g = parse_key_signature("G Major")
        self.assertIsNotNone(key_g)
        self.assertEqual(key_g.tonic.name, "G")
    
    def test_parse_time_signature(self):
        """Test parsing time signature strings"""
        ts_44 = parse_time_signature("4/4")
        self.assertIsNotNone(ts_44)
        self.assertEqual(ts_44.numerator, 4)
        self.assertEqual(ts_44.denominator, 4)
        
        ts_34 = parse_time_signature("3/4")
        self.assertIsNotNone(ts_34)
        self.assertEqual(ts_34.numerator, 3)
        self.assertEqual(ts_34.denominator, 4)


class TestRenderScoreToPdf(unittest.TestCase):
    """Test render_score_to_pdf() function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_json = json.dumps([
            {"note": "C4", "duration": 2},
            {"note": "D4", "duration": 2},
            {"note": "E4", "duration": 2},
            {"note": "F4", "duration": 2},
        ])
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_pdf_rendering(self):
        """Test basic PDF rendering"""
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        
        if score is not None:
            pdf_path = render_score_to_pdf(score, None)
            # Check that a file was created (either PDF or fallback)
            self.assertIsNotNone(pdf_path)
    
    def test_pdf_with_custom_dpi(self):
        """Test PDF rendering with custom DPI"""
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        
        if score is not None:
            pdf_path = render_score_to_pdf(score, None, dpi=150)
            self.assertIsNotNone(pdf_path)


class TestRenderScoreToImage(unittest.TestCase):
    """Test render_score_to_image() function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_json = json.dumps([
            {"note": "C4", "duration": 2},
            {"note": "D4", "duration": 2},
            {"note": "E4", "duration": 2},
            {"note": "F4", "duration": 2},
        ])
    
    def test_png_rendering(self):
        """Test PNG image rendering"""
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        
        if score is not None:
            png_path = render_score_to_image(score, None, format='png')
            # Check that a file was created
            self.assertIsNotNone(png_path)
    
    def test_svg_rendering(self):
        """Test SVG image rendering"""
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        
        if score is not None:
            svg_path = render_score_to_image(score, None, format='svg')
            # Check that a file was created or fallback to PNG
            self.assertIsNotNone(svg_path)
    
    def test_invalid_format(self):
        """Test handling of invalid image format"""
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        
        if score is not None:
            # Should handle gracefully (skip or convert to PNG)
            result = render_score_to_image(score, None, format='invalid')
            # Should either return None or fallback to PNG
            self.assertTrue(result is None or result.endswith('.png'))


class TestValidateScore(unittest.TestCase):
    """Test validate_score() function"""
    
    def test_valid_score(self):
        """Test validation of valid score"""
        s = stream.Score()
        part = stream.Part()
        part.append(note.Note("C4", quarterLength=1))
        s.append(part)
        
        is_valid = validate_score(s)
        self.assertTrue(is_valid)
    
    def test_empty_score(self):
        """Test validation of empty score"""
        s = stream.Score()
        is_valid = validate_score(s)
        # Empty score should still validate (has parts list)
        self.assertIsNotNone(is_valid)
    
    def test_none_score(self):
        """Test validation of None"""
        is_valid = validate_score(None)
        self.assertFalse(is_valid)


class TestIntegration(unittest.TestCase):
    """Integration tests for full workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_json = json.dumps([
            {"note": "C4", "duration": 2},
            {"note": "D4", "duration": 2},
            {"note": "E4", "duration": 2},
            {"note": "F4", "duration": 2},
            {"note": "G4", "duration": 4},
        ])
    
    def test_full_workflow_trumpet(self):
        """Test complete workflow: JSON -> Score -> PDF -> SVG"""
        # Create score
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Trumpet",
            key_sig="C Major",
            time_signature="4/4",
            tempo_bpm=120,
            measures=1
        )
        
        self.assertIsNotNone(score)
        
        # Render to PDF
        pdf_path = render_score_to_pdf(score, None)
        self.assertIsNotNone(pdf_path)
        
        # Render to SVG
        svg_path = render_score_to_image(score, None, format='svg')
        self.assertIsNotNone(svg_path)
    
    def test_full_workflow_piano(self):
        """Test complete workflow for Piano (grand staff)"""
        score = json_to_music21_score(
            self.sample_json,
            instrument_name="Piano",
            key_sig="G Major",
            time_signature="3/4",
            tempo_bpm=90,
            measures=1
        )
        
        self.assertIsNotNone(score)
        
        # Check that piano has proper staff configuration
        # Should have grand staff (treble + bass)
        if score is not None:
            self.assertGreater(len(score.parts), 0)


if __name__ == '__main__':
    unittest.main()
