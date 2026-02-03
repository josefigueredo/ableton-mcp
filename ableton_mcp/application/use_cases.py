"""Application use cases implementing business workflows."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ableton_mcp.core.exceptions import (
    ClipNotFoundError,
    DeviceNotFoundError,
    InvalidParameterError,
    TrackNotFoundError,
    ValidationError,
)
from ableton_mcp.domain.entities import (
    AnalysisResult,
    Clip,
    ClipType,
    Device,
    EntityId,
    Note,
    Song,
    Track,
    TrackType,
    TransportState,
)
from ableton_mcp.domain.repositories import (
    ClipRepository,
    DeviceRepository,
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
    data: Optional[Any] = None
    message: Optional[str] = None
    error_code: Optional[str] = None


class UseCase(ABC):
    """Base class for all use cases."""
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> UseCaseResult:
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

    def __init__(self, connection_service: Any) -> None:  # Type hint would be interface
        self._connection_service = connection_service

    async def execute(self, request: ConnectToAbletonRequest) -> UseCaseResult:
        """Execute connection to Ableton Live."""
        try:
            await self._connection_service.connect(
                request.host, request.send_port, request.receive_port
            )
            return UseCaseResult(
                success=True,
                message=f"Connected to Ableton Live at {request.host}:{request.send_port}",
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Failed to connect: {str(e)}",
                error_code="CONNECTION_FAILED",
            )


@dataclass
class TransportControlRequest:
    """Request for transport control operations."""
    action: str  # play, stop, record, get_status
    value: Optional[float] = None


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
                message=f"Transport control error: {str(e)}",
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
                message=f"Error getting song info: {str(e)}",
                error_code="SONG_INFO_ERROR",
            )


@dataclass
class TrackOperationRequest:
    """Request for track operations."""
    action: str  # get_info, set_volume, set_pan, mute, solo, arm, create, delete
    track_id: Optional[int] = None
    value: Optional[float] = None
    name: Optional[str] = None
    track_type: Optional[str] = None


class TrackOperationsUseCase(UseCase):
    """Use case for track operations."""

    def __init__(
        self,
        track_repository: TrackRepository,
        song_repository: SongRepository,
        track_service: Any,
    ) -> None:
        self._track_repository = track_repository
        self._song_repository = song_repository
        self._track_service = track_service

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
                return UseCaseResult(
                    success=True, message=f"Set track pan to {track.pan:.2f}"
                )

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

            else:
                return UseCaseResult(
                    success=False,
                    message=f"Unknown track action: {request.action}",
                    error_code="INVALID_ACTION",
                )

        except (TrackNotFoundError, InvalidParameterError) as e:
            return UseCaseResult(
                success=False, message=str(e), error_code=e.error_code
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Track operation error: {str(e)}",
                error_code="TRACK_ERROR",
            )


@dataclass
class AddNotesRequest:
    """Request for adding MIDI notes to a clip."""
    track_id: int
    clip_id: int
    notes: List[Dict[str, Any]]
    quantize: bool = False
    scale_filter: Optional[str] = None


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

            clip = track.get_clip(request.clip_id)
            if not clip:
                raise ClipNotFoundError(f"Clip {request.clip_id} not found")

            if clip.clip_type != ClipType.MIDI:
                raise InvalidParameterError("Can only add notes to MIDI clips")

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
                    raise InvalidParameterError(f"Invalid note data: {str(e)}")

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

            # Add notes to clip
            for note in notes:
                clip.add_note(note)
                await self._clip_service.add_note(
                    request.track_id, request.clip_id, note
                )

            await self._clip_repository.update_clip(clip)

            return UseCaseResult(
                success=True,
                message=f"Added {len(notes)} notes to clip",
                data={"notes_added": len(notes), "clip_length": clip.length},
            )

        except (TrackNotFoundError, ClipNotFoundError, InvalidParameterError, ValidationError) as e:
            return UseCaseResult(
                success=False, message=str(e), error_code=e.error_code
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                message=f"Error adding notes: {str(e)}",
                error_code="ADD_NOTES_ERROR",
            )


@dataclass
class AnalyzeHarmonyRequest:
    """Request for harmony analysis."""
    notes: List[int]
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
            notes = [
                Note(pitch=pitch, start=0.0, duration=1.0) for pitch in request.notes
            ]

            # Analyze key
            keys = await self._music_theory_service.analyze_key(notes)
            
            result_data = {
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
                message=f"Harmony analysis error: {str(e)}",
                error_code="HARMONY_ANALYSIS_ERROR",
            )


@dataclass
class AnalyzeTempoRequest:
    """Request for tempo analysis."""
    current_bpm: Optional[float] = None
    genre: Optional[str] = None
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
                if song:
                    current_bpm = song.tempo
                else:
                    current_bpm = 120.0

            result_data = {
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
                message=f"Tempo analysis error: {str(e)}",
                error_code="TEMPO_ANALYSIS_ERROR",
            )