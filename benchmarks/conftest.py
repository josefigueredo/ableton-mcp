"""Pytest configuration for benchmarks."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure benchmark markers."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a performance benchmark"
    )
