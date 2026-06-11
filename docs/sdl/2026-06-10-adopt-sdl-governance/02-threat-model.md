# 02 — Threat Model

## Components and data flows

One new component: `.github/workflows/sdl.yml`. On `pull_request` and `push` it calls `savioke/sdl/.github/workflows/sdl-validate.yml@v1`, which checks out the repo and runs the validator read-only. No secrets, default token, no write operations.

## Threats <!-- SR-2 -->

No new presently-reachable threats. Adding a read-only validation workflow that uses the default token and an org-owned reusable workflow introduces no new live attack surface. The standing supply-chain exposure it inherits is tracked in the baseline, below.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B1** — the new workflow executes the validator in CI; integrity of `validate.py` / `sdl-validate.yml` governs what runs. Mitigated by org ownership and PR review.
- **baseline:B5** — the workflow pins the reusable workflow at the moving `@v1` tag, so a bad release reaches this repo's CI immediately. Accepted; single consumer.

## Out-of-scope threats

- `GITHUB_TOKEN` privilege escalation — the workflow sets no `permissions:` block and performs read-only validation; no elevation. Owner: this cycle's verification.
- Secret exposure via the reusable workflow — none exposed (**baseline:B4**).
- Workstation scripts — unaffected by this change (**baseline:B3**).

## Noted for future cycles

- If `sdl.yml` ever gains write permissions or secrets, re-threat-model it.
- Consider pinning the reusable workflow to an immutable tag or SHA (**baseline:B5**, **baseline:B6**).
