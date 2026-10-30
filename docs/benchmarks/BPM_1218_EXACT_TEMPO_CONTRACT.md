---
doc_id: bpm-1218-exact-tempo-contract
doc_type: contract
lifecycle: active
authority: supporting
scope: bpm-exact-tempo
---

# #1218 exact-tempo evaluation contract

Derived from sample-brain#1218. Distinct from AQ1 ±0.5/±1/±2 BPM bands.

## Layers

| Layer | Rule |
|---|---|
| Ground truth | PCM-realized BPM from generated beat sample positions (`60 * sr / median_interval`), never requested parameter alone and never metadata tags |
| Representation | ≥ 0.01 BPM resolution preserved Analysis → release → persist → Browser |
| `ELIGIBLE_EXACT` accuracy | Predeclared fixtures only: `abs(result - truth) ≤ 0.005` and `round(result, 2) == round(truth, 2)` with `bpm_normalization="none"` |
| Tempo family | half/double on `ELIGIBLE_EXACT` or intentional traps = defect |
| Abstention | non-periodic / silence / one-shot / ultrashort → `None` |
| Determinism | same input + version + config → identical BPM |

## `ELIGIBLE_EXACT` predeclaration

Frozen from fixture geometry before any analyzer call:

- duration ≥ 8.0 s
- pulse count ≥ 16
- structure ∈ {mono_pulse_train, mono_kick_transient}
- leading silence ≤ 0.05 s
- sample rate 44100 (ANALYZE_SR); other rates are VARIATION
- mono
- interval jitter ≤ 1 sample
- not a half/double trap, not force_variation, not abstain_expected

Membership is never revised after seeing analyzer results.
