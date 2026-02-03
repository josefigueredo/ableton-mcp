Domain Layer
============

The domain layer contains core business entities, repository interfaces,
and domain service contracts. This layer has no external dependencies.

Entities
--------

.. automodule:: ableton_mcp.domain.entities
   :members:
   :undoc-members:
   :show-inheritance:

Core Entities
^^^^^^^^^^^^^

Song
""""

Represents an Ableton Live project/song.

.. code-block:: python

   from ableton_mcp.domain.entities import Song

   song = Song(
       tempo=120.0,
       time_signature="4/4",
       is_playing=False,
       current_time=0.0,
       tracks=[]
   )

Track
"""""

Represents a track in the session.

.. code-block:: python

   from ableton_mcp.domain.entities import Track

   track = Track(
       id=0,
       name="Bass",
       track_type="midi",
       volume=0.85,
       pan=0.0,
       is_muted=False,
       is_solo=False,
       is_armed=True,
       devices=[],
       clips=[]
   )

Note
""""

Represents a MIDI note.

.. code-block:: python

   from ableton_mcp.domain.entities import Note

   note = Note(
       pitch=60,      # MIDI pitch (0-127)
       start=0.0,     # Start time in beats
       duration=1.0,  # Duration in beats
       velocity=100   # Velocity (0-127)
   )

Clip
""""

Represents a clip in a track.

.. code-block:: python

   from ableton_mcp.domain.entities import Clip

   clip = Clip(
       id=0,
       name="Intro",
       length=4.0,
       is_playing=False,
       notes=[]
   )

Device
""""""

Represents an audio/MIDI device on a track.

.. code-block:: python

   from ableton_mcp.domain.entities import Device

   device = Device(
       id=0,
       name="Wavetable",
       is_enabled=True,
       parameters=[]
   )

Repositories
------------

.. automodule:: ableton_mcp.domain.repositories
   :members:
   :undoc-members:
   :show-inheritance:

Repository Pattern
^^^^^^^^^^^^^^^^^^

The domain defines abstract repository interfaces that are implemented
in the infrastructure layer.

.. code-block:: python

   from abc import ABC, abstractmethod
   from ableton_mcp.domain.entities import Track

   class TrackRepository(ABC):
       @abstractmethod
       async def get_all(self) -> list[Track]:
           ...

       @abstractmethod
       async def get_by_id(self, track_id: int) -> Track | None:
           ...

       @abstractmethod
       async def save(self, track: Track) -> None:
           ...

Services
--------

.. automodule:: ableton_mcp.domain.services
   :members:
   :undoc-members:
   :show-inheritance:

Domain Service Interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^

The domain defines service interfaces that encapsulate complex business logic:

- **MusicTheoryService** - Key analysis, chord progressions, scale operations
- **TempoAnalysisService** - BPM analysis, genre suggestions

These interfaces are implemented in the infrastructure layer.
