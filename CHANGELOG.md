# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Scene operations MCP tool (fire, create, delete, rename, recolor scenes)
- Clip operations MCP tool (get/set name, length, loop start/end, fire, stop, create, delete, has_clip)
- Song properties MCP tool (set swing, metronome, overdub, loop, loop start/length, tempo)
- Return track operations MCP tool (create, get info, set volume/pan/mute/name for return tracks; get/set master volume/pan)
- Device operations MCP tool (get device info, toggle active, get/set individual parameter value/name/display value/min/max)
- Extended transport control with undo, redo, continue, stop all clips, tap tempo, capture MIDI, session record, jump by/to, next/prev cue
- Extended track operations with color, sends, stop all clips, duplicate
- Extended get_song_info with swing, metronome, overdub, loop, song length, record mode, session record, punch in/out, num return tracks
- Connection verification via /live/test endpoint
- Application version query
- View/navigation support (get/set selected track and scene)
- Track creation feature for MCP
- Comprehensive test suite with 85%+ coverage
- Open source documentation (LICENSE, CODE_OF_CONDUCT, SECURITY, CONTRIBUTING)
- GitHub Actions CI/CD pipelines (tests, lint, release)
- Issue and PR templates
- Structured JSON logging with file rotation

### Changed
- Improved code organization following Clean Architecture principles

## [1.0.0] - 2026-02-03

### Added
- Initial release of Ableton Live MCP Server
- Real-time OSC communication with Ableton Live via AbletonOSC
- Complete transport control (play, stop, record)
- Track operations (volume, pan, mute, solo, arm, create, delete)
- Device and plugin parameter control
- Clip management and MIDI note addition
- Music theory engine with scale filtering and quantization
- Harmonic analysis with key detection and chord progression suggestions
- Tempo analysis with genre-specific BPM suggestions
- Clean Architecture implementation with dependency injection
- Comprehensive type hints with strict mypy configuration
- Pydantic models for domain entities with validation

### Technical Details
- Python 3.11+ support
- MCP protocol integration for AI assistant compatibility
- OSC ports: 11000 (send), 11001 (receive)
- Dependency injection using dependency-injector
- Structlog for JSON formatted logging

---

## Release Notes Format

### Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

[Unreleased]: https://github.com/josefigueredo/ableton-mcp/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/josefigueredo/ableton-mcp/releases/tag/v1.0.0
