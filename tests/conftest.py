"""Pytest configuration and shared fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from dependency_injector import containers, providers

from ableton_mcp.adapters.service_adapters import (
    AbletonClipService,
    AbletonConnectionService,
    AbletonTrackService,
    AbletonTransportService,
)
from ableton_mcp.application.use_cases import (
    AddNotesUseCase,
    AnalyzeHarmonyUseCase,
    ConnectToAbletonUseCase,
    GetSongInfoUseCase,
    TrackOperationsUseCase,
    TransportControlUseCase,
)
from ableton_mcp.domain.entities import (
    Clip,
    ClipType,
    Device,
    DeviceType,
    Note,
    Song,
    Track,
    TrackType,
    TransportState,
)
from ableton_mcp.domain.ports import AbletonGateway
from ableton_mcp.infrastructure.repositories import (
    InMemoryClipRepository,
    InMemorySongRepository,
    InMemoryTrackRepository,
)
from ableton_mcp.infrastructure.services import MusicTheoryServiceImpl


def create_mock_gateway() -> Mock:
    """Create a mock gateway with all async methods set up."""
    mock = Mock(spec=AbletonGateway)

    # Connection methods
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.is_connected.return_value = True

    # Transport methods
    mock.start_playing = AsyncMock()
    mock.stop_playing = AsyncMock()
    mock.start_recording = AsyncMock()
    mock.stop_recording = AsyncMock()

    # Song queries
    mock.get_tempo = AsyncMock(return_value=120.0)
    mock.set_tempo = AsyncMock()
    mock.get_time_signature = AsyncMock(return_value=(4, 4))
    mock.get_song_time = AsyncMock(return_value=0.0)
    mock.get_num_tracks = AsyncMock(return_value=0)
    mock.get_is_playing = AsyncMock(return_value=False)

    # Track operations
    mock.get_track_name = AsyncMock(return_value="Track")
    mock.set_track_name = AsyncMock()
    mock.get_track_volume = AsyncMock(return_value=0.8)
    mock.set_track_volume = AsyncMock()
    mock.get_track_pan = AsyncMock(return_value=0.0)
    mock.set_track_pan = AsyncMock()
    mock.set_track_mute = AsyncMock()
    mock.set_track_solo = AsyncMock()
    mock.set_track_arm = AsyncMock()
    mock.create_midi_track = AsyncMock(return_value=0)
    mock.create_audio_track = AsyncMock(return_value=0)
    mock.delete_track = AsyncMock()

    # Clip operations
    mock.fire_clip = AsyncMock()
    mock.stop_clip = AsyncMock()
    mock.create_clip = AsyncMock()
    mock.delete_clip = AsyncMock()
    mock.add_note = AsyncMock()
    mock.remove_notes = AsyncMock()
    mock.get_clip_notes = AsyncMock(return_value=[])

    # Device operations
    mock.get_device_parameters = AsyncMock(return_value=[])
    mock.set_device_parameter = AsyncMock()
    mock.bypass_device = AsyncMock()

    return mock


class TestContainer(containers.DeclarativeContainer):
    """Test container with mocked dependencies."""

    # Mock Ableton Gateway
    ableton_gateway = providers.Singleton(create_mock_gateway)

    # Real repositories for testing
    song_repository = providers.Singleton(InMemorySongRepository)
    track_repository = providers.Singleton(InMemoryTrackRepository)
    clip_repository = providers.Singleton(InMemoryClipRepository)

    # Real services for testing
    music_theory_service = providers.Singleton(MusicTheoryServiceImpl)

    # Service adapters with mock gateway
    connection_service = providers.Factory(
        AbletonConnectionService,
        gateway=ableton_gateway
    )
    transport_service = providers.Factory(
        AbletonTransportService,
        gateway=ableton_gateway
    )
    track_service = providers.Factory(
        AbletonTrackService,
        gateway=ableton_gateway
    )
    clip_service = providers.Factory(
        AbletonClipService,
        gateway=ableton_gateway
    )

    # Use cases with dependencies
    connect_use_case = providers.Factory(
        ConnectToAbletonUseCase,
        connection_service=connection_service
    )

    transport_use_case = providers.Factory(
        TransportControlUseCase,
        transport_service=transport_service,
        song_repository=song_repository
    )

    song_info_use_case = providers.Factory(
        GetSongInfoUseCase,
        song_repository=song_repository
    )

    track_ops_use_case = providers.Factory(
        TrackOperationsUseCase,
        track_repository=track_repository,
        song_repository=song_repository,
        track_service=track_service
    )

    add_notes_use_case = providers.Factory(
        AddNotesUseCase,
        clip_repository=clip_repository,
        song_repository=song_repository,
        music_theory_service=music_theory_service,
        clip_service=clip_service
    )

    harmony_analysis_use_case = providers.Factory(
        AnalyzeHarmonyUseCase,
        music_theory_service=music_theory_service
    )


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_container() -> TestContainer:
    """Provide test container with mocked dependencies."""
    container = TestContainer()
    container.wire(modules=["tests"])
    return container


@pytest.fixture
async def song_repository(test_container: TestContainer) -> InMemorySongRepository:
    """Provide song repository."""
    return test_container.song_repository()


@pytest.fixture
async def track_repository(test_container: TestContainer) -> InMemoryTrackRepository:
    """Provide track repository."""
    return test_container.track_repository()


@pytest.fixture
async def clip_repository(test_container: TestContainer) -> InMemoryClipRepository:
    """Provide clip repository."""
    return test_container.clip_repository()


@pytest.fixture
async def music_theory_service(test_container: TestContainer) -> MusicTheoryServiceImpl:
    """Provide music theory service."""
    return test_container.music_theory_service()


@pytest.fixture
def mock_gateway() -> Mock:
    """Provide mocked Ableton gateway."""
    return create_mock_gateway()


@pytest.fixture
def sample_song() -> Song:
    """Provide a sample song for testing."""
    song = Song(
        name="Test Song",
        tempo=120.0,
        time_signature_numerator=4,
        time_signature_denominator=4,
        key="C major",
        transport_state=TransportState.STOPPED
    )

    # Add sample tracks
    midi_track = Track(
        name="MIDI Track",
        track_type=TrackType.MIDI,
        volume=0.8,
        pan=0.0
    )

    audio_track = Track(
        name="Audio Track",
        track_type=TrackType.AUDIO,
        volume=0.7,
        pan=-0.2
    )

    song.add_track(midi_track)
    song.add_track(audio_track)

    return song


@pytest.fixture
def sample_track() -> Track:
    """Provide a sample track for testing."""
    track = Track(
        name="Test Track",
        track_type=TrackType.MIDI,
        volume=0.75,
        pan=0.1
    )

    # Add sample device
    device = Device(
        name="Operator",
        device_type=DeviceType.INSTRUMENT
    )
    track.add_device(device)

    return track


@pytest.fixture
def sample_clip() -> Clip:
    """Provide a sample MIDI clip for testing."""
    clip = Clip(
        name="Test Clip",
        clip_type=ClipType.MIDI,
        length=4.0,
        loop_start=0.0,
        loop_end=4.0
    )

    # Add sample notes
    notes = [
        Note(pitch=60, start=0.0, duration=1.0, velocity=100),  # C4
        Note(pitch=64, start=1.0, duration=1.0, velocity=90),   # E4
        Note(pitch=67, start=2.0, duration=1.0, velocity=95),   # G4
        Note(pitch=72, start=3.0, duration=1.0, velocity=100),  # C5
    ]

    for note in notes:
        clip.add_note(note)

    return clip


@pytest.fixture
def sample_notes() -> list[Note]:
    """Provide sample notes for testing."""
    return [
        Note(pitch=60, start=0.0, duration=1.0, velocity=100),  # C4
        Note(pitch=64, start=1.0, duration=1.0, velocity=90),   # E4
        Note(pitch=67, start=2.0, duration=1.0, velocity=95),   # G4
        Note(pitch=72, start=3.0, duration=1.0, velocity=100),  # C5
    ]


@pytest.fixture
def c_major_notes() -> list[int]:
    """Provide C major scale MIDI notes."""
    return [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
