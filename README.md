# Sample Brain Analysis

Independent Python distribution `sample-brain-analysis`, imported as
`sample_brain_analysis`. It owns a small, database-free analysis API extracted
from Sample Brain. The library does not own catalog persistence, product
orchestration, UI, or real-time audio.

The source baseline for the initial extraction is Sample Brain `main` at
`bd302c70084e481a1189f0aeddb2392273357d75`. Public names and owner modules are
listed in [the v1 contract](docs/contracts/analysis-public-api-v1.md); module
ownership and non-goals are in [the architecture](ARCHITECTURE.md).

This is the initial `0.1.0` distribution. No stable SemVer compatibility
promise is made yet. Releases are versioned GitHub artifacts; no package index
publication is configured.

## Local development

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe tools/check_knowledge_graph.py
```

The library is offline-first after its declared dependencies are installed.
Tests use generated synthetic audio only. Do not add private samples, runtime
audio, credentials, machine-specific paths, or model downloads.
