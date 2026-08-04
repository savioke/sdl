# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

Added a release procedure and the two tools that make it mechanical. `scripts/release.sh` reads the version from `plugin.json`, refuses unless `main` is clean, matches `origin/main`, has green checks, has a `CHANGELOG.md` entry, and has no existing tag for that version; then creates the annotated (signed where configured) `vX.Y.Z`, force-moves the `vX` alias, and rewrites `source.ref` and `version` in the marketplace manifest via a temp clone. `scripts/check_release.py` is its read-only counterpart in CI: PR mode fails a diff that changes shipped content without a version increase and changelog entry; released mode fails `main` when the declared version has no tag, when the alias and the exact tag disagree, when shipped files have changed since the tag, or when the marketplace manifest names something else. `self-check.yml` gains a `release` job running both modes plus 44 new unit tests, and a daily schedule so manifest and action-pin drift surface without a push. Documentation is `docs/releasing.md` (procedure and compatibility contract) plus `CHANGELOG.md`; `admin-setup.md`, `developer-guide.md`, `README.md`, and `Plan.md` were corrected where they described the old tag-by-judgment process or told clone-based developers that `git pull` alone upgrades them. The plugin is promoted to 1.0.0 and the marketplace manifest pins `v1.0.0` instead of `main`.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Bounded read (1 MB) before parse; 30 s timeout; HTTPS with default cert verification; every failure returns an error value and is downgraded to a note by the caller, so an outage cannot masquerade as drift; every field of the parsed document is type-checked before use, so a well-formed-but-wrong-shaped manifest is drift rather than a crash | `scripts/check_release.py:51`, `:78-122`, `:150-177`, `:268-275` | pending (pre-commit review) |
| T2 | Strict `^[0-9]+\.[0-9]+\.[0-9]+$` gate before the version reaches a ref name, tag message, or any command; alias derived by parameter expansion from the validated value; same rule enforced at PR time | `scripts/release.sh:56-59`; `scripts/check_release.py:55`, `:58-60` | pending (pre-commit review) |
| T3 | No CI credential can write a tag or the manifest — `check_release.py` only reads; release is interactive with a printed plan and confirmation; immutable tag refused if it exists locally or on the remote; alias push is the only force; green-checks precondition | `scripts/release.sh:74-77`, `:81-104`, `:117-119`, `:136-140`; `.github/workflows/self-check.yml` (`release` job, no `permissions:` grant beyond default read) | pending (pre-commit review) |

## Secure coding practices applied <!-- SI-2 -->

- **Input validation before use, not after:** the version is regex-gated at `release.sh:57` before it becomes `$tag`, `$alias_tag`, a `git tag` argument, or a commit message. Verified by execution, not inspection — see 04.
- **Shell hygiene:** `set -euo pipefail`, every expansion quoted, `shellcheck` clean (CI-enforced, `self-check.yml`); temp clone directory created with `mktemp -d` (`release.sh:145`) and removed by an `EXIT` trap (`release.sh:32-34`).
- **Fail-closed ordering:** all refusals happen before any mutation; the immutable tag is pushed before the alias moves (`release.sh:135-140`), so the alias can never point at an object the remote does not have.
- **Bounded, timed, non-raising network I/O** for the one external fetch (`check_release.py:150-177`); no other network access in either tool.
- **No credential handling:** neither tool reads, writes, or prints a token; `release.sh` delegates authentication entirely to the maintainer's `gh`/`git` configuration, and CI uses only the default read-only `GITHUB_TOKEN`.
- **Correct diff range:** shipped-change detection uses three-dot (`merge-base..HEAD`, `check_release.py:135-142`), matching `validate.py`; a two-dot comparison would attribute `main`'s post-branch-point changes to the PR. Caught in functional testing and regression-tested.
- **Stdlib only**, consistent with the standing requirement in `baseline.md`.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. `check_release.py` is standard library only. `release.sh` uses `git`, `gh`, and `python3` — all already required by this repo's workflow; `gh` is newly required for *releasing* (it was previously optional tooling), which is a maintainer-workstation prerequisite now stated in `docs/releasing.md`. No third-party actions added, so no new pins.

## Deviations from spec or threat model

- **The marketplace manifest is not edited by this cycle at all.** It cannot be: `source.ref` must name `v1.0.0`, and that tag does not exist until the release runs. `release.sh` makes the edit in its own clone as step 6, which was exercised against a fixture (see 04). The manifest therefore says `main` until the moment of release.
- **Released-mode drift detection runs daily, not on push to `main` as 01 implied.** Requirement SR-6 (detect drift without CI holding write credentials) is met either way, but running it on push deadlocked against SR-3 (do not release a commit whose checks are red). See the defect in 04; the cost is up-to-a-day detection latency for a forgotten release, recorded as R5.
- **T1's read cap was added during threat modeling**, not requirements — 01 asked only for graceful failure (SR-8). Tightening, not scope change.
- **The green-checks precondition (SR-3) is enforced against check *runs*, not commit statuses.** GitHub Actions reports check runs; a repo using only legacy commit statuses would see "no checks found" and be refused, which is the safe direction.
