"""Unit tests for use cases."""

from unittest.mock import AsyncMock, Mock

from ableton_mcp.application.use_cases import (
    AddNotesRequest,
    AddNotesUseCase,
    AnalyzeHarmonyRequest,
    AnalyzeHarmonyUseCase,
    ConnectToAbletonRequest,
    ConnectToAbletonUseCase,
    GetClipContentRequest,
    GetClipContentUseCase,
    GetSongInfoRequest,
    GetSongInfoUseCase,
    TrackOperationRequest,
    TrackOperationsUseCase,
    TransportControlRequest,
    TransportControlUseCase,
)
from ableton_mcp.domain.entities import Clip, ClipType, Song, Track, TrackType
from ableton_mcp.infrastructure.repositories import InMemorySongRepository
from ableton_mcp.infrastructure.services import MusicTheoryServiceImpl


class TestConnectToAbletonUseCase:
    """Test cases for connection use case."""

    def _create_mock_gateway(self) -> Mock:
        """Create a mock gateway with song data responses."""
        mock_gateway = Mock()
        mock_gateway.get_tempo = AsyncMock(return_value=120.0)
        mock_gateway.get_time_signature = AsyncMock(return_value=(4, 4))
        mock_gateway.get_song_time = AsyncMock(return_value=0.0)
        mock_gateway.get_is_playing = AsyncMock(return_value=False)
        mock_gateway.get_num_tracks = AsyncMock(return_value=2)
        mock_gateway.get_track_name = AsyncMock(side_effect=["Track 1", "Track 2"])
        mock_gateway.get_track_volume = AsyncMock(return_value=0.85)
        mock_gateway.get_track_pan = AsyncMock(return_value=0.0)
        return mock_gateway

    async def test_successful_connection(self) -> None:
        """Test successful connection to Ableton."""
        mock_service = Mock()
        mock_service.connect = AsyncMock()
        mock_repository = Mock()
        mock_repository.save_song = AsyncMock()
        mock_gateway = self._create_mock_gateway()

        use_case = ConnectToAbletonUseCase(mock_service, mock_repository, mock_gateway)
        request = ConnectToAbletonRequest(host="localhost", send_port=11000)

        result = await use_case.execute(request)

        assert result.success is True
        assert "Connected to Ableton Live" in result.message
        mock_service.connect.assert_called_once_with("localhost", 11000, 11001)
        mock_repository.save_song.assert_called_once()

    async def test_connection_failure(self) -> None:
        """Test connection failure handling."""
        mock_service = Mock()
        mock_service.connect = AsyncMock(side_effect=Exception("Connection refused"))
        mock_repository = Mock()
        mock_gateway = Mock()

        use_case = ConnectToAbletonUseCase(mock_service, mock_repository, mock_gateway)
        request = ConnectToAbletonRequest()

        result = await use_case.execute(request)

        assert result.success is False
        assert "Failed to connect" in result.message
        assert result.error_code == "CONNECTION_FAILED"


class TestTransportControlUseCase:
    """Test cases for transport control use case."""

    async def test_start_playing(self) -> None:
        """Test starting playback."""
        mock_transport = Mock()
        mock_transport.start_playing = AsyncMock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="play")

        result = await use_case.execute(request)

        assert result.success is True
        assert "Playback started" in result.message
        mock_transport.start_playing.assert_called_once()

    async def test_stop_playing(self) -> None:
        """Test stopping playback."""
        mock_transport = Mock()
        mock_transport.stop_playing = AsyncMock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="stop")

        result = await use_case.execute(request)

        assert result.success is True
        assert "Playback stopped" in result.message
        mock_transport.stop_playing.assert_called_once()

    async def test_get_status_with_song(self) -> None:
        """Test getting transport status with active song."""
        mock_transport = Mock()
        mock_repository = Mock()

        sample_song = Song(name="Test Song", tempo=128.0)
        mock_repository.get_current_song = AsyncMock(return_value=sample_song)

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="get_status")

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data is not None
        assert result.data["tempo"] == 128.0

    async def test_invalid_action(self) -> None:
        """Test invalid transport action."""
        mock_transport = Mock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="invalid")

        result = await use_case.execute(request)

        assert result.success is False
        assert "Unknown transport action" in result.message


class TestGetSongInfoUseCase:
    """Test cases for song info use case."""

    async def test_get_song_info_basic(self) -> None:
        """Test getting basic song information."""
        repository = InMemorySongRepository()
        song = Song(name="Test Song", tempo=120.0, key="C major")
        await repository.save_song(song)

        use_case = GetSongInfoUseCase(repository)
        request = GetSongInfoRequest(include_tracks=False)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["name"] == "Test Song"
        assert result.data["tempo"] == 120.0
        assert result.data["key"] == "C major"

    async def test_get_song_info_with_tracks(self) -> None:
        """Test getting song info including tracks."""
        repository = InMemorySongRepository()
        song = Song(name="Test Song", tempo=120.0)

        track = Track(name="MIDI Track", track_type=TrackType.MIDI)
        song.add_track(track)

        await repository.save_song(song)

        use_case = GetSongInfoUseCase(repository)
        request = GetSongInfoRequest(include_tracks=True)

        result = await use_case.execute(request)

        assert result.success is True
        assert "tracks" in result.data
        assert len(result.data["tracks"]) == 1
        assert result.data["tracks"][0]["name"] == "MIDI Track"

    async def test_get_song_info_no_song(self) -> None:
        """Test getting song info when no song is loaded."""
        repository = InMemorySongRepository()

        use_case = GetSongInfoUseCase(repository)
        request = GetSongInfoRequest()

        result = await use_case.execute(request)

        assert result.success is False
        assert "No active song" in result.message


class TestTrackOperationsUseCase:
    """Test cases for track operations use case."""

    async def test_create_midi_track(self) -> None:
        """Test creating a MIDI track."""
        song_repository = InMemorySongRepository()
        track_repository = Mock()
        track_service = Mock()
        track_service.create_track = AsyncMock()

        song = Song(name="Test Song")
        await song_repository.save_song(song)

        use_case = TrackOperationsUseCase(track_repository, song_repository, track_service)
        request = TrackOperationRequest(action="create", track_type="midi", name="New MIDI")

        result = await use_case.execute(request)

        assert result.success is True
        assert "Created midi track" in result.message
        track_service.create_track.assert_called_once()

    async def test_set_track_volume(self) -> None:
        """Test setting track volume."""
        song_repository = InMemorySongRepository()
        track_repository = Mock()
        track_service = Mock()
        track_service.set_track_volume = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Test Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = TrackOperationsUseCase(track_repository, song_repository, track_service)
        request = TrackOperationRequest(action="set_volume", track_id=0, value=0.8)

        result = await use_case.execute(request)

        assert result.success is True
        track_service.set_track_volume.assert_called_once_with(0, 0.8)

    async def test_track_not_found(self) -> None:
        """Test operation on non-existent track."""
        song_repository = InMemorySongRepository()
        track_repository = Mock()
        track_service = Mock()

        song = Song(name="Test Song")
        await song_repository.save_song(song)

        use_case = TrackOperationsUseCase(track_repository, song_repository, track_service)
        request = TrackOperationRequest(action="get_info", track_id=999)

        result = await use_case.execute(request)

        assert result.success is False
        assert "Track 999 not found" in result.message


class TestAddNotesUseCase:
    """Test cases for add notes use case."""

    async def test_add_notes_success(self) -> None:
        """Test successfully adding notes to a clip."""
        from ableton_mcp.infrastructure.repositories import InMemoryClipRepository

        song_repository = InMemorySongRepository()
        clip_repository = InMemoryClipRepository()
        music_theory_service = MusicTheoryServiceImpl()
        clip_service = Mock()
        clip_service.add_note = AsyncMock()

        # Setup song with track and clip
        song = Song(name="Test Song")
        track = Track(name="MIDI Track", track_type=TrackType.MIDI)
        clip = Clip(name="Test Clip", clip_type=ClipType.MIDI, length=4.0)

        track.set_clip(0, clip)
        song.add_track(track)

        await song_repository.save_song(song)
        await clip_repository.create_clip(clip)

        use_case = AddNotesUseCase(
            clip_repository, song_repository, music_theory_service, clip_service
        )

        notes_data = [{"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100}]
        request = AddNotesRequest(track_id=0, clip_id=0, notes=notes_data)

        result = await use_case.execute(request)

        assert result.success is True
        assert "Added 1 notes" in result.message

    async def test_add_notes_with_quantization(self) -> None:
        """Test adding notes with quantization."""
        from ableton_mcp.infrastructure.repositories import InMemoryClipRepository

        song_repository = InMemorySongRepository()
        clip_repository = InMemoryClipRepository()
        music_theory_service = MusicTheoryServiceImpl()
        clip_service = Mock()
        clip_service.add_note = AsyncMock()

        # Setup song with track and clip
        song = Song(name="Test Song")
        track = Track(name="MIDI Track", track_type=TrackType.MIDI)
        clip = Clip(name="Test Clip", clip_type=ClipType.MIDI, length=4.0)

        track.set_clip(0, clip)
        song.add_track(track)

        await song_repository.save_song(song)
        await clip_repository.create_clip(clip)

        use_case = AddNotesUseCase(
            clip_repository, song_repository, music_theory_service, clip_service
        )

        # Note with off-grid timing
        notes_data = [{"pitch": 60, "start": 0.1, "duration": 0.9}]
        request = AddNotesRequest(track_id=0, clip_id=0, notes=notes_data, quantize=True)

        result = await use_case.execute(request)

        assert result.success is True

    async def test_add_notes_to_audio_clip_fails(self) -> None:
        """Test that adding notes to audio clip fails."""
        from ableton_mcp.infrastructure.repositories import InMemoryClipRepository

        song_repository = InMemorySongRepository()
        clip_repository = InMemoryClipRepository()
        music_theory_service = MusicTheoryServiceImpl()
        clip_service = Mock()

        # Setup song with audio clip
        song = Song(name="Test Song")
        track = Track(name="Audio Track", track_type=TrackType.AUDIO)
        clip = Clip(name="Audio Clip", clip_type=ClipType.AUDIO, length=4.0)

        track.set_clip(0, clip)
        song.add_track(track)

        await song_repository.save_song(song)
        await clip_repository.create_clip(clip)

        use_case = AddNotesUseCase(
            clip_repository, song_repository, music_theory_service, clip_service
        )

        notes_data = [{"pitch": 60, "start": 0.0, "duration": 1.0}]
        request = AddNotesRequest(track_id=0, clip_id=0, notes=notes_data)

        result = await use_case.execute(request)

        assert result.success is False
        assert "Can only add notes to MIDI tracks" in result.message


class TestAnalyzeHarmonyUseCase:
    """Test cases for harmony analysis use case."""

    async def test_analyze_c_major_chord(self) -> None:
        """Test analyzing C major chord."""
        music_theory_service = MusicTheoryServiceImpl()
        use_case = AnalyzeHarmonyUseCase(music_theory_service)

        # C major triad
        request = AnalyzeHarmonyRequest(notes=[60, 64, 67])  # C, E, G

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data is not None
        assert "detected_keys" in result.data
        assert len(result.data["detected_keys"]) > 0

        # Should detect C major as primary key
        best_key = result.data["detected_keys"][0]
        assert best_key["root"] == 0  # C
        assert best_key["mode"] == "major"

    async def test_analyze_harmony_with_progressions(self) -> None:
        """Test harmony analysis with progression suggestions."""
        music_theory_service = MusicTheoryServiceImpl()
        use_case = AnalyzeHarmonyUseCase(music_theory_service)

        request = AnalyzeHarmonyRequest(notes=[60, 64, 67], suggest_progressions=True, genre="pop")

        result = await use_case.execute(request)

        assert result.success is True
        assert "chord_progressions" in result.data
        assert len(result.data["chord_progressions"]) > 0

    async def test_analyze_harmony_empty_notes(self) -> None:
        """Test harmony analysis with empty notes."""
        music_theory_service = MusicTheoryServiceImpl()
        use_case = AnalyzeHarmonyUseCase(music_theory_service)

        request = AnalyzeHarmonyRequest(notes=[])

        result = await use_case.execute(request)

        assert result.success is False
        assert "No notes provided" in result.message


class TestGetClipContentUseCase:
    """Test cases for get clip content use case."""

    async def test_get_clip_content_success(self) -> None:
        """Test successfully getting clip content."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()

        # Mock clip service to return notes
        mock_notes = [
            {"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100, "mute": False},
            {"pitch": 64, "start": 1.0, "duration": 0.5, "velocity": 80, "mute": False},
        ]
        clip_service.get_clip_notes = AsyncMock(return_value=mock_notes)

        # Setup song with track
        song = Song(name="Test Song")
        track = Track(name="MIDI Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = GetClipContentUseCase(clip_service, song_repository)
        request = GetClipContentRequest(track_id=0, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["note_count"] == 2
        assert len(result.data["notes"]) == 2
        # Verify note names are added
        assert result.data["notes"][0]["note_name"] == "C4"
        assert result.data["notes"][1]["note_name"] == "E4"
        clip_service.get_clip_notes.assert_called_once_with(0, 0)

    async def test_get_clip_content_empty_clip(self) -> None:
        """Test getting content from an empty clip."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()
        clip_service.get_clip_notes = AsyncMock(return_value=[])

        song = Song(name="Test Song")
        track = Track(name="MIDI Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = GetClipContentUseCase(clip_service, song_repository)
        request = GetClipContentRequest(track_id=0, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["note_count"] == 0
        assert result.data["notes"] == []

    async def test_get_clip_content_track_not_found(self) -> None:
        """Test getting clip content from non-existent track."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()

        song = Song(name="Test Song")
        await song_repository.save_song(song)

        use_case = GetClipContentUseCase(clip_service, song_repository)
        request = GetClipContentRequest(track_id=999, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is False
        assert "Track 999 not found" in result.message

    async def test_get_clip_content_no_song(self) -> None:
        """Test getting clip content when no song is loaded."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()

        use_case = GetClipContentUseCase(clip_service, song_repository)
        request = GetClipContentRequest(track_id=0, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is False
        assert "No active song" in result.message


class TestAnalyzeTempoUseCase:
    """Test cases for tempo analysis use case."""

    async def test_analyze_tempo_with_current_bpm(self) -> None:
        """Test tempo analysis with provided BPM."""
        from ableton_mcp.application.use_cases import AnalyzeTempoRequest, AnalyzeTempoUseCase
        from ableton_mcp.infrastructure.services import TempoAnalysisServiceImpl

        tempo_service = TempoAnalysisServiceImpl()
        song_repository = InMemorySongRepository()

        use_case = AnalyzeTempoUseCase(tempo_service, song_repository)
        request = AnalyzeTempoRequest(
            current_bpm=128.0,
            genre="house",
            energy_level="medium",
        )

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["current_tempo"] == 128.0
        assert "suggestions" in result.data
        assert "relationships" in result.data["suggestions"]

    async def test_analyze_tempo_from_song(self) -> None:
        """Test tempo analysis using song's tempo."""
        from ableton_mcp.application.use_cases import AnalyzeTempoRequest, AnalyzeTempoUseCase
        from ableton_mcp.domain.entities import EntityId
        from ableton_mcp.infrastructure.services import TempoAnalysisServiceImpl

        tempo_service = TempoAnalysisServiceImpl()
        song_repository = InMemorySongRepository()

        # Create and save a song with specific tempo
        song = Song(id=EntityId("song-1"), name="Test", tempo=135.0, tracks=[])
        await song_repository.save_song(song)

        use_case = AnalyzeTempoUseCase(tempo_service, song_repository)
        request = AnalyzeTempoRequest(
            current_bpm=None,  # Will use song's tempo
            genre="techno",
            energy_level="high",
        )

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["current_tempo"] == 135.0

    async def test_analyze_tempo_no_song_defaults(self) -> None:
        """Test tempo analysis with no song defaults to 120 BPM."""
        from ableton_mcp.application.use_cases import AnalyzeTempoRequest, AnalyzeTempoUseCase
        from ableton_mcp.infrastructure.services import TempoAnalysisServiceImpl

        tempo_service = TempoAnalysisServiceImpl()
        song_repository = InMemorySongRepository()

        use_case = AnalyzeTempoUseCase(tempo_service, song_repository)
        request = AnalyzeTempoRequest(
            current_bpm=None,
            genre="pop",
            energy_level="medium",
        )

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["current_tempo"] == 120.0

    async def test_analyze_tempo_without_genre(self) -> None:
        """Test tempo analysis without genre."""
        from ableton_mcp.application.use_cases import AnalyzeTempoRequest, AnalyzeTempoUseCase
        from ableton_mcp.infrastructure.services import TempoAnalysisServiceImpl

        tempo_service = TempoAnalysisServiceImpl()
        song_repository = InMemorySongRepository()

        use_case = AnalyzeTempoUseCase(tempo_service, song_repository)
        request = AnalyzeTempoRequest(
            current_bpm=120.0,
            genre=None,
            energy_level="medium",
        )

        result = await use_case.execute(request)

        assert result.success is True
        # Should not have genre_optimal suggestion
        assert "genre_optimal" not in result.data["suggestions"]


class TestMixAnalysisUseCase:
    """Test cases for mix analysis use case."""

    async def test_mix_analysis_success(self) -> None:
        """Test successful mix analysis."""
        from ableton_mcp.application.use_cases import MixAnalysisRequest, MixAnalysisUseCase
        from ableton_mcp.domain.entities import EntityId
        from ableton_mcp.infrastructure.services import MixingServiceImpl

        mixing_service = MixingServiceImpl()
        song_repository = InMemorySongRepository()

        # Create song with tracks
        tracks = [
            Track(
                id=EntityId("track-1"),
                name="Kick Drum",
                track_type=TrackType.MIDI,
                volume=0.8,
            ),
            Track(
                id=EntityId("track-2"),
                name="Bass",
                track_type=TrackType.MIDI,
                volume=0.7,
            ),
        ]
        song = Song(id=EntityId("song-1"), name="Test", tempo=120.0, tracks=tracks)
        await song_repository.save_song(song)

        use_case = MixAnalysisUseCase(mixing_service, song_repository)
        request = MixAnalysisRequest(
            analyze_levels=True,
            analyze_frequency=True,
            target_lufs=-14.0,
            platform="spotify",
        )

        result = await use_case.execute(request)

        assert result.success is True
        assert "track_count" in result.data
        assert "frequency_analysis" in result.data
        assert "stereo_analysis" in result.data
        assert "loudness_targets" in result.data

    async def test_mix_analysis_no_song(self) -> None:
        """Test mix analysis with no active song."""
        from ableton_mcp.application.use_cases import MixAnalysisRequest, MixAnalysisUseCase
        from ableton_mcp.infrastructure.services import MixingServiceImpl

        mixing_service = MixingServiceImpl()
        song_repository = InMemorySongRepository()

        use_case = MixAnalysisUseCase(mixing_service, song_repository)
        request = MixAnalysisRequest()

        result = await use_case.execute(request)

        assert result.success is False
        assert "No active song" in result.message

    async def test_mix_analysis_high_volume_warning(self) -> None:
        """Test mix analysis warns about high volume tracks."""
        from ableton_mcp.application.use_cases import MixAnalysisRequest, MixAnalysisUseCase
        from ableton_mcp.domain.entities import EntityId
        from ableton_mcp.infrastructure.services import MixingServiceImpl

        mixing_service = MixingServiceImpl()
        song_repository = InMemorySongRepository()

        tracks = [
            Track(
                id=EntityId("track-1"),
                name="Loud Track",
                track_type=TrackType.MIDI,
                volume=0.95,  # Very high volume
            ),
        ]
        song = Song(id=EntityId("song-1"), name="Test", tempo=120.0, tracks=tracks)
        await song_repository.save_song(song)

        use_case = MixAnalysisUseCase(mixing_service, song_repository)
        request = MixAnalysisRequest(analyze_levels=True)

        result = await use_case.execute(request)

        assert result.success is True
        assert any("warning" in track_info for track_info in result.data.get("track_levels", []))


class TestArrangementSuggestionsUseCase:
    """Test cases for arrangement suggestions use case."""

    async def test_arrangement_suggestions_success(self) -> None:
        """Test successful arrangement suggestions."""
        from ableton_mcp.application.use_cases import (
            ArrangementSuggestionsRequest,
            ArrangementSuggestionsUseCase,
        )
        from ableton_mcp.domain.entities import EntityId
        from ableton_mcp.infrastructure.services import ArrangementServiceImpl

        arrangement_service = ArrangementServiceImpl()
        song_repository = InMemorySongRepository()

        tracks = [
            Track(id=EntityId("track-1"), name="Track 1", track_type=TrackType.MIDI),
        ]
        song = Song(id=EntityId("song-1"), name="Test", tempo=120.0, tracks=tracks)
        await song_repository.save_song(song)

        use_case = ArrangementSuggestionsUseCase(arrangement_service, song_repository)
        request = ArrangementSuggestionsRequest(genre="pop", song_length=128.0)

        result = await use_case.execute(request)

        assert result.success is True
        assert "current_structure" in result.data
        assert "improvement_suggestions" in result.data
        assert "recommended_section_lengths" in result.data
        assert "energy_curve" in result.data

    async def test_arrangement_suggestions_no_song(self) -> None:
        """Test arrangement suggestions with no active song."""
        from ableton_mcp.application.use_cases import (
            ArrangementSuggestionsRequest,
            ArrangementSuggestionsUseCase,
        )
        from ableton_mcp.infrastructure.services import ArrangementServiceImpl

        arrangement_service = ArrangementServiceImpl()
        song_repository = InMemorySongRepository()

        use_case = ArrangementSuggestionsUseCase(arrangement_service, song_repository)
        request = ArrangementSuggestionsRequest()

        result = await use_case.execute(request)

        assert result.success is False
        assert "No active song" in result.message

    async def test_arrangement_suggestions_default_genre(self) -> None:
        """Test arrangement suggestions defaults to pop genre."""
        from ableton_mcp.application.use_cases import (
            ArrangementSuggestionsRequest,
            ArrangementSuggestionsUseCase,
        )
        from ableton_mcp.domain.entities import EntityId
        from ableton_mcp.infrastructure.services import ArrangementServiceImpl

        arrangement_service = ArrangementServiceImpl()
        song_repository = InMemorySongRepository()

        song = Song(id=EntityId("song-1"), name="Test", tempo=120.0, tracks=[])
        await song_repository.save_song(song)

        use_case = ArrangementSuggestionsUseCase(arrangement_service, song_repository)
        request = ArrangementSuggestionsRequest(genre=None)  # No genre specified

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["genre"] == "pop"  # Should default to pop
