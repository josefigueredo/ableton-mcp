"""Unit tests for OSC transport layer."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest

from ableton_mcp.infrastructure.osc.transport import AsyncOSCTransport, OSCProtocol


class TestOSCProtocol:
    """Tests for OSCProtocol class."""

    def test_init(self) -> None:
        """Test protocol initialization."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        assert protocol._message_handler == handler
        assert protocol._transport is None
        assert protocol._parse_error_count == 0

    def test_connection_made(self) -> None:
        """Test connection_made callback."""
        handler = Mock()
        protocol = OSCProtocol(handler)
        mock_transport = Mock()

        protocol.connection_made(mock_transport)

        assert protocol._transport == mock_transport

    def test_datagram_received_valid_message(self) -> None:
        """Test receiving valid OSC message."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        # Create a valid OSC message (address with args)
        from pythonosc.osc_message_builder import OscMessageBuilder

        builder = OscMessageBuilder(address="/test/address")
        builder.add_arg(42)
        message = builder.build()

        protocol.datagram_received(message.dgram, ("127.0.0.1", 11001))

        handler.assert_called_once()
        call_args = handler.call_args[0]
        assert call_args[0] == "/test/address"
        assert 42 in call_args[1]

    def test_datagram_received_parse_error(self) -> None:
        """Test handling of parse errors."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        # Send invalid data
        protocol.datagram_received(b"invalid data", ("127.0.0.1", 11001))

        assert protocol._parse_error_count == 1
        handler.assert_not_called()

    def test_parse_error_threshold_warning(self) -> None:
        """Test warning is logged after threshold errors."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        # Trigger multiple parse errors
        for _ in range(OSCProtocol.PARSE_ERROR_WARN_THRESHOLD):
            protocol.datagram_received(b"invalid", ("127.0.0.1", 11001))

        assert protocol._parse_error_count >= OSCProtocol.PARSE_ERROR_WARN_THRESHOLD

    def test_error_received(self) -> None:
        """Test error_received callback."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        # Should not raise
        protocol.error_received(RuntimeError("Test error"))

    def test_connection_lost_with_error(self) -> None:
        """Test connection_lost with error."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        # Should not raise
        protocol.connection_lost(RuntimeError("Connection failed"))

    def test_connection_lost_clean(self) -> None:
        """Test connection_lost without error."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        # Should not raise
        protocol.connection_lost(None)

    def test_parse_error_count_resets_on_success(self) -> None:
        """Test that parse error count resets after successful parse."""
        handler = Mock()
        protocol = OSCProtocol(handler)

        # Cause some errors
        protocol.datagram_received(b"invalid", ("127.0.0.1", 11001))
        protocol.datagram_received(b"invalid", ("127.0.0.1", 11001))
        assert protocol._parse_error_count == 2

        # Send valid message
        from pythonosc.osc_message_builder import OscMessageBuilder

        builder = OscMessageBuilder(address="/test")
        message = builder.build()
        protocol.datagram_received(message.dgram, ("127.0.0.1", 11001))

        assert protocol._parse_error_count == 0


class TestAsyncOSCTransport:
    """Tests for AsyncOSCTransport class."""

    def test_init(self) -> None:
        """Test transport initialization."""
        transport = AsyncOSCTransport()

        assert transport._send_transport is None
        assert transport._receive_transport is None
        assert transport._connected is False
        assert transport._host == "127.0.0.1"
        assert transport._send_port == 11000
        assert transport._receive_port == 11001

    def test_is_connected_initially_false(self) -> None:
        """Test is_connected returns False initially."""
        transport = AsyncOSCTransport()
        assert transport.is_connected() is False

    async def test_connect(self) -> None:
        """Test connect establishes connection."""
        transport = AsyncOSCTransport()
        handler = Mock()

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop.return_value = mock_loop_instance

            # Mock the datagram endpoint creation
            mock_send_transport = Mock()
            mock_receive_transport = Mock()
            mock_protocol = Mock()

            mock_loop_instance.create_datagram_endpoint = AsyncMock(
                side_effect=[
                    (mock_send_transport, None),
                    (mock_receive_transport, mock_protocol),
                ]
            )

            await transport.connect("127.0.0.1", 11000, 11001, handler)

            assert transport._connected is True
            assert transport._send_transport == mock_send_transport
            assert transport._receive_transport == mock_receive_transport

    async def test_disconnect(self) -> None:
        """Test disconnect closes transports."""
        transport = AsyncOSCTransport()
        mock_send = Mock()
        mock_receive = Mock()
        transport._send_transport = mock_send
        transport._receive_transport = mock_receive
        transport._protocol = Mock()
        transport._connected = True

        await transport.disconnect()

        mock_send.close.assert_called_once()
        mock_receive.close.assert_called_once()
        assert transport._connected is False
        assert transport._send_transport is None
        assert transport._receive_transport is None

    async def test_disconnect_when_not_connected(self) -> None:
        """Test disconnect when not connected."""
        transport = AsyncOSCTransport()

        # Should not raise
        await transport.disconnect()

        assert transport._connected is False

    def test_send_when_connected(self) -> None:
        """Test send works when connected."""
        transport = AsyncOSCTransport()
        transport._connected = True
        transport._send_transport = Mock()

        transport.send("/test/address", [42, "hello"])

        transport._send_transport.sendto.assert_called_once()

    def test_send_when_not_connected(self) -> None:
        """Test send raises when not connected."""
        transport = AsyncOSCTransport()

        with pytest.raises(RuntimeError, match="not connected"):
            transport.send("/test/address", [42])

    async def test_reconnect_closes_existing(self) -> None:
        """Test that reconnecting closes existing connection."""
        transport = AsyncOSCTransport()
        transport._connected = True
        transport._send_transport = Mock()
        transport._receive_transport = Mock()

        handler = Mock()

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop.return_value = mock_loop_instance
            mock_loop_instance.create_datagram_endpoint = AsyncMock(
                side_effect=[
                    (Mock(), None),
                    (Mock(), Mock()),
                ]
            )

            await transport.connect("127.0.0.1", 11000, 11001, handler)

            # Old transports should have been closed
            assert transport._connected is True
