"""Concrete repository implementations."""

from typing import List, Optional

from ableton_mcp.domain.entities import (
    AnalysisResult,
    Clip,
    Device,
    EntityId,
    Song,
    Track,
)
from ableton_mcp.domain.repositories import (
    AnalysisRepository,
    ClipRepository,
    DeviceRepository,
    SongRepository,
    TrackRepository,
)


class InMemorySongRepository(SongRepository):
    """In-memory implementation of song repository for development/testing."""

    def __init__(self) -> None:
        self._current_song: Optional[Song] = None

    async def get_current_song(self) -> Optional[Song]:
        """Get the currently loaded song."""
        return self._current_song

    async def save_song(self, song: Song) -> None:
        """Save song data."""
        self._current_song = song

    async def update_song(self, song: Song) -> None:
        """Update existing song."""
        if self._current_song and self._current_song.id == song.id:
            self._current_song = song


class InMemoryTrackRepository(TrackRepository):
    """In-memory implementation of track repository."""

    def __init__(self) -> None:
        self._tracks: dict[str, Track] = {}

    async def get_track(self, track_id: EntityId) -> Optional[Track]:
        """Get track by ID."""
        return self._tracks.get(track_id.value)

    async def get_tracks_by_song(self, song_id: EntityId) -> List[Track]:
        """Get all tracks for a song."""
        # In a real implementation, this would filter by song_id
        return list(self._tracks.values())

    async def create_track(self, track: Track) -> None:
        """Create a new track."""
        self._tracks[track.id.value] = track

    async def update_track(self, track: Track) -> None:
        """Update existing track."""
        self._tracks[track.id.value] = track

    async def delete_track(self, track_id: EntityId) -> None:
        """Delete a track."""
        if track_id.value in self._tracks:
            del self._tracks[track_id.value]


class InMemoryDeviceRepository(DeviceRepository):
    """In-memory implementation of device repository."""

    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}

    async def get_device(self, device_id: EntityId) -> Optional[Device]:
        """Get device by ID."""
        return self._devices.get(device_id.value)

    async def get_devices_by_track(self, track_id: EntityId) -> List[Device]:
        """Get all devices for a track."""
        # In a real implementation, this would filter by track_id
        return list(self._devices.values())

    async def create_device(self, device: Device) -> None:
        """Create a new device."""
        self._devices[device.id.value] = device

    async def update_device(self, device: Device) -> None:
        """Update existing device."""
        self._devices[device.id.value] = device

    async def delete_device(self, device_id: EntityId) -> None:
        """Delete a device."""
        if device_id.value in self._devices:
            del self._devices[device_id.value]


class InMemoryClipRepository(ClipRepository):
    """In-memory implementation of clip repository."""

    def __init__(self) -> None:
        self._clips: dict[str, Clip] = {}

    async def get_clip(self, clip_id: EntityId) -> Optional[Clip]:
        """Get clip by ID."""
        return self._clips.get(clip_id.value)

    async def get_clips_by_track(self, track_id: EntityId) -> List[Optional[Clip]]:
        """Get all clips for a track."""
        # In a real implementation, this would filter by track_id
        return list(self._clips.values())

    async def create_clip(self, clip: Clip) -> None:
        """Create a new clip."""
        self._clips[clip.id.value] = clip

    async def update_clip(self, clip: Clip) -> None:
        """Update existing clip."""
        self._clips[clip.id.value] = clip

    async def delete_clip(self, clip_id: EntityId) -> None:
        """Delete a clip."""
        if clip_id.value in self._clips:
            del self._clips[clip_id.value]


class InMemoryAnalysisRepository(AnalysisRepository):
    """In-memory implementation of analysis repository."""

    def __init__(self) -> None:
        self._analyses: dict[str, AnalysisResult] = {}

    async def save_analysis(self, result: AnalysisResult) -> None:
        """Save analysis result."""
        self._analyses[result.id.value] = result

    async def get_analysis(self, result_id: EntityId) -> Optional[AnalysisResult]:
        """Get analysis result by ID."""
        return self._analyses.get(result_id.value)

    async def get_analyses_by_type(self, analysis_type: str) -> List[AnalysisResult]:
        """Get all analysis results of a specific type."""
        return [
            result
            for result in self._analyses.values()
            if result.analysis_type == analysis_type
        ]

    async def delete_analysis(self, result_id: EntityId) -> None:
        """Delete analysis result."""
        if result_id.value in self._analyses:
            del self._analyses[result_id.value]