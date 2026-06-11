# SDL — Admin Setup

For whoever maintains the SDL governance infrastructure for savioke. Covers first-time org setup, releasing changes, and onboarding repos and developers.

This document is for administrators. Day-to-day developers should read `developer-guide.md`.

## Overview of the moving parts

| Piece | Where it lives | Why |
|-------|----------------|-----|
| `savioke/sdl` repo (public) | github.com/savioke/sdl | Single source of truth for skills, templates, workflows. |
| Cloned install at `~/.sdl-governance` on each dev box | Per-developer | Source for skills + scripts on the local machine. |

The repo is public. Consuming repos' CI checks it out with the default `GITHUB_TOKEN`, and the reusable workflow (`sdl-validate.yml`) is callable by any repo — no deploy key, org secret, or access policy is required. The repo holds no secrets and nothing competitively sensitive (see "If we ever need to go private" below).

## First-time setup

The repo must be public so consuming repos can resolve the reusable workflow and check out the validator with the default `GITHUB_TOKEN`:

```sh
gh repo edit savioke/sdl --visibility public --accept-visibility-change-consequences
```

That is the entire infrastructure setup — no keys, secrets, or access policy. The only remaining step is tagging a release.

### Tag a release

Project repos pin to a tagged ref of this repo (`@v1` in the reusable workflow). Cut the tag once the skills have been exercised on a real feature:

```sh
git tag -a v1 -m "v1: initial SDL governance release"
git push origin v1
```

Subsequent breaking changes get `v2`, `v3`, etc. Non-breaking improvements move the existing tag forward (`git tag -f v1 && git push -f origin v1`) only if you're confident; otherwise, cut a new patch.

## Onboarding a new repo

Have whoever owns the repo run, on their workstation:

```sh
~/.sdl-governance/scripts/sync-to-repo.sh /path/to/their/repo
```

That drops `.github/workflows/sdl.yml`, creates `docs/sdl/.gitkeep`, and writes a `docs/sdl/baseline.md` stub. All get committed. No admin step is needed — the workflow checks this public repo out with the default `GITHUB_TOKEN`, so CI works as soon as the files land, including on Dependabot and external fork PRs.

Then have them run the `sdl-baseline` skill once ("initialize the SDL baseline"). It records the repo's standing security posture — exposure model, trust boundaries, standing risks — in `baseline.md`, which later cycles reference instead of re-deriving. CI emits a non-fatal `[warn]` until the baseline is filled.

## Onboarding a new developer

Send them:

```sh
gh repo clone savioke/sdl ~/.sdl-governance
~/.sdl-governance/scripts/install.sh
```

That clones the repo and symlinks skills into Claude Code (`~/.claude/skills/sdl`) and Copilot (`~/.copilot/skills/sdl`).

They update later with `cd ~/.sdl-governance && git pull`. Symlinks mean updates apply everywhere immediately.

## Updating the validator or skills

Skills and the validator are pulled live from this repo by all consumers (devs via symlinks, CI via `actions/checkout`). To ship a change:

1. Make the change on a branch in this repo.
2. Open a PR. Self-review carefully — there's no second-order SDL gate on this repo, you are the gate. Bad logic here breaks every other repo's CI.
3. Merge to `main`.
4. Move the appropriate version tag forward (or cut a new one) so consuming repos pick it up.

Consuming repos can pin a major version (`@v1`) and accept moving tags, or pin an exact tag (`@v1.2.0`) for stricter reproducibility. Default is `@v1` — see `templates/docs-sdl/...` and `scripts/sync-to-repo.sh` (the `SDL_REF` variable).

## Why this repo is public

This repo holds no secrets and nothing competitively sensitive, and a public source repo is the only design where SDL CI works everywhere without a distributed credential:

- Private reusable workflows are only callable by repos granted access via an Actions access policy — and the validator's checkout needs a secret, which is **never exposed to external fork PRs** (by design). So a private design can never validate fork PRs without `pull_request_target` (a security footgun) or forcing contributors onto origin branches.
- Public removes all of it: the reusable workflow is callable by anyone, and `actions/checkout` pulls this repo with the default `GITHUB_TOKEN`. CI works uniformly on internal branches, Dependabot, and external forks, with no deploy key, org secret, or access policy to maintain or rotate.

The mild downside accepted: `security-checks.md` reveals our review categories, and `docs/62443-mapping.md` holds some internal audit prose. Neither is a real disclosure risk — an attacker learns more from `package.json` than from these.

If we ever need to go private, the conversion is: flip visibility, re-add a read-only deploy key plus an org secret consumed via an `ssh-key:` line on the sdl checkout, set the repo's Actions access policy to `organization`, and mirror the secret into each consuming repo's Dependabot secret store. Fork PRs will stop being validatable. Don't do this without a concrete reason.

## Troubleshooting

**A consuming repo's CI fails to parse with "called workflow was not found" (`savioke/sdl/.github/workflows/sdl-validate.yml@v1`).** Either the `@v1` tag doesn't exist in this repo, or this repo was made private (a private repo's reusable workflow is invisible to callers without an access policy). Confirm the tag exists and the repo is public.

**Local skills aren't loading for a developer.** Confirm `~/.claude/skills/sdl` is a symlink pointing at `~/.sdl-governance/skills` (`ls -la ~/.claude/skills/sdl`). If something else is at that path, move it aside and re-run `install.sh`.

**Validator passes locally but fails in CI (or vice versa).** Confirm both are running the same `SDL_REF` (tag) and the same merge base. Local default is `HEAD~1`-ish depending on branch state; CI uses `origin/main`.
