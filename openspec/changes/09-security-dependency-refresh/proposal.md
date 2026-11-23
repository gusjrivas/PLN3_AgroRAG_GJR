# Refresh vulnerable optional and runner dependencies

## Why

The optional tracing lock contains `opentelemetry-api 1.45.1`, which is affected by
CVE-2026-126360. The Garak runner image contains `fsspec 2025.3.0`, affected by
CVE-2026-104851, and its exception expired. Garak 0.17.0 constrains datasets so the patched
fsspec cannot be selected without updating the upstream runner release and its dependency lock.

The current mainline image scans no longer report the expired gateway findings. Tracing contract
tests also run outside the main coverage report.

## Scope

- Upgrade the optional tracing SDK and continuously audit the installed tracing environment.
- Upgrade Garak to an upstream version whose dependency requirements allow patched fsspec; resolve
  and lock the complete runner dependency set.
- Rebuild and scan the runner image before removing its exception. Remove gateway exceptions absent
  from the scan artifact for the audited commit.
- Include tracing tests in CI coverage

No runtime query contract, Garak scan behavior, provider credentials, budget, or release policy is
changed. Do not execute Garak as part of this change.

## Out of scope

- Repeating or expanding the adversarial Garak evaluation.
- Publishing a new runner image to GHCR.
- Replacing `httpx` in application runtime or changing Starlette `TestClient` until compatibility
  is established separately.

## Validation

Run the focused architecture tests, lock installation, pip-audit with the tracing extra, full offline
suite, static checks, a local runner image build, and Trivy against that image. Confirm the supply
chain policy using the new scan report and today's date. Run OpenSpec strict validation and GitHub
CI on the proposed branch.
