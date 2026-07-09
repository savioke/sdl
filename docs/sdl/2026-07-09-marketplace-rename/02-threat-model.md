# 02 — Threat Model

## Components and data flows

- **`.claude-plugin/marketplace.json`** — marketplace manifest read by `claude plugin`. Identity fields only (`name`, `displayName`, `owner.name`, description); the plugin `source` path is untouched, so what gets installed is unchanged.
- **`scripts/install.sh`** — workstation setup script (baseline:B3). Edits are string-only: the install target `sdl@savioke` → `sdl@relay-sdl` and printed footer text. The legacy-marketplace auto-removal considered during development was reverted before commit.
- **`docs/developer-guide.md`, `docs/admin-setup.md`, `Plan.md`** — documentation. No execution surface.

## Threats <!-- SR-2 -->

### T1 — Orphaned registration leaves stale plugin on existing installs

- **Category:** Denial of service
- **Component / flow:** existing developer machines with the marketplace registered as `savioke`, after `git pull` renames it to `relay-sdl` in the underlying clone.
- **Description:** The marketplace name has no migration path in Claude Code. After this merges and an existing install pulls, the old `savioke` registration no longer matches the manifest; `/plugin marketplace update savioke` fails and the `sdl@savioke` plugin silently stops receiving updates — stale SDL skills keep running on the developer machine.
- **Likelihood / Impact:** high / low — it happens deterministically on every pre-rename install, but there is exactly one existing user (the maintainer, two installations), who is performing the migration knowingly.
- **Mitigation:** manual migration by the sole existing user: `claude plugin uninstall sdl@savioke`, `claude plugin marketplace remove savioke`, re-run `install.sh` (registers `relay-sdl`, installs `sdl@relay-sdl`). Fresh installs are unaffected.
- **Mitigation type:** corrective
- **Defense in depth notes:** `install.sh`'s printed footer and `developer-guide.md` now name `relay-sdl` in the update command, so a half-migrated install fails loudly at the documented step rather than drifting unnoticed.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B3** — `install.sh` remains a workstation script; this edit changes strings only (install target, printed text), no new fetch, logic, or privileged operation. `accept` disposition unchanged.
- **2026-06-11-fix-update-instructions** wrote no numbered threats; its concern (documented update procedure must be accurate) carries into this diff — the documented command is now `/plugin marketplace update relay-sdl`, matching the renamed manifest.

## Out-of-scope threats

- Tampering with `marketplace.json` to deliver a different plugin — the `source` field is the vector and is untouched here; the general supply-chain concern is baseline:B1/B2, owned by PR review and the SDL gate.
- Marketplace-name squatting/spoofing of `relay-sdl` — marketplace names are per-user local identifiers in Claude Code, not a global registry; there is nothing to squat. Reserved-name collision checked (not an Anthropic-reserved name).
- Automated legacy-marketplace removal in `install.sh` — declined per `01-requirements.md` scope: new executable behavior in a B3 script isn't warranted for one self-migrating user. Owner: future cycle if the rename must reach unmanaged machines.

## Noted for future cycles

- If a marketplace rename ever recurs with real external users, add the remove/re-add migration to `install.sh` (re-threat-model against baseline:B3) rather than relying on manual steps.
- If `install.sh` ever gains a network fetch to refresh the marketplace automatically, re-threat-model against baseline:B3 and B5 (carried from 2026-06-11-fix-update-instructions).
