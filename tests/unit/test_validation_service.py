"""Unit tests for ValidationService."""


from ableton_mcp.domain.entities import (
    Clip,
    ClipType,
    EntityId,
    Note,
    Song,
    Track,
    TrackType,
)
from ableton_mcp.domain.services import ValidationService


class TestValidationService:
    """Tests for ValidationService static methods."""

    def test_validate_note_range_valid(self) -> None:
        """Test valid note range."""
        note = Note(pitch=60, start=0.0, duration=1.0)
        assert ValidationService.validate_note_range(note) is True

    def test_validate_note_range_zero(self) -> None:
        """Test note at pitch 0."""
        note = Note(pitch=0, start=0.0, duration=1.0)
        assert ValidationService.validate_note_range(note) is True

    def test_validate_note_range_max(self) -> None:
        """Test note at pitch 127."""
        note = Note(pitch=127, start=0.0, duration=1.0)
        assert ValidationService.validate_note_range(note) is True

    def test_validate_tempo_valid(self) -> None:
        """Test valid tempo."""
        assert ValidationService.validate_tempo(120.0) is True

    def test_validate_tempo_min(self) -> None:
        """Test minimum valid tempo."""
        assert ValidationService.validate_tempo(20.0) is True

    def test_validate_tempo_max(self) -> None:
        """Test maximum valid tempo."""
        assert ValidationService.validate_tempo(999.0) is True

    def test_validate_tempo_too_low(self) -> None:
        """Test tempo below minimum."""
        assert ValidationService.validate_tempo(19.0) is False

    def test_validate_tempo_too_high(self) -> None:
        """Test tempo above maximum."""
        assert ValidationService.validate_tempo(1000.0) is False

    def test_validate_clip_timing_valid(self) -> None:
        """Test valid clip timing."""
        clip = Clip(
            id=EntityId("clip-1"),
            clip_type=ClipType.MIDI,
            length=4.0,
            loop_start=0.0,
            loop_end=4.0,
        )
        assert ValidationService.validate_clip_timing(clip) is True

    def test_validate_clip_timing_no_loop_end(self) -> None:
        """Test clip timing with no loop end."""
        clip = Clip(
            id=EntityId("clip-1"),
            clip_type=ClipType.MIDI,
            length=4.0,
            loop_start=0.0,
            loop_end=None,
        )
        assert ValidationService.validate_clip_timing(clip) is True

    def test_validate_clip_timing_invalid_loop_start_gte_end(self) -> None:
        """Test invalid clip timing where loop_start >= loop_end."""
        clip = Clip(
            id=EntityId("clip-1"),
            clip_type=ClipType.MIDI,
            length=4.0,
            loop_start=4.0,
            loop_end=2.0,
        )
        assert ValidationService.validate_clip_timing(clip) is False

    def test_validate_clip_timing_loop_end_equals_length(self) -> None:
        """Test valid clip timing where loop_end equals length."""
        clip = Clip(
            id=EntityId("clip-1"),
            clip_type=ClipType.MIDI,
            length=4.0,
            loop_start=0.0,
            loop_end=4.0,  # Equals length - valid
        )
        assert ValidationService.validate_clip_timing(clip) is True

    def test_validate_track_configuration_valid(self) -> None:
        """Test valid track configuration."""
        track = Track(
            id=EntityId("track-1"),
            name="Test Track",
            track_type=TrackType.MIDI,
            volume=0.8,
            pan=0.0,
        )
        issues = ValidationService.validate_track_configuration(track)
        assert len(issues) == 0

    def test_validate_track_configuration_empty_name(self) -> None:
        """Test track with empty name."""
        track = Track(
            id=EntityId("track-1"),
            name="   ",  # Whitespace-only name
            track_type=TrackType.MIDI,
            volume=0.8,
            pan=0.0,
        )
        issues = ValidationService.validate_track_configuration(track)
        assert any("name cannot be empty" in issue.lower() for issue in issues)

    def test_validate_track_configuration_with_clips(self) -> None:
        """Test track configuration with clips."""
        track = Track(
            id=EntityId("track-1"),
            name="Test Track",
            track_type=TrackType.MIDI,
            volume=0.8,
            pan=0.0,
            clips=[
                Clip(
                    id=EntityId("clip-1"),
                    clip_type=ClipType.MIDI,
                    length=4.0,
                    loop_start=0.0,
                    loop_end=4.0,
                )
            ],
        )
        issues = ValidationService.validate_track_configuration(track)
        assert len(issues) == 0

    def test_validate_track_configuration_invalid_clip(self) -> None:
        """Test track configuration with invalid clip timing."""
        track = Track(
            id=EntityId("track-1"),
            name="Test Track",
            track_type=TrackType.MIDI,
            volume=0.8,
            pan=0.0,
            clips=[
                Clip(
                    id=EntityId("clip-1"),
                    clip_type=ClipType.MIDI,
                    length=4.0,
                    loop_start=3.0,
                    loop_end=2.0,  # Invalid: start > end
                )
            ],
        )
        issues = ValidationService.validate_track_configuration(track)
        assert any("invalid timing" in issue.lower() for issue in issues)

    def test_validate_song_structure_valid(self) -> None:
        """Test valid song structure."""
        song = Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,
            loop_start=0.0,
            loop_end=16.0,
            tracks=[
                Track(
                    id=EntityId("track-1"),
                    name="Track 1",
                    track_type=TrackType.MIDI,
                )
            ],
        )
        issues = ValidationService.validate_song_structure(song)
        assert len(issues) == 0

    def test_validate_song_structure_valid_tempo(self) -> None:
        """Test song with valid tempo."""
        song = Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,  # Valid tempo
            loop_start=0.0,
            loop_end=16.0,
            tracks=[
                Track(
                    id=EntityId("track-1"),
                    name="Track 1",
                    track_type=TrackType.MIDI,
                )
            ],
        )
        issues = ValidationService.validate_song_structure(song)
        # No tempo issues for valid tempo
        assert not any("tempo" in issue.lower() for issue in issues)

    def test_validate_song_structure_invalid_loop(self) -> None:
        """Test song with invalid loop configuration."""
        song = Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,
            loop_start=16.0,
            loop_end=8.0,  # Start > End
            tracks=[
                Track(
                    id=EntityId("track-1"),
                    name="Track 1",
                    track_type=TrackType.MIDI,
                )
            ],
        )
        issues = ValidationService.validate_song_structure(song)
        assert any("loop" in issue.lower() for issue in issues)

    def test_validate_song_structure_no_tracks(self) -> None:
        """Test song with no tracks."""
        song = Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,
            loop_start=0.0,
            loop_end=16.0,
            tracks=[],  # No tracks
        )
        issues = ValidationService.validate_song_structure(song)
        assert any("at least one track" in issue.lower() for issue in issues)

    def test_validate_song_structure_with_track_issues(self) -> None:
        """Test song with track configuration issues."""
        song = Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,
            loop_start=0.0,
            loop_end=16.0,
            tracks=[
                Track(
                    id=EntityId("track-1"),
                    name="   ",  # Empty name
                    track_type=TrackType.MIDI,
                )
            ],
        )
        issues = ValidationService.validate_song_structure(song)
        assert any("track 0" in issue.lower() for issue in issues)
