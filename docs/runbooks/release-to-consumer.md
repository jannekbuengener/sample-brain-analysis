---
doc_id: release-to-consumer
doc_type: runbook
lifecycle: active
authority: operational
scope: release-consumer-delivery
---

# Analysis release to consumer

Use this runbook when a merged Analysis change must be consumed by Sample
Brain. The Analysis package owns its behavior and API contracts. Sample Brain
owns consumer integration, consumer regression, and its repository governance.

## Procedure

1. Confirm that the Analysis change is merged and decide the package version
   using the package's release policy. Do not create a release merely because
   a consumer wants a local checkout.
2. If the selected version differs from the package version currently declared
   in `pyproject.toml`, prepare that version as its own minimal repository
   change, run the Analysis gates, and merge it before tagging. Verify that the
   commit to be tagged declares the exact selected package version. The release
   workflow requires tag `v<version>` to match the installed package metadata.
3. Create the matching `v<version>` tag from the merged Analysis commit and let
   the release workflow publish the versioned wheel. Use the released artifact,
   never a sibling checkout, editable install, `PYTHONPATH` source copy, or
   locally rebuilt substitute.
4. Open the live GitHub release and download the exact wheel. Record its
   filename, version, URL, and SHA-256 digest from the live artifact before
   changing the consumer.
5. In Sample Brain, pin that exact artifact URL, version, and SHA-256. Keep
   the consumer change in Sample Brain; do not move consumer orchestration into
   this package.
6. Run the consumer regression and boundary validation against the installed
   released wheel. A passing Analysis package suite alone is not consumer
   validation.
7. Open the Sample Brain PR with its actual diff, checks, review feedback, and
   remaining uncertainty. Follow Sample Brain's required CI and review gates.
8. Merge only after those gates pass. Verify the merged Sample Brain head and
   the consumer's live dependency pin, then record the merge SHA and release
   identity in the delivery record.

## Ownership and evidence

- Analysis behavior, public API truth, and package contracts remain owned by
  this repository.
- Consumer integration, product behavior, and governance remain owned by
  Sample Brain.
- Artifact identity is established from the live versioned release and its
  SHA-256 digest. Local package tests do not establish release or consumer
  readiness.
- Do not add provider-specific credentials, connector instructions, local
  usernames, or machine-specific paths to this runbook.
