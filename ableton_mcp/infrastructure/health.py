"""Health check service for production monitoring.

Provides health status information for:
- Overall application health
- Component-level health (OSC connection, services)
- Readiness and liveness probes for container orchestration
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

logger = structlog.get_logger(__name__)


class HealthStatus(StrEnum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""

    name: str
    status: HealthStatus
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HealthCheckResult:
    """Overall health check result."""

    status: HealthStatus
    version: str
    uptime_seconds: float
    components: list[ComponentHealth] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": self.timestamp.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "details": c.details,
                    "last_check": c.last_check.isoformat(),
                }
                for c in self.components
            ],
        }


class HealthCheckService:
    """Service for performing health checks.

    Supports:
    - Registering health check functions for components
    - Performing async health checks
    - Caching results to avoid excessive checks
    - Liveness and readiness probe support
    """

    def __init__(
        self,
        version: str = "1.0.0",
        cache_ttl_seconds: float = 5.0,
    ) -> None:
        """Initialize health check service.

        Args:
            version: Application version string.
            cache_ttl_seconds: How long to cache health check results.
        """
        self._version = version
        self._cache_ttl = cache_ttl_seconds
        self._start_time = time.monotonic()
        self._checks: dict[str, Callable[[], Coroutine[Any, Any, ComponentHealth]]] = {}
        self._cached_result: HealthCheckResult | None = None
        self._cache_time: float = 0.0
        self._is_ready = False

    @property
    def uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return time.monotonic() - self._start_time

    def register_check(
        self,
        name: str,
        check_func: Callable[[], Coroutine[Any, Any, ComponentHealth]],
    ) -> None:
        """Register a health check function.

        Args:
            name: Component name.
            check_func: Async function that returns ComponentHealth.
        """
        self._checks[name] = check_func
        logger.debug("Registered health check", component=name)

    def unregister_check(self, name: str) -> None:
        """Unregister a health check.

        Args:
            name: Component name to remove.
        """
        if name in self._checks:
            del self._checks[name]
            logger.debug("Unregistered health check", component=name)

    def set_ready(self, ready: bool = True) -> None:
        """Set readiness status.

        Args:
            ready: Whether the application is ready to serve requests.
        """
        self._is_ready = ready
        logger.info("Readiness status changed", ready=ready)

    async def check_health(self, use_cache: bool = True) -> HealthCheckResult:
        """Perform health check on all registered components.

        Args:
            use_cache: Whether to use cached results if available.

        Returns:
            HealthCheckResult with overall and component statuses.
        """
        # Check cache
        if use_cache and self._cached_result:
            if time.monotonic() - self._cache_time < self._cache_ttl:
                return self._cached_result

        # Run all health checks concurrently
        components: list[ComponentHealth] = []

        if self._checks:
            tasks = [check() for check in self._checks.values()]
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for name, result in zip(self._checks.keys(), results, strict=False):
                    if isinstance(result, Exception):
                        components.append(
                            ComponentHealth(
                                name=name,
                                status=HealthStatus.UNHEALTHY,
                                message=str(result),
                            )
                        )
                    else:
                        components.append(result)
            except Exception as e:
                logger.error("Health check failed", error=str(e))

        # Determine overall status
        if not components:
            overall_status = HealthStatus.HEALTHY
        elif any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in components):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        result = HealthCheckResult(
            status=overall_status,
            version=self._version,
            uptime_seconds=self.uptime_seconds,
            components=components,
        )

        # Cache result
        self._cached_result = result
        self._cache_time = time.monotonic()

        return result

    async def liveness_check(self) -> bool:
        """Check if the application is alive.

        Liveness probe - should return True if the application
        is running and not deadlocked.

        Returns:
            True if alive, False otherwise.
        """
        # Simple liveness check - if we can respond, we're alive
        return True

    async def readiness_check(self) -> bool:
        """Check if the application is ready to serve requests.

        Readiness probe - should return True if the application
        is ready to accept traffic.

        Returns:
            True if ready, False otherwise.
        """
        if not self._is_ready:
            return False

        # Optionally check critical components
        result = await self.check_health(use_cache=True)
        return result.status != HealthStatus.UNHEALTHY


def create_osc_health_check(
    gateway: Any,
) -> Callable[[], Coroutine[Any, Any, ComponentHealth]]:
    """Create a health check function for OSC connection.

    Args:
        gateway: AbletonGateway instance.

    Returns:
        Async function that checks OSC connection health.
    """

    async def check() -> ComponentHealth:
        try:
            is_connected = gateway.is_connected()

            if is_connected:
                return ComponentHealth(
                    name="osc_connection",
                    status=HealthStatus.HEALTHY,
                    message="Connected to Ableton Live",
                    details={"connected": True},
                )
            else:
                return ComponentHealth(
                    name="osc_connection",
                    status=HealthStatus.DEGRADED,
                    message="Not connected to Ableton Live",
                    details={"connected": False},
                )
        except Exception as e:
            return ComponentHealth(
                name="osc_connection",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection check failed: {e}",
            )

    return check


def create_repository_health_check(
    repository: Any,
    name: str,
) -> Callable[[], Coroutine[Any, Any, ComponentHealth]]:
    """Create a health check function for a repository.

    Args:
        repository: Repository instance.
        name: Repository name for identification.

    Returns:
        Async function that checks repository health.
    """

    async def check() -> ComponentHealth:
        try:
            # Try a simple operation to verify repository is working
            # Most repositories have a get_all or similar method
            if hasattr(repository, "get_all"):
                await repository.get_all()

            return ComponentHealth(
                name=f"repository_{name}",
                status=HealthStatus.HEALTHY,
                message=f"{name} repository operational",
            )
        except Exception as e:
            return ComponentHealth(
                name=f"repository_{name}",
                status=HealthStatus.UNHEALTHY,
                message=f"Repository check failed: {e}",
            )

    return check
