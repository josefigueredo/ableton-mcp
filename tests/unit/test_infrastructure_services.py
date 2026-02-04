"""Unit tests for infrastructure service implementations."""

import pytest

from ableton_mcp.domain.entities import (
    Clip,
    ClipType,
    EntityId,
    Note,
    Song,
    Track,
    TrackType,
)
from ableton_mcp.infrastructure.services import (
    ArrangementServiceImpl,
    MixingServiceImpl,
    TempoAnalysisServiceImpl,
)


class TestTempoAnalysisServiceImpl:
    """Tests for TempoAnalysisServiceImpl."""

    @pytest.fixture
    def service(self) -> TempoAnalysisServiceImpl:
        """Provide tempo analysis service instance."""
        return TempoAnalysisServiceImpl()

    @pytest.fixture
    def sample_clip(self) -> Clip:
        """Create a sample clip."""
        return Clip(
            id=EntityId("clip-1"),
            name="Test Clip",
            clip_type=ClipType.MIDI,
            length=4.0,
            is_playing=False,
            notes=[
                Note(pitch=60, start=0.0, duration=1.0),
                Note(pitch=64, start=1.0, duration=1.0),
            ],
        )

    @pytest.fixture
    def sample_song(self) -> Song:
        """Create a sample song."""
        return Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,
            time_signature_numerator=4,
            time_signature_denominator=4,
            tracks=[],
        )

    async def test_detect_tempo(self, service: TempoAnalysisServiceImpl, sample_clip: Clip) -> None:
        """Test tempo detection from MIDI note patterns."""
        tempo = await service.detect_tempo(sample_clip)
        # Now returns computed tempo based on IOI analysis
        assert 60.0 <= tempo <= 200.0  # Valid BPM range

    async def test_detect_tempo_empty_clip(self, service: TempoAnalysisServiceImpl) -> None:
        """Test tempo detection falls back for empty clips."""
        empty_clip = Clip(
            id=EntityId("clip-empty"),
            name="Empty Clip",
            clip_type=ClipType.MIDI,
            length=4.0,
            notes=[],
        )
        tempo = await service.detect_tempo(empty_clip)
        assert tempo == 120.0  # Default fallback

    async def test_detect_tempo_audio_clip(self, service: TempoAnalysisServiceImpl) -> None:
        """Test tempo detection for audio clip returns default."""
        audio_clip = Clip(
            id=EntityId("clip-audio"),
            name="Audio Clip",
            clip_type=ClipType.AUDIO,
            length=4.0,
        )
        tempo = await service.detect_tempo(audio_clip)
        assert tempo == 120.0  # Cannot analyze audio

    async def test_suggest_tempo_for_genre_house(self, service: TempoAnalysisServiceImpl) -> None:
        """Test tempo suggestion for house music."""
        tempo = await service.suggest_tempo_for_genre("house", "medium")
        assert 120 <= tempo <= 130

    async def test_suggest_tempo_for_genre_hip_hop_low(
        self, service: TempoAnalysisServiceImpl
    ) -> None:
        """Test tempo suggestion for hip hop with low energy."""
        tempo = await service.suggest_tempo_for_genre("hip_hop", "low")
        assert 70 <= tempo <= 80

    async def test_suggest_tempo_for_genre_high_energy(
        self, service: TempoAnalysisServiceImpl
    ) -> None:
        """Test tempo suggestion with high energy."""
        tempo = await service.suggest_tempo_for_genre("techno", "high")
        assert 125 <= tempo <= 135

    async def test_suggest_tempo_for_unknown_genre(self, service: TempoAnalysisServiceImpl) -> None:
        """Test tempo suggestion for unknown genre defaults to 120."""
        tempo = await service.suggest_tempo_for_genre("unknown_genre", "medium")
        assert tempo == 120.0

    async def test_analyze_rhythmic_patterns(
        self, service: TempoAnalysisServiceImpl, sample_clip: Clip
    ) -> None:
        """Test rhythmic pattern analysis."""
        result = await service.analyze_rhythmic_patterns(sample_clip)

        assert result.analysis_type == "rhythmic_pattern"
        assert result.confidence > 0
        assert "pattern_type" in result.data
        assert "complexity" in result.data

    async def test_suggest_tempo_changes(
        self, service: TempoAnalysisServiceImpl, sample_song: Song
    ) -> None:
        """Test tempo change suggestions."""
        target_energy = [0.3, 0.5, 0.8, 1.0, 0.5]

        suggestions = await service.suggest_tempo_changes(sample_song, target_energy)

        assert len(suggestions) == 5

        # Verify structure of suggestions
        for time_pos, tempo in suggestions:
            assert isinstance(time_pos, float)
            assert isinstance(tempo, float)
            assert 60.0 <= tempo <= 200.0

    async def test_suggest_tempo_changes_extreme_energy(
        self, service: TempoAnalysisServiceImpl, sample_song: Song
    ) -> None:
        """Test tempo changes with extreme energy values."""
        target_energy = [0.0, 1.0]  # Extreme low and high

        suggestions = await service.suggest_tempo_changes(sample_song, target_energy)

        # Check clamping to reasonable range
        for _, tempo in suggestions:
            assert 60.0 <= tempo <= 200.0


class TestArrangementServiceImpl:
    """Tests for ArrangementServiceImpl."""

    @pytest.fixture
    def service(self) -> ArrangementServiceImpl:
        """Provide arrangement service instance."""
        return ArrangementServiceImpl()

    @pytest.fixture
    def sample_song(self) -> Song:
        """Create a sample song."""
        return Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,
            time_signature_numerator=4,
            time_signature_denominator=4,
            tracks=[
                Track(
                    id=EntityId("track-1"),
                    name="Track 1",
                    track_type=TrackType.MIDI,
                ),
                Track(
                    id=EntityId("track-2"),
                    name="Track 2",
                    track_type=TrackType.AUDIO,
                ),
            ],
        )

    async def test_analyze_song_structure(
        self, service: ArrangementServiceImpl, sample_song: Song
    ) -> None:
        """Test song structure analysis."""
        result = await service.analyze_song_structure(sample_song)

        assert result.analysis_type == "song_structure"
        assert result.confidence > 0
        assert "sections" in result.data
        assert "total_length_bars" in result.data or "analysis_note" in result.data
        assert isinstance(result.data["sections"], list)

    async def test_analyze_song_structure_with_clips(self, service: ArrangementServiceImpl) -> None:
        """Test song structure analysis with clips containing data."""
        clip = Clip(
            id=EntityId("clip-1"),
            name="Verse",
            clip_type=ClipType.MIDI,
            length=16.0,
            notes=[
                Note(pitch=60, start=0.0, duration=1.0, velocity=100),
                Note(pitch=64, start=1.0, duration=1.0, velocity=90),
            ],
        )
        track = Track(
            id=EntityId("track-1"),
            name="Lead",
            track_type=TrackType.MIDI,
            clips=[clip],
        )
        song = Song(
            id=EntityId("song-1"),
            name="Test Song",
            tempo=120.0,
            tracks=[track],
        )

        result = await service.analyze_song_structure(song)

        assert result.confidence >= 0.5
        assert "detected_keywords" in result.data
        assert "verse" in result.data["detected_keywords"]

    async def test_suggest_arrangement_improvements_pop(
        self, service: ArrangementServiceImpl, sample_song: Song
    ) -> None:
        """Test arrangement suggestions for pop genre."""
        suggestions = await service.suggest_arrangement_improvements(sample_song, "pop")

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # Should include some suggestions
        assert any("harmonic layers" in s.lower() or "rule of 3" in s.lower() for s in suggestions)

    async def test_suggest_arrangement_improvements_electronic(
        self, service: ArrangementServiceImpl, sample_song: Song
    ) -> None:
        """Test arrangement suggestions for electronic genre."""
        suggestions = await service.suggest_arrangement_improvements(sample_song, "electronic")

        assert isinstance(suggestions, list)
        assert any("breakdown" in s.lower() for s in suggestions)

    async def test_suggest_arrangement_improvements_house(
        self, service: ArrangementServiceImpl, sample_song: Song
    ) -> None:
        """Test arrangement suggestions for house genre."""
        suggestions = await service.suggest_arrangement_improvements(sample_song, "house")

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    async def test_suggest_arrangement_improvements_many_tracks(
        self, service: ArrangementServiceImpl
    ) -> None:
        """Test arrangement suggestions with many tracks."""
        tracks = [
            Track(id=EntityId(f"track-{i}"), name=f"Track {i}", track_type=TrackType.MIDI)
            for i in range(25)
        ]

        song = Song(
            id=EntityId("song-1"),
            name="Complex Song",
            tempo=120.0,
            tracks=tracks,
        )

        suggestions = await service.suggest_arrangement_improvements(song, "rock")

        # Should suggest grouping when too many tracks
        assert any("group" in s.lower() for s in suggestions)

    async def test_calculate_energy_curve(
        self, service: ArrangementServiceImpl, sample_song: Song
    ) -> None:
        """Test energy curve calculation for empty song returns flat curve."""
        energy_points = await service.calculate_energy_curve(sample_song)

        # Empty song returns default flat curve
        assert len(energy_points) >= 10

        for time_pos, energy in energy_points:
            assert isinstance(time_pos, float)
            assert isinstance(energy, float)
            assert 0.0 <= energy <= 1.0

    async def test_calculate_energy_curve_with_notes(self, service: ArrangementServiceImpl) -> None:
        """Test energy curve reflects MIDI content."""
        loud_clip = Clip(
            id=EntityId("clip-loud"),
            name="Loud Section",
            clip_type=ClipType.MIDI,
            length=4.0,
            notes=[
                Note(pitch=60, start=0.0, duration=0.5, velocity=127),
                Note(pitch=64, start=0.5, duration=0.5, velocity=127),
                Note(pitch=67, start=1.0, duration=0.5, velocity=127),
                Note(pitch=72, start=1.5, duration=0.5, velocity=127),
            ],
        )
        track = Track(
            id=EntityId("track-1"),
            name="Lead",
            track_type=TrackType.MIDI,
            volume=1.0,
            clips=[loud_clip],
        )
        song = Song(
            id=EntityId("song-1"),
            name="Test",
            tempo=120.0,
            tracks=[track],
        )

        energy_points = await service.calculate_energy_curve(song)

        # Should have energy data based on clips
        assert len(energy_points) > 0
        # At least one point should have non-zero energy
        assert any(e[1] > 0 for e in energy_points)

    async def test_suggest_section_lengths_pop(self, service: ArrangementServiceImpl) -> None:
        """Test section length suggestions for pop."""
        sections = await service.suggest_section_lengths("pop", 240.0)

        assert "intro" in sections
        assert "verse" in sections
        assert "chorus" in sections
        assert "bridge" in sections
        assert "outro" in sections

    async def test_suggest_section_lengths_electronic(
        self, service: ArrangementServiceImpl
    ) -> None:
        """Test section length suggestions for electronic music."""
        sections = await service.suggest_section_lengths("electronic", 300.0)

        assert "intro" in sections
        assert "build" in sections
        assert "drop" in sections
        assert "breakdown" in sections

    async def test_suggest_section_lengths_house(self, service: ArrangementServiceImpl) -> None:
        """Test section length suggestions for house music."""
        sections = await service.suggest_section_lengths("house", 300.0)

        # House uses same template as electronic
        assert "intro" in sections
        assert "drop" in sections

    async def test_suggest_section_lengths_default(self, service: ArrangementServiceImpl) -> None:
        """Test section length suggestions for unknown genre uses default."""
        sections = await service.suggest_section_lengths("unknown_genre", 200.0)

        assert "intro" in sections
        assert "verse" in sections


class TestMixingServiceImpl:
    """Tests for MixingServiceImpl."""

    @pytest.fixture
    def service(self) -> MixingServiceImpl:
        """Provide mixing service instance."""
        return MixingServiceImpl()

    @pytest.fixture
    def sample_tracks(self) -> list[Track]:
        """Create sample tracks."""
        return [
            Track(
                id=EntityId("track-1"),
                name="Kick Drum",
                track_type=TrackType.MIDI,
                pan=0.0,
            ),
            Track(
                id=EntityId("track-2"),
                name="Vocals",
                track_type=TrackType.AUDIO,
                pan=0.0,
            ),
            Track(
                id=EntityId("track-3"),
                name="Guitar",
                track_type=TrackType.AUDIO,
                pan=-0.5,
            ),
            Track(
                id=EntityId("track-4"),
                name="Synth",
                track_type=TrackType.MIDI,
                pan=0.5,
            ),
        ]

    async def test_analyze_frequency_balance(
        self, service: MixingServiceImpl, sample_tracks: list[Track]
    ) -> None:
        """Test frequency balance analysis."""
        result = await service.analyze_frequency_balance(sample_tracks)

        assert result.analysis_type == "frequency_balance"
        assert result.confidence > 0
        assert "suggestions" in result.data
        assert isinstance(result.data["suggestions"], list)

    async def test_suggest_eq_adjustments_midi(self, service: MixingServiceImpl) -> None:
        """Test EQ suggestions for MIDI track."""
        track = Track(
            id=EntityId("track-1"),
            name="Synth Lead",
            track_type=TrackType.MIDI,
        )

        suggestions = await service.suggest_eq_adjustments(track)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # Check structure
        for suggestion in suggestions:
            assert "frequency" in suggestion
            assert "type" in suggestion

    async def test_suggest_eq_adjustments_vocal(self, service: MixingServiceImpl) -> None:
        """Test EQ suggestions for vocal track."""
        track = Track(
            id=EntityId("track-1"),
            name="Lead Vocals",
            track_type=TrackType.AUDIO,
        )

        suggestions = await service.suggest_eq_adjustments(track)

        assert len(suggestions) >= 3  # Should have multiple suggestions for vocals

        # Check for typical vocal EQ adjustments
        frequencies = [s["frequency"] for s in suggestions]
        assert any(f >= 3000 for f in frequencies)  # Presence boost

    async def test_suggest_eq_adjustments_drums(self, service: MixingServiceImpl) -> None:
        """Test EQ suggestions for drum track."""
        track = Track(
            id=EntityId("track-1"),
            name="Kick Drum",
            track_type=TrackType.AUDIO,
        )

        suggestions = await service.suggest_eq_adjustments(track)

        assert len(suggestions) >= 2

        # Check for drum-specific EQ
        frequencies = [s["frequency"] for s in suggestions]
        assert any(f <= 100 for f in frequencies)  # Sub-bass

    async def test_analyze_stereo_image_balanced(
        self, service: MixingServiceImpl, sample_tracks: list[Track]
    ) -> None:
        """Test stereo image analysis with balanced panning."""
        result = await service.analyze_stereo_image(sample_tracks)

        assert result.analysis_type == "stereo_image"
        assert "left_elements" in result.data
        assert "center_elements" in result.data
        assert "right_elements" in result.data
        assert "balance" in result.data
        assert "suggestions" in result.data

    async def test_analyze_stereo_image_unbalanced(self, service: MixingServiceImpl) -> None:
        """Test stereo image analysis with unbalanced panning."""
        tracks = [
            Track(id=EntityId("1"), name="Track 1", track_type=TrackType.MIDI, pan=-0.8),
            Track(id=EntityId("2"), name="Track 2", track_type=TrackType.MIDI, pan=-0.6),
            Track(id=EntityId("3"), name="Track 3", track_type=TrackType.MIDI, pan=-0.5),
        ]

        result = await service.analyze_stereo_image(tracks)

        assert result.data["balance"] == "unbalanced"

    async def test_calculate_lufs_target_spotify(self, service: MixingServiceImpl) -> None:
        """Test LUFS target calculation for Spotify."""
        lufs, peak = await service.calculate_lufs_target("pop", "spotify")

        assert lufs == -14
        assert peak == -1.0

    async def test_calculate_lufs_target_apple_music(self, service: MixingServiceImpl) -> None:
        """Test LUFS target calculation for Apple Music."""
        lufs, peak = await service.calculate_lufs_target("pop", "apple_music")

        assert lufs == -16
        assert peak == -1.0

    async def test_calculate_lufs_target_electronic(self, service: MixingServiceImpl) -> None:
        """Test LUFS target for electronic genre."""
        lufs, _peak = await service.calculate_lufs_target("electronic", "spotify")

        # Electronic gets +1 adjustment
        assert lufs == -13

    async def test_calculate_lufs_target_jazz(self, service: MixingServiceImpl) -> None:
        """Test LUFS target for jazz (more dynamic range)."""
        lufs, peak = await service.calculate_lufs_target("jazz", "spotify")

        # Jazz gets -2 adjustment for more dynamic range
        assert lufs == -16
        assert peak == -3.0

    async def test_calculate_lufs_target_classical(self, service: MixingServiceImpl) -> None:
        """Test LUFS target for classical (most dynamic range)."""
        lufs, peak = await service.calculate_lufs_target("classical", "spotify")

        # Classical gets -6 adjustment
        assert lufs == -20
        assert peak == -3.0

    async def test_calculate_lufs_target_unknown_platform(self, service: MixingServiceImpl) -> None:
        """Test LUFS target for unknown platform defaults to -14."""
        lufs, _peak = await service.calculate_lufs_target("pop", "unknown_platform")

        assert lufs == -14

    async def test_calculate_lufs_target_hip_hop(self, service: MixingServiceImpl) -> None:
        """Test LUFS target for hip hop."""
        lufs, _peak = await service.calculate_lufs_target("hip_hop", "spotify")

        # Hip hop gets +1 adjustment
        assert lufs == -13
