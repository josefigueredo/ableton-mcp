"""OSC infrastructure package for Ableton Live communication.

This package provides async OSC communication using asyncio.DatagramProtocol.
"""

from ableton_mcp.infrastructure.osc.gateway import AbletonOSCGateway

__all__ = ["AbletonOSCGateway"]
