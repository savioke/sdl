# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

String-only rename of the plugin marketplace identity from `savioke` to `relay`: the four identity/description fields in `.claude-plugin/marketplace.json`, the install target and printed instructions in `scripts/install.sh` (`sdl@savioke` → `sdl@relay`, update command), the update command in `docs/developer-guide.md` and `Plan.md`, and the company name in `docs/admin-setup.md`'s intro. Net diff: 11 insertions, 11 deletions across 5 files; no logic, control flow, or executable behavior changed. An interim version of the branch added legacy-marketplace auto-removal (`plugin uninstall` / `marketplace remove`) to `install.sh`; it was reverted per the scope decision in `01-requirements.md`.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Procedural, not code: sole existing user migrates his two installs manually (uninstall `sdl@savioke`, remove `savioke` marketplace, re-run `install.sh`). Defense in depth in code: the documented update command now names `relay`, so a half-migrated install fails at the documented step instead of drifting. | `scripts/install.sh:56,67,75`; `docs/developer-guide.md:28` | b2fc1a4 (+ pending revert commit for the auto-removal block) |

## Secure coding practices applied <!-- SI-2 -->

- `install.sh` edits confined to command-target strings and heredoc/printed text — no new network fetch, privileged operation, or control flow, preserving baseline:B3's `accept` disposition (verified per-hunk: `scripts/install.sh:56-57,67,75`).
- `.claude-plugin/marketplace.json` edits confined to identity fields (`name`, `displayName`, `owner.name`, `description`); the plugin `source` (`./plugins/sdl`) and the plugin list are untouched, so the artifact `claude plugin install` delivers is unchanged.
- `shellcheck` and `bash -n` pass on the edited script; `python3 -m json.tool` validates the manifest.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None.

## Deviations from spec or threat model

None against the final `01-requirements.md`/`02-threat-model.md`. Historical note: automated legacy-marketplace removal was implemented, then reverted before review when the scope decision was made (one self-migrating user does not justify new executable behavior in a baseline:B3 script). The revert is part of this branch's final diff.
