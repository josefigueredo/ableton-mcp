"""Full production workflow example.

This example demonstrates a complete workflow:
1. Connect to Ableton Live
2. Analyze existing project
3. Create new tracks
4. Add MIDI content with music theory assistance
5. Apply mixing suggestions

Prerequisites:
- Ableton Live running with AbletonOSC installed
- An existing project (optional, will work with empty project too)
"""

import asyncio

from ableton_mcp.container import Container
from ableton_mcp.domain.entities import Note


async def main() -> None:
    """Execute complete production workflow."""
    container = Container()
    gateway = container.ableton_gateway()
    music_theory = container.music_theory_service()
    tempo_service = container.tempo_analysis_service()

    print("=" * 60)
    print("ABLETON LIVE MCP - FULL WORKFLOW EXAMPLE")
    print("=" * 60)

    try:
        # Step 1: Connect
        print("\n[1/6] CONNECTING TO ABLETON LIVE")
        print("-" * 40)
        await gateway.connect()
        print("Connected successfully!")

        # Step 2: Analyze current project
        print("\n[2/6] ANALYZING PROJECT")
        print("-" * 40)

        song = await gateway.get_song_info()
        tracks = await gateway.get_tracks()

        print(f"Current tempo: {song.tempo} BPM")
        print(f"Track count: {len(tracks)}")

        # Get tempo suggestions
        tempo_suggestions = await tempo_service.analyze_tempo(
            current_bpm=song.tempo,
            genre="electronic",
        )
        print(f"\nTempo analysis for electronic music:")
        print(f"  Current BPM: {song.tempo}")
        print(f"  Suggested range: {tempo_suggestions.min_bpm}-{tempo_suggestions.max_bpm} BPM")
        print(f"  Energy level: {tempo_suggestions.energy_level}")

        # Step 3: Choose a key for our composition
        print("\n[3/6] SELECTING KEY AND SCALE")
        print("-" * 40)

        root = "A"
        mode = "minor"
        print(f"Composing in: {root} {mode}")

        # Get chord progressions for this key
        progressions = await music_theory.suggest_chord_progressions(
            root=root,
            mode=mode,
            genre="electronic",
        )

        print("\nSuggested chord progressions:")
        for i, prog in enumerate(progressions[:3]):
            chords = " -> ".join(prog.chords)
            print(f"  {i + 1}. {chords}")

        # Select the first progression
        selected_progression = progressions[0] if progressions else None
        if selected_progression:
            print(f"\nSelected: {' -> '.join(selected_progression.chords)}")

        # Step 4: Create a bass track (if we have permission)
        print("\n[4/6] CREATING TRACKS")
        print("-" * 40)

        response = input("Create a new bass track? (y/n): ")
        bass_track_index = None

        if response.lower() == "y":
            bass_track_index = await gateway.create_track(
                track_type="midi",
                name="Bass (Generated)",
                index=-1,
            )
            print(f"Created bass track at index {bass_track_index}")

            # Set volume slightly lower
            await gateway.set_track_volume(bass_track_index, 0.75)
            print("  Volume set to 75%")
        else:
            print("Skipping track creation.")

        # Step 5: Generate bass line
        print("\n[5/6] GENERATING CONTENT")
        print("-" * 40)

        if bass_track_index is not None:
            # Create a simple bass line in A minor
            # Following the chord progression: Am -> F -> C -> G
            bass_notes = [
                # Bar 1: Am (A2)
                Note(pitch=45, start=0.0, duration=0.5, velocity=100),
                Note(pitch=45, start=1.0, duration=0.5, velocity=90),
                Note(pitch=45, start=2.0, duration=0.5, velocity=100),
                Note(pitch=45, start=3.0, duration=0.5, velocity=90),
                # Bar 2: F (F2)
                Note(pitch=41, start=4.0, duration=0.5, velocity=100),
                Note(pitch=41, start=5.0, duration=0.5, velocity=90),
                Note(pitch=41, start=6.0, duration=0.5, velocity=100),
                Note(pitch=41, start=7.0, duration=0.5, velocity=90),
                # Bar 3: C (C3)
                Note(pitch=48, start=8.0, duration=0.5, velocity=100),
                Note(pitch=48, start=9.0, duration=0.5, velocity=90),
                Note(pitch=48, start=10.0, duration=0.5, velocity=100),
                Note(pitch=48, start=11.0, duration=0.5, velocity=90),
                # Bar 4: G (G2)
                Note(pitch=43, start=12.0, duration=0.5, velocity=100),
                Note(pitch=43, start=13.0, duration=0.5, velocity=90),
                Note(pitch=43, start=14.0, duration=0.5, velocity=100),
                Note(pitch=43, start=15.0, duration=0.5, velocity=90),
            ]

            print(f"Adding {len(bass_notes)} notes to bass track...")

            try:
                await gateway.add_notes(
                    track_id=bass_track_index,
                    clip_id=0,
                    notes=bass_notes,
                    quantize=True,
                )
                print("Bass line added successfully!")
            except Exception as e:
                print(f"Note: Could not add notes - {e}")
                print("(You may need to create a MIDI clip in the track first)")
        else:
            print("No bass track created, skipping content generation.")

        # Step 6: Playback preview
        print("\n[6/6] PREVIEW")
        print("-" * 40)

        response = input("Preview the result? (y/n): ")

        if response.lower() == "y":
            print("Starting playback...")
            await gateway.start_playback()

            # Play for 8 bars (16 beats at typical tempo)
            play_duration = (16 / song.tempo) * 60
            print(f"Playing for {play_duration:.1f} seconds...")
            await asyncio.sleep(play_duration)

            await gateway.stop_playback()
            print("Playback stopped.")
        else:
            print("Skipping preview.")

        # Summary
        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETE")
        print("=" * 60)
        print("\nSummary:")
        print(f"  - Key: {root} {mode}")
        if selected_progression:
            print(f"  - Progression: {' -> '.join(selected_progression.chords)}")
        if bass_track_index:
            print(f"  - Created bass track with 16 notes")
        print("\nYour project is ready for further development!")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await gateway.disconnect()
        print("\nDisconnected from Ableton Live.")


if __name__ == "__main__":
    asyncio.run(main())
