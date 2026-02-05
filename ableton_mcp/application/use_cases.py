"""Application use cases implementing business workflows."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import structlog

from ableton_mcp.core.exceptions import (
    ClipNotFoundError,
    InvalidParameterError,
    TrackNotFoundError,
    ValidationError,
)
from ableton_mcp.domain.entities import (
    EntityId,
    Note,
    Song,
    Track,
    TrackType,
    TransportState,
)
from ableton_mcp.domain.repositories import (
    ClipRepository,
    SongRepository,
    TrackRepository,
)
from ableton_mcp.domain.services import (
    ArrangementService,
    MixingService,
    MusicTheoryService,
    TempoAnalysisService,
    ValidationService,
)


@dataclass
class UseCaseResult:
    """Result wrapper for use case operations."""

    success: bool
    data: Any | None = None
    message: str | None = None
    error_code: str | None = None


class UseCase(ABC):
    """Base class for all use cases."""

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> UseCaseResult:
        """Execute the use case."""
        pass


@dataclass
class ConnectToAbletonRequest:
    """Request to connect to Ableton Live."""

    host: str = "127.0.0.1"
    send_port: int = 11000
    receive_port: int = 11001


class ConnectToAbletonUseCase(UseCase):
    """Use case for establishing connection to Ableton Live."""

    def __init__(
        self,
        connection_service: Any,
        song_repository: SongRepository,
        ableton_gateway: Any,
    ) -> None:
        self._connection_service = connection_service
        self._song_repository = song_repository
        self._gateway = ableton_gateway

    async def execute(self, request: ConnectToAbletonRequest) -> UseCaseResult:
        """Execute connection to Ableton Live and sync song data."""
        try:
            await self._connection_service.connect(
                request.host, request.send_port, request.receive_port
            )

            # Fetch and store song data from Ableton
            await self._sync_song_data()

            return UseCaseResult(
                success=True,
                message=f"Connected to Ableton Live at {request.host}:{request.send_port}",
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Failed to connect: {e!s}",
                error_code="CONNECTION_FAILED",
            )

    async def _sync_song_data(self) -> None:
        """Fetch song data from Ableton and store in repository."""
        # Get basic song info
        tempo = await self._gateway.get_tempo()
        time_sig = await self._gateway.get_time_signature()
        song_time = await self._gateway.get_song_time()
        is_playing = await self._gateway.get_is_playing()
        num_tracks = await self._gateway.get_num_tracks()

        # Build track list
        tracks: list[Track] = []
        for i in range(num_tracks):
            try:
                track_name = await self._gateway.get_track_name(i)
                track_volume = await self._gateway.get_track_volume(i)
                track_pan = await self._gateway.get_track_pan(i)
                has_midi_input = await self._gateway.get_track_has_midi_input(i)
                track_type = TrackType.MIDI if has_midi_input else TrackType.AUDIO
                is_muted = await self._gateway.get_track_mute(i)
                is_soloed = await self._gateway.get_track_solo(i)
                is_armed = await self._gateway.get_track_arm(i)

                track = Track(
                    id=EntityId(value=f"track_{i}"),
                    name=track_name,
                    track_type=track_type,
                    volume=track_volume,
                    pan=track_pan,
                    is_muted=is_muted,
                    is_soloed=is_soloed,
                    is_armed=is_armed,
                )
                tracks.append(track)
            except Exception:
                # Skip tracks that fail to load
                continue

        # Build and save song
        song = Song(
            id=EntityId(value="current_song"),
            name="Live Set",
            tempo=tempo,
            time_signature_numerator=time_sig[0],
            time_signature_denominator=time_sig[1],
            current_song_time=song_time,
            transport_state=TransportState.PLAYING if is_playing else TransportState.STOPPED,
            tracks=tracks,
        )

        await self._song_repository.save_song(song)


@dataclass
class RefreshSongDataRequest:
    """Request for refreshing song data cache from Ableton."""

    pass


class RefreshSongDataUseCase(UseCase):
    """Use case for refreshing cached song data from Ableton Live."""

    def __init__(
        self,
        song_repository: SongRepository,
        ableton_gateway: Any,
    ) -> None:
        self._song_repository = song_repository
        self._gateway = ableton_gateway
        self._logger = structlog.get_logger(__name__)

    async def execute(self, _request: RefreshSongDataRequest | None = None) -> UseCaseResult:
        """Refresh song data from Ableton Live."""
        try:
            self._logger.info("Refreshing song data from Ableton")
            await self._sync_song_data()
            self._logger.info("Song data refreshed successfully")
            return UseCaseResult(
                success=True,
                message="Song data refreshed from Ableton Live",
            )
        except Exception as e:
            self._logger.error("Failed to refresh song data", error=str(e))
            return UseCaseResult(
                success=False,
                message=f"Failed to refresh song data: {e!s}",
                error_code="REFRESH_FAILED",
            )

    async def _sync_song_data(self) -> None:
        """Fetch song data from Ableton and store in repository."""
        # Get basic song info
        tempo = await self._gateway.get_tempo()
        time_sig = await self._gateway.get_time_signature()
        song_time = await self._gateway.get_song_time()
        is_playing = await self._gateway.get_is_playing()
        num_tracks = await self._gateway.get_num_tracks()

        # Build track list
        tracks: list[Track] = []
        for i in range(num_tracks):
            try:
                track_name = await self._gateway.get_track_name(i)
                track_volume = await self._gateway.get_track_volume(i)
                track_pan = await self._gateway.get_track_pan(i)
                has_midi_input = await self._gateway.get_track_has_midi_input(i)
                track_type = TrackType.MIDI if has_midi_input else TrackType.AUDIO
                is_muted = await self._gateway.get_track_mute(i)
                is_soloed = await self._gateway.get_track_solo(i)
                is_armed = await self._gateway.get_track_arm(i)

                track = Track(
                    id=EntityId(value=f"track_{i}"),
                    name=track_name,
                    track_type=track_type,
                    volume=track_volume,
                    pan=track_pan,
                    is_muted=is_muted,
                    is_soloed=is_soloed,
                    is_armed=is_armed,
                )
                tracks.append(track)
            except Exception:
                # Skip tracks that fail to load
                continue

        # Build and save song
        song = Song(
            id=EntityId(value="current_song"),
            name="Live Set",
            tempo=tempo,
            time_signature_numerator=time_sig[0],
            time_signature_denominator=time_sig[1],
            current_song_time=song_time,
            transport_state=TransportState.PLAYING if is_playing else TransportState.STOPPED,
            tracks=tracks,
        )

        await self._song_repository.save_song(song)


@dataclass
class TransportControlRequest:
    """Request for transport control operations."""

    action: str  # play, stop, record, get_status, continue, stop_all_clips,
    #   tap_tempo, undo, redo, capture_midi, session_record,
    #   jump_by, jump_to, next_cue, prev_cue
    value: float | None = None


class TransportControlUseCase(UseCase):
    """Use case for controlling Ableton Live transport."""

    def __init__(self, transport_service: Any, song_repository: SongRepository) -> None:
        self._transport_service = transport_service
        self._song_repository = song_repository

    async def execute(self, request: TransportControlRequest) -> UseCaseResult:
        """Execute transport control command."""
        try:
            if request.action == "play":
                await self._transport_service.start_playing()
                return UseCaseResult(success=True, message="Playback started")

            elif request.action == "stop":
                await self._transport_service.stop_playing()
                return UseCaseResult(success=True, message="Playback stopped")

            elif request.action == "record":
                await self._transport_service.start_recording()
                return UseCaseResult(success=True, message="Recording started")

            elif request.action == "continue":
                await self._transport_service.continue_playing()
                return UseCaseResult(success=True, message="Playback continued")

            elif request.action == "stop_all_clips":
                await self._transport_service.stop_all_clips()
                return UseCaseResult(success=True, message="All clips stopped")

            elif request.action == "tap_tempo":
                await self._transport_service.tap_tempo()
                return UseCaseResult(success=True, message="Tap tempo registered")

            elif request.action == "undo":
                await self._transport_service.undo()
                return UseCaseResult(success=True, message="Undo performed")

            elif request.action == "redo":
                await self._transport_service.redo()
                return UseCaseResult(success=True, message="Redo performed")

            elif request.action == "capture_midi":
                await self._transport_service.capture_midi()
                return UseCaseResult(success=True, message="MIDI captured")

            elif request.action == "session_record":
                await self._transport_service.trigger_session_record()
                return UseCaseResult(success=True, message="Session record toggled")

            elif request.action == "jump_by":
                if request.value is None:
                    return UseCaseResult(
                        success=False,
                        message="Value (beats) is required for jump_by",
                        error_code="INVALID_PARAMETER",
                    )
                await self._transport_service.jump_by(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Jumped by {request.value} beats",
                )

            elif request.action == "jump_to":
                if request.value is None:
                    return UseCaseResult(
                        success=False,
                        message="Value (time) is required for jump_to",
                        error_code="INVALID_PARAMETER",
                    )
                await self._transport_service.jump_to(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Jumped to position {request.value}",
                )

            elif request.action == "next_cue":
                await self._transport_service.jump_to_next_cue()
                return UseCaseResult(success=True, message="Jumped to next cue point")

            elif request.action == "prev_cue":
                await self._transport_service.jump_to_prev_cue()
                return UseCaseResult(success=True, message="Jumped to previous cue point")

            elif request.action == "get_status":
                song = await self._song_repository.get_current_song()
                if song:
                    return UseCaseResult(
                        success=True,
                        data={
                            "state": song.transport_state.value,
                            "tempo": song.tempo,
                            "current_time": song.current_song_time,
                        },
                    )
                return UseCaseResult(success=False, message="No active song")

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown transport action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Transport control error: {e!s}",
                error_code="TRANSPORT_ERROR",
            )


@dataclass
class GetSongInfoRequest:
    """Request for getting song information."""

    include_tracks: bool = True
    include_devices: bool = True
    include_clips: bool = False


class GetSongInfoUseCase(UseCase):
    """Use case for retrieving song information."""

    def __init__(self, song_repository: SongRepository) -> None:
        self._song_repository = song_repository

    async def execute(self, request: GetSongInfoRequest) -> UseCaseResult:
        """Get comprehensive song information."""
        try:
            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            data = {
                "name": song.name,
                "tempo": song.tempo,
                "time_signature": f"{song.time_signature_numerator}/{song.time_signature_denominator}",
                "key": song.key,
                "current_time": song.current_song_time,
                "transport_state": song.transport_state.value,
                "loop_enabled": song.is_loop_on,
                "loop_start": song.loop_start,
                "loop_end": song.loop_end,
            }

            if request.include_tracks:
                tracks_data = []
                for i, track in enumerate(song.tracks):
                    track_data = {
                        "index": i,
                        "name": track.name,
                        "type": track.track_type.value,
                        "volume": track.volume,
                        "pan": track.pan,
                        "muted": track.is_muted,
                        "soloed": track.is_soloed,
                        "armed": track.is_armed,
                    }

                    if request.include_devices:
                        track_data["devices"] = [
                            {"name": device.name, "type": device.device_type.value}
                            for device in track.devices
                        ]

                    if request.include_clips:
                        track_data["clips"] = [
                            {
                                "name": clip.name if clip else None,
                                "type": clip.clip_type.value if clip else None,
                                "length": clip.length if clip else None,
                            }
                            for clip in track.clips
                        ]

                    tracks_data.append(track_data)

                data["tracks"] = tracks_data

            return UseCaseResult(success=True, data=data)

        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Error getting song info: {e!s}",
                error_code="SONG_INFO_ERROR",
            )


@dataclass
class TrackOperationRequest:
    """Request for track operations."""

    action: str  # get_info, set_volume, set_pan, mute, solo, arm, create, delete,
    #   set_color, set_send, stop_all_clips, duplicate, select
    track_id: int | None = None
    value: float | None = None
    name: str | None = None
    track_type: str | None = None
    color: int | None = None
    send_id: int | None = None


class TrackOperationsUseCase(UseCase):
    """Use case for track operations."""

    def __init__(
        self,
        track_repository: TrackRepository,
        song_repository: SongRepository,
        track_service: Any,
        refresh_use_case: Optional["RefreshSongDataUseCase"] = None,
    ) -> None:
        self._track_repository = track_repository
        self._song_repository = song_repository
        self._track_service = track_service
        self._refresh_use_case = refresh_use_case
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: TrackOperationRequest) -> UseCaseResult:
        """Execute track operation."""
        try:
            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            if request.action == "create":
                track_type = TrackType(request.track_type or "midi")
                track_name = request.name or f"New {track_type.value.title()} Track"

                new_track = Track(
                    name=track_name,
                    track_type=track_type,
                )

                await self._track_service.create_track(new_track)

                # Auto-refresh song data after track creation
                if self._refresh_use_case:
                    self._logger.info("Auto-refreshing song data after track creation")
                    await self._refresh_use_case.execute()

                return UseCaseResult(
                    success=True,
                    message=f"Created {track_type.value} track: {track_name}",
                )

            # Operations requiring existing track
            if request.track_id is None:
                raise InvalidParameterError("Track ID is required")

            track = song.get_track_by_index(request.track_id)
            if not track:
                raise TrackNotFoundError(f"Track {request.track_id} not found")

            if request.action == "get_info":
                return UseCaseResult(
                    success=True,
                    data={
                        "name": track.name,
                        "type": track.track_type.value,
                        "volume": track.volume,
                        "pan": track.pan,
                        "muted": track.is_muted,
                        "soloed": track.is_soloed,
                        "armed": track.is_armed,
                        "device_count": len(track.devices),
                        "clip_count": len([c for c in track.clips if c is not None]),
                    },
                )

            elif request.action == "set_volume":
                if request.value is None:
                    raise InvalidParameterError("Volume value is required")

                track.volume = max(0.0, min(1.0, request.value))
                await self._track_service.set_track_volume(request.track_id, track.volume)
                return UseCaseResult(
                    success=True, message=f"Set track volume to {track.volume:.2f}"
                )

            elif request.action == "set_pan":
                if request.value is None:
                    raise InvalidParameterError("Pan value is required")

                track.pan = max(-1.0, min(1.0, request.value))
                await self._track_service.set_track_pan(request.track_id, track.pan)
                return UseCaseResult(success=True, message=f"Set track pan to {track.pan:.2f}")

            elif request.action in ["mute", "solo", "arm"]:
                if request.action == "mute":
                    track.is_muted = not track.is_muted
                    await self._track_service.set_track_mute(request.track_id, track.is_muted)
                    state = "muted" if track.is_muted else "unmuted"
                elif request.action == "solo":
                    track.is_soloed = not track.is_soloed
                    await self._track_service.set_track_solo(request.track_id, track.is_soloed)
                    state = "soloed" if track.is_soloed else "unsoloed"
                else:  # arm
                    track.is_armed = not track.is_armed
                    await self._track_service.set_track_arm(request.track_id, track.is_armed)
                    state = "armed" if track.is_armed else "disarmed"

                return UseCaseResult(success=True, message=f"Track {state}")

            elif request.action == "set_color":
                if request.color is None:
                    raise InvalidParameterError("Color value is required")
                await self._track_service.set_track_color(request.track_id, request.color)
                return UseCaseResult(
                    success=True,
                    message=f"Set track color to {request.color}",
                )

            elif request.action == "set_send":
                if request.send_id is None or request.value is None:
                    raise InvalidParameterError("send_id and value are required for set_send")
                await self._track_service.set_track_send(
                    request.track_id, request.send_id, request.value
                )
                return UseCaseResult(
                    success=True,
                    message=f"Set track send {request.send_id} to {request.value:.2f}",
                )

            elif request.action == "stop_all_clips":
                await self._track_service.stop_all_track_clips(request.track_id)
                return UseCaseResult(success=True, message="Stopped all clips on track")

            elif request.action == "duplicate":
                await self._track_service.duplicate_track(request.track_id)
                if self._refresh_use_case:
                    await self._refresh_use_case.execute()
                return UseCaseResult(success=True, message="Track duplicated")

            elif request.action == "delete":
                from ableton_mcp.adapters.service_adapters import AbletonTrackService

                if isinstance(self._track_service, AbletonTrackService):
                    await self._track_service._gateway.delete_track(request.track_id)
                if self._refresh_use_case:
                    await self._refresh_use_case.execute()
                return UseCaseResult(success=True, message="Track deleted")

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown track action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except (TrackNotFoundError, InvalidParameterError) as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Track operation error: {e!s}",
                error_code="TRACK_ERROR",
            )


@dataclass
class AddNotesRequest:
    """Request for adding MIDI notes to a clip."""

    track_id: int
    clip_id: int
    notes: list[dict[str, Any]]
    quantize: bool = False
    scale_filter: str | None = None


class AddNotesUseCase(UseCase):
    """Use case for adding MIDI notes with music theory assistance."""

    def __init__(
        self,
        clip_repository: ClipRepository,
        song_repository: SongRepository,
        music_theory_service: MusicTheoryService,
        clip_service: Any,
    ) -> None:
        self._clip_repository = clip_repository
        self._song_repository = song_repository
        self._music_theory_service = music_theory_service
        self._clip_service = clip_service

    async def execute(self, request: AddNotesRequest) -> UseCaseResult:
        """Add MIDI notes to a clip with intelligent processing."""
        try:
            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            track = song.get_track_by_index(request.track_id)
            if not track:
                raise TrackNotFoundError(f"Track {request.track_id} not found")

            # Check track type - only MIDI tracks can have notes added
            if track.track_type != TrackType.MIDI:
                raise InvalidParameterError("Can only add notes to MIDI tracks")

            # Convert note dictionaries to Note objects
            notes = []
            for note_data in request.notes:
                try:
                    note = Note(
                        pitch=note_data["pitch"],
                        start=note_data["start"],
                        duration=note_data["duration"],
                        velocity=note_data.get("velocity", 100),
                    )
                    notes.append(note)
                except Exception as e:
                    raise InvalidParameterError(f"Invalid note data: {e!s}") from e

            # Apply music theory processing
            if request.scale_filter:
                from ableton_mcp.domain.entities import MusicKey

                # This would use actual key detection in a real implementation
                key = MusicKey(root=0, mode=request.scale_filter)
                notes = await self._music_theory_service.filter_notes_to_scale(notes, key)

            if request.quantize:
                notes = await self._music_theory_service.quantize_notes(notes)

            # Validate notes
            for note in notes:
                if not ValidationService.validate_note_range(note):
                    raise ValidationError(f"Note {note.pitch} is out of range")

            # Calculate clip length based on notes (end time of last note, rounded up to nearest bar)
            max_end_time = max(note.start + note.duration for note in notes)
            # Round up to nearest 4 beats (1 bar in 4/4)
            clip_length = ((int(max_end_time) // 4) + 1) * 4

            # Create the clip first (required before adding notes)
            await self._clip_service.create_clip(request.track_id, request.clip_id, clip_length)

            # Add notes directly to Ableton via clip service
            for note in notes:
                await self._clip_service.add_note(request.track_id, request.clip_id, note)

            return UseCaseResult(
                success=True,
                message=f"Added {len(notes)} notes to clip",
                data={"notes_added": len(notes)},
            )

        except (TrackNotFoundError, ClipNotFoundError, InvalidParameterError, ValidationError) as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Error adding notes: {e!s}",
                error_code="ADD_NOTES_ERROR",
            )


@dataclass
class AnalyzeHarmonyRequest:
    """Request for harmony analysis."""

    notes: list[int]
    suggest_progressions: bool = False
    genre: str = "pop"


class AnalyzeHarmonyUseCase(UseCase):
    """Use case for analyzing harmony and suggesting progressions."""

    def __init__(self, music_theory_service: MusicTheoryService) -> None:
        self._music_theory_service = music_theory_service

    async def execute(self, request: AnalyzeHarmonyRequest) -> UseCaseResult:
        """Analyze harmony and provide suggestions."""
        try:
            if not request.notes:
                return UseCaseResult(
                    success=False,
                    message="No notes provided for analysis",
                    error_code="INVALID_INPUT",
                )

            # Convert MIDI notes to Note objects for analysis
            notes = [Note(pitch=pitch, start=0.0, duration=1.0) for pitch in request.notes]

            # Analyze key
            keys = await self._music_theory_service.analyze_key(notes)

            result_data: dict[str, Any] = {
                "input_notes": request.notes,
                "detected_keys": [],
                "chord_progressions": [],
            }

            if keys:
                best_key = keys[0]
                result_data["detected_keys"] = [
                    {
                        "root": key.root,
                        "root_name": key.root_name,
                        "mode": key.mode,
                        "confidence": key.confidence,
                        "scale_notes": key.scale_notes,
                    }
                    for key in keys[:3]  # Top 3 matches
                ]

                if request.suggest_progressions:
                    progressions = await self._music_theory_service.suggest_chord_progressions(
                        best_key, request.genre
                    )
                    result_data["chord_progressions"] = progressions

            return UseCaseResult(success=True, data=result_data)

        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Harmony analysis error: {e!s}",
                error_code="HARMONY_ANALYSIS_ERROR",
            )


@dataclass
class AnalyzeTempoRequest:
    """Request for tempo analysis."""

    current_bpm: float | None = None
    genre: str | None = None
    energy_level: str = "medium"


class AnalyzeTempoUseCase(UseCase):
    """Use case for tempo analysis and suggestions."""

    def __init__(
        self,
        tempo_service: TempoAnalysisService,
        song_repository: SongRepository,
    ) -> None:
        self._tempo_service = tempo_service
        self._song_repository = song_repository

    async def execute(self, request: AnalyzeTempoRequest) -> UseCaseResult:
        """Analyze tempo and provide suggestions."""
        try:
            current_bpm = request.current_bpm
            if current_bpm is None:
                song = await self._song_repository.get_current_song()
                current_bpm = song.tempo if song else 120.0

            result_data: dict[str, Any] = {
                "current_tempo": current_bpm,
                "analysis": {
                    "energy_level": request.energy_level,
                    "genre": request.genre,
                },
                "suggestions": {},
            }

            if request.genre:
                suggested_tempo = await self._tempo_service.suggest_tempo_for_genre(
                    request.genre, request.energy_level
                )
                result_data["suggestions"]["genre_optimal"] = suggested_tempo

            # Mathematical relationships
            result_data["suggestions"]["relationships"] = {
                "half_time": current_bpm / 2,
                "double_time": current_bpm * 2,
                "three_quarter": current_bpm * 0.75,
                "four_thirds": current_bpm * 1.33,
            }

            return UseCaseResult(success=True, data=result_data)

        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Tempo analysis error: {e!s}",
                error_code="TEMPO_ANALYSIS_ERROR",
            )


@dataclass
class MixAnalysisRequest:
    """Request for mix analysis."""

    analyze_levels: bool = True
    analyze_frequency: bool = True
    target_lufs: float = -14.0
    platform: str = "spotify"


class MixAnalysisUseCase(UseCase):
    """Use case for mix analysis and suggestions."""

    def __init__(
        self,
        mixing_service: MixingService,
        song_repository: SongRepository,
    ) -> None:
        self._mixing_service = mixing_service
        self._song_repository = song_repository

    async def execute(self, request: MixAnalysisRequest) -> UseCaseResult:
        """Analyze mix and provide professional mixing suggestions."""
        try:
            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            result_data: dict[str, Any] = {
                "track_count": len(song.tracks),
                "platform": request.platform,
                "target_lufs": request.target_lufs,
            }

            # Analyze frequency balance
            if request.analyze_frequency:
                frequency_analysis = await self._mixing_service.analyze_frequency_balance(
                    song.tracks
                )
                result_data["frequency_analysis"] = frequency_analysis.data

            # Analyze stereo image
            stereo_analysis = await self._mixing_service.analyze_stereo_image(song.tracks)
            result_data["stereo_analysis"] = stereo_analysis.data

            # Analyze levels and get LUFS targets
            if request.analyze_levels:
                # Infer genre from song context or use default
                genre = "pop"  # Could be enhanced to detect from song
                target_lufs, target_peak = await self._mixing_service.calculate_lufs_target(
                    genre, request.platform
                )
                result_data["loudness_targets"] = {
                    "target_lufs": target_lufs,
                    "target_peak_db": target_peak,
                    "platform": request.platform,
                }

                # Analyze individual track levels
                level_analysis = []
                for i, track in enumerate(song.tracks):
                    track_info = {
                        "index": i,
                        "name": track.name,
                        "volume": track.volume,
                        "pan": track.pan,
                        "is_muted": track.is_muted,
                        "is_soloed": track.is_soloed,
                    }
                    # Flag potential issues
                    if track.volume > 0.9:
                        track_info["warning"] = "Volume near maximum - watch for clipping"
                    level_analysis.append(track_info)
                result_data["track_levels"] = level_analysis

            # Get EQ suggestions for each track
            eq_suggestions = []
            for track in song.tracks[:5]:  # Limit to first 5 tracks
                suggestions = await self._mixing_service.suggest_eq_adjustments(track)
                if suggestions:
                    eq_suggestions.append(
                        {
                            "track": track.name,
                            "suggestions": suggestions,
                        }
                    )
            result_data["eq_suggestions"] = eq_suggestions

            return UseCaseResult(success=True, data=result_data)

        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Mix analysis error: {e!s}",
                error_code="MIX_ANALYSIS_ERROR",
            )


@dataclass
class ArrangementSuggestionsRequest:
    """Request for arrangement suggestions."""

    song_length: float | None = None
    genre: str | None = None
    current_structure: list[str] | None = None


@dataclass
class GetClipContentRequest:
    """Request for getting clip content (MIDI notes)."""

    track_id: int
    clip_id: int


class GetClipContentUseCase(UseCase):
    """Use case for retrieving MIDI notes from a clip."""

    def __init__(
        self,
        clip_service: Any,
        song_repository: SongRepository,
    ) -> None:
        self._clip_service = clip_service
        self._song_repository = song_repository
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: GetClipContentRequest) -> UseCaseResult:
        """Get MIDI notes from a clip."""
        try:
            self._logger.info(
                "Getting clip content",
                track_id=request.track_id,
                clip_id=request.clip_id,
            )

            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            track = song.get_track_by_index(request.track_id)
            if not track:
                raise TrackNotFoundError(f"Track {request.track_id} not found")

            # Get notes from Ableton via clip service
            notes = await self._clip_service.get_clip_notes(request.track_id, request.clip_id)

            # Convert MIDI pitch to note names for display
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            notes_with_names = []
            for note in notes:
                pitch = note["pitch"]
                octave = (pitch // 12) - 1
                note_name = note_names[pitch % 12]
                notes_with_names.append(
                    {
                        **note,
                        "note_name": f"{note_name}{octave}",
                    }
                )

            self._logger.info(
                "Retrieved clip content",
                track_id=request.track_id,
                clip_id=request.clip_id,
                note_count=len(notes),
            )

            return UseCaseResult(
                success=True,
                data={
                    "track_id": request.track_id,
                    "clip_id": request.clip_id,
                    "note_count": len(notes),
                    "notes": notes_with_names,
                },
            )

        except TrackNotFoundError as e:
            self._logger.warning(
                "Track not found",
                track_id=request.track_id,
                error=str(e),
            )
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except ClipNotFoundError as e:
            self._logger.warning(
                "Clip not found",
                track_id=request.track_id,
                clip_id=request.clip_id,
                error=str(e),
            )
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            self._logger.error(
                "Error getting clip content",
                track_id=request.track_id,
                clip_id=request.clip_id,
                error=str(e),
            )
            return UseCaseResult(
                success=False,
                message=f"Error getting clip content: {e!s}",
                error_code="CLIP_CONTENT_ERROR",
            )


@dataclass
class SceneOperationRequest:
    """Request for scene operations."""

    action: str  # fire, get_info, create, delete, set_name, set_color, select
    scene_id: int | None = None
    name: str | None = None
    color: int | None = None
    index: int | None = None


class SceneOperationsUseCase(UseCase):
    """Use case for scene operations."""

    def __init__(self, scene_service: Any, song_repository: SongRepository) -> None:
        self._scene_service = scene_service
        self._song_repository = song_repository
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: SceneOperationRequest) -> UseCaseResult:
        """Execute scene operation."""
        try:
            if request.action == "fire":
                if request.scene_id is None:
                    raise InvalidParameterError("scene_id is required")
                await self._scene_service.fire_scene(request.scene_id)
                return UseCaseResult(success=True, message=f"Fired scene {request.scene_id}")

            elif request.action == "get_info":
                if request.scene_id is None:
                    raise InvalidParameterError("scene_id is required")
                info = await self._scene_service.get_scene_info(request.scene_id)
                return UseCaseResult(success=True, data=info)

            elif request.action == "create":
                index = request.index if request.index is not None else -1
                await self._scene_service.create_scene(index)
                return UseCaseResult(success=True, message=f"Created scene at index {index}")

            elif request.action == "delete":
                if request.scene_id is None:
                    raise InvalidParameterError("scene_id is required")
                await self._scene_service.delete_scene(request.scene_id)
                return UseCaseResult(
                    success=True,
                    message=f"Deleted scene {request.scene_id}",
                )

            elif request.action == "set_name":
                if request.scene_id is None or request.name is None:
                    raise InvalidParameterError("scene_id and name are required")
                await self._scene_service.set_scene_name(request.scene_id, request.name)
                return UseCaseResult(
                    success=True,
                    message=f"Set scene name to '{request.name}'",
                )

            elif request.action == "set_color":
                if request.scene_id is None or request.color is None:
                    raise InvalidParameterError("scene_id and color are required")
                await self._scene_service.set_scene_color(request.scene_id, request.color)
                return UseCaseResult(
                    success=True,
                    message=f"Set scene color to {request.color}",
                )

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown scene action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except InvalidParameterError as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            self._logger.error("Scene operation error", error=str(e))
            return UseCaseResult(
                success=False,
                message=f"Scene operation error: {e!s}",
                error_code="SCENE_ERROR",
            )


@dataclass
class SongPropertyRequest:
    """Request for song property operations."""

    action: str  # set_swing, set_metronome, set_overdub, set_loop,
    #   set_loop_start, set_loop_length, set_tempo, get_properties
    value: float | None = None
    enabled: bool | None = None


class SongPropertyUseCase(UseCase):
    """Use case for setting song-level properties."""

    def __init__(self, song_property_service: Any) -> None:
        self._service = song_property_service
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: SongPropertyRequest) -> UseCaseResult:
        """Execute song property operation."""
        try:
            if request.action == "get_properties":
                props = await self._service.get_song_properties()
                return UseCaseResult(success=True, data=props)

            elif request.action == "set_swing":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_swing")
                await self._service.set_swing(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set swing to {request.value}",
                )

            elif request.action == "set_metronome":
                if request.enabled is None:
                    raise InvalidParameterError("enabled is required for set_metronome")
                await self._service.set_metronome(request.enabled)
                state = "enabled" if request.enabled else "disabled"
                return UseCaseResult(success=True, message=f"Metronome {state}")

            elif request.action == "set_overdub":
                if request.enabled is None:
                    raise InvalidParameterError("enabled is required for set_overdub")
                await self._service.set_overdub(request.enabled)
                state = "enabled" if request.enabled else "disabled"
                return UseCaseResult(success=True, message=f"Overdub {state}")

            elif request.action == "set_loop":
                if request.enabled is None:
                    raise InvalidParameterError("enabled is required for set_loop")
                await self._service.set_loop(request.enabled)
                state = "enabled" if request.enabled else "disabled"
                return UseCaseResult(success=True, message=f"Loop {state}")

            elif request.action == "set_loop_start":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_loop_start")
                await self._service.set_loop_start(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set loop start to {request.value}",
                )

            elif request.action == "set_loop_length":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_loop_length")
                await self._service.set_loop_length(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set loop length to {request.value}",
                )

            elif request.action == "set_tempo":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_tempo")
                await self._service.set_tempo(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set tempo to {request.value} BPM",
                )

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown song property action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except InvalidParameterError as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            self._logger.error("Song property error", error=str(e))
            return UseCaseResult(
                success=False,
                message=f"Song property error: {e!s}",
                error_code="SONG_PROPERTY_ERROR",
            )


@dataclass
class ClipOperationRequest:
    """Request for clip operations."""

    action: str  # get_info, set_name, set_length, set_loop_start, set_loop_end,
    #   fire, stop, create, delete, has_clip
    track_id: int
    clip_id: int
    name: str | None = None
    length: float | None = None
    value: float | None = None


class ClipOperationsUseCase(UseCase):
    """Use case for clip operations beyond note manipulation."""

    def __init__(
        self,
        clip_service: Any,
        song_repository: SongRepository,
    ) -> None:
        self._clip_service = clip_service
        self._song_repository = song_repository
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: ClipOperationRequest) -> UseCaseResult:
        """Execute clip operation."""
        try:
            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            track = song.get_track_by_index(request.track_id)
            if not track:
                raise TrackNotFoundError(f"Track {request.track_id} not found")

            if request.action == "has_clip":
                result = await self._clip_service.has_clip(request.track_id, request.clip_id)
                return UseCaseResult(
                    success=True,
                    data={"has_clip": result},
                    message=f"Clip slot {'has' if result else 'does not have'} a clip",
                )

            elif request.action == "get_info":
                has = await self._clip_service.has_clip(request.track_id, request.clip_id)
                if not has:
                    raise ClipNotFoundError(
                        f"No clip in slot {request.clip_id} on track {request.track_id}"
                    )
                name = await self._clip_service.get_clip_name(request.track_id, request.clip_id)
                length = await self._clip_service.get_clip_length(request.track_id, request.clip_id)
                loop_start = await self._clip_service.get_clip_loop_start(
                    request.track_id, request.clip_id
                )
                loop_end = await self._clip_service.get_clip_loop_end(
                    request.track_id, request.clip_id
                )
                is_playing = await self._clip_service.get_clip_is_playing(
                    request.track_id, request.clip_id
                )
                return UseCaseResult(
                    success=True,
                    data={
                        "track_id": request.track_id,
                        "clip_id": request.clip_id,
                        "name": name,
                        "length": length,
                        "loop_start": loop_start,
                        "loop_end": loop_end,
                        "is_playing": is_playing,
                    },
                )

            elif request.action == "set_name":
                if request.name is None:
                    raise InvalidParameterError("name is required for set_name")
                await self._clip_service.set_clip_name(
                    request.track_id, request.clip_id, request.name
                )
                return UseCaseResult(
                    success=True,
                    message=f"Set clip name to '{request.name}'",
                )

            elif request.action == "set_length":
                if request.length is None:
                    raise InvalidParameterError("length is required for set_length")
                await self._clip_service.set_clip_length(
                    request.track_id, request.clip_id, request.length
                )
                return UseCaseResult(
                    success=True,
                    message=f"Set clip length to {request.length}",
                )

            elif request.action == "set_loop_start":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_loop_start")
                await self._clip_service.set_clip_loop_start(
                    request.track_id, request.clip_id, request.value
                )
                return UseCaseResult(
                    success=True,
                    message=f"Set clip loop start to {request.value}",
                )

            elif request.action == "set_loop_end":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_loop_end")
                await self._clip_service.set_clip_loop_end(
                    request.track_id, request.clip_id, request.value
                )
                return UseCaseResult(
                    success=True,
                    message=f"Set clip loop end to {request.value}",
                )

            elif request.action == "fire":
                await self._clip_service.fire_clip(request.track_id, request.clip_id)
                return UseCaseResult(success=True, message="Clip fired")

            elif request.action == "stop":
                await self._clip_service.stop_clip(request.track_id, request.clip_id)
                return UseCaseResult(success=True, message="Clip stopped")

            elif request.action == "create":
                clip_length = request.length or 4.0
                await self._clip_service.create_clip(request.track_id, request.clip_id, clip_length)
                return UseCaseResult(
                    success=True,
                    message=f"Created clip with length {clip_length}",
                )

            elif request.action == "delete":
                await self._clip_service.delete_clip(request.track_id, request.clip_id)
                return UseCaseResult(success=True, message="Clip deleted")

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown clip action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except (TrackNotFoundError, ClipNotFoundError, InvalidParameterError) as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            self._logger.error("Clip operation error", error=str(e))
            return UseCaseResult(
                success=False,
                message=f"Clip operation error: {e!s}",
                error_code="CLIP_ERROR",
            )


@dataclass
class ReturnTrackOperationRequest:
    """Request for return track operations."""

    action: str  # get_info, set_volume, set_pan, mute, set_name, create,
    #   get_master_info, set_master_volume, set_master_pan
    return_id: int | None = None
    value: float | None = None
    name: str | None = None


class ReturnTrackOperationsUseCase(UseCase):
    """Use case for return track and master track operations."""

    def __init__(
        self,
        return_track_service: Any,
        song_repository: SongRepository,
    ) -> None:
        self._service = return_track_service
        self._song_repository = song_repository
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: ReturnTrackOperationRequest) -> UseCaseResult:
        """Execute return/master track operation."""
        try:
            if request.action == "create":
                await self._service.create_return_track()
                return UseCaseResult(success=True, message="Created return track")

            elif request.action == "get_info":
                if request.return_id is None:
                    raise InvalidParameterError("return_id is required for get_info")
                info = await self._service.get_return_track_info(request.return_id)
                return UseCaseResult(success=True, data=info)

            elif request.action == "set_volume":
                if request.return_id is None or request.value is None:
                    raise InvalidParameterError("return_id and value are required")
                await self._service.set_return_track_volume(request.return_id, request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set return track volume to {request.value:.2f}",
                )

            elif request.action == "set_pan":
                if request.return_id is None or request.value is None:
                    raise InvalidParameterError("return_id and value are required")
                await self._service.set_return_track_pan(request.return_id, request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set return track pan to {request.value:.2f}",
                )

            elif request.action == "mute":
                if request.return_id is None:
                    raise InvalidParameterError("return_id is required for mute")
                # Toggle - get current then flip
                info = await self._service.get_return_track_info(request.return_id)
                new_state = not info["muted"]
                await self._service.set_return_track_mute(request.return_id, new_state)
                state = "muted" if new_state else "unmuted"
                return UseCaseResult(success=True, message=f"Return track {state}")

            elif request.action == "set_name":
                if request.return_id is None or request.name is None:
                    raise InvalidParameterError("return_id and name are required")
                await self._service.set_return_track_name(request.return_id, request.name)
                return UseCaseResult(
                    success=True,
                    message=f"Set return track name to '{request.name}'",
                )

            elif request.action == "get_master_info":
                info = await self._service.get_master_info()
                return UseCaseResult(success=True, data=info)

            elif request.action == "set_master_volume":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_master_volume")
                await self._service.set_master_volume(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set master volume to {request.value:.2f}",
                )

            elif request.action == "set_master_pan":
                if request.value is None:
                    raise InvalidParameterError("value is required for set_master_pan")
                await self._service.set_master_pan(request.value)
                return UseCaseResult(
                    success=True,
                    message=f"Set master pan to {request.value:.2f}",
                )

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown return track action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except InvalidParameterError as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            self._logger.error("Return track operation error", error=str(e))
            return UseCaseResult(
                success=False,
                message=f"Return track operation error: {e!s}",
                error_code="RETURN_TRACK_ERROR",
            )


@dataclass
class DeviceOperationRequest:
    """Request for device operations."""

    action: str  # get_info, set_active, get_parameter, set_parameter, list_parameters
    track_id: int
    device_id: int
    parameter_id: int | None = None
    value: float | None = None
    active: bool | None = None


class DeviceOperationsUseCase(UseCase):
    """Use case for device operations."""

    def __init__(
        self,
        device_service: Any,
        song_repository: SongRepository,
    ) -> None:
        self._device_service = device_service
        self._song_repository = song_repository
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: DeviceOperationRequest) -> UseCaseResult:
        """Execute device operation."""
        try:
            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            track = song.get_track_by_index(request.track_id)
            if not track:
                raise TrackNotFoundError(f"Track {request.track_id} not found")

            if request.action == "get_info":
                info = await self._device_service.get_device_info(
                    request.track_id, request.device_id
                )
                return UseCaseResult(success=True, data=info)

            elif request.action == "set_active":
                if request.active is None:
                    raise InvalidParameterError("active is required for set_active")
                await self._device_service.set_device_active(
                    request.track_id, request.device_id, request.active
                )
                state = "activated" if request.active else "deactivated"
                return UseCaseResult(success=True, message=f"Device {state}")

            elif request.action == "get_parameter":
                if request.parameter_id is None:
                    raise InvalidParameterError("parameter_id is required for get_parameter")
                info = await self._device_service.get_parameter_info(
                    request.track_id,
                    request.device_id,
                    request.parameter_id,
                )
                return UseCaseResult(success=True, data=info)

            elif request.action == "set_parameter":
                if request.parameter_id is None or request.value is None:
                    raise InvalidParameterError("parameter_id and value are required")
                await self._device_service.set_parameter_value(
                    request.track_id,
                    request.device_id,
                    request.parameter_id,
                    request.value,
                )
                return UseCaseResult(
                    success=True,
                    message=f"Set parameter {request.parameter_id} to {request.value}",
                )

            elif request.action == "list_parameters":
                params = await self._device_service.get_all_parameters(
                    request.track_id, request.device_id
                )
                return UseCaseResult(
                    success=True,
                    data={
                        "track_id": request.track_id,
                        "device_id": request.device_id,
                        "parameters": params,
                    },
                )

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown device action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except (TrackNotFoundError, InvalidParameterError) as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
        except Exception as e:
            self._logger.error("Device operation error", error=str(e))
            return UseCaseResult(
                success=False,
                message=f"Device operation error: {e!s}",
                error_code="DEVICE_ERROR",
            )


class ArrangementSuggestionsUseCase(UseCase):
    """Use case for arrangement analysis and suggestions."""

    def __init__(
        self,
        arrangement_service: ArrangementService,
        song_repository: SongRepository,
    ) -> None:
        self._arrangement_service = arrangement_service
        self._song_repository = song_repository

    async def execute(self, request: ArrangementSuggestionsRequest) -> UseCaseResult:
        """Analyze arrangement and provide structure suggestions."""
        try:
            song = await self._song_repository.get_current_song()
            if not song:
                return UseCaseResult(success=False, message="No active song")

            genre = request.genre or "pop"
            result_data: dict[str, Any] = {
                "genre": genre,
                "tempo": song.tempo,
                "track_count": len(song.tracks),
            }

            # Analyze current song structure
            structure_analysis = await self._arrangement_service.analyze_song_structure(song)
            result_data["current_structure"] = structure_analysis.data

            # Get arrangement improvement suggestions
            improvements = await self._arrangement_service.suggest_arrangement_improvements(
                song, genre
            )
            result_data["improvement_suggestions"] = improvements

            # Get recommended section lengths
            song_length = request.song_length or 128.0  # Default 128 bars
            section_lengths = await self._arrangement_service.suggest_section_lengths(
                genre, song_length
            )
            result_data["recommended_section_lengths"] = section_lengths

            # Calculate energy curve
            energy_curve = await self._arrangement_service.calculate_energy_curve(song)
            result_data["energy_curve"] = [
                {"time": time, "energy": energy} for time, energy in energy_curve
            ]

            return UseCaseResult(success=True, data=result_data)

        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Arrangement analysis error: {e!s}",
                error_code="ARRANGEMENT_ANALYSIS_ERROR",
            )
