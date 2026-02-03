# Ableton MCP Server - Architecture & Development Guide

> Complete technical documentation for understanding, extending, and debugging the Ableton Live MCP Server

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Clean Architecture Layers](#2-clean-architecture-layers)
3. [Design Patterns](#3-design-patterns)
4. [Sequence Diagrams](#4-sequence-diagrams)
5. [Adding New Features Guide](#5-adding-new-features-guide)
6. [Bug Hunting & Debugging Guide](#6-bug-hunting--debugging-guide)
7. [AI Context Prompt](#7-ai-context-prompt)

---

## 1. Architecture Overview

### High-Level System Architecture

```mermaid
flowchart TB
    subgraph External["External Systems"]
        User["User/AI Assistant"]
        Ableton["Ableton Live + AbletonOSC"]
    end

    subgraph MCP["MCP Server (Python)"]
        subgraph Interface["Interfaces Layer"]
            MCPServer["MCP Server<br/>mcp_server.py"]
        end

        subgraph Application["Application Layer"]
            UseCases["Use Cases<br/>use_cases.py"]
        end

        subgraph Domain["Domain Layer"]
            Entities["Entities<br/>entities.py"]
            Services["Domain Services<br/>services.py"]
            Repos["Repository Interfaces<br/>repositories.py"]
            Ports["Gateway Ports<br/>ports.py"]
        end

        subgraph Adapters["Adapters Layer"]
            ServiceAdapters["Service Adapters<br/>service_adapters.py"]
        end

        subgraph Infrastructure["Infrastructure Layer"]
            OSCGateway["OSC Gateway<br/>gateway.py"]
            RepoImpl["Repository Implementations<br/>repositories.py"]
            ServiceImpl["Service Implementations<br/>services.py"]
            Transport["OSC Transport<br/>transport.py"]
            Correlator["Message Correlator<br/>correlator.py"]
        end

        subgraph Core["Core Layer"]
            Exceptions["Exceptions<br/>exceptions.py"]
            Logging["Logging<br/>logging.py"]
        end

        DI["DI Container<br/>container.py"]
    end

    User -->|MCP Protocol| MCPServer
    MCPServer --> UseCases
    UseCases --> Services
    UseCases --> ServiceAdapters
    ServiceAdapters --> OSCGateway
    OSCGateway --> Transport
    Transport -->|OSC UDP| Ableton
    Ableton -->|OSC Response| Transport
    Transport --> Correlator
    UseCases --> Repos
    RepoImpl -.->|implements| Repos
    ServiceImpl -.->|implements| Services
    OSCGateway -.->|implements| Ports
    DI -->|wires| MCPServer
    DI -->|wires| UseCases
    DI -->|wires| ServiceAdapters
    DI -->|wires| RepoImpl
    DI -->|wires| ServiceImpl
```

### Directory Structure

```
ableton_mcp/
├── __init__.py              # Package initialization
├── main.py                  # Application entry point
├── container.py             # Dependency Injection container
│
├── core/                    # Cross-cutting concerns
│   ├── __init__.py
│   ├── exceptions.py        # Custom exception hierarchy
│   └── logging.py           # JSON structured logging
│
├── domain/                  # Business entities & contracts
│   ├── __init__.py
│   ├── entities.py          # Song, Track, Clip, Note, etc.
│   ├── repositories.py      # Repository interfaces (ABC)
│   ├── services.py          # Domain service interfaces (ABC)
│   └── ports.py             # Gateway port interface (ABC)
│
├── application/             # Use cases (business logic)
│   ├── __init__.py
│   └── use_cases.py         # All use case classes
│
├── adapters/                # Bridge domain to infrastructure
│   ├── __init__.py
│   └── service_adapters.py  # Ableton service adapters
│
├── infrastructure/          # External implementations
│   ├── __init__.py
│   ├── repositories.py      # In-memory repository implementations
│   ├── services.py          # Music theory, mixing implementations
│   └── osc/                 # OSC communication
│       ├── __init__.py
│       ├── gateway.py       # AbletonOSCGateway implementation
│       ├── transport.py     # AsyncOSCTransport (UDP)
│       └── correlator.py    # Request-response correlation
│
└── interfaces/              # External interfaces
    ├── __init__.py
    └── mcp_server.py        # MCP protocol handler
```

---

## 2. Clean Architecture Layers

### Layer Dependency Rules

```mermaid
flowchart TB
    subgraph Outer["Outer Layers (can depend on inner)"]
        I["Interfaces"]
        Infra["Infrastructure"]
        Adapt["Adapters"]
    end

    subgraph Middle["Middle Layer"]
        App["Application"]
    end

    subgraph Inner["Inner Layers (no external dependencies)"]
        Dom["Domain"]
        Core["Core"]
    end

    I --> App
    I --> Dom
    Infra --> Dom
    Infra --> Core
    Adapt --> Dom
    App --> Dom
    App --> Core
    Dom --> Core

    style Inner fill:#90EE90
    style Middle fill:#FFD700
    style Outer fill:#FFA07A
```

### Layer Responsibilities

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **Interfaces** | Protocol handling, request/response formatting | `mcp_server.py` |
| **Application** | Business logic orchestration, use case execution | `use_cases.py` |
| **Domain** | Business entities, contracts, core business rules | `entities.py`, `services.py`, `repositories.py`, `ports.py` |
| **Adapters** | Bridge domain services to infrastructure | `service_adapters.py` |
| **Infrastructure** | External system implementations (OSC, storage) | `gateway.py`, `repositories.py`, `services.py` |
| **Core** | Cross-cutting concerns (exceptions, logging) | `exceptions.py`, `logging.py` |

### Domain Entities Hierarchy

```mermaid
classDiagram
    class Song {
        +EntityId id
        +str name
        +float tempo
        +int time_signature_numerator
        +int time_signature_denominator
        +TransportState transport_state
        +List~Track~ tracks
        +add_track(Track)
        +get_track_by_index(int)
    }

    class Track {
        +EntityId id
        +str name
        +TrackType track_type
        +float volume
        +float pan
        +bool is_muted
        +bool is_soloed
        +List~Device~ devices
        +List~Clip~ clips
        +set_clip(int, Clip)
        +get_clip(int)
    }

    class Clip {
        +EntityId id
        +str name
        +ClipType clip_type
        +float length
        +List~Note~ notes
        +add_note(Note)
    }

    class Note {
        +int pitch
        +float start
        +float duration
        +int velocity
        +bool mute
        +note_name: str
        +octave: int
        +pitch_class: int
    }

    class Device {
        +EntityId id
        +str name
        +DeviceType device_type
        +List~Parameter~ parameters
    }

    class MusicKey {
        +int root
        +str mode
        +float confidence
        +root_name: str
        +scale_notes: List~int~
    }

    Song "1" --> "*" Track
    Track "1" --> "*" Clip
    Track "1" --> "*" Device
    Clip "1" --> "*" Note
```

---

## 3. Design Patterns

### 3.1 Use Case Pattern

Each business operation is encapsulated in a dedicated use case class with an `execute()` method.

```mermaid
classDiagram
    class UseCase {
        <<abstract>>
        +execute(*args, **kwargs) UseCaseResult
    }

    class UseCaseResult {
        +bool success
        +Any data
        +str message
        +str error_code
    }

    class ConnectToAbletonUseCase {
        -connection_service
        -song_repository
        -gateway
        +execute(ConnectToAbletonRequest) UseCaseResult
    }

    class GetClipContentUseCase {
        -clip_service
        -song_repository
        +execute(GetClipContentRequest) UseCaseResult
    }

    UseCase <|-- ConnectToAbletonUseCase
    UseCase <|-- GetClipContentUseCase
    ConnectToAbletonUseCase --> UseCaseResult
    GetClipContentUseCase --> UseCaseResult
```

**Pattern Structure:**
```python
@dataclass
class MyRequest:
    """Input DTO for the use case."""
    field1: str
    field2: int = None

class MyUseCase(UseCase):
    def __init__(self, service: SomeService, repository: SomeRepository) -> None:
        self._service = service
        self._repository = repository

    async def execute(self, request: MyRequest) -> UseCaseResult:
        try:
            # Business logic here
            result = await self._service.do_something(request.field1)
            return UseCaseResult(success=True, data=result)
        except DomainError as e:
            return UseCaseResult(success=False, message=str(e), error_code=e.error_code)
```

### 3.2 Repository Pattern

Abstract interfaces define data access contracts; implementations are in infrastructure.

```mermaid
classDiagram
    class SongRepository {
        <<interface>>
        +get_current_song() Song
        +save_song(Song)
        +update_song(Song)
    }

    class InMemorySongRepository {
        -_current_song: Song
        -_lock: asyncio.Lock
        +get_current_song() Song
        +save_song(Song)
        +update_song(Song)
    }

    SongRepository <|.. InMemorySongRepository
```

### 3.3 Gateway/Port Pattern

The domain defines what it needs (port); infrastructure provides implementation (adapter).

```mermaid
classDiagram
    class AbletonGateway {
        <<interface>>
        +connect(host, send_port, receive_port)
        +disconnect()
        +is_connected() bool
        +start_playing()
        +stop_playing()
        +get_tempo() float
        +get_clip_notes(track_id, clip_id) List
    }

    class AbletonOSCGateway {
        -_transport: AsyncOSCTransport
        -_correlator: OSCCorrelator
        +connect(host, send_port, receive_port)
        +disconnect()
        +is_connected() bool
        -_send(address, args)
        -_request(address, args) List
    }

    AbletonGateway <|.. AbletonOSCGateway
```

### 3.4 Service Adapter Pattern

Thin wrappers that translate between domain and infrastructure.

```mermaid
classDiagram
    class AbletonClipService {
        -_gateway: AbletonGateway
        +fire_clip(track_id, clip_id)
        +stop_clip(track_id, clip_id)
        +add_note(track_id, clip_id, Note)
        +get_clip_notes(track_id, clip_id) List
    }

    class AbletonGateway {
        <<interface>>
    }

    AbletonClipService --> AbletonGateway
```

### 3.5 Dependency Injection Pattern

All wiring happens in `container.py` using `dependency-injector`.

```mermaid
flowchart LR
    subgraph Container["DI Container (container.py)"]
        Gateway["ableton_gateway<br/>Singleton"]
        Repos["Repositories<br/>Singleton"]
        Services["Domain Services<br/>Singleton"]
        Adapters["Service Adapters<br/>Factory"]
        UseCases["Use Cases<br/>Factory"]
        Server["MCP Server<br/>Factory"]
    end

    Gateway --> Adapters
    Repos --> UseCases
    Services --> UseCases
    Adapters --> UseCases
    UseCases --> Server
```

---

## 4. Sequence Diagrams

### 4.1 Connection Sequence

```mermaid
sequenceDiagram
    participant User
    participant MCPServer
    participant ConnectUseCase
    participant ConnectionService
    participant Gateway
    participant Transport
    participant Ableton

    User->>MCPServer: connect_ableton(host, ports)
    MCPServer->>ConnectUseCase: execute(request)
    ConnectUseCase->>ConnectionService: connect(host, ports)
    ConnectionService->>Gateway: connect(host, ports)
    Gateway->>Transport: connect(host, ports, handler)
    Transport->>Transport: Start UDP listener
    Transport-->>Gateway: Connected
    Gateway->>Gateway: Test connection (get_tempo)
    Gateway->>Transport: send("/live/song/get/tempo")
    Transport->>Ableton: OSC Message
    Ableton-->>Transport: OSC Response
    Transport-->>Gateway: Response (120.0)
    Gateway-->>ConnectionService: Connected
    ConnectionService-->>ConnectUseCase: Success
    ConnectUseCase->>ConnectUseCase: _sync_song_data()
    ConnectUseCase-->>MCPServer: UseCaseResult(success=True)
    MCPServer-->>User: "Connected to Ableton Live"
```

### 4.2 Add Notes Sequence

```mermaid
sequenceDiagram
    participant User
    participant MCPServer
    participant AddNotesUseCase
    participant MusicTheoryService
    participant ClipService
    participant Gateway
    participant Ableton

    User->>MCPServer: add_notes(track, clip, notes, quantize)
    MCPServer->>AddNotesUseCase: execute(request)
    AddNotesUseCase->>AddNotesUseCase: Validate track exists
    AddNotesUseCase->>AddNotesUseCase: Convert to Note objects

    alt quantize=True
        AddNotesUseCase->>MusicTheoryService: quantize_notes(notes)
        MusicTheoryService-->>AddNotesUseCase: quantized_notes
    end

    alt scale_filter specified
        AddNotesUseCase->>MusicTheoryService: filter_notes_to_scale(notes, key)
        MusicTheoryService-->>AddNotesUseCase: filtered_notes
    end

    loop For each note
        AddNotesUseCase->>ClipService: add_note(track, clip, note)
        ClipService->>Gateway: add_note(params)
        Gateway->>Ableton: /live/clip/add_new_notes
    end

    AddNotesUseCase-->>MCPServer: UseCaseResult(success, notes_added)
    MCPServer-->>User: "Added N notes to clip"
```

### 4.3 Get Clip Content Sequence

```mermaid
sequenceDiagram
    participant User
    participant MCPServer
    participant GetClipContentUseCase
    participant ClipService
    participant Gateway
    participant Correlator
    participant Transport
    participant Ableton

    User->>MCPServer: get_clip_content(track_id, clip_id)
    MCPServer->>GetClipContentUseCase: execute(request)
    GetClipContentUseCase->>GetClipContentUseCase: Validate track exists
    GetClipContentUseCase->>ClipService: get_clip_notes(track, clip)
    ClipService->>Gateway: get_clip_notes(track, clip)
    Gateway->>Correlator: expect_response("/live/clip/get/notes")
    Correlator-->>Gateway: Future
    Gateway->>Transport: send("/live/clip/get/notes", [track, clip])
    Transport->>Ableton: OSC Request
    Ableton-->>Transport: OSC Response (notes data)
    Transport->>Correlator: handle_response(address, args)
    Correlator-->>Gateway: Resolved Future with data
    Gateway->>Gateway: Parse notes from flat format
    Gateway-->>ClipService: List[Dict] notes
    ClipService-->>GetClipContentUseCase: notes
    GetClipContentUseCase->>GetClipContentUseCase: Add note names
    GetClipContentUseCase-->>MCPServer: UseCaseResult(notes)
    MCPServer->>MCPServer: Format for display
    MCPServer-->>User: Formatted clip content
```

### 4.4 Harmony Analysis Sequence

```mermaid
sequenceDiagram
    participant User
    participant MCPServer
    participant AnalyzeHarmonyUseCase
    participant MusicTheoryService

    User->>MCPServer: analyze_harmony(notes, genre)
    MCPServer->>AnalyzeHarmonyUseCase: execute(request)
    AnalyzeHarmonyUseCase->>AnalyzeHarmonyUseCase: Convert to Note objects
    AnalyzeHarmonyUseCase->>MusicTheoryService: analyze_key(notes)
    MusicTheoryService->>MusicTheoryService: Calculate pitch classes
    MusicTheoryService->>MusicTheoryService: Match against all scales
    MusicTheoryService->>MusicTheoryService: Calculate confidence scores
    MusicTheoryService-->>AnalyzeHarmonyUseCase: List[MusicKey]

    alt suggest_progressions=True
        AnalyzeHarmonyUseCase->>MusicTheoryService: suggest_chord_progressions(key, genre)
        MusicTheoryService->>MusicTheoryService: Get genre progressions
        MusicTheoryService->>MusicTheoryService: Transpose to key
        MusicTheoryService-->>AnalyzeHarmonyUseCase: progressions
    end

    AnalyzeHarmonyUseCase-->>MCPServer: UseCaseResult(analysis)
    MCPServer->>MCPServer: Format with special harmony formatting
    MCPServer-->>User: "Primary Key: C major (89%)"
```

---

## 5. Adding New Features Guide

### Step-by-Step Process

Follow this checklist when adding a new MCP tool or feature:

#### Step 1: Define the Request DTO (use_cases.py)

```python
@dataclass
class MyNewFeatureRequest:
    """Request for my new feature."""
    required_param: str
    optional_param: int = None
```

#### Step 2: Create the Use Case (use_cases.py)

```python
class MyNewFeatureUseCase(UseCase):
    """Use case for my new feature."""

    def __init__(
        self,
        some_service: SomeService,
        song_repository: SongRepository,
    ) -> None:
        self._some_service = some_service
        self._song_repository = song_repository
        self._logger = structlog.get_logger(__name__)

    async def execute(self, request: MyNewFeatureRequest) -> UseCaseResult:
        try:
            self._logger.info(
                "Executing my new feature",
                param=request.required_param,
            )

            # Business logic here
            result = await self._some_service.do_work(request.required_param)

            self._logger.info("Feature completed", result=result)

            return UseCaseResult(
                success=True,
                data={"result": result},
                message="Feature executed successfully",
            )

        except SomeDomainError as e:
            self._logger.warning("Domain error", error=str(e))
            return UseCaseResult(
                success=False,
                message=str(e),
                error_code=e.error_code,
            )
        except Exception as e:
            self._logger.error("Unexpected error", error=str(e))
            return UseCaseResult(
                success=False,
                message=f"Error: {str(e)}",
                error_code="MY_FEATURE_ERROR",
            )
```

#### Step 3: Add Service Adapter Method (if needed) (service_adapters.py)

```python
class AbletonSomeService:
    def __init__(self, gateway: AbletonGateway) -> None:
        self._gateway = gateway

    async def do_work(self, param: str) -> Any:
        """Do work via gateway."""
        return await self._gateway.some_method(param)
```

#### Step 4: Add Gateway Method (if new OSC command) (gateway.py & ports.py)

First, add to the port interface (ports.py):
```python
@abstractmethod
async def some_method(self, param: str) -> Any:
    """Description of what this does."""
    ...
```

Then implement in gateway (gateway.py):
```python
async def some_method(self, param: str) -> Any:
    """Implementation with OSC communication."""
    response = await self._request("/live/some/endpoint", [param])
    return self._parse_response(response)
```

#### Step 5: Wire in DI Container (container.py)

```python
# Import the use case
from ableton_mcp.application.use_cases import MyNewFeatureUseCase

# Add factory provider
my_new_feature_use_case = providers.Factory(
    MyNewFeatureUseCase,
    some_service=some_service,
    song_repository=song_repository,
)

# Add to MCP server factory
mcp_server = providers.Factory(
    AbletonMCPServer,
    # ... existing use cases ...
    my_new_feature_use_case=my_new_feature_use_case,
)
```

#### Step 6: Add MCP Tool Definition (mcp_server.py)

```python
# In __init__, add parameter:
def __init__(
    self,
    # ... existing ...
    my_new_feature_use_case: MyNewFeatureUseCase,
) -> None:
    # ... existing ...
    self._my_new_feature_use_case = my_new_feature_use_case

# In handle_list_tools(), add tool definition:
types.Tool(
    name="my_new_feature",
    description="Description for AI to understand the tool",
    inputSchema={
        "type": "object",
        "properties": {
            "required_param": {
                "type": "string",
                "description": "What this parameter does",
            },
            "optional_param": {
                "type": "integer",
                "description": "Optional parameter description",
            },
        },
        "required": ["required_param"],
    },
),

# In handle_call_tool(), add handler:
elif name == "my_new_feature":
    request = MyNewFeatureRequest(
        required_param=arguments["required_param"],
        optional_param=arguments.get("optional_param"),
    )
    result = await self._my_new_feature_use_case.execute(request)
```

#### Step 7: Add Tests (tests/unit/test_use_cases.py)

```python
class TestMyNewFeatureUseCase:
    async def test_success(self) -> None:
        # Arrange
        mock_service = Mock()
        mock_service.do_work = AsyncMock(return_value="result")
        song_repository = InMemorySongRepository()

        use_case = MyNewFeatureUseCase(mock_service, song_repository)
        request = MyNewFeatureRequest(required_param="test")

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.success is True
        assert result.data["result"] == "result"
        mock_service.do_work.assert_called_once_with("test")

    async def test_error_handling(self) -> None:
        # Test error cases
        pass
```

#### Step 8: Run Quality Checks

```bash
# Format code
black ableton_mcp/ tests/

# Lint
ruff check ableton_mcp/ tests/

# Type check
mypy ableton_mcp/

# Run tests
pytest tests/unit/ -v
```

---

## 6. Bug Hunting & Debugging Guide

### Common Issue Categories

#### Category 1: OSC Communication Issues

**Symptoms:**
- Connection timeouts
- Commands not executing in Ableton
- No response from Ableton

**Debugging Steps:**

1. **Check AbletonOSC is installed and enabled:**
   - Ableton Preferences > MIDI > Control Surface = AbletonOSC
   - Check Ableton's Log.txt for "AbletonOSC: Listening on port 11000"

2. **Verify ports are available:**
   ```bash
   # Windows
   netstat -an | findstr 11000

   # macOS/Linux
   lsof -i :11000
   ```

3. **Check gateway connection state:**
   ```python
   # In gateway.py, add logging
   logger.debug("Sending OSC", address=address, args=args)
   ```

4. **Verify correlator is receiving responses:**
   ```python
   # In correlator.py
   def handle_response(self, address: str, args: List[Any]) -> None:
       logger.debug("Received response", address=address, args=args)
   ```

**Common Fixes:**
- Increase timeout in `_request()` method
- Add delays between rapid OSC commands
- Restart Ableton to reset OSC script

#### Category 2: Use Case Logic Errors

**Symptoms:**
- Wrong data returned
- Validation errors
- Unexpected behavior

**Debugging Steps:**

1. **Check structured logs:**
   ```bash
   # View recent logs
   tail -f ableton_mcp.log | jq
   ```

2. **Add contextual logging:**
   ```python
   self._logger.debug(
       "Processing request",
       track_id=request.track_id,
       current_song=song.name if song else None,
   )
   ```

3. **Verify request DTOs:**
   ```python
   # Print request contents
   self._logger.info("Request received", request=vars(request))
   ```

#### Category 3: Dependency Injection Issues

**Symptoms:**
- `None` services
- Wrong instances injected
- Missing dependencies

**Debugging Steps:**

1. **Check container wiring:**
   ```python
   # In container.py, verify all dependencies are listed
   my_use_case = providers.Factory(
       MyUseCase,
       service=service,  # Is this defined above?
       repository=repository,  # Is this defined?
   )
   ```

2. **Verify import statements:**
   - Use case imported in container.py?
   - Request DTO imported in mcp_server.py?

3. **Test container resolution:**
   ```python
   container = Container()
   use_case = container.my_use_case()
   print(type(use_case))  # Should show MyUseCase
   ```

#### Category 4: MCP Protocol Issues

**Symptoms:**
- Tool not appearing in AI assistant
- Tool calls failing silently
- Wrong parameter types

**Debugging Steps:**

1. **Verify tool schema:**
   - JSON schema must be valid
   - Required parameters must be in "required" array
   - Types must match MCP expectations

2. **Check handler routing:**
   ```python
   # In handle_call_tool
   logger.info("Tool called", tool=name, arguments=arguments)
   ```

3. **Verify result formatting:**
   ```python
   # Check _format_result is handling your data type
   logger.debug("Formatting result", result_type=type(result.data))
   ```

### Debugging Workflow

```mermaid
flowchart TD
    A[Bug Reported] --> B{Where does it fail?}

    B -->|MCP Level| C[Check mcp_server.py logs]
    B -->|Use Case| D[Check use_cases.py logs]
    B -->|OSC Communication| E[Check gateway.py logs]
    B -->|Ableton| F[Check Ableton Log.txt]

    C --> G{Tool visible?}
    G -->|No| H[Check tool definition schema]
    G -->|Yes| I[Check handler routing]

    D --> J{Request valid?}
    J -->|No| K[Check DTO conversion]
    J -->|Yes| L[Check business logic]

    E --> M{Connected?}
    M -->|No| N[Check connection sequence]
    M -->|Yes| O[Check OSC message format]

    F --> P{Script loaded?}
    P -->|No| Q[Reinstall AbletonOSC]
    P -->|Yes| R[Check OSC command path]
```

### Log Analysis

The server uses JSON structured logging. Key fields:

| Field | Description |
|-------|-------------|
| `event` | Log message |
| `level` | info, warning, error |
| `logger` | Module name |
| `timestamp` | ISO 8601 timestamp |
| `tool` | MCP tool name (for tool calls) |
| `track_id`, `clip_id` | Context for operations |
| `error` | Error message |
| `error_code` | Exception error code |

**Useful jq queries:**

```bash
# Errors only
cat ableton_mcp.log | jq 'select(.level == "error")'

# Specific tool calls
cat ableton_mcp.log | jq 'select(.tool == "add_notes")'

# Recent errors with context
tail -100 ableton_mcp.log | jq 'select(.level == "error") | {event, error, error_code}'
```

---

## 7. AI Context Prompt

Use this prompt when asking an AI assistant to work on this codebase:

---

### Context Prompt for AI Assistants

```
# Ableton MCP Server - Development Context

## Project Overview
This is a Model Context Protocol (MCP) server that enables AI assistants to control Ableton Live via OSC. It follows Clean Architecture with strict layer separation.

## Architecture Summary
- **Interfaces Layer** (`interfaces/mcp_server.py`): MCP protocol handling, tool definitions
- **Application Layer** (`application/use_cases.py`): Business logic in use case classes
- **Domain Layer** (`domain/`): Entities, repository interfaces, service interfaces, gateway ports
- **Adapters Layer** (`adapters/service_adapters.py`): Bridge domain to infrastructure
- **Infrastructure Layer** (`infrastructure/`): OSC gateway, repository implementations, service implementations
- **Core Layer** (`core/`): Exceptions, logging

## Key Patterns
1. **Use Case Pattern**: Each operation is a class with `execute(Request) -> UseCaseResult`
2. **Repository Pattern**: Abstract interfaces in domain, implementations in infrastructure
3. **Gateway/Port Pattern**: Domain defines contracts (`AbletonGateway`), infrastructure implements (`AbletonOSCGateway`)
4. **Dependency Injection**: All wiring in `container.py` using `dependency-injector`
5. **Request/Response DTOs**: Dataclasses for inputs, `UseCaseResult` for outputs

## When Adding Features
1. Create Request DTO in `use_cases.py`
2. Create UseCase class in `use_cases.py`
3. Add service adapter method if needed (`service_adapters.py`)
4. Add gateway method if new OSC command (`ports.py` interface, `gateway.py` implementation)
5. Wire in DI container (`container.py`)
6. Add tool definition and handler in `mcp_server.py`
7. Add tests in `tests/unit/test_use_cases.py`

## Code Standards
- Python 3.11+ with strict mypy (`disallow_untyped_defs = true`)
- Line length: 100 (black + ruff)
- Pydantic models for domain entities
- Structlog for JSON structured logging
- All use cases must have structured logging for key operations

## OSC Communication
- Default ports: 11000 (send), 11001 (receive)
- Fire-and-forget commands: Use `_send()` method
- Request-response: Use `_request()` method with correlator
- Note format: [pitch, start, duration, velocity, mute] as flat list

## Testing
- pytest with asyncio_mode="auto"
- Mock external dependencies (OSC, services)
- Use `InMemory*Repository` fixtures for repository tests
- Coverage target: 85%

## File Locations for Common Tasks
- Add new MCP tool: `interfaces/mcp_server.py`, `application/use_cases.py`, `container.py`
- Add new OSC command: `domain/ports.py`, `infrastructure/osc/gateway.py`
- Add new entity: `domain/entities.py`
- Add business logic: `application/use_cases.py`, `infrastructure/services.py`
- Fix exception handling: `core/exceptions.py`

## Current MCP Tools
- `connect_ableton`: OSC connection
- `transport_control`: Play/stop/record
- `get_song_info`: Song metadata
- `track_operations`: Track manipulation
- `add_notes`: Add MIDI notes
- `get_clip_content`: Read MIDI notes from clip
- `analyze_harmony`: Key detection, chord suggestions
- `analyze_tempo`: BPM analysis
- `mix_analysis`: Mixing suggestions
- `arrangement_suggestions`: Structure suggestions
```

---

## Quick Reference

### Command Cheat Sheet

```bash
# Development
pip install -e ".[dev]"     # Install with dev dependencies
ableton-mcp                  # Run MCP server
python -m ableton_mcp.main  # Alternative run method

# Testing
pytest                       # All tests with coverage
pytest tests/unit/ -v       # Unit tests verbose
pytest -k "test_name"       # Specific test

# Code Quality
black ableton_mcp/ tests/   # Format
ruff check ableton_mcp/     # Lint
mypy ableton_mcp/           # Type check

# Logs
tail -f ableton_mcp.log     # Watch logs
cat ableton_mcp.log | jq    # Parse JSON logs
```

### Exception Hierarchy

```
AbletonMCPError (base)
├── ConnectionError
├── OSCCommunicationError
├── InvalidParameterError
├── MusicTheoryError
├── DeviceNotFoundError
├── TrackNotFoundError
├── ClipNotFoundError
├── ConfigurationError
└── ValidationError
```

### Environment Variables

```bash
ABLETON_MCP_LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
ABLETON_MCP_LOG_FILE=ableton_mcp.log
ABLETON_MCP_LOG_TO_CONSOLE=false
```

---

**Document Version**: 1.0
**Last Updated**: February 2026
**Maintainers**: Development Team
