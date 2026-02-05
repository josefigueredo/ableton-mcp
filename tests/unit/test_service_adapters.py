"""Unit tests for service adapters."""

from unittest.mock import AsyncMock, Mock

from ableton_mcp.adapters.service_adapters import (
    AbletonClipService,
    AbletonConnectionService,
    AbletonDeviceService,
    AbletonReturnTrackService,
    AbletonSceneService,
    AbletonSongPropertyService,
    AbletonTrackService,
    AbletonTransportService,
)
from ableton_mcp.domain.entities import Note, Track, TrackType
from ableton_mcp.domain.ports import AbletonGateway


class TestAbletonConnectionService:
    """Test cases for connection service adapter."""

    async def test_connect(self) -> None:
        """Test connecting through adapter."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.connect = AsyncMock()

        service = AbletonConnectionService(gateway=mock_gateway)
        await service.connect("localhost", 11000, 11001)

        mock_gateway.connect.assert_called_once_with("localhost", 11000, 11001)

    async def test_disconnect(self) -> None:
        """Test disconnecting through adapter."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.disconnect = AsyncMock()

        service = AbletonConnectionService(gateway=mock_gateway)
        await service.disconnect()

        mock_gateway.disconnect.assert_called_once()

    def test_is_connected(self) -> None:
        """Test checking connection status."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.is_connected.return_value = True

        service = AbletonConnectionService(gateway=mock_gateway)

        assert service.is_connected() is True
        mock_gateway.is_connected.assert_called_once()


class TestAbletonTransportService:
    """Test cases for transport service adapter."""

    async def test_start_playing(self) -> None:
        """Test starting playback."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.start_playing = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.start_playing()

        mock_gateway.start_playing.assert_called_once()

    async def test_stop_playing(self) -> None:
        """Test stopping playback."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_playing = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.stop_playing()

        mock_gateway.stop_playing.assert_called_once()

    async def test_start_recording(self) -> None:
        """Test starting recording."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.start_recording = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.start_recording()

        mock_gateway.start_recording.assert_called_once()

    async def test_stop_recording(self) -> None:
        """Test stopping recording."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_recording = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.stop_recording()

        mock_gateway.stop_recording.assert_called_once()

    async def test_set_tempo(self) -> None:
        """Test setting tempo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_tempo = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.set_tempo(128.0)

        mock_gateway.set_tempo.assert_called_once_with(128.0)


class TestAbletonTrackService:
    """Test cases for track service adapter."""

    async def test_create_midi_track(self) -> None:
        """Test creating MIDI track."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_midi_track = AsyncMock()

        track = Track(name="Test", track_type=TrackType.MIDI)

        service = AbletonTrackService(gateway=mock_gateway)
        await service.create_track(track)

        mock_gateway.create_midi_track.assert_called_once()

    async def test_create_audio_track(self) -> None:
        """Test creating audio track."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_audio_track = AsyncMock()

        track = Track(name="Test", track_type=TrackType.AUDIO)

        service = AbletonTrackService(gateway=mock_gateway)
        await service.create_track(track)

        mock_gateway.create_audio_track.assert_called_once()

    async def test_set_track_volume(self) -> None:
        """Test setting track volume."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_volume = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_volume(0, 0.8)

        mock_gateway.set_track_volume.assert_called_once_with(0, 0.8)

    async def test_set_track_pan(self) -> None:
        """Test setting track pan."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_pan = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_pan(0, -0.5)

        mock_gateway.set_track_pan.assert_called_once_with(0, -0.5)

    async def test_set_track_mute(self) -> None:
        """Test setting track mute."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_mute = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_mute(0, True)

        mock_gateway.set_track_mute.assert_called_once_with(0, True)

    async def test_set_track_solo(self) -> None:
        """Test setting track solo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_solo = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_solo(0, True)

        mock_gateway.set_track_solo.assert_called_once_with(0, True)

    async def test_set_track_arm(self) -> None:
        """Test setting track arm."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_arm = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_arm(0, True)

        mock_gateway.set_track_arm.assert_called_once_with(0, True)


class TestAbletonClipService:
    """Test cases for clip service adapter."""

    async def test_fire_clip(self) -> None:
        """Test firing a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.fire_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.fire_clip(0, 0)

        mock_gateway.fire_clip.assert_called_once_with(0, 0)

    async def test_stop_clip(self) -> None:
        """Test stopping a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.stop_clip(0, 0)

        mock_gateway.stop_clip.assert_called_once_with(0, 0)

    async def test_add_note(self) -> None:
        """Test adding a note to a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.add_note = AsyncMock()

        note = Note(pitch=60, start=0.0, duration=1.0, velocity=100, mute=False)

        service = AbletonClipService(gateway=mock_gateway)
        await service.add_note(0, 0, note)

        mock_gateway.add_note.assert_called_once_with(
            track_id=0,
            clip_id=0,
            pitch=60,
            start=0.0,
            duration=1.0,
            velocity=100,
            mute=False,
        )

    async def test_create_clip(self) -> None:
        """Test creating a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.create_clip(0, 0, 4.0)

        mock_gateway.create_clip.assert_called_once_with(0, 0, 4.0)

    async def test_delete_clip(self) -> None:
        """Test deleting a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.delete_clip = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.delete_clip(0, 0)

        mock_gateway.delete_clip.assert_called_once_with(0, 0)

    async def test_get_clip_notes(self) -> None:
        """Test getting clip notes."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_clip_notes = AsyncMock(return_value=[])

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.get_clip_notes(0, 1)

        assert result == []
        mock_gateway.get_clip_notes.assert_called_once_with(0, 1)

    async def test_get_clip_name(self) -> None:
        """Test getting clip name."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_clip_name = AsyncMock(return_value="My Clip")

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.get_clip_name(0, 0)

        assert result == "My Clip"

    async def test_set_clip_name(self) -> None:
        """Test setting clip name."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_clip_name = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.set_clip_name(0, 0, "New Name")

        mock_gateway.set_clip_name.assert_called_once_with(0, 0, "New Name")

    async def test_get_clip_length(self) -> None:
        """Test getting clip length."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_clip_length = AsyncMock(return_value=8.0)

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.get_clip_length(0, 0)

        assert result == 8.0

    async def test_set_clip_length(self) -> None:
        """Test setting clip length."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_clip_length = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.set_clip_length(0, 0, 16.0)

        mock_gateway.set_clip_length.assert_called_once_with(0, 0, 16.0)

    async def test_get_clip_loop_start(self) -> None:
        """Test getting clip loop start."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_clip_loop_start = AsyncMock(return_value=2.0)

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.get_clip_loop_start(0, 0)

        assert result == 2.0

    async def test_set_clip_loop_start(self) -> None:
        """Test setting clip loop start."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_clip_loop_start = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.set_clip_loop_start(0, 0, 4.0)

        mock_gateway.set_clip_loop_start.assert_called_once_with(0, 0, 4.0)

    async def test_get_clip_loop_end(self) -> None:
        """Test getting clip loop end."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_clip_loop_end = AsyncMock(return_value=8.0)

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.get_clip_loop_end(0, 0)

        assert result == 8.0

    async def test_set_clip_loop_end(self) -> None:
        """Test setting clip loop end."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_clip_loop_end = AsyncMock()

        service = AbletonClipService(gateway=mock_gateway)
        await service.set_clip_loop_end(0, 0, 16.0)

        mock_gateway.set_clip_loop_end.assert_called_once_with(0, 0, 16.0)

    async def test_get_clip_is_playing(self) -> None:
        """Test checking if clip is playing."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_clip_is_playing = AsyncMock(return_value=True)

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.get_clip_is_playing(0, 0)

        assert result is True

    async def test_get_clip_playing_position(self) -> None:
        """Test getting clip playing position."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_clip_playing_position = AsyncMock(return_value=3.5)

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.get_clip_playing_position(0, 0)

        assert result == 3.5

    async def test_has_clip(self) -> None:
        """Test checking if clip slot has a clip."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.has_clip = AsyncMock(return_value=True)

        service = AbletonClipService(gateway=mock_gateway)
        result = await service.has_clip(0, 0)

        assert result is True


class TestAbletonTransportServiceExtended:
    """Test cases for extended transport service adapter methods."""

    async def test_continue_playing(self) -> None:
        """Test continuing playback."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.continue_playing = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.continue_playing()

        mock_gateway.continue_playing.assert_called_once()

    async def test_stop_all_clips(self) -> None:
        """Test stopping all clips."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_all_clips = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.stop_all_clips()

        mock_gateway.stop_all_clips.assert_called_once()

    async def test_tap_tempo(self) -> None:
        """Test tap tempo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.tap_tempo = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.tap_tempo()

        mock_gateway.tap_tempo.assert_called_once()

    async def test_undo(self) -> None:
        """Test undo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.undo = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.undo()

        mock_gateway.undo.assert_called_once()

    async def test_redo(self) -> None:
        """Test redo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.redo = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.redo()

        mock_gateway.redo.assert_called_once()

    async def test_capture_midi(self) -> None:
        """Test capture MIDI."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.capture_midi = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.capture_midi()

        mock_gateway.capture_midi.assert_called_once()

    async def test_trigger_session_record(self) -> None:
        """Test trigger session record."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.trigger_session_record = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.trigger_session_record()

        mock_gateway.trigger_session_record.assert_called_once()

    async def test_jump_by(self) -> None:
        """Test jump by beats."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.jump_by = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.jump_by(8.0)

        mock_gateway.jump_by.assert_called_once_with(8.0)

    async def test_jump_to(self) -> None:
        """Test jump to position."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.jump_to = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.jump_to(32.0)

        mock_gateway.jump_to.assert_called_once_with(32.0)

    async def test_jump_to_next_cue(self) -> None:
        """Test jump to next cue."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.jump_to_next_cue = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.jump_to_next_cue()

        mock_gateway.jump_to_next_cue.assert_called_once()

    async def test_jump_to_prev_cue(self) -> None:
        """Test jump to previous cue."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.jump_to_prev_cue = AsyncMock()

        service = AbletonTransportService(gateway=mock_gateway)
        await service.jump_to_prev_cue()

        mock_gateway.jump_to_prev_cue.assert_called_once()


class TestAbletonTrackServiceExtended:
    """Test cases for extended track service adapter methods."""

    async def test_set_track_color(self) -> None:
        """Test setting track color."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_color = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_color(0, 5)

        mock_gateway.set_track_color.assert_called_once_with(0, 5)

    async def test_get_track_send(self) -> None:
        """Test getting track send."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_track_send = AsyncMock(return_value=0.6)

        service = AbletonTrackService(gateway=mock_gateway)
        result = await service.get_track_send(0, 1)

        assert result == 0.6
        mock_gateway.get_track_send.assert_called_once_with(0, 1)

    async def test_set_track_send(self) -> None:
        """Test setting track send."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_track_send = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.set_track_send(0, 1, 0.8)

        mock_gateway.set_track_send.assert_called_once_with(0, 1, 0.8)

    async def test_stop_all_track_clips(self) -> None:
        """Test stopping all clips on a track."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.stop_all_track_clips = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.stop_all_track_clips(2)

        mock_gateway.stop_all_track_clips.assert_called_once_with(2)

    async def test_duplicate_track(self) -> None:
        """Test duplicating a track."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.duplicate_track = AsyncMock()

        service = AbletonTrackService(gateway=mock_gateway)
        await service.duplicate_track(1)

        mock_gateway.duplicate_track.assert_called_once_with(1)


class TestAbletonSceneService:
    """Test cases for scene service adapter."""

    async def test_get_num_scenes(self) -> None:
        """Test getting number of scenes."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_num_scenes = AsyncMock(return_value=8)

        service = AbletonSceneService(gateway=mock_gateway)
        result = await service.get_num_scenes()

        assert result == 8

    async def test_fire_scene(self) -> None:
        """Test firing a scene."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.fire_scene = AsyncMock()

        service = AbletonSceneService(gateway=mock_gateway)
        await service.fire_scene(2)

        mock_gateway.fire_scene.assert_called_once_with(2)

    async def test_get_scene_info(self) -> None:
        """Test getting scene info."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_scene_name = AsyncMock(return_value="Intro")
        mock_gateway.get_scene_color = AsyncMock(return_value=5)

        service = AbletonSceneService(gateway=mock_gateway)
        result = await service.get_scene_info(0)

        assert result == {"scene_id": 0, "name": "Intro", "color": 5}

    async def test_set_scene_name(self) -> None:
        """Test setting scene name."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_scene_name = AsyncMock()

        service = AbletonSceneService(gateway=mock_gateway)
        await service.set_scene_name(0, "Chorus")

        mock_gateway.set_scene_name.assert_called_once_with(0, "Chorus")

    async def test_set_scene_color(self) -> None:
        """Test setting scene color."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_scene_color = AsyncMock()

        service = AbletonSceneService(gateway=mock_gateway)
        await service.set_scene_color(0, 10)

        mock_gateway.set_scene_color.assert_called_once_with(0, 10)

    async def test_create_scene(self) -> None:
        """Test creating a scene."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_scene = AsyncMock()

        service = AbletonSceneService(gateway=mock_gateway)
        await service.create_scene(3)

        mock_gateway.create_scene.assert_called_once_with(3)

    async def test_delete_scene(self) -> None:
        """Test deleting a scene."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.delete_scene = AsyncMock()

        service = AbletonSceneService(gateway=mock_gateway)
        await service.delete_scene(1)

        mock_gateway.delete_scene.assert_called_once_with(1)


class TestAbletonReturnTrackService:
    """Test cases for return track service adapter."""

    async def test_create_return_track(self) -> None:
        """Test creating a return track."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.create_return_track = AsyncMock()

        service = AbletonReturnTrackService(gateway=mock_gateway)
        await service.create_return_track()

        mock_gateway.create_return_track.assert_called_once()

    async def test_get_return_track_info(self) -> None:
        """Test getting return track info."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_return_track_name = AsyncMock(return_value="Reverb")
        mock_gateway.get_return_track_volume = AsyncMock(return_value=0.8)
        mock_gateway.get_return_track_pan = AsyncMock(return_value=0.0)
        mock_gateway.get_return_track_mute = AsyncMock(return_value=False)

        service = AbletonReturnTrackService(gateway=mock_gateway)
        result = await service.get_return_track_info(0)

        assert result["name"] == "Reverb"
        assert result["volume"] == 0.8
        assert result["muted"] is False

    async def test_set_return_track_volume(self) -> None:
        """Test setting return track volume."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_return_track_volume = AsyncMock()

        service = AbletonReturnTrackService(gateway=mock_gateway)
        await service.set_return_track_volume(0, 0.7)

        mock_gateway.set_return_track_volume.assert_called_once_with(0, 0.7)

    async def test_set_return_track_pan(self) -> None:
        """Test setting return track pan."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_return_track_pan = AsyncMock()

        service = AbletonReturnTrackService(gateway=mock_gateway)
        await service.set_return_track_pan(0, -0.3)

        mock_gateway.set_return_track_pan.assert_called_once_with(0, -0.3)

    async def test_set_return_track_mute(self) -> None:
        """Test setting return track mute."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_return_track_mute = AsyncMock()

        service = AbletonReturnTrackService(gateway=mock_gateway)
        await service.set_return_track_mute(0, True)

        mock_gateway.set_return_track_mute.assert_called_once_with(0, True)

    async def test_set_return_track_name(self) -> None:
        """Test setting return track name."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_return_track_name = AsyncMock()

        service = AbletonReturnTrackService(gateway=mock_gateway)
        await service.set_return_track_name(0, "Delay")

        mock_gateway.set_return_track_name.assert_called_once_with(0, "Delay")

    async def test_get_master_info(self) -> None:
        """Test getting master track info."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_master_volume = AsyncMock(return_value=0.85)
        mock_gateway.get_master_pan = AsyncMock(return_value=0.0)

        service = AbletonReturnTrackService(gateway=mock_gateway)
        result = await service.get_master_info()

        assert result == {"volume": 0.85, "pan": 0.0}

    async def test_set_master_volume(self) -> None:
        """Test setting master volume."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_master_volume = AsyncMock()

        service = AbletonReturnTrackService(gateway=mock_gateway)
        await service.set_master_volume(0.9)

        mock_gateway.set_master_volume.assert_called_once_with(0.9)

    async def test_set_master_pan(self) -> None:
        """Test setting master pan."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_master_pan = AsyncMock()

        service = AbletonReturnTrackService(gateway=mock_gateway)
        await service.set_master_pan(0.1)

        mock_gateway.set_master_pan.assert_called_once_with(0.1)


class TestAbletonDeviceService:
    """Test cases for device service adapter."""

    async def test_get_device_info(self) -> None:
        """Test getting device info."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_device_name = AsyncMock(return_value="EQ Eight")
        mock_gateway.get_device_class_name = AsyncMock(return_value="PluginDevice")
        mock_gateway.get_device_num_parameters = AsyncMock(return_value=10)
        mock_gateway.get_device_is_active = AsyncMock(return_value=True)

        service = AbletonDeviceService(gateway=mock_gateway)
        result = await service.get_device_info(0, 0)

        assert result["name"] == "EQ Eight"
        assert result["class_name"] == "PluginDevice"
        assert result["num_parameters"] == 10
        assert result["is_active"] is True

    async def test_set_device_active(self) -> None:
        """Test setting device active state."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_device_is_active = AsyncMock()

        service = AbletonDeviceService(gateway=mock_gateway)
        await service.set_device_active(0, 0, False)

        mock_gateway.set_device_is_active.assert_called_once_with(0, 0, False)

    async def test_get_parameter_info(self) -> None:
        """Test getting parameter info."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_device_parameter_name = AsyncMock(return_value="Frequency")
        mock_gateway.get_device_parameter_value = AsyncMock(return_value=0.5)
        mock_gateway.get_device_parameter_display_value = AsyncMock(return_value="1.00 kHz")
        mock_gateway.get_device_parameter_min = AsyncMock(return_value=0.0)
        mock_gateway.get_device_parameter_max = AsyncMock(return_value=1.0)

        service = AbletonDeviceService(gateway=mock_gateway)
        result = await service.get_parameter_info(0, 0, 1)

        assert result["name"] == "Frequency"
        assert result["value"] == 0.5
        assert result["display_value"] == "1.00 kHz"

    async def test_set_parameter_value(self) -> None:
        """Test setting parameter value."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_device_parameter = AsyncMock()

        service = AbletonDeviceService(gateway=mock_gateway)
        await service.set_parameter_value(0, 0, 1, 0.75)

        mock_gateway.set_device_parameter.assert_called_once_with(0, 0, 1, 0.75)

    async def test_get_all_parameters(self) -> None:
        """Test getting all parameters."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_device_parameters = AsyncMock(return_value=[{"id": 0, "name": "On"}])

        service = AbletonDeviceService(gateway=mock_gateway)
        result = await service.get_all_parameters(0, 0)

        assert len(result) == 1
        assert result[0]["name"] == "On"


class TestAbletonSongPropertyService:
    """Test cases for song property service adapter."""

    async def test_set_swing(self) -> None:
        """Test setting swing."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_swing_amount = AsyncMock()

        service = AbletonSongPropertyService(gateway=mock_gateway)
        await service.set_swing(0.4)

        mock_gateway.set_swing_amount.assert_called_once_with(0.4)

    async def test_set_metronome(self) -> None:
        """Test setting metronome."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_metronome = AsyncMock()

        service = AbletonSongPropertyService(gateway=mock_gateway)
        await service.set_metronome(True)

        mock_gateway.set_metronome.assert_called_once_with(True)

    async def test_set_overdub(self) -> None:
        """Test setting overdub."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_overdub = AsyncMock()

        service = AbletonSongPropertyService(gateway=mock_gateway)
        await service.set_overdub(True)

        mock_gateway.set_overdub.assert_called_once_with(True)

    async def test_set_loop(self) -> None:
        """Test setting loop."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_loop = AsyncMock()

        service = AbletonSongPropertyService(gateway=mock_gateway)
        await service.set_loop(True)

        mock_gateway.set_loop.assert_called_once_with(True)

    async def test_set_loop_start(self) -> None:
        """Test setting loop start."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_loop_start = AsyncMock()

        service = AbletonSongPropertyService(gateway=mock_gateway)
        await service.set_loop_start(16.0)

        mock_gateway.set_loop_start.assert_called_once_with(16.0)

    async def test_set_loop_length(self) -> None:
        """Test setting loop length."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_loop_length = AsyncMock()

        service = AbletonSongPropertyService(gateway=mock_gateway)
        await service.set_loop_length(32.0)

        mock_gateway.set_loop_length.assert_called_once_with(32.0)

    async def test_set_tempo(self) -> None:
        """Test setting tempo."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.set_tempo = AsyncMock()

        service = AbletonSongPropertyService(gateway=mock_gateway)
        await service.set_tempo(140.0)

        mock_gateway.set_tempo.assert_called_once_with(140.0)

    async def test_get_song_properties(self) -> None:
        """Test getting all song properties."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.get_swing_amount = AsyncMock(return_value=0.0)
        mock_gateway.get_metronome = AsyncMock(return_value=False)
        mock_gateway.get_overdub = AsyncMock(return_value=False)
        mock_gateway.get_song_length = AsyncMock(return_value=128.0)
        mock_gateway.get_loop = AsyncMock(return_value=True)
        mock_gateway.get_loop_start = AsyncMock(return_value=0.0)
        mock_gateway.get_loop_length = AsyncMock(return_value=16.0)
        mock_gateway.get_record_mode = AsyncMock(return_value=False)
        mock_gateway.get_session_record = AsyncMock(return_value=False)
        mock_gateway.get_punch_in = AsyncMock(return_value=False)
        mock_gateway.get_punch_out = AsyncMock(return_value=False)

        service = AbletonSongPropertyService(gateway=mock_gateway)
        result = await service.get_song_properties()

        assert result["swing_amount"] == 0.0
        assert result["loop"] is True
        assert result["song_length"] == 128.0
        assert result["loop_length"] == 16.0
