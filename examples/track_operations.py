"""Track operations example.

This example demonstrates how to:
1. Create new tracks
2. Modify track properties (volume, pan, mute, solo)
3. Arm tracks for recording
4. Delete tracks

Prerequisites:
- Ableton Live running with AbletonOSC installed
"""

import asyncio

from ableton_mcp.container import Container


async def main() -> None:
    """Demonstrate track operations."""
    container = Container()
    gateway = container.ableton_gateway()

    print("Connecting to Ableton Live...")

    try:
        await gateway.connect()
        print("Connected!\n")

        # Get initial track count
        tracks = await gateway.get_tracks()
        initial_count = len(tracks)
        print(f"Initial track count: {initial_count}")

        # Create a new MIDI track
        print("\nCreating new MIDI track...")
        new_track_index = await gateway.create_track(
            track_type="midi",
            name="Example MIDI Track",
            index=-1,  # -1 means append at end
        )
        print(f"Created track at index: {new_track_index}")

        # Wait for Ableton to process
        await asyncio.sleep(0.5)

        # Modify track properties
        print("\nModifying track properties...")

        # Set volume (0.0 to 1.0, where 0.85 is approximately 0dB)
        await gateway.set_track_volume(new_track_index, 0.7)
        print(f"  Volume set to 0.7")

        # Set pan (-1.0 to 1.0, where 0 is center)
        await gateway.set_track_pan(new_track_index, 0.0)
        print(f"  Pan set to center")

        # Arm the track for recording
        await gateway.set_track_arm(new_track_index, True)
        print(f"  Track armed for recording")

        # Get updated track info
        await asyncio.sleep(0.3)
        tracks = await gateway.get_tracks()
        if new_track_index < len(tracks):
            track = tracks[new_track_index]
            print(f"\nTrack '{track.name}' properties:")
            print(f"  Volume: {track.volume:.2f}")
            print(f"  Pan: {track.pan:.2f}")
            print(f"  Armed: {track.is_armed}")

        # Demonstrate mute/solo
        print("\nDemonstrating mute/solo...")
        await gateway.set_track_mute(new_track_index, True)
        print("  Track muted")
        await asyncio.sleep(1)

        await gateway.set_track_mute(new_track_index, False)
        await gateway.set_track_solo(new_track_index, True)
        print("  Track soloed")
        await asyncio.sleep(1)

        await gateway.set_track_solo(new_track_index, False)
        print("  Solo disabled")

        # Ask before deleting
        print("\n" + "-" * 40)
        response = input("Delete the example track? (y/n): ")

        if response.lower() == "y":
            await gateway.delete_track(new_track_index)
            print("Track deleted!")

            # Verify deletion
            tracks = await gateway.get_tracks()
            print(f"Final track count: {len(tracks)}")
        else:
            print("Track kept. You can delete it manually in Ableton Live.")

        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        await gateway.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
