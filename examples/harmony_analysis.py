"""Harmony analysis example.

This example demonstrates how to:
1. Analyze the musical key of notes
2. Get chord progression suggestions
3. Use the music theory service

Prerequisites:
- ableton-mcp package installed (pip install -e .)
"""

import asyncio

from ableton_mcp.container import Container
from ableton_mcp.domain.entities import Note


async def main() -> None:
    """Demonstrate harmony analysis capabilities."""
    container = Container()

    # Get the music theory service
    music_theory = container.music_theory_service()

    print("=" * 50)
    print("HARMONY ANALYSIS EXAMPLES")
    print("=" * 50)

    # Example 1: Analyze key from a set of notes
    print("\n1. KEY DETECTION")
    print("-" * 40)

    # C major scale notes
    c_major_notes = [
        Note(pitch=60, start=0.0, duration=1.0),  # C
        Note(pitch=62, start=1.0, duration=1.0),  # D
        Note(pitch=64, start=2.0, duration=1.0),  # E
        Note(pitch=65, start=3.0, duration=1.0),  # F
        Note(pitch=67, start=4.0, duration=1.0),  # G
        Note(pitch=69, start=5.0, duration=1.0),  # A
        Note(pitch=71, start=6.0, duration=1.0),  # B
    ]

    print("Analyzing C major scale notes...")
    keys = await music_theory.analyze_key(c_major_notes)

    print("Detected keys (sorted by confidence):")
    for i, key in enumerate(keys[:3]):  # Top 3 results
        print(f"  {i + 1}. {key.root} {key.mode} (confidence: {key.confidence:.1%})")

    # Example 2: Analyze a minor key
    print("\n" + "-" * 40)

    # A minor notes
    a_minor_notes = [
        Note(pitch=57, start=0.0, duration=1.0),  # A
        Note(pitch=59, start=1.0, duration=1.0),  # B
        Note(pitch=60, start=2.0, duration=1.0),  # C
        Note(pitch=62, start=3.0, duration=1.0),  # D
        Note(pitch=64, start=4.0, duration=1.0),  # E
        Note(pitch=65, start=5.0, duration=1.0),  # F
        Note(pitch=67, start=6.0, duration=1.0),  # G
    ]

    print("Analyzing A minor scale notes...")
    keys = await music_theory.analyze_key(a_minor_notes)

    print("Detected keys (sorted by confidence):")
    for i, key in enumerate(keys[:3]):
        print(f"  {i + 1}. {key.root} {key.mode} (confidence: {key.confidence:.1%})")

    # Example 3: Chord progression suggestions
    print("\n2. CHORD PROGRESSION SUGGESTIONS")
    print("-" * 40)

    # Get chord suggestions for C major
    print("Chord progressions for C major (Pop genre):")
    progressions = await music_theory.suggest_chord_progressions(
        root="C",
        mode="major",
        genre="pop",
    )

    for i, prog in enumerate(progressions[:5]):
        chords = " -> ".join(prog.chords)
        print(f"  {i + 1}. {chords}")
        if prog.name:
            print(f"     ({prog.name})")

    # Example 4: Jazz chord suggestions
    print("\n" + "-" * 40)
    print("Chord progressions for D minor (Jazz genre):")

    jazz_progressions = await music_theory.suggest_chord_progressions(
        root="D",
        mode="minor",
        genre="jazz",
    )

    for i, prog in enumerate(jazz_progressions[:5]):
        chords = " -> ".join(prog.chords)
        print(f"  {i + 1}. {chords}")
        if prog.name:
            print(f"     ({prog.name})")

    # Example 5: Scale notes
    print("\n3. SCALE INFORMATION")
    print("-" * 40)

    scales = ["major", "minor", "dorian", "mixolydian", "pentatonic"]

    for scale in scales:
        notes = await music_theory.get_scale_notes(root="C", scale_type=scale)
        note_names = [n.name for n in notes]
        print(f"  C {scale}: {' '.join(note_names)}")

    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
