"""MIDI note addition example.

This example demonstrates how to:
1. Add MIDI notes to a clip
2. Use quantization options
3. Apply scale filtering for musical results

Prerequisites:
- Ableton Live running with AbletonOSC installed
- A MIDI track with an empty clip slot
"""

import asyncio

from ableton_mcp.container import Container
from ableton_mcp.domain.entities import Note


async def main() -> None:
    """Demonstrate MIDI note addition."""
    container = Container()
    gateway = container.ableton_gateway()

    print("Connecting to Ableton Live...")

    try:
        await gateway.connect()
        print("Connected!\n")

        # Configuration
        track_index = 0  # First track
        clip_index = 0   # First clip slot

        print(f"Target: Track {track_index}, Clip slot {clip_index}")
        print("-" * 40)

        # Create a simple C major chord (C4, E4, G4)
        print("\nExample 1: Simple C Major Chord")
        chord_notes = [
            Note(pitch=60, start=0.0, duration=1.0, velocity=100),  # C4
            Note(pitch=64, start=0.0, duration=1.0, velocity=100),  # E4
            Note(pitch=67, start=0.0, duration=1.0, velocity=100),  # G4
        ]

        await gateway.add_notes(
            track_id=track_index,
            clip_id=clip_index,
            notes=chord_notes,
        )
        print("  Added C major chord at beat 0")

        # Create a melody with quantization
        print("\nExample 2: Melody with Quantization")
        melody_notes = [
            Note(pitch=60, start=1.0, duration=0.5, velocity=90),   # C4
            Note(pitch=62, start=1.55, duration=0.5, velocity=85),  # D4 (slightly off-grid)
            Note(pitch=64, start=2.0, duration=0.5, velocity=90),   # E4
            Note(pitch=65, start=2.48, duration=0.5, velocity=85),  # F4 (slightly off-grid)
            Note(pitch=67, start=3.0, duration=1.0, velocity=100),  # G4
        ]

        await gateway.add_notes(
            track_id=track_index,
            clip_id=clip_index,
            notes=melody_notes,
            quantize=True,
            quantize_value=0.5,  # Quantize to 8th notes
        )
        print("  Added melody with 8th note quantization")

        # Create notes with scale filtering
        print("\nExample 3: Scale-Filtered Notes (C Minor)")

        # These notes include some out-of-scale pitches
        # Scale filtering will adjust them to fit C minor
        raw_notes = [
            Note(pitch=60, start=4.0, duration=0.5, velocity=90),   # C4 (in scale)
            Note(pitch=62, start=4.5, duration=0.5, velocity=85),   # D4 (in scale)
            Note(pitch=64, start=5.0, duration=0.5, velocity=90),   # E4 -> Eb4 (filtered)
            Note(pitch=65, start=5.5, duration=0.5, velocity=85),   # F4 (in scale)
            Note(pitch=67, start=6.0, duration=0.5, velocity=90),   # G4 (in scale)
            Note(pitch=69, start=6.5, duration=0.5, velocity=85),   # A4 -> Ab4 (filtered)
            Note(pitch=71, start=7.0, duration=0.5, velocity=90),   # B4 -> Bb4 (filtered)
            Note(pitch=72, start=7.5, duration=0.5, velocity=100),  # C5 (in scale)
        ]

        await gateway.add_notes(
            track_id=track_index,
            clip_id=clip_index,
            notes=raw_notes,
            scale_filter="minor",
            root_note=60,  # C
        )
        print("  Added scale-filtered notes (adjusted to C minor)")

        # Summary
        print("\n" + "=" * 40)
        print("SUMMARY")
        print("=" * 40)
        print(f"Total notes added to Track {track_index}, Clip {clip_index}:")
        print(f"  - C major chord (3 notes)")
        print(f"  - Quantized melody (5 notes)")
        print(f"  - Scale-filtered phrase (8 notes)")
        print("\nCheck Ableton Live to see the results!")

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Ensure the target track has a MIDI clip in the first slot.")
        print("You may need to create an empty MIDI clip first.")

    finally:
        await gateway.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
