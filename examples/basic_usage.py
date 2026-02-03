"""Basic usage example for Ableton Live MCP Server.

This example demonstrates how to:
1. Connect to Ableton Live via OSC
2. Control transport (play/stop)
3. Get basic song information

Prerequisites:
- Ableton Live running with AbletonOSC installed
- ableton-mcp package installed (pip install -e .)
"""

import asyncio

from ableton_mcp.container import Container


async def main() -> None:
    """Run basic usage example."""
    # Initialize the dependency injection container
    container = Container()

    # Get the gateway (handles OSC communication)
    gateway = container.ableton_gateway()

    print("Connecting to Ableton Live...")

    try:
        # Connect to Ableton Live
        # Default ports: 11000 (send), 11001 (receive)
        await gateway.connect(
            host="127.0.0.1",
            send_port=11000,
            receive_port=11001,
        )
        print("Connected successfully!")

        # Get song information
        song = await gateway.get_song_info()
        print(f"Song Info: BPM={song.tempo}, Time Signature={song.time_signature}")

        # Start playback
        print("Starting playback...")
        await gateway.start_playback()
        print("Playback started!")

        # Wait a few seconds
        print("Waiting 5 seconds...")
        await asyncio.sleep(5)

        # Stop playback
        print("Stopping playback...")
        await gateway.stop_playback()

        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Ableton Live is running")
        print("2. Verify AbletonOSC remote script is enabled")
        print("3. Check that ports 11000-11001 are available")

    finally:
        # Clean up
        await gateway.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
