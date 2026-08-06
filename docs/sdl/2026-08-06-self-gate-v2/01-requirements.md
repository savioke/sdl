# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Point this repo's own gate at `@v2`, the release that was just cut. Until now
`.github/workflows/sdl.yml` called `sdl-validate.yml@v1` — not by preference but
because `@v2` did not exist while the PR that created it was in flight, and a
workflow cannot call a tag that has yet to be written. The consequence is
measurable rather than theoretical: the `push` run on `main` for the 2.0.0 merge
(run 31082092951) reported `[ok ] no substantive code changes; cycle presence
not required` against `--base origin/main`, which is the exact vacuous pass that
2.0.0 exists to eliminate. This repo is the first consumer of its own gate, so
until it moves, the gate is untested by the one repo best placed to notice a
defect in it.

## Scope

In scope: the `uses:` ref in `.github/workflows/sdl.yml`, and the `@v1`
references in `docs/sdl/baseline.md` that describe the present rather than the
past — the distribution channel, the "this repo → consumer CI" crossing point,
the self-gate standing requirement, and the wording of B4/B5/B6.

Out of scope: `@v1` in merged cycle folders and in pre-2.0.0 changelog entries.
Those are records of what was true when written; editing an audit trail to match
the present makes it a worse record, not a better one. Also out of scope: cutting
any release (2.0.0 is already tagged at `059cf28`), and the other savioke repos
still on `@v1`, which the maintainer re-points separately.

## Assets touched <!-- SR-1 -->

`.github/workflows/sdl.yml` — the file that decides whether this repo's own
changes are gated, and by which version of the gate. `docs/sdl/baseline.md` —
the standing exposure model every later cycle reads instead of re-deriving; a
baseline that describes a channel the repo no longer uses misinforms every cycle
that references it. No credentials, no runtime, no consumer-facing code.

## Trust boundaries crossed <!-- SR-2 -->

No new boundary. This moves this repo to the far side of an existing one: the
"this repo → consumer CI" boundary in `baseline.md`. Its own CI now runs the
released validator rather than the previous major's, which is the point — a
regression that would reach consumers now reaches this repo first.

## Data classification <!-- SR-1 -->

Public. No PII, credentials, or customer data. The gate runs read-only with the
default `GITHUB_TOKEN` and holds no secret.

## External inputs introduced <!-- SR-2 -->

None new to this repo's code. The `@v2` workflow does consume inputs this repo
did not previously send it — the GitHub event payload's `before` SHA and the
PR-association API response — but those are properties of the called workflow,
threat-modelled in `2026-08-06-gate-direct-pushes` and unchanged here. What is
new is that this repo is now subject to them.

## Security requirements <!-- SR-3, SR-4 -->

- The gate must call an existing, resolvable tag — never `main`, and never a ref
  that does not resolve (an unresolvable `uses:` fails the run in a way that
  reads as infrastructure noise rather than as a missing gate).
- The ref must be the same moving major alias consumers pin, not a pinned
  `vX.Y.Z`. Dogfooding is worth nothing if this repo runs a different artifact
  from the one it ships.
- `baseline.md` must not name a channel the repo does not use.

## Related prior cycles

- `2026-08-06-gate-direct-pushes` — cut 2.0.0 and left this ref at `@v1`
  deliberately, recording the move as the release's last step.
- `2026-08-03-release-process` — established the alias/immutable-tag contract
  this ref depends on.
- `2026-06-10-adopt-sdl-governance` — created `sdl.yml` and its original `@v1`.

## Carried-forward residual risks

- `2026-08-06-gate-direct-pushes:R2` — the push path was unexercised against
  real GitHub events. This cycle is the first change that subjects this repo to
  it, and is the intended venue for closing it.
