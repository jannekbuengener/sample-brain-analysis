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
