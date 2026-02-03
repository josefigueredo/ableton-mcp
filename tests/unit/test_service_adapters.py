"""Unit tests for service adapters."""

from unittest.mock import AsyncMock, Mock

import pytest

from ableton_mcp.adapters.service_adapters import (
    AbletonClipService,
    AbletonConnectionService,
    AbletonTrackService,
    AbletonTransportService,
)
from ableton_mcp.domain.entities import Note, Track, TrackType
from ableton_mcp.domain.ports import AbletonGateway


class TestAbletonConnectionService:
    """Test cases for connection service adapter."""

    async def test_connect(self) -> None:
        """Test connecting through adapter."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.connect = AsyncMock()

        service = AbletonConnectionService(gateway=mock_gateway)
        await service.connect("localhost", 11000, 11001)

        mock_gateway.connect.assert_called_once_with("localhost", 11000, 11001)

    async def test_disconnect(self) -> None:
        """Test disconnecting through adapter."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.disconnect = AsyncMock()

        service = AbletonConnectionService(gateway=mock_gateway)
        await service.disconnect()

        mock_gateway.disconnect.assert_called_once()

    def test_is_connected(self) -> None:
        """Test checking connection status."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.is_connected.return_value = True

        service = AbletonConnectionService(gateway=mock_gateway)

        assert service.is_connected() is True
        mock_gateway.is_connected.assert_called_once()


class TestAbletonTransportService:
    """Test cases for transport service adapter."""

    async def test_start_playing(self) -> None:
        """Test starting playback."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.start_playing = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.start_playing()

        mock_gateway.start_playing.assert_called_once()

    async def test_stop_playing(self) -> None:
        """Test stopping playback."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_playing = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.stop_playing()

        mock_gateway.stop_playing.assert_called_once()

    async def test_start_recording(self) -> None:
        """Test starting recording."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.start_recording = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.start_recording()

        mock_gateway.start_recording.assert_called_once()

    async def test_stop_recording(self) -> None:
        """Test stopping recording."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_recording = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.stop_recording()

        mock_gateway.stop_recording.assert_called_once()

    async def test_set_tempo(self) -> None:
        """Test setting tempo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_tempo = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.set_tempo(128.0)

        mock_gateway.set_tempo.assert_called_once_with(128.0)


class TestAbletonTrackService:
    """Test cases for track service adapter."""

    async def test_create_midi_track(self) -> None:
        """Test creating MIDI track."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_midi_track = AsyncMock()

        track = Track(name="Test", track_type=TrackType.MIDI)

        service = AbletonTrackService(gateway=mock_gateway)
        await service.create_track(track)

        mock_gateway.create_midi_track.assert_called_once()

    async def test_create_audio_track(self) -> None:
        """Test creating audio track."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_audio_track = AsyncMock()

        track = Track(name="Test", track_type=TrackType.AUDIO)

        service = AbletonTrackService(gateway=mock_gateway)
        await service.create_track(track)

        mock_gateway.create_audio_track.assert_called_once()

    async def test_set_track_volume(self) -> None:
        """Test setting track volume."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_volume = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_volume(0, 0.8)

        mock_gateway.set_track_volume.assert_called_once_with(0, 0.8)

    async def test_set_track_pan(self) -> None:
        """Test setting track pan."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_pan = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_pan(0, -0.5)

        mock_gateway.set_track_pan.assert_called_once_with(0, -0.5)

    async def test_set_track_mute(self) -> None:
        """Test setting track mute."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_mute = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_mute(0, True)

        mock_gateway.set_track_mute.assert_called_once_with(0, True)

    async def test_set_track_solo(self) -> None:
        """Test setting track solo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_solo = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_solo(0, True)

        mock_gateway.set_track_solo.assert_called_once_with(0, True)

    async def test_set_track_arm(self) -> None:
        """Test setting track arm."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_arm = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_arm(0, True)

        mock_gateway.set_track_arm.assert_called_once_with(0, True)


class TestAbletonClipService:
    """Test cases for clip service adapter."""

    async def test_fire_clip(self) -> None:
        """Test firing a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.fire_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.fire_clip(0, 0)

        mock_gateway.fire_clip.assert_called_once_with(0, 0)

    async def test_stop_clip(self) -> None:
        """Test stopping a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.stop_clip(0, 0)

        mock_gateway.stop_clip.assert_called_once_with(0, 0)

    async def test_add_note(self) -> None:
        """Test adding a note to a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.add_note = AsyncMock()

        note = Note(pitch=60, start=0.0, duration=1.0, velocity=100, mute=False)

        service = AbletonClipService(gateway=mock_gateway)
        await service.add_note(0, 0, note)

        mock_gateway.add_note.assert_called_once_with(
            track_id=0,
            clip_id=0,
            pitch=60,
            start=0.0,
            duration=1.0,
            velocity=100,
            mute=False,
        )

    async def test_create_clip(self) -> None:
        """Test creating a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.create_clip(0, 0, 4.0)

        mock_gateway.create_clip.assert_called_once_with(0, 0, 4.0)

    async def test_delete_clip(self) -> None:
        """Test deleting a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.delete_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.delete_clip(0, 0)

        mock_gateway.delete_clip.assert_called_once_with(0, 0)
