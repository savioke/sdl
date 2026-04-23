# SDL — Admin Setup

For whoever maintains the SDL governance infrastructure for savioke. Covers first-time org setup, key rotation, and the option of making this repo public.

This document is for administrators. Day-to-day developers should read `developer-guide.md`.

## Overview of the moving parts

| Piece | Where it lives | Why |
|-------|----------------|-----|
| `savioke/sdl` repo | github.com/savioke/sdl | Single source of truth for skills, templates, workflows. |
| Read-only deploy key on `savioke/sdl` | Repo settings → Deploy keys | Lets CI in other savioke repos check out this repo to run the validator. |
| `SDL_DEPLOY_KEY` org secret | Org settings → Secrets and variables → Actions | Distributes the private half of that key to consuming repos. |
| Cloned install at `~/.sdl-governance` on each dev box | Per-developer | Source for skills + scripts on the local machine. |

The deploy key is read-only and scoped to this one repo. It exists purely to let GitHub Actions runners in consuming repos pull this repo's `lib/validate.py`. The repo itself contains no secrets — the key is plumbing, not a security boundary.

## First-time setup

### 1. Create the deploy keypair

Do this on a machine you trust. The private key is never committed and never written into the repo.

```sh
ssh-keygen -t ed25519 -C "sdl-ci-deploy-key" -f ./sdl_deploy_key -N ""
```

No passphrase — CI uses it non-interactively.

### 2. Register the public key as a deploy key

```sh
gh repo deploy-key add ./sdl_deploy_key.pub -R savioke/sdl -t "CI checkout"
```

Confirm in the GitHub UI: Settings → Deploy keys → "CI checkout" should appear with **read-only** access. Do not tick "Allow write access".

### 3. Register the private key as an org secret

```sh
gh secret set SDL_DEPLOY_KEY \
  --org savioke \
  --visibility selected \
  --body "$(cat ./sdl_deploy_key)"
```

`--visibility selected` means the secret is exposed only to repos you explicitly opt in. Then add each consuming repo:

```sh
gh secret set SDL_DEPLOY_KEY --org savioke --repos savioke/some-project
```

Or, in the UI: Org Settings → Secrets and variables → Actions → `SDL_DEPLOY_KEY` → "Selected repositories" → add the repo.

(If you prefer, set `--visibility all` to expose it to every repo automatically. Lower friction; we have nothing sensitive in this repo, so the blast radius of "all repos can read it" is just "all repos can clone the public-ish skills repo." Either is defensible.)

### 4. Destroy the local copies of the key

```sh
shred -u ./sdl_deploy_key ./sdl_deploy_key.pub
```

The public key now lives in GitHub repo settings; the private key now lives in GitHub org secrets. There is no third copy that needs storing.

### 5. Tag a release

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

That drops `.github/workflows/sdl.yml` and creates `docs/sdl/.gitkeep`. Both get committed.

Then, separately (admin step), expose the deploy secret to that repo:

```sh
gh secret set SDL_DEPLOY_KEY --org savioke --repos savioke/<new-repo-name>
```

If you set `--visibility all` in step 3, this is unnecessary.

## Onboarding a new developer

Send them:

```sh
gh repo clone savioke/sdl ~/.sdl-governance
~/.sdl-governance/scripts/install.sh
```

That clones the repo and symlinks skills into Claude Code (`~/.claude/skills/sdl`) and Copilot (`~/.copilot/skills/sdl`).

They update later with `cd ~/.sdl-governance && git pull`. Symlinks mean updates apply everywhere immediately.

## Rotating the deploy key

Do this on a regular cadence (annually is reasonable), or immediately if you suspect compromise.

```sh
# Generate a new keypair
ssh-keygen -t ed25519 -C "sdl-ci-deploy-key-$(date +%Y%m%d)" -f ./sdl_deploy_key_new -N ""

# Add the new public key alongside the old one
gh repo deploy-key add ./sdl_deploy_key_new.pub -R savioke/sdl -t "CI checkout $(date +%Y-%m-%d)"

# Update the org secret to the new private key
gh secret set SDL_DEPLOY_KEY \
  --org savioke \
  --visibility selected \
  --body "$(cat ./sdl_deploy_key_new)"

# Verify a real PR's CI run still passes (give it one full run cycle)

# Once verified, remove the old deploy key from the repo
gh repo deploy-key list -R savioke/sdl                  # find the old key's ID
gh repo deploy-key delete <old-key-id> -R savioke/sdl

# Destroy local copies of the new key
shred -u ./sdl_deploy_key_new ./sdl_deploy_key_new.pub
```

Order matters: add the new key before changing the secret, then verify, then remove the old key. If you change the secret first and the new key isn't yet registered, every consuming repo's CI breaks until you finish.

## Updating the validator or skills

Skills and the validator are pulled live from this repo by all consumers (devs via symlinks, CI via `actions/checkout`). To ship a change:

1. Make the change on a branch in this repo.
2. Open a PR. Self-review carefully — there's no second-order SDL gate on this repo, you are the gate. Bad logic here breaks every other repo's CI.
3. Merge to `main`.
4. Move the appropriate version tag forward (or cut a new one) so consuming repos pick it up.

Consuming repos can pin a major version (`@v1`) and accept moving tags, or pin an exact tag (`@v1.2.0`) for stricter reproducibility. Default is `@v1` — see `templates/docs-sdl/...` and `scripts/sync-to-repo.sh` (the `SDL_REF` variable).

## Should this repo be public?

It contains no secrets and nothing competitively sensitive. Going public would slightly simplify operations:

- The deploy key and `SDL_DEPLOY_KEY` org secret become unnecessary — `actions/checkout` can pull a public repo with the default `GITHUB_TOKEN`.
- New devs and contractors don't need org membership to clone it.
- Other organizations could adopt or contribute, which has some incidental community-good value.

Reasons to stay private:

- The set of security categories in `security-checks.md` is mildly informative about our posture. Not a real disclosure risk; an attacker learns more from `package.json` than from this list.
- Internal-only audit prose in `docs/62443-mapping.md` may grow over time and might eventually warrant privacy.

No urgency either way. Default is private. If we ever decide to flip it, the conversion is: remove the deploy key, remove the org secret, drop the `ssh-key:` line from `.github/workflows/sdl-validate.yml`. That's it.

## Troubleshooting

**CI fails with "Repository not found" on the sdl checkout step.** The consuming repo doesn't have access to `SDL_DEPLOY_KEY`. Either add it via `gh secret set --repos`, or check that the secret's "selected repositories" list includes it.

**CI fails with "Permission denied (publickey)" on the sdl checkout step.** The deploy key in `savioke/sdl` doesn't match the private key in `SDL_DEPLOY_KEY`. Most often happens during a key rotation when the order of operations was wrong. Re-run rotation in the documented order.

**Local skills aren't loading for a developer.** Confirm `~/.claude/skills/sdl` is a symlink pointing at `~/.sdl-governance/skills` (`ls -la ~/.claude/skills/sdl`). If something else is at that path, move it aside and re-run `install.sh`.

**Validator passes locally but fails in CI (or vice versa).** Confirm both are running the same `SDL_REF` (tag) and the same merge base. Local default is `HEAD~1`-ish depending on branch state; CI uses `origin/main`.
