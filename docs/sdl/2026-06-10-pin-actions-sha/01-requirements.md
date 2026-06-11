# 01 — Requirements

## Summary

Pin the third-party GitHub Actions used in this repo's workflows to immutable commit SHAs, and add Dependabot to keep them current. Mitigates `baseline:B6` (a compromised mutable action tag would otherwise run in CI).

## Scope

In scope: pinning `actions/checkout` and `actions/setup-python` by SHA in `.github/workflows/sdl-validate.yml` and `.github/workflows/self-check.yml`; a `.github/dependabot.yml` for grouped weekly action updates. Out of scope: consumer repos' own action pinning (their concern); the `savioke/sdl@v1` self-reference, intentionally left as a moving tag (`baseline:B5`).

## Assets touched <!-- SR-1 -->

This repo's CI configuration. Standing integrity assets per `baseline.md`.

## Trust boundaries crossed <!-- SR-2 -->

None new. Tightens an existing one: third-party action code executing in this repo's CI.

## Data classification <!-- SR-1 -->

None. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None.

## Security requirements <!-- SR-3, SR-4 -->

- Every third-party `uses:` pinned to a full commit SHA with the version as a trailing comment.
- Pins bumped to the current major (`checkout` v6, `setup-python` v6) so future Dependabot updates stay within-major.
- Dependabot configured so pins do not rot; bumps grouped into one PR to minimize gated cycles.

## Related prior cycles

`2026-06-10-adopt-sdl-governance` — established the baseline that records B6.

## Carried-forward residual risks

None. This cycle closes the standing item `baseline:B6`.
