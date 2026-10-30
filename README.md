# Sample Brain Analysis

Independent Python distribution `sample-brain-analysis`, imported as
`sample_brain_analysis`. It owns the database-free Analysis API, contracts, and
deterministic computation extracted from Sample Brain. It does not own catalog
persistence, product orchestration, Workbench/QML/session state, AQ orchestration,
or real-time audio.

Public names and owner modules are listed in [the v1 contract](docs/contracts/analysis-public-api-v1.md);
module ownership and non-goals are in [the architecture](ARCHITECTURE.md).

Package metadata is currently `0.1.2` (pending release after merge of the
#1218 exact-tempo fix). The latest published GitHub release remains
[`v0.1.1`](https://github.com/jannekbuengener/sample-brain-analysis/releases/tag/v0.1.1)
until `v0.1.2` is tagged. No stable SemVer compatibility promise is made yet.
Releases are versioned GitHub artifacts; no package index publication is configured.

## Consumer relationship

[`jannekbuengener/sample-brain`](https://github.com/jannekbuengener/sample-brain) is
the product consumer. Consumer integration, persistence, Workbench/QML/session
state, AQ orchestration, and product governance remain owned there.

Compatibility is validated against the exact versioned release artifact. Do not
treat a sibling checkout, editable install, `PYTHONPATH` source copy, or unversioned
`main` as release evidence. Follow the [release-to-consumer runbook](docs/runbooks/release-to-consumer.md)
and the Sample Brain [consumer contract](https://github.com/jannekbuengener/sample-brain/blob/main/docs/ANALYSIS_PUBLIC_CONTRACT_V1.md).

## Documentation

- [Architecture and ownership boundary](ARCHITECTURE.md)
- [Documentation index](docs/README.md)
- [Public Analysis API v1](docs/contracts/analysis-public-api-v1.md)
- [Release to consumer runbook](docs/runbooks/release-to-consumer.md)
- [Contributing](CONTRIBUTING.md)

## Local development

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe tools/check_knowledge_graph.py
```

On Windows, use a fresh repository-local pytest temp base when the shared
system temp directory causes cleanup or permission failures:

```powershell
$pytestBase = Join-Path (Get-Location) ('.pytest-local-' + [guid]::NewGuid())
python -m pytest -q --basetemp $pytestBase
```

The library is offline-first after its declared dependencies are installed.
Tests use generated synthetic audio only. Do not add private samples, runtime
audio, credentials, machine-specific paths, or model downloads.
