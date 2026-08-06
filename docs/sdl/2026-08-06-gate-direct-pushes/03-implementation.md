# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

`sdl-validate.yml` gained a resolve step that decides, per event, what to
validate: a `pull_request` run is unchanged; a `push` run asks GitHub whether
the commit came from a merged PR and skips it if so, otherwise diffs against
`github.event.before` and passes `--push`. `validate.py` gained that flag, which
switches cycle resolution from `find_cycle_for_branch` to the new
`cycle_in_diff`, and now reports an empty diff as an empty diff instead of as
"no substantive code changes." `new_cycle.py --slug` names a cycle explicitly
and lifts the one-cycle-per-branch guard, without which a second direct-push
cycle could not be scaffolded at all. Supporting changes: workflow inputs moved
out of `run:` interpolation into `env:`, explicit read-only `permissions:`,
`sdl-spec` and the developer guide describe the direct-push path, the generated
consumer workflow's comment is corrected, and the plugin goes to 2.0.0 with a
changelog entry. The `pull_request` path is untouched.

Because 2.0.0 is the first major, the release surface moved with it: the
`sdl_ref` input defaults to `v2` so a caller on `@v2` cannot check out a v1
validator, `sync_to_repo.sh` onboards new repos at `@v2`, and `docs/releasing.md`,
`docs/admin-setup.md`, and the changelog header describe `@v2` as the alias
consumers pin. `v1` is documented as end-of-life rather than as an alternative.
One `@v1` reference remains by necessity: this repo's own `.github/workflows/sdl.yml`
cannot point at `@v2` until `@v2` exists, or the PR that creates it cannot pass
its own gate.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Skip requires a positive answer: the count is filtered to `merged_at != null` and any failure resolves to the literal `unknown`, which validates and logs why it could not tell. Uses the PR-association API rather than parent count, which squash and rebase merges defeat. | `.github/workflows/sdl-validate.yml:66-78` | this branch |
| T2 | On `--push` the cycle must be carried by the diff — `cycle_in_diff` collects slugs from `docs/sdl/<slug>/…` paths in the push and requires a `.sdl-meta.yml`, so a pre-existing `branch: main` cycle cannot vouch for later work. | `plugins/sdl/lib/validate.py:236-256,377-384` | this branch |
| T3 | Inputs reach the shell through `env:` as quoted variables rather than `${{ }}` interpolation into script text; `permissions:` declared read-only. | `.github/workflows/sdl-validate.yml:16-18,47-54,96-99` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- **Uncertainty resolves toward checking.** Every unknown in the resolve step —
  API failure, missing permission, unparseable output — falls through to running
  the validator, and says so in the log. There is no path where an error is read
  as "nothing to do."
- **Do not re-implement a decision, defer to it.** Anything that came through a
  PR is skipped rather than re-judged, because the `pull_request` run already
  applied the adoption exemption, the dependency-update class rules, and the
  stub checks. A second implementation of those rules on the push path would be
  a second place to get them wrong.
- **No interpolation into shell.** All `${{ }}` values are bound to `env:` and
  referenced as quoted shell variables.
- **Explicit failure over silent skip.** `set -e` is deliberately not combined
  with `[ … ] && args+=(…)` — a false test would end the step and skip the very
  validator it configures. Written as an `if` block with a comment saying why.
- **Reachability checked before use.** `github.event.before` is tested with
  `git cat-file -e` and compared against the all-zeros sentinel before being
  used as a diff base, so a force-push or branch creation produces a stated
  reason rather than a git error.
- **Guards loosened deliberately, not removed.** `new_cycle.py` still refuses a
  duplicate slug and still guards feature branches; only an explicit `--slug`
  lifts the branch guard.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

No packages. `validate.py` remains standard-library only per the baseline's
standing requirement. The workflow now depends on `gh`, preinstalled on GitHub
runners, and on the GitHub API — a runtime dependency of the gate, not a build
dependency, and one whose failure is handled by validating anyway.
`plugins/sdl/.claude-plugin/plugin.json` 1.3.0 → 2.0.0.

## Deviations from spec or threat model

None. Two decisions are worth recording rather than leaving implicit:

- **The scope grew mid-cycle.** Requiring a cycle on direct pushes exposed that
  `new_cycle.py` could not produce one: the first push to `main` scaffolded
  `<date>-main` and every later one was refused as "branch 'main' already has a
  cycle." Shipping the gate without `--slug` would have demanded evidence the
  tooling refuses to create. It is in this cycle because the gate change is
  incomplete without it.
- **`branches: [main]` is still hardcoded** in the generated consumer workflow.
  Detecting the default branch at adoption time is the real fix; for now the
  generated file carries a comment saying to change it, and the gap is recorded
  in 02 "Noted for future cycles" and as a residual risk.
