# SDL — Admin Setup

For whoever maintains the SDL governance infrastructure for Relay. Covers first-time org setup, releasing changes, and onboarding repos and developers.

This document is for administrators. Day-to-day developers should read `developer-guide.md`.

## Overview of the moving parts

| Piece | Where it lives | Why |
|-------|----------------|-----|
| `savioke/sdl` repo (public) | github.com/savioke/sdl | Single source of truth: the `sdl` plugin (skills, lib, templates), workflows, scripts. |
| `savioke/relay-plugin-marketplace` repo (public) | github.com/savioke/relay-plugin-marketplace | Org-wide Claude Code plugin marketplace; its manifest points at `plugins/sdl` here. How Claude Code devs install and update. |
| Cloned install at `~/.sdl-governance` | Per-developer, only if they use Copilot or another non-Claude agent; also needed by whoever runs `sync-to-repo.sh` | Non-Claude agents have no marketplace path, so they read skills from the clone. |

The repo is public. Consuming repos' CI checks it out with the default `GITHUB_TOKEN`, and the reusable workflow (`sdl-validate.yml`) is callable by any repo — no deploy key, org secret, or access policy is required. The repo holds no secrets and nothing competitively sensitive (see "If we ever need to go private" below).

## First-time setup

The repo must be public so consuming repos can resolve the reusable workflow and check out the validator with the default `GITHUB_TOKEN`:

```sh
gh repo edit savioke/sdl --visibility public --accept-visibility-change-consequences
```

That is the entire infrastructure setup — no keys, secrets, or access policy. The only remaining step is cutting a release, which is `scripts/release.sh` and is documented in `releasing.md`.

## Onboarding a new repo

Have whoever owns the repo run, on their workstation:

```sh
~/.sdl-governance/scripts/sync-to-repo.sh /path/to/their/repo
```

That drops `.github/workflows/sdl.yml`, creates `docs/sdl/.gitkeep`, and writes a `docs/sdl/baseline.md` stub. No admin step is needed — the workflow checks this public repo out with the default `GITHUB_TOKEN`, so CI works as soon as the files land, including on Dependabot and external fork PRs.

Then have them run the `sdl-baseline` skill once ("initialize the SDL baseline"), and commit the scaffold and the filled baseline in one PR. It records the repo's standing security posture — exposure model, trust boundaries, standing risks — in `baseline.md`, which later cycles reference instead of re-deriving.

The gate waives the cycle requirement for that adoption PR (the workflow it installs counts as code, and no cycle can exist yet) — but only for a diff that adds `sdl.yml` and `baseline.md` and touches nothing else outside `docs/sdl/`, and only once the baseline is more than a stub. Splitting it — scaffold in one PR, baseline in the next — fails the gate, and so does folding unrelated code in. Both are recoverable: fill the baseline, or run `sdl-spec` for a real cycle. On later PRs, an unfilled baseline is only a non-fatal `[warn]`.

## Onboarding a new developer

**Claude Code only** (the common case) — send them two slash commands, no clone:

```
/plugin marketplace add savioke/relay-plugin-marketplace
/plugin install sdl@relay
```

They update later with `/plugin marketplace update relay`.

**Copilot or other agents** — send them:

```sh
gh repo clone savioke/sdl ~/.sdl-governance
~/.sdl-governance/scripts/install.sh
```

That symlinks skills into Copilot (`~/.copilot/skills/sdl`) and also registers the Claude Code marketplace. They update with `cd ~/.sdl-governance && git pull`; the symlink applies it to Copilot immediately.

Anyone whose clone predates 1.0.0 must re-run `install.sh` once, not just pull: skills moved to `plugins/sdl/skills/` in the 1.0.0 release, and a symlink created before that move points at a path that no longer exists — Copilot then silently has no skills. `install.sh` repairs the link.

## Updating the validator or skills

Full procedure and the compatibility contract: **`releasing.md`**. In short:

1. Make the change on a branch, with its SDL cycle. In the same PR, bump `version` in `plugins/sdl/.claude-plugin/plugin.json` and add the matching `CHANGELOG.md` entry — CI fails the PR if shipped content changed without them.
2. Open a PR. This repo runs its own SDL gate (`.github/workflows/sdl.yml`, self-referential at the current alias) plus `self-check.yml` unit tests — but you are still the primary reviewer: single maintainer, no second human. Bad logic here breaks every other repo's CI, so self-review carefully.
3. Merge to `main`.
4. Run `scripts/release.sh`. It tags `vX.Y.Z`, moves the `vX` alias consumers pin, and updates the marketplace manifest. Do it right after the merge, while you are still at the keyboard: **nothing goes red in the meantime.** Merging and forgetting is silent until the next daily `self-check` run (06:17 UTC), which is when a merged-but-unreleased state is reported. Releasing immediately is the control; the daily run is only the backstop. To check on demand, run the `self-check` workflow from the Actions tab, or `python scripts/check_release.py --mode released` locally.

   Released-mode checks deliberately do not run on push to `main` — between a merge and its release they are all transient, and failing there would block the very release that clears them. `releasing.md`, "What CI checks", has the reasoning; cycle `2026-08-03-release-process` records it as residual risk R5.

Consuming repos default to the moving `@v2` and need no action per release; they can pin an exact tag (`@v2.0.0`) for stricter reproducibility or to hold still during an audit, in which case pin `sdl_ref` to match. See `scripts/sync-to-repo.sh` (the `SDL_REF` variable).

## Why this repo is public

This repo holds no secrets and nothing competitively sensitive, and a public source repo is the only design where SDL CI works everywhere without a distributed credential:

- Private reusable workflows are only callable by repos granted access via an Actions access policy — and the validator's checkout needs a secret, which is **never exposed to external fork PRs** (by design). So a private design can never validate fork PRs without `pull_request_target` (a security footgun) or forcing contributors onto origin branches.
- Public removes all of it: the reusable workflow is callable by anyone, and `actions/checkout` pulls this repo with the default `GITHUB_TOKEN`. CI works uniformly on internal branches, Dependabot, and external forks, with no deploy key, org secret, or access policy to maintain or rotate.

The mild downside accepted: `security-checks.md` reveals our review categories, and `docs/62443-mapping.md` holds some internal audit prose. Neither is a real disclosure risk — an attacker learns more from `package.json` than from these.

If we ever need to go private, the conversion is: flip visibility, re-add a read-only deploy key plus an org secret consumed via an `ssh-key:` line on the sdl checkout, set the repo's Actions access policy to `organization`, and mirror the secret into each consuming repo's Dependabot secret store. Fork PRs will stop being validatable. Don't do this without a concrete reason.

## Troubleshooting

**A consuming repo's CI fails to parse with "called workflow was not found" (`savioke/sdl/.github/workflows/sdl-validate.yml@v2`).** Either the pinned tag doesn't exist in this repo, or this repo was made private (a private repo's reusable workflow is invisible to callers without an access policy). Confirm the tag exists and the repo is public.

**Skills aren't loading in Claude Code.** Run `/plugin` and confirm `sdl` is installed and enabled from marketplace `relay`. If the marketplace is missing, re-add it (`/plugin marketplace add savioke/relay-plugin-marketplace`).

**Skills aren't loading in Copilot.** Confirm `~/.copilot/skills/sdl` is a symlink pointing at `~/.sdl-governance/plugins/sdl/skills` (`ls -la ~/.copilot/skills/sdl`). If something else is at that path, move it aside and re-run `install.sh`.

**Validator passes locally but fails in CI (or vice versa).** Confirm both are running the same `SDL_REF` (tag) and the same merge base. Local default is `HEAD~1`-ish depending on branch state; CI uses `origin/main`.
