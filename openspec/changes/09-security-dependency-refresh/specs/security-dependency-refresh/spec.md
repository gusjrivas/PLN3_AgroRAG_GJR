# Security dependency refresh

## ADDED Requirements

### Requirement: SEC-DEP-01 Optional tracing dependencies are patched and audited

The optional tracing environment MUST use a patched OpenTelemetry API and CI MUST audit the
installed environment whenever the tracing contract is verified.

#### Scenario: SEC-DEP-01-tracing-audit

- **GIVEN** CI has installed the locked `tracing` extra.
- **WHEN** it runs the tracing contract tests.
- **THEN** it audits the same installed environment and fails on a known vulnerable dependency.

### Requirement: SEC-DEP-02 Runner dependency exceptions track scanned images

The Garak runner MUST use an upstream compatible dependency set with patched fsspec, and an
exception for a runner image finding MUST be removed only after a scan of the rebuilt image no
longer reports that finding.

#### Scenario: SEC-DEP-02-runner-remediation

- **GIVEN** the previous runner image reported CVE-2026-104851 through fsspec.
- **WHEN** the runner is rebuilt with its updated, fully pinned dependency lock and scanned.
- **THEN** the scan reports no CVE-2026-104851, the current-date policy passes, and no Garak
  evaluation is executed.

### Requirement: SEC-DEP-03 Tracing coverage is included in CI reports

The tracing contract suite MUST append its coverage to the offline suite before CI publishes the
combined report and applies the existing coverage thresholds.

#### Scenario: SEC-DEP-03-tracing-coverage

- **GIVEN** the optional tracing SDK is installed.
- **WHEN** CI runs the tracing contract suite after the offline suite.
- **THEN** the combined coverage report includes `infrastructure/tracing.py` without excluding
  source files or relaxing thresholds.
