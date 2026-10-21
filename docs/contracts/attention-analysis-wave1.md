---
doc_id: attention-analysis-wave1
doc_type: contract
lifecycle: active
authority: canonical
scope: spectral-envelope-analysis
---

# Attention Analysis Wave 1 — Spectral + Envelope Evidence Contract

## Status

**ACTIVE CANON / OWNER RE-ENTRY 2026-10-21**

Issue owner: `#15` — Spectral understanding as a first-class analysis dimension.

This contract freezes the Analysis-side evidence required by the first Sample Brain Ambient Attention / Contextual Browser experiment. It does **not** authorize consumer persistence/UI work, automatic recommendation behavior, Artist Model work, Live rendered-context work, or a consumer release by itself.

## 1. Purpose

Wave 1 answers one narrow Analysis question:

> What deterministic, reusable evidence about a sample is needed so the consumer can later reason about spectral occupancy, complementarity, overlap risk and transient/envelope contrast?

The Analysis package measures audio. It does not decide which sample a producer should choose.

Conceptually:

```text
Audio
  ↓
versioned measured evidence
  ↓
released Analysis DTOs
  ↓
sample-brain consumer
  ↓
context / ranking / Browser salience
```

## 2. Ownership boundary

`sample-brain-analysis` owns:

- deterministic per-sample DSP compute;
- Analysis DTOs/contracts;
- algorithm/config provenance;
- abstention/invalid semantics;
- synthetic deterministic fixtures;
- package-local performance/reproducibility evidence.

`sample-brain` owns:

- SQLite/SQLAlchemy persistence;
- corpus statistics and percentiles;
- Live Kit/Edit context aggregation;
- candidate context scoring;
- ranking, salience, hysteresis and Top-K policy;
- Browser/QML presentation;
- Artist Model / preference learning;
- later rendered/live context;
- final product/runtime acceptance.

The Analysis package MUST NOT gain DB, UI, network or product-ranking ownership from this contract.

## 3. Compatibility with current Analysis canon

Current shared Analysis constants remain authoritative for Wave 1:

```text
ANALYZE_SR = 44100
ANALYZE_HOP_LENGTH = 512
```

The external research proposal to use a 48 kHz analysis path is **not** adopted here. A future sample-rate contract change requires separate evidence and a versioned decision.

Wave 1 MUST NOT silently change the meaning of the existing public `Features` DTO.

Existing Gesture Analysis remains protected:

```text
FEATURE_DIM = 15
RMS(1) + spectral centroid(1) + MFCC mean(13)
CLUSTER_DISTANCE_THRESHOLD = 5.0
```

No Wave-1 implementation may alter that vector, normalization or threshold without a separate recalibration contract.

## 4. Evidence taxonomy

Every value must remain classifiable as one of:

1. **MEASURED** — direct deterministic DSP evidence;
2. **DERIVED** — deterministic transformation/aggregation of measured evidence;
3. **HEURISTIC** — calibrated interpretation requiring evaluation;
4. **SUBJECTIVE/PREFERENCE** — producer judgement, outside Analysis ownership.

Wave 1 Analysis DTOs contain MEASURED evidence plus explicit provenance/status. They do not contain subjective labels such as `warm`, `punchy`, `good`, `bad`, `best` or `recommended`.

## 5. Contract family

Wave-1 measurements should be exposed as a separate versioned result family rather than overloading the current `Features` semantics.

Logical result:

```text
AttentionAnalysisV1
├── provenance
├── spectral
└── envelope
```

Exact Python class/module names are implementation details, but the semantics below are canonical.

## 6. Provenance contract

Required logical fields:

```text
schema_version
analysis_sample_rate
analysis_hop_length
spectral_schema_id
envelope_schema_id
extractor_version
config_fingerprint
status
invalid_reason?
```

Allowed top-level statuses:

```text
OK
UNREADABLE
SILENCE
TOO_SHORT
INVALID
```

Rules:

- no absolute path is required in the DTO;
- no library/user/project identity is required;
- `invalid_reason` is a stable machine code, not arbitrary free text;
- incompatible schema/config versions must never be silently mixed;
- no public float may be NaN or infinity.

## 7. Spectral Profile V1

Purpose: describe **where spectral energy lives** without converting it into musical judgement.

Logical fields:

```text
SpectralProfileV1
├── band_schema_id
├── band_share[]
├── band_power_dbfs[]?      # optional absolute companion
├── spectral_centroid_hz
├── spectral_bandwidth_hz
├── rolloff_85_hz
├── rolloff_95_hz
├── spectral_flatness
└── spectral_sketch?        # compact time × band summary
```

### `band_share[]`

- non-negative relative band energy;
- approximately sums to `1.0` for valid non-silent material;
- intended to be gain-invariant;
- band count/edges are defined by `band_schema_id`.

### `band_power_dbfs[]`

- optional absolute-energy companion;
- gain-sensitive by definition;
- MUST NOT be substituted for normalized `band_share` semantics.

### `spectral_centroid_hz`

Measured spectral center of mass.

The existing consumer-facing `brightness` field keeps its current semantics until an explicit consumer migration/reconciliation decision exists.

### `spectral_bandwidth_hz`

Measured spread around spectral centroid.

### `rolloff_85_hz` / `rolloff_95_hz`

Measured spectral extent at versioned cumulative-energy thresholds.

### `spectral_flatness`

Measured noise-like versus peak-dominated spectral structure. It is not a semantic class.

### `spectral_sketch`

Optional compact time-varying evidence for loops/evolving material.

Rules:

- fixed bounded shape per schema version;
- no default persisted full spectrogram;
- no product persistence semantics inside this package;
- shape/dtype/normalization must be versioned before public exposure.

## 8. Band schema policy

Wave 1 freezes **versioned band schemas**, not one eternal set of frequency edges.

Each promoted band schema defines:

```text
band_schema_id
band_edges_hz[]
normalization_semantics
```

Research candidate edges are:

```text
20–40
40–60
60–90
90–150
150–250
250–400
400–800
800–1600
1600–3200
3200–6400
6400–12000
12000–20000 Hz
```

These edges are `CALIBRATION_CANDIDATE`, not physical truth and not yet a frozen public V1 band schema.

Before promotion, the candidate grid must prove:

- meaningful information beyond current centroid/MFCC/chroma;
- adequate Techno low-end discrimination;
- sample-rate-canonicalized robustness;
- acceptable redundancy/correlation;
- bounded runtime/storage cost.

## 9. Envelope / Transient Profile V1

Purpose: describe **how energy appears and decays**.

Logical fields:

```text
EnvelopeProfileV1
├── rms_dbfs
├── sample_peak_dbfs
├── crest_factor_db
├── attack_ms
├── peak_time_ms
├── decay_20db_ms?
├── effective_duration_ms
├── transient_body_ratio_db
└── tail_energy_ratio
```

Rules:

- RMS/peak are explicitly gain-sensitive;
- crest factor and normalized shape metrics are intended to be gain-robust;
- `decay_20db_ms` is nullable when the threshold is not reached;
- leading/trailing silence policy must be versioned;
- unavailable values stay unavailable; do not zero-fill them as if measured evidence existed;
- this family remains independent from Gesture clustering features.

## 10. Conditional applicability and abstention

One-shots, loops, sustained textures, silence and extremely short files are not forced into identical evidence.

Required behavior:

- silence: explicit `SILENCE`; no fabricated normalized spectral distribution;
- unreadable input: explicit `UNREADABLE`;
- extremely short material: unsupported fields remain absent;
- insufficient frames for a metric: abstain for that metric;
- no feature becomes valid merely because a downstream consumer would prefer a complete vector.

## 11. Transform robustness contract

Every promoted field must declare whether it is expected to be invariant, robust, or intentionally sensitive to a transform.

Minimum evaluation dimensions:

| Transform | Required interpretation |
|---|---|
| Gain ±12 dB | normalized spectral/envelope-shape values stay within calibrated tolerance; absolute dB fields move predictably |
| Equivalent 44.1/48/96 kHz source | after current 44.1 kHz canonicalization, intended comparable values stay within calibrated tolerance |
| Mono vs equivalent dual-mono | all non-spatial Wave-1 values remain equivalent within tolerance |
| Leading/trailing silence | attack/duration behavior follows the frozen trimming/window policy |
| Complete silence | no NaN/Inf; explicit abstention/status |
| Extremely short input | unsupported fields absent, never fabricated |

Tolerance values are validation/calibration data, not semantic field definitions.

## 12. Shared-compute rule

Implementation should reuse common intermediate transforms where doing so preserves semantics and simplicity.

Preferred direction:

```text
one decoded/canonical waveform
        ↓
shared bounded spectral/envelope intermediates
        ↓
multiple measured fields
```

Do not repeatedly decode the same source or run equivalent FFT work per scalar metric without evidence that separation is required.

This is an implementation efficiency rule, not permission to couple unrelated public contracts.

## 13. Dependency rule

Initial implementation MUST first evaluate the existing dependency set:

```text
librosa
numpy
soundfile
```

A new runtime DSP dependency requires evidence that an important Wave-1 measurement cannot be implemented robustly enough with the current stack.

Reference libraries may inform algorithm comparison without becoming runtime dependencies.

## 14. Consumer interpretation boundary

The following concepts are **not Analysis measurements** and MUST stay in `sample-brain`:

```text
spectral_complementarity
spectral_overlap_risk
masking_risk
transient_complementarity
redundancy
context_fit
attention_salience
highlight_level
reason_codes
```

Analysis supplies evidence from which those values may later be derived.

Particularly:

> Static spectral overlap is not proof of final rendered masking.

EQ, gain, distortion, sidechain, bus processing and arrangement timing belong to later consumer/rendered-context evidence. Analysis must not claim those effects from source assets alone.

## 15. Wave-1 Analysis acceptance gates

A promoted implementation must prove at least:

### A1 — deterministic output

Same audio contents + same contract/config version produce the same status, shapes and values within documented numerical tolerances.

### A2 — no invalid public floats

NaN/Inf count across public result fields is zero.

### A3 — silence honesty

Silence returns explicit non-success evidence and no fabricated spectral profile.

### A4 — short-input honesty

Unsupported measurements are absent rather than guessed.

### A5 — gain behavior

Gain-invariant fields remain within calibrated tolerance under safe gain changes; gain-sensitive fields move predictably.

### A6 — sample-rate canonicalization

Equivalent 44.1/48/96 kHz fixtures remain within calibrated tolerance after the current 44.1 kHz analysis path.

### A7 — mono equivalence

Mono and equivalent dual-mono inputs produce equivalent non-spatial results.

### A8 — spectral golden fixtures

Generated low sine, high sine, broadband noise, band-limited noise, sweep and impulse fixtures produce directionally correct deterministic evidence.

### A9 — envelope golden fixtures

Generated controlled attack/decay fixtures preserve expected ordering such as fast-vs-slow attack and short-vs-long tail.

### A10 — existing-contract regression

Wave-1 work must not silently alter:

```text
Features semantics
BPM semantics
Key/Mode semantics
Gesture FEATURE_DIM
Gesture CLUSTER_DISTANCE_THRESHOLD
Gesture golden cases
```

## 16. Benchmark / promotion gate

No candidate metric is accepted because its number merely looks plausible.

Before a field is promoted to a released public contract, evaluate:

- deterministic synthetic fixtures;
- representative repo-safe audio classes;
- transform robustness;
- runtime/CPU cost;
- storage footprint of the result shape;
- correlation/redundancy against existing features;
- concrete consumer usefulness for contextual Browser evidence.

Metrics with no demonstrated independent value should be rejected.

## 17. Explicit Wave-1 non-goals

Not authorized by this Analysis contract:

```text
Artist Model
personal preference learning
Explore/Discovery model
Contextual Bandits
BPR
Browser/UI implementation
product persistence/schema migration
rendered Live context
realtime FFT tap
post-FX masking truth
beat-phase occupancy
new Key/Mode detector
new Harmonic Match ranking
LUFS/True Peak
Vector DB
new neural embedding
sample generation
automatic mixing
automatic arrangement
```

## 18. Calibration values not frozen here

The following require measured evidence before they become implementation constants:

```text
frequency-band edges
FFT/window details for the new profile
spectral-sketch shape
feature-specific numeric tolerances
consumer score weights
consumer highlight thresholds
consumer hysteresis
consumer highlight count
consumer latency SLOs
```

## 19. First executable Analysis slice after re-entry

The smallest evidence-producing slice is:

```text
1. inventory current spectral/envelope measurements at exact head;
2. implement a private/internal candidate extractor for the proposed V1 fields;
3. add deterministic synthetic fixtures and transform-robustness tests;
4. benchmark runtime and redundancy against current centroid/MFCC/chroma evidence;
5. decide which candidate fields survive;
6. only then freeze/export the minimal public V1 DTO surface.
```

This prevents the research inventory from turning directly into an oversized public API.

Consumer persistence and Ambient Browser work are routed separately to `sample-brain` after a versioned Analysis release exists.

## 20. Exit semantics

This contract establishes:

```text
ATTENTION_ANALYSIS_WAVE1_CONTRACT_ACTIVE
```

It does **not** establish:

```text
ANALYSIS_QUALITY_PROVEN
CONSUMER_INTEGRATED
ATTENTION_ENGINE_PRODUCT_READY
LIVE_ATTENTION_READY
```

Those require their owning evidence and repositories.