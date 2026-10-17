"""Small public Analysis surface for Sample Brain consumers.

This facade exposes only the frozen, database-free analysis contracts and
computation. Implementation ownership remains in the explicit domain modules.
"""

from __future__ import annotations

from .analysis_contracts import (
    ANALYZE_HOP_LENGTH,
    ANALYZE_SR,
    BPMNormalizationMode,
    Features,
    validate_bpm_normalization,
)
from .attack_analysis import AttackSuggestion, suggest_attack_ms
from .bpm_matching import score_bpm_match
from .classification import rule_type
from .feature_analysis import extract_features, normalize_bpm
from .gesture_analysis import GestureAnalysis, GestureEvent, analyze_gesture_audio
from .harmony import (
    HarmonyInput,
    HarmonyRelation,
    HarmonySuggestion,
    determine_relation,
    find_harmony_matches,
    rate_harmony,
)
from . import key_analysis_v2_core as _key_analysis_v2_core

KeyAnalysisV2Result = _key_analysis_v2_core.KeyAnalysisV2Result
estimate_key_v2_shadow = _key_analysis_v2_core.estimate_key_v2_shadow
from .key_signature import (
    ParsedKey,
    format_key_signature,
    is_same_mode,
    is_same_root,
    key_distance_semitones,
    parse_key_signature,
)

__all__ = [
    "ANALYZE_HOP_LENGTH",
    "ANALYZE_SR",
    "AttackSuggestion",
    "BPMNormalizationMode",
    "Features",
    "GestureAnalysis",
    "GestureEvent",
    "HarmonyInput",
    "HarmonyRelation",
    "HarmonySuggestion",
    "KeyAnalysisV2Result",
    "ParsedKey",
    "analyze_gesture_audio",
    "determine_relation",
    "estimate_key_v2_shadow",
    "extract_features",
    "find_harmony_matches",
    "format_key_signature",
    "is_same_mode",
    "is_same_root",
    "key_distance_semitones",
    "normalize_bpm",
    "parse_key_signature",
    "rate_harmony",
    "rule_type",
    "score_bpm_match",
    "suggest_attack_ms",
    "validate_bpm_normalization",
]
