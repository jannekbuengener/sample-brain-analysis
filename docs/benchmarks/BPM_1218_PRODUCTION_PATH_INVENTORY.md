---
doc_id: bpm-1218-production-path-inventory
doc_type: reference
lifecycle: active
authority: supporting
scope: bpm-exact-tempo
---

# #1218 BPM production path inventory

Measurement baseline for sample-brain#1218 / sample-brain-analysis#18.
Not authorization for unrelated algorithm rewrites.

Exact Heads at inventory time:

- sample-brain: `0c6c5f77b26210f284185597c8520b105289db0d`
- sample-brain-analysis: `722b90231d2510aa5701df8d4f8b705f63cdbf31`

| STAGE | OWNER | FILE / MODULE | INPUT | OUTPUT | PRECISION | NORMALIZATION | ROUNDING | UNKNOWN | VERSION / RELEASE | CONSUMER |
|---|---|---|---|---|---|---|---|---|---|---|
| Estimator entry | sample-brain-analysis | `feature_analysis.extract_features` | audio path, duration, `bpm_normalization` | `Features` | float | default `none` | none at estimate | short clip / weak periodicity → `None` | package release wheel | sample-brain `analyze` |
| Period estimate | sample-brain-analysis | `_estimate_bpm_from_onset_intervals` | PCM `y`, `sr` | `float \| None` | sample-accurate interval | — | none | gate fail → `None` | #18 | Features.bpm |
| Scalar legacy helper | sample-brain-analysis | `_extract_bpm_scalar` | tempo object | `float \| None` | float | — | none | ≤0 / empty → `None` | retained | tests / normalize |
| Normalize | sample-brain-analysis | `normalize_bpm` | bpm, mode | `float \| None` | float | `none` / `heuristic` / `domain_110_170` | none | invalid mode → `None` | public API | Features.bpm |
| Result contract | sample-brain-analysis | `Features.bpm` | — | `float \| None` | float | — | none | `None` | public API v1 | consumer |
| Release artifact | sample-brain-analysis | GitHub Release `v*` wheel | tagged source | wheel + sha256 | — | — | — | — | tag=`v${VERSION}` | sample-brain pin |
| Consumer pin | sample-brain | `pyproject.toml` / `requirements.txt` | release URL | installed version | — | — | — | — | sha256 pinned | analyze / tests |
| Analyze persist | sample-brain | `src/analyze.py` | `Features.bpm` | SQL upsert | float passthrough | profile mode | none | skip when Features None | app | SQLite |
| SQLite | sample-brain | `src/db.py` `features.bpm` | float/NULL | REAL | SQLite REAL | — | none | NULL | schema | catalog |
| Catalog | sample-brain | `src/workbench_catalog.py` | `f.bpm` | `row.bpm` | float \| None | — | none | None | — | QML / SYNC / Harmony |
| Browser QML | sample-brain | `src/workbench_qml.py` | `row.bpm` | string `:g` | display of authoritative float | — | formatting only | `"—"` | — | Screen-1 Browser |
| Display int (non-Browser) | sample-brain-analysis | `bpm_display.round_bpm_display` | float | int | integer | — | half-up | placeholder | package | Tk / FL / CSV |
| SYNC rate | sample-brain | `session_grid.compute_sync_playback_rate` | master/source floats | rate, status | full float ratio | none | none | `not_syncable` | #1215 consumer | transport / loops |
| Harmony BPM leg | sample-brain-analysis | `harmony` / `bpm_matching` | candidate/reference bpm | score | float; tol 8 BPM | half/double match penalty 0.9 | display ints in reasons | missing → no score | package | Workbench harmonic match |

## Grep notes

- No integer coercion on analysis → SQLite write path.
- QML does not estimate BPM.
- `round_bpm_display` is display/reconcile only, not Browser authority.
- Unknown is `None` / NULL / `"—"` — not `0` or default `120` on the analyze path.
