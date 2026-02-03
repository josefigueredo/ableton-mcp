"""Repository interfaces defining data access contracts."""

from abc import ABC, abstractmethod

from ableton_mcp.domain.entities import (
    AnalysisResult,
    Clip,
    Device,
    EntityId,
    Song,
    Track,
)


class SongRepository(ABC):
    """Repository for managing song data."""

    @abstractmethod
    async def get_current_song(self) -> Song | None:
        """Get the currently loaded song."""
        pass

    @abstractmethod
    async def save_song(self, song: Song) -> None:
        """Save song data."""
        pass

    @abstractmethod
    async def update_song(self, song: Song) -> None:
        """Update existing song."""
        pass


class TrackRepository(ABC):
    """Repository for managing track data."""

    @abstractmethod
    async def get_track(self, track_id: EntityId) -> Track | None:
        """Get track by ID."""
        pass

    @abstractmethod
    async def get_tracks_by_song(self, song_id: EntityId) -> list[Track]:
        """Get all tracks for a song."""
        pass

    @abstractmethod
    async def create_track(self, track: Track) -> None:
        """Create a new track."""
        pass

    @abstractmethod
    async def update_track(self, track: Track) -> None:
        """Update existing track."""
        pass

    @abstractmethod
    async def delete_track(self, track_id: EntityId) -> None:
        """Delete a track."""
        pass


class DeviceRepository(ABC):
    """Repository for managing device data."""

    @abstractmethod
    async def get_device(self, device_id: EntityId) -> Device | None:
        """Get device by ID."""
        pass

    @abstractmethod
    async def get_devices_by_track(self, track_id: EntityId) -> list[Device]:
        """Get all devices for a track."""
        pass

    @abstractmethod
    async def create_device(self, device: Device) -> None:
        """Create a new device."""
        pass

    @abstractmethod
    async def update_device(self, device: Device) -> None:
        """Update existing device."""
        pass

    @abstractmethod
    async def delete_device(self, device_id: EntityId) -> None:
        """Delete a device."""
        pass


class ClipRepository(ABC):
    """Repository for managing clip data."""

    @abstractmethod
    async def get_clip(self, clip_id: EntityId) -> Clip | None:
        """Get clip by ID."""
        pass

    @abstractmethod
    async def get_clips_by_track(self, track_id: EntityId) -> list[Clip | None]:
        """Get all clips for a track."""
        pass

    @abstractmethod
    async def create_clip(self, clip: Clip) -> None:
        """Create a new clip."""
        pass

    @abstractmethod
    async def update_clip(self, clip: Clip) -> None:
        """Update existing clip."""
        pass

    @abstractmethod
    async def delete_clip(self, clip_id: EntityId) -> None:
        """Delete a clip."""
        pass


class AnalysisRepository(ABC):
    """Repository for managing analysis results."""

    @abstractmethod
    async def save_analysis(self, result: AnalysisResult) -> None:
        """Save analysis result."""
        pass

    @abstractmethod
    async def get_analysis(self, result_id: EntityId) -> AnalysisResult | None:
        """Get analysis result by ID."""
        pass

    @abstractmethod
    async def get_analyses_by_type(self, analysis_type: str) -> list[AnalysisResult]:
        """Get all analysis results of a specific type."""
        pass

    @abstractmethod
    async def delete_analysis(self, result_id: EntityId) -> None:
        """Delete analysis result."""
        pass
