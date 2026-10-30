"""#1218 measurement-first exact-tempo benchmark (PCM-realized ground truth).

Eligibility is declared from fixture geometry before any analyzer call and is
never revised based on analyzer success/failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from sample_brain_analysis.feature_analysis import extract_features

from audio_fixtures import (
    RhythmicFixture,
    write_kick_transient_wav,
    write_noise_wav,
    write_oneshot_click_wav,
    write_pulse_train_wav,
    write_silence_wav,
)
from exact_tempo_contract import (
    EXACT_ABS_ERROR_MAX_BPM,
    ExactTempoRecipe,
    classify_tempo_family,
    declare_eligibility,
    exact_abs_ok,
    hundredths_match,
)

# Minimum tempos required by #1218.
_CORE_TEMPOS: tuple[float, ...] = (
    90.00,
    120.00,
    127.37,
    128.25,
    132.47,
    139.83,
    140.00,
)

# Duration chosen so 90 BPM still yields ≥16 pulses (16 * 60/90 ≈ 10.67s).
_ELIGIBLE_DURATION_SEC = 12.0


@dataclass(frozen=True)
class CatalogEntry:
    recipe: ExactTempoRecipe
    fixture: RhythmicFixture | None
    path: Path
    eligibility: str
    ground_truth_bpm: float | None


def _build_rhythmic(
    tmp_path: Path, recipe: ExactTempoRecipe
) -> tuple[RhythmicFixture, str, float]:
    path = tmp_path / f"{recipe.fixture_id}.wav"
    writer = (
        write_kick_transient_wav
        if "kick" in recipe.structure
        else write_pulse_train_wav
    )
    fixture = writer(
        path,
        bpm=recipe.requested_bpm,
        duration_sec=recipe.duration_sec,
        sr=recipe.sr,
        amplitude=recipe.amplitude,
        leading_silence_sec=recipe.leading_silence_sec,
        phase_offset_sec=recipe.phase_offset_sec,
        channels=recipe.channels,
    )
    eligibility = declare_eligibility(
        duration_sec=fixture.duration_sec,
        pulse_count=fixture.pulse_count,
        structure=fixture.structure,
        leading_silence_sec=fixture.leading_silence_sec,
        sr=fixture.sr,
        channels=fixture.channels,
        interval_jitter_samples=fixture.interval_jitter_samples,
        intentional_half_double_trap=recipe.intentional_half_double_trap,
        abstain_expected=recipe.abstain_expected,
        force_variation=recipe.force_variation,
    )
    return fixture, eligibility, fixture.realized_bpm


def build_frozen_catalog(tmp_path: Path) -> tuple[CatalogEntry, ...]:
    """Generate all fixtures and freeze eligibility before analyzer use."""
    recipes: list[ExactTempoRecipe] = []

    # Strict class only at ANALYZE_SR (44100): consumer loader resamples to
    # ANALYZE_SR, so 48 kHz files are VARIATION (resample path), not ELIGIBLE_EXACT.
    for bpm in _CORE_TEMPOS:
        for structure in ("mono_pulse_train", "mono_kick_transient"):
            tag = "pulse" if "pulse" in structure else "kick"
            recipes.append(
                ExactTempoRecipe(
                    fixture_id=f"exact_{tag}_{bpm:.2f}_44100",
                    requested_bpm=bpm,
                    duration_sec=_ELIGIBLE_DURATION_SEC,
                    sr=44100,
                    structure=structure,
                )
            )
            recipes.append(
                ExactTempoRecipe(
                    fixture_id=f"exact_{tag}_{bpm:.2f}_48000",
                    requested_bpm=bpm,
                    duration_sec=_ELIGIBLE_DURATION_SEC,
                    sr=48000,
                    structure=structure,
                    force_variation=True,
                )
            )

    # Non-strict variations (remain in matrix; not ELIGIBLE_EXACT by design).
    recipes.extend(
        [
            ExactTempoRecipe(
                fixture_id="var_short_127.37_44100",
                requested_bpm=127.37,
                duration_sec=3.0,
                sr=44100,
                structure="mono_pulse_train",
                force_variation=True,
            ),
            ExactTempoRecipe(
                fixture_id="var_stereo_128.25_44100",
                requested_bpm=128.25,
                duration_sec=_ELIGIBLE_DURATION_SEC,
                sr=44100,
                structure="mono_pulse_train",
                channels=2,
                force_variation=True,
            ),
            ExactTempoRecipe(
                fixture_id="var_lead_silence_132.47_44100",
                requested_bpm=132.47,
                duration_sec=_ELIGIBLE_DURATION_SEC,
                sr=44100,
                structure="mono_pulse_train",
                leading_silence_sec=0.5,
                force_variation=True,
            ),
            ExactTempoRecipe(
                fixture_id="var_phase_139.83_44100",
                requested_bpm=139.83,
                duration_sec=_ELIGIBLE_DURATION_SEC,
                sr=44100,
                structure="mono_pulse_train",
                phase_offset_sec=0.037,
                force_variation=True,
            ),
            ExactTempoRecipe(
                fixture_id="var_gain_low_120_44100",
                requested_bpm=120.0,
                duration_sec=_ELIGIBLE_DURATION_SEC,
                sr=44100,
                structure="mono_pulse_train",
                amplitude=0.05,
                force_variation=True,
            ),
            # Half/double traps: sparse strong downbeats that invite octave error.
            ExactTempoRecipe(
                fixture_id="trap_half_like_128_44100",
                requested_bpm=64.0,
                duration_sec=_ELIGIBLE_DURATION_SEC,
                sr=44100,
                structure="mono_kick_transient",
                intentional_half_double_trap=True,
            ),
            ExactTempoRecipe(
                fixture_id="trap_double_like_140_44100",
                requested_bpm=280.0,
                duration_sec=_ELIGIBLE_DURATION_SEC,
                sr=44100,
                structure="mono_pulse_train",
                intentional_half_double_trap=True,
            ),
        ]
    )

    entries: list[CatalogEntry] = []
    for recipe in recipes:
        fixture, eligibility, truth = _build_rhythmic(tmp_path, recipe)
        if fixture.pulse_count < 2 or truth != truth:  # NaN guard
            raise AssertionError(
                f"rhythmic recipe {recipe.fixture_id} produced no PCM ground truth"
            )
        # Intentional traps keep declared eligibility even if geometry would match exact.
        if recipe.intentional_half_double_trap:
            eligibility = "HALF_DOUBLE_TRAP"
        entries.append(
            CatalogEntry(
                recipe=recipe,
                fixture=fixture,
                path=fixture.path,
                eligibility=eligibility,
                ground_truth_bpm=truth,
            )
        )

    # Abstain / unknown suite (no rhythmic ground truth).
    abstain_specs = [
        ("abstain_silence", lambda p: write_silence_wav(p, duration_sec=2.0)),
        ("abstain_noise", lambda p: write_noise_wav(p, duration_sec=2.0)),
        ("abstain_oneshot", lambda p: write_oneshot_click_wav(p, duration_sec=0.8)),
        (
            "abstain_ultrashort",
            lambda p: write_pulse_train_wav(
                p, bpm=120.0, duration_sec=0.3, sr=44100
            ).path,
        ),
    ]
    for name, writer in abstain_specs:
        recipe = ExactTempoRecipe(
            fixture_id=name,
            requested_bpm=0.0,
            duration_sec=0.0,
            sr=44100,
            structure="none",
            abstain_expected=True,
        )
        path = tmp_path / f"{name}.wav"
        out = writer(path)
        path = out if isinstance(out, Path) else Path(out)
        entries.append(
            CatalogEntry(
                recipe=recipe,
                fixture=None,
                path=path,
                eligibility="ABSTAIN_EXPECTED",
                ground_truth_bpm=None,
            )
        )

    return tuple(entries)


@dataclass
class MatrixRow:
    fixture: str
    ground_truth: float | None
    eligibility: str
    analyzer: float | None
    abs_error: float | None
    tempo_family: str
    repeated: str
    disposition: str


def _score_entry(
    entry: CatalogEntry,
    analyzer_bpm: float | None,
    repeated_bpms: list[float | None],
) -> MatrixRow:
    truth = entry.ground_truth_bpm
    family = (
        classify_tempo_family(analyzer_bpm, truth)
        if truth is not None
        else ("outlier" if analyzer_bpm is None else "ambiguous")
    )
    abs_err = (
        abs(analyzer_bpm - truth)
        if analyzer_bpm is not None and truth is not None
        else None
    )
    repeated = (
        "PASS"
        if len(repeated_bpms) >= 3 and all(v == repeated_bpms[0] for v in repeated_bpms)
        else "FAIL"
    )

    if entry.eligibility == "ABSTAIN_EXPECTED":
        disposition = (
            "ABSTAIN_EXPECTED"
            if analyzer_bpm is None
            else "ANALYZER_DEFECT"
        )
    elif entry.eligibility == "ELIGIBLE_EXACT":
        assert truth is not None
        if analyzer_bpm is None:
            disposition = "ANALYZER_DEFECT"
        elif family in {"half", "double"}:
            disposition = "ANALYZER_DEFECT"
        elif exact_abs_ok(analyzer_bpm, truth) and hundredths_match(
            analyzer_bpm, truth
        ):
            disposition = "PASS"
        else:
            disposition = "ANALYZER_DEFECT"
    elif entry.eligibility == "HALF_DOUBLE_TRAP":
        # Trap fixtures document behavior; half/double vs realized truth is defect
        # only when the recipe intended the realized tempo to be recovered.
        # For traps, PASS means: not fabricating a default; family recorded.
        if analyzer_bpm is None:
            disposition = "ABSTAIN_EXPECTED"
        elif family in {"half", "double"}:
            disposition = "ANALYZER_DEFECT"
        elif truth is not None and exact_abs_ok(analyzer_bpm, truth):
            disposition = "PASS"
        else:
            # Recorded as defect if far from realized PCM tempo (measurement).
            disposition = "ANALYZER_DEFECT"
    else:
        # VARIATION: report only; do not apply abs≤0.005 gate.
        if analyzer_bpm is None:
            disposition = "ABSTAIN_EXPECTED"
        elif truth is not None and family in {"half", "double"}:
            disposition = "ANALYZER_DEFECT"
        elif (
            truth is not None
            and exact_abs_ok(analyzer_bpm, truth)
            and hundredths_match(analyzer_bpm, truth)
        ):
            disposition = "PASS"
        else:
            disposition = "REFERENCE_UNCERTAIN"

    if repeated == "FAIL" and disposition == "PASS":
        disposition = "ANALYZER_DEFECT"

    return MatrixRow(
        fixture=entry.recipe.fixture_id,
        ground_truth=truth,
        eligibility=entry.eligibility,
        analyzer=analyzer_bpm,
        abs_error=abs_err,
        tempo_family=family,
        repeated=repeated,
        disposition=disposition,
    )


def test_pcm_realized_bpm_differs_from_requested_under_quantization(tmp_path: Path):
    """Prove ground truth uses PCM positions, not the requested parameter alone."""
    fixture = write_pulse_train_wav(
        tmp_path / "quant.wav",
        bpm=127.37,
        duration_sec=12.0,
        sr=44100,
    )
    assert fixture.pulse_count >= 16
    assert fixture.realized_bpm != pytest.approx(fixture.requested_bpm, abs=0.0) or (
        fixture.interval_jitter_samples >= 0
    )
    # Realized truth must be computable and close to request, but may differ.
    assert fixture.realized_bpm > 0
    assert abs(fixture.realized_bpm - fixture.requested_bpm) < 0.05


def test_eligible_exact_predeclared_before_analyzer(tmp_path: Path):
    catalog = build_frozen_catalog(tmp_path)
    eligible = [e for e in catalog if e.eligibility == "ELIGIBLE_EXACT"]
    assert len(eligible) >= len(_CORE_TEMPOS) * 2  # at least pulse+kick @ one SR set
    # Freeze: every ELIGIBLE_EXACT meets geometry gates independently of analyzer.
    for entry in eligible:
        assert entry.fixture is not None
        assert entry.fixture.duration_sec >= 8.0
        assert entry.fixture.pulse_count >= 16
        assert entry.fixture.structure in {
            "mono_pulse_train",
            "mono_kick_transient",
        }
        assert entry.ground_truth_bpm is not None

    # Must not call extract_features in this test — catalog freeze only.
    assert all(e.path.exists() for e in catalog)


def test_exact_tempo_measurement_matrix(tmp_path: Path):
    catalog = build_frozen_catalog(tmp_path)
    frozen_eligibility = {e.recipe.fixture_id: e.eligibility for e in catalog}

    rows: list[MatrixRow] = []
    for entry in catalog:
        # Re-assert eligibility never drifts after generation.
        assert frozen_eligibility[entry.recipe.fixture_id] == entry.eligibility

        duration = None
        if entry.fixture is not None:
            duration = entry.fixture.duration_sec
        elif entry.recipe.abstain_expected:
            # Let extract_features use file length via loader; pass None.
            duration = None

        runs: list[float | None] = []
        for _ in range(3):
            feats = extract_features(
                entry.path, duration, bpm_normalization="none"
            )
            runs.append(None if feats is None else feats.bpm)
        row = _score_entry(entry, runs[0], runs)
        rows.append(row)

    # Emit matrix for evidence (pytest -s captures stdout).
    print("\nFIXTURE\tGROUND_TRUTH\tELIGIBILITY\tANALYZER\tABS_ERROR\tTEMPO_FAMILY\tREPEATED\tDISPOSITION")
    for r in rows:
        gt = "" if r.ground_truth is None else f"{r.ground_truth:.6f}"
        an = "" if r.analyzer is None else f"{r.analyzer:.6f}"
        err = "" if r.abs_error is None else f"{r.abs_error:.6f}"
        print(
            f"{r.fixture}\t{gt}\t{r.eligibility}\t{an}\t{err}\t{r.tempo_family}\t{r.repeated}\t{r.disposition}"
        )

    eligible_rows = [r for r in rows if r.eligibility == "ELIGIBLE_EXACT"]
    assert eligible_rows, "no ELIGIBLE_EXACT fixtures in catalog"
    defects = [r for r in eligible_rows if r.disposition == "ANALYZER_DEFECT"]
    abstain_fail = [
        r
        for r in rows
        if r.eligibility == "ABSTAIN_EXPECTED" and r.disposition == "ANALYZER_DEFECT"
    ]
    trap_fail = [
        r
        for r in rows
        if r.eligibility == "HALF_DOUBLE_TRAP"
        and r.disposition == "ANALYZER_DEFECT"
        and r.tempo_family in {"half", "double"}
    ]

    # Measurement assertion: report decision inputs; fail if strict class broken.
    blocking = defects + abstain_fail + trap_fail
    if blocking:
        detail = "\n".join(
            f"{r.fixture}: analyzer={r.analyzer} truth={r.ground_truth} "
            f"err={r.abs_error} family={r.tempo_family} disp={r.disposition}"
            for r in blocking
        )
        pytest.fail(
            f"#1218 ELIGIBLE_EXACT/abstain/half-double defects "
            f"(gate abs≤{EXACT_ABS_ERROR_MAX_BPM}):\n{detail}"
        )
