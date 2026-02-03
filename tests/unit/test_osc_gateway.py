"""Unit tests for Ableton OSC gateway."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from ableton_mcp.core.exceptions import ConnectionError, OSCCommunicationError
from ableton_mcp.infrastructure.osc.correlator import OSCCorrelator
from ableton_mcp.infrastructure.osc.gateway import AbletonOSCGateway
from ableton_mcp.infrastructure.osc.transport import AsyncOSCTransport


class TestAbletonOSCGateway:
    """Test cases for AbletonOSCGateway."""

    @pytest.fixture
    def mock_transport(self) -> Mock:
        """Create a mock transport."""
        transport = Mock(spec=AsyncOSCTransport)
        transport.connect = AsyncMock()
        transport.disconnect = AsyncMock()
        transport.is_connected.return_value = True
        transport.send = Mock()
        return transport

    @pytest.fixture
    def mock_correlator(self) -> Mock:
        """Create a mock correlator."""
        correlator = Mock(spec=OSCCorrelator)
        correlator.expect_response = AsyncMock()
        correlator.handle_response = Mock()
        correlator.cancel_all = Mock()
        return correlator

    async def test_connect_success(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test successful connection to Ableton."""
        # Set up correlator to return tempo response
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([120.0])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        await gateway.connect("127.0.0.1", 11000, 11001)

        mock_transport.connect.assert_called_once()
        assert gateway.is_connected()

    async def test_connect_timeout_raises_error(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test connection times out when Ableton doesn't respond."""
        # Set up correlator to return a future that never completes
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=0.1,
        )

        with pytest.raises(ConnectionError) as exc_info:
            await gateway.connect("127.0.0.1", 11000, 11001)

        assert "not responding" in str(exc_info.value)
        # Should disconnect after timeout
        mock_transport.disconnect.assert_called_once()

    async def test_disconnect(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test disconnection."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.disconnect()

        mock_correlator.cancel_all.assert_called_once()
        mock_transport.disconnect.assert_called_once()

    async def test_fire_and_forget_operations(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test fire-and-forget transport operations."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        # Test transport controls
        await gateway.start_playing()
        mock_transport.send.assert_called_with("/live/song/start_playing", [])

        await gateway.stop_playing()
        mock_transport.send.assert_called_with("/live/song/stop_playing", [])

        await gateway.start_recording()
        mock_transport.send.assert_called_with("/live/song/start_recording", [])

        await gateway.stop_recording()
        mock_transport.send.assert_called_with("/live/song/stop_recording", [])

    async def test_fire_and_forget_when_disconnected(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test that operations fail when disconnected."""
        mock_transport.is_connected.return_value = False

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.start_playing()

        assert "Not connected" in str(exc_info.value)

    async def test_get_tempo(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting tempo from Ableton."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([120.0])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        tempo = await gateway.get_tempo()

        assert tempo == 120.0
        mock_transport.send.assert_called_with("/live/song/get/tempo", [])
        mock_correlator.expect_response.assert_called_with("/live/song/get/tempo")

    async def test_set_tempo_validates_range(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test that set_tempo validates BPM range."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.set_tempo(10.0)  # Too low

        assert "20 and 999" in str(exc_info.value)

        with pytest.raises(OSCCommunicationError):
            await gateway.set_tempo(1000.0)  # Too high

    async def test_track_operations(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test track operation methods."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        # Test volume
        await gateway.set_track_volume(0, 0.8)
        mock_transport.send.assert_called_with("/live/track/set/volume", [0, 0.8])

        # Test pan
        await gateway.set_track_pan(0, -0.5)
        mock_transport.send.assert_called_with("/live/track/set/panning", [0, -0.5])

        # Test mute
        await gateway.set_track_mute(0, True)
        mock_transport.send.assert_called_with("/live/track/set/mute", [0, 1])

        # Test solo
        await gateway.set_track_solo(0, True)
        mock_transport.send.assert_called_with("/live/track/set/solo", [0, 1])

        # Test arm
        await gateway.set_track_arm(0, True)
        mock_transport.send.assert_called_with("/live/track/set/arm", [0, 1])

    async def test_track_volume_validates_range(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test that track volume validates range."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        with pytest.raises(OSCCommunicationError):
            await gateway.set_track_volume(0, 1.5)  # Too high

        with pytest.raises(OSCCommunicationError):
            await gateway.set_track_volume(0, -0.1)  # Too low

    async def test_track_pan_validates_range(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test that track pan validates range."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        with pytest.raises(OSCCommunicationError):
            await gateway.set_track_pan(0, 1.5)  # Too high

        with pytest.raises(OSCCommunicationError):
            await gateway.set_track_pan(0, -1.5)  # Too low

    async def test_add_note(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test adding a MIDI note."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.add_note(
            track_id=0,
            clip_id=0,
            pitch=60,
            start=0.0,
            duration=1.0,
            velocity=100,
            mute=False,
        )

        mock_transport.send.assert_called_with(
            "/live/clip/add/notes",
            [0, 0, 60, 0.0, 1.0, 100, 0],
        )

    async def test_message_handler_dispatches_to_correlator(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test that incoming messages are dispatched to correlator."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        # Simulate message received
        gateway._handle_osc_message("/live/song/get/tempo", [120.0])

        mock_correlator.handle_response.assert_called_once_with("/live/song/get/tempo", [120.0])

    async def test_connect_cleanup_error_is_logged(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test that cleanup errors during connection timeout are handled."""
        # Set up correlator to return a future that never completes
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        mock_correlator.expect_response.return_value = future
        # Make disconnect raise an error
        mock_transport.disconnect = AsyncMock(side_effect=RuntimeError("Cleanup failed"))

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=0.1,
        )

        with pytest.raises(ConnectionError) as exc_info:
            await gateway.connect("127.0.0.1", 11000, 11001)

        assert "not responding" in str(exc_info.value)

    async def test_connect_os_error(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test OSError during connection."""
        mock_transport.connect = AsyncMock(side_effect=OSError("Network error"))

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        with pytest.raises(ConnectionError) as exc_info:
            await gateway.connect("127.0.0.1", 11000, 11001)

        assert "Failed to connect" in str(exc_info.value)

    async def test_request_when_not_connected(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test that _request raises when not connected."""
        mock_transport.is_connected.return_value = False

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_tempo()

        assert "Not connected" in str(exc_info.value)

    async def test_get_tempo_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test get_tempo with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_tempo()

        assert "Empty response" in str(exc_info.value)

    async def test_set_tempo_valid(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test setting valid tempo."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.set_tempo(140.0)

        mock_transport.send.assert_called_with("/live/song/set/tempo", [140.0])

    async def test_get_time_signature(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting time signature."""
        future_num: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future_num.set_result([4])
        future_denom: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future_denom.set_result([4])

        mock_correlator.expect_response.side_effect = [future_num, future_denom]

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        numerator, denominator = await gateway.get_time_signature()

        assert numerator == 4
        assert denominator == 4

    async def test_get_time_signature_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test get_time_signature with empty response."""
        future_num: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future_num.set_result([])
        future_denom: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future_denom.set_result([])

        mock_correlator.expect_response.side_effect = [future_num, future_denom]

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_time_signature()

        assert "Empty response" in str(exc_info.value)

    async def test_get_song_time(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting song time."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([8.5])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        song_time = await gateway.get_song_time()

        assert song_time == 8.5

    async def test_get_song_time_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test get_song_time with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_song_time()

        assert "Empty response" in str(exc_info.value)

    async def test_get_num_tracks(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting number of tracks."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([8])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        num_tracks = await gateway.get_num_tracks()

        assert num_tracks == 8

    async def test_get_num_tracks_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test get_num_tracks with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_num_tracks()

        assert "Empty response" in str(exc_info.value)

    async def test_get_is_playing(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test checking if playing."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        is_playing = await gateway.get_is_playing()

        assert is_playing is True

    async def test_get_is_playing_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test get_is_playing with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_is_playing()

        assert "Empty response" in str(exc_info.value)

    async def test_get_track_name(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting track name."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, "Bass"])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        name = await gateway.get_track_name(0)

        assert name == "Bass"

    async def test_get_track_name_single_value_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track name with single value response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result(["Drums"])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        name = await gateway.get_track_name(0)

        assert name == "Drums"

    async def test_get_track_name_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track name with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_track_name(0)

        assert "Empty response" in str(exc_info.value)

    async def test_set_track_name(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test setting track name."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.set_track_name(0, "Lead Synth")

        mock_transport.send.assert_called_with("/live/track/set/name", [0, "Lead Synth"])

    async def test_get_track_volume(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting track volume."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, 0.75])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        volume = await gateway.get_track_volume(0)

        assert volume == 0.75

    async def test_get_track_volume_single_value_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track volume with single value response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0.5])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        volume = await gateway.get_track_volume(0)

        assert volume == 0.5

    async def test_get_track_volume_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track volume with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_track_volume(0)

        assert "Empty response" in str(exc_info.value)

    async def test_get_track_pan(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting track pan."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, -0.3])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        pan = await gateway.get_track_pan(0)

        assert pan == -0.3

    async def test_get_track_pan_single_value_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track pan with single value response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0.5])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        pan = await gateway.get_track_pan(0)

        assert pan == 0.5

    async def test_get_track_pan_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track pan with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        with pytest.raises(OSCCommunicationError) as exc_info:
            await gateway.get_track_pan(0)

        assert "Empty response" in str(exc_info.value)

    async def test_get_track_mute(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting track mute state."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, 1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        muted = await gateway.get_track_mute(0)

        assert muted is True

    async def test_get_track_mute_single_value_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track mute with single value response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        muted = await gateway.get_track_mute(0)

        assert muted is False

    async def test_get_track_mute_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track mute with empty response returns False."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        muted = await gateway.get_track_mute(0)

        assert muted is False

    async def test_get_track_solo(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting track solo state."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, 1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        soloed = await gateway.get_track_solo(0)

        assert soloed is True

    async def test_get_track_solo_single_value_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track solo with single value response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        soloed = await gateway.get_track_solo(0)

        assert soloed is True

    async def test_get_track_solo_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track solo with empty response returns False."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        soloed = await gateway.get_track_solo(0)

        assert soloed is False

    async def test_get_track_arm(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting track arm state."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, 1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        armed = await gateway.get_track_arm(0)

        assert armed is True

    async def test_get_track_arm_single_value_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track arm with single value response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        armed = await gateway.get_track_arm(0)

        assert armed is False

    async def test_get_track_arm_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting track arm with empty response returns False."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        armed = await gateway.get_track_arm(0)

        assert armed is False

    async def test_get_track_has_midi_input(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test checking if track has MIDI input."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, 1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        has_midi = await gateway.get_track_has_midi_input(0)

        assert has_midi is True

    async def test_get_track_has_midi_input_single_value_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test track MIDI input with single value response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        has_midi = await gateway.get_track_has_midi_input(0)

        assert has_midi is True

    async def test_get_track_has_midi_input_empty_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test track MIDI input with empty response returns False."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        has_midi = await gateway.get_track_has_midi_input(0)

        assert has_midi is False

    async def test_create_midi_track(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test creating MIDI track."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.create_midi_track(2)

        mock_transport.send.assert_called_with("/live/song/create_midi_track", [2])

    async def test_create_audio_track(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test creating audio track."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.create_audio_track(3)

        mock_transport.send.assert_called_with("/live/song/create_audio_track", [3])

    async def test_delete_track(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test deleting track."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.delete_track(1)

        mock_transport.send.assert_called_with("/live/song/delete_track", [1])

    async def test_fire_clip(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test firing a clip."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.fire_clip(0, 1)

        mock_transport.send.assert_called_with("/live/clip_slot/fire", [0, 1])

    async def test_stop_clip(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test stopping a clip."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.stop_clip(0, 1)

        mock_transport.send.assert_called_with("/live/clip_slot/stop", [0, 1])

    async def test_create_clip(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test creating a clip."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.create_clip(0, 1, 4.0)

        mock_transport.send.assert_called_with("/live/clip_slot/create_clip", [0, 1, 4.0])

    async def test_delete_clip(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test deleting a clip."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.delete_clip(0, 1)

        mock_transport.send.assert_called_with("/live/clip_slot/delete_clip", [0, 1])

    async def test_add_note_with_mute(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test adding a muted MIDI note."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.add_note(
            track_id=0,
            clip_id=0,
            pitch=64,
            start=1.0,
            duration=0.5,
            velocity=80,
            mute=True,
        )

        mock_transport.send.assert_called_with(
            "/live/clip/add/notes",
            [0, 0, 64, 1.0, 0.5, 80, 1],
        )

    async def test_remove_notes(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test removing notes from a clip."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.remove_notes(
            track_id=0,
            clip_id=0,
            start_time=0.0,
            time_span=4.0,
            pitch_start=60,
            pitch_span=12,
        )

        mock_transport.send.assert_called_with(
            "/live/clip/remove_notes",
            [0, 0, 0.0, 4.0, 60, 12],
        )

    async def test_get_clip_notes(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting clip notes."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        # Response format: [track_id, clip_id, pitch, start, duration, velocity, mute, ...]
        future.set_result([0, 0, 60, 0.0, 1.0, 100, 0, 64, 1.0, 0.5, 80, 1])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        notes = await gateway.get_clip_notes(0, 0)

        assert len(notes) == 2
        assert notes[0]["pitch"] == 60
        assert notes[0]["start"] == 0.0
        assert notes[0]["duration"] == 1.0
        assert notes[0]["velocity"] == 100
        assert notes[0]["mute"] is False
        assert notes[1]["pitch"] == 64
        assert notes[1]["mute"] is True

    async def test_get_clip_notes_empty(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting notes from empty clip."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([0, 0])  # Just track_id and clip_id
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        notes = await gateway.get_clip_notes(0, 0)

        assert len(notes) == 0

    async def test_get_clip_notes_no_response(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting notes with no response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        notes = await gateway.get_clip_notes(0, 0)

        assert len(notes) == 0

    async def test_get_device_parameters(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test getting device parameters."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        # Response format: [param_count, id1, name1, value1, min1, max1, ...]
        future.set_result([2, 0, "Freq", 1000.0, 20.0, 20000.0, 1, "Gain", 0.5, 0.0, 1.0])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        params = await gateway.get_device_parameters(0, 0)

        assert len(params) == 2
        assert params[0]["id"] == 0
        assert params[0]["name"] == "Freq"
        assert params[0]["value"] == 1000.0
        assert params[0]["min"] == 20.0
        assert params[0]["max"] == 20000.0
        assert params[1]["id"] == 1
        assert params[1]["name"] == "Gain"

    async def test_get_device_parameters_empty(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting device parameters with empty response."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=1.0,
        )

        params = await gateway.get_device_parameters(0, 0)

        assert len(params) == 0

    async def test_set_device_parameter(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test setting device parameter."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.set_device_parameter(0, 0, 1, 0.75)

        mock_transport.send.assert_called_with(
            "/live/device/set/parameter/value",
            [0, 0, 1, 0.75],
        )

    async def test_bypass_device(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test bypassing a device."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.bypass_device(0, 0, True)

        mock_transport.send.assert_called_with(
            "/live/device/set/enabled",
            [0, 0, 0],  # 0 means bypassed/disabled
        )

    async def test_enable_device(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test enabling a device."""
        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
        )

        await gateway.bypass_device(0, 0, False)

        mock_transport.send.assert_called_with(
            "/live/device/set/enabled",
            [0, 0, 1],  # 1 means enabled
        )

    async def test_request_timeout(self, mock_transport: Mock, mock_correlator: Mock) -> None:
        """Test request timeout handling."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=0.1,
        )

        with pytest.raises(asyncio.TimeoutError):
            await gateway.get_tempo()

    async def test_request_custom_timeout(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test request with custom timeout."""
        future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
        future.set_result([120.0])
        mock_correlator.expect_response.return_value = future

        gateway = AbletonOSCGateway(
            transport=mock_transport,
            correlator=mock_correlator,
            default_timeout=10.0,  # Long default timeout
        )

        # Should complete quickly since future is already resolved
        tempo = await gateway.get_tempo()

        assert tempo == 120.0
