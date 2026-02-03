"""Metrics collection for production monitoring.

Provides Prometheus-compatible metrics for:
- Request counts and latencies
- Connection status
- Error rates
- Resource usage

Note: This module provides a lightweight metrics implementation.
For full Prometheus integration, install prometheus-client and
use the PrometheusMetricsExporter class.
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Generator

logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class MetricValue:
    """A single metric value with metadata."""

    name: str
    type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    help_text: str = ""


class Counter:
    """A counter metric that only increases."""

    def __init__(self, name: str, help_text: str = "") -> None:
        """Initialize counter.

        Args:
            name: Metric name.
            help_text: Description of the metric.
        """
        self.name = name
        self.help_text = help_text
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment the counter.

        Args:
            value: Amount to increment by (must be positive).
            **labels: Label key-value pairs.
        """
        if value < 0:
            raise ValueError("Counter can only be incremented")
        key = tuple(sorted(labels.items()))
        self._values[key] += value

    def get(self, **labels: str) -> float:
        """Get current counter value.

        Args:
            **labels: Label key-value pairs.

        Returns:
            Current counter value.
        """
        key = tuple(sorted(labels.items()))
        return self._values[key]

    def collect(self) -> list[MetricValue]:
        """Collect all metric values.

        Returns:
            List of MetricValue instances.
        """
        return [
            MetricValue(
                name=self.name,
                type=MetricType.COUNTER,
                value=value,
                labels=dict(labels),
                help_text=self.help_text,
            )
            for labels, value in self._values.items()
        ]


class Gauge:
    """A gauge metric that can increase or decrease."""

    def __init__(self, name: str, help_text: str = "") -> None:
        """Initialize gauge.

        Args:
            name: Metric name.
            help_text: Description of the metric.
        """
        self.name = name
        self.help_text = help_text
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)

    def set(self, value: float, **labels: str) -> None:
        """Set the gauge value.

        Args:
            value: New value.
            **labels: Label key-value pairs.
        """
        key = tuple(sorted(labels.items()))
        self._values[key] = value

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment the gauge.

        Args:
            value: Amount to increment by.
            **labels: Label key-value pairs.
        """
        key = tuple(sorted(labels.items()))
        self._values[key] += value

    def dec(self, value: float = 1.0, **labels: str) -> None:
        """Decrement the gauge.

        Args:
            value: Amount to decrement by.
            **labels: Label key-value pairs.
        """
        key = tuple(sorted(labels.items()))
        self._values[key] -= value

    def get(self, **labels: str) -> float:
        """Get current gauge value.

        Args:
            **labels: Label key-value pairs.

        Returns:
            Current gauge value.
        """
        key = tuple(sorted(labels.items()))
        return self._values[key]

    def collect(self) -> list[MetricValue]:
        """Collect all metric values.

        Returns:
            List of MetricValue instances.
        """
        return [
            MetricValue(
                name=self.name,
                type=MetricType.GAUGE,
                value=value,
                labels=dict(labels),
                help_text=self.help_text,
            )
            for labels, value in self._values.items()
        ]


class Histogram:
    """A histogram metric for measuring distributions."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(
        self,
        name: str,
        help_text: str = "",
        buckets: tuple[float, ...] | None = None,
    ) -> None:
        """Initialize histogram.

        Args:
            name: Metric name.
            help_text: Description of the metric.
            buckets: Bucket boundaries for the histogram.
        """
        self.name = name
        self.help_text = help_text
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: dict[tuple[tuple[str, str], ...], list[int]] = defaultdict(
            lambda: [0] * (len(self.buckets) + 1)
        )
        self._sums: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._totals: dict[tuple[tuple[str, str], ...], int] = defaultdict(int)

    def observe(self, value: float, **labels: str) -> None:
        """Record an observation.

        Args:
            value: Observed value.
            **labels: Label key-value pairs.
        """
        key = tuple(sorted(labels.items()))
        self._sums[key] += value
        self._totals[key] += 1

        # Update bucket counts
        for i, bucket in enumerate(self.buckets):
            if value <= bucket:
                self._counts[key][i] += 1
        self._counts[key][-1] += 1  # +Inf bucket

    @contextmanager
    def time(self, **labels: str) -> Generator[None, None, None]:
        """Context manager to time a block of code.

        Args:
            **labels: Label key-value pairs.

        Yields:
            None
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            self.observe(time.perf_counter() - start, **labels)

    def get_sum(self, **labels: str) -> float:
        """Get sum of all observations.

        Args:
            **labels: Label key-value pairs.

        Returns:
            Sum of observations.
        """
        key = tuple(sorted(labels.items()))
        return self._sums[key]

    def get_count(self, **labels: str) -> int:
        """Get count of observations.

        Args:
            **labels: Label key-value pairs.

        Returns:
            Number of observations.
        """
        key = tuple(sorted(labels.items()))
        return self._totals[key]

    def collect(self) -> list[MetricValue]:
        """Collect all metric values.

        Returns:
            List of MetricValue instances for buckets, sum, and count.
        """
        values = []
        for labels, counts in self._counts.items():
            label_dict = dict(labels)

            # Bucket values
            cumulative = 0
            for i, bucket in enumerate(self.buckets):
                cumulative += counts[i]
                values.append(
                    MetricValue(
                        name=f"{self.name}_bucket",
                        type=MetricType.HISTOGRAM,
                        value=float(cumulative),
                        labels={**label_dict, "le": str(bucket)},
                        help_text=self.help_text,
                    )
                )

            # +Inf bucket
            cumulative += counts[-1]
            values.append(
                MetricValue(
                    name=f"{self.name}_bucket",
                    type=MetricType.HISTOGRAM,
                    value=float(cumulative),
                    labels={**label_dict, "le": "+Inf"},
                    help_text=self.help_text,
                )
            )

            # Sum and count
            values.append(
                MetricValue(
                    name=f"{self.name}_sum",
                    type=MetricType.HISTOGRAM,
                    value=self._sums[labels],
                    labels=label_dict,
                    help_text=self.help_text,
                )
            )
            values.append(
                MetricValue(
                    name=f"{self.name}_count",
                    type=MetricType.HISTOGRAM,
                    value=float(self._totals[labels]),
                    labels=label_dict,
                    help_text=self.help_text,
                )
            )

        return values


class MetricsRegistry:
    """Registry for collecting and exporting metrics."""

    def __init__(self, prefix: str = "ableton_mcp") -> None:
        """Initialize metrics registry.

        Args:
            prefix: Prefix for all metric names.
        """
        self.prefix = prefix
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}

        # Register default metrics
        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        """Register default application metrics."""
        # Request metrics
        self.request_count = self.counter(
            "requests_total",
            "Total number of MCP requests",
        )
        self.request_latency = self.histogram(
            "request_duration_seconds",
            "Request latency in seconds",
        )
        self.request_errors = self.counter(
            "request_errors_total",
            "Total number of request errors",
        )

        # Connection metrics
        self.connection_status = self.gauge(
            "connection_status",
            "OSC connection status (1=connected, 0=disconnected)",
        )
        self.connection_attempts = self.counter(
            "connection_attempts_total",
            "Total connection attempts",
        )

        # Operation metrics
        self.operations_total = self.counter(
            "operations_total",
            "Total operations by type",
        )

        # Active sessions
        self.active_sessions = self.gauge(
            "active_sessions",
            "Number of active sessions",
        )

    def counter(self, name: str, help_text: str = "") -> Counter:
        """Create and register a counter.

        Args:
            name: Metric name (will be prefixed).
            help_text: Description of the metric.

        Returns:
            Counter instance.
        """
        full_name = f"{self.prefix}_{name}"
        counter = Counter(full_name, help_text)
        self._metrics[full_name] = counter
        return counter

    def gauge(self, name: str, help_text: str = "") -> Gauge:
        """Create and register a gauge.

        Args:
            name: Metric name (will be prefixed).
            help_text: Description of the metric.

        Returns:
            Gauge instance.
        """
        full_name = f"{self.prefix}_{name}"
        gauge = Gauge(full_name, help_text)
        self._metrics[full_name] = gauge
        return gauge

    def histogram(
        self,
        name: str,
        help_text: str = "",
        buckets: tuple[float, ...] | None = None,
    ) -> Histogram:
        """Create and register a histogram.

        Args:
            name: Metric name (will be prefixed).
            help_text: Description of the metric.
            buckets: Bucket boundaries.

        Returns:
            Histogram instance.
        """
        full_name = f"{self.prefix}_{name}"
        histogram = Histogram(full_name, help_text, buckets)
        self._metrics[full_name] = histogram
        return histogram

    def collect(self) -> list[MetricValue]:
        """Collect all registered metrics.

        Returns:
            List of all metric values.
        """
        values = []
        for metric in self._metrics.values():
            values.extend(metric.collect())
        return values

    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string.
        """
        lines = []
        seen_help: set[str] = set()

        for metric in self._metrics.values():
            for value in metric.collect():
                # Add help and type once per metric name
                base_name = (
                    value.name.rsplit("_", 1)[0]
                    if value.type == MetricType.HISTOGRAM
                    else value.name
                )
                if base_name not in seen_help:
                    if value.help_text:
                        lines.append(f"# HELP {base_name} {value.help_text}")
                    lines.append(f"# TYPE {base_name} {value.type.value}")
                    seen_help.add(base_name)

                # Format labels
                if value.labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(value.labels.items()))
                    lines.append(f"{value.name}{{{label_str}}} {value.value}")
                else:
                    lines.append(f"{value.name} {value.value}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary.

        Returns:
            Dictionary of metric values.
        """
        result: dict[str, Any] = {}
        for value in self.collect():
            key = value.name
            if value.labels:
                key += "_" + "_".join(f"{k}_{v}" for k, v in sorted(value.labels.items()))
            result[key] = value.value
        return result


# Global metrics registry singleton
_metrics_registry: MetricsRegistry | None = None


def get_metrics_registry() -> MetricsRegistry:
    """Get the global metrics registry.

    Returns:
        Global MetricsRegistry instance.
    """
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = MetricsRegistry()
    return _metrics_registry


def reset_metrics_registry() -> None:
    """Reset the global metrics registry (mainly for testing)."""
    global _metrics_registry
    _metrics_registry = None
