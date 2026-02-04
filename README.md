# Ableton Live MCP Server

> 🎵 **Professional AI-Powered Music Production Assistant**

A sophisticated Model Context Protocol (MCP) server that transforms any AI assistant into an expert Ableton Live collaborator with deep music production knowledge and real-time DAW control.

[![Tests](https://github.com/josefigueredo/ableton-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/josefigueredo/ableton-mcp/actions/workflows/tests.yml)
[![Lint](https://github.com/josefigueredo/ableton-mcp/actions/workflows/lint.yml/badge.svg)](https://github.com/josefigueredo/ableton-mcp/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/josefigueredo/ableton-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/josefigueredo/ableton-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue.svg)](https://github.com/josefigueredo/ableton-mcp/pkgs/container/ableton-mcp)

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

Choose your preferred installation method:

### Option 1: Docker (Recommended)

The easiest way to get started. No Python installation required.

```bash
# Pull and run (Linux)
docker run --network host ghcr.io/josefigueredo/ableton-mcp:latest

# Pull and run (macOS / Windows)
docker run -p 11000:11000/udp -p 11001:11001/udp \
  -e ABLETON_OSC_HOST=host.docker.internal \
  ghcr.io/josefigueredo/ableton-mcp:latest
```

Or use Docker Compose:

```bash
# Download docker-compose.yml and run
curl -O https://raw.githubusercontent.com/josefigueredo/ableton-mcp/main/docker-compose.yml
docker-compose up
```

### Option 2: Python (For Development)

Best for debugging and contributing to the project.

```bash
# Clone the repository
git clone https://github.com/josefigueredo/ableton-mcp.git
cd ableton-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install package in development mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Configure AbletonOSC (Required for both methods)

1. Download [AbletonOSC](https://github.com/ideoforms/AbletonOSC)
2. Copy the `AbletonOSC` folder to your Ableton MIDI Remote Scripts directory:
   - **Windows**: `C:\ProgramData\Ableton\Live x.x\Resources\MIDI Remote Scripts\`
   - **macOS**: `/Applications/Ableton Live x.x/Contents/App-Resources/MIDI Remote Scripts/`
3. Restart Ableton Live
4. Go to **Preferences > Link/Tempo/MIDI** and select `AbletonOSC` in a Control Surface slot

## 🎯 Quick Start

### Starting the Server

**Docker:**

```bash
# Linux (uses host networking)
docker run --network host ghcr.io/josefigueredo/ableton-mcp:latest

# macOS / Windows
docker run -p 11000:11000/udp -p 11001:11001/udp \
  -e ABLETON_OSC_HOST=host.docker.internal \
  ghcr.io/josefigueredo/ableton-mcp:latest
```

**Python:**

```bash
# Start the MCP server
ableton-mcp

# Or run directly (useful for debugging)
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

| Tool                      | Description                        | Key Parameters                              |
| ------------------------- | ---------------------------------- | ------------------------------------------- |
| `connect_ableton`         | Connect to Ableton Live via OSC    | `host`, `send_port`, `receive_port`         |
| `transport_control`       | Control playback and transport     | `action` (play/stop/record)                 |
| `get_song_info`           | Get comprehensive song information | `include_tracks`, `include_devices`         |
| `track_operations`        | Track manipulation and control     | `action`, `track_id`, `value`               |
| `add_notes`               | Intelligent MIDI note addition     | `track_id`, `clip_id`, `notes`, `quantize`  |
| `analyze_harmony`         | Music theory and chord analysis    | `notes`, `suggest_progressions`, `genre`    |
| `analyze_tempo`           | Tempo optimization suggestions     | `current_bpm`, `genre`, `energy_level`      |
| `mix_analysis`            | Professional mixing guidance       | `analyze_levels`, `target_lufs`, `platform` |
| `arrangement_suggestions` | Song structure optimization        | `song_length`, `genre`, `current_structure` |

### Error Codes

| Code                      | Description                    | Resolution                                    |
| ------------------------- | ------------------------------ | --------------------------------------------- |
| `CONNECTION_FAILED`       | Cannot connect to Ableton Live | Check AbletonOSC installation and ports       |
| `TRACK_NOT_FOUND`         | Invalid track ID               | Verify track exists and ID is correct         |
| `CLIP_NOT_FOUND`          | Invalid clip reference         | Ensure clip slot has content                  |
| `VALIDATION_ERROR`        | Invalid parameter values       | Check parameter ranges and types              |
| `OSC_COMMUNICATION_ERROR` | OSC message failed             | Verify Ableton Live is running and responsive |

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

## 🔒 Security

### Network Security Considerations

This application uses **OSC (Open Sound Control)** over UDP for communication with Ableton Live. Important security notes:

- **Local use only**: OSC communication is unencrypted and designed for local DAW control
- **Default binding**: The server binds to `127.0.0.1` (localhost) by default
- **Do not expose to untrusted networks**: Never expose ports 11000-11001 to the internet or untrusted networks
- **Firewall configuration**: Ensure your firewall restricts OSC ports to localhost only

```bash
# Example: Linux firewall rule to restrict OSC ports to localhost
sudo iptables -A INPUT -p udp --dport 11000:11001 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 11000:11001 -j DROP
```

### Security Scanning

The project includes automated security scanning in CI/CD:

- **pip-audit**: Weekly dependency vulnerability scanning
- **CodeQL**: Static code analysis for security issues

For a complete security assessment, see [docs/SECURITY_ASSESSMENT.md](docs/SECURITY_ASSESSMENT.md).

## 🚀 Production Deployment

### Docker (Recommended)

The official Docker image is available on GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/josefigueredo/ableton-mcp:latest

# Run with environment configuration
docker run -d \
  --name ableton-mcp \
  --restart unless-stopped \
  --network host \
  -e ABLETON_MCP_LOG_LEVEL=INFO \
  ghcr.io/josefigueredo/ableton-mcp:latest
```

**Using Docker Compose:**

```yaml
# docker-compose.yml
services:
  ableton-mcp:
    image: ghcr.io/josefigueredo/ableton-mcp:latest
    network_mode: host # Linux
    # For macOS/Windows, use ports instead:
    # ports:
    #   - "11000:11000/udp"
    #   - "11001:11001/udp"
    environment:
      - ABLETON_OSC_HOST=127.0.0.1
      - ABLETON_MCP_LOG_LEVEL=INFO
    restart: unless-stopped
```

### Systemd Service (Linux)

For running directly on the host without Docker:

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
Environment=ABLETON_MCP_LOG_LEVEL=INFO

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

- **[Claude](https://claude.ai)** by Anthropic - AI co-creator and pair programming partner
- **[GitHub Speckit](https://github.com/github/speckit)** - Spec-driven development helper
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
