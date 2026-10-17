---
doc_id: analysis-architecture
doc_type: architecture
lifecycle: active
authority: canonical
scope: package-architecture
---

# Analysis package architecture

The distribution contains pure or local-file analysis contracts and
computation. Its import root is `sample_brain_analysis`. `__init__.py` is the
public facade; each public name has one implementation owner recorded in the
[v1 contract](docs/contracts/analysis-public-api-v1.md).

| Package module | Owner responsibility |
| --- | --- |
| `analysis_contracts` | Shared result types, analysis constants, BPM normalization contract |
| `feature_analysis` | Feature extraction and BPM normalization computation |
| `classification` | Deterministic rule-based type classification |
| `key_analysis_v2_core` | Pure shadow key-estimation algorithm and result |
| `joint_key_profile` | Joint-key profile computation |
| `bpm_matching` | BPM candidate score |
| `attack_analysis` | Attack suggestion computation |
| `gesture_analysis` | Gesture result types and local audio analysis |
| `harmony` | Harmony contracts, relation and match scoring |
| `key_signature` | Key signature parsing, formatting, and comparisons |
| `canon_audio` | Canonical audio read/write and provenance primitives |
| `bpm_display`, `content_hash`, `utils` | Narrow shared helpers required by the owners above |

The extraction preserves behavior and public names from Sample Brain main
`bd302c70084e481a1189f0aeddb2392273357d75`. Package modules must not import
Sample Brain modules. The allowed runtime dependency roots are `librosa`,
`numpy`, and `soundfile`, plus the Python standard library. No direct SciPy,
database, SQLAlchemy, UI toolkit, environment-state, or network dependency is
part of this v1 boundary.

## Ownership ledger

| Item | Current owner | Destination | Exposure | Action | Evidence |
| --- | --- | --- | --- | --- | --- |
| Analysis contracts, features, classification, key core/profile, BPM matching, attack, gesture, harmony, key signatures, canonical audio | `sample-brain/src` | This package | Internal modules; frozen facade only | Move once; consumer retains delegating compatibility facades as needed | Package boundary and behavioral tests |
| `bpm_display`, `content_hash`, `utils` used by moved algorithms | `sample-brain/src` | This package | Internal helpers | Move shared ownership; consumer adapters delegate | Import closure test |
| Frozen public facade | `sample-brain/src/analysis.py` | `sample_brain_analysis` | Public v1 | Re-home and preserve names/owner identity | Public manifest test |
| Pure behavioral tests and generated synthetic audio | `sample-brain/tests` | This package | Test-only | Move/adapt pure contracts and synthetic fixtures; exclude app/database/evaluation assertions | Package test suite |
| Harmony theory truth table | Synthetic fixture in `sample-brain/tests` | This package test data | Test-only | Move only the self-contained synthetic table | Harmony contract tests |
| Public API and ownership contract | Sample Brain docs | Package contract docs | Public | Rewrite for the independent distribution | Contract review |
| Analysis boundary and architecture | Sample Brain docs | Package architecture/canon docs | Public | Rewrite package-owned and app-owned boundaries | Boundary review |
| Knowledge Standard v1 and deterministic checker | New repository | This repository | Maintainer tooling | Define and validate metadata, relations, links, and routing | Checker tests and CI |
| Scan, catalog DB, SQLAlchemy/SQLite, DB batches/upserts, CLI accounting | `sample-brain` | `sample-brain` | Application-owned | Stay | Consumer tests |
| Classification seed/index/DB orchestration and `pred_type` adapter | `sample-brain` | `sample-brain` | Application-owned | Stay; call the library computation behind adapters | Consumer tests |
| Key V2 persistence adapter, candidate DB loading, Track Map/Context/Asset projection | `sample-brain` | `sample-brain` | Application-owned | Stay | Consumer integration tests |
| Workbench, Session, QML, controllers, UI state and product cache | `sample-brain` | `sample-brain` | Application-owned | Stay | Consumer UI tests |
| Realtime audio ownership, packaging/installers | `sample-brain` | `sample-brain` | Application-owned | Stay | Consumer/runtime checks |
| AQ/quality loop, benchmark orchestration, evidence and promotion decisions | `sample-brain` | `sample-brain` | Application/evaluation-owned | Stay; do not infer quality from extraction | Existing evaluation gates |

## Import behavior

Importing the package must not inspect the current directory, read
`SAMPLE_BRAIN_*` environment variables, contact the network, create directories,
or initialize application state. File access is explicit through the relevant
analysis call. The package does not own a real-time audio clock or playback
engine.

## Release boundary

The initial version is `0.1.0`; it is a versioned GitHub wheel, not a PyPI
release. A consumer migration is valid only after the corresponding artifact
exists and its hash/version are pinned by the consumer. Extraction alone does
not establish analysis quality or production readiness.
