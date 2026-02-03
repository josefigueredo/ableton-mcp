# Ableton Live - Complete Deep Dive Reference

## Table of Contents
1. [Live Object Model Overview](#live-object-model-overview)
2. [Core Object Hierarchy](#core-object-hierarchy)
3. [Song Object](#song-object)
4. [Track Objects](#track-objects)
5. [Clip Objects](#clip-objects)
6. [Device Objects](#device-objects)
7. [OSC Command Reference](#osc-command-reference)
8. [Session vs Arrangement Workflows](#session-vs-arrangement-workflows)
9. [Advanced Integration Patterns](#advanced-integration-patterns)
10. [Implementation Guidelines](#implementation-guidelines)

---

## Live Object Model Overview

### Architecture Principles
The Ableton Live Object Model (LOM) represents the entire Live application as a hierarchy of interconnected objects. Each object type has specific properties, methods, and child relationships that enable comprehensive programmatic control.

**Core Design Philosophy:**
- **Hierarchical Navigation:** Objects are accessed through parent-child paths
- **Zero-based Indexing:** All collections use 0-based indexing
- **Multiple Access Paths:** Objects can be reached via different hierarchical routes
- **Real-time Monitoring:** Observer pattern for property change notifications
- **Type Safety:** Strict data types with defined ranges and validation

### Access Methods
```python
ACCESS_METHODS = {
    'python_api': {
        'direct': 'Live.Application.get_application()',
        'objects': ['Song', 'Track', 'Clip', 'Device', 'DeviceParameter'],
        'limitations': 'Requires Max for Live or Control Surface script'
    },
    'osc_protocol': {
        'port_send': 11000,
        'port_receive': 11001,
        'addressing': '/live/object_type/action/property',
        'wildcards': 'Supported for batch queries'
    },
    'max_for_live': {
        'objects': ['live.path', 'live.object', 'live.observer'],
        'javascript': 'Direct API access in JS devices'
    }
}
```

---

## Core Object Hierarchy

### Root Structure
```
Live Application
├── Live Set (Song)
│   ├── Tracks[]
│   │   ├── Clip Slots[]
│   │   │   └── Clips
│   │   ├── Devices[]
│   │   │   └── Parameters[]
│   │   └── Mixer Device
│   │       ├── Volume
│   │       ├── Panning
│   │       └── Sends[]
│   ├── Scenes[]
│   ├── Master Track
│   ├── Return Tracks[]
│   └── Browser
└── Control Surfaces[]
```

### Navigation Paths
```python
NAVIGATION_EXAMPLES = {
    'absolute_paths': {
        'first_track': 'live_set tracks 0',
        'clip_in_track': 'live_set tracks 2 clip_slots 0 clip',
        'device_parameter': 'live_set tracks 1 devices 0 parameters 5',
        'scene': 'live_set scenes 3'
    },
    'alternative_paths': {
        'same_clip': [
            'live_set tracks 2 clip_slots 0 clip',  # Via track
            'live_set scenes 0 clip_slots 2 clip'   # Via scene
        ]
    }
}
```

---

## Song Object

### Properties and Methods

#### Core Properties
```python
SONG_PROPERTIES = {
    # Transport
    'tempo': {'type': 'float', 'range': (20.0, 999.0), 'default': 120.0},
    'signature_numerator': {'type': 'int', 'range': (1, 99), 'default': 4},
    'signature_denominator': {'type': 'int', 'values': [2, 4, 8, 16], 'default': 4},
    'swing_amount': {'type': 'float', 'range': (0.0, 1.0), 'default': 0.0},
    'current_song_time': {'type': 'float', 'unit': 'beats'},
    'song_length': {'type': 'float', 'unit': 'beats', 'readonly': True},
    
    # Recording and Playback
    'is_playing': {'type': 'bool', 'readonly': True},
    'overdub': {'type': 'bool', 'default': False},
    'metronome': {'type': 'bool', 'default': False},
    'record_mode': {'type': 'bool', 'default': False},
    'punch_in': {'type': 'bool', 'default': False},
    'punch_out': {'type': 'bool', 'default': False},
    
    # Loop and Arrangement
    'loop': {'type': 'bool', 'default': False},
    'loop_start': {'type': 'float', 'unit': 'beats'},
    'loop_length': {'type': 'float', 'unit': 'beats'},
    'session_record': {'type': 'bool', 'default': False},
    'session_automation_record': {'type': 'bool', 'default': False},
    
    # Collections
    'tracks': {'type': 'list', 'readonly': True},
    'visible_tracks': {'type': 'list', 'readonly': True},
    'return_tracks': {'type': 'list', 'readonly': True},
    'scenes': {'type': 'list', 'readonly': True},
    'master_track': {'type': 'Track', 'readonly': True}
}
```

#### Transport Control Methods
```python
SONG_METHODS = {
    'playback': {
        'start_playing': {'params': [], 'description': 'Start playback from current position'},
        'stop_playing': {'params': [], 'description': 'Stop playback'},
        'continue_playing': {'params': [], 'description': 'Continue from stopped position'},
        'stop_all_clips': {'params': [], 'description': 'Stop all playing clips'},
        'tap_tempo': {'params': [], 'description': 'Tap to set tempo'}
    },
    
    'recording': {
        'trigger_session_record': {'params': [], 'description': 'Start/stop session recording'},
        'capture_midi': {'params': [], 'description': 'Capture recent MIDI input'},
        'undo': {'params': [], 'description': 'Undo last action'},
        'redo': {'params': [], 'description': 'Redo last undone action'}
    },
    
    'structure': {
        'create_scene': {'params': ['index: int'], 'description': 'Create new scene'},
        'create_midi_track': {'params': ['index: int'], 'description': 'Create MIDI track'},
        'create_audio_track': {'params': ['index: int'], 'description': 'Create audio track'},
        'create_return_track': {'params': [], 'description': 'Create return track'},
        'delete_track': {'params': ['track_index: int'], 'description': 'Delete track'},
        'duplicate_track': {'params': ['track_index: int'], 'description': 'Duplicate track'}
    },
    
    'navigation': {
        'jump_by': {'params': ['amount: float'], 'description': 'Jump by beats'},
        'jump_to': {'params': ['time: float'], 'description': 'Jump to specific time'},
        'jump_to_next_cue': {'params': [], 'description': 'Jump to next arrangement cue'},
        'jump_to_prev_cue': {'params': [], 'description': 'Jump to previous arrangement cue'}
    }
}
```

#### OSC Commands for Song Control
```python
SONG_OSC_COMMANDS = {
    # Transport
    '/live/song/start_playing': {'params': [], 'response': None},
    '/live/song/stop_playing': {'params': [], 'response': None},
    '/live/song/continue_playing': {'params': [], 'response': None},
    
    # Tempo and Time
    '/live/song/set/tempo': {'params': ['bpm: float'], 'range': (20.0, 999.0)},
    '/live/song/get/tempo': {'params': [], 'response': 'float'},
    '/live/song/set/swing_amount': {'params': ['swing: float'], 'range': (0.0, 1.0)},
    '/live/song/get/current_song_time': {'params': [], 'response': 'float'},
    
    # Structure
    '/live/song/create_midi_track': {'params': ['index: int'], 'response': 'int (track_id)'},
    '/live/song/create_audio_track': {'params': ['index: int'], 'response': 'int (track_id)'},
    '/live/song/create_scene': {'params': ['index: int'], 'response': 'int (scene_id)'},
    '/live/song/delete_track': {'params': ['track_index: int'], 'response': None},
    
    # Global Settings
    '/live/song/set/metronome': {'params': ['enabled: bool'], 'response': None},
    '/live/song/get/metronome': {'params': [], 'response': 'bool'},
    '/live/song/set/overdub': {'params': ['enabled: bool'], 'response': None},
    '/live/song/get/overdub': {'params': [], 'response': 'bool'}
}
```

---

## Track Objects

### Track Types and Properties

#### Track Type Classification
```python
TRACK_TYPES = {
    'midi_track': {
        'description': 'Hosts MIDI clips and MIDI/Audio devices',
        'input_routing': ['midi_inputs', 'none'],
        'output_routing': ['master', 'external_out', 'resampling'],
        'monitoring': ['in', 'auto', 'off']
    },
    'audio_track': {
        'description': 'Hosts audio clips and audio devices only',
        'input_routing': ['audio_inputs', 'resampling', 'none'],
        'output_routing': ['master', 'external_out'],
        'monitoring': ['in', 'auto', 'off']
    },
    'return_track': {
        'description': 'Receives sends from other tracks',
        'input_routing': ['sends_only'],
        'output_routing': ['master', 'external_out'],
        'characteristics': ['no_clips', 'send_destination']
    },
    'master_track': {
        'description': 'Final output stage',
        'characteristics': ['single_instance', 'no_sends', 'no_clips']
    },
    'group_track': {
        'description': 'Contains grouped tracks',
        'characteristics': ['no_clips', 'contains_tracks', 'rack_device']
    }
}
```

#### Core Track Properties
```python
TRACK_PROPERTIES = {
    # Identification
    'name': {'type': 'string', 'editable': True, 'max_length': 255},
    'color': {'type': 'int', 'range': (0, 69), 'description': 'Color palette index'},
    'is_visible': {'type': 'bool', 'editable': True},
    'is_grouped': {'type': 'bool', 'readonly': True},
    'group_track': {'type': 'Track', 'readonly': True, 'nullable': True},
    
    # State
    'mute': {'type': 'bool', 'editable': True},
    'solo': {'type': 'bool', 'editable': True},
    'arm': {'type': 'bool', 'editable': True},
    'current_monitoring_state': {'type': 'int', 'values': [0, 1, 2]},  # Off, Auto, In
    
    # Audio/MIDI routing
    'has_midi_input': {'type': 'bool', 'readonly': True},
    'has_audio_input': {'type': 'bool', 'readonly': True},
    'has_midi_output': {'type': 'bool', 'readonly': True},
    'has_audio_output': {'type': 'bool', 'readonly': True},
    'input_routing_type': {'type': 'InputRoutingType', 'readonly': True},
    'output_routing_type': {'type': 'OutputRoutingType', 'readonly': True},
    
    # Collections
    'devices': {'type': 'list', 'readonly': True},
    'clip_slots': {'type': 'list', 'readonly': True},
    'mixer_device': {'type': 'MixerDevice', 'readonly': True}
}
```

### Mixer Device Properties
```python
MIXER_DEVICE_PROPERTIES = {
    'volume': {
        'type': 'DeviceParameter',
        'range': (0.0, 1.0),
        'default': 0.85,  # ~0dB
        'unit': 'linear',
        'db_range': (-60.0, 6.0)
    },
    'panning': {
        'type': 'DeviceParameter', 
        'range': (-1.0, 1.0),
        'default': 0.0,
        'unit': 'bipolar'
    },
    'sends': {
        'type': 'list[DeviceParameter]',
        'count': 'dynamic',  # Based on return track count
        'range': (0.0, 1.0),
        'default': 0.0
    },
    'track_activator': {
        'type': 'DeviceParameter',
        'range': (0.0, 1.0),
        'description': 'Track on/off'
    }
}
```

#### Track OSC Commands
```python
TRACK_OSC_COMMANDS = {
    # Basic Properties
    '/live/track/get/name': {'params': ['track_id: int'], 'response': 'string'},
    '/live/track/set/name': {'params': ['track_id: int', 'name: string'], 'response': None},
    '/live/track/get/color': {'params': ['track_id: int'], 'response': 'int'},
    '/live/track/set/color': {'params': ['track_id: int', 'color: int'], 'response': None},
    
    # State Control
    '/live/track/set/mute': {'params': ['track_id: int', 'mute: bool'], 'response': None},
    '/live/track/get/mute': {'params': ['track_id: int'], 'response': 'bool'},
    '/live/track/set/solo': {'params': ['track_id: int', 'solo: bool'], 'response': None},
    '/live/track/get/solo': {'params': ['track_id: int'], 'response': 'bool'},
    '/live/track/set/arm': {'params': ['track_id: int', 'arm: bool'], 'response': None},
    
    # Mixer Controls
    '/live/track/set/volume': {'params': ['track_id: int', 'volume: float'], 'range': (0.0, 1.0)},
    '/live/track/get/volume': {'params': ['track_id: int'], 'response': 'float'},
    '/live/track/set/panning': {'params': ['track_id: int', 'pan: float'], 'range': (-1.0, 1.0)},
    '/live/track/get/panning': {'params': ['track_id: int'], 'response': 'float'},
    '/live/track/set/send': {'params': ['track_id: int', 'send_id: int', 'amount: float'], 'range': (0.0, 1.0)},
    
    # Clip Control
    '/live/track/stop_all_clips': {'params': ['track_id: int'], 'response': None},
    '/live/track/get/num_devices': {'params': ['track_id: int'], 'response': 'int'},
    '/live/track/get/devices': {'params': ['track_id: int'], 'response': 'list[string]'}
}
```

---

## Clip Objects

### Clip Types and Properties

#### Clip Type Classification
```python
CLIP_TYPES = {
    'midi_clip': {
        'description': 'Contains MIDI note data and automation',
        'file_extensions': ['.mid', '.midi'],
        'note_manipulation': True,
        'pitch_properties': ['pitch_coarse', 'pitch_fine'],
        'time_properties': ['start_marker', 'end_marker', 'loop_start', 'loop_end']
    },
    'audio_clip': {
        'description': 'Contains audio sample data and warp information',
        'file_extensions': ['.wav', '.aif', '.mp3', '.flac', '.ogg'],
        'warp_modes': ['Beats', 'Tones', 'Texture', 'Re-Pitch', 'Complex', 'Complex Pro'],
        'gain_properties': ['gain']
    }
}
```

#### Core Clip Properties
```python
CLIP_PROPERTIES = {
    # Identity
    'name': {'type': 'string', 'editable': True, 'max_length': 255},
    'color': {'type': 'int', 'range': (0, 69), 'editable': True},
    'canonical_parent': {'type': 'Track', 'readonly': True},
    'is_midi_clip': {'type': 'bool', 'readonly': True},
    'is_audio_clip': {'type': 'bool', 'readonly': True},
    
    # Timing and Length
    'length': {'type': 'float', 'unit': 'beats', 'editable': True, 'min': 0.0625},
    'loop_start': {'type': 'float', 'unit': 'beats', 'editable': True},
    'loop_end': {'type': 'float', 'unit': 'beats', 'editable': True},
    'start_marker': {'type': 'float', 'unit': 'beats', 'editable': True},
    'end_marker': {'type': 'float', 'unit': 'beats', 'editable': True},
    'signature_numerator': {'type': 'int', 'range': (1, 99)},
    'signature_denominator': {'type': 'int', 'values': [2, 4, 8, 16]},
    
    # Playback State
    'is_playing': {'type': 'bool', 'readonly': True},
    'is_triggered': {'type': 'bool', 'readonly': True},
    'playing_position': {'type': 'float', 'unit': 'beats', 'readonly': True},
    'is_recording': {'type': 'bool', 'readonly': True},
    
    # Loop Properties
    'looping': {'type': 'bool', 'editable': True, 'default': True},
    'warping': {'type': 'bool', 'editable': True, 'default': True},
    
    # Audio-specific
    'gain': {'type': 'float', 'range': (-60.0, 6.0), 'unit': 'dB', 'audio_only': True},
    'pitch_coarse': {'type': 'int', 'range': (-48, 48), 'unit': 'semitones', 'audio_only': True},
    'pitch_fine': {'type': 'int', 'range': (-50, 50), 'unit': 'cents', 'audio_only': True},
    
    # MIDI-specific
    'has_notes': {'type': 'bool', 'readonly': True, 'midi_only': True}
}
```

### MIDI Clip Note Manipulation
```python
MIDI_NOTE_OPERATIONS = {
    'note_structure': {
        'pitch': {'type': 'int', 'range': (0, 127), 'description': 'MIDI note number'},
        'start_time': {'type': 'float', 'unit': 'beats', 'min': 0.0},
        'duration': {'type': 'float', 'unit': 'beats', 'min': 0.0625},
        'velocity': {'type': 'int', 'range': (1, 127), 'default': 100},
        'mute': {'type': 'bool', 'default': False}
    },
    
    'methods': {
        'get_notes': {
            'params': ['from_time: float', 'from_pitch: int', 'time_span: float', 'pitch_span: int'],
            'returns': 'list[Note]',
            'description': 'Get notes in specified region'
        },
        'add_new_notes': {
            'params': ['notes: list[Note]'],
            'description': 'Add notes to clip'
        },
        'remove_notes': {
            'params': ['from_time: float', 'from_pitch: int', 'time_span: float', 'pitch_span: int'],
            'description': 'Remove notes in specified region'
        },
        'replace_selected_notes': {
            'params': ['notes: list[Note]'],
            'description': 'Replace currently selected notes'
        },
        'select_all_notes': {
            'description': 'Select all notes in clip'
        },
        'quantize': {
            'params': ['quantization: float', 'amount: float', 'swing: float'],
            'description': 'Quantize notes to grid'
        },
        'duplicate_region': {
            'params': ['from_time: float', 'time_span: float', 'to_time: float'],
            'description': 'Duplicate notes within time region'
        }
    }
}
```

#### Clip OSC Commands
```python
CLIP_OSC_COMMANDS = {
    # Playback Control
    '/live/clip/fire': {'params': ['track_id: int', 'clip_id: int'], 'response': None},
    '/live/clip/stop': {'params': ['track_id: int', 'clip_id: int'], 'response': None},
    '/live/clip/get/is_playing': {'params': ['track_id: int', 'clip_id: int'], 'response': 'bool'},
    '/live/clip/get/playing_position': {'params': ['track_id: int', 'clip_id: int'], 'response': 'float'},
    
    # Properties
    '/live/clip/get/name': {'params': ['track_id: int', 'clip_id: int'], 'response': 'string'},
    '/live/clip/set/name': {'params': ['track_id: int', 'clip_id: int', 'name: string'], 'response': None},
    '/live/clip/get/length': {'params': ['track_id: int', 'clip_id: int'], 'response': 'float'},
    '/live/clip/set/length': {'params': ['track_id: int', 'clip_id: int', 'length: float'], 'response': None},
    
    # Loop Control
    '/live/clip/get/loop_start': {'params': ['track_id: int', 'clip_id: int'], 'response': 'float'},
    '/live/clip/set/loop_start': {'params': ['track_id: int', 'clip_id: int', 'start: float'], 'response': None},
    '/live/clip/get/loop_end': {'params': ['track_id: int', 'clip_id: int'], 'response': 'float'},
    '/live/clip/set/loop_end': {'params': ['track_id: int', 'clip_id: int', 'end: float'], 'response': None},
    
    # MIDI Notes
    '/live/clip/add/notes': {
        'params': ['track_id: int', 'clip_id: int', 'notes: list[float]'],
        'format': '[pitch1, start1, duration1, velocity1, mute1, pitch2, ...]',
        'response': None
    },
    '/live/clip/get/notes': {
        'params': ['track_id: int', 'clip_id: int'],
        'response': '[track_id, clip_id, pitch1, start1, duration1, velocity1, mute1, ...]'
    },
    '/live/clip/remove/notes': {
        'params': ['track_id: int', 'clip_id: int', 'from_time: float', 'time_span: float'],
        'response': None
    },
    
    # Clip Creation
    '/live/clip_slot/create_clip': {
        'params': ['track_id: int', 'clip_id: int', 'length: float'],
        'response': None
    },
    '/live/clip_slot/delete_clip': {
        'params': ['track_id: int', 'clip_id: int'],
        'response': None
    },
    '/live/clip_slot/get/has_clip': {
        'params': ['track_id: int', 'clip_id: int'],
        'response': 'bool'
    }
}
```

---

## Device Objects

### Device Type Classification

#### Built-in Instruments
```python
ABLETON_INSTRUMENTS = {
    'Operator': {
        'type': 'FM_Synthesis',
        'oscillators': 4,
        'key_parameters': [
            {'name': 'Operator A Level', 'range': (0.0, 1.0), 'cc': None},
            {'name': 'Operator A Frequency', 'range': (0.0, 1.0), 'cc': None},
            {'name': 'Filter Frequency', 'range': (0.0, 1.0), 'cc': None},
            {'name': 'LFO Rate', 'range': (0.0, 1.0), 'cc': None}
        ],
        'parameter_count': 32
    },
    'Simpler': {
        'type': 'Sample_Playback',
        'features': ['pitch', 'filter', 'envelope'],
        'key_parameters': [
            {'name': 'Volume', 'range': (0.0, 1.0)},
            {'name': 'Transpose', 'range': (-48, 48), 'unit': 'semitones'},
            {'name': 'Filter Freq', 'range': (0.0, 1.0)},
            {'name': 'Filter Res', 'range': (0.0, 1.0)}
        ]
    },
    'Impulse': {
        'type': 'Drum_Machine',
        'slots': 8,
        'per_slot_parameters': ['Volume', 'Pan', 'Transpose', 'Decay'],
        'global_parameters': ['Global Volume', 'Global Transpose']
    },
    'Bass': {
        'type': 'Virtual_Analog',
        'oscillators': 3,
        'features': ['sub_oscillator', 'overdrive', 'multimode_filter']
    }
}
```

#### Built-in Audio Effects
```python
ABLETON_AUDIO_EFFECTS = {
    'EQ Eight': {
        'type': 'Equalizer',
        'bands': 8,
        'parameters_per_band': ['Frequency', 'Gain', 'Q'],
        'global_parameters': ['Adaptive Q', 'Scale', 'Output']
    },
    'Compressor': {
        'type': 'Dynamics_Processor',
        'key_parameters': [
            {'name': 'Threshold', 'range': (-60.0, 0.0), 'unit': 'dB'},
            {'name': 'Ratio', 'range': (1.0, 100.0)},
            {'name': 'Attack', 'range': (0.01, 100.0), 'unit': 'ms'},
            {'name': 'Release', 'range': (1.0, 1000.0), 'unit': 'ms'},
            {'name': 'Makeup', 'range': (0.0, 30.0), 'unit': 'dB'}
        ]
    },
    'Reverb': {
        'type': 'Spatial_Effect',
        'key_parameters': [
            {'name': 'PreDelay', 'range': (0.0, 250.0), 'unit': 'ms'},
            {'name': 'Room Size', 'range': (0.0, 1.0)},
            {'name': 'Decay Time', 'range': (0.1, 60.0), 'unit': 's'},
            {'name': 'Diffusion', 'range': (0.0, 1.0)},
            {'name': 'Hi Cut', 'range': (1000.0, 20000.0), 'unit': 'Hz'}
        ]
    },
    'Delay': {
        'type': 'Time_Effect',
        'key_parameters': [
            {'name': 'Time', 'sync_modes': ['Note', 'Time'], 'range': (0.0, 1.0)},
            {'name': 'Feedback', 'range': (0.0, 1.0)},
            {'name': 'Dry/Wet', 'range': (0.0, 1.0)}
        ]
    },
    'Auto Filter': {
        'type': 'Filter',
        'filter_types': ['Lowpass', 'Highpass', 'Bandpass', 'Notch'],
        'key_parameters': [
            {'name': 'Frequency', 'range': (20.0, 20000.0), 'unit': 'Hz'},
            {'name': 'Resonance', 'range': (0.0, 1.0)},
            {'name': 'LFO Amount', 'range': (-1.0, 1.0)},
            {'name': 'LFO Rate', 'range': (0.0, 1.0)}
        ]
    }
}
```

### Device Parameter System
```python
DEVICE_PARAMETER_PROPERTIES = {
    'value': {
        'type': 'float',
        'description': 'Current parameter value (normalized 0.0-1.0)',
        'editable': True
    },
    'display_value': {
        'type': 'string',
        'description': 'Human-readable value with units',
        'readonly': True
    },
    'min': {
        'type': 'float',
        'description': 'Minimum parameter value',
        'readonly': True
    },
    'max': {
        'type': 'float', 
        'description': 'Maximum parameter value',
        'readonly': True
    },
    'name': {
        'type': 'string',
        'description': 'Parameter display name',
        'readonly': True
    },
    'original_name': {
        'type': 'string',
        'description': 'Internal parameter name',
        'readonly': True
    },
    'is_enabled': {
        'type': 'bool',
        'description': 'Whether parameter is currently active',
        'readonly': True
    },
    'automation_state': {
        'type': 'int',
        'values': {0: 'None', 1: 'Overridden', 2: 'Automated'},
        'readonly': True
    }
}
```

#### Device OSC Commands
```python
DEVICE_OSC_COMMANDS = {
    # Device Info
    '/live/device/get/name': {
        'params': ['track_id: int', 'device_id: int'],
        'response': 'string'
    },
    '/live/device/get/class_name': {
        'params': ['track_id: int', 'device_id: int'],
        'response': 'string'
    },
    '/live/device/get/num_parameters': {
        'params': ['track_id: int', 'device_id: int'],
        'response': 'int'
    },
    
    # Device State
    '/live/device/set/is_active': {
        'params': ['track_id: int', 'device_id: int', 'active: bool'],
        'response': None
    },
    '/live/device/get/is_active': {
        'params': ['track_id: int', 'device_id: int'],
        'response': 'bool'
    },
    
    # Parameter Control
    '/live/device/set/parameter/value': {
        'params': ['track_id: int', 'device_id: int', 'param_id: int', 'value: float'],
        'range': (0.0, 1.0),
        'response': None
    },
    '/live/device/get/parameter/value': {
        'params': ['track_id: int', 'device_id: int', 'param_id: int'],
        'response': 'float'
    },
    '/live/device/get/parameter/name': {
        'params': ['track_id: int', 'device_id: int', 'param_id: int'],
        'response': 'string'
    },
    '/live/device/get/parameter/display_value': {
        'params': ['track_id: int', 'device_id: int', 'param_id: int'],
        'response': 'string'
    },
    '/live/device/get/parameter/min': {
        'params': ['track_id: int', 'device_id: int', 'param_id: int'],
        'response': 'float'
    },
    '/live/device/get/parameter/max': {
        'params': ['track_id: int', 'device_id: int', 'param_id: int'],
        'response': 'float'
    }
}
```

---

## OSC Command Reference

### Complete Command Categories

#### Application Control
```python
APPLICATION_COMMANDS = {
    '/live/test': {
        'description': 'Test OSC connection',
        'params': [],
        'response': 'Test response message'
    },
    '/live/application/get/version': {
        'description': 'Get Ableton Live version',
        'params': [],
        'response': 'string (version number)'
    }
}
```

#### Scene Management
```python
SCENE_COMMANDS = {
    '/live/scene/fire': {
        'params': ['scene_id: int'],
        'description': 'Launch scene (all clips in row)'
    },
    '/live/scene/get/name': {
        'params': ['scene_id: int'],
        'response': 'string'
    },
    '/live/scene/set/name': {
        'params': ['scene_id: int', 'name: string']
    },
    '/live/scene/get/color': {
        'params': ['scene_id: int'],
        'response': 'int'
    },
    '/live/scene/set/color': {
        'params': ['scene_id: int', 'color: int']
    }
}
```

#### View and Navigation
```python
VIEW_COMMANDS = {
    '/live/view/set/selected_track': {
        'params': ['track_id: int'],
        'description': 'Select track in UI'
    },
    '/live/view/get/selected_track': {
        'response': 'int (track_id)'
    },
    '/live/view/set/selected_scene': {
        'params': ['scene_id: int']
    },
    '/live/view/get/selected_scene': {
        'response': 'int (scene_id)'
    }
}
```

### Batch Operations and Wildcards
```python
BATCH_OPERATIONS = {
    'wildcard_syntax': {
        '/live/clip/get/*': {
            'description': 'Get all properties of specified clip',
            'params': ['track_id: int', 'clip_id: int'],
            'response': 'Multiple property responses'
        },
        '/live/track/get/*': {
            'description': 'Get all properties of specified track',
            'params': ['track_id: int'],
            'response': 'Multiple property responses'
        }
    },
    'pattern_matching': {
        'single_property': '/live/track/get/name *',
        'multiple_tracks': '/live/track/*/get/mute',
        'all_clips': '/live/clip/*/*/get/is_playing'
    }
}
```

---

## Session vs Arrangement Workflows

### Session View Characteristics
```python
SESSION_VIEW = {
    'structure': {
        'clips_grid': 'Horizontal scenes × Vertical tracks',
        'clip_launching': 'Non-linear, loop-based performance',
        'scene_launching': 'Launch entire horizontal row',
        'recording': 'Loop recording into clip slots'
    },
    
    'use_cases': {
        'live_performance': 'Trigger clips and scenes in real-time',
        'composition': 'Build songs from loops and ideas',
        'jamming': 'Experiment with different combinations',
        'sound_design': 'Layer and manipulate loops'
    },
    
    'clip_behaviors': {
        'launch_modes': {
            'trigger': 'Clip plays when launched',
            'gate': 'Clip plays while button held',
            'toggle': 'Clip toggles on/off',
            'repeat': 'Clip retrigs at rate'
        },
        'launch_quantization': ['None', 'Global', 'Bar', '1/2 Note', '1/4 Note', '1/8 Note'],
        'follow_actions': 'Automatic progression to other clips'
    },
    
    'automation_recording': {
        'session_automation': 'Records parameter changes in clips',
        'overdub_mode': 'Layers automation over existing'
    }
}
```

### Arrangement View Characteristics  
```python
ARRANGEMENT_VIEW = {
    'structure': {
        'timeline': 'Linear time-based composition',
        'tracks_vertical': 'Tracks stacked vertically',
        'clips_horizontal': 'Clips extend across time',
        'arrangement_markers': 'Song sections and cue points'
    },
    
    'use_cases': {
        'song_arrangement': 'Linear song structure creation',
        'audio_editing': 'Precise audio clip editing',
        'mixing': 'Final mix automation and tweaking',
        'mastering_prep': 'Final arrangement decisions'
    },
    
    'automation': {
        'envelope_editing': 'Precise automation curve drawing',
        'breakpoint_automation': 'Point-based parameter control',
        'automation_lanes': 'Multiple parameters per track'
    },
    
    'recording_modes': {
        'arrangement_recording': 'Records directly into timeline',
        'punch_recording': 'In/out point based recording',
        'overdub_recording': 'Layers over existing audio'
    }
}
```

### Session ↔ Arrangement Integration
```python
SESSION_ARRANGEMENT_WORKFLOW = {
    'session_to_arrangement': {
        'method': 'Record button captures session performance',
        'timing': 'Global quantization or immediate',
        'automation_transfer': 'Session automation becomes arrangement',
        'use_case': 'Capture live performance or arrangement structure'
    },
    
    'arrangement_to_session': {
        'consolidate_clips': 'Render arrangement sections to clips',
        'extract_loops': 'Create session clips from arrangement',
        'back_to_arrangement': 'Seamless return to linear mode'
    },
    
    'best_practices': {
        'composition_flow': 'Session for ideas → Arrangement for structure',
        'performance_prep': 'Arrangement for practice → Session for performance',
        'collaboration': 'Session for jamming → Arrangement for production'
    }
}
```

---

## Advanced Integration Patterns

### Real-time Parameter Monitoring
```python
class ParameterMonitor:
    def __init__(self, osc_client):
        self.osc_client = osc_client
        self.monitored_parameters = {}
        self.listeners = {}
    
    def monitor_parameter(self, track_id, device_id, param_id, callback):
        """Set up real-time monitoring for device parameter"""
        param_path = f"/live/device/parameter/{track_id}/{device_id}/{param_id}"
        
        # Store callback
        self.listeners[param_path] = callback
        
        # Enable parameter monitoring
        self.osc_client.send_message("/live/api/enable_parameter_monitoring", [
            track_id, device_id, param_id
        ])
    
    def handle_parameter_change(self, address, value):
        """Handle incoming parameter change notifications"""
        if address in self.listeners:
            self.listeners[address](value)
```

### Multi-Track Operations
```python
class MultiTrackController:
    def __init__(self, osc_client):
        self.osc_client = osc_client
    
    def bulk_mute_operation(self, track_ids, mute_state):
        """Mute/unmute multiple tracks atomically"""
        for track_id in track_ids:
            self.osc_client.send_message("/live/track/set/mute", [track_id, mute_state])
    
    def create_bus_configuration(self, track_count, return_tracks):
        """Set up routing for multiple tracks"""
        # Create return tracks first
        for i in range(return_tracks):
            self.osc_client.send_message("/live/song/create_return_track", [])
        
        # Route tracks to returns
        for track_id in range(track_count):
            for return_id in range(return_tracks):
                # Set send levels
                self.osc_client.send_message("/live/track/set/send", 
                                           [track_id, return_id, 0.0])
```

### Pattern-Based Clip Creation
```python
class PatternGenerator:
    def __init__(self, osc_client):
        self.osc_client = osc_client
    
    def create_drum_pattern(self, track_id, pattern_dict, bars=4):
        """Create drum pattern from dictionary specification"""
        clip_id = 0
        clip_length = bars
        
        # Create clip
        self.osc_client.send_message("/live/clip_slot/create_clip", 
                                   [track_id, clip_id, clip_length])
        
        # Build note list
        notes = []
        beats_per_bar = 4
        
        for instrument, timings in pattern_dict.items():
            pitch = self.get_drum_pitch(instrument)
            
            for bar in range(bars):
                for timing in timings:
                    absolute_time = bar * beats_per_bar + timing
                    notes.extend([pitch, absolute_time, 0.25, 100, False])
        
        # Send notes
        self.osc_client.send_message("/live/clip/add/notes", 
                                   [track_id, clip_id] + notes)
    
    def get_drum_pitch(self, instrument_name):
        """Map instrument names to MIDI pitches"""
        drum_map = {
            'kick': 36,
            'snare': 38, 
            'hihat_closed': 42,
            'hihat_open': 46,
            'crash': 49,
            'ride': 51
        }
        return drum_map.get(instrument_name, 60)
```

---

## Implementation Guidelines

### Error Handling and Validation
```python
class AbletonOSCClient:
    def __init__(self, send_port=11000, receive_port=11001):
        self.send_port = send_port
        self.receive_port = receive_port
        self.connection_verified = False
        self.parameter_cache = {}
    
    def send_with_validation(self, address, args=[], timeout=1.0):
        """Send OSC message with parameter validation and error handling"""
        try:
            # Validate parameters based on command specification
            validated_args = self.validate_parameters(address, args)
            
            # Send message
            self.osc_client.send_message(address, validated_args)
            
            # Wait for response if expected
            if self.expects_response(address):
                return self.wait_for_response(address, timeout)
                
        except ValidationError as e:
            raise AbletonOSCError(f"Parameter validation failed: {e}")
        except TimeoutError:
            raise AbletonOSCError(f"No response received for {address}")
    
    def validate_parameters(self, address, args):
        """Validate parameter types and ranges"""
        command_spec = self.get_command_specification(address)
        
        if len(args) != len(command_spec.get('params', [])):
            raise ValidationError("Parameter count mismatch")
        
        validated = []
        for i, (arg, param_spec) in enumerate(zip(args, command_spec['params'])):
            validated_arg = self.validate_single_parameter(arg, param_spec)
            validated.append(validated_arg)
        
        return validated
```

### Performance Optimization
```python
class OptimizedOSCController:
    def __init__(self):
        self.batch_operations = []
        self.parameter_cache = {}
        self.change_listeners = set()
    
    def batch_parameter_updates(self, updates):
        """Batch multiple parameter changes for efficiency"""
        for track_id, device_id, param_id, value in updates:
            self.batch_operations.append({
                'address': '/live/device/set/parameter/value',
                'args': [track_id, device_id, param_id, value]
            })
    
    def execute_batch(self):
        """Execute all batched operations"""
        for operation in self.batch_operations:
            self.osc_client.send_message(operation['address'], operation['args'])
        self.batch_operations.clear()
    
    def cache_parameter_values(self, track_id, device_id):
        """Cache all parameter values for a device"""
        cache_key = f"{track_id}_{device_id}"
        
        # Get parameter count
        param_count = self.send_with_validation(
            '/live/device/get/num_parameters', [track_id, device_id]
        )
        
        # Cache all parameter values
        self.parameter_cache[cache_key] = {}
        for param_id in range(param_count):
            value = self.send_with_validation(
                '/live/device/get/parameter/value', 
                [track_id, device_id, param_id]
            )
            self.parameter_cache[cache_key][param_id] = value
```

### Usage Examples
```python
# Example: Create and populate a basic track
async def create_complete_track(osc_client, track_name="Generated Track"):
    """Create track with instrument, pattern, and effects"""
    
    # Create MIDI track
    track_id = await osc_client.send_with_validation('/live/song/create_midi_track', [-1])
    
    # Set track name
    await osc_client.send_with_validation('/live/track/set/name', [track_id, track_name])
    
    # Load a device (would require device loading capability)
    # This is a limitation - OSC doesn't directly support device loading
    
    # Create a simple melody pattern
    notes = [
        60, 0.0, 0.5, 80, False,    # C4 at beat 0
        64, 0.5, 0.5, 75, False,    # E4 at beat 0.5
        67, 1.0, 1.0, 85, False,    # G4 at beat 1
        60, 2.0, 2.0, 70, False     # C4 at beat 2 (longer)
    ]
    
    await osc_client.send_with_validation('/live/clip_slot/create_clip', [track_id, 0, 4.0])
    await osc_client.send_with_validation('/live/clip/add/notes', [track_id, 0] + notes)
    
    # Set some track properties
    await osc_client.send_with_validation('/live/track/set/volume', [track_id, 0.8])
    await osc_client.send_with_validation('/live/track/set/color', [track_id, 5])
    
    return track_id
```

This comprehensive reference provides the foundation for building sophisticated Ableton Live integration systems. The combination of Live Object Model understanding and complete OSC command coverage enables powerful programmatic control over every aspect of the DAW.

---

**Document Status:** Phase 1.1 Complete  
**Next Phase:** Audio Processing & DSP Knowledge Investigation  
**Integration Ready:** ✅ Full MCP implementation possible with this reference