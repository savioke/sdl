# 01 — Requirements

## Summary

Dependabot PR #11 bumps the two SHA-pinned GitHub Actions in this repo's workflows: `actions/checkout` v6.0.3 → v7.0.0 and `actions/setup-python` v6.2.0 → v6.3.0. This is the maintenance loop the `2026-06-10-pin-actions-sha` cycle set up to keep `baseline:B6` mitigated. Dependabot authored the change without SDL docs; this cycle was written retroactively against the diff.

## Scope

In scope: the version/SHA bumps in `.github/workflows/sdl-validate.yml` and `.github/workflows/self-check.yml`, and reviewing the upstream changes they pull in — notably the checkout v7 major. Out of scope: consumer repos' own action pins; the `savioke/sdl@v1` self-reference (`baseline:B5`).

## Assets touched <!-- SR-1 -->

This repo's CI configuration (`sdl-validate.yml` runs in every consumer's CI). Standing integrity assets per `baseline.md`.

## Trust boundaries crossed <!-- SR-2 -->

None new. Refreshes the third-party-action-code-in-CI boundary tightened by `2026-06-10-pin-actions-sha`: new upstream code enters CI under new pins.

## Data classification <!-- SR-1 -->

None. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None.

## Security requirements <!-- SR-3, SR-4 -->

- New SHAs must match the upstream release tags they claim (comment matches pin).
- Upstream release notes reviewed, especially for the checkout v6 → v7 major: no behavior change may break the reusable workflow for consumers or weaken the fork-PR validation model (`baseline:B4`).
- Pins stay within the Dependabot-maintained loop; no mutable tags reintroduced.

## Related prior cycles

`2026-06-10-pin-actions-sha` — established the SHA pins and the Dependabot loop this PR exercises.

## Carried-forward residual risks

None. `2026-06-10-pin-actions-sha` recorded no deferred items; it did note B6 reopens if pins rot — this PR is that maintenance happening.
