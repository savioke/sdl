# 03 — Implementation

## Summary of changes

`check_cycle_present` gains two arguments (the merge base and the templates dir) and one new branch: when the diff changed code and no cycle names the branch, it consults `check_adoption` before failing. `check_adoption` returns `None` unless the diff adds `docs/sdl/baseline.md` and every changed path is either under `docs/sdl/` or the newly-added `.github/workflows/sdl.yml`; on that shape it then requires a non-stub baseline and a caller-only workflow (`is_adoption_workflow`), failing with a pointed message if either is wrong. `added_files` is a new one-line wrapper over `git diff --diff-filter=A`. The missing-cycle message was rewritten — it read as if the gate demanded a particular branch name, which is how the field report described it.

Outside the validator: `sync_to_repo.sh` and `sdl-baseline/SKILL.md` now tell the user to fill the baseline before the adoption commit rather than after, since a split lands the stub in CI; `developer-guide.md` and `admin-setup.md` document the exemption and its edges; version 1.0.1 → 1.1.0 with the changelog entry (minor: only widens what passes).

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Admitted workflow must be the generated caller — a matching `savioke/sdl` reusable `uses:` must be present, and any inline `run:` or foreign `uses:` rejects the file | `plugins/sdl/lib/validate.py:61-68` (`SDL_CALLER_RE`, `INLINE_RUN_RE`), `:286-299` (`is_adoption_workflow`) | this branch |
| T2 | Allowlist over *every* changed path; anything else returns `None` and the ordinary cycle requirement stands | `plugins/sdl/lib/validate.py:313-319` | this branch |
| T3 | Exemption gated on `docs/sdl/baseline.md` being an addition, and on `sdl.yml` being an addition | `plugins/sdl/lib/validate.py:310-317`, `added_files` at `:222-224` | this branch |
| T4 | `is_nonstub` against the shipped `templates/baseline.md`; a stub is a hard failure naming `sdl-baseline` | `plugins/sdl/lib/validate.py:320-323` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- **Fail-closed classification.** Every predicate in the new path admits only what it positively recognizes: an unmatched `uses:` line rejects rather than being ignored, a `uses:` with a trailing comment rejects, an absent caller rejects, and an unrecognized changed path returns `None` (fall through to the strict requirement) rather than being skipped. This mirrors the dependency classifier's stance (`2026-07-09-dep-update-tier`).
- **Ordering.** A real cycle is checked first and wins; the exemption is only consulted on the path that was previously an unconditional failure. Nothing that passed before takes a different route through the function.
- **Input validation.** `SDL_CALLER_RE` anchors both ends and constrains the ref to `[\w./-]+`; `INLINE_RUN_RE` matches the YAML list-item form as well as the bare key. Neither regex has nested quantifiers, so there is no backtracking exposure on a hostile workflow file.
- **No new I/O surface.** `added_files` uses the same `run()` helper and `base...HEAD` range as `changed_files`; both file reads use the existing `errors="replace"` pattern. Nothing is executed, deserialized, or fetched — the workflow is parsed line-wise as text, not loaded as YAML, so no parser is introduced.
- **Blast radius of a bug.** The failure mode of a bug in the new code is a repo needing a cycle it should not have needed (noisy, recoverable), except in the T1/T3 directions, which is why both are pinned by tests rather than left to review.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. Stdlib only, as the rest of `lib/`.

## Deviations from spec or threat model

None. One implementation note: `check_adoption` distinguishes "not an adoption diff" (`None`, fall through) from "adoption diff that is wrong" (failing `Result`). The three-valued return is what lets a stub baseline produce a useful message instead of the generic missing-cycle failure — requirement 6 in `01`.
