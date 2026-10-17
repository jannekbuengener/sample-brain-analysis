from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "sample_brain_analysis"
IMPORT_ROOT = "sample_brain_analysis"
PUBLIC_API = (
    "ANALYZE_HOP_LENGTH", "ANALYZE_SR", "AttackSuggestion", "BPMNormalizationMode",
    "Features", "GestureAnalysis", "GestureEvent", "HarmonyInput", "HarmonyRelation",
    "HarmonySuggestion", "KeyAnalysisV2Result", "ParsedKey", "analyze_gesture_audio",
    "determine_relation", "estimate_key_v2_shadow", "extract_features", "find_harmony_matches",
    "format_key_signature", "is_same_mode", "is_same_root", "key_distance_semitones",
    "normalize_bpm", "parse_key_signature", "rate_harmony", "rule_type", "score_bpm_match",
    "suggest_attack_ms", "validate_bpm_normalization",
)
OWNERS = {
    "ANALYZE_HOP_LENGTH": "analysis_contracts", "ANALYZE_SR": "analysis_contracts",
    "AttackSuggestion": "attack_analysis", "BPMNormalizationMode": "analysis_contracts",
    "Features": "analysis_contracts", "GestureAnalysis": "gesture_analysis",
    "GestureEvent": "gesture_analysis", "HarmonyInput": "harmony",
    "HarmonyRelation": "harmony", "HarmonySuggestion": "harmony",
    "KeyAnalysisV2Result": "key_analysis_v2_core", "ParsedKey": "key_signature",
    "analyze_gesture_audio": "gesture_analysis", "determine_relation": "harmony",
    "estimate_key_v2_shadow": "key_analysis_v2_core", "extract_features": "feature_analysis",
    "find_harmony_matches": "harmony", "format_key_signature": "key_signature",
    "is_same_mode": "key_signature", "is_same_root": "key_signature",
    "key_distance_semitones": "key_signature", "normalize_bpm": "feature_analysis",
    "parse_key_signature": "key_signature", "rate_harmony": "harmony",
    "rule_type": "classification", "score_bpm_match": "bpm_matching",
    "suggest_attack_ms": "attack_analysis", "validate_bpm_normalization": "analysis_contracts",
}
MODULES = (
    "__init__", "analysis_contracts", "feature_analysis", "classification",
    "key_analysis_v2_core", "joint_key_profile", "bpm_matching", "attack_analysis",
    "gesture_analysis", "harmony", "key_signature", "canon_audio", "bpm_display",
    "content_hash", "utils",
)
ALLOWED_EXTERNAL = {"librosa", "numpy", "soundfile"}
FORBIDDEN_ROOTS = {"sqlite3", "_sqlite3", "sqlalchemy", "PySide6", "tkinter", "src"}


def test_public_manifest_and_canonical_owner_identity_are_frozen() -> None:
    api = importlib.import_module(IMPORT_ROOT)
    assert tuple(api.__all__) == PUBLIC_API
    assert set(OWNERS) == set(PUBLIC_API)
    for name, owner in OWNERS.items():
        assert getattr(api, name) is getattr(importlib.import_module(f"{IMPORT_ROOT}.{owner}"), name)


def test_transitive_package_import_closure_has_no_application_or_unknown_dependencies() -> None:
    pending = [f"{IMPORT_ROOT}.{module}" if module != "__init__" else IMPORT_ROOT for module in MODULES]
    seen: set[str] = set()
    imports: set[str] = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        relative = module.removeprefix(f"{IMPORT_ROOT}.").replace(".", "/")
        path = SOURCE_ROOT / ("__init__.py" if module == IMPORT_ROOT else f"{relative}.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        package = module if path.name == "__init__.py" else module.rpartition(".")[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = importlib.util.resolve_name("." * node.level + (node.module or ""), package) if node.level else (node.module or "")
                if base:
                    imports.add(base)
        for imported in imports:
            if imported == IMPORT_ROOT or imported.startswith(f"{IMPORT_ROOT}."):
                if imported not in seen:
                    pending.append(imported)

    violations: list[str] = []
    for name in imports:
        root = name.split(".", 1)[0]
        if root in FORBIDDEN_ROOTS:
            violations.append(name)
        elif root not in sys.stdlib_module_names and root not in ALLOWED_EXTERNAL and root != IMPORT_ROOT:
            violations.append(name)
    assert not violations, sorted(violations)


def test_wheel_installs_and_imports_from_clean_foreign_directory(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    target = tmp_path / "install"
    wheelhouse.mkdir()
    target.mkdir()
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "--no-cache-dir", "--wheel-dir", str(wheelhouse), str(REPO_ROOT)],
        check=True,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    wheel = next(wheelhouse.glob("sample_brain_analysis-*.whl"))
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps", "--no-index", "--target", str(target), str(wheel)],
        check=True,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for key in tuple(env):
        if key.startswith("SAMPLE_BRAIN_"):
            env.pop(key, None)
    env["PYTHONPATH"] = str(target)
    result = subprocess.run(
        [sys.executable, "-c", "import os, sample_brain_analysis as a; cwd=os.getcwd(); assert a.validate_bpm_normalization('heuristic') == 'heuristic'; assert a.score_bpm_match(120,120,8) == 1.0; assert a.parse_key_signature('C major') is not None; assert os.getcwd() == cwd"],
        check=False,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
