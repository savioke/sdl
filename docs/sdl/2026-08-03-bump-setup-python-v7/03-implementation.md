# 03 — Implementation

## Summary of changes

Commit 961d53d (Dependabot) updates every pinned `uses:` in the two workflows: `actions/checkout@9c091bb2… # v7.0.0` → `actions/checkout@3d3c42e5… # v7.0.1` (6 sites) and `actions/setup-python@ece7cb06… # v6.3.0` → `actions/setup-python@5fda3b95… # v7.0.0` (2 sites). No other changes; no `with:` block was touched.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | SHA pins retained and verified against upstream tags; version comments kept accurate | `.github/workflows/sdl-validate.yml:21,26,33`; `.github/workflows/self-check.yml:11,14,30,39,48` | 961d53d |
| T2 | Both `setup-python` sites left configured with `python-version` only; no removed input was in use | `.github/workflows/sdl-validate.yml:33-35`; `.github/workflows/self-check.yml:14-16` | 961d53d (no change required) |

## Secure coding practices applied <!-- SI-2 -->

Not applicable — configuration-only diff; no application code.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

- `actions/setup-python` v6.3.0 → **v7.0.0** (major). The only breaking change is removal of the `pip-install` input. Otherwise: migration to ESM, `@actions/cache` → 6.2.0, `certifi` 2020.6.20 → 2024.7.4 in test fixtures, stderr warnings reclassified from errors to warnings in annotations, and added validation plus retry on manifest fetch (a robustness improvement on the action's own download path). `runs.using` stays `node24`, so no runner-version requirement change.
- `actions/checkout` v7.0.0 → v7.0.1 (patch). Skips the unsafe-PR check when the input is default, trims only ASCII whitespace for branch names, escapes values passed to `git config --unset`, plus dependency bumps.

## Deviations from spec or threat model

None. Retroactive-docs note: Dependabot authored the change before this cycle existed; 01/02 were written against the finished diff rather than ahead of it, accepted for dependency-bump PRs. The commit was moved onto branch `bump-setup-python-v7` so the cycle slug is readable and Dependabot's rebase loop is not disturbed.
