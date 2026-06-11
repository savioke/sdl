# 02 — Threat Model

## Components and data flows

No new components. Modifies how existing CI steps resolve third-party action code: from mutable tags (`@v4`, `@v5`) to immutable commit SHAs. Adds `.github/dependabot.yml`, which controls bump PRs but executes nothing in CI.

## Threats <!-- SR-2 -->

No new presently-reachable threats. This change removes a threat rather than adding one (see inherited, below).

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B6** — a compromised mutable action tag running in CI. This cycle mitigates it: SHAs are immutable, so a moved tag can no longer redirect our workflows; Dependabot keeps the SHAs current.

## Out-of-scope threats

- `savioke/sdl@v1` self-reference remains a moving tag by design (**baseline:B5**); Dependabot is configured to ignore it.
- Consumer repos pinning their own actions — their responsibility, not enforced here.
- Dependabot bump PRs editing workflow files will trip the SDL gate (workflow YAML is code). Intended: each supply-chain bump gets a quick review cycle. Grouped weekly to keep volume low.

## Noted for future cycles

- If a new third-party action is added, pin it by SHA in the same PR (**baseline:B6** stays closed only if all `uses:` remain pinned).
