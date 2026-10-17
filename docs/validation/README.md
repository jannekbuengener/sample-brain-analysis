---
doc_id: analysis-validation
doc_type: validation
lifecycle: active
authority: canonical
scope: package-validation
---

# Validation and release gates

Run the four project gates from the repository root:

1. `python -m pytest -q` covers the public API, behavioral contracts, import
   closure, wheel installation, and Knowledge Standard checker.
2. `python -m ruff check .` checks Python source and tests.
3. `python tools/check_knowledge_graph.py` validates documentation metadata,
   links, relations, provenance, and reachability offline.
4. `git diff --check` checks patch whitespace.

The release workflow builds a wheel and attaches it to a versioned GitHub
release. No release or consumer installation is implied by a local test pass.
Consumer integration checks remain owned by Sample Brain.

### Windows local test path

On Windows, give each local pytest run a fresh repository-local temporary base
to avoid collisions with the shared system temp directory:

```powershell
$pytestBase = Join-Path (Get-Location) ('.pytest-local-' + [guid]::NewGuid())
python -m pytest -q --basetemp $pytestBase
```

Run this from the repository root. The generated `.pytest-local-*` directory is
ignored by Git and may be removed after the run. CI keeps the simple,
cross-platform `python -m pytest -q` command above.

### Release to consumer handshake

For the reusable cross-repository procedure, follow the
[release-to-consumer runbook](../runbooks/release-to-consumer.md). A local
Analysis test pass validates this package only; it does not validate a
consumer installation.
