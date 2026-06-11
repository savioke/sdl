# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-06-10
- **Diff range:** origin/main..HEAD

## Checks performed <!-- SVV-1, SVV-2 -->

### Build, CI, and supply chain

- **Finding:** All third-party `uses:` are now pinned to immutable commit SHAs with version comments — `actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3` and `actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0`. SHAs confirmed against the upstream release tags via `gh api repos/<action>/commits/<tag>`. No mutable third-party tag remains. `.github/dependabot.yml` parses and is scoped to `github-actions`, grouped, ignoring `savioke/sdl`. This mitigates `baseline:B6`.
- **References:** `.github/workflows/sdl-validate.yml:21`, `.github/workflows/sdl-validate.yml:26`, `.github/workflows/sdl-validate.yml:33`, `.github/workflows/self-check.yml:11`, `.github/workflows/self-check.yml:14`, `.github/workflows/self-check.yml:27`, `.github/workflows/self-check.yml:36`, `.github/dependabot.yml:1`

**Not applicable (no code in these areas):** input handling, persistence, network/transport, authentication/authorization, cryptography, secrets, logging, concurrency, dependencies (runtime), frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

`self-check.yml` (now itself SHA-pinned) runs the validator unit tests, `shellcheck`, and structure checks. The SHA pins are verifiable against upstream tags. No additional SAST.

## Residual risks <!-- DM-1 -->

No new residual risks. `baseline:B6` moves from `mitigate-later` to mitigated. The pins must be kept current (Dependabot) and any newly-added action must also be pinned, or B6 reopens.

| ID | Description | Severity | Disposition | Carry-forward target |
|----|-------------|----------|-------------|----------------------|
| —  | None new; closes baseline:B6 |  | accept |  |

## Sign-off

- [ ] Threat model mitigations verified or residual risk recorded
- [ ] Secure coding checks for applicable categories complete
- [ ] Static analysis and dependency scan reviewed
- [ ] Residual risks documented and dispositioned
