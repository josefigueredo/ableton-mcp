"""Application use cases implementing business workflows."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog

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
                message=f"Failed to connect: {str(e)}",
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
        tracks: List[Track] = []
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

    async def execute(
        self, request: Optional[RefreshSongDataRequest] = None
    ) -> UseCaseResult:
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
                message=f"Failed to refresh song data: {str(e)}",
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
        tracks: List[Track] = []
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

            # Add notes directly to Ableton via clip service
            # This sends OSC commands directly without requiring local clip cache
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
            notes = [Note(pitch=pitch, start=0.0, duration=1.0) for pitch in request.notes]

            # Analyze key
            keys = await self._music_theory_service.analyze_key(notes)

            result_data: Dict[str, Any] = {
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

            result_data: Dict[str, Any] = {
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

            result_data: Dict[str, Any] = {
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
                message=f"Mix analysis error: {str(e)}",
                error_code="MIX_ANALYSIS_ERROR",
            )


@dataclass
class ArrangementSuggestionsRequest:
    """Request for arrangement suggestions."""

    song_length: Optional[float] = None
    genre: Optional[str] = None
    current_structure: Optional[List[str]] = None


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
                message=f"Error getting clip content: {str(e)}",
                error_code="CLIP_CONTENT_ERROR",
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
            result_data: Dict[str, Any] = {
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
                message=f"Arrangement analysis error: {str(e)}",
                error_code="ARRANGEMENT_ANALYSIS_ERROR",
            )
