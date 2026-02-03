# Ableton Live MCP Server

> 🎵 **Professional AI-Powered Music Production Assistant**

A sophisticated Model Context Protocol (MCP) server that transforms any AI assistant into an expert Ableton Live collaborator with deep music production knowledge and real-time DAW control.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Clean Architecture](https://img.shields.io/badge/architecture-clean-green.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
[![SOLID Principles](https://img.shields.io/badge/design-SOLID-orange.svg)](https://en.wikipedia.org/wiki/SOLID)
[![Type Hints](https://img.shields.io/badge/typing-strict-red.svg)](https://docs.python.org/3/library/typing.html)

## 🚀 Features

### Core Ableton Live Integration
- **Real-time OSC Communication** - Bidirectional control via AbletonOSC remote script
- **Complete Transport Control** - Play, stop, record, and transport management
- **Track Operations** - Volume, pan, mute, solo, arm, create, and delete tracks
- **Device & Plugin Control** - Parameter automation and preset management
- **Clip Management** - Fire, stop, create clips with intelligent MIDI note addition

### AI-Powered Music Intelligence
- **Harmonic Analysis** - Intelligent key detection and chord progression suggestions
- **Music Theory Engine** - Scale filtering, note quantization, and melody harmonization
- **Arrangement Intelligence** - Song structure analysis and improvement suggestions
- **Professional Mixing Guidance** - LUFS targeting, frequency analysis, and EQ suggestions
- **Tempo Optimization** - Genre-specific BPM suggestions and energy curve analysis

### Enterprise-Grade Architecture
- **Clean Architecture** with clear separation of concerns
- **SOLID Principles** implementation throughout
- **Dependency Injection** using dependency-injector
- **Comprehensive Testing** with 85%+ code coverage
- **Type Safety** with strict mypy configuration
- **Structured Logging** with rich formatting
- **Error Handling** with custom exception hierarchy

## 📋 Prerequisites

### Required Software
- **Ableton Live** (any recent version)
- **AbletonOSC Remote Script** - [Download and Installation Guide](https://github.com/ideoforms/AbletonOSC)
- **Python 3.11+** with pip

### System Requirements
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Network**: Local network access for OSC communication
- **Ports**: 11000-11001 available for OSC (configurable)

## 🔧 Installation

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ableton-live-mcp
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install package in development mode
pip install -e .
```

### 3. Install Development Dependencies (Optional)
```bash
pip install -e ".[dev]"
```

### 4. Configure AbletonOSC
1. Install the AbletonOSC remote script in Ableton Live
2. Enable the script in Live's MIDI preferences
3. Ensure OSC ports 11000-11001 are available

## 🎯 Quick Start

### Basic Usage
```bash
# Start the MCP server
ableton-mcp

# Or run directly
python -m ableton_mcp.main
```

### MCP Integration
The server provides these core tools:

#### Connection Management
```python
# Connect to Ableton Live
await mcp_client.call_tool("connect_ableton", {
    "host": "127.0.0.1",
    "send_port": 11000,
    "receive_port": 11001
})
```

#### Transport Control
```python
# Start playback
await mcp_client.call_tool("transport_control", {
    "action": "play"
})

# Get song information
song_info = await mcp_client.call_tool("get_song_info", {
    "include_tracks": True,
    "include_devices": True
})
```

#### Intelligent Music Creation
```python
# Add notes with music theory assistance
await mcp_client.call_tool("add_notes", {
    "track_id": 0,
    "clip_id": 0,
    "notes": [
        {"pitch": 60, "start": 0.0, "duration": 1.0},
        {"pitch": 64, "start": 1.0, "duration": 1.0}
    ],
    "quantize": True,
    "scale_filter": "major"
})

# Analyze harmony
harmony_analysis = await mcp_client.call_tool("analyze_harmony", {
    "notes": [60, 64, 67, 72],
    "suggest_progressions": True,
    "genre": "pop"
})
```

## 🏗️ Architecture

This project implements **Clean Architecture** with clear layer separation:

```
┌─────────────────────────────────────────┐
│              Interfaces                 │  ← MCP Protocol
│         (MCP Server, CLI)               │
├─────────────────────────────────────────┤
│               Adapters                  │  ← Service Integration
│       (OSC, Service Adapters)           │
├─────────────────────────────────────────┤
│              Application                │  ← Use Cases
│           (Business Logic)              │
├─────────────────────────────────────────┤
│               Domain                    │  ← Core Business
│     (Entities, Services, Repos)         │
├─────────────────────────────────────────┤
│            Infrastructure               │  ← External Concerns
│    (OSC Client, Repositories)           │
└─────────────────────────────────────────┘
```

### Key Design Patterns
- **Repository Pattern** for data access abstraction
- **Use Case Pattern** for business logic encapsulation
- **Adapter Pattern** for external service integration
- **Dependency Injection** for loose coupling
- **Command Pattern** for operation encapsulation

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=ableton_mcp --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Slow tests excluded
pytest -m "not slow"
```

### Type Checking
```bash
mypy ableton_mcp/
```

### Code Quality
```bash
# Format code
black ableton_mcp/ tests/

# Lint code
ruff ableton_mcp/ tests/
```

## 📚 API Reference

### Available Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `connect_ableton` | Connect to Ableton Live via OSC | `host`, `send_port`, `receive_port` |
| `transport_control` | Control playback and transport | `action` (play/stop/record) |
| `get_song_info` | Get comprehensive song information | `include_tracks`, `include_devices` |
| `track_operations` | Track manipulation and control | `action`, `track_id`, `value` |
| `add_notes` | Intelligent MIDI note addition | `track_id`, `clip_id`, `notes`, `quantize` |
| `analyze_harmony` | Music theory and chord analysis | `notes`, `suggest_progressions`, `genre` |
| `analyze_tempo` | Tempo optimization suggestions | `current_bpm`, `genre`, `energy_level` |
| `mix_analysis` | Professional mixing guidance | `analyze_levels`, `target_lufs`, `platform` |
| `arrangement_suggestions` | Song structure optimization | `song_length`, `genre`, `current_structure` |

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `CONNECTION_FAILED` | Cannot connect to Ableton Live | Check AbletonOSC installation and ports |
| `TRACK_NOT_FOUND` | Invalid track ID | Verify track exists and ID is correct |
| `CLIP_NOT_FOUND` | Invalid clip reference | Ensure clip slot has content |
| `VALIDATION_ERROR` | Invalid parameter values | Check parameter ranges and types |
| `OSC_COMMUNICATION_ERROR` | OSC message failed | Verify Ableton Live is running and responsive |

## 🔧 Configuration

### Environment Variables
```bash
# OSC Configuration
ABLETON_OSC_HOST=127.0.0.1
ABLETON_OSC_SEND_PORT=11000
ABLETON_OSC_RECEIVE_PORT=11001

# Logging Level
LOG_LEVEL=INFO

# Development Mode
DEBUG=False
```

### Custom Configuration
```python
from ableton_mcp.container import Container

# Configure container
container = Container()
container.config.osc.host.from_env("ABLETON_OSC_HOST", default="127.0.0.1")
container.config.osc.send_port.from_env("ABLETON_OSC_SEND_PORT", default=11000)
```

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 11000 11001
CMD ["ableton-mcp"]
```

### Systemd Service
```ini
[Unit]
Description=Ableton Live MCP Server
After=network.target

[Service]
Type=simple
User=music
ExecStart=/usr/local/bin/ableton-mcp
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests before committing
pytest && mypy ableton_mcp/
```

### Code Standards
- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking
- **pytest** for testing
- **Conventional Commits** for commit messages

### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass and coverage remains above 85%
5. Update documentation as needed
6. Commit using conventional commit format
7. Push to your branch and create a Pull Request

## 🐛 Troubleshooting

### Common Issues

**Connection Refused**
```bash
Error: [CONNECTION_FAILED] Failed to connect to Ableton Live
```
- Verify Ableton Live is running
- Check AbletonOSC remote script is enabled
- Ensure ports 11000-11001 are not blocked

**Import Errors**
```bash
ModuleNotFoundError: No module named 'ableton_mcp'
```
- Install in development mode: `pip install -e .`
- Verify virtual environment is activated

**OSC Timeout**
```bash
Error: [OSC_COMMUNICATION_ERROR] OSC message timeout
```
- Check Ableton Live is responsive
- Verify AbletonOSC script is properly loaded
- Restart both applications

## 📖 Documentation

### Additional Resources
- **[Clean Architecture Guide](docs/architecture.md)** - Detailed architecture explanation
- **[Music Theory Integration](docs/music-theory.md)** - Music intelligence features
- **[OSC Protocol Reference](docs/osc-protocol.md)** - Communication details
- **[Deployment Guide](docs/deployment.md)** - Production setup
- **[Contributing Guide](CONTRIBUTING.md)** - Development workflow

### API Documentation
Generate API docs:
```bash
sphinx-build -b html docs/ docs/_build/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ableton Live** - Industry-leading DAW platform
- **AbletonOSC** - OSC remote script enabling MCP integration
- **Model Context Protocol** - Standardized AI assistant integration
- **Clean Architecture** principles by Robert C. Martin
- **Music theory resources** from Berkeley, Coursera, and academic institutions

## 🔮 Roadmap

### Version 1.1.0
- [ ] Real-time audio analysis integration
- [ ] Advanced arrangement intelligence
- [ ] Hardware controller support
- [ ] Cloud collaboration features

### Version 1.2.0
- [ ] Machine learning model integration
- [ ] Advanced mixing automation
- [ ] Cross-DAW compatibility layer
- [ ] Performance optimization suite

---

<div align="center">

**Built with ❤️ for the music production community**

[Documentation](docs/) • [Contributing](CONTRIBUTING.md) • [Issues](../../issues) • [Discussions](../../discussions)

</div>