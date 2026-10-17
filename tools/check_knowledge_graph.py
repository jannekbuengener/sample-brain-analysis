#!/usr/bin/env python3
"""Deterministic, offline integrity checks for durable Analysis documentation."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by a clean user environment
    raise SystemExit("Install the dev extra before running the knowledge gate: pip install -e '.[dev]'") from exc


DOC_TYPES = {"architecture", "contract", "decision", "spec", "runbook", "validation", "reference"}
LIFECYCLES = {"draft", "active", "superseded", "historical"}
AUTHORITIES = {"canonical", "supporting", "operational", "generated", "historical"}
REQUIRED_FIELDS = ("doc_id", "doc_type", "lifecycle", "authority", "scope")
FRONTMATTER = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
MACHINE_PATH = re.compile(
    r"(?:\b[A-Za-z]:[\\/]|\\\\[^\\\s]+\\|"
    r"(?<!:)\/(?:Users|home|tmp|workspace|private|mnt|Volumes)\/|"
    r"%USERPROFILE%|%LOCALAPPDATA%|\$HOME(?:/|\b)|~/)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Document:
    path: Path
    metadata: dict[str, object]
    body: str


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_yaml(path: Path, root: Path, errors: list[str]) -> dict[str, object] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"{_rel(root, path)}: invalid YAML: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{_rel(root, path)}: expected a YAML mapping")
        return None
    return value


def _load_docs(root: Path, errors: list[str]) -> list[Document]:
    docs_root = root / "docs"
    result: list[Document] = []
    for path in sorted(docs_root.rglob("*.md")) if docs_root.exists() else []:
        if path.is_symlink():
            errors.append(f"{_rel(root, path)}: symlinked governed docs are not allowed")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{_rel(root, path)}: cannot read UTF-8 Markdown: {exc}")
            continue
        match = FRONTMATTER.match(content)
        if match is None:
            errors.append(f"{_rel(root, path)}: missing YAML frontmatter")
            continue
        try:
            metadata = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            errors.append(f"{_rel(root, path)}: invalid frontmatter YAML: {exc}")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"{_rel(root, path)}: frontmatter must be a mapping")
            continue
        body = content[match.end():]
        result.append(Document(path=path, metadata=metadata, body=body))
    return result


def _values(metadata: dict[str, object], key: str) -> list[str]:
    value = metadata.get(key)
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [item for item in values if isinstance(item, str) and item]


def _validate_metadata(root: Path, docs: list[Document], errors: list[str]) -> dict[str, Document]:
    by_id: dict[str, Document] = {}
    duplicates: set[str] = set()
    for doc in docs:
        label = _rel(root, doc.path)
        for field in REQUIRED_FIELDS:
            value = doc.metadata.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: frontmatter field {field!r} is required and must be a non-empty string")
        for field, allowed in (("doc_type", DOC_TYPES), ("lifecycle", LIFECYCLES), ("authority", AUTHORITIES)):
            value = doc.metadata.get(field)
            if value is not None and value not in allowed:
                errors.append(f"{label}: invalid {field} {value!r}; allowed: {', '.join(sorted(allowed))}")
        doc_id = doc.metadata.get("doc_id")
        if isinstance(doc_id, str) and doc_id:
            if doc_id in by_id:
                duplicates.add(doc_id)
                errors.append(f"{label}: duplicate doc_id {doc_id!r} also used by {_rel(root, by_id[doc_id].path)}")
            else:
                by_id[doc_id] = doc
        text = doc.path.read_text(encoding="utf-8")
        if MACHINE_PATH.search(text):
            errors.append(f"{label}: machine-local or absolute path found in governed document")
    return by_id


def _link_target(root: Path, source: Path, destination: str) -> Path | None:
    split = urlsplit(destination.strip().split()[0].strip("<>"))
    if split.scheme or split.netloc or not split.path:
        return None
    decoded = unquote(split.path)
    if decoded.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", decoded):
        return Path("/")  # caller reports an invalid non-relative link
    target = (source.parent / decoded).resolve() if decoded else source.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return Path("/")
    return target


def _validate_links(root: Path, docs: list[Document], errors: list[str]) -> dict[Path, set[Path]]:
    graph: dict[Path, set[Path]] = defaultdict(set)
    for doc in docs:
        for match in MARKDOWN_LINK.finditer(doc.body):
            destination = match.group(1).strip()
            target = _link_target(root, doc.path, destination)
            if target is None:
                continue
            if target == Path("/"):
                errors.append(f"{_rel(root, doc.path)}: Markdown link must remain repo-relative: {destination!r}")
                continue
            if target.is_dir():
                target = target / "README.md"
            if not target.exists():
                errors.append(f"{_rel(root, doc.path)}: broken Markdown link {destination!r}")
                continue
            if target.suffix.lower() == ".md" and target.is_file():
                graph[doc.path.resolve()].add(target.resolve())
    return graph


def _validate_relations(root: Path, docs: list[Document], by_id: dict[str, Document], errors: list[str]) -> None:
    dependencies: dict[str, list[str]] = {}
    for doc in docs:
        source_id = doc.metadata.get("doc_id")
        if not isinstance(source_id, str) or not source_id:
            continue
        dependencies[source_id] = _values(doc.metadata, "depends_on")
        supersedes = _values(doc.metadata, "supersedes")
        superseded_by = _values(doc.metadata, "superseded_by")
        lifecycle = doc.metadata.get("lifecycle")
        label = _rel(root, doc.path)
        if superseded_by and lifecycle not in {"superseded", "historical"}:
            errors.append(f"{label}: superseded_by requires lifecycle superseded or historical")
        for target_id in supersedes:
            target = by_id.get(target_id)
            if target is None:
                errors.append(f"{label}: supersession target {target_id!r} does not exist")
                continue
            if source_id not in _values(target.metadata, "superseded_by"):
                errors.append(f"{label}: supersession is inconsistent; {target_id!r} must list {source_id!r} in superseded_by")
            if target.metadata.get("lifecycle") not in {"superseded", "historical"}:
                errors.append(f"{label}: supersession target {target_id!r} must be superseded or historical")
        for target_id in superseded_by:
            target = by_id.get(target_id)
            if target is None:
                errors.append(f"{label}: superseded_by target {target_id!r} does not exist")
            elif source_id not in _values(target.metadata, "supersedes"):
                errors.append(f"{label}: supersession is inconsistent; {target_id!r} must list {source_id!r} in supersedes")
        for target_id in dependencies[source_id]:
            if target_id not in by_id:
                errors.append(f"{label}: depends_on target {target_id!r} does not exist")

        generated_from = doc.metadata.get("generated_from")
        if generated_from is None and doc.metadata.get("authority") == "generated":
            errors.append(f"{label}: generated document requires generated_from")
        for source in _values(doc.metadata, "generated_from"):
            source_path = (root / source).resolve()
            try:
                source_path.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{label}: generated_from must be repo-relative: {source!r}")
                continue
            if not source_path.exists():
                errors.append(f"{label}: generated_from source does not exist: {source!r}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(doc_id: str, path: list[str]) -> None:
        if doc_id in visiting:
            cycle = " -> ".join(path + [doc_id])
            errors.append(f"{_rel(root, by_id[doc_id].path)}: depends_on cycle: {cycle}")
            return
        if doc_id in visited:
            return
        visiting.add(doc_id)
        for target_id in dependencies.get(doc_id, []):
            if target_id in by_id:
                visit(target_id, path + [doc_id])
        visiting.remove(doc_id)
        visited.add(doc_id)

    for doc_id in sorted(dependencies):
        visit(doc_id, [])


def _validate_reachability(root: Path, docs: list[Document], graph: dict[Path, set[Path]], errors: list[str]) -> None:
    router = root / "docs" / "README.md"
    if not router.is_file():
        errors.append("docs/README.md: required docs router does not exist")
        return
    by_path = {doc.path.resolve(): doc for doc in docs}
    reachable: set[Path] = set()
    pending = [router.resolve()]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(graph.get(current, ()))
    for path, doc in by_path.items():
        if doc.metadata.get("lifecycle") == "active" and doc.metadata.get("authority") == "canonical" and path not in reachable:
            errors.append(f"{_rel(root, path)}: active canonical document is unreachable from docs/README.md")


def _validate_project_meta(root: Path, errors: list[str]) -> None:
    path = root / "PROJECT_META.yaml"
    if not path.is_file():
        errors.append("PROJECT_META.yaml: required project metadata file does not exist")
        return
    metadata = _load_yaml(path, root, errors)
    if metadata is None:
        return
    for section_name in ("project", "package", "ownership", "canonical_docs", "quality_gates", "policy"):
        if not isinstance(metadata.get(section_name), dict):
            errors.append(f"PROJECT_META.yaml: {section_name} must be a mapping")
    canonical = metadata.get("canonical_docs")
    if isinstance(canonical, dict):
        for key, value in canonical.items():
            if not isinstance(value, str) or not value:
                errors.append(f"PROJECT_META.yaml: canonical_docs.{key} must be a repo-relative path")
                continue
            target = (root / value).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                errors.append(f"PROJECT_META.yaml: canonical_docs.{key} must be repo-relative")
                continue
            if not target.exists():
                errors.append(f"PROJECT_META.yaml: canonical_docs.{key} path does not exist: {value}")
    gates = metadata.get("quality_gates")
    if isinstance(gates, dict):
        for key in ("tests", "lint", "knowledge", "whitespace"):
            if not isinstance(gates.get(key), str) or not gates[key].strip():
                errors.append(f"PROJECT_META.yaml: quality_gates.{key} must be a non-empty command")
        knowledge = gates.get("knowledge")
        if isinstance(knowledge, str) and "tools/check_knowledge_graph.py" in knowledge and not (root / "tools/check_knowledge_graph.py").is_file():
            errors.append("PROJECT_META.yaml: quality_gates.knowledge points to a missing checker")


def check(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    if not root.is_dir():
        return [f"repository root does not exist: {root}"]
    docs = _load_docs(root, errors)
    by_id = _validate_metadata(root, docs, errors)
    link_graph = _validate_links(root, docs, errors)
    _validate_relations(root, docs, by_id, errors)
    _validate_reachability(root, docs, link_graph, errors)
    _validate_project_meta(root, errors)
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = check(args.root)
    if errors:
        print("Knowledge graph check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Knowledge graph check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
