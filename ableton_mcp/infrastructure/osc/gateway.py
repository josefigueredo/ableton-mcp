"""AbletonOSCGateway - High-level async Ableton communication via OSC.

This implements the AbletonGateway port defined in the domain layer.
"""

import asyncio
from typing import Any

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
        transport: AsyncOSCTransport | None = None,
        correlator: OSCCorrelator | None = None,
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

    def _handle_osc_message(self, address: str, args: list[Any]) -> None:
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
            except TimeoutError:
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
                ) from None

        except OSError as e:
            raise ConnectionError(f"Failed to connect to Ableton Live: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Ableton Live."""
        self._correlator.cancel_all()
        await self._transport.disconnect()
        logger.info("Disconnected from Ableton Live")

    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._transport.is_connected()

    # Internal helpers

    def _send(self, address: str, args: list[Any] | None = None) -> None:
        """Send an OSC message without waiting for response."""
        if not self.is_connected():
            raise OSCCommunicationError("Not connected to Ableton Live")
        self._transport.send(address, args or [])

    async def _request(
        self,
        address: str,
        args: list[Any] | None = None,
        timeout: float | None = None,
    ) -> list[Any]:
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
        except TimeoutError:
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

    async def get_time_signature(self) -> tuple[int, int]:
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
            raise OSCCommunicationError(
                f"Empty response from Ableton Live for track {track_id} name"
            )
        # Response format: [track_id, name]
        return str(response[1]) if len(response) > 1 else str(response[0])

    async def set_track_name(self, track_id: int, name: str) -> None:
        """Set track name (fire-and-forget, no confirmation)."""
        self._send("/live/track/set/name", [track_id, name])

    async def get_track_volume(self, track_id: int) -> float:
        """Get track volume (0.0-1.0)."""
        response = await self._request("/live/track/get/volume", [track_id])
        if not response:
            raise OSCCommunicationError(
                f"Empty response from Ableton Live for track {track_id} volume"
            )
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
            raise OSCCommunicationError(
                f"Empty response from Ableton Live for track {track_id} pan"
            )
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

    async def create_clip(self, track_id: int, clip_id: int, length: float) -> None:
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
            "/live/clip/add/notes",
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

    async def get_clip_notes(self, track_id: int, clip_id: int) -> list[dict[str, Any]]:
        """Get all notes in a clip."""
        response = await self._request("/live/clip/get/notes", [track_id, clip_id])

        # AbletonOSC returns notes in flat format:
        # [track_id, clip_id, pitch1, start1, duration1, velocity1, mute1, ...]
        notes: list[dict[str, Any]] = []
        if not response or len(response) < 2:
            return notes

        # Skip track_id and clip_id prefix, notes data starts at index 2
        data = response[2:]

        # Each note has 5 values: pitch, start, duration, velocity, mute
        note_count = len(data) // 5
        for i in range(note_count):
            base = i * 5
            if base + 5 <= len(data):
                notes.append(
                    {
                        "pitch": int(data[base]),
                        "start": float(data[base + 1]),
                        "duration": float(data[base + 2]),
                        "velocity": int(data[base + 3]),
                        "mute": bool(data[base + 4]),
                    }
                )

        return notes

    # Device operations

    async def get_device_parameters(self, track_id: int, device_id: int) -> list[dict[str, Any]]:
        """Get device parameters."""
        response = await self._request("/live/device/get/parameters", [track_id, device_id])

        # AbletonOSC returns parameters in flat format:
        # [param_count, id1, name1, value1, min1, max1, ...]
        parameters: list[dict[str, Any]] = []
        if not response:
            return parameters

        param_count = int(response[0])
        data = response[1:]

        # Each parameter has 5 values: id, name, value, min, max
        for i in range(param_count):
            base = i * 5
            if base + 5 <= len(data):
                parameters.append(
                    {
                        "id": int(data[base]),
                        "name": str(data[base + 1]),
                        "value": float(data[base + 2]),
                        "min": float(data[base + 3]),
                        "max": float(data[base + 4]),
                    }
                )

        return parameters

    async def set_device_parameter(
        self, track_id: int, device_id: int, parameter_id: int, value: float
    ) -> None:
        """Set device parameter value (fire-and-forget, no confirmation)."""
        self._send(
            "/live/device/set/parameter/value",
            [track_id, device_id, parameter_id, value],
        )

    async def bypass_device(self, track_id: int, device_id: int, bypass: bool) -> None:
        """Bypass or enable a device (fire-and-forget, no confirmation)."""
        self._send(
            "/live/device/set/enabled",
            [track_id, device_id, 0 if bypass else 1],
        )

    # Connection verification & View/Navigation

    async def test_connection(self) -> bool:
        """Test connection to Ableton Live."""
        try:
            response = await self._request("/live/test")
            return len(response) > 0
        except Exception:
            return False

    async def get_application_version(self) -> str:
        """Get Ableton Live application version."""
        response = await self._request("/live/application/get/version")
        if not response:
            raise OSCCommunicationError("Empty response for application version")
        return str(response[0])

    async def get_selected_track(self) -> int:
        """Get currently selected track index."""
        response = await self._request("/live/view/get/selected_track")
        if not response:
            raise OSCCommunicationError("Empty response for selected track")
        return int(response[0])

    async def set_selected_track(self, track_id: int) -> None:
        """Set selected track by index."""
        self._send("/live/view/set/selected_track", [track_id])

    async def get_selected_scene(self) -> int:
        """Get currently selected scene index."""
        response = await self._request("/live/view/get/selected_scene")
        if not response:
            raise OSCCommunicationError("Empty response for selected scene")
        return int(response[0])

    async def set_selected_scene(self, scene_id: int) -> None:
        """Set selected scene by index."""
        self._send("/live/view/set/selected_scene", [scene_id])

    # Scene operations

    async def get_num_scenes(self) -> int:
        """Get total number of scenes."""
        response = await self._request("/live/song/get/num_scenes")
        if not response:
            raise OSCCommunicationError("Empty response for num_scenes")
        return int(response[0])

    async def fire_scene(self, scene_id: int) -> None:
        """Fire (launch) a scene."""
        self._send("/live/scene/fire", [scene_id])

    async def get_scene_name(self, scene_id: int) -> str:
        """Get scene name."""
        response = await self._request("/live/scene/get/name", [scene_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for scene {scene_id} name")
        return str(response[1]) if len(response) > 1 else str(response[0])

    async def set_scene_name(self, scene_id: int, name: str) -> None:
        """Set scene name."""
        self._send("/live/scene/set/name", [scene_id, name])

    async def get_scene_color(self, scene_id: int) -> int:
        """Get scene color index."""
        response = await self._request("/live/scene/get/color", [scene_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for scene {scene_id} color")
        return int(response[1]) if len(response) > 1 else int(response[0])

    async def set_scene_color(self, scene_id: int, color: int) -> None:
        """Set scene color index."""
        self._send("/live/scene/set/color", [scene_id, color])

    async def create_scene(self, index: int) -> None:
        """Create a new scene at the given index."""
        self._send("/live/song/create_scene", [index])

    async def delete_scene(self, scene_id: int) -> None:
        """Delete a scene."""
        self._send("/live/song/delete_scene", [scene_id])

    # Extended transport controls

    async def continue_playing(self) -> None:
        """Continue playback from current position."""
        self._send("/live/song/continue_playing")

    async def stop_all_clips(self) -> None:
        """Stop all playing clips."""
        self._send("/live/song/stop_all_clips")

    async def tap_tempo(self) -> None:
        """Tap tempo."""
        self._send("/live/song/tap_tempo")

    async def undo(self) -> None:
        """Undo last action."""
        self._send("/live/song/undo")

    async def redo(self) -> None:
        """Redo last undone action."""
        self._send("/live/song/redo")

    async def capture_midi(self) -> None:
        """Capture recently played MIDI."""
        self._send("/live/song/capture_midi")

    async def trigger_session_record(self) -> None:
        """Toggle session record."""
        self._send("/live/song/trigger_session_record")

    async def jump_by(self, beats: float) -> None:
        """Jump forward/backward by beats."""
        self._send("/live/song/jump_by", [beats])

    async def jump_to(self, time: float) -> None:
        """Jump to a specific time position."""
        self._send("/live/song/jump_to", [time])

    async def jump_to_next_cue(self) -> None:
        """Jump to the next cue point."""
        self._send("/live/song/jump_to_next_cue")

    async def jump_to_prev_cue(self) -> None:
        """Jump to the previous cue point."""
        self._send("/live/song/jump_to_prev_cue")

    # Song property getters/setters

    async def get_swing_amount(self) -> float:
        """Get song swing amount."""
        response = await self._request("/live/song/get/swing_amount")
        if not response:
            raise OSCCommunicationError("Empty response for swing_amount")
        return float(response[0])

    async def set_swing_amount(self, swing: float) -> None:
        """Set song swing amount."""
        self._send("/live/song/set/swing_amount", [swing])

    async def get_metronome(self) -> bool:
        """Get metronome enabled state."""
        response = await self._request("/live/song/get/metronome")
        if not response:
            raise OSCCommunicationError("Empty response for metronome")
        return bool(response[0])

    async def set_metronome(self, enabled: bool) -> None:
        """Set metronome enabled state."""
        self._send("/live/song/set/metronome", [1 if enabled else 0])

    async def get_overdub(self) -> bool:
        """Get overdub enabled state."""
        response = await self._request("/live/song/get/overdub")
        if not response:
            raise OSCCommunicationError("Empty response for overdub")
        return bool(response[0])

    async def set_overdub(self, enabled: bool) -> None:
        """Set overdub enabled state."""
        self._send("/live/song/set/overdub", [1 if enabled else 0])

    async def get_song_length(self) -> float:
        """Get song length in beats."""
        response = await self._request("/live/song/get/song_length")
        if not response:
            raise OSCCommunicationError("Empty response for song_length")
        return float(response[0])

    async def get_loop(self) -> bool:
        """Get loop enabled state."""
        response = await self._request("/live/song/get/loop")
        if not response:
            raise OSCCommunicationError("Empty response for loop")
        return bool(response[0])

    async def set_loop(self, enabled: bool) -> None:
        """Set loop enabled state."""
        self._send("/live/song/set/loop", [1 if enabled else 0])

    async def get_loop_start(self) -> float:
        """Get loop start position in beats."""
        response = await self._request("/live/song/get/loop_start")
        if not response:
            raise OSCCommunicationError("Empty response for loop_start")
        return float(response[0])

    async def set_loop_start(self, start: float) -> None:
        """Set loop start position in beats."""
        self._send("/live/song/set/loop_start", [start])

    async def get_loop_length(self) -> float:
        """Get loop length in beats."""
        response = await self._request("/live/song/get/loop_length")
        if not response:
            raise OSCCommunicationError("Empty response for loop_length")
        return float(response[0])

    async def set_loop_length(self, length: float) -> None:
        """Set loop length in beats."""
        self._send("/live/song/set/loop_length", [length])

    async def get_record_mode(self) -> bool:
        """Get record mode state."""
        response = await self._request("/live/song/get/record_mode")
        if not response:
            raise OSCCommunicationError("Empty response for record_mode")
        return bool(response[0])

    async def get_session_record(self) -> bool:
        """Get session record state."""
        response = await self._request("/live/song/get/session_record")
        if not response:
            raise OSCCommunicationError("Empty response for session_record")
        return bool(response[0])

    async def get_punch_in(self) -> bool:
        """Get punch-in state."""
        response = await self._request("/live/song/get/punch_in")
        if not response:
            raise OSCCommunicationError("Empty response for punch_in")
        return bool(response[0])

    async def get_punch_out(self) -> bool:
        """Get punch-out state."""
        response = await self._request("/live/song/get/punch_out")
        if not response:
            raise OSCCommunicationError("Empty response for punch_out")
        return bool(response[0])

    async def get_num_return_tracks(self) -> int:
        """Get number of return tracks."""
        response = await self._request("/live/song/get/num_return_tracks")
        if not response:
            raise OSCCommunicationError("Empty response for num_return_tracks")
        return int(response[0])

    # Clip property operations

    async def get_clip_name(self, track_id: int, clip_id: int) -> str:
        """Get clip name."""
        response = await self._request("/live/clip/get/name", [track_id, clip_id])
        if not response:
            raise OSCCommunicationError("Empty response for clip name")
        return str(response[2]) if len(response) > 2 else str(response[-1])

    async def set_clip_name(self, track_id: int, clip_id: int, name: str) -> None:
        """Set clip name."""
        self._send("/live/clip/set/name", [track_id, clip_id, name])

    async def get_clip_length(self, track_id: int, clip_id: int) -> float:
        """Get clip length in beats."""
        response = await self._request("/live/clip/get/length", [track_id, clip_id])
        if not response:
            raise OSCCommunicationError("Empty response for clip length")
        return float(response[2]) if len(response) > 2 else float(response[-1])

    async def set_clip_length(self, track_id: int, clip_id: int, length: float) -> None:
        """Set clip length in beats."""
        self._send("/live/clip/set/length", [track_id, clip_id, length])

    async def get_clip_loop_start(self, track_id: int, clip_id: int) -> float:
        """Get clip loop start position."""
        response = await self._request("/live/clip/get/loop_start", [track_id, clip_id])
        if not response:
            raise OSCCommunicationError("Empty response for clip loop_start")
        return float(response[2]) if len(response) > 2 else float(response[-1])

    async def set_clip_loop_start(self, track_id: int, clip_id: int, start: float) -> None:
        """Set clip loop start position."""
        self._send("/live/clip/set/loop_start", [track_id, clip_id, start])

    async def get_clip_loop_end(self, track_id: int, clip_id: int) -> float:
        """Get clip loop end position."""
        response = await self._request("/live/clip/get/loop_end", [track_id, clip_id])
        if not response:
            raise OSCCommunicationError("Empty response for clip loop_end")
        return float(response[2]) if len(response) > 2 else float(response[-1])

    async def set_clip_loop_end(self, track_id: int, clip_id: int, end: float) -> None:
        """Set clip loop end position."""
        self._send("/live/clip/set/loop_end", [track_id, clip_id, end])

    async def get_clip_is_playing(self, track_id: int, clip_id: int) -> bool:
        """Check if clip is currently playing."""
        response = await self._request("/live/clip/get/is_playing", [track_id, clip_id])
        if not response:
            return False
        return bool(response[2]) if len(response) > 2 else bool(response[-1])

    async def get_clip_playing_position(self, track_id: int, clip_id: int) -> float:
        """Get clip's current playing position."""
        response = await self._request("/live/clip/get/playing_position", [track_id, clip_id])
        if not response:
            raise OSCCommunicationError("Empty response for clip playing_position")
        return float(response[2]) if len(response) > 2 else float(response[-1])

    async def has_clip(self, track_id: int, clip_id: int) -> bool:
        """Check if a clip slot contains a clip."""
        response = await self._request("/live/clip_slot/get/has_clip", [track_id, clip_id])
        if not response:
            return False
        return bool(response[2]) if len(response) > 2 else bool(response[-1])

    # Track enhancements

    async def get_track_color(self, track_id: int) -> int:
        """Get track color index."""
        response = await self._request("/live/track/get/color", [track_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for track {track_id} color")
        return int(response[1]) if len(response) > 1 else int(response[0])

    async def set_track_color(self, track_id: int, color: int) -> None:
        """Set track color index."""
        self._send("/live/track/set/color", [track_id, color])

    async def get_track_send(self, track_id: int, send_id: int) -> float:
        """Get track send amount."""
        response = await self._request("/live/track/get/send", [track_id, send_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for track {track_id} send {send_id}")
        return float(response[-1])

    async def set_track_send(self, track_id: int, send_id: int, amount: float) -> None:
        """Set track send amount."""
        self._send("/live/track/set/send", [track_id, send_id, amount])

    async def stop_all_track_clips(self, track_id: int) -> None:
        """Stop all clips on a track."""
        self._send("/live/track/stop_all_clips", [track_id])

    async def duplicate_track(self, track_id: int) -> None:
        """Duplicate a track."""
        self._send("/live/song/duplicate_track", [track_id])

    async def get_track_num_devices(self, track_id: int) -> int:
        """Get number of devices on a track."""
        response = await self._request("/live/track/get/num_devices", [track_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for track {track_id} num_devices")
        return int(response[1]) if len(response) > 1 else int(response[0])

    async def get_track_devices(self, track_id: int) -> list[str]:
        """Get list of device names on a track."""
        response = await self._request("/live/track/get/devices/name", [track_id])
        if not response:
            return []
        # Response format: [track_id, name1, name2, ...]
        if len(response) > 1:
            return [str(name) for name in response[1:]]
        return []

    # Return tracks & Master track

    async def create_return_track(self) -> None:
        """Create a new return track."""
        self._send("/live/song/create_return_track")

    async def get_return_track_volume(self, return_id: int) -> float:
        """Get return track volume."""
        response = await self._request("/live/return_track/get/volume", [return_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for return track {return_id} volume")
        return float(response[1]) if len(response) > 1 else float(response[0])

    async def set_return_track_volume(self, return_id: int, volume: float) -> None:
        """Set return track volume."""
        self._send("/live/return_track/set/volume", [return_id, volume])

    async def get_return_track_pan(self, return_id: int) -> float:
        """Get return track panning."""
        response = await self._request("/live/return_track/get/panning", [return_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for return track {return_id} pan")
        return float(response[1]) if len(response) > 1 else float(response[0])

    async def set_return_track_pan(self, return_id: int, pan: float) -> None:
        """Set return track panning."""
        self._send("/live/return_track/set/panning", [return_id, pan])

    async def get_return_track_mute(self, return_id: int) -> bool:
        """Get return track mute state."""
        response = await self._request("/live/return_track/get/mute", [return_id])
        if not response:
            return False
        return bool(response[1]) if len(response) > 1 else bool(response[0])

    async def set_return_track_mute(self, return_id: int, mute: bool) -> None:
        """Set return track mute state."""
        self._send("/live/return_track/set/mute", [return_id, 1 if mute else 0])

    async def get_return_track_name(self, return_id: int) -> str:
        """Get return track name."""
        response = await self._request("/live/return_track/get/name", [return_id])
        if not response:
            raise OSCCommunicationError(f"Empty response for return track {return_id} name")
        return str(response[1]) if len(response) > 1 else str(response[0])

    async def set_return_track_name(self, return_id: int, name: str) -> None:
        """Set return track name."""
        self._send("/live/return_track/set/name", [return_id, name])

    async def get_master_volume(self) -> float:
        """Get master track volume."""
        response = await self._request("/live/master_track/get/volume")
        if not response:
            raise OSCCommunicationError("Empty response for master volume")
        return float(response[0])

    async def set_master_volume(self, volume: float) -> None:
        """Set master track volume."""
        self._send("/live/master_track/set/volume", [volume])

    async def get_master_pan(self) -> float:
        """Get master track panning."""
        response = await self._request("/live/master_track/get/panning")
        if not response:
            raise OSCCommunicationError("Empty response for master pan")
        return float(response[0])

    async def set_master_pan(self, pan: float) -> None:
        """Set master track panning."""
        self._send("/live/master_track/set/panning", [pan])

    # Device operations enhancement

    async def get_device_name(self, track_id: int, device_id: int) -> str:
        """Get device name."""
        response = await self._request("/live/device/get/name", [track_id, device_id])
        if not response:
            raise OSCCommunicationError("Empty response for device name")
        return str(response[-1])

    async def get_device_class_name(self, track_id: int, device_id: int) -> str:
        """Get device class name."""
        response = await self._request("/live/device/get/class_name", [track_id, device_id])
        if not response:
            raise OSCCommunicationError("Empty response for device class_name")
        return str(response[-1])

    async def get_device_num_parameters(self, track_id: int, device_id: int) -> int:
        """Get number of parameters on a device."""
        response = await self._request("/live/device/get/num_parameters", [track_id, device_id])
        if not response:
            raise OSCCommunicationError("Empty response for device num_parameters")
        return int(response[-1])

    async def get_device_is_active(self, track_id: int, device_id: int) -> bool:
        """Get device active/enabled state."""
        response = await self._request("/live/device/get/is_active", [track_id, device_id])
        if not response:
            return False
        return bool(response[-1])

    async def set_device_is_active(self, track_id: int, device_id: int, active: bool) -> None:
        """Set device active/enabled state."""
        self._send(
            "/live/device/set/is_active",
            [track_id, device_id, 1 if active else 0],
        )

    async def get_device_parameter_value(
        self, track_id: int, device_id: int, param_id: int
    ) -> float:
        """Get a single device parameter value."""
        response = await self._request(
            "/live/device/get/parameter/value",
            [track_id, device_id, param_id],
        )
        if not response:
            raise OSCCommunicationError("Empty response for parameter value")
        return float(response[-1])

    async def get_device_parameter_name(self, track_id: int, device_id: int, param_id: int) -> str:
        """Get device parameter name."""
        response = await self._request(
            "/live/device/get/parameter/name",
            [track_id, device_id, param_id],
        )
        if not response:
            raise OSCCommunicationError("Empty response for parameter name")
        return str(response[-1])

    async def get_device_parameter_display_value(
        self, track_id: int, device_id: int, param_id: int
    ) -> str:
        """Get device parameter display value."""
        response = await self._request(
            "/live/device/get/parameter/display_value",
            [track_id, device_id, param_id],
        )
        if not response:
            raise OSCCommunicationError("Empty response for parameter display_value")
        return str(response[-1])

    async def get_device_parameter_min(self, track_id: int, device_id: int, param_id: int) -> float:
        """Get device parameter minimum value."""
        response = await self._request(
            "/live/device/get/parameter/min",
            [track_id, device_id, param_id],
        )
        if not response:
            raise OSCCommunicationError("Empty response for parameter min")
        return float(response[-1])

    async def get_device_parameter_max(self, track_id: int, device_id: int, param_id: int) -> float:
        """Get device parameter maximum value."""
        response = await self._request(
            "/live/device/get/parameter/max",
            [track_id, device_id, param_id],
        )
        if not response:
            raise OSCCommunicationError("Empty response for parameter max")
        return float(response[-1])
