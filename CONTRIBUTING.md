# Contributing to Ableton Live MCP Server

Thank you for your interest in contributing to the Ableton Live MCP Server! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to <josefigueredo@gmail.com>.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your changes
5. Make your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ableton-mcp.git
cd ableton-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running the Application

```bash
# Start the MCP server
ableton-mcp

# Or run directly
python -m ableton_mcp.main
```

## Code Standards

### Formatting

We use **Black** for code formatting with a line length of 100 characters.

```bash
# Format code
black ableton_mcp/ tests/

# Check formatting without modifying
black --check ableton_mcp/ tests/
```

### Linting

We use **Ruff** for linting.

```bash
# Run linter
ruff check ableton_mcp/ tests/

# Auto-fix issues
ruff check --fix ableton_mcp/ tests/
```

### Type Checking

We use **mypy** with strict configuration.

```bash
# Run type checker
mypy ableton_mcp/
```

### Documentation

- Use Google-style docstrings for all public functions, classes, and methods
- Keep docstrings concise but informative
- Include type hints for all function parameters and return values

Example:

```python
def analyze_key(self, notes: list[Note]) -> list[MusicKey]:
    """Analyze the musical key of given notes.

    Args:
        notes: List of Note objects to analyze.

    Returns:
        List of MusicKey objects sorted by confidence.

    Raises:
        MusicTheoryError: If note data is invalid.
    """
```

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ableton_mcp --cov-report=html

# Run specific test file
pytest tests/unit/test_use_cases.py

# Run tests matching a pattern
pytest -k "test_transport"
```

### Coverage Requirements

- Minimum coverage: **85%**
- All new code must include tests
- Coverage should not decrease with new changes

### Test Guidelines

1. **Unit tests** should be fast and isolated
2. **Integration tests** should test component interactions
3. Use **pytest fixtures** for common setup
4. Use **async tests** for async functions (`pytest-asyncio`)
5. Mock external dependencies (OSC, file system, etc.)

Example test:

```python
import pytest
from ableton_mcp.application.use_cases import TransportControlUseCase

class TestTransportControl:
    @pytest.fixture
    def use_case(self, mock_gateway):
        return TransportControlUseCase(gateway=mock_gateway)

    async def test_play_starts_playback(self, use_case, mock_gateway):
        request = TransportControlRequest(action="play")

        result = await use_case.execute(request)

        assert result.success is True
        mock_gateway.start_playback.assert_called_once()
```

## Commit Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring without feature changes
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system or dependency changes
- `ci`: CI configuration changes
- `chore`: Other changes that don't modify src or test files

### Examples

```bash
feat(harmony): add chord progression suggestions for jazz genre

fix(osc): handle connection timeout gracefully

docs(readme): update installation instructions

test(use-cases): add tests for track operations
```

## Pull Request Process

### Before Submitting

1. **Update your fork** with the latest changes from upstream
2. **Run all checks** locally:
   ```bash
   black --check ableton_mcp/ tests/
   ruff check ableton_mcp/ tests/
   mypy ableton_mcp/
   pytest
   ```
3. **Update documentation** if needed
4. **Add tests** for new functionality

### PR Template

When creating a PR, include:

- Clear description of changes
- Type of change (bug fix, feature, etc.)
- Testing performed
- Checklist of requirements

### Review Process

1. At least one maintainer approval required
2. All CI checks must pass
3. Coverage must remain at or above 85%
4. No unresolved conversations

### After Merge

- Delete your feature branch
- Update your local main branch
- Celebrate your contribution!

## Issue Guidelines

### Bug Reports

Include:

1. **Environment**: Python version, OS, Ableton Live version
2. **Steps to reproduce**: Clear, numbered steps
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Error messages**: Full stack traces if available
6. **Screenshots**: If applicable

### Feature Requests

Include:

1. **Problem statement**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches you've thought about
4. **Additional context**: Use cases, examples, mockups

### Questions

For general questions:

1. Check existing documentation first
2. Search existing issues
3. Use GitHub Discussions if available
4. Tag with `question` label

## Architecture Guidelines

This project follows **Clean Architecture**. When contributing:

1. **Domain layer**: Core business logic, no external dependencies
2. **Application layer**: Use cases, orchestration
3. **Infrastructure layer**: External concerns (OSC, databases)
4. **Interfaces layer**: MCP protocol, CLI

### Adding New Features

1. Start with domain entities if needed
2. Define repository interfaces in domain
3. Implement use cases in application layer
4. Add infrastructure implementations
5. Wire everything in the container

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers at <josefigueredo@gmail.com>

---

Thank you for contributing to Ableton Live MCP Server!
