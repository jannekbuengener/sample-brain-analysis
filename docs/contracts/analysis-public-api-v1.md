---
doc_id: analysis-public-api-v1
doc_type: contract
lifecycle: active
authority: canonical
scope: public-python-api
---

# Analysis public API v1

Distribution: `sample-brain-analysis`. Import root: `sample_brain_analysis`.
The v1 API is the exact `__all__` manifest below. Each public symbol is owned
by the named module; the package facade must re-export that same object.

| Public name | Owner module |
| --- | --- |
| `ANALYZE_HOP_LENGTH` | `analysis_contracts` |
| `ANALYZE_SR` | `analysis_contracts` |
| `AttackSuggestion` | `attack_analysis` |
| `BPMNormalizationMode` | `analysis_contracts` |
| `Features` | `analysis_contracts` |
| `GestureAnalysis` | `gesture_analysis` |
| `GestureEvent` | `gesture_analysis` |
| `HarmonyInput` | `harmony` |
| `HarmonyRelation` | `harmony` |
| `HarmonySuggestion` | `harmony` |
| `KeyAnalysisV2Result` | `key_analysis_v2_core` |
| `ParsedKey` | `key_signature` |
| `analyze_gesture_audio` | `gesture_analysis` |
| `determine_relation` | `harmony` |
| `estimate_key_v2_shadow` | `key_analysis_v2_core` |
| `extract_features` | `feature_analysis` |
| `find_harmony_matches` | `harmony` |
| `format_key_signature` | `key_signature` |
| `is_same_mode` | `key_signature` |
| `is_same_root` | `key_signature` |
| `key_distance_semitones` | `key_signature` |
| `normalize_bpm` | `feature_analysis` |
| `parse_key_signature` | `key_signature` |
| `rate_harmony` | `harmony` |
| `rule_type` | `classification` |
| `score_bpm_match` | `bpm_matching` |
| `suggest_attack_ms` | `attack_analysis` |
| `validate_bpm_normalization` | `analysis_contracts` |

These names and owner identities are frozen for v1. Adding a name requires a
contract change and tests. Renaming, removing, or changing semantics requires a
new explicitly reviewed contract decision. Internal module paths are not
promised as a consumer API beyond the owners listed here.

The facade does not promise product persistence, catalog orchestration,
classification seed policy, quality uplift, or runtime readiness. Consumers
own those decisions and adapters.
