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

    async def continue_playing(self) -> None:
        """Continue playback from current position."""
        await self._gateway.continue_playing()

    async def stop_all_clips(self) -> None:
        """Stop all playing clips."""
        await self._gateway.stop_all_clips()

    async def tap_tempo(self) -> None:
        """Tap tempo."""
        await self._gateway.tap_tempo()

    async def undo(self) -> None:
        """Undo last action."""
        await self._gateway.undo()

    async def redo(self) -> None:
        """Redo last undone action."""
        await self._gateway.redo()

    async def capture_midi(self) -> None:
        """Capture recently played MIDI."""
        await self._gateway.capture_midi()

    async def trigger_session_record(self) -> None:
        """Toggle session record."""
        await self._gateway.trigger_session_record()

    async def jump_by(self, beats: float) -> None:
        """Jump forward/backward by beats."""
        await self._gateway.jump_by(beats)

    async def jump_to(self, time: float) -> None:
        """Jump to a specific time position."""
        await self._gateway.jump_to(time)

    async def jump_to_next_cue(self) -> None:
        """Jump to next cue point."""
        await self._gateway.jump_to_next_cue()

    async def jump_to_prev_cue(self) -> None:
        """Jump to previous cue point."""
        await self._gateway.jump_to_prev_cue()


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

    async def set_track_color(self, track_id: int, color: int) -> None:
        """Set track color."""
        await self._gateway.set_track_color(track_id, color)

    async def get_track_send(self, track_id: int, send_id: int) -> float:
        """Get track send amount."""
        return await self._gateway.get_track_send(track_id, send_id)

    async def set_track_send(self, track_id: int, send_id: int, amount: float) -> None:
        """Set track send amount."""
        await self._gateway.set_track_send(track_id, send_id, amount)

    async def stop_all_track_clips(self, track_id: int) -> None:
        """Stop all clips on a track."""
        await self._gateway.stop_all_track_clips(track_id)

    async def duplicate_track(self, track_id: int) -> None:
        """Duplicate a track."""
        await self._gateway.duplicate_track(track_id)


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
        """Get all MIDI notes from a clip."""
        return await self._gateway.get_clip_notes(track_id, clip_id)

    async def get_clip_name(self, track_id: int, clip_id: int) -> str:
        """Get clip name."""
        return await self._gateway.get_clip_name(track_id, clip_id)

    async def set_clip_name(self, track_id: int, clip_id: int, name: str) -> None:
        """Set clip name."""
        await self._gateway.set_clip_name(track_id, clip_id, name)

    async def get_clip_length(self, track_id: int, clip_id: int) -> float:
        """Get clip length."""
        return await self._gateway.get_clip_length(track_id, clip_id)

    async def set_clip_length(self, track_id: int, clip_id: int, length: float) -> None:
        """Set clip length."""
        await self._gateway.set_clip_length(track_id, clip_id, length)

    async def get_clip_loop_start(self, track_id: int, clip_id: int) -> float:
        """Get clip loop start."""
        return await self._gateway.get_clip_loop_start(track_id, clip_id)

    async def set_clip_loop_start(self, track_id: int, clip_id: int, start: float) -> None:
        """Set clip loop start."""
        await self._gateway.set_clip_loop_start(track_id, clip_id, start)

    async def get_clip_loop_end(self, track_id: int, clip_id: int) -> float:
        """Get clip loop end."""
        return await self._gateway.get_clip_loop_end(track_id, clip_id)

    async def set_clip_loop_end(self, track_id: int, clip_id: int, end: float) -> None:
        """Set clip loop end."""
        await self._gateway.set_clip_loop_end(track_id, clip_id, end)

    async def get_clip_is_playing(self, track_id: int, clip_id: int) -> bool:
        """Check if clip is playing."""
        return await self._gateway.get_clip_is_playing(track_id, clip_id)

    async def get_clip_playing_position(self, track_id: int, clip_id: int) -> float:
        """Get clip playing position."""
        return await self._gateway.get_clip_playing_position(track_id, clip_id)

    async def has_clip(self, track_id: int, clip_id: int) -> bool:
        """Check if clip slot has a clip."""
        return await self._gateway.has_clip(track_id, clip_id)


class AbletonSceneService:
    """Service adapter for scene operations."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def get_num_scenes(self) -> int:
        """Get number of scenes."""
        return await self._gateway.get_num_scenes()

    async def fire_scene(self, scene_id: int) -> None:
        """Fire a scene."""
        await self._gateway.fire_scene(scene_id)

    async def get_scene_info(self, scene_id: int) -> dict[str, Any]:
        """Get scene information."""
        name = await self._gateway.get_scene_name(scene_id)
        color = await self._gateway.get_scene_color(scene_id)
        return {
            "scene_id": scene_id,
            "name": name,
            "color": color,
        }

    async def set_scene_name(self, scene_id: int, name: str) -> None:
        """Set scene name."""
        await self._gateway.set_scene_name(scene_id, name)

    async def set_scene_color(self, scene_id: int, color: int) -> None:
        """Set scene color."""
        await self._gateway.set_scene_color(scene_id, color)

    async def create_scene(self, index: int) -> None:
        """Create a scene."""
        await self._gateway.create_scene(index)

    async def delete_scene(self, scene_id: int) -> None:
        """Delete a scene."""
        await self._gateway.delete_scene(scene_id)


class AbletonReturnTrackService:
    """Service adapter for return track and master track operations."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def create_return_track(self) -> None:
        """Create a new return track."""
        await self._gateway.create_return_track()

    async def get_return_track_info(self, return_id: int) -> dict[str, Any]:
        """Get return track information."""
        name = await self._gateway.get_return_track_name(return_id)
        volume = await self._gateway.get_return_track_volume(return_id)
        pan = await self._gateway.get_return_track_pan(return_id)
        mute = await self._gateway.get_return_track_mute(return_id)
        return {
            "return_id": return_id,
            "name": name,
            "volume": volume,
            "pan": pan,
            "muted": mute,
        }

    async def set_return_track_volume(self, return_id: int, volume: float) -> None:
        """Set return track volume."""
        await self._gateway.set_return_track_volume(return_id, volume)

    async def set_return_track_pan(self, return_id: int, pan: float) -> None:
        """Set return track panning."""
        await self._gateway.set_return_track_pan(return_id, pan)

    async def set_return_track_mute(self, return_id: int, mute: bool) -> None:
        """Set return track mute state."""
        await self._gateway.set_return_track_mute(return_id, mute)

    async def set_return_track_name(self, return_id: int, name: str) -> None:
        """Set return track name."""
        await self._gateway.set_return_track_name(return_id, name)

    async def get_master_info(self) -> dict[str, Any]:
        """Get master track information."""
        volume = await self._gateway.get_master_volume()
        pan = await self._gateway.get_master_pan()
        return {
            "volume": volume,
            "pan": pan,
        }

    async def set_master_volume(self, volume: float) -> None:
        """Set master track volume."""
        await self._gateway.set_master_volume(volume)

    async def set_master_pan(self, pan: float) -> None:
        """Set master track panning."""
        await self._gateway.set_master_pan(pan)


class AbletonDeviceService:
    """Service adapter for device operations."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def get_device_info(self, track_id: int, device_id: int) -> dict[str, Any]:
        """Get device information."""
        name = await self._gateway.get_device_name(track_id, device_id)
        class_name = await self._gateway.get_device_class_name(track_id, device_id)
        num_params = await self._gateway.get_device_num_parameters(track_id, device_id)
        is_active = await self._gateway.get_device_is_active(track_id, device_id)
        return {
            "track_id": track_id,
            "device_id": device_id,
            "name": name,
            "class_name": class_name,
            "num_parameters": num_params,
            "is_active": is_active,
        }

    async def set_device_active(self, track_id: int, device_id: int, active: bool) -> None:
        """Set device active state."""
        await self._gateway.set_device_is_active(track_id, device_id, active)

    async def get_parameter_info(
        self, track_id: int, device_id: int, param_id: int
    ) -> dict[str, Any]:
        """Get parameter information."""
        name = await self._gateway.get_device_parameter_name(track_id, device_id, param_id)
        value = await self._gateway.get_device_parameter_value(track_id, device_id, param_id)
        display_value = await self._gateway.get_device_parameter_display_value(
            track_id, device_id, param_id
        )
        min_val = await self._gateway.get_device_parameter_min(track_id, device_id, param_id)
        max_val = await self._gateway.get_device_parameter_max(track_id, device_id, param_id)
        return {
            "parameter_id": param_id,
            "name": name,
            "value": value,
            "display_value": display_value,
            "min": min_val,
            "max": max_val,
        }

    async def set_parameter_value(
        self, track_id: int, device_id: int, param_id: int, value: float
    ) -> None:
        """Set device parameter value."""
        await self._gateway.set_device_parameter(track_id, device_id, param_id, value)

    async def get_all_parameters(self, track_id: int, device_id: int) -> list[dict[str, Any]]:
        """Get all parameters for a device."""
        return await self._gateway.get_device_parameters(track_id, device_id)


class AbletonSongPropertyService:
    """Service adapter for song property operations."""

    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def set_swing(self, value: float) -> None:
        """Set swing amount."""
        await self._gateway.set_swing_amount(value)

    async def set_metronome(self, enabled: bool) -> None:
        """Set metronome state."""
        await self._gateway.set_metronome(enabled)

    async def set_overdub(self, enabled: bool) -> None:
        """Set overdub state."""
        await self._gateway.set_overdub(enabled)

    async def set_loop(self, enabled: bool) -> None:
        """Set loop state."""
        await self._gateway.set_loop(enabled)

    async def set_loop_start(self, start: float) -> None:
        """Set loop start."""
        await self._gateway.set_loop_start(start)

    async def set_loop_length(self, length: float) -> None:
        """Set loop length."""
        await self._gateway.set_loop_length(length)

    async def set_tempo(self, bpm: float) -> None:
        """Set tempo."""
        await self._gateway.set_tempo(bpm)

    async def get_song_properties(self) -> dict[str, Any]:
        """Get all song properties."""
        swing = await self._gateway.get_swing_amount()
        metronome = await self._gateway.get_metronome()
        overdub = await self._gateway.get_overdub()
        song_length = await self._gateway.get_song_length()
        loop = await self._gateway.get_loop()
        loop_start = await self._gateway.get_loop_start()
        loop_length = await self._gateway.get_loop_length()
        record_mode = await self._gateway.get_record_mode()
        session_record = await self._gateway.get_session_record()
        punch_in = await self._gateway.get_punch_in()
        punch_out = await self._gateway.get_punch_out()
        return {
            "swing_amount": swing,
            "metronome": metronome,
            "overdub": overdub,
            "song_length": song_length,
            "loop": loop,
            "loop_start": loop_start,
            "loop_length": loop_length,
            "record_mode": record_mode,
            "session_record": session_record,
            "punch_in": punch_in,
            "punch_out": punch_out,
        }
