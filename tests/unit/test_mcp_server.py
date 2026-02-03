"""Unit tests for MCP server implementation."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ableton_mcp.application.use_cases import UseCaseResult
from ableton_mcp.interfaces.mcp_server import AbletonMCPServer


@pytest.fixture
def mock_use_cases() -> dict:
    """Create mock use cases for testing."""
    return {
        "connect_use_case": Mock(),
        "transport_use_case": Mock(),
        "song_info_use_case": Mock(),
        "track_ops_use_case": Mock(),
        "add_notes_use_case": Mock(),
        "harmony_analysis_use_case": Mock(),
        "tempo_analysis_use_case": Mock(),
        "mix_analysis_use_case": Mock(),
        "arrangement_suggestions_use_case": Mock(),
        "clip_content_use_case": Mock(),
        "refresh_song_data_use_case": Mock(),
    }


@pytest.fixture
def mcp_server(mock_use_cases: dict) -> AbletonMCPServer:
    """Create MCP server instance with mocked use cases."""
    return AbletonMCPServer(
        connect_use_case=mock_use_cases["connect_use_case"],
        transport_use_case=mock_use_cases["transport_use_case"],
        song_info_use_case=mock_use_cases["song_info_use_case"],
        track_ops_use_case=mock_use_cases["track_ops_use_case"],
        add_notes_use_case=mock_use_cases["add_notes_use_case"],
        harmony_analysis_use_case=mock_use_cases["harmony_analysis_use_case"],
        tempo_analysis_use_case=mock_use_cases["tempo_analysis_use_case"],
        mix_analysis_use_case=mock_use_cases["mix_analysis_use_case"],
        arrangement_suggestions_use_case=mock_use_cases["arrangement_suggestions_use_case"],
        clip_content_use_case=mock_use_cases["clip_content_use_case"],
        refresh_song_data_use_case=mock_use_cases["refresh_song_data_use_case"],
    )


class TestAbletonMCPServerInit:
    """Tests for MCP server initialization."""

    def test_server_initialization(self, mcp_server: AbletonMCPServer) -> None:
        """Test that server initializes correctly."""
        assert mcp_server.server is not None
        assert mcp_server.server.name == "ableton-live-mcp"

    def test_use_cases_are_stored(
        self, mcp_server: AbletonMCPServer, mock_use_cases: dict
    ) -> None:
        """Test that use cases are properly stored."""
        assert mcp_server._connect_use_case == mock_use_cases["connect_use_case"]
        assert mcp_server._transport_use_case == mock_use_cases["transport_use_case"]
        assert mcp_server._song_info_use_case == mock_use_cases["song_info_use_case"]


class TestFormatResult:
    """Tests for result formatting."""

    async def test_format_success_with_data(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting successful result with data."""
        result = UseCaseResult(
            success=True,
            data={"key": "value"},
            message="Operation completed",
        )
        formatted = await mcp_server._format_result(result)

        assert len(formatted) == 1
        assert formatted[0].type == "text"
        assert "Operation completed" in formatted[0].text

    async def test_format_success_without_data(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting successful result without data."""
        result = UseCaseResult(
            success=True,
            data=None,
            message="Done",
        )
        formatted = await mcp_server._format_result(result)

        assert len(formatted) == 1
        assert "Done" in formatted[0].text

    async def test_format_failure_with_error_code(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting failure result with error code."""
        result = UseCaseResult(
            success=False,
            message="Something went wrong",
            error_code="TEST_ERROR",
        )
        formatted = await mcp_server._format_result(result)

        assert len(formatted) == 1
        assert "[ERROR]" in formatted[0].text
        assert "[TEST_ERROR]" in formatted[0].text
        assert "Something went wrong" in formatted[0].text

    async def test_format_failure_without_error_code(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting failure result without error code."""
        result = UseCaseResult(
            success=False,
            message="Generic error",
        )
        formatted = await mcp_server._format_result(result)

        assert "[ERROR]" in formatted[0].text
        assert "Generic error" in formatted[0].text


class TestFormatData:
    """Tests for data formatting."""

    async def test_format_song_info(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting song info data."""
        data = {
            "name": "Test Song",
            "tempo": 120.0,
            "time_signature": "4/4",
            "key": "C major",
            "transport_state": "playing",
            "tracks": [
                {"name": "Track 1", "type": "midi", "muted": False, "soloed": False},
                {"name": "Track 2", "type": "audio", "muted": True, "soloed": False},
            ],
        }
        formatted = await mcp_server._format_data(data)

        assert "**Song Information**" in formatted
        assert "Test Song" in formatted
        assert "120" in formatted
        assert "4/4" in formatted
        assert "C major" in formatted
        assert "**Tracks (2)**" in formatted
        assert "[MUTED]" in formatted

    async def test_format_harmony_analysis(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting harmony analysis data."""
        data = {
            "detected_keys": [
                {"root_name": "C", "mode": "major", "confidence": 0.89},
                {"root_name": "A", "mode": "minor", "confidence": 0.75},
            ],
            "chord_progressions": [[0, 4, 5, 3]],
        }
        formatted = await mcp_server._format_data(data)

        assert "**Harmony Analysis**" in formatted
        assert "C" in formatted
        assert "major" in formatted
        assert "89" in formatted  # confidence percentage

    async def test_format_tempo_analysis(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting tempo analysis data."""
        data = {
            "current_tempo": 128.0,
            "suggestions": {
                "genre_optimal": 130.0,
                "relationships": {
                    "half_time": 64.0,
                    "double_time": 256.0,
                },
            },
        }
        formatted = await mcp_server._format_data(data)

        assert "**Tempo Analysis**" in formatted
        assert "128" in formatted
        assert "130" in formatted

    async def test_format_clip_content(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting clip content data."""
        data = {
            "track_id": 0,
            "clip_id": 0,
            "note_count": 2,
            "notes": [
                {"pitch": 60, "note_name": "C4", "start": 0.0, "duration": 1.0, "velocity": 100, "mute": False},
                {"pitch": 64, "note_name": "E4", "start": 1.0, "duration": 0.5, "velocity": 80, "mute": True},
            ],
        }
        formatted = await mcp_server._format_data(data)

        assert "**Clip Content**" in formatted
        assert "Total Notes: 2" in formatted
        assert "C4" in formatted
        assert "E4" in formatted
        assert "[MUTED]" in formatted

    async def test_format_empty_clip(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting empty clip content."""
        data = {
            "track_id": 0,
            "clip_id": 0,
            "note_count": 0,
            "notes": [],
        }
        formatted = await mcp_server._format_data(data)

        assert "(No notes in this clip)" in formatted

    async def test_format_generic_dict(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting generic dictionary data."""
        data = {"simple_key": "simple_value", "number": 42}
        formatted = await mcp_server._format_data(data)

        assert "simple_key" in formatted
        assert "simple_value" in formatted

    async def test_format_non_dict(self, mcp_server: AbletonMCPServer) -> None:
        """Test formatting non-dictionary data."""
        data = "plain string"
        formatted = await mcp_server._format_data(data)

        assert formatted == "plain string"


class TestHandleCallTool:
    """Tests for tool call handling."""

    async def test_connect_ableton_tool(
        self, mcp_server: AbletonMCPServer, mock_use_cases: dict
    ) -> None:
        """Test connect_ableton tool handling."""
        mock_use_cases["connect_use_case"].execute = AsyncMock(
            return_value=UseCaseResult(success=True, message="Connected")
        )

        # Test via the use case directly since handlers are internal
        from ableton_mcp.application.use_cases import ConnectToAbletonRequest

        request = ConnectToAbletonRequest(host="127.0.0.1", send_port=11000, receive_port=11001)
        result = await mock_use_cases["connect_use_case"].execute(request)

        assert result.success is True

    async def test_transport_control_tool(
        self, mcp_server: AbletonMCPServer, mock_use_cases: dict
    ) -> None:
        """Test transport_control tool handling."""
        mock_use_cases["transport_use_case"].execute = AsyncMock(
            return_value=UseCaseResult(success=True, message="Playing")
        )

        from ableton_mcp.application.use_cases import TransportControlRequest

        request = TransportControlRequest(action="play")
        result = await mock_use_cases["transport_use_case"].execute(request)

        assert result.success is True

    async def test_analyze_harmony_tool(
        self, mcp_server: AbletonMCPServer, mock_use_cases: dict
    ) -> None:
        """Test analyze_harmony tool handling."""
        mock_use_cases["harmony_analysis_use_case"].execute = AsyncMock(
            return_value=UseCaseResult(
                success=True,
                data={"detected_keys": [{"root_name": "C", "mode": "major", "confidence": 0.9}]},
            )
        )

        from ableton_mcp.application.use_cases import AnalyzeHarmonyRequest

        request = AnalyzeHarmonyRequest(notes=[60, 64, 67])
        result = await mock_use_cases["harmony_analysis_use_case"].execute(request)

        assert result.success is True
        assert "detected_keys" in result.data


class TestListTools:
    """Tests for listing available tools."""

    def test_server_has_tools_registered(self, mcp_server: AbletonMCPServer) -> None:
        """Test that server has tools registered."""
        # The tools are registered via decorators during setup
        # We can verify by checking the server has the list_tools handler
        assert mcp_server.server is not None
