# 03 — Implementation

## Summary of changes

`lib/validate.py` gains a `class: dependency-update` cycle type: a fail-closed classifier (`check_dep_class_diff`, `pin_only_workflow_diff`, `is_dep_manifest`) accepts only manifest/lockfile paths and workflow diffs whose every changed line is a SHA-pinned same-action same-major `uses:` bump; qualifying cycles need `.sdl-meta.yml` + `dep-update.md` (`check_dep_record`) instead of the four artifacts, with declared major bumps rejected. New `lib/check_pins.py` verifies every pinned action SHA against its version comment's upstream tag via the GitHub API. New `sdl-dep-update` skill, `templates/docs-sdl/dep-update.md`, and fleet policy `docs/dependency-updates.md`. `self-check.yml` gains a `pins` job and runs the new test module; plugin bumped to 0.4.0. Manifest-only diffs without a record get a warning (warn-first).

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Exact-filename manifest allowlist; pin-line shape + same `owner/repo` + same-major + no add/remove asymmetry; unclassifiable → fail; unknown class → fail | `lib/validate.py:60-113` (classifier), `lib/validate.py:116-134` (`check_dep_class_diff`), `lib/validate.py:330-336` (class dispatch); rejection cases pinned in `lib/test_validate.py:246-315` | pending (this branch) |
| T2 | Validator re-derives majors from the diff independently of the record (`pin_only_workflow_diff`); `check_pins.py` re-verifies SHA↔tag in CI; template labels attested-only checks | `lib/validate.py:106-113`, `lib/validate.py:137-163`, `lib/check_pins.py:81-110`, `.github/workflows/self-check.yml:24-31` | pending (this branch) |
| T3 | Not machine-mitigated (accepted): policy requires ecosystem integrity mode, human merge, trusted-automation sourcing; hand-edited lockfiles are an escalation trigger | `docs/dependency-updates.md` (Escalation tier, Checks, Merge rules) | pending (this branch) |

Commit column: this cycle's artifacts are authored before first commit; SHAs land with the PR (evidence per SM-5: PR/CI/git, not per-file sign-off).

## Secure coding practices applied <!-- SI-2 -->

- All new regexes anchored and linear (no nested quantifiers) against adversarial diff/record content (`lib/validate.py:72-78`, `lib/check_pins.py:32-40`).
- `check_pins.py`: stdlib HTTPS with default certificate verification, 30 s timeout, `HTTPError`/`URLError`/response-shape errors caught per pin and reported without the token; token read from env only, never printed (`lib/check_pins.py:67-101`).
- Subprocess use stays list-argv, no shell, `--` path separator in the new `git diff` call (`lib/validate.py:88`).
- Diff header parsing uses exact `"--- "`/`"+++ "` forms so dash-shaped content lines cannot be skipped as headers (`lib/validate.py:92-94`, regression test `lib/test_validate.py:302-305`).

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. Both new modules are Python standard library only, preserving the baseline requirement that the validator has no dependency supply-chain of its own.

## Deviations from spec or threat model

- Review found and closed a T1 gap not in the original design: removal-only pin changes (deleting a one-line `uses:` step) passed the classifier; now rejected (`lib/validate.py:110-112`).
- Policy doc originally overclaimed classifier coverage of manifest-content triggers; corrected to state plainly that lockfile/manifest *content* is not parsed and those triggers are attestation (T2/T3 honesty).
