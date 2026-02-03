"""Unit tests for repository implementations."""

import pytest

from ableton_mcp.domain.entities import (
    AnalysisResult,
    Clip,
    ClipType,
    Device,
    DeviceType,
    EntityId,
    Note,
    Parameter,
    Song,
    Track,
    TrackType,
)
from ableton_mcp.infrastructure.repositories import (
    InMemoryAnalysisRepository,
    InMemoryClipRepository,
    InMemoryDeviceRepository,
    InMemorySongRepository,
    InMemoryTrackRepository,
)


class TestInMemorySongRepository:
    """Tests for InMemorySongRepository."""

    @pytest.fixture
    def repository(self) -> InMemorySongRepository:
        """Create a fresh repository instance."""
        return InMemorySongRepository()

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

    async def test_get_current_song_when_empty(self, repository: InMemorySongRepository) -> None:
        """Test getting current song when none exists."""
        result = await repository.get_current_song()
        assert result is None

    async def test_save_song(self, repository: InMemorySongRepository, sample_song: Song) -> None:
        """Test saving a song."""
        await repository.save_song(sample_song)
        result = await repository.get_current_song()
        assert result is not None
        assert result.id == sample_song.id
        assert result.name == sample_song.name

    async def test_update_song(self, repository: InMemorySongRepository, sample_song: Song) -> None:
        """Test updating a song."""
        # First save the song
        await repository.save_song(sample_song)

        # Create updated version
        updated_song = Song(
            id=sample_song.id,
            name="Updated Song",
            tempo=140.0,
            time_signature_numerator=4,
            time_signature_denominator=4,
            tracks=[],
        )

        await repository.update_song(updated_song)
        result = await repository.get_current_song()

        assert result is not None
        assert result.name == "Updated Song"
        assert result.tempo == 140.0

    async def test_update_song_with_different_id(
        self, repository: InMemorySongRepository, sample_song: Song
    ) -> None:
        """Test updating with different ID doesn't change the song."""
        # First save the song
        await repository.save_song(sample_song)

        # Try to update with different ID
        different_song = Song(
            id=EntityId("different-id"),
            name="Different Song",
            tempo=140.0,
            time_signature_numerator=4,
            time_signature_denominator=4,
            tracks=[],
        )

        await repository.update_song(different_song)
        result = await repository.get_current_song()

        # Original song should remain unchanged
        assert result is not None
        assert result.name == sample_song.name
        assert result.tempo == sample_song.tempo


class TestInMemoryTrackRepository:
    """Tests for InMemoryTrackRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryTrackRepository:
        """Create a fresh repository instance."""
        return InMemoryTrackRepository()

    @pytest.fixture
    def sample_track(self) -> Track:
        """Create a sample track."""
        return Track(
            id=EntityId("track-1"),
            name="Test Track",
            track_type=TrackType.MIDI,
            volume=0.8,
            pan=0.0,
            is_muted=False,
            is_soloed=False,
            is_armed=False,
        )

    async def test_get_track_when_empty(self, repository: InMemoryTrackRepository) -> None:
        """Test getting a track when none exists."""
        result = await repository.get_track(EntityId("nonexistent"))
        assert result is None

    async def test_create_track(
        self, repository: InMemoryTrackRepository, sample_track: Track
    ) -> None:
        """Test creating a track."""
        await repository.create_track(sample_track)
        result = await repository.get_track(sample_track.id)

        assert result is not None
        assert result.id == sample_track.id
        assert result.name == sample_track.name

    async def test_get_tracks_by_song(
        self, repository: InMemoryTrackRepository, sample_track: Track
    ) -> None:
        """Test getting all tracks."""
        # Create multiple tracks
        track2 = Track(
            id=EntityId("track-2"),
            name="Track 2",
            track_type=TrackType.AUDIO,
            volume=0.7,
            pan=0.5,
            is_muted=True,
            is_soloed=False,
            is_armed=False,
        )

        await repository.create_track(sample_track)
        await repository.create_track(track2)

        tracks = await repository.get_tracks_by_song(EntityId("song-1"))

        assert len(tracks) == 2

    async def test_update_track(
        self, repository: InMemoryTrackRepository, sample_track: Track
    ) -> None:
        """Test updating a track."""
        await repository.create_track(sample_track)

        updated_track = Track(
            id=sample_track.id,
            name="Updated Track",
            track_type=TrackType.MIDI,
            volume=0.5,
            pan=-0.3,
            is_muted=True,
            is_soloed=False,
            is_armed=True,
        )

        await repository.update_track(updated_track)
        result = await repository.get_track(sample_track.id)

        assert result is not None
        assert result.name == "Updated Track"
        assert result.volume == 0.5
        assert result.is_muted is True

    async def test_delete_track(
        self, repository: InMemoryTrackRepository, sample_track: Track
    ) -> None:
        """Test deleting a track."""
        await repository.create_track(sample_track)
        await repository.delete_track(sample_track.id)

        result = await repository.get_track(sample_track.id)
        assert result is None

    async def test_delete_nonexistent_track(self, repository: InMemoryTrackRepository) -> None:
        """Test deleting a track that doesn't exist."""
        # Should not raise
        await repository.delete_track(EntityId("nonexistent"))


class TestInMemoryDeviceRepository:
    """Tests for InMemoryDeviceRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryDeviceRepository:
        """Create a fresh repository instance."""
        return InMemoryDeviceRepository()

    @pytest.fixture
    def sample_device(self) -> Device:
        """Create a sample device."""
        return Device(
            id=EntityId("device-1"),
            name="EQ Eight",
            device_type=DeviceType.AUDIO_EFFECT,
            is_enabled=True,
            parameters=[
                Parameter(
                    id=0,
                    name="Freq",
                    value=0.5,
                    min_value=0.0,
                    max_value=1.0,
                )
            ],
        )

    async def test_get_device_when_empty(self, repository: InMemoryDeviceRepository) -> None:
        """Test getting a device when none exists."""
        result = await repository.get_device(EntityId("nonexistent"))
        assert result is None

    async def test_create_device(
        self, repository: InMemoryDeviceRepository, sample_device: Device
    ) -> None:
        """Test creating a device."""
        await repository.create_device(sample_device)
        result = await repository.get_device(sample_device.id)

        assert result is not None
        assert result.id == sample_device.id
        assert result.name == sample_device.name

    async def test_get_devices_by_track(
        self, repository: InMemoryDeviceRepository, sample_device: Device
    ) -> None:
        """Test getting all devices for a track."""
        device2 = Device(
            id=EntityId("device-2"),
            name="Compressor",
            device_type=DeviceType.AUDIO_EFFECT,
            is_enabled=True,
            parameters=[],
        )

        await repository.create_device(sample_device)
        await repository.create_device(device2)

        devices = await repository.get_devices_by_track(EntityId("track-1"))

        assert len(devices) == 2

    async def test_update_device(
        self, repository: InMemoryDeviceRepository, sample_device: Device
    ) -> None:
        """Test updating a device."""
        await repository.create_device(sample_device)

        updated_device = Device(
            id=sample_device.id,
            name="Updated EQ",
            device_type=DeviceType.AUDIO_EFFECT,
            is_enabled=False,
            parameters=[],
        )

        await repository.update_device(updated_device)
        result = await repository.get_device(sample_device.id)

        assert result is not None
        assert result.name == "Updated EQ"
        assert result.is_enabled is False

    async def test_delete_device(
        self, repository: InMemoryDeviceRepository, sample_device: Device
    ) -> None:
        """Test deleting a device."""
        await repository.create_device(sample_device)
        await repository.delete_device(sample_device.id)

        result = await repository.get_device(sample_device.id)
        assert result is None

    async def test_delete_nonexistent_device(self, repository: InMemoryDeviceRepository) -> None:
        """Test deleting a device that doesn't exist."""
        # Should not raise
        await repository.delete_device(EntityId("nonexistent"))


class TestInMemoryClipRepository:
    """Tests for InMemoryClipRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryClipRepository:
        """Create a fresh repository instance."""
        return InMemoryClipRepository()

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
                Note(
                    pitch=60,
                    start=0.0,
                    duration=1.0,
                    velocity=100,
                )
            ],
        )

    async def test_get_clip_when_empty(self, repository: InMemoryClipRepository) -> None:
        """Test getting a clip when none exists."""
        result = await repository.get_clip(EntityId("nonexistent"))
        assert result is None

    async def test_create_clip(self, repository: InMemoryClipRepository, sample_clip: Clip) -> None:
        """Test creating a clip."""
        await repository.create_clip(sample_clip)
        result = await repository.get_clip(sample_clip.id)

        assert result is not None
        assert result.id == sample_clip.id
        assert result.name == sample_clip.name

    async def test_get_clips_by_track(
        self, repository: InMemoryClipRepository, sample_clip: Clip
    ) -> None:
        """Test getting all clips for a track."""
        clip2 = Clip(
            id=EntityId("clip-2"),
            name="Clip 2",
            clip_type=ClipType.AUDIO,
            length=8.0,
            is_playing=False,
            notes=[],
        )

        await repository.create_clip(sample_clip)
        await repository.create_clip(clip2)

        clips = await repository.get_clips_by_track(EntityId("track-1"))

        assert len(clips) == 2

    async def test_update_clip(self, repository: InMemoryClipRepository, sample_clip: Clip) -> None:
        """Test updating a clip."""
        await repository.create_clip(sample_clip)

        updated_clip = Clip(
            id=sample_clip.id,
            name="Updated Clip",
            clip_type=ClipType.MIDI,
            length=8.0,
            is_playing=True,
            notes=[],
        )

        await repository.update_clip(updated_clip)
        result = await repository.get_clip(sample_clip.id)

        assert result is not None
        assert result.name == "Updated Clip"
        assert result.length == 8.0
        assert result.is_playing is True

    async def test_delete_clip(self, repository: InMemoryClipRepository, sample_clip: Clip) -> None:
        """Test deleting a clip."""
        await repository.create_clip(sample_clip)
        await repository.delete_clip(sample_clip.id)

        result = await repository.get_clip(sample_clip.id)
        assert result is None

    async def test_delete_nonexistent_clip(self, repository: InMemoryClipRepository) -> None:
        """Test deleting a clip that doesn't exist."""
        # Should not raise
        await repository.delete_clip(EntityId("nonexistent"))


class TestInMemoryAnalysisRepository:
    """Tests for InMemoryAnalysisRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryAnalysisRepository:
        """Create a fresh repository instance."""
        return InMemoryAnalysisRepository()

    @pytest.fixture
    def sample_analysis(self) -> AnalysisResult:
        """Create a sample analysis result."""
        return AnalysisResult(
            id=EntityId("analysis-1"),
            analysis_type="harmony",
            confidence=0.9,
            data={"key": "C major"},
        )

    async def test_get_analysis_when_empty(self, repository: InMemoryAnalysisRepository) -> None:
        """Test getting an analysis when none exists."""
        result = await repository.get_analysis(EntityId("nonexistent"))
        assert result is None

    async def test_save_analysis(
        self, repository: InMemoryAnalysisRepository, sample_analysis: AnalysisResult
    ) -> None:
        """Test saving an analysis."""
        await repository.save_analysis(sample_analysis)
        result = await repository.get_analysis(sample_analysis.id)

        assert result is not None
        assert result.id == sample_analysis.id
        assert result.analysis_type == sample_analysis.analysis_type

    async def test_get_analyses_by_type(
        self, repository: InMemoryAnalysisRepository, sample_analysis: AnalysisResult
    ) -> None:
        """Test getting analyses by type."""
        analysis2 = AnalysisResult(
            id=EntityId("analysis-2"),
            analysis_type="harmony",
            confidence=0.85,
            data={"key": "G major"},
        )
        analysis3 = AnalysisResult(
            id=EntityId("analysis-3"),
            analysis_type="tempo",
            confidence=0.95,
            data={"bpm": 120},
        )

        await repository.save_analysis(sample_analysis)
        await repository.save_analysis(analysis2)
        await repository.save_analysis(analysis3)

        harmony_results = await repository.get_analyses_by_type("harmony")
        tempo_results = await repository.get_analyses_by_type("tempo")

        assert len(harmony_results) == 2
        assert len(tempo_results) == 1

    async def test_delete_analysis(
        self, repository: InMemoryAnalysisRepository, sample_analysis: AnalysisResult
    ) -> None:
        """Test deleting an analysis."""
        await repository.save_analysis(sample_analysis)
        await repository.delete_analysis(sample_analysis.id)

        result = await repository.get_analysis(sample_analysis.id)
        assert result is None

    async def test_delete_nonexistent_analysis(
        self, repository: InMemoryAnalysisRepository
    ) -> None:
        """Test deleting an analysis that doesn't exist."""
        # Should not raise
        await repository.delete_analysis(EntityId("nonexistent"))


class TestConcurrentAccess:
    """Test concurrent access to repositories."""

    async def test_concurrent_track_operations(self) -> None:
        """Test concurrent track operations are thread-safe."""
        import asyncio

        repository = InMemoryTrackRepository()

        async def create_tracks(start_idx: int) -> None:
            for i in range(10):
                track = Track(
                    id=EntityId(f"track-{start_idx + i}"),
                    name=f"Track {start_idx + i}",
                    track_type=TrackType.MIDI,
                    volume=0.8,
                    pan=0.0,
                    is_muted=False,
                    is_soloed=False,
                    is_armed=False,
                )
                await repository.create_track(track)

        # Run multiple concurrent operations
        await asyncio.gather(
            create_tracks(0),
            create_tracks(100),
            create_tracks(200),
        )

        # Verify all tracks were created
        tracks = await repository.get_tracks_by_song(EntityId("any"))
        assert len(tracks) == 30
