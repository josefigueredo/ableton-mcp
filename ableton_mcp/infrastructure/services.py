"""Concrete implementations of domain services."""

import math
from typing import Dict, List, Optional, Tuple

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
            "ii_V_I": [1, 4, 0],        # Dm G C
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
            "i_iv_VII_iv": [0, 5, 10, 5],    # Am Dm G Dm
            "i_VI_III_VII": [0, 8, 3, 10],   # Am F C G
            "i_v_i_v": [0, 7, 0, 7],         # Am Em Am Em
        },
        "rock": {
            "I_V_vi_IV": [0, 4, 5, 3],  # C G Am F
            "I_VII_IV_I": [0, 10, 3, 0],  # C Bb F C
            "vi_IV_I_V": [5, 3, 0, 4],   # Am F C G
            "I_IV_V_I": [0, 3, 4, 0],    # C F G C
        }
    }

    async def analyze_key(self, notes: List[Note]) -> List[MusicKey]:
        """Analyze the musical key of given notes."""
        if not notes:
            return []

        # Extract pitch classes from notes
        pitch_classes = list(set(note.pitch_class for note in notes))
        
        # Calculate key candidates with confidence scores
        key_candidates = []
        
        for scale_name, scale_intervals in self.SCALES.items():
            for root in range(12):
                scale_notes = set((root + interval) % 12 for interval in scale_intervals)
                
                # Calculate match score using Jaccard similarity
                intersection = len(set(pitch_classes).intersection(scale_notes))
                union = len(set(pitch_classes).union(scale_notes))
                
                if union > 0:
                    confidence = intersection / union
                    
                    # Boost confidence for exact matches
                    if set(pitch_classes).issubset(scale_notes):
                        confidence += 0.2
                    
                    # Penalize for missing important scale degrees
                    if root not in pitch_classes:  # Missing tonic
                        confidence *= 0.8
                    
                    if confidence > 0.3:  # Only include reasonable matches
                        key_candidates.append(
                            MusicKey(root=root, mode=scale_name, confidence=min(1.0, confidence))
                        )
        
        # Sort by confidence and return top candidates
        return sorted(key_candidates, key=lambda k: k.confidence, reverse=True)[:5]

    async def suggest_chord_progressions(
        self, key: MusicKey, genre: str
    ) -> List[List[int]]:
        """Suggest chord progressions for a given key and genre."""
        if genre not in self.CHORD_PROGRESSIONS:
            genre = "pop"  # Default to pop progressions
        
        progressions = []
        scale_intervals = self.SCALES.get(key.mode, self.SCALES["major"])
        
        for prog_name, progression in self.CHORD_PROGRESSIONS[genre].items():
            # Transpose progression to the given key
            transposed_progression = []
            for degree in progression:
                if degree < len(scale_intervals):
                    chord_root = (key.root + scale_intervals[degree]) % 12
                    transposed_progression.append(chord_root)
            
            if transposed_progression:
                progressions.append(transposed_progression)
        
        return progressions

    async def harmonize_melody(self, melody_notes: List[Note], key: MusicKey) -> List[Note]:
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

    async def quantize_notes(self, notes: List[Note], grid_division: float = 0.25) -> List[Note]:
        """Quantize notes to a rhythmic grid."""
        quantized_notes = []
        
        for note in notes:
            # Quantize start time
            quantized_start = round(note.start / grid_division) * grid_division
            
            # Quantize duration to nearest grid division
            quantized_duration = max(grid_division, round(note.duration / grid_division) * grid_division)
            
            quantized_note = Note(
                pitch=note.pitch,
                start=quantized_start,
                duration=quantized_duration,
                velocity=note.velocity,
                mute=note.mute,
            )
            quantized_notes.append(quantized_note)
        
        return quantized_notes

    async def filter_notes_to_scale(self, notes: List[Note], key: MusicKey) -> List[Note]:
        """Filter notes to fit within a musical scale."""
        scale_intervals = self.SCALES.get(key.mode, self.SCALES["major"])
        scale_notes = set((key.root + interval) % 12 for interval in scale_intervals)
        
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
                        abs(note_pitch_class - scale_note),
                        12 - abs(note_pitch_class - scale_note)
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
        """Detect tempo from an audio clip."""
        # In a real implementation, this would use audio analysis libraries
        # like librosa, essentia, or aubio for beat tracking
        # For now, return a placeholder
        return 120.0

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
        """Analyze rhythmic patterns in a clip."""
        # Placeholder implementation - would use advanced rhythm analysis
        return AnalysisResult(
            analysis_type="rhythmic_pattern",
            confidence=0.8,
            data={
                "pattern_type": "4/4",
                "complexity": "medium",
                "groove_type": "straight",
                "syncopation_level": 0.3,
            }
        )

    async def suggest_tempo_changes(
        self, song: Song, target_energy: List[float]
    ) -> List[Tuple[float, float]]:
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

    async def analyze_song_structure(self, song: Song) -> AnalysisResult:
        """Analyze the structure of a song."""
        # Placeholder implementation - would analyze audio/MIDI content
        return AnalysisResult(
            analysis_type="song_structure",
            confidence=0.7,
            data={
                "sections": ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "outro"],
                "total_length": len(song.tracks) * 32,  # Placeholder calculation
                "repetition_factor": 0.6,
                "energy_curve": [0.2, 0.5, 0.8, 0.5, 0.8, 0.6, 0.9, 0.3],
            }
        )

    async def suggest_arrangement_improvements(self, song: Song, genre: str) -> List[str]:
        """Suggest improvements to song arrangement."""
        suggestions = []
        
        # Analyze current structure
        num_tracks = len(song.tracks)
        song_length_bars = 128  # Placeholder
        
        # Genre-specific suggestions
        if genre.lower() == "pop":
            if song_length_bars < 100:
                suggestions.append("Consider extending song length - pop songs typically run 3-4 minutes")
            if num_tracks < 8:
                suggestions.append("Add more harmonic layers - consider strings or background vocals")
        
        elif genre.lower() in ["electronic", "house", "techno"]:
            if song_length_bars < 150:
                suggestions.append("Electronic tracks benefit from longer arrangements for DJ mixing")
            suggestions.append("Consider adding breakdown sections for dynamic contrast")
        
        # Universal suggestions
        if num_tracks > 20:
            suggestions.append("High track count - consider grouping similar elements")
        
        suggestions.append("Use the 'rule of 3' - repeat musical ideas 3 times before changing")
        suggestions.append("Create energy peaks and valleys for listener engagement")
        
        return suggestions

    async def calculate_energy_curve(self, song: Song) -> List[Tuple[float, float]]:
        """Calculate energy levels throughout the song."""
        # Placeholder implementation - would analyze amplitude, frequency content, etc.
        energy_points = []
        duration = 240.0  # 4 minutes in seconds
        
        for i in range(32):  # 32 points across the song
            time = (i / 31) * duration
            
            # Create a typical energy curve shape
            if i < 4:  # Intro
                energy = 0.2 + i * 0.1
            elif i < 8:  # Verse 1
                energy = 0.5
            elif i < 12:  # Chorus 1
                energy = 0.8
            elif i < 16:  # Verse 2
                energy = 0.6
            elif i < 20:  # Chorus 2
                energy = 0.9
            elif i < 24:  # Bridge
                energy = 0.4
            elif i < 28:  # Final Chorus
                energy = 1.0
            else:  # Outro
                energy = max(0.1, 0.8 - (i - 28) * 0.2)
            
            energy_points.append((time, energy))
        
        return energy_points

    async def suggest_section_lengths(self, genre: str, song_length: float) -> Dict[str, float]:
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

    async def analyze_frequency_balance(self, tracks: List[Track]) -> AnalysisResult:
        """Analyze frequency balance across tracks."""
        # Placeholder implementation - would use FFT analysis
        return AnalysisResult(
            analysis_type="frequency_balance",
            confidence=0.6,
            data={
                "bass_heavy_tracks": [],
                "mid_frequency_buildup": ["Track 3", "Track 5"],
                "high_frequency_content": "adequate",
                "masking_issues": [],
                "suggestions": [
                    "High-pass filter non-bass instruments at 80-100Hz",
                    "Cut around 300-500Hz to reduce muddiness",
                    "Add subtle high-shelf at 10kHz for air"
                ]
            }
        )

    async def suggest_eq_adjustments(self, track: Track) -> List[Dict[str, float]]:
        """Suggest EQ adjustments for a track."""
        # Placeholder implementation based on track type
        suggestions = []
        
        if track.track_type.value == "midi":
            # Assuming this might be a virtual instrument
            suggestions.append({
                "frequency": 100,
                "gain": -2,
                "q": 0.7,
                "type": "high_pass",
                "description": "Remove sub-bass rumble"
            })
            
        elif "vocal" in track.name.lower():
            suggestions.extend([
                {"frequency": 80, "gain": 0, "q": 0.7, "type": "high_pass", "description": "Remove low rumble"},
                {"frequency": 3000, "gain": 2, "q": 1.0, "type": "bell", "description": "Add presence"},
                {"frequency": 12000, "gain": 1, "q": 0.5, "type": "high_shelf", "description": "Add air"},
            ])
            
        elif "drum" in track.name.lower() or "kick" in track.name.lower():
            suggestions.extend([
                {"frequency": 60, "gain": 2, "q": 1.0, "type": "bell", "description": "Boost sub-bass"},
                {"frequency": 2500, "gain": 1, "q": 1.0, "type": "bell", "description": "Add click"},
            ])
            
        return suggestions

    async def analyze_stereo_image(self, tracks: List[Track]) -> AnalysisResult:
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
                    "Use complementary panning for similar instruments"
                ]
            }
        )

    async def calculate_lufs_target(self, genre: str, platform: str) -> Tuple[float, float]:
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
        if genre.lower() in ["jazz", "classical"]:
            target_peak = -3.0
        else:
            target_peak = -1.0
        
        return target_lufs, target_peak