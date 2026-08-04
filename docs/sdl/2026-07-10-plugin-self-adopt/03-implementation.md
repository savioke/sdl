# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

Moved the per-repo SDL onboarding logic into the plugin package: new `plugins/sdl/lib/sync_to_repo.sh` resolves the baseline template relative to its own location, so it works from the Claude plugin cache, a `~/.sdl-governance` clone, or any checkout. `scripts/sync-to-repo.sh` became a two-line delegate to it. The `sdl-baseline` skill gained a step 0 that scaffolds an un-adopted repo (on explicit user request only) before authoring the baseline. `self-check.yml` now shellchecks `plugins/sdl/lib/*.sh` and requires the new script; README documents the clone-free adoption path; plugin version bumped to 0.7.0.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | `SDL_REF` charset allowlist (`^[A-Za-z0-9._/-]+$`) before YAML interpolation; `uses:` repo path hardcoded | `plugins/sdl/lib/sync_to_repo.sh:19`, `:45` | pending (pre-commit review) |
| T2 | Explicit-request precondition gates scaffolding; skill still exits silently otherwise; script never overwrites or commits | `plugins/sdl/skills/sdl-baseline/SKILL.md:12`, `:19-22`; `plugins/sdl/lib/sync_to_repo.sh:36`, `:57` | pending (pre-commit review) |

## Secure coding practices applied <!-- SI-2 -->

- `set -euo pipefail` in both scripts; all path expansions quoted; `shellcheck` clean (now CI-enforced for `plugins/sdl/lib/*.sh`, `self-check.yml:43`).
- Input validation: target must contain `.git/` (`sync_to_repo.sh:27`); resolved plugin root must contain the template or the script dies before writing (`sync_to_repo.sh:29`).
- Fail-safe writes: existing `sdl.yml` and `baseline.md` are never overwritten (`sync_to_repo.sh:36`, `:57`).
- Single source of truth: repo-root script delegates via `exec` (`scripts/sync-to-repo.sh:5`) — the two distribution channels cannot drift.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. Bash + coreutils only; no network access; the Python tooling is untouched.

## Deviations from spec or threat model

The T1 `SDL_REF` allowlist was added during threat modeling, not in the original requirements — 01 asked only for preserved behavior; the guard tightens it. No other deviations.
