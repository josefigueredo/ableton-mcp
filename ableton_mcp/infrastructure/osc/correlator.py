"""Request-response correlation for OSC communication.

AbletonOSC responds on the same address pattern as the request.
This module correlates requests with their responses using FIFO queues.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Default timeout for waiting on responses
DEFAULT_TIMEOUT_SECONDS = 5.0


@dataclass
class PendingRequest:
    """Represents a pending request awaiting a response.

    Note: future and timestamp should always be provided explicitly.
    The defaults exist only for dataclass mechanics but will fail
    if used outside an async context.
    """

    address: str
    future: asyncio.Future[List[Any]]
    timestamp: float


class OSCCorrelator:
    """Correlates OSC requests with their responses.

    Uses FIFO queues per OSC address since AbletonOSC responds
    on the same address pattern as the request.
    """

    def __init__(self, default_timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        """Initialize the correlator.

        Args:
            default_timeout: Default timeout for waiting on responses
        """
        # Use regular dict instead of defaultdict to avoid creating Queue outside async context
        self._pending: Dict[str, asyncio.Queue[PendingRequest]] = {}
        self._default_timeout = default_timeout

    async def expect_response(
        self,
        address: str,
        timeout: Optional[float] = None,
    ) -> asyncio.Future[List[Any]]:
        """Register expectation for a response on an address.

        Args:
            address: OSC address to expect response on
            timeout: Optional timeout override

        Returns:
            Future that will be resolved with the response args
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[List[Any]] = loop.create_future()

        request = PendingRequest(
            address=address,
            future=future,
            timestamp=loop.time(),
        )

        # Create queue for this address if it doesn't exist (inside async context)
        if address not in self._pending:
            self._pending[address] = asyncio.Queue()

        await self._pending[address].put(request)

        logger.debug("Registered pending request", address=address)
        return future

    def handle_response(self, address: str, args: List[Any]) -> bool:
        """Handle an incoming response for an address.

        Args:
            address: OSC address of the response
            args: Response arguments

        Returns:
            True if a pending request was matched, False otherwise
        """
        queue = self._pending.get(address)
        if queue is None or queue.empty():
            logger.debug("No pending request for response", address=address)
            return False

        try:
            # Get the oldest pending request (FIFO)
            request = queue.get_nowait()

            if not request.future.done():
                request.future.set_result(args)
                logger.debug(
                    "Resolved pending request",
                    address=address,
                    args=args,
                )
                return True
            else:
                logger.warning(
                    "Pending request future already done",
                    address=address,
                )
                return False

        except asyncio.QueueEmpty:
            logger.debug("Queue empty for response", address=address)
            return False

    async def wait_for_response(
        self,
        address: str,
        timeout: Optional[float] = None,
    ) -> List[Any]:
        """Wait for a response on an address.

        This is a convenience method that combines expect_response and await.

        Args:
            address: OSC address to wait for
            timeout: Optional timeout override

        Returns:
            Response arguments

        Raises:
            asyncio.TimeoutError: If response not received within timeout
        """
        future = await self.expect_response(address)
        effective_timeout = timeout if timeout is not None else self._default_timeout

        try:
            return await asyncio.wait_for(future, timeout=effective_timeout)
        except asyncio.TimeoutError:
            # Clean up the timed-out request from the queue to prevent memory leak
            self._cleanup_timed_out_request(address, future)
            logger.warning("Request timed out", address=address, timeout=effective_timeout)
            raise

    def _cleanup_timed_out_request(
        self, address: str, future: asyncio.Future[List[Any]]
    ) -> None:
        """Remove a timed-out request from the queue.

        This prevents memory leaks from accumulating timed-out futures.
        """
        queue = self._pending.get(address)
        if queue is None:
            return

        # Drain and rebuild the queue without the timed-out future
        remaining: List[PendingRequest] = []
        while not queue.empty():
            try:
                request = queue.get_nowait()
                if request.future is not future:
                    remaining.append(request)
            except asyncio.QueueEmpty:
                break

        # Re-add non-timed-out requests
        for request in remaining:
            queue.put_nowait(request)

    def cancel_all(self) -> None:
        """Cancel all pending requests.

        Useful during disconnect to clean up.
        """
        for address, queue in self._pending.items():
            while not queue.empty():
                try:
                    request = queue.get_nowait()
                    if not request.future.done():
                        request.future.cancel()
                except asyncio.QueueEmpty:
                    break

        self._pending.clear()
        logger.debug("Cancelled all pending requests")
