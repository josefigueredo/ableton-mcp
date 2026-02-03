# Ableton Live MCP Server Examples

This directory contains runnable examples demonstrating how to use the Ableton Live MCP Server.

## Prerequisites

Before running these examples, ensure you have:

1. **Ableton Live** running with a project open
2. **AbletonOSC** remote script installed and enabled ([Installation Guide](https://github.com/ideoforms/AbletonOSC))
3. **ableton-mcp** package installed (`pip install -e .` from project root)

## Examples Overview

| File | Description | Difficulty |
|------|-------------|------------|
| `basic_usage.py` | Connect and control transport | Beginner |
| `song_info.py` | Retrieve song metadata and track information | Beginner |
| `track_operations.py` | Create, modify, and delete tracks | Intermediate |
| `add_notes.py` | Add MIDI notes with quantization and scale filtering | Intermediate |
| `harmony_analysis.py` | Analyze musical key and get chord suggestions | Intermediate |
| `full_workflow.py` | Complete production workflow automation | Advanced |

## Running Examples

Each example can be run directly:

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Run an example
python examples/basic_usage.py
```

## Example Output

When running `basic_usage.py`, you should see:

```
Connecting to Ableton Live...
Connected successfully!
Song Info: BPM=120.0, Time Signature=4/4
Starting playback...
Playback started!
Waiting 5 seconds...
Stopping playback...
Done!
```

## Troubleshooting

### Connection Refused
- Ensure Ableton Live is running
- Verify AbletonOSC is enabled in Live's MIDI preferences
- Check that ports 11000-11001 are not blocked

### OSC Timeout
- Restart Ableton Live
- Reload the AbletonOSC remote script
- Check firewall settings

### Import Errors
- Ensure you've installed the package: `pip install -e .`
- Verify your virtual environment is activated

## API Documentation

For complete API documentation, see:
- [README.md](../README.md) - Project overview and API reference
- [docs/](../docs/) - Detailed documentation

## Contributing

Have an example to share? We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
