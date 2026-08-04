# 02 — Threat Model

## Components and data flows

- `.github/workflows/sdl-validate.yml` — reusable workflow run in consumer CI; two `checkout` steps and one `setup-python` step re-pinned.
- `.github/workflows/self-check.yml` — this repo's own CI; four `checkout` steps and one `setup-python` step re-pinned.
- No code of ours changes; the delta is which upstream action code executes in CI.

## Threats <!-- SR-2 -->

### T1 — Malicious or compromised upstream release enters CI

- **Category:** Tampering
- **Component / flow:** New `actions/setup-python` v7.0.0 and `actions/checkout` v7.0.1 code executing in this repo's and every consumer's CI.
- **Description:** A version bump is the one moment SHA pinning lets new third-party code in. A compromised upstream release, or a Dependabot PR whose SHA doesn't match the claimed tag, would run with each caller's `GITHUB_TOKEN`.
- **Likelihood / Impact:** low / high
- **Mitigation:** Both SHAs verified against upstream release tags by `check_pins.py`, in CI and locally; release notes reviewed; actions are GitHub-official (`actions/*`), the lowest-risk publisher tier.
- **Mitigation type:** preventive
- **Defense in depth notes:** Pins remain immutable SHAs after merge; Dependabot PRs still pass PR review and the SDL gate rather than auto-merging.

### T2 — A removed input silently changes CI behavior

- **Category:** Tampering
- **Component / flow:** `setup-python` v7 removes the `pip-install` input. GitHub Actions ignores unknown `with:` keys rather than failing, so a caller that still set it would silently lose the behavior instead of getting an error.
- **Description:** For the step that provisions the interpreter the validator runs under, a silent behavior change is worse than a hard failure: the gate could keep reporting success while running under different assumptions than the ones it was verified against.
- **Likelihood / Impact:** low / medium
- **Mitigation:** Verified that `pip-install` appears nowhere in this repo and that both `setup-python` sites set only `python-version: '3.x'`. Consumers do not configure this step — they call `sdl-validate.yml` via `workflow_call`, whose inputs are `base` and `sdl_ref` only — so the removal cannot reach them through us either.
- **Mitigation type:** preventive
- **Defense in depth notes:** `self-check.yml` exercises the new pin on this PR itself; a provisioning regression surfaces as failing validator unit tests rather than a silent pass.

## Threats inherited from prior cycles <!-- SR-2 -->

`2026-06-10-pin-actions-sha` and `2026-07-09-actions-3e1200532a` apply unchanged: this PR is the pin-refresh path they anticipated. `baseline:B6` stays mitigated only while this loop runs. `baseline:B5` (moving `v1`) means the bump reaches every consumer the moment `v1` moves, with no per-consumer opt-in — the standing accepted risk, not new here.

## Out-of-scope threats

- setup-python's ESM migration and its `@actions/cache` bump are internal to the action; we set no cache input, so that code path is not exercised by either workflow.
- checkout v7.0.1's `--unset` value-escaping fix and its narrowed unsafe-PR check are upstream hardening we inherit; no action needed.

## Noted for future cycles

- Both v6.3.0 and v7.0.0 declare `runs.using: node24`, so this major does **not** raise the runner requirement. A future major that does would break self-hosted runners on older runner versions — here and in every consumer at once. Check `runs.using` on the next major bump.
- `sdl-validate.yml` becomes a shipped path under the release process in `2026-08-03-release-process`; once that lands, a Dependabot PR touching it will also need a plugin version bump and a changelog entry before it can merge.
