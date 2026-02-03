"""Performance benchmarks for critical operations.

Run benchmarks with:
    pytest benchmarks/ -v --benchmark-only
    pytest benchmarks/ -v --benchmark-compare
    pytest benchmarks/ -v --benchmark-autosave

Requires pytest-benchmark:
    pip install pytest-benchmark
"""

import asyncio
from typing import Any

import pytest

from ableton_mcp.domain.entities import (
    Clip,
    ClipType,
    Note,
    Song,
    Track,
    TrackType,
    MusicKey,
)
from ableton_mcp.infrastructure.services import MusicTheoryServiceImpl
from ableton_mcp.infrastructure.repositories import (
    InMemorySongRepository,
    InMemoryTrackRepository,
    InMemoryClipRepository,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def music_service() -> MusicTheoryServiceImpl:
    """Provide music theory service."""
    return MusicTheoryServiceImpl()


@pytest.fixture
def song_repository() -> InMemorySongRepository:
    """Provide song repository."""
    return InMemorySongRepository()


@pytest.fixture
def track_repository() -> InMemoryTrackRepository:
    """Provide track repository."""
    return InMemoryTrackRepository()


@pytest.fixture
def clip_repository() -> InMemoryClipRepository:
    """Provide clip repository."""
    return InMemoryClipRepository()


@pytest.fixture
def sample_notes_small() -> list[Note]:
    """10 notes for small dataset benchmarks."""
    return [
        Note(pitch=60 + i % 12, start=float(i) * 0.5, duration=0.5, velocity=100)
        for i in range(10)
    ]


@pytest.fixture
def sample_notes_medium() -> list[Note]:
    """100 notes for medium dataset benchmarks."""
    return [
        Note(pitch=36 + i % 48, start=float(i) * 0.25, duration=0.25, velocity=80 + i % 40)
        for i in range(100)
    ]


@pytest.fixture
def sample_notes_large() -> list[Note]:
    """1000 notes for large dataset benchmarks."""
    return [
        Note(pitch=24 + i % 72, start=float(i) * 0.125, duration=0.125, velocity=60 + i % 60)
        for i in range(1000)
    ]


@pytest.fixture
def sample_song_with_tracks() -> Song:
    """Song with multiple tracks for benchmarks."""
    song = Song(name="Benchmark Song", tempo=120.0)

    for i in range(16):
        track = Track(
            name=f"Track {i + 1}",
            track_type=TrackType.MIDI if i % 2 == 0 else TrackType.AUDIO,
            volume=0.8,
            pan=0.0,
        )

        # Add clips to MIDI tracks
        if track.track_type == TrackType.MIDI:
            for j in range(8):
                clip = Clip(
                    name=f"Clip {j + 1}",
                    clip_type=ClipType.MIDI,
                    length=4.0,
                )
                # Add notes to clip
                for k in range(16):
                    clip.add_note(Note(
                        pitch=60 + k % 12,
                        start=float(k) * 0.25,
                        duration=0.25,
                        velocity=100,
                    ))
                track.set_clip(j, clip)

        song.add_track(track)

    return song


# =============================================================================
# Entity Creation Benchmarks
# =============================================================================

class TestEntityCreationBenchmarks:
    """Benchmarks for entity creation performance."""

    @pytest.mark.benchmark(group="entity-creation")
    def test_note_creation(self, benchmark: Any) -> None:
        """Benchmark single Note creation."""
        def create_note() -> Note:
            return Note(pitch=60, start=0.0, duration=1.0, velocity=100)

        result = benchmark(create_note)
        assert result.pitch == 60

    @pytest.mark.benchmark(group="entity-creation")
    def test_note_batch_creation(self, benchmark: Any) -> None:
        """Benchmark batch Note creation (100 notes)."""
        def create_notes() -> list[Note]:
            return [
                Note(pitch=60 + i % 12, start=float(i), duration=1.0, velocity=100)
                for i in range(100)
            ]

        result = benchmark(create_notes)
        assert len(result) == 100

    @pytest.mark.benchmark(group="entity-creation")
    def test_clip_with_notes_creation(self, benchmark: Any) -> None:
        """Benchmark Clip creation with 50 notes."""
        def create_clip() -> Clip:
            clip = Clip(name="Test", clip_type=ClipType.MIDI, length=16.0)
            for i in range(50):
                clip.add_note(Note(
                    pitch=60 + i % 12,
                    start=float(i) * 0.25,
                    duration=0.25,
                    velocity=100,
                ))
            return clip

        result = benchmark(create_clip)
        assert len(result.notes) == 50

    @pytest.mark.benchmark(group="entity-creation")
    def test_track_creation(self, benchmark: Any) -> None:
        """Benchmark Track creation."""
        def create_track() -> Track:
            return Track(
                name="Test Track",
                track_type=TrackType.MIDI,
                volume=0.8,
                pan=0.0,
            )

        result = benchmark(create_track)
        assert result.name == "Test Track"

    @pytest.mark.benchmark(group="entity-creation")
    def test_song_creation(self, benchmark: Any) -> None:
        """Benchmark Song creation with 8 tracks."""
        def create_song() -> Song:
            song = Song(name="Test Song", tempo=120.0)
            for i in range(8):
                track = Track(
                    name=f"Track {i}",
                    track_type=TrackType.MIDI,
                )
                song.add_track(track)
            return song

        result = benchmark(create_song)
        assert len(result.tracks) == 8


# =============================================================================
# Music Theory Benchmarks
# =============================================================================

class TestMusicTheoryBenchmarks:
    """Benchmarks for music theory operations."""

    @pytest.mark.benchmark(group="music-theory")
    def test_key_analysis_small(
        self,
        benchmark: Any,
        music_service: MusicTheoryServiceImpl,
        sample_notes_small: list[Note],
    ) -> None:
        """Benchmark key analysis with 10 notes."""
        async def analyze() -> list[MusicKey]:
            return await music_service.analyze_key(sample_notes_small)

        result = benchmark(lambda: asyncio.run(analyze()))
        assert isinstance(result, list)

    @pytest.mark.benchmark(group="music-theory")
    def test_key_analysis_medium(
        self,
        benchmark: Any,
        music_service: MusicTheoryServiceImpl,
        sample_notes_medium: list[Note],
    ) -> None:
        """Benchmark key analysis with 100 notes."""
        async def analyze() -> list[MusicKey]:
            return await music_service.analyze_key(sample_notes_medium)

        result = benchmark(lambda: asyncio.run(analyze()))
        assert isinstance(result, list)

    @pytest.mark.benchmark(group="music-theory")
    def test_key_analysis_large(
        self,
        benchmark: Any,
        music_service: MusicTheoryServiceImpl,
        sample_notes_large: list[Note],
    ) -> None:
        """Benchmark key analysis with 1000 notes."""
        async def analyze() -> list[MusicKey]:
            return await music_service.analyze_key(sample_notes_large)

        result = benchmark(lambda: asyncio.run(analyze()))
        assert isinstance(result, list)

    @pytest.mark.benchmark(group="music-theory")
    def test_chord_progression_suggestion(
        self,
        benchmark: Any,
        music_service: MusicTheoryServiceImpl,
    ) -> None:
        """Benchmark chord progression suggestion."""
        async def suggest() -> list[dict[str, Any]]:
            return await music_service.suggest_progressions("C", "major", "pop")

        result = benchmark(lambda: asyncio.run(suggest()))
        assert isinstance(result, list)


# =============================================================================
# Repository Benchmarks
# =============================================================================

class TestRepositoryBenchmarks:
    """Benchmarks for repository operations."""

    @pytest.mark.benchmark(group="repository")
    def test_song_save(
        self,
        benchmark: Any,
        song_repository: InMemorySongRepository,
        sample_song_with_tracks: Song,
    ) -> None:
        """Benchmark song save operation."""
        async def save() -> None:
            await song_repository.save(sample_song_with_tracks)

        benchmark(lambda: asyncio.run(save()))

    @pytest.mark.benchmark(group="repository")
    def test_song_get(
        self,
        benchmark: Any,
        song_repository: InMemorySongRepository,
        sample_song_with_tracks: Song,
    ) -> None:
        """Benchmark song retrieval."""
        # Pre-save the song
        asyncio.run(song_repository.save(sample_song_with_tracks))

        async def get() -> Song | None:
            return await song_repository.get_by_id(sample_song_with_tracks.id)

        result = benchmark(lambda: asyncio.run(get()))
        assert result is not None

    @pytest.mark.benchmark(group="repository")
    def test_track_batch_save(
        self,
        benchmark: Any,
        track_repository: InMemoryTrackRepository,
    ) -> None:
        """Benchmark saving 100 tracks."""
        tracks = [
            Track(name=f"Track {i}", track_type=TrackType.MIDI)
            for i in range(100)
        ]

        async def save_all() -> None:
            for track in tracks:
                await track_repository.save(track)

        benchmark(lambda: asyncio.run(save_all()))


# =============================================================================
# Clip Operations Benchmarks
# =============================================================================

class TestClipOperationsBenchmarks:
    """Benchmarks for clip operations."""

    @pytest.mark.benchmark(group="clip-ops")
    def test_add_notes_small(self, benchmark: Any, sample_notes_small: list[Note]) -> None:
        """Benchmark adding 10 notes to clip."""
        def add_notes() -> Clip:
            clip = Clip(name="Test", clip_type=ClipType.MIDI, length=16.0)
            for note in sample_notes_small:
                clip.add_note(note)
            return clip

        result = benchmark(add_notes)
        assert len(result.notes) == 10

    @pytest.mark.benchmark(group="clip-ops")
    def test_add_notes_large(self, benchmark: Any, sample_notes_large: list[Note]) -> None:
        """Benchmark adding 1000 notes to clip."""
        def add_notes() -> Clip:
            clip = Clip(name="Test", clip_type=ClipType.MIDI, length=256.0)
            for note in sample_notes_large:
                clip.add_note(note)
            return clip

        result = benchmark(add_notes)
        assert len(result.notes) == 1000

    @pytest.mark.benchmark(group="clip-ops")
    def test_remove_notes_in_range(self, benchmark: Any) -> None:
        """Benchmark removing notes in a time range."""
        # Create clip with notes
        clip = Clip(name="Test", clip_type=ClipType.MIDI, length=64.0)
        for i in range(500):
            clip.add_note(Note(
                pitch=60 + i % 12,
                start=float(i) * 0.125,
                duration=0.125,
                velocity=100,
            ))

        def remove_notes() -> int:
            # Remove notes in the middle third
            clip.remove_notes_in_range(20.0, 40.0)
            return len(clip.notes)

        result = benchmark(remove_notes)
        # Some notes should have been removed
        assert result < 500


# =============================================================================
# Note Property Access Benchmarks
# =============================================================================

class TestNotePropertyBenchmarks:
    """Benchmarks for note property access."""

    @pytest.mark.benchmark(group="note-props")
    def test_pitch_class_access(self, benchmark: Any, sample_notes_large: list[Note]) -> None:
        """Benchmark pitch class property access."""
        def access_pitch_classes() -> list[int]:
            return [note.pitch_class for note in sample_notes_large]

        result = benchmark(access_pitch_classes)
        assert len(result) == 1000

    @pytest.mark.benchmark(group="note-props")
    def test_note_name_access(self, benchmark: Any, sample_notes_large: list[Note]) -> None:
        """Benchmark note name property access."""
        def access_note_names() -> list[str]:
            return [note.note_name for note in sample_notes_large]

        result = benchmark(access_note_names)
        assert len(result) == 1000

    @pytest.mark.benchmark(group="note-props")
    def test_octave_access(self, benchmark: Any, sample_notes_large: list[Note]) -> None:
        """Benchmark octave property access."""
        def access_octaves() -> list[int]:
            return [note.octave for note in sample_notes_large]

        result = benchmark(access_octaves)
        assert len(result) == 1000
