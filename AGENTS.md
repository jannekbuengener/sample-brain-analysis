# Repository guidance

- Write durable analysis contracts here; keep Sample Brain product and storage
  ownership in the consumer repository.
- Preserve the public v1 names and owner modules in
  `docs/contracts/analysis-public-api-v1.md`.
- Keep package imports free of database, UI, filesystem discovery, environment
  reads, network access, and import-time directory creation.
- Do not add private audio or host-specific paths.
- Documentation under `docs/` needs valid YAML frontmatter and a link from
  `docs/README.md` when active and canonical.
- Run the commands in `PROJECT_META.yaml` before proposing a change. Report
  failures as observed; do not weaken frozen behavioral contracts to make a
  gate pass.
- Keep issue and PR scope narrow. The package does not establish analysis
  quality, production readiness, or a consumer release by itself.
