Architecture Guide
==================

This guide explains the Clean Architecture implementation in the
Ableton Live MCP Server.

Overview
--------

The project follows **Clean Architecture** principles, ensuring:

- **Independence** from frameworks, UI, databases, and external agencies
- **Testability** through clear boundaries and dependency injection
- **Maintainability** via separation of concerns

Layer Structure
---------------

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │              Interfaces                 │  External Communication
   │         (MCP Server, CLI)               │
   ├─────────────────────────────────────────┤
   │               Adapters                  │  Protocol Translation
   │       (Service Adapters)                │
   ├─────────────────────────────────────────┤
   │              Application                │  Business Logic
   │           (Use Cases)                   │
   ├─────────────────────────────────────────┤
   │               Domain                    │  Core Entities
   │     (Entities, Services, Repos)         │
   ├─────────────────────────────────────────┤
   │            Infrastructure               │  External Concerns
   │    (OSC, Repositories, Services)        │
   └─────────────────────────────────────────┘

Dependency Rule
---------------

Dependencies point **inward**. Outer layers depend on inner layers,
never the reverse.

.. code-block:: text

   Interfaces → Adapters → Application → Domain ← Infrastructure

The Domain layer has NO external dependencies.

Layer Responsibilities
----------------------

Domain Layer
^^^^^^^^^^^^

**Location**: ``ableton_mcp/domain/``

Contains:

- **Entities** - Core business objects (Song, Track, Clip, Note)
- **Repository Interfaces** - Abstract data access contracts
- **Service Interfaces** - Abstract business logic contracts

.. code-block:: python

   # Domain entities are pure Python with no dependencies
   @dataclass
   class Note:
       pitch: int
       start: float
       duration: float
       velocity: int = 100

Application Layer
^^^^^^^^^^^^^^^^^

**Location**: ``ableton_mcp/application/``

Contains:

- **Use Cases** - Single-purpose business operations
- **Request/Response DTOs** - Data transfer objects

.. code-block:: python

   class TransportControlUseCase:
       def __init__(self, gateway: AbletonGateway):
           self.gateway = gateway

       async def execute(self, request: TransportControlRequest) -> UseCaseResult:
           if request.action == "play":
               await self.gateway.start_playback()
           return UseCaseResult(success=True)

Infrastructure Layer
^^^^^^^^^^^^^^^^^^^^

**Location**: ``ableton_mcp/infrastructure/``

Contains:

- **OSC Client** - Network communication
- **Repository Implementations** - Data storage
- **Service Implementations** - Business logic

.. code-block:: python

   class MusicTheoryService:
       async def analyze_key(self, notes: list[Note]) -> list[MusicKey]:
           # Implementation using music theory algorithms
           ...

Interfaces Layer
^^^^^^^^^^^^^^^^

**Location**: ``ableton_mcp/interfaces/``

Contains:

- **MCP Server** - Protocol handling
- **Tool Definitions** - External API

Dependency Injection
--------------------

The project uses ``dependency-injector`` for wiring components.

Container
^^^^^^^^^

**Location**: ``ableton_mcp/container.py``

.. code-block:: python

   from dependency_injector import containers, providers

   class Container(containers.DeclarativeContainer):
       config = providers.Configuration()

       # Infrastructure
       osc_client = providers.Singleton(OSCClient)

       # Gateway
       ableton_gateway = providers.Singleton(
           AbletonGateway,
           osc_client=osc_client
       )

       # Services
       music_theory_service = providers.Singleton(MusicTheoryService)

       # Use Cases
       transport_use_case = providers.Factory(
           TransportControlUseCase,
           gateway=ableton_gateway
       )

Usage
^^^^^

.. code-block:: python

   container = Container()

   # Get singleton gateway
   gateway = container.ableton_gateway()

   # Get new use case instance
   use_case = container.transport_use_case()

Design Patterns
---------------

Repository Pattern
^^^^^^^^^^^^^^^^^^

Abstract data access behind interfaces:

.. code-block:: python

   # Domain defines the interface
   class TrackRepository(ABC):
       @abstractmethod
       async def get_all(self) -> list[Track]:
           ...

   # Infrastructure implements it
   class InMemoryTrackRepository(TrackRepository):
       async def get_all(self) -> list[Track]:
           return list(self._tracks.values())

Use Case Pattern
^^^^^^^^^^^^^^^^

Each operation is a discrete use case:

.. code-block:: python

   class AddNotesUseCase:
       async def execute(self, request: AddNotesRequest) -> UseCaseResult:
           # 1. Validate request
           # 2. Apply business rules (quantization, scale filtering)
           # 3. Persist changes
           # 4. Return result

Adapter Pattern
^^^^^^^^^^^^^^^

Bridge between layers:

.. code-block:: python

   class ServiceAdapter:
       def __init__(self, gateway: AbletonGateway):
           self.gateway = gateway

       async def get_song_info(self) -> dict:
           song = await self.gateway.get_song_info()
           return self._to_dict(song)

Testing Strategy
----------------

The architecture enables comprehensive testing:

Unit Tests
^^^^^^^^^^

Test domain logic in isolation:

.. code-block:: python

   def test_note_creation():
       note = Note(pitch=60, start=0.0, duration=1.0)
       assert note.pitch == 60

Integration Tests
^^^^^^^^^^^^^^^^^

Test component interactions with mocks:

.. code-block:: python

   async def test_transport_control(mock_gateway):
       use_case = TransportControlUseCase(gateway=mock_gateway)
       result = await use_case.execute(TransportControlRequest(action="play"))
       assert result.success
       mock_gateway.start_playback.assert_called_once()

Benefits
--------

1. **Testability** - Each layer can be tested independently
2. **Flexibility** - Swap implementations without changing business logic
3. **Maintainability** - Clear boundaries reduce coupling
4. **Scalability** - Add features without architectural changes
