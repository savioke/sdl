# SDL — Releasing

How a change in this repo reaches the people who depend on it.

## The procedure

Same every time, whether the change is a typo in a skill or a new validator check.

1. **Branch**, make the change with its SDL cycle as normal.
2. **In the same PR**, bump `version` to the same value in `plugins/sdl/.claude-plugin/plugin.json` and `plugins/sdl/.codex-plugin/plugin.json`, then add a matching `## X.Y.Z` entry to `CHANGELOG.md`. Which digit to bump: see the contract below.
3. **Open the PR, merge it.**
4. **Back on `main`, pulled:** run `scripts/release.sh`. No arguments.

```sh
git checkout main && git pull
scripts/release.sh
```

That's the whole thing. The script tags the release, moves the pointer consumers follow, and updates the Claude Code and Codex marketplace catalogs — refusing if anything about the state is wrong.

If the PR touches nothing under `plugins/sdl/` or `.github/workflows/sdl-validate.yml`, skip steps 2 and 4 — nothing shipped, so there is nothing to release. CI tells you which case you are in.

**Wait for CI before step 4.** The release refuses while checks on the merge commit are still running (`check 'x' is still in_progress`). Give it a minute and re-run.

**One-time Codex bootstrap for 2.1.0:** merge the `relay-plugin-marketplace`
`codex-support` branch before merging and releasing this repo's `codex-support`
branch. That marketplace change adds the Codex catalog but leaves both catalogs
pinned at the already-released `v2.0.0`, so Claude Code is not moved early.
Codex installation becomes functional when `release.sh` creates `v2.1.0` and
advances both catalogs together.

## What the script does

1. Refuses unless: you are on `main`, the tree is clean, `main` matches `origin/main`, both plugin manifests declare the same `X.Y.Z`, `CHANGELOG.md` has an entry for it, that version has never been tagged, both marketplace catalogs are readable and have exactly one editable `sdl` entry, and every check on the commit is green.
2. Shows you the plan — including what both catalogs say now — and asks once.
3. Creates the annotated, signed tag `vX.Y.Z`, using your changelog entry as the message.
4. Force-moves the `vX` alias to the same commit.
5. Points both marketplace catalogs at `vX.Y.Z` and mirrors the version into the Claude catalog, whose schema carries it explicitly.
6. Re-verifies the result locally.

Every refusal in step 1 happens before anything is pushed, including the manifest check — the manifest is read and validated up front even though it is written last. Once `vX.Y.Z` exists it cannot be recut, so a problem discovered after the tags were pushed would leave you with no way to re-run.

Released tags are never rewritten. If `v1.2.3` is wrong, release `v1.2.4`.

## Which digit to bump

The `vX` alias moves under repos that did not ask for it, so what may move is constrained. For a gate, the question is not API shape — it is *can a previously-passing PR now fail?*

| | Rule | Examples |
|---|---|---|
| **Major** | Anything that can turn a previously-green PR red. Cut `vX+1`; leave `vX` where it is so repos migrate on their own schedule. | A new required document; stricter parsing; promoting a `[warn]` to a failure. |
| **Minor** | Only widens what passes, or adds capability. | The dependency-update routine tier; a new skill or template; a new check that emits `[warn]` only. |
| **Patch** | Cannot change a gate outcome. | Bug fixes, wording, docs, refactors with identical behavior. |

**New checks land as `[warn]` in the current major and are promoted to failures only at a major bump.** That is what keeps majors rare, and rare majors are what make a force-moved alias safe. `validate.py` already works this way — see the dependency-manifest warning near the end of `main()`.

Versions are strict `X.Y.Z`. No prerelease or build suffixes: the version is both a git ref and a plugin cache directory name.

## Why it works this way

Two channels deliver this repo, with opposite pinning economics:

| Channel | Who consumes it | What it pins | Why |
|---------|-----------------|--------------|-----|
| CI gate | Every governed repo's `.github/workflows/sdl.yml` | the moving alias `@v2` | There are N of these, owned by other teams. Asking them to edit a pin per release does not scale, so the alias moves under them. |
| Claude Code and Codex plugin | Two host-specific catalogs in `savioke/relay-plugin-marketplace` | the same immutable tag, for example `v2.1.0` | There are only two centrally maintained pins and the release script edits both, so pinning exactly is free — and it makes a version identify one specific tree. |

*Pin exactly where pins are centrally maintained; use a moving alias where there
are many consumers.* The release script sets both from the same commit so they
cannot diverge.

Plugin installs are cached, so **an install stays on its cached copy until its marketplace and plugin version advance**. Shipping plugin content without bumping the shared version delivers it to nobody. That is why step 2 is not optional bookkeeping.

## What CI checks

- **On a PR** — if the diff touches shipped content, the version must have increased against the base branch and have a changelog entry. This is what enforces step 2.
- **On demand** — the declared version has an immutable tag, the `vX` alias points at the same commit, no shipped file has changed since that tag, and both marketplace catalogs pin that exact tag (with the Claude catalog also naming the version). A catalog that cannot be fetched warns rather than fails; an outage is not drift. Run it from the Actions tab (`self-check`, "Run workflow"), or `python scripts/check_release.py --mode released` locally.

Released-mode runs on no automatic trigger, deliberately: between a merge and its release, every one of those conditions is transient, and reporting them would mark a pending release as a broken `main`. It used to run on a daily schedule for exactly that reason — off the push path — but a scheduled run attaches its check-runs to whichever commit `main` is resting on, and `release.sh` refuses to release a commit whose checks are not green. The monitor therefore blocked the release that would have cleared it. Detecting "merged but never released" is not worth a deadlock, and the real control is releasing right after the merge.

What the schedule was also there for is covered without it: `check_pins.py` runs on every push and PR, so an action retagged upstream after we pinned it is caught on the next change; and the marketplace catalogs have exactly one writer — `release.sh`, which verifies its own work at step 8. A catalog edited by hand in its own repo is the one drift class now found only when someone asks. Ask after any manual edit there.

**CI does not release.** It holds no credential that can write a tag or the marketplace catalogs, and it should not: a CI job that can rewrite the distribution channel turns any compromise of this repo's workflows into arbitrary code on every developer's machine and in every consumer's CI. Detection lives in CI; the action stays with the maintainer. See cycle `2026-08-03-release-process`, T3.

## Escape hatches

Named so their use shows up in your shell history. For exceptional situations — say why in the changelog entry.

- `SDL_RELEASE_SKIP_CI=1` — release a commit whose checks are not green (unrelated infrastructure flake).
- `SDL_RELEASE_YES=1` — skip the confirmation prompt.
- `SDL_MARKETPLACE_REPO=owner/repo` — release to a different marketplace, for testing the process itself.

There is no escape hatch for rewriting a released tag.

## Tag signing

Consumer CI executes these tags, so they should be attributable. `release.sh` signs when `user.signingkey` is set and warns when it is not. One-time SSH setup, no GPG:

```sh
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
gh api -X POST /user/ssh_signing_keys -f title=sdl -f key="$(cat ~/.ssh/id_ed25519.pub)"
```

Nothing verifies these signatures yet — they are attribution and audit evidence, not a barrier. If verification is ever added, its allowlist of authorized signers must live outside this repo; an anchor that shares a write boundary with the artifact it authorizes proves nothing against whoever can write that boundary.

## Onboarding a repo mid-flight

Nothing to coordinate: `sync-to-repo.sh` writes a workflow pinned to the current alias (`@v2`; override with `SDL_REF`), and the repo picks up whatever that alias points at on its first run. A repo that needs to hold still — mid-audit, say — can pin an exact tag in its own `sdl.yml`:

```yaml
uses: savioke/sdl/.github/workflows/sdl-validate.yml@v2.0.0
```

Pin `sdl_ref` to the same tag if you do, so the validator code and the workflow come from one commit.

That is also the fix when a release breaks someone: pin the previous exact tag to unblock, tell the maintainer, go back to the alias once it is fixed. Say so in the changelog entry if a release is likely to need it.

## If a release goes wrong

1. **Roll the alias back.** `git tag -f v2 v2.0.0 && git push -f origin v2` — consumers recover on their next run. The bad tag stays; it is evidence.
2. **Roll both marketplace catalogs back** to the previous `source.ref` (and the Claude catalog's previous version) if developers are affected. Tell Claude Code users to run `/plugin marketplace update relay` and Codex users to run `codex plugin marketplace upgrade relay`, then restart their session.
3. **Fix forward** in a normal PR with a version bump, noting both the break and the fix in `CHANGELOG.md`.

Rolling the alias back is a distribution change, not a code change, so it needs no cycle of its own — the fix does.
