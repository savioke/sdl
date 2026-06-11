# 03 — Implementation

## Summary of changes

Pinned both third-party actions to commit SHAs with version comments: `actions/checkout` → `df4cb1c` (v6.0.3) and `actions/setup-python` → `a309ff8` (v6.2.0), across `sdl-validate.yml` (3 uses) and `self-check.yml` (4 uses). Added `.github/dependabot.yml` (grouped weekly `github-actions` updates, ignoring the `savioke/sdl` self-reference). Updated `baseline.md` B6 to mitigated.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| baseline:B6 | All third-party `uses:` pinned to immutable SHAs; Dependabot keeps them current | `.github/workflows/sdl-validate.yml`, `.github/workflows/self-check.yml`, `.github/dependabot.yml` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- Pinned to full 40-char commit SHAs, not tags; version retained as a trailing comment for readability.
- Bumped to the current major (v6/v6) so Dependabot updates stay within-major and low-risk. Inputs used (`fetch-depth`, `repository`, `ref`, `path`, `python-version`) are unchanged across these majors; the bumps are runtime-only (Node 24), satisfied by `ubuntu-latest`.
- Dependabot scoped to `github-actions`, grouped to one PR, with the `savioke/sdl` moving tag explicitly ignored.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

`actions/checkout` v4 → v6.0.3 (SHA-pinned); `actions/setup-python` v5 → v6.2.0 (SHA-pinned). No runtime dependencies (validator is standard-library only).

## Deviations from spec or threat model

None.
