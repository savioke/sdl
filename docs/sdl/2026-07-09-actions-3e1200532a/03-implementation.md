# 03 — Implementation

## Summary of changes

Commit 62d26dc (Dependabot) updates every pinned `uses:` in the two workflows: `actions/checkout@df4cb1c0… # v6.0.3` → `actions/checkout@9c091bb2… # v7.0.0` (5 sites) and `actions/setup-python@a309ff8b… # v6.2.0` → `actions/setup-python@ece7cb06… # v6.3.0` (2 sites). No other changes.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1     | SHA pins retained and verified against upstream tags; version comments kept accurate | `.github/workflows/sdl-validate.yml:21,26,33`; `.github/workflows/self-check.yml:11,14,27,36` | 62d26dc |

## Secure coding practices applied <!-- SI-2 -->

Not applicable — configuration-only diff; no application code.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

- `actions/checkout` v6.0.3 → v7.0.0 (major). Headline change is a security hardening: blocks checking out fork PR refs under `pull_request_target`/`workflow_run` (actions/checkout#2454); also an ESM migration and dependency bumps. No input or default we rely on changed.
- `actions/setup-python` v6.3.0 (minor): RHEL support, cache-key and pip-cache fixes, dependency bumps.

## Deviations from spec or threat model

None. Retroactive-docs note: Dependabot authored the change before this cycle existed; 01/02 were written against the finished diff rather than ahead of it, accepted for dependency-bump PRs.
