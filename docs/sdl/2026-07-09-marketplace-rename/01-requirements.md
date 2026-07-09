# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Rename the Claude Code plugin marketplace from `savioke` to `relay-sdl` following the company rename, qualified with `-sdl` (rather than bare `relay`) to leave the unqualified namespace free for future unrelated Relay plugin marketplaces. The GitHub org remains `savioke` (the desired name is taken; renaming an org is disruptive), so this cycle changes only the marketplace identity: `name`, `displayName`, `owner.name`, and description in `.claude-plugin/marketplace.json`, the `sdl@savioke` → `sdl@relay-sdl` install/update references in `scripts/install.sh` output and docs, and one prose mention of the company in `docs/admin-setup.md`. The marketplace name is an arbitrary identifier — nothing binds it to the GitHub org.

## Scope

In scope: marketplace identity fields in `.claude-plugin/marketplace.json`; `sdl@relay-sdl` and `/plugin marketplace update relay-sdl` strings in `scripts/install.sh`, `docs/developer-guide.md`, and `Plan.md`; company-name prose in `docs/admin-setup.md`.

Out of scope: every `savioke/sdl` GitHub path (clone URLs, the reusable-workflow ref, `check_pins.py --exempt`) — these refer to the org, which is not changing. Also out of scope: automated removal of the legacy `savioke` marketplace registration in `install.sh`. Considered and reverted — it would add new executable behavior (`plugin uninstall` / `marketplace remove`) to a baseline:B3 workstation script for the benefit of exactly one existing user (the maintainer), who migrates his two installations manually instead. Revisit if the rename ever needs to reach machines the maintainer does not control.

## Assets touched <!-- SR-1 -->

`scripts/install.sh` (baseline:B3 workstation script — string-only edits to the install target and printed footer) and `.claude-plugin/marketplace.json` (integrity asset: it determines which plugin `claude plugin install` delivers to developer machines; identity fields only, `source` untouched). Docs otherwise. Standing assets per `baseline.md`.

## Trust boundaries crossed <!-- SR-2 -->

None new. Exposure model per `baseline.md`.

## Data classification <!-- SR-1 -->

None new. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None.

## Security requirements <!-- SR-3, SR-4 -->

- The `install.sh` edit must remain string-only: no new network fetch, privileged operation, or executable logic, so baseline:B3's disposition stays unchanged.
- `.claude-plugin/marketplace.json` changes are limited to identity/description fields; the plugin `source` path must not change.
- The new name `relay-sdl` must be a valid marketplace identifier (kebab-case, not an Anthropic-reserved name).
- Docs must state the correct post-rename update command (`/plugin marketplace update relay-sdl`); the rename is a breaking change for registered installs, migrated manually by the sole existing user.

## Related prior cycles

- `2026-06-11-fix-update-instructions` — wrote the `sdl@savioke` update instructions this cycle renames; same files (`install.sh` footer, `developer-guide.md`, `Plan.md`).

## Carried-forward residual risks

None. No prior cycle has residual risks with `Disposition: defer` or `mitigate-later` in its `04-verification.md`.
