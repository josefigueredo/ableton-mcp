"""Async UDP transport for OSC communication using asyncio.DatagramProtocol."""

import asyncio
from typing import Any, Callable, List, Optional, Tuple

import structlog
from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_bundle import OscBundle

logger = structlog.get_logger(__name__)


class OSCProtocol(asyncio.DatagramProtocol):
    """Asyncio datagram protocol for receiving OSC messages."""

    def __init__(
        self,
        message_handler: Callable[[str, List[Any]], None],
    ) -> None:
        """Initialize the protocol.

        Args:
            message_handler: Callback for received OSC messages (address, args)
        """
        self._message_handler = message_handler
        self._transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:  # type: ignore[override]
        """Called when connection is established."""
        self._transport = transport
        logger.debug("OSC receiver connection established")

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Called when a datagram is received."""
        try:
            self._parse_and_dispatch(data)
        except Exception as e:
            logger.error("Failed to parse OSC message", error=str(e), addr=addr)

    def _parse_and_dispatch(self, data: bytes) -> None:
        """Parse OSC data and dispatch to handler."""
        if data.startswith(b"#bundle"):
            bundle = OscBundle(data)
            for content in bundle:
                if isinstance(content, OscMessage):
                    self._dispatch_message(content)
        else:
            message = OscMessage(data)
            self._dispatch_message(message)

    def _dispatch_message(self, message: OscMessage) -> None:
        """Dispatch a parsed OSC message to the handler."""
        logger.debug(
            "Received OSC message",
            address=message.address,
            args=message.params,
        )
        self._message_handler(message.address, list(message.params))

    def error_received(self, exc: Exception) -> None:
        """Called when an error is received."""
        logger.error("OSC protocol error", error=str(exc))

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Called when connection is lost."""
        if exc:
            logger.warning("OSC connection lost", error=str(exc))
        else:
            logger.debug("OSC connection closed")


class AsyncOSCTransport:
    """Async OSC transport managing send and receive endpoints."""

    def __init__(self) -> None:
        self._send_transport: Optional[asyncio.DatagramTransport] = None
        self._receive_transport: Optional[asyncio.DatagramTransport] = None
        self._protocol: Optional[OSCProtocol] = None
        self._host: str = "127.0.0.1"
        self._send_port: int = 11000
        self._receive_port: int = 11001
        self._connected: bool = False

    async def connect(
        self,
        host: str,
        send_port: int,
        receive_port: int,
        message_handler: Callable[[str, List[Any]], None],
    ) -> None:
        """Establish OSC connection.

        Args:
            host: Target host IP
            send_port: Port to send messages to
            receive_port: Port to receive messages on
            message_handler: Callback for received messages
        """
        # Clean up existing connection first to allow reconnection
        if self._connected:
            logger.debug("Closing existing connection before reconnecting")
            await self.disconnect()

        self._host = host
        self._send_port = send_port
        self._receive_port = receive_port

        loop = asyncio.get_running_loop()

        # Create send endpoint (client)
        self._send_transport, _ = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(host, send_port),
        )

        # Create receive endpoint (server)
        self._receive_transport, self._protocol = await loop.create_datagram_endpoint(
            lambda: OSCProtocol(message_handler),
            local_addr=("0.0.0.0", receive_port),
        )

        self._connected = True
        logger.info(
            "OSC transport connected",
            host=host,
            send_port=send_port,
            receive_port=receive_port,
        )

    async def disconnect(self) -> None:
        """Close OSC connection."""
        if self._send_transport:
            self._send_transport.close()
            self._send_transport = None

        if self._receive_transport:
            self._receive_transport.close()
            self._receive_transport = None

        self._protocol = None
        self._connected = False
        logger.info("OSC transport disconnected")

    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected

    def send(self, address: str, args: List[Any]) -> None:
        """Send an OSC message.

        Args:
            address: OSC address pattern (e.g., "/live/song/start_playing")
            args: Message arguments

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or not self._send_transport:
            raise RuntimeError("Transport not connected")

        builder = OscMessageBuilder(address=address)
        for arg in args:
            builder.add_arg(arg)

        message = builder.build()
        self._send_transport.sendto(message.dgram)

        logger.debug("Sent OSC message", address=address, args=args)
