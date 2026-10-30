"""#1218 exact-tempo evaluation contract — frozen before analyzer measurement.

Representation precision and eligible accuracy are distinct from AQ1 ±0.5/±1/±2
BPM bands. Do not loosen these gates to greenwash estimator error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Eligibility = Literal[
    "ELIGIBLE_EXACT",
    "VARIATION",
    "HALF_DOUBLE_TRAP",
    "ABSTAIN_EXPECTED",
]

# Strict gate for predeclared ELIGIBLE_EXACT only.
EXACT_ABS_ERROR_MAX_BPM = 0.005

ELIGIBLE_EXACT_MIN_DURATION_SEC = 8.0
ELIGIBLE_EXACT_MIN_PULSES = 16
ELIGIBLE_EXACT_MAX_LEADING_SILENCE_SEC = 0.05
ELIGIBLE_EXACT_STRUCTURES = frozenset({"mono_pulse_train", "mono_kick_transient"})
ELIGIBLE_EXACT_SAMPLE_RATES = frozenset({44100, 48000})
# Integer sample placement may alternate intervals by 1 sample for fractional BPM.
ELIGIBLE_EXACT_MAX_INTERVAL_JITTER_SAMPLES = 1

Disposition = Literal[
    "PASS",
    "ABSTAIN_EXPECTED",
    "ANALYZER_DEFECT",
    "CONSUMER_DEFECT",
    "REFERENCE_UNCERTAIN",
]


@dataclass(frozen=True)
class ExactTempoRecipe:
    """Fixture recipe. Eligibility is declared from this + generated pulse metadata,
    never from analyzer output.
    """

    fixture_id: str
    requested_bpm: float
    duration_sec: float
    sr: int
    structure: str
    leading_silence_sec: float = 0.0
    channels: int = 1
    amplitude: float = 0.8
    phase_offset_sec: float = 0.0
    intentional_half_double_trap: bool = False
    abstain_expected: bool = False
    force_variation: bool = False


def declare_eligibility(
    *,
    duration_sec: float,
    pulse_count: int,
    structure: str,
    leading_silence_sec: float,
    sr: int,
    channels: int,
    interval_jitter_samples: int,
    intentional_half_double_trap: bool,
    abstain_expected: bool,
    force_variation: bool = False,
) -> Eligibility:
    """Deterministic eligibility from fixture geometry only (no analyzer result)."""
    if abstain_expected:
        return "ABSTAIN_EXPECTED"
    if intentional_half_double_trap:
        return "HALF_DOUBLE_TRAP"
    if force_variation:
        return "VARIATION"
    if (
        duration_sec >= ELIGIBLE_EXACT_MIN_DURATION_SEC
        and pulse_count >= ELIGIBLE_EXACT_MIN_PULSES
        and structure in ELIGIBLE_EXACT_STRUCTURES
        and leading_silence_sec <= ELIGIBLE_EXACT_MAX_LEADING_SILENCE_SEC
        and sr in ELIGIBLE_EXACT_SAMPLE_RATES
        and channels == 1
        and interval_jitter_samples <= ELIGIBLE_EXACT_MAX_INTERVAL_JITTER_SAMPLES
        and not intentional_half_double_trap
        and not abstain_expected
        and not force_variation
    ):
        return "ELIGIBLE_EXACT"
    return "VARIATION"


def hundredths_match(result_bpm: float, truth_bpm: float) -> bool:
    return round(result_bpm, 2) == round(truth_bpm, 2)


def exact_abs_ok(result_bpm: float, truth_bpm: float) -> bool:
    return abs(result_bpm - truth_bpm) <= EXACT_ABS_ERROR_MAX_BPM


# Tempo-family ratios aligned with sample-brain bpm_evidence.classify_bpm_error
# (methodology reuse only — not AQ1 ±0.5 accuracy gates).
_CORRECT_RATIO = (0.95, 1.05)
_HALF_RATIO = (0.45, 0.55)
_DOUBLE_RATIO = (1.90, 2.10)


def classify_tempo_family(actual_bpm: float | None, truth_bpm: float) -> str:
    if actual_bpm is None or actual_bpm <= 0 or truth_bpm <= 0:
        return "outlier"
    ratio = actual_bpm / truth_bpm
    if _CORRECT_RATIO[0] <= ratio <= _CORRECT_RATIO[1]:
        return "correct"
    if _HALF_RATIO[0] <= ratio <= _HALF_RATIO[1]:
        return "half"
    if _DOUBLE_RATIO[0] <= ratio <= _DOUBLE_RATIO[1]:
        return "double"
    if 0.2 < ratio < 5.0:
        return "ambiguous"
    return "outlier"