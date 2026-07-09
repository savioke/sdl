# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-07-09
- **Diff range:** main..HEAD (62d26dc)

## Checks performed <!-- SVV-1, SVV-2 -->

### Build, CI, and supply chain

- **Finding:** Both new SHAs confirmed to match their upstream release tags via `gh api repos/actions/checkout/commits/v7.0.0` → `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` and `gh api repos/actions/setup-python/commits/v6.3.0` → `ece7cb06caefa5fff74198d8649806c4678c61a1`. Version comments match the pins. No mutable tag reintroduced; diff touches only `uses:` lines.
- **References:** `.github/workflows/sdl-validate.yml:21`, `.github/workflows/sdl-validate.yml:26`, `.github/workflows/sdl-validate.yml:33`, `.github/workflows/self-check.yml:11`, `.github/workflows/self-check.yml:14`, `.github/workflows/self-check.yml:27`, `.github/workflows/self-check.yml:36`

### Behavior change in checkout v7 (major bump)

- **Finding:** v7 blocks fork-PR checkout under `pull_request_target`/`workflow_run`. `self-check.yml` triggers on `pull_request`/`push` and `sdl-validate.yml` is `workflow_call`; neither checks out a fork PR head ref (project checkout uses the event default, second checkout targets `savioke/sdl` at `sdl_ref`). Non-breaking for this repo and current consumers; fail-closed if a consumer ever hits it.
- **References:** `.github/workflows/self-check.yml:2-5`, `.github/workflows/sdl-validate.yml:2-3`, `.github/workflows/sdl-validate.yml:20-28`

**Not applicable (no code in these areas):** input handling, persistence, network/transport, authentication/authorization, cryptography, secrets, logging, concurrency, runtime dependencies, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

`self-check.yml` (validator unit tests, shellcheck, structure checks) runs on this PR under the new pins — passing CI doubles as a smoke test of both bumped actions. No further SAST applicable to a workflow-pin diff.

## Residual risks <!-- DM-1 -->

None new. `baseline:B6` remains mitigated; this PR is the pin-maintenance its disposition depends on.

| ID | Description | Severity | Disposition | Carry-forward target |
|----|-------------|----------|-------------|----------------------|
| —  | None new | | accept | |
