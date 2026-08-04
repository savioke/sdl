# 01 — Requirements

## Summary

Dependabot's grouped actions PR bumps the two SHA-pinned GitHub Actions in this repo's workflows: `actions/setup-python` v6.3.0 → **v7.0.0** (major) and `actions/checkout` v7.0.0 → v7.0.1 (patch). The major bump is what pulls this out of the routine dependency-update tier (`docs/dependency-updates.md`) and into a full cycle. This is the maintenance loop `2026-06-10-pin-actions-sha` set up to keep `baseline:B6` mitigated; the cycle is written against the finished diff, as with `2026-07-09-actions-3e1200532a`.

## Scope

In scope: the version/SHA bumps in `.github/workflows/sdl-validate.yml` and `.github/workflows/self-check.yml`, and reviewing the upstream changes they pull in — notably the setup-python v7 major. Out of scope: consumer repos' own action pins; the `savioke/sdl@v1` self-reference (`baseline:B5`).

## Assets touched <!-- SR-1 -->

This repo's CI configuration. `sdl-validate.yml` runs in every consumer's CI, so the setup-python major executes there too, not only here. Standing integrity assets per `baseline.md`.

## Trust boundaries crossed <!-- SR-2 -->

None new. Refreshes the third-party-action-code-in-CI boundary tightened by `2026-06-10-pin-actions-sha`: new upstream code enters CI under new pins.

## Data classification <!-- SR-1 -->

None. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None.

## Security requirements <!-- SR-3, SR-4 -->

- New SHAs must match the upstream release tags they claim (comment matches pin).
- The setup-python v6 → v7 major must be reviewed against what we and our consumers actually depend on: no removed input may be one we set, and no runtime requirement may change in a way that breaks a consumer's runner.
- Pins stay within the Dependabot-maintained loop; no mutable tags reintroduced.

## Related prior cycles

- `2026-06-10-pin-actions-sha` — established the SHA pins and the Dependabot loop this PR exercises.
- `2026-07-09-actions-3e1200532a` — the previous run of this loop; same shape, checkout v6 → v7 was the major that time.
- `2026-07-09-dep-update-tier` — defined the routine/escalation split that routes this PR to a full cycle.

## Carried-forward residual risks

None. The prior cycles recorded no deferred items; both noted `baseline:B6` reopens if pins rot — this PR is that maintenance happening.
