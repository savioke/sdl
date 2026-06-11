# 01 — Requirements

## Summary

Adopt SDL governance for the `savioke/sdl` repo itself (dogfooding). Add a self-referential CI gate, author the repo baseline, and record this first cycle. The repo is a supply-chain dependency for every consumer's CI, so it should be held to the process it enforces elsewhere.

## Scope

In scope: the self-gate workflow (`.github/workflows/sdl.yml`), `docs/sdl/baseline.md`, this cycle, and the `admin-setup.md` update reflecting that the repo now self-gates. Out of scope: the validator gate-widening (PR #3) and the `pull_request` branch-detection fix (PR #4), both merged before participation began; no change to consumer-facing behavior.

## Assets touched <!-- SR-1 -->

This repo's own CI configuration. Standing integrity assets (validator, reusable workflow, skills, scripts) per `baseline.md`.

## Trust boundaries crossed <!-- SR-2 -->

Adds one new CI workflow that runs in this repo's CI with the default `GITHUB_TOKEN`. Exposure model otherwise per `baseline.md`.

## Data classification <!-- SR-1 -->

None new. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None. The new workflow consumes only the repo checkout and the org-owned reusable workflow.

## Security requirements <!-- SR-3, SR-4 -->

- The self-gate must not weaken the existing `self-check.yml` CI.
- Least privilege: default `GITHUB_TOKEN`, no `permissions:` elevation, read-only validation, no secrets.
- Pin the reusable workflow to the org-owned `@v1`.

## Related prior cycles

None. First cycle in this repo.

## Carried-forward residual risks

None.
