# 02 — Threat Model

## Components and data flows

- `.github/workflows/sdl-validate.yml` — reusable workflow run in consumer CI; two `checkout` steps and one `setup-python` step re-pinned.
- `.github/workflows/self-check.yml` — this repo's own CI; three `checkout` steps and one `setup-python` step re-pinned.
- No code of ours changes; the delta is which upstream action code executes in CI.

## Threats <!-- SR-2 -->

### T1 — Malicious or compromised upstream release enters CI

- **Category:** Tampering
- **Component / flow:** New `actions/checkout` v7.0.0 and `actions/setup-python` v6.3.0 code executing in this repo's and every consumer's CI.
- **Description:** A version bump is the one moment SHA pinning lets new third-party code in. A compromised upstream release, or a Dependabot PR whose SHA doesn't match the claimed tag, would run with each caller's `GITHUB_TOKEN`.
- **Likelihood / Impact:** low / high
- **Mitigation:** Both SHAs verified against upstream release tags (`gh api repos/<action>/commits/<tag>`); release notes reviewed; actions are GitHub-official (`actions/*`), the lowest-risk publisher tier.
- **Mitigation type:** preventive
- **Defense in depth notes:** Pins remain immutable SHAs after merge; Dependabot PRs still pass PR review and the SDL gate rather than auto-merging.

## Threats inherited from prior cycles <!-- SR-2 -->

`2026-06-10-pin-actions-sha` T-model applies unchanged: this PR is the pin-refresh path it anticipated. `baseline:B6` stays mitigated only while this loop runs.

## Out-of-scope threats

- checkout v7's fork-PR blocking under `pull_request_target`/`workflow_run` is an upstream hardening, not a threat here — verified non-breaking in 04 since our workflows use `workflow_call`/`pull_request`/`push` and never check out a fork PR head ref (`baseline:B4` model unaffected).

## Noted for future cycles

- If a consumer ever calls `sdl-validate.yml` from `pull_request_target`, checkout v7's new blocking may surface there; the failure mode is fail-closed (checkout refuses), not a bypass.
