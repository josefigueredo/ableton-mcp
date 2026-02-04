"""Concrete implementations of domain services."""

from typing import Any

from ableton_mcp.domain.entities import (
    AnalysisResult,
    Clip,
    MusicKey,
    Note,
    Song,
    Track,
)
from ableton_mcp.domain.services import (
    ArrangementService,
    MixingService,
    MusicTheoryService,
    TempoAnalysisService,
)


class MusicTheoryServiceImpl(MusicTheoryService):
    """Implementation of music theory service with comprehensive analysis."""

    # Scale definitions with intervals
    SCALES = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
        "pentatonic_major": [0, 2, 4, 7, 9],
        "pentatonic_minor": [0, 3, 5, 7, 10],
        "blues": [0, 3, 5, 6, 7, 10],
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
        "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    }

    # Chord progressions by genre
    CHORD_PROGRESSIONS = {
        "pop": {
            "vi_IV_I_V": [5, 3, 0, 4],  # Am F C G in C major
            "I_V_vi_IV": [0, 4, 5, 3],  # C G Am F
            "ii_V_I": [1, 4, 0],  # Dm G C
            "vi_ii_V_I": [5, 1, 4, 0],  # Am Dm G C
            "I_vi_IV_V": [0, 5, 3, 4],  # C Am F G
        },
        "jazz": {
            "ii_V_I": [1, 4, 0],
            "vi_ii_V_I": [5, 1, 4, 0],
            "I_vi_ii_V": [0, 5, 1, 4],
            "iii_vi_ii_V": [2, 5, 1, 4],
            "circle_of_fifths": [0, 4, 1, 5, 2, 6, 3],
        },
        "electronic": {
            "i_VII_VI_VII": [0, 10, 9, 10],  # Am G F G (minor)
            "i_iv_VII_iv": [0, 5, 10, 5],  # Am Dm G Dm
            "i_VI_III_VII": [0, 8, 3, 10],  # Am F C G
            "i_v_i_v": [0, 7, 0, 7],  # Am Em Am Em
        },
        "rock": {
            "I_V_vi_IV": [0, 4, 5, 3],  # C G Am F
            "I_VII_IV_I": [0, 10, 3, 0],  # C Bb F C
            "vi_IV_I_V": [5, 3, 0, 4],  # Am F C G
            "I_IV_V_I": [0, 3, 4, 0],  # C F G C
        },
    }

    # Diatonic scales (7-note scales) should be preferred over pentatonic/blues
    DIATONIC_SCALES = {
        "major",
        "minor",
        "dorian",
        "phrygian",
        "lydian",
        "mixolydian",
        "locrian",
        "harmonic_minor",
        "melodic_minor",
    }

    async def analyze_key(self, notes: list[Note]) -> list[MusicKey]:
        """Analyze the musical key of given notes."""
        if not notes:
            return []

        # Extract pitch classes from notes
        pitch_classes = list({note.pitch_class for note in notes})

        # Calculate key candidates with confidence scores
        key_candidates = []

        for scale_name, scale_intervals in self.SCALES.items():
            for root in range(12):
                scale_notes = {(root + interval) % 12 for interval in scale_intervals}

                # Calculate match score - how many input notes are in the scale
                input_set = set(pitch_classes)
                matches = len(input_set.intersection(scale_notes))

                # Base confidence: percentage of input notes that fit the scale
                confidence = matches / len(pitch_classes) if len(pitch_classes) > 0 else 0.0

                # Boost confidence for exact matches (all notes fit)
                if input_set.issubset(scale_notes):
                    confidence += 0.1

                # Prefer diatonic scales over pentatonic/blues for better harmonic context
                if scale_name in self.DIATONIC_SCALES:
                    confidence += 0.15

                # Penalize for missing important scale degrees
                if root not in pitch_classes:  # Missing tonic
                    confidence *= 0.8

                if confidence > 0.3:  # Only include reasonable matches
                    key_candidates.append(
                        MusicKey(root=root, mode=scale_name, confidence=min(1.0, confidence))
                    )

        # Sort by confidence and return top candidates
        return sorted(key_candidates, key=lambda k: k.confidence, reverse=True)[:5]

    async def suggest_chord_progressions(self, key: MusicKey, genre: str) -> list[list[int]]:
        """Suggest chord progressions for a given key and genre."""
        if genre not in self.CHORD_PROGRESSIONS:
            genre = "pop"  # Default to pop progressions

        progressions = []
        scale_intervals = self.SCALES.get(key.mode, self.SCALES["major"])

        for _prog_name, progression in self.CHORD_PROGRESSIONS[genre].items():
            # Transpose progression to the given key
            transposed_progression = []
            for degree in progression:
                if degree < len(scale_intervals):
                    chord_root = (key.root + scale_intervals[degree]) % 12
                    transposed_progression.append(chord_root)

            if transposed_progression:
                progressions.append(transposed_progression)

        return progressions

    async def harmonize_melody(self, melody_notes: list[Note], key: MusicKey) -> list[Note]:
        """Generate harmony notes for a melody."""
        harmony_notes = []
        scale_intervals = self.SCALES.get(key.mode, self.SCALES["major"])

        for note in melody_notes:
            # Find the degree of the melody note in the scale
            melody_pitch_class = note.pitch_class
            scale_notes = [(key.root + interval) % 12 for interval in scale_intervals]

            if melody_pitch_class in scale_notes:
                degree_index = scale_notes.index(melody_pitch_class)

                # Add third and fifth harmonies
                third_degree = (degree_index + 2) % len(scale_notes)
                fifth_degree = (degree_index + 4) % len(scale_notes)

                third_note = Note(
                    pitch=note.pitch + ((scale_notes[third_degree] - melody_pitch_class) % 12),
                    start=note.start,
                    duration=note.duration,
                    velocity=max(60, note.velocity - 20),  # Softer harmony
                )

                fifth_note = Note(
                    pitch=note.pitch + ((scale_notes[fifth_degree] - melody_pitch_class) % 12),
                    start=note.start,
                    duration=note.duration,
                    velocity=max(50, note.velocity - 30),  # Even softer
                )

                harmony_notes.extend([third_note, fifth_note])

        return harmony_notes

    async def quantize_notes(self, notes: list[Note], grid_division: float = 0.25) -> list[Note]:
        """Quantize notes to a rhythmic grid."""
        quantized_notes = []

        for note in notes:
            # Quantize start time
            quantized_start = round(note.start / grid_division) * grid_division

            # Quantize duration to nearest grid division
            quantized_duration = max(
                grid_division, round(note.duration / grid_division) * grid_division
            )

            quantized_note = Note(
                pitch=note.pitch,
                start=quantized_start,
                duration=quantized_duration,
                velocity=note.velocity,
                mute=note.mute,
            )
            quantized_notes.append(quantized_note)

        return quantized_notes

    async def filter_notes_to_scale(self, notes: list[Note], key: MusicKey) -> list[Note]:
        """Filter notes to fit within a musical scale."""
        scale_intervals = self.SCALES.get(key.mode, self.SCALES["major"])
        scale_notes = {(key.root + interval) % 12 for interval in scale_intervals}

        filtered_notes = []

        for note in notes:
            note_pitch_class = note.pitch_class

            if note_pitch_class in scale_notes:
                # Note is already in scale
                filtered_notes.append(note)
            else:
                # Find nearest scale note
                distances = []
                for scale_note in scale_notes:
                    # Calculate distance considering octave wrapping
                    distance = min(
                        abs(note_pitch_class - scale_note), 12 - abs(note_pitch_class - scale_note)
                    )
                    distances.append((distance, scale_note))

                _, nearest_scale_note = min(distances)

                # Adjust pitch to nearest scale note
                adjusted_pitch = (note.pitch // 12) * 12 + nearest_scale_note

                adjusted_note = Note(
                    pitch=adjusted_pitch,
                    start=note.start,
                    duration=note.duration,
                    velocity=note.velocity,
                    mute=note.mute,
                )
                filtered_notes.append(adjusted_note)

        return filtered_notes


class TempoAnalysisServiceImpl(TempoAnalysisService):
    """Implementation of tempo analysis service."""

    # Genre BPM ranges based on analysis of commercial music
    GENRE_BPM_RANGES = {
        "house": (120, 130),
        "techno": (125, 135),
        "trance": (128, 140),
        "dubstep": (140, 150),
        "drum_and_bass": (160, 180),
        "breakbeat": (130, 150),
        "hip_hop": (70, 90),
        "trap": (140, 170),
        "pop": (100, 130),
        "rock": (110, 140),
        "punk": (150, 200),
        "metal": (120, 180),
        "jazz": (90, 180),
        "blues": (60, 120),
        "reggae": (60, 90),
        "ska": (120, 180),
        "ambient": (60, 90),
        "downtempo": (80, 110),
        "classical": (60, 180),
    }

    async def detect_tempo(self, clip: Clip) -> float:
        """Detect tempo from a clip by analyzing MIDI note patterns.

        For MIDI clips, analyzes inter-onset intervals (IOI) to estimate tempo.
        For audio clips or empty clips, returns default 120.0 BPM.

        Note: Since raw audio data is not accessible via OSC, audio clip
        tempo detection is not possible. Use Ableton's built-in tempo
        detection for audio files.
        """
        from ableton_mcp.domain.entities import ClipType

        # Cannot detect from audio clips (no audio access) or empty clips
        if clip.clip_type != ClipType.MIDI or not clip.notes:
            return 120.0

        # Sort notes by start time
        sorted_notes = sorted(clip.notes, key=lambda n: n.start)

        if len(sorted_notes) < 2:
            return 120.0

        # Calculate inter-onset intervals (IOI)
        iois: list[float] = []
        for i in range(1, len(sorted_notes)):
            delta = sorted_notes[i].start - sorted_notes[i - 1].start
            # Filter out simultaneous notes and very long gaps
            if 0.01 < delta < 4.0:
                iois.append(delta)

        if not iois:
            return 120.0

        # Find median IOI (more robust than mean for rhythm analysis)
        iois.sort()
        median_ioi = iois[len(iois) // 2]

        # Calculate note density (notes per beat)
        density = len(sorted_notes) / clip.length if clip.length > 0 else 1.0

        # Estimate BPM based on rhythmic patterns
        # Common IOI values: 0.25 (16th), 0.5 (8th), 1.0 (quarter), 2.0 (half)
        if median_ioi <= 0.25:
            # Very busy 16th-note patterns suggest faster genres
            estimated = 125.0 + (density * 3)
        elif median_ioi <= 0.5:
            # 8th-note patterns
            estimated = 110.0 + (density * 2)
        elif median_ioi <= 1.0:
            # Quarter-note patterns
            estimated = 95.0 + (density * 2)
        else:
            # Half notes or slower
            estimated = 80.0 + (density * 2)

        # Clamp to reasonable BPM range
        return max(60.0, min(200.0, round(estimated, 1)))

    async def suggest_tempo_for_genre(self, genre: str, energy_level: str) -> float:
        """Suggest appropriate tempo for genre and energy level."""
        genre_lower = genre.lower()

        if genre_lower not in self.GENRE_BPM_RANGES:
            # Default to moderate tempo if genre not found
            base_tempo = 120.0
        else:
            min_bpm, max_bpm = self.GENRE_BPM_RANGES[genre_lower]

            # Calculate base tempo based on energy level
            if energy_level == "low":
                base_tempo = min_bpm + (max_bpm - min_bpm) * 0.2
            elif energy_level == "high":
                base_tempo = min_bpm + (max_bpm - min_bpm) * 0.8
            else:  # medium
                base_tempo = min_bpm + (max_bpm - min_bpm) * 0.5

        return round(base_tempo, 1)

    async def analyze_rhythmic_patterns(self, clip: Clip) -> AnalysisResult:
        """Analyze rhythmic patterns in a MIDI clip.

        Detects time signature feel, rhythmic complexity, groove type,
        and syncopation level by analyzing note positions and timing.
        """
        from ableton_mcp.domain.entities import ClipType

        # Cannot analyze audio clips or empty clips
        if clip.clip_type != ClipType.MIDI or not clip.notes:
            return AnalysisResult(
                analysis_type="rhythmic_pattern",
                confidence=0.3,
                data={
                    "pattern_type": "unknown",
                    "complexity": "unknown",
                    "groove_type": "unknown",
                    "syncopation_level": 0.0,
                    "note_count": 0,
                    "analysis_note": "No MIDI data available for analysis",
                },
            )

        sorted_notes = sorted(clip.notes, key=lambda n: n.start)

        # === Detect time signature feel ===
        # Count notes on downbeats for 4/4 vs 3/4 detection
        bar_4_4_downbeats = sum(1 for n in sorted_notes if n.start % 4 < 0.1)
        bar_3_4_downbeats = sum(1 for n in sorted_notes if n.start % 3 < 0.1)

        # Also check beat positions
        beat_positions_4_4 = sum(1 for n in sorted_notes if n.start % 1 < 0.1)
        beat_positions_3_4 = sum(1 for n in sorted_notes if (n.start * 4 / 3) % 1 < 0.1)

        if bar_3_4_downbeats > bar_4_4_downbeats * 1.2 and beat_positions_3_4 > beat_positions_4_4:
            pattern_type = "3/4"
        else:
            pattern_type = "4/4"

        # === Detect complexity ===
        # Based on unique note positions (quantized to 16th notes)
        unique_positions = len({round(n.start * 4) / 4 for n in sorted_notes})
        position_variety = unique_positions / len(sorted_notes) if sorted_notes else 0

        # Also consider note density
        notes_per_beat = len(sorted_notes) / clip.length if clip.length > 0 else 0

        if position_variety > 0.6 and notes_per_beat > 2:
            complexity = "high"
        elif position_variety > 0.3 or notes_per_beat > 1:
            complexity = "medium"
        else:
            complexity = "low"

        # === Detect groove type (straight vs swung) ===
        # Analyze offbeat 8th note positions
        offbeat_timings: list[float] = []
        for note in sorted_notes:
            # Get position within the beat
            beat_position = note.start % 1
            # Check if it's an offbeat (around 0.5)
            if 0.3 < beat_position < 0.7:
                offbeat_timings.append(beat_position)

        if offbeat_timings:
            avg_offbeat = sum(offbeat_timings) / len(offbeat_timings)
            # Swing typically pushes offbeats later (> 0.5)
            if avg_offbeat > 0.55:
                groove_type = "swung"
            elif avg_offbeat < 0.45:
                groove_type = "pushed"
            else:
                groove_type = "straight"
        else:
            groove_type = "straight"

        # === Calculate syncopation level ===
        # Syncopation: notes on weak subdivisions
        syncopated_notes = 0
        for note in sorted_notes:
            grid_16th = note.start * 4  # Convert to 16th note grid
            grid_remainder = grid_16th % 1
            # Notes not on the 16th note grid are syncopated
            if grid_remainder > 0.1 and grid_remainder < 0.9:
                syncopated_notes += 1

        syncopation_level = syncopated_notes / len(sorted_notes) if sorted_notes else 0.0

        # === Velocity analysis for dynamics ===
        velocities = [n.velocity for n in sorted_notes]
        avg_velocity = sum(velocities) / len(velocities)
        velocity_variance = sum((v - avg_velocity) ** 2 for v in velocities) / len(velocities)
        dynamics = "dynamic" if velocity_variance > 300 else "consistent"

        return AnalysisResult(
            analysis_type="rhythmic_pattern",
            confidence=0.8 if len(sorted_notes) >= 4 else 0.5,
            data={
                "pattern_type": pattern_type,
                "complexity": complexity,
                "groove_type": groove_type,
                "syncopation_level": round(syncopation_level, 2),
                "note_count": len(sorted_notes),
                "notes_per_beat": round(notes_per_beat, 2),
                "dynamics": dynamics,
                "average_velocity": round(avg_velocity),
            },
        )

    async def suggest_tempo_changes(
        self, song: Song, target_energy: list[float]
    ) -> list[tuple[float, float]]:
        """Suggest tempo changes to match target energy curve."""
        suggestions = []
        base_tempo = song.tempo

        for i, energy in enumerate(target_energy):
            # Calculate tempo adjustment based on energy level
            # Higher energy = faster tempo (up to +20% of base)
            tempo_multiplier = 1.0 + (energy - 0.5) * 0.4
            suggested_tempo = base_tempo * tempo_multiplier

            # Clamp to reasonable range
            suggested_tempo = max(60.0, min(200.0, suggested_tempo))

            time_position = i * 4.0  # Assume 4-bar sections
            suggestions.append((time_position, suggested_tempo))

        return suggestions


class ArrangementServiceImpl(ArrangementService):
    """Implementation of arrangement service."""

    # Section keywords for detecting structure from clip names
    SECTION_KEYWORDS: dict[str, list[str]] = {
        "intro": ["intro", "begin", "start", "opening"],
        "verse": ["verse", "vs", "v1", "v2", "v3", "v4"],
        "chorus": ["chorus", "hook", "ch", "refrain"],
        "bridge": ["bridge", "br", "breakdown", "break", "middle8"],
        "outro": ["outro", "end", "finale", "ending", "coda"],
        "drop": ["drop", "main", "peak"],
        "buildup": ["build", "buildup", "riser", "rise"],
        "pre_chorus": ["prechorus", "pre-chorus", "pre"],
    }

    async def analyze_song_structure(self, song: Song) -> AnalysisResult:
        """Analyze song structure from track and clip metadata.

        Detects sections by analyzing:
        - Clip names for section keywords (verse, chorus, etc.)
        - Track activity patterns per section
        - Note density changes across time
        """
        from ableton_mcp.domain.entities import ClipType

        # Collect all clip data
        clip_data: list[dict[str, Any]] = []
        section_hints: dict[int, str] = {}  # bar_position -> section_name
        max_end = 0.0

        for track in song.tracks:
            for slot_idx, clip in enumerate(track.clips):
                if clip is None:
                    continue

                # Estimate clip position (slot_idx * 16 beats = 4 bars per slot)
                clip_start = slot_idx * 16.0
                clip_end = clip_start + clip.length

                max_end = max(max_end, clip_end)

                note_count = len(clip.notes) if clip.clip_type == ClipType.MIDI else 0
                total_velocity = (
                    sum(n.velocity for n in clip.notes) if clip.clip_type == ClipType.MIDI else 0
                )

                clip_data.append(
                    {
                        "start": clip_start,
                        "end": clip_end,
                        "track": track.name,
                        "clip_name": clip.name or "",
                        "note_count": note_count,
                        "total_velocity": total_velocity,
                        "track_volume": track.volume,
                    }
                )

                # Check clip name for section hints
                if clip.name:
                    clip_lower = clip.name.lower()
                    for section, keywords in self.SECTION_KEYWORDS.items():
                        if any(kw in clip_lower for kw in keywords):
                            bar_pos = int(clip_start / 4)  # Convert beats to bars
                            section_hints[bar_pos] = section
                            break

        # Handle empty song
        if not clip_data:
            return AnalysisResult(
                analysis_type="song_structure",
                confidence=0.3,
                data={
                    "sections": [],
                    "total_length_bars": 0,
                    "track_count": len(song.tracks),
                    "analysis_note": "No clip data available for analysis",
                },
            )

        total_bars = max(1, int(max_end / 4))

        # Analyze activity per 8-bar section
        section_size = 32.0  # 8 bars = 32 beats
        sections: list[dict[str, Any]] = []
        section_labels: list[str] = []

        for section_start in range(0, int(max_end), int(section_size)):
            section_end = section_start + section_size

            # Count active clips and notes in this section
            active_clips = [
                c for c in clip_data if c["start"] < section_end and c["end"] > section_start
            ]

            density = len(active_clips) / max(1, len(song.tracks))
            total_notes = sum(c["note_count"] for c in active_clips)
            total_vel = sum(c["total_velocity"] for c in active_clips)

            # Determine section type
            bar_num = section_start // 4
            if bar_num in section_hints:
                section_name = section_hints[bar_num]
            elif section_start == 0 and density < 0.4:
                section_name = "intro"
            elif density < 0.3:
                section_name = "breakdown"
            elif density > 0.7 and total_notes > 20:
                section_name = "chorus"
            elif density > 0.5:
                section_name = "verse"
            else:
                section_name = "transition"

            sections.append(
                {
                    "bar": int(bar_num),
                    "type": section_name,
                    "density": round(density, 2),
                    "note_count": total_notes,
                    "energy": (
                        round(total_vel / max(1, total_notes * 127), 2) if total_notes > 0 else 0.0
                    ),
                }
            )
            section_labels.append(section_name)

        # Calculate repetition factor
        repetition_factor = self._calculate_repetition_factor(sections)

        return AnalysisResult(
            analysis_type="song_structure",
            confidence=0.7 if section_hints else 0.5,
            data={
                "sections": section_labels,
                "detailed_sections": sections,
                "total_length_bars": total_bars,
                "total_length_beats": max_end,
                "track_count": len(song.tracks),
                "clip_count": len(clip_data),
                "detected_keywords": list(set(section_hints.values())),
                "repetition_factor": repetition_factor,
            },
        )

    def _calculate_repetition_factor(self, sections: list[dict[str, Any]]) -> float:
        """Calculate how repetitive the song structure is."""
        if len(sections) < 2:
            return 0.0

        # Count section type occurrences
        type_counts: dict[str, int] = {}
        for s in sections:
            t = s["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        # More repeated sections = higher repetition
        max_count = max(type_counts.values()) if type_counts else 1
        return round(min(1.0, max_count / len(sections) * 2), 2)

    async def suggest_arrangement_improvements(self, song: Song, genre: str) -> list[str]:
        """Suggest improvements to song arrangement."""
        suggestions = []

        # Analyze current structure
        num_tracks = len(song.tracks)
        song_length_bars = 128  # Placeholder

        # Genre-specific suggestions
        if genre.lower() == "pop":
            if song_length_bars < 100:
                suggestions.append(
                    "Consider extending song length - pop songs typically run 3-4 minutes"
                )
            if num_tracks < 8:
                suggestions.append(
                    "Add more harmonic layers - consider strings or background vocals"
                )

        elif genre.lower() in ["electronic", "house", "techno"]:
            if song_length_bars < 150:
                suggestions.append(
                    "Electronic tracks benefit from longer arrangements for DJ mixing"
                )
            suggestions.append("Consider adding breakdown sections for dynamic contrast")

        # Universal suggestions
        if num_tracks > 20:
            suggestions.append("High track count - consider grouping similar elements")

        suggestions.append("Use the 'rule of 3' - repeat musical ideas 3 times before changing")
        suggestions.append("Create energy peaks and valleys for listener engagement")

        return suggestions

    async def calculate_energy_curve(self, song: Song) -> list[tuple[float, float]]:
        """Calculate energy levels throughout the song from MIDI data.

        Analyzes note density, velocity, and track volume to compute
        energy at each time point. For songs without MIDI data,
        returns a flat energy curve.
        """
        from ableton_mcp.domain.entities import ClipType

        # Collect all note events with their energy contribution
        energy_events: list[tuple[float, float]] = []  # (time, energy)
        max_time = 0.0

        for track in song.tracks:
            track_weight = track.volume

            for slot_idx, clip in enumerate(track.clips):
                if clip is None:
                    continue

                # Estimate clip position
                clip_start = slot_idx * 16.0  # 4 bars per slot

                if clip.clip_type == ClipType.MIDI and clip.notes:
                    # Calculate energy from MIDI notes
                    for note in clip.notes:
                        abs_time = clip_start + note.start
                        # Energy = velocity normalized * track volume
                        energy = (note.velocity / 127.0) * track_weight
                        energy_events.append((abs_time, energy))
                        max_time = max(max_time, abs_time)
                else:
                    # Audio clip: assume moderate energy throughout
                    for beat in range(int(clip.length)):
                        abs_time = clip_start + beat
                        energy_events.append((abs_time, 0.5 * track_weight))
                        max_time = max(max_time, abs_time)

        # Handle empty song
        if not energy_events or max_time == 0:
            # Return flat energy curve for 4 minutes
            return [(i * 8.0, 0.5) for i in range(30)]

        # Create energy buckets (1 bar = 4 beats)
        bucket_size = 4.0
        num_buckets = max(1, int(max_time / bucket_size) + 1)

        buckets: list[float] = [0.0] * num_buckets
        bucket_counts: list[int] = [0] * num_buckets

        for time, energy in energy_events:
            bucket_idx = min(int(time / bucket_size), num_buckets - 1)
            buckets[bucket_idx] += energy
            bucket_counts[bucket_idx] += 1

        # Calculate average energy per bucket and normalize
        max_bucket_energy = max(
            (b / max(1, c) for b, c in zip(buckets, bucket_counts, strict=True)),
            default=1.0,
        )

        energy_curve: list[tuple[float, float]] = []
        for i, (total_energy, count) in enumerate(zip(buckets, bucket_counts, strict=True)):
            time_pos = i * bucket_size

            if count > 0:
                avg_energy = total_energy / count
                normalized = (
                    min(1.0, avg_energy / max_bucket_energy) if max_bucket_energy > 0 else 0.5
                )
            else:
                normalized = 0.1  # Low energy for empty sections

            energy_curve.append((time_pos, round(normalized, 3)))

        # Apply simple smoothing (3-point moving average)
        smoothed: list[tuple[float, float]] = []
        for i in range(len(energy_curve)):
            start_idx = max(0, i - 1)
            end_idx = min(len(energy_curve), i + 2)
            avg = sum(e[1] for e in energy_curve[start_idx:end_idx]) / (end_idx - start_idx)
            smoothed.append((energy_curve[i][0], round(avg, 3)))

        return smoothed

    async def suggest_section_lengths(self, genre: str, song_length: float) -> dict[str, float]:
        """Suggest optimal section lengths for a genre."""
        if genre.lower() == "pop":
            return {
                "intro": 8.0,
                "verse": 16.0,
                "chorus": 16.0,
                "bridge": 8.0,
                "outro": 8.0,
            }
        elif genre.lower() in ["electronic", "house"]:
            return {
                "intro": 32.0,
                "build": 32.0,
                "drop": 32.0,
                "breakdown": 16.0,
                "outro": 16.0,
            }
        else:  # Default
            return {
                "intro": 8.0,
                "verse": 16.0,
                "chorus": 16.0,
                "bridge": 8.0,
                "outro": 8.0,
            }


class MixingServiceImpl(MixingService):
    """Implementation of mixing service."""

    # Track name keywords mapped to frequency ranges
    FREQUENCY_KEYWORDS: dict[str, dict[str, Any]] = {
        "sub_bass": {
            "keywords": ["sub", "808"],
            "range": "20-80 Hz",
            "typical_issues": ["Mud with kick", "Phase issues"],
        },
        "bass": {
            "keywords": ["bass", "low", "kick", "drum"],
            "range": "60-250 Hz",
            "typical_issues": ["Masking with kick", "Boomy around 200Hz"],
        },
        "low_mid": {
            "keywords": ["guitar", "keys", "piano", "synth", "pad", "organ"],
            "range": "250-500 Hz",
            "typical_issues": ["Muddy buildup", "Boxy sound around 400Hz"],
        },
        "mid": {
            "keywords": ["vocal", "voice", "lead", "snare", "melody"],
            "range": "500-2000 Hz",
            "typical_issues": ["Nasal around 1kHz", "Harshness"],
        },
        "high_mid": {
            "keywords": ["hi-hat", "hh", "cymbal", "bright", "hat"],
            "range": "2-6 kHz",
            "typical_issues": ["Sibilance", "Presence fights"],
        },
        "high": {
            "keywords": ["air", "shaker", "perc", "crash", "ride"],
            "range": "6-20 kHz",
            "typical_issues": ["Harshness", "Listening fatigue"],
        },
    }

    async def analyze_frequency_balance(self, tracks: list[Track]) -> AnalysisResult:
        """Analyze frequency balance across tracks using name-based heuristics.

        Since raw audio data is not accessible, this classifies tracks by
        their names to estimate frequency distribution and identify
        potential mixing issues.
        """
        from ableton_mcp.domain.entities import TrackType

        # Classify tracks by likely frequency content
        frequency_distribution: dict[str, list[str]] = {
            "sub_bass": [],
            "bass": [],
            "low_mid": [],
            "mid": [],
            "high_mid": [],
            "high": [],
            "unknown": [],
        }

        for track in tracks:
            track_lower = track.name.lower()
            classified = False

            for range_name, info in self.FREQUENCY_KEYWORDS.items():
                if any(kw in track_lower for kw in info["keywords"]):
                    frequency_distribution[range_name].append(track.name)
                    classified = True
                    break

            if not classified:
                # Classify by track type as fallback
                if track.track_type == TrackType.MIDI:
                    frequency_distribution["mid"].append(track.name)
                else:
                    frequency_distribution["unknown"].append(track.name)

        # Identify potential issues
        issues: list[dict[str, Any]] = []
        suggestions: list[str] = []

        # Check for bass conflicts
        bass_tracks = frequency_distribution["sub_bass"] + frequency_distribution["bass"]
        if len(bass_tracks) > 2:
            issues.append(
                {
                    "type": "frequency_conflict",
                    "range": "bass",
                    "tracks": bass_tracks,
                    "description": "Multiple bass elements may cause masking",
                }
            )
            suggestions.append("Use sidechain compression between bass elements")
            suggestions.append("EQ carving: kick at 60Hz, bass at 80-100Hz")

        # Check for mid buildup
        mid_tracks = frequency_distribution["low_mid"] + frequency_distribution["mid"]
        if len(mid_tracks) > 4:
            issues.append(
                {
                    "type": "frequency_buildup",
                    "range": "mids",
                    "tracks": mid_tracks[:5],
                    "description": "Potential mid-frequency congestion",
                }
            )
            suggestions.append("Cut 300-500Hz on non-bass instruments")
            suggestions.append("Use different EQ curves to create separation")

        # Check for missing high frequency content
        high_content = frequency_distribution["high"] + frequency_distribution["high_mid"]
        if not high_content:
            issues.append(
                {
                    "type": "frequency_gap",
                    "range": "highs",
                    "description": "Limited high-frequency content detected",
                }
            )
            suggestions.append("Add subtle high-shelf boost on master (10-12kHz)")
            suggestions.append("Consider adding air/brightness to lead elements")

        # Check for too many elements in one range
        for range_name, track_names in frequency_distribution.items():
            if range_name != "unknown" and len(track_names) > 3:
                issues.append(
                    {
                        "type": "crowded_range",
                        "range": range_name,
                        "count": len(track_names),
                        "description": f"Many elements competing in {range_name} range",
                    }
                )

        # Generic mixing suggestions
        suggestions.extend(
            [
                "High-pass filter non-bass instruments at 80-100Hz",
                "Cut muddy frequencies around 300-400Hz on most tracks",
                "Leave headroom on individual tracks for master processing",
            ]
        )

        # Determine high frequency status
        if len(high_content) >= 2:
            high_freq_status = "adequate"
        elif len(high_content) == 1:
            high_freq_status = "minimal"
        else:
            high_freq_status = "lacking"

        return AnalysisResult(
            analysis_type="frequency_balance",
            confidence=0.6,  # Moderate confidence (heuristic-based)
            data={
                "frequency_distribution": {k: v for k, v in frequency_distribution.items() if v},
                "track_count_by_range": {k: len(v) for k, v in frequency_distribution.items()},
                "bass_heavy_tracks": bass_tracks,
                "high_frequency_content": high_freq_status,
                "potential_issues": issues,
                "masking_issues": [i for i in issues if i["type"] == "frequency_conflict"],
                "suggestions": suggestions[:8],
                "analysis_method": "heuristic_name_based",
                "note": "Analysis based on track naming. Use spectrum analyzer for accurate frequency analysis.",
            },
        )

    async def suggest_eq_adjustments(self, track: Track) -> list[dict[str, Any]]:
        """Suggest EQ adjustments for a track."""
        # Placeholder implementation based on track type
        suggestions = []

        if track.track_type.value == "midi":
            # Assuming this might be a virtual instrument
            suggestions.append(
                {
                    "frequency": 100,
                    "gain": -2,
                    "q": 0.7,
                    "type": "high_pass",
                    "description": "Remove sub-bass rumble",
                }
            )

        elif "vocal" in track.name.lower():
            suggestions.extend(
                [
                    {
                        "frequency": 80,
                        "gain": 0,
                        "q": 0.7,
                        "type": "high_pass",
                        "description": "Remove low rumble",
                    },
                    {
                        "frequency": 3000,
                        "gain": 2,
                        "q": 1.0,
                        "type": "bell",
                        "description": "Add presence",
                    },
                    {
                        "frequency": 12000,
                        "gain": 1,
                        "q": 0.5,
                        "type": "high_shelf",
                        "description": "Add air",
                    },
                ]
            )

        elif "drum" in track.name.lower() or "kick" in track.name.lower():
            suggestions.extend(
                [
                    {
                        "frequency": 60,
                        "gain": 2,
                        "q": 1.0,
                        "type": "bell",
                        "description": "Boost sub-bass",
                    },
                    {
                        "frequency": 2500,
                        "gain": 1,
                        "q": 1.0,
                        "type": "bell",
                        "description": "Add click",
                    },
                ]
            )

        return suggestions

    async def analyze_stereo_image(self, tracks: list[Track]) -> AnalysisResult:
        """Analyze stereo imaging and panning."""
        # Calculate panning distribution
        left_heavy = sum(1 for track in tracks if track.pan < -0.3)
        center = sum(1 for track in tracks if -0.3 <= track.pan <= 0.3)
        right_heavy = sum(1 for track in tracks if track.pan > 0.3)

        return AnalysisResult(
            analysis_type="stereo_image",
            confidence=0.8,
            data={
                "left_elements": left_heavy,
                "center_elements": center,
                "right_elements": right_heavy,
                "balance": "good" if abs(left_heavy - right_heavy) <= 1 else "unbalanced",
                "suggestions": [
                    "Keep bass elements centered",
                    "Pan percussion elements for width",
                    "Use complementary panning for similar instruments",
                ],
            },
        )

    async def calculate_lufs_target(self, genre: str, platform: str) -> tuple[float, float]:
        """Calculate target LUFS and peak levels for genre/platform."""
        # Streaming platform targets
        platform_targets = {
            "spotify": -14,
            "apple_music": -16,
            "youtube": -14,
            "tidal": -14,
            "soundcloud": -12,
            "bandcamp": -16,
        }

        # Genre adjustments
        genre_adjustments = {
            "electronic": 1,  # Slightly louder
            "hip_hop": 1,
            "pop": 0,
            "rock": 0,
            "jazz": -2,  # More dynamic range
            "classical": -6,  # Much more dynamic range
        }

        base_lufs = platform_targets.get(platform.lower(), -14)
        genre_adj = genre_adjustments.get(genre.lower(), 0)
        target_lufs = base_lufs + genre_adj

        # True peak should be at least -1 dBFS, more for genres needing headroom
        target_peak = -3.0 if genre.lower() in ["jazz", "classical"] else -1.0

        return target_lufs, target_peak
