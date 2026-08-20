# 01 — Requirements

## Summary

Two refs in this repo name a major by hand, and nothing cross-checks either against the version being released: `sdl-validate.yml`'s `sdl_ref` input default, which is the validator every consumer checks out, and `sdl.yml`'s `uses:` ref, which is the alias this repo pins its own gate at. `check_release.py` exists to detect exactly this class of drift and does not look at either. This cycle adds both assertions, closing `gate-direct-pushes:R3a` and the first half of `self-gate-v2:R2`.

## Scope

In scope: `scripts/check_release.py` and its tests, plus the "What CI checks" section of `docs/releasing.md`. Out of scope: deriving the checkout ref from `github.job_workflow_sha` (R3a's other option — it changes the reusable workflow, which is shipped content, and a detector is the smaller step); detecting *consumer* repos left on a retired alias, which `self-gate-v2:R2` already records as out of this repo's reach.

## Assets touched <!-- SR-1 -->

None shipped. `check_release.py` is release tooling: CI runs it on every PR and daily, and `release.sh` runs it as its final verification. It reads two workflow files and `plugin.json` from the repo it is pointed at; it writes nothing and holds no credential.

## Trust boundaries crossed <!-- SR-2 -->

None new. The two files read are already in the checkout the script runs against, and are already read by CI as executable content.

## Data classification <!-- SR-1 -->

None. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None. No new network call, argument, or environment variable; the marketplace fetch is untouched.

## Security requirements <!-- SR-3, SR-4 -->

- The check must fail closed. A workflow file that is missing, or that carries no ref where one is expected, is drift to report — not a condition to skip past.
- `sdl_ref` must be read from its own input block. A `default:` belonging to a neighbouring input must never be compared in its place.
- No condition that passes today may start failing. In particular the release procedure must still end green: `release.sh` verifies immediately after cutting the alias that this repo's own gate must move to, and on that commit the gate legitimately still names the previous major.

## Related prior cycles

- `2026-08-06-gate-direct-pushes` — recorded the near-miss (`sdl_ref` left at `v1` beside a v2 workflow) and named this check as one of two ways to close R3a.
- `2026-08-06-self-gate-v2` — moved this repo's own gate to `@v2` and recorded R2: two edits per major that nothing cross-checks.
- `2026-08-03-release-process` — introduced `check_release.py` and the two-channel release contract this extends.

## Carried-forward residual risks

- `2026-08-06-gate-direct-pushes:R3a` — closed by the `sdl_ref` assertion.
- `2026-08-06-self-gate-v2:R2` — the in-repo half is closed; the stale-consumer half is not, and is re-recorded in 04 rather than dropped.
