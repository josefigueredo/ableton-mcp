"""Domain ports defining contracts for external communication.

These interfaces follow the Dependency Inversion Principle - the domain layer
defines the contracts, and infrastructure provides implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class AbletonGateway(ABC):
    """Port for Ableton Live communication.

    This interface defines what the domain/application layer needs from Ableton,
    without specifying how communication happens (OSC, MIDI, etc.).
    """

    # Connection lifecycle

    @abstractmethod
    async def connect(self, host: str, send_port: int, receive_port: int) -> None:
        """Establish connection to Ableton Live.

        Args:
            host: Ableton Live host IP address
            send_port: OSC port to send commands
            receive_port: OSC port to receive responses

        Raises:
            ConnectionError: If connection cannot be established
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from Ableton Live."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to Ableton Live."""
        ...

    # Transport control (fire-and-forget)

    @abstractmethod
    async def start_playing(self) -> None:
        """Start playback."""
        ...

    @abstractmethod
    async def stop_playing(self) -> None:
        """Stop playback."""
        ...

    @abstractmethod
    async def start_recording(self) -> None:
        """Start recording."""
        ...

    @abstractmethod
    async def stop_recording(self) -> None:
        """Stop recording."""
        ...

    # Song queries (request-response)

    @abstractmethod
    async def get_tempo(self) -> float:
        """Get current song tempo in BPM."""
        ...

    @abstractmethod
    async def set_tempo(self, bpm: float) -> None:
        """Set song tempo.

        Args:
            bpm: Tempo in beats per minute (20-999)
        """
        ...

    @abstractmethod
    async def get_time_signature(self) -> Tuple[int, int]:
        """Get time signature as (numerator, denominator)."""
        ...

    @abstractmethod
    async def get_song_time(self) -> float:
        """Get current song position in beats."""
        ...

    @abstractmethod
    async def get_num_tracks(self) -> int:
        """Get total number of tracks."""
        ...

    @abstractmethod
    async def get_is_playing(self) -> bool:
        """Check if transport is playing."""
        ...

    # Track operations

    @abstractmethod
    async def get_track_name(self, track_id: int) -> str:
        """Get track name."""
        ...

    @abstractmethod
    async def set_track_name(self, track_id: int, name: str) -> None:
        """Set track name."""
        ...

    @abstractmethod
    async def get_track_volume(self, track_id: int) -> float:
        """Get track volume (0.0-1.0)."""
        ...

    @abstractmethod
    async def set_track_volume(self, track_id: int, volume: float) -> None:
        """Set track volume (0.0-1.0)."""
        ...

    @abstractmethod
    async def get_track_pan(self, track_id: int) -> float:
        """Get track pan (-1.0 to 1.0)."""
        ...

    @abstractmethod
    async def set_track_pan(self, track_id: int, pan: float) -> None:
        """Set track pan (-1.0 to 1.0)."""
        ...

    @abstractmethod
    async def set_track_mute(self, track_id: int, mute: bool) -> None:
        """Set track mute state."""
        ...

    @abstractmethod
    async def set_track_solo(self, track_id: int, solo: bool) -> None:
        """Set track solo state."""
        ...

    @abstractmethod
    async def set_track_arm(self, track_id: int, arm: bool) -> None:
        """Set track record arm state."""
        ...

    @abstractmethod
    async def create_midi_track(self, index: int = -1) -> int:
        """Create a new MIDI track.

        Args:
            index: Position to insert track (-1 for end)

        Returns:
            Index of the created track
        """
        ...

    @abstractmethod
    async def create_audio_track(self, index: int = -1) -> int:
        """Create a new audio track.

        Args:
            index: Position to insert track (-1 for end)

        Returns:
            Index of the created track
        """
        ...

    @abstractmethod
    async def delete_track(self, track_id: int) -> None:
        """Delete a track."""
        ...

    # Clip operations

    @abstractmethod
    async def fire_clip(self, track_id: int, clip_id: int) -> None:
        """Fire (launch) a clip."""
        ...

    @abstractmethod
    async def stop_clip(self, track_id: int, clip_id: int) -> None:
        """Stop a clip."""
        ...

    @abstractmethod
    async def create_clip(
        self, track_id: int, clip_id: int, length: float
    ) -> None:
        """Create a new MIDI clip.

        Args:
            track_id: Track index
            clip_id: Clip slot index
            length: Clip length in beats
        """
        ...

    @abstractmethod
    async def delete_clip(self, track_id: int, clip_id: int) -> None:
        """Delete a clip."""
        ...

    @abstractmethod
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
        """Add a MIDI note to a clip.

        Args:
            track_id: Track index
            clip_id: Clip slot index
            pitch: MIDI note number (0-127)
            start: Start time in beats
            duration: Note duration in beats
            velocity: Note velocity (1-127)
            mute: Whether note is muted
        """
        ...

    @abstractmethod
    async def remove_notes(
        self,
        track_id: int,
        clip_id: int,
        start_time: float,
        time_span: float,
        pitch_start: int = 0,
        pitch_span: int = 128,
    ) -> None:
        """Remove notes from a clip within a time/pitch range."""
        ...

    @abstractmethod
    async def get_clip_notes(
        self, track_id: int, clip_id: int
    ) -> List[Dict[str, Any]]:
        """Get all notes in a clip.

        Returns:
            List of note dicts with keys: pitch, start, duration, velocity, mute
        """
        ...

    # Device operations

    @abstractmethod
    async def get_device_parameters(
        self, track_id: int, device_id: int
    ) -> List[Dict[str, Any]]:
        """Get device parameters.

        Returns:
            List of parameter dicts with keys: id, name, value, min, max
        """
        ...

    @abstractmethod
    async def set_device_parameter(
        self, track_id: int, device_id: int, parameter_id: int, value: float
    ) -> None:
        """Set device parameter value."""
        ...

    @abstractmethod
    async def bypass_device(
        self, track_id: int, device_id: int, bypass: bool
    ) -> None:
        """Bypass or enable a device."""
        ...
