"""Domain entities representing core business objects."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class TransportState(str, Enum):
    """Transport playback states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    RECORDING = "recording"
    PAUSED = "paused"


class TrackType(str, Enum):
    """Types of tracks in Ableton Live."""
    MIDI = "midi"
    AUDIO = "audio"
    RETURN = "return"
    MASTER = "master"
    GROUP = "group"


class DeviceType(str, Enum):
    """Types of devices/plugins."""
    INSTRUMENT = "instrument"
    AUDIO_EFFECT = "audio_effect"
    MIDI_EFFECT = "midi_effect"


class ClipType(str, Enum):
    """Types of clips."""
    MIDI = "midi"
    AUDIO = "audio"


@dataclass(frozen=True)
class EntityId:
    """Value object for entity identification."""
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


class Note(BaseModel):
    """MIDI note representation with music theory awareness."""
    pitch: int = Field(ge=0, le=127, description="MIDI note number")
    start: float = Field(ge=0, description="Start time in beats")
    duration: float = Field(gt=0, description="Duration in beats")
    velocity: int = Field(ge=1, le=127, default=100, description="Note velocity")
    mute: bool = Field(default=False, description="Whether note is muted")

    @validator("pitch")
    def validate_pitch(cls, v: int) -> int:
        if not 0 <= v <= 127:
            raise ValueError("MIDI pitch must be between 0 and 127")
        return v

    @property
    def note_name(self) -> str:
        """Get the note name (C, C#, D, etc.)."""
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return note_names[self.pitch % 12]

    @property
    def octave(self) -> int:
        """Get the octave number."""
        return (self.pitch // 12) - 1

    @property
    def pitch_class(self) -> int:
        """Get the pitch class (0-11)."""
        return self.pitch % 12


class Parameter(BaseModel):
    """Device parameter representation."""
    id: int = Field(description="Parameter ID")
    name: str = Field(description="Parameter name")
    value: float = Field(description="Current parameter value")
    min_value: float = Field(default=0.0, description="Minimum value")
    max_value: float = Field(default=1.0, description="Maximum value")
    default_value: float = Field(default=0.5, description="Default value")
    is_enabled: bool = Field(default=True, description="Whether parameter is enabled")
    unit: Optional[str] = Field(default=None, description="Parameter unit")

    @validator("value")
    def validate_value_range(cls, v: float, values: Dict[str, Any]) -> float:
        min_val = values.get("min_value", 0.0)
        max_val = values.get("max_value", 1.0)
        return max(min_val, min(max_val, v))


class Device(BaseModel):
    """Audio/MIDI device or plugin."""
    id: EntityId = Field(default_factory=EntityId)
    name: str = Field(description="Device name")
    device_type: DeviceType = Field(description="Type of device")
    is_enabled: bool = Field(default=True, description="Whether device is enabled")
    parameters: List[Parameter] = Field(default_factory=list)
    preset_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_parameter(self, name: str) -> Optional[Parameter]:
        """Get parameter by name."""
        return next((p for p in self.parameters if p.name == name), None)

    def set_parameter_value(self, name: str, value: float) -> None:
        """Set parameter value by name."""
        param = self.get_parameter(name)
        if param:
            param.value = max(param.min_value, min(param.max_value, value))


class Clip(BaseModel):
    """Audio or MIDI clip."""
    id: EntityId = Field(default_factory=EntityId)
    name: Optional[str] = Field(default=None)
    clip_type: ClipType = Field(description="Type of clip")
    length: float = Field(gt=0, description="Clip length in beats")
    loop_start: float = Field(default=0.0, ge=0)
    loop_end: Optional[float] = Field(default=None, ge=0)
    is_looping: bool = Field(default=True)
    is_playing: bool = Field(default=False)
    notes: List[Note] = Field(default_factory=list)  # For MIDI clips
    file_path: Optional[str] = Field(default=None)  # For audio clips
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("loop_end")
    def validate_loop_end(cls, v: Optional[float], values: Dict[str, Any]) -> Optional[float]:
        if v is not None and "length" in values:
            return min(v, values["length"])
        return v

    def add_note(self, note: Note) -> None:
        """Add a MIDI note to the clip."""
        if self.clip_type == ClipType.MIDI:
            self.notes.append(note)

    def remove_notes_in_range(self, start: float, end: float) -> None:
        """Remove notes within a time range."""
        self.notes = [n for n in self.notes if not (start <= n.start < end)]


class Track(BaseModel):
    """Audio or MIDI track."""
    id: EntityId = Field(default_factory=EntityId)
    name: str = Field(description="Track name")
    track_type: TrackType = Field(description="Type of track")
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    is_muted: bool = Field(default=False)
    is_soloed: bool = Field(default=False)
    is_armed: bool = Field(default=False)
    color: Optional[int] = Field(default=None, description="Track color index")
    devices: List[Device] = Field(default_factory=list)
    clips: List[Optional[Clip]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def add_device(self, device: Device) -> None:
        """Add a device to the track."""
        self.devices.append(device)

    def get_device_by_name(self, name: str) -> Optional[Device]:
        """Get device by name."""
        return next((d for d in self.devices if d.name == name), None)

    def set_clip(self, slot_index: int, clip: Optional[Clip]) -> None:
        """Set clip at specific slot."""
        # Extend clips list if necessary
        while len(self.clips) <= slot_index:
            self.clips.append(None)
        self.clips[slot_index] = clip

    def get_clip(self, slot_index: int) -> Optional[Clip]:
        """Get clip at specific slot."""
        if 0 <= slot_index < len(self.clips):
            return self.clips[slot_index]
        return None


class Song(BaseModel):
    """Ableton Live song/project."""
    id: EntityId = Field(default_factory=EntityId)
    name: str = Field(default="Untitled")
    tempo: float = Field(default=120.0, gt=0, le=999)
    time_signature_numerator: int = Field(default=4, ge=1, le=32)
    time_signature_denominator: int = Field(default=4, ge=1, le=32)
    key: Optional[str] = Field(default=None, description="Song key signature")
    current_song_time: float = Field(default=0.0, ge=0)
    loop_start: float = Field(default=0.0, ge=0)
    loop_end: float = Field(default=4.0, gt=0)
    is_loop_on: bool = Field(default=False)
    transport_state: TransportState = Field(default=TransportState.STOPPED)
    tracks: List[Track] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)

    @validator("tempo")
    def validate_tempo(cls, v: float) -> float:
        if not 20.0 <= v <= 999.0:
            raise ValueError("Tempo must be between 20 and 999 BPM")
        return v

    def add_track(self, track: Track) -> None:
        """Add a track to the song."""
        self.tracks.append(track)
        self.last_modified = datetime.utcnow()

    def get_track_by_id(self, track_id: EntityId) -> Optional[Track]:
        """Get track by ID."""
        return next((t for t in self.tracks if t.id == track_id), None)

    def get_track_by_index(self, index: int) -> Optional[Track]:
        """Get track by index."""
        if 0 <= index < len(self.tracks):
            return self.tracks[index]
        return None

    def get_track_by_name(self, name: str) -> Optional[Track]:
        """Get track by name."""
        return next((t for t in self.tracks if t.name == name), None)

    @property
    def midi_tracks(self) -> List[Track]:
        """Get all MIDI tracks."""
        return [t for t in self.tracks if t.track_type == TrackType.MIDI]

    @property
    def audio_tracks(self) -> List[Track]:
        """Get all audio tracks."""
        return [t for t in self.tracks if t.track_type == TrackType.AUDIO]


class MusicKey(BaseModel):
    """Musical key representation with theory awareness."""
    root: int = Field(ge=0, le=11, description="Root note (0=C, 1=C#, etc.)")
    mode: str = Field(description="Mode (major, minor, dorian, etc.)")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)

    @property
    def root_name(self) -> str:
        """Get the root note name."""
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return note_names[self.root]

    @property
    def scale_notes(self) -> List[int]:
        """Get the scale notes for this key."""
        # This would be expanded with full scale definitions
        scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            # ... more scales
        }
        if self.mode in scales:
            return [(self.root + interval) % 12 for interval in scales[self.mode]]
        return []


class AnalysisResult(BaseModel):
    """Result of music analysis."""
    id: EntityId = Field(default_factory=EntityId)
    analysis_type: str = Field(description="Type of analysis performed")
    confidence: float = Field(ge=0.0, le=1.0)
    data: Dict[str, Any] = Field(description="Analysis data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True