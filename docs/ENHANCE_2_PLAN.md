# Plan: Implement Remaining ~60% of AbletonOSC Capabilities

## Gap Analysis

**Currently implemented:** 47 OSC paths, 38 gateway methods, 11 MCP tools
**Documented in reference:** ~120+ OSC paths across all object types

### What's Missing (by category)

| Category | Implemented | Missing | Gap |
|----------|------------|---------|-----|
| Song/Transport | 11 paths | ~25 paths (swing, metronome, overdub, loop, navigation, undo/redo, session record, capture MIDI) | Scene, loop, global settings, navigation |
| Scenes | 0 paths | 7 paths (fire, get/set name, get/set color, create) | Entirely missing |
| Clip Properties | 7 paths (fire, stop, create, delete, notes) | 9 paths (name, length, loop start/end, is_playing, position, has_clip) | Properties beyond notes |
| Track Enhancements | 16 paths | 8 paths (color, sends, stop_all_clips, duplicate, device listing) | Sends & routing |
| Return/Master Tracks | 0 paths | ~10 paths (create return, return volume/pan/mute, master volume/pan) | Entirely missing |
| Device Enhancements | 3 paths | 8 paths (name, class_name, is_active, individual param queries) | Per-parameter queries |
| View/Navigation | 0 paths | 4 paths (selected track/scene get/set) | Entirely missing |
| Application | 0 paths | 2 paths (test, version) | Connection verification |

---

## Implementation Phases

### Phase 1: Scene Operations (NEW MCP tool: `scene_operations`)

**Impact:** Unlocks Ableton's session view workflow. Currently zero scene support.

#### Layer-by-layer changes:

**1a. Gateway port interface** (`domain/ports.py`)
```
+ get_num_scenes() -> int
+ fire_scene(scene_id: int) -> None
+ get_scene_name(scene_id: int) -> str
+ set_scene_name(scene_id: int, name: str) -> None
+ get_scene_color(scene_id: int) -> int
+ set_scene_color(scene_id: int, color: int) -> None
+ create_scene(index: int) -> None
+ delete_scene(scene_id: int) -> None
```

**1b. Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths to add:
  /live/song/get/num_scenes          (request-response)
  /live/scene/fire [scene_id]        (fire-and-forget)
  /live/scene/get/name [scene_id]    (request-response)
  /live/scene/set/name [scene_id, name] (fire-and-forget)
  /live/scene/get/color [scene_id]   (request-response)
  /live/scene/set/color [scene_id, color] (fire-and-forget)
  /live/song/create_scene [index]    (fire-and-forget)
  /live/song/delete_scene [scene_id] (fire-and-forget)
```

**1c. Service adapter** (`adapters/service_adapters.py`)
```
+ class AbletonSceneService:
    __init__(gateway: AbletonGateway)
    get_num_scenes() -> int
    fire_scene(scene_id) -> None
    get_scene_info(scene_id) -> dict
    set_scene_name(scene_id, name) -> None
    set_scene_color(scene_id, color) -> None
    create_scene(index) -> None
    delete_scene(scene_id) -> None
```

**1d. Use case** (`application/use_cases.py`)
```
+ @dataclass SceneOperationRequest:
    action: str  # fire, get_info, create, delete, set_name, set_color
    scene_id: int | None
    name: str | None
    color: int | None
    index: int | None

+ class SceneOperationsUseCase(UseCase):
    __init__(scene_service, song_repository)
    execute(request) -> UseCaseResult
```

**1e. DI wiring** (`container.py`)
```
+ scene_service = providers.Factory(AbletonSceneService, gateway=ableton_gateway)
+ scene_ops_use_case = providers.Factory(SceneOperationsUseCase, ...)
+ Add to mcp_server factory params
```

**1f. MCP tool** (`interfaces/mcp_server.py`)
```
+ Tool "scene_operations":
    action: enum [fire, get_info, create, delete, set_name, set_color]
    scene_id: int (optional)
    name: string (optional)
    color: int (optional, 0-69)
    index: int (optional, for create)
```

**1g. Tests** (`tests/unit/test_use_cases.py`)
```
+ class TestSceneOperationsUseCase:
    test_fire_scene
    test_get_scene_info
    test_create_scene
    test_delete_scene
    test_set_scene_name
```

---

### Phase 2: Enhanced Transport & Song Properties (EXTEND `transport_control` + `get_song_info`)

**Impact:** Adds loop control, swing, metronome, undo/redo, navigation - fundamental DAW controls.

#### 2A: Transport extensions

**Gateway port** (`domain/ports.py`)
```
+ continue_playing() -> None
+ stop_all_clips() -> None
+ tap_tempo() -> None
+ undo() -> None
+ redo() -> None
+ capture_midi() -> None
+ trigger_session_record() -> None
+ jump_by(beats: float) -> None
+ jump_to(time: float) -> None
+ jump_to_next_cue() -> None
+ jump_to_prev_cue() -> None
```

**Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths:
  /live/song/continue_playing        (fire-and-forget)
  /live/song/stop_all_clips          (fire-and-forget)
  /live/song/tap_tempo               (fire-and-forget)
  /live/song/undo                    (fire-and-forget)
  /live/song/redo                    (fire-and-forget)
  /live/song/capture_midi            (fire-and-forget)
  /live/song/trigger_session_record  (fire-and-forget)
  /live/song/jump_by [beats]         (fire-and-forget)
  /live/song/jump_to [time]          (fire-and-forget)
  /live/song/jump_to_next_cue        (fire-and-forget)
  /live/song/jump_to_prev_cue        (fire-and-forget)
```

**Service adapter** (`adapters/service_adapters.py`)
```
Extend AbletonTransportService:
  + continue_playing()
  + stop_all_clips()
  + tap_tempo()
  + undo()
  + redo()
  + capture_midi()
  + trigger_session_record()
  + jump_by(beats)
  + jump_to(time)
  + jump_to_next_cue()
  + jump_to_prev_cue()
```

**MCP tool extension** (`interfaces/mcp_server.py`)
```
Extend transport_control action enum:
  + continue, stop_all_clips, tap_tempo, undo, redo,
    capture_midi, session_record, jump_by, jump_to,
    next_cue, prev_cue
```

**Use case** (`application/use_cases.py`)
```
Extend TransportControlUseCase.execute() with new action handlers
```

#### 2B: Song property getters/setters

**Gateway port** (`domain/ports.py`)
```
+ get_swing_amount() -> float
+ set_swing_amount(swing: float) -> None
+ get_metronome() -> bool
+ set_metronome(enabled: bool) -> None
+ get_overdub() -> bool
+ set_overdub(enabled: bool) -> None
+ get_song_length() -> float
+ get_loop() -> bool
+ set_loop(enabled: bool) -> None
+ get_loop_start() -> float
+ set_loop_start(start: float) -> None
+ get_loop_length() -> float
+ set_loop_length(length: float) -> None
+ get_record_mode() -> bool
+ get_session_record() -> bool
+ get_punch_in() -> bool
+ get_punch_out() -> bool
+ get_num_return_tracks() -> int
```

**Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths:
  /live/song/get/swing_amount                (request-response)
  /live/song/set/swing_amount [float]        (fire-and-forget)
  /live/song/get/metronome                   (request-response)
  /live/song/set/metronome [bool]            (fire-and-forget)
  /live/song/get/overdub                     (request-response)
  /live/song/set/overdub [bool]              (fire-and-forget)
  /live/song/get/song_length                 (request-response)
  /live/song/get/loop                        (request-response)
  /live/song/set/loop [bool]                 (fire-and-forget)
  /live/song/get/loop_start                  (request-response)
  /live/song/set/loop_start [float]          (fire-and-forget)
  /live/song/get/loop_length                 (request-response)
  /live/song/set/loop_length [float]         (fire-and-forget)
  /live/song/get/record_mode                 (request-response)
  /live/song/get/session_record              (request-response)
  /live/song/get/punch_in                    (request-response)
  /live/song/get/punch_out                   (request-response)
  /live/song/get/num_return_tracks           (request-response)
```

**MCP tool extension** - Extend `get_song_info` response to include:
```
+ swing_amount, metronome, overdub, song_length
+ loop (on/off, start, length)
+ num_scenes, num_return_tracks
+ record_mode, session_record, punch_in, punch_out
```

**NEW MCP tool: `song_properties`** for setting song-level values:
```
Tool "song_properties":
    action: enum [set_swing, set_metronome, set_overdub, set_loop, set_loop_start, set_loop_length, set_tempo]
    value: number | bool
```

---

### Phase 3: Clip Operations (NEW MCP tool: `clip_operations`)

**Impact:** Enables full clip manipulation beyond just adding notes.

**Gateway port** (`domain/ports.py`)
```
+ get_clip_name(track_id, clip_id) -> str
+ set_clip_name(track_id, clip_id, name) -> None
+ get_clip_length(track_id, clip_id) -> float
+ set_clip_length(track_id, clip_id, length) -> None
+ get_clip_loop_start(track_id, clip_id) -> float
+ set_clip_loop_start(track_id, clip_id, start) -> None
+ get_clip_loop_end(track_id, clip_id) -> float
+ set_clip_loop_end(track_id, clip_id, end) -> None
+ get_clip_is_playing(track_id, clip_id) -> bool
+ get_clip_playing_position(track_id, clip_id) -> float
+ has_clip(track_id, clip_id) -> bool
```

**Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths:
  /live/clip/get/name [track_id, clip_id]               (request-response)
  /live/clip/set/name [track_id, clip_id, name]          (fire-and-forget)
  /live/clip/get/length [track_id, clip_id]              (request-response)
  /live/clip/set/length [track_id, clip_id, length]      (fire-and-forget)
  /live/clip/get/loop_start [track_id, clip_id]          (request-response)
  /live/clip/set/loop_start [track_id, clip_id, start]   (fire-and-forget)
  /live/clip/get/loop_end [track_id, clip_id]            (request-response)
  /live/clip/set/loop_end [track_id, clip_id, end]       (fire-and-forget)
  /live/clip/get/is_playing [track_id, clip_id]          (request-response)
  /live/clip/get/playing_position [track_id, clip_id]    (request-response)
  /live/clip_slot/get/has_clip [track_id, clip_id]       (request-response)
```

**Service adapter** (`adapters/service_adapters.py`)
```
Extend AbletonClipService:
  + get_clip_name(track_id, clip_id) -> str
  + set_clip_name(track_id, clip_id, name)
  + get_clip_length(track_id, clip_id) -> float
  + set_clip_length(track_id, clip_id, length)
  + get_clip_loop_start(track_id, clip_id) -> float
  + set_clip_loop_start(track_id, clip_id, start)
  + get_clip_loop_end(track_id, clip_id) -> float
  + set_clip_loop_end(track_id, clip_id, end)
  + get_clip_is_playing(track_id, clip_id) -> bool
  + get_clip_playing_position(track_id, clip_id) -> float
  + has_clip(track_id, clip_id) -> bool
```

**Use case** (`application/use_cases.py`)
```
+ @dataclass ClipOperationRequest:
    action: str  # get_info, set_name, set_length, set_loop_start, set_loop_end,
                 #  fire, stop, create, delete, has_clip
    track_id: int
    clip_id: int
    name: str | None
    length: float | None
    value: float | None

+ class ClipOperationsUseCase(UseCase):
    __init__(clip_service, song_repository)
    execute(request) -> UseCaseResult
```

**MCP tool** (`interfaces/mcp_server.py`)
```
+ Tool "clip_operations":
    action: enum [get_info, set_name, set_length, set_loop_start, set_loop_end,
                  fire, stop, create, delete, has_clip]
    track_id: int (required)
    clip_id: int (required)
    name: string (optional)
    length: number (optional)
    value: number (optional)
```

---

### Phase 4: Track Enhancements (EXTEND `track_operations`)

**Impact:** Adds color, send/return routing, clip stopping, track duplication.

**Gateway port** (`domain/ports.py`)
```
+ get_track_color(track_id) -> int
+ set_track_color(track_id, color: int) -> None
+ get_track_send(track_id, send_id) -> float
+ set_track_send(track_id, send_id, amount: float) -> None
+ stop_all_track_clips(track_id) -> None
+ duplicate_track(track_id) -> None
+ get_track_num_devices(track_id) -> int
+ get_track_devices(track_id) -> list[str]
```

**Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths:
  /live/track/get/color [track_id]                    (request-response)
  /live/track/set/color [track_id, color]             (fire-and-forget)
  /live/track/get/send [track_id, send_id]            (request-response)
  /live/track/set/send [track_id, send_id, amount]    (fire-and-forget)
  /live/track/stop_all_clips [track_id]               (fire-and-forget)
  /live/song/duplicate_track [track_id]               (fire-and-forget)
  /live/track/get/num_devices [track_id]              (request-response)
  /live/track/get/devices [track_id]                  (request-response)
```

**Use case extension** (`application/use_cases.py`)
```
Extend TrackOperationsUseCase with new actions:
  + set_color, get_send, set_send, stop_all_clips, duplicate
```

**MCP tool extension** (`interfaces/mcp_server.py`)
```
Extend track_operations action enum:
  + set_color, set_send, stop_all_clips, duplicate
Add parameters:
  + color: int (0-69)
  + send_id: int
```

---

### Phase 5: Return Tracks & Master Track (NEW MCP tool: `return_track_operations`)

**Impact:** Enables send/return mixing workflows - core to Ableton mixing.

**Gateway port** (`domain/ports.py`)
```
+ create_return_track() -> None
+ get_return_track_volume(return_id) -> float
+ set_return_track_volume(return_id, volume: float) -> None
+ get_return_track_pan(return_id) -> float
+ set_return_track_pan(return_id, pan: float) -> None
+ get_return_track_mute(return_id) -> bool
+ set_return_track_mute(return_id, mute: bool) -> None
+ get_return_track_name(return_id) -> str
+ set_return_track_name(return_id, name: str) -> None
+ get_master_volume() -> float
+ set_master_volume(volume: float) -> None
+ get_master_pan() -> float
+ set_master_pan(pan: float) -> None
```

**Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths:
  /live/song/create_return_track                      (fire-and-forget)
  /live/return_track/get/volume [return_id]            (request-response)
  /live/return_track/set/volume [return_id, volume]    (fire-and-forget)
  /live/return_track/get/panning [return_id]           (request-response)
  /live/return_track/set/panning [return_id, pan]      (fire-and-forget)
  /live/return_track/get/mute [return_id]              (request-response)
  /live/return_track/set/mute [return_id, mute]        (fire-and-forget)
  /live/return_track/get/name [return_id]              (request-response)
  /live/return_track/set/name [return_id, name]        (fire-and-forget)
  /live/master_track/get/volume                        (request-response)
  /live/master_track/set/volume [volume]               (fire-and-forget)
  /live/master_track/get/panning                       (request-response)
  /live/master_track/set/panning [pan]                 (fire-and-forget)
```

**Service adapter** (`adapters/service_adapters.py`)
```
+ class AbletonReturnTrackService:
    __init__(gateway)
    create_return_track()
    get_return_track_info(return_id) -> dict
    set_return_track_volume(return_id, volume)
    set_return_track_pan(return_id, pan)
    set_return_track_mute(return_id, mute)
    set_return_track_name(return_id, name)
    get_master_info() -> dict
    set_master_volume(volume)
    set_master_pan(pan)
```

**Use case** (`application/use_cases.py`)
```
+ @dataclass ReturnTrackOperationRequest:
    action: str  # get_info, set_volume, set_pan, mute, set_name, create,
                 #  get_master_info, set_master_volume, set_master_pan
    return_id: int | None
    value: float | None
    name: str | None

+ class ReturnTrackOperationsUseCase(UseCase)
```

**MCP tool** (`interfaces/mcp_server.py`)
```
+ Tool "return_track_operations":
    action: enum [get_info, set_volume, set_pan, mute, set_name, create,
                  get_master_info, set_master_volume, set_master_pan]
    return_id: int (optional)
    value: number (optional)
    name: string (optional)
```

---

### Phase 6: Device Operations Enhancement (NEW MCP tool: `device_operations`)

**Impact:** Enables querying individual device parameters, reading display values, toggling devices.

**Gateway port** (`domain/ports.py`)
```
+ get_device_name(track_id, device_id) -> str
+ get_device_class_name(track_id, device_id) -> str
+ get_device_num_parameters(track_id, device_id) -> int
+ get_device_is_active(track_id, device_id) -> bool
+ set_device_is_active(track_id, device_id, active: bool) -> None
+ get_device_parameter_value(track_id, device_id, param_id) -> float
+ get_device_parameter_name(track_id, device_id, param_id) -> str
+ get_device_parameter_display_value(track_id, device_id, param_id) -> str
+ get_device_parameter_min(track_id, device_id, param_id) -> float
+ get_device_parameter_max(track_id, device_id, param_id) -> float
```

**Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths:
  /live/device/get/name [track_id, device_id]                         (request-response)
  /live/device/get/class_name [track_id, device_id]                   (request-response)
  /live/device/get/num_parameters [track_id, device_id]               (request-response)
  /live/device/get/is_active [track_id, device_id]                    (request-response)
  /live/device/set/is_active [track_id, device_id, active]            (fire-and-forget)
  /live/device/get/parameter/value [track_id, device_id, param_id]    (request-response)
  /live/device/get/parameter/name [track_id, device_id, param_id]     (request-response)
  /live/device/get/parameter/display_value [track_id, device_id, param_id] (request-response)
  /live/device/get/parameter/min [track_id, device_id, param_id]      (request-response)
  /live/device/get/parameter/max [track_id, device_id, param_id]      (request-response)
```

**Service adapter** (`adapters/service_adapters.py`)
```
+ class AbletonDeviceService:
    __init__(gateway)
    get_device_info(track_id, device_id) -> dict
    set_device_active(track_id, device_id, active)
    get_parameter_info(track_id, device_id, param_id) -> dict
    set_parameter_value(track_id, device_id, param_id, value)
    get_all_parameters(track_id, device_id) -> list[dict]
```

**Use case** (`application/use_cases.py`)
```
+ @dataclass DeviceOperationRequest:
    action: str  # get_info, set_active, get_parameter, set_parameter, list_parameters
    track_id: int
    device_id: int
    parameter_id: int | None
    value: float | None
    active: bool | None

+ class DeviceOperationsUseCase(UseCase)
```

**MCP tool** (`interfaces/mcp_server.py`)
```
+ Tool "device_operations":
    action: enum [get_info, set_active, get_parameter, set_parameter, list_parameters]
    track_id: int (required)
    device_id: int (required)
    parameter_id: int (optional)
    value: number (optional)
    active: bool (optional)
```

---

### Phase 7: View/Navigation & Application (EXTEND `connect_ableton` + NEW internal usage)

**Impact:** Enables UI navigation and better connection verification.

**Gateway port** (`domain/ports.py`)
```
+ test_connection() -> bool
+ get_application_version() -> str
+ get_selected_track() -> int
+ set_selected_track(track_id: int) -> None
+ get_selected_scene() -> int
+ set_selected_scene(scene_id: int) -> None
```

**Gateway implementation** (`infrastructure/osc/gateway.py`)
```
OSC paths:
  /live/test                                    (request-response)
  /live/application/get/version                 (request-response)
  /live/view/get/selected_track                 (request-response)
  /live/view/set/selected_track [track_id]      (fire-and-forget)
  /live/view/get/selected_scene                 (request-response)
  /live/view/set/selected_scene [scene_id]      (fire-and-forget)
```

**Usage:**
- `test_connection()` replaces current `get_tempo()` check in `ConnectToAbletonUseCase`
- `get_application_version()` included in connect response
- View selection exposed through `track_operations` (extend action enum with `select`) and `scene_operations` (extend action enum with `select`)

---

## Files Modified Per Phase (Summary)

| File | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|------|----|----|----|----|----|----|-----|
| `domain/ports.py` | +8 | +28 | +11 | +8 | +13 | +10 | +6 |
| `infrastructure/osc/gateway.py` | +8 | +28 | +11 | +8 | +13 | +10 | +6 |
| `adapters/service_adapters.py` | +new class | +extend | +extend | +extend | +new class | +new class | +extend |
| `application/use_cases.py` | +new UC | +extend UC | +new UC | +extend UC | +new UC | +new UC | +extend UC |
| `interfaces/mcp_server.py` | +new tool | +extend 2 tools, +new tool | +new tool | +extend tool | +new tool | +new tool | +extend |
| `container.py` | +wire | +wire | +wire | — | +wire | +wire | — |
| `tests/unit/test_use_cases.py` | +tests | +tests | +tests | +tests | +tests | +tests | +tests |

**Total new MCP tools: 5** (`scene_operations`, `song_properties`, `clip_operations`, `return_track_operations`, `device_operations`)
**Extended MCP tools: 3** (`transport_control`, `track_operations`, `get_song_info`)
**Total new gateway methods: ~84**
**Total new OSC paths: ~84**

---

## Implementation Order & Dependencies

```
Phase 7 (connection/view) ──────────────────────────────────┐
Phase 1 (scenes) ──────────────────────────────────────────┐ │
Phase 2A (transport extensions) ───────────────────────────┤ │
Phase 2B (song properties) ────────────────────────────────┤ │
Phase 3 (clip operations) ─────────────────────────────────┤ │
Phase 4 (track enhancements) ──────────────────────────────┤ │
Phase 5 (return/master tracks) ─ requires Phase 4 (sends) ─┤ │
Phase 6 (device operations) ───────────────────────────────┘ │
                                                              │
All phases use /live/test from Phase 7 ◄──────────────────────┘
```

**Recommended execution order:**
1. Phase 7 first (small, improves connection reliability for all subsequent work)
2. Phases 1-4 in parallel (independent of each other)
3. Phase 5 after Phase 4 (sends depend on return track awareness)
4. Phase 6 last (independent but largest single phase)

---

## Verification Plan

### Per-Phase Testing
- **Unit tests**: Mock gateway, test each use case action. Follow existing pattern in `tests/unit/test_use_cases.py`.
- **Run quality checks**: `black`, `ruff`, `mypy`, `pytest` after each phase.

### End-to-End Verification (with Ableton Live running)
After all phases, verify these workflows:

1. **Scene workflow**: "Create 4 scenes named Intro/Verse/Chorus/Bridge, launch scene 2"
2. **Loop control**: "Set loop from bar 5 to bar 13, enable loop, set swing to 40%"
3. **Clip manipulation**: "Get clip info, rename it, change loop end to bar 8"
4. **Track routing**: "Set track 1 send A to 60%, set return A reverb mix to 80%"
5. **Device control**: "List parameters of device 0 on track 2, set filter frequency to 0.7"
6. **Transport**: "Undo last action, jump to bar 16, tap tempo"
7. **Master**: "Set master volume to 0.85, check master pan"

### CI Verification
- All existing tests must still pass
- New tests achieve coverage for all new use case paths
- `mypy`, `ruff`, `black` pass with zero errors
