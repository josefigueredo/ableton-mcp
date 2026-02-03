"""Unit tests for main application entry point."""

import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ableton_mcp.main import cli, display_banner, main


class TestDisplayBanner:
    """Tests for banner display function."""

    def test_display_banner_executes(self) -> None:
        """Test that display_banner executes without error."""
        # Should not raise any exceptions
        display_banner()

    @patch("ableton_mcp.main.Console")
    def test_display_banner_uses_console(self, mock_console_class: Mock) -> None:
        """Test that display_banner uses Rich console."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        display_banner()

        # Should call print at least twice (banner and starting message)
        assert mock_console.print.call_count >= 2


class TestMain:
    """Tests for main async entry point."""

    @patch("ableton_mcp.main.Container")
    @patch("ableton_mcp.main.setup_logging")
    @patch("ableton_mcp.main.get_logger")
    @patch("ableton_mcp.main.display_banner")
    async def test_main_initializes_components(
        self,
        mock_display_banner: Mock,
        mock_get_logger: Mock,
        mock_setup_logging: Mock,
        mock_container_class: Mock,
    ) -> None:
        """Test that main initializes all components."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_container = Mock()
        mock_mcp_server = Mock()
        mock_mcp_server.run = AsyncMock()
        mock_container.mcp_server.return_value = mock_mcp_server
        mock_container_class.return_value = mock_container

        await main()

        mock_setup_logging.assert_called_once()
        mock_display_banner.assert_called_once()
        mock_container_class.assert_called_once()
        mock_mcp_server.run.assert_awaited_once()

    @patch("ableton_mcp.main.Container")
    @patch("ableton_mcp.main.setup_logging")
    @patch("ableton_mcp.main.get_logger")
    @patch("ableton_mcp.main.display_banner")
    @patch("ableton_mcp.main.sys.exit")
    async def test_main_handles_keyboard_interrupt(
        self,
        mock_exit: Mock,
        mock_display_banner: Mock,
        mock_get_logger: Mock,
        mock_setup_logging: Mock,
        mock_container_class: Mock,
    ) -> None:
        """Test that main handles KeyboardInterrupt gracefully."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_container = Mock()
        mock_mcp_server = Mock()
        mock_mcp_server.run = AsyncMock(side_effect=KeyboardInterrupt())
        mock_container.mcp_server.return_value = mock_mcp_server
        mock_container_class.return_value = mock_container

        await main()

        mock_exit.assert_called_once_with(0)
        mock_logger.info.assert_called()

    @patch("ableton_mcp.main.Container")
    @patch("ableton_mcp.main.setup_logging")
    @patch("ableton_mcp.main.get_logger")
    @patch("ableton_mcp.main.display_banner")
    @patch("ableton_mcp.main.sys.exit")
    async def test_main_handles_ableton_error(
        self,
        mock_exit: Mock,
        mock_display_banner: Mock,
        mock_get_logger: Mock,
        mock_setup_logging: Mock,
        mock_container_class: Mock,
    ) -> None:
        """Test that main handles AbletonMCPError."""
        from ableton_mcp.core.exceptions import AbletonMCPError

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_container = Mock()
        mock_mcp_server = Mock()
        mock_mcp_server.run = AsyncMock(
            side_effect=AbletonMCPError("Test error", "TEST_CODE")
        )
        mock_container.mcp_server.return_value = mock_mcp_server
        mock_container_class.return_value = mock_container

        await main()

        mock_exit.assert_called_once_with(1)
        mock_logger.error.assert_called()

    @patch("ableton_mcp.main.Container")
    @patch("ableton_mcp.main.setup_logging")
    @patch("ableton_mcp.main.get_logger")
    @patch("ableton_mcp.main.display_banner")
    @patch("ableton_mcp.main.sys.exit")
    async def test_main_handles_unexpected_error(
        self,
        mock_exit: Mock,
        mock_display_banner: Mock,
        mock_get_logger: Mock,
        mock_setup_logging: Mock,
        mock_container_class: Mock,
    ) -> None:
        """Test that main handles unexpected exceptions."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_container = Mock()
        mock_mcp_server = Mock()
        mock_mcp_server.run = AsyncMock(side_effect=RuntimeError("Unexpected"))
        mock_container.mcp_server.return_value = mock_mcp_server
        mock_container_class.return_value = mock_container

        await main()

        mock_exit.assert_called_once_with(1)


class TestCli:
    """Tests for CLI entry point."""

    @patch("ableton_mcp.main.asyncio.run")
    def test_cli_calls_asyncio_run(self, mock_asyncio_run: Mock) -> None:
        """Test that cli() calls asyncio.run with main."""
        cli()
        mock_asyncio_run.assert_called_once()

    @patch("ableton_mcp.main.asyncio.run")
    @patch("ableton_mcp.main.sys.exit")
    @patch("builtins.print")
    def test_cli_handles_keyboard_interrupt(
        self, mock_print: Mock, mock_exit: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that cli() handles KeyboardInterrupt."""
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        cli()

        mock_exit.assert_called_once_with(0)
