"""Unit tests for music theory service."""

import pytest

from ableton_mcp.domain.entities import Note
from ableton_mcp.infrastructure.services import MusicTheoryServiceImpl


class TestMusicTheoryService:
    """Test cases for music theory service."""

    @pytest.fixture
    def service(self) -> MusicTheoryServiceImpl:
        """Provide music theory service instance."""
        return MusicTheoryServiceImpl()

    async def test_analyze_key_c_major(self, service: MusicTheoryServiceImpl) -> None:
        """Test key analysis for C major scale."""
        notes = [
            Note(pitch=60, start=0.0, duration=1.0),  # C4
            Note(pitch=64, start=1.0, duration=1.0),  # E4
            Note(pitch=67, start=2.0, duration=1.0),  # G4
            Note(pitch=72, start=3.0, duration=1.0),  # C5
        ]
        
        keys = await service.analyze_key(notes)
        
        assert len(keys) > 0
        best_key = keys[0]
        assert best_key.root == 0  # C
        assert best_key.mode == "major"
        assert best_key.confidence > 0.5

    async def test_analyze_key_empty_notes(self, service: MusicTheoryServiceImpl) -> None:
        """Test key analysis with empty notes list."""
        keys = await service.analyze_key([])
        assert keys == []

    async def test_suggest_chord_progressions_pop(self, service: MusicTheoryServiceImpl) -> None:
        """Test chord progression suggestions for pop genre."""
        from ableton_mcp.domain.entities import MusicKey
        
        key = MusicKey(root=0, mode="major")  # C major
        progressions = await service.suggest_chord_progressions(key, "pop")
        
        assert len(progressions) > 0
        
        # Check that we get some common pop progressions
        progression_lengths = [len(prog) for prog in progressions]
        assert any(length >= 3 for length in progression_lengths)

    async def test_harmonize_melody(self, service: MusicTheoryServiceImpl) -> None:
        """Test melody harmonization."""
        from ableton_mcp.domain.entities import MusicKey
        
        melody_notes = [
            Note(pitch=60, start=0.0, duration=1.0),  # C4
            Note(pitch=64, start=1.0, duration=1.0),  # E4
        ]
        
        key = MusicKey(root=0, mode="major")  # C major
        harmony_notes = await service.harmonize_melody(melody_notes, key)
        
        # Should generate harmony notes (thirds and fifths)
        assert len(harmony_notes) == 4  # 2 melody notes * 2 harmony notes each
        
        # Check that harmony notes have lower velocity
        for harmony_note in harmony_notes:
            assert harmony_note.velocity < 100

    async def test_quantize_notes(self, service: MusicTheoryServiceImpl) -> None:
        """Test note quantization."""
        notes = [
            Note(pitch=60, start=0.1, duration=0.9),    # Slightly off-grid
            Note(pitch=64, start=1.05, duration=1.1),   # Slightly off-grid
        ]
        
        quantized = await service.quantize_notes(notes, grid_division=0.25)
        
        assert len(quantized) == 2
        
        # Check quantization
        assert quantized[0].start == 0.0    # Quantized to nearest 0.25
        assert quantized[1].start == 1.0    # Quantized to nearest 0.25
        
        # Duration should be quantized too
        assert quantized[0].duration == 1.0  # Quantized up to 1.0
        assert quantized[1].duration == 1.0  # Quantized down to 1.0

    async def test_filter_notes_to_scale(self, service: MusicTheoryServiceImpl) -> None:
        """Test filtering notes to a musical scale."""
        from ableton_mcp.domain.entities import MusicKey
        
        # Notes including some outside C major
        notes = [
            Note(pitch=60, start=0.0, duration=1.0),  # C4 (in scale)
            Note(pitch=61, start=1.0, duration=1.0),  # C#4 (not in scale)
            Note(pitch=64, start=2.0, duration=1.0),  # E4 (in scale)
            Note(pitch=66, start=3.0, duration=1.0),  # F#4 (not in scale)
        ]
        
        key = MusicKey(root=0, mode="major")  # C major
        filtered = await service.filter_notes_to_scale(notes, key)
        
        assert len(filtered) == 4
        
        # Check that out-of-scale notes were adjusted
        scale_pitch_classes = {0, 2, 4, 5, 7, 9, 11}  # C major
        
        for note in filtered:
            assert note.pitch_class in scale_pitch_classes

    async def test_analyze_key_multiple_candidates(self, service: MusicTheoryServiceImpl) -> None:
        """Test that key analysis returns multiple candidates."""
        # Notes that could fit multiple keys
        notes = [
            Note(pitch=60, start=0.0, duration=1.0),  # C
            Note(pitch=62, start=1.0, duration=1.0),  # D
            Note(pitch=64, start=2.0, duration=1.0),  # E
        ]
        
        keys = await service.analyze_key(notes)
        
        # Should return multiple key candidates
        assert len(keys) >= 2
        
        # Should be sorted by confidence
        confidences = [key.confidence for key in keys]
        assert confidences == sorted(confidences, reverse=True)

    async def test_chord_progressions_unknown_genre(self, service: MusicTheoryServiceImpl) -> None:
        """Test chord progressions with unknown genre defaults to pop."""
        from ableton_mcp.domain.entities import MusicKey
        
        key = MusicKey(root=0, mode="major")
        progressions = await service.suggest_chord_progressions(key, "unknown_genre")
        
        # Should still return progressions (defaulting to pop)
        assert len(progressions) > 0

    async def test_quantize_notes_minimum_duration(self, service: MusicTheoryServiceImpl) -> None:
        """Test that quantization respects minimum duration."""
        notes = [
            Note(pitch=60, start=0.0, duration=0.01),  # Very short note
        ]
        
        quantized = await service.quantize_notes(notes, grid_division=0.25)
        
        # Should be quantized to at least the grid division
        assert quantized[0].duration >= 0.25

    async def test_harmonize_melody_out_of_scale_notes(self, service: MusicTheoryServiceImpl) -> None:
        """Test harmonization with notes outside the scale."""
        from ableton_mcp.domain.entities import MusicKey
        
        melody_notes = [
            Note(pitch=61, start=0.0, duration=1.0),  # C# (not in C major)
        ]
        
        key = MusicKey(root=0, mode="major")
        harmony_notes = await service.harmonize_melody(melody_notes, key)
        
        # Should handle gracefully, possibly with no harmony notes
        # or by adjusting the melody note to fit the scale
        assert isinstance(harmony_notes, list)