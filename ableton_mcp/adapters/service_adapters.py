"""Service adapters bridging infrastructure with application layer."""

from typing import Any

from ableton_mcp.domain.ports import AbletonGateway


class AbletonConnectionService:
    """Service adapter for Ableton Live connection management."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def connect(self, host: str, send_port: int, receive_port: int) -> None:
        """Connect to Ableton Live."""
        await self._gateway.connect(host, send_port, receive_port)

    async def disconnect(self) -> None:
        """Disconnect from Ableton Live."""
        await self._gateway.disconnect()

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._gateway.is_connected()


class AbletonTransportService:
    """Service adapter for transport control."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def start_playing(self) -> None:
        """Start playback."""
        await self._gateway.start_playing()

    async def stop_playing(self) -> None:
        """Stop playback."""
        await self._gateway.stop_playing()

    async def start_recording(self) -> None:
        """Start recording."""
        await self._gateway.start_recording()

    async def stop_recording(self) -> None:
        """Stop recording."""
        await self._gateway.stop_recording()

    async def set_tempo(self, bpm: float) -> None:
        """Set song tempo."""
        await self._gateway.set_tempo(bpm)


class AbletonTrackService:
    """Service adapter for track operations."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def create_track(self, track: Any) -> None:
        """Create a new track."""
        if track.track_type.value == "midi":
            await self._gateway.create_midi_track()
        else:
            await self._gateway.create_audio_track()

    async def set_track_volume(self, track_id: int, volume: float) -> None:
        """Set track volume."""
        await self._gateway.set_track_volume(track_id, volume)

    async def set_track_pan(self, track_id: int, pan: float) -> None:
        """Set track panning."""
        await self._gateway.set_track_pan(track_id, pan)

    async def set_track_mute(self, track_id: int, mute: bool) -> None:
        """Set track mute state."""
        await self._gateway.set_track_mute(track_id, mute)

    async def set_track_solo(self, track_id: int, solo: bool) -> None:
        """Set track solo state."""
        await self._gateway.set_track_solo(track_id, solo)

    async def set_track_arm(self, track_id: int, arm: bool) -> None:
        """Set track arm state."""
        await self._gateway.set_track_arm(track_id, arm)


class AbletonClipService:
    """Service adapter for clip operations."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def fire_clip(self, track_id: int, clip_id: int) -> None:
        """Fire a clip."""
        await self._gateway.fire_clip(track_id, clip_id)

    async def stop_clip(self, track_id: int, clip_id: int) -> None:
        """Stop a clip."""
        await self._gateway.stop_clip(track_id, clip_id)

    async def add_note(self, track_id: int, clip_id: int, note: Any) -> None:
        """Add a MIDI note to a clip."""
        await self._gateway.add_note(
            track_id=track_id,
            clip_id=clip_id,
            pitch=note.pitch,
            start=note.start,
            duration=note.duration,
            velocity=note.velocity,
            mute=note.mute,
        )

    async def create_clip(self, track_id: int, clip_id: int, length: float) -> None:
        """Create a new clip."""
        await self._gateway.create_clip(track_id, clip_id, length)

    async def delete_clip(self, track_id: int, clip_id: int) -> None:
        """Delete a clip."""
        await self._gateway.delete_clip(track_id, clip_id)

    async def get_clip_notes(self, track_id: int, clip_id: int) -> list[dict[str, Any]]:
        """Get all MIDI notes from a clip.

        Args:
            track_id: Track index (0-based)
            clip_id: Clip slot index (0-based)

        Returns:
            List of note dicts with keys: pitch, start, duration, velocity, mute
        """
        return await self._gateway.get_clip_notes(track_id, clip_id)
