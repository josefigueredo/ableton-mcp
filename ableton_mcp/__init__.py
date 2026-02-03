"""
Ableton Live MCP Server

A professional Model Context Protocol server for Ableton Live integration
with AI-powered music intelligence and production assistance.

This package follows Clean Architecture principles with clear separation
of concerns, dependency inversion, and enterprise-grade patterns.
"""

__version__ = "1.0.0"
__author__ = "Jose Figueredo"

from ableton_mcp.core.exceptions import AbletonMCPError

__all__ = ["AbletonMCPError", "__author__", "__version__"]
