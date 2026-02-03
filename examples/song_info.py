"""Song information retrieval example.

This example demonstrates how to:
1. Get comprehensive song metadata
2. List all tracks with their properties
3. Enumerate devices on tracks

Prerequisites:
- Ableton Live running with AbletonOSC installed
- A project with tracks and devices loaded
"""

import asyncio

from ableton_mcp.container import Container


async def main() -> None:
    """Retrieve and display song information."""
    container = Container()
    gateway = container.ableton_gateway()

    print("Connecting to Ableton Live...")

    try:
        await gateway.connect()
        print("Connected!\n")

        # Get full song information
        song = await gateway.get_song_info()

        # Display song metadata
        print("=" * 50)
        print("SONG INFORMATION")
        print("=" * 50)
        print(f"Tempo: {song.tempo} BPM")
        print(f"Time Signature: {song.time_signature}")
        print(f"Is Playing: {song.is_playing}")
        print(f"Current Time: {song.current_time:.2f} beats")

        # Display track information
        print("\n" + "=" * 50)
        print("TRACKS")
        print("=" * 50)

        tracks = await gateway.get_tracks()

        if not tracks:
            print("No tracks found in the project.")
        else:
            for i, track in enumerate(tracks):
                print(f"\n[Track {i}] {track.name}")
                print(f"  Type: {track.track_type}")
                print(f"  Volume: {track.volume:.2f}")
                print(f"  Pan: {track.pan:.2f}")
                print(f"  Mute: {track.is_muted}")
                print(f"  Solo: {track.is_solo}")
                print(f"  Arm: {track.is_armed}")

                # Display devices if available
                if track.devices:
                    print(f"  Devices ({len(track.devices)}):")
                    for device in track.devices:
                        print(f"    - {device.name} ({'ON' if device.is_enabled else 'OFF'})")

        print("\n" + "=" * 50)
        print("Done!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        await gateway.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
