# 03 — Implementation

## Summary of changes

`on: [pull_request, push]` becomes `on: {pull_request, push: {branches: [main]}}` in the workflow `sync_to_repo.sh` writes and in this repo's own `sdl.yml`, with a comment recording why. Plugin version 1.0.0 → 1.0.1 plus the changelog entry, which tells existing consumers to apply the same edit themselves since `sync_to_repo.sh` will not overwrite a workflow that already exists.

## Mitigations implemented <!-- SI-1 -->

No threats in `02`, so no mitigation rows.

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| —      | none identified | | |

## Secure coding practices applied <!-- SI-2 -->

Not applicable — configuration-only diff; no application code.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None.

## Deviations from spec or threat model

None.
