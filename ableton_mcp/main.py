"""Main application entry point for Ableton Live MCP Server."""

import asyncio
import logging
import sys
from pathlib import Path

import structlog
from rich.console import Console
from rich.logging import RichHandler

from ableton_mcp.container import Container
from ableton_mcp.core.exceptions import AbletonMCPError


def setup_logging() -> None:
    """Configure structured logging with rich formatting."""
    # Configure standard library logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def display_banner() -> None:
    """Display startup banner."""
    console = Console()
    
    banner = """
+------------------------------------------------------+
|                                                      |
|  Ableton Live MCP Server v1.0.0                      |
|                                                      |
|  Professional AI-Powered Music Production Assistant  |
|  ==================================================  |
|                                                      |
|  Features:                                           |
|  * Real-time Ableton Live control via OSC            |
|  * Intelligent music theory analysis                 |
|  * Professional mixing guidance                      |
|  * Arrangement suggestions                           |
|  * Clean Architecture with SOLID principles          |
|                                                      |
|  Requirements:                                       |
|  * Ableton Live with AbletonOSC remote script        |
|  * Python 3.11+ with MCP support                     |
|                                                      |
+------------------------------------------------------+
"""
    
    console.print(banner, style="bold cyan")
    console.print("Starting MCP server...\n", style="bold green")


async def main() -> None:
    """Main application entry point."""
    try:
        # Setup logging
        setup_logging()
        logger = structlog.get_logger(__name__)
        
        # Display banner
        display_banner()
        
        # Create and configure container
        container = Container()
        
        # Get MCP server instance
        mcp_server = container.mcp_server()
        
        logger.info("Ableton Live MCP Server starting", version="1.0.0")
        
        # Run the MCP server
        await mcp_server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
        
    except AbletonMCPError as e:
        logger.error("Application error", error=str(e), code=e.error_code)
        sys.exit(1)
        
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        sys.exit(1)


def cli() -> None:
    """CLI entry point for package installation."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    cli()