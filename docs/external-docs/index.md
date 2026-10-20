---
doc_id: external-reference-index
doc_type: reference
lifecycle: active
authority: canonical
scope: documentation
---

# External References — Sample Brain Analysis

This index records external technical references that are materially relevant to the `sample-brain-analysis` package. It follows the Agent Workforce external-reference contract: <https://github.com/jannekbuengener/agent-workforce/blob/main/contracts/EXTERNAL_REFERENCE_CONTRACT.md>.

It is not repository truth. GitHub/repo live state, local `AGENTS.md`, `PROJECT_META.yaml`, package contracts, source, tests and CI remain authoritative.

## Priority and authority

- `P0` — active/core reference backed by current repo evidence.
- `P1` — active secondary reference backed by current repo evidence.
- `P2` — parked/reference-only; not evidence of an active dependency or capability.

External source authority is independent from priority: `OFFICIAL_SPEC` > `OFFICIAL_DOCS` > `UPSTREAM_PROJECT_DOCS` > `UPSTREAM_ISSUES_RELEASES` > `ESTABLISHED_TECHNICAL_KNOWLEDGE` > `COMMUNITY` > `EXAMPLE_DISCOVERY`.

## Active references

| Category | Name | Priority | Source type | Authority | Purpose | Repo signal | When to use | Canonical URL / identity |
|---|---|---|---|---|---|---|---|---|
| Runtime | Python | `P0` | `official_docs` | `OFFICIAL_DOCS` | Language/runtime and stdlib semantics. | `pyproject.toml` requires Python `>=3.12`; `PROJECT_META.yaml` quality gates run Python modules directly. | Runtime, stdlib, typing or compatibility work. | https://docs.python.org/3/ |
| Packaging | Setuptools | `P0` | `official_docs` | `OFFICIAL_DOCS` | Build backend and src-layout packaging behavior. | `pyproject.toml` uses `setuptools.build_meta` and package discovery from `src`. | Build, editable install or package layout changes. | https://setuptools.pypa.io/en/latest/ |
| Audio analysis | librosa | `P0` | `official_docs` | `OFFICIAL_DOCS` | Analysis API and DSP behavior used by package compute. | `pyproject.toml` direct dependency `librosa==1.0.0`. | Analysis implementation or librosa compatibility work. | https://librosa.org/doc/latest/ |
| Numeric | NumPy | `P0` | `official_docs` | `OFFICIAL_DOCS` | Array/numerical semantics used by analysis code. | `pyproject.toml` direct dependency `numpy>=2.5,<3`. | Array, dtype, vector or numerical behavior. | https://numpy.org/doc/stable/ |
| Audio I/O | SoundFile | `P0` | `upstream_project_docs` | `UPSTREAM_PROJECT_DOCS` | Audio file I/O behavior. | `pyproject.toml` direct dependency `soundfile>=0.14,<0.15`. | Audio decode/read/write or format behavior. | https://python-soundfile.readthedocs.io/ |
| Testing | pytest | `P0` | `official_docs` | `OFFICIAL_DOCS` | Test collection, fixtures and assertions for contract/compute regression. | `pyproject.toml` dev dependency and `[tool.pytest.ini_options]`; `PROJECT_META.yaml` gate `python -m pytest -q`. | Test behavior, fixtures, markers or collection. | https://docs.pytest.org/en/stable/ |
| Static analysis | Ruff | `P1` | `official_docs` | `OFFICIAL_DOCS` | Current lint/static-correctness gate. | `pyproject.toml` dev dependency/config; `PROJECT_META.yaml` gate `python -m ruff check .`. | Ruff configuration or lint-gate work. | https://docs.astral.sh/ruff/ |
| Docs/contracts | PyYAML | `P1` | `upstream_project_docs` | `UPSTREAM_PROJECT_DOCS` | YAML parsing used by development/knowledge tooling. | `pyproject.toml` dev dependency `PyYAML>=6,<7`; docs and project metadata use YAML frontmatter/metadata. | YAML/frontmatter/knowledge-tooling changes. | https://pyyaml.org/wiki/PyYAMLDocumentation |
| Packaging | Wheel | `P1` | `official_docs` | `OFFICIAL_DOCS` | Wheel build/distribution format used by release-to-consumer flow. | `pyproject.toml` build/dev dependency `wheel`; Sample Brain consumes a pinned wheel release. | Wheel build/release/consumer packaging work. | https://packaging.python.org/en/latest/specifications/binary-distribution-format/ |
| Repository CI | GitHub Actions | `P1` | `official_docs` | `OFFICIAL_DOCS` | CI workflow/check semantics. | `.github/workflows/` and repo quality-gate policy; releases are integrated with GitHub. | Workflow/check/release automation changes. | https://docs.github.com/en/actions |

## Parked references

No future technology is listed only because it may be interesting. Add `P2` only when a concrete local issue/canon path gives it a real future purpose.

## Maintenance rules

- Every `P0`/`P1` row must retain a current repo signal.
- Package imports remain free of database/UI/network/environment side effects unless local canon explicitly changes that boundary.
- External references cannot expand package ownership, establish analysis quality, or authorize a consumer release.
- Community/example material may aid discovery but never overrides current official/upstream or repo evidence.
- Do not commit host-specific paths, private audio, credentials, private endpoints or transient installation state.