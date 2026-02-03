"""Unit tests for Ableton OSC gateway."""

import asyncio
from typing import Any, List
from unittest.mock import AsyncMock, Mock, patch

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

    async def test_connect_success(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test successful connection to Ableton."""
        # Set up correlator to return tempo response
        future: asyncio.Future[List[Any]] = asyncio.get_event_loop().create_future()
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
        future: asyncio.Future[List[Any]] = asyncio.get_event_loop().create_future()
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

    async def test_disconnect(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
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

    async def test_get_tempo(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
        """Test getting tempo from Ableton."""
        future: asyncio.Future[List[Any]] = asyncio.get_event_loop().create_future()
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

    async def test_track_operations(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
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

    async def test_add_note(
        self, mock_transport: Mock, mock_correlator: Mock
    ) -> None:
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
            "/live/clip/add_new_notes",
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

        mock_correlator.handle_response.assert_called_once_with(
            "/live/song/get/tempo", [120.0]
        )
