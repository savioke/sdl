# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Define and mechanize one release process for this repo, replacing a per-release judgment call — the previous guidance was to move the tag forward "only if you're confident" — with one procedure that is the same every time. This repo distributes executable content to two consumer populations over two channels with different pinning economics: N consumer repos pin the reusable workflow at `@v1` (a moving tag they cannot be asked to edit per release), and exactly one marketplace manifest pins the Claude Code plugin. The release procedure gives each channel the pin it can afford — a moving major alias for CI, an immutable exact tag for the plugin — and makes both point at the same commit by construction. Every release produces a signed annotated `vX.Y.Z` tag as the auditable artifact, a force-moved `vX` alias, a `CHANGELOG.md` entry, and a marketplace manifest bumped to that exact tag. `scripts/release.sh` performs it in one command; `scripts/check_release.py` detects in CI when it has not been performed.

The trigger is a delivery defect found while preparing 0.7.0: the plugin cache is keyed by manifest version (`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, a plain directory with no `.git`), so shipped content that does not carry a version bump never reaches an existing install; and because `source.ref` was `main`, a version that did get bumped still did not identify a specific tree — two developers updating a day apart could receive different code under the same declared version. Concurrently `v1` had drifted 25 commits behind `main`, leaving the CI gate running a validator that predates the dependency-update routine tier while the plugin channel shipped the skills that emit it — a skew that fails consumer PRs. This cycle also promotes the version to 1.0.0 so that the plugin's semver and the tag consumers already pin (`@v1`) denote the same major.

## Scope

In scope:

- Release procedure and its compatibility contract, documented in `docs/releasing.md`.
- `scripts/release.sh` — preconditions, signed tag, alias move, marketplace manifest update.
- `scripts/check_release.py` + tests — PR-mode and released-mode drift detection.
- `CHANGELOG.md`, seeded with the unreleased history back to the last real release.
- Version promotion to 1.0.0 (`plugins/sdl/.claude-plugin/plugin.json`).
- Marketplace manifest: `version` 1.0.0 and `source.ref` pinned to `v1.0.0` — applied to `savioke/relay-plugin-marketplace` by `release.sh`, not by hand.
- Correcting the upgrade instructions that tell clone-based developers a `git pull` is sufficient — it no longer is, since `2026-07-09-split-marketplace` moved `skills/` under `plugins/sdl/`.
- `docs/62443-mapping.md`: SUM moves from out-of-scope to in-scope for this repo.
- Added during PR review: a "Proportionality" section in the `sdl-review` skill and a constrained "Defects found" section in the `04-verification.md` template. Both are agent-executable instructions (`baseline:B2`) and so are gated as code. The trigger was this cycle's own review producing paragraph-length entries for non-security defects; the standard now says only defects in a security control belong in the artifacts, because non-security content buries the signal an auditor comes here for.

Out of scope:

- Executing the release. The tag push and the marketplace commit are run by the maintainer.
- Automating the release from CI. Rejected on threat-model grounds — see T3.
- `dep-update-tier:R2` (consumers do not run `check_pins`): unchanged by this cycle, still deferred there.
- The end-to-end plugin-cache install test (`plugin-self-adopt:R1`): still deferred, retargeted at `v1.0.0`.

## Assets touched <!-- SR-1 -->

Integrity assets per `baseline.md` — no confidentiality assets exist in this repo. This cycle touches the two distribution crossing points directly:

- The `v1` tag and the new `vX.Y.Z` tags — what consumer CI executes.
- The marketplace manifest `source.ref` in `savioke/relay-plugin-marketplace` — what developer agents execute (`baseline:B7`).
- The maintainer's git push credentials and, newly, their tag-signing key.
- `scripts/release.sh` and `scripts/check_release.py`, both new, both executing on the maintainer's workstation and in CI respectively.

## Trust boundaries crossed <!-- SR-2 -->

Standing boundaries per `baseline.md` (repo → consumer CI, repo → developer workstation) are unchanged in shape; this cycle changes what sits at the crossing point, from a mutable branch and a lagging alias to an immutable per-release tag.

One new boundary: `check_release.py` fetches the marketplace manifest from `raw.githubusercontent.com` into this repo's CI and parses it. That is a network read of an externally-hosted document into a CI context — the first network fetch in this repo's own tooling (`baseline:B3` notes the scripts have none). See T1.

## Data classification <!-- SR-1 -->

Public. No PII, no customer data, no secrets. The release process deliberately introduces no CI-held credential (see T3); the only credentials involved are the maintainer's own, used interactively on their workstation.

## External inputs introduced <!-- SR-2 -->

- **Marketplace manifest over HTTPS** (`check_release.py`, released mode) — externally-hosted JSON parsed in CI.
- **`plugin.json` version string** (`release.sh`) — repo-controlled, but it is interpolated into a git ref name and a shell context, so it is validated as strict semver before use.
- **`SDL_MARKETPLACE_REPO` / `SDL_RELEASE_*` environment variables** — maintainer-controlled release-time overrides.
- **`gh`/`git` remote responses** — existing-tag and CI-status queries whose output gates the release.

## Security requirements <!-- SR-3, SR-4 -->

1. **A released version identifies exactly one tree.** The marketplace `ref` must be an immutable tag equal to the declared version; `main` must never be a distribution ref.
2. **Immutable tags are never rewritten.** `release.sh` refuses if `vX.Y.Z` already exists locally or on the remote. Only the `vX` alias moves.
3. **Nothing is released that CI has not passed.** The release refuses on a commit whose checks are not green; the override is explicit and named.
4. **A tag is attributable.** Annotated, and signed when a signing key is configured (`baseline:B1` names signed releases as its revisit path).
5. **Version input is validated before it becomes a ref or reaches a shell.** Strict `^\d+\.\d+\.\d+$`, no interpolation of unvalidated values.
6. **Drift is detected without CI holding write credentials.** CI may detect that a release is pending or that the manifest disagrees; it may not perform the release (T3).
7. **A moving alias only ever moves within a major.** Any change that can turn a previously-passing consumer PR red requires a new major; new checks land as `[warn]` first. This is the property that makes force-moving `vX` under N repos safe.
8. **Network failure must not be indistinguishable from drift.** A failed manifest fetch warns; only a successfully fetched, disagreeing manifest fails.

## Related prior cycles

- `2026-07-09-split-marketplace` — moved the plugin out to the external marketplace repo, creating the `source.ref` crossing point (`baseline:B7`) this cycle pins.
- `2026-07-10-plugin-self-adopt` — the 0.7.0 content this release ships; its R1 verification target moves to `v1.0.0`.
- `2026-07-09-actions-3e1200532a` — the precedent that a mitigation is not live for consumers until `v1` advances (`baseline:B6`), which the released-mode drift check now detects automatically.
- `2026-07-09-dep-update-tier` — introduced both the routine tier that the stale `v1` cannot validate and the warn-first pattern (`validate.py:353`) this cycle promotes to a documented contract.

## Carried-forward residual risks

- `baseline:B5` (moving `v1` tag weakens reproducibility; "revisit as consumer count grows") — **addressed here**, partially: immutable per-release tags now exist and are what the plugin channel consumes, the CI channel keeps the moving alias by necessity, and the warn-first contract bounds what a move can do.
- `baseline:B7` (marketplace manifest outside this repo's gates) — **addressed here**, partially: pinning `source.ref` to an immutable tag means an unreviewed change to `main` can no longer reach developer machines, and released-mode drift detection makes an unexpected manifest edit visible in this repo's CI. Write access to the manifest remains the residual exposure.
- `plugin-self-adopt:R1` (plugin-cache path never exercised against a published release) — **still deferred**, retargeted from 0.7.0 to `v1.0.0`; the maintainer plans it with the next repo onboarding.
- `dep-update-tier:R2` (consumers do not run `check_pins`) — **still deferred**, untouched by this cycle.
