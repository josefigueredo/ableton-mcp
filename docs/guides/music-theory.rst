Music Theory Guide
==================

This guide explains the music theory features of the Ableton Live MCP Server.

Overview
--------

The server includes a comprehensive music theory engine that provides:

- Key detection and analysis
- Chord progression suggestions
- Scale filtering for MIDI notes
- Quantization options

Key Detection
-------------

The ``analyze_key`` function determines the most likely musical key
from a set of notes.

Algorithm
^^^^^^^^^

1. Extract pitch classes from MIDI notes (0-11)
2. Compare against known scale patterns
3. Score each potential key by note matches
4. Return keys sorted by confidence

.. code-block:: python

   from ableton_mcp.domain.entities import Note

   notes = [
       Note(pitch=60, start=0.0, duration=1.0),  # C
       Note(pitch=64, start=1.0, duration=1.0),  # E
       Note(pitch=67, start=2.0, duration=1.0),  # G
   ]

   keys = await music_theory.analyze_key(notes)
   # Returns: [MusicKey(root="C", mode="major", confidence=0.95), ...]

Supported Scales
^^^^^^^^^^^^^^^^

- Major (Ionian)
- Natural Minor (Aeolian)
- Harmonic Minor
- Melodic Minor
- Dorian
- Phrygian
- Lydian
- Mixolydian
- Locrian
- Pentatonic Major
- Pentatonic Minor
- Blues

Chord Progressions
------------------

The server suggests chord progressions based on key and genre.

Genre-Specific Suggestions
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Pop**

Common progressions for pop music:

- I - V - vi - IV (C - G - Am - F)
- I - IV - V - I (C - F - G - C)
- vi - IV - I - V (Am - F - C - G)

**Jazz**

Complex progressions for jazz:

- ii - V - I (Dm7 - G7 - Cmaj7)
- I - vi - ii - V (Cmaj7 - Am7 - Dm7 - G7)
- iii - vi - ii - V - I (Em7 - Am7 - Dm7 - G7 - Cmaj7)

**Electronic**

Progressions for electronic music:

- i - VII - VI - VII (Am - G - F - G)
- i - iv - i - VII (Am - Dm - Am - G)
- i - III - VII - IV (Am - C - G - F)

.. code-block:: python

   progressions = await music_theory.suggest_chord_progressions(
       root="A",
       mode="minor",
       genre="electronic"
   )

   for prog in progressions:
       print(f"{prog.name}: {' -> '.join(prog.chords)}")

Scale Filtering
---------------

When adding MIDI notes, you can filter them to fit a specific scale.

How It Works
^^^^^^^^^^^^

1. Define target scale (root + mode)
2. For each input note, check if pitch is in scale
3. If not, adjust to nearest scale degree

.. code-block:: python

   # Notes that might be out of scale
   notes = [
       Note(pitch=60, start=0.0, duration=0.5),  # C (in C minor)
       Note(pitch=64, start=0.5, duration=0.5),  # E (out of C minor, becomes Eb)
       Note(pitch=67, start=1.0, duration=0.5),  # G (in C minor)
   ]

   await gateway.add_notes(
       track_id=0,
       clip_id=0,
       notes=notes,
       scale_filter="minor",
       root_note=60  # C
   )

Scale Degrees
^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 15 42 43

   * - Scale
     - Intervals (semitones)
     - Example (C root)
   * - Major
     - 0, 2, 4, 5, 7, 9, 11
     - C, D, E, F, G, A, B
   * - Minor
     - 0, 2, 3, 5, 7, 8, 10
     - C, D, Eb, F, G, Ab, Bb
   * - Dorian
     - 0, 2, 3, 5, 7, 9, 10
     - C, D, Eb, F, G, A, Bb
   * - Pentatonic
     - 0, 2, 4, 7, 9
     - C, D, E, G, A

Quantization
------------

Quantization aligns note timing to a grid.

Options
^^^^^^^

- **1.0** - Whole notes
- **0.5** - Half notes
- **0.25** - Quarter notes (default)
- **0.125** - Eighth notes
- **0.0625** - Sixteenth notes

.. code-block:: python

   # Note slightly off the grid
   notes = [
       Note(pitch=60, start=0.13, duration=0.5),  # Should be at 0.0 or 0.25
   ]

   await gateway.add_notes(
       track_id=0,
       clip_id=0,
       notes=notes,
       quantize=True,
       quantize_value=0.25  # Quarter note grid
   )
   # Note will be moved to start=0.0 (nearest grid point)

Quantization Algorithm
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def quantize_time(time: float, grid: float) -> float:
       return round(time / grid) * grid

MIDI Pitch Reference
--------------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20 20

   * - Note
     - Octave 3
     - Octave 4
     - Octave 5
     - Octave 6
   * - C
     - 48
     - 60
     - 72
     - 84
   * - D
     - 50
     - 62
     - 74
     - 86
   * - E
     - 52
     - 64
     - 76
     - 88
   * - F
     - 53
     - 65
     - 77
     - 89
   * - G
     - 55
     - 67
     - 79
     - 91
   * - A
     - 57
     - 69
     - 81
     - 93
   * - B
     - 59
     - 71
     - 83
     - 95

Best Practices
--------------

1. **Analyze before filtering** - Detect the key first, then use that for filtering
2. **Use appropriate quantization** - Match the grid to the musical style
3. **Consider velocity** - Vary velocity for more musical results
4. **Layer progressions** - Combine bass notes with chord voicings
