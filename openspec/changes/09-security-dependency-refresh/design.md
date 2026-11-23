# Design: security dependency refresh

## Decisions

- Use the upstream Garak 0.17.1 dependency metadata. It requires datasets 5.0.1 or newer and
  Transformers below 5.20, allowing a complete lock with fsspec 2026.9.0 while retaining existing
  compatible pins where possible.
- Keep the runner exception until a fresh image scan confirms the patched dependency in the built
  artifact. Remove the six gateway exceptions because the latest scan for main reports none of
  those findings.
- Audit the installed CI environment after installing the optional tracing extra. This checks
  exactly the code exercised by tracing tests and avoids claiming that absent optional packages
  were evaluated.
- Append tracing contract coverage before reporting total and domain/application coverage.
- Keep all tests offline; use fakes for Pinecone and model providers.

## Risks and rollback

Garak 0.17.1 changes its `datasets` and Transformers dependency ranges. The runner is isolated from
the product API/UI, and the image must build, report the expected version, pass its offline adapter
contracts, and scan without the fsspec exception before integration. If compatibility or the scan
fails, retain the current runner lock and record the blocker; do not renew the exception silently.

The tracing change only upgrades the optional SDK and adds a CI audit. If the tracing extra fails
to install or audit, do not merge. The default runtime and retrieval path remain unchanged.
