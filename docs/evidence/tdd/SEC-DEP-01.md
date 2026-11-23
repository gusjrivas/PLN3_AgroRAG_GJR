# SEC-DEP-01 — refreshed security dependencies

Audit start: 2026-11-22; final image scan: 2026-11-23 (America/Argentina/Buenos_Aires)
Base commit: `b9ad1b5ba047c116bc3dff2fbdefc5dd387f6483`
Implementation commit: `8fb6b0720c4d881cbfef3a0b5587f0d5d42e016c`.
Branch: `fix/main-audit-2026-11-23`

## RED

Before the fixes, the new architecture contracts failed on the old Garak version, vulnerable
`fsspec` pin and retained exception; the CI contract failed because tracing coverage was not
appended and the tracing environment was not audited.

## GREEN

- `uv sync --locked --extra tracing` installed `opentelemetry-sdk` and `opentelemetry-api` 1.45.2.
- `uv run python -m pip_audit --skip-editable` — no known vulnerabilities; only the editable
  project distribution was skipped.
- Focused contracts and tracing: `uv run pytest tests/unit/test_garak_runner.py tests/architecture/test_garak_container_contract.py tests/architecture/test_quality_ci_contract.py tests/contract/test_academic_tracing.py -q` — 15 passed, 1 skipped.
- Full suite: `uv run pytest -q` — 353 passed, 1 skipped, 3 deselected; one existing Starlette/httpx
  deprecation warning.
- Static checks: Ruff, format check, mypy (40 source files), and import-linter (2 contracts kept)
  passed.
- `npx --yes @fission-ai/openspec@1.14.3 validate --all --strict` — 11 passed, 0 failed.
- GitHub Actions for PR #61 at source commit `9a8d56c`: `offline`, `specs`, `browser`, and `container-supply-chain` all passed. The image publish steps were skipped for the pull request event.
- Garak lock resolved to 197 exact pins, including Garak 0.17.1, datasets 5.2.0, transformers
  5.19.0 and fsspec 2026.9.0.
- Local image `agrorag-garak:security-audit`: runtime UID 10003; `garak --version` reported 0.17.1.
- Trivy 0.76.1 scan with vulnerability and secret scanners: 0 CRITICAL/HIGH vulnerabilities and
  0 secrets. The final image was rebuilt with OCI revision label `8fb6b0720c4d881cbfef3a0b5587f0d5d42e016c` (image ID `sha256:d36b82c803c8d509d7a9c1d6372770559633d422b1ff22fbf07f430a87fca1d2`). A second Trivy 0.76.1 scan on 2026-11-23 also found 0 CRITICAL/HIGH vulnerabilities and 0 secrets. The final supply-chain policy check for 2026-11-23 returned `{"accepted_high": [],
  "blocked": [], "status": "approved"}`. The expired runner exception was removed after this
  scan; the six gateway exceptions were absent from main's latest image reports and were removed.

## Scope and limitations

Garak was not executed. The local image was not published to GHCR. Remote PR checks are pending.
The final local build and Trivy scan used the implementation commit and matching OCI revision label.