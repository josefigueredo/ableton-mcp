"""Concrete repository implementations.

These in-memory repositories use asyncio.Lock for thread-safety
in concurrent async contexts.
"""

import asyncio

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
    """In-memory implementation of song repository for development/testing.

    Thread-safe via asyncio.Lock for concurrent access.
    """

    def __init__(self) -> None:
        self._current_song: Song | None = None
        self._lock = asyncio.Lock()

    async def get_current_song(self) -> Song | None:
        """Get the currently loaded song."""
        async with self._lock:
            return self._current_song

    async def save_song(self, song: Song) -> None:
        """Save song data."""
        async with self._lock:
            self._current_song = song

    async def update_song(self, song: Song) -> None:
        """Update existing song."""
        async with self._lock:
            if self._current_song and self._current_song.id == song.id:
                self._current_song = song


class InMemoryTrackRepository(TrackRepository):
    """In-memory implementation of track repository.

    Thread-safe via asyncio.Lock for concurrent access.
    """

    def __init__(self) -> None:
        self._tracks: dict[str, Track] = {}
        self._lock = asyncio.Lock()

    async def get_track(self, track_id: EntityId) -> Track | None:
        """Get track by ID."""
        async with self._lock:
            return self._tracks.get(track_id.value)

    async def get_tracks_by_song(self, song_id: EntityId) -> list[Track]:
        """Get all tracks for a song."""
        async with self._lock:
            # In a real implementation, this would filter by song_id
            return list(self._tracks.values())

    async def create_track(self, track: Track) -> None:
        """Create a new track."""
        async with self._lock:
            self._tracks[track.id.value] = track

    async def update_track(self, track: Track) -> None:
        """Update existing track."""
        async with self._lock:
            self._tracks[track.id.value] = track

    async def delete_track(self, track_id: EntityId) -> None:
        """Delete a track."""
        async with self._lock:
            if track_id.value in self._tracks:
                del self._tracks[track_id.value]


class InMemoryDeviceRepository(DeviceRepository):
    """In-memory implementation of device repository.

    Thread-safe via asyncio.Lock for concurrent access.
    """

    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}
        self._lock = asyncio.Lock()

    async def get_device(self, device_id: EntityId) -> Device | None:
        """Get device by ID."""
        async with self._lock:
            return self._devices.get(device_id.value)

    async def get_devices_by_track(self, track_id: EntityId) -> list[Device]:
        """Get all devices for a track."""
        async with self._lock:
            # In a real implementation, this would filter by track_id
            return list(self._devices.values())

    async def create_device(self, device: Device) -> None:
        """Create a new device."""
        async with self._lock:
            self._devices[device.id.value] = device

    async def update_device(self, device: Device) -> None:
        """Update existing device."""
        async with self._lock:
            self._devices[device.id.value] = device

    async def delete_device(self, device_id: EntityId) -> None:
        """Delete a device."""
        async with self._lock:
            if device_id.value in self._devices:
                del self._devices[device_id.value]


class InMemoryClipRepository(ClipRepository):
    """In-memory implementation of clip repository.

    Thread-safe via asyncio.Lock for concurrent access.
    """

    def __init__(self) -> None:
        self._clips: dict[str, Clip] = {}
        self._lock = asyncio.Lock()

    async def get_clip(self, clip_id: EntityId) -> Clip | None:
        """Get clip by ID."""
        async with self._lock:
            return self._clips.get(clip_id.value)

    async def get_clips_by_track(self, track_id: EntityId) -> list[Clip | None]:
        """Get all clips for a track."""
        async with self._lock:
            # In a real implementation, this would filter by track_id
            return list(self._clips.values())

    async def create_clip(self, clip: Clip) -> None:
        """Create a new clip."""
        async with self._lock:
            self._clips[clip.id.value] = clip

    async def update_clip(self, clip: Clip) -> None:
        """Update existing clip."""
        async with self._lock:
            self._clips[clip.id.value] = clip

    async def delete_clip(self, clip_id: EntityId) -> None:
        """Delete a clip."""
        async with self._lock:
            if clip_id.value in self._clips:
                del self._clips[clip_id.value]


class InMemoryAnalysisRepository(AnalysisRepository):
    """In-memory implementation of analysis repository.

    Thread-safe via asyncio.Lock for concurrent access.
    """

    def __init__(self) -> None:
        self._analyses: dict[str, AnalysisResult] = {}
        self._lock = asyncio.Lock()

    async def save_analysis(self, result: AnalysisResult) -> None:
        """Save analysis result."""
        async with self._lock:
            self._analyses[result.id.value] = result

    async def get_analysis(self, result_id: EntityId) -> AnalysisResult | None:
        """Get analysis result by ID."""
        async with self._lock:
            return self._analyses.get(result_id.value)

    async def get_analyses_by_type(self, analysis_type: str) -> list[AnalysisResult]:
        """Get all analysis results of a specific type."""
        async with self._lock:
            return [
                result
                for result in self._analyses.values()
                if result.analysis_type == analysis_type
            ]

    async def delete_analysis(self, result_id: EntityId) -> None:
        """Delete analysis result."""
        async with self._lock:
            if result_id.value in self._analyses:
                del self._analyses[result_id.value]
