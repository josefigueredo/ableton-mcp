# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ableton Live MCP Server - A Model Context Protocol server that enables AI assistants to control Ableton Live via OSC and provide music production intelligence. Requires Ableton Live with [AbletonOSC](https://github.com/ideoforms/AbletonOSC) remote script installed.

## Commands

```bash
# Install dependencies
pip install -e .           # Production
pip install -e ".[dev]"    # Development (includes testing/linting tools)

# Run the MCP server
ableton-mcp                # Via entry point
python -m ableton_mcp.main # Direct execution

# Testing
pytest                     # Run all tests with coverage
pytest tests/unit/         # Unit tests only
pytest -m "not slow"       # Exclude slow tests
pytest -k "test_name"      # Run specific test by name

# Code quality
black ableton_mcp/ tests/  # Format code
ruff ableton_mcp/ tests/   # Lint
mypy ableton_mcp/          # Type checking

# Pre-commit (runs black, ruff, mypy, pytest)
pre-commit install         # Install hooks
pre-commit run --all-files # Run manually
```

## Architecture

This project follows **Clean Architecture** with strict layer separation:

```
ableton_mcp/
├── interfaces/         # MCP protocol layer (mcp_server.py)
│   └── Handles MCP tool definitions and request routing
├── adapters/           # Service adapters bridging domain to infrastructure
│   └── service_adapters.py - Ableton-specific service implementations
├── application/        # Use cases (business logic orchestration)
│   └── use_cases.py - All use case classes (ConnectToAbleton, TransportControl, etc.)
├── domain/             # Core business entities and contracts
│   ├── entities.py - Song, Track, Clip, Note, Device, etc.
│   ├── repositories.py - Repository interfaces (abstract)
│   └── services.py - Domain service interfaces
├── infrastructure/     # External concerns implementation
│   ├── osc_client.py - OSC communication with Ableton
│   ├── repositories.py - In-memory repository implementations
│   └── services.py - MusicTheoryService, TempoAnalysisService implementations
├── core/               # Shared exceptions and utilities
└── container.py        # Dependency injection (dependency-injector)
```

**Key patterns:**
- **Dependency Injection**: All wiring in `container.py` using `dependency-injector`
- **Use Case Pattern**: Each operation is a distinct use case class with `execute()` method returning `UseCaseResult`
- **Repository Pattern**: Abstract interfaces in domain, implementations in infrastructure
- **Request/Response DTOs**: Dataclasses like `TransportControlRequest`, `AddNotesRequest` for use case inputs

## MCP Tools

The server exposes these tools to AI assistants:
- `connect_ableton` - OSC connection (host, ports)
- `transport_control` - Play/stop/record
- `get_song_info` - Song metadata, tracks, devices
- `track_operations` - Volume, pan, mute, solo, arm, create/delete
- `add_notes` - MIDI notes with quantization and scale filtering
- `analyze_harmony` - Key detection, chord progression suggestions
- `analyze_tempo` - BPM analysis and genre-specific suggestions

## Testing

Tests use `pytest-asyncio` with `asyncio_mode = "auto"`. Fixtures in `tests/conftest.py` provide:
- `TestContainer` with mocked OSC client and real repositories
- `sample_song`, `sample_track`, `sample_clip`, `sample_notes` fixtures

Coverage requirement: 85% minimum (enforced by pytest-cov).

## OSC Communication

Default ports: 11000 (send), 11001 (receive). The `OSCClient` in `infrastructure/osc_client.py` handles bidirectional communication with AbletonOSC remote script.

## Logging

JSON-formatted structured logging with file output by default. Configuration via environment variables:

```bash
# Environment variables
ABLETON_MCP_LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR, CRITICAL
ABLETON_MCP_LOG_FILE=ableton_mcp.log  # Log file path
ABLETON_MCP_LOG_TO_CONSOLE=false      # Also output to console (true/false)
```

Log files use rotation (10MB max, 5 backups). Example log entry:
```json
{"event": "Connected to Ableton Live", "host": "127.0.0.1", "logger": "gateway", "level": "info", "timestamp": "2024-01-15T10:30:00.123Z"}
```

## Code Standards

- Python 3.11+ with strict mypy (`disallow_untyped_defs = true`)
- Line length: 100 (black + ruff)
- Pydantic models for domain entities with validation
- Structlog for JSON structured logging to file
