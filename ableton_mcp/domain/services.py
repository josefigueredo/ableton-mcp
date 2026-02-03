"""Domain services containing business logic that doesn't belong to entities."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ableton_mcp.domain.entities import (
    AnalysisResult,
    Clip,
    MusicKey,
    Note,
    Song,
    Track,
)


class MusicTheoryService(ABC):
    """Service for music theory analysis and suggestions."""

    @abstractmethod
    async def analyze_key(self, notes: List[Note]) -> List[MusicKey]:
        """Analyze the musical key of given notes."""
        pass

    @abstractmethod
    async def suggest_chord_progressions(
        self, key: MusicKey, genre: str
    ) -> List[List[int]]:
        """Suggest chord progressions for a given key and genre."""
        pass

    @abstractmethod
    async def harmonize_melody(
        self, melody_notes: List[Note], key: MusicKey
    ) -> List[Note]:
        """Generate harmony notes for a melody."""
        pass

    @abstractmethod
    async def quantize_notes(
        self, notes: List[Note], grid_division: float = 0.25
    ) -> List[Note]:
        """Quantize notes to a rhythmic grid."""
        pass

    @abstractmethod
    async def filter_notes_to_scale(
        self, notes: List[Note], key: MusicKey
    ) -> List[Note]:
        """Filter notes to fit within a musical scale."""
        pass


class ArrangementService(ABC):
    """Service for song arrangement analysis and suggestions."""

    @abstractmethod
    async def analyze_song_structure(self, song: Song) -> AnalysisResult:
        """Analyze the structure of a song."""
        pass

    @abstractmethod
    async def suggest_arrangement_improvements(
        self, song: Song, genre: str
    ) -> List[str]:
        """Suggest improvements to song arrangement."""
        pass

    @abstractmethod
    async def calculate_energy_curve(self, song: Song) -> List[Tuple[float, float]]:
        """Calculate energy levels throughout the song."""
        pass

    @abstractmethod
    async def suggest_section_lengths(
        self, genre: str, song_length: float
    ) -> Dict[str, float]:
        """Suggest optimal section lengths for a genre."""
        pass


class MixingService(ABC):
    """Service for mixing analysis and suggestions."""

    @abstractmethod
    async def analyze_frequency_balance(self, tracks: List[Track]) -> AnalysisResult:
        """Analyze frequency balance across tracks."""
        pass

    @abstractmethod
    async def suggest_eq_adjustments(self, track: Track) -> List[Dict[str, Any]]:
        """Suggest EQ adjustments for a track."""
        pass

    @abstractmethod
    async def analyze_stereo_image(self, tracks: List[Track]) -> AnalysisResult:
        """Analyze stereo imaging and panning."""
        pass

    @abstractmethod
    async def calculate_lufs_target(
        self, genre: str, platform: str
    ) -> Tuple[float, float]:
        """Calculate target LUFS and peak levels for genre/platform."""
        pass


class TempoAnalysisService(ABC):
    """Service for tempo analysis and suggestions."""

    @abstractmethod
    async def detect_tempo(self, clip: Clip) -> float:
        """Detect tempo from an audio clip."""
        pass

    @abstractmethod
    async def suggest_tempo_for_genre(self, genre: str, energy_level: str) -> float:
        """Suggest appropriate tempo for genre and energy level."""
        pass

    @abstractmethod
    async def analyze_rhythmic_patterns(self, clip: Clip) -> AnalysisResult:
        """Analyze rhythmic patterns in a clip."""
        pass

    @abstractmethod
    async def suggest_tempo_changes(
        self, song: Song, target_energy: List[float]
    ) -> List[Tuple[float, float]]:
        """Suggest tempo changes to match target energy curve."""
        pass


class ValidationService:
    """Service for validating domain objects and business rules."""

    @staticmethod
    def validate_note_range(note: Note) -> bool:
        """Validate that a note is within acceptable range."""
        return 0 <= note.pitch <= 127

    @staticmethod
    def validate_tempo(tempo: float) -> bool:
        """Validate tempo is within acceptable range."""
        return 20.0 <= tempo <= 999.0

    @staticmethod
    def validate_clip_timing(clip: Clip) -> bool:
        """Validate clip timing is consistent."""
        if clip.loop_end is not None:
            return clip.loop_start < clip.loop_end <= clip.length
        return clip.loop_start < clip.length

    @staticmethod
    def validate_track_configuration(track: Track) -> List[str]:
        """Validate track configuration and return any issues."""
        issues = []
        
        if not track.name.strip():
            issues.append("Track name cannot be empty")
        
        if not 0.0 <= track.volume <= 1.0:
            issues.append("Track volume must be between 0.0 and 1.0")
        
        if not -1.0 <= track.pan <= 1.0:
            issues.append("Track pan must be between -1.0 and 1.0")
        
        # Validate clips
        for i, clip in enumerate(track.clips):
            if clip and not ValidationService.validate_clip_timing(clip):
                issues.append(f"Invalid timing in clip at slot {i}")
        
        return issues

    @staticmethod
    def validate_song_structure(song: Song) -> List[str]:
        """Validate overall song structure."""
        issues = []
        
        if not ValidationService.validate_tempo(song.tempo):
            issues.append("Invalid tempo range")
        
        if song.loop_start >= song.loop_end:
            issues.append("Loop start must be before loop end")
        
        if not song.tracks:
            issues.append("Song must have at least one track")
        
        # Validate all tracks
        for i, track in enumerate(song.tracks):
            track_issues = ValidationService.validate_track_configuration(track)
            for issue in track_issues:
                issues.append(f"Track {i}: {issue}")
        
        return issues