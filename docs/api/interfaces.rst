Interfaces Layer
================

The interfaces layer handles external communication, primarily through the
Model Context Protocol (MCP).

MCP Server
----------

.. automodule:: ableton_mcp.interfaces.mcp_server
   :members:
   :undoc-members:
   :show-inheritance:

Available MCP Tools
-------------------

The MCP server exposes the following tools to AI assistants:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Tool Name
     - Description
   * - ``connect_ableton``
     - Establish OSC connection to Ableton Live
   * - ``transport_control``
     - Control playback (play, stop, record)
   * - ``get_song_info``
     - Retrieve song metadata and track information
   * - ``track_operations``
     - Manipulate track properties (volume, pan, mute, solo, arm)
   * - ``add_notes``
     - Add MIDI notes to clips with optional quantization
   * - ``analyze_harmony``
     - Analyze musical key and suggest chord progressions
   * - ``analyze_tempo``
     - Get tempo suggestions based on genre and energy

Tool Schemas
------------

connect_ableton
^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "host": "127.0.0.1",
     "send_port": 11000,
     "receive_port": 11001
   }

transport_control
^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "action": "play"  // "play", "stop", or "record"
   }

get_song_info
^^^^^^^^^^^^^

.. code-block:: json

   {
     "include_tracks": true,
     "include_devices": true
   }

track_operations
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "action": "set_volume",
     "track_id": 0,
     "value": 0.75
   }

add_notes
^^^^^^^^^

.. code-block:: json

   {
     "track_id": 0,
     "clip_id": 0,
     "notes": [
       {"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100}
     ],
     "quantize": true,
     "quantize_value": 0.25,
     "scale_filter": "major",
     "root_note": 60
   }

analyze_harmony
^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "notes": [60, 64, 67, 72],
     "suggest_progressions": true,
     "genre": "pop"
   }
