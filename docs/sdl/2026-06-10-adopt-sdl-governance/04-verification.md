# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-06-10
- **Diff range:** origin/main..HEAD

## Checks performed <!-- SVV-1, SVV-2 -->

### Build, CI, and supply chain

- **Finding:** New workflow `.github/workflows/sdl.yml` calls `savioke/sdl/.github/workflows/sdl-validate.yml@v1`. Uses the default `GITHUB_TOKEN` with no `permissions:` elevation; performs read-only validation; references no secrets; adds no third-party action directly (the reusable workflow pins `actions/checkout@v4` and `actions/setup-python@v5`). The reusable workflow is org-owned; `@v1` is a moving tag (**baseline:B5**, **baseline:B6**).
- **References:** `.github/workflows/sdl.yml:1`

**Not applicable (no code in these areas):** input handling, persistence, network/transport, authentication/authorization, cryptography, secrets, logging, concurrency, dependencies, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

`self-check.yml` runs the validator unit tests (`lib/test_validate.py`), `shellcheck` on `scripts/*.sh`, and structure checks. The validator is standard-library only, so there is no dependency SBOM surface. No additional SAST configured.

## Residual risks <!-- DM-1 -->

No new residual risks introduced by this cycle. The new workflow inherits **baseline:B1** and **baseline:B5** (supply-chain exposure via the org-owned reusable workflow pinned at a moving tag), already dispositioned in the baseline.

| ID | Description | Severity | Disposition | Carry-forward target |
|----|-------------|----------|-------------|----------------------|
| —  | None new; see baseline:B1, baseline:B5 |  | accept |  |

## Sign-off

- [ ] Threat model mitigations verified or residual risk recorded
- [ ] Secure coding checks for applicable categories complete
- [ ] Static analysis and dependency scan reviewed
- [ ] Residual risks documented and dispositioned
