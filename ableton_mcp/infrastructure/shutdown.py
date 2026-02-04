"""Graceful shutdown handling for production deployments.

Provides mechanisms for:
- Handling shutdown signals (SIGTERM, SIGINT)
- Draining in-flight requests
- Cleaning up resources
- Coordinated shutdown of multiple components

Usage:
    shutdown_handler = GracefulShutdown()

    # Register cleanup callbacks
    shutdown_handler.register_callback(cleanup_database)
    shutdown_handler.register_callback(close_connections)

    # Setup signal handlers
    shutdown_handler.setup_signal_handlers()

    # In your main loop
    while not shutdown_handler.should_shutdown:
        # Process requests
        pass

    # Trigger shutdown
    await shutdown_handler.shutdown()
"""

from __future__ import annotations

import asyncio
import signal
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

logger = structlog.get_logger(__name__)


class ShutdownPhase(StrEnum):
    """Phases of the shutdown process."""

    RUNNING = "running"
    DRAINING = "draining"
    CLEANUP = "cleanup"
    STOPPED = "stopped"


@dataclass
class ShutdownState:
    """Current shutdown state."""

    phase: ShutdownPhase = ShutdownPhase.RUNNING
    started_at: datetime | None = None
    reason: str | None = None
    in_flight_requests: int = 0


class GracefulShutdown:
    """Manages graceful shutdown of the application.

    Features:
    - Signal handling for SIGTERM and SIGINT
    - Request draining with timeout
    - Ordered callback execution
    - Shutdown state tracking
    """

    def __init__(
        self,
        drain_timeout: float = 30.0,
        force_timeout: float = 60.0,
    ) -> None:
        """Initialize graceful shutdown handler.

        Args:
            drain_timeout: Seconds to wait for in-flight requests to complete.
            force_timeout: Seconds before forcing shutdown regardless of state.
        """
        self.drain_timeout = drain_timeout
        self.force_timeout = force_timeout

        self._state = ShutdownState()
        self._callbacks: list[tuple[int, Callable[[], Coroutine[Any, Any, None]]]] = []
        self._shutdown_event = asyncio.Event()
        self._drain_complete = asyncio.Event()
        self._active_requests = 0
        self._lock = asyncio.Lock()

    @property
    def should_shutdown(self) -> bool:
        """Check if shutdown has been requested."""
        return self._state.phase != ShutdownPhase.RUNNING

    @property
    def is_draining(self) -> bool:
        """Check if currently draining requests."""
        return self._state.phase == ShutdownPhase.DRAINING

    @property
    def state(self) -> ShutdownState:
        """Get current shutdown state."""
        return self._state

    def register_callback(
        self,
        callback: Callable[[], Coroutine[Any, Any, None]],
        priority: int = 0,
    ) -> None:
        """Register a cleanup callback.

        Callbacks are executed in order of priority (lower first).
        Callbacks with the same priority are executed in registration order.

        Args:
            callback: Async function to call during shutdown.
            priority: Execution priority (lower = earlier).
        """
        self._callbacks.append((priority, callback))
        self._callbacks.sort(key=lambda x: x[0])
        logger.debug(
            "Registered shutdown callback",
            callback=callback.__name__,
            priority=priority,
        )

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown.

        Handles SIGTERM and SIGINT signals.
        Note: Signal handlers only work on Unix-like systems for the main thread.
        """
        if sys.platform == "win32":
            # Windows doesn't support SIGTERM properly in asyncio
            # Use a different approach for Windows
            logger.warning("Signal handlers limited on Windows platform")
            return

        loop = asyncio.get_event_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s: asyncio.create_task(self._handle_signal(s)),
                sig,
            )

        logger.info("Signal handlers installed", signals=["SIGTERM", "SIGINT"])

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal.

        Args:
            sig: The signal that was received.
        """
        signal_name = sig.name if hasattr(sig, "name") else str(sig)
        logger.info("Received shutdown signal", signal=signal_name)

        await self.shutdown(reason=f"Received {signal_name}")

    async def request_started(self) -> None:
        """Track that a request has started.

        Call this when a new request begins processing.
        """
        async with self._lock:
            self._active_requests += 1
            self._state.in_flight_requests = self._active_requests

    async def request_completed(self) -> None:
        """Track that a request has completed.

        Call this when a request finishes (success or failure).
        """
        async with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            self._state.in_flight_requests = self._active_requests

            # Check if draining is complete
            if self.is_draining and self._active_requests == 0:
                self._drain_complete.set()

    async def shutdown(self, reason: str = "Shutdown requested") -> None:
        """Initiate graceful shutdown.

        Args:
            reason: Reason for shutdown (for logging).
        """
        if self._state.phase != ShutdownPhase.RUNNING:
            logger.warning("Shutdown already in progress", current_phase=self._state.phase.value)
            return

        logger.info("Starting graceful shutdown", reason=reason)

        self._state.phase = ShutdownPhase.DRAINING
        self._state.started_at = datetime.now(UTC)
        self._state.reason = reason
        self._shutdown_event.set()

        # Wait for in-flight requests to complete
        await self._drain_requests()

        # Run cleanup callbacks
        await self._run_callbacks()

        self._state.phase = ShutdownPhase.STOPPED
        logger.info("Shutdown complete")

    async def _drain_requests(self) -> None:
        """Wait for in-flight requests to complete."""
        if self._active_requests == 0:
            logger.info("No in-flight requests to drain")
            return

        logger.info(
            "Draining in-flight requests",
            count=self._active_requests,
            timeout=self.drain_timeout,
        )

        try:
            await asyncio.wait_for(
                self._drain_complete.wait(),
                timeout=self.drain_timeout,
            )
            logger.info("All requests drained successfully")
        except TimeoutError:
            logger.warning(
                "Drain timeout exceeded",
                remaining_requests=self._active_requests,
            )

    async def _run_callbacks(self) -> None:
        """Execute registered cleanup callbacks."""
        self._state.phase = ShutdownPhase.CLEANUP

        if not self._callbacks:
            logger.info("No cleanup callbacks registered")
            return

        logger.info("Running cleanup callbacks", count=len(self._callbacks))

        for priority, callback in self._callbacks:
            try:
                logger.debug(
                    "Executing cleanup callback",
                    callback=callback.__name__,
                    priority=priority,
                )
                await asyncio.wait_for(callback(), timeout=10.0)
            except TimeoutError:
                logger.error(
                    "Cleanup callback timed out",
                    callback=callback.__name__,
                )
            except Exception as e:
                logger.error(
                    "Cleanup callback failed",
                    callback=callback.__name__,
                    error=str(e),
                )

    async def wait_for_shutdown(self) -> None:
        """Wait until shutdown is requested.

        Useful for blocking the main coroutine until shutdown.
        """
        await self._shutdown_event.wait()


class RequestTracker:
    """Context manager for tracking requests during shutdown.

    Usage:
        async with RequestTracker(shutdown_handler):
            # Process request
            pass
    """

    def __init__(self, shutdown: GracefulShutdown) -> None:
        """Initialize request tracker.

        Args:
            shutdown: GracefulShutdown instance.
        """
        self._shutdown = shutdown

    async def __aenter__(self) -> RequestTracker:
        """Enter context - track request start."""
        if self._shutdown.should_shutdown:
            raise RuntimeError("Server is shutting down")
        await self._shutdown.request_started()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit context - track request completion."""
        await self._shutdown.request_completed()


def create_shutdown_callbacks(
    gateway: Any | None = None,
    health_service: Any | None = None,
) -> list[tuple[int, Callable[[], Coroutine[Any, Any, None]]]]:
    """Create standard shutdown callbacks.

    Args:
        gateway: Optional AbletonGateway instance.
        health_service: Optional HealthCheckService instance.

    Returns:
        List of (priority, callback) tuples.
    """
    callbacks: list[tuple[int, Callable[[], Coroutine[Any, Any, None]]]] = []

    # Mark service as not ready (priority 0 - first)
    if health_service is not None:

        async def mark_not_ready() -> None:
            health_service.set_ready(False)
            logger.info("Marked service as not ready")

        callbacks.append((0, mark_not_ready))

    # Disconnect from Ableton (priority 10)
    if gateway is not None:

        async def disconnect_gateway() -> None:
            try:
                await gateway.disconnect()
                logger.info("Disconnected from Ableton Live")
            except Exception as e:
                logger.error("Error disconnecting", error=str(e))

        callbacks.append((10, disconnect_gateway))

    # Log final message (priority 100 - last)
    async def final_log() -> None:
        logger.info("Shutdown callbacks completed")

    callbacks.append((100, final_log))

    return callbacks
