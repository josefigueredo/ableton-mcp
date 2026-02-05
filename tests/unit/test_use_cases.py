"""Unit tests for use cases."""

from unittest.mock import AsyncMock, Mock

from ableton_mcp.application.use_cases import (
    AddNotesRequest,
    AddNotesUseCase,
    AnalyzeHarmonyRequest,
    AnalyzeHarmonyUseCase,
    ClipOperationRequest,
    ClipOperationsUseCase,
    ConnectToAbletonRequest,
    ConnectToAbletonUseCase,
    DeviceOperationRequest,
    DeviceOperationsUseCase,
    GetClipContentRequest,
    GetClipContentUseCase,
    GetSongInfoRequest,
    GetSongInfoUseCase,
    ReturnTrackOperationRequest,
    ReturnTrackOperationsUseCase,
    SceneOperationRequest,
    SceneOperationsUseCase,
    SongPropertyRequest,
    SongPropertyUseCase,
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
        clip_service.create_clip = AsyncMock()

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
        clip_service.create_clip = AsyncMock()

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


class TestSceneOperationsUseCase:
    """Test cases for scene operations use case."""

    async def test_fire_scene(self) -> None:
        """Test firing a scene."""
        mock_service = Mock()
        mock_service.fire_scene = AsyncMock()
        mock_repository = InMemorySongRepository()

        use_case = SceneOperationsUseCase(mock_service, mock_repository)
        request = SceneOperationRequest(action="fire", scene_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert "Fired scene 0" in result.message
        mock_service.fire_scene.assert_called_once_with(0)

    async def test_get_scene_info(self) -> None:
        """Test getting scene info."""
        mock_service = Mock()
        mock_service.get_scene_info = AsyncMock(
            return_value={"scene_id": 0, "name": "Intro", "color": 5}
        )
        mock_repository = InMemorySongRepository()

        use_case = SceneOperationsUseCase(mock_service, mock_repository)
        request = SceneOperationRequest(action="get_info", scene_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["name"] == "Intro"

    async def test_create_scene(self) -> None:
        """Test creating a scene."""
        mock_service = Mock()
        mock_service.create_scene = AsyncMock()
        mock_repository = InMemorySongRepository()

        use_case = SceneOperationsUseCase(mock_service, mock_repository)
        request = SceneOperationRequest(action="create", index=2)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.create_scene.assert_called_once_with(2)

    async def test_delete_scene(self) -> None:
        """Test deleting a scene."""
        mock_service = Mock()
        mock_service.delete_scene = AsyncMock()
        mock_repository = InMemorySongRepository()

        use_case = SceneOperationsUseCase(mock_service, mock_repository)
        request = SceneOperationRequest(action="delete", scene_id=1)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.delete_scene.assert_called_once_with(1)

    async def test_set_scene_name(self) -> None:
        """Test setting scene name."""
        mock_service = Mock()
        mock_service.set_scene_name = AsyncMock()
        mock_repository = InMemorySongRepository()

        use_case = SceneOperationsUseCase(mock_service, mock_repository)
        request = SceneOperationRequest(action="set_name", scene_id=0, name="Chorus")

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_scene_name.assert_called_once_with(0, "Chorus")

    async def test_fire_scene_missing_id(self) -> None:
        """Test firing scene without scene_id."""
        mock_service = Mock()
        mock_repository = InMemorySongRepository()

        use_case = SceneOperationsUseCase(mock_service, mock_repository)
        request = SceneOperationRequest(action="fire")

        result = await use_case.execute(request)

        assert result.success is False
        assert "scene_id is required" in result.message


class TestSongPropertyUseCase:
    """Test cases for song property use case."""

    async def test_get_properties(self) -> None:
        """Test getting song properties."""
        mock_service = Mock()
        mock_service.get_song_properties = AsyncMock(
            return_value={
                "swing_amount": 0.0,
                "metronome": False,
                "overdub": False,
                "song_length": 128.0,
                "loop": False,
                "loop_start": 0.0,
                "loop_length": 16.0,
                "record_mode": False,
                "session_record": False,
                "punch_in": False,
                "punch_out": False,
            }
        )

        use_case = SongPropertyUseCase(mock_service)
        request = SongPropertyRequest(action="get_properties")

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["swing_amount"] == 0.0

    async def test_set_swing(self) -> None:
        """Test setting swing."""
        mock_service = Mock()
        mock_service.set_swing = AsyncMock()

        use_case = SongPropertyUseCase(mock_service)
        request = SongPropertyRequest(action="set_swing", value=0.5)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_swing.assert_called_once_with(0.5)

    async def test_set_metronome(self) -> None:
        """Test setting metronome."""
        mock_service = Mock()
        mock_service.set_metronome = AsyncMock()

        use_case = SongPropertyUseCase(mock_service)
        request = SongPropertyRequest(action="set_metronome", enabled=True)

        result = await use_case.execute(request)

        assert result.success is True
        assert "enabled" in result.message
        mock_service.set_metronome.assert_called_once_with(True)

    async def test_set_loop(self) -> None:
        """Test setting loop."""
        mock_service = Mock()
        mock_service.set_loop = AsyncMock()

        use_case = SongPropertyUseCase(mock_service)
        request = SongPropertyRequest(action="set_loop", enabled=True)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_loop.assert_called_once_with(True)

    async def test_set_tempo(self) -> None:
        """Test setting tempo."""
        mock_service = Mock()
        mock_service.set_tempo = AsyncMock()

        use_case = SongPropertyUseCase(mock_service)
        request = SongPropertyRequest(action="set_tempo", value=140.0)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_tempo.assert_called_once_with(140.0)

    async def test_set_swing_missing_value(self) -> None:
        """Test setting swing without value."""
        mock_service = Mock()

        use_case = SongPropertyUseCase(mock_service)
        request = SongPropertyRequest(action="set_swing")

        result = await use_case.execute(request)

        assert result.success is False


class TestClipOperationsUseCase:
    """Test cases for clip operations use case."""

    async def test_has_clip(self) -> None:
        """Test checking if clip exists."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()
        clip_service.has_clip = AsyncMock(return_value=True)

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = ClipOperationsUseCase(clip_service, song_repository)
        request = ClipOperationRequest(action="has_clip", track_id=0, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["has_clip"] is True

    async def test_get_clip_info(self) -> None:
        """Test getting clip info."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()
        clip_service.has_clip = AsyncMock(return_value=True)
        clip_service.get_clip_name = AsyncMock(return_value="My Clip")
        clip_service.get_clip_length = AsyncMock(return_value=8.0)
        clip_service.get_clip_loop_start = AsyncMock(return_value=0.0)
        clip_service.get_clip_loop_end = AsyncMock(return_value=8.0)
        clip_service.get_clip_is_playing = AsyncMock(return_value=False)

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = ClipOperationsUseCase(clip_service, song_repository)
        request = ClipOperationRequest(action="get_info", track_id=0, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["name"] == "My Clip"
        assert result.data["length"] == 8.0

    async def test_set_clip_name(self) -> None:
        """Test setting clip name."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()
        clip_service.set_clip_name = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = ClipOperationsUseCase(clip_service, song_repository)
        request = ClipOperationRequest(action="set_name", track_id=0, clip_id=0, name="New Name")

        result = await use_case.execute(request)

        assert result.success is True
        clip_service.set_clip_name.assert_called_once_with(0, 0, "New Name")

    async def test_fire_clip(self) -> None:
        """Test firing a clip."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()
        clip_service.fire_clip = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = ClipOperationsUseCase(clip_service, song_repository)
        request = ClipOperationRequest(action="fire", track_id=0, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        clip_service.fire_clip.assert_called_once_with(0, 0)

    async def test_create_clip(self) -> None:
        """Test creating a clip."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()
        clip_service.create_clip = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = ClipOperationsUseCase(clip_service, song_repository)
        request = ClipOperationRequest(action="create", track_id=0, clip_id=0, length=8.0)

        result = await use_case.execute(request)

        assert result.success is True
        clip_service.create_clip.assert_called_once_with(0, 0, 8.0)

    async def test_clip_track_not_found(self) -> None:
        """Test clip operation on nonexistent track."""
        song_repository = InMemorySongRepository()
        clip_service = Mock()

        song = Song(name="Test Song")
        await song_repository.save_song(song)

        use_case = ClipOperationsUseCase(clip_service, song_repository)
        request = ClipOperationRequest(action="get_info", track_id=99, clip_id=0)

        result = await use_case.execute(request)

        assert result.success is False
        assert "Track 99 not found" in result.message


class TestExtendedTransportUseCase:
    """Test cases for extended transport actions."""

    async def test_undo(self) -> None:
        """Test undo action."""
        mock_transport = Mock()
        mock_transport.undo = AsyncMock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="undo")

        result = await use_case.execute(request)

        assert result.success is True
        assert "Undo" in result.message
        mock_transport.undo.assert_called_once()

    async def test_redo(self) -> None:
        """Test redo action."""
        mock_transport = Mock()
        mock_transport.redo = AsyncMock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="redo")

        result = await use_case.execute(request)

        assert result.success is True
        mock_transport.redo.assert_called_once()

    async def test_jump_by(self) -> None:
        """Test jump_by action."""
        mock_transport = Mock()
        mock_transport.jump_by = AsyncMock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="jump_by", value=8.0)

        result = await use_case.execute(request)

        assert result.success is True
        mock_transport.jump_by.assert_called_once_with(8.0)

    async def test_jump_by_missing_value(self) -> None:
        """Test jump_by without value."""
        mock_transport = Mock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="jump_by")

        result = await use_case.execute(request)

        assert result.success is False

    async def test_capture_midi(self) -> None:
        """Test capture MIDI action."""
        mock_transport = Mock()
        mock_transport.capture_midi = AsyncMock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="capture_midi")

        result = await use_case.execute(request)

        assert result.success is True
        mock_transport.capture_midi.assert_called_once()

    async def test_stop_all_clips(self) -> None:
        """Test stop all clips."""
        mock_transport = Mock()
        mock_transport.stop_all_clips = AsyncMock()
        mock_repository = Mock()

        use_case = TransportControlUseCase(mock_transport, mock_repository)
        request = TransportControlRequest(action="stop_all_clips")

        result = await use_case.execute(request)

        assert result.success is True
        mock_transport.stop_all_clips.assert_called_once()


class TestReturnTrackOperationsUseCase:
    """Test cases for return track operations."""

    async def test_create_return_track(self) -> None:
        """Test creating a return track."""
        mock_service = Mock()
        mock_service.create_return_track = AsyncMock()
        mock_repository = InMemorySongRepository()

        use_case = ReturnTrackOperationsUseCase(mock_service, mock_repository)
        request = ReturnTrackOperationRequest(action="create")

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.create_return_track.assert_called_once()

    async def test_get_return_track_info(self) -> None:
        """Test getting return track info."""
        mock_service = Mock()
        mock_service.get_return_track_info = AsyncMock(
            return_value={
                "return_id": 0,
                "name": "Reverb",
                "volume": 0.8,
                "pan": 0.0,
                "muted": False,
            }
        )
        mock_repository = InMemorySongRepository()

        use_case = ReturnTrackOperationsUseCase(mock_service, mock_repository)
        request = ReturnTrackOperationRequest(action="get_info", return_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["name"] == "Reverb"

    async def test_set_return_volume(self) -> None:
        """Test setting return track volume."""
        mock_service = Mock()
        mock_service.set_return_track_volume = AsyncMock()
        mock_repository = InMemorySongRepository()

        use_case = ReturnTrackOperationsUseCase(mock_service, mock_repository)
        request = ReturnTrackOperationRequest(action="set_volume", return_id=0, value=0.7)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_return_track_volume.assert_called_once_with(0, 0.7)

    async def test_get_master_info(self) -> None:
        """Test getting master track info."""
        mock_service = Mock()
        mock_service.get_master_info = AsyncMock(return_value={"volume": 0.85, "pan": 0.0})
        mock_repository = InMemorySongRepository()

        use_case = ReturnTrackOperationsUseCase(mock_service, mock_repository)
        request = ReturnTrackOperationRequest(action="get_master_info")

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["volume"] == 0.85

    async def test_set_master_volume(self) -> None:
        """Test setting master volume."""
        mock_service = Mock()
        mock_service.set_master_volume = AsyncMock()
        mock_repository = InMemorySongRepository()

        use_case = ReturnTrackOperationsUseCase(mock_service, mock_repository)
        request = ReturnTrackOperationRequest(action="set_master_volume", value=0.9)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_master_volume.assert_called_once_with(0.9)

    async def test_missing_return_id(self) -> None:
        """Test operation requiring return_id without it."""
        mock_service = Mock()
        mock_repository = InMemorySongRepository()

        use_case = ReturnTrackOperationsUseCase(mock_service, mock_repository)
        request = ReturnTrackOperationRequest(action="get_info")

        result = await use_case.execute(request)

        assert result.success is False


class TestDeviceOperationsUseCase:
    """Test cases for device operations."""

    async def test_get_device_info(self) -> None:
        """Test getting device info."""
        song_repository = InMemorySongRepository()
        mock_service = Mock()
        mock_service.get_device_info = AsyncMock(
            return_value={
                "track_id": 0,
                "device_id": 0,
                "name": "EQ Eight",
                "class_name": "PluginDevice",
                "num_parameters": 10,
                "is_active": True,
            }
        )

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = DeviceOperationsUseCase(mock_service, song_repository)
        request = DeviceOperationRequest(action="get_info", track_id=0, device_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["name"] == "EQ Eight"

    async def test_set_device_active(self) -> None:
        """Test toggling device active state."""
        song_repository = InMemorySongRepository()
        mock_service = Mock()
        mock_service.set_device_active = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = DeviceOperationsUseCase(mock_service, song_repository)
        request = DeviceOperationRequest(action="set_active", track_id=0, device_id=0, active=False)

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_device_active.assert_called_once_with(0, 0, False)

    async def test_get_parameter(self) -> None:
        """Test getting parameter info."""
        song_repository = InMemorySongRepository()
        mock_service = Mock()
        mock_service.get_parameter_info = AsyncMock(
            return_value={
                "parameter_id": 1,
                "name": "Frequency",
                "value": 0.5,
                "display_value": "1.00 kHz",
                "min": 0.0,
                "max": 1.0,
            }
        )

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = DeviceOperationsUseCase(mock_service, song_repository)
        request = DeviceOperationRequest(
            action="get_parameter",
            track_id=0,
            device_id=0,
            parameter_id=1,
        )

        result = await use_case.execute(request)

        assert result.success is True
        assert result.data["name"] == "Frequency"

    async def test_set_parameter(self) -> None:
        """Test setting parameter value."""
        song_repository = InMemorySongRepository()
        mock_service = Mock()
        mock_service.set_parameter_value = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = DeviceOperationsUseCase(mock_service, song_repository)
        request = DeviceOperationRequest(
            action="set_parameter",
            track_id=0,
            device_id=0,
            parameter_id=1,
            value=0.75,
        )

        result = await use_case.execute(request)

        assert result.success is True
        mock_service.set_parameter_value.assert_called_once_with(0, 0, 1, 0.75)

    async def test_list_parameters(self) -> None:
        """Test listing all parameters."""
        song_repository = InMemorySongRepository()
        mock_service = Mock()
        mock_service.get_all_parameters = AsyncMock(
            return_value=[
                {"id": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
            ]
        )

        song = Song(name="Test Song")
        track = Track(name="Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = DeviceOperationsUseCase(mock_service, song_repository)
        request = DeviceOperationRequest(action="list_parameters", track_id=0, device_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        assert len(result.data["parameters"]) == 1

    async def test_device_track_not_found(self) -> None:
        """Test device operation on nonexistent track."""
        song_repository = InMemorySongRepository()
        mock_service = Mock()

        song = Song(name="Test Song")
        await song_repository.save_song(song)

        use_case = DeviceOperationsUseCase(mock_service, song_repository)
        request = DeviceOperationRequest(action="get_info", track_id=99, device_id=0)

        result = await use_case.execute(request)

        assert result.success is False
        assert "Track 99 not found" in result.message


class TestTrackEnhancementsUseCase:
    """Test cases for track enhancement operations."""

    async def test_set_track_color(self) -> None:
        """Test setting track color."""
        song_repository = InMemorySongRepository()
        track_repository = Mock()
        track_service = Mock()
        track_service.set_track_color = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Test Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = TrackOperationsUseCase(track_repository, song_repository, track_service)
        request = TrackOperationRequest(action="set_color", track_id=0, color=5)

        result = await use_case.execute(request)

        assert result.success is True
        track_service.set_track_color.assert_called_once_with(0, 5)

    async def test_set_track_send(self) -> None:
        """Test setting track send."""
        song_repository = InMemorySongRepository()
        track_repository = Mock()
        track_service = Mock()
        track_service.set_track_send = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Test Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = TrackOperationsUseCase(track_repository, song_repository, track_service)
        request = TrackOperationRequest(action="set_send", track_id=0, send_id=0, value=0.6)

        result = await use_case.execute(request)

        assert result.success is True
        track_service.set_track_send.assert_called_once_with(0, 0, 0.6)

    async def test_stop_all_track_clips(self) -> None:
        """Test stopping all clips on a track."""
        song_repository = InMemorySongRepository()
        track_repository = Mock()
        track_service = Mock()
        track_service.stop_all_track_clips = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Test Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = TrackOperationsUseCase(track_repository, song_repository, track_service)
        request = TrackOperationRequest(action="stop_all_clips", track_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        track_service.stop_all_track_clips.assert_called_once_with(0)

    async def test_duplicate_track(self) -> None:
        """Test duplicating a track."""
        song_repository = InMemorySongRepository()
        track_repository = Mock()
        track_service = Mock()
        track_service.duplicate_track = AsyncMock()

        song = Song(name="Test Song")
        track = Track(name="Test Track", track_type=TrackType.MIDI)
        song.add_track(track)
        await song_repository.save_song(song)

        use_case = TrackOperationsUseCase(track_repository, song_repository, track_service)
        request = TrackOperationRequest(action="duplicate", track_id=0)

        result = await use_case.execute(request)

        assert result.success is True
        track_service.duplicate_track.assert_called_once_with(0)
