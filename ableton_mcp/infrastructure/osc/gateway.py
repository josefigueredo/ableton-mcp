"""AbletonOSCGateway - High-level async Ableton communication via OSC.

This implements the AbletonGateway port defined in the domain layer.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import structlog

from ableton_mcp.core.exceptions import ConnectionError, OSCCommunicationError
from ableton_mcp.domain.ports import AbletonGateway
from ableton_mcp.infrastructure.osc.correlator import OSCCorrelator
from ableton_mcp.infrastructure.osc.transport import AsyncOSCTransport

logger = structlog.get_logger(__name__)


class AbletonOSCGateway(AbletonGateway):
    """High-level async gateway to Ableton Live via OSC.

    Composes the transport and correlator to provide a clean async API
    that implements the AbletonGateway port.
    """

    def __init__(
        self,
        transport: Optional[AsyncOSCTransport] = None,
        correlator: Optional[OSCCorrelator] = None,
        default_timeout: float = 5.0,
    ) -> None:
        """Initialize the gateway.

        Args:
            transport: Optional transport instance (created if not provided)
            correlator: Optional correlator instance (created if not provided)
            default_timeout: Default timeout for request-response operations
        """
        self._transport = transport or AsyncOSCTransport()
        self._correlator = correlator or OSCCorrelator(default_timeout=default_timeout)
        self._default_timeout = default_timeout

    def _handle_osc_message(self, address: str, args: List[Any]) -> None:
        """Handle incoming OSC messages from transport."""
        self._correlator.handle_response(address, args)

    # Connection lifecycle

    async def connect(self, host: str, send_port: int, receive_port: int) -> None:
        """Establish connection to Ableton Live."""
        try:
            await self._transport.connect(
                host=host,
                send_port=send_port,
                receive_port=receive_port,
                message_handler=self._handle_osc_message,
            )

            # Test connection by requesting tempo
            try:
                tempo = await self.get_tempo()
                logger.info(
                    "Connected to Ableton Live",
                    host=host,
                    send_port=send_port,
                    receive_port=receive_port,
                    tempo=tempo,
                )
            except asyncio.TimeoutError:
                # Ensure cleanup even if disconnect fails
                try:
                    await self._transport.disconnect()
                except Exception as cleanup_error:
                    logger.error(
                        "Failed to cleanup after connection timeout",
                        error=str(cleanup_error),
                    )
                raise ConnectionError(
                    "Ableton Live not responding. Is AbletonOSC installed and enabled?"
                )

        except OSError as e:
            raise ConnectionError(f"Failed to connect to Ableton Live: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Ableton Live."""
        self._correlator.cancel_all()
        await self._transport.disconnect()
        logger.info("Disconnected from Ableton Live")

    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._transport.is_connected()

    # Internal helpers

    def _send(self, address: str, args: Optional[List[Any]] = None) -> None:
        """Send an OSC message without waiting for response."""
        if not self.is_connected():
            raise OSCCommunicationError("Not connected to Ableton Live")
        self._transport.send(address, args or [])

    async def _request(
        self,
        address: str,
        args: Optional[List[Any]] = None,
        timeout: Optional[float] = None,
    ) -> List[Any]:
        """Send request and wait for response.

        Args:
            address: OSC address to send to
            args: Optional message arguments
            timeout: Optional timeout override

        Returns:
            Response arguments

        Raises:
            OSCCommunicationError: If not connected or communication fails
            asyncio.TimeoutError: If response not received in time
        """
        if not self.is_connected():
            raise OSCCommunicationError("Not connected to Ableton Live")

        # Register expectation before sending
        future = await self._correlator.expect_response(address)

        # Send the request
        self._transport.send(address, args or [])

        # Wait for response
        effective_timeout = timeout if timeout is not None else self._default_timeout
        try:
            return await asyncio.wait_for(future, timeout=effective_timeout)
        except asyncio.TimeoutError:
            logger.warning("Request timed out", address=address, timeout=effective_timeout)
            raise

    # Transport control (fire-and-forget commands)
    # These are async for interface consistency but execute synchronously.
    # No confirmation is received from Ableton - commands are sent immediately.

    async def start_playing(self) -> None:
        """Start playback (fire-and-forget, no confirmation)."""
        self._send("/live/song/start_playing")

    async def stop_playing(self) -> None:
        """Stop playback (fire-and-forget, no confirmation)."""
        self._send("/live/song/stop_playing")

    async def start_recording(self) -> None:
        """Start recording (fire-and-forget, no confirmation)."""
        self._send("/live/song/start_recording")

    async def stop_recording(self) -> None:
        """Stop recording (fire-and-forget, no confirmation)."""
        self._send("/live/song/stop_recording")

    # Song queries (request-response)

    async def get_tempo(self) -> float:
        """Get current song tempo in BPM."""
        response = await self._request("/live/song/get/tempo")
        if not response:
            raise OSCCommunicationError("Empty response from Ableton Live for tempo")
        return float(response[0])

    async def set_tempo(self, bpm: float) -> None:
        """Set song tempo (fire-and-forget, no confirmation)."""
        if not 20.0 <= bpm <= 999.0:
            raise OSCCommunicationError("Tempo must be between 20 and 999 BPM")
        self._send("/live/song/set/tempo", [bpm])

    async def get_time_signature(self) -> Tuple[int, int]:
        """Get time signature as (numerator, denominator)."""
        num_response = await self._request("/live/song/get/signature_numerator")
        denom_response = await self._request("/live/song/get/signature_denominator")
        if not num_response or not denom_response:
            raise OSCCommunicationError("Empty response from Ableton Live for time signature")
        return int(num_response[0]), int(denom_response[0])

    async def get_song_time(self) -> float:
        """Get current song position in beats."""
        response = await self._request("/live/song/get/current_song_time")
        if not response:
            raise OSCCommunicationError("Empty response from Ableton Live for song time")
        return float(response[0])

    async def get_num_tracks(self) -> int:
        """Get total number of tracks."""
        response = await self._request("/live/song/get/num_tracks")
        if not response:
            raise OSCCommunicationError("Empty response from Ableton Live for num_tracks")
        return int(response[0])

    async def get_is_playing(self) -> bool:
        """Check if transport is playing."""
        response = await self._request("/live/song/get/is_playing")
        if not response:
            raise OSCCommunicationError("Empty response from Ableton Live for is_playing")
        return bool(response[0])

    # Track operations

    async def get_track_name(self, track_id: int) -> str:
        """Get track name."""
        response = await self._request("/live/track/get/name", [track_id])
        if not response:
            raise OSCCommunicationError(f"Empty response from Ableton Live for track {track_id} name")
        # Response format: [track_id, name]
        return str(response[1]) if len(response) > 1 else str(response[0])

    async def set_track_name(self, track_id: int, name: str) -> None:
        """Set track name (fire-and-forget, no confirmation)."""
        self._send("/live/track/set/name", [track_id, name])

    async def get_track_volume(self, track_id: int) -> float:
        """Get track volume (0.0-1.0)."""
        response = await self._request("/live/track/get/volume", [track_id])
        if not response:
            raise OSCCommunicationError(f"Empty response from Ableton Live for track {track_id} volume")
        # Response format: [track_id, volume]
        return float(response[1]) if len(response) > 1 else float(response[0])

    async def set_track_volume(self, track_id: int, volume: float) -> None:
        """Set track volume (0.0-1.0, fire-and-forget, no confirmation)."""
        if not 0.0 <= volume <= 1.0:
            raise OSCCommunicationError("Volume must be between 0.0 and 1.0")
        self._send("/live/track/set/volume", [track_id, volume])

    async def get_track_pan(self, track_id: int) -> float:
        """Get track pan (-1.0 to 1.0)."""
        response = await self._request("/live/track/get/panning", [track_id])
        if not response:
            raise OSCCommunicationError(f"Empty response from Ableton Live for track {track_id} pan")
        # Response format: [track_id, pan]
        return float(response[1]) if len(response) > 1 else float(response[0])

    async def set_track_pan(self, track_id: int, pan: float) -> None:
        """Set track pan (-1.0 to 1.0, fire-and-forget, no confirmation)."""
        if not -1.0 <= pan <= 1.0:
            raise OSCCommunicationError("Pan must be between -1.0 and 1.0")
        self._send("/live/track/set/panning", [track_id, pan])

    async def get_track_mute(self, track_id: int) -> bool:
        """Get track mute state."""
        response = await self._request("/live/track/get/mute", [track_id])
        if not response:
            return False
        return bool(response[1]) if len(response) > 1 else bool(response[0])

    async def set_track_mute(self, track_id: int, mute: bool) -> None:
        """Set track mute state (fire-and-forget, no confirmation)."""
        self._send("/live/track/set/mute", [track_id, 1 if mute else 0])

    async def get_track_solo(self, track_id: int) -> bool:
        """Get track solo state."""
        response = await self._request("/live/track/get/solo", [track_id])
        if not response:
            return False
        return bool(response[1]) if len(response) > 1 else bool(response[0])

    async def set_track_solo(self, track_id: int, solo: bool) -> None:
        """Set track solo state (fire-and-forget, no confirmation)."""
        self._send("/live/track/set/solo", [track_id, 1 if solo else 0])

    async def get_track_arm(self, track_id: int) -> bool:
        """Get track record arm state."""
        response = await self._request("/live/track/get/arm", [track_id])
        if not response:
            return False
        return bool(response[1]) if len(response) > 1 else bool(response[0])

    async def set_track_arm(self, track_id: int, arm: bool) -> None:
        """Set track record arm state (fire-and-forget, no confirmation)."""
        self._send("/live/track/set/arm", [track_id, 1 if arm else 0])

    async def get_track_has_midi_input(self, track_id: int) -> bool:
        """Check if track has MIDI input capability."""
        response = await self._request("/live/track/get/has_midi_input", [track_id])
        if not response:
            return False
        # Response format: [track_id, has_midi_input]
        return bool(response[1]) if len(response) > 1 else bool(response[0])

    async def create_midi_track(self, index: int = -1) -> None:
        """Create a new MIDI track (fire-and-forget, no confirmation)."""
        self._send("/live/song/create_midi_track", [index])

    async def create_audio_track(self, index: int = -1) -> None:
        """Create a new audio track (fire-and-forget, no confirmation)."""
        self._send("/live/song/create_audio_track", [index])

    async def delete_track(self, track_id: int) -> None:
        """Delete a track (fire-and-forget, no confirmation)."""
        self._send("/live/song/delete_track", [track_id])

    # Clip operations (fire-and-forget commands)

    async def fire_clip(self, track_id: int, clip_id: int) -> None:
        """Fire (launch) a clip (fire-and-forget, no confirmation)."""
        self._send("/live/clip_slot/fire", [track_id, clip_id])

    async def stop_clip(self, track_id: int, clip_id: int) -> None:
        """Stop a clip (fire-and-forget, no confirmation)."""
        self._send("/live/clip_slot/stop", [track_id, clip_id])

    async def create_clip(
        self, track_id: int, clip_id: int, length: float
    ) -> None:
        """Create a new MIDI clip (fire-and-forget, no confirmation)."""
        self._send("/live/clip_slot/create_clip", [track_id, clip_id, length])

    async def delete_clip(self, track_id: int, clip_id: int) -> None:
        """Delete a clip (fire-and-forget, no confirmation)."""
        self._send("/live/clip_slot/delete_clip", [track_id, clip_id])

    async def add_note(
        self,
        track_id: int,
        clip_id: int,
        pitch: int,
        start: float,
        duration: float,
        velocity: int,
        mute: bool = False,
    ) -> None:
        """Add a MIDI note to a clip (fire-and-forget, no confirmation)."""
        self._send(
            "/live/clip/add_new_notes",
            [track_id, clip_id, pitch, start, duration, velocity, 1 if mute else 0],
        )

    async def remove_notes(
        self,
        track_id: int,
        clip_id: int,
        start_time: float,
        time_span: float,
        pitch_start: int = 0,
        pitch_span: int = 128,
    ) -> None:
        """Remove notes from a clip within a time/pitch range (fire-and-forget)."""
        self._send(
            "/live/clip/remove_notes",
            [track_id, clip_id, start_time, time_span, pitch_start, pitch_span],
        )

    async def get_clip_notes(
        self, track_id: int, clip_id: int
    ) -> List[Dict[str, Any]]:
        """Get all notes in a clip."""
        response = await self._request("/live/clip/get/notes", [track_id, clip_id])

        # AbletonOSC returns notes in flat format:
        # [note_count, pitch1, start1, duration1, velocity1, mute1, ...]
        notes: List[Dict[str, Any]] = []
        if not response:
            return notes

        # First element is note count
        note_count = int(response[0])
        data = response[1:]

        # Each note has 5 values: pitch, start, duration, velocity, mute
        for i in range(note_count):
            base = i * 5
            if base + 5 <= len(data):
                notes.append({
                    "pitch": int(data[base]),
                    "start": float(data[base + 1]),
                    "duration": float(data[base + 2]),
                    "velocity": int(data[base + 3]),
                    "mute": bool(data[base + 4]),
                })

        return notes

    # Device operations

    async def get_device_parameters(
        self, track_id: int, device_id: int
    ) -> List[Dict[str, Any]]:
        """Get device parameters."""
        response = await self._request(
            "/live/device/get/parameters", [track_id, device_id]
        )

        # AbletonOSC returns parameters in flat format:
        # [param_count, id1, name1, value1, min1, max1, ...]
        parameters: List[Dict[str, Any]] = []
        if not response:
            return parameters

        param_count = int(response[0])
        data = response[1:]

        # Each parameter has 5 values: id, name, value, min, max
        for i in range(param_count):
            base = i * 5
            if base + 5 <= len(data):
                parameters.append({
                    "id": int(data[base]),
                    "name": str(data[base + 1]),
                    "value": float(data[base + 2]),
                    "min": float(data[base + 3]),
                    "max": float(data[base + 4]),
                })

        return parameters

    async def set_device_parameter(
        self, track_id: int, device_id: int, parameter_id: int, value: float
    ) -> None:
        """Set device parameter value (fire-and-forget, no confirmation)."""
        self._send(
            "/live/device/set/parameter/value",
            [track_id, device_id, parameter_id, value],
        )

    async def bypass_device(
        self, track_id: int, device_id: int, bypass: bool
    ) -> None:
        """Bypass or enable a device (fire-and-forget, no confirmation)."""
        self._send(
            "/live/device/set/enabled",
            [track_id, device_id, 0 if bypass else 1],
        )
