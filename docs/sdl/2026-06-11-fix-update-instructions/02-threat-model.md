# 02 — Threat Model

## Components and data flows

- **`scripts/install.sh`** — workstation setup script (baseline:B3). Edit touches only the `cat` heredoc footer printed to the user; no logic, fetch, or privileged operation changes.
- **`docs/developer-guide.md`, `Plan.md`** — documentation. No execution surface.

## Threats <!-- SR-2 -->

No new presently-reachable threats. The change is documentation plus printed help text; it adds no input, network call, or privileged operation, and changes no agent-executed instruction. Per proportionality, nothing here earns a stanza.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B3** — `install.sh` is a workstation script, but this edit is confined to heredoc-printed text and comments. No new network fetch or privileged operation, so B3's `accept` disposition is unchanged.

## Out-of-scope threats

- Marketplace auto-update as an alternative to documenting the manual step — declined; it is the plugin-channel analogue of baseline:B5 (a bad release reaches everyone at once) and is unverified for local/path-based marketplaces. Owner: baseline / future cycle if revisited.

## Noted for future cycles

- If `install.sh` ever gains a network fetch to refresh the marketplace automatically, re-threat-model it against baseline:B3 and B5.
