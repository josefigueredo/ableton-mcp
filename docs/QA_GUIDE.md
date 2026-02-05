# QA Guide

How this project implements tests and how to write new ones following established patterns.

## Test Directory Structure

```
tests/
├── conftest.py                          # Shared fixtures and TestContainer
├── unit/
│   ├── test_use_cases.py                # Use case business logic tests
│   ├── test_service_adapters.py         # Service adapter → gateway delegation tests
│   ├── test_osc_gateway.py             # Gateway → transport/correlator tests
│   ├── test_mcp_server.py              # MCP server initialization and formatting tests
│   └── test_container.py               # DI container wiring verification tests
├── integration/
│   └── test_full_workflow.py           # Multi-component workflow tests (currently skipped)
└── property/
    └── test_entities_properties.py     # Hypothesis property-based tests for domain entities
```

## pytest Configuration

Defined in `pyproject.toml`:

- **Async mode**: `asyncio_mode = "auto"` -- all `async def test_*` methods run automatically without `@pytest.mark.asyncio`
- **Test paths**: `tests/`
- **Coverage**: `--cov=ableton_mcp --cov-fail-under=75`
- **Markers**: `slow`, `integration`, `unit`, `benchmark`
- **Strict markers**: enabled -- only declared markers are allowed

### Running Tests

```bash
pytest                     # All tests with coverage
pytest tests/unit/         # Unit tests only
pytest -k "test_name"      # Specific test
pytest -m "not slow"       # Exclude slow tests
```

## Mocking Conventions

All tests use `unittest.mock`:

| Import | Used For |
|--------|----------|
| `Mock()` | Synchronous methods, return values |
| `Mock(spec=ClassName)` | Type-safe mocking (enforces interface) |
| `AsyncMock()` | Async methods (`async def`) |

**Key rule**: Always use `AsyncMock()` for any method that is `async def` in the real implementation. Use `Mock()` for synchronous methods and attributes.

---

## Test Patterns by Layer

### 1. Use Case Tests (`tests/unit/test_use_cases.py`)

Use cases are the core business logic. Each test creates inline mocks for the dependencies, constructs the use case, calls `execute()`, and asserts on the `UseCaseResult`.

**Pattern:**

```python
from unittest.mock import AsyncMock, Mock
from ableton_mcp.application.use_cases import SomeRequest, SomeUseCase

class TestSomeUseCase:
    """Test cases for some use case."""

    async def test_successful_action(self) -> None:
        """Test successful action."""
        # 1. Create mock dependencies inline
        mock_service = Mock()
        mock_service.do_something = AsyncMock()
        mock_repository = Mock()

        # 2. Create use case with mocked dependencies
        use_case = SomeUseCase(mock_service, mock_repository)

        # 3. Create request dataclass
        request = SomeRequest(action="do_something", value=42)

        # 4. Execute and assert
        result = await use_case.execute(request)

        assert result.success is True
        assert "expected message" in result.message
        mock_service.do_something.assert_called_once_with(42)

    async def test_failure_case(self) -> None:
        """Test failure handling."""
        mock_service = Mock()
        mock_repository = Mock()

        use_case = SomeUseCase(mock_service, mock_repository)
        request = SomeRequest(action="invalid")

        result = await use_case.execute(request)

        assert result.success is False
        assert "error description" in result.message
```

**What to test:**
- Each action the use case supports (success path)
- Missing required parameters (e.g., `scene_id is required`)
- Invalid actions (`Unknown action`)
- Entity not found (`Track 999 not found`, `No active song`)
- Edge cases specific to the action

**Real example** (from `TestSceneOperationsUseCase`):

```python
async def test_fire_scene(self) -> None:
    mock_service = Mock()
    mock_service.fire_scene = AsyncMock()
    mock_repository = InMemorySongRepository()

    use_case = SceneOperationsUseCase(mock_service, mock_repository)
    request = SceneOperationRequest(action="fire", scene_id=0)

    result = await use_case.execute(request)

    assert result.success is True
    assert "Fired scene 0" in result.message
    mock_service.fire_scene.assert_called_once_with(0)
```

**When the use case needs a song in the repository** (common for track/clip operations):

```python
async def test_operation_requiring_song(self) -> None:
    song_repository = InMemorySongRepository()
    service = Mock()
    service.some_method = AsyncMock()

    # Setup: song with track must exist
    song = Song(name="Test Song")
    track = Track(name="Track", track_type=TrackType.MIDI)
    song.add_track(track)
    await song_repository.save_song(song)

    use_case = SomeUseCase(service, song_repository)
    request = SomeRequest(action="do_something", track_id=0)

    result = await use_case.execute(request)
    assert result.success is True
```

---

### 2. Service Adapter Tests (`tests/unit/test_service_adapters.py`)

Service adapters are thin wrappers that delegate to the gateway. Each test mocks the gateway, creates the adapter, calls the method, and verifies the correct gateway method was called with correct arguments.

**Pattern:**

```python
from unittest.mock import AsyncMock, Mock
from ableton_mcp.adapters.service_adapters import SomeService
from ableton_mcp.domain.ports import AbletonGateway

class TestSomeService:
    """Test cases for some service adapter."""

    async def test_method_delegates_to_gateway(self) -> None:
        """Test that method delegates to gateway."""
        # 1. Mock gateway with spec for type safety
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.gateway_method = AsyncMock(return_value=expected_value)

        # 2. Create service with mock gateway
        service = SomeService(gateway=mock_gateway)

        # 3. Call service method
        result = await service.service_method(arg1, arg2)

        # 4. Assert gateway was called correctly
        assert result == expected_value
        mock_gateway.gateway_method.assert_called_once_with(arg1, arg2)

    async def test_fire_and_forget_method(self) -> None:
        """Test fire-and-forget method."""
        mock_gateway = Mock(spec=AbletonGateway)
        mock_gateway.gateway_method = AsyncMock()

        service = SomeService(gateway=mock_gateway)
        await service.fire_and_forget_method(arg)

        mock_gateway.gateway_method.assert_called_once_with(arg)
```

**What to test:**
- Every public method on the adapter delegates to the correct gateway method
- Arguments are passed through correctly
- Return values are returned correctly
- For composite methods (like `get_scene_info` that calls multiple gateway methods), verify all calls and the assembled result

**Real example** (from `TestAbletonSceneService`):

```python
async def test_get_scene_info(self) -> None:
    mock_gateway = Mock(spec=AbletonGateway)
    mock_gateway.get_scene_name = AsyncMock(return_value="Intro")
    mock_gateway.get_scene_color = AsyncMock(return_value=5)

    service = AbletonSceneService(gateway=mock_gateway)
    result = await service.get_scene_info(0)

    assert result == {"scene_id": 0, "name": "Intro", "color": 5}
```

---

### 3. Gateway Tests (`tests/unit/test_osc_gateway.py`)

Gateway tests verify OSC message sending and response parsing. They mock `AsyncOSCTransport` and `OSCCorrelator`.

**Pattern:**

```python
import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock
from ableton_mcp.infrastructure.osc.gateway import AbletonOSCGateway
from ableton_mcp.infrastructure.osc.transport import AsyncOSCTransport
from ableton_mcp.infrastructure.osc.correlator import OSCCorrelator

class TestAbletonOSCGateway:

    @pytest.fixture
    def mock_transport(self) -> Mock:
        transport = Mock(spec=AsyncOSCTransport)
        transport.connect = AsyncMock()
        transport.disconnect = AsyncMock()
        transport.is_connected.return_value = True
        transport.send = Mock()
        return transport

    @pytest.fixture
    def mock_correlator(self) -> Mock:
        correlator = Mock(spec=OSCCorrelator)
        correlator.expect_response = AsyncMock()
        correlator.handle_response = Mock()
        correlator.cancel_all = Mock()
        return correlator
```

**For fire-and-forget operations** (no response expected):

```python
async def test_fire_and_forget(self, mock_transport, mock_correlator) -> None:
    gateway = AbletonOSCGateway(
        transport=mock_transport,
        correlator=mock_correlator,
    )

    await gateway.start_playing()

    mock_transport.send.assert_called_with("/live/song/start_playing", [])
```

**For request-response operations** (expects a response via correlator):

```python
async def test_request_response(self, mock_transport, mock_correlator) -> None:
    # 1. Create a resolved future with the expected response
    future: asyncio.Future[list[Any]] = asyncio.get_event_loop().create_future()
    future.set_result([120.0])
    mock_correlator.expect_response.return_value = future

    gateway = AbletonOSCGateway(
        transport=mock_transport,
        correlator=mock_correlator,
        default_timeout=1.0,
    )

    # 2. Call the method
    tempo = await gateway.get_tempo()

    # 3. Assert result and OSC path
    assert tempo == 120.0
    mock_transport.send.assert_called_with("/live/song/get/tempo", [])
    mock_correlator.expect_response.assert_called_with("/live/song/get/tempo")
```

**What to test:**
- Correct OSC path and arguments for each method
- Response parsing (extract correct value from response list)
- Empty response handling (raise `OSCCommunicationError`)
- Disconnected state (raise `OSCCommunicationError("Not connected")`)
- Input validation (e.g., tempo range 20-999, volume 0-1)
- Timeout handling

---

### 4. MCP Server Tests (`tests/unit/test_mcp_server.py`)

MCP server tests verify initialization, result formatting, and tool registration. All use cases are mocked.

**Pattern:**

```python
from unittest.mock import AsyncMock, Mock
from ableton_mcp.interfaces.mcp_server import AbletonMCPServer

@pytest.fixture
def mock_use_cases() -> dict:
    """Create mock use cases for testing."""
    return {
        "connect_use_case": Mock(),
        "transport_use_case": Mock(),
        "song_info_use_case": Mock(),
        # ... ALL use cases must be included
        "device_ops_use_case": Mock(),
    }

@pytest.fixture
def mcp_server(mock_use_cases: dict) -> AbletonMCPServer:
    return AbletonMCPServer(
        connect_use_case=mock_use_cases["connect_use_case"],
        transport_use_case=mock_use_cases["transport_use_case"],
        # ... ALL use cases must be passed
    )
```

**When adding a new use case, you MUST update both fixtures** (`mock_use_cases` and `mcp_server`) in this file, otherwise all tests will fail.

**What to test:**
- Server initialization
- `_format_result()` for success/failure/error codes
- `_format_data()` for different data shapes (song info, harmony, tempo, clips, generic dicts)
- Tool call handling via use case mocks

---

### 5. Container Tests (`tests/unit/test_container.py`)

Container tests verify that all DI providers are wired correctly.

**Pattern:**

```python
from ableton_mcp.container import Container

class TestContainer:
    def test_provider_exists(self) -> None:
        container = Container()
        assert container.some_provider is not None

    def test_singleton_behavior(self) -> None:
        container = Container()
        instance1 = container.some_singleton()
        instance2 = container.some_singleton()
        assert instance1 is instance2

    def test_factory_behavior(self) -> None:
        container = Container()
        instance1 = container.some_factory()
        instance2 = container.some_factory()
        assert instance1 is not instance2
```

---

### 6. Property-Based Tests (`tests/property/test_entities_properties.py`)

Property-based tests use Hypothesis to verify invariants across many random inputs. They test domain entities only.

**Custom strategies** (reuse these, do not create new ones):

```python
from hypothesis import strategies as st

midi_pitch = st.integers(min_value=0, max_value=127)
midi_velocity = st.integers(min_value=1, max_value=127)
beat_time = st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
positive_duration = st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False)
tempo = st.floats(min_value=20.0, max_value=999.0, allow_nan=False, allow_infinity=False)
volume_pan = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
pan_value = st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False)
pitch_class = st.integers(min_value=0, max_value=11)
confidence = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
```

**Pattern:**

```python
from hypothesis import given

class TestEntityProperties:
    @given(pitch=midi_pitch)
    def test_invariant_holds(self, pitch: int) -> None:
        """Property: describe the invariant."""
        entity = Entity(pitch=pitch)
        assert invariant_condition(entity)
```

Property tests are **synchronous** (not async) since they test pure domain logic.

---

### 7. Integration Tests (`tests/integration/test_full_workflow.py`)

Integration tests verify multi-component workflows using `TestContainer` from `conftest.py`. They are currently skipped and marked with `@pytest.mark.integration`.

**Pattern:**

```python
@pytest.mark.integration
class TestWorkflow:
    async def test_full_workflow(self, test_container: TestContainer) -> None:
        use_case = test_container.some_use_case()
        repo = test_container.some_repository()

        # Setup state
        await repo.save_song(song)

        # Execute workflow steps
        result = await use_case.execute(request)
        assert result.success
```

---

## Shared Fixtures (`tests/conftest.py`)

### `create_mock_gateway()`

Factory function that returns a `Mock(spec=AbletonGateway)` with all async methods pre-configured as `AsyncMock()`. Used by `TestContainer`.

### `TestContainer`

DI container for tests. Uses `create_mock_gateway` as the gateway and real repositories/services. Provides pre-wired use cases.

### Entity Fixtures

| Fixture | Returns | Description |
|---------|---------|-------------|
| `sample_song` | `Song` | Song with 2 tracks (MIDI + Audio), 120 BPM |
| `sample_track` | `Track` | MIDI track with Operator device |
| `sample_clip` | `Clip` | MIDI clip with 4 notes (C4, E4, G4, C5) |
| `sample_notes` | `list[Note]` | 4 notes: C4, E4, G4, C5 |
| `c_major_notes` | `list[int]` | MIDI pitches for C major scale |
| `mock_gateway` | `Mock` | Standalone mock gateway |

---

## Adding Tests for New Functionality

### When adding a new use case

1. **`tests/unit/test_use_cases.py`**: Add a new `TestXxxUseCase` class
   - Test each action (success path)
   - Test missing required parameters
   - Test invalid actions
   - Test entity-not-found scenarios

2. **`tests/unit/test_service_adapters.py`**: Add a new `TestXxxService` class
   - Test every public method delegates to the correct gateway method
   - Test arguments pass through correctly
   - Test return values

3. **`tests/unit/test_mcp_server.py`**: Update both `mock_use_cases` and `mcp_server` fixtures
   - Add the new use case key to the dict
   - Add the new keyword argument to `AbletonMCPServer()`

4. **`tests/unit/test_container.py`**: Add assertion for the new provider (if a new provider was added to `container.py`)

### When adding a new gateway method

Add tests in `tests/unit/test_osc_gateway.py`:
- For fire-and-forget: verify `mock_transport.send` is called with the correct OSC path and args
- For request-response: create a resolved `asyncio.Future`, verify the response is parsed correctly
- Add empty-response test for request-response methods
- Add disconnected-state test if the method doesn't share the common `_send`/`_request` path

### When adding a new domain entity

Add property-based tests in `tests/property/test_entities_properties.py`:
- Use existing Hypothesis strategies (do not create new ones unless the value domain is genuinely new)
- Test invariants: "for any valid input, this property holds"
- Keep tests synchronous

---

## Code Quality Checks

Run all of these before committing:

```bash
black ableton_mcp/ tests/       # Format code
ruff check ableton_mcp/ tests/  # Lint
mypy ableton_mcp/               # Type checking
pytest                          # Tests with coverage
```

All four must pass with zero errors.
