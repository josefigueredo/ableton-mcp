"""MCP server implementation providing tools for Ableton Live control."""

from typing import Any

import mcp.server.stdio
import mcp.types as types
import structlog
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from ableton_mcp.application.use_cases import (
    AddNotesRequest,
    AddNotesUseCase,
    AnalyzeHarmonyRequest,
    AnalyzeHarmonyUseCase,
    AnalyzeTempoRequest,
    AnalyzeTempoUseCase,
    ArrangementSuggestionsRequest,
    ArrangementSuggestionsUseCase,
    ClipOperationRequest,
    ClipOperationsUseCase,
    ConnectToAbletonRequest,
    ConnectToAbletonUseCase,
    DeviceOperationRequest,
    DeviceOperationsUseCase,
    GetClipContentRequest,
    GetClipContentUseCase,
    GetSongInfoRequest,
    GetSongInfoUseCase,
    MixAnalysisRequest,
    MixAnalysisUseCase,
    RefreshSongDataUseCase,
    ReturnTrackOperationRequest,
    ReturnTrackOperationsUseCase,
    SceneOperationRequest,
    SceneOperationsUseCase,
    SongPropertyRequest,
    SongPropertyUseCase,
    TrackOperationRequest,
    TrackOperationsUseCase,
    TransportControlRequest,
    TransportControlUseCase,
    UseCaseResult,
)
from ableton_mcp.core.exceptions import AbletonMCPError

logger = structlog.get_logger(__name__)


class AbletonMCPServer:
    """MCP server for Ableton Live integration with AI music intelligence."""

    def __init__(
        self,
        connect_use_case: ConnectToAbletonUseCase,
        transport_use_case: TransportControlUseCase,
        song_info_use_case: GetSongInfoUseCase,
        track_ops_use_case: TrackOperationsUseCase,
        add_notes_use_case: AddNotesUseCase,
        harmony_analysis_use_case: AnalyzeHarmonyUseCase,
        tempo_analysis_use_case: AnalyzeTempoUseCase,
        mix_analysis_use_case: MixAnalysisUseCase,
        arrangement_suggestions_use_case: ArrangementSuggestionsUseCase,
        clip_content_use_case: GetClipContentUseCase,
        refresh_song_data_use_case: RefreshSongDataUseCase,
        scene_ops_use_case: SceneOperationsUseCase,
        song_property_use_case: SongPropertyUseCase,
        clip_ops_use_case: ClipOperationsUseCase,
        return_track_ops_use_case: ReturnTrackOperationsUseCase,
        device_ops_use_case: DeviceOperationsUseCase,
    ) -> None:
        """Initialize MCP server with use cases."""
        self.server = Server("ableton-live-mcp")

        # Inject use cases
        self._connect_use_case = connect_use_case
        self._transport_use_case = transport_use_case
        self._song_info_use_case = song_info_use_case
        self._track_ops_use_case = track_ops_use_case
        self._add_notes_use_case = add_notes_use_case
        self._harmony_analysis_use_case = harmony_analysis_use_case
        self._tempo_analysis_use_case = tempo_analysis_use_case
        self._mix_analysis_use_case = mix_analysis_use_case
        self._arrangement_suggestions_use_case = arrangement_suggestions_use_case
        self._clip_content_use_case = clip_content_use_case
        self._refresh_song_data_use_case = refresh_song_data_use_case
        self._scene_ops_use_case = scene_ops_use_case
        self._song_property_use_case = song_property_use_case
        self._clip_ops_use_case = clip_ops_use_case
        self._return_track_ops_use_case = return_track_ops_use_case
        self._device_ops_use_case = device_ops_use_case

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup MCP tool handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools for Ableton Live control and music production."""
            return [
                types.Tool(
                    name="connect_ableton",
                    description="Connect to Ableton Live via OSC protocol",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "host": {
                                "type": "string",
                                "description": "Ableton Live host IP address",
                                "default": "127.0.0.1",
                            },
                            "send_port": {
                                "type": "integer",
                                "description": "OSC send port for commands",
                                "default": 11000,
                                "minimum": 1024,
                                "maximum": 65535,
                            },
                            "receive_port": {
                                "type": "integer",
                                "description": "OSC receive port for responses",
                                "default": 11001,
                                "minimum": 1024,
                                "maximum": 65535,
                            },
                        },
                    },
                ),
                types.Tool(
                    name="transport_control",
                    description="Control Ableton Live transport (play, stop, record, undo/redo, navigation, and more)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "play",
                                    "stop",
                                    "record",
                                    "get_status",
                                    "continue",
                                    "stop_all_clips",
                                    "tap_tempo",
                                    "undo",
                                    "redo",
                                    "capture_midi",
                                    "session_record",
                                    "jump_by",
                                    "jump_to",
                                    "next_cue",
                                    "prev_cue",
                                ],
                                "description": "Transport action to perform",
                            },
                            "value": {
                                "type": "number",
                                "description": "Value for jump_by (beats) or jump_to (time position)",
                            },
                        },
                        "required": ["action"],
                    },
                ),
                types.Tool(
                    name="get_song_info",
                    description="Get comprehensive information about the current Ableton Live song",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_tracks": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include track information in response",
                            },
                            "include_devices": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include device/plugin information",
                            },
                            "include_clips": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include clip information (can be large)",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="track_operations",
                    description="Perform operations on Ableton Live tracks (volume, pan, mute, solo, arm, color, sends, duplicate, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "get_info",
                                    "set_volume",
                                    "set_pan",
                                    "mute",
                                    "solo",
                                    "arm",
                                    "create",
                                    "delete",
                                    "set_color",
                                    "set_send",
                                    "stop_all_clips",
                                    "duplicate",
                                ],
                                "description": "Track operation to perform",
                            },
                            "track_id": {
                                "type": "integer",
                                "description": "Track ID (0-based index)",
                                "minimum": 0,
                            },
                            "value": {
                                "type": "number",
                                "description": "Value for volume/pan/send operations",
                                "minimum": -1.0,
                                "maximum": 1.0,
                            },
                            "name": {
                                "type": "string",
                                "description": "Track name for creation operations",
                            },
                            "track_type": {
                                "type": "string",
                                "enum": ["midi", "audio", "return", "group"],
                                "description": "Type of track to create",
                            },
                            "color": {
                                "type": "integer",
                                "description": "Color index (0-69) for set_color action",
                                "minimum": 0,
                                "maximum": 69,
                            },
                            "send_id": {
                                "type": "integer",
                                "description": "Send index (0-based) for set_send action",
                                "minimum": 0,
                            },
                        },
                        "required": ["action"],
                    },
                ),
                types.Tool(
                    name="add_notes",
                    description="Add MIDI notes to a clip with intelligent music theory assistance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "track_id": {
                                "type": "integer",
                                "description": "Target track ID (0-based)",
                                "minimum": 0,
                            },
                            "clip_id": {
                                "type": "integer",
                                "description": "Target clip slot ID (0-based)",
                                "minimum": 0,
                            },
                            "notes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "pitch": {
                                            "type": "integer",
                                            "description": "MIDI note number (0-127)",
                                            "minimum": 0,
                                            "maximum": 127,
                                        },
                                        "start": {
                                            "type": "number",
                                            "description": "Start time in beats",
                                            "minimum": 0,
                                        },
                                        "duration": {
                                            "type": "number",
                                            "description": "Note duration in beats",
                                            "minimum": 0.01,
                                        },
                                        "velocity": {
                                            "type": "integer",
                                            "description": "Note velocity (1-127)",
                                            "minimum": 1,
                                            "maximum": 127,
                                            "default": 100,
                                        },
                                    },
                                    "required": ["pitch", "start", "duration"],
                                },
                                "description": "Array of MIDI notes to add",
                            },
                            "quantize": {
                                "type": "boolean",
                                "default": False,
                                "description": "Quantize notes to 16th note grid",
                            },
                            "scale_filter": {
                                "type": "string",
                                "enum": [
                                    "major",
                                    "minor",
                                    "pentatonic_major",
                                    "pentatonic_minor",
                                    "blues",
                                    "dorian",
                                    "mixolydian",
                                    "none",
                                ],
                                "default": "none",
                                "description": "Filter notes to specific musical scale",
                            },
                        },
                        "required": ["track_id", "clip_id", "notes"],
                    },
                ),
                types.Tool(
                    name="analyze_harmony",
                    description="Analyze harmonic content and suggest chord progressions with music theory intelligence",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notes": {
                                "type": "array",
                                "items": {"type": "integer", "minimum": 0, "maximum": 127},
                                "description": "MIDI note numbers to analyze",
                            },
                            "suggest_progressions": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include chord progression suggestions",
                            },
                            "genre": {
                                "type": "string",
                                "enum": ["pop", "jazz", "electronic", "rock", "classical"],
                                "default": "pop",
                                "description": "Musical genre for progression suggestions",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="analyze_tempo",
                    description="Analyze tempo and provide genre-appropriate suggestions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "current_bpm": {
                                "type": "number",
                                "description": "Current BPM (will auto-detect if not provided)",
                                "minimum": 20,
                                "maximum": 999,
                            },
                            "genre": {
                                "type": "string",
                                "description": "Musical genre for tempo optimization",
                            },
                            "energy_level": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "default": "medium",
                                "description": "Desired energy level",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="mix_analysis",
                    description="Analyze mix balance and suggest professional mixing improvements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "analyze_levels": {
                                "type": "boolean",
                                "default": True,
                                "description": "Analyze volume levels and dynamics",
                            },
                            "analyze_frequency": {
                                "type": "boolean",
                                "default": True,
                                "description": "Analyze frequency balance",
                            },
                            "target_lufs": {
                                "type": "number",
                                "default": -14,
                                "description": "Target LUFS for streaming platforms",
                            },
                            "platform": {
                                "type": "string",
                                "enum": [
                                    "spotify",
                                    "apple_music",
                                    "youtube",
                                    "tidal",
                                    "soundcloud",
                                ],
                                "default": "spotify",
                                "description": "Target streaming platform",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="arrangement_suggestions",
                    description="Get intelligent arrangement and song structure suggestions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "song_length": {
                                "type": "number",
                                "description": "Current song length in bars",
                                "minimum": 0,
                            },
                            "genre": {
                                "type": "string",
                                "description": "Musical genre for structure suggestions",
                            },
                            "current_structure": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Current song sections (e.g., ['intro', 'verse', 'chorus'])",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="get_clip_content",
                    description="Get MIDI notes and content from a clip in Ableton Live",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "track_id": {
                                "type": "integer",
                                "description": "Track ID (0-based index)",
                                "minimum": 0,
                            },
                            "clip_id": {
                                "type": "integer",
                                "description": "Clip slot ID (0-based index)",
                                "minimum": 0,
                            },
                        },
                        "required": ["track_id", "clip_id"],
                    },
                ),
                types.Tool(
                    name="refresh_song_data",
                    description="Refresh cached song data from Ableton Live. Use this when you've made manual changes in Ableton (renamed tracks, added/deleted tracks, etc.) and need to sync the cached state.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                types.Tool(
                    name="scene_operations",
                    description="Perform operations on Ableton Live scenes (fire, create, delete, rename, recolor)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "fire",
                                    "get_info",
                                    "create",
                                    "delete",
                                    "set_name",
                                    "set_color",
                                ],
                                "description": "Scene operation to perform",
                            },
                            "scene_id": {
                                "type": "integer",
                                "description": "Scene ID (0-based index)",
                                "minimum": 0,
                            },
                            "name": {
                                "type": "string",
                                "description": "Scene name for set_name action",
                            },
                            "color": {
                                "type": "integer",
                                "description": "Color index (0-69) for set_color action",
                                "minimum": 0,
                                "maximum": 69,
                            },
                            "index": {
                                "type": "integer",
                                "description": "Index for scene creation (-1 for end)",
                            },
                        },
                        "required": ["action"],
                    },
                ),
                types.Tool(
                    name="song_properties",
                    description="Get and set song-level properties (swing, metronome, overdub, loop, tempo)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "get_properties",
                                    "set_swing",
                                    "set_metronome",
                                    "set_overdub",
                                    "set_loop",
                                    "set_loop_start",
                                    "set_loop_length",
                                    "set_tempo",
                                ],
                                "description": "Song property operation to perform",
                            },
                            "value": {
                                "type": "number",
                                "description": "Numeric value for swing/loop_start/loop_length/tempo",
                            },
                            "enabled": {
                                "type": "boolean",
                                "description": "Boolean value for metronome/overdub/loop toggle",
                            },
                        },
                        "required": ["action"],
                    },
                ),
                types.Tool(
                    name="clip_operations",
                    description="Perform operations on Ableton Live clips (get info, rename, resize, loop settings, fire, stop, create, delete)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "get_info",
                                    "set_name",
                                    "set_length",
                                    "set_loop_start",
                                    "set_loop_end",
                                    "fire",
                                    "stop",
                                    "create",
                                    "delete",
                                    "has_clip",
                                ],
                                "description": "Clip operation to perform",
                            },
                            "track_id": {
                                "type": "integer",
                                "description": "Track ID (0-based index)",
                                "minimum": 0,
                            },
                            "clip_id": {
                                "type": "integer",
                                "description": "Clip slot ID (0-based index)",
                                "minimum": 0,
                            },
                            "name": {
                                "type": "string",
                                "description": "Clip name for set_name action",
                            },
                            "length": {
                                "type": "number",
                                "description": "Clip length in beats for set_length/create",
                                "minimum": 0.1,
                            },
                            "value": {
                                "type": "number",
                                "description": "Value for loop_start/loop_end",
                            },
                        },
                        "required": ["action", "track_id", "clip_id"],
                    },
                ),
                types.Tool(
                    name="return_track_operations",
                    description="Control Ableton Live return tracks and master track (volume, pan, mute, create)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "get_info",
                                    "set_volume",
                                    "set_pan",
                                    "mute",
                                    "set_name",
                                    "create",
                                    "get_master_info",
                                    "set_master_volume",
                                    "set_master_pan",
                                ],
                                "description": "Return/master track operation",
                            },
                            "return_id": {
                                "type": "integer",
                                "description": "Return track ID (0-based index)",
                                "minimum": 0,
                            },
                            "value": {
                                "type": "number",
                                "description": "Value for volume/pan operations",
                            },
                            "name": {
                                "type": "string",
                                "description": "Name for set_name action",
                            },
                        },
                        "required": ["action"],
                    },
                ),
                types.Tool(
                    name="device_operations",
                    description="Control Ableton Live devices and their parameters (get info, toggle active, get/set parameters)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "get_info",
                                    "set_active",
                                    "get_parameter",
                                    "set_parameter",
                                    "list_parameters",
                                ],
                                "description": "Device operation to perform",
                            },
                            "track_id": {
                                "type": "integer",
                                "description": "Track ID (0-based index)",
                                "minimum": 0,
                            },
                            "device_id": {
                                "type": "integer",
                                "description": "Device ID (0-based index)",
                                "minimum": 0,
                            },
                            "parameter_id": {
                                "type": "integer",
                                "description": "Parameter ID for get/set parameter",
                                "minimum": 0,
                            },
                            "value": {
                                "type": "number",
                                "description": "Value for set_parameter",
                            },
                            "active": {
                                "type": "boolean",
                                "description": "Active state for set_active",
                            },
                        },
                        "required": ["action", "track_id", "device_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            """Handle tool calls with comprehensive error handling."""
            try:
                logger.info("Tool called", tool=name, arguments=arguments)
                result: UseCaseResult

                if name == "connect_ableton":
                    connect_req = ConnectToAbletonRequest(
                        host=arguments.get("host", "127.0.0.1"),
                        send_port=arguments.get("send_port", 11000),
                        receive_port=arguments.get("receive_port", 11001),
                    )
                    result = await self._connect_use_case.execute(connect_req)

                elif name == "transport_control":
                    transport_req = TransportControlRequest(
                        action=arguments["action"], value=arguments.get("value")
                    )
                    result = await self._transport_use_case.execute(transport_req)

                elif name == "get_song_info":
                    song_info_req = GetSongInfoRequest(
                        include_tracks=arguments.get("include_tracks", True),
                        include_devices=arguments.get("include_devices", True),
                        include_clips=arguments.get("include_clips", False),
                    )
                    result = await self._song_info_use_case.execute(song_info_req)

                elif name == "track_operations":
                    track_ops_req = TrackOperationRequest(
                        action=arguments["action"],
                        track_id=arguments.get("track_id"),
                        value=arguments.get("value"),
                        name=arguments.get("name"),
                        track_type=arguments.get("track_type"),
                        color=arguments.get("color"),
                        send_id=arguments.get("send_id"),
                    )
                    result = await self._track_ops_use_case.execute(track_ops_req)

                elif name == "add_notes":
                    add_notes_req = AddNotesRequest(
                        track_id=arguments["track_id"],
                        clip_id=arguments["clip_id"],
                        notes=arguments["notes"],
                        quantize=arguments.get("quantize", False),
                        scale_filter=arguments.get("scale_filter"),
                    )
                    result = await self._add_notes_use_case.execute(add_notes_req)

                elif name == "analyze_harmony":
                    harmony_req = AnalyzeHarmonyRequest(
                        notes=arguments.get("notes", []),
                        suggest_progressions=arguments.get("suggest_progressions", False),
                        genre=arguments.get("genre", "pop"),
                    )
                    result = await self._harmony_analysis_use_case.execute(harmony_req)

                elif name == "analyze_tempo":
                    tempo_req = AnalyzeTempoRequest(
                        current_bpm=arguments.get("current_bpm"),
                        genre=arguments.get("genre"),
                        energy_level=arguments.get("energy_level", "medium"),
                    )
                    result = await self._tempo_analysis_use_case.execute(tempo_req)

                elif name == "mix_analysis":
                    mix_req = MixAnalysisRequest(
                        analyze_levels=arguments.get("analyze_levels", True),
                        analyze_frequency=arguments.get("analyze_frequency", True),
                        target_lufs=arguments.get("target_lufs", -14.0),
                        platform=arguments.get("platform", "spotify"),
                    )
                    result = await self._mix_analysis_use_case.execute(mix_req)

                elif name == "arrangement_suggestions":
                    arrangement_req = ArrangementSuggestionsRequest(
                        song_length=arguments.get("song_length"),
                        genre=arguments.get("genre"),
                        current_structure=arguments.get("current_structure"),
                    )
                    result = await self._arrangement_suggestions_use_case.execute(arrangement_req)

                elif name == "get_clip_content":
                    clip_content_req = GetClipContentRequest(
                        track_id=arguments["track_id"], clip_id=arguments["clip_id"]
                    )
                    result = await self._clip_content_use_case.execute(clip_content_req)

                elif name == "refresh_song_data":
                    result = await self._refresh_song_data_use_case.execute()

                elif name == "scene_operations":
                    scene_req = SceneOperationRequest(
                        action=arguments["action"],
                        scene_id=arguments.get("scene_id"),
                        name=arguments.get("name"),
                        color=arguments.get("color"),
                        index=arguments.get("index"),
                    )
                    result = await self._scene_ops_use_case.execute(scene_req)

                elif name == "song_properties":
                    song_prop_req = SongPropertyRequest(
                        action=arguments["action"],
                        value=arguments.get("value"),
                        enabled=arguments.get("enabled"),
                    )
                    result = await self._song_property_use_case.execute(song_prop_req)

                elif name == "clip_operations":
                    clip_ops_req = ClipOperationRequest(
                        action=arguments["action"],
                        track_id=arguments["track_id"],
                        clip_id=arguments["clip_id"],
                        name=arguments.get("name"),
                        length=arguments.get("length"),
                        value=arguments.get("value"),
                    )
                    result = await self._clip_ops_use_case.execute(clip_ops_req)

                elif name == "return_track_operations":
                    return_req = ReturnTrackOperationRequest(
                        action=arguments["action"],
                        return_id=arguments.get("return_id"),
                        value=arguments.get("value"),
                        name=arguments.get("name"),
                    )
                    result = await self._return_track_ops_use_case.execute(return_req)

                elif name == "device_operations":
                    device_req = DeviceOperationRequest(
                        action=arguments["action"],
                        track_id=arguments["track_id"],
                        device_id=arguments["device_id"],
                        parameter_id=arguments.get("parameter_id"),
                        value=arguments.get("value"),
                        active=arguments.get("active"),
                    )
                    result = await self._device_ops_use_case.execute(device_req)

                else:
                    result = UseCaseResult(
                        success=False, message=f"Unknown tool: {name}", error_code="UNKNOWN_TOOL"
                    )

                return await self._format_result(result)

            except AbletonMCPError as e:
                logger.error("MCP error", tool=name, error=str(e))
                return [types.TextContent(type="text", text=f"[ERROR] {e.error_code}: {e.message}")]

            except Exception as e:
                logger.error("Unexpected error", tool=name, error=str(e))
                return [
                    types.TextContent(
                        type="text", text=f"[ERROR] Unexpected error in {name}: {e!s}"
                    )
                ]

    async def _format_result(self, result: UseCaseResult) -> list[types.TextContent]:
        """Format use case result for MCP response."""
        if result.success:
            if result.data:
                # Format structured data nicely
                formatted_data = await self._format_data(result.data)
                message = result.message or "Operation completed successfully"
                return [types.TextContent(type="text", text=f"{message}\n\n{formatted_data}")]
            else:
                return [
                    types.TextContent(
                        type="text", text=result.message or "Operation completed successfully"
                    )
                ]
        else:
            error_prefix = "[ERROR]"
            if result.error_code:
                error_prefix += f" [{result.error_code}]"

            return [types.TextContent(type="text", text=f"{error_prefix} {result.message}")]

    async def _format_data(self, data: Any) -> str:
        """Format data for display with music-specific formatting."""
        if isinstance(data, dict):
            formatted_lines = []

            # Special formatting for song info
            if "tempo" in data and "time_signature" in data:
                formatted_lines.append("**Song Information**")
                formatted_lines.append(f"- Name: {data.get('name', 'Untitled')}")
                formatted_lines.append(f"- Tempo: {data.get('tempo')} BPM")
                formatted_lines.append(f"- Time Signature: {data.get('time_signature')}")
                if data.get("key"):
                    formatted_lines.append(f"- Key: {data.get('key')}")
                formatted_lines.append(
                    f"- Transport: {data.get('transport_state', 'unknown').title()}"
                )

                if data.get("tracks"):
                    formatted_lines.append(f"\n**Tracks ({len(data['tracks'])})**")
                    for i, track in enumerate(data["tracks"][:5]):  # Show first 5
                        track_info = f"- {i}: {track['name']} ({track['type']})"
                        if track.get("muted"):
                            track_info += " [MUTED]"
                        if track.get("soloed"):
                            track_info += " [SOLO]"
                        formatted_lines.append(track_info)

                    if len(data["tracks"]) > 5:
                        formatted_lines.append(f"... and {len(data['tracks']) - 5} more tracks")

            # Special formatting for harmony analysis
            elif "detected_keys" in data:
                formatted_lines.append("**Harmony Analysis**")

                if data["detected_keys"]:
                    best_key = data["detected_keys"][0]
                    formatted_lines.append(
                        f"- **Primary Key**: {best_key['root_name']} {best_key['mode']} ({best_key['confidence']:.1%} confidence)"
                    )

                    if len(data["detected_keys"]) > 1:
                        formatted_lines.append("- **Alternatives**:")
                        for key in data["detected_keys"][1:3]:
                            formatted_lines.append(
                                f"  - {key['root_name']} {key['mode']} ({key['confidence']:.1%})"
                            )

                if data.get("chord_progressions"):
                    formatted_lines.append("\n**Suggested Chord Progressions**:")
                    for _i, progression in enumerate(data["chord_progressions"][:3]):
                        note_names = [
                            "C",
                            "C#",
                            "D",
                            "D#",
                            "E",
                            "F",
                            "F#",
                            "G",
                            "G#",
                            "A",
                            "A#",
                            "B",
                        ]
                        chord_names = [note_names[root] for root in progression]
                        formatted_lines.append(f"- {' - '.join(chord_names)}")

            # Special formatting for tempo analysis
            elif "current_tempo" in data:
                formatted_lines.append("**Tempo Analysis**")
                formatted_lines.append(f"- Current: {data['current_tempo']} BPM")

                if data.get("suggestions", {}).get("genre_optimal"):
                    formatted_lines.append(
                        f"- Optimal for genre: {data['suggestions']['genre_optimal']} BPM"
                    )

                if data.get("suggestions", {}).get("relationships"):
                    rels = data["suggestions"]["relationships"]
                    formatted_lines.append("\n**Related Tempos**:")
                    formatted_lines.append(f"- Half-time: {rels.get('half_time', 0):.0f} BPM")
                    formatted_lines.append(f"- Double-time: {rels.get('double_time', 0):.0f} BPM")

            # Special formatting for clip content
            elif "note_count" in data and "notes" in data:
                formatted_lines.append("**Clip Content**")
                formatted_lines.append(f"- Track: {data.get('track_id', 'N/A')}")
                formatted_lines.append(f"- Clip: {data.get('clip_id', 'N/A')}")
                formatted_lines.append(f"- Total Notes: {data['note_count']}")

                if data["notes"]:
                    formatted_lines.append("\n**Notes**:")
                    # Show first 20 notes to avoid overwhelming output
                    display_notes = data["notes"][:20]
                    for note in display_notes:
                        note_name = note.get("note_name", f"MIDI {note['pitch']}")
                        mute_str = " [MUTED]" if note.get("mute") else ""
                        formatted_lines.append(
                            f"- {note_name} | Start: {note['start']:.2f} | "
                            f"Duration: {note['duration']:.2f} | "
                            f"Velocity: {note['velocity']}{mute_str}"
                        )

                    if len(data["notes"]) > 20:
                        formatted_lines.append(f"... and {len(data['notes']) - 20} more notes")
                else:
                    formatted_lines.append("\n(No notes in this clip)")

            # Default formatting
            else:
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        formatted_lines.append(f"- {key}: {str(value)[:100]}...")
                    else:
                        formatted_lines.append(f"- {key}: {value}")

            return "\n".join(formatted_lines)

        return str(data)

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Ableton Live MCP Server")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ableton-live-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(), experimental_capabilities={}
                    ),
                ),
            )
