---
doc_id: analysis-canon-router
doc_type: reference
lifecycle: active
authority: canonical
scope: documentation-canon
---

# Canon and Knowledge Standard v1

This repository uses document metadata to identify authority and lifecycle.
Each Markdown file under `docs/` has YAML frontmatter containing `doc_id`,
`doc_type`, `lifecycle`, `authority`, and `scope`.

Allowed values are defined by `tools/check_knowledge_graph.py`. `doc_id` values
are unique. Markdown links remain repository-relative. Active canonical docs
must be reachable from [the docs router](../README.md). `depends_on` references
must resolve and be acyclic. `supersedes` and `superseded_by` must agree with
the lifecycle of both documents. Generated documents identify a valid
`generated_from` repository path. Project canonical paths and gate commands are
recorded in [PROJECT_META.yaml](../../PROJECT_META.yaml).

The checker is deterministic and offline. It does not fetch, rewrite, infer,
summarize, or generate documents. One fact has one canonical owner; other docs
link to that owner.
