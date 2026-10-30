from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class RhythmicFixture:
    """Synthetic rhythmic WAV with PCM-realized tempo ground truth.

    ``realized_bpm`` is derived from actual beat sample positions after
    integer sample quantization — not from the requested ``bpm`` parameter alone.
    """

    path: Path
    sr: int
    beat_sample_positions: tuple[int, ...]
    requested_bpm: float
    realized_bpm: float
    duration_sec: float
    structure: str
    pulse_count: int
    leading_silence_sec: float
    channels: int
    interval_jitter_samples: int


def realized_bpm_from_beat_positions(
    positions: Sequence[int], sr: int
) -> float | None:
    """Ground-truth BPM from realized PCM beat starts (median interval)."""
    if sr <= 0 or len(positions) < 2:
        return None
    intervals = np.diff(np.asarray(positions, dtype=np.int64))
    positive = intervals[intervals > 0]
    if positive.size == 0:
        return None
    median_interval = float(np.median(positive.astype(np.float64)))
    if median_interval <= 0:
        return None
    return 60.0 * float(sr) / median_interval


def interval_jitter_samples(positions: Sequence[int]) -> int:
    if len(positions) < 2:
        return 0
    intervals = np.diff(np.asarray(positions, dtype=np.int64))
    positive = intervals[intervals > 0]
    if positive.size == 0:
        return 0
    return int(positive.max() - positive.min())


def _pulse_waveform(
    *,
    pulse_duration: float,
    sr: int,
    amplitude: float,
) -> np.ndarray:
    pulse_samples = max(1, int(pulse_duration * sr))
    if pulse_samples > 1:
        t_pulse = np.linspace(0.0, pulse_duration, pulse_samples, dtype=np.float32)
        envelope = np.linspace(1.0, 0.0, pulse_samples, dtype=np.float32) ** 2
        return amplitude * np.sin(2.0 * np.pi * 800.0 * t_pulse) * envelope
    return np.ones(1, dtype=np.float32) * amplitude


def _kick_waveform(
    *,
    interval_sec: float,
    sr: int,
    amplitude: float,
) -> np.ndarray:
    kick_duration = min(0.15, interval_sec * 0.4)
    kick_samples = max(1, int(kick_duration * sr))
    t_kick = np.linspace(0.0, kick_duration, kick_samples, dtype=np.float32)
    envelope = np.exp(-t_kick * 25.0)
    return amplitude * np.sin(2.0 * np.pi * 60.0 * t_kick) * envelope


def _place_periodic_events(
    *,
    n_total: int,
    bpm: float,
    sr: int,
    event: np.ndarray,
    leading_silence_sec: float = 0.0,
    phase_offset_sec: float = 0.0,
    duration_sec: float,
) -> tuple[np.ndarray, tuple[int, ...]]:
    """Place events on a constant integer sample period.

    Using ``round((60/bpm)*sr)`` as the period avoids float-accumulation
    jitter of 2+ samples that would unfairly exclude integer tempos from
    ELIGIBLE_EXACT. Ground truth is always derived from the returned positions.
    """
    y = np.zeros(n_total, dtype=np.float32)
    interval_sec = 60.0 / bpm
    interval_samples = max(1, int(round(interval_sec * sr)))
    event_samples = int(event.shape[0])
    lead = int(round(leading_silence_sec * sr))
    phase = int(round(phase_offset_sec * sr))
    usable_samples = max(0, n_total - lead)
    num_pulses = max(0, usable_samples // interval_samples)
    # Keep events fully inside the buffer.
    positions: list[int] = []
    for i in range(num_pulses):
        start = lead + phase + i * interval_samples
        if start < 0:
            continue
        if start + event_samples <= n_total:
            y[start : start + event_samples] += event.astype(np.float32)
            positions.append(start)
    return np.clip(y, -1.0, 1.0), tuple(positions)


def _write_audio(path: Path, y: np.ndarray, sr: int, channels: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if channels <= 1:
        sf.write(path, y, sr, subtype="PCM_16")
        return
    stereo = np.column_stack([y, y]).astype(np.float32)
    sf.write(path, stereo, sr, subtype="PCM_16")


def write_sine_wav(
    path: Path,
    *,
    duration_sec: float,
    frequency_hz: float,
    sr: int = 44100,
    amplitude: float = 0.5,
) -> Path:
    """Generate a deterministic mono sine-wave WAV fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_count = max(1, int(sr * duration_sec))
    t = np.linspace(0.0, duration_sec, sample_count, endpoint=False, dtype=np.float32)
    wave = amplitude * np.sin(2.0 * np.pi * frequency_hz * t)
    sf.write(path, wave.astype(np.float32), sr, subtype="PCM_16")
    return path


def write_pulse_train_wav(
    path: Path,
    *,
    bpm: float,
    duration_sec: float = 4.0,
    sr: int = 44100,
    pulse_duration: float = 0.005,
    amplitude: float = 0.8,
    leading_silence_sec: float = 0.0,
    phase_offset_sec: float = 0.0,
    channels: int = 1,
) -> RhythmicFixture:
    """Generate a rhythmic pulse-train WAV; ground truth from PCM positions."""
    n_total = max(1, int(sr * duration_sec))
    pulse = _pulse_waveform(
        pulse_duration=pulse_duration, sr=sr, amplitude=amplitude
    )
    y, positions = _place_periodic_events(
        n_total=n_total,
        bpm=bpm,
        sr=sr,
        event=pulse,
        leading_silence_sec=leading_silence_sec,
        phase_offset_sec=phase_offset_sec,
        duration_sec=duration_sec,
    )
    realized = realized_bpm_from_beat_positions(positions, sr)
    structure = "stereo_pulse_train" if channels > 1 else "mono_pulse_train"
    _write_audio(path, y, sr, channels)
    if realized is None:
        # Short / incomplete trains are valid for abstain fixtures; callers that
        # need ground truth must require pulse_count >= 2 themselves.
        realized = float("nan")
    return RhythmicFixture(
        path=path,
        sr=sr,
        beat_sample_positions=positions,
        requested_bpm=float(bpm),
        realized_bpm=float(realized),
        duration_sec=float(duration_sec),
        structure=structure,
        pulse_count=len(positions),
        leading_silence_sec=float(leading_silence_sec),
        channels=int(channels),
        interval_jitter_samples=interval_jitter_samples(positions),
    )


def write_kick_transient_wav(
    path: Path,
    *,
    bpm: float,
    duration_sec: float = 4.0,
    sr: int = 44100,
    amplitude: float = 0.8,
    leading_silence_sec: float = 0.0,
    phase_offset_sec: float = 0.0,
    channels: int = 1,
) -> RhythmicFixture:
    """Generate kick-like transients; ground truth from PCM positions."""
    n_total = max(1, int(sr * duration_sec))
    interval_sec = 60.0 / bpm
    kick = _kick_waveform(interval_sec=interval_sec, sr=sr, amplitude=amplitude)
    y, positions = _place_periodic_events(
        n_total=n_total,
        bpm=bpm,
        sr=sr,
        event=kick,
        leading_silence_sec=leading_silence_sec,
        phase_offset_sec=phase_offset_sec,
        duration_sec=duration_sec,
    )
    realized = realized_bpm_from_beat_positions(positions, sr)
    if realized is None:
        raise ValueError(f"kick transient produced insufficient beats: {path}")
    structure = "stereo_kick_transient" if channels > 1 else "mono_kick_transient"
    _write_audio(path, y, sr, channels)
    return RhythmicFixture(
        path=path,
        sr=sr,
        beat_sample_positions=positions,
        requested_bpm=float(bpm),
        realized_bpm=float(realized),
        duration_sec=float(duration_sec),
        structure=structure,
        pulse_count=len(positions),
        leading_silence_sec=float(leading_silence_sec),
        channels=int(channels),
        interval_jitter_samples=interval_jitter_samples(positions),
    )


def write_silence_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    sr: int = 44100,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_total = max(1, int(sr * duration_sec))
    sf.write(path, np.zeros(n_total, dtype=np.float32), sr, subtype="PCM_16")
    return path


def write_noise_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    sr: int = 44100,
    amplitude: float = 0.3,
    seed: int = 1218,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    n_total = max(1, int(sr * duration_sec))
    y = (amplitude * rng.standard_normal(n_total)).astype(np.float32)
    sf.write(path, np.clip(y, -1.0, 1.0), sr, subtype="PCM_16")
    return path


def write_oneshot_click_wav(
    path: Path,
    *,
    duration_sec: float = 0.8,
    sr: int = 44100,
    amplitude: float = 0.8,
) -> Path:
    """Single transient then silence — not a periodic tempo signal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n_total = max(1, int(sr * duration_sec))
    y = np.zeros(n_total, dtype=np.float32)
    pulse = _pulse_waveform(pulse_duration=0.01, sr=sr, amplitude=amplitude)
    end = min(n_total, pulse.shape[0])
    y[:end] = pulse[:end]
    sf.write(path, y, sr, subtype="PCM_16")
    return path


def _chord_wave(
    *,
    duration_sec: float,
    root_hz: float,
    third_ratio: float,
    fifth_ratio: float = 2.0 ** (7.0 / 12.0),
    sr: int = 44100,
    amplitude: float = 0.5,
) -> np.ndarray:
    sample_count = max(1, int(sr * duration_sec))
    t = np.linspace(0.0, duration_sec, sample_count, endpoint=False, dtype=np.float32)
    freqs = [root_hz, root_hz * third_ratio, root_hz * fifth_ratio]
    wave = sum(amplitude / 3.0 * np.sin(2.0 * np.pi * f * t) for f in freqs).astype(
        np.float32
    )
    return np.clip(wave, -1.0, 1.0)


def write_major_chord_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    frequency_hz: float = 261.63,
    sr: int = 44100,
    amplitude: float = 0.5,
) -> Path:
    """Deterministic major triad (root, major third, fifth) WAV fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wave = _chord_wave(
        duration_sec=duration_sec,
        root_hz=frequency_hz,
        third_ratio=2.0 ** (4.0 / 12.0),
        sr=sr,
        amplitude=amplitude,
    )
    sf.write(path, wave, sr, subtype="PCM_16")
    return path


def write_minor_chord_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    frequency_hz: float = 261.63,
    sr: int = 44100,
    amplitude: float = 0.5,
) -> Path:
    """Deterministic minor triad (root, minor third, fifth) WAV fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wave = _chord_wave(
        duration_sec=duration_sec,
        root_hz=frequency_hz,
        third_ratio=2.0 ** (3.0 / 12.0),
        sr=sr,
        amplitude=amplitude,
    )
    sf.write(path, wave, sr, subtype="PCM_16")
    return path


def write_root_fifth_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    frequency_hz: float = 261.63,
    sr: int = 44100,
    amplitude: float = 0.5,
) -> Path:
    """Deterministic root + perfect fifth (power chord) WAV fixture.

    Ambiguous for mode: contains no third, so neither major nor minor is
    evidenced.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_count = max(1, int(sr * duration_sec))
    t = np.linspace(0.0, duration_sec, sample_count, endpoint=False, dtype=np.float32)
    fifth_ratio = 2.0 ** (7.0 / 12.0)
    wave = sum(
        amplitude / 2.0 * np.sin(2.0 * np.pi * f * t)
        for f in (frequency_hz, frequency_hz * fifth_ratio)
    ).astype(np.float32)
    sf.write(path, np.clip(wave, -1.0, 1.0), sr, subtype="PCM_16")
    return path


def write_octave_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    frequency_hz: float = 261.63,
    sr: int = 44100,
    amplitude: float = 0.5,
) -> Path:
    """Deterministic root + octave WAV fixture (single pitch class, ambiguous)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_count = max(1, int(sr * duration_sec))
    t = np.linspace(0.0, duration_sec, sample_count, endpoint=False, dtype=np.float32)
    wave = sum(
        amplitude / 2.0 * np.sin(2.0 * np.pi * f * t)
        for f in (frequency_hz, frequency_hz * 2.0)
    ).astype(np.float32)
    sf.write(path, np.clip(wave, -1.0, 1.0), sr, subtype="PCM_16")
    return path


# Profile weights are retained only to synthesize deterministic tonal fixtures.
# The current root detector does not use Krumhansl-Schmuckler profile matching;
# it selects the strongest mean chroma pitch class.
_MAJOR_SCALE_DEGREES = (0, 2, 4, 5, 7, 9, 11)
_MINOR_SCALE_DEGREES = (0, 2, 3, 5, 7, 8, 10)
_MAJOR_KEY_WEIGHTS = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
_MINOR_KEY_WEIGHTS = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


def write_key_audio_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    frequency_hz: float = 261.63,
    mode: str = "maj",
    sr: int = 44100,
    amplitude: float = 0.5,
) -> Path:
    """Deterministic sustained 'known key' WAV built from a peaked triad.

    Root + third + fifth, with the root clearly dominant (as in real tonal
    audio). In the requested mode the third is the characteristic major/minor
    third. This gives ``estimate_key_mode`` (third-contrast detector) a clean
    Dur/Moll signal: the major third (root + 4) dominates for major fixtures and
    the minor third (root + 3) dominates for minor fixtures, yielding a contrast
    well above ``MODE_CONTRAST_MIN`` while keeping the root the dominant pitch
    class. Used by the synthetic validation gate in
    tests/test_key_mode_analysis.py.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "min":
        degrees = (0, 3, 7)
    else:
        degrees = (0, 4, 7)
    weights = (1.0, 0.85, 0.7)

    sample_count = max(1, int(sr * duration_sec))
    t = np.linspace(0.0, duration_sec, sample_count, endpoint=False, dtype=np.float32)
    wave = np.zeros(sample_count, dtype=np.float64)
    for deg, w in zip(degrees, weights):
        freq = frequency_hz * (2.0 ** (deg / 12.0))
        wave = wave + w * np.sin(2.0 * np.pi * freq * t)
    peak = float(np.max(np.abs(wave))) or 1.0
    wave = (amplitude * wave / peak).astype(np.float32)
    sf.write(path, wave, sr, subtype="PCM_16")
    return path


def write_major_minor_blend_wav(
    path: Path,
    *,
    duration_sec: float = 2.0,
    frequency_hz: float = 261.63,
    sr: int = 44100,
    amplitude: float = 0.5,
) -> Path:
    """Deterministic ambiguous blend: root + equal major & minor third + fifth.

    Neither Dur/Moll mode is evidenced, so the analyzer should abstain.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_count = max(1, int(sr * duration_sec))
    t = np.linspace(0.0, duration_sec, sample_count, endpoint=False, dtype=np.float32)
    freqs = [
        frequency_hz,
        frequency_hz * 2.0 ** (3.0 / 12.0),
        frequency_hz * 2.0 ** (4.0 / 12.0),
        frequency_hz * 2.0 ** (7.0 / 12.0),
    ]
    wave = sum(amplitude / 4.0 * np.sin(2.0 * np.pi * f * t) for f in freqs).astype(
        np.float32
    )
    sf.write(path, np.clip(wave, -1.0, 1.0), sr, subtype="PCM_16")
    return path
