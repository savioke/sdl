# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Move the plugin marketplace out of this repo into a dedicated org-wide repo (`savioke/relay-plugin-marketplace`, marketplace name `relay`), and make the `sdl` plugin self-contained so Claude Code developers — the common case — install with two slash commands and no clone. `skills/`, `lib/`, and `templates/` move into `plugins/sdl/` (replacing the old out-of-tree symlinks), skills locate their tooling relative to their own SKILL.md instead of hardcoding `~/.sdl-governance`, and the clone-plus-symlink path remains only for Copilot/other agents and repo onboarding. Follows this morning's `2026-07-09-marketplace-rename`, which established that `relay-sdl` squatted the namespace an org marketplace needs (`sdl@relay-sdl` was also redundant).

## Scope

In scope: deleting `.claude-plugin/marketplace.json` here (its replacement lives in `savioke/relay-plugin-marketplace`); moving `skills/`, `lib/`, `templates/` under `plugins/sdl/`; plugin-relative tooling paths in `sdl-spec`, `sdl-review`, `sdl-dep-update` SKILL.md files and `validate.py`'s `template_dir()`; path updates in `install.sh` (Copilot symlink target, marketplace registration by SSH URL), `sync-to-repo.sh`, both workflows, and docs; plugin version bump to 0.6.0.

Out of scope: the marketplace repo's own contents (one manifest, validated with `claude plugin validate` but not SDL-gated — accepted as baseline:B7 this cycle); sha-pinning the plugin source (tracks `main`, matching the prior clone behavior); migration automation for the sole pre-split user (manual, per the same reasoning as 2026-07-09-marketplace-rename).

## Assets touched <!-- SR-1 -->

Every integrity asset in the baseline moves or changes: `validate.py` and the skills relocate (content changes limited to path resolution), `install.sh` and `sync-to-repo.sh` get new target paths, `sdl-validate.yml` points at the validator's new location. New external integrity asset: the marketplace manifest in `savioke/relay-plugin-marketplace` now decides what `sdl@relay` delivers to developer machines (baseline:B7).

## Trust boundaries crossed <!-- SR-2 -->

One new boundary: **marketplace repo → Claude Code developer machines.** Claude Code fetches `plugins/sdl` from this repo's `main` as directed by the external manifest's `source` field. Recorded in `baseline.md` (trust boundaries + B7). Existing boundaries (repo → consumer CI at `@v1`, scripts → workstation) unchanged in kind; crossing-point paths updated.

## Data classification <!-- SR-1 -->

None new. Public repo, no secrets — per `baseline.md`. The marketplace repo is also public and holds only the manifest, which references this public repo.

## External inputs introduced <!-- SR-2 -->

None. No new network fetches in scripts: `install.sh` swaps the argument of the existing `claude plugin marketplace add` from a local path to an SSH URL — the fetch happens inside the `claude` CLI, as it already did for plugin installs.

## Security requirements <!-- SR-3, SR-4 -->

- The plugin must be self-contained: nothing under `plugins/sdl/` may reference files outside it at runtime (no out-of-tree symlinks, no `~/.sdl-governance` assumptions), so a marketplace install cannot silently depend on clone state.
- Skill path resolution must be identical for a plugin install and a clone (relative to SKILL.md), so the two delivery channels cannot diverge in behavior.
- `validate.py` must prefer its own adjacent templates over the clone's, so CI and plugin installs compare against the templates they shipped with.
- The marketplace manifest's `source` must point at `https://github.com/savioke/sdl.git` path `plugins/sdl` — the public canonical repo, nothing else.
- `install.sh` stays string/path-level changes only; baseline:B3 disposition unchanged.

## Related prior cycles

- `2026-07-09-marketplace-rename` — renamed the in-repo marketplace to `relay-sdl` this morning; this cycle supersedes it by removing the in-repo marketplace entirely. Its T1 (orphaned registration) recurs here identically.
- `2026-06-11-fix-update-instructions` — wrote the update instructions rewritten again here.

## Carried-forward residual risks

None. No prior cycle has residual risks with `Disposition: defer` or `mitigate-later` in its `04-verification.md`.
