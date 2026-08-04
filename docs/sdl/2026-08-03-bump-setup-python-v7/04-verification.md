# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-03
- **Diff range:** main...HEAD (961d53d)

## Checks performed <!-- SVV-1, SVV-2 -->

### Build, CI, and supply chain

- **Finding:** `check_pins.py --exempt savioke/sdl` reports `8/8 pin(s) verified against upstream tags`. Spot-confirmed independently: `gh api repos/actions/checkout/commits/v7.0.1` → `3d3c42e5aac5ba805825da76410c181273ba90b1` and `gh api repos/actions/setup-python/commits/v7.0.0` → `5fda3b95a4ea91299a34e894583c3862153e4b97`, both matching the pins and their version comments. Diff touches only `uses:` lines; no mutable tag reintroduced.
- **References:** `.github/workflows/sdl-validate.yml:21`, `.github/workflows/sdl-validate.yml:26`, `.github/workflows/sdl-validate.yml:33`, `.github/workflows/self-check.yml:11`, `.github/workflows/self-check.yml:14`, `.github/workflows/self-check.yml:30`, `.github/workflows/self-check.yml:39`, `.github/workflows/self-check.yml:48`

### Behavior change in setup-python v7 (major bump) — T2

- **Finding:** The sole breaking change is removal of the `pip-install` input. `grep -rn "pip-install"` across the repo returns no match outside this cycle's own documents, and both `setup-python` steps pass `python-version: '3.x'` and nothing else, so no input we set was removed. Consumers cannot be affected through us: `sdl-validate.yml` is `workflow_call` with inputs `base` and `sdl_ref` only, so no caller can reach the `setup-python` step's configuration. `runs.using` is `node24` in both v6.3.0 and v7.0.0 (read from `action.yml` at each pinned SHA), so the major does not raise the runner requirement for this repo or any consumer — the one v7 change that could plausibly have broken a self-hosted consumer runner.
- **References:** `.github/workflows/sdl-validate.yml:2-13`, `.github/workflows/sdl-validate.yml:33-35`, `.github/workflows/self-check.yml:14-16`

**Not applicable (no code in these areas):** input handling, persistence, network/transport, authentication/authorization, cryptography, secrets, logging, concurrency, runtime dependencies, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

`self-check.yml` (validator unit tests, `check_pins.py`, shellcheck, structure checks) runs on this PR under the new pins — passing CI doubles as a smoke test of both bumped actions, and specifically of the `setup-python` v7 provisioning path the validator depends on. No further SAST applicable to a workflow-pin diff.

## Residual risks <!-- DM-1 -->

None new. `baseline:B6` remains mitigated; this PR is the pin-maintenance its disposition depends on. `baseline:B5` still governs the blast radius of the `v1` tag moving this change to all consumers at once.

| ID | Description | Severity | Disposition | Carry-forward target |
|----|-------------|----------|-------------|----------------------|
| —  | None new | | accept | |
