Infrastructure Layer
====================

The infrastructure layer implements external concerns: OSC communication,
repository implementations, and service implementations.

OSC Client
----------

.. automodule:: ableton_mcp.infrastructure.osc_client
   :members:
   :undoc-members:
   :show-inheritance:

OSC Communication
^^^^^^^^^^^^^^^^^

The OSC client handles bidirectional communication with Ableton Live
via the AbletonOSC remote script.

.. code-block:: python

   from ableton_mcp.infrastructure.osc_client import OSCClient

   client = OSCClient()

   # Connect
   await client.connect(
       host="127.0.0.1",
       send_port=11000,
       receive_port=11001
   )

   # Send message
   await client.send("/live/song/get/tempo")

   # Receive response
   response = await client.receive()

   # Disconnect
   await client.disconnect()

OSC Message Protocol
^^^^^^^^^^^^^^^^^^^^

Common OSC addresses used:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Address
     - Description
   * - ``/live/song/get/tempo``
     - Get current tempo
   * - ``/live/song/set/tempo``
     - Set tempo
   * - ``/live/song/start_playing``
     - Start playback
   * - ``/live/song/stop_playing``
     - Stop playback
   * - ``/live/track/get/volume``
     - Get track volume
   * - ``/live/track/set/volume``
     - Set track volume
   * - ``/live/clip/add_notes``
     - Add MIDI notes to clip

Repositories
------------

.. automodule:: ableton_mcp.infrastructure.repositories
   :members:
   :undoc-members:
   :show-inheritance:

In-Memory Repositories
^^^^^^^^^^^^^^^^^^^^^^

The infrastructure layer provides in-memory implementations of repository
interfaces for caching and testing:

.. code-block:: python

   from ableton_mcp.infrastructure.repositories import InMemoryTrackRepository

   repo = InMemoryTrackRepository()

   # Save track
   await repo.save(track)

   # Retrieve tracks
   tracks = await repo.get_all()

Services
--------

.. automodule:: ableton_mcp.infrastructure.services
   :members:
   :undoc-members:
   :show-inheritance:

MusicTheoryService
^^^^^^^^^^^^^^^^^^

Provides music theory analysis and suggestions:

.. code-block:: python

   from ableton_mcp.infrastructure.services import MusicTheoryService

   service = MusicTheoryService()

   # Analyze key
   keys = await service.analyze_key(notes)
   print(f"Detected key: {keys[0].root} {keys[0].mode}")

   # Get chord progressions
   progressions = await service.suggest_chord_progressions(
       root="C",
       mode="major",
       genre="pop"
   )

   # Get scale notes
   scale = await service.get_scale_notes(
       root="A",
       scale_type="minor"
   )

TempoAnalysisService
^^^^^^^^^^^^^^^^^^^^

Provides tempo analysis and genre-specific suggestions:

.. code-block:: python

   from ableton_mcp.infrastructure.services import TempoAnalysisService

   service = TempoAnalysisService()

   # Analyze tempo
   analysis = await service.analyze_tempo(
       current_bpm=128,
       genre="house"
   )

   print(f"Suggested range: {analysis.min_bpm}-{analysis.max_bpm} BPM")
   print(f"Energy level: {analysis.energy_level}")

Gateway
-------

.. automodule:: ableton_mcp.infrastructure.osc.gateway
   :members:
   :undoc-members:
   :show-inheritance:

The AbletonGateway provides a high-level interface to Ableton Live,
abstracting the OSC protocol details.
