"""Unit tests for OSC correlator."""

import asyncio

import pytest

from ableton_mcp.infrastructure.osc.correlator import OSCCorrelator


class TestOSCCorrelator:
    """Test cases for OSC request-response correlation."""

    async def test_basic_request_response(self) -> None:
        """Test basic request-response correlation."""
        correlator = OSCCorrelator()

        # Set up expectation
        future = await correlator.expect_response("/live/song/get/tempo")

        # Simulate response
        handled = correlator.handle_response("/live/song/get/tempo", [120.0])

        assert handled is True
        assert future.done()
        assert await future == [120.0]

    async def test_response_without_pending_request(self) -> None:
        """Test handling response when no request is pending."""
        correlator = OSCCorrelator()

        # Handle response without pending request
        handled = correlator.handle_response("/live/song/get/tempo", [120.0])

        assert handled is False

    async def test_fifo_ordering(self) -> None:
        """Test that requests are handled in FIFO order."""
        correlator = OSCCorrelator()

        # Set up multiple expectations on same address
        future1 = await correlator.expect_response("/live/song/get/tempo")
        future2 = await correlator.expect_response("/live/song/get/tempo")

        # First response goes to first request
        correlator.handle_response("/live/song/get/tempo", [120.0])
        assert future1.done()
        assert await future1 == [120.0]
        assert not future2.done()

        # Second response goes to second request
        correlator.handle_response("/live/song/get/tempo", [130.0])
        assert future2.done()
        assert await future2 == [130.0]

    async def test_wait_for_response_success(self) -> None:
        """Test waiting for response with success."""
        correlator = OSCCorrelator(default_timeout=1.0)

        async def send_response_delayed() -> None:
            await asyncio.sleep(0.1)
            correlator.handle_response("/live/song/get/tempo", [120.0])

        # Start response in background
        asyncio.create_task(send_response_delayed())

        # Wait for response
        result = await correlator.wait_for_response("/live/song/get/tempo")

        assert result == [120.0]

    async def test_wait_for_response_timeout(self) -> None:
        """Test that waiting times out correctly."""
        correlator = OSCCorrelator(default_timeout=0.1)

        with pytest.raises(asyncio.TimeoutError):
            await correlator.wait_for_response("/live/song/get/tempo")

    async def test_cancel_all(self) -> None:
        """Test cancelling all pending requests."""
        correlator = OSCCorrelator()

        # Set up expectations
        future1 = await correlator.expect_response("/live/song/get/tempo")
        future2 = await correlator.expect_response("/live/track/get/name")

        # Cancel all
        correlator.cancel_all()

        assert future1.cancelled()
        assert future2.cancelled()

    async def test_different_addresses_independent(self) -> None:
        """Test that different addresses are handled independently."""
        correlator = OSCCorrelator()

        # Set up expectations on different addresses
        future_tempo = await correlator.expect_response("/live/song/get/tempo")
        future_tracks = await correlator.expect_response("/live/song/get/num_tracks")

        # Respond to tracks first
        correlator.handle_response("/live/song/get/num_tracks", [5])

        assert not future_tempo.done()
        assert future_tracks.done()
        assert await future_tracks == [5]

        # Now respond to tempo
        correlator.handle_response("/live/song/get/tempo", [128.0])
        assert future_tempo.done()
        assert await future_tempo == [128.0]
