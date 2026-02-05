"""Domain ports defining contracts for external communication.

These interfaces follow the Dependency Inversion Principle - the domain layer
defines the contracts, and infrastructure provides implementations.
"""

from abc import ABC, abstractmethod
from typing import Any


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
    async def get_time_signature(self) -> tuple[int, int]:
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
    async def get_track_mute(self, track_id: int) -> bool:
        """Get track mute state."""
        ...

    @abstractmethod
    async def set_track_mute(self, track_id: int, mute: bool) -> None:
        """Set track mute state."""
        ...

    @abstractmethod
    async def get_track_solo(self, track_id: int) -> bool:
        """Get track solo state."""
        ...

    @abstractmethod
    async def set_track_solo(self, track_id: int, solo: bool) -> None:
        """Set track solo state."""
        ...

    @abstractmethod
    async def get_track_arm(self, track_id: int) -> bool:
        """Get track record arm state."""
        ...

    @abstractmethod
    async def set_track_arm(self, track_id: int, arm: bool) -> None:
        """Set track record arm state."""
        ...

    @abstractmethod
    async def get_track_has_midi_input(self, track_id: int) -> bool:
        """Check if track has MIDI input capability.

        Used to determine if a track is a MIDI track vs audio track.
        """
        ...

    @abstractmethod
    async def create_midi_track(self, index: int = -1) -> None:
        """Create a new MIDI track (fire-and-forget, no confirmation).

        Args:
            index: Position to insert track (-1 for end)
        """
        ...

    @abstractmethod
    async def create_audio_track(self, index: int = -1) -> None:
        """Create a new audio track (fire-and-forget, no confirmation).

        Args:
            index: Position to insert track (-1 for end)
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
    async def create_clip(self, track_id: int, clip_id: int, length: float) -> None:
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
    async def get_clip_notes(self, track_id: int, clip_id: int) -> list[dict[str, Any]]:
        """Get all notes in a clip.

        Returns:
            List of note dicts with keys: pitch, start, duration, velocity, mute
        """
        ...

    # Device operations

    @abstractmethod
    async def get_device_parameters(self, track_id: int, device_id: int) -> list[dict[str, Any]]:
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
    async def bypass_device(self, track_id: int, device_id: int, bypass: bool) -> None:
        """Bypass or enable a device."""
        ...

    # Connection verification & View/Navigation

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to Ableton Live."""
        ...

    @abstractmethod
    async def get_application_version(self) -> str:
        """Get Ableton Live application version."""
        ...

    @abstractmethod
    async def get_selected_track(self) -> int:
        """Get currently selected track index."""
        ...

    @abstractmethod
    async def set_selected_track(self, track_id: int) -> None:
        """Set selected track by index."""
        ...

    @abstractmethod
    async def get_selected_scene(self) -> int:
        """Get currently selected scene index."""
        ...

    @abstractmethod
    async def set_selected_scene(self, scene_id: int) -> None:
        """Set selected scene by index."""
        ...

    # Scene operations

    @abstractmethod
    async def get_num_scenes(self) -> int:
        """Get total number of scenes."""
        ...

    @abstractmethod
    async def fire_scene(self, scene_id: int) -> None:
        """Fire (launch) a scene."""
        ...

    @abstractmethod
    async def get_scene_name(self, scene_id: int) -> str:
        """Get scene name."""
        ...

    @abstractmethod
    async def set_scene_name(self, scene_id: int, name: str) -> None:
        """Set scene name."""
        ...

    @abstractmethod
    async def get_scene_color(self, scene_id: int) -> int:
        """Get scene color index."""
        ...

    @abstractmethod
    async def set_scene_color(self, scene_id: int, color: int) -> None:
        """Set scene color index."""
        ...

    @abstractmethod
    async def create_scene(self, index: int) -> None:
        """Create a new scene at the given index."""
        ...

    @abstractmethod
    async def delete_scene(self, scene_id: int) -> None:
        """Delete a scene."""
        ...

    # Extended transport controls

    @abstractmethod
    async def continue_playing(self) -> None:
        """Continue playback from current position."""
        ...

    @abstractmethod
    async def stop_all_clips(self) -> None:
        """Stop all playing clips."""
        ...

    @abstractmethod
    async def tap_tempo(self) -> None:
        """Tap tempo."""
        ...

    @abstractmethod
    async def undo(self) -> None:
        """Undo last action."""
        ...

    @abstractmethod
    async def redo(self) -> None:
        """Redo last undone action."""
        ...

    @abstractmethod
    async def capture_midi(self) -> None:
        """Capture recently played MIDI."""
        ...

    @abstractmethod
    async def trigger_session_record(self) -> None:
        """Toggle session record."""
        ...

    @abstractmethod
    async def jump_by(self, beats: float) -> None:
        """Jump forward/backward by beats."""
        ...

    @abstractmethod
    async def jump_to(self, time: float) -> None:
        """Jump to a specific time position."""
        ...

    @abstractmethod
    async def jump_to_next_cue(self) -> None:
        """Jump to the next cue point."""
        ...

    @abstractmethod
    async def jump_to_prev_cue(self) -> None:
        """Jump to the previous cue point."""
        ...

    # Song property getters/setters

    @abstractmethod
    async def get_swing_amount(self) -> float:
        """Get song swing amount (0.0-1.0)."""
        ...

    @abstractmethod
    async def set_swing_amount(self, swing: float) -> None:
        """Set song swing amount (0.0-1.0)."""
        ...

    @abstractmethod
    async def get_metronome(self) -> bool:
        """Get metronome enabled state."""
        ...

    @abstractmethod
    async def set_metronome(self, enabled: bool) -> None:
        """Set metronome enabled state."""
        ...

    @abstractmethod
    async def get_overdub(self) -> bool:
        """Get overdub enabled state."""
        ...

    @abstractmethod
    async def set_overdub(self, enabled: bool) -> None:
        """Set overdub enabled state."""
        ...

    @abstractmethod
    async def get_song_length(self) -> float:
        """Get song length in beats."""
        ...

    @abstractmethod
    async def get_loop(self) -> bool:
        """Get loop enabled state."""
        ...

    @abstractmethod
    async def set_loop(self, enabled: bool) -> None:
        """Set loop enabled state."""
        ...

    @abstractmethod
    async def get_loop_start(self) -> float:
        """Get loop start position in beats."""
        ...

    @abstractmethod
    async def set_loop_start(self, start: float) -> None:
        """Set loop start position in beats."""
        ...

    @abstractmethod
    async def get_loop_length(self) -> float:
        """Get loop length in beats."""
        ...

    @abstractmethod
    async def set_loop_length(self, length: float) -> None:
        """Set loop length in beats."""
        ...

    @abstractmethod
    async def get_record_mode(self) -> bool:
        """Get record mode state."""
        ...

    @abstractmethod
    async def get_session_record(self) -> bool:
        """Get session record state."""
        ...

    @abstractmethod
    async def get_punch_in(self) -> bool:
        """Get punch-in state."""
        ...

    @abstractmethod
    async def get_punch_out(self) -> bool:
        """Get punch-out state."""
        ...

    @abstractmethod
    async def get_num_return_tracks(self) -> int:
        """Get number of return tracks."""
        ...

    # Clip property operations

    @abstractmethod
    async def get_clip_name(self, track_id: int, clip_id: int) -> str:
        """Get clip name."""
        ...

    @abstractmethod
    async def set_clip_name(self, track_id: int, clip_id: int, name: str) -> None:
        """Set clip name."""
        ...

    @abstractmethod
    async def get_clip_length(self, track_id: int, clip_id: int) -> float:
        """Get clip length in beats."""
        ...

    @abstractmethod
    async def set_clip_length(self, track_id: int, clip_id: int, length: float) -> None:
        """Set clip length in beats."""
        ...

    @abstractmethod
    async def get_clip_loop_start(self, track_id: int, clip_id: int) -> float:
        """Get clip loop start position."""
        ...

    @abstractmethod
    async def set_clip_loop_start(self, track_id: int, clip_id: int, start: float) -> None:
        """Set clip loop start position."""
        ...

    @abstractmethod
    async def get_clip_loop_end(self, track_id: int, clip_id: int) -> float:
        """Get clip loop end position."""
        ...

    @abstractmethod
    async def set_clip_loop_end(self, track_id: int, clip_id: int, end: float) -> None:
        """Set clip loop end position."""
        ...

    @abstractmethod
    async def get_clip_is_playing(self, track_id: int, clip_id: int) -> bool:
        """Check if clip is currently playing."""
        ...

    @abstractmethod
    async def get_clip_playing_position(self, track_id: int, clip_id: int) -> float:
        """Get clip's current playing position."""
        ...

    @abstractmethod
    async def has_clip(self, track_id: int, clip_id: int) -> bool:
        """Check if a clip slot contains a clip."""
        ...

    # Track enhancements

    @abstractmethod
    async def get_track_color(self, track_id: int) -> int:
        """Get track color index."""
        ...

    @abstractmethod
    async def set_track_color(self, track_id: int, color: int) -> None:
        """Set track color index."""
        ...

    @abstractmethod
    async def get_track_send(self, track_id: int, send_id: int) -> float:
        """Get track send amount (0.0-1.0)."""
        ...

    @abstractmethod
    async def set_track_send(self, track_id: int, send_id: int, amount: float) -> None:
        """Set track send amount (0.0-1.0)."""
        ...

    @abstractmethod
    async def stop_all_track_clips(self, track_id: int) -> None:
        """Stop all clips on a track."""
        ...

    @abstractmethod
    async def duplicate_track(self, track_id: int) -> None:
        """Duplicate a track."""
        ...

    @abstractmethod
    async def get_track_num_devices(self, track_id: int) -> int:
        """Get number of devices on a track."""
        ...

    @abstractmethod
    async def get_track_devices(self, track_id: int) -> list[str]:
        """Get list of device names on a track."""
        ...

    # Return tracks & Master track

    @abstractmethod
    async def create_return_track(self) -> None:
        """Create a new return track."""
        ...

    @abstractmethod
    async def get_return_track_volume(self, return_id: int) -> float:
        """Get return track volume."""
        ...

    @abstractmethod
    async def set_return_track_volume(self, return_id: int, volume: float) -> None:
        """Set return track volume."""
        ...

    @abstractmethod
    async def get_return_track_pan(self, return_id: int) -> float:
        """Get return track panning."""
        ...

    @abstractmethod
    async def set_return_track_pan(self, return_id: int, pan: float) -> None:
        """Set return track panning."""
        ...

    @abstractmethod
    async def get_return_track_mute(self, return_id: int) -> bool:
        """Get return track mute state."""
        ...

    @abstractmethod
    async def set_return_track_mute(self, return_id: int, mute: bool) -> None:
        """Set return track mute state."""
        ...

    @abstractmethod
    async def get_return_track_name(self, return_id: int) -> str:
        """Get return track name."""
        ...

    @abstractmethod
    async def set_return_track_name(self, return_id: int, name: str) -> None:
        """Set return track name."""
        ...

    @abstractmethod
    async def get_master_volume(self) -> float:
        """Get master track volume."""
        ...

    @abstractmethod
    async def set_master_volume(self, volume: float) -> None:
        """Set master track volume."""
        ...

    @abstractmethod
    async def get_master_pan(self) -> float:
        """Get master track panning."""
        ...

    @abstractmethod
    async def set_master_pan(self, pan: float) -> None:
        """Set master track panning."""
        ...

    # Device operations enhancement

    @abstractmethod
    async def get_device_name(self, track_id: int, device_id: int) -> str:
        """Get device name."""
        ...

    @abstractmethod
    async def get_device_class_name(self, track_id: int, device_id: int) -> str:
        """Get device class name."""
        ...

    @abstractmethod
    async def get_device_num_parameters(self, track_id: int, device_id: int) -> int:
        """Get number of parameters on a device."""
        ...

    @abstractmethod
    async def get_device_is_active(self, track_id: int, device_id: int) -> bool:
        """Get device active/enabled state."""
        ...

    @abstractmethod
    async def set_device_is_active(self, track_id: int, device_id: int, active: bool) -> None:
        """Set device active/enabled state."""
        ...

    @abstractmethod
    async def get_device_parameter_value(
        self, track_id: int, device_id: int, param_id: int
    ) -> float:
        """Get a single device parameter value."""
        ...

    @abstractmethod
    async def get_device_parameter_name(self, track_id: int, device_id: int, param_id: int) -> str:
        """Get device parameter name."""
        ...

    @abstractmethod
    async def get_device_parameter_display_value(
        self, track_id: int, device_id: int, param_id: int
    ) -> str:
        """Get device parameter display value (human-readable string)."""
        ...

    @abstractmethod
    async def get_device_parameter_min(self, track_id: int, device_id: int, param_id: int) -> float:
        """Get device parameter minimum value."""
        ...

    @abstractmethod
    async def get_device_parameter_max(self, track_id: int, device_id: int, param_id: int) -> float:
        """Get device parameter maximum value."""
        ...
