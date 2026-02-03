Quick Start
===========

This guide will help you get started with the Ableton Live MCP Server.

Starting the Server
-------------------

Before starting the server, ensure:

1. Ableton Live is running with a project open
2. AbletonOSC remote script is enabled

Then start the MCP server:

.. code-block:: bash

   # Using the entry point
   ableton-mcp

   # Or run directly
   python -m ableton_mcp.main

Basic Usage with Python
-----------------------

Here's a simple example of connecting to Ableton Live:

.. code-block:: python

   import asyncio
   from ableton_mcp.container import Container

   async def main():
       # Initialize the container
       container = Container()
       gateway = container.ableton_gateway()

       # Connect to Ableton Live
       await gateway.connect(
           host="127.0.0.1",
           send_port=11000,
           receive_port=11001,
       )

       # Get song information
       song = await gateway.get_song_info()
       print(f"Tempo: {song.tempo} BPM")

       # Start playback
       await gateway.start_playback()

       # Wait and stop
       await asyncio.sleep(5)
       await gateway.stop_playback()

       # Disconnect
       await gateway.disconnect()

   asyncio.run(main())

MCP Tool Examples
-----------------

When integrated with an MCP client, the following tools are available:

Connection
^^^^^^^^^^

.. code-block:: python

   # Connect to Ableton Live
   await mcp_client.call_tool("connect_ableton", {
       "host": "127.0.0.1",
       "send_port": 11000,
       "receive_port": 11001
   })

Transport Control
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Start playback
   await mcp_client.call_tool("transport_control", {"action": "play"})

   # Stop playback
   await mcp_client.call_tool("transport_control", {"action": "stop"})

   # Start recording
   await mcp_client.call_tool("transport_control", {"action": "record"})

Song Information
^^^^^^^^^^^^^^^^

.. code-block:: python

   # Get song metadata
   song_info = await mcp_client.call_tool("get_song_info", {
       "include_tracks": True,
       "include_devices": True
   })

Track Operations
^^^^^^^^^^^^^^^^

.. code-block:: python

   # Set track volume (0.0 to 1.0)
   await mcp_client.call_tool("track_operations", {
       "action": "set_volume",
       "track_id": 0,
       "value": 0.75
   })

   # Mute a track
   await mcp_client.call_tool("track_operations", {
       "action": "set_mute",
       "track_id": 0,
       "value": True
   })

Adding MIDI Notes
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Add notes with scale filtering
   await mcp_client.call_tool("add_notes", {
       "track_id": 0,
       "clip_id": 0,
       "notes": [
           {"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100},
           {"pitch": 64, "start": 1.0, "duration": 1.0, "velocity": 90},
       ],
       "quantize": True,
       "scale_filter": "major",
       "root_note": 60
   })

Music Theory Analysis
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Analyze harmony
   result = await mcp_client.call_tool("analyze_harmony", {
       "notes": [60, 64, 67, 72],
       "suggest_progressions": True,
       "genre": "pop"
   })

Running Examples
----------------

The ``examples/`` directory contains runnable scripts:

.. code-block:: bash

   # Basic usage
   python examples/basic_usage.py

   # Song information
   python examples/song_info.py

   # Harmony analysis
   python examples/harmony_analysis.py

   # Full workflow
   python examples/full_workflow.py

There's also a Jupyter notebook for interactive exploration:

.. code-block:: bash

   jupyter notebook examples/quickstart.ipynb

Next Steps
----------

- :doc:`configuration` - Learn about configuration options
- :doc:`api/index` - Explore the full API reference
- :doc:`guides/architecture` - Understand the architecture
