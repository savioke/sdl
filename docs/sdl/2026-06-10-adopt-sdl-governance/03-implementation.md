# 03 — Implementation

## Summary of changes

Added `.github/workflows/sdl.yml`, which invokes the reusable validator at `savioke/sdl/.github/workflows/sdl-validate.yml@v1` on `pull_request` and `push`. Authored `docs/sdl/baseline.md` (standing exposure model and risk register B1–B6). Created this cycle. Updated `docs/admin-setup.md` to reflect that the repo now self-gates.

## Mitigations implemented <!-- SI-1 -->

No new threats in `02-threat-model.md`, so no per-threat mitigation rows. The new workflow inherits the standing supply-chain risks, mitigated as recorded in the baseline.

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| baseline:B1 | Org-owned reusable workflow, read-only validation, PR review | `.github/workflows/sdl.yml` | this branch |
| baseline:B5 | Single consumer; exact-tag pinning available if needed | `.github/workflows/sdl.yml` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- No `permissions:` elevation; default `GITHUB_TOKEN`, read-only validation.
- No secrets referenced.
- Reusable workflow pinned to the org-owned `@v1`; no third-party action added directly.
- No new runtime dependencies (validator is standard-library only).

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None.

## Deviations from spec or threat model

None.
