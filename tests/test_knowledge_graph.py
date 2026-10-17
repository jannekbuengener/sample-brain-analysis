from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "tools" / "check_knowledge_graph.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _valid_repo(root: Path) -> None:
    _write(root / "tools/check_knowledge_graph.py", "# fixture checker\n")
    _write(
        root / "PROJECT_META.yaml",
        """schema_version: 1
project:
  name: sample-brain-analysis
  system: sample-brain
  role: analysis-library
package:
  distribution_name: sample-brain-analysis
  import_name: sample_brain_analysis
ownership:
  analysis: local
consumers:
  - repository: jannekbuengener/sample-brain
canonical_docs:
  architecture: ARCHITECTURE.md
  canon: docs/canon/README.md
  contracts: docs/contracts/README.md
  validation: docs/validation/README.md
quality_gates:
  tests: python -m pytest -q
  lint: python -m ruff check .
  knowledge: python tools/check_knowledge_graph.py
  whitespace: git diff --check
policy:
  offline_first: true
  private_data_in_repo: false
""",
    )
    _write(
        root / "docs/README.md",
        """---
doc_id: docs-router
doc_type: reference
lifecycle: active
authority: canonical
scope: docs
---

# Docs

- [Canon](canon/README.md)
- [Architecture](architecture/boundaries.md)
- [Contracts](contracts/README.md)
- [Validation](validation/README.md)
""",
    )
    _write(root / "ARCHITECTURE.md", "# Architecture\n")
    for rel, doc_id, doc_type in (
        ("canon/README.md", "canon", "reference"),
        ("architecture/boundaries.md", "boundaries", "architecture"),
        ("contracts/README.md", "contracts", "contract"),
        ("validation/README.md", "validation", "validation"),
    ):
        _write(
            root / "docs" / rel,
            f"---\ndoc_id: {doc_id}\ndoc_type: {doc_type}\nlifecycle: active\nauthority: canonical\nscope: analysis\n---\n\n# {doc_id}\n",
        )


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_clean_knowledge_tree_passes_offline(tmp_path: Path) -> None:
    _valid_repo(tmp_path)

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_checker_reports_missing_metadata_duplicate_ids_and_broken_links(
    tmp_path: Path,
) -> None:
    _valid_repo(tmp_path)
    _write(tmp_path / "docs/architecture/boundaries.md", "# Missing frontmatter\n")
    _write(
        tmp_path / "docs/contracts/extra.md",
        "---\ndoc_id: validation\ndoc_type: invalid\nlifecycle: active\nauthority: canonical\nscope: analysis\n---\n\n[broken](missing.md)\n",
    )
    _write(tmp_path / "docs/README.md", "# Docs\n\n[Missing](missing-router.md)\n")

    result = _run(tmp_path)

    assert result.returncode != 0
    for expected in ("frontmatter", "duplicate doc_id", "doc_type", "missing.md", "unreachable"):
        assert expected in (result.stdout + result.stderr)


def test_checker_rejects_inconsistent_supersession_and_dependency_cycles(
    tmp_path: Path,
) -> None:
    _valid_repo(tmp_path)
    _write(
        tmp_path / "docs/architecture/a.md",
        "---\ndoc_id: a\ndoc_type: architecture\nlifecycle: active\nauthority: supporting\nscope: analysis\ndepends_on: [b]\nsupersedes: [b]\n---\n",
    )
    _write(
        tmp_path / "docs/architecture/b.md",
        "---\ndoc_id: b\ndoc_type: architecture\nlifecycle: active\nauthority: supporting\nscope: analysis\ndepends_on: [a]\n---\n",
    )

    result = _run(tmp_path)

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "depends_on cycle" in output
    assert "supersession" in output


def test_checker_rejects_machine_paths_and_missing_generated_source(
    tmp_path: Path,
) -> None:
    _valid_repo(tmp_path)
    _write(
        tmp_path / "docs/validation/leak.md",
        "---\ndoc_id: leak\ndoc_type: validation\nlifecycle: active\nauthority: generated\nscope: analysis\ngenerated_from: tools/missing.py\n---\n\nC:\\Users\\janne\\samples\\kick.wav\n",
    )
    _write(tmp_path / "docs/README.md", "# Docs\n")

    result = _run(tmp_path)

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "machine-local" in output
    assert "generated_from" in output
