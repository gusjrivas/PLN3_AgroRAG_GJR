# Tasks: security dependency refresh

Responsable: coordinador. Rama: `fix/main-audit-2026-11-23`. Base:
`b9ad1b5ba047c116bc3dff2fbdefc5dd387f6483`.

## SEC-DEP-01 — Optional tracing dependency

- [x] 1.1 Confirm RED: `pip-audit` identifies CVE-2026-126360 in `opentelemetry-api 1.45.1`.
- [x] 1.2 Add RED architecture contract for CI audit and tracing coverage.
- [x] 1.3 Upgrade `opentelemetry-sdk` and regenerate `uv.lock` with the pinned uv release.
- [x] 1.4 Audit tracing environment and run tracing contract suite.

## SEC-DEP-02 — Garak runner image

- [x] 2.1 Confirm RED architecture contract for fsspec minimum and exception removal.
- [x] 2.2 Resolve Garak 0.17.1 dependency set with fsspec >= 2026.6.0 and preserve compatible pins.
- [x] 2.3 Build runner image locally; verify user, Garak version and startup contract.
- [x] 2.4 Scan the built image; remove the fsspec exception only after the current-date gate passes.
- [x] 2.5 Remove gateway exceptions absent from the latest scan for main.
- [x] 2.6 Update the current runbook while preserving historical scan evidence.

## SEC-DEP-03 — Coverage and infrastructure tests

- [x] 3.1 Confirm RED for the missing coverage append and identified infrastructure branches.
- [x] 3.2 Append tracing coverage in CI and move report/threshold steps after tracing tests.
- [ ] 3.4 Run full suite, lint, format, typing, import boundaries, OpenSpec validation and GitHub CI.

Do not execute Garak, call model providers, publish images, or merge this branch as part of the
change.
